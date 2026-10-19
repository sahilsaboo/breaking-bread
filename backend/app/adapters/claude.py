"""Claude API adapter: one structured call that returns a validated Pydantic model.

Every LLM step in the pipeline goes through `ask`, so tests can replace this
one function instead of mocking HTTP.
"""

import logging
import os
from typing import TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

from app import usage

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

DEFAULT_MODEL = "claude-opus-5-5"


class ClaudeError(RuntimeError):
    """Claude couldn't produce a usable answer (refusal, bad output, API error)."""


_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        # Reads ANTHROPIC_API_KEY (or an `ant auth login` profile) from the environment.
        _client = anthropic.Anthropic()
    return _client


def is_configured() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def ask(*, system: str, prompt: str, output: type[T], effort: str = "medium", max_tokens: int = 16000) -> T:
    """Send one request and return Claude's answer parsed into `output`.

    Retries once if the answer doesn't validate against the schema. Uses the
    server-side refusal fallback so a safety decline is re-run on Anthropic's
    recommended fallback model instead of failing the job.
    """
    model = os.environ.get("CLAUDE_MODEL", DEFAULT_MODEL)
    last_error: Exception | None = None

    for attempt in range(2):
        try:
            response = _get_client().beta.messages.parse(
                model=model,
                max_tokens=max_tokens,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                output_config={"effort": effort},
                system=system,
                messages=[{"role": "user", "content": prompt}],
                output_format=output,
            )
        except ValidationError as e:
            last_error = e
            log.warning("Claude output failed validation (attempt %d): %s", attempt + 1, e)
            continue
        except anthropic.RateLimitError as e:
            raise ClaudeError("We're getting a lot of requests right now. Try again in a minute.") from e
        except anthropic.APIStatusError as e:
            log.error("Claude API error %s (request %s): %s", e.status_code, e.request_id, e.message)
            raise ClaudeError("Our recipe helper isn't responding right now. Try again soon.") from e
        except anthropic.APIConnectionError as e:
            raise ClaudeError("We couldn't reach our recipe helper. Check your connection and try again.") from e

        # Every attempt is billed, including ones we retry, so record them all.
        usage.record(output.__name__, response.model, response.usage)

        if response.stop_reason == "refusal":
            log.warning("Claude declined (request %s): %s", response._request_id, response.stop_details)
            raise ClaudeError("We couldn't turn this into a recipe. Try pasting the ingredient list instead.")
        if response.stop_reason == "max_tokens":
            last_error = ClaudeError("Answer was cut off at max_tokens")
            log.warning("Claude hit max_tokens (request %s)", response._request_id)
            continue
        if response.parsed_output is not None:
            return response.parsed_output
        last_error = ClaudeError("No parsed output")

    raise ClaudeError("We couldn't read this recipe. Try pasting the ingredient list instead.") from last_error
