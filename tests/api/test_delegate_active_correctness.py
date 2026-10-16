"""Public active inventory versus independently written records and process identity."""

from __future__ import annotations

import json
import os
import subprocess
import sys
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


@pytest.mark.parametrize("status", ["running", "spawning"])
def test_legacy_unrelated_live_pid_is_unknown_and_dead_pid_is_proven(inventory, status):
    client, tasks = inventory
    process = subprocess.Popen(["sleep", "30"])
    path = tasks / "legacy.json"
    try:
        # No identity or launch binding: this durable record names an unrelated process.
        contents = json.dumps({"task_id": "legacy", "status": status, "pid": process.pid})
        path.write_text(contents, encoding="utf-8")
        response = client.get("/api/delegate/active")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert [(row["task_id"], row["status"], row["alive"]) for row in body["tasks"]] == [("legacy", status, None)]
        observation = body["observations"][0]
        assert observation["task_id"] == "legacy"
        assert observation["alive"] is None
        assert observation["liveness_reason"] == "legacy_worker_identity_unattested"
        assert observation["liveness_basis"] == "legacy_pid_namespace"
        assert observation["excluded_dead_running"] is False
        assert body["source"]["records_scanned"] == body["source"]["records_in_scope"] == 1
        assert body["source"]["excluded_dead_running"] == 0
        assert path.read_text(encoding="utf-8") == contents
    finally:
        process.terminate()
        process.wait(timeout=5)

    # The same namespace-qualified legacy record now has proof of process absence.
    response = client.get("/api/delegate/active")
    assert response.status_code == 200
    body = response.json()
    assert body["observations"][0]["alive"] is False
    assert body["observations"][0]["liveness_reason"] is None
    assert body["observations"][0]["record_status"] == status
    if status == "running":
        assert body["total"] == 0
        assert body["tasks"] == []
        assert body["source"]["excluded_dead_running"] == 1
    else:
        assert body["total"] == 1
        assert body["tasks"][0]["alive"] is False
        assert body["source"]["excluded_dead_running"] == 0
    assert body["source"]["records_in_scope"] == 1
    assert path.read_text(encoding="utf-8") == contents


@pytest.mark.parametrize("identity_change", [{"start_time": None}, {"pid_namespace": "pid:[0]"}])
def test_identity_bound_unverifiable_live_process_stays_unknown(inventory, identity_change):
    client, tasks = inventory
    identity = capture_worker_identity(os.getpid())
    identity.update(identity_change)
    write(tasks, worker_identity=identity)
    response = client.get("/api/delegate/active")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["tasks"][0]["alive"] is None
    assert body["observations"][0]["alive"] is None
    assert body["observations"][0]["liveness_basis"] == "worker_identity"
    assert body["observations"][0]["liveness_reason"] == "worker_identity_or_visibility_unknown"


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


def closeout_state():
    return {
        "target": None,
        "target_args": None,
        "baseline": None,
        "behavior_proof": {},
        "cycle_outstanding_counts": [],
        "findings": [],
        "resolved_reviewer": {},
    }


def test_validated_closeout_artifacts_are_counted_by_content(inventory):
    client, tasks = inventory
    for name in ("ordinary", "review.closeout", "review-resolve", "another"):
        (tasks / f"{name}.json").write_text(json.dumps(closeout_state()))
    write(tasks, "real.closeout")
    body = client.get("/api/delegate/active").json()
    assert body["total"] == 1
    assert body["tasks"][0]["task_id"] == "real.closeout"
    assert body["source"]["records_scanned"] == 1
    assert body["source"]["closeout_artifacts"] == 4
    assert client.get("/api/delegate/active").json()["source"]["closeout_artifacts"] == 4


