from agents.base import BaseAgent
from services import apify_service, groq_service
from db.queries import ResearchQueries
from datetime import datetime, timezone


SYSTEM_PROMPT = """You are a startup research analyst. Given search results about AI companies and market trends,
produce a structured research summary.

Respond in JSON with keys:
- summary: overall summary (2-3 sentences)
- findings: list of objects with {title, insight, source_url}
- trends: list of key trends identified
- opportunities: list of potential opportunities for a founder"""


class ResearchAgent(BaseAgent):
    agent_type = "research"

    async def execute(self, input_data: dict) -> dict:
        query = input_data.get("query", "AI startup trends")
        max_results = input_data.get("max_results", 10)

        self._log("info", f"Researching: {query}")

        # Search via Apify
        search_results = await apify_service.search_google(
            query, max_results=max_results
        )
        snippets = "\n\n".join(
            f"Title: {r.get('title', '')}\nURL: {r.get('url', '')}\nSnippet: {r.get('description', '')}"
            for r in search_results[:10]
        )

        # Analyze with Groq
        analysis_raw = await groq_service.complete(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=f"Query: {query}\n\nSearch Results:\n{snippets}",
        )

        import json

        try:
            analysis = json.loads(analysis_raw)
        except json.JSONDecodeError:
            analysis = {
                "summary": analysis_raw,
                "findings": [],
                "trends": [],
                "opportunities": [],
            }

        # Persist findings
        saved = []
        for f in analysis.get("findings", []):
            finding = ResearchQueries.save_finding(
                {
                    "source_url": f.get("source_url", ""),
                    "title": f.get("title", "Research finding"),
                    "summary": f.get("insight", ""),
                    "tags": ["research", query],
                    "found_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            saved.append(finding["id"])

        return {
            "query": query,
            "analysis": analysis,
            "saved_finding_ids": saved,
        }
