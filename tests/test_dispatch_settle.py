"""Tests for scripts.orchestration.dispatch_settle."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts.fleet import idle_settle
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


def test_attach_idle_reminder_requires_disposition_when_eligible(tmp_path: Path) -> None:
    report = ds.SettleReport(
        task_id="infra-6976",
        status="done",
        pid=None,
        pid_alive=False,
        worktree_path=None,
        branch=None,
        commits_ahead=0,
        dirty=False,
        pr_url=None,
        pr_number=None,
        actions=[],
        closeout={},
    )
    snapshot = idle_settle.parse_snapshot(
        {
            "lanes": [{"lane": "cursor", "status": "cool", "in_flight": 0, "will_last": True}],
            "items": [{"item_id": "issue:6976", "ready": True, "valuable": True, "independent": True}],
            "caps": {},
        }
    )
    store = tmp_path / "idle.jsonl"
    rc, decision, event = ds.attach_idle_reminder(report, snapshot=snapshot, store=store)
    assert rc == 0
    assert decision.outcome == "missing_action"
    assert decision.reminder_fired is True
    assert event is not None
    assert event["outcome"] == "missing_action"


def test_attach_idle_reminder_rejects_unknown_disposition() -> None:
    report = ds.SettleReport(
        task_id="review-6981",
        status="done",
        pid=None,
        pid_alive=False,
        worktree_path=None,
        branch=None,
        commits_ahead=0,
        dirty=False,
        pr_url=None,
        pr_number=None,
        actions=[],
        closeout={},
    )
    snapshot = idle_settle.parse_snapshot(
        {
            "lanes": [{"lane": "cursor", "status": "cool", "in_flight": 0, "will_last": True}],
            "items": [{"item_id": "issue:6976"}],
        }
    )
    rc, decision, event = ds.attach_idle_reminder(
        report,
        snapshot=snapshot,
        disposition="later",
        record=False,
    )
    assert rc == 2
    assert decision.settle_kind == "review"
    assert decision.outcome == "invalid_disposition"
    assert event is None


def test_cmd_task_prints_reminder_and_accepts_disposition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    canned = ds.SettleReport(
        task_id="t-idle",
        status="done",
        pid=None,
        pid_alive=False,
        worktree_path=None,
        branch="codex/t-idle",
        commits_ahead=0,
        dirty=False,
        pr_url=None,
        pr_number=None,
        actions=[],
        closeout={"branch": "codex/t-idle", "pr": "NONE", "blocker": "none"},
    )
    monkeypatch.setattr(ds, "settle_task", lambda *_args, **_kwargs: canned)

    snap = tmp_path / "snap.json"
    snap.write_text(
        json.dumps(
            {
                "lanes": [{"lane": "cursor", "status": "cool", "in_flight": 0, "will_last": True}],
                "items": [{"item_id": "issue:6976"}],
            }
        ),
        encoding="utf-8",
    )
    store = tmp_path / "idle.jsonl"
    rc = ds.main(
        [
            "task",
            "--task-id",
            "t-idle",
            "--no-release-stale",
            "--idle-snapshot-json",
            str(snap),
            "--idle-store",
            str(store),
            "--disposition",
            "human_decision",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "SETTLE REMINDER" in out
    assert "satisfied via disposed" in out
    assert "ACTION REQUIRED" not in out
    events = idle_settle.load_events(store)
    assert events[0]["outcome"] == "disposed"
    assert events[0]["disposition"] == "human_decision"


def test_cmd_task_silent_without_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    canned = ds.SettleReport(
        task_id="t-silent",
        status="done",
        pid=None,
        pid_alive=False,
        worktree_path=None,
        branch="codex/t-silent",
        commits_ahead=0,
        dirty=False,
        pr_url=None,
        pr_number=None,
        actions=[],
        closeout={"branch": "codex/t-silent", "pr": "NONE", "blocker": "none"},
    )
    monkeypatch.setattr(ds, "settle_task", lambda *_args, **_kwargs: canned)
    store = tmp_path / "idle.jsonl"
    rc = ds.main(
        [
            "task",
            "--task-id",
            "t-silent",
            "--no-release-stale",
            "--idle-store",
            str(store),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "SETTLE REMINDER" not in out
    assert not store.exists()


def _seed_claim(ledger_path: Path, task_id: str) -> None:
    import sqlite3
    import time

    conn = sqlite3.connect(ledger_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS write_claims (task_id TEXT, claim_json TEXT, pid INTEGER, created_at REAL, PRIMARY KEY (task_id, claim_json))"
    )
    conn.execute(
        "INSERT INTO write_claims VALUES (?,?,?,?)",
        (task_id, '{"kind":"file","norm":"scripts/x.py"}', 999_999_999, time.time() - 10_000),
    )
    conn.commit()
    conn.close()


def _claim_count(ledger_path: Path, task_id: str) -> int:
    import sqlite3

    conn = sqlite3.connect(ledger_path)
    try:
        row = conn.execute("SELECT COUNT(*) FROM write_claims WHERE task_id = ?", (task_id,)).fetchone()
    finally:
        conn.close()
    return int(row[0])


def test_settle_task_settles_missing_worktree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    task_id = "dead-wt"
    (task_dir / f"{task_id}.json").write_text(
        json.dumps(
            {
                "task_id": task_id,
                "status": "needs_finalize",
                "pid": 999_999_999,
                "worktree_path": str(tmp_path / "reaped-wt"),
                "worktree_branch": "atlas/dead-wt",
            }
        ),
        encoding="utf-8",
    )
    ledger_path = tmp_path / "own.sqlite3"
    _seed_claim(ledger_path, task_id)
    monkeypatch.setattr(ds, "default_ledger_path", lambda: ledger_path)

    report = ds.settle_task(
        task_id,
        repo_root=tmp_path,
        task_dir=task_dir,
        release_stale=False,
    )

    assert "marked_failed_missing_worktree" in report.actions
    assert "released_ownership_claims" in report.actions
    healed = json.loads((task_dir / f"{task_id}.json").read_text(encoding="utf-8"))
    assert healed["status"] == "failed"
    assert "worktree is missing" in healed["last_error"]
    assert _claim_count(ledger_path, task_id) == 0
    assert report.commits_ahead is None
    assert report.pr_url is None
    assert report.closeout["blocker"] == "none"


def test_settle_task_missing_worktree_live_pid_not_settled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    task_id = "live-wt"
    (task_dir / f"{task_id}.json").write_text(
        json.dumps(
            {
                "task_id": task_id,
                "status": "running",
                "pid": os.getpid(),
                "worktree_path": str(tmp_path / "reaped-wt"),
                "worktree_branch": "codex/live-wt",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(ds, "default_ledger_path", lambda: tmp_path / "own.sqlite3")

    seen_cwds: list[Path] = []

    def fake_find_pr(_branch: str | None, cwd: Path) -> tuple[str | None, int | None]:
        seen_cwds.append(cwd)
        return None, None

    monkeypatch.setattr(ds, "_find_pr", fake_find_pr)

    report = ds.settle_task(
        task_id,
        repo_root=tmp_path,
        task_dir=task_dir,
        release_stale=False,
    )

    assert "marked_failed_missing_worktree" not in report.actions
    assert report.status == "running"
    assert report.pid_alive is True
    # PR probing must not use the reaped worktree as cwd (crashes with Errno 2).
    assert seen_cwds and all(cwd == tmp_path for cwd in seen_cwds)
    state = json.loads((task_dir / f"{task_id}.json").read_text(encoding="utf-8"))
    assert state["status"] == "running"


def test_settle_task_worktree_present_path_unchanged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    task_id = "present-wt"
    wt = tmp_path / "wt"
    wt.mkdir()
    (task_dir / f"{task_id}.json").write_text(
        json.dumps(
            {
                "task_id": task_id,
                "status": "done",
                "pid": 999_999_999,
                "worktree_path": str(wt),
                "worktree_branch": "codex/present-wt",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(ds, "default_ledger_path", lambda: tmp_path / "own.sqlite3")

    probed: list[Path] = []

    def fake_git_info(worktree: Path) -> tuple[str | None, int | None, bool | None]:
        probed.append(worktree)
        return "codex/present-wt", 0, False

    monkeypatch.setattr(ds, "_git_info", fake_git_info)
    monkeypatch.setattr(ds, "_find_pr", lambda _b, _c: (None, None))

    report = ds.settle_task(
        task_id,
        repo_root=tmp_path,
        task_dir=task_dir,
        release_stale=False,
    )

    assert probed == [wt]
    assert "marked_failed_missing_worktree" not in report.actions
    assert report.status == "done"
    assert report.commits_ahead == 0
    assert report.closeout["blocker"] == "none"
    state = json.loads((task_dir / f"{task_id}.json").read_text(encoding="utf-8"))
    assert state["status"] == "done"
