"""Tests for runtime monitor API endpoints."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

import scripts.api.runtime_router as runtime_router
from scripts.agent_runtime.acpx_discuss import AcpxDiscussionController
from scripts.api.main import app

client = TestClient(app, raise_server_exceptions=False)
DASHBOARDS = Path(__file__).resolve().parents[1] / "dashboards"


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _write_usage_file(path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def _write_acp_db(root, conversations: list[tuple], events: list[tuple]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(root / "comms.sqlite3")
    try:
        connection.executescript(
            """
            CREATE TABLE acp_conversations (
                conversation_id TEXT PRIMARY KEY,
                task_digest TEXT,
                correlation_digest TEXT,
                idempotency_digest TEXT,
                rounds_requested INTEGER,
                participants_json TEXT,
                created_at TEXT,
                deadline_at TEXT,
                token_budget INTEGER,
                content_budget_bytes INTEGER
            );
            CREATE TABLE acp_conversation_events (
                event_id TEXT,
                conversation_id TEXT,
                sequence INTEGER,
                event_type TEXT,
                state TEXT,
                sender TEXT,
                recipient TEXT,
                round INTEGER,
                outcome TEXT,
                duration_ms INTEGER,
                token_count INTEGER,
                leg_key_digest TEXT,
                message_id TEXT,
                metadata_json TEXT,
                created_at TEXT,
                UNIQUE(conversation_id, sequence)
            );
            CREATE TABLE comms_messages (
                message_id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                in_reply_to TEXT,
                kind TEXT NOT NULL,
                sender TEXT NOT NULL,
                recipient TEXT,
                body_inline TEXT,
                body_artifact_id TEXT,
                content_sha256 TEXT,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );
            """
        )
        connection.executemany(
            "INSERT INTO acp_conversations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            conversations,
        )
        connection.executemany(
            "INSERT INTO acp_conversation_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            events,
        )
        connection.commit()
    finally:
        connection.close()


def test_agents_endpoint_returns_known_adapters():
    response = client.get("/api/runtime/agents")

    assert response.status_code == 200
    agents = response.json()["agents"]
    names = {agent["name"] for agent in agents}
    assert {"claude", "gemini", "codex"} <= names
    assert not any(name.startswith("acpx-") for name in names)
    codex = next(agent for agent in agents if agent["name"] == "codex")
    assert codex["binary"] == "codex"
    assert codex["default_model"] == "gpt-5.6-terra"


def test_usage_aggregates_by_agent(tmp_path, monkeypatch):
    usage_dir = tmp_path / "api_usage"
    today = datetime.now(UTC)
    monkeypatch.setattr(runtime_router, "USAGE_DIR", usage_dir)

    _write_usage_file(
        usage_dir / f"usage_codex-dispatch_{today:%Y-%m-%d}.jsonl",
        [
            {
                "ts": _iso(today - timedelta(minutes=4)),
                "agent": "codex",
                "entrypoint": "dispatch",
                "model": "gpt-5.5",
                "duration_s": 10.5,
                "outcome": "ok",
            },
            {
                "ts": _iso(today - timedelta(minutes=3)),
                "agent": "codex",
                "entrypoint": "dispatch",
                "model": "gpt-5.5",
                "duration_s": 4.0,
                "outcome": "error",
            },
        ],
    )
    _write_usage_file(
        usage_dir / f"usage_gemini-bridge_{today:%Y-%m-%d}.jsonl",
        [
            {
                "ts": _iso(today - timedelta(minutes=2)),
                "agent": "gemini",
                "entrypoint": "bridge",
                "model": "gemini-3.1-pro-preview",
                "duration_s": 8.0,
                "outcome": "rate_limited",
            }
        ],
    )

    response = client.get("/api/runtime/usage?days=7")

    assert response.status_code == 200
    data = response.json()
    assert data["records_total"] == 3
    assert data["by_agent"]["codex"]["total"] == 2
    assert data["by_agent"]["codex"]["ok"] == 1
    assert data["by_agent"]["codex"]["error"] == 1
    assert data["by_agent"]["codex"]["total_duration_s"] == 14.5
    assert data["by_entrypoint"]["bridge"]["rate_limited"] == 1


def test_acpx_overview_is_read_only_and_aggregates_hyphenated_seats(
    tmp_path,
    monkeypatch,
):
    usage_dir = tmp_path / "api_usage"
    today = datetime.now(UTC)
    monkeypatch.setattr(runtime_router, "USAGE_DIR", usage_dir)
    monkeypatch.setenv("LU_ACPX_TRANSPORT", "shadow")
    original_iter = runtime_router._iter_usage_records
    iter_calls: list[tuple] = []

    def tracked_iter(paths):
        iter_calls.append(tuple(paths))
        return original_iter(paths)

    monkeypatch.setattr(runtime_router, "_iter_usage_records", tracked_iter)

    _write_usage_file(
        usage_dir / f"usage_acpx-grok-shadow-runner_{today:%Y-%m-%d}.jsonl",
        [
            {
                "ts": _iso(today - timedelta(minutes=2)),
                "agent": "acpx-grok-shadow",
                "entrypoint": "runner",
                "model": "grok-4.5",
                "duration_s": 6.25,
                "outcome": "ok",
                "task_id": "must-not-leak",
                "cwd": "/private/must-not-leak",
                "stderr_excerpt": "must-not-leak",
                "provider_session_id": "must-not-leak",
            }
        ],
    )
    _write_usage_file(
        usage_dir / f"usage_acpx-shadow-pilot-acpx-pilot_{today:%Y-%m-%d}.jsonl",
        [
            {
                "ts": _iso(today - timedelta(minutes=1)),
                "agent": "acpx-shadow-pilot",
                "entrypoint": "acpx-pilot",
                "event": "acpx_shadow_comparison",
                "model": "native-plus-shadow",
                "outcome": "ok",
                "target": "grok",
                "executed": True,
                "duplicate": False,
                "busy": False,
                "native_outcome": "ok",
                "shadow_outcome": "ok",
                "classification_parity": True,
                "native_duration_s": 4.0,
                "shadow_duration_s": 6.25,
                "native_tokens": 12,
                "shadow_tokens": 15,
                "correlation_digest": "must-not-leak",
                "idempotency_digest": "must-not-leak",
            },
            {
                "ts": _iso(today),
                "agent": "acpx-shadow-pilot",
                "entrypoint": "acpx-pilot",
                "event": "acpx_shadow_comparison",
                "model": "native-plus-shadow",
                "outcome": "ok",
                "target": "grok",
                "executed": False,
                "duplicate": True,
                "busy": False,
                "correlation_digest": "must-not-leak",
                "idempotency_digest": "must-not-leak",
            },
        ],
    )

    response = client.get("/api/runtime/acpx?days=7")

    assert response.status_code == 200
    assert len(iter_calls) == 1
    data = response.json()
    assert data["transport"] == {
        "mode": "shadow",
        "scope": "monitor_process",
        "default_mode": "off",
        "authority": "native_runtime",
        "posture": "evidence_only",
        "writable": False,
    }
    assert data["pins"] == {
        "acpx": "0.13.0",
        "grok_cli": "0.2.118",
        "validation": "before_spawn",
    }
    assert data["safety"]["max_in_flight"] == 1
    assert data["safety"]["explicit_pilot_only"] is True
    assert data["safety"]["chat"] is False
    assert data["safety"]["mutations"] is False
    comparison = data["comparison_evidence"]
    assert comparison["state"] == "observed"
    assert comparison["attempts"] == 2
    assert comparison["comparisons"] == 1
    assert comparison["classification_parity"] == 1
    assert comparison["classification_mismatch"] == 0
    assert comparison["duplicates_suppressed"] == 1
    assert comparison["native"]["ok"] == 1
    assert comparison["native"]["total_tokens"] == 12
    assert comparison["shadow"]["total_duration_s"] == 6.25
    assert comparison["shadow"]["total_tokens"] == 15

    seats = {seat["name"]: seat for seat in data["seats"]}
    assert seats["acpx-codex-shadow"]["evidence_state"] == "no_evidence"
    assert seats["acpx-codex-shadow"]["evidence"]["total"] == 0
    assert seats["acpx-grok-shadow"]["evidence_state"] == "observed"
    assert seats["acpx-grok-shadow"]["evidence"]["ok"] == 1
    assert seats["acpx-grok-shadow"]["evidence"]["total_duration_s"] == 6.25

    serialized = response.text
    for private_field in (
        "task_id",
        "cwd",
        "stderr_excerpt",
        "provider_session_id",
        "correlation_digest",
        "idempotency_digest",
        "must-not-leak",
    ):
        assert private_field not in serialized


def test_acpx_overview_sanitizes_unrecognized_transport_mode(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(runtime_router, "USAGE_DIR", tmp_path / "missing")
    monkeypatch.setenv("LU_ACPX_TRANSPORT", "secret-looking-invalid-value")

    response = client.get("/api/runtime/acpx")

    assert response.status_code == 200
    data = response.json()
    assert data["transport"]["mode"] == "invalid"
    assert "secret-looking-invalid-value" not in response.text


def test_acp_conversation_api_is_ordered_allowlisted_and_read_only(tmp_path, monkeypatch):
    root = tmp_path / "plane"
    now = datetime.now(UTC)
    conversation = (
        "conv-001",
        "task-digest-must-not-leak",
        "correlation-digest-must-not-leak",
        "idempotency-digest-must-not-leak",
        2,
        '["root", "codex", "grok", "poisoned"]',
        _iso(now - timedelta(minutes=5)),
        _iso(now + timedelta(minutes=5)),
        999,
        12345,
    )
    events = [
        (
            "event-1", "conv-001", 1, "created", "CREATED", "root", None, None,
            "queued", 0, 0, "leg-secret", "message-secret", '{"body":"must-not-leak"}',
            _iso(now - timedelta(minutes=5)),
        ),
        (
            "event-2", "conv-001", 2, "participant_message", "INITIAL_FANOUT", "root", "codex", 1,
            "running", 100, 12, "leg-secret", "message-secret", '{"prompt":"must-not-leak"}',
            _iso(now - timedelta(minutes=4)),
        ),
        (
            "event-3", "conv-001", 3, "participant_message", "INITIAL_COMPLETE", "root", "grok", 1,
            "succeeded", 200, 15, "leg-secret", "message-secret", '{"response":"must-not-leak"}',
            _iso(now - timedelta(minutes=3)),
        ),
        (
            "event-4", "conv-001", 4, "synthesis_complete", "COMPLETE", "root", None, 2,
            "succeeded", 300, 8, "leg-secret", "message-secret", '{"credential":"must-not-leak"}',
            _iso(now - timedelta(minutes=2)),
        ),
    ]
    _write_acp_db(root, [conversation], events)
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(root))
    db_path = root / "comms.sqlite3"
    before = db_path.stat().st_mtime_ns

    collection = client.get("/api/runtime/acp/conversations")
    detail = client.get("/api/runtime/acp/conversations/conv-001")

    assert collection.status_code == 200
    assert collection.json()["availability"] == "available"
    assert collection.json()["conversations"] == [
        {
            "conversation_id": "conv-001",
            "current_state": "COMPLETE",
            "classification": "complete",
            "participants": ["codex", "grok"],
            "rounds_requested": 2,
            "rounds_completed": 1,
            "created_at": _iso(now - timedelta(minutes=5)),
            "deadline_at": _iso(now + timedelta(minutes=5)),
            "expired": False,
            "stale_or_unhealthy": False,
            "updated_at": _iso(now - timedelta(minutes=2)),
            "total_duration_ms": 600,
            "total_tokens": 35,
            "synthesis_state": "complete",
            "duplicate_suppressed": False,
            "termination_reason": None,
        }
    ]
    assert detail.status_code == 200
    timeline = detail.json()
    assert [event["sequence"] for event in timeline["events"]] == [1, 2, 3, 4]
    assert timeline["events"][1]["sender"] == "root"
    assert timeline["events"][1]["recipient"] == "codex"
    assert db_path.stat().st_mtime_ns == before
    assert not (root / "comms.sqlite3-journal").exists()
    assert not (root / "comms.sqlite3-wal").exists()
    for private_value in (
        "task_digest", "correlation_digest", "idempotency_digest",
        "token_budget", "content_budget_bytes", "metadata_json", "message_id",
        "leg_key_digest", "must-not-leak", "leg-secret", "message-secret",
    ):
        assert private_value not in detail.text


def test_acp_runtime_api_hides_persisted_message_content_and_references(
    tmp_path, monkeypatch
):
    root = tmp_path / "plane"
    controller = AcpxDiscussionController(root=root)
    try:
        conversation_id, replay = controller._reserve(
            task_digest="task-digest",
            correlation_digest="correlation-digest",
            idempotency_digest="idempotency-digest",
            rounds=1,
            deadline_at="2099-01-01T00:00:00Z",
        )
        assert replay is None
        message_id = controller._message(
            conversation_id,
            sender="codex",
            recipient="root",
            body="private ACP body must not leak",
            reply_to=None,
        )
        artifact_id = controller.conn.execute(
            "SELECT body_artifact_id FROM comms_messages WHERE message_id = ?",
            (message_id,),
        ).fetchone()[0]
    finally:
        controller.close()

    monkeypatch.setenv("FLEET_COMMS_ROOT", str(root))
    response = client.get(f"/api/runtime/acp/conversations/{conversation_id}")

    assert response.status_code == 200
    for private_value in (
        "private ACP body must not leak",
        message_id,
        artifact_id,
    ):
        assert private_value not in response.text


def test_acp_transcript_is_loopback_only_ordered_allowlisted_and_no_store(tmp_path, monkeypatch):
    root = tmp_path / "plane"
    now = datetime.now(UTC)
    conversation = (
        "conv-transcript", "secret", "secret", "secret", 1, "[]", _iso(now), None, 1, 1,
    )
    events = [
        (
            "event-later", "conv-transcript", 2, "CALL_TERMINAL", "INITIAL_FANOUT", "codex", "root", 1,
            "ok", 1, 1, "secret", "message-later", "{}", _iso(now + timedelta(seconds=2)),
        ),
        (
            "event-early", "conv-transcript", 1, "CALL_RESERVED", "INITIAL_FANOUT", "root", "codex", 1,
            "queued", 1, 1, "secret", "message-early", "{}", _iso(now + timedelta(seconds=1)),
        ),
        (
            "event-synthesis", "conv-transcript", 3, "SYNTHESIS_TERMINAL", "COMPLETE", "codex", "root", None,
            "ok", 1, 1, "secret", "message-synthesis", "{}", _iso(now + timedelta(seconds=3)),
        ),
    ]
    _write_acp_db(root, [conversation], events)
    connection = sqlite3.connect(root / "comms.sqlite3")
    try:
        connection.executemany(
            """INSERT INTO comms_messages(
                message_id, conversation_id, kind, sender, recipient, body_inline,
                body_artifact_id, content_sha256, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    "message-later", "conv-transcript", "reply", "codex", "root", "second body",
                    "artifact-secret", "hash-secret", '{"credential":"secret"}', _iso(now + timedelta(seconds=2)),
                ),
                (
                    "message-early", "conv-transcript", "request", "root", "codex", "first body",
                    "artifact-secret", "hash-secret", '{"command":"secret"}', _iso(now + timedelta(seconds=1)),
                ),
                (
                    "message-synthesis", "conv-transcript", "synthesis", "codex", "root", "final synthesis",
                    "artifact-secret", "hash-secret", '{}', _iso(now + timedelta(seconds=3)),
                ),
            ],
        )
        connection.commit()
    finally:
        connection.close()
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(root))

    loopback_client = TestClient(
        app,
        raise_server_exceptions=False,
        client=("127.0.0.1", 50000),
        base_url="http://localhost",
    )
    response = loopback_client.get("/api/runtime/acp/conversations/conv-transcript/transcript")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "conversation_id": "conv-transcript",
        "messages": [
            {
                "ordinal": 1,
                "kind": "request",
                "sender": "root",
                "recipient": "codex",
                "created_at": _iso(now + timedelta(seconds=1)),
                "body": "first body",
                "round": 1,
            },
            {
                "ordinal": 2,
                "kind": "reply",
                "sender": "codex",
                "recipient": "root",
                "created_at": _iso(now + timedelta(seconds=2)),
                "body": "second body",
                "round": 1,
            },
            {
                "ordinal": 3,
                "kind": "synthesis",
                "sender": "codex",
                "recipient": "root",
                "created_at": _iso(now + timedelta(seconds=3)),
                "body": "final synthesis",
            },
        ],
    }
    for private_value in (
        "message-later", "message-early", "artifact-secret", "hash-secret", "metadata_json", "secret",
    ):
        assert private_value not in response.text

    remote = TestClient(
        app,
        raise_server_exceptions=False,
        client=("203.0.113.10", 50000),
        base_url="http://localhost",
    )
    denied = remote.get("/api/runtime/acp/conversations/conv-transcript/transcript")
    assert denied.status_code == 403
    assert denied.headers["cache-control"] == "no-store"
    assert denied.json() == {"detail": "Forbidden"}

    for host in ("127.0.0.1", "::1", "::ffff:127.0.0.1"):
        loopback = TestClient(
            app,
            raise_server_exceptions=False,
            client=(host, 50000),
            base_url="http://localhost",
        )
        assert loopback.get("/api/runtime/acp/conversations/conv-transcript/transcript").status_code == 200

    rebound = TestClient(
        app,
        raise_server_exceptions=False,
        client=("127.0.0.1", 50000),
        base_url="http://monitor.example",
    )
    assert rebound.get("/api/runtime/acp/conversations/conv-transcript/transcript").status_code == 403


