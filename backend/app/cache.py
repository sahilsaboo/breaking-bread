"""SQLite cache of finished extractions (docs/decisions.md #9).

Re-pasting a video someone already processed returns the stored result
instantly, with no download, transcription, or Claude calls. Keys are the
video's identity (TikTok video id, Instagram reel code) so different
spellings of the same link match; pasted text is keyed by a hash.

Best effort: the free host wipes its disk on restart, and any cache error is
logged and treated as a miss. Set EXTRACTION_CACHE=off to always reprocess
(for example while tuning prompts).
"""

import hashlib
import json
import logging
import os
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import urlparse

from app.models import Macros, Product, Recipe, Step
from app.pipeline.result import Extraction

log = logging.getLogger(__name__)

# Bump when prompts or the output schema change, so old results aren't served.
CACHE_VERSION = 1


def enabled() -> bool:
    return os.environ.get("EXTRACTION_CACHE", "on").lower() not in ("off", "0", "false", "no")


def _db_path() -> Path:
    return Path(os.environ.get("CACHE_DB", Path(__file__).resolve().parent.parent / ".cache" / "extractions.sqlite3"))


def key_for_url(url: str) -> str:
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower().removeprefix("www.").removeprefix("m.")
    path = parsed.path.rstrip("/")
    if host.endswith("tiktok.com") and (m := re.search(r"/video/(\d+)", path)):
        return f"tiktok:{m.group(1)}"
    if host.endswith("instagram.com") and (m := re.match(r"/(?:reel|reels|p)/([^/]+)", path)):
        return f"instagram:{m.group(1)}"
    # Short links (vm.tiktok.com/...) only resolve after fetching; key them as written.
    return f"url:{host}{path}"


def key_for_text(text: str) -> str:
    normalized = " ".join(text.lower().split())
    return "text:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=5)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS extractions (key TEXT PRIMARY KEY, version INTEGER NOT NULL, data TEXT NOT NULL)"
    )
    return conn


def _dump(e: Extraction) -> str:
    return json.dumps(
        {
            "recipe": e.recipe.model_dump(mode="json"),
            "steps": [s.model_dump(mode="json") for s in e.steps],
            "products": {k: p.model_dump(mode="json") for k, p in e.products.items()},
            "macros_total": e.macros_total.model_dump(mode="json"),
        },
        ensure_ascii=False,
    )


def _load(data: str, recipe_id: str) -> Extraction:
    d = json.loads(data)
    recipe = Recipe.model_validate({**d["recipe"], "id": recipe_id})
    return Extraction(
        recipe=recipe,
        steps=[Step.model_validate(s) for s in d["steps"]],
        products={k: Product.model_validate(p) for k, p in d["products"].items()},
        macros_total=Macros.model_validate(d["macros_total"]),
    )


def get(key: str, *, recipe_id: str) -> Extraction | None:
    """The stored extraction for `key`, re-labeled with a fresh recipe id, or None."""
    if not enabled():
        return None
    try:
        with closing(_connect()) as conn:
            row = conn.execute("SELECT data FROM extractions WHERE key = ? AND version = ?", (key, CACHE_VERSION)).fetchone()
        return _load(row[0], recipe_id) if row else None
    except (sqlite3.Error, OSError, ValueError, KeyError) as e:
        log.warning("Cache read failed for %s: %s", key, e)
        return None


def put(keys: list[str], extraction: Extraction) -> None:
    if not enabled():
        return
    try:
        data = _dump(extraction)
        with closing(_connect()) as conn, conn:  # closing() closes; the inner `conn` commits
            conn.executemany(
                "INSERT OR REPLACE INTO extractions (key, version, data) VALUES (?, ?, ?)",
                [(k, CACHE_VERSION, data) for k in dict.fromkeys(keys)],
            )
    except (sqlite3.Error, OSError, ValueError) as e:
        log.warning("Cache write failed: %s", e)
