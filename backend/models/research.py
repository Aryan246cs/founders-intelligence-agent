from __future__ import annotations

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ResearchFinding(BaseModel):
    id: Optional[str] = None
    competitor_id: Optional[str] = None
    source_url: str
    title: str
    summary: str
    sentiment: Optional[str] = None
    tags: List[str] = []
    found_at: Optional[datetime] = None
