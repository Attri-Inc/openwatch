"""OpenWatch database layer — all query functions.

Shared by both REST API and MCP server. Read-only queries against SQLite.
"""

import aiosqlite
from src.config import DB_PATH

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA query_only=ON")
    return _db


async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None


def _days_filter(col: str, days: int) -> str:
    return f"{col} >= datetime('now', '-{days} days')"


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

async def get_summary_stats(days: int = 30, account_uuid: str | None = None) -> dict:
    db = await get_db()
    acct = "AND s.account_uuid = ?" if account_uuid else ""
    params: list = []
    if account_uuid:
        params = [account_uuid] * 4  # used in 4 subqueries

    row = await db.execute_fetchall(f"""
        SELECT
            (SELECT COUNT(*) FROM cowork__sessions s WHERE {_days_filter('s.first_timestamp', days)} {acct}) as total_sessions,
            (SELECT COUNT(DISTINCT s.account_uuid) FROM cowork__sessions s WHERE {_days_filter('s.first_timestamp', days)} {acct}) as active_users,
            (SELECT COALESCE(SUM(s.user_message_count), 0) FROM cowork__sessions s WHERE {_days_filter('s.first_timestamp', days)} {acct}) as user_messages,
            (SELECT COALESCE(SUM(s.assistant_message_count), 0) FROM cowork__sessions s WHERE {_days_filter('s.first_timestamp', days)} {acct}) as assistant_messages,
            (SELECT COALESCE(SUM(s.total_input_tokens), 0) FROM cowork__sessions s WHERE {_days_filter('s.first_timestamp', days)} {acct}) as total_input_tokens,
            (SELECT COALESCE(SUM(s.total_output_tokens), 0) FROM cowork__sessions s WHERE {_days_filter('s.first_timestamp', days)} {acct}) as total_output_tokens,
            (SELECT COALESCE(SUM(s.total_cache_read_tokens), 0) FROM cowork__sessions s WHERE {_days_filter('s.first_timestamp', days)} {acct}) as total_cache_read_tokens,
            (SELECT COALESCE(SUM(s.total_cost_usd), 0) FROM cowork__sessions s WHERE {_days_filter('s.first_timestamp', days)} {acct}) as total_cost_usd,
            (SELECT COALESCE(SUM(s.actual_cost_usd), 0) FROM cowork__sessions s WHERE {_days_filter('s.first_timestamp', days)} {acct}) as actual_cost_usd
    """, params)
    r = dict(row[0])

    # Tool calls count
    tc_acct = "AND t.account_uuid = ?" if account_uuid else ""
    tc_params = [account_uuid] if account_uuid else []
    tc = await db.execute_fetchall(f"""
        SELECT COUNT(*) as total_calls FROM cowork__tool_calls t
        WHERE {_days_filter('t.timestamp', days)} {tc_acct}
    """, tc_params)
    r["total_tool_calls"] = dict(tc[0])["total_calls"]

    # Compliance events
    comp_params = [account_uuid] if account_uuid else []
    comp_acct = "AND ca.actor_email = (SELECT email FROM cowork__users WHERE account_uuid = ?)" if account_uuid else ""
    comp = await db.execute_fetchall(f"""
        SELECT COUNT(*) as cnt FROM compliance__claude_activities ca
        WHERE {_days_filter('ca.source_created_at', days)} {comp_acct}
    """, comp_params)
    r["compliance_events"] = dict(comp[0])["cnt"]

    # Agent runs
    ar = await db.execute_fetchall(f"""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
               SUM(CASE WHEN status IN ('failed','error') THEN 1 ELSE 0 END) as failed
        FROM agent__runs WHERE {_days_filter('created_at', days)}
    """)
    ar_row = dict(ar[0])
    r["agent_runs"] = {"total": ar_row["total"], "completed": ar_row["completed"] or 0, "failed": ar_row["failed"] or 0}

    return r


