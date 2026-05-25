from __future__ import annotations

from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.agent import AgentTaskCreate
from agents.orchestrator import get_agent
from db.queries import AgentTaskQueries

router = APIRouter()


@router.post("/run", response_model=dict)
async def run_agent(task: AgentTaskCreate, background_tasks: BackgroundTasks):
    """Dispatch an agent task in the background. Returns task_id to poll for status."""
    db_task = AgentTaskQueries.create(task.agent_type.value, task.input)
    task_id = db_task["id"]

    async def _run() -> None:
        agent = get_agent(task.agent_type.value)
        agent.task_id = task_id
        AgentTaskQueries.update_status(task_id, "running")
        try:
            result = await agent.execute(task.input)
            AgentTaskQueries.update_status(task_id, "completed", result=result)
        except Exception as e:
            AgentTaskQueries.update_status(task_id, "failed", error=str(e))

    background_tasks.add_task(_run)
    return {"task_id": task_id, "status": "queued"}


@router.get("/{task_id}", response_model=dict)
async def get_task(task_id: str):
    """Get the status and result of an agent task."""
    task = AgentTaskQueries.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
