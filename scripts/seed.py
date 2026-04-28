"""Bootstrap a fresh OpenWatch SQLite database with the schema and a small set of sample rows.

Usage:
    python scripts/seed.py                     # writes ./data/openwatch.db
    OPENWATCH_DB=/tmp/dev.db python scripts/seed.py

If the target DB already exists it is overwritten.
"""

from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "scripts" / "schema.sql"
DB_PATH = Path(os.getenv("OPENWATCH_DB", str(ROOT / "data" / "openwatch.db")))


def now_iso(offset_minutes: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=offset_minutes)).isoformat()


def reset_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_PATH.read_text())
    return conn


def seed_users(conn: sqlite3.Connection) -> list[str]:
    rows = [
        (str(uuid.uuid4()), "alice@example.com", "Alice"),
        (str(uuid.uuid4()), "bob@example.com", "Bob"),
        (str(uuid.uuid4()), "carol@example.com", "Carol"),
    ]
    for uid, email, name in rows:
        conn.execute(
            "INSERT INTO cowork__users (account_uuid, email, display_name) VALUES (?, ?, ?)",
            (uid, email, name),
        )
    return [r[0] for r in rows]


def seed_sessions(conn: sqlite3.Connection, user_ids: list[str]) -> None:
    for i, uid in enumerate(user_ids):
        sid = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO cowork__sessions
               (session_id, account_uuid, started_at, last_activity_at, project_name)
               VALUES (?, ?, ?, ?, ?)""",
            (sid, uid, now_iso(60 * (i + 1)), now_iso(i * 5), f"sample-project-{i + 1}"),
        )


def seed_agent_runs(conn: sqlite3.Connection) -> None:
    for i in range(3):
        conn.execute(
            """INSERT INTO agent__runs (run_uuid, agent_type, status, started_at, ended_at)
               VALUES (?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), "sql_retriever", "succeeded", now_iso(30 + i * 10), now_iso(29 + i * 10)),
        )


def main() -> None:
    if not SCHEMA_PATH.exists():
        raise SystemExit(f"schema not found at {SCHEMA_PATH} — run from repo root")
    print(f"→ resetting {DB_PATH}")
    conn = reset_db()
    try:
        # Seeders are best-effort: skip silently if a column the demo expects has changed.
        try:
            user_ids = seed_users(conn)
            seed_sessions(conn, user_ids)
        except sqlite3.OperationalError as e:
            print(f"  ! skipped cowork seed: {e}")
        try:
            seed_agent_runs(conn)
        except sqlite3.OperationalError as e:
            print(f"  ! skipped agent seed: {e}")
        conn.commit()
    finally:
        conn.close()
    print(f"✓ seeded {DB_PATH}")


if __name__ == "__main__":
    main()
