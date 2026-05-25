from __future__ import annotations

from typing import Any, Dict

from agents.base import BaseAgent
from db.queries import MemoryQueries


class MemoryAgent(BaseAgent):
    """Agent for reading and writing persistent memory entries."""

    agent_type = "memory"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action", "get")  # get | set | list

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

        else:
            raise ValueError(f"Unknown memory action: {action}")
