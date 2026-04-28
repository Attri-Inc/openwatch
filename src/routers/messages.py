from fastapi import APIRouter, Query
from src import db

router = APIRouter(prefix="/api/v1/messages", tags=["messages"])


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    days: int = Query(7),
    account_uuid: str | None = Query(None),
    type: str | None = Query(None),
    limit: int = Query(25, le=100),
):
    return await db.search_messages(q, days, account_uuid, type, limit)
