from __future__ import annotations

import fcntl
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest

from scripts.orchestration import reap_worktrees as rw

_REAL_RUN = subprocess.run


def git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and not key.startswith("PRE_COMMIT") and key != "AGENT_NO_MERGE"
    }


def git(cwd: Path, *args: str) -> str:
    proc = _REAL_RUN(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=git_env(),
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return (proc.stdout or "").strip()


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    remote = tmp_path / "origin.git"
    git(tmp_path, "init", "--bare", str(remote))
    git(tmp_path, "init", "--initial-branch=main", str(repo))
    git(repo, "config", "user.email", "tester@example.com")
    git(repo, "config", "user.name", "Test User")
    (repo / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    git(repo, "add", ".gitignore", "README.md")
    git(repo, "commit", "-m", "base")
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")
    return repo


def add_worktree(
    repo: Path,
    branch: str,
    *,
    path: Path | None = None,
    base: str = "main",
) -> Path:
    worktree = path or repo / ".worktrees" / branch.replace("/", "-")
    worktree.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "add", "-b", branch, str(worktree), base)
    return worktree


def patch_gh(
    monkeypatch: pytest.MonkeyPatch,
    states_by_branch: dict[str, list[dict[str, Any]]],
) -> list[str]:
    calls: list[str] = []

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if args and args[0] == "gh":
            branch = args[args.index("--head") + 1]
            calls.append(branch)
            payload = [dict(item) for item in states_by_branch.get(branch, [])]
            for item in payload:
                if item.get("headRefOid") or item.get("state") == "OPEN":
                    continue
                head = _REAL_RUN(
                    ["git", "rev-parse", f"refs/heads/{branch}"],
                    cwd=kwargs["cwd"],
                    capture_output=True,
                    text=True,
                    check=True,
                    env=git_env(),
                ).stdout.strip()
                item["headRefOid"] = head
            return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
        return _REAL_RUN(args, **kwargs)

    monkeypatch.setattr(rw.subprocess, "run", fake_run)
    return calls


def result_for(results: list[rw.ReapResult], path: Path) -> rw.ReapResult:
    matches = [result for result in results if Path(result.path).resolve() == path.resolve()]
    assert matches, [result.path for result in results]
    return matches[0]


def assert_main_checkout_unchanged(repo: Path) -> None:
    assert git(repo, "branch", "--show-current") == "main"
    assert git(repo, "status", "--porcelain") == ""


def test_primary_checkout_root_resolves_from_linked_worktree(tmp_path: Path) -> None:
    main = tmp_path / "learn-ukrainian"
    worktree = main / ".worktrees" / "dispatch" / "codex" / "task"
    git_dir = main / ".git" / "worktrees" / "task"
    worktree.mkdir(parents=True)
    git_dir.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {git_dir}\n", encoding="utf-8")

    assert rw.primary_checkout_root(worktree) == main


def test_merged_clean_removes_worktree_and_keeps_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "codex/merged")
    patch_gh(monkeypatch, {"codex/merged": [{"number": 12, "state": "MERGED"}]})

    results = rw.reap_worktrees(repo_root=repo, apply=True)

    result = result_for(results, worktree)
    assert result.action == "removed"
    assert result.reason == "PR #12 MERGED"
    assert not worktree.exists()
    assert git(repo, "rev-parse", "--verify", "codex/merged")
    assert_main_checkout_unchanged(repo)


