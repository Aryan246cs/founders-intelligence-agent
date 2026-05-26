from __future__ import annotations

from typing import Any, Dict, List

from agents.base import BaseAgent
from db.queries import MemoryQueries, CompetitorSnapshotQueries
from services.comparison.comparison_engine import (
    compare_findings,
    build_briefing_changes_section,
)
from services.memory.retrieval import (
    get_previous_findings_for_competitor,
    get_latest_competitor_snapshot,
    save_competitor_snapshot,
)


class MemoryAgent(BaseAgent):
    """Agent for reading and writing persistent memory entries.

    Extended to support historical comparison:
      action='compare'  — fetch previous findings, run comparison engine,
                          return structured delta results.
      action='snapshot' — persist a competitor's current findings as a snapshot
                          for future comparison runs.
    """

    agent_type = "memory"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get(
            "action", "get"
        )  # get | set | list | compare | snapshot

        # ------------------------------------------------------------------ #
        # Existing actions — unchanged                                         #
        # ------------------------------------------------------------------ #
        if action == "set":
            entry = MemoryQueries.upsert(
                key=input_data["key"],
                namespace=input_data.get("namespace", "default"),
                value=input_data["value"],
                tags=input_data.get("tags", []),
            )
            self._log("info", f"Memory set: {input_data['key']}")
            return {"action": "set", "entry": entry}

        elif action == "get":
            entry = MemoryQueries.get(
                key=input_data["key"],
                namespace=input_data.get("namespace", "default"),
            )
            return {"action": "get", "entry": entry}

        elif action == "list":
            entries = MemoryQueries.list_by_namespace(
                namespace=input_data.get("namespace", "default"),
                limit=input_data.get("limit", 50),
            )
            return {"action": "list", "entries": entries, "count": len(entries)}

        # ------------------------------------------------------------------ #
        # New: snapshot — persist current findings for a competitor           #
        # ------------------------------------------------------------------ #
        elif action == "snapshot":
            competitor = input_data.get("competitor_name", "")
            if not competitor:
                raise ValueError("snapshot action requires 'competitor_name'")

            summary = input_data.get("summary", "")
            key_points: List[str] = input_data.get("key_points", [])
            tags: List[str] = input_data.get("tags", [])

            self._log(
                "info",
                f"Saving competitor snapshot: {competitor}",
                {"key_points_count": len(key_points)},
            )

            row = CompetitorSnapshotQueries.save(
                competitor_name=competitor,
                summary=summary,
                key_points=key_points,
                tags=tags,
            )

            # Also mirror into memory_entries for lightweight retrieval
            save_competitor_snapshot(
                competitor_name=competitor,
                snapshot={"summary": summary, "key_points": key_points, "tags": tags},
            )

            self._log("info", f"Snapshot saved: {competitor}")
            return {
                "action": "snapshot",
                "competitor": competitor,
                "snapshot_id": row["id"],
            }

        # ------------------------------------------------------------------ #
        # New: compare — fetch history and run comparison engine              #
        # ------------------------------------------------------------------ #
        elif action == "compare":
            competitor = input_data.get("competitor_name", "")
            if not competitor:
                raise ValueError("compare action requires 'competitor_name'")

            current_findings: List[Dict[str, Any]] = input_data.get(
                "current_findings", []
            )

            self._log(
                "info",
                f"Fetching previous findings for comparison: {competitor}",
                {"current_count": len(current_findings)},
            )

            # Retrieve previous findings from research_findings (tagged) and snapshots
            previous_from_findings = get_previous_findings_for_competitor(
                competitor, limit=10
            )
            previous_snapshot = get_latest_competitor_snapshot(competitor)

            # Build a unified previous findings list
            previous_findings: List[Dict[str, Any]] = list(previous_from_findings)
            if previous_snapshot and previous_snapshot.get("value"):
                snap_val = previous_snapshot["value"]
                # Treat the snapshot summary as a synthetic finding for comparison
                if snap_val.get("summary"):
                    previous_findings.append({"summary": snap_val["summary"]})

            if not previous_findings:
                self._log("info", f"No historical data found for: {competitor}")
            else:
                self._log(
                    "info",
                    f"Historical data retrieved for: {competitor}",
                    {"previous_count": len(previous_findings)},
                )

            comparison = compare_findings(
                competitor=competitor,
                current_findings=current_findings,
                previous_findings=previous_findings,
            )

            self._log(
                "info",
                f"Comparison complete: {competitor}",
                {
                    "has_changes": comparison["has_changes"],
                    "change_count": len(comparison["changes"]),
                },
            )

            return {"action": "compare", "comparison": comparison}

        # ------------------------------------------------------------------ #
        # New: compare_batch — compare multiple competitors at once           #
        # ------------------------------------------------------------------ #
        elif action == "compare_batch":
            competitors_data: Dict[str, List[Dict[str, Any]]] = input_data.get(
                "competitors", {}
            )
            if not competitors_data:
                raise ValueError("compare_batch action requires 'competitors' dict")

            self._log(
                "info",
                "Running batch comparison",
                {"competitor_count": len(competitors_data)},
            )

            results = []
            for competitor, current_findings in competitors_data.items():
                previous_from_findings = get_previous_findings_for_competitor(
                    competitor, limit=10
                )
                previous_snapshot = get_latest_competitor_snapshot(competitor)

                previous_findings: List[Dict[str, Any]] = list(previous_from_findings)
                if previous_snapshot and previous_snapshot.get("value", {}).get(
                    "summary"
                ):
                    previous_findings.append(
                        {"summary": previous_snapshot["value"]["summary"]}
                    )

                comparison = compare_findings(
                    competitor=competitor,
                    current_findings=current_findings,
                    previous_findings=previous_findings,
                )
                results.append(comparison)

            changes_section_md = build_briefing_changes_section(results)

            self._log(
                "info",
                "Batch comparison complete",
                {"results_count": len(results)},
            )

            return {
                "action": "compare_batch",
                "comparisons": results,
                "changes_section_markdown": changes_section_md,
            }

        else:
            raise ValueError(f"Unknown memory action: {action}")
