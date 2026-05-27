"""
Memory comparisons endpoint — returns structured competitor snapshot diffs
for the Memory History page.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from db.client import get_supabase
from db.queries import CompetitorSnapshotQueries
from services.comparison.comparison_engine import compare_findings
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _build_comparison(
    competitor: str,
    previous: dict,
    current: dict,
) -> dict:
    """Build a MemoryComparison-shaped dict from two snapshot rows."""
    prev_key_points: List[str] = previous.get("key_points") or []
    curr_key_points: List[str] = current.get("key_points") or []

    # Run comparison engine on summaries
    prev_findings = [{"summary": previous.get("summary", "")}]
    curr_findings = [{"summary": current.get("summary", "")}]
    # Also include key_points as synthetic findings
    for kp in prev_key_points:
        prev_findings.append({"summary": kp})
    for kp in curr_key_points:
        curr_findings.append({"summary": kp})

    result = compare_findings(
        competitor=competitor,
        current_findings=curr_findings,
        previous_findings=prev_findings,
    )

    changes = [
        {
            "type": c["type"],
            "summary": c["summary"],
            "isAddition": True,
            "isRemoval": False,
        }
        for c in result.get("changes", [])
    ]

    # Build a detected signal from the delta summary
    delta = result.get("delta_summary", "")
    signal = delta if result.get("has_changes") else ""

    return {
        "id": f"cmp-{current['id']}",
        "competitor": competitor.title(),
        "previousSnapshot": {
            "id": previous["id"],
            "competitor": competitor.title(),
            "capturedAt": previous.get("captured_at", ""),
            "summary": previous.get("summary", ""),
            "keyPoints": prev_key_points,
            "tags": previous.get("tags") or [],
        },
        "currentSnapshot": {
            "id": current["id"],
            "competitor": competitor.title(),
            "capturedAt": current.get("captured_at", ""),
            "summary": current.get("summary", ""),
            "keyPoints": curr_key_points,
            "tags": current.get("tags") or [],
        },
        "hasChanges": result.get("has_changes", False),
        "changes": changes,
        "deltaSummary": delta,
        "detectedSignal": signal,
        "comparedAt": current.get("captured_at", ""),
    }


@router.get("/comparisons")
async def get_memory_comparisons(limit: int = 20, changes_only: bool = True):
    """
    Return structured memory comparisons for all tracked competitors.
    Only returns pairs where a previous snapshot exists.
    """
    try:
        db = get_supabase()

        # Get all distinct competitors
        competitors = CompetitorSnapshotQueries.list_all_competitors()

        comparisons = []
        for competitor in competitors:
            # Get the two most recent snapshots
            res = (
                db.table("competitor_snapshots")
                .select("*")
                .eq("competitor_name", competitor)
                .order("captured_at", desc=True)
                .limit(2)
                .execute()
            )
            rows = res.data or []
            if len(rows) < 2:
                continue  # Need at least 2 snapshots to compare

            current = rows[0]
            previous = rows[1]

            comparison = _build_comparison(competitor, previous, current)

            if changes_only and not comparison["hasChanges"]:
                continue

            comparisons.append(comparison)

        # Sort by most recent comparison first
        comparisons.sort(key=lambda c: c["comparedAt"], reverse=True)

        return {
            "comparisons": comparisons[:limit],
            "total": len(comparisons),
        }
    except Exception as e:
        logger.error("Memory comparisons failed", error=str(e))
        return {"comparisons": [], "total": 0, "error": str(e)}


@router.get("/stats")
async def get_memory_stats():
    """Return aggregate memory system statistics."""
    try:
        db = get_supabase()

        snapshots_res = (
            db.table("competitor_snapshots").select("id", count="exact").execute()
        )
        total_snapshots = snapshots_res.count or 0

        comparisons_res = (
            db.table("agent_tasks")
            .select("id", count="exact")
            .eq("agent_type", "memory")
            .execute()
        )
        total_comparisons = comparisons_res.count or 0

        competitors = CompetitorSnapshotQueries.list_all_competitors()

        # Count high-signal comparisons (tasks with has_changes in result)
        tasks_res = (
            db.table("agent_tasks")
            .select("result")
            .eq("agent_type", "memory")
            .eq("status", "completed")
            .execute()
        )
        signals = 0
        for task in tasks_res.data or []:
            result = task.get("result") or {}
            comparisons = result.get("comparisons", [])
            signals += sum(1 for c in comparisons if c.get("has_changes"))

        return {
            "totalSnapshots": total_snapshots,
            "comparisonsRun": total_comparisons,
            "signalsDetected": signals,
            "competitorsTracked": len(competitors),
        }
    except Exception as e:
        logger.error("Memory stats failed", error=str(e))
        return {
            "totalSnapshots": 0,
            "comparisonsRun": 0,
            "signalsDetected": 0,
            "competitorsTracked": 0,
            "error": str(e),
        }