def test_merged_dirty_is_preserved_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A scheduled cleanup must never silently commit and remove dirty work."""
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "codex/dirty")
    (worktree / "dirty.txt").write_text("not committed\n", encoding="utf-8")
    patch_gh(monkeypatch, {"codex/dirty": [{"number": 13, "state": "MERGED"}]})

    results = rw.reap_worktrees(repo_root=repo, apply=True)

    result = result_for(results, worktree)
    assert result.action == "skipped"
    assert result.reason == "dirty; qualifies for reap because PR #13 MERGED"
    assert worktree.exists()
    assert (worktree / "dirty.txt").read_text(encoding="utf-8") == "not committed\n"
    assert_main_checkout_unchanged(repo)


def test_preserve_then_reap_commits_dirty_worktree_before_removal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "codex/preserve")
    (worktree / "artifact.txt").write_text("recover me\n", encoding="utf-8")
    patch_gh(monkeypatch, {"codex/preserve": [{"number": 14, "state": "MERGED"}]})

    results = rw.reap_worktrees(
        repo_root=repo,
        apply=True,
        preserve_then_reap=True,
    )

    result = result_for(results, worktree)
    assert result.action == "preserved_then_removed"
    assert not worktree.exists()

    recovered = tmp_path / "recovered-preserve"
    git(repo, "worktree", "add", str(recovered), "codex/preserve")
    assert (recovered / "artifact.txt").read_text(encoding="utf-8") == "recover me\n"
    assert (
        git(recovered, "log", "-1", "--format=%s")
        == "wip: preserve codex/preserve before reap [skip ci]"
    )
    assert_main_checkout_unchanged(repo)


def test_build_branch_clean_and_aged_is_removed_but_branch_is_kept(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "build/a1/aged")
    now = time.time()
    old = now - 8 * 3600
    os.utime(worktree, (old, old))
    patch_gh(monkeypatch, {})

    results = rw.reap_worktrees(
        repo_root=repo,
        apply=True,
        build_age_hours=6,
        now=now,
    )

    result = result_for(results, worktree)
    assert result.action == "removed"
    assert result.reason == "build branch age 8.0h > 6h"
    assert not worktree.exists()
    assert git(repo, "rev-parse", "--verify", "build/a1/aged")
    assert_main_checkout_unchanged(repo)


def test_pushed_origin_clean_worktree_is_removed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "codex/pushed")
    (worktree / "pushed.txt").write_text("pushed\n", encoding="utf-8")
    git(worktree, "add", "pushed.txt")
    git(worktree, "commit", "-m", "feat: pushed")
    git(worktree, "push", "-u", "origin", "codex/pushed")
    patch_gh(monkeypatch, {})

    results = rw.reap_worktrees(repo_root=repo, apply=True)

    result = result_for(results, worktree)
    assert result.action == "removed"
    assert result.reason == "HEAD matches origin/codex/pushed"
    assert not worktree.exists()
    assert git(repo, "rev-parse", "--verify", "codex/pushed")
    assert_main_checkout_unchanged(repo)


def test_external_worktree_path_is_untouched(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    external = add_worktree(
        repo,
        "codex/external",
        path=tmp_path / "external-worktree",
    )
    calls = patch_gh(
        monkeypatch,
        {"codex/external": [{"number": 15, "state": "MERGED"}]},
    )

    results = rw.reap_worktrees(repo_root=repo, apply=True)

    result = result_for(results, external)
    assert result.action == "skipped"
    assert result.reason == "outside repo .worktrees/"
    assert external.exists()
    assert "codex/external" not in calls
    assert_main_checkout_unchanged(repo)


def test_dry_run_makes_zero_filesystem_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "codex/dry-run")
    patch_gh(monkeypatch, {"codex/dry-run": [{"number": 16, "state": "MERGED"}]})

    rc = rw.main(["--repo-root", str(repo), "--dry-run"])

    captured = capsys.readouterr()
    assert rc == 0
    assert "DRY RUN:" in captured.out
    assert "WOULD_REMOVE" in captured.out
    assert str(worktree) in captured.out
    assert worktree.exists()
    assert git(worktree, "status", "--porcelain") == ""
    assert_main_checkout_unchanged(repo)


def test_class_a_settled_dispatch_removed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    task_id = "5102-raisa-review-repair"
    worktree_path = repo / ".worktrees" / "dispatch" / "codex" / task_id
    add_worktree(repo, "codex/5102-raisa", path=worktree_path)

    # Create task JSON
    tasks_dir = repo / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / f"{task_id}.json").write_text(
        json.dumps({"status": "done"}), encoding="utf-8"
    )

    # Mock active set and PR state
    monkeypatch.setattr(rw, "_active_task_ids", lambda: set())
    patch_gh(monkeypatch, {"codex/5102-raisa": []})

    results = rw.reap_worktrees(repo_root=repo, apply=True)
    result = result_for(results, worktree_path)
    assert result.action == "removed"
    assert "settled dispatch" in result.reason
    assert "task-id=5102-raisa-review-repair" in result.reason
    assert not worktree_path.exists()


def test_class_a_no_deliverable_dispatch_removed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``no_deliverable`` dispatch is terminal; its clean worktree reaps."""
    repo = init_repo(tmp_path)
    task_id = "5800-false-success-noop"
    worktree_path = repo / ".worktrees" / "dispatch" / "codex" / task_id
    add_worktree(repo, "codex/5800-false-success", path=worktree_path)

    tasks_dir = repo / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / f"{task_id}.json").write_text(
        json.dumps({"status": "no_deliverable"}), encoding="utf-8"
    )

    monkeypatch.setattr(rw, "_active_task_ids", lambda: set())
    patch_gh(monkeypatch, {"codex/5800-false-success": []})

    results = rw.reap_worktrees(repo_root=repo, apply=True)
    result = result_for(results, worktree_path)
    assert result.action == "removed"
    assert "settled dispatch" in result.reason
    assert "status=no_deliverable" in result.reason
    assert not worktree_path.exists()


