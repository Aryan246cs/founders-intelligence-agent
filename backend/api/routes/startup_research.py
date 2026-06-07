"""
Startup Research endpoints.

POST /api/startup-research/run       — launch full autonomous research pipeline
GET  /api/startup-research/          — list research history
GET  /api/startup-research/{id}      — fetch a single report
POST /api/startup-research/{id}/slack — send a saved report to Slack
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.startup_research_agent import StartupResearchAgent, _send_research_to_slack
from db.queries import StartupResearchQueries, WorkflowExecutionQueries
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class StartupResearchRequest(BaseModel):
    startup_idea: str
    startup_name: Optional[str] = None
    send_to_slack: bool = False


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/run")
async def run_startup_research(req: StartupResearchRequest):
    """Launch the full autonomous startup research pipeline."""
    if not req.startup_idea or len(req.startup_idea.strip()) < 5:
        raise HTTPException(status_code=422, detail="startup_idea is required")

    started_at = datetime.now(timezone.utc)

    # Create a workflow execution record so the run appears in Executions page
    execution = WorkflowExecutionQueries.create(
        trigger_source="manual",
        request_summary=f"Startup Research: {req.startup_idea[:80]}",
    )
    execution_id = execution["id"]

    try:
        agent = StartupResearchAgent()
        result = await agent.run(
            {
                "startup_idea": req.startup_idea.strip(),
                "startup_name": (req.startup_name or "").strip(),
                "send_to_slack": req.send_to_slack,
            }
        )

        # Mark workflow execution complete
        WorkflowExecutionQueries.complete(
            execution_id,
            steps_total=10,
            steps_completed=10,
            plan_summary=f"Startup Research: {req.startup_idea[:60]}",
            briefing_id=None,
            briefing_available=False,
            slack_delivered=result.get("sent_to_slack", False),
            comparison_ran=False,
            has_competitor_changes=False,
            started_at=started_at,
        )

        return {
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

    except Exception as e:
        WorkflowExecutionQueries.fail(execution_id, str(e), started_at)
        logger.error("Startup research failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


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
