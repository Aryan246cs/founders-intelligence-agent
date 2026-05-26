"""
Comparison engine for detecting meaningful changes between competitor findings.

Strategy:
  1. Normalize and deduplicate text.
  2. Keyword-group detection for known change categories.
  3. Fuzzy similarity to filter out near-duplicate content.
  4. Only invoke LLM summarization AFTER structured deltas are identified.

Output schema:
  {
    "competitor": str,
    "has_changes": bool,
    "changes": [{"type": str, "summary": str}],
    "delta_summary": str,
    "historical_context": str,
  }
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Change category keyword groups
# ---------------------------------------------------------------------------

CHANGE_CATEGORIES: Dict[str, List[str]] = {
    "product_launch": [
        "launch",
        "released",
        "introducing",
        "new product",
        "new feature",
        "now available",
        "general availability",
        "ga release",
        "shipped",
    ],
    "pricing": [
        "pricing",
        "price",
        "cost",
        "subscription",
        "tier",
        "plan",
        "free tier",
        "enterprise plan",
        "per seat",
        "per token",
        "api pricing",
    ],
    "model_release": [
        "model",
        "gpt",
        "claude",
        "gemini",
        "llm",
        "foundation model",
        "fine-tuned",
        "checkpoint",
        "weights",
        "benchmark",
        "parameter",
    ],
    "positioning": [
        "positioning",
        "messaging",
        "rebrand",
        "tagline",
        "mission",
        "vision",
        "strategy",
        "pivot",
        "focus",
        "narrative",
    ],
    "partnership": [
        "partner",
        "partnership",
        "integration",
        "collaboration",
        "alliance",
        "joint",
        "ecosystem",
        "marketplace",
    ],
    "acquisition": [
        "acqui",
        "acquired",
        "acquisition",
        "merger",
        "bought",
        "takeover",
        "deal closed",
    ],
    "funding": [
        "funding",
        "raised",
        "series",
        "seed",
        "round",
        "valuation",
        "investment",
        "investor",
        "venture",
        "ipo",
    ],
    "enterprise": [
        "enterprise",
        "soc 2",
        "compliance",
        "sla",
        "dedicated",
        "on-premise",
        "private cloud",
        "audit",
        "governance",
    ],
    "api_change": [
        "api",
        "sdk",
        "endpoint",
        "rate limit",
        "deprecat",
        "v2",
        "v3",
        "breaking change",
        "migration guide",
        "changelog",
    ],
}

# Similarity threshold below which two texts are considered different enough to flag
SIMILARITY_THRESHOLD = 0.85


# ---------------------------------------------------------------------------
# Text normalization helpers
# ---------------------------------------------------------------------------


def _normalize(text: str) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _similarity(a: str, b: str) -> float:
    """Return a 0–1 similarity ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()


def _is_duplicate(
    text: str, seen: List[str], threshold: float = SIMILARITY_THRESHOLD
) -> bool:
    """Return True if text is too similar to any already-seen string."""
    norm = _normalize(text)
    for s in seen:
        if _similarity(norm, s) >= threshold:
            return True
    return False


# ---------------------------------------------------------------------------
# Change detection
# ---------------------------------------------------------------------------


def _detect_change_type(text: str) -> Optional[str]:
    """
    Return the first matching change category for a piece of text, or None.
    """
    norm = _normalize(text)
    for category, keywords in CHANGE_CATEGORIES.items():
        for kw in keywords:
            if kw in norm:
                return category
    return None


