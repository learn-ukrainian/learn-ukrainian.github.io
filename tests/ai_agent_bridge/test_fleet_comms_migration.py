from __future__ import annotations

import sqlite3

from scripts.ai_agent_bridge import _db


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
        assert migrated.execute("SELECT MAX(version) FROM comms_schema_migrations").fetchone()[0] == 2
        tables = {row[0] for row in migrated.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        assert {"comms_messages", "requests", "artifacts", "formal_review_jobs"}.issubset(tables)
    finally:
        migrated.close()
