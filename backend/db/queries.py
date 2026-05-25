from __future__ import annotations

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
        task_id: str, status: str, result: dict = None, error: str = None
    ) -> dict:
        db = get_supabase()
        payload = {"status": status}
        if result is not None:
            payload["result"] = result
        if error is not None:
            payload["error"] = error
        if status in ("completed", "failed"):
            payload["completed_at"] = "now()"
        res = db.table("agent_tasks").update(payload).eq("id", task_id).execute()
        return res.data[0]

    @staticmethod
    def get(task_id: str) -> dict | None:
        db = get_supabase()
        res = db.table("agent_tasks").select("*").eq("id", task_id).single().execute()
        return res.data


class MemoryQueries:
    @staticmethod
    def upsert(key: str, namespace: str, value: any, tags: list[str] = None) -> dict:
        db = get_supabase()
        res = (
            db.table("memory_entries")
            .upsert(
                {
                    "key": key,
                    "namespace": namespace,
                    "value": value,
                    "tags": tags or [],
                    "updated_at": "now()",
                },
                on_conflict="key,namespace",
            )
            .execute()
        )
        return res.data[0]

    @staticmethod
    def get(key: str, namespace: str = "default") -> dict | None:
        db = get_supabase()
        res = (
            db.table("memory_entries")
            .select("*")
            .eq("key", key)
            .eq("namespace", namespace)
            .single()
            .execute()
        )
        return res.data

    @staticmethod
    def list_by_namespace(namespace: str, limit: int = 50) -> list[dict]:
        db = get_supabase()
        res = (
            db.table("memory_entries")
            .select("*")
            .eq("namespace", namespace)
            .limit(limit)
            .execute()
        )
        return res.data


class ResearchQueries:
    @staticmethod
    def save_finding(finding: dict) -> dict:
        db = get_supabase()
        res = db.table("research_findings").insert(finding).execute()
        return res.data[0]

    @staticmethod
    def list_recent(limit: int = 20) -> list[dict]:
        db = get_supabase()
        res = (
            db.table("research_findings")
            .select("*")
            .order("found_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data


class BriefingQueries:
    @staticmethod
    def save(briefing: dict) -> dict:
        db = get_supabase()
        res = db.table("briefings").insert(briefing).execute()
        return res.data[0]

    @staticmethod
    def list_recent(limit: int = 10) -> list[dict]:
        db = get_supabase()
        res = (
            db.table("briefings")
            .select("*")
            .order("generated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data

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
        task_id: str, agent_type: str, level: str, message: str, metadata: dict = None
    ):
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
