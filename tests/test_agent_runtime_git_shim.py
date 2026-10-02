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
        timeout=30,
    )

@pytest.fixture
def repo_layout(tmp_path: Path):
    main = tmp_path / "main"
    main.mkdir()
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(main)],
        check=True, capture_output=True, text=True, env=_clean_env(),
        timeout=30,
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

def run_git_shim(repo: Path, *args: str, agent_no_merge: bool = True, python_bin: str | None = None):
    repo_root = Path(__file__).resolve().parent.parent
    shim_path = repo_root / "scripts" / "agent_runtime" / "shims" / "git"

    env = _clean_env()
    if agent_no_merge:
        env["AGENT_NO_MERGE"] = "1"
    else:
        env.pop("AGENT_NO_MERGE", None)

    if python_bin is not None:
        env["AGENT_GIT_SHIM_PYTHON"] = python_bin

    # To avoid the shim blocking push due to missing AGENT_REAL_GIT,
    # we can set AGENT_REAL_GIT or let it find it.

    return subprocess.run(
        [str(shim_path), *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=30,
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


@pytest.mark.parametrize("verb,args", [
    ("checkout", ("feature-1",)),
    ("switch", ("feature-1",)),
    ("checkout", ("-b", "new-branch")),
    ("switch", ("-c", "new-branch")),
    ("checkout", ("--", "tracked.txt")),
])
def test_git_shim_fails_closed_when_guard_interpreter_absent(repo_layout, verb, args, tmp_path):
    nonexistent = str(tmp_path / "missing-python")
    proc = run_git_shim(repo_layout.main, verb, *args, python_bin=nonexistent)
    assert proc.returncode == 1
    assert "error: git shim guard interpreter unavailable" in proc.stderr
    assert "Cannot verify branch containment; failing closed." in proc.stderr


def test_git_shim_fails_closed_when_guard_interpreter_fails(repo_layout, tmp_path):
    failing_python = tmp_path / "failing-python"
    failing_python.write_text("#!/usr/bin/env bash\nexit 1\n")
    failing_python.chmod(0o755)
    proc = run_git_shim(repo_layout.main, "checkout", "feature-1", python_bin=str(failing_python))
    assert proc.returncode == 1
    assert "failing closed" in proc.stderr


def test_git_shim_fails_closed_on_fake_interpreter_stdout(repo_layout):
    # A dummy binary like /bin/true that exits 0 but does not output GUARD_ALLOW must fail closed
    proc = run_git_shim(repo_layout.main, "checkout", "feature-1", python_bin="/bin/true")
    assert proc.returncode == 1
    assert "failing closed" in proc.stderr


def test_git_shim_works_when_hosted_in_worktree_without_venv(repo_layout, tmp_path):
    # Simulate a linked worktree hosting the shim without its own .venv
    # It must find the main repo's .venv via git-common-dir and allow switching in dispatch worktree
    # Create mock main repo with .venv/bin/python
    mock_main = tmp_path / "mock_main"
    mock_main.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(mock_main)], check=True, env=_clean_env(), timeout=30)
    _git(mock_main, "config", "user.email", "test@example.com")
    _git(mock_main, "config", "user.name", "Test")
    (mock_main / "file.txt").write_text("ok\n")
    _git(mock_main, "add", "-A")
    _git(mock_main, "commit", "-q", "-m", "init")

    venv_python = mock_main / ".venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    # Symlink project python
    import sys
    venv_python.symlink_to(sys.executable)

    # Symlink scripts package so mock_main has scripts.guardrails
    repo_root = Path(__file__).resolve().parent.parent
    (mock_main / "scripts").symlink_to(repo_root / "scripts")

    # Create linked worktree where the shim lives
    mock_wt = mock_main / ".worktrees" / "dispatch" / "test" / "shim_wt"
    _git(mock_main, "worktree", "add", "-q", "-b", "test/shim_wt", str(mock_wt))

    # Copy shims into this worktree (no .venv here)
    repo_root = Path(__file__).resolve().parent.parent
    real_shim = repo_root / "scripts" / "agent_runtime" / "shims" / "git"
    wt_shim = mock_wt / "scripts" / "agent_runtime" / "shims" / "git"
    wt_shim.parent.mkdir(parents=True)
    wt_shim.write_text(real_shim.read_text())
    wt_shim.chmod(0o755)

    # Add another dispatch worktree to switch in
    target_wt = mock_main / ".worktrees" / "dispatch" / "test" / "target_wt"
    _git(mock_main, "worktree", "add", "-q", "-b", "test/target_wt", str(target_wt))
    _git(mock_main, "branch", "branch-to-switch")

    # Run the worktree-hosted shim from target_wt
    env = _clean_env()
    env["AGENT_NO_MERGE"] = "1"
    env.pop("AGENT_GIT_SHIM_PYTHON", None)

    proc = subprocess.run(
        [str(wt_shim), "checkout", "branch-to-switch"],
        cwd=str(target_wt),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=30,
    )
    assert proc.returncode == 0, f"Expected success, got stderr: {proc.stderr}"
