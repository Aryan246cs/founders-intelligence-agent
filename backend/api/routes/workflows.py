from fastapi import APIRouter
from services.n8n_service import trigger_workflow
from agents.orchestrator import OrchestratorAgent

router = APIRouter()


@router.post("/trigger/{workflow_name}")
async def trigger_n8n_workflow(workflow_name: str, payload: dict = None):
    """Trigger an n8n workflow by name."""
    result = await trigger_workflow(workflow_name, payload or {})
    return {"status": "triggered", "workflow": workflow_name, "result": result}


@router.post("/orchestrate")
async def orchestrate(steps: list[dict]):
    """Run a multi-agent orchestration workflow."""
    agent = OrchestratorAgent()
    result = await agent.run({"steps": steps})
    return result
