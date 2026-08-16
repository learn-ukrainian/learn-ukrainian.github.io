"""Tests for delegate monitor API endpoints."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

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
    assert data["tasks"][0]["substitution"] is None


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


def test_tasks_timeout_status_is_distinct_from_failed(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)
    _write_task(tasks_dir / "timeout.json", _task_payload("timeout", status="timeout"))
    _write_task(tasks_dir / "failed.json", _task_payload("failed", status="failed"))

    timeout_response = client.get("/api/delegate/tasks?status=timeout")
    failed_response = client.get("/api/delegate/tasks?status=failed")

    assert timeout_response.status_code == 200
    assert failed_response.status_code == 200
    assert [task["task_id"] for task in timeout_response.json()["tasks"]] == ["timeout"]
    assert [task["task_id"] for task in failed_response.json()["tasks"]] == ["failed"]


def test_tasks_attention_status_filters_are_queryable(tmp_path, monkeypatch):
    """``needs_finalize``/``no_deliverable`` are real settle states — the API
    must not 422 when an orchestrator filters by them (#5800 review)."""
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)
    _write_task(tasks_dir / "finalize.json", _task_payload("finalize", status="needs_finalize"))
    _write_task(tasks_dir / "nodeliv.json", _task_payload("nodeliv", status="no_deliverable"))

    finalize_response = client.get("/api/delegate/tasks?status=needs_finalize")
    nodeliv_response = client.get("/api/delegate/tasks?status=no_deliverable")

    assert finalize_response.status_code == 200
    assert nodeliv_response.status_code == 200
    assert [task["task_id"] for task in finalize_response.json()["tasks"]] == ["finalize"]
    assert [task["task_id"] for task in nodeliv_response.json()["tasks"]] == ["nodeliv"]


def test_active_lists_only_live_running_tasks(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)

    def fake_kill(pid: int, sig: int) -> None:
        if pid == 222:
            raise ProcessLookupError

    monkeypatch.setattr(delegate_router.os, "kill", fake_kill)
    _write_task(tasks_dir / "running.json", _task_payload("running", status="running", pid=111))
    _write_task(tasks_dir / "zombie.json", _task_payload("zombie", status="running", pid=222))
    _write_task(tasks_dir / "done.json", _task_payload("done", status="done", pid=333))

    response = client.get("/api/delegate/active")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["tasks"][0]["task_id"] == "running"


def test_task_state_path_stays_under_tasks_dir(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)

    for task_id in ("normal", "agent/task", "../../etc/passwd", r"..\..\windows"):
        path = Path(delegate_router._task_state_path(task_id))
        resolved = path.resolve()
        assert resolved == tasks_dir.resolve() / resolved.name
        assert resolved.is_relative_to(tasks_dir.resolve())


def test_task_detail_truncates_large_result(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)
    # Production writes ``.result`` siblings under TASKS_DIR; reads are
    # containment-checked there (CodeQL py/path-injection).
    result_file = tasks_dir / "large.result"
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


def test_task_detail_rejects_result_outside_tasks_dir(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)
    escape = tmp_path / "outside.result"
    escape.write_text("secret", encoding="utf-8")
    _write_task(
        tasks_dir / "escape.json",
        _task_payload("escape", result_file=str(escape), status="done"),
    )

    response = client.get("/api/delegate/tasks/escape")

    assert response.status_code == 200
    data = response.json()
    assert data["result"] is None
    assert data["result_truncated"] is False


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


# Legacy public summary keys for list/active (no repository attribution).
_LEGACY_DELEGATE_SUMMARY_KEYS = {
    "task_id",
    "agent",
    "model",
    "effort",
    "cli_version",
    "substitution",
    "status",
    "started_at",
    "duration_s",
    "age_s",
    "alive",
}


def _assert_legacy_summary_shape(tasks: list) -> None:
    """Rows must keep legacy keys and never emit repository identity fields."""
    for task in tasks:
        assert isinstance(task, dict)
        assert set(task) <= _LEGACY_DELEGATE_SUMMARY_KEYS
        assert "repository" not in task
        assert "repository_id" not in task


