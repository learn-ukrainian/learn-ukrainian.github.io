"""A pushed fix is a delivery even when its ``--base`` branch was deleted (#9451).

The dispatcher counts a write task's commits against the named base ref. A base
branch deleted after it merged left nothing to count against, so a worker that
pushed a real commit settled as ``no_deliverable`` / ``commit_count_unknown``.
The count now falls back to the recorded base commit, then to the default
branch, and still fails closed when neither resolves.

Every test runs in real temporary git repositories (bare origin, clone, linked
dispatch worktree); git is never mocked.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate

BASE_BRANCH = "feat/base"
TASK_BRANCH = "claude/task"
UNREACHABLE_SHA = "0123456789abcdef0123456789abcdef01234567"


@pytest.fixture
def tmp_tasks_dir(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks_dir))
    return tasks_dir


@pytest.fixture(autouse=True)
def _clean_git_env(monkeypatch):
    import os

    for key in tuple(os.environ):
        if key.startswith(("GIT_", "PRE_COMMIT")):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    monkeypatch.setenv("GIT_ALLOW_PROTOCOL", "file")


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True, timeout=30)
    return proc.stdout.strip()


def _commit(cwd: Path, name: str, message: str) -> None:
    (cwd / name).write_text(f"{message}\n", encoding="utf-8")
    _git(cwd, "add", name)
    _git(cwd, "commit", "-q", "-m", message)


class _Repo:
    """A primary clone plus a dispatch worktree branched from a pushed base branch."""

    def __init__(self, primary: Path, worktree: Path, base_sha: str) -> None:
        self.primary = primary
        self.worktree = worktree
        self.base_sha = base_sha

    def delete_base_branch(self, *, merged_into_main: bool) -> None:
        """Delete the base branch everywhere, as after its PR merged."""
        if merged_into_main:
            _git(self.primary, "push", "-q", "origin", f"{self.base_sha}:refs/heads/main")
            _git(self.primary, "fetch", "-q", "origin")
        _git(self.primary, "push", "-q", "origin", "--delete", BASE_BRANCH)
        _git(self.primary, "fetch", "-q", "--prune", "origin")
        _git(self.primary, "branch", "-D", BASE_BRANCH)

    def deliver(self) -> None:
        _commit(self.worktree, "fix.py", "the fix")
        _git(self.worktree, "push", "-q", "origin", TASK_BRANCH)


@pytest.fixture
def repo(tmp_path) -> _Repo:
    origin = tmp_path / "origin.git"
    primary = tmp_path / "primary"
    subprocess.run(["git", "init", "--bare", "-q", "-b", "main", str(origin)], check=True, timeout=30)
    subprocess.run(["git", "init", "-q", "-b", "main", str(primary)], check=True, timeout=30)
    _git(primary, "config", "user.email", "test@example.com")
    _git(primary, "config", "user.name", "Test")
    _git(primary, "remote", "add", "origin", str(origin))
    _commit(primary, "tracked.txt", "initial")
    _git(primary, "push", "-q", "-u", "origin", "main")
    _git(primary, "checkout", "-q", "-b", BASE_BRANCH)
    _commit(primary, "base.txt", "work on the base branch")
    _git(primary, "push", "-q", "-u", "origin", BASE_BRANCH)
    base_sha = _git(primary, "rev-parse", "HEAD")
    _git(primary, "checkout", "-q", "--detach")
    worktree = primary / ".worktrees" / "dispatch" / "claude" / "task"
    _git(primary, "worktree", "add", "-q", "-b", TASK_BRANCH, str(worktree), f"origin/{BASE_BRANCH}")
    _git(worktree, "config", "user.email", "test@example.com")
    _git(worktree, "config", "user.name", "Test")
    _git(worktree, "push", "-q", "-u", "origin", TASK_BRANCH)
    return _Repo(primary.resolve(), worktree.resolve(), base_sha)


def _settle(repo: _Repo, task_id: str, *, base_sha: str | None) -> dict:
    """Run the worker's terminal settle against the real repository; return the state record."""
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(
        state_path,
        {
            "task_id": task_id,
            "agent": "claude",
            "mode": "workspace-write",
            "cwd": str(repo.worktree),
            "worktree_path": str(repo.worktree),
            "worktree_branch": TASK_BRANCH,
            "worktree_base": BASE_BRANCH,
            "worktree_base_sha": base_sha,
            "status": "running",
        },
    )
    result = type(
        "_Result",
        (),
        {
            "ok": True,
            "response": "Finished the task.",
            "stderr_excerpt": None,
            "returncode": 0,
            "rate_limited": False,
            "model": "claude-opus-5-5",
            "effort": "high",
            "cli_version": "1.0.0",
        },
    )()
    with (
        patch.object(delegate, "_REPO_ROOT", repo.primary),
        patch("agent_runtime.runner.invoke", return_value=result),
    ):
        delegate._run_worker(
            task_id=task_id,
            agent="claude",
            prompt="implement the fix",
            mode="workspace-write",
            cwd_str=str(repo.worktree),
            model=None,
            hard_timeout=60,
            effort="high",
        )
    state = delegate._read_state(state_path)
    assert state is not None
    return state


