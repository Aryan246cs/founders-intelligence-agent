"""
Tests for the startup research pipeline's observable behaviour.

Two things are checked here that the unit tests elsewhere cannot cover:

  1. the job timeline the UI renders matches what the agent actually did,
     including steps that were legitimately skipped;
  2. the degraded path stays honest — when the LLM is unavailable the report
     reports only what was crawled and never invents market claims.
"""

from __future__ import annotations

import json

import pytest

from agents import startup_research_agent as sra
from agents.startup_research_agent import (
    RESEARCH_STEPS,
    StartupResearchAgent,
    _build_fallback_strategic,
)
from services.job_tracker import JobRegistry, ProgressReporter

# ---------------------------------------------------------------------------
# Fakes — one search hit, one scrapeable competitor, deterministic LLM
# ---------------------------------------------------------------------------

SEARCH_RESULTS = [
    {
        "organicResults": [
            {
                "url": "https://interviewbuddy.in/",
                "title": "InterviewBuddy",
                "description": "Live mock interviews with industry experts for Indian job seekers.",
            }
        ]
    }
]

SCRAPED_PAGE = [
    {
        "text": (
            "InterviewBuddy runs live mock interviews with industry experts. "
            "We serve engineering students and early-career professionals across India. "
            "Features include live video interviews, expert feedback reports, and resume review. "
        )
        * 4
    }
]

LLM_RESPONSES = {
    "startup analyst": {
        "industry": "Interview Prep",
        "keywords": ["mock interview", "interview prep"],
        "icp": "Engineering students in India",
        "business_model": "Subscription",
        "india_competitor_queries": ["mock interview startups India"],
        "global_competitor_queries": ["best interview prep platforms"],
    },
    "competitive intelligence analyst. extract": {
        "name": "InterviewBuddy",
        "website": "https://interviewbuddy.in",
        "description": "Live mock interviews with industry experts.",
        "business_focus": "Interview readiness",
        "target_audience": "Students",
        "market_positioning": "Consumer-focused",
        "key_features": ["Live video interviews", "Expert feedback"],
        "pricing_model": "Subscription",
        "pricing_tiers": [{"tier": "Basic", "price": "₹999", "features": ["2 sessions"]}],
        "strengths": ["Expert network"],
        "source_url": "https://interviewbuddy.in",
    },
    "senior strategic analyst": {
        "executive_summary": "A summary grounded in the crawl.",
        "positioning_analysis": "Two paragraphs of positioning analysis.",
        "market_gaps": ["Gap one", "Gap two"],
        "differentiation_opportunities": ["Opportunity one"],
        "swot": {
            "strengths": ["s"],
            "weaknesses": ["w"],
            "opportunities": ["o"],
            "threats": ["t"],
        },
        "founder_recommendations": ["Do the thing"],
    },
}


def _fake_llm(system_prompt: str, **_kwargs) -> str:
    lowered = system_prompt.lower()
    for marker, payload in LLM_RESPONSES.items():
        if marker in lowered:
            return json.dumps(payload)
    return "{}"


@pytest.fixture()
def wired_agent(monkeypatch):
    """A research agent with every external dependency replaced."""
    saved: dict = {}

    async def fake_complete(system_prompt, user_prompt, **kwargs):
        return _fake_llm(system_prompt)

    async def fake_search(query, max_results=10):
        return SEARCH_RESULTS

    async def fake_scrape(url, max_pages=3):
        if "/pricing" in url or "/plans" in url or "/price" in url:
            raise RuntimeError("404")
        return SCRAPED_PAGE

    monkeypatch.setattr(sra.groq_service, "complete", fake_complete)
    monkeypatch.setattr(sra.apify_service, "search_google", fake_search)
    monkeypatch.setattr(sra.apify_service, "scrape_website", fake_scrape)
    monkeypatch.setattr(
        sra.StartupResearchQueries, "save", lambda report: {"id": "report-1", **report}
    )
    monkeypatch.setattr(sra.MemoryQueries, "upsert", lambda **kwargs: saved.update(kwargs))

    registry = JobRegistry()
    job = registry.create(kind="startup_research", steps=RESEARCH_STEPS)
    reporter = ProgressReporter(job)

    agent = StartupResearchAgent(progress=reporter)
    # execute() is called directly, so no agent_tasks row exists to log against.
    monkeypatch.setattr(agent, "_log", lambda *a, **k: None)
    return agent, job


