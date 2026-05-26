"""
Memory retrieval utilities for historical comparison.

Provides reusable helpers to fetch previous workflow runs, competitor findings,
and stored memory snapshots from Supabase — without hardcoding competitor names.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from db.client import get_supabase
from utils.logger import get_logger

logger = get_logger(__name__)


def get_previous_workflow_runs(
    agent_type: str = "competitor_monitor", limit: int = 10
) -> List[dict]:
    """
    Retrieve the most recent completed agent task runs for a given agent type.

    Args:
        agent_type: The agent type to filter by (e.g. 'competitor_monitor').
        limit: Maximum number of records to return.

    Returns:
        List of agent_task dicts ordered by completion time descending.
    """
    db = get_supabase()
    res = (
        db.table("agent_tasks")
        .select("*")
        .eq("agent_type", agent_type)
        .eq("status", "completed")
        .order("completed_at", desc=True)
        .limit(limit)
        .execute()
    )
    runs = res.data or []
    logger.info(
        "Retrieved previous workflow runs", agent_type=agent_type, count=len(runs)
    )
    return runs


def get_previous_findings_for_competitor(
    competitor_name: str, limit: int = 5
) -> List[dict]:
    """
    Retrieve the most recent research findings tagged with a competitor name.

    Uses the tags array on research_findings — no hardcoded names.

    Args:
        competitor_name: The competitor name to search for in tags.
        limit: Maximum number of findings to return.

    Returns:
        List of research_finding dicts ordered by found_at descending.
    """
    db = get_supabase()
    tag = competitor_name.lower()
    res = (
        db.table("research_findings")
        .select("*")
        .contains("tags", [tag])
        .order("found_at", desc=True)
        .limit(limit)
        .execute()
    )
    findings = res.data or []
    logger.info(
        "Retrieved previous findings for competitor",
        competitor=competitor_name,
        count=len(findings),
    )
    return findings


def get_latest_competitor_snapshot(competitor_name: str) -> Optional[dict]:
    """
    Retrieve the most recently stored memory snapshot for a competitor.

    Snapshots are stored in memory_entries under namespace='competitor_snapshots'
    with key=competitor_name (lowercased).

    Args:
        competitor_name: The competitor name (case-insensitive).

    Returns:
        The memory_entry dict, or None if no snapshot exists.
    """
    db = get_supabase()
    key = competitor_name.lower()
    res = (
        db.table("memory_entries")
        .select("*")
        .eq("namespace", "competitor_snapshots")
        .eq("key", key)
        .execute()
    )
    entry = res.data[0] if res.data else None
    if entry:
        logger.info("Found existing snapshot", competitor=competitor_name)
    else:
        logger.info("No existing snapshot found", competitor=competitor_name)
    return entry


def get_historical_summaries(
    namespace: str = "competitor_snapshots", limit: int = 50
) -> List[dict]:
    """
    Retrieve all stored competitor snapshots from memory_entries.

    Args:
        namespace: The memory namespace to query.
        limit: Maximum number of entries to return.

    Returns:
        List of memory_entry dicts.
    """
    db = get_supabase()
    res = (
        db.table("memory_entries")
        .select("*")
        .eq("namespace", namespace)
        .order("updated_at", desc=True)
        .limit(limit)
        .execute()
    )
    summaries = res.data or []
    logger.info(
        "Retrieved historical summaries", namespace=namespace, count=len(summaries)
    )
    return summaries


def save_competitor_snapshot(competitor_name: str, snapshot: Dict[str, Any]) -> dict:
    """
    Upsert a competitor snapshot into memory_entries.

    Args:
        competitor_name: The competitor name (used as the key, lowercased).
        snapshot: The snapshot payload to store as the value.

    Returns:
        The saved memory_entry dict.
    """
    from datetime import datetime, timezone

    db = get_supabase()
    key = competitor_name.lower()
    res = (
        db.table("memory_entries")
        .upsert(
            {
                "key": key,
                "namespace": "competitor_snapshots",
                "value": snapshot,
                "tags": ["competitor_snapshot", key],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            on_conflict="key,namespace",
        )
        .execute()
    )
    entry = res.data[0]
    logger.info("Saved competitor snapshot", competitor=competitor_name)
    return entry