@pytest.mark.parametrize(
    "record",
    [
        {"task_id": "impl-9447", "agent": "codex", "model": "unknown", "repository": "public/project"},
        {**closeout_state(), "status": "running"},
        {**closeout_state(), "task_id": "real-task"},
        {**closeout_state(), "findings": None},
        {**closeout_state(), "resolved_reviewer": []},
        {"target": None},
    ],
)
def test_unclassified_or_malformed_sidecar_cannot_hide_a_record(inventory, record):
    client, tasks = inventory
    # A status-bearing record remains a task even when it has closeout keys.
    (tasks / "review.closeout.json").write_text(json.dumps(record))
    response = client.get("/api/delegate/active")
    if record.get("status") == "running":
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert response.json()["source"]["closeout_artifacts"] == 0
    else:
        assert response.status_code == 503
        assert response.json()["detail"]["reason"] == "task_record_unreadable_or_invalid"


@pytest.mark.parametrize("identity", [False, True])
def test_oversized_pid_has_explicit_unknown_liveness(inventory, identity):
    client, tasks = inventory
    changes = {"pid": 2**40, "worker_identity": None}
    if identity:
        changes["worker_identity"] = {**capture_worker_identity(os.getpid()), "pid": 2**40}
    write(tasks, **changes)
    body = client.get("/api/delegate/active").json()
    assert body["total"] == 1
    assert body["tasks"][0]["alive"] is None
    assert body["observations"][0]["liveness_reason"] == "worker_identity_or_visibility_unknown"


