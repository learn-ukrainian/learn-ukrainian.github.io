"""Tests for scripts.orchestration.reconcile_sweep."""

from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

import pytest

from scripts.guardrails.delegate_ownership import OwnershipLedger
from scripts.orchestration import dead_worker_state, reconcile_sweep


@pytest.fixture(autouse=True)
def _synthetic_host_pid_view(monkeypatch):
    """Legacy-record cases explicitly model a host reader, even in a sandbox."""
    monkeypatch.setattr(
        dead_worker_state, "_pid_namespace", lambda process="self": dead_worker_state.INITIAL_PID_NAMESPACE
    )
    monkeypatch.setattr(dead_worker_state, "_proc_pid_namespace", lambda: dead_worker_state.INITIAL_PID_NAMESPACE)


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize("identity_case", ["foreign", "alive", "reused", "dead", "unreadable"])
def test_reconcile_sweep_uses_worker_identity(tmp_path, monkeypatch, apply, identity_case):
    pid = 999_999_999
    identity = {
        "pid": pid,
        "host_pid": pid,
        "start_time": 100,
        "pid_namespace": dead_worker_state.INITIAL_PID_NAMESPACE,
        "recorder_pid_namespace": dead_worker_state.INITIAL_PID_NAMESPACE,
    }
    if identity_case == "foreign":
        identity["pid_namespace"] = "pid:[999999]"
    elif identity_case == "unreadable":
        pid = os.getpid()
        identity["pid"] = pid
        identity["host_pid"] = pid
        identity["start_time"] = None
    elif identity_case in ("alive", "reused"):
        original_stat = dead_worker_state._process_stat

        def stat(process):
            if process == str(pid):
                return pid, 100 if identity_case == "alive" else 101
            return original_stat(process)

        monkeypatch.setattr(dead_worker_state, "_process_stat", stat)
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    path = task_dir / "identity-worker.json"
    state = {"task_id": "identity-worker", "status": "running", "pid": pid, "worker_identity": identity}
    path.write_text(json.dumps(state))
    before = path.read_bytes()
    ledger = OwnershipLedger(tmp_path / "claims.sqlite3", task_state_dir=task_dir)

    report = reconcile_sweep.run_reconcile_sweep(apply=apply, task_dir=task_dir, ledger=ledger)
    dead = identity_case in ("dead", "reused")
    assert report.zombie_tasks == (["identity-worker"] if dead else [])
    assert report.live_tasks == ([] if dead else ["identity-worker"])
    assert report.unparseable_tasks == []
    assert path.read_bytes() == before