async def get_cost_timeseries(days: int = 30, granularity: str = "day", account_uuid: str | None = None) -> list[dict]:
    db = await get_db()
    acct = "AND account_uuid = ?" if account_uuid else ""
    params = [account_uuid] if account_uuid else []

    if granularity == "week":
        date_expr = "strftime('%Y-W%W', first_timestamp)"
    else:
        date_expr = "date(first_timestamp)"

    rows = await db.execute_fetchall(f"""
        SELECT {date_expr} as period,
               ROUND(SUM(total_cost_usd), 4) as cost_usd,
               ROUND(SUM(actual_cost_usd), 4) as actual_cost_usd,
               COUNT(*) as session_count,
               SUM(total_input_tokens) as input_tokens,
               SUM(total_output_tokens) as output_tokens
        FROM cowork__sessions
        WHERE {_days_filter('first_timestamp', days)} {acct}
        GROUP BY {date_expr}
        ORDER BY period
    """, params)
    return [dict(r) for r in rows]


async def get_tool_usage_stats(days: int = 30, account_uuid: str | None = None, tool_name: str | None = None) -> list[dict]:
    db = await get_db()
    conditions = [_days_filter('tc.timestamp', days)]
    params = []
    if account_uuid:
        conditions.append("tc.account_uuid = ?")
        params.append(account_uuid)
    if tool_name:
        conditions.append("tc.tool_name = ?")
        params.append(tool_name)
    where = " AND ".join(conditions)

    rows = await db.execute_fetchall(f"""
        SELECT tc.tool_name, tc.tool_category,
               COUNT(*) as call_count,
               COALESCE(SUM(CASE WHEN tr.is_error = 1 THEN 1 ELSE 0 END), 0) as error_count,
               ROUND(CAST(COALESCE(SUM(CASE WHEN tr.is_error = 1 THEN 1 ELSE 0 END), 0) AS FLOAT) / COUNT(*), 4) as error_rate
        FROM cowork__tool_calls tc
        LEFT JOIN cowork__tool_results tr ON tc.tool_use_id = tr.tool_use_id
        WHERE {where}
        GROUP BY tc.tool_name, tc.tool_category
        ORDER BY call_count DESC
    """, params)
    return [dict(r) for r in rows]


async def get_activity_timeline(days: int = 7, account_uuid: str | None = None) -> list[dict]:
    db = await get_db()
    acct = "AND s.account_uuid = ?" if account_uuid else ""
    params = [account_uuid] if account_uuid else []

    rows = await db.execute_fetchall(f"""
        SELECT
            date(s.first_timestamp) as date,
            s.session_id,
            s.total_cost_usd,
            s.user_message_count,
            s.assistant_message_count,
            s.primary_model,
            w.title,
            w.cwd,
            w.origin_cwd,
            u.email,
            u.display_name
        FROM cowork__sessions s
        LEFT JOIN cowork__workers w ON s.worker_id = w.worker_id
        LEFT JOIN cowork__users u ON s.account_uuid = u.account_uuid
        WHERE {_days_filter('s.first_timestamp', days)} {acct}
        ORDER BY s.first_timestamp DESC
    """, params)

    # Group by date
    timeline: dict[str, dict] = {}
    for r in rows:
        r = dict(r)
        d = r.pop("date")
        if d not in timeline:
            timeline[d] = {"date": d, "total_cost_usd": 0, "session_count": 0, "sessions": []}
        timeline[d]["total_cost_usd"] += r.get("total_cost_usd") or 0
        timeline[d]["session_count"] += 1
        # Extract project from origin_cwd or cwd
        project = _extract_project(r.get("origin_cwd") or r.get("cwd"))
        timeline[d]["sessions"].append({
            "session_id": r["session_id"],
            "title": r.get("title"),
            "project": project,
            "cost_usd": r.get("total_cost_usd"),
            "messages": (r.get("user_message_count") or 0) + (r.get("assistant_message_count") or 0),
            "model": r.get("primary_model"),
            "user": r.get("display_name") or r.get("email"),
        })
    timeline = {k: {**v, "total_cost_usd": round(v["total_cost_usd"], 4)} for k, v in timeline.items()}
    return sorted(timeline.values(), key=lambda x: x["date"], reverse=True)


