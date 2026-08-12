"""
Tests for the in-process job tracker.

The UI renders whatever these snapshots say, so the invariants that matter are:
a finished job never shows pending rows, a failed job pins the blame on the step
that was actually running, and the step a caller sees as "current" is the one
the agent is really inside.
"""

from __future__ import annotations

import pytest

from services.job_tracker import JobRegistry, ProgressReporter, NULL_REPORTER

STEPS = [
    ("parse", "Understanding idea"),
    ("search", "Searching"),
    ("report", "Writing report"),
]


@pytest.fixture()
def registry():
    return JobRegistry(max_jobs=5)


@pytest.fixture()
def reporter(registry):
    job = registry.create(kind="test", steps=STEPS, summary="a test run")
    return ProgressReporter(job)


def test_new_job_is_queued_with_all_steps_pending(reporter):
    snap = reporter.job.to_dict()
    assert snap["status"] == "queued"
    assert snap["steps_total"] == 3
    assert snap["steps_completed"] == 0
    assert snap["progress_pct"] == 0
    assert [s["status"] for s in snap["steps"]] == ["pending"] * 3


def test_running_step_is_reported_as_current(reporter):
    reporter.begin()
    reporter.start("search", "Searching Google")

    snap = reporter.job.to_dict()
    assert snap["status"] == "running"
    assert snap["current_step"] == "search"
    assert snap["current_step_label"] == "Searching"
    assert snap["steps"][1]["detail"] == "Searching Google"


def test_starting_a_later_step_closes_an_open_earlier_step(reporter):
    """An optional step that is skipped must not strand the timeline."""
    reporter.begin()
    reporter.start("parse")
    reporter.start("report")  # jumped over 'search' without closing 'parse'

    statuses = {s["key"]: s["status"] for s in reporter.job.to_dict()["steps"]}
    assert statuses["parse"] == "done"
    assert statuses["report"] == "running"


def test_finish_marks_unreached_steps_skipped_not_pending(reporter):
    reporter.begin()
    reporter.start("parse")
    reporter.done("parse")
    reporter.finish({"report_id": "abc"})

    snap = reporter.job.to_dict()
    assert snap["status"] == "completed"
    assert snap["result"] == {"report_id": "abc"}
    assert [s["status"] for s in snap["steps"]] == ["done", "skipped", "skipped"]
    # Skipped steps still count as resolved, so a completed job reads 100%.
    assert snap["progress_pct"] == 100
    assert snap["current_step"] is None


def test_failure_marks_the_running_step_as_failed(reporter):
    reporter.begin()
    reporter.done("parse")
    reporter.start("search")
    reporter.fail("Apify token rejected")

    snap = reporter.job.to_dict()
    assert snap["status"] == "failed"
    assert snap["error"] == "Apify token rejected"
    statuses = {s["key"]: s["status"] for s in snap["steps"]}
    assert statuses["search"] == "failed"
    assert statuses["report"] == "pending"


def test_skipped_step_records_its_reason(reporter):
    reporter.begin()
    reporter.skip("report", "Slack delivery not requested")

    step = next(s for s in reporter.job.to_dict()["steps"] if s["key"] == "report")
    assert step["status"] == "skipped"
    assert step["detail"] == "Slack delivery not requested"


def test_steps_record_durations_once_started(reporter):
    reporter.begin()
    reporter.start("parse")
    reporter.done("parse")

    step = reporter.job.to_dict()["steps"][0]
    assert step["duration_ms"] is not None and step["duration_ms"] >= 0
    assert step["started_at"] and step["completed_at"]
    # Never-started steps report no duration rather than a misleading zero.
    assert reporter.job.to_dict()["steps"][2]["duration_ms"] is None


def test_extend_appends_runtime_discovered_steps(reporter):
    reporter.extend([("step_0", "Analysing Zomato"), ("step_1", "Analysing Swiggy")])
    keys = [s["key"] for s in reporter.job.to_dict()["steps"]]
    assert keys == ["parse", "search", "report", "step_0", "step_1"]


def test_extend_ignores_duplicate_keys(reporter):
    reporter.extend([("parse", "Duplicate")])
    keys = [s["key"] for s in reporter.job.to_dict()["steps"]]
    assert keys.count("parse") == 1


def test_unknown_step_keys_are_ignored(reporter):
    """A typo in an agent must not crash a running pipeline."""
    reporter.begin()
    reporter.start("does-not-exist")
    reporter.done("does-not-exist")
    assert reporter.job.to_dict()["current_step"] is None


def test_null_reporter_accepts_every_call():
    """Agents run untracked (tests, n8n, scripts) with no branching."""
    NULL_REPORTER.begin()
    NULL_REPORTER.start("anything")
    NULL_REPORTER.detail("anything", "x")
    NULL_REPORTER.done("anything")
    NULL_REPORTER.skip("anything")
    NULL_REPORTER.fail_step("anything")
    NULL_REPORTER.extend([("a", "b")])
    NULL_REPORTER.finish({"ok": True})
    NULL_REPORTER.fail("boom")
    assert NULL_REPORTER.job is None


def test_registry_returns_none_for_unknown_job(registry):
    assert registry.get("missing") is None


def test_registry_evicts_oldest_jobs_past_the_cap(registry):
    jobs = [registry.create(kind="test", steps=STEPS) for _ in range(7)]
    assert registry.get(jobs[0].id) is None
    assert registry.get(jobs[-1].id) is not None
    assert len(registry.list_recent(limit=50)) == 5


def test_list_recent_is_newest_first(registry):
    first = registry.create(kind="test", steps=STEPS, summary="first")
    second = registry.create(kind="test", steps=STEPS, summary="second")
    assert [j.id for j in registry.list_recent()] == [second.id, first.id]
