"""
StartupResearchAgent — autonomous founder research pipeline.

Given a startup idea (and optional name), this agent:
  1. Parses the idea → extracts industry, keywords, ICP, business model
  2. Builds targeted search queries
  3. Searches for competitors via Apify Google Search
  4. Scrapes competitor websites
  5. Collects pricing and positioning intelligence
  6. Generates a comprehensive structured report via Groq
  7. Persists to startup_research_reports table
  8. Saves key findings to memory
  9. Optionally sends a Slack summary
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent
from services import apify_service, groq_service, slack_service
from db.queries import StartupResearchQueries, MemoryQueries, ExecutionLogQueries
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

PARSE_IDEA_PROMPT = """You are a startup analyst. Given a startup idea, extract structured metadata.

Respond ONLY with valid JSON (no markdown, no explanation):
{
  "industry": "one concise industry label e.g. 'Voice AI', 'Legal Tech', 'HR Tech'",
  "keywords": ["3-6 search keywords relevant to this startup space"],
  "icp": "ideal customer profile in one sentence",
  "business_model": "e.g. SaaS, Marketplace, B2B, B2C, API",
  "competitor_search_queries": [
    "3-5 Google search queries to find direct competitors",
    "e.g. 'AI interview preparation platform competitors'",
    "e.g. 'best AI mock interview tools 2024'"
  ]
}"""

ANALYZE_COMPETITOR_PROMPT = """You are a competitive intelligence analyst. Given scraped website content about a company, extract structured intelligence.

Respond ONLY with valid JSON (no markdown):
{
  "name": "company name",
  "website": "website URL",
  "description": "1-2 sentence description of what they do",
  "business_focus": "their core value proposition in one sentence",
  "target_audience": "who they primarily serve",
  "market_positioning": "e.g. Enterprise-focused, Developer-focused, SMB-focused, Consumer-focused",
  "key_features": ["up to 5 notable product features or capabilities"],
  "pricing_model": "e.g. Freemium, Subscription, Usage-based, Enterprise",
  "pricing_tiers": [
    {"tier": "Free", "price": "$0/mo", "features": ["feature1"]},
    {"tier": "Pro", "price": "$X/mo", "features": ["feature1"]}
  ],
  "strengths": ["2-3 clear competitive strengths"],
  "source_url": "the primary URL scraped"
}

If pricing is not found, set pricing_tiers to [] and note in pricing_model.
Base ONLY on actual content found — never hallucinate."""

GENERATE_REPORT_PROMPT = """You are a strategic analyst for startup founders. Generate a comprehensive competitive research report.

You will receive:
- The founder's startup idea
- Analyzed competitor data
- Market context

Your report must be EVIDENCE-BASED. Every claim must reference something discovered, not generic advice.

NEVER write:
- "monitor competitors" — useless
- "focus on innovation" — useless  
- "prioritize AI" — useless

ALWAYS write specific, actionable insights tied to actual findings.

