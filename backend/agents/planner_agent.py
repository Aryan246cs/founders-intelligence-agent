from __future__ import annotations

from typing import Any, Dict, List

from agents.base import BaseAgent
from services import groq_service

SYSTEM_PROMPT = """You are an AI workflow planner for a startup intelligence platform.
Given a user request, produce an execution plan as a list of agent steps.

Available agents:
- research: searches the web for information (input: {"query": "...", "max_results": 10})
- competitor_monitor: scrapes and analyzes a competitor website (input: {"competitor_name": "...", "website": "https://..."})
- memory: stores data persistently (input: {"action": "set", "key": "...", "namespace": "...", "value": {...}})
- briefing: generates a founder intelligence briefing (input: {"time_range_days": 7, "send_to_slack": false})

Respond ONLY with valid JSON (no markdown) in this format:
{
  "plan_summary": "one sentence describing what will be done",
  "steps": [
    {"agent_type": "research", "input": {"query": "...", "max_results": 10}},
    {"agent_type": "briefing", "input": {"time_range_days": 7, "send_to_slack": false}}
  ]
}

Keep plans focused. 2-4 steps maximum. Always end with a briefing step."""


class PlannerAgent(BaseAgent):
    agent_type = "planner"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        user_request = input_data.get("request", "")
        self._log("info", f"Planning workflow for: {user_request}")

        plan_raw = await groq_service.complete(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=f"User request: {user_request}",
            temperature=0.2,
        )

        plan = groq_service.parse_json_response(plan_raw)
        plan.setdefault("plan_summary", "Execute research and generate briefing")
        plan.setdefault(
            "steps",
            [
                {
                    "agent_type": "research",
                    "input": {"query": user_request, "max_results": 10},
                },
                {
                    "agent_type": "briefing",
                    "input": {"time_range_days": 7, "send_to_slack": False},
                },
            ],
        )

        self._log("info", f"Plan created: {len(plan['steps'])} steps")
        return plan