def test_reconcile_sweep_dry_run_default(tmp_path: Path) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    dead_task_id = "dead-task-1"
    state = {
        "task_id": dead_task_id,
        "status": "running",
        "pid": 999_999_999,
    }
    task_file = task_dir / f"{dead_task_id}.json"
    task_file.write_text(json.dumps(state), encoding="utf-8")

    ledger_path = tmp_path / "own.sqlite3"
    ledger = OwnershipLedger(ledger_path, task_state_dir=task_dir)

    report = reconcile_sweep.run_reconcile_sweep(
        apply=False,
        task_dir=task_dir,
        ledger=ledger,
    )

    assert report.mode == "dry_run"
    assert report.scanned_tasks == 1
    assert report.zombie_tasks == [dead_task_id]
    assert report.stale_claims == []
    assert report.live_tasks == []

    # File on disk must NOT be modified in dry-run
    unchanged = json.loads(task_file.read_text(encoding="utf-8"))
    assert unchanged["status"] == "running"
    assert "reconcile-sweep: mode=dry_run scanned_tasks=1 zombie_tasks=1 stale_claims=0" in report.summary_line()


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize(
    "identity",
    ["absent_pid", "pid_reuse", "alive", "unpublished", "null_start", "null_dead", "empty_start", "empty_dead", "unreadable", "eperm", "zombie"],
)
def test_reconcile_sweep_requires_proven_death_before_crashing_v2(tmp_path: Path, monkeypatch, apply, identity) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    dead_task_id = "dead-task-2"
    state = _v2_record(dead_task_id, 999_999_999, tmp_path / "missing-worktree")
    if identity == "unpublished":
        state.update(pid=None, process_start=None, status="spawning")
    elif identity in ("null_start", "null_dead"):
        state["process_start"] = None
    elif identity in ("empty_start", "empty_dead"):
        state["process_start"] = ""
    readable = identity in ("pid_reuse", "alive", "null_start", "empty_start")
    actual = "exited-process" if identity == "alive" else "live-process"
    monkeypatch.setattr(reconcile_sweep.worker, "_identity", lambda pid: actual if readable else None)
    monkeypatch.setattr(dead_worker_state, "process_is_zombie", lambda pid: identity == "zombie")

    def probe(pid, sig):
        assert (pid, sig) == (999_999_999, 0)
        if identity in ("absent_pid", "null_dead", "empty_dead"):
            raise ProcessLookupError
        if identity == "eperm":
            raise PermissionError

    monkeypatch.setattr(reconcile_sweep.os, "kill", probe)
    dead = identity in ("absent_pid", "pid_reuse", "zombie", "null_dead", "empty_dead")
    live = identity in ("alive", "null_start")
    unknown = not dead and not live
    task_file = task_dir / f"{dead_task_id}.json"
    task_file.write_text(json.dumps(state), encoding="utf-8")
    before = task_file.read_bytes()

    ledger_path = tmp_path / "own.sqlite3"
    ledger = OwnershipLedger(ledger_path, task_state_dir=task_dir)

    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "other-store"))
    report = reconcile_sweep.run_reconcile_sweep(
        apply=apply,
        task_dir=task_dir,
        ledger=ledger,
    )

    assert report.mode == ("apply" if apply else "dry_run")
    assert report.scanned_tasks == 1
    assert report.zombie_tasks == ([dead_task_id] if dead else [])
    assert report.live_tasks == ([dead_task_id] if live else [])
    assert report.unknown_tasks == ([dead_task_id] if unknown else [])
    assert report.to_dict()["unknown_tasks"] == ([dead_task_id] if unknown else [])
    assert report.unparseable_tasks == []

    observed = json.loads(task_file.read_text(encoding="utf-8"))
    assert observed["status"] == ("crashed" if apply and dead else state["status"])
    if apply and dead:
        assert observed["error"] == "supervisor exited without a result"
        assert observed["finished_at"]
    else:
        assert observed == state
        assert task_file.read_bytes() == before
    if unknown:
        assert "unknown_tasks=1" in report.summary_line()
    assert os.environ["LU_TASKS_DIR"] == str(tmp_path / "other-store")
    assert f"zombie_tasks={int(dead)}" in report.summary_line()


def test_reconcile_sweep_does_not_touch_live_pid(tmp_path: Path) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    live_task_id = "live-task-1"
    my_pid = os.getpid()
    state = {
        "task_id": live_task_id,
        "status": "running",
        "pid": my_pid,
    }
    task_file = task_dir / f"{live_task_id}.json"
    task_file.write_text(json.dumps(state), encoding="utf-8")

    ledger_path = tmp_path / "own.sqlite3"
    ledger = OwnershipLedger(ledger_path, task_state_dir=task_dir)

    report = reconcile_sweep.run_reconcile_sweep(
        apply=True,
        task_dir=task_dir,
        ledger=ledger,
    )

    assert report.live_tasks == [live_task_id]
    assert report.zombie_tasks == []

    # File on disk must remain running
    unchanged = json.loads(task_file.read_text(encoding="utf-8"))
    assert unchanged["status"] == "running"


