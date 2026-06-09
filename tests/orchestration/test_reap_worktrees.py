from __future__ import annotations

import json
import os
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
        if not key.startswith("GIT_") and not key.startswith("PRE_COMMIT")
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
            payload = states_by_branch.get(branch, [])
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
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "codex/dirty")
    (worktree / "dirty.txt").write_text("not committed\n", encoding="utf-8")
    patch_gh(monkeypatch, {"codex/dirty": [{"number": 13, "state": "MERGED"}]})

    results = rw.reap_worktrees(repo_root=repo, apply=True)

    result = result_for(results, worktree)
    assert result.action == "skipped"
    assert "dirty; qualifies for reap because PR #13 MERGED" in result.reason
    assert worktree.exists()
    assert git(worktree, "status", "--porcelain")
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
