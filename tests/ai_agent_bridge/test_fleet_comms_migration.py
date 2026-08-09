from __future__ import annotations

import sqlite3

from scripts.ai_agent_bridge import _db
from scripts.fleet_comms import migrations
from scripts.fleet_comms.migrations import MIGRATIONS


def test_bridge_upgrades_legacy_copy_without_mutating_legacy_rows(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "messages.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, from_llm TEXT NOT NULL,
            to_llm TEXT NOT NULL, message_type TEXT, content TEXT NOT NULL, data TEXT,
            timestamp TEXT NOT NULL, acknowledged INTEGER DEFAULT 0
        )"""
    )
    conn.execute(
        "INSERT INTO messages(task_id, from_llm, to_llm, content, timestamp) VALUES ('legacy', 'codex', 'agy', 'body', 'now')"
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(_db, "DB_PATH", db_path)

    migrated = _db.get_db()
    try:
        assert migrated.execute("SELECT content FROM messages WHERE task_id = 'legacy'").fetchone()[0] == "body"
        assert (
            migrated.execute("SELECT MAX(version) FROM comms_schema_migrations").fetchone()[0]
            == MIGRATIONS[-1].version
        )
        tables = {row[0] for row in migrated.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        assert {
            "comms_messages",
            "requests",
            "artifacts",
            "formal_review_jobs",
            "acp_conversations",
            "acp_conversation_events",
        }.issubset(tables)
    finally:
        migrated.close()


def test_apply_migrations_closes_prelock_read_transaction_and_returns_version(
    tmp_path, monkeypatch
) -> None:
    """A transaction retained by the optimistic read must not nest BEGIN IMMEDIATE."""
    conn = sqlite3.connect(tmp_path / "messages.db")
    original_applied_migrations = migrations._applied_migrations
    calls = 0

    def retain_initial_read_transaction(connection: sqlite3.Connection):
        nonlocal calls
        applied = original_applied_migrations(connection)
        if calls == 0:
            calls += 1
            connection.execute("BEGIN")
        return applied

    monkeypatch.setattr(migrations, "_applied_migrations", retain_initial_read_transaction)
    try:
        applied_version = migrations.apply_migrations(conn)
        assert isinstance(applied_version, int)
        assert applied_version == MIGRATIONS[-1].version
        assert conn.in_transaction is False
    finally:
        conn.close()