def _extract_project(cwd: str | None) -> str | None:
    if not cwd:
        return None
    # /Users/attriai/projects/cpiai_be → cpiai_be
    # /sessions/something → something
    parts = cwd.rstrip("/").split("/")
    return parts[-1] if parts else None


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

async def list_sessions(
    days: int = 30, limit: int = 50, offset: int = 0,
    account_uuid: str | None = None, project: str | None = None,
    sort: str = "recent", order: str = "desc"
) -> dict:
    db = await get_db()
    conditions = [_days_filter('s.first_timestamp', days)]
    params: list = []
    if account_uuid:
        conditions.append("s.account_uuid = ?")
        params.append(account_uuid)
    if project:
        conditions.append("(w.origin_cwd LIKE ? OR w.cwd LIKE ?)")
        params.extend([f"%{project}%", f"%{project}%"])
    where = " AND ".join(conditions)

    sort_map = {"cost": "s.total_cost_usd", "recent": "s.last_timestamp", "messages": "s.user_message_count"}
    sort_col = sort_map.get(sort, "s.last_timestamp")

    count_row = await db.execute_fetchall(f"""
        SELECT COUNT(*) as cnt FROM cowork__sessions s
        LEFT JOIN cowork__workers w ON s.worker_id = w.worker_id
        WHERE {where}
    """, params)
    total = dict(count_row[0])["cnt"]

    rows = await db.execute_fetchall(f"""
        SELECT s.session_id, s.first_timestamp, s.last_timestamp,
               s.user_message_count, s.assistant_message_count,
               s.total_cost_usd, s.actual_cost_usd, s.primary_model,
               s.total_input_tokens, s.total_output_tokens,
               u.email, u.display_name,
               w.title, w.cwd, w.origin_cwd
        FROM cowork__sessions s
        LEFT JOIN cowork__users u ON s.account_uuid = u.account_uuid
        LEFT JOIN cowork__workers w ON s.worker_id = w.worker_id
        WHERE {where}
        ORDER BY {sort_col} {order}
        LIMIT ? OFFSET ?
    """, params + [limit, offset])

    items = []
    for r in rows:
        r = dict(r)
        r["project"] = _extract_project(r.pop("origin_cwd", None) or r.pop("cwd", None))
        items.append(r)

    return {"data": items, "total": total, "limit": limit, "offset": offset}


async def get_session(session_id: str) -> dict | None:
    db = await get_db()
    rows = await db.execute_fetchall("""
        SELECT s.*, u.email, u.display_name,
               w.title, w.cwd, w.origin_cwd, w.model as worker_model,
               w.permission_mode, w.session_type
        FROM cowork__sessions s
        LEFT JOIN cowork__users u ON s.account_uuid = u.account_uuid
        LEFT JOIN cowork__workers w ON s.worker_id = w.worker_id
        WHERE s.session_id = ?
    """, [session_id])
    if not rows:
        return None
    r = dict(rows[0])
    r["project"] = _extract_project(r.get("origin_cwd") or r.get("cwd"))
    return r


async def get_session_messages(session_id: str, msg_type: str | None = None, limit: int = 100, offset: int = 0) -> list[dict]:
    db = await get_db()
    conditions = ["session_id = ?"]
    params: list = [session_id]
    if msg_type:
        conditions.append("type = ?")
        params.append(msg_type)
    where = " AND ".join(conditions)
    rows = await db.execute_fetchall(f"""
        SELECT uuid, type, timestamp, model, cost_usd,
               SUBSTR(content_text, 1, 500) as content_preview,
               input_tokens, output_tokens, has_thinking, git_branch, cwd
        FROM cowork__messages
        WHERE {where}
        ORDER BY timestamp
        LIMIT ? OFFSET ?
    """, params + [limit, offset])
    return [dict(r) for r in rows]