@pytest.mark.parametrize("error", [OverflowError, ValueError])
def test_final_liveness_sample_contains_expected_probe_errors(inventory, monkeypatch, error):
    client, tasks = inventory
    write(tasks)
    calls = 0

    def probe(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return True
        raise error("invalid pid")

    monkeypatch.setattr(delegate_router, "worker_liveness", probe)
    response = client.get("/api/delegate/active")
    assert response.status_code == 503
    assert response.json()["detail"]["reason"] == "task_authority_changed"
    assert calls == 2


@pytest.mark.parametrize("phase", ["read", "final-sample"])
@pytest.mark.parametrize("change", ["sqlite-sidecars", "added-task", "removed-task", "replacement"])
def test_directory_changes_recheck_record_membership_and_tokens(inventory, monkeypatch, phase, change):
    client, tasks = inventory
    path = write(tasks)
    original = delegate_router._read_task_state if phase == "read" else delegate_router._active_worker_liveness
    calls = 0

    def hooked(*args):
        nonlocal calls
        result = original(*args)
        calls += 1
        if calls == (1 if phase == "read" else 2):
            if change == "sqlite-sidecars":
                for name in (".task_cache.sqlite3", ".task_cache.sqlite3-wal", ".task_cache.sqlite3-shm"):
                    (tasks / name).write_bytes(b"cache")
            elif change == "added-task":
                write(tasks, "new")
            elif change == "removed-task":
                path.unlink()
            else:
                before = path.stat()
                replacement = tasks / "replacement.tmp"
                replacement.write_bytes(path.read_bytes())
                os.utime(replacement, ns=(before.st_atime_ns, before.st_mtime_ns))
                replacement.replace(path)
        return result

    target = "_read_task_state" if phase == "read" else "_active_worker_liveness"
    monkeypatch.setattr(delegate_router, target, hooked)
    response = client.get("/api/delegate/active")
    assert response.status_code == (200 if change == "sqlite-sidecars" else 503)
    if response.status_code == 200:
        assert response.json()["total"] == 1
    else:
        assert response.json()["detail"]["reason"] == "task_authority_changed"


@pytest.mark.parametrize("change", ["restored-mtime", "replacement", "disappearance"])
def test_terminal_fact_cache_revalidates_full_generation(inventory, change):
    client, tasks = inventory
    path = write(tasks, status="done")
    assert client.get("/api/delegate/active").json()["total"] == 0
    before = path.stat()
    if change == "disappearance":
        path.unlink()
    else:
        if change == "replacement":
            path.unlink()
        write(tasks, status="running", run_nonce="fresh-attempt")
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    body = client.get("/api/delegate/active").json()
    assert body["total"] == (0 if change == "disappearance" else 1)
    if change != "disappearance":
        assert body["observations"][0]["run_nonce"] == "fresh-attempt"
    else:
        assert client.app.state.ctx.runtime._derived["delegate_active_facts"]["facts"] == {}


def test_terminal_fact_cache_is_compact_bounded_and_context_owned(inventory, monkeypatch):
    client, tasks = inventory
    monkeypatch.setattr(delegate_router, "ACTIVE_FACT_CACHE_LIMIT", 2)
    for i in range(3):
        write(tasks, str(i), status="done", payload="unretained" * 10000)
    # Every uncached record is read once, whether or not it is then parsed.
    original = delegate_router._read_task_bytes
    reads = []

    def read(*args):
        reads.append(args[0])
        return original(*args)

    monkeypatch.setattr(delegate_router, "_read_task_bytes", read)
    for expected_reads in (3, 4):
        body = client.get("/api/delegate/active").json()
        assert body["total"] == 0
        assert body["source"]["records_scanned"] == 3
        assert len(reads) == expected_reads
    cache = client.app.state.ctx.runtime._derived["delegate_active_facts"]["facts"]
    assert len(cache) == 2
    assert all(len(token) == 5 and status == "done" for token, status in cache.values())
    # A second context over identical paths still starts without parsed facts.
    other = fixture_context(tasks.parent.parent)
    assert delegate_router.active_delegate_tasks(ctx=other)["source"]["records_scanned"] == 3
    assert len(reads) == 7


@pytest.mark.parametrize("outside", [False, True])
def test_active_reader_resolves_contained_links_and_refuses_escapes(inventory, outside):
    client, tasks = inventory
    original = write(tasks, "target")
    if outside:
        destination = tasks.parent / "outside.json"
        original.rename(destination)
    else:
        destination = original
    (tasks / "linked.json").symlink_to(destination)
    response = client.get("/api/delegate/active")
    assert response.status_code == (503 if outside else 200)
    if not outside:
        assert response.json()["total"] == 2


@pytest.mark.parametrize("change", ["cache-sidecar", "task", "directory"])
def test_directory_change_during_final_token_walk_is_rechecked(inventory, monkeypatch, change):
    client, tasks = inventory
    path = write(tasks)
    original = delegate_router.os.stat
    fired = False

    def probe(name, *args, **kwargs):
        nonlocal fired
        result = original(name, *args, **kwargs)
        if str(name) == str(path) and kwargs.get("follow_symlinks") is False and not fired:
            fired = True
            if change == "cache-sidecar":
                (tasks / ".task_cache.sqlite3-wal").write_bytes(b"cache")
            elif change == "task":
                write(tasks, "new")
            else:
                old = tasks.with_name("old-tasks")
                tasks.rename(old)
                tasks.mkdir()
                # Preserve record tokens while changing directory identity.
                os.link(old / path.name, path)
        return result

    monkeypatch.setattr(delegate_router.os, "stat", probe)
    response = client.get("/api/delegate/active")
    assert fired
    assert response.status_code == (200 if change == "cache-sidecar" else 503)


def test_cache_does_not_retain_unbounded_status_or_payload(inventory):
    client, tasks = inventory
    write(tasks, status="x" * 100000, payload="unretained" * 10000)
    assert client.get("/api/delegate/active").json()["source"]["records_scanned"] == 1
    assert client.app.state.ctx.runtime._derived["delegate_active_facts"]["facts"] == {}


def test_cached_terminal_replaced_by_outside_symlink_is_refused(inventory):
    client, tasks = inventory
    path = write(tasks, status="done")
    outside = tasks.parent / "outside.json"
    os.link(path, outside)
    assert client.get("/api/delegate/active").json()["total"] == 0
    path.unlink()
    path.symlink_to(outside)
    response = client.get("/api/delegate/active")
    assert response.status_code == 503
    assert response.json()["detail"]["reason"] == "task_record_unreadable_or_invalid"


def test_multiple_benign_sidecars_during_final_recheck_remain_qualified(inventory, monkeypatch):
    client, tasks = inventory
    write(tasks)
    original = type(tasks).stat
    calls = 0

    def probe(path, *args, **kwargs):
        nonlocal calls
        if path == tasks:
            calls += 1
            if calls in (3, 5):
                (tasks / f".task_cache.sqlite3-{calls}").write_bytes(b"cache")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(type(tasks), "stat", probe)
    response = client.get("/api/delegate/active")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert calls >= 5


@pytest.mark.parametrize("scan", [False, True])
@pytest.mark.parametrize("candidate", ["absolute", "traversal", "prefix-sibling"])
def test_reader_refuses_lexical_escape_before_filesystem_access(inventory, monkeypatch, scan, candidate):
    client, tasks = inventory
    paths = {
        "absolute": tasks.parent / "outside.json",
        "traversal": tasks / ".." / "outside.json",
        "prefix-sibling": tasks.with_name("tasks-other") / "one.json",
    }

    def refuse(*args, **kwargs):
        pytest.fail("escaped candidate reached a filesystem probe")

    root = str(tasks.resolve())
    if not scan:
        monkeypatch.setattr(delegate_router, "_tasks_root", lambda ctx: root)
    for name in ("islink", "realpath"):
        monkeypatch.setattr(delegate_router.os.path, name, refuse)
    for name in ("lstat", "open"):
        monkeypatch.setattr(delegate_router.os, name, refuse)
    assert delegate_router._read_task_state(str(paths[candidate]), client.app.state.ctx, root if scan else None) is None


@pytest.mark.parametrize("scan", [False, True])
def test_reader_preserves_nested_detail_and_contained_links(inventory, scan):
    client, tasks = inventory
    nested = tasks / "archive"
    nested.mkdir()
    target = write(nested, status="done")
    link = tasks / "linked.json"
    link.symlink_to(target)
    for path in (target, link):
        assert (
            delegate_router._read_task_state(str(path), client.app.state.ctx, str(tasks.resolve()) if scan else None)[
                "task_id"
            ]
            == "one"
        )
    response = client.get("/api/delegate/tasks/one")
    assert response.status_code == 200
    assert response.json()["task"]["status"] == "done"


@pytest.mark.parametrize("held", [False, True])
@pytest.mark.parametrize("failure", ["none", "corrupt", "directory", "fifo", "fstat", "read"])
def test_reader_closes_every_opened_descriptor(inventory, monkeypatch, failure, held):
    client, tasks = inventory
    path = tasks / "one.json"
    if failure == "directory":
        path.mkdir()
    elif failure == "fifo":
        os.mkfifo(path)
    else:
        path.write_text("{" if failure == "corrupt" else '{"status":"done"}')
    root = str(tasks.resolve())
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY) if held else None
    opened = []
    closed = []
    original_open, original_close = os.open, os.close
    original_fstat, original_read = os.fstat, os.read

    def open_record(name, flags, **kwargs):
        fd = original_open(name, flags, **kwargs)
        opened.append(fd)
        return fd

    def close_record(fd):
        closed.append(fd)
        return original_close(fd)

    def fstat(fd):
        if failure == "fstat":
            raise OSError("injected descriptor stat failure")
        return original_fstat(fd)

    def read(fd, size):
        if failure == "read":
            raise OSError("injected descriptor read failure")
        return original_read(fd, size)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(delegate_router.os, "open", open_record)
            patch.setattr(delegate_router.os, "close", close_record)
            patch.setattr(delegate_router.os, "fstat", fstat)
            patch.setattr(delegate_router.os, "read", read)
            result = delegate_router._read_task_state(str(path), client.app.state.ctx, root, root_fd)
        # An unheld read opens the root descriptor too; a held one is never closed here.
        per_attempt = 1 if held else 2
        assert result == ({"status": "done"} if failure == "none" else None)
        assert len(opened) == per_attempt * (2 if failure in {"corrupt", "fstat", "read"} else 1)
        assert sorted(closed) == sorted(opened)
        assert root_fd not in closed
    finally:
        if root_fd is not None:
            os.close(root_fd)


