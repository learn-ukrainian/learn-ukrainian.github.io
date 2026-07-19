"""Tests for large ask-reply sidecars (#5392) and empty-body transport guard (#4915)."""

from __future__ import annotations

import json
import sqlite3
from unittest.mock import patch

import pytest

from scripts.ai_agent_bridge import _reply_sidecar
from scripts.ai_agent_bridge._ask_lifecycle import assert_ask_content_present


def test_looks_truncated_detects_mid_diff_tail():
    body = "Here is analysis.\n\nNow the complete unified diff:\n"
    assert _reply_sidecar.looks_truncated(body) is True


def test_small_response_stays_inline(tmp_path, monkeypatch):
    monkeypatch.setattr(_reply_sidecar, "_SIDECAR_ROOT", tmp_path / "asks")
    monkeypatch.setenv("AB_REPLY_INLINE_MAX_BYTES", "10000")
    result = _reply_sidecar.maybe_sidecare_response(
        "short ok",
        task_id="t-small",
        from_llm="glm",
        msg_type="response",
    )
    assert result.truncated is False
    assert result.sidecar_path is None
    assert result.content == "short ok"


def test_large_response_writes_sidecar_and_truncated_footer(tmp_path, monkeypatch):
    monkeypatch.setattr(_reply_sidecar, "_SIDECAR_ROOT", tmp_path / "asks")
    monkeypatch.setenv("AB_REPLY_INLINE_MAX_BYTES", "200")
    monkeypatch.setenv("AB_REPLY_INLINE_HEAD_BYTES", "80")
    body = "A" * 500 + "\n## VERDICT: APPROVED\n"
    result = _reply_sidecar.maybe_sidecare_response(
        body,
        task_id="t-large",
        from_llm="pool",
        msg_type="response",
    )
    assert result.truncated is True
    assert result.sidecar_path is not None
    assert "TRUNCATED" in result.content
    assert f"bytes: {result.full_bytes}" in result.content
    assert result.full_sha256 in result.content
    candidates = list((tmp_path / "asks").rglob("reply-*.md"))
    assert len(candidates) == 1
    assert candidates[0].read_text(encoding="utf-8") == body


def test_ask_query_never_sidecared(tmp_path, monkeypatch):
    monkeypatch.setattr(_reply_sidecar, "_SIDECAR_ROOT", tmp_path / "asks")
    monkeypatch.setenv("AB_REPLY_INLINE_MAX_BYTES", "10")
    body = "Q" * 500
    result = _reply_sidecar.maybe_sidecare_response(
        body,
        task_id="t-query",
        from_llm="claude",
        msg_type="query",
    )
    assert result.truncated is False
    assert result.content == body


def test_send_message_large_response_records_sidecar_metadata(tmp_path, monkeypatch):
    from scripts.ai_agent_bridge import _messaging

    monkeypatch.setattr(_reply_sidecar, "_SIDECAR_ROOT", tmp_path / "asks")
    monkeypatch.setenv("AB_REPLY_INLINE_MAX_BYTES", "100")
    monkeypatch.setenv("AB_REPLY_INLINE_HEAD_BYTES", "40")

    db_path = tmp_path / "msg.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT, from_llm TEXT NOT NULL, to_llm TEXT NOT NULL,
            message_type TEXT DEFAULT 'message', content TEXT NOT NULL,
            data TEXT, timestamp TEXT NOT NULL, acknowledged INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending'
        )"""
    )
    conn.commit()
    conn.close()

    def _fresh_conn():
        return sqlite3.connect(str(db_path))

    body = "B" * 400
    with (
        patch("scripts.ai_agent_bridge._messaging.get_db", side_effect=_fresh_conn),
        patch("subprocess.run"),
    ):
        msg_id = _messaging.send_message(
            body,
            task_id="t-meta",
            msg_type="response",
            from_llm="glm",
            to_llm="claude",
            quiet=True,
        )

    conn = sqlite3.connect(str(db_path))
    row = conn.execute("SELECT content, data FROM messages WHERE id = ?", (msg_id,)).fetchone()
    conn.close()
    assert "TRUNCATED" in row[0]
    meta = json.loads(row[1])
    assert meta["reply_sidecar"]["truncated"] is True
    assert meta["reply_sidecar"]["bytes"] == len(body.encode("utf-8"))


def test_assert_ask_content_present_ok():
    text = assert_ask_content_present(
        {"content": "hello world"},
        message_id=1,
        target="grok",
    )
    assert text == "hello world"


def test_assert_ask_content_present_empty_raises_transport(tmp_path):
    db_path = tmp_path / "msg.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT, from_llm TEXT NOT NULL, to_llm TEXT NOT NULL,
            message_type TEXT DEFAULT 'message', content TEXT NOT NULL,
            data TEXT, timestamp TEXT NOT NULL, acknowledged INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending'
        )"""
    )
    conn.execute(
        "INSERT INTO messages (task_id, from_llm, to_llm, message_type, content, timestamp, status) "
        "VALUES ('t', 'claude', 'grok', 'query', '', '2026-07-19T00:00:00Z', 'processing')"
    )
    mid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    def _fresh_conn():
        return sqlite3.connect(str(db_path))

    with patch("scripts.ai_agent_bridge._ask_lifecycle.get_db", side_effect=_fresh_conn):
        with pytest.raises(ValueError, match="transport empty-ask-body"):
            assert_ask_content_present({"content": ""}, message_id=mid, target="grok")

        conn = sqlite3.connect(str(db_path))
        status = conn.execute("SELECT status FROM messages WHERE id = ?", (mid,)).fetchone()[0]
        conn.close()
        assert status.startswith("failed:")
        assert "transport empty-ask-body" in status


def test_pending_backlog_skips_dead_lane(monkeypatch):
    """#5113: warnings must not nag retired gemini deliveries."""
    from scripts.ai_agent_bridge import _channels_cli

    monkeypatch.setenv("AB_DEAD_LANES", "gemini")

    class _Row(dict):
        def __getitem__(self, key):
            return dict.__getitem__(self, key)

    fake_rows = [
        _Row(to_agent="gemini", count=7, oldest_created_at="2026-07-01T00:00:00+00:00"),
        _Row(to_agent="claude", count=1, oldest_created_at="2026-07-01T00:00:00+00:00"),
    ]

    class _Conn:
        def execute(self, *_a, **_k):
            class _R:
                def fetchall(self_inner):
                    return fake_rows

            return _R()

        def close(self):
            return None

    with patch("scripts.ai_agent_bridge._db.get_db", return_value=_Conn()):
        rows = _channels_cli._pending_backlog_rows()
    agents = {r["agent"] for r in rows}
    assert "gemini" not in agents
    assert "claude" in agents
