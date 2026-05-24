import httpx
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


async def send_message(text: str, blocks: list[dict] = None) -> bool:
    """Send a message to the configured Slack webhook."""
    payload: dict = {"text": text}
    if blocks:
        payload["blocks"] = blocks

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            res = await client.post(settings.slack_webhook_url, json=payload)
            res.raise_for_status()
            logger.info("Slack message sent")
            return True
        except httpx.HTTPError as e:
            logger.error("Slack send failed", error=str(e))
            return False


async def send_briefing(title: str, markdown: str) -> bool:
    """Format and send a briefing to Slack."""
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": title},
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": markdown[:2900]},  # Slack block limit
        },
    ]
    return await send_message(text=title, blocks=blocks)
