"""Speech-to-text with faster-whisper (local, CPU, int8).

The model size is still open (docs/decisions.md #13): the free host has
512 MB, so the default is the smallest model. Override with WHISPER_MODEL
(tiny, base, small, ...) once the spike settles it.

The model is loaded per call and released afterwards, so its memory isn't
held between jobs on the small host. It runs on one CPU thread by default
(faster-whisper's default is 4, each with its own working memory); the free
host has a fraction of a CPU, so extra threads add memory without adding
speed. Override with WHISPER_THREADS.
"""

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MODEL = "tiny"
DEFAULT_THREADS = 1


@dataclass
class Segment:
    start: float
    end: float
    text: str


def transcribe(media: Path) -> list[Segment]:
    from faster_whisper import WhisperModel  # heavy import; only load when needed

    whisper = WhisperModel(
        os.environ.get("WHISPER_MODEL", DEFAULT_MODEL),
        device="cpu",
        compute_type="int8",
        cpu_threads=int(os.environ.get("WHISPER_THREADS", DEFAULT_THREADS)),
        num_workers=1,
    )
    try:
        # vad_filter skips non-speech. Without it, music-only reels produce
        # confident nonsense (including invented quantities). See scripts/spike.py.
        segments, _info = whisper.transcribe(str(media), beam_size=5, vad_filter=True)
        # Segments are lazy; iterating runs the model.
        return [Segment(start=s.start, end=s.end, text=s.text.strip()) for s in segments if s.text.strip()]
    finally:
        del whisper
