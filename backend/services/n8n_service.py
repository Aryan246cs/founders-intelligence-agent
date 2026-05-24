import httpx
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


async def trigger_workflow(workflow_name: str, payload: dict) -> dict | None:
    """Trigger an n8n workflow via its webhook URL."""
    url = f"{settings.n8n_webhook_base_url}/{workflow_name}"

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            res = await client.post(url, json=payload)
            res.raise_for_status()
            logger.info("n8n workflow triggered", workflow=workflow_name)
            return res.json()
        except httpx.HTTPError as e:
            logger.error("n8n trigger failed", workflow=workflow_name, error=str(e))
            return None
