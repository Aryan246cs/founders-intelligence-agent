from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from agents.base import BaseAgent
from services import apify_service, groq_service
from db.queries import ResearchQueries

SYSTEM_PROMPT = """You are a competitive intelligence analyst for a startup founder.
Given scraped content from a competitor's website, extract key intelligence.

Respond ONLY with valid JSON (no markdown, no explanation) with these exact keys:
{
  "summary": "2-3 sentence summary of what this competitor is doing",
  "key_points": ["point1", "point2"],
  "sentiment": "positive|neutral|negative",
  "tags": ["tag1", "tag2"]
}"""


class CompetitorMonitorAgent(BaseAgent):
    agent_type = "competitor_monitor"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        competitor_name = input_data.get("competitor_name", "")
        website = input_data.get("website", "")

        self._log("info", f"Scraping competitor: {competitor_name}", {"website": website})

        pages = await apify_service.scrape_website(website, max_pages=3)
        combined_text = "\n\n".join(
            p.get("text", p.get("markdown", "")) for p in pages
        )[:8000]

        if not combined_text.strip():
            combined_text = f"No content scraped from {website}"

        analysis_raw = await groq_service.complete(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=f"Competitor: {competitor_name}\n\nWebsite content:\n{combined_text}",
        )

        analysis = groq_service.parse_json_response(analysis_raw)
        analysis.setdefault("summary", analysis_raw[:500])
        analysis.setdefault("key_points", [])
        analysis.setdefault("sentiment", "neutral")
        analysis.setdefault("tags", [])

        finding = ResearchQueries.save_finding({
            "source_url": website,
            "title": f"Competitor update: {competitor_name}",
            "summary": analysis["summary"],
            "sentiment": analysis["sentiment"],
            "tags": analysis["tags"] + ["competitor", competitor_name.lower()],
            "found_at": datetime.now(timezone.utc).isoformat(),
        })

        self._log("info", f"Competitor monitor complete: {competitor_name}")

        return {
            "competitor": competitor_name,
            "finding_id": finding["id"],
            "analysis": analysis,
        }
