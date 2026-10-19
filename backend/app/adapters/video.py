"""TikTok / Instagram access through yt-dlp.

Two calls, cheapest first: `fetch_metadata` reads the caption without
downloading anything; `download` fetches just enough of the video to
transcribe it.
"""

from dataclasses import dataclass
from pathlib import Path

import yt_dlp

# Reels longer than this are rarely recipes and would strain the free host.
MAX_DURATION_SECONDS = 10 * 60


class VideoError(RuntimeError):
    """The platform blocked us, the link is dead, or the video is unusable."""


@dataclass
class VideoInfo:
    url: str
    title: str
    description: str
    uploader: str | None
    duration: float | None


_BASE_OPTS = {"quiet": True, "noprogress": True, "no_warnings": True, "noplaylist": True}


def _friendly(e: Exception) -> VideoError:
    text = str(e).lower()
    if "login" in text or "private" in text or "cookies" in text:
        return VideoError("This video needs a login to watch, so we can't read it. Paste the caption or ingredient list below instead.")
    if "not available" in text or "404" in text or "removed" in text:
        return VideoError("We couldn't find this video. It may have been deleted. Check the link, or paste the recipe text below.")
    return VideoError("We couldn't get this video. The platform may be blocking access. Paste the caption or ingredient list below instead.")


def fetch_metadata(url: str) -> VideoInfo:
    try:
        with yt_dlp.YoutubeDL(_BASE_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:  # yt-dlp raises many error types
        raise _friendly(e) from e
    return VideoInfo(
        url=info.get("webpage_url") or url,
        title=info.get("title") or "",
        description=info.get("description") or "",
        uploader=info.get("uploader") or info.get("channel"),
        duration=info.get("duration"),
    )


# Only the sound is transcribed, so take the smallest file that has it: an
# audio-only stream if the platform offers one, else the lowest-quality video
# that has sound (TikTok usually serves only combined mp4s). Smaller files keep
# the 512 MB free host further from its limit. No ffmpeg step is needed:
# faster-whisper reads the audio track straight out of either file.
AUDIO_FORMAT = "bestaudio/worst[acodec!=none][ext=mp4]/worst[acodec!=none]"


def download(url: str, workdir: Path) -> Path:
    """Download the audio (or smallest video with sound) into `workdir` and return its path. Caller deletes it."""
    opts = {
        **_BASE_OPTS,
        "format": AUDIO_FORMAT,
        "outtmpl": str(workdir / "media.%(ext)s"),
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = Path(ydl.prepare_filename(info))
    except Exception as e:
        raise _friendly(e) from e
    if not path.exists():
        raise VideoError("We couldn't download this video. Paste the caption or ingredient list below instead.")
    return path
