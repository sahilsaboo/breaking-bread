"""Link validation and recipe extraction.

Real pipeline (docs/technical-spec.md), three Claude calls per new video:
  cache     a link or text someone already processed returns the stored result (no cost)
  metadata  read the caption with yt-dlp (no download)
  audio     always (except very long videos): download and transcribe. The transcript
            times drive cook mode's step-by-step video clips
  merge     one call structures the recipe from caption + transcript together
            (ingredients, amounts, servings said out loud); then, in parallel, one
            call writes beginner steps and one estimates prices/macros
The frame stage (Claude vision on sampled frames) isn't built yet.

Without an Anthropic API key, or with PIPELINE_MODE=stub, every link returns
the sample fixture instead (STUB), so the app and tests run without network.
"""

import contextvars
import logging
import os
import tempfile
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

from app import cache
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
        # Run each call in a copy of this context so its token usage is counted for this job.
        steps_future = pool.submit(
            contextvars.copy_context().run,
            guidance.write_steps,
            recipe,
            caption=caption,
            segments=segments,
            pasted=pasted,
            video_duration=video_duration,
        )
        estimates_future = pool.submit(contextvars.copy_context().run, estimates.estimate, recipe)
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
    on_cache_hit: Callable[[], None] | None = None,
) -> Extraction:
    def cached(key: str) -> Extraction | None:
        hit = cache.get(key, recipe_id=recipe_id)
        if hit is not None:
            log.info("Cache hit for %s", key)
            if on_cache_hit:
                on_cache_hit()
            on_stage(Stage.merge)
        return hit

    try:
        if text is not None:
            text_key = cache.key_for_text(text)
            if hit := cached(text_key):
                return hit
            on_stage(Stage.merge)
            draft, recipe = structure.structure_recipe(recipe_id=recipe_id, source_url=None, pasted=text)
            if not draft.is_recipe or not recipe.ingredients:
                raise ExtractionError("We couldn't find ingredients in that text. Paste the ingredient list with amounts.")
            result = _finish(recipe, pasted=text)
            cache.put([text_key], result)
            return result

        assert url is not None
        link_key = cache.key_for_url(url)
        if hit := cached(link_key):
            return hit
        on_stage(Stage.metadata)
        info = video.fetch_metadata(url)
        # Short links (vm.tiktok.com/...) only reveal the video id after fetching.
        video_key = cache.key_for_url(info.url)
        if video_key != link_key and (hit := cached(video_key)):
            cache.put([link_key], hit)
            return hit
        caption = "\n".join(p for p in (info.title, info.description) if p).strip() or None

        # Transcribe even when the caption has the whole recipe: the segment times
        # are what let cook mode play each step's clip. Doing it before structuring
        # means one Claude call reads caption and transcript together (ingredients,
        # amounts, and a serving count said out loud) instead of one per source.
        too_long = info.duration is not None and info.duration > video.MAX_DURATION_SECONDS
        segments: list[transcribe.Segment] = []
        transcription_error: Exception | None = None
        if too_long:
            skip_stage(Stage.audio)
        else:
            on_stage(Stage.audio)
            try:
                segments = _transcribe_video(info.url)
            except Exception as e:
                if not caption:
                    raise
                # A complete caption can still carry the recipe; only video timing is lost.
                log.warning("Transcription failed, trying the caption alone: %s", e)
                transcription_error = e

        transcript = "\n".join(s.text for s in segments) or None
        if not caption and not transcript:
            raise ExtractionError(NO_RECIPE)
        draft, recipe = structure.structure_recipe(
            recipe_id=recipe_id, source_url=info.url, creator=info.uploader, caption=caption, transcript=transcript
        )
        if transcription_error is not None and not draft.complete:
            # Without the audio, a partial caption would mean a recipe with missing ingredients.
            raise transcription_error
        if not draft.is_recipe or not recipe.ingredients:
            raise ExtractionError(NO_RECIPE)

        on_stage(Stage.merge)
        # The transcript times let cook mode follow along with the video.
        result = _finish(recipe, caption=caption, segments=segments or None, video_duration=info.duration)
        cache.put([link_key, video_key], result)
        return result
    except video.VideoError as e:
        raise ExtractionError(str(e)) from e
    except claude.ClaudeError as e:
        raise ExtractionError(str(e)) from e
