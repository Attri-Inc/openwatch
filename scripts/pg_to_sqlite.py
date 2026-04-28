#!/usr/bin/env python3
"""Convert local PostgreSQL database to SQLite.

Reads from local Postgres (claude_audit_local) and writes to data/openwatch.db.
No dump parsing — just reads tables directly.
"""

import sqlite3
from pathlib import Path

import psycopg2
import psycopg2.extras

SQLITE_DB = Path(__file__).resolve().parent.parent / "data" / "openwatch.db"
PG_DSN = "dbname=claude_audit_local"
SCHEMAS = ["cowork", "compliance", "agent"]


def pg_type_to_sqlite(pg_type: str) -> str:
    mapping = {
        "bigint": "INTEGER", "integer": "INTEGER", "smallint": "INTEGER",
        "boolean": "INTEGER", "text": "TEXT", "character varying": "TEXT",
        "uuid": "TEXT", "jsonb": "TEXT", "json": "TEXT",
        "timestamp with time zone": "TEXT", "timestamp without time zone": "TEXT",
        "date": "TEXT", "numeric": "REAL", "double precision": "REAL",
        "real": "REAL", "bytea": "BLOB",
    }
    for k, v in mapping.items():
        if pg_type.startswith(k):
            return v
    return "TEXT"


def main():
    SQLITE_DB.parent.mkdir(parents=True, exist_ok=True)
    if SQLITE_DB.exists():
        SQLITE_DB.unlink()

    pg = psycopg2.connect(PG_DSN)
    pg_cur = pg.cursor()

    sq = sqlite3.connect(str(SQLITE_DB))
    sq.execute("PRAGMA journal_mode=WAL")
    sq.execute("PRAGMA synchronous=NORMAL")
    sq_cur = sq.cursor()

    total_tables = 0
    total_rows = 0

    for schema in SCHEMAS:
        # Get all tables in schema
        pg_cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """, (schema,))
        tables = [r[0] for r in pg_cur.fetchall()]

        for table in tables:
            sqlite_table = f"{schema}__{table}"

            # Get column info
            pg_cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (schema, table))
            columns = pg_cur.fetchall()

            if not columns:
                continue

            # Build CREATE TABLE
            col_defs = []
            col_names = []
            for col_name, data_type, nullable, default in columns:
                sqlite_type = pg_type_to_sqlite(data_type)
                parts = [col_name, sqlite_type]
                if nullable == "NO":
                    parts.append("NOT NULL")
                col_defs.append(" ".join(parts))
                col_names.append(col_name)

            create_sql = f"CREATE TABLE {sqlite_table} (\n  " + ",\n  ".join(col_defs) + "\n);"
            sq_cur.execute(create_sql)
            total_tables += 1

            # Copy data
            pg_cur.execute(f'SELECT * FROM {schema}."{table}"')
            rows = pg_cur.fetchall()
            if rows:
                placeholders = ",".join(["?"] * len(col_names))
                cols = ",".join(col_names)
                insert_sql = f"INSERT INTO {sqlite_table} ({cols}) VALUES ({placeholders})"

                # Convert values (booleans, etc.)
                converted = []
                for row in rows:
                    converted.append(tuple(
                        int(v) if isinstance(v, bool)
                        else str(v) if v is not None and not isinstance(v, (int, float, str, bytes, type(None)))
                        else v
                        for v in row
                    ))

                sq_cur.executemany(insert_sql, converted)
                total_rows += len(rows)
                print(f"  {sqlite_table}: {len(rows)} rows")
            else:
                print(f"  {sqlite_table}: (empty)")

            sq.commit()

    # Create indexes
    print("\nCreating indexes...")
    indexes = [
        ("cowork__sessions", "account_uuid"),
        ("cowork__messages", "session_uuid"),
        ("cowork__tool_calls", "session_uuid"),
        ("cowork__audit_events", "session_uuid"),
        ("compliance__claude_chats", "organization_id"),
        ("compliance__claude_activities", "organization_id"),
        ("agent__runs", "agent_type"),
        ("agent__runs", "status"),
        ("agent__outputs", "run_id"),
    ]
    for tbl, col in indexes:
        try:
            sq_cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{tbl}_{col} ON {tbl}({col})")
        except Exception as e:
            print(f"  Skip {tbl}.{col}: {e}")

    sq.commit()
    pg.close()
    sq.close()

    db_size = SQLITE_DB.stat().st_size / (1024 * 1024)
    print(f"\nDone! {total_tables} tables, {total_rows} rows → {SQLITE_DB} ({db_size:.1f} MB)")


if __name__ == "__main__":
    main()