async def get_session_tools(session_id: str) -> list[dict]:
    db = await get_db()
    rows = await db.execute_fetchall("""
        SELECT tc.tool_use_id, tc.tool_name, tc.tool_category, tc.timestamp,
               SUBSTR(tc.tool_input, 1, 200) as input_preview,
               SUBSTR(tr.result_text, 1, 200) as result_preview,
               tr.is_error
        FROM cowork__tool_calls tc
        LEFT JOIN cowork__tool_results tr ON tc.tool_use_id = tr.tool_use_id
        WHERE tc.session_id = ?
        ORDER BY tc.timestamp
    """, [session_id])
    return [dict(r) for r in rows]


async def get_session_audit(session_id: str, event_type: str | None = None, subtype: str | None = None) -> list[dict]:
    db = await get_db()
    conditions = ["session_id = ?"]
    params: list = [session_id]
    if event_type:
        conditions.append("type = ?")
        params.append(event_type)
    if subtype:
        conditions.append("subtype = ?")
        params.append(subtype)
    where = " AND ".join(conditions)
    rows = await db.execute_fetchall(f"""
        SELECT id, type, subtype, uuid, timestamp, content_preview
        FROM cowork__audit_events
        WHERE {where}
        ORDER BY timestamp
        LIMIT 500
    """, params)
    return [dict(r) for r in rows]


async def get_session_summary(session_id: str) -> dict | None:
    """Build an AI-friendly summary of what happened in a session."""
    session = await get_session(session_id)
    if not session:
        return None

    db = await get_db()

    # Get user messages (what was asked)
    user_msgs = await db.execute_fetchall("""
        SELECT SUBSTR(content_text, 1, 300) as content, timestamp
        FROM cowork__messages
        WHERE session_id = ? AND type = 'user' AND content_text IS NOT NULL
        ORDER BY timestamp
        LIMIT 20
    """, [session_id])

    # Get unique tools used
    tools = await db.execute_fetchall("""
        SELECT tool_name, COUNT(*) as cnt
        FROM cowork__tool_calls WHERE session_id = ?
        GROUP BY tool_name ORDER BY cnt DESC
    """, [session_id])

    # Get branches
    branches = await db.execute_fetchall("""
        SELECT DISTINCT git_branch FROM cowork__messages
        WHERE session_id = ? AND git_branch IS NOT NULL
    """, [session_id])

    # Get directories
    dirs = await db.execute_fetchall("""
        SELECT DISTINCT cwd FROM cowork__messages
        WHERE session_id = ? AND cwd IS NOT NULL
    """, [session_id])

    return {
        "session_id": session_id,
        "title": session.get("title"),
        "project": session.get("project"),
        "cost_usd": session.get("total_cost_usd"),
        "model": session.get("primary_model"),
        "user": session.get("display_name") or session.get("email"),
        "start": session.get("first_timestamp"),
        "end": session.get("last_timestamp"),
        "message_count": (session.get("user_message_count") or 0) + (session.get("assistant_message_count") or 0),
        "user_requests": [dict(m) for m in user_msgs],
        "tools_used": [dict(t) for t in tools],
        "git_branches": [dict(b)["git_branch"] for b in branches],
        "directories": [dict(d)["cwd"] for d in dirs],
    }


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

