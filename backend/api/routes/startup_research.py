"""
Startup Research endpoints.

POST /api/startup-research/run          — launch the autonomous research pipeline
GET  /api/startup-research/jobs/{id}    — live step-by-step progress of a run
GET  /api/startup-research/             — list research history
GET  /api/startup-research/{id}         — fetch a single report
POST /api/startup-research/{id}/slack   — send a saved report to Slack

The pipeline takes 1-5 minutes (Apify crawls + ~10 LLM calls), so `/run`
launches it as a background task and returns a job_id immediately. Callers that
genuinely want to block — n8n, cron, scripts — pass `?wait=true` and get the
finished result in the response instead.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.startup_research_agent import (
    RESEARCH_STEPS,
    StartupResearchAgent,
    _send_research_to_slack,
)
from db.client import describe_db_error
from db.queries import StartupResearchQueries, WorkflowExecutionQueries
from services.job_tracker import ProgressReporter, registry
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# asyncio only holds a weak reference to tasks; without this set a background
# run can be garbage-collected mid-flight.
_background_tasks: Set[asyncio.Task] = set()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class StartupResearchRequest(BaseModel):
    startup_idea: str = Field(min_length=5)
    startup_name: Optional[str] = None
    send_to_slack: bool = False


# ---------------------------------------------------------------------------
# Pipeline runner — shared by the background and blocking paths
# ---------------------------------------------------------------------------


async def _run_pipeline(
    req: StartupResearchRequest,
    execution_id: str,
    started_at: datetime,
    reporter: ProgressReporter,
) -> Dict[str, Any]:
    """Run the agent and keep both the job and the DB execution record in sync."""
    reporter.begin()
    try:
        agent = StartupResearchAgent(progress=reporter)
        result = await agent.run(
            {
                "startup_idea": req.startup_idea.strip(),
                "startup_name": (req.startup_name or "").strip(),
                "send_to_slack": req.send_to_slack,
            }
        )

        WorkflowExecutionQueries.complete(
            execution_id,
            steps_total=len(RESEARCH_STEPS),
            steps_completed=len(RESEARCH_STEPS),
            plan_summary=f"Startup Research: {req.startup_idea[:60]}",
            briefing_id=None,
            briefing_available=False,
            slack_delivered=result.get("sent_to_slack", False),
            comparison_ran=False,
            has_competitor_changes=False,
            started_at=started_at,
        )

        payload = {
            "execution_id": execution_id,
            "report_id": result["report_id"],
            "status": "completed",
            "startup_idea": result["startup_idea"],
            "industry": result["industry"],
            "competitors_found": result["competitors_found"],
            "sources_analyzed": result["sources_analyzed"],
            "research_score": result["research_score"],
            "sent_to_slack": result["sent_to_slack"],
        }
        reporter.finish(payload)
        return payload

    except Exception as exc:
        error = str(exc)
        logger.error("Startup research failed", execution_id=execution_id, error=error)
        reporter.fail(error)
        # A failed DB write here must not mask the original failure.
        try:
            WorkflowExecutionQueries.fail(execution_id, error, started_at)
        except Exception as db_exc:
            logger.error("Could not record failure", error=str(db_exc))
        raise


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/run", status_code=202)
async def run_startup_research(req: StartupResearchRequest, wait: bool = False):
    """
    Launch the autonomous startup research pipeline.

    Default (`wait=false`): returns 202 with a `job_id` to poll.
    `wait=true`: blocks until the pipeline finishes and returns the result.
    """
    started_at = datetime.now(timezone.utc)

    # The execution record is created up front so the run appears on the
    # Executions page as 'running' for its entire duration, not only at the end.
    # It is also the first thing to touch the database, so it is where an
    # unreachable Supabase surfaces — as a clear 503, not an opaque 500.
    try:
        execution = WorkflowExecutionQueries.create(
            trigger_source="manual",
            request_summary=f"Startup Research: {req.startup_idea[:80]}",
        )
    except Exception as exc:
        logger.error("Could not create execution record", error=str(exc))
        raise HTTPException(status_code=503, detail=describe_db_error(exc))
    execution_id = execution["id"]

    job = registry.create(
        kind="startup_research",
        steps=RESEARCH_STEPS,
        summary=req.startup_idea[:120],
        execution_id=execution_id,
    )
    reporter = ProgressReporter(job)

    if wait:
        try:
            return await _run_pipeline(req, execution_id, started_at, reporter)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    async def _background() -> None:
        try:
            await _run_pipeline(req, execution_id, started_at, reporter)
        except Exception:
            # Already recorded on the job and the execution row; the poller
            # surfaces it. Swallowed here so the task doesn't log a traceback.
            pass

    task = asyncio.create_task(_background())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return {
        "job_id": job.id,
        "execution_id": execution_id,
        "status": "running",
        "steps_total": len(RESEARCH_STEPS),
        "poll_url": f"/api/startup-research/jobs/{job.id}",
    }


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Live progress for a research run — which step is executing right now."""
    job = registry.get(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"No job {job_id}. Jobs are held in memory and are lost on restart.",
        )
    return job.to_dict()


@router.get("/")
async def list_research(limit: int = 20):
    """List recent startup research reports."""
    reports = StartupResearchQueries.list_recent(limit=limit)
    return {"reports": reports, "total": len(reports)}


@router.get("/{report_id}")
async def get_report(report_id: str):
    """Fetch a full research report by ID."""
    report = StartupResearchQueries.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/{report_id}/slack")
async def send_to_slack(report_id: str):
    """Send a saved research report to Slack."""
    report = StartupResearchQueries.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    sent = await _send_research_to_slack(report["startup_idea"], report, report_id)

    if sent:
        StartupResearchQueries.mark_sent(report_id)

    return {"sent": sent, "report_id": report_id}
