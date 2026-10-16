"""Public active inventory versus independently written records and process identity."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api import delegate_router
from scripts.api.monitor_context import fixture_context
from scripts.orchestration.dead_worker_state import capture_worker_identity


@pytest.fixture
def inventory(tmp_path):
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(delegate_router.router, prefix="/api/delegate")
    tasks = tmp_path / "batch_state" / "tasks"
    tasks.mkdir(parents=True)
    with TestClient(app) as client:
        yield client, tasks


def write(tasks, name="one", **changes):
    record = {
        "task_id": name,
        "status": "running",
        "pid": os.getpid(),
        "worker_identity": capture_worker_identity(os.getpid()),
        "run_nonce": "attempt-1",
    }
    record.update(changes)
    path = tasks / f"{name}.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


def test_empty_is_observed_but_missing_is_unavailable(inventory):
    client, tasks = inventory
    response = client.get("/api/delegate/active")
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["tasks"] == []
    assert response.json()["source"]["records_scanned"] == 0
    tasks.rmdir()
    response = client.get("/api/delegate/active")
    assert response.status_code == 503
    assert response.json()["detail"] == {"status": "unknown", "reason": "task_directory_unavailable"}


@pytest.mark.parametrize("contents", ["{", "[]", '{"task_id":"one"}', '{"status":42}'])
def test_invalid_record_refuses_complete_inventory(inventory, contents):
    client, tasks = inventory
    (tasks / "broken.json").write_text(contents, encoding="utf-8")
    response = client.get("/api/delegate/active")
    assert response.status_code == 503
    assert response.json()["detail"]["reason"] == "task_record_unreadable_or_invalid"
    assert "total" not in response.json()


def test_reader_failure_cannot_be_zero(inventory, monkeypatch):
    client, tasks = inventory
    write(tasks)
    monkeypatch.setattr(delegate_router, "_read_task_state", lambda *args: None)
    response = client.get("/api/delegate/active")
    assert response.status_code == 503
    assert response.json()["detail"]["status"] == "unknown"


def test_directory_reader_failure_cannot_be_zero(inventory, monkeypatch):
    client, _ = inventory
    monkeypatch.setattr(delegate_router.os, "scandir", lambda *args: (_ for _ in ()).throw(PermissionError()))
    response = client.get("/api/delegate/active")
    assert response.status_code == 503
    assert response.json()["detail"]["reason"] == "task_directory_unavailable"


@pytest.mark.parametrize("status", ["running", "spawning"])
def test_live_dead_unknown_attempts_are_explicit(inventory, status):
    client, tasks = inventory
    write(tasks, "live", status=status)
    identity = capture_worker_identity(os.getpid())
    identity["start_time"] += 1
    write(tasks, "recycled", status=status, worker_identity=identity)
    write(tasks, "unknown", status=status, pid=None, worker_identity=None)
    response = client.get("/api/delegate/active")
    assert response.status_code == 200
    body = response.json()
    expected = {"live": True, "unknown": None}
    if status == "spawning":
        expected["recycled"] = False
    assert {row["task_id"]: row["alive"] for row in body["tasks"]} == expected
    assert body["total"] == len(body["tasks"]) == len(expected)
    observations = {row["task_id"]: row for row in body["observations"]}
    assert observations["recycled"]["alive"] is False
    assert observations["unknown"]["liveness_reason"] == "worker_identity_or_visibility_unknown"
    assert observations["live"]["record_status"] == status
    assert observations["live"]["run_nonce"] == "attempt-1"
    assert body["source"]["excluded_dead_running"] == (1 if status == "running" else 0)


def test_in_place_status_and_nonce_update_inside_old_ttl(inventory):
    client, tasks = inventory
    path = write(tasks)
    directory_mtime = tasks.stat().st_mtime_ns
    assert client.get("/api/delegate/active").json()["observations"][0]["run_nonce"] == "attempt-1"
    write(tasks, run_nonce="attempt-2", status="spawning", pid=None)
    assert tasks.stat().st_mtime_ns == directory_mtime
    body = client.get("/api/delegate/active").json()
    assert body["total"] == 1
    assert body["tasks"][0]["status"] == "spawning"
    assert body["observations"][0]["run_nonce"] == "attempt-2"
    # Restoring mtime must not defeat ctime/content observation.
    prior = path.stat()
    write(tasks, run_nonce="attempt-3", status="done")
    os.utime(path, ns=(prior.st_atime_ns, prior.st_mtime_ns))
    body = client.get("/api/delegate/active").json()
    assert body["total"] == 0
    assert body["tasks"] == []


@pytest.mark.parametrize("change", ["rewrite", "add", "remove", "replace-directory"])
def test_concurrent_authority_change_refuses_success(inventory, monkeypatch, change):
    client, tasks = inventory
    path = write(tasks)
    original = delegate_router._read_task_state
    changed = False

    def read(*args):
        nonlocal changed
        record = original(*args)
        if not changed:
            changed = True
            if change == "rewrite":
                write(tasks, run_nonce="replacement")
            elif change == "add":
                write(tasks, "new")
            elif change == "remove":
                path.unlink()
            else:
                tasks.rename(tasks.with_name("old-tasks"))
                tasks.mkdir()
        return record

    monkeypatch.setattr(delegate_router, "_read_task_state", read)
    response = client.get("/api/delegate/active")
    assert response.status_code == 503
    assert response.json()["detail"]["reason"] == "task_authority_changed"


def test_source_age_is_not_start_age_or_cache_age(inventory):
    client, tasks = inventory
    path = write(tasks, started_at="2000-01-01T00:00:00Z", prompt="PRIVATE", cwd="/private/location")
    os.utime(path, (1_600_000_000, 1_600_000_000))
    body = client.get("/api/delegate/active").json()
    observation = body["observations"][0]
    assert observation["record_updated_at"] == "2020-09-13T12:26:40+00:00"
    assert observation["record_age_s"] > 1000
    assert observation["liveness_age_s"] >= 0
    assert body["cache_age_s"] == 0
    assert datetime.fromisoformat(body["source"]["observed_at"]) <= datetime.now(UTC)
    assert body["tasks"][0]["age_s"] > observation["record_age_s"]
    blob = json.dumps(body)
    assert "PRIVATE" not in blob
    assert "/private/location" not in blob
    assert str(tasks) not in blob


def test_hot_scope_excludes_archive_and_snapshot_sidecars(inventory):
    client, tasks = inventory
    write(tasks)
    (tasks / "one.snapshots.json").write_text("[]", encoding="utf-8")
    (tasks / "archive").mkdir()
    write(tasks / "archive", "old", status="running")
    write(tasks, "terminal", status="done")
    body = client.get("/api/delegate/active").json()
    assert body["total"] == 1
    assert body["source"]["records_scanned"] == 2
    assert body["source"]["records_in_scope"] == 1
    assert [row["task_id"] for row in body["tasks"]] == ["one"]


def test_exited_process_and_missing_identity_are_not_live(inventory):
    client, tasks = inventory
    process = subprocess.Popen(["sleep", "30"])
    try:
        identity = capture_worker_identity(process.pid)
        write(tasks, "exited", pid=process.pid, worker_identity=identity)
        assert client.get("/api/delegate/active").json()["tasks"][0]["alive"] is True
    finally:
        process.terminate()
        process.wait(timeout=5)
    body = client.get("/api/delegate/active").json()
    assert body["total"] == 0
    assert body["observations"][0]["alive"] is False
    assert body["source"]["excluded_dead_running"] == 1


def test_liveness_change_during_scan_refuses_success(inventory, monkeypatch):
    client, tasks = inventory
    write(tasks)
    answers = iter([True, None])
    monkeypatch.setattr(delegate_router, "worker_liveness", lambda *a, **k: next(answers))
    response = client.get("/api/delegate/active")
    assert response.status_code == 503
    assert response.json()["detail"]["reason"] == "task_authority_changed"


def test_unreadable_encoding_refuses_complete_inventory(inventory):
    client, tasks = inventory
    (tasks / "broken.json").write_bytes(b"\xff")
    response = client.get("/api/delegate/active")
    assert response.status_code == 503
    assert response.json()["detail"]["reason"] == "task_record_unreadable_or_invalid"


def test_internal_filtered_source_does_not_expose_foreign_attempts(inventory):
    client, tasks = inventory
    write(tasks, "public", repository_id="public/project")
    write(tasks, "foreign", repository_id="private/project")
    write(tasks, "unclassified", repository_id=None)
    body = delegate_router.active_delegate_tasks(repository="public/project", ctx=client.app.state.ctx)
    assert body["total"] == 1
    assert [row["task_id"] for row in body["tasks"]] == ["public"]
    assert [row["task_id"] for row in body["observations"]] == ["public"]
    assert "private/project" not in json.dumps(body)