Respond ONLY with valid JSON (no markdown):
{
  "executive_summary": "3-4 sentence summary: what the startup is, what market it's entering, key market dynamics observed",
  "positioning_analysis": "2-3 paragraphs on how competitors position themselves, what narratives dominate, who controls what segments",
  "market_gaps": [
    "Specific gap identified: e.g. 'No competitor offers real-time AI coaching during practice sessions — all are async'"
  ],
  "differentiation_opportunities": [
    "Specific actionable opportunity: e.g. 'Build voice-first mobile experience — all competitors are desktop/web-only'"
  ],
  "swot": {
    "strengths": ["advantage of entering now vs incumbents based on observed gaps"],
    "weaknesses": ["realistic entry challenges given competitor moats"],
    "opportunities": ["specific market gaps from research"],
    "threats": ["specific competitive threats from analyzed companies"]
  },
  "founder_recommendations": [
    "Specific, evidence-based recommendation with reasoning"
  ]
}"""


# ---------------------------------------------------------------------------
# Research pipeline helpers
# ---------------------------------------------------------------------------


def _build_search_queries(idea: str, parsed: dict) -> List[str]:
    """Build a list of search queries for competitor discovery."""
    queries = list(parsed.get("competitor_search_queries", []))
    keywords = parsed.get("keywords", [])
    industry = parsed.get("industry", "")

    # Add fallback queries if fewer than 3
    if len(queries) < 3 and keywords:
        queries.append(f"{' '.join(keywords[:3])} startup competitors")
    if len(queries) < 3 and industry:
        queries.append(f"best {industry} tools alternatives")

    # Cap at 4 queries to keep the pipeline fast
    return queries[:4]


def _extract_urls_from_search(results: List[dict]) -> List[dict]:
    """Extract clean URL + title pairs from Apify Google search results."""
    seen_domains: set = set()
    urls = []
    skip_domains = {
        "reddit.com",
        "quora.com",
        "medium.com",
        "twitter.com",
        "linkedin.com",
        "facebook.com",
        "youtube.com",
        "github.com",
        "wikipedia.org",
        "g2.com",
        "capterra.com",
        "producthunt.com",
        "techcrunch.com",
        "crunchbase.com",
        "ycombinator.com",
    }
    for item in results:
        url = item.get("url", item.get("link", ""))
        title = item.get("title", "")
        if not url or not url.startswith("http"):
            continue
        # Extract domain
        try:
            domain = url.split("/")[2].replace("www.", "")
        except IndexError:
            continue
        if domain in skip_domains or domain in seen_domains:
            continue
        seen_domains.add(domain)
        urls.append({"url": url, "title": title, "domain": domain})
        if len(urls) >= 8:
            break
    return urls


def _scrape_text_from_pages(pages: List[dict]) -> str:
    """Concatenate scraped page text into a single context string (capped)."""
    parts = []
    for page in pages[:3]:
        text = page.get("text", page.get("markdown", ""))
        if text:
            parts.append(text[:2000])
    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class StartupResearchAgent(BaseAgent):
    agent_type = "startup_research"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        startup_idea: str = input_data.get("startup_idea", "")
        startup_name: str = input_data.get("startup_name", "")
        send_to_slack: bool = input_data.get("send_to_slack", False)

        if not startup_idea:
            raise ValueError("startup_idea is required")

        self._log("info", f"Research started: {startup_idea[:80]}")

        sources: List[dict] = []
        competitors: List[dict] = []

        # ----------------------------------------------------------------
        # Step 1: Parse startup idea
        # ----------------------------------------------------------------
        self._log("info", "Step 1: Understanding startup idea")
        parsed_raw = await groq_service.complete(
            system_prompt=PARSE_IDEA_PROMPT,
            user_prompt=f"Startup idea: {startup_idea}\nStartup name (if any): {startup_name}",
            max_tokens=800,
            temperature=0.2,
        )
        parsed = groq_service.parse_json_response(parsed_raw)
        industry = parsed.get("industry", "Technology")
        keywords = parsed.get("keywords", [])
        icp = parsed.get("icp", "")
        business_model = parsed.get("business_model", "SaaS")

        self._log(
            "info", f"Step 2: Industry identified as '{industry}', keywords: {keywords}"
        )

        # ----------------------------------------------------------------
        # Step 2-3: Search for competitors
        # ----------------------------------------------------------------
        self._log("info", "Step 3: Searching for competitors")
        search_queries = _build_search_queries(startup_idea, parsed)
        all_search_results: List[dict] = []
        for query in search_queries:
            try:
                results = await apify_service.search_google(query, max_results=8)
                all_search_results.extend(results)
            except Exception as e:
                self._log("warning", f"Search failed for '{query}': {e}")

        competitor_urls = _extract_urls_from_search(all_search_results)
        self._log("info", f"Found {len(competitor_urls)} potential competitor URLs")

        # ----------------------------------------------------------------
        # Step 3-5: Scrape and analyze competitor websites
        # ----------------------------------------------------------------
        self._log("info", "Step 4: Analyzing competitor websites")
        for url_info in competitor_urls[:6]:
            url = url_info["url"]
            domain = url_info["domain"]
            try:
                self._log("info", f"Scraping: {domain}")
                pages = await apify_service.scrape_website(url, max_pages=3)
                content = _scrape_text_from_pages(pages)
                if not content or len(content) < 100:
                    continue

                sources.append(
                    {
                        "name": url_info.get("title", domain),
                        "url": url,
                        "type": "Competitor website",
                    }
                )

                self._log(
                    "info", f"Step 5: Gathering pricing intelligence from {domain}"
                )
                analysis_raw = await groq_service.complete(
                    system_prompt=ANALYZE_COMPETITOR_PROMPT,
                    user_prompt=f"Website URL: {url}\n\nScraped content:\n{content[:4000]}",
                    max_tokens=1000,
                    temperature=0.1,
                )
                competitor = groq_service.parse_json_response(analysis_raw)
                competitor["source_url"] = url
                competitor["domain"] = domain

                # Enrich with pricing page if not found
                pricing_tiers = competitor.get("pricing_tiers", [])
                if not pricing_tiers:
                    pricing_url = f"https://{domain}/pricing"
                    try:
                        pricing_pages = await apify_service.scrape_website(
                            pricing_url, max_pages=1
                        )
                        pricing_content = _scrape_text_from_pages(pricing_pages)
                        if pricing_content and len(pricing_content) > 100:
                            sources.append(
                                {
                                    "name": f"{domain} Pricing",
                                    "url": pricing_url,
                                    "type": "Pricing page",
                                }
                            )
                            pricing_raw = await groq_service.complete(
                                system_prompt=ANALYZE_COMPETITOR_PROMPT,
                                user_prompt=f"Website URL: {pricing_url}\n\nPricing page content:\n{pricing_content[:3000]}",
                                max_tokens=600,
                                temperature=0.1,
                            )
                            pricing_data = groq_service.parse_json_response(pricing_raw)
                            if pricing_data.get("pricing_tiers"):
                                competitor["pricing_tiers"] = pricing_data[
                                    "pricing_tiers"
                                ]
                                competitor["pricing_model"] = pricing_data.get(
                                    "pricing_model", competitor.get("pricing_model", "")
                                )
                    except Exception:
                        pass  # pricing page optional

                competitors.append(competitor)

            except Exception as e:
                self._log("warning", f"Failed to analyze {domain}: {e}")
                continue

        self._log(
            "info", f"Step 6: Extracted positioning from {len(competitors)} competitors"
        )

        # ----------------------------------------------------------------
        # Step 4: Build feature comparison matrix
        # ----------------------------------------------------------------
        all_features: set = set()
        for comp in competitors:
            for f in comp.get("key_features", []):
                if isinstance(f, str) and len(f) > 3:
                    all_features.add(f.lower().strip())

        feature_comparison = []
        for feature in list(all_features)[:10]:
            row: dict = {"feature": feature.title(), "your_idea": "✓ Planned"}
            for comp in competitors:
                comp_features_lower = [
                    (f.lower() if isinstance(f, str) else "")
                    for f in comp.get("key_features", [])
                ]
                has_feature = any(
                    feature in cf or cf in feature for cf in comp_features_lower
                )
                name = comp.get("name", comp.get("domain", "Competitor"))
                row[name] = "✓" if has_feature else "—"
            feature_comparison.append(row)

        # ----------------------------------------------------------------
        # Step 5-6: Build pricing table
        # ----------------------------------------------------------------
        pricing_analysis = []
        for comp in competitors:
            name = comp.get("name", comp.get("domain", ""))
            tiers = comp.get("pricing_tiers", [])
            pricing_analysis.append(
                {
                    "competitor": name,
                    "model": comp.get("pricing_model", "Unknown"),
                    "tiers": tiers,
                }
            )

        # ----------------------------------------------------------------
        # Step 7: Generate strategic report via Groq
        # ----------------------------------------------------------------
        self._log("info", "Step 7: Generating strategic insights")
        competitor_context = json.dumps(
            [
                {
                    "name": c.get("name", ""),
                    "description": c.get("description", ""),
                    "target_audience": c.get("target_audience", ""),
                    "market_positioning": c.get("market_positioning", ""),
                    "key_features": c.get("key_features", []),
                    "pricing_model": c.get("pricing_model", ""),
                    "strengths": c.get("strengths", []),
                }
                for c in competitors[:6]
            ],
            indent=2,
        )

        strategic_raw = await groq_service.complete(
            system_prompt=GENERATE_REPORT_PROMPT,
            user_prompt=(
                f"Startup idea: {startup_idea}\n"
                f"Industry: {industry}\n"
                f"ICP: {icp}\n\n"
                f"Competitor data:\n{competitor_context}"
            ),
            max_tokens=2500,
            temperature=0.3,
        )
        strategic = groq_service.parse_json_response(strategic_raw)

        # ----------------------------------------------------------------
        # Step 8: Build final report
        # ----------------------------------------------------------------
        self._log("info", "Step 8: Building founder report")

        # Calculate a simple research score
        research_score = min(
            100,
            len(competitors) * 15
            + len(sources) * 5
            + (20 if strategic.get("market_gaps") else 0)
            + (10 if strategic.get("founder_recommendations") else 0),
        )

        report = {
            "startup_name": startup_name or None,
            "startup_idea": startup_idea,
            "industry": industry,
            "keywords": keywords,
            "icp": icp,
            "business_model": business_model,
            "executive_summary": strategic.get("executive_summary", ""),
            "competitors": competitors,
            "feature_comparison": feature_comparison,
            "pricing_analysis": pricing_analysis,
            "positioning_analysis": strategic.get("positioning_analysis", ""),
            "market_gaps": strategic.get("market_gaps", []),
            "differentiation": strategic.get("differentiation_opportunities", []),
            "swot": strategic.get("swot", {}),
            "founder_recommendations": strategic.get("founder_recommendations", []),
            "sources": sources,
            "competitors_found": len(competitors),
            "sources_analyzed": len(sources),
            "research_score": research_score,
            "sent_to_slack": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # ----------------------------------------------------------------
        # Step 9: Save to database + memory
        # ----------------------------------------------------------------
        self._log("info", "Step 9: Saving research to memory")
        saved = StartupResearchQueries.save(report)
        report_id = saved["id"]

        # Store in memory for future comparisons
        MemoryQueries.upsert(
            key=f"startup_research_{report_id}",
            namespace="startup_research",
            value={
                "idea": startup_idea,
                "industry": industry,
                "competitors": [c.get("name", "") for c in competitors],
                "gaps": strategic.get("market_gaps", []),
                "report_id": report_id,
            },
            tags=["startup_research", industry.lower()],
        )

        # ----------------------------------------------------------------
        # Step 10: Slack delivery
        # ----------------------------------------------------------------
        slack_sent = False
        if send_to_slack:
            self._log("info", "Sending research summary to Slack")
            slack_sent = await _send_research_to_slack(startup_idea, report, report_id)
            if slack_sent:
                StartupResearchQueries.mark_sent(report_id)

        self._log("info", f"Step 10: Research report complete — {report_id}")

        return {
            "report_id": report_id,
            "startup_idea": startup_idea,
            "industry": industry,
            "competitors_found": len(competitors),
            "sources_analyzed": len(sources),
            "research_score": research_score,
            "sent_to_slack": slack_sent,
            "skipped": False,
        }


# ---------------------------------------------------------------------------
# Slack formatter
# ---------------------------------------------------------------------------


async def _send_research_to_slack(
    startup_idea: str, report: dict, report_id: str
) -> bool:
    blocks: List[dict] = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🔬 Startup Research Report",
                "emoji": True,
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Idea:* {startup_idea}\n*Industry:* {report.get('industry', '')} | *Score:* {report.get('research_score', 0)}/100",
            },
        },
        {"type": "divider"},
    ]

    # Executive summary
    summary = report.get("executive_summary", "")
    if summary:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Executive Summary*\n{summary[:500]}",
                },
            }
        )
        blocks.append({"type": "divider"})

    # Top competitors
    competitors = report.get("competitors", [])[:4]
    if competitors:
        comp_text = "\n".join(
            f"• *{c.get('name', 'Unknown')}* — {c.get('description', '')[:120]}"
            for c in competitors
        )
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Top Competitors Found*\n{comp_text}",
                },
            }
        )
        blocks.append({"type": "divider"})

    # Market gaps (top 3)
    gaps = report.get("market_gaps", [])[:3]
    if gaps:
        gaps_text = "\n".join(f"• {g}" for g in gaps)
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Market Gaps*\n{gaps_text}"},
            }
        )
        blocks.append({"type": "divider"})

    # Top founder recommendation
    recs = report.get("founder_recommendations", [])
    if recs:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Founder Takeaway*\n_{recs[0]}_"},
            }
        )
        blocks.append({"type": "divider"})

    # Sources
    sources = report.get("sources", [])[:3]
    if sources:
        src_text = "\n".join(
            f"• <{s['url']}|{s['name']}> ({s['type']})" for s in sources
        )
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Verified Sources*\n{src_text}"},
            }
        )

    return await slack_service.send_message(
        text=f"Startup Research: {startup_idea[:60]}",
        blocks=blocks,
    )
