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
