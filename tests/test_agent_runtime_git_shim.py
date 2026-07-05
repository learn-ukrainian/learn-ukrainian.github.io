import os
import subprocess
from pathlib import Path

import pytest

from scripts.guardrails import worktree_containment as wc


def _clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in wc._GIT_ENV_DENYLIST}

def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, capture_output=True, text=True, env=_clean_env(),
    )

@pytest.fixture
def repo_layout(tmp_path: Path):
    main = tmp_path / "main"
    main.mkdir()
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(main)],
        check=True, capture_output=True, text=True, env=_clean_env(),
    )
    _git(main, "config", "user.email", "test@example.com")
    _git(main, "config", "user.name", "Test")

    # Tracked content + gitignore rules covering runtime/local state.
    (main / ".gitignore").write_text(".worktrees/\nbuild/\n*.log\nlocal_state/\n")
    (main / "tracked.txt").write_text("tracked\n")
    (main / "pkg").mkdir()
    (main / "pkg" / "module.py").write_text("x = 1\n")
    _git(main, "add", "-A")
    _git(main, "commit", "-q", "-m", "init")

    # create some branches
    _git(main, "branch", "feature-1")
    _git(main, "branch", "feature-2")

    # add a dispatch worktree
    dispatch_wt = main / ".worktrees" / "dispatch" / "agy" / "task-1"
    _git(main, "worktree", "add", "-q", "-b", "agy/task-1", str(dispatch_wt))

    class Layout:
        def __init__(self):
            self.main = wc.canonicalize(main)
            self.dispatch_wt = wc.canonicalize(dispatch_wt)

    return Layout()

def run_git_shim(repo: Path, *args: str, agent_no_merge: bool = True):
    repo_root = Path(__file__).resolve().parent.parent
    shim_path = repo_root / "scripts" / "agent_runtime" / "shims" / "git"

    env = _clean_env()
    if agent_no_merge:
        env["AGENT_NO_MERGE"] = "1"
    else:
        env.pop("AGENT_NO_MERGE", None)

    # To avoid the shim blocking push due to missing AGENT_REAL_GIT,
    # we can set AGENT_REAL_GIT or let it find it.

    return subprocess.run(
        [str(shim_path), *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env=env,
        check=False
    )

def test_git_shim_blocks_branch_switch_in_main(repo_layout):
    # Checking out a branch in main (protected) should be blocked
    proc = run_git_shim(repo_layout.main, "checkout", "feature-1")
    assert proc.returncode == 1
    assert "agent cannot switch branches in the primary checkout" in proc.stderr

    proc = run_git_shim(repo_layout.main, "switch", "feature-1")
    assert proc.returncode == 1

    proc = run_git_shim(repo_layout.main, "checkout", "-b", "new-branch")
    assert proc.returncode == 1

    proc = run_git_shim(repo_layout.main, "switch", "-c", "new-branch")
    assert proc.returncode == 1

def test_git_shim_allows_file_checkout(repo_layout):
    # Checking out a file in main should be allowed
    proc = run_git_shim(repo_layout.main, "checkout", "--", "tracked.txt")
    assert proc.returncode == 0

    proc = run_git_shim(repo_layout.main, "checkout", "feature-1", "--", "tracked.txt")
    assert proc.returncode == 0

def test_git_shim_allows_branch_switch_in_worktree(repo_layout):
    # Checking out a branch in worktree should be allowed
    proc = run_git_shim(repo_layout.dispatch_wt, "checkout", "feature-2")
    assert proc.returncode == 0

def test_git_shim_allows_worktree_add(repo_layout):
    proc = run_git_shim(repo_layout.main, "worktree", "add", "-b", "new-wt-branch", ".worktrees/dispatch/test/1")
    assert proc.returncode == 0

def test_git_shim_allows_read_only(repo_layout):
    proc = run_git_shim(repo_layout.main, "status")
    assert proc.returncode == 0

    proc = run_git_shim(repo_layout.main, "log")
    assert proc.returncode == 0

def test_git_shim_human_operator_unaffected(repo_layout):
    # When AGENT_NO_MERGE=1 is not set, block should not occur
    proc = run_git_shim(repo_layout.main, "checkout", "feature-1", agent_no_merge=False)
    assert proc.returncode == 0
