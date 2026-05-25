from __future__ import annotations

from typing import Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.queries import MemoryQueries

router = APIRouter()


class MemoryUpsert(BaseModel):
    key: str
    value: Any
    namespace: str = "default"
    tags: List[str] = []


class MemoryListQuery(BaseModel):
    namespace: str = "default"
    limit: int = 50


@router.post("/set")
async def set_memory(entry: MemoryUpsert):
    """Store or update a memory entry."""
    saved = MemoryQueries.upsert(
        key=entry.key,
        namespace=entry.namespace,
        value=entry.value,
        tags=entry.tags,
    )
    return {"status": "ok", "entry": saved}


@router.get("/{namespace}/{key}")
async def get_memory(namespace: str, key: str):
    """Retrieve a memory entry by namespace and key."""
    entry = MemoryQueries.get(key=key, namespace=namespace)
    if not entry:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return entry


@router.post("/list")
async def list_memory(query: MemoryListQuery):
    """List all memory entries in a namespace."""
    entries = MemoryQueries.list_by_namespace(
        namespace=query.namespace, limit=query.limit
    )
    return {"entries": entries, "count": len(entries)}
