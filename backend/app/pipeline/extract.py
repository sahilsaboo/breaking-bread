"""Link validation and recipe extraction.

Real pipeline (docs/technical-spec.md), cheapest stage first, stopping early:
  metadata  read the caption with yt-dlp (no download) and try to structure it
  audio     always (except very long videos): download and transcribe. The transcript
            times drive cook mode's step-by-step video clips. If the caption wasn't
            enough, the recipe is also structured again with the transcript; if it was,
            a cheap call checks the transcript for a serving count said out loud
  merge     write beginner steps and estimate prices/macros
The frame stage (Claude vision on sampled frames) isn't built yet.

Without an Anthropic API key, or with PIPELINE_MODE=stub, every link returns
the sample fixture instead (STUB), so the app and tests run without network.
"""

import logging
import os
import tempfile
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

from app.adapters import claude, transcribe, video
from app.models import Macros, Product, Recipe, Stage, Step
from app.pipeline import estimates, guidance, structure
from app.pipeline.fixtures import sample
from app.pipeline.result import Extraction

log = logging.getLogger(__name__)

TIKTOK_HOSTS = {"tiktok.com", "www.tiktok.com", "m.tiktok.com", "vm.tiktok.com", "vt.tiktok.com"}
INSTAGRAM_HOSTS = {"instagram.com", "www.instagram.com"}
INSTAGRAM_PATH_PREFIXES = ("/reel/", "/reels/", "/p/")

LINK_STAGES = [Stage.metadata, Stage.audio, Stage.merge]
TEXT_STAGES = [Stage.merge]

# Downloading and transcribing is the memory-hungry part; on the 512 MB free
# host, run one at a time.
_heavy_work = threading.Semaphore(1)


class InvalidLinkError(ValueError):
    pass


class ExtractionError(RuntimeError):
    """Raised when a platform can't be reached or yields no usable recipe."""


NO_RECIPE = (
    "We couldn't find a recipe in this video. Paste the caption or ingredient list below "
    "and we'll take it from there."
)


def validate_link(url: str) -> str:
    """Check the link is a TikTok or Instagram Reel URL and return it trimmed."""
    url = url.strip()
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https"):
        raise InvalidLinkError("That doesn't look like a link. It should start with https://")
    if host in TIKTOK_HOSTS:
        return url
    if host in INSTAGRAM_HOSTS and parsed.path.startswith(INSTAGRAM_PATH_PREFIXES):
        return url
    raise InvalidLinkError("Paste a TikTok or Instagram Reel link.")


def pipeline_mode() -> str:
    """'real' when Claude is configured, else 'stub'. PIPELINE_MODE overrides."""
    mode = os.environ.get("PIPELINE_MODE", "").lower()
    if mode in ("stub", "real"):
        return mode
    return "real" if claude.is_configured() else "stub"


# --- Stub ----------------------------------------------------------------------


def stub_extraction(*, recipe_id: str, url: str | None, text: str | None) -> Extraction:
    # STUB: any link containing "stub-fail" fails, so the error and paste-text
    # fallback can be exercised without a real broken video.
    if url and "stub-fail" in url:
        raise ExtractionError(
            "We couldn't get this video. The platform may be blocking access. "
            "Paste the caption or ingredient list below instead."
        )
    data = sample()
    recipe = Recipe.model_validate({**data["recipe"], "id": recipe_id})
    recipe.source_url = url
    if text is not None:
        recipe.creator = None
        for ingredient in recipe.ingredients:
            ingredient.source = "pasted"
    products = {
        i.id: Product(store_id="stub", store_name="Estimated prices", price_type="estimate", **data["products"][i.id])
        for i in recipe.ingredients
        if i.id in data["products"]
    }
    approximate = recipe.servings.estimated or any(i.estimated for i in recipe.ingredients)
    # The fixture states macros per serving; the pipeline carries whole-recipe totals.
    total = {k: v * recipe.servings.value for k, v in data["macros_per_serving"].items()}
    return Extraction(
        recipe=recipe,
        steps=[Step.model_validate(s) for s in data["steps"]],
        products=products,
        macros_total=Macros(**total, approximate=approximate),
    )