@pytest.mark.asyncio
async def test_pipeline_reports_a_completed_timeline(wired_agent):
    agent, job = wired_agent
    reporter = agent.progress

    reporter.begin()
    result = await agent.execute(
        {"startup_idea": "AI interview prep for Indian students", "send_to_slack": False}
    )
    reporter.finish(result)

    snap = job.to_dict()
    assert snap["status"] == "completed"
    assert snap["progress_pct"] == 100
    # No step may be left pending once a run finishes.
    assert not [s for s in snap["steps"] if s["status"] == "pending"]


@pytest.mark.asyncio
async def test_steps_that_did_not_apply_are_marked_skipped(wired_agent):
    """Scraping succeeded and Slack was not requested — both must read as skipped."""
    agent, job = wired_agent
    agent.progress.begin()
    result = await agent.execute(
        {"startup_idea": "AI interview prep for Indian students", "send_to_slack": False}
    )
    agent.progress.finish(result)

    statuses = {s["key"]: s["status"] for s in job.to_dict()["steps"]}
    assert statuses["parse"] == "done"
    assert statuses["search"] == "done"
    assert statuses["insights"] == "done"
    assert statuses["persist"] == "done"
    assert statuses["deliver"] == "skipped"


@pytest.mark.asyncio
async def test_failure_pins_the_step_that_was_running(wired_agent, monkeypatch):
    agent, job = wired_agent

    async def exploding_search(query, max_results=10):
        raise RuntimeError("Apify token rejected")

    # Search failures are caught per-query, so the run continues on to the
    # persist step, which is where this test makes it fail.
    monkeypatch.setattr(sra.apify_service, "search_google", exploding_search)
    monkeypatch.setattr(
        sra.StartupResearchQueries,
        "save",
        lambda report: (_ for _ in ()).throw(RuntimeError("insert failed")),
    )

    agent.progress.begin()
    with pytest.raises(RuntimeError):
        await agent.execute({"startup_idea": "AI interview prep", "send_to_slack": False})
    agent.progress.fail("insert failed")

    snap = job.to_dict()
    assert snap["status"] == "failed"
    assert snap["error"] == "insert failed"
    failed = [s["key"] for s in snap["steps"] if s["status"] == "failed"]
    assert failed == ["persist"]


@pytest.mark.asyncio
async def test_report_carries_the_scraped_competitor(wired_agent):
    agent, _ = wired_agent
    result = await agent.execute(
        {"startup_idea": "AI interview prep for Indian students", "send_to_slack": False}
    )
    assert result["report_id"] == "report-1"
    assert result["competitors_found"] >= 1
    assert result["research_score"] > 0


# ---------------------------------------------------------------------------
# Degraded path — the LLM is unreachable
# ---------------------------------------------------------------------------

COMPETITORS = [
    {
        "name": "InterviewBuddy",
        "market_positioning": "Consumer-focused",
        "pricing_tiers": [{"tier": "Basic", "price": "₹999"}],
    },
    {"name": "PrepInsta", "market_positioning": "Consumer-focused", "pricing_tiers": []},
]


def test_fallback_names_only_competitors_that_were_found():
    strategic = _build_fallback_strategic(
        startup_idea="AI interview prep", industry="Interview Prep", competitors=COMPETITORS
    )
    assert "InterviewBuddy" in strategic["executive_summary"]
    assert strategic["swot"]["threats"] == [
        "Direct competition from InterviewBuddy",
        "Direct competition from PrepInsta",
    ]


def test_fallback_gaps_are_derived_from_observed_data():
    strategic = _build_fallback_strategic(
        startup_idea="AI interview prep", industry="Interview Prep", competitors=COMPETITORS
    )
    gaps = " ".join(strategic["market_gaps"])
    # One of the two competitors publishes no pricing — that is a fact from the
    # crawl, not a guess.
    assert "do not publish pricing" in gaps
    assert "PrepInsta" in gaps


def test_fallback_never_invents_domain_specific_claims():
    """
    Regression guard: the fallback once contained hardcoded quick-commerce
    copy, so a legal-tech idea would be told about kirana stores.
    """
    strategic = _build_fallback_strategic(
        startup_idea="AI legal document assistant", industry="Legal Tech", competitors=[]
    )
    blob = json.dumps(strategic).lower()
    for leaked in ("fashion", "kirana", "hyperlocal", "neighbourhood", "quick commerce"):
        assert leaked not in blob


def test_fallback_is_explicit_that_analysis_is_missing():
    strategic = _build_fallback_strategic(
        startup_idea="AI legal document assistant", industry="Legal Tech", competitors=[]
    )
    assert "could not be generated" in strategic["executive_summary"]
    assert strategic["swot"]["strengths"] == []
    assert any("Re-run this research" in r for r in strategic["founder_recommendations"])