def _extract_new_content(
    current_texts: List[str], previous_texts: List[str]
) -> List[str]:
    """
    Return items from current_texts that are not near-duplicates of anything
    in previous_texts.
    """
    prev_normalized = [_normalize(t) for t in previous_texts]
    new_items: List[str] = []
    seen_new: List[str] = []

    for text in current_texts:
        norm = _normalize(text)
        # Skip if it's a near-duplicate of previous content
        if _is_duplicate(norm, prev_normalized):
            continue
        # Skip if it's a near-duplicate of another new item (dedup within batch)
        if _is_duplicate(norm, seen_new):
            continue
        new_items.append(text)
        seen_new.append(norm)

    return new_items


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compare_findings(
    competitor: str,
    current_findings: List[Dict[str, Any]],
    previous_findings: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compare current competitor findings against previous ones.

    Args:
        competitor: Competitor name (used only for labeling output).
        current_findings: List of finding dicts with at least a 'summary' key.
        previous_findings: List of previous finding dicts with at least a 'summary' key.

    Returns:
        Comparison result dict matching the standard output schema.
    """
    logger.info(
        "Running comparison",
        competitor=competitor,
        current_count=len(current_findings),
        previous_count=len(previous_findings),
    )

    # Graceful fallback when no history exists
    if not previous_findings:
        logger.info(
            "No previous findings — skipping delta detection", competitor=competitor
        )
        return {
            "competitor": competitor,
            "has_changes": False,
            "changes": [],
            "delta_summary": "No previous historical data available.",
            "historical_context": "",
        }

    current_texts = [f.get("summary", "") for f in current_findings if f.get("summary")]
    previous_texts = [
        f.get("summary", "") for f in previous_findings if f.get("summary")
    ]

    new_content = _extract_new_content(current_texts, previous_texts)

    if not new_content:
        logger.info("No meaningful changes detected", competitor=competitor)
        return {
            "competitor": competitor,
            "has_changes": False,
            "changes": [],
            "delta_summary": "No significant changes detected since the previous run.",
            "historical_context": _build_historical_context(previous_findings),
        }

    # Categorize each new piece of content
    changes: List[Dict[str, str]] = []
    for text in new_content:
        change_type = _detect_change_type(text) or "general"
        changes.append({"type": change_type, "summary": text[:300]})

    logger.info("Changes detected", competitor=competitor, count=len(changes))

    return {
        "competitor": competitor,
        "has_changes": True,
        "changes": changes,
        "delta_summary": _build_delta_summary(competitor, changes),
        "historical_context": _build_historical_context(previous_findings),
    }


def compare_all_competitors(
    current_findings_by_competitor: Dict[str, List[Dict[str, Any]]],
    previous_findings_by_competitor: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Run comparison for every competitor in the current batch.

    Args:
        current_findings_by_competitor: {competitor_name: [finding, ...]}
        previous_findings_by_competitor: {competitor_name: [finding, ...]}

    Returns:
        List of comparison result dicts, one per competitor.
    """
    results = []
    for competitor, current in current_findings_by_competitor.items():
        previous = previous_findings_by_competitor.get(competitor, [])
        result = compare_findings(competitor, current, previous)
        results.append(result)
    return results


# ---------------------------------------------------------------------------
# Formatting helpers (no LLM — pure string construction)
# ---------------------------------------------------------------------------


def _build_delta_summary(competitor: str, changes: List[Dict[str, str]]) -> str:
    """Build a concise plain-text delta summary from detected changes."""
    if not changes:
        return f"No significant changes detected for {competitor}."

    lines = [f"{competitor} — {len(changes)} new development(s) detected:"]
    for c in changes:
        category_label = c["type"].replace("_", " ").title()
        lines.append(f"  [{category_label}] {c['summary'][:200]}")
    return "\n".join(lines)


def _build_historical_context(previous_findings: List[Dict[str, Any]]) -> str:
    """Summarize previous findings into a short historical context string."""
    if not previous_findings:
        return ""
    snippets = [
        f.get("summary", "")[:150] for f in previous_findings[:3] if f.get("summary")
    ]
    return " | ".join(snippets)


def build_briefing_changes_section(comparison_results: List[Dict[str, Any]]) -> str:
    """
    Format comparison results into a Markdown section for the founder briefing.

    Args:
        comparison_results: List of comparison result dicts from compare_findings().

    Returns:
        Markdown string for the "Changes Since Previous Run" section.
    """
    if not comparison_results:
        return (
            "## Changes Since Previous Run\n\nNo previous historical data available.\n"
        )

    lines = ["## Changes Since Previous Run\n"]
    any_changes = False

    for result in comparison_results:
        competitor = result.get("competitor", "Unknown")
        has_changes = result.get("has_changes", False)
        changes = result.get("changes", [])

        if not has_changes:
            lines.append(f"**{competitor}**: No significant changes since last run.\n")
            continue

        any_changes = True
        lines.append(f"**{competitor}**:\n")
        for change in changes:
            category_label = change["type"].replace("_", " ").title()
            lines.append(f"- [{category_label}] {change['summary'][:200]}")
        lines.append("")

    if not any_changes:
        lines.append(
            "\n_No meaningful changes detected across monitored competitors._\n"
        )

    return "\n".join(lines)
