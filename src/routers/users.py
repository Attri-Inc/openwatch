from fastapi import APIRouter, Query
from src import db

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("")
async def list_users(days: int = Query(30)):
    return await db.list_users(days)


@router.get("/{account_uuid}/activity")
async def user_activity(account_uuid: str, days: int = Query(30)):
    return await db.get_user_activity(account_uuid, days)
