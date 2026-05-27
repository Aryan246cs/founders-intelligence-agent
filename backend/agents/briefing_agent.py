from __future__ import annotations

from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent
from services import groq_service, slack_service
from db.queries import ResearchQueries, BriefingQueries
from services.comparison.comparison_engine import (
    compare_findings,
    build_briefing_changes_section,
    has_any_high_signal_changes,
    _is_suppressed_entity,
)
from services.memory.retrieval import get_previous_findings_for_competitor
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an autonomous competitive intelligence analyst for a startup founder.

You will receive research findings about SPECIFIC companies. Your job is to synthesize them into a concise, founder-grade briefing about ONLY those companies.

STRICT RULES:
- Write ONLY about the companies mentioned in the findings provided. Do not bring in other companies.
- Be specific: name exact products, features, numbers, pricing, partnerships.
- Do NOT write generic industry commentary.
- Do NOT mention companies not present in the findings.
- Strategic Intelligence must identify a specific competitive dynamic between the companies in the findings.
- Founder Takeaway must be a specific action relevant to the domain in the findings.

OUTPUT FORMAT (use exactly these headings and bullet style):
# Founder Intelligence Briefing — {date}
## Topic: {topic}

## Key Developments
- [Company name]: [specific action or data point and its implication]
- [Company name]: [specific action or data point and its implication]
(3-5 bullets maximum)

## Strategic Intelligence
[2-3 sentences on the competitive dynamic between these specific companies]

## Founder Takeaway
[1-2 sentences: specific action this intelligence should trigger]"""

# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

BRIEFING_SIMILARITY_THRESHOLD = 0.75


def _briefing_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a[:1500].lower(), b[:1500].lower()).ratio()


def _is_duplicate_briefing(new_markdown: str, recent_briefings: List[dict]) -> bool:
    for b in recent_briefings[:3]:
        existing = b.get("raw_markdown", "")
        if not existing:
            continue
        sim = _briefing_similarity(new_markdown, existing)
        if sim >= BRIEFING_SIMILARITY_THRESHOLD:
            logger.info("Briefing duplicate suppressed", similarity=round(sim, 3))
            return True
    return False


# ---------------------------------------------------------------------------
# Finding helpers
# ---------------------------------------------------------------------------


def _get_findings_for_workflow(
    competitor_names: List[str],
    time_range_minutes: int = 30,
    limit: int = 40,
) -> List[dict]:
    """
    Fetch findings saved in the last N minutes for specific competitors.
    This ensures the briefing only uses findings from THIS workflow run,
    not stale findings from previous runs about different topics.
    """
    from db.client import get_supabase

    db = get_supabase()

    cutoff = (
        datetime.now(timezone.utc) - timedelta(minutes=time_range_minutes)
    ).isoformat()

    # Fetch recent findings
    res = (
        db.table("research_findings")
        .select("*")
        .gte("found_at", cutoff)
        .order("found_at", desc=True)
        .limit(limit)
        .execute()
    )
    findings = res.data or []

    # If we have competitor names, filter to only those competitors
    if competitor_names and findings:
        names_lower = [n.lower() for n in competitor_names]
        filtered = []
        for f in findings:
            tags = [t.lower() for t in f.get("tags", [])]
            title_lower = f.get("title", "").lower()
            summary_lower = f.get("summary", "").lower()
            # Include if any competitor name appears in tags, title, or summary
            if any(
                name in tags or name in title_lower or name in summary_lower
                for name in names_lower
            ):
                filtered.append(f)
        if filtered:
            return filtered

    # Fallback: return all recent findings if filtering left nothing
    return findings


def _extract_topic_from_request(request: str) -> str:
    """Extract a short topic label from the user's request."""
    request_lower = request.lower()
    # Common domain keywords
    domains = [
        "quick commerce",
        "food delivery",
        "fintech",
        "edtech",
        "healthtech",
        "saas",
        "ai",
        "crypto",
        "ecommerce",
        "logistics",
        "mobility",
        "proptech",
        "insurtech",
        "legaltech",
        "hrtech",
        "martech",
    ]
    for domain in domains:
        if domain in request_lower:
            return domain.title()
    # Fall back to first 60 chars of request
    return request[:60].strip()


def _extract_competitor_names_from_request(request: str) -> List[str]:
    """
    Extract competitor names from the workflow request string.
    The planner passes these via input_data, but we also parse the request
    as a fallback.
    """
    # Common patterns: "Monitor X, Y and Z", "Monitor X and Y"
    import re

    # Remove common filler words
    cleaned = re.sub(
        r"\b(monitor|research|analyze|track|generate|briefing|brief|and|a|the|on|for|about|trends|founder\'?s?)\b",
        " ",
        request,
        flags=re.IGNORECASE,
    )
    # Split on commas and spaces, filter short/empty tokens
    tokens = [t.strip().strip(",") for t in re.split(r"[,\s]+", cleaned)]
    names = [t for t in tokens if len(t) > 2 and t[0].isupper()]
    return names


def _extract_competitors_from_findings(findings: List[dict]) -> List[str]:
    """Derive competitor names from finding tags."""
    competitors: List[str] = []
    seen: set = set()
    for f in findings:
        tags: List[str] = f.get("tags", [])
        if "competitor" in tags:
            for tag in tags:
                if (
                    tag not in ("competitor", "research")
                    and tag not in seen
                    and not _is_suppressed_entity(tag)
                    and len(tag) > 2
                ):
                    seen.add(tag)
                    competitors.append(tag)
    return competitors