def test_class_a_fail_safe_skips(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    task_id = "5102-raisa-fail"
    worktree_path = repo / ".worktrees" / "dispatch" / "codex" / task_id
    add_worktree(repo, "codex/5102-raisa-fail", path=worktree_path)

    tasks_dir = repo / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    task_file = tasks_dir / f"{task_id}.json"
    task_file.write_text(json.dumps({"status": "done"}), encoding="utf-8")

    # Case 1: active task
    monkeypatch.setattr(rw, "_active_task_ids", lambda: {task_id})
    patch_gh(monkeypatch, {"codex/5102-raisa-fail": []})
    results = rw.reap_worktrees(repo_root=repo, apply=True)
    assert result_for(results, worktree_path).action == "skipped"

    # Case 2: API down
    monkeypatch.setattr(rw, "_active_task_ids", lambda: None)
    results = rw.reap_worktrees(repo_root=repo, apply=True)
    assert result_for(results, worktree_path).action == "skipped"

    # Case 3: missing task file
    monkeypatch.setattr(rw, "_active_task_ids", lambda: set())
    task_file.unlink()
    results = rw.reap_worktrees(repo_root=repo, apply=True)
    assert result_for(results, worktree_path).action == "skipped"

    # Re-create task file for remaining cases
    task_file.write_text(json.dumps({"status": "running"}), encoding="utf-8")

    # Case 4: task status is not done/failed
    results = rw.reap_worktrees(repo_root=repo, apply=True)
    assert result_for(results, worktree_path).action == "skipped"

    # Set status back to done
    task_file.write_text(json.dumps({"status": "done"}), encoding="utf-8")

    # Case 5: dirty tree
    (worktree_path / "dirty.txt").write_text("uncommitted change", encoding="utf-8")
    results = rw.reap_worktrees(repo_root=repo, apply=True)
    assert result_for(results, worktree_path).action == "skipped"

    # Clean up dirty file
    (worktree_path / "dirty.txt").unlink()

    # Case 6: branch has open PR
    patch_gh(monkeypatch, {"codex/5102-raisa-fail": [{"number": 42, "state": "OPEN"}]})
    results = rw.reap_worktrees(repo_root=repo, apply=True)
    assert result_for(results, worktree_path).action == "skipped"


def test_class_b_detached_head_removed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    # Add a detached HEAD worktree
    worktree_path = repo / ".worktrees" / "detached-wt"
    git(repo, "worktree", "add", "--detach", str(worktree_path), "main")

    # Set age > 24h
    now = time.time()
    old = now - 25 * 3600
    os.utime(worktree_path, (old, old))

    monkeypatch.setattr(rw, "_active_task_ids", lambda: set())

    # Check it is removed because age > 24h and no matching task
    results = rw.reap_worktrees(repo_root=repo, apply=True, now=now)
    result = result_for(results, worktree_path)
    assert result.action == "removed"
    assert "detached HEAD ancestor of origin/main" in result.reason
    assert "age 25.0h > 24h" in result.reason
    assert not worktree_path.exists()


def test_class_b_settled_task_removed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    # Add detached HEAD under dispatch
    task_id = "detached-task"
    worktree_path = repo / ".worktrees" / "dispatch" / "codex" / task_id
    git(repo, "worktree", "add", "--detach", str(worktree_path), "main")

    # Create task JSON
    tasks_dir = repo / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / f"{task_id}.json").write_text(
        json.dumps({"status": "done"}), encoding="utf-8"
    )

    monkeypatch.setattr(rw, "_active_task_ids", lambda: set())

    # Check it is removed even if age is fresh (e.g. 0h) because task is settled
    results = rw.reap_worktrees(repo_root=repo, apply=True)
    result = result_for(results, worktree_path)
    assert result.action == "removed"
    assert "detached HEAD ancestor of origin/main; settled dispatch task-id=detached-task" in result.reason
    assert not worktree_path.exists()


