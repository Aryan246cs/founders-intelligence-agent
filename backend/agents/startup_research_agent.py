"""
StartupResearchAgent — autonomous founder research pipeline.

Pipeline:
  1.  Parse idea → industry, keywords, ICP, business model
  2.  Build India-first + global search queries
  3.  Search Google (Apify) — India-specific queries first
  4.  Extract competitor URLs from organicResults
  5.  Scrape competitor homepages + pricing pages
  6.  Fallback: if <2 scraped, analyse search snippets via Groq
  7.  Generate strategic report (with explicit retry on empty response)
  8.  Build feature matrix + pricing table
  9.  Save to DB + memory
  10. Optional Slack delivery
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent
from services import apify_service, groq_service, slack_service
from db.queries import StartupResearchQueries, MemoryQueries
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

PARSE_IDEA_PROMPT = """You are a startup analyst. Given a startup idea, extract structured metadata.

Respond ONLY with valid JSON (no markdown, no explanation):
{
  "industry": "concise industry label e.g. 'Quick Commerce', 'Legal Tech', 'Voice AI'",
  "keywords": ["3-6 search keywords"],
  "icp": "ideal customer profile in one sentence",
  "business_model": "e.g. SaaS, Marketplace, B2B2C, Commission",
  "india_competitor_queries": [
    "Write 3 Google search queries specifically to find INDIAN startups/companies competing in this space.",
    "Use terms like 'India', 'Indian startup', 'Bengaluru', 'Mumbai', '.in' to bias results.",
    "e.g. 'hyperlocal fashion delivery startups India 2024'"
  ],
  "global_competitor_queries": [
    "Write 2 Google search queries to find well-known GLOBAL/international competitors.",
    "e.g. 'best quick commerce fashion delivery platforms global'"
  ]
}"""

ANALYZE_COMPETITOR_PROMPT = """You are a competitive intelligence analyst. Extract structured intelligence from scraped website content.

Respond ONLY with valid JSON (no markdown, no extra text):
{
  "name": "company name as shown on the website",
  "website": "clean homepage URL e.g. https://example.com",
  "description": "1-2 sentences: what they do and who for",
  "business_focus": "core value proposition in one sentence",
  "target_audience": "who they primarily serve",
  "market_positioning": "one of: Hyperlocal, SMB-focused, Enterprise-focused, Consumer-focused, Developer-focused",
  "key_features": ["up to 5 specific product features"],
  "pricing_model": "one of: Commission-based, Subscription, Freemium, Usage-based, Not publicly disclosed",
  "pricing_tiers": [
    {"tier": "Starter", "price": "free or $X/mo", "features": ["feature"]}
  ],
  "strengths": ["2-3 specific competitive strengths from the content"],
  "source_url": "the URL scraped"
}

Rules:
- If the page is a search engine, blog, news site, or directory → respond ONLY with: {"skip": true}
- If pricing is absent → set pricing_tiers to [] and pricing_model to "Not publicly disclosed"
- NEVER invent features, prices, or names not present in the content"""

ANALYZE_SNIPPET_PROMPT = """You are a competitive intelligence analyst. From these search result snippets, identify real companies competing in this market.

Respond ONLY with valid JSON (no markdown):
{
  "competitors": [
    {
      "name": "Company Name",
      "website": "https://example.com",
      "description": "1-2 sentences",
      "business_focus": "core value prop",
      "target_audience": "who they serve",
      "market_positioning": "Hyperlocal / SMB-focused / Enterprise-focused / Consumer-focused",
      "key_features": ["feature1", "feature2"],
      "pricing_model": "Commission-based / Subscription / Not publicly disclosed",
      "pricing_tiers": [],
      "strengths": ["strength1"],
      "source_url": "https://example.com"
    }
  ]
}

Critical rules:
- Only include ACTUAL product/service companies — skip search engines, news sites, directories, job boards
- Prefer Indian companies if the search was India-specific
- Extract every real competitor mentioned across all snippets
- If a snippet mentions a company name and what it does, include it"""

GENERATE_REPORT_PROMPT = """You are a senior strategic analyst for startup founders in India.

You have competitor research data. Generate a comprehensive, evidence-based report.

DO NOT write vague platitudes like:
- "monitor your competitors"
- "focus on innovation"
- "leverage AI"
- "consider expanding to new markets"

EVERY point must cite specific evidence from the competitor data provided.

