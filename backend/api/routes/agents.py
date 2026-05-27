from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List

from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.agent import AgentTaskCreate
from agents.orchestrator import get_agent
from db.queries import AgentTaskQueries
from db.client import get_supabase
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

AGENT_DEFINITIONS = [
    {
        "id": "agent-research",
        "name": "Web Monitoring Agent",
        "type": "research",
        "description": "Continuously monitors competitor websites and news sources via Apify",
        "icon": "Globe",
    },
    {
        "id": "agent-competitor",
        "name": "Competitor Intelligence Agent",
        "type": "competitor_monitor",
        "description": "Scrapes and analyzes competitor positioning, pricing, and product updates",
        "icon": "Crosshair",
    },
    {
        "id": "agent-memory",
        "name": "Memory Comparison Agent",
        "type": "memory",
        "description": "Compares new findings against historical snapshots to detect meaningful signals",
        "icon": "Brain",
    },
    {
        "id": "agent-planner",
        "name": "Strategic Insight Agent",
        "type": "planner",
        "description": "Synthesizes intelligence into actionable founder briefings using Groq LLM",
        "icon": "Lightbulb",
    },
    {
        "id": "agent-briefing",
        "name": "Slack Delivery Agent",
        "type": "briefing",
        "description": "Formats and delivers executive briefings to configured Slack channels",
        "icon": "Send",
    },
]


def _relative_time(iso: str | None) -> str:
    if not iso:
        return "Never"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = int((now - dt).total_seconds())
        if diff < 60:
            return "Just now"
        if diff < 3600:
            return f"{diff // 60} min ago"
        if diff < 86400:
            return f"{diff // 3600}h ago"
        return f"{diff // 86400}d ago"
    except Exception:
        return "Recently"


# NOTE: /status must be declared BEFORE /{task_id} to avoid route conflict
@router.get("/status")
async def get_agents_status():
    """Return live status for all agents derived from agent_tasks."""
    try:
        db = get_supabase()

        agents = []
        for defn in AGENT_DEFINITIONS:
            agent_type = defn["type"]

            latest_res = (
                db.table("agent_tasks")
                .select("*")
                .eq("agent_type", agent_type)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            latest = latest_res.data[0] if latest_res.data else None

            count_res = (
                db.table("agent_tasks")
                .select("id", count="exact")
                .eq("agent_type", agent_type)
                .execute()
            )
            total_count = count_res.count or 0

            fail_res = (
                db.table("agent_tasks")
                .select("id", count="exact")
                .eq("agent_type", agent_type)
                .eq("status", "failed")
                .execute()
            )
            fail_count = fail_res.count or 0

            if latest and latest["status"] == "running":
                status = "running"
            elif latest and latest["status"] == "failed":
                status = "error"
            elif total_count > 0:
                status = "active"
            else:
                status = "idle"

            uptime = "100%"
            if total_count > 0:
                success_rate = ((total_count - fail_count) / total_count) * 100
                uptime = f"{success_rate:.1f}%"

            last_run_iso = None
            if latest:
                last_run_iso = latest.get("completed_at") or latest.get("created_at")

            agents.append(
                {
                    **defn,
                    "status": status,
                    "lastExecution": _relative_time(last_run_iso),
                    "lastExecutionIso": last_run_iso,
                    "uptime": uptime,
                    "executionCount": total_count,
                    "failureCount": fail_count,
                }
            )

        return {"agents": agents}
    except Exception as e:
        logger.error("Agent status failed", error=str(e))
        return {"agents": [], "error": str(e)}


@router.post("/run", response_model=dict)
async def run_agent(task: AgentTaskCreate, background_tasks: BackgroundTasks):
    """Dispatch an agent task in the background. Returns task_id to poll for status."""
    db_task = AgentTaskQueries.create(task.agent_type.value, task.input)
    task_id = db_task["id"]

    async def _run() -> None:
        agent = get_agent(task.agent_type.value)
        agent.task_id = task_id
        AgentTaskQueries.update_status(task_id, "running")
        try:
            result = await agent.execute(task.input)
            AgentTaskQueries.update_status(task_id, "completed", result=result)
        except Exception as e:
            AgentTaskQueries.update_status(task_id, "failed", error=str(e))

    background_tasks.add_task(_run)
    return {"task_id": task_id, "status": "queued"}


@router.get("/{task_id}", response_model=dict)
async def get_task(task_id: str):
    """Get the status and result of an agent task."""
    task = AgentTaskQueries.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
