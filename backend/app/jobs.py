"""In-memory job and recipe store.

Real mode: each job runs the extraction pipeline in a background thread and
reports the stage it's on. Stub mode (no API key, or PIPELINE_MODE=stub):
progress is simulated by advancing one stage every `STUB_STAGE_SECONDS`
(default 1.5s), then the sample fixture is returned.

Everything lives in memory and disappears on restart, until the SQLite cache
lands (docs/decisions.md #9).
"""

import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field

from app import usage
from app.models import Job, JobStatus, Recipe, Stage
from app.pipeline.extract import (
    LINK_STAGES,
    TEXT_STAGES,
    ExtractionError,
    pipeline_mode,
    real_extraction,
    stub_extraction,
)
from app.pipeline.result import Extraction

log = logging.getLogger(__name__)

UNEXPECTED_ERROR = "Something went wrong while reading this recipe. Try again, or paste the ingredient list below."


def _stage_seconds() -> float:
    return float(os.environ.get("STUB_STAGE_SECONDS", "1.5"))


@dataclass
class _JobRecord:
    job_id: str
    mode: str
    stages: list[Stage]
    started_at: float
    url: str | None
    text: str | None
    stage: Stage | None = None
    completed: list[Stage] = field(default_factory=list)
    recipe_id: str | None = None
    error: str | None = None
    finished: bool = False


class Store:
    def __init__(self) -> None:
        self._jobs: dict[str, _JobRecord] = {}
        self._results: dict[str, Extraction] = {}
        self._lock = threading.Lock()

    def create_job(self, *, url: str | None, text: str | None) -> Job:
        record = _JobRecord(
            job_id=f"job_{uuid.uuid4().hex[:12]}",
            mode=pipeline_mode(),
            stages=list(LINK_STAGES if url else TEXT_STAGES),
            started_at=time.monotonic(),
            url=url,
            text=text,
        )
        record.stage = record.stages[0]
        with self._lock:
            self._jobs[record.job_id] = record
        if record.mode == "real":
            threading.Thread(target=self._run_real, args=(record,), daemon=True, name=record.job_id).start()
        return self.get_job(record.job_id)

    def get_job(self, job_id: str) -> Job | None:
        record = self._jobs.get(job_id)
        if record is None:
            return None
        with self._lock:
            if record.mode == "stub":
                self._advance_stub(record)
            if record.error:
                return Job(
                    job_id=record.job_id,
                    stages=list(record.stages),
                    status=JobStatus.failed,
                    stage=record.stage,
                    completed_stages=list(record.completed),
                    error=record.error,
                )
            if record.finished:
                return Job(
                    job_id=record.job_id,
                    stages=list(record.stages),
                    status=JobStatus.done,
                    stage=None,
                    completed_stages=list(record.stages),
                    recipe_id=record.recipe_id,
                )
            return Job(
                job_id=record.job_id,
                stages=list(record.stages),
                status=JobStatus.running,
                stage=record.stage,
                completed_stages=list(record.completed),
            )

    def get_recipe(self, recipe_id: str) -> Recipe | None:
        result = self._results.get(recipe_id)
        return result.recipe if result else None

    def get_extraction(self, recipe_id: str) -> Extraction | None:
        return self._results.get(recipe_id)

    # --- Real ------------------------------------------------------------------

    def _run_real(self, record: _JobRecord) -> None:
        recipe_id = f"rcp_{uuid.uuid4().hex[:12]}"

        def on_stage(stage: Stage) -> None:
            with self._lock:
                if record.stage is not None and record.stage != stage and record.stage not in record.completed:
                    record.completed.append(record.stage)
                record.stage = stage

        def skip_stage(stage: Stage) -> None:
            with self._lock:
                if stage in record.stages:
                    record.stages.remove(stage)

        job_usage = usage.JobUsage(job_id=record.job_id, source=record.url or "pasted text")
        usage.current.set(job_usage)  # this thread's context: every Claude call in the job reports here

        def on_cache_hit() -> None:
            job_usage.cache_hit = True

        try:
            result = real_extraction(
                recipe_id=recipe_id,
                url=record.url,
                text=record.text,
                on_stage=on_stage,
                skip_stage=skip_stage,
                on_cache_hit=on_cache_hit,
            )
        except ExtractionError as e:
            with self._lock:
                record.error = str(e)
        except Exception:
            log.exception("Extraction failed for job %s", record.job_id)
            with self._lock:
                record.error = UNEXPECTED_ERROR
        else:
            with self._lock:
                self._results[recipe_id] = result
                record.recipe_id = recipe_id
                record.finished = True
        finally:
            usage.finish(job_usage)  # failed jobs still cost tokens, so log them too

    # --- Stub ------------------------------------------------------------------

    def _advance_stub(self, record: _JobRecord) -> None:
        if record.finished or record.error:
            return
        stage_seconds = _stage_seconds()
        elapsed = time.monotonic() - record.started_at
        index = int(elapsed // stage_seconds) if stage_seconds > 0 else len(record.stages)
        failing = bool(record.url and "stub-fail" in record.url)

        # A failing link fails during the first stage, the way a blocked download would.
        if index >= len(record.stages) or (failing and index >= 1):
            recipe_id = f"rcp_{uuid.uuid4().hex[:12]}"
            try:
                result = stub_extraction(recipe_id=recipe_id, url=record.url, text=record.text)
            except ExtractionError as e:
                record.error = str(e)
                record.stage = record.stages[0]
                record.completed = []
            else:
                self._results[recipe_id] = result
                record.recipe_id = recipe_id
                record.finished = True
            return
        record.stage = record.stages[index]
        record.completed = record.stages[:index]


store = Store()
