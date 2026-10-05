"""Link validation and recipe extraction.

STUB: `extract_recipe` returns the sample fixture. The real version runs
metadata -> audio -> frames -> merge (see docs/technical-spec.md).
"""

import uuid
from urllib.parse import urlparse

from app.models import Recipe, Stage
from app.pipeline.fixtures import sample

TIKTOK_HOSTS = {"tiktok.com", "www.tiktok.com", "m.tiktok.com", "vm.tiktok.com", "vt.tiktok.com"}
INSTAGRAM_HOSTS = {"instagram.com", "www.instagram.com"}
INSTAGRAM_PATH_PREFIXES = ("/reel/", "/reels/", "/p/")

LINK_STAGES = [Stage.metadata, Stage.audio, Stage.frames, Stage.merge]
TEXT_STAGES = [Stage.merge]


class InvalidLinkError(ValueError):
    pass


class ExtractionError(RuntimeError):
    """Raised when a platform can't be reached or yields no usable recipe."""


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


def extract_recipe(*, url: str | None = None, text: str | None = None) -> Recipe:
    # STUB: any link containing "stub-fail" fails, so the error and paste-text
    # fallback can be exercised before real extraction exists.
    if url and "stub-fail" in url:
        raise ExtractionError(
            "We couldn't get this video. The platform may be blocking access. "
            "Paste the caption or ingredient list below instead."
        )

    data = sample()["recipe"]
    recipe = Recipe.model_validate({**data, "id": f"rcp_{uuid.uuid4().hex[:12]}"})
    recipe.source_url = url
    if text is not None:
        recipe.creator = None
        for ingredient in recipe.ingredients:
            ingredient.source = "pasted"
    return recipe
