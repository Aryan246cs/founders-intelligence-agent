from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class MemoryEntry(BaseModel):
    id: Optional[str] = None
    key: str
    value: Any
    namespace: str = "default"
    tags: list[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MemoryUpsert(BaseModel):
    key: str
    value: Any
    namespace: str = "default"
    tags: list[str] = []


class MemoryQuery(BaseModel):
    namespace: str = "default"
    tags: list[str] = []
    limit: int = 50
