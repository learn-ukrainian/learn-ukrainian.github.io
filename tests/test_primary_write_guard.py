from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

# Add repo root to sys.path to resolve imports
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.guardrails import primary_write_guard as pwg

_GIT_ENV = {
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
    "GIT_CEILING_DIRECTORIES",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_COMMON_DIR",
}


def _clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in _GIT_ENV}


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=_clean_env(),
    )


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> dict[str, Path]:
    """Sets up a primary git repository and a clone for pulling."""
    main_dir = tmp_path / "main"
    main_dir.mkdir()
    _git(main_dir, "init", "-q", "-b", "main")
    _git(main_dir, "config", "user.email", "test@example.com")
    _git(main_dir, "config", "user.name", "Test User")

    # Create tracked files
    (main_dir / "a.txt").write_text("Hello A\n", encoding="utf-8")
    (main_dir / "b.txt").write_text("Hello B\n", encoding="utf-8")

    # Create UTF-8 filename and file with spaces in name to verify handling
    (main_dir / "українська книга.txt").write_text("Ukrainian Book\n", encoding="utf-8")
    (main_dir / "space file.txt").write_text("Space File\n", encoding="utf-8")

    # Create gitignore
    (main_dir / ".gitignore").write_text("*.local\nignored_dir/\n", encoding="utf-8")

    _git(main_dir, "add", "a.txt", "b.txt", "українська книга.txt", "space file.txt", ".gitignore")
    _git(main_dir, "commit", "-q", "-m", "Initial commit")

    # Setup worktree (needs directories created manually first)
    (main_dir / ".worktrees" / "dispatch").mkdir(parents=True, exist_ok=True)
    _git(main_dir, "worktree", "add", "-q", ".worktrees/dispatch/task1", "-b", "task1-branch")

    # Setup a separate cloned repo to simulate pull
    clone_dir = tmp_path / "clone"
    _git(tmp_path, "clone", "-q", str(main_dir), "clone")
    _git(clone_dir, "config", "user.email", "clone@example.com")
    _git(clone_dir, "config", "user.name", "Clone User")

    return {
        "main": main_dir,
        "clone": clone_dir,
        "worktree": main_dir / ".worktrees" / "dispatch" / "task1",
    }


def test_apply_protects_tracked_files(temp_git_repo, monkeypatch):
    main_dir = temp_git_repo["main"]
    monkeypatch.chdir(main_dir)

    # Apply guard
    pwg.apply_guard(hook_mode=False)

    # Trying to write to tracked file should raise PermissionError
    a_file = main_dir / "a.txt"
    with pytest.raises(PermissionError):
        a_file.write_text("Modified\n", encoding="utf-8")

    # Writing to untracked file should succeed
    untracked_file = main_dir / "untracked.txt"
    untracked_file.write_text("Untracked content\n", encoding="utf-8")
    assert untracked_file.read_text(encoding="utf-8") == "Untracked content\n"

    # Writing to gitignored file should succeed
    ignored_file = main_dir / "test.local"
    ignored_file.write_text("Ignored content\n", encoding="utf-8")
    assert ignored_file.read_text(encoding="utf-8") == "Ignored content\n"


def test_idempotent_release_and_status(temp_git_repo, monkeypatch, capsys):
    main_dir = temp_git_repo["main"]
    monkeypatch.chdir(main_dir)

    # Initial state should be OFF
    pwg.status_guard()
    out, _ = capsys.readouterr()
    assert "OFF" in out

    # pwg.check_guard() should raise SystemExit(1)
    with pytest.raises(SystemExit) as excinfo:
        pwg.check_guard()
    assert excinfo.value.code == 1

    # Apply guard
    pwg.apply_guard(hook_mode=False)

    # Status should be ON
    pwg.status_guard()
    out, _ = capsys.readouterr()
    assert "ON" in out
    assert "0 writable tracked files" in out

    # check_guard should pass with exit code 0
    with pytest.raises(SystemExit) as excinfo:
        pwg.check_guard()
    assert excinfo.value.code == 0

    # Apply again (idempotent)
    pwg.apply_guard(hook_mode=False)

    # Status still ON
    pwg.status_guard()
    out, _ = capsys.readouterr()
    assert "ON" in out

    # Release guard
    pwg.release_guard()
    out, _ = capsys.readouterr()
    assert "Guard released" in out

    # Status should be OFF
    pwg.status_guard()
    out, _ = capsys.readouterr()
    assert "OFF" in out
    assert "5 writable tracked files" in out

    # check_guard should exit with 1
    with pytest.raises(SystemExit) as excinfo:
        pwg.check_guard()
    assert excinfo.value.code == 1


