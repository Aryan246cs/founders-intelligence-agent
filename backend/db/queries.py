from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from db.client import get_supabase
from utils.logger import get_logger

logger = get_logger(__name__)


class AgentTaskQueries:
    @staticmethod
    def create(agent_type: str, input_data: dict) -> dict:
        db = get_supabase()
        res = (
            db.table("agent_tasks")
            .insert(
                {
                    "agent_type": agent_type,
                    "input": input_data,
                    "status": "idle",
                }
            )
            .execute()
        )
        return res.data[0]

    @staticmethod
    def update_status(
        task_id: str,
        status: str,
        result: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> dict:
        db = get_supabase()
        payload: Dict[str, Any] = {"status": status}
        if result is not None:
            payload["result"] = result
        if error is not None:
            payload["error"] = error
        if status in ("completed", "failed"):
            payload["completed_at"] = datetime.now(timezone.utc).isoformat()
        res = db.table("agent_tasks").update(payload).eq("id", task_id).execute()
        return res.data[0]

    @staticmethod
    def get(task_id: str) -> Optional[dict]:
        db = get_supabase()
        res = db.table("agent_tasks").select("*").eq("id", task_id).execute()
        return res.data[0] if res.data else None


class MemoryQueries:
    @staticmethod
    def upsert(
        key: str, namespace: str, value: Any, tags: Optional[List[str]] = None
    ) -> dict:
        db = get_supabase()
        res = (
            db.table("memory_entries")
            .upsert(
                {
                    "key": key,
                    "namespace": namespace,
                    "value": value,
                    "tags": tags or [],
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                on_conflict="key,namespace",
            )
            .execute()
        )
        return res.data[0]

    @staticmethod
    def get(key: str, namespace: str = "default") -> Optional[dict]:
        db = get_supabase()
        res = (
            db.table("memory_entries")
            .select("*")
            .eq("key", key)
            .eq("namespace", namespace)
            .execute()
        )
        return res.data[0] if res.data else None

    @staticmethod
    def list_by_namespace(namespace: str, limit: int = 50) -> List[dict]:
        db = get_supabase()
        res = (
            db.table("memory_entries")
            .select("*")
            .eq("namespace", namespace)
            .limit(limit)
            .execute()
        )
        return res.data or []


class ResearchQueries:
    @staticmethod
    def save_finding(finding: dict) -> dict:
        db = get_supabase()
        res = db.table("research_findings").insert(finding).execute()
        return res.data[0]

    @staticmethod
    def list_recent(limit: int = 20) -> List[dict]:
        db = get_supabase()
        res = (
            db.table("research_findings")
            .select("*")
            .order("found_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []


class BriefingQueries:
    @staticmethod
    def save(briefing: dict) -> dict:
        db = get_supabase()
        res = db.table("briefings").insert(briefing).execute()
        return res.data[0]

    @staticmethod
    def list_recent(limit: int = 10) -> List[dict]:
        db = get_supabase()
        res = (
            db.table("briefings")
            .select("*")
            .order("generated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []

    @staticmethod
    def mark_sent(briefing_id: str) -> dict:
        db = get_supabase()
        res = (
            db.table("briefings")
            .update({"sent_to_slack": True})
            .eq("id", briefing_id)
            .execute()
        )
        return res.data[0]


class CompetitorSnapshotQueries:
    """
    Queries for competitor snapshot history stored in the competitor_snapshots table.
    This is an additive table — existing tables are untouched.
    """

    @staticmethod
    def save(
        competitor_name: str, summary: str, key_points: List[str], tags: List[str]
    ) -> dict:
        """Persist a new snapshot row for a competitor."""
        db = get_supabase()
        res = (
            db.table("competitor_snapshots")
            .insert(
                {
                    "competitor_name": competitor_name.lower(),
                    "summary": summary,
                    "key_points": key_points,
                    "tags": tags,
                }
            )
            .execute()
        )
        return res.data[0]

    @staticmethod
    def get_previous(competitor_name: str, limit: int = 5) -> List[dict]:
        """
        Retrieve the N most recent snapshots for a competitor, excluding the latest one
        (i.e. the ones before the current run).
        """
        db = get_supabase()
        res = (
            db.table("competitor_snapshots")
            .select("*")
            .eq("competitor_name", competitor_name.lower())
            .order("captured_at", desc=True)
            .limit(limit + 1)  # fetch one extra so we can skip the most recent
            .execute()
        )
        rows = res.data or []
        # Skip the very first row (most recent = current run just saved)
        return rows[1:] if len(rows) > 1 else []

    @staticmethod
    def get_latest(competitor_name: str) -> Optional[dict]:
        """Return the single most recent snapshot for a competitor."""
        db = get_supabase()
        res = (
            db.table("competitor_snapshots")
            .select("*")
            .eq("competitor_name", competitor_name.lower())
            .order("captured_at", desc=True)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    @staticmethod
    def list_all_competitors() -> List[str]:
        """Return distinct competitor names that have snapshots."""
        db = get_supabase()
        res = db.table("competitor_snapshots").select("competitor_name").execute()
        seen: set = set()
        names: List[str] = []
        for row in res.data or []:
            name = row["competitor_name"]
            if name not in seen:
                seen.add(name)
                names.append(name)
        return names


class ExecutionLogQueries:
    @staticmethod
    def log(
        task_id: Optional[str],
        agent_type: str,
        level: str,
        message: str,
        metadata: Optional[dict] = None,
    ):
        try:
            db = get_supabase()
            db.table("execution_logs").insert(
                {
                    "task_id": task_id,
                    "agent_type": agent_type,
                    "level": level,
                    "message": message,
                    "metadata": metadata or {},
                }
            ).execute()
        except Exception as e:
            # Never let logging failures crash the agent
            logger.error("Failed to write execution log", error=str(e))
