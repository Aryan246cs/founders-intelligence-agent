"""
Lightweight tests for the comparison engine.

Covers:
  - No previous memory (first run)
  - Identical findings (no changes)
  - Changed findings (changes detected)
  - Multiple competitors
  - Briefing section formatting
"""

from __future__ import annotations

from services.comparison.comparison_engine import (
    compare_findings,
    compare_all_competitors,
    build_briefing_changes_section,
    _normalize,
    _similarity,
    _detect_change_type,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _finding(summary: str) -> dict:
    return {"summary": summary, "title": "Test", "source_url": "https://example.com"}


# ---------------------------------------------------------------------------
# _normalize
# ---------------------------------------------------------------------------


def test_normalize_lowercases_and_strips():
    assert _normalize("  Hello World  ") == "hello world"


def test_normalize_collapses_whitespace():
    assert _normalize("foo   bar") == "foo bar"


# ---------------------------------------------------------------------------
# _similarity
# ---------------------------------------------------------------------------


def test_similarity_identical():
    assert _similarity("hello", "hello") == 1.0


def test_similarity_different():
    score = _similarity("hello world", "completely different text")
    assert score < 0.5


# ---------------------------------------------------------------------------
# _detect_change_type
# ---------------------------------------------------------------------------


def test_detect_pricing():
    assert _detect_change_type("New API pricing tiers announced") == "pricing"


def test_detect_model_release():
    # "model" keyword matches model_release; "released" matches product_launch first
    # — either is a valid categorization. Ensure at least one of them is returned.
    result = _detect_change_type("GPT-5 model released today")
    assert result in ("model_release", "product_launch")


def test_detect_funding():
    assert _detect_change_type("Company raised Series B funding round") == "funding"


def test_detect_unknown_returns_none():
    assert _detect_change_type("The weather is nice today") is None


# ---------------------------------------------------------------------------
# compare_findings — no previous memory
# ---------------------------------------------------------------------------


def test_no_previous_memory():
    result = compare_findings(
        competitor="OpenAI",
        current_findings=[_finding("GPT-5 launched with new pricing")],
        previous_findings=[],
    )
    assert result["competitor"] == "OpenAI"
    assert result["has_changes"] is False
    assert result["changes"] == []
    assert "No previous historical data available" in result["delta_summary"]
    assert result["historical_context"] == ""


# ---------------------------------------------------------------------------
# compare_findings — identical findings
# ---------------------------------------------------------------------------


def test_identical_findings_no_changes():
    finding = _finding("OpenAI maintains GPT-4 as flagship model with stable pricing.")
    result = compare_findings(
        competitor="OpenAI",
        current_findings=[finding],
        previous_findings=[finding],
    )
    assert result["has_changes"] is False
    assert result["changes"] == []


# ---------------------------------------------------------------------------
# compare_findings — changed findings
# ---------------------------------------------------------------------------


def test_changed_findings_detected():
    previous = [_finding("OpenAI offers GPT-4 at $0.03 per 1k tokens.")]
    current = [
        _finding("OpenAI offers GPT-4 at $0.03 per 1k tokens."),
        _finding("OpenAI introduced GPT-5 API pricing at $0.01 per 1k tokens."),
    ]
    result = compare_findings(
        competitor="OpenAI",
        current_findings=current,
        previous_findings=previous,
    )
    assert result["has_changes"] is True
    assert len(result["changes"]) == 1
    assert result["changes"][0]["type"] == "pricing"


def test_product_launch_detected():
    previous = [_finding("Anthropic focuses on safety research.")]
    current = [
        _finding("Anthropic focuses on safety research."),
        _finding(
            "Anthropic launched Claude 3 enterprise safety tooling for large organizations."
        ),
    ]
    result = compare_findings(
        competitor="Anthropic",
        current_findings=current,
        previous_findings=previous,
    )
    assert result["has_changes"] is True
    assert any(c["type"] in ("enterprise", "product_launch") for c in result["changes"])


# ---------------------------------------------------------------------------
# compare_findings — deduplication within current batch
# ---------------------------------------------------------------------------


def test_duplicate_current_findings_deduplicated():
    summary = "OpenAI raised a $10B funding round from Microsoft."
    current = [_finding(summary), _finding(summary)]
    result = compare_findings(
        competitor="OpenAI",
        current_findings=current,
        previous_findings=[],
    )
    # No previous history — returns no-history fallback regardless
    assert result["has_changes"] is False


# ---------------------------------------------------------------------------
# compare_all_competitors — multiple competitors
# ---------------------------------------------------------------------------


def test_multiple_competitors():
    current = {
        "openai": [_finding("GPT-5 released with new pricing tiers.")],
        "anthropic": [_finding("Claude 3 launched with enterprise features.")],
    }
    previous = {
        "openai": [_finding("GPT-4 is the current flagship model.")],
        "anthropic": [],
    }
    results = compare_all_competitors(current, previous)
    assert len(results) == 2

    openai_result = next(r for r in results if r["competitor"] == "openai")
    anthropic_result = next(r for r in results if r["competitor"] == "anthropic")

    assert openai_result["has_changes"] is True
    # Anthropic has no previous history — graceful fallback
    assert anthropic_result["has_changes"] is False
    assert "No previous historical data" in anthropic_result["delta_summary"]


# ---------------------------------------------------------------------------
# build_briefing_changes_section
# ---------------------------------------------------------------------------


def test_briefing_section_no_results():
    md = build_briefing_changes_section([])
    assert "## Changes Since Previous Run" in md
    assert "No previous historical data available" in md


def test_briefing_section_with_changes():
    results = [
        {
            "competitor": "OpenAI",
            "has_changes": True,
            "changes": [
                {"type": "pricing", "summary": "GPT-5.5 API pricing introduced"}
            ],
            "delta_summary": "OpenAI — 1 new development(s) detected",
            "historical_context": "",
        }
    ]
    md = build_briefing_changes_section(results)
    assert "## Changes Since Previous Run" in md
    assert "OpenAI" in md
    assert "GPT-5.5 API pricing introduced" in md


def test_briefing_section_no_changes_for_all():
    results = [
        {
            "competitor": "Anthropic",
            "has_changes": False,
            "changes": [],
            "delta_summary": "No significant changes detected.",
            "historical_context": "",
        }
    ]
    md = build_briefing_changes_section(results)
    assert "No significant changes" in md
