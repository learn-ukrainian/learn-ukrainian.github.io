"""Tests for delegate monitor API endpoints."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

import scripts.api.delegate_router as delegate_router
from scripts.api.main import app

client = TestClient(app, raise_server_exceptions=False)


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _write_task(path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _task_payload(task_id: str, **overrides) -> dict:
    started = datetime.now(UTC) - timedelta(minutes=5)
    payload = {
        "task_id": task_id,
        "agent": "codex",
        "model": "gpt-5.5",
        "effort": "high",
        "cli_version": "0.123.0",
        "mode": "workspace-write",
        "cwd": "/tmp/repo",
        "pid": 12345,
        "status": "done",
        "started_at": _iso(started),
        "finished_at": _iso(started + timedelta(seconds=30)),
        "duration_s": 30.0,
        "prompt_chars": 10,
        "response_chars": 20,
        "result_file": None,
        "returncode": 0,
        "stderr_excerpt": None,
    }
    payload.update(overrides)
    return payload


def test_tasks_lists_state_files(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)
    _write_task(tasks_dir / "first.json", _task_payload("first", started_at=_iso(datetime.now(UTC) - timedelta(minutes=10))))
    _write_task(tasks_dir / "second.json", _task_payload("second", started_at=_iso(datetime.now(UTC) - timedelta(minutes=1))))

    response = client.get("/api/delegate/tasks")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["tasks"][0]["task_id"] == "second"
    assert data["tasks"][1]["task_id"] == "first"
    assert data["tasks"][0]["model"] == "gpt-5.5"
    assert data["tasks"][0]["effort"] == "high"
    assert data["tasks"][0]["cli_version"] == "0.123.0"


def test_tasks_status_filter(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)
    _write_task(tasks_dir / "done.json", _task_payload("done", status="done"))
    _write_task(tasks_dir / "running.json", _task_payload("running", status="running"))

    response = client.get("/api/delegate/tasks?status=done")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["tasks"][0]["task_id"] == "done"
    assert data["tasks"][0]["status"] == "done"


def test_task_detail_truncates_large_result(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)
    result_file = tmp_path / "big.result"
    result_file.write_text("x" * (70 * 1024), encoding="utf-8")
    _write_task(
        tasks_dir / "large.json",
        _task_payload("large", result_file=str(result_file), status="done"),
    )

    response = client.get("/api/delegate/tasks/large")

    assert response.status_code == 200
    data = response.json()
    assert data["result_truncated"] is True
    assert len(data["result"].encode("utf-8")) <= delegate_router.RESULT_BYTES_LIMIT


def test_zombie_detection_works_on_dead_pid(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)

    def fake_kill(pid: int, sig: int) -> None:
        raise ProcessLookupError

    monkeypatch.setattr(delegate_router.os, "kill", fake_kill)
    _write_task(
        tasks_dir / "zombie.json",
        _task_payload("zombie", status="running", pid=424242, finished_at=None, duration_s=None),
    )

    response = client.get("/api/delegate/tasks")

    assert response.status_code == 200
    task = response.json()["tasks"][0]
    assert task["task_id"] == "zombie"
    assert task["status"] == "zombie"
    assert task["alive"] is False