def test_acp_transcript_hides_unavailable_malformed_and_body_free_routes(tmp_path, monkeypatch):
    root = tmp_path / "plane"
    now = datetime.now(UTC)
    conversation = (
        "conv-malformed", "secret", "secret", "secret", 1, "[]", _iso(now), None, 1, 1,
    )
    _write_acp_db(root, [conversation], [])
    connection = sqlite3.connect(root / "comms.sqlite3")
    try:
        connection.executemany(
            """INSERT INTO comms_messages(
                message_id, conversation_id, kind, sender, recipient, body_inline, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                ("message-private", "conv-malformed", "reply", "codex", "root", "body only in transcript", '{"path":"secret"}', _iso(now)),
                ("message-unlinked", "conv-malformed", "reply", "codex", "root", "must not appear", '{}', _iso(now)),
            ],
        )
        connection.execute(
            """INSERT INTO acp_conversation_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("event-private", "conv-malformed", 1, "CALL_TERMINAL", "COMPLETE", "codex", "root", 1, "ok", 1, 1, "secret", "message-private", "{}", _iso(now)),
        )
        connection.commit()
    finally:
        connection.close()
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(root))

    loopback_client = TestClient(
        app,
        raise_server_exceptions=False,
        client=("127.0.0.1", 50000),
        base_url="http://localhost",
    )
    body_free = client.get("/api/runtime/acp/conversations/conv-malformed")
    transcript = loopback_client.get("/api/runtime/acp/conversations/conv-malformed/transcript")
    malformed = loopback_client.get("/api/runtime/acp/conversations/not%20an%20id/transcript")
    missing = loopback_client.get("/api/runtime/acp/conversations/not-found/transcript")

    assert body_free.status_code == 200
    assert "body only in transcript" not in body_free.text
    assert transcript.status_code == 200
    assert transcript.json()["messages"][0]["body"] == "body only in transcript"
    assert "must not appear" not in transcript.text
    assert malformed.status_code == 404
    assert missing.status_code == 404
    assert malformed.headers["cache-control"] == "no-store"
    assert missing.headers["cache-control"] == "no-store"

    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "missing"))
    unavailable = loopback_client.get("/api/runtime/acp/conversations/conv-malformed/transcript")
    assert unavailable.status_code == 404
    assert unavailable.headers["cache-control"] == "no-store"

    malformed_root = tmp_path / "malformed"
    malformed_root.mkdir()
    malformed_db = sqlite3.connect(malformed_root / "comms.sqlite3")
    try:
        malformed_db.execute("CREATE TABLE unrelated (value TEXT)")
        malformed_db.commit()
    finally:
        malformed_db.close()
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(malformed_root))
    malformed_storage = loopback_client.get("/api/runtime/acp/conversations/conv-malformed/transcript")
    assert malformed_storage.status_code == 404
    assert malformed_storage.headers["cache-control"] == "no-store"


