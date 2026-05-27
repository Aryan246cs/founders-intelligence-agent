from __future__ import annotations

from datetime import datetime, timezone
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
    _is_low_signal_text,
)
from services.memory.retrieval import get_previous_findings_for_competitor
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# System prompt — sharp, no filler
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an autonomous competitive intelligence analyst for a startup founder.

Your job: synthesize ONLY the high-signal strategic changes provided into a concise, founder-grade briefing.

STRICT RULES:
- Only write about what is explicitly in the provided findings. Do NOT invent or extrapolate.
- Do NOT include generic AI industry commentary.
- Do NOT repeat "focus on safety", "AI transparency", "monitor developments" or similar filler.
- Do NOT pad with background context the founder already knows.
- Every sentence must contain a specific company name, product name, number, or named event.
- Strategic Insight must identify a directional market shift, not restate the findings.
- Founder Takeaway must be a specific, actionable decision — not generic advice.

OUTPUT FORMAT (Markdown, exactly this structure):
# Founder Intelligence Briefing — {date}

## Key Developments
(3-5 bullet points, each naming a specific company + specific action + specific implication)

## Strategic Intelligence
(2-3 sentences identifying the directional market shift these developments signal)

## Founder Takeaway
(1-2 sentences: what specific decision or action this intelligence should trigger)

If the findings do not contain enough specific, high-signal information to fill this template honestly: respond with exactly: INSUFFICIENT_SIGNAL"""

# ---------------------------------------------------------------------------
# Briefing deduplication
# ---------------------------------------------------------------------------

BRIEFING_SIMILARITY_THRESHOLD = 0.68


def _briefing_similarity(a: str, b: str) -> float:
    """Compare two briefing texts for semantic similarity."""
    # Use first 1500 chars — the executive content, not boilerplate
    return SequenceMatcher(None, a[:1500].lower(), b[:1500].lower()).ratio()


def _is_duplicate_briefing(new_markdown: str, recent_briefings: List[dict]) -> bool:
    """Return True if new briefing is too similar to a recent one."""
    for b in recent_briefings[:5]:
        existing = b.get("raw_markdown", "")
        if not existing:
            continue
        sim = _briefing_similarity(new_markdown, existing)
        if sim >= BRIEFING_SIMILARITY_THRESHOLD:
            logger.info(
                "Briefing too similar to recent — suppressing",
                similarity=round(sim, 3),
            )
            return True
    return False


# ---------------------------------------------------------------------------
# Finding filtering
# ---------------------------------------------------------------------------


def _filter_high_signal_findings(findings: List[dict]) -> List[dict]:
    """Remove low-signal findings before passing to LLM."""
    filtered = []
    for f in findings:
        summary = f.get("summary", "")
        title = f.get("title", "")
        # Skip if summary is too short or generic
        if _is_low_signal_text(summary):
            continue
        # Skip if tagged with suppressed entities only
        tags = f.get("tags", [])
        non_suppressed_tags = [
            t
            for t in tags
            if t not in ("research", "competitor") and not _is_suppressed_entity(t)
        ]
        if tags and not non_suppressed_tags:
            continue
        filtered.append(f)
    return filtered


def _extract_competitors_from_findings(findings: List[dict]) -> List[str]:
    """Derive deduplicated competitor names from finding tags."""
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
                ):
                    seen.add(tag)
                    competitors.append(tag)
    return competitors


def _build_changes_section(findings: List[dict]) -> tuple[str, bool]:
    """
    Build the strategic changes section.
    Returns (markdown_section, has_high_signal_changes).
    """
    competitors = _extract_competitors_from_findings(findings)

    if not competitors:
        logger.info("No competitor tags in findings — skipping comparison")
        return "", False

    comparison_results = []
    for competitor in competitors:
        current = [f for f in findings if competitor in f.get("tags", [])]
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
        time_range_days = input_data.get("time_range_days", 7)
        send_to_slack = input_data.get("send_to_slack", False)
        force = input_data.get("force", False)  # bypass signal gate if True

        self._log("info", "Starting briefing pipeline")

        # 1. Fetch and filter findings
        raw_findings = ResearchQueries.list_recent(limit=30)
        findings = _filter_high_signal_findings(raw_findings)

        self._log(
            "info",
            f"Findings filtered: {len(raw_findings)} raw → {len(findings)} high-signal",
        )

        if not findings and not force:
            self._log("info", "No high-signal findings — skipping briefing generation")
            return {
                "briefing_id": None,
                "title": None,
                "markdown": None,
                "sent_to_slack": False,
                "skipped": True,
                "reason": "No high-signal findings available",
            }

        # 2. Build strategic changes section
        self._log("info", "Running strategic comparison")
        try:
            changes_section, has_signal = _build_changes_section(findings)
        except Exception as exc:
            logger.error("Comparison failed", error=str(exc))
            changes_section, has_signal = "", False

        if not has_signal and not force:
            self._log(
                "info",
                "No high-signal strategic changes detected — skipping briefing",
            )
            return {
                "briefing_id": None,
                "title": None,
                "markdown": None,
                "sent_to_slack": False,
                "skipped": True,
                "reason": "No high-signal strategic changes detected",
            }

        # 3. Build findings text for LLM — only high-signal content
        findings_text = "\n\n".join(
            f"[{f.get('title', 'Finding')}] {f['summary']}" for f in findings[:15]
        )

        if changes_section:
            findings_text = (
                f"{changes_section}\n\n---\n\nAdditional findings:\n{findings_text}"
            )

        today = datetime.now(timezone.utc).strftime("%B %d, %Y")

        # 4. Generate briefing via LLM
        self._log("info", "Generating briefing via LLM")
        briefing_md = await groq_service.complete(
            system_prompt=SYSTEM_PROMPT.replace("{date}", today),
            user_prompt=f"High-signal findings for briefing:\n\n{findings_text}",
            max_tokens=1200,
            temperature=0.2,
        )

        # 5. Gate on LLM signal check
        if "INSUFFICIENT_SIGNAL" in briefing_md:
            self._log("info", "LLM determined insufficient signal — skipping briefing")
            return {
                "briefing_id": None,
                "title": None,
                "markdown": None,
                "sent_to_slack": False,
                "skipped": True,
                "reason": "LLM: insufficient signal for a quality briefing",
            }

        # 6. Deduplication check against recent briefings
        if not force:
            recent = BriefingQueries.list_recent(limit=5)
            if _is_duplicate_briefing(briefing_md, recent):
                self._log(
                    "info", "Briefing too similar to recent — suppressing duplicate"
                )
                return {
                    "briefing_id": None,
                    "title": None,
                    "markdown": None,
                    "sent_to_slack": False,
                    "skipped": True,
                    "reason": "Duplicate briefing suppressed — no new intelligence",
                }

        # 7. Save
        title = f"Founder Briefing — {today}"
        saved = BriefingQueries.save(
            {
                "title": title,
                "sections": [],
                "raw_markdown": briefing_md,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "sent_to_slack": False,
            }
        )

        # 8. Slack delivery
        slack_sent = False
        if send_to_slack:
            slack_sent = await slack_service.send_briefing(
                title=title,
                markdown=briefing_md,
            )
            if slack_sent:
                BriefingQueries.mark_sent(saved["id"])

        self._log("info", f"Briefing saved: {saved['id']}")

        return {
            "briefing_id": saved["id"],
            "title": title,
            "markdown": briefing_md,
            "sent_to_slack": slack_sent,
            "skipped": False,
        }
