from __future__ import annotations

import re
from typing import List

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from agents.briefing_agent import BriefingAgent
from db.queries import BriefingQueries
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class BriefingRequest(BaseModel):
    time_range_days: int = 7
    send_to_slack: bool = False


def _enrich_briefing(row: dict) -> dict:
    """
    Enrich a raw briefings row with derived fields the frontend expects.
    Parses raw_markdown to extract key changes, strategic insight, etc.
    """
    md = row.get("raw_markdown", "") or ""

    # Extract key changes from bullet points in the markdown
    key_changes: List[str] = []
    for line in md.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and len(stripped) > 10:
            key_changes.append(stripped[2:].strip())
    key_changes = key_changes[:8]  # cap at 8

    # Extract strategic insight from ## Strategic Opportunities section
    strategic_insight = ""
    opp_match = re.search(
        r"##\s*Strategic Opportunities\s*\n(.*?)(?=\n##|\Z)", md, re.DOTALL
    )
    if opp_match:
        strategic_insight = opp_match.group(1).strip()[:600]

    # Extract opportunity signals from ## Recommended Actions
    opportunity_signals: List[str] = []
    actions_match = re.search(
        r"##\s*Recommended Actions\s*\n(.*?)(?=\n##|\Z)", md, re.DOTALL
    )
    if actions_match:
        for line in actions_match.group(1).splitlines():
            stripped = line.strip()
            if stripped.startswith("- ") and len(stripped) > 5:
                opportunity_signals.append(stripped[2:].strip())
    opportunity_signals = opportunity_signals[:5]

    # Extract companies mentioned (simple heuristic: capitalized words near known names)
    companies_mentioned: List[str] = []
    known = [
        "OpenAI",
        "Anthropic",
        "Google",
        "DeepMind",
        "Mistral",
        "Cohere",
        "Together AI",
        "Cognition",
        "Microsoft",
        "Meta",
        "Amazon",
        "Apple",
        "Nvidia",
        "Hugging Face",
        "Stability AI",
        "Inflection",
        "xAI",
    ]
    for company in known:
        if company.lower() in md.lower():
            companies_mentioned.append(company)

    # Derive priority from content signals
    priority = "medium"
    md_lower = md.lower()
    if any(w in md_lower for w in ["critical", "urgent", "immediate", "breaking"]):
        priority = "critical"
    elif any(
        w in md_lower for w in ["significant", "major", "important", "enterprise"]
    ):
        priority = "high"
    elif any(w in md_lower for w in ["minor", "small", "incremental"]):
        priority = "low"

    return {
        **row,
        "keyChanges": key_changes,
        "strategicInsight": strategic_insight
        or "See full briefing for strategic analysis.",
        "opportunitySignals": opportunity_signals,
        "companiesMentioned": companies_mentioned,
        "priority": priority,
        "riskLevel": priority,
        "sourceCount": len(key_changes) + len(companies_mentioned),
        "aiConfidence": 88,  # static until we add confidence scoring
        "sentToSlack": row.get("sent_to_slack", False),
        "generatedAt": row.get("generated_at", ""),
    }


@router.post("/generate")
async def generate_briefing(req: BriefingRequest, background_tasks: BackgroundTasks):
    """Queue a briefing generation task."""
    agent = BriefingAgent()
    background_tasks.add_task(
        agent.run,
        {
            "time_range_days": req.time_range_days,
            "send_to_slack": req.send_to_slack,
        },
    )
    return {"status": "queued"}


@router.get("/")
async def list_briefings(limit: int = 10):
    """List recent briefings with enriched frontend-ready fields."""
    briefings = BriefingQueries.list_recent(limit=limit)
    enriched = [_enrich_briefing(b) for b in briefings]
    return {"briefings": enriched, "total": len(enriched)}


@router.get("/{briefing_id}")
async def get_briefing(briefing_id: str):
    """Get a single briefing by ID."""
    from db.client import get_supabase

    db = get_supabase()
    res = db.table("briefings").select("*").eq("id", briefing_id).execute()
    if not res.data:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Briefing not found")
    return _enrich_briefing(res.data[0])