def _build_changes_section(findings: List[dict]) -> tuple[str, bool]:
    """Build strategic changes section. Returns (markdown, has_signal)."""
    competitors = _extract_competitors_from_findings(findings)
    if not competitors:
        return "", False

    comparison_results = []
    for competitor in competitors:
        current = [
            f for f in findings if competitor in [t.lower() for t in f.get("tags", [])]
        ]
        previous = get_previous_findings_for_competitor(competitor, limit=10)
        result = compare_findings(
            competitor=competitor,
            current_findings=current,
            previous_findings=previous,
        )
        if not result.get("suppressed"):
            comparison_results.append(result)

    has_signal = has_any_high_signal_changes(comparison_results)
    section = build_briefing_changes_section(comparison_results)
    return section, has_signal


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class BriefingAgent(BaseAgent):
    agent_type = "briefing"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        send_to_slack = input_data.get("send_to_slack", False)
        force = input_data.get("force", False)
        auto = input_data.get("auto", False)
        # Competitor names passed from the planner/orchestrator
        competitor_names: List[str] = input_data.get("competitor_names", [])
        # Original request for topic extraction
        original_request: str = input_data.get("original_request", "")
        # How far back to look for findings (default 30 min = this workflow run)
        lookback_minutes: int = input_data.get("lookback_minutes", 30)

        self._log("info", "Starting briefing pipeline")

        # 1. Fetch findings scoped to this workflow run's competitors
        findings = _get_findings_for_workflow(
            competitor_names=competitor_names,
            time_range_minutes=lookback_minutes,
            limit=40,
        )

        self._log(
            "info",
            f"Findings fetched: {len(findings)} for competitors: {competitor_names}",
        )

        if not findings:
            self._log("info", "No findings for this workflow run")
            return {
                "briefing_id": None,
                "title": None,
                "markdown": None,
                "sent_to_slack": False,
                "skipped": True,
                "reason": "No research findings found. Competitor monitoring may have failed.",
            }

        # 2. Build comparison section (context only, not a gate on manual runs)
        try:
            changes_section, has_signal = _build_changes_section(findings)
        except Exception as exc:
            logger.error("Comparison failed — continuing", error=str(exc))
            changes_section, has_signal = "", False

        # 3. Signal gate — only for automated scheduled runs
        if auto and not force and not has_signal:
            self._log("info", "Automated run: no high-signal changes — skipping")
            return {
                "briefing_id": None,
                "title": None,
                "markdown": None,
                "sent_to_slack": False,
                "skipped": True,
                "reason": "No high-signal strategic changes detected since last run.",
            }

        # 4. Build findings text — ONLY the findings from this run
        findings_text = "\n\n".join(
            f"- [{f.get('title', 'Finding')}]: {f['summary']}"
            for f in findings[:20]
            if f.get("summary") and len(f["summary"].strip()) > 30
        )

        if not findings_text.strip():
            self._log("info", "All findings too short to use")
            return {
                "briefing_id": None,
                "title": None,
                "markdown": None,
                "sent_to_slack": False,
                "skipped": True,
                "reason": "Findings were too short to generate a quality briefing.",
            }

        if changes_section:
            findings_text = f"{changes_section}\n\n---\n\n{findings_text}"

        # 5. Derive topic and title
        topic = (
            _extract_topic_from_request(original_request)
            if original_request
            else (
                ", ".join(competitor_names[:3])
                if competitor_names
                else "Competitive Intelligence"
            )
        )
        today = datetime.now(timezone.utc).strftime("%B %d, %Y")
        title = f"{topic} Intelligence — {today}"

        # 6. Generate via LLM
        self._log("info", f"Generating briefing: {title}")
        briefing_md = await groq_service.complete(
            system_prompt=SYSTEM_PROMPT.replace("{date}", today).replace(
                "{topic}", topic
            ),
            user_prompt=(
                f"Generate a briefing about: {topic}\n\n"
                f"Research findings (ONLY use these companies and facts):\n\n{findings_text}"
            ),
            max_tokens=1400,
            temperature=0.2,
        )

        # 7. Dedup check
        if not force:
            recent = BriefingQueries.list_recent(limit=3)
            if _is_duplicate_briefing(briefing_md, recent):
                self._log("info", "Duplicate briefing suppressed")
                return {
                    "briefing_id": None,
                    "title": None,
                    "markdown": None,
                    "sent_to_slack": False,
                    "skipped": True,
                    "reason": "Duplicate briefing suppressed — no new intelligence.",
                }

        # 8. Save
        saved = BriefingQueries.save(
            {
                "title": title,
                "sections": [],
                "raw_markdown": briefing_md,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "sent_to_slack": False,
            }
        )

        # 9. Slack
        slack_sent = False
        if send_to_slack:
            slack_sent = await slack_service.send_briefing(
                title=title,
                markdown=briefing_md,
            )
            if slack_sent:
                BriefingQueries.mark_sent(saved["id"])

        self._log("info", f"Briefing saved: {saved['id']} — {title}")

        return {
            "briefing_id": saved["id"],
            "title": title,
            "markdown": briefing_md,
            "sent_to_slack": slack_sent,
            "skipped": False,
        }
