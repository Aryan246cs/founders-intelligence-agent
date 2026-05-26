from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from agents.base import BaseAgent
from services import groq_service, slack_service
from db.queries import ResearchQueries, BriefingQueries
from services.comparison.comparison_engine import (
    compare_findings,
    build_briefing_changes_section,
)
from services.memory.retrieval import get_previous_findings_for_competitor
from utils.logger import get_logger

logger = get_logger(__name__)

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


def _extract_competitors_from_findings(findings: List[dict]) -> List[str]:
    """Derive deduplicated competitor names from finding tags.

    Tags follow the convention: ["competitor", "<name>", ...].
    """
    competitors: List[str] = []
    seen: set = set()
    for f in findings:
        tags: List[str] = f.get("tags", [])
        if "competitor" in tags:
            for tag in tags:
                if tag != "competitor" and tag not in seen:
                    seen.add(tag)
                    competitors.append(tag)
    return competitors


def _build_changes_section(findings: List[dict]) -> str:
    """Build the 'Changes Since Previous Run' Markdown section.

    Steps:
      1. Extract competitor names from finding tags.
      2. Fetch previous findings per competitor from DB.
      3. Run the comparison engine (no LLM).
      4. Format results into Markdown.

    Falls back gracefully when no history exists.
    """
    competitors = _extract_competitors_from_findings(findings)

    if not competitors:
        logger.info("No competitor tags in findings — skipping historical comparison")
        return (
            "## Changes Since Previous Run\n\nNo previous historical data available.\n"
        )

    comparison_results = []
    for competitor in competitors:
        current = [f for f in findings if competitor in f.get("tags", [])]
        previous = get_previous_findings_for_competitor(competitor, limit=10)

        logger.info(
            "Comparing findings for competitor",
            competitor=competitor,
            current=len(current),
            previous=len(previous),
        )

        result = compare_findings(
            competitor=competitor,
            current_findings=current,
            previous_findings=previous,
        )
        comparison_results.append(result)

    return build_briefing_changes_section(comparison_results)


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
            findings_text = (
                "No recent research findings available. "
                "Generate a general AI startup landscape briefing."
            )

        today = datetime.now(timezone.utc).strftime("%B %d, %Y")

        # Build historical changes section — pure structured logic, no LLM
        self._log("info", "Building historical comparison section")
        try:
            changes_section = _build_changes_section(findings)
        except Exception as exc:
            # Never let comparison failures block briefing generation
            logger.error(
                "Historical comparison failed — using fallback", error=str(exc)
            )
            changes_section = "## Changes Since Previous Run\n\nNo previous historical data available.\n"
        self._log("info", "Historical comparison section ready")

        # LLM briefing generation
        briefing_md = await groq_service.complete(
            system_prompt=SYSTEM_PROMPT.replace("{date}", today),
            user_prompt=f"Recent findings (last {time_range_days} days):\n\n{findings_text}",
            max_tokens=3000,
        )

        # Inject changes section before Competitor Landscape, or append at end
        if "## Competitor Landscape" in briefing_md:
            briefing_md = briefing_md.replace(
                "## Competitor Landscape",
                f"{changes_section}\n## Competitor Landscape",
                1,
            )
        else:
            briefing_md = f"{briefing_md}\n\n{changes_section}"

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
