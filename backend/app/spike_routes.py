"""Temporary endpoints to run scripts/spike.py on the deployed host.

Render's free tier has no shell, so this is how the spike runs there. The
routes exist only when the SPIKE_TOKEN environment variable is set, and every
call must send that token in the X-Spike-Token header. Delete this module,
and scripts/spike.py, once decision #13 is recorded.
"""

import hmac
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "spike.py"
WORKDIR = Path(tempfile.gettempdir()) / "breaking-bread-spike"

router = APIRouter(prefix="/api/spike")
_proc: subprocess.Popen | None = None


class SpikeRequest(BaseModel):
    url: str
    models: str = "tiny,base"


def _check_token(token: str | None) -> None:
    expected = os.environ.get("SPIKE_TOKEN", "")
    if not expected or not token or not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=403, detail="Missing or wrong X-Spike-Token.")


@router.post("", status_code=202)
def start_spike(body: SpikeRequest, x_spike_token: str | None = Header(default=None)) -> dict:
    global _proc
    _check_token(x_spike_token)
    if _proc is not None and _proc.poll() is None:
        raise HTTPException(status_code=409, detail="A spike is already running.")

    WORKDIR.mkdir(exist_ok=True)
    (WORKDIR / "report.json").unlink(missing_ok=True)
    _proc = subprocess.Popen(
        [sys.executable, str(SCRIPT), body.url, "--models", body.models, "--json", str(WORKDIR / "report.json")],
        stdout=(WORKDIR / "output.txt").open("w"),
        stderr=subprocess.STDOUT,
    )
    return {"status": "running"}


@router.get("")
def spike_status(x_spike_token: str | None = Header(default=None)) -> dict:
    _check_token(x_spike_token)
    if _proc is None:
        return {"status": "idle"}
    code = _proc.poll()
    output = (WORKDIR / "output.txt").read_text()[-4000:] if (WORKDIR / "output.txt").exists() else ""
    if code is None:
        return {"status": "running", "output": output}
    report_path = WORKDIR / "report.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else None
    return {"status": "done" if code == 0 else "failed", "exit_code": code, "output": output, "report": report}
