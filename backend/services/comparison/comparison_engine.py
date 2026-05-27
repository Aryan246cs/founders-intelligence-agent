"""
Comparison engine — detects MEANINGFUL strategic changes between competitor findings.

Design principles:
  - Suppress low-signal entities (AI, chatbots, safety, transparency, etc.)
  - Only surface high-signal strategic movements
  - Require minimum text length and specificity before flagging a change
  - Deduplicate aggressively (similarity threshold 0.72 — tighter than before)
  - Categorize by strategic impact, not generic keywords
  - Never emit "no significant changes" noise into briefings
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Entities that produce zero-value comparisons — always suppressed
# ---------------------------------------------------------------------------

SUPPRESSED_ENTITIES = {
    "ai",
    "artificial intelligence",
    "chatbot",
    "chatbots",
    "machine learning",
    "deep learning",
    "neural network",
    "nlp",
    "natural language processing",
    "transparency",
    "safety",
    "responsible ai",
    "ai safety",
    "ethics",
    "customer service",
    "automation",
    "productivity",
    "efficiency",
    "innovation",
    "technology",
    "software",
    "platform",
    "solution",
    "digital transformation",
    "cloud",
    "data",
    "analytics",
}

# ---------------------------------------------------------------------------
# High-signal change categories — only these matter
# ---------------------------------------------------------------------------

HIGH_SIGNAL_CATEGORIES: Dict[str, List[str]] = {
    "pricing_change": [
        "pricing",
        "price cut",
        "price increase",
        "per token",
        "per seat",
        "enterprise plan",
        "free tier",
        "api pricing",
        "cost reduction",
        "subscription",
        "billing",
        "rate limit",
        "usage limit",
    ],
    "enterprise_expansion": [
        "enterprise",
        "soc 2",
        "iso 27001",
        "hipaa",
        "gdpr compliance",
        "on-premise",
        "private cloud",
        "dedicated instance",
        "audit log",
        "role-based access",
        "sso",
        "saml",
        "governance",
        "data residency",
    ],
    "product_launch": [
        "launched",
        "released",
        "shipped",
        "now available",
        "general availability",
        "ga release",
        "introducing",
        "new product",
        "new capability",
        "new feature",
        "beta launch",
        "early access",
    ],
    "model_release": [
        "gpt-",
        "claude ",
        "gemini ",
        "llama ",
        "mistral ",
        "codestral",
        "new model",
        "model release",
        "context window",
        "benchmark",
        "outperforms",
        "state of the art",
        "sota",
        "multimodal",
    ],
    "infrastructure_move": [
        "inference",
        "latency",
        "throughput",
        "tokens per second",
        "custom silicon",
        "tpu",
        "gpu cluster",
        "dedicated hardware",
        "edge deployment",
        "on-device",
        "inference optimization",
        "distillation",
        "quantization",
    ],
    "partnership_deal": [
        "partnership",
        "signed deal",
        "enterprise agreement",
        "integration with",
        "acquired",
        "acquisition",
        "merger",
        "joint venture",
        "strategic alliance",
        "distribution agreement",
        "oem",
        "reseller",
    ],
    "funding_event": [
        "raised",
        "series a",
        "series b",
        "series c",
        "seed round",
        "valuation",
        "ipo",
        "spac",
        "funding round",
        "investment",
        "venture capital",
        "lead investor",
    ],
    "developer_ecosystem": [
        "open source",
        "open-source",
        "github",
        "sdk release",
        "api v",
        "developer platform",
        "plugin",
        "marketplace",
        "extension",
        "developer adoption",
        "community growth",
        "npm downloads",
    ],
    "competitive_positioning": [
        "market share",
        "displacing",
        "replacing",
        "competing with",
        "alternative to",
        "beats",
        "surpasses",
        "outperforms",
        "positioning against",
        "direct competitor",
    ],
    "go_to_market": [
        "sales team",
        "channel partner",
        "reseller",
        "distribution",
        "enterprise sales",
        "direct sales",
        "self-serve",
        "product-led",
        "go-to-market",
        "gtm",
        "land and expand",
    ],
}

# Minimum character length for a finding to be worth comparing
MIN_FINDING_LENGTH = 80

# Similarity above this = duplicate, skip
SIMILARITY_THRESHOLD = 0.72

# A change must match at least one high-signal category to be included
REQUIRE_HIGH_SIGNAL = True


# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _is_duplicate(text: str, seen: List[str]) -> bool:
    norm = _normalize(text)
    for s in seen:
        if _similarity(norm, s) >= SIMILARITY_THRESHOLD:
            return True
    return False


def _is_suppressed_entity(competitor: str) -> bool:
    """Return True if this competitor name is a generic/suppressed entity."""
    return _normalize(competitor) in SUPPRESSED_ENTITIES


def _is_low_signal_text(text: str) -> bool:
    """Return True if the text is too short or too generic to be useful."""
    if len(text.strip()) < MIN_FINDING_LENGTH:
        return True
    norm = _normalize(text)
    # Generic filler phrases that add no intelligence value
    filler_patterns = [
        r"^(ai|chatbot|machine learning|nlp)\b.{0,60}$",
        r"no significant change",
        r"continues to focus on",
        r"remains committed to",
        r"ongoing efforts",
        r"as previously noted",
        r"similar to last",
    ]
    for pattern in filler_patterns:
        if re.search(pattern, norm):
            return True
    return False


# ---------------------------------------------------------------------------
# Change detection
# ---------------------------------------------------------------------------


def _detect_change_type(text: str) -> Optional[str]:
    """Return the highest-signal category for a piece of text, or None."""
    norm = _normalize(text)
    for category, keywords in HIGH_SIGNAL_CATEGORIES.items():
        for kw in keywords:
            if kw in norm:
                return category
    return None


def _extract_new_content(
    current_texts: List[str],
    previous_texts: List[str],
) -> List[str]:
    """
    Return items from current_texts that are:
    1. Not near-duplicates of previous content
    2. Not near-duplicates of each other
    3. Long enough to be meaningful
    4. Not generic filler
    """
    prev_normalized = [_normalize(t) for t in previous_texts if t.strip()]
    new_items: List[str] = []
    seen_new: List[str] = []

    for text in current_texts:
        if not text or _is_low_signal_text(text):
            continue
        norm = _normalize(text)
        if _is_duplicate(norm, prev_normalized):
            continue
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
    Only returns has_changes=True when genuinely high-signal changes exist.
    """
    # Suppress generic/useless entities entirely
    if _is_suppressed_entity(competitor):
        logger.info("Suppressed generic entity", competitor=competitor)
        return {
            "competitor": competitor,
            "has_changes": False,
            "changes": [],
            "delta_summary": "",
            "historical_context": "",
            "suppressed": True,
        }

    logger.info(
        "Running comparison",
        competitor=competitor,
        current_count=len(current_findings),
        previous_count=len(previous_findings),
    )

    if not previous_findings:
        logger.info(
            "No previous findings — skipping delta detection", competitor=competitor
        )
        return {
            "competitor": competitor,
            "has_changes": False,
            "changes": [],
            "delta_summary": "",
            "historical_context": "",
        }

    current_texts = [
        f.get("summary", "")
        for f in current_findings
        if f.get("summary") and not _is_low_signal_text(f.get("summary", ""))
    ]
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
            "delta_summary": "",
            "historical_context": _build_historical_context(previous_findings),
        }

    # Only keep changes that match a high-signal category
    changes: List[Dict[str, str]] = []
    for text in new_content:
        change_type = _detect_change_type(text)
        if REQUIRE_HIGH_SIGNAL and change_type is None:
            logger.info(
                "Skipping low-signal change", competitor=competitor, text=text[:80]
            )
            continue
        changes.append(
            {
                "type": change_type or "strategic_shift",
                "summary": text[:400],
            }
        )

    if not changes:
        logger.info("All changes were low-signal — suppressing", competitor=competitor)
        return {
            "competitor": competitor,
            "has_changes": False,
            "changes": [],
            "delta_summary": "",
            "historical_context": _build_historical_context(previous_findings),
        }

    logger.info(
        "High-signal changes detected", competitor=competitor, count=len(changes)
    )

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
    results = []
    for competitor, current in current_findings_by_competitor.items():
        previous = previous_findings_by_competitor.get(competitor, [])
        result = compare_findings(competitor, current, previous)
        # Only include non-suppressed results
        if not result.get("suppressed"):
            results.append(result)
    return results


