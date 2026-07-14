"""Tests for cleanup state-machine and Codex-state bridge primitives."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from scripts.orchestration.task_family import codex_state, git_safety
from scripts.orchestration.task_family.executor import CleanupExecutor, CleanupPlan, load_state


def _git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }


def git(tmp_path: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        env=_git_env(),
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    return (completed.stdout or "").strip()


def init_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    remote = tmp_path / "origin.git"
    git(tmp_path, "init", "--initial-branch=main", str(repo))
    git(tmp_path, "init", "--bare", str(remote))
    git(repo, "config", "user.email", "cleanup-tester@example.com")
    git(repo, "config", "user.name", "Cleanup Executor")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "seed")
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")
    return repo, remote


def add_worktree_branch(repo: Path, branch: str, *, push_remote: bool = False) -> Path:
    worktree = repo.parent / f"wt-{branch.replace('/', '-')}-{uuid4().hex[:6]}"
    git(repo, "worktree", "add", "-b", branch, str(worktree), "main")
    (worktree / "payload.txt").write_text(f"{branch}\n", encoding="utf-8")
    git(worktree, "add", "payload.txt")
    git(worktree, "commit", "-m", f"worktree {branch}")
    if push_remote:
        git(worktree, "push", "-u", "origin", branch)
    return worktree


def write_codex_db(
    path: Path,
    *,
    task_id: int,
    title: str,
    cwd: str,
    archived: bool = False,
    archived_at: str | None = None,
    host: str = "runner-host",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE threads(id INTEGER PRIMARY KEY, title TEXT, cwd TEXT, archived INTEGER, archived_at TEXT, host TEXT)"
    )
    conn.execute(
        "INSERT INTO threads(id,title,cwd,archived,archived_at,host) VALUES (?,?,?,?,?,?)",
        (task_id, title, cwd, int(archived), archived_at, host),
    )
    conn.commit()
    conn.close()


def make_plan(
    repo: Path,
    worktree: Path,
    db_path: Path,
    *,
    lineage_id: str = "lineage-5140",
    task_id: int = 1,
    branch: str,
) -> CleanupPlan:
    return CleanupPlan(
        task_id=task_id,
        family="cleanup",
        lineage_id=lineage_id,
        title="Cleanup Task",
        cwd=str(worktree),
        branch=branch,
        worktree=worktree,
        thread_id=task_id,
        db_path=db_path,
        host="runner-host",
        explicit_protected=frozenset({"forbidden/branch"}),
    )


def mk_pr_payload(worktree: Path) -> dict[str, Any]:
    head = git(worktree, "rev-parse", "HEAD")
    return {
        "number": 42,
        "state": "MERGED",
        "headRefOid": head,
        "headRefName": worktree.name,
        "baseRefName": "main",
        "mergeStateStatus": "CLEAN",
        "mergeCommit": "0" * 40,
        "isCrossRepository": False,
    }


def test_codex_state_discovery_and_archive_restore(tmp_path: Path) -> None:
    home = tmp_path / ".codex"
    home.mkdir()
    first = home / "state_old.sqlite"
    second = home / "state_new.sqlite"
    third = home / "state_invalid.sqlite"
    write_codex_db(first, task_id=1, title="a", cwd="/x", archived=False)
    write_codex_db(second, task_id=1, title="a", cwd="/x", archived=False)
    third.write_text("", encoding="utf-8")
    now = time.time()
    os.utime(first, (now - 10, now - 10))
    os.utime(second, (now, now))
    os.utime(third, (now - 20, now - 20))

    discovered = codex_state.discover_state_database(codex_home=home)
    assert discovered == second

    with pytest.raises(codex_state.CodexStateDiscoveryError):
        os.utime(first, (now, now))
        codex_state.discover_state_database(codex_home=home)

    with pytest.raises(codex_state.CodexStateSchemaError):
        conn = sqlite3.connect(third)
        conn.execute("CREATE TABLE missing_threads(value INTEGER)")
        conn.commit()
        conn.close()
        codex_state.discover_state_database(codex_home=home)


def test_codex_state_reconcile_archive_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "state.sqlite"
    write_codex_db(
        db_path,
        task_id=11,
        title="task",
        cwd="/repo/main",
        archived=False,
        archived_at=None,
    )

    before, after, changed = codex_state.reconcile_task_thread(
        task_id=11,
        action="archive",
        expected_title="task",
        expected_cwd="/repo/main",
        expected_host="runner-host",
        db_path=db_path,
    )
    assert changed
    assert not before.archived and after.archived
    assert after.archived_at is not None

    unchanged = codex_state.reconcile_task_thread(
        task_id=11,
        action="archive",
        expected_title="task",
        expected_cwd="/repo/main",
        expected_host="runner-host",
        db_path=db_path,
    )
    assert unchanged[2] is False

    before_restore, after_restore, restored = codex_state.reconcile_task_thread(
        task_id=11,
        action="restore",
        expected_title="task",
        expected_cwd="/repo/main",
        expected_host="runner-host",
        db_path=db_path,
    )
    assert restored
    assert before_restore.archived and not after_restore.archived

    _again, final, unchanged_restore = codex_state.reconcile_task_thread(
        task_id=11,
        action="restore",
        expected_title="task",
        expected_cwd="/repo/main",
        expected_host="runner-host",
        db_path=db_path,
    )
    assert unchanged_restore is False
    assert not final.archived and final.archived_at is None


def test_codex_state_read_thread_record_stable_and_conflict(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    db_path = tmp_path / "state.sqlite"
    db_path.write_text("", encoding="utf-8")
    record_one = codex_state.ThreadRecord(1, "task", "/repo", False, None, "host")
    record_two = codex_state.ThreadRecord(1, "task", "/repo", False, None, "host")
    record_three = codex_state.ThreadRecord(1, "task", "/repo", False, None, "host")

    calls = {"n": 0}

    def unstable_read(*args: Any, **kwargs: Any) -> codex_state.ThreadRecord:
        calls["n"] += 1
        if calls["n"] <= 2:
            return record_one
        if calls["n"] <= 4:
            return record_two
        return record_three

    monkeypatch.setattr(codex_state, "_read_thread_once", unstable_read)
    assert codex_state.read_thread_record(1, db_path, read_window_seconds=1.2) == record_three

    calls["n"] = 0

    def never_stable(*args: Any, **kwargs: Any) -> codex_state.ThreadRecord:
        calls["n"] += 1
        return record_one if calls["n"] % 2 else record_two

    monkeypatch.setattr(codex_state, "_read_thread_once", never_stable)
    with pytest.raises(codex_state.CodexStateConflictError):
        codex_state.read_thread_record(1, db_path, read_window_seconds=0.01)


def test_codex_state_context_and_host_mismatch(tmp_path: Path) -> None:
    db = tmp_path / "state.sqlite"
    write_codex_db(db, task_id=9, title="clean", cwd="/a", archived=False, archived_at=None)
    with pytest.raises(codex_state.CodexStateContextError):
        codex_state.reconcile_task_thread(
            task_id=9,
            action="archive",
            expected_title="clean",
            expected_cwd="/b",
            expected_host="runner-host",
            db_path=db,
        )

    with pytest.raises(codex_state.CodexStateContextError):
        codex_state.reconcile_task_thread(
            task_id=9,
            action="archive",
            expected_title="clean",
            expected_cwd="/a",
            expected_host="different-host",
            db_path=db,
        )


def test_verify_frozen_preconditions_blocks_active_jobs(tmp_path: Path) -> None:
    repo, _ = init_repo(tmp_path)
    state_root = git_safety.resolve_state_root(repo)
    active = state_root / "jobs" / "job-lineage-5140.json"
    active.parent.mkdir(parents=True, exist_ok=True)
    active.write_text(json.dumps({"lineage": "lineage-5140"}), encoding="utf-8")
    with (
        git_safety.operation_lock(repo),
        git_safety.lineage_lock(repo, "lineage-5140"),
        git_safety.family_lock(repo, "cleanup"),
        git_safety.worktree_lock(repo, repo),
    ):
        with pytest.raises(git_safety.GitSafetyError, match="active jobs/leases"):
            git_safety.verify_frozen_preconditions(
                repo, lineage_id="lineage-5140", family="cleanup", worktree=repo
            )


def test_verify_worktree_candidate_blocks_dirty_worktree(tmp_path: Path) -> None:
    repo, _ = init_repo(tmp_path)
    worktree = add_worktree_branch(repo, "cleanup/dirty")
    (worktree / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(git_safety.GitSafetyError, match="dirty"):
        git_safety.verify_worktree_candidate(
            repo,
            worktree=worktree,
            branch=worktree.name,
        )


def test_verify_worktree_candidate_blocks_shared_worktree(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo, _ = init_repo(tmp_path)
    worktree = add_worktree_branch(repo, "cleanup/shared")
    info = git_safety.worktree_list(repo)
    shared = git_safety.WorktreeInfo(worktree, worktree.name)
    fake_list = [*info, git_safety.WorktreeInfo(repo / ".tmp-fake", worktree.name)]
    monkeypatch.setattr(git_safety, "worktree_list", lambda *_args, **_kwargs: fake_list)
    with pytest.raises(git_safety.GitSafetyError, match="shared"):
        git_safety.verify_worktree_candidate(
            repo,
            worktree=worktree,
            branch=worktree.name,
        )


def test_protected_branch_lookup_failure_blocks_decision(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _ = init_repo(tmp_path)

    def fake_run_gh(args: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 1, "", "network unavailable")

    monkeypatch.setattr(git_safety, "run_gh", fake_run_gh)
    with pytest.raises(git_safety.GitHubQueryError):
        git_safety.protected_branches(repo)


def test_build_and_verify_bundle_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _ = init_repo(tmp_path)
    monkeypatch.setattr(git_safety, "assert_no_unknown_branch_mutation", lambda *args, **kwargs: None)
    receipt = git_safety.build_bundle(
        repo,
        branch="main",
        bundle_dir=tmp_path / "bundles",
    )
    git_safety.verify_bundle(receipt.path, branch="main", repo_root=repo)

    with receipt.path.open("a", encoding="utf-8") as handle:
        handle.write("tamper\n")
    with pytest.raises(git_safety.GitSafetyError):
        git_safety.assert_bundle_matches_receipt(receipt, branch="main")


def test_remote_present_blocks_branch_deletion_precondition(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _ = init_repo(tmp_path)
    branch = "cleanup/locked"
    worktree = add_worktree_branch(repo, branch, push_remote=False)
    monkeypatch.setattr(git_safety, "is_protected_branch", lambda *args, **kwargs: False)

    bundle = git_safety.build_bundle(
        repo,
        branch=branch,
        bundle_dir=tmp_path / "bundles",
    )
    head = git(worktree, "rev-parse", "HEAD")
    pr = {
        "state": "MERGED",
        "headRefOid": head,
        "mergeCommit": "0" * 40,
        "number": 99,
        "baseRefName": "main",
        "mergeStateStatus": "CLEAN",
        "isCrossRepository": False,
    }

    # remote branch exists => should block.
    git(worktree, "push", "-u", "origin", branch)
    with pytest.raises(git_safety.GitSafetyError, match="remote branch"):
        git_safety.assert_branch_deletion_preconditions(
            repo_root=repo,
            branch=branch,
            pr_data=pr,
            bundle=bundle,
        )
    git(repo, "push", "origin", f":{branch}")
    assert git_safety.assert_branch_deletion_preconditions(
        repo_root=repo,
        branch=branch,
        pr_data=pr,
        bundle=bundle,
    )


def test_executor_partial_failure_resume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _ = init_repo(tmp_path)
    branch = "cleanup/resume"
    worktree = add_worktree_branch(repo, branch)
    db = tmp_path / "state.sqlite"
    write_codex_db(db, task_id=1, title="Cleanup Task", cwd=str(worktree), archived=False)
    plan = make_plan(
        repo,
        worktree,
        db,
        task_id=1,
        lineage_id="lineage-resume",
        branch=branch,
    )

    monkeypatch.setattr(git_safety, "assert_no_unknown_branch_mutation", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        git_safety,
        "query_pr_by_head",
        lambda *args, **kwargs: mk_pr_payload(worktree),
    )

    executor = CleanupExecutor(repo, plan, crash_after_stage="tasks_archived")
    blocked = executor.run()
    assert blocked["state"] == "blocked"
    assert blocked["resume_stage"] == "tasks_archived"

    resumed = CleanupExecutor(repo, plan).run()
    assert resumed["state"] == "completed"
    assert resumed["stages"]["runtime_retired"]["retained"] is True
    assert resumed["history"] == [
        "planned",
        "frozen",
        "verified",
        "snapshotted",
        "tasks_archived",
        "worktrees_removed",
        "branches_deleted",
        "runtime_retired",
        "completed",
    ]

    payload = load_state(repo, plan)
    assert payload["stages"]["snapshotted"]["bundle"]["sha256"]
    assert not worktree.exists()

    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{worktree.name}"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
            env=_git_env(),
        )

    conn = sqlite3.connect(db)
    row = conn.execute("SELECT archived FROM threads WHERE id = 1").fetchone()
    conn.close()
    assert row == (1,)


def test_executor_remote_block_then_remote_gone_cleanup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _ = init_repo(tmp_path)
    branch = "cleanup/remote"
    worktree = add_worktree_branch(repo, branch)
    db = tmp_path / "state.sqlite"
    write_codex_db(db, task_id=2, title="Cleanup Task", cwd=str(worktree), archived=False)
    plan = make_plan(
        repo,
        worktree,
        db,
        task_id=2,
        lineage_id="lineage-remote",
        branch=branch,
    )

    monkeypatch.setattr(git_safety, "assert_no_unknown_branch_mutation", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        git_safety,
        "query_pr_by_head",
        lambda *args, **kwargs: mk_pr_payload(worktree),
    )
    git(worktree, "push", "-u", "origin", branch)
    first = CleanupExecutor(repo, plan, crash_after_stage="worktrees_removed")
    stopped = first.run()
    assert stopped["state"] == "blocked"
    assert stopped["resume_stage"] == "worktrees_removed"

    second = CleanupExecutor(repo, plan)
    still_blocked = second.run()
    assert still_blocked["state"] == "blocked"
    assert still_blocked["resume_stage"] == "worktrees_removed"
    assert "remote branch still present" in still_blocked["blocked"]["reason"]

    git(repo, "push", "origin", f":{branch}")
    completed = CleanupExecutor(repo, plan).run()
    assert completed["state"] == "completed"


def test_executor_unmerged_pr_blocks_verification(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _ = init_repo(tmp_path)
    branch = "cleanup/reject"
    worktree = add_worktree_branch(repo, branch)
    db = tmp_path / "state.sqlite"
    write_codex_db(db, task_id=3, title="Cleanup Task", cwd=str(worktree), archived=False)
    plan = make_plan(
        repo,
        worktree,
        db,
        task_id=3,
        lineage_id="lineage-reject",
        branch=branch,
    )

    pr_open = mk_pr_payload(worktree)
    pr_open["state"] = "OPEN"
    monkeypatch.setattr(git_safety, "assert_no_unknown_branch_mutation", lambda *args, **kwargs: None)
    monkeypatch.setattr(git_safety, "query_pr_by_head", lambda *args, **kwargs: pr_open)

    blocked = CleanupExecutor(repo, plan).run()
    assert blocked["state"] == "blocked"
    assert blocked["resume_stage"] == "frozen"


def test_executor_restore_archive_is_supported_before_cleanup_stages(tmp_path: Path) -> None:
    repo, _ = init_repo(tmp_path)
    branch = "cleanup/restore"
    worktree = add_worktree_branch(repo, branch)
    db = tmp_path / "state.sqlite"
    write_codex_db(
        db,
        task_id=4,
        title="Cleanup Task",
        cwd=str(worktree),
        archived=True,
        archived_at="2026-07-13T00:00:00Z",
    )
    plan = make_plan(
        repo,
        worktree,
        db,
        task_id=4,
        lineage_id="lineage-restore",
        branch=branch,
    )
    restored = CleanupExecutor(repo, plan).restore_archive()
    assert restored["state"] == "verified"

    conn = sqlite3.connect(db)
    row = conn.execute("SELECT archived, archived_at FROM threads WHERE id = 4").fetchone()
    conn.close()
    assert row == (0, None)


def test_executor_preserves_unrelated_files_and_receipts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _ = init_repo(tmp_path)
    branch = "cleanup/unrelated"
    worktree = add_worktree_branch(repo, branch)
    db = tmp_path / "state.sqlite"
    write_codex_db(db, task_id=5, title="Cleanup Task", cwd=str(worktree), archived=False)
    marker = git_safety.resolve_state_root(repo) / "states" / "external.txt"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("preserve\n", encoding="utf-8")

    plan = make_plan(
        repo,
        worktree,
        db,
        task_id=5,
        lineage_id="lineage-unrelated",
        branch=branch,
    )
    monkeypatch.setattr(git_safety, "assert_no_unknown_branch_mutation", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        git_safety,
        "query_pr_by_head",
        lambda *args, **kwargs: mk_pr_payload(worktree),
    )

    result = CleanupExecutor(repo, plan).run()
    assert result["state"] == "completed"
    assert marker.exists()
    assert "snapshotted" in result["stages"]
    assert "bundle" in result["stages"]["snapshotted"]
