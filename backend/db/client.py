from __future__ import annotations

from supabase import create_client, Client
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_client = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )
        logger.info("Supabase client initialized")
    return _client


def describe_db_error(exc: Exception) -> str:
    """
    Turn a Supabase/httpx failure into something a human can act on.

    A raw `[Errno 8] nodename nor servname provided` reads like an application
    bug; the actual cause is nearly always a free-tier project paused for
    inactivity, which is a two-click fix in the dashboard.
    """
    msg = str(exc)
    if "nodename nor servname" in msg or "Name or service not known" in msg:
        return (
            "Supabase is unreachable — the project host does not resolve, which usually "
            "means the project is paused. Resume it at supabase.com/dashboard, then retry."
        )
    if "Connection" in msg or "timed out" in msg.lower():
        return f"Supabase is unreachable: {msg[:150]}"
    if "row-level security" in msg.lower() or "RLS" in msg:
        return (
            f"Supabase rejected the write due to row-level security: {msg[:150]}. "
            "Disable RLS on the affected table or add a service-role policy."
        )
    return f"Database error: {msg[:200]}"