def test_acp_conversations_refuse_poisoned_rows_and_hide_unavailable_storage(tmp_path, monkeypatch):
    root = tmp_path / "plane"
    now = datetime.now(UTC)
    conversation = (
        "conv-good", "secret", "secret", "secret", 1, "not-json", _iso(now), None, 1, 1,
    )
    events = [
        (
            "event-good", "conv-good", 1, "CALL_TERMINAL", "INITIAL_FANOUT", "root", "grok", 1,
            "timeout", 4, 2, "secret", "secret", '{broken', _iso(now),
        ),
        (
            "event-busy", "conv-good", 2, "CALL_TERMINAL", "INITIAL_FANOUT", "root", "codex", 1,
            "busy", 0, 0, "secret", "secret", "{}", _iso(now),
        ),
        (
            "event-duplicate", "conv-good", 3, "duplicate_suppressed", "PARTIAL_COMPLETE", "root", None, 1,
            "duplicate_suppressed", 0, 0, "secret", "secret", '{"body":"must-not-leak"}', _iso(now),
        ),
        (
            "event-poison", "conv-good", 4, "prompt body must not leak", "COMPLETE", "intruder", "grok", 1,
            "succeeded", 4, 2, "secret", "secret", '{"body":"must-not-leak"}', _iso(now),
        ),
    ]
    _write_acp_db(root, [conversation], events)
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(root))

    response = client.get("/api/runtime/acp/conversations/conv-good")

    assert response.status_code == 200
    data = response.json()
    assert data["current_state"] == "PARTIAL_COMPLETE"
    assert data["termination_reason"] == "duplicate_suppressed"
    assert data["duplicate_suppressed"] is True
    assert len(data["events"]) == 3
    assert data["events"][0]["event_type"] == "CALL_TERMINAL"
    assert data["events"][0]["outcome"] == "failed"
    assert data["events"][1]["recipient"] == "codex"
    assert data["events"][1]["outcome"] == "partial"
    assert "must-not-leak" not in response.text
    assert client.get("/api/runtime/acp/conversations/not-found").status_code == 404

    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "missing"))
    missing = client.get("/api/runtime/acp/conversations")
    assert missing.json() == {"availability": "unavailable", "conversations": []}


