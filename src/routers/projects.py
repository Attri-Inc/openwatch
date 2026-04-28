from fastapi import APIRouter, Query
from src import db

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.get("")
async def list_projects(days: int = Query(30), account_uuid: str | None = Query(None)):
    return await db.list_projects(days, account_uuid)


@router.get("/{project_name}/sessions")
async def project_sessions(project_name: str, days: int = Query(30)):
    return await db.get_project_sessions(project_name, days)


@router.get("/{project_name}/stats")
async def project_stats(project_name: str, days: int = Query(30)):
    return await db.get_project_stats(project_name, days)
