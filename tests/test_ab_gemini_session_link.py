from __future__ import annotations

import json
import sqlite3
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.errors import AgentTimeoutError
from ai_agent_bridge import _channels, _db, _gemini_session_link, _inbox


@pytest.fixture(autouse=True)
def isolate_db(tmp_path):
    db_file = tmp_path / "messages.db"
    with patch("ai_agent_bridge._config.DB_PATH", db_file), patch(
        "ai_agent_bridge._db.DB_PATH", db_file
    ):
        _db.init_db()
        yield


def _session_filename(start_time: datetime, suffix: str) -> str:
    safe = start_time.astimezone(UTC).strftime("%Y-%m-%dT%H-%M-%S.%fZ")
    return f"session-{safe}-{suffix}.json"


def _write_session(
    chats_root: Path,
    *,
    start_time: datetime,
    session_id: str,
    messages: list[dict[str, object]],
    project_name: str = "learn-ukrainian",
) -> Path:
    chats_dir = chats_root / project_name / "chats"
    chats_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "sessionId": session_id,
        "startTime": start_time.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "messages": messages,
    }
    path = chats_dir / _session_filename(start_time, session_id[-4:])
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _make_thread(agent: str, *, body: str = "please review this") -> dict[str, object]:
    if _channels.get_channel("topic") is None:
        _channels.create_channel("topic")
    return _channels.post(
        "topic",
        "user",
        body,
        to_agents=[agent],
        auto_snapshot=False,
    )


def _delivery_row(message_id: str) -> sqlite3.Row:
    conn = _db.get_db()
    try:
        row = conn.execute(
            "SELECT status, error, last_error_kind, to_model FROM deliveries WHERE message_id = ?",
            (message_id,),
        ).fetchone()
        assert row is not None
        return row
    finally:
        conn.close()


def test_find_session_recovery_returns_last_non_empty_gemini_message(tmp_path):
    started_at = datetime.now(UTC)
    _write_session(
        tmp_path,
        start_time=started_at,
        session_id="session-final",
        messages=[
            {
                "type": "user",
                "content": [{"text": "please review this carefully"}],
            },
            {
                "type": "gemini",
                "model": "gemini-3.1-pro-preview",
                "content": [{"text": "draft"}],
            },
            {
                "type": "gemini",
                "model": "gemini-3.1-pro-preview",
                "content": [],
            },
            {
                "type": "gemini",
                "model": "gemini-3.1-pro-preview",
                "content": [{"text": "final answer"}],
            },
        ],
    )

    recovery = _gemini_session_link.find_session_recovery(
        delivery_brief="please review this carefully",
        started_at=started_at,
        chats_root=tmp_path,
    )

    assert recovery is not None
    assert recovery.session_id == "session-final"
    assert recovery.text == "final answer"


def test_find_session_recovery_returns_none_when_no_candidate_matches(tmp_path):
    started_at = datetime.now(UTC)
    _write_session(
        tmp_path,
        start_time=started_at + timedelta(minutes=5),
        session_id="session-far",
        messages=[
            {"type": "user", "content": [{"text": "unrelated"}]},
            {"type": "gemini", "content": [{"text": "answer"}]},
        ],
    )

    recovery = _gemini_session_link.find_session_recovery(
        delivery_brief="please review this carefully",
        started_at=started_at,
        chats_root=tmp_path,
    )

    assert recovery is None


def test_find_session_recovery_returns_none_when_last_gemini_message_is_empty(tmp_path):
    started_at = datetime.now(UTC)
    _write_session(
        tmp_path,
        start_time=started_at,
        session_id="session-empty",
        messages=[
            {"type": "user", "content": [{"text": "please review this carefully"}]},
            {"type": "gemini", "content": []},
        ],
    )

    recovery = _gemini_session_link.find_session_recovery(
        delivery_brief="please review this carefully",
        started_at=started_at,
        chats_root=tmp_path,
    )

    assert recovery is None


def test_find_session_recovery_prefers_brief_match_when_windows_overlap(tmp_path):
    started_at = datetime.now(UTC)
    brief = "Please review module #1235 and summarize the blockers clearly."
    _write_session(
        tmp_path,
        start_time=started_at + timedelta(seconds=1),
        session_id="session-wrong",
        messages=[
            {"type": "user", "content": [{"text": "Completely different task"}]},
            {"type": "gemini", "content": [{"text": "wrong reply"}]},
        ],
    )
    _write_session(
        tmp_path,
        start_time=started_at + timedelta(seconds=20),
        session_id="session-right",
        messages=[
            {"type": "user", "content": [{"text": f"Context\n\n{brief}\n\nReply once."}]},
            {"type": "gemini", "content": [{"text": "right reply"}]},
        ],
    )

    recovery = _gemini_session_link.find_session_recovery(
        delivery_brief=brief,
        started_at=started_at,
        chats_root=tmp_path,
    )

    assert recovery is not None
    assert recovery.session_id == "session-right"
    assert recovery.text == "right reply"


@patch("ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_gemini_timeout_recovers_session_reply(mock_invoke, tmp_path):
    thread = _make_thread("gemini", body="please review this carefully")
    started_at = datetime.now(UTC)
    _write_session(
        tmp_path,
        start_time=started_at,
        session_id="session-timeout",
        messages=[
            {"type": "user", "content": [{"text": "Context\n\nplease review this carefully"}]},
            {
                "type": "gemini",
                "model": "gemini-3.1-pro-preview",
                "content": [{"text": "Recovered from session file."}],
            },
        ],
        project_name=_inbox.REPO_ROOT.name,
    )
    mock_invoke.side_effect = AgentTimeoutError("gemini", 900)

    with patch("ai_agent_bridge._gemini_session_link._GEMINI_TMP_ROOT", tmp_path):
        summary = _inbox.run_inbox("gemini")

    row = _delivery_row(str(thread["message_id"]))
    assert summary.deliveries_delivered == 1
    assert summary.replies_posted == 1
    assert row["status"] == "delivered"
    assert row["error"] == "session-recovery"
    messages = _channels.read("topic", thread_id=str(thread["thread_id"]))
    assert len(messages) == 2
    assert messages[-1]["from_agent"] == "gemini"
    assert messages[-1]["body"].startswith("[source=session-recovery, model=gemini-3.1-pro-preview]")
    assert "Recovered from session file." in messages[-1]["body"]


@patch("ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_gemini_timeout_without_session_keeps_delivery_pending(mock_invoke, tmp_path):
    thread = _make_thread("gemini", body="please review this carefully")
    mock_invoke.side_effect = AgentTimeoutError("gemini", 900)

    with patch("ai_agent_bridge._gemini_session_link._GEMINI_TMP_ROOT", tmp_path):
        summary = _inbox.run_inbox("gemini")

    row = _delivery_row(str(thread["message_id"]))
    assert summary.deliveries_released == 1
    assert summary.replies_posted == 0
    assert row["status"] == "pending"
    assert row["last_error_kind"] == "timeout"
    messages = _channels.read("topic", thread_id=str(thread["thread_id"]))
    assert len(messages) == 1
