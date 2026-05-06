"""Add broker indexes for bounded comms dashboard reads.

The original issue text used the logical names ``to_agent``/``from_agent``
and ``created_at`` for the legacy message bus. The live legacy table in
this repo is named ``messages`` and uses ``to_llm``/``from_llm`` plus
``timestamp``. Channel tables already use ``created_at``.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = PROJECT_ROOT / ".mcp" / "servers" / "message-broker" / "messages.db"


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def apply(conn: sqlite3.Connection) -> None:
    """Apply the broker index migration idempotently."""
    if _table_exists(conn, "messages"):
        columns = _table_columns(conn, "messages")
        if {"to_llm", "timestamp"}.issubset(columns):
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_to_agent_created
                ON messages(to_llm, timestamp DESC)
                """
            )
        if {"from_llm", "timestamp"}.issubset(columns):
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_from_agent_created
                ON messages(from_llm, timestamp DESC)
                """
            )
        if "task_id" in columns:
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_task_id
                ON messages(task_id)
                """
            )

    if _table_exists(conn, "channel_messages"):
        columns = _table_columns(conn, "channel_messages")
        if {"channel", "created_at"}.issubset(columns):
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_channel_messages_channel_created
                ON channel_messages(channel, created_at DESC)
                """
            )
        if {"thread_id", "channel", "round_index", "created_at"}.issubset(columns):
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_channel_messages_thread_id
                ON channel_messages(thread_id, channel, round_index, created_at)
                """
            )

    if _table_exists(conn, "deliveries"):
        columns = _table_columns(conn, "deliveries")
        if {"to_agent", "status"}.issubset(columns):
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_deliveries_to_agent_status
                ON deliveries(to_agent, status)
                """
            )

    conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Add broker indexes for comms hot paths.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    if not args.db.exists():
        raise SystemExit(f"Broker DB not found: {args.db}")

    with sqlite3.connect(str(args.db)) as conn:
        apply(conn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
