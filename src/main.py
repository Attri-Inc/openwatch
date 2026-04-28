"""OpenWatch — Agent Governance & Observability API"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import db
from src.config import HOST, PORT
from src.routers import dashboard, sessions, users, projects, messages, compliance, agents


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await db.close_db()


app = FastAPI(
    title="OpenWatch",
    description="Agent Governance & Observability API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(sessions.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(messages.router)
app.include_router(compliance.router)
app.include_router(agents.router)


@app.get("/")
async def root():
    return {"name": "OpenWatch", "version": "0.1.0", "docs": "/docs"}


@app.get("/health")
async def health():
    conn = await db.get_db()
    r = await conn.execute_fetchall("SELECT COUNT(*) as tables FROM sqlite_master WHERE type='table'")
    return {"status": "ok", "tables": dict(r[0])["tables"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host=HOST, port=PORT, reload=True)
