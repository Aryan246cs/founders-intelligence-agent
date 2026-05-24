from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BriefingSection(BaseModel):
    title: str
    content: str
    priority: str = "medium"  # low | medium | high


class Briefing(BaseModel):
    id: Optional[str] = None
    title: str
    sections: list[BriefingSection]
    raw_markdown: str
    generated_at: Optional[datetime] = None
    sent_to_slack: bool = False


class BriefingRequest(BaseModel):
    focus_areas: list[str] = []
    include_competitors: bool = True
    include_market_trends: bool = True
    time_range_days: int = 7


class BriefingResponse(BaseModel):
    briefing: Briefing
    task_id: str