def test_acp_summary_prefers_terminal_wall_duration_and_token_total(tmp_path, monkeypatch):
    root = tmp_path / "plane"
    now = datetime.now(UTC)
    conversation = (
        "conv-total", "task", "correlation", "idempotency", 1, '["codex","grok"]',
        _iso(now), _iso(now + timedelta(minutes=5)), 160_000, 512 * 1024,
    )
    events = [
        (
            "event-1", "conv-total", 1, "CREATED", "CREATED", None, None, None,
            None, None, None, None, None, "{}", _iso(now),
        ),
        (
            "event-2", "conv-total", 2, "CALL_TERMINAL", "INITIAL_FANOUT", "codex", "root", 1,
            "ok", 100, 2, "leg-1", "message-1", "{}", _iso(now),
        ),
        (
            "event-3", "conv-total", 3, "CALL_TERMINAL", "INITIAL_FANOUT", "grok", "root", 1,
            "ok", 200, 3, "leg-2", "message-2", "{}", _iso(now),
        ),
        (
            "event-4", "conv-total", 4, "STATE", "COMPLETE", None, None, None,
            None, 250, 5, None, None, "{}", _iso(now + timedelta(milliseconds=250)),
        ),
    ]
    _write_acp_db(root, [conversation], events)
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(root))

    summary = client.get("/api/runtime/acp/conversations").json()["conversations"][0]

    assert summary["total_duration_ms"] == 250
    assert summary["total_tokens"] == 5


