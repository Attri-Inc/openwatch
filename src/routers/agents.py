from fastapi import APIRouter, Query, HTTPException
from src import db

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get("/runs")
async def list_runs(
    days: int = Query(90),
    agent_type: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
):
    return await db.list_agent_runs(days, agent_type, status, limit, offset)


@router.get("/runs/{run_uuid}")
async def get_run(run_uuid: str):
    r = await db.get_agent_run(run_uuid)
    if not r:
        raise HTTPException(404, "Run not found")
    return r


@router.get("/runs/{run_uuid}/outputs")
async def get_outputs(run_uuid: str):
    return await db.get_agent_outputs(run_uuid)