_NONREGULAR_FLIGHT = r"""
import asyncio
import json
import os
from pathlib import Path
import sys
import httpx
from fastapi import FastAPI
from scripts.api import delegate_router
from scripts.api.monitor_context import fixture_context
root, variant = Path(sys.argv[1]), sys.argv[2]
tasks = root / 'batch_state/tasks'
tasks.mkdir(parents=True)
path = tasks / 'one.json'
record = '{"task_id":"one","status":"spawning"}'
path.write_text(record)
app = FastAPI()
app.state.ctx = fixture_context(root)
app.include_router(delegate_router.router, prefix='/api/delegate')
original_open = os.open
swapped = False
def replace_at_open(name, flags, *args, **kwargs):
    global swapped
    if os.path.basename(str(name)) == path.name and not swapped:
        swapped = True
        path.unlink()
        if variant == 'swap-link':
            outside = root / 'outside.json'
            outside.write_text(record)
            path.symlink_to(outside)
        else:
            os.mkfifo(path)
    return original_open(name, flags, *args, **kwargs)
async def run():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        if variant == 'cached-fifo':
            path.write_text('{"status":"done"}')
            assert (await client.get('/api/delegate/active')).status_code == 200
        if variant in {'fifo', 'cached-fifo'}:
            path.unlink()
            os.mkfifo(path)
        else:
            delegate_router.os.open = replace_at_open
        responses = await asyncio.gather(*[client.get('/api/delegate/active') for _ in range(2)])
        responses.append(await client.get('/api/delegate/active'))
        delegate_router.os.open = original_open
        path.unlink()
        path.write_text(record)
        recovered = await client.get('/api/delegate/active')
        print(json.dumps({'statuses': [r.status_code for r in responses],
            'details': [r.json()['detail'] for r in responses],
            'recovered_status': recovered.status_code, 'recovered_total': recovered.json()['total']}))
asyncio.run(run())
"""


