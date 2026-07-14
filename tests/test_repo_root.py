"""Unit and integration tests for repository root resolver and primary checkout anchoring."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.common.repo_root import main_checkout_root, resolve_repo_root


def test_main_checkout_root_resolves_primary_checkout_from_worktree(tmp_path):
    """Verify that main_checkout_root correctly identifies primary repo root from a worktree."""
    main_repo = tmp_path / "main"
    worktree = main_repo / ".worktrees" / "dispatch" / "agy" / "task-123"
    git_dir = main_repo / ".git" / "worktrees" / "task-123"

    git_dir.mkdir(parents=True)
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {git_dir}\n")

    assert main_checkout_root(worktree) == main_repo


def test_main_checkout_root_is_identity_in_primary_checkout(tmp_path):
    """Verify that main_checkout_root is an identity function in a primary checkout."""
    main_repo = tmp_path / "main"
    (main_repo / ".git").mkdir(parents=True)

    assert main_checkout_root(main_repo) == main_repo


def test_resolve_repo_root_generalized_depths(tmp_path):
    """Verify resolve_repo_root with different parents/depth levels."""
    main_repo = tmp_path / "main"
    worktree = main_repo / ".worktrees" / "dispatch" / "agy" / "task-123"
    git_dir = main_repo / ".git" / "worktrees" / "task-123"

    git_dir.mkdir(parents=True)
    (worktree / "scripts" / "ai_agent_bridge").mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {git_dir}\n")

    # depth = 1 (scripts/delegate.py)
    dummy_delegate = worktree / "scripts" / "delegate.py"
    assert resolve_repo_root(dummy_delegate, 1) == main_repo

    # depth = 2 (scripts/ai_agent_bridge/_config.py)
    dummy_config = worktree / "scripts" / "ai_agent_bridge" / "_config.py"
    assert resolve_repo_root(dummy_config, 2) == main_repo


@pytest.fixture
def wt_layout(tmp_path) -> tuple[Path, Path]:
    """Sets up a mock primary repo and a mock worktree layout.

    Returns a tuple of (mock_primary_root, mock_worktree_root).
    """
    main_repo = tmp_path / "main"
    worktree = main_repo / ".worktrees" / "dispatch" / "agy" / "task-123"
    git_dir = main_repo / ".git" / "worktrees" / "task-123"

    git_dir.mkdir(parents=True)
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {git_dir}\n")

    # Copy the bridge and common module code files to the mock worktree
    src_root = Path(__file__).resolve().parents[1]

    # Create empty init for the bridge package to avoid loading other bridge modules
    bridge_init = worktree / "scripts" / "ai_agent_bridge" / "__init__.py"
    bridge_init.parent.mkdir(parents=True, exist_ok=True)
    bridge_init.write_text("", encoding="utf-8")

    files_to_copy = [
        "scripts/common/__init__.py",
        "scripts/common/repo_root.py",
        "scripts/ai_agent_bridge/_config.py",
        "scripts/ai_agent_bridge/_env.py",
        "scripts/ai_agent_bridge/_dispatch_wrappers.py",
        "scripts/ai_agent_bridge/_monitor_cache.py",
    ]
    for f in files_to_copy:
        dest = worktree / f
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text((src_root / f).read_text(encoding="utf-8"), encoding="utf-8")

    return main_repo, worktree


def test_bridge_config_state_paths_resolve_to_primary_in_worktree(wt_layout):
    """Verify that importing _config.py from a worktree layout resolves state paths to the primary root."""
    main_repo, worktree = wt_layout

    # Run subprocess to check DB_PATH and PID_DIR
    script = (
        "from scripts.ai_agent_bridge._config import DB_PATH, PID_DIR; "
        "print(f'{DB_PATH};{PID_DIR}')"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(worktree),
        capture_output=True,
        text=True,
        check=True,
    )
    db_path_str, pid_dir_str = proc.stdout.strip().split(";")

    expected_db_path = main_repo / ".mcp" / "servers" / "message-broker" / "messages.db"
    expected_pid_dir = main_repo / ".mcp" / "servers" / "message-broker" / "pids"

    assert Path(db_path_str).resolve() == expected_db_path.resolve()
    assert Path(pid_dir_str).resolve() == expected_pid_dir.resolve()


def test_bridge_dispatch_wrappers_repo_root_resolves_to_primary_in_worktree(wt_layout):
    """Verify that importing _dispatch_wrappers.py from a worktree layout resolves REPO_ROOT to primary."""
    main_repo, worktree = wt_layout

    script = "from scripts.ai_agent_bridge._dispatch_wrappers import REPO_ROOT; print(REPO_ROOT)"
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(worktree),
        capture_output=True,
        text=True,
        check=True,
    )
    resolved_repo_root = Path(proc.stdout.strip())
    assert resolved_repo_root.resolve() == main_repo.resolve()


def test_bridge_monitor_cache_project_root_resolves_to_primary_in_worktree(wt_layout):
    """Verify that importing _monitor_cache.py from a worktree layout resolves _PROJECT_ROOT to primary."""
    main_repo, worktree = wt_layout

    script = "from scripts.ai_agent_bridge._monitor_cache import _PROJECT_ROOT; print(_PROJECT_ROOT)"
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(worktree),
        capture_output=True,
        text=True,
        check=True,
    )
    resolved_project_root = Path(proc.stdout.strip())
    assert resolved_project_root.resolve() == main_repo.resolve()
