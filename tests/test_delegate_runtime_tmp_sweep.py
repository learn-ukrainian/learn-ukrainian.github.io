"""Regression tests for runtime-tmp orphan sweep performance (#7203)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

import pytest

import scripts.delegate as delegate
from scripts.orchestration import job_host_exec
from tests.test_delegate import _init_git_repo_for_test, _seed_read_only_checkout_fixture


@pytest.fixture
def tmp_tasks_dir(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks_dir))
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path))
    monkeypatch.setattr(delegate, "scratch_scan_roots", lambda: [tmp_path])
    return tasks_dir


def _write_decoy_task_record(tasks_dir: Path, task_id: str) -> None:
    tasks_dir.mkdir(parents=True, exist_ok=True)
    state_path = tasks_dir / f"{task_id.replace('/', '_')}.json"
    state_path.write_text(
        json.dumps({"task_id": task_id, "status": "done", "pid": None}),
        encoding="utf-8",
    )


def _seed_sweep_fixture(
    tmp_path: Path,
    tasks_dir: Path,
    *,
    marked_lease_count: int,
    legacy_lease_count: int,
    decoy_record_count: int,
    legacy_status: str = "done",
) -> Path:
    namespace = tmp_path / "learn-ukrainian"
    namespace.mkdir(parents=True, exist_ok=True)

    for index in range(decoy_record_count):
        _write_decoy_task_record(tasks_dir, f"decoy-task-{index:04d}")

    for index in range(marked_lease_count):
        task_id = f"marked-task-{index:04d}"
        lease = namespace / delegate._runtime_tmp_lease_name(task_id)
        lease.mkdir(parents=True)
        delegate._write_runtime_tmp_task_id_marker(lease, task_id)
        delegate._write_state_atomic(
            delegate._state_path(task_id),
            {"task_id": task_id, "status": "done", "pid": None},
        )

    for index in range(legacy_lease_count):
        task_id = f"legacy-task-{index:04d}"
        lease = namespace / delegate._runtime_tmp_lease_name(task_id)
        lease.mkdir(parents=True)
        delegate._write_state_atomic(
            delegate._state_path(task_id),
            {"task_id": task_id, "status": legacy_status, "pid": None},
        )

    return namespace


@pytest.mark.parametrize("identity_case,kept", [("foreign", True), ("reused", False), ("alive", True)])
def test_runtime_tmp_sweep_preserves_unknown_identity(tmp_path, tmp_tasks_dir, monkeypatch, identity_case, kept):
    from scripts.orchestration import dead_worker_state as dead

    namespace = _seed_sweep_fixture(
        tmp_path, tmp_tasks_dir, marked_lease_count=1, legacy_lease_count=0, decoy_record_count=0,
    )
    task_id = "marked-task-0000"
    identity = {"pid": 123, "start_time": 100, "pid_namespace": dead.INITIAL_PID_NAMESPACE}
    monkeypatch.setattr(dead, "_pid_namespace", lambda process="self": dead.INITIAL_PID_NAMESPACE)
    monkeypatch.setattr(dead, "_proc_pid_namespace", lambda: dead.INITIAL_PID_NAMESPACE)
    monkeypatch.setattr(dead, "_process_stat", lambda process: (123, 100))
    if identity_case == "foreign":
        identity["pid_namespace"] = "pid:[999999]"
    elif identity_case == "reused":
        identity["start_time"] -= 1
    delegate._write_state_atomic(delegate._state_path(task_id), {
        "task_id": task_id, "status": "done", "pid": identity["pid"], "worker_identity": identity,
    })
    monkeypatch.setattr(delegate, "_preserve_runtime_tmp_held_work", lambda *_: {})
    result = delegate._sweep_runtime_tmp_orphans()
    assert result["leases_reaped"] == (0 if kept else 1)
    assert (namespace / delegate._runtime_tmp_lease_name(task_id)).exists() is kept


def test_read_only_dispatch_task_record_stays_within_byte_budget(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _init_git_repo_for_test(checkout, monkeypatch)
    _seed_read_only_checkout_fixture(checkout, monkeypatch)
    for index in range(2_000):
        relative = f"bulk/path-{index:04d}.txt"
        target = checkout / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("x" * 200, encoding="utf-8")
        subprocess.run(
            ["git", "add", relative],
            cwd=checkout,
            check=True,
            capture_output=True,
            timeout=30,
        )
    subprocess.run(
        ["git", "commit", "-m", "bulk fixture"],
        cwd=checkout,
        check=True,
        capture_output=True,
        timeout=30,
    )

    task_id = "read-only-record-budget"
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(state_path, {"task_id": task_id, "cwd": str(checkout)})
    huge_snapshot = {f"path-{index:04d}.txt": " M" for index in range(100_000)}

    with (
        patch(
            "agent_runtime.runner.invoke",
            return_value=type(
                "Result",
                (),
                {
                    "ok": True,
                    "response": "ok",
                    "stderr_excerpt": None,
                    "returncode": 0,
                    "rate_limited": False,
                },
            )(),
        ),
        patch.object(
            delegate,
            "_read_only_checkout_snapshot",
            side_effect=[(huge_snapshot, None), (huge_snapshot, None)],
        ),
    ):
        rc = delegate._run_worker(
            task_id=task_id,
            agent="codex",
            prompt="read-only inventory",
            mode="read-only",
            cwd_str=str(checkout),
            model=None,
            hard_timeout=60,
        )

    assert rc == 0
    record_bytes = state_path.stat().st_size
    snapshot_dir = delegate._read_only_snapshot_dir_for(task_id)
    assert snapshot_dir.is_dir()
    assert (snapshot_dir / "digest.json").is_file()
    assert not (snapshot_dir / "read_only_checkout_pre.json").exists()
    assert not (snapshot_dir / "read_only_checkout_post.json").exists()
    assert record_bytes < delegate._READ_ONLY_CHECKOUT_RECORD_BYTE_BUDGET
    state = delegate._read_state(state_path)
    assert state is not None
    assert state["read_only_snapshot_retention"] == "digest"
    assert "read_only_checkout_pre" not in state
    assert "read_only_checkout_pre" not in json.loads(state_path.read_text(encoding="utf-8"))


def _lease_task_id(prefix: str) -> str:
    """One lease task id for this case. A shared id names one shared lease directory (#9927)."""
    current = os.environ.get("PYTEST_CURRENT_TEST", prefix)
    node = current.split(" ", 1)[0]
    digest = hashlib.sha256(node.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def _seed_legacy_running_lease(
    tmp_path: Path,
    tasks_dir: Path,
    *,
    task_id: str | None = None,
) -> Path:
    if task_id is None:
        task_id = _lease_task_id("legacy-running")
    namespace = tmp_path / "learn-ukrainian"
    lease = namespace / delegate._runtime_tmp_lease_name(task_id)
    lease.mkdir(parents=True)
    delegate._write_state_atomic(
        delegate._state_path(task_id),
        {"task_id": task_id, "status": "running", "pid": None},
    )
    return lease


def test_runtime_tmp_orphan_sweep_backfill_write_failure_is_non_fatal(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """Lease gone between resolution and backfill must not abort the sweep."""
    _seed_legacy_running_lease(tmp_path, tmp_tasks_dir)
    original_write = delegate._write_runtime_tmp_task_id_marker

    def fail_backfill_write(lease_root: Path, task_id: str, *, no_clobber: bool = False) -> None:
        if no_clobber:
            raise FileNotFoundError(lease_root)
        original_write(lease_root, task_id, no_clobber=no_clobber)

    monkeypatch.setattr(delegate, "_write_runtime_tmp_task_id_marker", fail_backfill_write)

    result = delegate._sweep_runtime_tmp_orphans()

    assert result["errors"] == 0
    assert result["leases_reaped"] == 0


def test_dispatch_survives_runtime_tmp_backfill_write_failure(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """Dispatch must proceed when orphan-sweep marker backfill is best-effort."""
    from tests.helpers.dispatch_checkout import isolate_dispatch_repo

    isolate_dispatch_repo(monkeypatch, tmp_path, delegate)
    monkeypatch.setenv(job_host_exec.ENV_ALLOW_NOTEBOOK, "1")
    _seed_legacy_running_lease(tmp_path, tmp_tasks_dir)
    original_write = delegate._write_runtime_tmp_task_id_marker

    def fail_backfill_write(lease_root: Path, task_id: str, *, no_clobber: bool = False) -> None:
        if no_clobber:
            raise FileNotFoundError(lease_root)
        original_write(lease_root, task_id, no_clobber=no_clobber)

    monkeypatch.setattr(delegate, "_write_runtime_tmp_task_id_marker", fail_backfill_write)

    class _FakeStdin:
        def write(self, _data):
            pass

        def close(self):
            pass

    class _FakeProc:
        pid = 24680
        stdin = _FakeStdin()

    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *args, **kwargs: _FakeProc())

    args = argparse.Namespace(
        agent="codex",
        task_id="backfill-survives-dispatch",
        prompt="test",
        prompt_file=None,
        mode="read-only",
        model=None,
        cwd=str(delegate._REPO_ROOT),
        worktree=None,
        hard_timeout=3600,
        allow_merge=False,
        dry_run=False,
        force_new=False,
        initiator="codex",
        output_schema=None,
        output_schema_sha256=None,
        sparse_include=None,
        full_checkout=False,
    )

    assert delegate.cmd_dispatch(args) == 0


def test_runtime_tmp_orphan_sweep_corrupt_marker_falls_back_to_legacy(
    tmp_tasks_dir,
    tmp_path,
):
    """Non-UTF-8 markers must not crash the sweep; legacy resolution still works."""
    task_id = "legacy-task-0000"
    namespace = tmp_path / "learn-ukrainian"
    lease = namespace / delegate._runtime_tmp_lease_name(task_id)
    lease.mkdir(parents=True)
    delegate._runtime_tmp_task_id_marker_path(lease).write_bytes(b"\xff\xfe\xfd")
    delegate._write_state_atomic(
        delegate._state_path(task_id),
        {"task_id": task_id, "status": "done", "pid": None},
    )

    result = delegate._sweep_runtime_tmp_orphans()

    assert result["errors"] == 0
    assert result["leases_reaped"] == 1
    assert not lease.exists()


def test_runtime_tmp_orphan_sweep_marker_without_record_uses_orphan_age(
    tmp_tasks_dir,
    tmp_path,
):
    """A marker with no task record reaps only after the seven-day orphan window."""
    task_id = "missing-record-task"
    namespace = tmp_path / "learn-ukrainian"
    lease = namespace / delegate._runtime_tmp_lease_name(task_id)
    lease.mkdir(parents=True)
    delegate._write_runtime_tmp_task_id_marker(lease, task_id)
    now = time.time()
    os.utime(lease, (now, now))

    young_result = delegate._sweep_runtime_tmp_orphans(now=now)
    assert young_result["leases_reaped"] == 0
    assert lease.is_dir()

    old_mtime = now - delegate._RUNTIME_TMP_ORPHAN_MAX_AGE_S - 1
    os.utime(lease, (old_mtime, old_mtime))
    old_result = delegate._sweep_runtime_tmp_orphans(now=now)
    assert old_result["leases_reaped"] == 1
    assert not lease.exists()


def test_runtime_tmp_orphan_sweep_marker_backfill_does_not_clobber(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """Backfill must not replace an existing marker owned by another task id."""
    lease_name = "shared-lease"
    namespace = tmp_path / "learn-ukrainian"
    lease = namespace / lease_name
    lease.mkdir(parents=True)
    fresh_task_id = "fresh/live-task"
    stale_task_id = "stale/resolved-task"
    delegate._write_state_atomic(
        delegate._state_path(stale_task_id),
        {"task_id": stale_task_id, "status": "running", "pid": None},
    )

    def legacy_only_for_stale(
        lease_name_arg: str,
        lease_root: Path,
        *,
        legacy_stem_index: dict[str, str] | None,
    ):
        if lease_name_arg != lease_name:
            return None
        return delegate._read_state_json(delegate._state_path(stale_task_id))

    original_write = delegate._write_runtime_tmp_task_id_marker

    def backfill_after_concurrent_marker(
        lease_root: Path,
        task_id: str,
        *,
        no_clobber: bool = False,
    ) -> None:
        if no_clobber:
            original_write(lease_root, fresh_task_id)
        original_write(lease_root, task_id, no_clobber=no_clobber)

    monkeypatch.setattr(delegate, "_runtime_tmp_state_for_lease", legacy_only_for_stale)
    monkeypatch.setattr(delegate, "_write_runtime_tmp_task_id_marker", backfill_after_concurrent_marker)

    result = delegate._sweep_runtime_tmp_orphans()

    assert result["leases_reaped"] == 0
    assert delegate._read_runtime_tmp_task_id_marker(lease) == fresh_task_id
