from fastapi import APIRouter, Query
from src import db

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/summary")
async def summary(days: int = Query(30), account_uuid: str | None = Query(None)):
    return await db.get_summary_stats(days, account_uuid)


@router.get("/cost-timeseries")
async def cost_timeseries(
    days: int = Query(30),
    granularity: str = Query("day"),
    account_uuid: str | None = Query(None),
):
    return await db.get_cost_timeseries(days, granularity, account_uuid)


@router.get("/tool-usage")
async def tool_usage(days: int = Query(30), account_uuid: str | None = Query(None)):
    return await db.get_tool_usage_stats(days, account_uuid)


@router.get("/activity-timeline")
async def activity_timeline(days: int = Query(7), account_uuid: str | None = Query(None)):
    return await db.get_activity_timeline(days, account_uuid)
