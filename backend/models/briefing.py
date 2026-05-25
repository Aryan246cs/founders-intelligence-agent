from __future__ import annotations

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class BriefingSection(BaseModel):
    title: str
    content: str
    priority: str = "medium"


class Briefing(BaseModel):
    id: Optional[str] = None
    title: str
    sections: List[BriefingSection]
    raw_markdown: str
    generated_at: Optional[datetime] = None
    sent_to_slack: bool = False