def test_reconcile_sweep_does_not_touch_other_terminal_or_worktree_statuses(
    tmp_path: Path,
) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()

    statuses = ["done", "needs_finalize", "failed", "crashed", "timeout"]
    for idx, status in enumerate(statuses):
        task_id = f"task-{status}-{idx}"
        state = {
            "task_id": task_id,
            "status": status,
            "pid": 999_999_999,
            "worktree_path": str(tmp_path / f"wt-{idx}"),
        }
        (task_dir / f"{task_id}.json").write_text(json.dumps(state), encoding="utf-8")

    ledger_path = tmp_path / "own.sqlite3"
    ledger = OwnershipLedger(ledger_path, task_state_dir=task_dir)

    report = reconcile_sweep.run_reconcile_sweep(
        apply=True,
        task_dir=task_dir,
        ledger=ledger,
    )

    assert report.scanned_tasks == len(statuses)
    assert report.zombie_tasks == []
    assert report.live_tasks == []

    for idx, status in enumerate(statuses):
        task_id = f"task-{status}-{idx}"
        current = json.loads((task_dir / f"{task_id}.json").read_text(encoding="utf-8"))
        assert current["status"] == status


def test_reconcile_sweep_stale_claims(tmp_path: Path) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    dead_task_id = "stale-claim-task"
    state = {
        "task_id": dead_task_id,
        "status": "failed",
        "pid": 999_999_999,
    }
    (task_dir / f"{dead_task_id}.json").write_text(json.dumps(state), encoding="utf-8")

    ledger_path = tmp_path / "own.sqlite3"
    ledger = OwnershipLedger(ledger_path, task_state_dir=task_dir)

    # Seed write claim in ledger
    conn = sqlite3.connect(ledger_path)
    conn.execute(
        "CREATE TABLE write_claims (task_id TEXT, claim_json TEXT, pid INTEGER, created_at REAL, PRIMARY KEY (task_id, claim_json))"
    )
    conn.execute(
        "INSERT INTO write_claims VALUES (?,?,?,?)",
        (
            dead_task_id,
            '{"kind":"file","norm":"scripts/foo.py"}',
            999_999_999,
            time.time() - 10_000,
        ),
    )
    conn.commit()
    conn.close()

    # Dry-run check: claims reported but not deleted
    report_dry = reconcile_sweep.run_reconcile_sweep(
        apply=False,
        task_dir=task_dir,
        ledger=ledger,
    )
    assert report_dry.stale_claims == [dead_task_id]

    conn = sqlite3.connect(ledger_path)
    count = conn.execute("SELECT COUNT(*) FROM write_claims").fetchone()[0]
    conn.close()
    assert count == 1

    # Apply check: claims released
    report_apply = reconcile_sweep.run_reconcile_sweep(
        apply=True,
        task_dir=task_dir,
        ledger=ledger,
    )
    assert report_apply.stale_claims == [dead_task_id]

    conn = sqlite3.connect(ledger_path)
    count_after = conn.execute("SELECT COUNT(*) FROM write_claims").fetchone()[0]
    conn.close()
    assert count_after == 0


