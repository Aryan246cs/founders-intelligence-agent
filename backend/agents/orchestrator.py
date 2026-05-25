from __future__ import annotations

from typing import Any, Dict, List, Type

from agents.base import BaseAgent
from agents.competitor_monitor import CompetitorMonitorAgent
from agents.research_agent import ResearchAgent
from agents.briefing_agent import BriefingAgent
from agents.memory_agent import MemoryAgent
from agents.planner_agent import PlannerAgent
from utils.logger import get_logger

logger = get_logger(__name__)

AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {
    "competitor_monitor": CompetitorMonitorAgent,
    "research": ResearchAgent,
    "briefing": BriefingAgent,
    "memory": MemoryAgent,
    "planner": PlannerAgent,
}


class OrchestratorAgent(BaseAgent):
    """Runs a sequence of agent tasks as a workflow."""

    agent_type = "orchestrator"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        steps: List[dict] = input_data.get("steps", [])
        results = []

        for i, step in enumerate(steps):
            agent_type = step.get("agent_type")
            step_input = step.get("input", {})

            agent_cls = AGENT_REGISTRY.get(agent_type)
            if not agent_cls:
                raise ValueError(f"Unknown agent type: {agent_type}")

            self._log("info", f"Step {i + 1}/{len(steps)}: running {agent_type}")
            agent = agent_cls()
            result = await agent.run(step_input)
            results.append({"agent_type": agent_type, "result": result})

        return {"steps_completed": len(results), "results": results}


def get_agent(agent_type: str) -> BaseAgent:
    """Factory — returns an agent instance by type string."""
    if agent_type == "orchestrator":
        return OrchestratorAgent()
    agent_cls = AGENT_REGISTRY.get(agent_type)
    if not agent_cls:
        raise ValueError(f"Unknown agent type: {agent_type}")
    return agent_cls()
