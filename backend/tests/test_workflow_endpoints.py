"""
Tests for workflow orchestration endpoint helpers.

These tests cover the pure helper functions in api/routes/workflows.py
that build and interpret execution envelopes — no DB or agent calls needed.
"""

from __future__ import annotations

from api.routes.workflows import (
    _build_execution_response,
    _extract_briefing,
    _has_competitor_changes,
    _comparison_ran,
)


# ---------------------------------------------------------------------------
# _build_execution_response
# ---------------------------------------------------------------------------


def _make_record(**overrides) -> dict:
    base = {
        "id": "exec-123",
        "status": "completed",
        "trigger_source": "api",
        "request_summary": "Monitor OpenAI",
        "plan_summary": "Research and brief",
        "steps_total": 2,
        "steps_completed": 2,
        "briefing_available": True,
        "briefing_id": "brief-456",
        "slack_delivered": False,
        "comparison_ran": True,
        "has_competitor_changes": True,
        "error": None,
        "started_at": "2026-05-26T10:00:00+00:00",
        "completed_at": "2026-05-26T10:01:00+00:00",
        "duration_ms": 60000,
    }
    base.update(overrides)
    return base


def test_envelope_has_all_required_keys():
    record = _make_record()
    result = _build_execution_response(record)
    required = {
        "execution_id",
        "status",
        "trigger_source",
        "request_summary",
        "plan_summary",
        "steps_total",
        "steps_completed",
        "briefing_available",
        "briefing_id",
        "slack_delivered",
        "comparison_ran",
        "has_competitor_changes",
        "error",
        "started_at",
        "completed_at",
        "duration_ms",
    }
    assert required.issubset(result.keys())


def test_envelope_maps_id_to_execution_id():
    record = _make_record(id="my-exec-id")
    result = _build_execution_response(record)
    assert result["execution_id"] == "my-exec-id"


def test_envelope_defaults_missing_optional_fields():
    # Minimal record — only required DB fields
    record = {"id": "x", "status": "running"}
    result = _build_execution_response(record)
    assert result["plan_summary"] == ""
    assert result["briefing_available"] is False
    assert result["slack_delivered"] is False
    assert result["error"] is None
    assert result["duration_ms"] is None


def test_envelope_failed_status_preserved():
    record = _make_record(status="failed", error="Planner returned no steps")
    result = _build_execution_response(record)
    assert result["status"] == "failed"
    assert result["error"] == "Planner returned no steps"


# ---------------------------------------------------------------------------
# _extract_briefing
# ---------------------------------------------------------------------------


def test_extract_briefing_found():
    results = [
        {"agent_type": "research", "result": {"query": "openai"}},
        {
            "agent_type": "briefing",
            "result": {"briefing_id": "b1", "sent_to_slack": False},
        },
    ]
    briefing = _extract_briefing(results)
    assert briefing is not None
    assert briefing["briefing_id"] == "b1"


def test_extract_briefing_not_present():
    results = [{"agent_type": "research", "result": {}}]
    assert _extract_briefing(results) is None


def test_extract_briefing_empty_list():
    assert _extract_briefing([]) is None


# ---------------------------------------------------------------------------
# _has_competitor_changes
# ---------------------------------------------------------------------------


def test_has_competitor_changes_true():
    results = [
        {
            "agent_type": "memory",
            "result": {
                "action": "compare_batch",
                "comparisons": [
                    {"competitor": "OpenAI", "has_changes": True},
                    {"competitor": "Anthropic", "has_changes": False},
                ],
            },
        }
    ]
    assert _has_competitor_changes(results) is True


def test_has_competitor_changes_false_when_no_changes():
    results = [
        {
            "agent_type": "memory",
            "result": {
                "action": "compare_batch",
                "comparisons": [{"competitor": "OpenAI", "has_changes": False}],
            },
        }
    ]
    assert _has_competitor_changes(results) is False


def test_has_competitor_changes_false_when_no_memory_step():
    results = [{"agent_type": "research", "result": {}}]
    assert _has_competitor_changes(results) is False


# ---------------------------------------------------------------------------
# _comparison_ran
# ---------------------------------------------------------------------------


def test_comparison_ran_compare_batch():
    results = [
        {
            "agent_type": "memory",
            "result": {"action": "compare_batch", "comparisons": []},
        }
    ]
    assert _comparison_ran(results) is True


def test_comparison_ran_compare():
    results = [
        {"agent_type": "memory", "result": {"action": "compare", "comparison": {}}}
    ]
    assert _comparison_ran(results) is True


def test_comparison_ran_false_for_set_action():
    results = [{"agent_type": "memory", "result": {"action": "set", "entry": {}}}]
    assert _comparison_ran(results) is False


def test_comparison_ran_false_no_memory_step():
    results = [{"agent_type": "briefing", "result": {}}]
    assert _comparison_ran(results) is False
