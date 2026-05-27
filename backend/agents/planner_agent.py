from __future__ import annotations

import re
from typing import Any, Dict, List

from agents.base import BaseAgent
from services import groq_service

SYSTEM_PROMPT = """You are an AI workflow planner for a startup intelligence platform.
Given a user request, produce an execution plan as a list of agent steps.

Available agents:
- competitor_monitor: scrapes and analyzes a competitor website
  input: {"competitor_name": "...", "website": "https://..."}
- research: searches the web for information
  input: {"query": "...", "max_results": 10}
- briefing: generates a founder intelligence briefing
  input: {"send_to_slack": false, "force": true, "competitor_names": [...], "original_request": "...", "lookback_minutes": 30}

RULES:
- For competitor monitoring, use competitor_monitor steps with the correct website URL.
- For well-known Indian companies: zomato.com, swiggy.in, zepto.in, blinkit.com, dunzo.com, bigbasket.com
- For well-known global companies: openai.com, anthropic.com, google.com, microsoft.com, meta.com
- Always end with ONE briefing step.
- The briefing step must include "competitor_names" listing all competitors being monitored.
- The briefing step must include "original_request" with the user's original request text.
- Keep plans to 2-5 steps maximum.
- Do NOT add a research step if the user only asked for competitor monitoring.

Respond ONLY with valid JSON (no markdown):
{
  "plan_summary": "one sentence",
  "steps": [
    {"agent_type": "competitor_monitor", "input": {"competitor_name": "Zomato", "website": "https://zomato.com"}},
    {"agent_type": "competitor_monitor", "input": {"competitor_name": "Swiggy", "website": "https://swiggy.in"}},
    {"agent_type": "briefing", "input": {"send_to_slack": false, "force": true, "competitor_names": ["zomato", "swiggy"], "original_request": "Monitor Zomato and Swiggy", "lookback_minutes": 30}}
  ]
}"""


def _extract_competitor_names_from_steps(steps: List[dict]) -> List[str]:
    """Pull competitor names from competitor_monitor steps."""
    names = []
    for step in steps:
        if step.get("agent_type") == "competitor_monitor":
            name = step.get("input", {}).get("competitor_name", "")
            if name:
                names.append(name.lower())
    return names


class PlannerAgent(BaseAgent):
    agent_type = "planner"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        user_request = input_data.get("request", "")
        self._log("info", f"Planning workflow for: {user_request}")

        plan_raw = await groq_service.complete(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=f"User request: {user_request}",
            temperature=0.1,
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
                    "input": {
                        "send_to_slack": False,
                        "force": True,
                        "competitor_names": [],
                        "original_request": user_request,
                        "lookback_minutes": 30,
                    },
                },
            ],
        )

        # Post-process: ensure briefing step has correct fields
        competitor_names = _extract_competitor_names_from_steps(plan["steps"])

        for step in plan.get("steps", []):
            if step.get("agent_type") == "briefing":
                inp = step.setdefault("input", {})
                inp["force"] = True
                inp["original_request"] = user_request
                inp["lookback_minutes"] = 30
                # Merge competitor names from monitor steps if not already set
                if not inp.get("competitor_names"):
                    inp["competitor_names"] = competitor_names
                elif isinstance(inp["competitor_names"], list):
                    # Ensure lowercase
                    inp["competitor_names"] = [
                        n.lower() for n in inp["competitor_names"]
                    ]

        self._log(
            "info", f"Plan: {len(plan['steps'])} steps, competitors: {competitor_names}"
        )
        return plan
