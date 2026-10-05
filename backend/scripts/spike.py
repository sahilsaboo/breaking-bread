"""Spike: can the free host download a TikTok and transcribe it within 512 MB?

Answers decision #13 (which faster-whisper model fits) and whether TikTok
blocks downloads from the host's IP. Throwaway code: delete it, and
app/spike_routes.py, once the decision is recorded.

Run locally:
    .venv/bin/python scripts/spike.py "https://www.tiktok.com/@user/video/123"
    .venv/bin/python scripts/spike.py URL --models tiny,base --json out.json

On Render it runs through POST /api/spike (see app/spike_routes.py).

Each model transcribes in its own child process so its peak memory is
measured alone, and so an out-of-memory kill takes down only that child.
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DEFAULT_MODELS = ["tiny", "base"]


def peak_mb(ru_maxrss: int) -> float:
    # ru_maxrss is kilobytes on Linux but bytes on macOS.
    divisor = 1024 * 1024 if sys.platform == "darwin" else 1024
    return round(ru_maxrss / divisor, 1)


def memory_limit_mb() -> float | None:
    """The container's memory cap (cgroup v2, then v1), if there is one."""
    for path in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        try:
            raw = Path(path).read_text().strip()
        except OSError:
            continue
        if raw.isdigit() and int(raw) < 1 << 60:
            return round(int(raw) / 1024 / 1024, 1)
    return None


def environment() -> dict:
    try:
        import curl_cffi  # noqa: F401

        impersonation = True
    except ImportError:
        impersonation = False
    import yt_dlp

    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "memory_limit_mb": memory_limit_mb(),
        "ffmpeg": shutil.which("ffmpeg"),
        "yt_dlp": yt_dlp.version.__version__,
        "curl_cffi_installed": impersonation,
    }


def download(url: str, workdir: Path) -> dict:
    import yt_dlp

    opts = {
        # TikTok serves a single mp4 with audio, so no ffmpeg merge is needed.
        "format": "best[ext=mp4]/best",
        "outtmpl": str(workdir / "video.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": False,
    }
    start = time.monotonic()
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = Path(ydl.prepare_filename(info))
    except Exception as e:  # yt-dlp raises many error types; report them all
        return {"ok": False, "seconds": round(time.monotonic() - start, 1), "error": str(e)[:500]}

    description = info.get("description") or ""
    return {
        "ok": True,
        "seconds": round(time.monotonic() - start, 1),
        "path": str(path),
        "file_mb": round(path.stat().st_size / 1024 / 1024, 2),
        "duration_s": info.get("duration"),
        "title": info.get("title"),
        "uploader": info.get("uploader"),
        "description_chars": len(description),
        "description_preview": description[:300],
    }


def transcribe_child(model: str, audio: str) -> None:
    """Runs in a child process; prints one JSON line with the result."""
    from faster_whisper import WhisperModel

    start = time.monotonic()
    whisper = WhisperModel(model, device="cpu", compute_type="int8")
    loaded = time.monotonic()
    segments, info = whisper.transcribe(audio, beam_size=5)
    text = " ".join(s.text.strip() for s in segments)  # segments are lazy; this runs the model
    done = time.monotonic()
    print(
        json.dumps(
            {
                "load_s": round(loaded - start, 1),
                "transcribe_s": round(done - loaded, 1),
                "language": info.language,
                "audio_duration_s": round(info.duration, 1),
                "text_preview": text[:300],
            }
        )
    )


def transcribe(model: str, audio: str) -> dict:
    # Temp files, not pipes: model-download progress on stderr could fill a
    # pipe and hang the child before it exits.
    with tempfile.TemporaryFile("w+") as out, tempfile.TemporaryFile("w+") as err:
        proc = subprocess.Popen([sys.executable, __file__, "--transcribe-child", model, audio], stdout=out, stderr=err)
        _, status, usage = os.wait4(proc.pid, 0)
        out.seek(0)
        err.seek(0)
        stdout, stderr = out.read(), err.read()
    result: dict = {"model": model, "peak_mb": peak_mb(usage.ru_maxrss)}

    if os.WIFSIGNALED(status):
        sig = os.WTERMSIG(status)
        # SIGKILL here almost always means the out-of-memory killer.
        result |= {"ok": False, "error": f"killed by signal {sig}" + (" (likely out of memory)" if sig == 9 else "")}
    elif os.WEXITSTATUS(status) != 0:
        result |= {"ok": False, "error": stderr.strip()[-500:]}
    else:
        result |= {"ok": True, **json.loads(stdout.strip().splitlines()[-1])}
    return result


def run(url: str, models: list[str]) -> dict:
    report: dict = {"url": url, "environment": environment()}
    with tempfile.TemporaryDirectory(prefix="spike-") as tmp:
        report["download"] = download(url, Path(tmp))
        if report["download"]["ok"]:
            audio = report["download"].pop("path")
            report["transcription"] = [transcribe(m, audio) for m in models]
        # The temp directory (and the video) is deleted here, per the spec.
    return report


def summarize(report: dict) -> str:
    env, dl = report["environment"], report["download"]
    lines = [
        f"Python {env['python']} | CPUs {env['cpu_count']} | memory limit "
        f"{env['memory_limit_mb'] or 'none found'} MB | ffmpeg {'yes' if env['ffmpeg'] else 'no'} | "
        f"yt-dlp {env['yt_dlp']} | curl_cffi {'yes' if env['curl_cffi_installed'] else 'NO'}",
        "",
    ]
    if dl["ok"]:
        lines.append(
            f"Download OK in {dl['seconds']}s: {dl['file_mb']} MB, {dl['duration_s']}s video, "
            f"caption {dl['description_chars']} chars"
        )
    else:
        lines.append(f"Download FAILED after {dl['seconds']}s: {dl['error']}")
    for t in report.get("transcription", []):
        if t["ok"]:
            lines.append(
                f"  {t['model']:<6} peak {t['peak_mb']} MB | load {t['load_s']}s | "
                f"transcribe {t['transcribe_s']}s for {t['audio_duration_s']}s of audio"
            )
        else:
            lines.append(f"  {t['model']:<6} FAILED (peak {t['peak_mb']} MB): {t['error']}")
    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) == 4 and sys.argv[1] == "--transcribe-child":
        transcribe_child(sys.argv[2], sys.argv[3])
        return

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url", help="TikTok video URL")
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS), help="comma-separated, e.g. tiny,base")
    parser.add_argument("--json", type=Path, help="also write the full report here")
    args = parser.parse_args()

    report = run(args.url, [m.strip() for m in args.models.split(",") if m.strip()])
    if args.json:
        args.json.write_text(json.dumps(report, indent=2))
    print(summarize(report))


if __name__ == "__main__":
    main()
