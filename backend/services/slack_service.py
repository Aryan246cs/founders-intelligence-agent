"""
Slack delivery service — executive-grade, concise briefing format.

Extracts only the high-value sections from the briefing markdown
and formats them as clean Slack blocks. Never sends walls of text.
"""

from __future__ import annotations

import re
from typing import List, Optional

import httpx
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Markdown extraction helpers
# ---------------------------------------------------------------------------


def _extract_section(markdown: str, heading: str) -> str:
    """Extract content under a specific ## heading."""
    pattern = rf"##\s*{re.escape(heading)}\s*\n(.*?)(?=\n##|\Z)"
    match = re.search(pattern, markdown, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def _extract_bullets(text: str, max_items: int = 5) -> List[str]:
    """Extract bullet point lines from a text block."""
    bullets = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "• ", "* ")):
            content = stripped[2:].strip()
            if len(content) > 20:
                bullets.append(content)
        if len(bullets) >= max_items:
            break
    return bullets


def _build_executive_slack_blocks(title: str, markdown: str) -> List[dict]:
    """
    Build concise Slack blocks from briefing markdown.
    Extracts: Key Developments, Strategic Intelligence, Founder Takeaway.
    """
    blocks: List[dict] = []

    # Header
    blocks.append(
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🧠 Founder Intelligence Briefing",
                "emoji": True,
            },
        }
    )
    blocks.append({"type": "divider"})

    # Key Developments
    developments_text = _extract_section(markdown, "Key Developments")
    bullets = _extract_bullets(developments_text, max_items=5)
    if bullets:
        bullet_text = "\n".join(f"• {b}" for b in bullets)
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Key Developments*\n{bullet_text}",
                },
            }
        )
        blocks.append({"type": "divider"})

    # Strategic Intelligence
    strategic_text = _extract_section(markdown, "Strategic Intelligence")
    if strategic_text:
        # Cap at 400 chars
        strategic_text = strategic_text[:400]
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Strategic Intelligence*\n{strategic_text}",
                },
            }
        )
        blocks.append({"type": "divider"})

    # Founder Takeaway
    takeaway_text = _extract_section(markdown, "Founder Takeaway")
    if takeaway_text:
        takeaway_text = takeaway_text[:300]
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Founder Takeaway*\n_{takeaway_text}_",
                },
            }
        )

    # Fallback if extraction failed
    if len(blocks) <= 2:
        # Just send the first 600 chars of the markdown
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": markdown[:600]},
            }
        )

    return blocks


# ---------------------------------------------------------------------------
# Send functions
# ---------------------------------------------------------------------------


async def send_message(text: str, blocks: Optional[List[dict]] = None) -> bool:
    """Send a message to the configured Slack webhook."""
    if "your/webhook" in settings.slack_webhook_url or not settings.slack_webhook_url:
        logger.info("Slack webhook not configured — skipping")
        return False

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
    """Format and send a concise executive briefing to Slack."""
    blocks = _build_executive_slack_blocks(title, markdown)
    return await send_message(text=title, blocks=blocks)
