from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class CompetitorProfile(BaseModel):
    id: Optional[str] = None
    name: str
    website: str
    description: Optional[str] = None
    funding_stage: Optional[str] = None
    last_scraped_at: Optional[datetime] = None
    raw_data: Optional[dict] = None


class ResearchFinding(BaseModel):
    id: Optional[str] = None
    competitor_id: Optional[str] = None
    source_url: str
    title: str
    summary: str
    sentiment: Optional[str] = None
    tags: list[str] = []
    found_at: Optional[datetime] = None


class ResearchRequest(BaseModel):
    query: str
    competitor_names: list[str] = []
    max_results: int = 10


class ResearchResponse(BaseModel):
    findings: list[ResearchFinding]
    total: int
    query: str