def test_acp_summary_marks_expired_and_partial_conversations_unhealthy(tmp_path, monkeypatch):
    root = tmp_path / "plane"
    now = datetime.now(UTC)
    conversation = (
        "conv-expired", "task", "correlation", "idempotency", 1, '[]',
        _iso(now - timedelta(minutes=10)), _iso(now - timedelta(minutes=1)), 1, 1,
    )
    events = [
        (
            "event-1", "conv-expired", 1, "STATE", "PARTIAL", None, None, None,
            None, None, None, None, None, "{}", _iso(now - timedelta(minutes=2)),
        ),
    ]
    _write_acp_db(root, [conversation], events)
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(root))

    summary = client.get("/api/runtime/acp/conversations").json()["conversations"][0]

    assert summary["deadline_at"] == _iso(now - timedelta(minutes=1))
    assert summary["expired"] is True
    assert summary["stale_or_unhealthy"] is True


def test_runtime_page_links_to_the_dedicated_read_only_acp_conversations_page():
    html = (DASHBOARDS / "runtime.html").read_text(encoding="utf-8")
    acp_panel = html[html.index('id="acp-heading"') : html.index('id="acpx-heading"')]

    assert "ACP Conversations" in acp_panel
    assert "Read-only, body-free event history" in acp_panel
    assert 'href="/acp.html"' in acp_panel
    assert "/api/runtime/acp/conversations" not in html
    assert (DASHBOARDS / "acp.html").is_file()

    for prohibited in [
        "<form",
        "acp-send",
        "acp-post",
        "acp-start",
        "acp-session",
        "acp-toggle",
        "acp-retry",
        "acp-cancel",
        "acp-route",
        "acp-review",
        "acp-config",
    ]:
        assert prohibited not in acp_panel

    assert html.index('id="acp-heading"') < html.index('id="acpx-heading"')
    assert "ACPX Shadow Transport" in html
    assert "ACPX evidence is observational only." in html