# --- Real ----------------------------------------------------------------------


def _finish(
    recipe: Recipe,
    *,
    caption: str | None = None,
    segments: list[transcribe.Segment] | None = None,
    pasted: str | None = None,
    video_duration: float | None = None,
) -> Extraction:
    """Merge stage: steps and estimates don't depend on each other, so run them together."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        steps_future = pool.submit(
            guidance.write_steps, recipe, caption=caption, segments=segments, pasted=pasted, video_duration=video_duration
        )
        estimates_future = pool.submit(estimates.estimate, recipe)
        steps = steps_future.result()
        products, macros = estimates_future.result()
    return Extraction(recipe=recipe, steps=steps, products=products, macros_total=macros)


def _transcribe_video(url: str) -> list[transcribe.Segment]:
    with _heavy_work, tempfile.TemporaryDirectory(prefix="bb-video-") as tmp:
        media = video.download(url, Path(tmp))
        return transcribe.transcribe(media)
        # The temp directory, video included, is deleted here (spec: don't keep media).


def real_extraction(
    *,
    recipe_id: str,
    url: str | None,
    text: str | None,
    on_stage: Callable[[Stage], None],
    skip_stage: Callable[[Stage], None],
) -> Extraction:
    try:
        if text is not None:
            on_stage(Stage.merge)
            draft, recipe = structure.structure_recipe(recipe_id=recipe_id, source_url=None, pasted=text)
            if not draft.is_recipe or not recipe.ingredients:
                raise ExtractionError("We couldn't find ingredients in that text. Paste the ingredient list with amounts.")
            return _finish(recipe, pasted=text)

        assert url is not None
        on_stage(Stage.metadata)
        info = video.fetch_metadata(url)
        caption = "\n".join(p for p in (info.title, info.description) if p).strip() or None
        draft, recipe = None, None
        if caption:
            draft, recipe = structure.structure_recipe(
                recipe_id=recipe_id, source_url=info.url, creator=info.uploader, caption=caption
            )

        caption_is_enough = bool(draft and draft.is_recipe and draft.complete and recipe and recipe.ingredients)
        too_long = info.duration is not None and info.duration > video.MAX_DURATION_SECONDS
        segments: list[transcribe.Segment] = []
        if too_long:
            skip_stage(Stage.audio)
        else:
            # Transcribe even when the caption has the whole recipe: the segment
            # times are what let cook mode play each step's clip.
            on_stage(Stage.audio)
            try:
                segments = _transcribe_video(info.url)
            except Exception as e:
                if not caption_is_enough:
                    raise
                # The recipe is already complete; only the video timing is lost.
                log.warning("Transcription failed, continuing with the caption recipe: %s", e)
            if segments and caption_is_enough and recipe is not None and recipe.servings.estimated:
                # The caption recipe stays; only check for a serving count said out loud.
                try:
                    spoken = structure.servings_from_transcript("\n".join(s.text for s in segments))
                except claude.ClaudeError as e:
                    log.warning("Servings check failed, keeping the estimate: %s", e)
                    spoken = None
                if spoken is not None:
                    recipe.servings = spoken
            if segments and not caption_is_enough:
                transcript = "\n".join(s.text for s in segments)
                draft, recipe = structure.structure_recipe(
                    recipe_id=recipe_id,
                    source_url=info.url,
                    creator=info.uploader,
                    caption=caption,
                    transcript=transcript,
                )

        if draft is None or recipe is None or not draft.is_recipe or not recipe.ingredients:
            raise ExtractionError(NO_RECIPE)

        on_stage(Stage.merge)
        # The transcript times let cook mode follow along with the video.
        return _finish(recipe, caption=caption, segments=segments or None, video_duration=info.duration)
    except video.VideoError as e:
        raise ExtractionError(str(e)) from e
    except claude.ClaudeError as e:
        raise ExtractionError(str(e)) from e
