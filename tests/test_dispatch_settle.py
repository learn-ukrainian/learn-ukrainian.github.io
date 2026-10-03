"""Tests for scripts.orchestration.dispatch_settle."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

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


def test_heal_zombie_review_names_dead_worker_reason(tmp_path: Path) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    task_id = "dead-review"
    path = task_dir / f"{task_id}.json"
    path.write_text(
        json.dumps(
            {
                "task_id": task_id,
                "status": "running",
                "pid": 999_999_999,
                "require_review_verdict": True,
                "failure_reason": None,
            }
        ),
        encoding="utf-8",
    )

    assert "marked_failed_zombie_running" in ds.heal_zombie_task(task_dir, task_id)
    healed = json.loads(path.read_text(encoding="utf-8"))
    assert healed["status"] == "failed"
    assert healed["failure_reason"] == "worker_process_dead"


def test_settle_missing_worktree_review_names_reason(tmp_path: Path) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    task_id = "missing-review"
    path = task_dir / f"{task_id}.json"
    path.write_text(
        json.dumps(
            {
                "task_id": task_id,
                "status": "running",
                "pid": 999_999_999,
                "worktree_path": str(tmp_path / "missing"),
                "require_review_verdict": True,
                "failure_reason": None,
            }
        ),
        encoding="utf-8",
    )

    assert "marked_failed_missing_worktree" in ds.settle_missing_worktree(task_dir, task_id)
    healed = json.loads(path.read_text(encoding="utf-8"))
    assert healed["status"] == "failed"
    assert healed["failure_reason"] == "worktree_missing_at_settle"
    assert healed.get("finished_at")


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


@pytest.mark.parametrize("open_pr", [False, True])
def test_settle_push_opens_pr_only_with_explicit_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, open_pr: bool
) -> None:
    args = ["task", "--task-id", "t1", "--push"]
    if open_pr:
        args.append("--open-pr")
    parsed = ds._build_parser().parse_args(args)
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command == ["gh", "repo", "view", "--json", "defaultBranchRef"]:
            return subprocess.CompletedProcess(command, 0, '{"defaultBranchRef":{"name":"trunk"}}', "")
        return subprocess.CompletedProcess(command, 0, "https://example.invalid/pr/1", "")

    monkeypatch.setattr(ds, "_run", fake_run)
    monkeypatch.setattr(ds, "_find_pr", lambda *_args: (None, None))
    actions = ds.push_and_maybe_open_pr(tmp_path, "codex/t1", open_pr=parsed.open_pr, title=None, body=None)

    assert calls[0] == ["git", "push", "-u", "origin", "HEAD"]
    from scripts.publish.github import Request

    creates = [call for call in calls if isinstance(call, Request)]
    assert len(creates) == int(open_pr)
    if creates:
        assert creates[0].verb == "pr-create"
        assert creates[0].fields["base"] == "trunk"
        assert creates[0].fields["title"] == "chore(dispatch): settle codex/t1"
        assert creates[0].fields["body"].startswith("Auto-opened")
    assert actions == (["pushed", "pr_created:https://example.invalid/pr/1"] if open_pr else ["pushed"])


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


def test_settle_missing_worktree_stale_observation_rejected_preserves_claims(tmp_path: Path, monkeypatch) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    task_id = "stale-race"
    path = task_dir / f"{task_id}.json"

    initial_data = {
        "task_id": task_id,
        "run_nonce": "run-1",
        "started_at": "2026-01-01T00:00:00Z",
        "status": "running",
        "pid": 999_999_999,
        "worktree_path": str(tmp_path / "missing"),
    }
    path.write_text(json.dumps(initial_data), encoding="utf-8")

    ledger_path = tmp_path / "own.sqlite3"
    ledger = OwnershipLedger(ledger_path, task_state_dir=task_dir)
    import sqlite3
    import time

    conn = sqlite3.connect(ledger_path)
    conn.execute(
        "CREATE TABLE write_claims (task_id TEXT, claim_json TEXT, pid INTEGER, created_at REAL, PRIMARY KEY (task_id, claim_json))"
    )
    conn.execute(
        "INSERT INTO write_claims VALUES (?,?,?,?)",
        (task_id, '{"kind":"file","norm":"scripts/foo.py"}', 999_999_999, time.time() - 100),
    )
    conn.commit()
    conn.close()

    # Inject replacement after initial read, so mark_missing_worktree_failed is exercised and rejects
    real_load = ds._load_task
    helper_called: list[bool] = []

    def load_and_replace(tdir: Path, tid: str) -> dict[str, Any]:
        loaded = real_load(tdir, tid)
        if tid == task_id and loaded.get("run_nonce") == "run-1":
            replaced_data = {
                "task_id": task_id,
                "run_nonce": "run-2",
                "started_at": "2026-01-01T01:00:00Z",
                "status": "running",
                "pid": os.getpid(),
                "worktree_path": str(tmp_path / "missing"),
            }
            path.write_text(json.dumps(replaced_data), encoding="utf-8")
        return loaded

    monkeypatch.setattr(ds, "_load_task", load_and_replace)

    real_helper = ds.mark_missing_worktree_failed

    def spy_helper(*args: Any, **kwargs: Any) -> tuple[dict[str, Any], bool]:
        helper_called.append(True)
        return real_helper(*args, **kwargs)

    monkeypatch.setattr(ds, "mark_missing_worktree_failed", spy_helper)

    actions = ds.settle_missing_worktree(task_dir, task_id, ledger=ledger)
    assert helper_called == [True], "mark_missing_worktree_failed must be called under lock"
    assert actions == []

    current = json.loads(path.read_text(encoding="utf-8"))
    assert current["status"] == "running"
    assert current["run_nonce"] == "run-2"

    conn = sqlite3.connect(ledger_path)
    rows = conn.execute("SELECT task_id FROM write_claims WHERE task_id = ?", (task_id,)).fetchall()
    conn.close()
    assert len(rows) == 1


def test_settle_missing_worktree_replacement_after_transition_preserves_new_run_claims(tmp_path: Path) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    task_id = "reuse-race"
    path = task_dir / f"{task_id}.json"

    initial_data = {
        "task_id": task_id,
        "run_nonce": "run-1",
        "started_at": "2026-01-01T00:00:00Z",
        "status": "running",
        "pid": 999_999_999,
        "worktree_path": str(tmp_path / "missing"),
    }
    path.write_text(json.dumps(initial_data), encoding="utf-8")

    ledger_path = tmp_path / "own.sqlite3"
    ledger = OwnershipLedger(ledger_path, task_state_dir=task_dir)
    import sqlite3
    import time

    conn = sqlite3.connect(ledger_path)
    conn.execute(
        "CREATE TABLE write_claims (task_id TEXT, claim_json TEXT, pid INTEGER, created_at REAL, PRIMARY KEY (task_id, claim_json))"
    )
    # Old dead run's claim
    conn.execute(
        "INSERT INTO write_claims VALUES (?,?,?,?)",
        (task_id, '{"kind":"file","norm":"scripts/foo.py"}', 999_999_999, time.time() - 300),
    )
    # Replacement live run's claim for the same task_id aged beyond the 180s grace window
    conn.execute(
        "INSERT INTO write_claims VALUES (?,?,?,?)",
        (task_id, '{"kind":"file","norm":"scripts/bar.py"}', os.getpid(), time.time() - 200),
    )
    conn.commit()
    conn.close()

    actions = ds.settle_missing_worktree(task_dir, task_id, ledger=ledger)
    assert "marked_failed_missing_worktree" in actions
    assert "released_ownership_claims" in actions

    current = json.loads(path.read_text(encoding="utf-8"))
    assert current["status"] == "failed"

    # Verify that the dead run's claim was deleted but the replacement run's claim was preserved
    conn = sqlite3.connect(ledger_path)
    rows = conn.execute("SELECT pid, claim_json FROM write_claims WHERE task_id = ?", (task_id,)).fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0][0] == os.getpid()
    assert "scripts/bar.py" in rows[0][1]

    # Beyond-grace reconciliation: overlapping challenger admission must not delete
    # the live replacement claim, and challenger must remain refused (#8659 / CF r4 F1).
    challenger = ledger.admit(
        task_id="challenger-task",
        mode="workspace-write",
        owned_paths=["scripts/bar.py"],
        pid=os.getpid(),
    )
    assert challenger.admitted is False
    assert challenger.would_refuse is True
    assert "path ownership conflict (REFUSE)" in (challenger.reason or "")

    conn = sqlite3.connect(ledger_path)
    rows_after = conn.execute("SELECT pid, claim_json FROM write_claims WHERE task_id = ?", (task_id,)).fetchall()
    conn.close()
    assert len(rows_after) == 1
    assert rows_after[0][0] == os.getpid()
    assert "scripts/bar.py" in rows_after[0][1]


def test_heal_zombie_task_pidless_preserves_replacement_run_claims(tmp_path: Path) -> None:
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    task_id = "pidless-zombie"
    path = task_dir / f"{task_id}.json"

    initial_data = {
        "task_id": task_id,
        "run_nonce": "run-1",
        "started_at": "2026-01-01T00:00:00Z",
        "status": "running",
        "pid": None,
    }
    path.write_text(json.dumps(initial_data), encoding="utf-8")

    ledger_path = tmp_path / "own.sqlite3"
    ledger = OwnershipLedger(ledger_path, task_state_dir=task_dir)
    import sqlite3
    import time

    conn = sqlite3.connect(ledger_path)
    conn.execute(
        "CREATE TABLE write_claims (task_id TEXT, claim_json TEXT, pid INTEGER, created_at REAL, PRIMARY KEY (task_id, claim_json))"
    )
    # Stale/pidless claim
    conn.execute(
        "INSERT INTO write_claims VALUES (?,?,?,?)",
        (task_id, '{"kind":"file","norm":"scripts/foo.py"}', None, time.time() - 300),
    )
    # Replacement live run's claim for the same task_id aged beyond the 180s grace window
    conn.execute(
        "INSERT INTO write_claims VALUES (?,?,?,?)",
        (task_id, '{"kind":"file","norm":"scripts/bar.py"}', os.getpid(), time.time() - 200),
    )
    conn.commit()
    conn.close()

    actions = ds.heal_zombie_task(task_dir, task_id, ledger=ledger)
    assert "marked_failed_zombie_running" in actions
    assert "released_ownership_claims" in actions

    current = json.loads(path.read_text(encoding="utf-8"))
    assert current["status"] == "failed"

    # Verify that the stale claim was deleted but the replacement run's live claim was preserved
    conn = sqlite3.connect(ledger_path)
    rows = conn.execute("SELECT pid, claim_json FROM write_claims WHERE task_id = ?", (task_id,)).fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0][0] == os.getpid()
    assert "scripts/bar.py" in rows[0][1]

    # Beyond-grace reconciliation: overlapping challenger admission must not delete
    # the live replacement claim, and challenger must remain refused (#8659 / CF r4 F1).
    challenger = ledger.admit(
        task_id="challenger-task",
        mode="workspace-write",
        owned_paths=["scripts/bar.py"],
        pid=os.getpid(),
    )
    assert challenger.admitted is False
    assert challenger.would_refuse is True
    assert "path ownership conflict (REFUSE)" in (challenger.reason or "")

    conn = sqlite3.connect(ledger_path)
    rows_after = conn.execute("SELECT pid, claim_json FROM write_claims WHERE task_id = ?", (task_id,)).fetchall()
    conn.close()
    assert len(rows_after) == 1
    assert rows_after[0][0] == os.getpid()
    assert "scripts/bar.py" in rows_after[0][1]


@pytest.fixture(autouse=True)
def _synthetic_publishing_rules(synthetic_opsec, publisher_transport, monkeypatch):
    """Use synthetic private tooling and an explicit destination for send spies."""
    monkeypatch.setenv("GH_REPO", "unit/public")