def test_list_delegate_tasks_repository_filter_before_limit(tmp_path, monkeypatch):
    """Internal repository predicate filters before total/limit so public rows are not starved."""
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)
    public_repo = "learn-ukrainian/learn-ukrainian.github.io"
    private_repo = "other-org/other-private-repo"
    now = datetime.now(UTC)

    # >500 newer foreign/unclassified tasks that would consume the default page.
    for index in range(520):
        _write_task(
            tasks_dir / f"foreign-{index:04d}.json",
            _task_payload(
                f"foreign-{index:04d}",
                status="done",
                started_at=_iso(now - timedelta(seconds=index)),
                repository=private_repo,
                cwd=f"/Users/private/{private_repo}",
                worktree_path=f"/Users/private/.worktrees/dispatch/codex/foreign-{index}",
            ),
        )
    for index in range(30):
        _write_task(
            tasks_dir / f"unclassified-{index:04d}.json",
            _task_payload(
                f"unclassified-{index:04d}",
                status="done",
                started_at=_iso(now - timedelta(seconds=600 + index)),
                cwd=f"/Users/private/projects/{public_repo}",
                worktree_path=f"/Users/private/.worktrees/dispatch/codex/issue-{index}",
            ),
        )
    # Older public tasks that must still appear when the list is repo-scoped.
    public_ids = []
    for index in range(7):
        task_id = f"public-old-{index:04d}"
        public_ids.append(task_id)
        _write_task(
            tasks_dir / f"{task_id}.json",
            _task_payload(
                task_id,
                status="done",
                started_at=_iso(now - timedelta(days=2, minutes=index)),
                repository=public_repo,
            ),
        )
    _write_task(
        tasks_dir / "public-running.json",
        _task_payload(
            "public-running",
            status="running",
            pid=111,
            started_at=_iso(now - timedelta(days=3)),
            repository=public_repo,
            duration_s=None,
        ),
    )
    _write_task(
        tasks_dir / "public-spawning.json",
        _task_payload(
            "public-spawning",
            status="spawning",
            pid=None,
            started_at=_iso(now - timedelta(days=3, minutes=1)),
            repository_id=public_repo,
            duration_s=None,
        ),
    )
    _write_task(
        tasks_dir / "ambiguous.json",
        _task_payload(
            "ambiguous",
            status="done",
            started_at=_iso(now - timedelta(days=1)),
            repository=public_repo,
            repository_id=private_repo,
        ),
    )
    monkeypatch.setattr(delegate_router.os, "kill", lambda pid, sig: None)

    unscoped = delegate_router.list_delegate_tasks(status="all", limit=500)
    # Unscoped page is filled by newer foreign volume; older public rows drop off.
    assert unscoped["total"] > 500
    unscoped_ids = {t["task_id"] for t in unscoped["tasks"]}
    assert "foreign-0000" in unscoped_ids
    assert "public-old-0000" not in unscoped_ids
    # Privacy: raw private repository on disk must never appear in generic summaries.
    _assert_legacy_summary_shape(unscoped["tasks"])
    unscoped_blob = json.dumps(unscoped)
    assert "repository" not in unscoped_blob
    assert "repository_id" not in unscoped_blob
    assert private_repo not in unscoped_blob

    scoped = delegate_router.list_delegate_tasks(
        status="all", limit=500, repository=public_repo
    )
    assert scoped["total"] == 9  # 7 older + running + spawning; ambiguous omitted
    scoped_ids = {t["task_id"] for t in scoped["tasks"]}
    assert scoped_ids == set(public_ids) | {"public-running", "public-spawning"}
    # Scoped internal results still use the legacy public summary shape.
    _assert_legacy_summary_shape(scoped["tasks"])
    blob = json.dumps(scoped)
    assert "repository" not in blob
    assert "repository_id" not in blob
    assert private_repo not in blob
    assert public_repo not in blob
    assert "/Users/private/" not in blob
    assert "cwd" not in blob
    assert "worktree_path" not in blob

    active = delegate_router.active_delegate_tasks(repository=public_repo)
    assert active["total"] == 2
    assert {t["task_id"] for t in active["tasks"]} == {
        "public-running",
        "public-spawning",
    }
    _assert_legacy_summary_shape(active["tasks"])
    assert "repository" not in json.dumps(active)

    # Default HTTP surface stays unscoped and free of repository/path metadata.
    response = client.get("/api/delegate/tasks?status=all&limit=500")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == unscoped["total"]
    _assert_legacy_summary_shape(data["tasks"])
    http_blob = json.dumps(data)
    assert "repository" not in http_blob
    assert "repository_id" not in http_blob
    assert private_repo not in http_blob
    assert "/Users/private/" not in http_blob
    assert "worktree_path" not in http_blob

    active_http = client.get("/api/delegate/active")
    assert active_http.status_code == 200
    active_data = active_http.json()
    _assert_legacy_summary_shape(active_data["tasks"])
    active_http_blob = json.dumps(active_data)
    assert "repository" not in active_http_blob
    assert "repository_id" not in active_http_blob
    assert private_repo not in active_http_blob

    # repository query param is not a free-form public selector
    response_q = client.get(
        f"/api/delegate/tasks?status=all&limit=50&repository={public_repo}"
    )
    assert response_q.status_code == 200
    # Unknown query keys are ignored by FastAPI; response stays unscoped.
    assert response_q.json()["total"] == unscoped["total"]
    _assert_legacy_summary_shape(response_q.json()["tasks"])


def test_delegate_http_redacts_repository_even_when_task_state_has_private(
    tmp_path, monkeypatch
):
    """Unscoped /tasks and /active must never serialize repository/repository_id."""
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)
    private_repo = "secret-org/secret-private-infra"
    public_repo = "learn-ukrainian/learn-ukrainian.github.io"
    now = datetime.now(UTC)
    _write_task(
        tasks_dir / "private-running.json",
        _task_payload(
            "private-running",
            status="running",
            pid=222,
            started_at=_iso(now),
            repository=private_repo,
            repository_id=private_repo,
            cwd=f"/Users/private/{private_repo}",
        ),
    )
    _write_task(
        tasks_dir / "public-done.json",
        _task_payload(
            "public-done",
            status="done",
            started_at=_iso(now - timedelta(minutes=1)),
            repository=public_repo,
        ),
    )
    monkeypatch.setattr(delegate_router.os, "kill", lambda pid, sig: None)

    tasks_resp = client.get("/api/delegate/tasks?status=all&limit=50")
    active_resp = client.get("/api/delegate/active")
    assert tasks_resp.status_code == 200
    assert active_resp.status_code == 200
    tasks_body = tasks_resp.json()
    active_body = active_resp.json()
    assert tasks_body["total"] == 2
    assert active_body["total"] == 1
    _assert_legacy_summary_shape(tasks_body["tasks"])
    _assert_legacy_summary_shape(active_body["tasks"])
    for body in (tasks_body, active_body):
        blob = json.dumps(body)
        assert "repository" not in blob
        assert "repository_id" not in blob
        assert private_repo not in blob
        assert public_repo not in blob
        assert "secret-org" not in blob
        assert "/Users/private/" not in blob
