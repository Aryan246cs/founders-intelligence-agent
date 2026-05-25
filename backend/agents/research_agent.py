from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from agents.base import BaseAgent
from services import apify_service, groq_service
from db.queries import ResearchQueries

SYSTEM_PROMPT = """You are a startup research analyst. Given search results about AI companies and market trends,
produce a structured research summary.

Respond ONLY with valid JSON (no markdown, no explanation) with these exact keys:
{
  "summary": "2-3 sentence overall summary",
  "findings": [{"title": "...", "insight": "...", "source_url": "..."}],
  "trends": ["trend1", "trend2"],
  "opportunities": ["opportunity1", "opportunity2"]
}"""


class ResearchAgent(BaseAgent):
    agent_type = "research"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get("query", "AI startup trends")
        max_results = input_data.get("max_results", 10)

        self._log("info", f"Researching: {query}")

        # Search via Apify
        search_results = await apify_service.search_google(
            query, max_results=max_results
        )

        snippets = "\n\n".join(
            f"Title: {r.get('title', '')}\nURL: {r.get('url', r.get('link', ''))}\nSnippet: {r.get('description', r.get('snippet', ''))}"
            for r in search_results[:10]
        )

        if not snippets.strip():
            snippets = f"No search results found for query: {query}"

        # Analyze with Groq
        analysis_raw = await groq_service.complete(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=f"Query: {query}\n\nSearch Results:\n{snippets}",
        )

        analysis = groq_service.parse_json_response(analysis_raw)

        # Ensure expected keys exist
        analysis.setdefault("summary", analysis_raw[:500])
        analysis.setdefault("findings", [])
        analysis.setdefault("trends", [])
        analysis.setdefault("opportunities", [])

        # Persist findings to Supabase
        saved_ids = []
        for f in analysis["findings"]:
            if not isinstance(f, dict):
                continue
            finding = ResearchQueries.save_finding(
                {
                    "source_url": f.get("source_url", ""),
                    "title": f.get("title", "Research finding"),
                    "summary": f.get("insight", ""),
                    "tags": ["research", query[:50]],
                    "found_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            saved_ids.append(finding["id"])

        self._log("info", f"Research complete — {len(saved_ids)} findings saved")

        return {
            "query": query,
            "analysis": analysis,
            "saved_finding_ids": saved_ids,
        }
