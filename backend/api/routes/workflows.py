from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.orchestrator import OrchestratorAgent
from agents.planner_agent import PlannerAgent
from services.n8n_service import trigger_workflow

router = APIRouter()


class RunRequest(BaseModel):
    request: str
    send_to_slack: bool = False


class OrchestrateRequest(BaseModel):
    steps: List[Dict[str, Any]]


@router.post("/run")
async def run_autonomous_flow(body: RunRequest):
    """
    Full autonomous end-to-end flow.

    1. PlannerAgent creates an execution plan from the user request
    2. OrchestratorAgent executes each step (research, competitor monitor, memory, briefing)
    3. Returns the complete structured result

    Example request body:
    {
      "request": "Monitor OpenAI and Anthropic and generate a founder intelligence briefing",
      "send_to_slack": false
    }
    """
    # Step 1: Plan
    planner = PlannerAgent()
    plan = await planner.run({"request": body.request})

    steps = plan.get("steps", [])
    if not steps:
        raise HTTPException(status_code=500, detail="Planner returned no steps")

    # Inject send_to_slack into any briefing steps
    for step in steps:
        if step.get("agent_type") == "briefing":
            step["input"]["send_to_slack"] = body.send_to_slack

    # Step 2: Execute
    orchestrator = OrchestratorAgent()
    execution_result = await orchestrator.run({"steps": steps})

    # Extract briefing from results for top-level response
    briefing_result = None
    for r in execution_result.get("results", []):
        if r["agent_type"] == "briefing":
            briefing_result = r["result"]
            break

    return {
        "status": "completed",
        "plan_summary": plan.get("plan_summary", ""),
        "steps_executed": execution_result["steps_completed"],
        "briefing": briefing_result,
        "full_results": execution_result["results"],
    }


@router.post("/orchestrate")
async def orchestrate(body: OrchestrateRequest):
    """Run a manually defined multi-agent workflow."""
    agent = OrchestratorAgent()
    result = await agent.run({"steps": body.steps})
    return result


@router.post("/trigger/{workflow_name}")
async def trigger_n8n_workflow(
    workflow_name: str, payload: Optional[Dict[str, Any]] = None
):
    """Trigger an n8n workflow by name."""
    result = await trigger_workflow(workflow_name, payload or {})
    return {"status": "triggered", "workflow": workflow_name, "result": result}
