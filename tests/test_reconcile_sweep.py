"""Tests for scripts.orchestration.reconcile_sweep."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from scripts.guardrails.delegate_ownership import OwnershipLedger
from scripts.orchestration import reconcile_sweep


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


def test_reconcile_sweep_apply_settles_dead_record(tmp_path: Path) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    dead_task_id = "dead-task-2"
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
        apply=True,
        task_dir=task_dir,
        ledger=ledger,
    )

    assert report.mode == "apply"
    assert report.scanned_tasks == 1
    assert report.zombie_tasks == [dead_task_id]

    # File on disk must be marked crashed by the lazy heal path
    healed = json.loads(task_file.read_text(encoding="utf-8"))
    assert healed["status"] == "crashed"
    assert "marked crashed by status probe" in healed.get("stderr_excerpt", "")
    assert (
        "reconcile-sweep: mode=apply scanned_tasks=1 zombies_crashed=1 stale_claims_released=0" in report.summary_line()
    )


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


def test_reconcile_sweep_cli_main(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    dead_task_id = "cli-dead-task"
    (task_dir / f"{dead_task_id}.json").write_text(
        json.dumps(
            {
                "task_id": dead_task_id,
                "status": "running",
                "pid": 999_999_999,
            }
        ),
        encoding="utf-8",
    )

    # Dry-run CLI
    rc = reconcile_sweep.main(
        [
            "--task-dir",
            str(task_dir),
            "--repo-root",
            str(tmp_path),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "reconcile-sweep: mode=dry_run scanned_tasks=1 zombie_tasks=1 stale_claims=0" in out

    # Verify task file is still running
    state = json.loads((task_dir / f"{dead_task_id}.json").read_text(encoding="utf-8"))
    assert state["status"] == "running"

    # Apply CLI with --json
    rc_apply = reconcile_sweep.main(
        [
            "--apply",
            "--task-dir",
            str(task_dir),
            "--repo-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert rc_apply == 0
    out_apply = capsys.readouterr().out
    assert "reconcile-sweep: mode=apply scanned_tasks=1 zombies_crashed=1 stale_claims_released=0" in out_apply
    payload = json.loads("\n".join(out_apply.splitlines()[1:]))
    assert payload["mode"] == "apply"
    assert payload["zombie_tasks"] == [dead_task_id]

    # Verify task file is now crashed
    state_after = json.loads((task_dir / f"{dead_task_id}.json").read_text(encoding="utf-8"))
    assert state_after["status"] == "crashed"


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

    # 2. Apply mode — should heal only valid dead PID zombie and not crash on unparseable records
    report_apply = reconcile_sweep.run_reconcile_sweep(
        apply=True,
        task_dir=task_dir,
        ledger=ledger,
    )

    assert report_apply.scanned_tasks == 9
    assert report_apply.zombie_tasks == ["task_valid_zombie"]
    assert report_apply.live_tasks == ["task_valid_live"]
    assert len(report_apply.unparseable_tasks) == 7

    # Zombie task healed to crashed
    zombie_state = json.loads((task_dir / "task_valid_zombie.json").read_text(encoding="utf-8"))
    assert zombie_state["status"] == "crashed"

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


def test_reconcile_sweep_systemd_exec_start_smoke(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    service_file = repo_root / "packaging" / "systemd" / "learn-ukrainian-reconcile.service"
    assert service_file.exists()
    content = service_file.read_text(encoding="utf-8")

    # 1. Verify exact ExecStart shape in systemd unit
    exec_line = next(line for line in content.splitlines() if line.startswith("ExecStart="))
    assert exec_line == "ExecStart=@REPO_ROOT@/.venv/bin/python -m scripts.orchestration.reconcile_sweep"

    # Derive module args from the unit command shape
    cmd_template = exec_line.removeprefix("ExecStart=").strip()
    module_args = cmd_template.replace("@REPO_ROOT@/.venv/bin/python", "").strip().split()

    # 2. Smoke test: module invocation with --help
    res_help = subprocess.run(
        [sys.executable, *module_args, "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_help.returncode == 0
    assert "Reconcile stale write-ownership claims" in res_help.stdout

    # 3. Smoke test: module invocation in default report mode
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    res_report = subprocess.run(
        [
            sys.executable,
            *module_args,
            "--repo-root",
            str(tmp_path),
            "--task-dir",
            str(task_dir),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_report.returncode == 0
    assert "reconcile-sweep: mode=dry_run scanned_tasks=0 zombie_tasks=0 stale_claims=0" in res_report.stdout

    # 4. Smoke test: direct script path execution with --help and report mode
    script_path = str(repo_root / "scripts" / "orchestration" / "reconcile_sweep.py")
    res_script_help = subprocess.run(
        [sys.executable, script_path, "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_script_help.returncode == 0
    assert "Reconcile stale write-ownership claims" in res_script_help.stdout

    res_script_report = subprocess.run(
        [
            sys.executable,
            script_path,
            "--repo-root",
            str(tmp_path),
            "--task-dir",
            str(task_dir),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_script_report.returncode == 0
    assert "reconcile-sweep: mode=dry_run scanned_tasks=0 zombie_tasks=0 stale_claims=0" in res_script_report.stdout
