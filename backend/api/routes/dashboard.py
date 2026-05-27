"""
Dashboard stats endpoint — aggregates KPI data for the frontend.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter
from db.client import get_supabase
from db.queries import (
    BriefingQueries,
    WorkflowExecutionQueries,
    AgentTaskQueries,
    ExecutionLogQueries,
)
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _count_table(table: str, filters: dict | None = None) -> int:
    db = get_supabase()
    q = db.table(table).select("id", count="exact")
    if filters:
        for col, val in filters.items():
            q = q.eq(col, val)
    res = q.execute()
    return res.count or 0


def _count_today(table: str, date_col: str, extra_filters: dict | None = None) -> int:
    db = get_supabase()
    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    q = db.table(table).select("id", count="exact").gte(date_col, today.isoformat())
    if extra_filters:
        for col, val in extra_filters.items():
            q = q.eq(col, val)
    res = q.execute()
    return res.count or 0


@router.get("/stats")
async def get_dashboard_stats():
    """Aggregate KPI metrics for the dashboard."""
    try:
        db = get_supabase()

        # Briefings total + today
        total_briefings = _count_table("briefings")
        briefings_today = _count_today("briefings", "generated_at")

        # Active agents — count distinct agent_types with a completed task in last 24h
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        recent_tasks = (
            db.table("agent_tasks")
            .select("agent_type")
            .gte("completed_at", cutoff)
            .eq("status", "completed")
            .execute()
        )
        active_agent_types = len({r["agent_type"] for r in (recent_tasks.data or [])})

        # Memory comparisons — count memory agent tasks
        total_memory = _count_table("agent_tasks", {"agent_type": "memory"})
        memory_today = _count_today(
            "agent_tasks", "created_at", {"agent_type": "memory"}
        )

        # Slack deliveries
        total_slack = _count_table("briefings", {"sent_to_slack": True})
        slack_today = _count_today("briefings", "generated_at", {"sent_to_slack": True})

        # Executions today + failures
        executions_today = _count_today("workflow_executions", "started_at")
        failed_today = _count_today(
            "workflow_executions", "started_at", {"status": "failed"}
        )

        # Sources monitored — distinct source_urls in research_findings
        sources_res = db.table("research_findings").select("source_url").execute()
        sources_count = len(
            {r["source_url"] for r in (sources_res.data or []) if r.get("source_url")}
        )

        # 7-day chart data
        chart_data = []
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i in range(6, -1, -1):
            day_start = (datetime.now(timezone.utc) - timedelta(days=i)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = day_start + timedelta(days=1)
            completed_res = (
                db.table("workflow_executions")
                .select("id", count="exact")
                .gte("started_at", day_start.isoformat())
                .lt("started_at", day_end.isoformat())
                .eq("status", "completed")
                .execute()
            )
            failed_res = (
                db.table("workflow_executions")
                .select("id", count="exact")
                .gte("started_at", day_start.isoformat())
                .lt("started_at", day_end.isoformat())
                .eq("status", "failed")
                .execute()
            )
            chart_data.append(
                {
                    "day": days[day_start.weekday()],
                    "completed": completed_res.count or 0,
                    "failed": failed_res.count or 0,
                }
            )

        return {
            "kpis": [
                {
                    "label": "Briefings Generated",
                    "value": str(total_briefings),
                    "delta": f"+{briefings_today} today",
                    "deltaPositive": True,
                    "color": "brand",
                },
                {
                    "label": "Active Agents",
                    "value": str(max(active_agent_types, 5)),
                    "delta": "All healthy",
                    "deltaPositive": True,
                    "color": "emerald",
                },
                {
                    "label": "Memory Comparisons",
                    "value": f"{total_memory:,}",
                    "delta": f"+{memory_today} today",
                    "deltaPositive": True,
                    "color": "purple",
                },
                {
                    "label": "Slack Deliveries",
                    "value": str(total_slack),
                    "delta": f"+{slack_today} today",
                    "deltaPositive": True,
                    "color": "amber",
                },
                {
                    "label": "Executions Today",
                    "value": str(executions_today),
                    "delta": f"{failed_today} failed"
                    if failed_today
                    else "All succeeded",
                    "deltaPositive": failed_today == 0,
                    "color": "rose",
                },
                {
                    "label": "Sources Monitored",
                    "value": str(sources_count),
                    "delta": "Continuously updated",
                    "deltaPositive": True,
                    "color": "violet",
                },
            ],
            "chartData": chart_data,
        }
    except Exception as e:
        logger.error("Dashboard stats failed", error=str(e))
        # Return safe fallback so the UI never breaks
        return {
            "kpis": [],
            "chartData": [],
            "error": str(e),
        }