def test_reconcile_sweep_filesystem_immutability_in_report_mode(tmp_path: Path) -> None:
    import hashlib
    import stat

    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    ledger_path = tmp_path / "write-ownership.sqlite3"

    # Seed ledger with a table and claim
    conn = sqlite3.connect(ledger_path)
    conn.execute(
        "CREATE TABLE write_claims (task_id TEXT, claim_json TEXT, pid INTEGER, created_at REAL, PRIMARY KEY (task_id, claim_json))"
    )
    conn.execute(
        "INSERT INTO write_claims VALUES (?,?,?,?)",
        ("test-task", '{"kind":"file","norm":"foo.py"}', 999_999_999, time.time() - 5000),
    )
    conn.commit()
    conn.close()

    # Remove any WAL/SHM artifacts from setup
    for p in tmp_path.glob("write-ownership.sqlite3-*"):
        p.unlink()

    initial_files = set(tmp_path.iterdir())
    initial_bytes = ledger_path.read_bytes()
    initial_sha = hashlib.sha256(initial_bytes).hexdigest()

    ledger = OwnershipLedger(ledger_path, task_state_dir=task_dir)

    # 1. Report mode sweep
    report = reconcile_sweep.run_reconcile_sweep(
        apply=False,
        task_dir=task_dir,
        ledger=ledger,
    )
    assert report.stale_claims == ["test-task"]

    # Assert no sidecars created and DB file byte-identical
    current_files = set(tmp_path.iterdir())
    assert current_files == initial_files
    assert not (tmp_path / "write-ownership.sqlite3-wal").exists()
    assert not (tmp_path / "write-ownership.sqlite3-shm").exists()
    assert hashlib.sha256(ledger_path.read_bytes()).hexdigest() == initial_sha

    # 2. Missing ledger file in report mode must NOT create a file
    missing_ledger_path = tmp_path / "nonexistent" / "missing.sqlite3"
    missing_ledger = OwnershipLedger(missing_ledger_path, task_state_dir=task_dir)
    report_missing = reconcile_sweep.run_reconcile_sweep(
        apply=False,
        task_dir=task_dir,
        ledger=missing_ledger,
    )
    assert report_missing.stale_claims == []
    assert not missing_ledger_path.exists()

    # 3. Read-only DB file permissions (chmod 0444)
    ledger_path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    try:
        report_ro = reconcile_sweep.run_reconcile_sweep(
            apply=False,
            task_dir=task_dir,
            ledger=ledger,
        )
        assert report_ro.stale_claims == ["test-task"]
        assert not (tmp_path / "write-ownership.sqlite3-wal").exists()
        assert not (tmp_path / "write-ownership.sqlite3-shm").exists()
    finally:
        ledger_path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def test_reconcile_sweep_malformed_pid_handled_per_record(tmp_path: Path) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()

    # Setup variety of malformed and valid task records
    records: dict[str, Any] = {
        "task_str_pid": {"task_id": "task_str_pid", "status": "running", "pid": "bad-pid-not-number"},
        "task_bool_pid": {"task_id": "task_bool_pid", "status": "running", "pid": True},
        "task_neg_pid": {"task_id": "task_neg_pid", "status": "running", "pid": -42},
        "task_zero_pid": {"task_id": "task_zero_pid", "status": "running", "pid": 0},
        "task_none_pid": {"task_id": "task_none_pid", "status": "running", "pid": None},
        "task_dict_pid": {"task_id": "task_dict_pid", "status": "running", "pid": {"pid": 123}},
        "task_valid_zombie": {"task_id": "task_valid_zombie", "status": "running", "pid": 999_999_999},
        "task_valid_live": {"task_id": "task_valid_live", "status": "running", "pid": os.getpid()},
    }

    for name, content in records.items():
        (task_dir / f"{name}.json").write_text(json.dumps(content), encoding="utf-8")

    # Add a completely corrupt JSON file
    (task_dir / "task_corrupt.json").write_text("{invalid json content:", encoding="utf-8")

    ledger_path = tmp_path / "own.sqlite3"
    ledger = OwnershipLedger(ledger_path, task_state_dir=task_dir)

    # 1. Dry run
    report_dry = reconcile_sweep.run_reconcile_sweep(
        apply=False,
        task_dir=task_dir,
        ledger=ledger,
    )

    assert report_dry.scanned_tasks == 9
    assert report_dry.zombie_tasks == ["task_valid_zombie"]
    assert report_dry.live_tasks == ["task_valid_live"]
    assert sorted(report_dry.unparseable_tasks) == sorted(
        [
            "task_str_pid",
            "task_bool_pid",
            "task_neg_pid",
            "task_zero_pid",
            "task_none_pid",
            "task_dict_pid",
            "task_corrupt",
        ]
    )
    assert "unparseable_tasks=7" in report_dry.summary_line()

    # Apply reports legacy zombies without rewriting their state.
    report_apply = reconcile_sweep.run_reconcile_sweep(
        apply=True,
        task_dir=task_dir,
        ledger=ledger,
    )

    assert report_apply.scanned_tasks == 9
    assert report_apply.zombie_tasks == ["task_valid_zombie"]
    assert report_apply.live_tasks == ["task_valid_live"]
    assert len(report_apply.unparseable_tasks) == 7

    # Legacy zombie stays read-only.
    zombie_state = json.loads((task_dir / "task_valid_zombie.json").read_text(encoding="utf-8"))
    assert zombie_state["status"] == "running"

    # Live task still running
    live_state = json.loads((task_dir / "task_valid_live.json").read_text(encoding="utf-8"))
    assert live_state["status"] == "running"

    # Unparseable string PID task still untouched running
    str_pid_state = json.loads((task_dir / "task_str_pid.json").read_text(encoding="utf-8"))
    assert str_pid_state["status"] == "running"