async def list_users(days: int = 30) -> list[dict]:
    db = await get_db()
    rows = await db.execute_fetchall(f"""
        SELECT u.account_uuid, u.email, u.display_name, u.organization_uuid,
               COUNT(s.session_id) as session_count,
               ROUND(COALESCE(SUM(s.total_cost_usd), 0), 4) as total_cost_usd,
               MAX(s.last_timestamp) as last_active,
               COALESCE(SUM(s.user_message_count), 0) as total_messages
        FROM cowork__users u
        LEFT JOIN cowork__sessions s ON u.account_uuid = s.account_uuid
            AND {_days_filter('s.first_timestamp', days)}
        GROUP BY u.account_uuid
        ORDER BY total_cost_usd DESC
    """)
    return [dict(r) for r in rows]


async def get_user_activity(account_uuid: str, days: int = 30) -> list[dict]:
    db = await get_db()
    rows = await db.execute_fetchall(f"""
        SELECT date(s.first_timestamp) as date,
               COUNT(*) as session_count,
               COALESCE(SUM(s.user_message_count + s.assistant_message_count), 0) as message_count,
               ROUND(SUM(s.total_cost_usd), 4) as cost_usd
        FROM cowork__sessions s
        WHERE s.account_uuid = ? AND {_days_filter('s.first_timestamp', days)}
        GROUP BY date(s.first_timestamp)
        ORDER BY date DESC
    """, [account_uuid])
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

async def list_projects(days: int = 30, account_uuid: str | None = None) -> list[dict]:
    db = await get_db()
    acct = "AND s.account_uuid = ?" if account_uuid else ""
    params = [account_uuid] if account_uuid else []

    rows = await db.execute_fetchall(f"""
        SELECT
            COALESCE(w.origin_cwd, w.cwd) as project_path,
            COUNT(DISTINCT s.session_id) as session_count,
            ROUND(SUM(s.total_cost_usd), 4) as total_cost_usd,
            MAX(s.last_timestamp) as last_active,
            COUNT(DISTINCT s.account_uuid) as user_count,
            SUM(s.user_message_count) as total_messages
        FROM cowork__sessions s
        LEFT JOIN cowork__workers w ON s.worker_id = w.worker_id
        WHERE {_days_filter('s.first_timestamp', days)} {acct}
            AND (w.origin_cwd IS NOT NULL OR w.cwd IS NOT NULL)
        GROUP BY COALESCE(w.origin_cwd, w.cwd)
        ORDER BY total_cost_usd DESC
    """, params)

    result = []
    for r in rows:
        r = dict(r)
        r["project_name"] = _extract_project(r.get("project_path"))
        result.append(r)
    return result


async def get_project_sessions(project_name: str, days: int = 30) -> list[dict]:
    db = await get_db()
    rows = await db.execute_fetchall(f"""
        SELECT s.session_id, s.first_timestamp, s.last_timestamp,
               s.user_message_count, s.total_cost_usd, s.primary_model,
               u.email, u.display_name, w.title
        FROM cowork__sessions s
        LEFT JOIN cowork__workers w ON s.worker_id = w.worker_id
        LEFT JOIN cowork__users u ON s.account_uuid = u.account_uuid
        WHERE {_days_filter('s.first_timestamp', days)}
            AND (w.origin_cwd LIKE ? OR w.cwd LIKE ?)
        ORDER BY s.first_timestamp DESC
    """, [f"%{project_name}%", f"%{project_name}%"])
    return [dict(r) for r in rows]


