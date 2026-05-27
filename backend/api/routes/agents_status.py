"""
Agent status endpoint — derives live agent health from agent_tasks table.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter
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


@router.get("/status")
async def get_agents_status():
    """Return live status for all agents derived from agent_tasks."""
    try:
        db = get_supabase()
        cutoff_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

        agents = []
        for defn in AGENT_DEFINITIONS:
            agent_type = defn["type"]

            # Latest task for this agent
            latest_res = (
                db.table("agent_tasks")
                .select("*")
                .eq("agent_type", agent_type)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            latest = latest_res.data[0] if latest_res.data else None

            # Total execution count
            count_res = (
                db.table("agent_tasks")
                .select("id", count="exact")
                .eq("agent_type", agent_type)
                .execute()
            )
            total_count = count_res.count or 0

            # Failure count
            fail_res = (
                db.table("agent_tasks")
                .select("id", count="exact")
                .eq("agent_type", agent_type)
                .eq("status", "failed")
                .execute()
            )
            fail_count = fail_res.count or 0

            # Derive status
            if latest and latest["status"] == "running":
                status = "running"
            elif latest and latest["status"] == "failed":
                status = "error"
            elif total_count > 0:
                status = "active"
            else:
                status = "idle"

            # Uptime calculation
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
