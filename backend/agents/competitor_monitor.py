from agents.base import BaseAgent
from services import apify_service, groq_service
from db.queries import ResearchQueries
from datetime import datetime, timezone


SYSTEM_PROMPT = """You are a competitive intelligence analyst for a startup founder.
Given scraped content from a competitor's website, extract:
- Key product features or updates
- Pricing changes
- New partnerships or integrations
- Hiring signals
- Strategic direction

Respond in JSON with keys: summary, key_points (list), sentiment (positive/neutral/negative), tags (list)."""


class CompetitorMonitorAgent(BaseAgent):
    agent_type = "competitor_monitor"

    async def execute(self, input_data: dict) -> dict:
        competitor_name = input_data.get("competitor_name", "")
        website = input_data.get("website", "")

        self._log(
            "info", f"Scraping competitor: {competitor_name}", {"website": website}
        )

        # Scrape the competitor website
        pages = await apify_service.scrape_website(website, max_pages=3)
        combined_text = "\n\n".join(p.get("text", "") for p in pages)[:8000]

        # Analyze with Groq
        analysis_raw = await groq_service.complete(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=f"Competitor: {competitor_name}\n\nContent:\n{combined_text}",
        )

        import json

        try:
            analysis = json.loads(analysis_raw)
        except json.JSONDecodeError:
            analysis = {
                "summary": analysis_raw,
                "key_points": [],
                "sentiment": "neutral",
                "tags": [],
            }

        # Persist finding
        finding = ResearchQueries.save_finding(
            {
                "source_url": website,
                "title": f"Competitor update: {competitor_name}",
                "summary": analysis.get("summary", ""),
                "sentiment": analysis.get("sentiment", "neutral"),
                "tags": analysis.get("tags", []),
                "found_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        return {
            "competitor": competitor_name,
            "finding_id": finding["id"],
            "analysis": analysis,
        }
