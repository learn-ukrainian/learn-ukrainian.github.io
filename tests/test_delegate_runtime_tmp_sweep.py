"""Regression tests for runtime-tmp orphan sweep performance (#7203)."""

from __future__ import annotations

import argparse
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

SYNTHETIC_TASK_RECORD_COUNT = 500
MARKED_LEASE_DIR_COUNT = 25
LEGACY_LEASE_DIR_COUNT = 3


@pytest.fixture
def tmp_tasks_dir(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setattr(delegate, "_TASKS_DIR", tasks_dir)
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


def _count_task_record_reads(monkeypatch) -> dict[str, int]:
    counts = {"read_state_json": 0}
    original_read_state_json = delegate._read_state_json

    def counting_read_state_json(path: Path):
        if path.parent == delegate._TASKS_DIR and path.suffix == ".json":
            counts["read_state_json"] += 1
        return original_read_state_json(path)

    monkeypatch.setattr(delegate, "_read_state_json", counting_read_state_json)
    return counts


def _old_runtime_tmp_state_for_lease(lease_name: str) -> dict | None:
    """Pre-#7203 behaviour: scan every task record for each lease."""
    try:
        state_files = tuple(delegate._TASKS_DIR.glob("*.json")) if delegate._TASKS_DIR.is_dir() else ()
    except OSError:
        return None
    for state_path in state_files:
        if state_path.name.endswith(".tmp") or ".tmp." in state_path.name:
            continue
        state = delegate._read_state_json(state_path)
        task_id = state.get("task_id") if isinstance(state, dict) else None
        if isinstance(task_id, str) and delegate._runtime_tmp_lease_name(task_id) == lease_name:
            return state
    return None


def test_runtime_tmp_orphan_sweep_avoids_record_scan_for_marked_leases(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    _seed_sweep_fixture(
        tmp_path,
        tmp_tasks_dir,
        marked_lease_count=MARKED_LEASE_DIR_COUNT,
        legacy_lease_count=LEGACY_LEASE_DIR_COUNT,
        decoy_record_count=SYNTHETIC_TASK_RECORD_COUNT,
    )
    counts = _count_task_record_reads(monkeypatch)

    result = delegate._sweep_runtime_tmp_orphans()

    assert result["leases_reaped"] == MARKED_LEASE_DIR_COUNT + LEGACY_LEASE_DIR_COUNT
    assert counts["read_state_json"] == MARKED_LEASE_DIR_COUNT + LEGACY_LEASE_DIR_COUNT


def test_runtime_tmp_orphan_sweep_marker_lookup_mutation_check(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """Reverting half 1 would parse far more records than marker-based lookup."""
    _seed_sweep_fixture(
        tmp_path,
        tmp_tasks_dir,
        marked_lease_count=MARKED_LEASE_DIR_COUNT,
        legacy_lease_count=0,
        decoy_record_count=SYNTHETIC_TASK_RECORD_COUNT,
    )
    fixed_counts = _count_task_record_reads(monkeypatch)
    delegate._sweep_runtime_tmp_orphans()
    fixed_reads = fixed_counts["read_state_json"]

    _seed_sweep_fixture(
        tmp_path,
        tmp_tasks_dir,
        marked_lease_count=MARKED_LEASE_DIR_COUNT,
        legacy_lease_count=0,
        decoy_record_count=SYNTHETIC_TASK_RECORD_COUNT,
    )
    reverted_counts = _count_task_record_reads(monkeypatch)

    def legacy_lookup(lease_name: str, lease_root: Path, *, legacy_stem_index):
        return _old_runtime_tmp_state_for_lease(lease_name)

    monkeypatch.setattr(delegate, "_runtime_tmp_state_for_lease", legacy_lookup)
    delegate._sweep_runtime_tmp_orphans()
    reverted_reads = reverted_counts["read_state_json"]

    assert fixed_reads == MARKED_LEASE_DIR_COUNT
    assert reverted_reads > fixed_reads
    assert reverted_reads >= 5_000


def test_runtime_tmp_orphan_sweep_stem_index_mutation_check(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """Reverting the stem index would scan records for every legacy lease."""
    _seed_sweep_fixture(
        tmp_path,
        tmp_tasks_dir,
        marked_lease_count=0,
        legacy_lease_count=LEGACY_LEASE_DIR_COUNT,
        decoy_record_count=SYNTHETIC_TASK_RECORD_COUNT,
    )
    fixed_counts = _count_task_record_reads(monkeypatch)
    delegate._sweep_runtime_tmp_orphans()
    fixed_reads = fixed_counts["read_state_json"]

    _seed_sweep_fixture(
        tmp_path,
        tmp_tasks_dir,
        marked_lease_count=0,
        legacy_lease_count=LEGACY_LEASE_DIR_COUNT,
        decoy_record_count=SYNTHETIC_TASK_RECORD_COUNT,
    )
    reverted_counts = _count_task_record_reads(monkeypatch)
    monkeypatch.setattr(
        delegate,
        "_build_runtime_tmp_legacy_stem_index",
        lambda: {},
    )
    delegate._sweep_runtime_tmp_orphans()
    reverted_reads = reverted_counts["read_state_json"]

    assert fixed_reads == LEGACY_LEASE_DIR_COUNT
    assert reverted_reads > fixed_reads
    assert reverted_reads >= 500


def test_runtime_tmp_orphan_sweep_marker_backfill_second_sweep(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """After one sweep, marker backfill makes the next sweep O(1) without legacy fallback."""
    namespace = _seed_sweep_fixture(
        tmp_path,
        tmp_tasks_dir,
        marked_lease_count=0,
        legacy_lease_count=LEGACY_LEASE_DIR_COUNT,
        decoy_record_count=SYNTHETIC_TASK_RECORD_COUNT,
        legacy_status="running",
    )
    delegate._sweep_runtime_tmp_orphans()

    for index in range(LEGACY_LEASE_DIR_COUNT):
        task_id = f"legacy-task-{index:04d}"
        lease = namespace / delegate._runtime_tmp_lease_name(task_id)
        assert lease.is_dir()
        assert delegate._read_runtime_tmp_task_id_marker(lease) == task_id

    def forbid_legacy_paths(*_args, **_kwargs):
        raise AssertionError("legacy resolution should not run after marker backfill")

    monkeypatch.setattr(
        delegate,
        "_build_runtime_tmp_legacy_stem_index",
        forbid_legacy_paths,
    )
    monkeypatch.setattr(
        delegate,
        "_read_runtime_tmp_state_for_legacy_lease",
        forbid_legacy_paths,
    )

    second_counts = _count_task_record_reads(monkeypatch)
    delegate._sweep_runtime_tmp_orphans()
    assert second_counts["read_state_json"] == LEGACY_LEASE_DIR_COUNT


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
    assert sum(path.stat().st_size for path in snapshot_dir.glob("*.json")) > record_bytes
    assert record_bytes < delegate._READ_ONLY_CHECKOUT_RECORD_BYTE_BUDGET
    state = delegate._read_state(state_path)
    assert state is not None
    assert isinstance(state.get("read_only_checkout_pre"), dict)
    assert isinstance(state.get("read_only_checkout_post"), dict)
    assert "read_only_checkout_pre" not in json.loads(state_path.read_text(encoding="utf-8"))


def test_read_only_dispatch_inline_snapshot_mutation_check(tmp_tasks_dir):
    """Reverting half 2 would embed whole-checkout snapshots in the task record."""
    task_id = "read-only-inline-bloat"
    state_path = delegate._state_path(task_id)
    huge_snapshot = {f"path-{index}.txt": " M" for index in range(400_000)}
    delegate._write_state_atomic(
        state_path,
        {
            "task_id": task_id,
            "status": "done",
            "read_only_checkout_pre": huge_snapshot,
            "read_only_checkout_post": huge_snapshot,
        },
    )
    assert state_path.stat().st_size >= delegate._READ_ONLY_CHECKOUT_RECORD_BYTE_BUDGET


def _seed_legacy_running_lease(
    tmp_path: Path,
    tasks_dir: Path,
    *,
    task_id: str = "legacy-running-task",
) -> Path:
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
        cwd=None,
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


def test_runtime_tmp_orphan_sweep_backfill_best_effort_mutation_check(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """Reverting the OSError guard around backfill must raise during sweep."""
    lease = _seed_legacy_running_lease(tmp_path, tmp_tasks_dir)

    def fail_backfill_write(lease_root: Path, task_id: str, *, no_clobber: bool = False) -> None:
        if no_clobber:
            raise FileNotFoundError(lease_root)

    monkeypatch.setattr(delegate, "_write_runtime_tmp_task_id_marker", fail_backfill_write)

    result = delegate._sweep_runtime_tmp_orphans()
    assert result["errors"] == 0

    with pytest.raises(FileNotFoundError):
        delegate._write_runtime_tmp_task_id_marker(
            lease,
            "legacy-running-task",
            no_clobber=True,
        )


def test_runtime_tmp_orphan_sweep_marker_backfill_no_clobber_mutation_check(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """Reverting no-clobber must let a stale backfill clobber a live marker."""
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
    delegate._write_state_atomic(
        delegate._state_path(fresh_task_id),
        {"task_id": fresh_task_id, "status": "running", "pid": None},
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

    def clobbering_backfill(
        lease_root: Path,
        task_id: str,
        *,
        no_clobber: bool = False,
    ) -> None:
        if no_clobber:
            original_write(lease_root, fresh_task_id)
            marker = delegate._runtime_tmp_task_id_marker_path(lease_root)
            tmp = marker.with_suffix(f".tmp.{os.getpid()}")
            tmp.write_text(task_id, encoding="utf-8")
            os.replace(tmp, marker)
            return
        original_write(lease_root, task_id, no_clobber=no_clobber)

    monkeypatch.setattr(delegate, "_runtime_tmp_state_for_lease", legacy_only_for_stale)
    monkeypatch.setattr(delegate, "_write_runtime_tmp_task_id_marker", clobbering_backfill)

    delegate._sweep_runtime_tmp_orphans()
    assert delegate._read_runtime_tmp_task_id_marker(lease) == stale_task_id

    delegate._write_state_atomic(
        delegate._state_path(stale_task_id),
        {"task_id": stale_task_id, "status": "done", "pid": None},
    )
    second_result = delegate._sweep_runtime_tmp_orphans()
    assert second_result["leases_reaped"] == 1
    assert not lease.exists()
