"""OpenWatch MCP Server — 14 tools for agent governance & observability."""

import json
import os
from mcp.server.fastmcp import FastMCP

from src import db

MCP_PORT = int(os.getenv("MCP_PORT", "8789"))

mcp = FastMCP("openwatch", instructions="""
OpenWatch is an agent governance & observability system.
It provides tools to query Claude Code session data, compliance logs, costs, and audit trails.
Use these tools to answer questions about AI agent usage, costs, projects, and user activity.
""")


# ---------------------------------------------------------------------------
# Core Analytics
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_usage_summary(days: int = 30, account_uuid: str | None = None) -> str:
    """Get overall usage stats: sessions, costs, tokens, active users, compliance events, agent runs.
    Use this for high-level questions like "how much are we spending?" or "how active is the team?"."""
    result = await db.get_summary_stats(days, account_uuid)
    return json.dumps(result, default=str)


@mcp.tool()
async def get_cost_breakdown(group_by: str = "day", days: int = 30) -> str:
    """Get cost breakdown grouped by: user, day, model, or project.
    Use for "who spent the most?", "daily spend trend?", "cost per project?"."""
    result = await db.get_cost_breakdown(group_by, days)
    return json.dumps(result, default=str)


@mcp.tool()
async def get_tool_usage_stats(days: int = 30, account_uuid: str | None = None, tool_name: str | None = None) -> str:
    """Get stats on which tools agents use, how often, and error rates.
    Use for "what tools are used most?", "any tools failing?"."""
    result = await db.get_tool_usage_stats(days, account_uuid, tool_name)
    return json.dumps(result, default=str)


@mcp.tool()
async def get_activity_timeline(days: int = 7, account_uuid: str | None = None) -> str:
    """Get day-by-day breakdown of what was done: sessions with titles, projects, branches, costs.
    Use for "what did I do last week?", "what did I work on Monday?"."""
    result = await db.get_activity_timeline(days, account_uuid)
    return json.dumps(result, default=str)


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_sessions(
    days: int = 7, account_uuid: str | None = None, project: str | None = None,
    sort_by: str = "recent", limit: int = 10
) -> str:
    """List Claude Code sessions. Sort by: cost, recent, or messages.
    Filter by user (account_uuid) or project name.
    Use for "show me recent sessions", "most expensive sessions?"."""
    result = await db.list_sessions(days, limit, 0, account_uuid, project, sort_by)
    return json.dumps(result, default=str)


@mcp.tool()
async def get_session_detail(
    session_id: str, include_messages: bool = False,
    include_tools: bool = False, include_audit: bool = False
) -> str:
    """Get full details of a session. Optionally include messages, tool calls, and audit trail.
    Use for "tell me about session X", "what happened in this session?"."""
    result = await db.get_session(session_id)
    if not result:
        return json.dumps({"error": "Session not found"})
    if include_messages:
        result["messages"] = await db.get_session_messages(session_id, limit=50)
    if include_tools:
        result["tools"] = await db.get_session_tools(session_id)
    if include_audit:
        result["audit_events"] = await db.get_session_audit(session_id)
    return json.dumps(result, default=str)


@mcp.tool()
async def get_session_summary(session_id: str) -> str:
    """Get an AI-friendly summary of a session: what was worked on, tools used, branches, directories, cost.
    Use for "summarize this session", "what was done here?"."""
    result = await db.get_session_summary(session_id)
    if not result:
        return json.dumps({"error": "Session not found"})
    return json.dumps(result, default=str)


# ---------------------------------------------------------------------------
# Users & Projects
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_user_activity(account_uuid: str | None = None, days: int = 30) -> str:
    """Get activity for one user or all users: session count, cost, last active.
    Omit account_uuid to get all users ranked by cost.
    Use for "who used Claude the most?", "show me user X's activity"."""
    if account_uuid:
        result = await db.get_user_activity(account_uuid, days)
    else:
        result = await db.list_users(days)
    return json.dumps(result, default=str)


@mcp.tool()
async def get_projects(days: int = 30, account_uuid: str | None = None) -> str:
    """List projects with session counts, costs, and active users.
    Projects are derived from working directories.
    Use for "what projects am I working on?", "which project costs the most?"."""
    result = await db.list_projects(days, account_uuid)
    return json.dumps(result, default=str)


@mcp.tool()
async def search_messages(query: str, days: int = 7, account_uuid: str | None = None, type: str | None = None, limit: int = 25) -> str:
    """Search message content across all sessions.
    Filter by user, message type (user/assistant), and time period.
    Use for "find sessions where I worked on auth", "what did I discuss about billing?"."""
    result = await db.search_messages(query, days, account_uuid, type, limit)
    return json.dumps(result, default=str)


# ---------------------------------------------------------------------------
# Compliance & Audit
# ---------------------------------------------------------------------------

@mcp.tool()
async def search_audit_events(
    session_id: str | None = None, event_type: str | None = None,
    subtype: str | None = None, days: int = 7, limit: int = 25
) -> str:
    """Search the audit trail. Filter by session, event type, or subtype.
    Event types: user, assistant, system, rate_limit_event, result, tool_use_summary.
    Subtypes: init, status, success, permission_request, error_during_execution, etc.
    Use for "any errors?", "show permission requests", "audit trail for session X"."""
    result = await db.search_audit_events(session_id, event_type, subtype, days, limit)
    return json.dumps(result, default=str)


@mcp.tool()
async def get_compliance_activities(
    activity_type: str | None = None, actor_email: str | None = None,
    days: int = 30, limit: int = 25
) -> str:
    """Get Claude.com compliance activity log: logins, chat views, file operations.
    Use for "who accessed Claude.com?", "compliance audit log"."""
    result = await db.list_compliance_activities(days, activity_type, actor_email, limit)
    return json.dumps(result, default=str)


@mcp.tool()
async def get_agent_runs(
    agent_type: str | None = None, status: str | None = None,
    days: int = 90, limit: int = 10
) -> str:
    """Get intelligence agent run history: costs, durations, success/failure.
    Agent types: intelligence, sql_retriever.
    Use for "show agent runs", "any failed agent jobs?"."""
    result = await db.list_agent_runs(days, agent_type, status, limit)
    return json.dumps(result, default=str)


# ---------------------------------------------------------------------------
# Raw Query
# ---------------------------------------------------------------------------

@mcp.tool()
async def run_query(sql: str) -> str:
    """Run a read-only SQL SELECT query against the OpenWatch database.
    Tables use schema__table naming: cowork__sessions, cowork__messages, cowork__tool_calls,
    cowork__users, cowork__workers, cowork__audit_events, compliance__claude_activities,
    compliance__claude_chats, compliance__claude_chat_messages, agent__runs, agent__outputs.
    Only SELECT is allowed — no mutations.
    Use as an escape hatch when other tools don't cover the question."""
    try:
        result = await db.run_query(sql)
        return json.dumps(result, default=str)
    except ValueError as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "sse")  # "stdio" or "sse"
    if transport == "sse":
        os.environ.setdefault("FASTMCP_PORT", str(MCP_PORT))
        mcp.run(transport="sse")
    else:
        mcp.run()
