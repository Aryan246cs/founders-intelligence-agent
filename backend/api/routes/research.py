from fastapi import APIRouter, BackgroundTasks
from models.research import ResearchRequest
from agents.research_agent import ResearchAgent
from agents.competitor_monitor import CompetitorMonitorAgent
from db.queries import ResearchQueries

router = APIRouter()


@router.post("/search")
async def run_research(req: ResearchRequest, background_tasks: BackgroundTasks):
    """Trigger a research agent run for a given query."""
    agent = ResearchAgent()
    background_tasks.add_task(
        agent.run, {"query": req.query, "max_results": req.max_results}
    )
    return {"status": "queued", "query": req.query}


@router.post("/competitor")
async def monitor_competitor(
    competitor_name: str, website: str, background_tasks: BackgroundTasks
):
    """Trigger competitor monitoring for a specific company."""
    agent = CompetitorMonitorAgent()
    background_tasks.add_task(
        agent.run, {"competitor_name": competitor_name, "website": website}
    )
    return {"status": "queued", "competitor": competitor_name}


@router.get("/findings")
async def list_findings(limit: int = 20):
    """List recent research findings."""
    findings = ResearchQueries.list_recent(limit=limit)
    return {"findings": findings, "total": len(findings)}