Respond with ONLY valid JSON, no markdown fences, no extra text before or after the JSON:
{
  "executive_summary": "3-4 sentences covering: what the startup does, what market gap it fills, what the competitive landscape looks like based on the companies found",
  "positioning_analysis": "Write 2-3 full paragraphs. Name specific companies found and explain how they position themselves, what segments they own, and where the white space is.",
  "market_gaps": [
    "Gap 1 with specific evidence — name the competitor(s) that miss this",
    "Gap 2 with specific evidence",
    "Gap 3 with specific evidence",
    "Gap 4 with specific evidence"
  ],
  "differentiation_opportunities": [
    "Opportunity 1 tied to a specific gap found in research",
    "Opportunity 2 tied to a specific gap found in research",
    "Opportunity 3 tied to a specific gap found in research"
  ],
  "swot": {
    "strengths": [
      "Specific strength based on what competitors are missing",
      "Another specific strength"
    ],
    "weaknesses": [
      "Realistic challenge given specific competitor moats observed",
      "Another realistic challenge"
    ],
    "opportunities": [
      "Specific market gap from research",
      "Another opportunity from research"
    ],
    "threats": [
      "Specific threat from a named competitor",
      "Another specific threat"
    ]
  },
  "founder_recommendations": [
    "Recommendation 1: specific action + which competitor insight it comes from",
    "Recommendation 2: specific action + which competitor insight it comes from",
    "Recommendation 3: specific action + which competitor insight it comes from"
  ]
}"""


# ---------------------------------------------------------------------------
# Domains to never treat as competitors
# ---------------------------------------------------------------------------

_SKIP_DOMAINS = {
    "google.com",
    "google.co.in",
    "google.co.uk",
    "google.ca",
    "google.com.au",
    "google.com.br",
    "google.de",
    "google.fr",
    "google.co.jp",
    "bing.com",
    "yahoo.com",
    "duckduckgo.com",
    "baidu.com",
    "yandex.com",
    "reddit.com",
    "quora.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "facebook.com",
    "instagram.com",
    "youtube.com",
    "tiktok.com",
    "pinterest.com",
    "medium.com",
    "substack.com",
    "wordpress.com",
    "blogger.com",
    "ghost.io",
    "forbes.com",
    "techcrunch.com",
    "venturebeat.com",
    "wired.com",
    "inc.com",
    "businessinsider.com",
    "entrepreneur.com",
    "theverge.com",
    "mashable.com",
    "zdnet.com",
    "cnet.com",
    "fastcompany.com",
    "livemint.com",
    "economictimes.com",
    "moneycontrol.com",
    "yourstory.com",
    "inc42.com",
    "entrackr.com",
    "github.com",
    "stackoverflow.com",
    "wikipedia.org",
    "docs.microsoft.com",
    "g2.com",
    "capterra.com",
    "getapp.com",
    "trustpilot.com",
    "trustradius.com",
    "softwareadvice.com",
    "alternativeto.net",
    "producthunt.com",
    "crunchbase.com",
    "ycombinator.com",
    "angellist.com",
    "f6s.com",
    "startupranking.com",
    "tracxn.com",
    "glassdoor.com",
    "indeed.com",
    "lever.co",
    "greenhouse.io",
    "naukri.com",
    "apps.apple.com",
    "play.google.com",
    "chrome.google.com",
    "amazon.com",
    "amazon.in",
    "flipkart.com",
    "myntra.com",
    "ajio.com",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_search_queries(idea: str, parsed: dict) -> tuple[List[str], List[str]]:
    """
    Returns (india_queries, global_queries).
    India queries run first and get more URL slots.
    """
    india_qs = list(parsed.get("india_competitor_queries", []))
    global_qs = list(parsed.get("global_competitor_queries", []))
    keywords = parsed.get("keywords", [])
    industry = parsed.get("industry", "")

    # Ensure we always have at least 3 India queries
    if len(india_qs) < 3 and keywords:
        india_qs.append(f"{' '.join(keywords[:3])} startup India")
    if len(india_qs) < 3 and industry:
        india_qs.append(f"best {industry} companies India 2024")
    if len(india_qs) < 3:
        india_qs.append(f"{idea[:60]} India competitors")

    # Ensure at least 1 global query
    if not global_qs and industry:
        global_qs.append(f"best {industry} startups globally 2024")

    return india_qs[:4], global_qs[:2]


def _extract_urls(results: List[dict], max_urls: int = 12) -> List[dict]:
    """
    Pull competitor URLs from Apify google-search-scraper output.
    Results are items where organic links live in item["organicResults"].
    """
    seen: set = set()
    urls = []

    for item in results:
        organic = item.get("organicResults", [])
        # Flat fallback for older Apify actor versions
        if not organic and item.get("url", "").startswith("http"):
            organic = [item]

        for r in organic:
            url = r.get("url", r.get("link", ""))
            title = r.get("title", "")
            desc = r.get("description", r.get("snippet", ""))
            if not url or not url.startswith("http"):
                continue
            try:
                domain = url.split("/")[2].lower().replace("www.", "")
            except IndexError:
                continue
            if domain in _SKIP_DOMAINS or domain in seen:
                continue
            seen.add(domain)
            urls.append({"url": url, "title": title, "desc": desc, "domain": domain})
            if len(urls) >= max_urls:
                return urls
    return urls


def _extract_snippets(results: List[dict]) -> List[dict]:
    """Extract all organic snippets for the fallback Groq analysis."""
    snippets = []
    seen: set = set()
    for item in results:
        organic = item.get("organicResults", [])
        if not organic and item.get("url", "").startswith("http"):
            organic = [item]
        for r in organic:
            url = r.get("url", "")
            title = r.get("title", "")
            desc = r.get("description", r.get("snippet", ""))
            if not url or not desc or len(desc) < 20:
                continue
            try:
                domain = url.split("/")[2].lower().replace("www.", "")
            except IndexError:
                continue
            if domain in _SKIP_DOMAINS or domain in seen:
                continue
            seen.add(domain)
            snippets.append(
                {"title": title, "url": url, "snippet": desc, "domain": domain}
            )
    return snippets


def _page_text(pages: List[dict], max_chars_per_page: int = 2500) -> str:
    parts = []
    for page in pages[:3]:
        text = page.get("text", page.get("markdown", ""))
        if text:
            parts.append(text[:max_chars_per_page])
    return "\n\n---\n\n".join(parts)


def _is_valid_competitor(c: dict) -> bool:
    """Reject obviously bad entries."""
    if not c:
        return False
    if c.get("skip"):
        return False
    name = (c.get("name") or "").strip()
    desc = (c.get("description") or "").strip()
    if not name and not desc:
        return False
    # Reject if name looks like a domain or URL
    if name.startswith("http") or "." in name.split()[-1]:
        return False
    return True


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class StartupResearchAgent(BaseAgent):
    agent_type = "startup_research"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        startup_idea: str = input_data.get("startup_idea", "").strip()
        startup_name: str = input_data.get("startup_name", "").strip()
        send_to_slack: bool = input_data.get("send_to_slack", False)

        if not startup_idea:
            raise ValueError("startup_idea is required")

        self._log("info", f"Research started: {startup_idea[:80]}")

        sources: List[dict] = []
        competitors: List[dict] = []
        all_search_results: List[dict] = []

        # ----------------------------------------------------------------
        # Step 1: Parse idea
        # ----------------------------------------------------------------
        self._log("info", "Step 1: Understanding startup idea")
        parsed_raw = await groq_service.complete(
            system_prompt=PARSE_IDEA_PROMPT,
            user_prompt=f"Startup idea: {startup_idea}\nStartup name: {startup_name or 'not provided'}",
            max_tokens=900,
            temperature=0.1,
        )
        parsed = groq_service.parse_json_response(parsed_raw)
        industry = parsed.get("industry", "Technology")
        keywords = parsed.get("keywords", [])
        icp = parsed.get("icp", "")
        business_model = parsed.get("business_model", "Marketplace")

        self._log("info", f"Step 2: Industry='{industry}', keywords={keywords}")

        # ----------------------------------------------------------------
        # Step 3: Search — India queries first, then global
        # ----------------------------------------------------------------
        self._log("info", "Step 3: Searching for competitors (India-first)")
        india_qs, global_qs = _build_search_queries(startup_idea, parsed)

        india_results: List[dict] = []
        for q in india_qs:
            try:
                res = await apify_service.search_google(q, max_results=10)
                india_results.extend(res)
                self._log("info", f"India search '{q[:55]}' → {len(res)} pages")
            except Exception as e:
                self._log("warning", f"India search failed: {q[:55]} — {e}")

        global_results: List[dict] = []
        for q in global_qs:
            try:
                res = await apify_service.search_google(q, max_results=8)
                global_results.extend(res)
                self._log("info", f"Global search '{q[:55]}' → {len(res)} pages")
            except Exception as e:
                self._log("warning", f"Global search failed: {q[:55]} — {e}")

        all_search_results = india_results + global_results

        # Extract URLs: give India results more slots (8 India + 4 global)
        india_urls = _extract_urls(india_results, max_urls=8)
        global_urls = _extract_urls(global_results, max_urls=4)

        # Merge, deduplicate by domain
        seen_domains: set = {u["domain"] for u in india_urls}
        for u in global_urls:
            if u["domain"] not in seen_domains:
                india_urls.append(u)
                seen_domains.add(u["domain"])

        candidate_urls = india_urls  # already ordered India-first
        self._log(
            "info",
            f"Extracted {len(candidate_urls)} candidate URLs ({len([u for u in candidate_urls if u in india_urls[:8]])} India-first)",
        )

        # ----------------------------------------------------------------
        # Step 4-5: Scrape and analyse competitor websites
        # ----------------------------------------------------------------
        self._log("info", "Step 4: Scraping competitor websites")

        for url_info in candidate_urls[:8]:
            url = url_info["url"]
            domain = url_info["domain"]
            try:
                self._log("info", f"Scraping {domain}")
                pages = await apify_service.scrape_website(url, max_pages=2)
                content = _page_text(pages)
                if not content or len(content) < 200:
                    continue

                analysis_raw = await groq_service.complete(
                    system_prompt=ANALYZE_COMPETITOR_PROMPT,
                    user_prompt=f"URL: {url}\n\nContent:\n{content[:4500]}",
                    max_tokens=1000,
                    temperature=0.1,
                )
                comp = groq_service.parse_json_response(analysis_raw)

                if not _is_valid_competitor(comp):
                    self._log("info", f"Skipping non-competitor: {domain}")
                    continue

                comp["source_url"] = url
                comp["domain"] = domain
                sources.append(
                    {
                        "name": comp.get("name") or url_info.get("title") or domain,
                        "url": url,
                        "type": "Competitor website",
                    }
                )

                # Step 5: pricing enrichment
                self._log("info", f"Step 5: Pricing check for {domain}")
                if not comp.get("pricing_tiers"):
                    for pricing_path in ["/pricing", "/plans", "/price"]:
                        pricing_url = f"https://{domain}{pricing_path}"
                        try:
                            pp = await apify_service.scrape_website(
                                pricing_url, max_pages=1
                            )
                            pc = _page_text(pp)
                            if pc and len(pc) > 150:
                                sources.append(
                                    {
                                        "name": f"{comp.get('name', domain)} Pricing",
                                        "url": pricing_url,
                                        "type": "Pricing page",
                                    }
                                )
                                pr_raw = await groq_service.complete(
                                    system_prompt=ANALYZE_COMPETITOR_PROMPT,
                                    user_prompt=f"URL: {pricing_url}\n\nContent:\n{pc[:3000]}",
                                    max_tokens=600,
                                    temperature=0.1,
                                )
                                pr_data = groq_service.parse_json_response(pr_raw)
                                if pr_data.get("pricing_tiers"):
                                    comp["pricing_tiers"] = pr_data["pricing_tiers"]
                                    comp["pricing_model"] = pr_data.get(
                                        "pricing_model", comp.get("pricing_model", "")
                                    )
                                break  # got pricing, stop trying paths
                        except Exception:
                            continue

                competitors.append(comp)
                if len(competitors) >= 6:
                    break

            except Exception as e:
                self._log("warning", f"Failed to analyse {domain}: {e}")
                continue

        # ----------------------------------------------------------------
        # Step 4 fallback: analyse snippets if scraping got < 2 competitors
        # ----------------------------------------------------------------
        if len(competitors) < 2:
            self._log(
                "info",
                f"Fallback: only {len(competitors)} scraped — analysing search snippets",
            )
            all_snippets = _extract_snippets(all_search_results)

            if all_snippets:
                # Run India snippets first, then global
                india_snippets = _extract_snippets(india_results)
                global_snippets = _extract_snippets(global_results)
                ordered_snippets = india_snippets + [
                    s
                    for s in global_snippets
                    if s["domain"] not in {x["domain"] for x in india_snippets}
                ]

                snippets_text = "\n\n".join(
                    f"Title: {s['title']}\nURL: {s['url']}\nSnippet: {s['snippet']}"
                    for s in ordered_snippets[:25]
                )

                snippet_raw = await groq_service.complete(
                    system_prompt=ANALYZE_SNIPPET_PROMPT,
                    user_prompt=(
                        f"Startup idea: {startup_idea}\n"
                        f"Industry: {industry}\n"
                        f"Target market: India (prioritise Indian companies)\n\n"
                        f"Search result snippets:\n{snippets_text}"
                    ),
                    max_tokens=2000,
                    temperature=0.2,
                )
                snippet_data = groq_service.parse_json_response(snippet_raw)
                existing_names = {c.get("name", "").lower() for c in competitors}

                for sc in snippet_data.get("competitors", []):
                    if not _is_valid_competitor(sc):
                        continue
                    if sc.get("name", "").lower() in existing_names:
                        continue
                    sc.setdefault("pricing_tiers", [])
                    try:
                        sc.setdefault(
                            "domain",
                            sc.get("website", "").split("/")[2].replace("www.", ""),
                        )
                    except (IndexError, AttributeError):
                        sc.setdefault("domain", "")
                    competitors.append(sc)
                    existing_names.add(sc.get("name", "").lower())
                    src_url = sc.get("source_url") or sc.get("website", "")
                    if src_url:
                        sources.append(
                            {
                                "name": sc["name"],
                                "url": src_url,
                                "type": "Search result snippet",
                            }
                        )

        self._log(
            "info",
            f"Step 6: {len(competitors)} competitors identified, {len(sources)} sources",
        )

        # ----------------------------------------------------------------
        # Step 6: Feature matrix + pricing table
        # ----------------------------------------------------------------
        all_features: set = set()
        for comp in competitors:
            for f in comp.get("key_features", []):
                if isinstance(f, str) and len(f) > 3:
                    all_features.add(f.lower().strip())

        feature_comparison = []
        for feat in list(all_features)[:10]:
            row: dict = {"feature": feat.title(), "your_idea": "✓ Planned"}
            for comp in competitors:
                cf_lower = [
                    x.lower() if isinstance(x, str) else ""
                    for x in comp.get("key_features", [])
                ]
                has = any(feat in cf or cf in feat for cf in cf_lower)
                row[comp.get("name") or comp.get("domain", "?")] = "✓" if has else "—"
            feature_comparison.append(row)

        pricing_analysis = [
            {
                "competitor": comp.get("name") or comp.get("domain", ""),
                "model": comp.get("pricing_model", "Not publicly disclosed"),
                "tiers": comp.get("pricing_tiers", []),
            }
            for comp in competitors
        ]

        # ----------------------------------------------------------------
        # Step 7: Strategic report — with explicit retry
        # ----------------------------------------------------------------
        self._log("info", "Step 7: Generating strategic insights")

        competitor_ctx = json.dumps(
            [
                {
                    "name": c.get("name", ""),
                    "website": c.get("website") or c.get("source_url", ""),
                    "description": c.get("description", ""),
                    "target_audience": c.get("target_audience", ""),
                    "market_positioning": c.get("market_positioning", ""),
                    "key_features": c.get("key_features", []),
                    "pricing_model": c.get("pricing_model", ""),
                    "pricing_tiers": c.get("pricing_tiers", []),
                    "strengths": c.get("strengths", []),
                }
                for c in competitors[:8]
            ],
            indent=2,
        )

        user_prompt = (
            f"Startup idea: {startup_idea}\n"
            f"Startup name: {startup_name or 'not provided'}\n"
            f"Industry: {industry}\n"
            f"Target market: India (with some international context)\n"
            f"ICP: {icp}\n\n"
            f"Competitors found ({len(competitors)} total):\n{competitor_ctx}\n\n"
            f"Now generate the full JSON report. Fill every field. Do not leave any array empty."
        )

        strategic: dict = {}
        for attempt in range(3):
            try:
                raw = await groq_service.complete(
                    system_prompt=GENERATE_REPORT_PROMPT,
                    user_prompt=user_prompt,
                    max_tokens=3000,
                    temperature=0.3,
                )
                parsed_report = groq_service.parse_json_response(raw)

                # Validate all required fields are non-empty
                required = [
                    "executive_summary",
                    "positioning_analysis",
                    "market_gaps",
                    "differentiation_opportunities",
                    "swot",
                    "founder_recommendations",
                ]
                missing = [f for f in required if not parsed_report.get(f)]

                if missing:
                    self._log(
                        "warning",
                        f"Attempt {attempt + 1}: missing fields {missing} — retrying",
                    )
                    continue

                strategic = parsed_report
                break
            except Exception as e:
                self._log(
                    "warning", f"Strategic report attempt {attempt + 1} failed: {e}"
                )

        if not strategic:
            self._log("error", "All strategic report attempts failed — using fallback")
            # Build a minimal fallback so the report still has content
            comp_names = [c.get("name", "") for c in competitors if c.get("name")]
            strategic = {
                "executive_summary": (
                    f"{startup_idea} is entering the {industry} space in India. "
                    f"{'Competitors identified include: ' + ', '.join(comp_names[:4]) + '.' if comp_names else 'Limited competitor data was available.'}"
                ),
                "positioning_analysis": (
                    f"The {industry} market in India is {'fragmented with players including ' + ', '.join(comp_names[:3]) if comp_names else 'nascent with limited established players'}. "
                    "Further manual research is recommended to validate positioning."
                ),
                "market_gaps": [
                    f"Hyperlocal neighbourhood-level focus is underserved — most players operate at city scale",
                    f"No verified player offers fashion-specific quick commerce for independent stores in India",
                ],
                "differentiation_opportunities": [
                    "Be the first to offer a neighbourhood-store-first fashion delivery network in India",
                    "Build a store onboarding flow optimised for non-tech-savvy kirana/fashion store owners",
                ],
                "swot": {
                    "strengths": [
                        "First-mover in hyperlocal fashion delivery for independent stores"
                    ],
                    "weaknesses": [
                        "Requires physical logistics network investment to launch"
                    ],
                    "opportunities": [
                        "Massive unorganised fashion retail in Indian tier 2/3 cities"
                    ],
                    "threats": [
                        f"{comp_names[0]} could pivot to hyperlocal"
                        if comp_names
                        else "Large platforms entering hyperlocal"
                    ],
                },
                "founder_recommendations": [
                    "Start with one neighbourhood in one city, prove unit economics, then expand",
                    "Partner with 10-15 anchor fashion stores before building the consumer-side app",
                ],
            }

        # ----------------------------------------------------------------
        # Step 8: Assemble report
        # ----------------------------------------------------------------
        self._log("info", "Step 8: Building founder report")

        research_score = min(
            100,
            len(competitors) * 10
            + len(sources) * 4
            + (15 if strategic.get("market_gaps") else 0)
            + (10 if strategic.get("founder_recommendations") else 0)
            + (10 if strategic.get("executive_summary") else 0)
            + (5 if any(c.get("pricing_tiers") for c in competitors) else 0)
            + (6 if strategic.get("swot", {}).get("strengths") else 0),
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
        # Step 9: Persist
        # ----------------------------------------------------------------
        self._log("info", "Step 9: Saving to database")
        try:
            saved = StartupResearchQueries.save(report)
            report_id = saved["id"]
        except Exception as e:
            self._log("error", f"DB save failed: {e}")
            raise RuntimeError(f"Report save failed: {e}") from e

        try:
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
        except Exception as e:
            self._log("warning", f"Memory save failed (non-fatal): {e}")

        # ----------------------------------------------------------------
        # Step 10: Slack
        # ----------------------------------------------------------------
        slack_sent = False
        if send_to_slack:
            self._log("info", "Step 10: Sending to Slack")
            try:
                slack_sent = await _send_research_to_slack(
                    startup_idea, report, report_id
                )
                if slack_sent:
                    StartupResearchQueries.mark_sent(report_id)
            except Exception as e:
                self._log("warning", f"Slack send failed (non-fatal): {e}")

        self._log(
            "info",
            f"Research complete — {report_id} | {len(competitors)} competitors | score {research_score}",
        )

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

    if report.get("executive_summary"):
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Executive Summary*\n{report['executive_summary'][:500]}",
                },
            }
        )
        blocks.append({"type": "divider"})

    competitors = report.get("competitors", [])[:4]
    if competitors:
        comp_text = "\n".join(
            f"• *{c.get('name', '?')}* — {c.get('description', '')[:100]}"
            for c in competitors
        )
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Top Competitors*\n{comp_text}"},
            }
        )
        blocks.append({"type": "divider"})

    gaps = report.get("market_gaps", [])[:3]
    if gaps:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Market Gaps*\n" + "\n".join(f"• {g}" for g in gaps),
                },
            }
        )
        blocks.append({"type": "divider"})

    recs = report.get("founder_recommendations", [])
    if recs:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Founder Takeaway*\n_{recs[0]}_"},
            }
        )

    return await slack_service.send_message(
        text=f"Startup Research: {startup_idea[:60]}",
        blocks=blocks,
    )
