from __future__ import annotations

from typing import Any, Dict, List, Type

from agents.base import BaseAgent
from agents.competitor_monitor import CompetitorMonitorAgent
from agents.research_agent import ResearchAgent
from agents.briefing_agent import BriefingAgent
from agents.memory_agent import MemoryAgent
from agents.planner_agent import PlannerAgent
from agents.startup_research_agent import StartupResearchAgent
from utils.logger import get_logger

logger = get_logger(__name__)

AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {
    "competitor_monitor": CompetitorMonitorAgent,
    "research": ResearchAgent,
    "briefing": BriefingAgent,
    "memory": MemoryAgent,
    "planner": PlannerAgent,
    "startup_research": StartupResearchAgent,
}


STEP_LABELS: Dict[str, str] = {
    "competitor_monitor": "Analysing competitor",
    "research": "Searching the web",
    "briefing": "Generating intelligence briefing",
    "memory": "Comparing against memory",
    "planner": "Planning workflow",
    "startup_research": "Running startup research",
}


def describe_steps(steps: List[dict]) -> List[tuple[str, str]]:
    """
    Turn a plan into (key, label) pairs for the job tracker.

    Keys are positional because the same agent can legitimately appear several
    times in one plan (one competitor_monitor step per competitor).
    """
    described = []
    for i, step in enumerate(steps):
        agent_type = step.get("agent_type", "unknown")
        label = STEP_LABELS.get(agent_type, agent_type.replace("_", " ").title())
        target = step.get("input", {}).get("competitor_name") or step.get(
            "input", {}
        ).get("query")
        described.append(
            (f"step_{i}", f"{label}: {target}" if target else label),
        )
    return described


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

            step_key = f"step_{i}"
            self._step(step_key, f"Step {i + 1}/{len(steps)}: running {agent_type}")
            # Child agents share the reporter so their own sub-steps (e.g. the
            # research pipeline's ten stages) land on the same job timeline.
            agent = agent_cls(progress=self.progress)
            result = await agent.run(step_input)
            self.progress.done(step_key)
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
