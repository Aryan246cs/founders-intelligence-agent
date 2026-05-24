from fastapi import APIRouter, BackgroundTasks
from models.briefing import BriefingRequest
from agents.briefing_agent import BriefingAgent
from db.queries import BriefingQueries

router = APIRouter()


@router.post("/generate")
async def generate_briefing(req: BriefingRequest, background_tasks: BackgroundTasks):
    """Generate a new founder briefing."""
    agent = BriefingAgent()
    background_tasks.add_task(
        agent.run,
        {
            "time_range_days": req.time_range_days,
            "send_to_slack": True,
        },
    )
    return {"status": "queued"}


@router.get("/")
async def list_briefings(limit: int = 10):
    """List recent briefings."""
    briefings = BriefingQueries.list_recent(limit=limit)
    return {"briefings": briefings, "total": len(briefings)}
