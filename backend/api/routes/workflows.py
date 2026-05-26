"""
Workflow orchestration endpoints.

Designed for external automation platforms (n8n, schedulers, cron jobs).
Every response uses a consistent, automation-friendly JSON envelope so
callers never need to inspect nested structures to determine outcome.

Endpoints
---------
POST /api/workflows/run            — autonomous plan → execute → briefing flow
POST /api/workflows/manual-trigger — execute a caller-supplied step list
GET  /api/workflows/status/{id}    — poll a workflow execution by ID
GET  /api/workflows/executions     — list recent executions
POST /api/workflows/trigger/{name} — fire an n8n webhook (unchanged)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.orchestrator import OrchestratorAgent
from agents.planner_agent import PlannerAgent
from db.queries import WorkflowExecutionQueries
from services.n8n_service import trigger_workflow
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class RunRequest(BaseModel):
    request: str
    send_to_slack: bool = False
    trigger_source: str = "api"  # 'api' | 'n8n' | 'scheduler' | 'manual'


class ManualTriggerRequest(BaseModel):
    steps: List[Dict[str, Any]]
    send_to_slack: bool = False
    trigger_source: str = "manual"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_execution_response(record: dict) -> dict:
    """
    Convert a workflow_executions row into the standard automation envelope.

    All fields are always present so n8n expressions never hit KeyError.
    """
    return {
        "execution_id": record["id"],
        "status": record["status"],
        "trigger_source": record.get("trigger_source", "api"),
        "request_summary": record.get("request_summary", ""),
        "plan_summary": record.get("plan_summary") or "",
        "steps_total": record.get("steps_total", 0),
        "steps_completed": record.get("steps_completed", 0),
        "briefing_available": record.get("briefing_available", False),
        "briefing_id": record.get("briefing_id"),
        "slack_delivered": record.get("slack_delivered", False),
        "comparison_ran": record.get("comparison_ran", False),
        "has_competitor_changes": record.get("has_competitor_changes", False),
        "error": record.get("error"),
        "started_at": record.get("started_at"),
        "completed_at": record.get("completed_at"),
        "duration_ms": record.get("duration_ms"),
    }


def _extract_briefing(results: List[dict]) -> Optional[dict]:
    """Pull the briefing agent result out of an orchestrator results list."""
    for r in results:
        if r.get("agent_type") == "briefing":
            return r.get("result")
    return None


def _has_competitor_changes(results: List[dict]) -> bool:
    """Return True if any memory compare_batch result detected changes."""
    for r in results:
        if r.get("agent_type") == "memory":
            comparisons = r.get("result", {}).get("comparisons", [])
            if any(c.get("has_changes") for c in comparisons):
                return True
    return False


def _comparison_ran(results: List[dict]) -> bool:
    """Return True if a memory comparison step was executed."""
    for r in results:
        if r.get("agent_type") == "memory":
            action = r.get("result", {}).get("action", "")
            if action in ("compare", "compare_batch"):
                return True
    return False


# ---------------------------------------------------------------------------
# POST /run  — autonomous plan → execute → briefing
# ---------------------------------------------------------------------------


@router.post("/run")
async def run_autonomous_flow(body: RunRequest):
    """
    Full autonomous end-to-end workflow.

    1. PlannerAgent builds an execution plan from the natural-language request.
    2. OrchestratorAgent runs each step sequentially.
    3. Returns a stable execution envelope suitable for n8n polling.

    Idempotent across repeated calls — each call creates a new execution record.
    """
    started_at = datetime.now(timezone.utc)
    execution = WorkflowExecutionQueries.create(
        trigger_source=body.trigger_source,
        request_summary=body.request,
    )
    execution_id: str = execution["id"]

    logger.info(
        "Workflow run started",
        execution_id=execution_id,
        trigger_source=body.trigger_source,
    )

    try:
        # Step 1: plan
        planner = PlannerAgent()
        plan = await planner.run({"request": body.request})

        steps: List[dict] = plan.get("steps", [])
        if not steps:
            raise ValueError("Planner returned no steps")

        # Inject send_to_slack into briefing steps
        for step in steps:
            if step.get("agent_type") == "briefing":
                step["input"]["send_to_slack"] = body.send_to_slack

        # Step 2: execute
        orchestrator = OrchestratorAgent()
        execution_result = await orchestrator.run({"steps": steps})

        all_results: List[dict] = execution_result.get("results", [])
        briefing = _extract_briefing(all_results)
        briefing_id: Optional[str] = briefing.get("briefing_id") if briefing else None

        record = WorkflowExecutionQueries.complete(
            execution_id=execution_id,
            steps_total=len(steps),
            steps_completed=execution_result.get("steps_completed", 0),
            plan_summary=plan.get("plan_summary", ""),
            briefing_id=briefing_id,
            briefing_available=briefing is not None,
            slack_delivered=bool(briefing and briefing.get("sent_to_slack")),
            comparison_ran=_comparison_ran(all_results),
            has_competitor_changes=_has_competitor_changes(all_results),
            started_at=started_at,
        )

        logger.info(
            "Workflow run completed",
            execution_id=execution_id,
            duration_ms=record.get("duration_ms"),
        )

        return _build_execution_response(record)

    except Exception as exc:
        error_msg = str(exc)
        logger.error("Workflow run failed", execution_id=execution_id, error=error_msg)
        record = WorkflowExecutionQueries.fail(
            execution_id=execution_id,
            error=error_msg,
            started_at=started_at,
        )
        raise HTTPException(
            status_code=500,
            detail={
                **_build_execution_response(record),
                "message": error_msg,
            },
        )


# ---------------------------------------------------------------------------
# POST /manual-trigger  — caller supplies explicit step list
# ---------------------------------------------------------------------------


@router.post("/manual-trigger")
async def manual_trigger(body: ManualTriggerRequest):
    """
    Execute a caller-supplied list of agent steps.

    Useful for n8n workflows that build their own step sequences and need
    a stable execution record back. Same envelope as /run.
    """
    started_at = datetime.now(timezone.utc)

    step_types = [s.get("agent_type", "unknown") for s in body.steps]
    request_summary = f"Manual trigger: {', '.join(step_types)}"

    execution = WorkflowExecutionQueries.create(
        trigger_source=body.trigger_source,
        request_summary=request_summary,
    )
    execution_id: str = execution["id"]

    logger.info(
        "Manual trigger started",
        execution_id=execution_id,
        steps=step_types,
    )

    try:
        # Inject send_to_slack into any briefing steps
        for step in body.steps:
            if step.get("agent_type") == "briefing":
                step["input"] = step.get("input", {})
                step["input"]["send_to_slack"] = body.send_to_slack

        orchestrator = OrchestratorAgent()
        execution_result = await orchestrator.run({"steps": body.steps})

        all_results: List[dict] = execution_result.get("results", [])
        briefing = _extract_briefing(all_results)
        briefing_id: Optional[str] = briefing.get("briefing_id") if briefing else None

        record = WorkflowExecutionQueries.complete(
            execution_id=execution_id,
            steps_total=len(body.steps),
            steps_completed=execution_result.get("steps_completed", 0),
            plan_summary=request_summary,
            briefing_id=briefing_id,
            briefing_available=briefing is not None,
            slack_delivered=bool(briefing and briefing.get("sent_to_slack")),
            comparison_ran=_comparison_ran(all_results),
            has_competitor_changes=_has_competitor_changes(all_results),
            started_at=started_at,
        )

        logger.info(
            "Manual trigger completed",
            execution_id=execution_id,
            duration_ms=record.get("duration_ms"),
        )

        return _build_execution_response(record)

    except Exception as exc:
        error_msg = str(exc)
        logger.error(
            "Manual trigger failed", execution_id=execution_id, error=error_msg
        )
        record = WorkflowExecutionQueries.fail(
            execution_id=execution_id,
            error=error_msg,
            started_at=started_at,
        )
        raise HTTPException(
            status_code=500,
            detail={
                **_build_execution_response(record),
                "message": error_msg,
            },
        )


# ---------------------------------------------------------------------------
# GET /status/{execution_id}  — poll a single execution
# ---------------------------------------------------------------------------


@router.get("/status/{execution_id}")
async def get_execution_status(execution_id: str):
    """
    Retrieve the current state of a workflow execution by ID.

    Designed for n8n polling loops. Always returns the full envelope —
    callers can check `status` ('running' | 'completed' | 'failed') and
    `briefing_available` without parsing nested structures.
    """
    record = WorkflowExecutionQueries.get(execution_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "execution_id": execution_id,
                "status": "not_found",
                "message": f"No execution found with id {execution_id}",
            },
        )
    return _build_execution_response(record)


# ---------------------------------------------------------------------------
# GET /executions  — list recent runs
# ---------------------------------------------------------------------------


@router.get("/executions")
async def list_executions(limit: int = 20):
    """List recent workflow executions, newest first."""
    records = WorkflowExecutionQueries.list_recent(limit=limit)
    return {
        "executions": [_build_execution_response(r) for r in records],
        "total": len(records),
    }


# ---------------------------------------------------------------------------
# POST /trigger/{workflow_name}  — fire an n8n webhook (unchanged)
# ---------------------------------------------------------------------------


@router.post("/trigger/{workflow_name}")
async def trigger_n8n_workflow(
    workflow_name: str,
    payload: Optional[Dict[str, Any]] = None,
):
    """Trigger an n8n workflow by name via its webhook URL."""
    result = await trigger_workflow(workflow_name, payload or {})
    return {"status": "triggered", "workflow": workflow_name, "result": result}
