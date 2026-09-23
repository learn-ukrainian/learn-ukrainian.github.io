"""Load failures on the cited comms_router sites stay on the response (#8521)."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import subprocess
import time
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.comms_router import router as comms_router
from scripts.api.monitor_context import fixture_context

pytestmark = pytest.mark.reads_content


@pytest.fixture()
def comms_client(tmp_path: Path) -> TestClient:
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(comms_router, prefix="/api/comms")
    return TestClient(app)


def test_corrupt_pid_file_is_surfaced_and_dead_pid_is_not(
    tmp_path: Path, comms_client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    pid_dir = tmp_path / ".mcp" / "servers" / "message-broker" / "pids"
    pid_dir.mkdir(parents=True, exist_ok=True)
    (pid_dir / "broken.json").write_text("{not-json", encoding="utf-8")
    # In-range but unused: a dead pid is not a load error. 2**31-1 is above the probe cap.
    (pid_dir / "dead.json").write_text(json.dumps({"pid": 2**22}), encoding="utf-8")

    with caplog.at_level(logging.WARNING, logger="scripts.api.comms_router"):
        resp = comms_client.get("/api/comms/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["alive_processes"] == 0
    assert any("broken.json" in item for item in body["errors"])
    assert all("dead.json" not in item for item in body["errors"])
    assert any("broken.json" in record.message for record in caplog.records)


def test_corrupt_curriculum_yaml_surfaces_track_error(
    tmp_path: Path, comms_client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    curriculum.mkdir(parents=True, exist_ok=True)
    (curriculum / "curriculum.yaml").write_text("levels: [", encoding="utf-8")

    with caplog.at_level(logging.WARNING, logger="scripts.api.comms_router"):
        resp = comms_client.get("/api/comms/batch-progress/a1")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_expected"] == 0
    assert any("a1" in item and "curriculum.yaml" in item for item in body["errors"])
    assert any("curriculum.yaml" in record.message for record in caplog.records)


def test_invalid_pid_records_are_named_and_not_counted_alive(
    tmp_path: Path, comms_client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    pid_dir = tmp_path / ".mcp" / "servers" / "message-broker" / "pids"
    pid_dir.mkdir(parents=True, exist_ok=True)
    records = {
        "missing.json": {},
        "huge.json": {"pid": 10**100},
        "text.json": {"pid": "abc"},
        "negative.json": {"pid": -1},
    }
    for name, payload in records.items():
        (pid_dir / name).write_text(json.dumps(payload), encoding="utf-8")

    with caplog.at_level(logging.WARNING, logger="scripts.api.comms_router"):
        resp = comms_client.get("/api/comms/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["alive_processes"] == 0
    for name in records:
        assert any(name in item and "invalid pid" in item for item in body["errors"])
    assert any("invalid pid" in record.message for record in caplog.records)


def test_broker_db_probe_failure_is_named(
    tmp_path: Path, comms_client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    db_path = tmp_path / ".mcp" / "servers" / "message-broker" / "messages.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.mkdir()

    with caplog.at_level(logging.WARNING, logger="scripts.api.comms_router"):
        resp = comms_client.get("/api/comms/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["db_exists"] is True
    assert body["db_writable"] is False
    assert any("db:" in item and "OperationalError" in item for item in body["errors"])
    assert any("broker DB" in record.message for record in caplog.records)


def test_ps_timeout_is_not_reported_as_zero_processes(
    comms_client: TestClient, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def _timeout(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=["ps", "aux"], timeout=5)

    monkeypatch.setattr("scripts.api.comms_router.subprocess.run", _timeout)

    with caplog.at_level(logging.WARNING, logger="scripts.api.comms_router"):
        resp = comms_client.get("/api/comms/batch-progress")

    assert resp.status_code == 200
    body = resp.json()
    assert body["running_processes"] is None
    assert body["tracks"] == {}
    assert any("ps:" in item and "TimeoutExpired" in item for item in body["errors"])
    assert any("ps" in record.message.lower() for record in caplog.records)


def _old_incomplete_log(tmp_path: Path, name: str = "hist-20260301-0100.log") -> None:
    log_dir = tmp_path / "logs" / "research-preseed"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / name
    log_file.write_text("Processing...\nVERDICT: PASS\n", encoding="utf-8")
    old = time.time() - 1200
    os.utime(log_file, (old, old))


def test_ps_timeout_does_not_mark_old_incomplete_log_dead(
    tmp_path: Path, comms_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _old_incomplete_log(tmp_path)

    def _timeout(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=["ps", "aux"], timeout=5)

    monkeypatch.setattr("scripts.api.comms_router.subprocess.run", _timeout)

    resp = comms_client.get("/api/comms/batch-progress")

    assert resp.status_code == 200
    body = resp.json()
    track = body["tracks"]["hist"]
    assert body["running_processes"] is None
    assert track["health"] == "unknown"
    assert track["reason"] == "ps: TimeoutExpired"
    assert "dead" not in {item["health"] for item in body["tracks"].values()}


def test_old_incomplete_log_stays_dead_when_process_probe_succeeds(
    tmp_path: Path, comms_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _old_incomplete_log(tmp_path)

    def _empty_ps(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=["ps", "aux"], returncode=0, stdout="", stderr="")

    monkeypatch.setattr("scripts.api.comms_router.subprocess.run", _empty_ps)

    resp = comms_client.get("/api/comms/batch-progress")

    assert resp.status_code == 200
    body = resp.json()
    assert body["running_processes"] == 0
    assert body["tracks"]["hist"]["health"] == "dead"
    assert "reason" not in body["tracks"]["hist"]


def test_context_preview_failure_is_named(
    tmp_path: Path, comms_client: TestClient, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    db_path = tmp_path / ".mcp" / "servers" / "message-broker" / "messages.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE channels (
            name TEXT PRIMARY KEY, created_at TEXT, description TEXT, include TEXT, subscribers TEXT
        );
        CREATE TABLE channel_messages (
            message_id TEXT PRIMARY KEY, channel TEXT
        );
        CREATE TABLE deliveries (
            delivery_id TEXT PRIMARY KEY, message_id TEXT, status TEXT
        );
        """
    )
    conn.execute(
        "INSERT INTO channels (name, created_at, description, include, subscribers) VALUES (?, ?, ?, ?, ?)",
        ("reviews", "2026-09-23T00:00:00Z", "", "", ""),
    )
    conn.commit()
    conn.close()

    context_root = tmp_path / "contexts"
    preview = context_root / "reviews" / "context.md"
    preview.parent.mkdir(parents=True)
    preview.write_text("pinned context", encoding="utf-8")
    monkeypatch.setattr("scripts.ai_agent_bridge._channels.CONTEXT_ROOT", context_root)

    original = Path.read_text

    def _unreadable(self: Path, *args: object, **kwargs: object) -> str:
        if self.name == "context.md":
            raise OSError("context unreadable")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", _unreadable)

    with caplog.at_level(logging.WARNING, logger="scripts.api.comms_router"):
        resp = comms_client.get("/api/comms/channels/reviews")

    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "reviews"
    assert body["context_preview"] == ""
    assert body["context_sha256"] == ""
    assert any("context_preview:" in item and "OSError" in item for item in body["errors"])
    assert any("context preview" in record.message for record in caplog.records)
