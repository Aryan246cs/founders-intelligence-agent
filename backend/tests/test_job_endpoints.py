"""
End-to-end HTTP contract for background runs.

Covers the handshake the UI depends on: POST returns immediately with a poll
URL, the job endpoint reports live step state while the pipeline runs, and the
finished job carries the result the UI renders.
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from api.routes import startup_research as sr_routes


@pytest.fixture()
def client(monkeypatch):
    """A client whose research pipeline is replaced by a controllable stub."""
    monkeypatch.setattr(
        sr_routes.WorkflowExecutionQueries,
        "create",
        lambda trigger_source, request_summary: {"id": "exec-1"},
    )
    monkeypatch.setattr(
        sr_routes.WorkflowExecutionQueries, "complete", lambda *a, **k: {"id": "exec-1"}
    )
    monkeypatch.setattr(
        sr_routes.WorkflowExecutionQueries, "fail", lambda *a, **k: {"id": "exec-1"}
    )

    import main

    with TestClient(main.app) as c:
        yield c


def _stub_agent(monkeypatch, *, steps_to_run, fail_with=None):
    """Replace StartupResearchAgent with one that walks a scripted step list."""

    class StubAgent:
        def __init__(self, progress=None):
            self.progress = progress

        async def run(self, input_data):
            for key in steps_to_run:
                self.progress.start(key)
                await asyncio.sleep(0)
                self.progress.done(key)
            if fail_with:
                raise RuntimeError(fail_with)
            return {
                "report_id": "report-1",
                "startup_idea": input_data["startup_idea"],
                "industry": "Interview Prep",
                "competitors_found": 3,
                "sources_analyzed": 5,
                "research_score": 72,
                "sent_to_slack": False,
            }

    monkeypatch.setattr(sr_routes, "StartupResearchAgent", StubAgent)


def _wait_for_terminal(client, poll_url, tries=50):
    for _ in range(tries):
        body = client.get(poll_url).json()
        if body["status"] in ("completed", "failed"):
            return body
    raise AssertionError(f"job never finished: {body}")


def test_run_returns_immediately_with_a_poll_url(client, monkeypatch):
    _stub_agent(monkeypatch, steps_to_run=["parse", "search"])

    res = client.post(
        "/api/startup-research/run",
        json={"startup_idea": "AI interview prep for Indian students"},
    )

    assert res.status_code == 202
    body = res.json()
    assert body["status"] == "running"
    assert body["execution_id"] == "exec-1"
    assert body["poll_url"] == f"/api/startup-research/jobs/{body['job_id']}"
    assert body["steps_total"] == 10


def test_job_endpoint_reports_the_full_step_timeline(client, monkeypatch):
    _stub_agent(monkeypatch, steps_to_run=["parse", "search", "insights", "persist"])

    started = client.post(
        "/api/startup-research/run",
        json={"startup_idea": "AI interview prep for Indian students"},
    ).json()
    job = _wait_for_terminal(client, started["poll_url"])

    assert job["status"] == "completed"
    assert job["progress_pct"] == 100
    assert job["result"]["report_id"] == "report-1"
    assert job["result"]["research_score"] == 72

    statuses = {s["key"]: s["status"] for s in job["steps"]}
    assert statuses["parse"] == "done"
    assert statuses["persist"] == "done"
    # Steps the stub never entered are reported as skipped, never pending.
    assert statuses["deliver"] == "skipped"
    assert "pending" not in statuses.values()


def test_failed_run_surfaces_the_error_on_the_job(client, monkeypatch):
    _stub_agent(monkeypatch, steps_to_run=["parse"], fail_with="Groq rejected the API key")

    started = client.post(
        "/api/startup-research/run", json={"startup_idea": "AI interview prep platform"}
    ).json()
    job = _wait_for_terminal(client, started["poll_url"])

    assert job["status"] == "failed"
    assert job["error"] == "Groq rejected the API key"


def test_wait_mode_blocks_and_returns_the_result(client, monkeypatch):
    """n8n and scripts keep the synchronous behaviour they were written against."""
    _stub_agent(monkeypatch, steps_to_run=["parse", "persist"])

    res = client.post(
        "/api/startup-research/run?wait=true",
        json={"startup_idea": "AI interview prep platform"},
    )

    body = res.json()
    assert body["status"] == "completed"
    assert body["report_id"] == "report-1"
    assert body["competitors_found"] == 3


def test_unknown_job_is_a_404(client):
    res = client.get("/api/startup-research/jobs/nope")
    assert res.status_code == 404


def test_database_outage_is_a_503_not_a_500(client, monkeypatch):
    def explode(**_kwargs):
        raise RuntimeError("[Errno 8] nodename nor servname provided, or not known")

    monkeypatch.setattr(sr_routes.WorkflowExecutionQueries, "create", explode)

    res = client.post(
        "/api/startup-research/run", json={"startup_idea": "AI interview prep platform"}
    )

    assert res.status_code == 503
    assert "paused" in res.json()["detail"]
