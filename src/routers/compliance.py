from fastapi import APIRouter, Query
from src import db

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])


@router.get("/activities")
async def list_activities(
    days: int = Query(30),
    activity_type: str | None = Query(None),
    actor_email: str | None = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
):
    return await db.list_compliance_activities(days, activity_type, actor_email, limit, offset)


@router.get("/activity-summary")
async def activity_summary(days: int = Query(30)):
    return await db.get_compliance_summary(days)


@router.get("/chats")
async def list_chats(limit: int = Query(50), offset: int = Query(0)):
    return await db.list_compliance_chats(limit, offset)


@router.get("/chats/{chat_id}/messages")
async def chat_messages(chat_id: int):
    return await db.get_chat_messages(chat_id)