def test_git_pull_with_guard_on(temp_git_repo, monkeypatch):
    main_dir = temp_git_repo["main"]
    clone_dir = temp_git_repo["clone"]

    # 1. Apply guard in clone_dir
    monkeypatch.chdir(clone_dir)
    pwg.apply_guard(hook_mode=False)

    # Verify files in clone are read-only
    with pytest.raises(PermissionError):
        (clone_dir / "a.txt").write_text("Try write", encoding="utf-8")

    # 2. Modify a.txt in main_dir and commit
    (main_dir / "a.txt").write_text("Hello A modified\n", encoding="utf-8")
    _git(main_dir, "add", "a.txt")
    _git(main_dir, "commit", "-q", "-m", "Modify a.txt in main")

    # 3. Pull in clone_dir. Pull should succeed despite files being read-only.
    _git(clone_dir, "pull", "--ff-only")

    # Pull should succeed and update a.txt content
    assert (clone_dir / "a.txt").read_text(encoding="utf-8") == "Hello A modified\n"

    # Simulate post-merge hook
    pwg.apply_guard(hook_mode=True)

    # Verify that a.txt is read-only again
    with pytest.raises(PermissionError):
        (clone_dir / "a.txt").write_text("Try write again", encoding="utf-8")


def test_apply_refuses_outside_primary_root(temp_git_repo, monkeypatch):
    main_dir = temp_git_repo["main"]
    worktree_dir = temp_git_repo["worktree"]

    # 1. From a subdirectory of main_dir
    subdir = main_dir / "subdir"
    subdir.mkdir(exist_ok=True)
    monkeypatch.chdir(subdir)
    with pytest.raises(SystemExit) as excinfo:
        pwg.apply_guard(hook_mode=False)
    assert excinfo.value.code == 1

    # 2. From a worktree
    monkeypatch.chdir(worktree_dir)
    with pytest.raises(SystemExit) as excinfo:
        pwg.apply_guard(hook_mode=False)
    assert excinfo.value.code == 1

    # With hook mode inside worktree it should exit 0 silently
    with pytest.raises(SystemExit) as excinfo:
        pwg.apply_guard(hook_mode=True)
    assert excinfo.value.code == 0


def test_unusual_filenames_handled(temp_git_repo, monkeypatch):
    main_dir = temp_git_repo["main"]
    monkeypatch.chdir(main_dir)

    pwg.apply_guard(hook_mode=False)

    utf8_file = main_dir / "українська книга.txt"
    space_file = main_dir / "space file.txt"

    with pytest.raises(PermissionError):
        utf8_file.write_text("trying write", encoding="utf-8")

    with pytest.raises(PermissionError):
        space_file.write_text("trying write", encoding="utf-8")

    pwg.release_guard()

    utf8_file.write_text("Ukrainian Book modified\n", encoding="utf-8")
    space_file.write_text("Space File modified\n", encoding="utf-8")

    assert utf8_file.read_text(encoding="utf-8") == "Ukrainian Book modified\n"
    assert space_file.read_text(encoding="utf-8") == "Space File modified\n"


def test_install_hooks(temp_git_repo, monkeypatch):
    main_dir = temp_git_repo["main"]
    monkeypatch.chdir(main_dir)

    pwg.install_hooks()

    hooks_dir = main_dir / ".git" / "hooks"
    for hook_name in ["post-merge", "post-checkout", "post-commit"]:
        hook_path = hooks_dir / hook_name
        assert hook_path.exists()
        content = hook_path.read_text(encoding="utf-8")
        assert "# AGY_PRIMARY_WRITE_GUARD_START" in content
        assert "primary_write_guard.py apply --hook" in content
        assert os.access(hook_path, os.X_OK)
