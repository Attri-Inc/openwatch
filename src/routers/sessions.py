from fastapi import APIRouter, Query, HTTPException
from src import db

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.get("")
async def list_sessions(
    days: int = Query(30),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    account_uuid: str | None = Query(None),
    project: str | None = Query(None),
    sort: str = Query("recent"),
    order: str = Query("desc"),
):
    return await db.list_sessions(days, limit, offset, account_uuid, project, sort, order)


@router.get("/{session_id}")
async def get_session(session_id: str):
    s = await db.get_session(session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    return s


@router.get("/{session_id}/messages")
async def get_messages(
    session_id: str,
    type: str | None = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
):
    return await db.get_session_messages(session_id, type, limit, offset)


@router.get("/{session_id}/tools")
async def get_tools(session_id: str):
    return await db.get_session_tools(session_id)


@router.get("/{session_id}/audit-trail")
async def get_audit(session_id: str, type: str | None = Query(None), subtype: str | None = Query(None)):
    return await db.get_session_audit(session_id, type, subtype)


@router.get("/{session_id}/summary")
async def get_summary(session_id: str):
    s = await db.get_session_summary(session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    return s
