from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from agents.briefing_agent import BriefingAgent
from db.queries import BriefingQueries

router = APIRouter()


class BriefingRequest(BaseModel):
    time_range_days: int = 7
    send_to_slack: bool = False


@router.post("/generate")
async def generate_briefing(req: BriefingRequest, background_tasks: BackgroundTasks):
    """Queue a briefing generation task."""
    agent = BriefingAgent()
    background_tasks.add_task(
        agent.run,
        {
            "time_range_days": req.time_range_days,
            "send_to_slack": req.send_to_slack,
        },
    )
    return {"status": "queued"}


@router.get("/")
async def list_briefings(limit: int = 10):
    """List recent briefings."""
    briefings = BriefingQueries.list_recent(limit=limit)
    return {"briefings": briefings, "total": len(briefings)}