@pytest.mark.parametrize("variant", ["fifo", "swap-fifo", "cached-fifo", "swap-link"])
def test_nonregular_or_swapped_leaf_refuses_shared_flight_without_hanging(tmp_path, variant):
    result = subprocess.run(
        [sys.executable, "-c", _NONREGULAR_FLIGHT, str(tmp_path), variant],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    assert json.loads(result.stdout) == {
        "statuses": [503, 503, 503],
        "details": [{"status": "unknown", "reason": "task_record_unreadable_or_invalid"}] * 3,
        "recovered_status": 200,
        "recovered_total": 1,
    }


def _linked_store(tmp_path):
    """A store whose configured batch_state path runs through a symlinked ancestor."""
    real = tmp_path / "real"
    (real / "batch_state" / "tasks").mkdir(parents=True)
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    app = FastAPI()
    app.state.ctx = fixture_context(real).with_roots(batch_state_dir=link / "batch_state")
    app.include_router(delegate_router.router, prefix="/api/delegate")
    return app, link / "batch_state" / "tasks"


def test_symlinked_store_ancestor_serves_history_detail_and_active(tmp_path):
    app, tasks = _linked_store(tmp_path)
    write(tasks, "live")
    write(tasks, "finished", status="done")
    (tasks / "archive").mkdir()
    write(tasks / "archive", "old", status="done")
    with TestClient(app) as client:
        active = client.get("/api/delegate/active")
        assert active.status_code == 200
        assert [row["task_id"] for row in active.json()["tasks"]] == ["live"]
        assert active.json()["source"]["records_scanned"] == 2
        history = client.get("/api/delegate/tasks", params={"status": "all"})
        assert history.status_code == 200
        assert sorted(row["task_id"] for row in history.json()["tasks"]) == ["finished", "live", "old"]
        assert client.get("/api/delegate/tasks/old").json()["task"]["status"] == "done"
    # The lexical configured path and the resolved path both read, with and without a scan root.
    root = os.path.realpath(tasks)
    for base in (tasks, tasks.resolve()):
        for scan_root in (None, root):
            state = delegate_router._read_task_state(str(base / "finished.json"), app.state.ctx, scan_root)
            assert state["status"] == "done"


@pytest.mark.parametrize("candidate", ["absolute", "traversal", "prefix-sibling"])
def test_symlinked_ancestor_still_refuses_lexical_escape_before_filesystem_access(tmp_path, monkeypatch, candidate):
    app, tasks = _linked_store(tmp_path)
    paths = {
        "absolute": tasks.parent / "outside.json",
        "traversal": tasks / ".." / "outside.json",
        "prefix-sibling": tasks.with_name("tasks-other") / "one.json",
    }

    def refuse(*args, **kwargs):
        pytest.fail("escaped candidate reached a filesystem probe")

    root = os.path.realpath(tasks)
    for name in ("islink", "realpath"):
        monkeypatch.setattr(delegate_router.os.path, name, refuse)
    for name in ("lstat", "open", "stat"):
        monkeypatch.setattr(delegate_router.os, name, refuse)
    monkeypatch.setattr(delegate_router, "_tasks_root", lambda ctx: root)
    for scan_root in (None, root):
        assert delegate_router._read_task_state(str(paths[candidate]), app.state.ctx, scan_root) is None


def test_parent_link_escaping_the_store_is_refused_and_contained_parent_link_reads(inventory):
    client, tasks = inventory
    outside = tasks.parent / "outside-archive"
    outside.mkdir()
    write(outside, "escaped", status="done")
    (tasks / "archive").symlink_to(outside, target_is_directory=True)
    write(tasks, "inside", status="done")
    nested = tasks / "nested"
    nested.mkdir()
    write(nested, "kept", status="done")
    (tasks / "alias").symlink_to(nested, target_is_directory=True)
    history = client.get("/api/delegate/tasks", params={"status": "all"})
    assert [row["task_id"] for row in history.json()["tasks"]] == ["inside"]
    assert client.get("/api/delegate/tasks/escaped").status_code == 404
    root = str(tasks.resolve())
    ctx = client.app.state.ctx
    for scan_root in (None, root):
        assert delegate_router._read_task_state(str(tasks / "archive" / "escaped.json"), ctx, scan_root) is None
        assert delegate_router._read_task_state(str(tasks / "alias" / "kept.json"), ctx, scan_root)["task_id"] == "kept"


def test_parent_swapped_after_resolution_cannot_redirect_the_read(inventory, monkeypatch):
    client, tasks = inventory
    nested = tasks / "nested"
    nested.mkdir()
    write(nested, "kept", status="done")
    decoy = tasks.parent / "decoy"
    decoy.mkdir()
    (decoy / "kept.json").write_text('{"status":"running"}', encoding="utf-8")
    original = os.path.realpath

    def swap_after_resolving(path, *args, **kwargs):
        resolved = original(path, *args, **kwargs)
        if resolved.endswith(os.path.join("nested", "kept.json")):
            nested.rename(tasks / "moved")
            nested.symlink_to(decoy, target_is_directory=True)
        return resolved

    monkeypatch.setattr(delegate_router.os.path, "realpath", swap_after_resolving)
    monkeypatch.setattr(delegate_router.time, "sleep", lambda _seconds: None)
    assert delegate_router._read_task_state(str(nested / "kept.json"), client.app.state.ctx) is None


def test_active_reads_stay_in_the_held_directory_when_the_store_path_is_swapped(inventory, monkeypatch):
    client, tasks = inventory
    write(tasks, "one")
    decoy = tasks.parent / "decoy"
    decoy.mkdir()
    (decoy / "one.json").write_text("{", encoding="utf-8")
    original = os.lstat
    swapped = False

    def swap_before_first_record(path, *args, **kwargs):
        nonlocal swapped
        if not swapped and os.path.basename(str(path)) == "one.json":
            swapped = True
            tasks.rename(tasks.with_name("held"))
            tasks.symlink_to(decoy, target_is_directory=True)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(delegate_router.os, "lstat", swap_before_first_record)
    response = client.get("/api/delegate/active")
    assert swapped
    # Following the swapped path would read the decoy's invalid record instead.
    assert response.status_code == 503
    assert response.json()["detail"] == {"status": "unknown", "reason": "task_authority_changed"}


def test_store_replaced_between_listing_and_holding_is_refused(inventory, monkeypatch):
    client, tasks = inventory
    write(tasks, "one")
    original = delegate_router._active_candidate_names
    calls = 0

    def replace_after_listing(directory):
        nonlocal calls
        calls += 1
        names = original(directory)
        if calls == 1:
            tasks.rename(tasks.with_name("held"))
            tasks.mkdir()
        return names

    monkeypatch.setattr(delegate_router, "_active_candidate_names", replace_after_listing)
    response = client.get("/api/delegate/active")
    assert response.status_code == 503
    assert response.json()["detail"] == {"status": "unknown", "reason": "task_authority_changed"}


@pytest.mark.parametrize("contents", ['{"status":"done"} trailing-invalid-data', None])
def test_short_reads_continue_until_eof(inventory, monkeypatch, contents):
    client, tasks = inventory
    if contents is None:
        path = write(tasks)
    else:
        path = tasks / "one.json"
        path.write_text(contents, encoding="utf-8")
    original = os.read
    # A reader may return fewer bytes than asked before the end of a regular file.
    monkeypatch.setattr(delegate_router.os, "read", lambda fd, size: original(fd, min(size, 17)))
    monkeypatch.setattr(delegate_router.time, "sleep", lambda _seconds: None)
    state = delegate_router._read_task_state(str(path), client.app.state.ctx)
    response = client.get("/api/delegate/active")
    if contents is None:
        assert state == json.loads(path.read_text(encoding="utf-8"))
        assert response.status_code == 200
        assert response.json()["total"] == 1
    else:
        assert state is None
        assert response.status_code == 503
        assert response.json()["detail"]["reason"] == "task_record_unreadable_or_invalid"


def test_cold_inventory_parses_only_possibly_active_records(inventory, monkeypatch):
    _, tasks = inventory
    statuses = ["done", "failed", "needs_finalize", "blocked", "cancelled"]
    for i in range(50):
        write(tasks, f"terminal-{i}", status=statuses[i % 5], dispatch=[{"status": "running", "note": "}"}] * 3)
    live = write(tasks, "live").read_text(encoding="utf-8")
    # Duplicate keys keep the last value, as the full parse does.
    duplicate = live.replace('"live"', '"duplicate"')
    duplicate = duplicate.replace('"status": "running"', '"status": "done", "status": "running"')
    assert duplicate.count('"status"') == 2
    (tasks / "duplicate.json").write_text(duplicate, encoding="utf-8")
    original_loads, original_read = json.loads, delegate_router._read_task_state
    parsed, parsed_records = [], []

    def loads(*args, **kwargs):
        parsed.append(args[0])
        return original_loads(*args, **kwargs)

    def read(*args):
        parsed_records.append(os.path.basename(args[0]))
        return original_read(*args)

    with monkeypatch.context() as patch:
        patch.setattr(delegate_router.json, "loads", loads)
        patch.setattr(delegate_router, "_read_task_state", read)
        body = delegate_router.active_delegate_tasks(ctx=fixture_context(tasks.parent.parent))
    assert sorted(row["task_id"] for row in body["tasks"]) == ["duplicate", "live"]
    assert body["source"]["records_scanned"] == 52
    assert sorted(parsed_records) == ["duplicate.json", "live.json"]
    assert len(parsed) == 2


def test_partial_or_extended_terminal_document_is_never_terminal(inventory):
    client, tasks = inventory
    record = json.dumps({"status": "done", "dispatch": [{"key": 1}, {"note": "a}b"}], "tail": {"x": "}"}})
    candidates = [record[:end] for end in range(len(record))]
    candidates += [record + " trailing", record + "{}", record + record, "[" + record + "]"]
    path = tasks / "one.json"
    for contents in candidates:
        path.write_text(contents, encoding="utf-8")
        response = client.get("/api/delegate/active")
        assert response.status_code == 503, contents
        assert response.json()["detail"]["reason"] == "task_record_unreadable_or_invalid"
    path.write_text(record, encoding="utf-8")
    response = client.get("/api/delegate/active")
    assert response.status_code == 200
    assert response.json()["source"]["records_scanned"] == 1
