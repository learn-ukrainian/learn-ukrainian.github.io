"""Regression tests for runtime-tmp orphan sweep performance (#7203)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

import scripts.delegate as delegate
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