async def get_project_stats(project_name: str, days: int = 30) -> dict:
    db = await get_db()
    rows = await db.execute_fetchall(f"""
        SELECT
            COUNT(DISTINCT s.session_id) as session_count,
            ROUND(SUM(s.total_cost_usd), 4) as total_cost_usd,
            SUM(s.user_message_count) as total_user_messages,
            SUM(s.assistant_message_count) as total_assistant_messages,
            SUM(s.total_input_tokens) as total_input_tokens,
            SUM(s.total_output_tokens) as total_output_tokens,
            COUNT(DISTINCT s.account_uuid) as user_count,
            MIN(s.first_timestamp) as first_session,
            MAX(s.last_timestamp) as last_session
        FROM cowork__sessions s
        LEFT JOIN cowork__workers w ON s.worker_id = w.worker_id
        WHERE {_days_filter('s.first_timestamp', days)}
            AND (w.origin_cwd LIKE ? OR w.cwd LIKE ?)
    """, [f"%{project_name}%", f"%{project_name}%"])
    result = dict(rows[0]) if rows else {}
    result["project_name"] = project_name

    # Top tools for this project
    tools = await db.execute_fetchall(f"""
        SELECT tc.tool_name, COUNT(*) as cnt
        FROM cowork__tool_calls tc
        JOIN cowork__sessions s ON tc.session_id = s.session_id
        LEFT JOIN cowork__workers w ON s.worker_id = w.worker_id
        WHERE {_days_filter('s.first_timestamp', days)}
            AND (w.origin_cwd LIKE ? OR w.cwd LIKE ?)
        GROUP BY tc.tool_name ORDER BY cnt DESC LIMIT 10
    """, [f"%{project_name}%", f"%{project_name}%"])
    result["top_tools"] = [dict(t) for t in tools]
    return result


# ---------------------------------------------------------------------------
# Messages search
# ---------------------------------------------------------------------------

async def search_messages(
    query: str, days: int = 7, account_uuid: str | None = None,
    msg_type: str | None = None, limit: int = 25
) -> list[dict]:
    db = await get_db()
    conditions = [_days_filter('m.timestamp', days), "m.content_text LIKE ?"]
    params: list = [f"%{query}%"]
    if account_uuid:
        conditions.append("m.account_uuid = ?")
        params.append(account_uuid)
    if msg_type:
        conditions.append("m.type = ?")
        params.append(msg_type)
    where = " AND ".join(conditions)

    rows = await db.execute_fetchall(f"""
        SELECT m.uuid, m.session_id, m.type, m.timestamp,
               SUBSTR(m.content_text, 1, 300) as content_preview,
               m.git_branch, m.cwd, m.model,
               u.email, u.display_name
        FROM cowork__messages m
        LEFT JOIN cowork__users u ON m.account_uuid = u.account_uuid
        WHERE {where}
        ORDER BY m.timestamp DESC
        LIMIT ?
    """, params + [limit])
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Compliance
# ---------------------------------------------------------------------------

async def list_compliance_activities(
    days: int = 30, activity_type: str | None = None,
    actor_email: str | None = None, limit: int = 50, offset: int = 0
) -> dict:
    db = await get_db()
    conditions = [_days_filter('source_created_at', days)]
    params: list = []
    if activity_type:
        conditions.append("activity_type = ?")
        params.append(activity_type)
    if actor_email:
        conditions.append("actor_email = ?")
        params.append(actor_email)
    where = " AND ".join(conditions)

    count_row = await db.execute_fetchall(f"SELECT COUNT(*) as cnt FROM compliance__claude_activities WHERE {where}", params)
    total = dict(count_row[0])["cnt"]

    rows = await db.execute_fetchall(f"""
        SELECT activity_id, activity_type, actor_email, actor_type,
               request_method, request_url, status_code,
               source_created_at, organization_uuid
        FROM compliance__claude_activities
        WHERE {where}
        ORDER BY source_created_at DESC
        LIMIT ? OFFSET ?
    """, params + [limit, offset])
    return {"data": [dict(r) for r in rows], "total": total, "limit": limit, "offset": offset}


