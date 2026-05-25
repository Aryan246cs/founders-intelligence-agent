from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from agents.research_agent import ResearchAgent
from agents.competitor_monitor import CompetitorMonitorAgent
from db.queries import ResearchQueries

router = APIRouter()


class ResearchRequest(BaseModel):
    query: str
    max_results: int = 10


class CompetitorRequest(BaseModel):
    competitor_name: str
    website: str


@router.post("/search")
async def run_research(req: ResearchRequest, background_tasks: BackgroundTasks):
    """Trigger a research agent run for a given query."""
    agent = ResearchAgent()
    background_tasks.add_task(
        agent.run, {"query": req.query, "max_results": req.max_results}
    )
    return {"status": "queued", "query": req.query}


@router.post("/competitor")
async def monitor_competitor(req: CompetitorRequest, background_tasks: BackgroundTasks):
    """Trigger competitor monitoring for a specific company."""
    agent = CompetitorMonitorAgent()
    background_tasks.add_task(
        agent.run, {"competitor_name": req.competitor_name, "website": req.website}
    )
    return {"status": "queued", "competitor": req.competitor_name}


@router.get("/findings")
async def list_findings(limit: int = 20):
    """List recent research findings."""
    findings = ResearchQueries.list_recent(limit=limit)
    return {"findings": findings, "total": len(findings)}
