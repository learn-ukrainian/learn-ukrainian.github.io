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

    def advance_main(self) -> str:
        """Land two changes on ``main`` after the base merged; return the tip's SHA.

        The tip has a parent the worker's branch lacks, so cherry-picking it onto the
        worktree yields a new commit (a different SHA) that is only patch-equivalent.
        """
        _git(self.primary, "checkout", "-q", "-B", "main", "origin/main")
        _commit(self.primary, "landed-first.txt", "an earlier change on main")
        _commit(self.primary, "landed.txt", "a change already on main")
        landed = _git(self.primary, "rev-parse", "HEAD")
        _git(self.primary, "push", "-q", "origin", "main")
        _git(self.primary, "fetch", "-q", "origin")
        _git(self.primary, "checkout", "-q", "--detach")
        return landed

    def push_task_branch(self) -> None:
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


# --- the default-branch fallback counts only real new changes (#9451) -------------
#
# ``origin/main..HEAD`` is a proxy for the lost base, and it overcounts: a merge of
# main, a cherry-pick of a change main already has, or a squash of work main already
# holds is "ahead" yet delivers nothing. The fallback asks git whether merging HEAD
# into main would change main's tree. Each shape below is a real worker end-state
# settled through ``_run_worker``.


def _cherry_pick_landed(repo: _Repo, landed: str) -> None:
    _git(repo.worktree, "cherry-pick", landed)


def _merge_main(repo: _Repo, landed: str) -> None:
    _git(repo.worktree, "merge", "-q", "--no-ff", "--no-edit", landed)


def _merge_main_then_fix(repo: _Repo, landed: str) -> None:
    _merge_main(repo, landed)
    _commit(repo.worktree, "fix.py", "the fix")


def _fix_then_merge_main(repo: _Repo, landed: str) -> None:
    _commit(repo.worktree, "fix.py", "the fix")
    _merge_main(repo, landed)


def _cherry_pick_then_fix(repo: _Repo, landed: str) -> None:
    _cherry_pick_landed(repo, landed)
    _commit(repo.worktree, "fix.py", "the fix")


def _merge_main_then_revert(repo: _Repo, landed: str) -> None:
    _merge_main(repo, landed)
    _git(repo.worktree, "revert", "--no-edit", landed)


def _empty_commit(repo: _Repo, landed: str) -> None:
    _git(repo.worktree, "commit", "-q", "--allow-empty", "-m", "nothing changed")


def _cherry_pick_all_of_main(repo: _Repo, landed: str) -> None:
    _git(repo.worktree, "cherry-pick", "--keep-redundant-commits", f"{repo.base_sha}..{landed}")


def _empty_commit_then_cherry_pick_all_of_main(repo: _Repo, landed: str) -> None:
    _empty_commit(repo, landed)
    _cherry_pick_all_of_main(repo, landed)


def _two_commits_squashing_main(repo: _Repo, landed: str) -> None:
    """Both patches differ from main's, yet together they rebuild exactly main's tree."""
    (repo.worktree / "landed-first.txt").write_text("an earlier change on main\n", encoding="utf-8")
    (repo.worktree / "landed.txt").write_text("a first draft\n", encoding="utf-8")
    _git(repo.worktree, "add", "landed-first.txt", "landed.txt")
    _git(repo.worktree, "commit", "-q", "-m", "most of main's change")
    _commit(repo.worktree, "landed.txt", "a change already on main")


def _three_commits_squashing_main(repo: _Repo, landed: str) -> None:
    _commit(repo.worktree, "landed-first.txt", "a first attempt")
    _commit(repo.worktree, "landed-first.txt", "an earlier change on main")
    _commit(repo.worktree, "landed.txt", "a change already on main")


def _new_commit(repo: _Repo, landed: str) -> None:
    _commit(repo.worktree, "fix.py", "the fix")


def _new_commit_that_conflicts_with_main(repo: _Repo, landed: str) -> None:
    _commit(repo.worktree, "landed.txt", "the worker's own take on the same file")


def _settle_after(repo: _Repo, task_id: str, work, *, base_sha: str | None) -> dict:
    repo.delete_base_branch(merged_into_main=True)
    landed = repo.advance_main()
    work(repo, landed)
    repo.push_task_branch()
    return _settle(repo, task_id, base_sha=base_sha)


@pytest.mark.parametrize(
    "work",
    [
        _cherry_pick_landed,
        _merge_main,
        _empty_commit,
        _empty_commit_then_cherry_pick_all_of_main,
        _two_commits_squashing_main,
        _three_commits_squashing_main,
    ],
    ids=[
        "cherry-pick-of-a-change-on-main",
        "merge-of-current-main",
        "empty-commit",
        "empty-commit-then-cherry-pick-of-main",
        "two-commits-squashing-main",
        "three-commits-squashing-main",
    ],
)
def test_default_branch_fallback_does_not_count_no_op_work_as_a_delivery(tmp_tasks_dir, repo, work):
    state = _settle_after(repo, f"noop-{work.__name__}", work, base_sha=None)

    assert state["status"] == "no_deliverable"
    assert state["no_deliverable_reason"] == "no_commits_no_changes"
    assert state["commits_ahead"] == 0


@pytest.mark.parametrize(
    ("work", "real_commits"),
    [
        (_new_commit, 1),
        (_new_commit_that_conflicts_with_main, 1),
        (_merge_main_then_fix, 2),
        (_fix_then_merge_main, 2),
        (_cherry_pick_then_fix, 2),
        (_merge_main_then_revert, 2),
    ],
    ids=[
        "new-commit",
        "new-commit-that-conflicts-with-main",
        "new-commit-on-top-of-merged-main",
        "new-commit-plus-merge-of-main",
        "cherry-pick-plus-new-commit",
        "revert-of-a-commit-on-main",
    ],
)
def test_default_branch_fallback_counts_real_commits_next_to_no_op_ones(tmp_tasks_dir, repo, work, real_commits):
    state = _settle_after(repo, f"real-{work.__name__}", work, base_sha=None)

    assert state["status"] == "done"
    assert state["commits_ahead"] == real_commits
    assert state.get("no_deliverable_reason") is None


@pytest.mark.parametrize(
    ("work", "expected_status", "expected_ahead"),
    [
        (_cherry_pick_landed, "done", 1),
        (_merge_main, "done", 3),
        (_empty_commit, "done", 1),
    ],
    ids=["cherry-pick", "merge-of-main", "empty-commit"],
)
def test_recorded_commit_count_stays_exact_for_the_same_shapes(
    tmp_tasks_dir, repo, work, expected_status, expected_ahead
):
    """The recorded commit is where the worktree started, so ``<sha>..HEAD`` is exact: unchanged."""
    state = _settle_after(repo, f"recorded-{work.__name__}", work, base_sha=repo.base_sha)

    assert state["status"] == expected_status
    assert state["commits_ahead"] == expected_ahead


def test_default_branch_fallback_fails_closed_when_the_merge_cannot_be_computed(tmp_tasks_dir, repo):
    repo.deliver()
    repo.delete_base_branch(merged_into_main=True)

    real_run = delegate._run_git_stdout

    def broken_merge_tree(worktree, *args):
        return (129, "") if args and args[0] == "merge-tree" else real_run(worktree, *args)

    with patch.object(delegate, "_run_git_stdout", broken_merge_tree):
        state = _settle(repo, "merge-unknown", base_sha=None)

    assert state["status"] == "no_deliverable"
    assert state["no_deliverable_reason"] == "commit_count_unknown"
