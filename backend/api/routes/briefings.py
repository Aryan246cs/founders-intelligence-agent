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

    # Extract key changes — supports both "- " and "* " bullet styles
    key_changes: List[str] = []
    for line in md.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ", "• ")) and len(stripped) > 10:
            key_changes.append(stripped[2:].strip())
    key_changes = [k for k in key_changes if len(k) > 15][:8]

    # Extract strategic insight — try multiple heading variants
    strategic_insight = ""
    for heading in [
        "Strategic Intelligence",
        "Strategic Opportunities",
        "Strategic Insight",
    ]:
        match = re.search(
            rf"##\s*{re.escape(heading)}\s*\n(.*?)(?=\n##|\Z)", md, re.DOTALL
        )
        if match:
            strategic_insight = match.group(1).strip()[:600]
            break

    # Extract opportunity signals — try multiple heading variants
    opportunity_signals: List[str] = []
    for heading in [
        "Founder Takeaway",
        "Recommended Actions",
        "Strategic Opportunities",
    ]:
        match = re.search(
            rf"##\s*{re.escape(heading)}\s*\n(.*?)(?=\n##|\Z)", md, re.DOTALL
        )
        if match:
            block = match.group(1)
            for line in block.splitlines():
                stripped = line.strip()
                if stripped.startswith(("- ", "* ", "• ")) and len(stripped) > 5:
                    opportunity_signals.append(stripped[2:].strip())
                elif stripped and not stripped.startswith("#") and len(stripped) > 20:
                    # Plain paragraph line (Founder Takeaway is often not bulleted)
                    opportunity_signals.append(stripped)
                    break
            if opportunity_signals:
                break
    opportunity_signals = opportunity_signals[:5]

    # Extract companies mentioned — scan the full markdown for any capitalized names
    companies_mentioned: List[str] = []
    # First check known global companies
    known_global = [
        "OpenAI",
        "Anthropic",
        "Google",
        "DeepMind",
        "Mistral",
        "Cohere",
        "Microsoft",
        "Meta",
        "Amazon",
        "Apple",
        "Nvidia",
        "Hugging Face",
        "Groq",
        "Together AI",
        "Perplexity",
        "Cursor",
        "xAI",
    ]
    # Then extract from title (topic-specific companies)
    title = row.get("title", "")
    for company in known_global:
        if company.lower() in md.lower():
            companies_mentioned.append(company)

    # Also extract capitalized words from Key Developments section as company names
    kd_match = re.search(r"##\s*Key Developments\s*\n(.*?)(?=\n##|\Z)", md, re.DOTALL)
    if kd_match:
        kd_text = kd_match.group(1)
        # Find "[CompanyName]:" patterns
        bracket_names = re.findall(r"\[([A-Z][a-zA-Z\s]+)\]", kd_text)
        # Find "CompanyName:" patterns at start of bullets
        colon_names = re.findall(
            r"[-*]\s+([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)?):", kd_text
        )
        for name in bracket_names + colon_names:
            name = name.strip()
            if name and name not in companies_mentioned and len(name) > 2:
                companies_mentioned.append(name)

    # Derive priority from content signals
    md_lower = md.lower()
    priority = "medium"
    if any(w in md_lower for w in ["critical", "urgent", "immediate", "breaking"]):
        priority = "critical"
    elif any(
        w in md_lower
        for w in [
            "significant",
            "major",
            "important",
            "enterprise",
            "launched",
            "raised",
        ]
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
        "companiesMentioned": list(
            dict.fromkeys(companies_mentioned)
        ),  # dedup, preserve order
        "priority": priority,
        "riskLevel": priority,
        "sourceCount": max(len(key_changes), 1),
        "aiConfidence": 88,
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
