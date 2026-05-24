from fastapi import APIRouter, HTTPException
from models.memory import MemoryUpsert, MemoryQuery
from db.queries import MemoryQueries

router = APIRouter()


@router.post("/set")
async def set_memory(entry: MemoryUpsert):
    saved = MemoryQueries.upsert(
        key=entry.key,
        namespace=entry.namespace,
        value=entry.value,
        tags=entry.tags,
    )
    return {"status": "ok", "entry": saved}


@router.get("/{namespace}/{key}")
async def get_memory(namespace: str, key: str):
    entry = MemoryQueries.get(key=key, namespace=namespace)
    if not entry:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return entry


@router.post("/list")
async def list_memory(query: MemoryQuery):
    entries = MemoryQueries.list_by_namespace(
        namespace=query.namespace, limit=query.limit
    )
    return {"entries": entries, "count": len(entries)}
