from __future__ import annotations

from pydantic import BaseModel
from typing import Any, List, Optional
from datetime import datetime


class MemoryEntry(BaseModel):
    id: Optional[str] = None
    key: str
    value: Any
    namespace: str = "default"
    tags: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
