"""
Tests for the comparison engine.

Updated to match the high-signal-only engine behavior:
  - Suppressed entities return has_changes=False with suppressed=True
  - Low-signal text is filtered out
  - build_briefing_changes_section returns "" when no high-signal changes
  - Category names updated to match HIGH_SIGNAL_CATEGORIES
"""

from __future__ import annotations

from services.comparison.comparison_engine import (
    compare_findings,
    compare_all_competitors,
    build_briefing_changes_section,
    has_any_high_signal_changes,
    _normalize,
    _similarity,
    _detect_change_type,
    _is_suppressed_entity,
    _is_low_signal_text,
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
# _is_suppressed_entity
# ---------------------------------------------------------------------------


def test_suppressed_entities():
    assert _is_suppressed_entity("ai") is True
    assert _is_suppressed_entity("chatbots") is True
    assert _is_suppressed_entity("transparency") is True
    assert _is_suppressed_entity("OpenAI") is False
    assert _is_suppressed_entity("Anthropic") is False


# ---------------------------------------------------------------------------
# _is_low_signal_text
# ---------------------------------------------------------------------------


def test_low_signal_short_text():
    assert _is_low_signal_text("AI is improving.") is True


def test_low_signal_filler():
    assert _is_low_signal_text("no significant changes detected in this area") is True


def test_high_signal_text():
    text = "Anthropic launched enterprise-grade Claude security tooling with SOC 2 Type II compliance for regulated industries."
    assert _is_low_signal_text(text) is False


# ---------------------------------------------------------------------------
# _detect_change_type
# ---------------------------------------------------------------------------


def test_detect_pricing():
    result = _detect_change_type(
        "New API pricing tiers announced for enterprise customers"
    )
    assert result == "pricing_change"


def test_detect_model_release():
    result = _detect_change_type(
        "GPT-5 model released with 128k context window and new benchmark results"
    )
    assert result in ("model_release", "product_launch")


def test_detect_funding():
    result = _detect_change_type(
        "Company raised Series B funding round at $2B valuation"
    )
    assert result == "funding_event"


def test_detect_enterprise():
    result = _detect_change_type(
        "Anthropic achieved SOC 2 Type II compliance for enterprise customers"
    )
    assert result == "enterprise_expansion"


def test_detect_unknown_returns_none():
    assert _detect_change_type("The weather is nice today") is None


# ---------------------------------------------------------------------------
# compare_findings — suppressed entity
# ---------------------------------------------------------------------------


def test_suppressed_entity_returns_no_changes():
    result = compare_findings(
        competitor="ai",
        current_findings=[_finding("AI is advancing rapidly across all sectors.")],
        previous_findings=[_finding("AI was advancing last year too.")],
    )
    assert result["has_changes"] is False
    assert result.get("suppressed") is True


# ---------------------------------------------------------------------------
# compare_findings — no previous memory
# ---------------------------------------------------------------------------


def test_no_previous_memory():
    result = compare_findings(
        competitor="OpenAI",
        current_findings=[
            _finding("GPT-5 launched with new enterprise pricing tiers.")
        ],
        previous_findings=[],
    )
    assert result["competitor"] == "OpenAI"
    assert result["has_changes"] is False
    assert result["changes"] == []


# ---------------------------------------------------------------------------
# compare_findings — identical findings
# ---------------------------------------------------------------------------


def test_identical_findings_no_changes():
    finding = _finding(
        "OpenAI maintains GPT-4 as flagship model with stable API pricing for enterprise customers."
    )
    result = compare_findings(
        competitor="OpenAI",
        current_findings=[finding],
        previous_findings=[finding],
    )
    assert result["has_changes"] is False
    assert result["changes"] == []


# ---------------------------------------------------------------------------
# compare_findings — high-signal changes detected
# ---------------------------------------------------------------------------


def test_pricing_change_detected():
    previous = [
        _finding(
            "OpenAI offers GPT-4 API at standard pricing for enterprise customers."
        )
    ]
    current = [
        _finding(
            "OpenAI offers GPT-4 API at standard pricing for enterprise customers."
        ),
        _finding(
            "OpenAI introduced GPT-5 API pricing at $0.01 per 1k tokens — "
            "a 40% reduction for enterprise tier customers with dedicated rate limits."
        ),
    ]
    result = compare_findings(
        competitor="OpenAI",
        current_findings=current,
        previous_findings=previous,
    )
    assert result["has_changes"] is True
    assert len(result["changes"]) >= 1
    assert result["changes"][0]["type"] == "pricing_change"


def test_enterprise_expansion_detected():
    previous = [
        _finding("Anthropic focuses on safety research and Claude API development.")
    ]
    current = [
        _finding("Anthropic focuses on safety research and Claude API development."),
        _finding(
            "Anthropic launched enterprise-grade Claude security tooling with "
            "SOC 2 Type II compliance and dedicated audit logging for regulated industries."
        ),
    ]
    result = compare_findings(
        competitor="Anthropic",
        current_findings=current,
        previous_findings=previous,
    )
    assert result["has_changes"] is True
    assert any(
        c["type"] in ("enterprise_expansion", "product_launch")
        for c in result["changes"]
    )


# ---------------------------------------------------------------------------
# compare_findings — low-signal changes suppressed
# ---------------------------------------------------------------------------


def test_low_signal_change_suppressed():
    """Generic text that doesn't match any high-signal category should be suppressed."""
    previous = [
        _finding(
            "Anthropic continues to develop AI models with a focus on safety research."
        )
    ]
    current = [
        _finding(
            "Anthropic continues to develop AI models with a focus on safety research."
        ),
        _finding(
            "Anthropic remains committed to responsible AI development practices."
        ),
    ]
    result = compare_findings(
        competitor="Anthropic",
        current_findings=current,
        previous_findings=previous,
    )
    # "remains committed to" is a filler pattern — should be suppressed
    assert result["has_changes"] is False


# ---------------------------------------------------------------------------
# compare_all_competitors
# ---------------------------------------------------------------------------


def test_multiple_competitors():
    current = {
        "openai": [
            _finding(
                "OpenAI launched GPT-5 with a new enterprise pricing tier at $0.01 per 1k tokens, "
                "a 40% reduction from GPT-4 pricing, targeting large-scale enterprise deployments "
                "with dedicated rate limits and SLA guarantees."
            )
        ],
        "anthropic": [
            _finding("Claude 3 launched with enterprise SOC 2 compliance features.")
        ],
    }
    previous = {
        "openai": [
            _finding(
                "Anthropic is the main competitor in the safety space. "
                "Research publications continue on constitutional AI methods."
            )
        ],
        "anthropic": [],
    }
    results = compare_all_competitors(current, previous)
    assert len(results) == 2

    openai_result = next(r for r in results if r["competitor"] == "openai")
    anthropic_result = next(r for r in results if r["competitor"] == "anthropic")

    assert openai_result["has_changes"] is True
    assert anthropic_result["has_changes"] is False  # no previous history


# ---------------------------------------------------------------------------
# has_any_high_signal_changes
# ---------------------------------------------------------------------------


def test_has_signal_true():
    results = [
        {"has_changes": False, "changes": []},
        {"has_changes": True, "changes": [{"type": "pricing_change", "summary": "x"}]},
    ]
    assert has_any_high_signal_changes(results) is True


def test_has_signal_false():
    results = [
        {"has_changes": False, "changes": []},
        {"has_changes": False, "changes": []},
    ]
    assert has_any_high_signal_changes(results) is False


# ---------------------------------------------------------------------------
# build_briefing_changes_section
# ---------------------------------------------------------------------------


def test_briefing_section_empty_returns_empty_string():
    """New behavior: empty results returns '' not a filler section."""
    md = build_briefing_changes_section([])
    assert md == ""


def test_briefing_section_no_changes_returns_empty():
    """No-change results produce no output — no filler lines."""
    results = [
        {
            "competitor": "Anthropic",
            "has_changes": False,
            "changes": [],
            "delta_summary": "",
            "historical_context": "",
        }
    ]
    md = build_briefing_changes_section(results)
    assert md == ""


def test_briefing_section_with_high_signal_changes():
    results = [
        {
            "competitor": "OpenAI",
            "has_changes": True,
            "changes": [
                {
                    "type": "pricing_change",
                    "summary": "GPT-5 API pricing reduced 40% for enterprise tier customers",
                }
            ],
            "delta_summary": "OpenAI — 1 strategic development",
            "historical_context": "",
        }
    ]
    md = build_briefing_changes_section(results)
    assert "## Strategic Intelligence Changes" in md
    assert "OpenAI" in md
    assert "GPT-5 API pricing" in md
    # No filler lines for competitors with no changes
    assert "No significant changes" not in md