def test_base_present_counts_against_it_unchanged(tmp_tasks_dir, repo):
    repo.deliver()

    state = _settle(repo, "base-present", base_sha=repo.base_sha)

    assert state["status"] == "done"
    assert state["commits_ahead"] == 1
    assert state.get("no_deliverable_reason") is None


def test_base_deleted_recorded_commit_reachable_counts_pushed_fix(tmp_tasks_dir, repo):
    repo.deliver()
    repo.delete_base_branch(merged_into_main=False)

    state = _settle(repo, "base-deleted-recorded", base_sha=repo.base_sha)

    assert state["status"] == "done"
    assert state["commits_ahead"] == 1
    assert state.get("no_deliverable_reason") is None


def test_base_deleted_recorded_commit_unreachable_falls_back_to_default_branch(tmp_tasks_dir, repo):
    repo.deliver()
    repo.delete_base_branch(merged_into_main=True)

    state = _settle(repo, "base-deleted-default", base_sha=UNREACHABLE_SHA)

    assert state["status"] == "done"
    assert state["commits_ahead"] == 1
    assert state.get("no_deliverable_reason") is None


def test_base_deleted_and_nothing_resolvable_fails_closed(tmp_tasks_dir, repo):
    repo.deliver()
    repo.delete_base_branch(merged_into_main=False)
    _git(repo.primary, "update-ref", "-d", "refs/remotes/origin/main")
    _git(repo.primary, "branch", "-D", "main")

    state = _settle(repo, "base-deleted-nothing", base_sha=UNREACHABLE_SHA)

    assert state["status"] == "no_deliverable"
    assert state["no_deliverable_reason"] == "commit_count_unknown"


@pytest.mark.parametrize(
    ("merged_into_main", "recorded"),
    [(False, "reachable"), (True, "unreachable")],
    ids=["recorded-base-commit", "default-branch-merge-base"],
)
def test_base_deleted_with_zero_new_commits_is_not_a_delivery(tmp_tasks_dir, repo, merged_into_main, recorded):
    repo.delete_base_branch(merged_into_main=merged_into_main)
    base_sha = repo.base_sha if recorded == "reachable" else UNREACHABLE_SHA

    state = _settle(repo, f"base-deleted-zero-{recorded}", base_sha=base_sha)

    assert state["status"] == "no_deliverable"
    assert state["no_deliverable_reason"] == "no_commits_no_changes"
    assert state["commits_ahead"] == 0


def test_recorded_commit_that_is_not_an_ancestor_is_not_trusted(repo):
    """A rebased-off base SHA must not inflate the count with commits that are not the worker's."""
    repo.deliver()
    repo.delete_base_branch(merged_into_main=True)
    _git(repo.primary, "checkout", "-q", "--detach", "origin/main")
    _commit(repo.primary, "other.txt", "unrelated commit on another line")
    unrelated = _git(repo.primary, "rev-parse", "HEAD")

    assert delegate._count_commits_ahead(repo.worktree, f"origin/{BASE_BRANCH}", base_sha=unrelated) == 1