def test_acp_termination_reason_allowlists_budget_and_deadline_events():
    assert runtime_router._acp_termination(
        [{"event_type": "BUDGET_EXHAUSTED"}], "PARTIAL_COMPLETE"
    ) == "budget_exhausted"
    assert runtime_router._acp_termination(
        [{"event_type": "DEADLINE_EXCEEDED"}], "PARTIAL_COMPLETE"
    ) == "deadline_exceeded"
    assert runtime_router._acp_termination(
        [{"event_type": "CALL_TERMINAL", "outcome": "failed"}], "PARTIAL_COMPLETE"
    ) is None
    assert runtime_router._acp_classification("CANCELLED") == "cancelled"
    assert runtime_router._acp_termination([], "CANCELLED") == "cancelled"


def test_headroom_rejects_missing_params():
    response = client.get("/api/runtime/headroom")

    assert response.status_code == 400
    assert "required" in response.json()["detail"]


def test_recent_limits_results(tmp_path, monkeypatch):
    usage_dir = tmp_path / "api_usage"
    now = datetime.now(UTC)
    monkeypatch.setattr(runtime_router, "USAGE_DIR", usage_dir)
    _write_usage_file(
        usage_dir / f"usage_codex-dispatch_{now:%Y-%m-%d}.jsonl",
        [
            {
                "ts": _iso(now - timedelta(minutes=3)),
                "agent": "codex",
                "entrypoint": "dispatch",
                "model": "gpt-5.5",
                "outcome": "ok",
                "duration_s": 9.0,
            },
            {
                "ts": _iso(now - timedelta(minutes=1)),
                "agent": "codex",
                "entrypoint": "dispatch",
                "model": "gpt-5.5",
                "outcome": "timeout",
                "duration_s": 12.0,
            },
            {
                "ts": _iso(now - timedelta(minutes=2)),
                "agent": "gemini",
                "entrypoint": "bridge",
                "initiator": "codex",
                "attribution_source": "explicit",
                "attribution_task_id": "review-6159",
                "model": "gemini-3.1-pro-preview",
                "outcome": "ok",
                "duration_s": 5.0,
            },
        ],
    )

    response = client.get("/api/runtime/recent?limit=2")

    assert response.status_code == 200
    records = response.json()["records"]
    assert len(records) == 2
    assert records[0]["outcome"] == "timeout"
    assert records[0]["source"] == "unknown"
    assert records[0]["via"] == "dispatch"
    assert records[1]["agent"] == "gemini"
    assert records[1]["source"] == "codex"
    assert records[1]["source_provenance"] == "explicit"
    assert records[1]["source_task_id"] == "review-6159"


