"""In-memory job and recipe store.

STUB: extraction is simulated by advancing one stage every
`STUB_STAGE_SECONDS` (default 1.5s) so the frontend's progress screen has
something to show. The real version runs the pipeline in a background task
and caches results in SQLite.
"""

import os
import time
import uuid
from dataclasses import dataclass, field

from app.models import Job, JobStatus, Recipe, Stage
from app.pipeline.extract import LINK_STAGES, TEXT_STAGES, ExtractionError, extract_recipe


def _stage_seconds() -> float:
    return float(os.environ.get("STUB_STAGE_SECONDS", "1.5"))


@dataclass
class _JobRecord:
    job_id: str
    stages: list[Stage]
    started_at: float
    url: str | None
    text: str | None
    recipe_id: str | None = None
    error: str | None = None
    finished: bool = field(default=False)


class Store:
    def __init__(self) -> None:
        self._jobs: dict[str, _JobRecord] = {}
        self._recipes: dict[str, Recipe] = {}

    def create_job(self, *, url: str | None, text: str | None) -> Job:
        record = _JobRecord(
            job_id=f"job_{uuid.uuid4().hex[:12]}",
            stages=LINK_STAGES if url else TEXT_STAGES,
            started_at=time.monotonic(),
            url=url,
            text=text,
        )
        self._jobs[record.job_id] = record
        return self.get_job(record.job_id)

    def get_job(self, job_id: str) -> Job | None:
        record = self._jobs.get(job_id)
        if record is None:
            return None

        stage_seconds = _stage_seconds()
        elapsed = time.monotonic() - record.started_at
        index = int(elapsed // stage_seconds) if stage_seconds > 0 else len(record.stages)

        if not record.finished and index >= len(record.stages):
            self._finish(record)
        elif not record.finished and index >= 1 and record.url and "stub-fail" in record.url:
            # Fail during the first stage, the way a blocked download would.
            self._finish(record)

        if record.error:
            return Job(
                job_id=record.job_id,
                stages=list(record.stages),
                status=JobStatus.failed,
                stage=record.stages[0],
                completed_stages=[],
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
            stage=record.stages[index],
            completed_stages=record.stages[:index],
        )

    def _finish(self, record: _JobRecord) -> None:
        try:
            recipe = extract_recipe(url=record.url, text=record.text)
        except ExtractionError as e:
            record.error = str(e)
        else:
            self._recipes[recipe.id] = recipe
            record.recipe_id = recipe.id
        record.finished = True

    def get_recipe(self, recipe_id: str) -> Recipe | None:
        return self._recipes.get(recipe_id)


store = Store()
