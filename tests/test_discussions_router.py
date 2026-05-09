from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.ai_agent_bridge import _db
from scripts.api import discussions_router


def _insert_message(
    conn: sqlite3.Connection,
    *,
    message_id: str,
    thread_id: str,
    round_index: int,
    from_agent: str,
    body: str,
    created_at: datetime,
) -> None:
    conn.execute(
        """
        INSERT INTO channel_messages (
            message_id, channel, thread_id, parent_id, correlation_id,
            round_index, from_agent, from_model, kind, body,
            attachments, context_rev_shared, context_rev_channel, created_at
        )
        VALUES (?, 'architecture', ?, NULL, NULL, ?, ?, NULL, 'post', ?, NULL, NULL, NULL, ?)
        """,
        (
            message_id,
            thread_id,
            round_index,
            from_agent,
            body,
            created_at.isoformat(),
        ),
    )


@pytest.fixture()
def discussions_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "messages.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(_db._CHANNELS_SCHEMA)
    conn.execute(
        """
        INSERT INTO channels (name, created_at, description, include, subscribers)
        VALUES ('architecture', '2026-05-09T00:00:00Z', 'Architecture', '', 'claude,codex,gemini')
        """
    )
    now = datetime.now(UTC)
    _insert_message(conn, message_id="m1", thread_id="running", round_index=0, from_agent="user", body="Discuss", created_at=now - timedelta(minutes=4))
    _insert_message(conn, message_id="m2", thread_id="running", round_index=1, from_agent="codex", body="Still working", created_at=now - timedelta(minutes=2))
    _insert_message(conn, message_id="m3", thread_id="converged", round_index=0, from_agent="user", body="Discuss", created_at=now - timedelta(minutes=8))
    _insert_message(conn, message_id="m4", thread_id="converged", round_index=1, from_agent="codex", body="Need another pass", created_at=now - timedelta(minutes=6))
    _insert_message(conn, message_id="m5", thread_id="converged", round_index=2, from_agent="codex", body="Agree [AGREE]", created_at=now - timedelta(minutes=5))
    _insert_message(conn, message_id="m6", thread_id="timed-out", round_index=0, from_agent="user", body="Discuss", created_at=now - timedelta(minutes=50))
    _insert_message(conn, message_id="m7", thread_id="timed-out", round_index=1, from_agent="gemini", body="Delayed", created_at=now - timedelta(minutes=45))
    _insert_message(conn, message_id="m8", thread_id="marker-timeout", round_index=1, from_agent="claude", body="[TIMEOUT]", created_at=now - timedelta(minutes=1))
    _insert_message(conn, message_id="m9", thread_id="timeout-topic", round_index=1, from_agent="codex", body="We should discuss [TIMEOUT] markers without ending yet.", created_at=now - timedelta(minutes=1))
    _insert_message(conn, message_id="m10", thread_id="old", round_index=1, from_agent="codex", body="Old thread", created_at=now - timedelta(days=10))
    _insert_message(conn, message_id="m11", thread_id="round-one-agree", round_index=1, from_agent="claude", body="Parallel reply [AGREE]", created_at=now - timedelta(minutes=1))
    _insert_message(conn, message_id="m12", thread_id="lowercase-agree", round_index=2, from_agent="claude", body="Parallel reply [agree]", created_at=now - timedelta(minutes=1))
    conn.commit()
    conn.close()
    monkeypatch.setattr(discussions_router, "MESSAGE_DB", db_path)
    app = FastAPI()
    app.include_router(discussions_router.router, prefix="/api/discussions")
    return TestClient(app, raise_server_exceptions=False)


def test_active_discussions_classifies_running_converged_and_timed_out(discussions_client: TestClient):
    response = discussions_client.get("/api/discussions/active")
    assert response.status_code == 200
    by_thread = {item["thread_id"]: item for item in response.json()["discussions"]}
    assert by_thread["running"]["status"] == "running"
    assert by_thread["converged"]["status"] == "converged"
    assert by_thread["timed-out"]["status"] == "timed_out"
    assert by_thread["marker-timeout"]["status"] == "timed_out"
    assert by_thread["timeout-topic"]["status"] == "running"
    assert by_thread["round-one-agree"]["status"] == "running"
    assert by_thread["lowercase-agree"]["status"] == "running"
    assert "old" not in by_thread
    assert by_thread["running"]["channel"] == "architecture"
    assert by_thread["running"]["last_round"] == 1
    assert by_thread["running"]["round_count"] == 1


def test_active_discussions_limit_and_lookback(discussions_client: TestClient):
    response = discussions_client.get("/api/discussions/active", params={"limit": 1, "lookback_days": 30})
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert len(body["discussions"]) == 1


def test_active_discussions_lookback_includes_older_threads(discussions_client: TestClient):
    response = discussions_client.get("/api/discussions/active", params={"lookback_days": 15})
    assert response.status_code == 200
    by_thread = {item["thread_id"]: item for item in response.json()["discussions"]}
    assert "old" in by_thread


def test_active_discussions_negative_path_missing_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(discussions_router, "MESSAGE_DB", tmp_path / "missing.db")
    app = FastAPI()
    app.include_router(discussions_router.router, prefix="/api/discussions")
    response = TestClient(app, raise_server_exceptions=False).get("/api/discussions/active")
    assert response.status_code == 200
    assert response.json()["error"] == "Broker DB not found"