async def get_compliance_summary(days: int = 30) -> dict:
    db = await get_db()
    by_type = await db.execute_fetchall(f"""
        SELECT activity_type, COUNT(*) as cnt
        FROM compliance__claude_activities
        WHERE {_days_filter('source_created_at', days)}
        GROUP BY activity_type ORDER BY cnt DESC
    """)
    by_actor = await db.execute_fetchall(f"""
        SELECT actor_email, COUNT(*) as cnt
        FROM compliance__claude_activities
        WHERE {_days_filter('source_created_at', days)} AND actor_email IS NOT NULL
        GROUP BY actor_email ORDER BY cnt DESC
    """)
    by_status = await db.execute_fetchall(f"""
        SELECT status_code, COUNT(*) as cnt
        FROM compliance__claude_activities
        WHERE {_days_filter('source_created_at', days)}
        GROUP BY status_code ORDER BY cnt DESC
    """)
    return {
        "by_type": [dict(r) for r in by_type],
        "by_actor": [dict(r) for r in by_actor],
        "by_status": [dict(r) for r in by_status],
    }


async def list_compliance_chats(limit: int = 50, offset: int = 0) -> list[dict]:
    db = await get_db()
    rows = await db.execute_fetchall("""
        SELECT id, claude_chat_id, name, organization_id, project_id, user_id,
               messages_synced, source_created_at, source_updated_at
        FROM compliance__claude_chats
        ORDER BY source_updated_at DESC
        LIMIT ? OFFSET ?
    """, [limit, offset])
    return [dict(r) for r in rows]


async def get_chat_messages(chat_id: int) -> list[dict]:
    db = await get_db()
    rows = await db.execute_fetchall("""
        SELECT claude_message_id, role, content, source_created_at
        FROM compliance__claude_chat_messages
        WHERE chat_id = ?
        ORDER BY source_created_at
    """, [chat_id])
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Agent Runs
# ---------------------------------------------------------------------------

async def list_agent_runs(
    days: int = 90, agent_type: str | None = None,
    status: str | None = None, limit: int = 50, offset: int = 0
) -> dict:
    db = await get_db()
    conditions = [_days_filter('created_at', days)]
    params: list = []
    if agent_type:
        conditions.append("agent_type = ?")
        params.append(agent_type)
    if status:
        conditions.append("status = ?")
        params.append(status)
    where = " AND ".join(conditions)

    count_row = await db.execute_fetchall(f"SELECT COUNT(*) as cnt FROM agent__runs WHERE {where}", params)
    total = dict(count_row[0])["cnt"]

    rows = await db.execute_fetchall(f"""
        SELECT run_uuid, agent_type, status, created_at, finished_at,
               total_cost_usd, total_tokens_in, total_tokens_out,
               total_duration_ms, total_turns, target_email, target_month,
               primary_model, error
        FROM agent__runs WHERE {where}
        ORDER BY created_at DESC LIMIT ? OFFSET ?
    """, params + [limit, offset])
    return {"data": [dict(r) for r in rows], "total": total, "limit": limit, "offset": offset}


async def get_agent_run(run_uuid: str) -> dict | None:
    db = await get_db()
    rows = await db.execute_fetchall("""
        SELECT * FROM agent__runs WHERE run_uuid = ?
    """, [run_uuid])
    if not rows:
        return None
    run = dict(rows[0])

    stages = await db.execute_fetchall("""
        SELECT * FROM agent__stages WHERE run_id = ? ORDER BY stage_number
    """, [run["id"]])
    run["stages"] = [dict(s) for s in stages]
    return run


async def get_agent_outputs(run_uuid: str) -> list[dict]:
    db = await get_db()
    # First get run_id from run_uuid
    run = await db.execute_fetchall("SELECT id FROM agent__runs WHERE run_uuid = ?", [run_uuid])
    if not run:
        return []
    run_id = dict(run[0])["id"]
    rows = await db.execute_fetchall("""
        SELECT filename, agent_type, output_type, size_bytes, created_at,
               SUBSTR(content, 1, 1000) as content_preview
        FROM agent__outputs WHERE run_id = ?
    """, [run_id])
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Audit Events (cross-session search)
# ---------------------------------------------------------------------------