def test_reconcile_sweep_cli_help_standard() -> None:
    import argparse

    parser = reconcile_sweep.build_parser()
    assert issubclass(parser.formatter_class, argparse.RawDescriptionHelpFormatter)
    assert parser.description and len(parser.description.strip().splitlines()) >= 2
    assert parser.epilog is not None
    assert "Examples:" in parser.epilog
    assert "Outputs:" in parser.epilog
    assert "Exit codes:" in parser.epilog
    assert "Related:" in parser.epilog

    help_text = parser.format_help()
    assert "reconcile_sweep.py" in help_text
    assert "--apply" in help_text
    assert "--repo-root" in help_text
    assert "--task-dir" in help_text
    assert "--json" in help_text


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize("kind", ["worktree_prep", "admission_hold"])
def test_reconcile_sweep_keeps_prep_record_without_rewriting_legacy_state(tmp_path, apply, kind):
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    state = {"task_id": "legacy-prep", "status": "spawning", "pid": None, kind: {}}
    path = task_dir / "legacy-prep.json"
    path.write_text(json.dumps(state))
    before = path.read_bytes()
    reconcile_sweep.run_reconcile_sweep(
        apply=apply,
        task_dir=task_dir,
        ledger=OwnershipLedger(tmp_path / "own.sqlite3", task_state_dir=task_dir),
    )
    assert path.read_bytes() == before


def _v2_record(task_id, pid, worktree):
    return dict(
        schema_version=2,
        task_id=task_id,
        run_nonce="test-nonce",
        status="running",
        pid=pid,
        process_start="exited-process",
        started_at="2026-10-26T00:00:00+00:00",
        agent="codex",
        model="test-model",
        effort=None,
        mode="read-only",
        worktree_path=str(worktree),
        prompt_file=str(worktree / "prompt"),
        result_file=str(worktree / "result"),
        claude_account=None,
        provider=None,
        worktree_base_sha="HEAD",
        worktree_branch="test-branch",
    )


@pytest.mark.parametrize("prior", [None, "1"])
def test_reconcile_sweep_runs_git_children_without_optional_locks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prior: str | None
) -> None:
    """#8874: settle and dispatcher observation must not take index.lock.

    An explicit operator value wins and is left as it was.
    """
    if prior is None:
        monkeypatch.delenv("GIT_OPTIONAL_LOCKS", raising=False)
    else:
        monkeypatch.setenv("GIT_OPTIONAL_LOCKS", prior)
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    (task_dir / "dead-task-locks.json").write_text(
        json.dumps(_v2_record("dead-task-locks", 999_999_999, tmp_path)),
        encoding="utf-8",
    )
    seen: dict[str, str | None] = {}

    def _release(_ledger: object) -> list[str]:
        seen["settle"] = os.environ.get("GIT_OPTIONAL_LOCKS")
        return []

    def _observe(state: dict) -> dict:
        seen["observe"] = os.environ.get("GIT_OPTIONAL_LOCKS")
        return state

    monkeypatch.setattr(reconcile_sweep.dispatch_settle, "release_inactive_claims", _release)
    monkeypatch.setattr(reconcile_sweep.worker, "_observe", _observe)
    report = reconcile_sweep.run_reconcile_sweep(
        apply=True,
        task_dir=task_dir,
        ledger=OwnershipLedger(tmp_path / "own.sqlite3", task_state_dir=task_dir),
    )

    assert report.zombie_tasks == ["dead-task-locks"]
    expected = prior or "0"
    assert seen == {"settle": expected, "observe": expected}
    assert os.environ.get("GIT_OPTIONAL_LOCKS") == prior
