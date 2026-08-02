"""Tests for scripts.orchestration.dispatch_settle."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts.guardrails.delegate_ownership import OwnershipLedger
from scripts.orchestration import dispatch_settle as ds


def test_pid_alive_self() -> None:
    assert ds._pid_alive(os.getpid()) is True
    assert ds._pid_alive(0) is False
    assert ds._pid_alive(None) is False


def test_heal_zombie_task_marks_failed_and_releases(tmp_path: Path) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    task_id = "example-task"
    state = {
        "task_id": task_id,
        "status": "running",
        "pid": 999_999_999,
        "worktree_path": str(tmp_path / "wt"),
        "worktree_branch": "codex/example-task",
    }
    (task_dir / f"{task_id}.json").write_text(json.dumps(state), encoding="utf-8")

    ledger_path = tmp_path / "own.sqlite3"
    ledger = OwnershipLedger(ledger_path, task_state_dir=task_dir)
    # seed a claim for the dead task
    import sqlite3
    import time

    conn = sqlite3.connect(ledger_path)
    conn.execute(
        "CREATE TABLE write_claims (task_id TEXT, claim_json TEXT, pid INTEGER, created_at REAL, PRIMARY KEY (task_id, claim_json))"
    )
    conn.execute(
        "INSERT INTO write_claims VALUES (?,?,?,?)",
        (task_id, '{"kind":"file","norm":"scripts/x.py"}', 999_999_999, time.time() - 10_000),
    )
    conn.commit()
    conn.close()

    actions = ds.heal_zombie_task(task_dir, task_id, ledger=ledger)
    assert "marked_failed_zombie_running" in actions
    assert "released_ownership_claims" in actions
    healed = json.loads((task_dir / f"{task_id}.json").read_text(encoding="utf-8"))
    assert healed["status"] == "failed"
    assert healed["exit_code"] == -9


def test_settle_task_reports_closeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    task_id = "t1"
    wt = tmp_path / "wt"
    wt.mkdir()
    (task_dir / f"{task_id}.json").write_text(
        json.dumps(
            {
                "task_id": task_id,
                "status": "done",
                "pid": os.getpid(),
                "worktree_path": str(wt),
                "worktree_branch": "codex/t1",
            }
        ),
        encoding="utf-8",
    )

    def fake_git_info(_worktree: Path) -> tuple[str | None, int | None, bool | None]:
        return "codex/t1", 2, False

    def fake_find_pr(branch: str | None, _cwd: Path) -> tuple[str | None, int | None]:
        assert branch == "codex/t1"
        return None, None

    monkeypatch.setattr(ds, "_git_info", fake_git_info)
    monkeypatch.setattr(ds, "_find_pr", fake_find_pr)
    monkeypatch.setattr(ds, "release_inactive_claims", lambda ledger=None: [])

    report = ds.settle_task(
        task_id,
        repo_root=tmp_path,
        task_dir=task_dir,
        push=False,
        release_stale=False,
    )
    assert report.commits_ahead == 2
    assert report.pr_url is None
    assert report.closeout["blocker"] == "commits_without_pr"
    assert report.closeout["branch"] == "codex/t1"
