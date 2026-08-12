"""
In-process job tracker — real, observable progress for long-running agent runs.

Why this exists
---------------
The research and briefing pipelines take 1-5 minutes (Apify crawls + several LLM
calls). Running them inside the HTTP request means the client holds a connection
open for minutes and gets zero feedback until the very end — so the UI had to
*guess* progress with timers.

This module gives every long run a Job: an ordered list of steps that agents
mark running / done / failed as they actually happen. The API launches the run
as a background asyncio task and returns a job_id immediately; the UI polls
`GET .../jobs/{job_id}` and renders real step state with real timings.

Scope note (worth saying out loud in a design review): this registry lives in
the API process memory, so it is correct for a single-process deployment and
loses in-flight jobs on restart. Terminal outcomes are always mirrored into the
`workflow_executions` table, which is the durable record. Moving to multiple
workers means swapping this one module for Redis or a real queue (Celery/RQ) —
the agent-facing API (`reporter.start/done/fail`) would not change.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

from utils.logger import get_logger

logger = get_logger(__name__)

StepStatus = Literal["pending", "running", "done", "failed", "skipped"]
JobStatus = Literal["queued", "running", "completed", "failed"]

# Jobs are evicted once this many newer jobs exist. Keeps memory bounded without
# a background sweeper — the UI only ever polls recent jobs.
MAX_JOBS = 200


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


@dataclass
class JobStep:
    key: str
    label: str
    status: StepStatus = "pending"
    detail: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def duration_ms(self) -> Optional[int]:
        if not self.started_at:
            return None
        end = self.completed_at or _now()
        return int((end - self.started_at).total_seconds() * 1000)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "status": self.status,
            "detail": self.detail,
            "started_at": _iso(self.started_at),
            "completed_at": _iso(self.completed_at),
            "duration_ms": self.duration_ms,
        }


@dataclass
class Job:
    id: str
    kind: str
    summary: str
    steps: List[JobStep]
    status: JobStatus = "queued"
    created_at: datetime = field(default_factory=_now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    execution_id: Optional[str] = None

    @property
    def duration_ms(self) -> int:
        start = self.started_at or self.created_at
        end = self.completed_at or _now()
        return int((end - start).total_seconds() * 1000)

    def to_dict(self) -> Dict[str, Any]:
        steps = [s.to_dict() for s in self.steps]
        done = sum(1 for s in self.steps if s.status in ("done", "skipped"))
        current = next((s for s in self.steps if s.status == "running"), None)
        return {
            "job_id": self.id,
            "kind": self.kind,
            "summary": self.summary,
            "status": self.status,
            "execution_id": self.execution_id,
            "steps": steps,
            "steps_total": len(steps),
            "steps_completed": done,
            "current_step": current.key if current else None,
            "current_step_label": current.label if current else None,
            "progress_pct": int(done / len(steps) * 100) if steps else 0,
            "created_at": _iso(self.created_at),
            "started_at": _iso(self.started_at),
            "completed_at": _iso(self.completed_at),
            "duration_ms": self.duration_ms,
            "error": self.error,
            "result": self.result,
        }


class JobRegistry:
    """Thread-safe store of recent jobs, keyed by job id, newest-last."""

    def __init__(self, max_jobs: int = MAX_JOBS) -> None:
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()
        self._max_jobs = max_jobs

    def create(
        self,
        kind: str,
        steps: Sequence[Tuple[str, str]],
        summary: str = "",
        execution_id: Optional[str] = None,
    ) -> Job:
        job = Job(
            id=str(uuid.uuid4()),
            kind=kind,
            summary=summary,
            steps=[JobStep(key=k, label=lbl) for k, lbl in steps],
            execution_id=execution_id,
        )
        with self._lock:
            self._jobs[job.id] = job
            self._evict_locked()
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_recent(self, limit: int = 20) -> List[Job]:
        with self._lock:
            jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    def _evict_locked(self) -> None:
        if len(self._jobs) <= self._max_jobs:
            return
        ordered = sorted(self._jobs.values(), key=lambda j: j.created_at)
        for job in ordered[: len(self._jobs) - self._max_jobs]:
            self._jobs.pop(job.id, None)


registry = JobRegistry()


class ProgressReporter:
    """
    The handle an agent uses to report progress. Every method is a no-op when
    `job` is None, so agents stay callable outside of a tracked job (tests,
    n8n's synchronous path, direct scripts) with no branching at the call site.
    """

    def __init__(self, job: Optional[Job] = None) -> None:
        self.job = job

    # -- job lifecycle ----------------------------------------------------

    def begin(self) -> None:
        if not self.job:
            return
        self.job.status = "running"
        self.job.started_at = _now()

    def finish(self, result: Optional[Dict[str, Any]] = None) -> None:
        if not self.job:
            return
        # Any step never reached is reported as skipped rather than left
        # pending, so a finished job never renders half-lit in the UI.
        for step in self.job.steps:
            if step.status == "pending":
                step.status = "skipped"
            elif step.status == "running":
                step.status = "done"
                step.completed_at = _now()
        self.job.status = "completed"
        self.job.result = result
        self.job.completed_at = _now()

    def fail(self, error: str) -> None:
        if not self.job:
            return
        for step in self.job.steps:
            if step.status == "running":
                step.status = "failed"
                step.completed_at = _now()
        self.job.status = "failed"
        self.job.error = error
        self.job.completed_at = _now()

    # -- step lifecycle ---------------------------------------------------

    def _find(self, key: str) -> Optional[JobStep]:
        if not self.job:
            return None
        return next((s for s in self.job.steps if s.key == key), None)

    def start(self, key: str, detail: str = "") -> None:
        step = self._find(key)
        if not step:
            return
        # Steps run in order; anything still open before this one is finished so
        # a skipped optional step can never strand the timeline.
        for earlier in self.job.steps if self.job else []:
            if earlier.key == key:
                break
            if earlier.status == "running":
                earlier.status = "done"
                earlier.completed_at = _now()
        step.status = "running"
        step.detail = detail
        step.started_at = _now()

    def detail(self, key: str, detail: str) -> None:
        step = self._find(key)
        if step:
            step.detail = detail

    def done(self, key: str, detail: str = "") -> None:
        step = self._find(key)
        if not step:
            return
        step.status = "done"
        step.completed_at = _now()
        if detail:
            step.detail = detail

    def skip(self, key: str, detail: str = "") -> None:
        step = self._find(key)
        if not step:
            return
        step.status = "skipped"
        step.completed_at = _now()
        if detail:
            step.detail = detail

    def fail_step(self, key: str, detail: str = "") -> None:
        step = self._find(key)
        if not step:
            return
        step.status = "failed"
        step.completed_at = _now()
        if detail:
            step.detail = detail

    def extend(self, steps: Sequence[Tuple[str, str]]) -> None:
        """Append steps discovered at runtime (e.g. a planner-generated plan)."""
        if not self.job:
            return
        existing = {s.key for s in self.job.steps}
        for key, label in steps:
            if key not in existing:
                self.job.steps.append(JobStep(key=key, label=label))
                existing.add(key)


# A reporter bound to no job — agents default to this.
NULL_REPORTER = ProgressReporter(None)
