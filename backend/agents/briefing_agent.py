from agents.base import BaseAgent
from services import groq_service, slack_service
from db.queries import ResearchQueries, BriefingQueries
from datetime import datetime, timezone


SYSTEM_PROMPT = """You are a strategic advisor to a startup founder. Based on recent research findings,
generate a concise founder briefing in Markdown format.

Structure:
# Founder Intelligence Briefing — {date}

## Executive Summary
(2-3 sentences)

## Competitor Landscape
(key competitor movements)

## Market Trends
(notable trends)

## Strategic Opportunities
(actionable opportunities)

## Recommended Actions
(3-5 bullet points)

Be direct, specific, and founder-focused. Avoid fluff."""


class BriefingAgent(BaseAgent):
    agent_type = "briefing"

    async def execute(self, input_data: dict) -> dict:
        time_range_days = input_data.get("time_range_days", 7)
        send_to_slack = input_data.get("send_to_slack", True)

        self._log("info", "Generating founder briefing")

        # Pull recent findings
        findings = ResearchQueries.list_recent(limit=20)
        findings_text = "\n\n".join(
            f"- [{f['title']}]({f['source_url']}): {f['summary']}" for f in findings
        )

        today = datetime.now(timezone.utc).strftime("%B %d, %Y")

        briefing_md = await groq_service.complete(
            system_prompt=SYSTEM_PROMPT.replace("{date}", today),
            user_prompt=f"Recent findings (last {time_range_days} days):\n\n{findings_text}",
            max_tokens=3000,
        )

        # Persist briefing
        saved = BriefingQueries.save(
            {
                "title": f"Founder Briefing — {today}",
                "sections": [],
                "raw_markdown": briefing_md,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "sent_to_slack": False,
            }
        )

        # Send to Slack
        slack_sent = False
        if send_to_slack:
            slack_sent = await slack_service.send_briefing(
                title=f"Founder Briefing — {today}",
                markdown=briefing_md,
            )
            if slack_sent:
                BriefingQueries.mark_sent(saved["id"])

        return {
            "briefing_id": saved["id"],
            "title": saved["title"],
            "markdown": briefing_md,
            "sent_to_slack": slack_sent,
        }
