"""
Live activity feed — aggregates recent execution logs into a unified event stream.
"""

from __future__ import annotations

from fastapi import APIRouter
from db.client import get_supabase
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

_LEVEL_TYPE_MAP = {
    "error": "error",
    "warning": "warning",
    "warn": "warning",
    "info": "info",
    "success": "success",
}

_AGENT_DISPLAY = {
    "research": "Research Agent",
    "competitor_monitor": "Competitor Agent",
    "memory": "Memory Agent",
    "briefing": "Briefing Agent",
    "planner": "Planner Agent",
    "orchestrator": "Orchestrator",
    "slack": "Slack Agent",
}

_SUCCESS_KEYWORDS = ["complete", "saved", "delivered", "generated", "snapshot", "done"]
_WARNING_KEYWORDS = ["detected", "signal", "change", "update", "new", "shift"]


def _infer_type(level: str, message: str) -> str:
    if level in ("error",):
        return "error"
    msg_lower = message.lower()
    if any(k in msg_lower for k in _SUCCESS_KEYWORDS):
        return "success"
    if any(k in msg_lower for k in _WARNING_KEYWORDS):
        return "warning"
    return "info"


def _relative_time(iso: str) -> str:
    from datetime import datetime, timezone

    try:
        logged = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = int((now - logged).total_seconds())
        if diff < 60:
            return "Just now"
        if diff < 3600:
            return f"{diff // 60} min ago"
        if diff < 86400:
            return f"{diff // 3600}h ago"
        return f"{diff // 86400}d ago"
    except Exception:
        return "Recently"


@router.get("/feed")
async def get_activity_feed(limit: int = 20):
    """Return recent execution log entries as a unified activity feed."""
    try:
        db = get_supabase()
        res = (
            db.table("execution_logs")
            .select("*")
            .order("logged_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = res.data or []

        events = []
        for row in rows:
            level = row.get("level", "info")
            message = row.get("message", "")
            agent_type = row.get("agent_type", "")
            logged_at = row.get("logged_at", "")

            events.append(
                {
                    "id": row["id"],
                    "timestamp": _relative_time(logged_at),
                    "message": message,
                    "type": _infer_type(level, message),
                    "agent": _AGENT_DISPLAY.get(
                        agent_type, agent_type.replace("_", " ").title()
                    ),
                    "loggedAt": logged_at,
                }
            )

        return {"events": events, "total": len(events)}
    except Exception as e:
        logger.error("Activity feed failed", error=str(e))
        return {"events": [], "total": 0, "error": str(e)}