def test_class_b_fail_safe_skips(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    worktree_path = repo / ".worktrees" / "detached-wt-fail"
    git(repo, "worktree", "add", "--detach", str(worktree_path), "main")

    # Case 1: HEAD is not ancestor of origin/main
    # Create a new commit in the worktree so HEAD is ahead of main (origin/main)
    git(worktree_path, "commit", "--allow-empty", "-m", "new commit")

    now = time.time()
    old = now - 25 * 3600
    os.utime(worktree_path, (old, old))
    monkeypatch.setattr(rw, "_active_task_ids", lambda: set())

    results = rw.reap_worktrees(repo_root=repo, apply=True, now=now)
    assert result_for(results, worktree_path).action == "skipped"


def test_squash_merge_branch_force_delete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    worktree_path = add_worktree(repo, "codex/squash-merged")

    # Commit a change so that the local branch has a commit not in main.
    (worktree_path / "change.txt").write_text("change\n", encoding="utf-8")
    git(worktree_path, "add", "change.txt")
    git(worktree_path, "commit", "-m", "feat: change")

    patch_gh(monkeypatch, {"codex/squash-merged": [{"number": 101, "state": "MERGED"}]})

    # Run reap with prune_merged_branches=True.
    results = rw.reap_worktrees(
        repo_root=repo,
        apply=True,
        prune_merged_branches=True,
    )

    result = result_for(results, worktree_path)
    assert result.action == "removed"
    assert result.branch_pruned is True
    assert not worktree_path.exists()

    # Check that the branch was indeed deleted
    proc = subprocess.run(
        ["git", "branch", "--list", "codex/squash-merged"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert "codex/squash-merged" not in proc.stdout


def test_prune_branch_refuses_branch_checked_out_in_another_worktree(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    branch = "codex/checked-out-during-prune"
    worktree = add_worktree(repo, branch)
    expected_head = git(repo, "rev-parse", branch)

    error = rw._prune_branch(
        repo,
        branch,
        force=True,
        expected_head=expected_head,
    )

    assert error is not None
    assert git(repo, "rev-parse", branch) == expected_head
    assert git(worktree, "branch", "--show-current") == branch


def test_open_pr_matching_origin_is_not_reaped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Open PR worktrees often match origin/<branch>; must stay mounted."""
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "codex/open-pr")
    (worktree / "wip.txt").write_text("wip\n", encoding="utf-8")
    git(worktree, "add", "wip.txt")
    git(worktree, "commit", "-m", "wip")
    git(worktree, "push", "-u", "origin", "codex/open-pr")
    patch_gh(
        monkeypatch,
        {"codex/open-pr": [{"number": 99, "state": "OPEN"}]},
    )

    results = rw.reap_worktrees(repo_root=repo, apply=True)

    result = result_for(results, worktree)
    assert result.action == "skipped"
    assert "no reap condition matched" in (result.reason or "")
    assert worktree.exists()
    assert_main_checkout_unchanged(repo)


def test_open_pr_wins_over_historical_merged_pr(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "codex/reused")
    head = git(worktree, "rev-parse", "HEAD")
    patch_gh(
        monkeypatch,
        {
            "codex/reused": [
                {"number": 8, "state": "MERGED", "headRefOid": head},
                {"number": 9, "state": "OPEN", "headRefOid": head},
            ]
        },
    )

    result = result_for(rw.reap_worktrees(repo_root=repo, apply=True), worktree)

    assert result.action == "skipped"
    assert result.pr == {"number": 9, "state": "OPEN", "head_sha": head}
    assert worktree.exists()


def test_merged_pr_head_must_match_worktree_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "codex/mismatched")
    patch_gh(
        monkeypatch,
        {
            "codex/mismatched": [
                {"number": 10, "state": "MERGED", "headRefOid": "0" * 40}
            ]
        },
    )

    result = result_for(
        rw.reap_worktrees(repo_root=repo, apply=True, safe_only=True),
        worktree,
    )

    assert result.action == "skipped"
    assert worktree.exists()


def test_closed_pr_requires_matching_worktree_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    matching = add_worktree(repo, "codex/closed-matching")
    mismatched = add_worktree(repo, "codex/closed-mismatched")
    patch_gh(
        monkeypatch,
        {
            "codex/closed-matching": [{"number": 12, "state": "CLOSED"}],
            "codex/closed-mismatched": [
                {"number": 13, "state": "CLOSED", "headRefOid": "0" * 40}
            ],
        },
    )

    results = rw.reap_worktrees(
        repo_root=repo,
        apply=True,
        safe_only=True,
        live_cwds=set(),
    )

    assert result_for(results, matching).action == "removed"
    assert result_for(results, mismatched).action == "skipped"
    assert not matching.exists()
    assert mismatched.exists()


def test_live_process_cwd_protects_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "codex/live")
    patch_gh(monkeypatch, {"codex/live": [{"number": 11, "state": "MERGED"}]})

    result = result_for(
        rw.reap_worktrees(
            repo_root=repo,
            apply=True,
            live_cwds={worktree / "site"},
        ),
        worktree,
    )

    assert result.action == "skipped"
    assert result.reason == f"live process cwd={worktree / 'site'}"
    assert worktree.exists()


def test_merged_flag_preserves_dirty_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "codex/merged-flag")
    (worktree / "dirty.txt").write_text("keep\n", encoding="utf-8")
    patch_gh(
        monkeypatch,
        {"codex/merged-flag": [{"number": 7, "state": "MERGED"}]},
    )
    rc = rw.main(["--repo-root", str(repo), "--apply", "--merged"])
    assert rc == 0
    assert worktree.exists()
    assert (worktree / "dirty.txt").read_text(encoding="utf-8") == "keep\n"


def test_apply_cli_requires_process_activity_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    monkeypatch.setattr(rw, "_active_task_ids", lambda: set())
    monkeypatch.setattr(rw, "_live_cwd_paths", lambda _repo: None)

    with pytest.raises(
        RuntimeError,
        match="process-CWD activity probe unavailable",
    ):
        rw.main(["--repo-root", str(repo), "--apply", "--merged"])


def test_reaper_lock_rejects_concurrent_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    monkeypatch.setattr(rw, "_active_task_ids", lambda: set())
    lock_path = rw._common_git_dir(repo) / "worktree-reaper.lock"

    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match="another worktree cleanup holds"):
            rw.reap_worktrees(
                repo_root=repo,
                apply=True,
                live_cwds=set(),
            )
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def test_missing_registered_worktree_is_reported_not_crashed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "codex/missing-registration")
    shutil.rmtree(worktree)
    monkeypatch.setattr(rw, "_active_task_ids", lambda: set())

    result = result_for(
        rw.reap_worktrees(
            repo_root=repo,
            apply=True,
            live_cwds=set(),
        ),
        worktree,
    )

    assert result.action == "skipped"
    assert result.reason == "registered worktree path is missing; run git worktree prune"


def test_merged_flag_does_not_remove_settled_dispatch_without_merged_pr(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    task_id = "settled-without-pr"
    worktree = repo / ".worktrees" / "dispatch" / "codex" / task_id
    add_worktree(repo, "codex/settled-without-pr", path=worktree)
    tasks_dir = repo / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / f"{task_id}.json").write_text(
        json.dumps({"status": "failed"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(rw, "_active_task_ids", lambda: set())
    patch_gh(monkeypatch, {"codex/settled-without-pr": []})

    rc = rw.main(["--repo-root", str(repo), "--apply", "--merged"])

    assert rc == 0
    assert worktree.exists()
