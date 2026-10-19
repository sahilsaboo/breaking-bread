"""Token usage per extraction job, so we can see what each recipe costs.

Every Claude call records its usage into the current job's tracker (a context
variable set by the job runner). When the job ends, one summary line is
logged and appended to backend/.cache/usage.jsonl for the team to compare.

Dollar figures are estimates at Anthropic's list prices
(https://platform.claude.com/docs/en/about-claude/pricing, checked 2026-10-19).
The MIT gateway may bill differently; its own dashboard is the real number.
"""

import contextvars
import json
import logging
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

# USD per million tokens: input, 5-minute cache write, cache read, output.
# Thinking tokens are billed as output.
LIST_PRICES = {
    "claude-opus-5-5": (4.00, 5.00, 0.20, 20.00),
    "claude-sonnet-5-5": (2.00, 2.50, 0.10, 10.00),
    "claude-haiku-5-5": (0.10, 0.125, 0.01, 0.50),
}


@dataclass
class CallUsage:
    label: str
    model: str
    input_tokens: int
    output_tokens: int  # includes thinking
    thinking_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int

    def list_price_usd(self) -> float | None:
        rates = LIST_PRICES.get(self.model)
        if rates is None:
            return None
        inp, write, read, out = rates
        return (
            self.input_tokens * inp
            + self.cache_write_tokens * write
            + self.cache_read_tokens * read
            + self.output_tokens * out
        ) / 1_000_000


@dataclass
class JobUsage:
    job_id: str
    source: str  # the link, or "pasted text"
    calls: list[CallUsage] = field(default_factory=list)
    cache_hit: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add(self, call: CallUsage) -> None:
        with self._lock:
            self.calls.append(call)

    def summary(self) -> dict:
        prices = [c.list_price_usd() for c in self.calls]
        return {
            "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "job_id": self.job_id,
            "source": self.source,
            "cache_hit": self.cache_hit,
            "claude_calls": len(self.calls),
            "input_tokens": sum(c.input_tokens for c in self.calls),
            "output_tokens": sum(c.output_tokens for c in self.calls),
            "thinking_tokens": sum(c.thinking_tokens for c in self.calls),
            "est_list_price_usd": round(sum(p for p in prices if p is not None), 4) if self.calls else 0.0,
            "calls": [asdict(c) for c in self.calls],
        }


current: contextvars.ContextVar[JobUsage | None] = contextvars.ContextVar("job_usage", default=None)


def record(label: str, model: str, usage) -> None:
    """Record one response's `usage` into the running job, and log it."""
    details = getattr(usage, "output_tokens_details", None)
    call = CallUsage(
        label=label,
        model=model,
        input_tokens=usage.input_tokens or 0,
        output_tokens=usage.output_tokens or 0,
        thinking_tokens=(getattr(details, "thinking_tokens", None) or 0) if details else 0,
        cache_write_tokens=usage.cache_creation_input_tokens or 0,
        cache_read_tokens=usage.cache_read_input_tokens or 0,
    )
    log.info(
        "claude %s: in %d, out %d (thinking %d), cache read %d / write %d",
        label, call.input_tokens, call.output_tokens, call.thinking_tokens, call.cache_read_tokens, call.cache_write_tokens,
    )
    job = current.get()
    if job is not None:
        job.add(call)


def _log_path() -> Path:
    return Path(os.environ.get("USAGE_LOG", Path(__file__).resolve().parent.parent / ".cache" / "usage.jsonl"))


def finish(job: JobUsage) -> None:
    s = job.summary()
    log.info(
        "job %s: %s, %d Claude calls, in %d / out %d tokens (thinking %d), ~$%.3f at list price",
        s["job_id"], "cache hit" if s["cache_hit"] else "processed", s["claude_calls"],
        s["input_tokens"], s["output_tokens"], s["thinking_tokens"], s["est_list_price_usd"],
    )
    try:
        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    except OSError as e:  # logging must never fail a job
        log.warning("Couldn't write usage log: %s", e)
