"""The video and transcription adapters' settings, checked without network or models."""

import sys
import types

import yt_dlp

from app.adapters import transcribe, video


def pick(formats):
    """Run yt-dlp's real format selection on a fake video, without downloading."""
    info = {"id": "1", "title": "t", "extractor": "fake", "extractor_key": "Fake", "webpage_url": "https://x", "formats": formats}
    with yt_dlp.YoutubeDL({"quiet": True, "format": video.AUDIO_FORMAT, "simulate": True}) as ydl:
        return ydl.process_video_result(info, download=False)["format_id"]


def mp4(format_id, height, acodec="aac"):
    return {"format_id": format_id, "url": "https://x/" + format_id, "ext": "mp4", "height": height, "width": height, "vcodec": "h264", "acodec": acodec, "tbr": height}


def test_download_prefers_audio_only():
    audio = {"format_id": "audio", "url": "https://x/a", "ext": "m4a", "vcodec": "none", "acodec": "aac", "abr": 128}
    assert pick([mp4("hd", 1080), audio]) == "audio"


def test_download_falls_back_to_smallest_video_with_sound():
    # TikTok usually serves only combined mp4s.
    formats = [mp4("hd", 1080), mp4("sd", 540), mp4("silent", 240, acodec="none")]
    assert pick(formats) == "sd"


def test_whisper_runs_on_one_thread_by_default(monkeypatch, tmp_path):
    seen = {}

    class FakeWhisper:
        def __init__(self, model, **kwargs):
            seen.update(kwargs, model=model)

        def transcribe(self, path, **_):
            return iter([types.SimpleNamespace(start=0.0, end=1.0, text=" hi ")]), None

    monkeypatch.setitem(sys.modules, "faster_whisper", types.SimpleNamespace(WhisperModel=FakeWhisper))
    monkeypatch.delenv("WHISPER_THREADS", raising=False)
    assert transcribe.transcribe(tmp_path / "media.mp4") == [transcribe.Segment(0.0, 1.0, "hi")]
    assert seen["cpu_threads"] == 1

    monkeypatch.setenv("WHISPER_THREADS", "2")
    transcribe.transcribe(tmp_path / "media.mp4")
    assert seen["cpu_threads"] == 2
