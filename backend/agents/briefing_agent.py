from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from agents.base import BaseAgent
from services import groq_service, slack_service
from db.queries import ResearchQueries, BriefingQueries

SYSTEM_PROMPT = """You are a strategic advisor to a startup founder.
Based on recent research findings, generate a concise founder intelligence briefing in Markdown.

Use this structure exactly:
# Founder Intelligence Briefing — {date}

## Executive Summary
(2-3 sentences on the most important developments)

## Competitor Landscape
(key competitor movements and what they mean)

## Market Trends
(notable trends worth tracking)

## Strategic Opportunities
(specific, actionable opportunities for a founder)

## Recommended Actions
- Action 1
- Action 2
- Action 3

Be direct, specific, and founder-focused. No fluff."""


class BriefingAgent(BaseAgent):
    agent_type = "briefing"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        time_range_days = input_data.get("time_range_days", 7)
        send_to_slack = input_data.get("send_to_slack", False)

        self._log("info", "Generating founder briefing")

        findings = ResearchQueries.list_recent(limit=20)

        if findings:
            findings_text = "\n\n".join(
                f"- [{f['title']}]({f.get('source_url', '')}): {f['summary']}"
                for f in findings
            )
        else:
            findings_text = "No recent research findings available. Generate a general AI startup landscape briefing."

        today = datetime.now(timezone.utc).strftime("%B %d, %Y")

        briefing_md = await groq_service.complete(
            system_prompt=SYSTEM_PROMPT.replace("{date}", today),
            user_prompt=f"Recent findings (last {time_range_days} days):\n\n{findings_text}",
            max_tokens=3000,
        )

        saved = BriefingQueries.save(
            {
                "title": f"Founder Briefing — {today}",
                "sections": [],
                "raw_markdown": briefing_md,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "sent_to_slack": False,
            }
        )

        slack_sent = False
        if send_to_slack:
            slack_sent = await slack_service.send_briefing(
                title=f"Founder Briefing — {today}",
                markdown=briefing_md,
            )
            if slack_sent:
                BriefingQueries.mark_sent(saved["id"])

        self._log("info", "Briefing generated and saved")

        return {
            "briefing_id": saved["id"],
            "title": saved["title"],
            "markdown": briefing_md,
            "sent_to_slack": slack_sent,
        }
