"""Regression tests for delegate active task reporting."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

import scripts.api.delegate_router as delegate_router
import scripts.api.main as api_main
import scripts.api.state_helpers as state_helpers

client = TestClient(api_main.app, raise_server_exceptions=False)


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
        "cli_version": "0.130.0",
        "status": "done",
        "pid": 12345,
        "started_at": _iso(started),
        "duration_s": 30.0,
    }
    payload.update(overrides)
    return payload


def _reset_orient_cache() -> None:
    for key in [k for k in state_helpers._ttl_cache if k.startswith("orient_")]:
        state_helpers._ttl_cache.pop(key, None)


def _patch_non_delegate_orient_sources(monkeypatch) -> None:
    monkeypatch.setattr(api_main, "_collect_git_orient_data", lambda: {"branch": "main"})
    monkeypatch.setattr(api_main, "_collect_issues_orient_data", lambda: {"issues": []})

    async def fake_pipeline():
        return {"summary": {}}

    monkeypatch.setattr(api_main, "_collect_pipeline_orient_data", fake_pipeline)
    monkeypatch.setattr(api_main, "_collect_runtime_orient_data", lambda: {})
    monkeypatch.setattr(api_main, "_collect_bridge_pending_orient_data", lambda: {})
    monkeypatch.setattr(api_main, "_collect_wiki_orient_data", lambda: {"by_track": {}})
    monkeypatch.setattr(
        api_main,
        "_collect_governance_orient_data",
        lambda: {
            "decisions_total": 0,
            "decisions_stale": 0,
            "decisions_approaching_expiry": 0,
            "adrs_total": 0,
            "adrs_warnings": 0,
            "adrs_errors": 0,
        },
    )
    monkeypatch.setattr(api_main, "_collect_health_orient_data", lambda: {"api": True})
    monkeypatch.setattr(api_main, "_collect_session_hints_orient_data", lambda: [])


def test_delegate_active_includes_spawning_task_without_pid(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)
    _reset_orient_cache()
    _patch_non_delegate_orient_sources(monkeypatch)

    def fake_kill(pid: int, sig: int) -> None:
        if pid != 111:
            raise ProcessLookupError

    monkeypatch.setattr(delegate_router.os, "kill", fake_kill)
    _write_task(
        tasks_dir / "running.json",
        _task_payload(
            "running",
            status="running",
            pid=111,
            started_at=_iso(datetime.now(UTC) - timedelta(minutes=2)),
            duration_s=None,
        ),
    )
    _write_task(
        tasks_dir / "spawning.json",
        _task_payload(
            "spawning",
            status="spawning",
            pid=None,
            started_at=_iso(datetime.now(UTC) - timedelta(minutes=1)),
            duration_s=None,
        ),
    )
    _write_task(tasks_dir / "done.json", _task_payload("done", status="done"))

    active_response = client.get("/api/delegate/active")
    orient_response = client.get("/api/orient?fresh=true")

    assert active_response.status_code == 200
    assert orient_response.status_code == 200
    active = active_response.json()
    orient = orient_response.json()
    assert active["total"] == 2
    assert orient["delegate"]["active_count"] == active["total"]
    assert [task["task_id"] for task in active["tasks"]] == ["spawning", "running"]
    assert active["tasks"][0]["status"] == "spawning"
    assert active["tasks"][0]["alive"] is False


def test_delegate_active_filters_before_limit_truncation(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)

    def fake_kill(pid: int, sig: int) -> None:
        if pid != 111:
            raise ProcessLookupError

    monkeypatch.setattr(delegate_router.os, "kill", fake_kill)
    now = datetime.now(UTC)
    for index in range(600):
        _write_task(
            tasks_dir / f"done-{index:03d}.json",
            _task_payload(
                f"done-{index:03d}",
                started_at=_iso(now - timedelta(minutes=index)),
            ),
        )
    _write_task(
        tasks_dir / "running.json",
        _task_payload(
            "running",
            status="running",
            pid=111,
            started_at=_iso(now - timedelta(days=1)),
        ),
    )
    _write_task(
        tasks_dir / "spawning.json",
        _task_payload(
            "spawning",
            status="spawning",
            pid=None,
            started_at=_iso(now - timedelta(days=1, minutes=1)),
        ),
    )

    response = client.get("/api/delegate/active")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert [task["task_id"] for task in data["tasks"]] == ["running", "spawning"]
    assert delegate_router.active_delegate_count() == 2


def test_delegate_active_retries_transient_invalid_json(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    task_path = tasks_dir / "running.json"
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)
    _write_task(task_path, _task_payload("running", status="running", pid=111))

    original_read_text = Path.read_text
    read_attempts = 0
    retry_delays = []

    def flaky_read_text(path: Path, *args, **kwargs) -> str:
        nonlocal read_attempts
        if path == task_path and read_attempts == 0:
            read_attempts += 1
            return "{"
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", flaky_read_text)
    monkeypatch.setattr(delegate_router.time, "sleep", retry_delays.append)
    monkeypatch.setattr(delegate_router.os, "kill", lambda pid, sig: None)

    response = client.get("/api/delegate/active")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["tasks"][0]["task_id"] == "running"
    assert retry_delays == [delegate_router.TASK_READ_RETRY_SECONDS]