async def search_audit_events(
    session_id: str | None = None, event_type: str | None = None,
    subtype: str | None = None, days: int = 7, limit: int = 25
) -> list[dict]:
    db = await get_db()
    conditions = [_days_filter('timestamp', days)]
    params: list = []
    if session_id:
        conditions.append("session_id = ?")
        params.append(session_id)
    if event_type:
        conditions.append("type = ?")
        params.append(event_type)
    if subtype:
        conditions.append("subtype = ?")
        params.append(subtype)
    where = " AND ".join(conditions)

    rows = await db.execute_fetchall(f"""
        SELECT id, session_id, type, subtype, uuid, timestamp, content_preview
        FROM cowork__audit_events
        WHERE {where}
        ORDER BY timestamp DESC LIMIT ?
    """, params + [limit])
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Cost Breakdown
# ---------------------------------------------------------------------------

async def get_cost_breakdown(group_by: str = "day", days: int = 30) -> list[dict]:
    db = await get_db()
    if group_by == "user":
        rows = await db.execute_fetchall(f"""
            SELECT u.email, u.display_name, s.account_uuid,
                   COUNT(*) as session_count,
                   ROUND(SUM(s.total_cost_usd), 4) as total_cost_usd,
                   SUM(s.total_input_tokens) as total_input_tokens,
                   SUM(s.total_output_tokens) as total_output_tokens
            FROM cowork__sessions s
            LEFT JOIN cowork__users u ON s.account_uuid = u.account_uuid
            WHERE {_days_filter('s.first_timestamp', days)}
            GROUP BY s.account_uuid ORDER BY total_cost_usd DESC
        """)
    elif group_by == "model":
        rows = await db.execute_fetchall(f"""
            SELECT primary_model as model,
                   COUNT(*) as session_count,
                   ROUND(SUM(total_cost_usd), 4) as total_cost_usd,
                   SUM(total_input_tokens) as total_input_tokens,
                   SUM(total_output_tokens) as total_output_tokens
            FROM cowork__sessions
            WHERE {_days_filter('first_timestamp', days)}
            GROUP BY primary_model ORDER BY total_cost_usd DESC
        """)
    elif group_by == "project":
        rows = await db.execute_fetchall(f"""
            SELECT COALESCE(w.origin_cwd, w.cwd) as project_path,
                   COUNT(*) as session_count,
                   ROUND(SUM(s.total_cost_usd), 4) as total_cost_usd,
                   SUM(s.total_input_tokens) as total_input_tokens,
                   SUM(s.total_output_tokens) as total_output_tokens
            FROM cowork__sessions s
            LEFT JOIN cowork__workers w ON s.worker_id = w.worker_id
            WHERE {_days_filter('s.first_timestamp', days)}
            GROUP BY COALESCE(w.origin_cwd, w.cwd) ORDER BY total_cost_usd DESC
        """)
    else:  # day
        rows = await db.execute_fetchall(f"""
            SELECT date(first_timestamp) as date,
                   COUNT(*) as session_count,
                   ROUND(SUM(total_cost_usd), 4) as total_cost_usd,
                   SUM(total_input_tokens) as total_input_tokens,
                   SUM(total_output_tokens) as total_output_tokens
            FROM cowork__sessions
            WHERE {_days_filter('first_timestamp', days)}
            GROUP BY date(first_timestamp) ORDER BY date DESC
        """)

    result = [dict(r) for r in rows]
    if group_by == "project":
        for r in result:
            r["project_name"] = _extract_project(r.get("project_path"))
    return result


# ---------------------------------------------------------------------------
# Raw Query (read-only)
# ---------------------------------------------------------------------------

async def run_query(sql: str) -> list[dict]:
    sql_stripped = sql.strip().upper()
    if not sql_stripped.startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed")
    for forbidden in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "ATTACH"]:
        if forbidden in sql_stripped:
            raise ValueError(f"{forbidden} is not allowed — read-only queries only")

    db = await get_db()
    rows = await db.execute_fetchall(sql)
    return [dict(r) for r in rows[:500]]