def test_runtime_page_labels_caller_source_separately_from_transport():
    html = (DASHBOARDS / "runtime.html").read_text(encoding="utf-8")

    assert "<th>Source</th>" in html
    assert "<th>Agent</th>" in html
    assert "<th>Via</th>" in html
    assert "record.source || 'unknown'" in html
    assert "record.via || record.entrypoint" in html


def test_transport_health_returns_sanitized_cached_probe(tmp_path, monkeypatch):
    receipt_path = tmp_path / "codex-transport-health.json"
    config_path = tmp_path / "config.toml"
    now = datetime.now(UTC)
    config_path.write_text(
        "[features.multi_agent_v2]\ntool_namespace = \"agents\"\n",
        encoding="utf-8",
    )
    receipt_path.write_text(
        json.dumps(
            {
                "schema_version": "codex-transport-health.v1",
                "status": "healthy",
                "checked_at": _iso(now - timedelta(seconds=5)),
                "expires_at": _iso(now + timedelta(minutes=10)),
                "model": "gpt-5.6-terra",
                "effort": "low",
                "task_id": "codex-transport-probe-test",
                "failure_class": None,
                "source": "fresh_bridge_probe",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(runtime_router, "CODEX_TRANSPORT_RECEIPT_PATH", receipt_path)
    monkeypatch.setattr(runtime_router, "CODEX_TRANSPORT_CONFIG_PATH", config_path)

    response = client.get("/api/runtime/transport-health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["fresh"] is True
    assert data["namespace_valid"] is True
    assert data["tool_namespace"] == "agents"
    assert "task_id" not in data
    assert "content" not in data


def test_transport_health_is_unknown_without_probe_receipt(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[features.multi_agent_v2]\ntool_namespace = \"agents\"\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        runtime_router,
        "CODEX_TRANSPORT_RECEIPT_PATH",
        tmp_path / "missing.json",
    )
    monkeypatch.setattr(runtime_router, "CODEX_TRANSPORT_CONFIG_PATH", config_path)

    response = client.get("/api/runtime/transport-health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unknown"
    assert data["fresh"] is False
    assert data["failure_class"] == "no_probe_receipt"