def has_any_high_signal_changes(comparison_results: List[Dict[str, Any]]) -> bool:
    """Return True if at least one competitor has real strategic changes."""
    return any(r.get("has_changes") for r in comparison_results)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _build_delta_summary(competitor: str, changes: List[Dict[str, str]]) -> str:
    if not changes:
        return ""
    lines = [f"{competitor} — {len(changes)} strategic development(s):"]
    for c in changes:
        label = c["type"].replace("_", " ").title()
        lines.append(f"  [{label}] {c['summary'][:200]}")
    return "\n".join(lines)


def _build_historical_context(previous_findings: List[Dict[str, Any]]) -> str:
    if not previous_findings:
        return ""
    snippets = [
        f.get("summary", "")[:150]
        for f in previous_findings[:3]
        if f.get("summary") and len(f.get("summary", "")) > 40
    ]
    return " | ".join(snippets)


def build_briefing_changes_section(comparison_results: List[Dict[str, Any]]) -> str:
    """
    Format only high-signal comparison results into a Markdown section.
    Completely omits competitors with no changes — no filler lines.
    """
    high_signal = [r for r in comparison_results if r.get("has_changes")]

    if not high_signal:
        return ""  # Return empty — caller decides whether to proceed

    lines = ["## Strategic Intelligence Changes\n"]
    for result in high_signal:
        competitor = result.get("competitor", "Unknown")
        changes = result.get("changes", [])
        lines.append(f"**{competitor}**:")
        for change in changes:
            label = change["type"].replace("_", " ").title()
            lines.append(f"- [{label}] {change['summary'][:250]}")
        lines.append("")

    return "\n".join(lines)
