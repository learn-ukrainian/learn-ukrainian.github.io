"""Tests for _review_safety subprocess timeout handling."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from scripts.ai_agent_bridge import _review_safety as safety


def test_primary_checkout_root_passes_timeout(tmp_path: Path) -> None:
    fake = subprocess.CompletedProcess(["git"], 0, stdout="/path/to/.git\n")
    with patch("subprocess.run", return_value=fake) as mock_run:
        res = safety.primary_checkout_root(tmp_path)
    assert res == Path("/path/to")
    assert mock_run.call_args.kwargs.get("timeout") == safety.DEFAULT_GIT_TIMEOUT_SECONDS


def test_primary_checkout_root_rev_parse_timeout_returns_root(tmp_path: Path) -> None:
    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git", "rev-parse"], safety.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        res = safety.primary_checkout_root(tmp_path)
    assert res == tmp_path.resolve()


def test_primary_checkout_root_worktree_list_timeout_returns_root(tmp_path: Path) -> None:
    def fake_run(cmd, **kwargs):
        if "rev-parse" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="/path/to/main/.git/worktrees/wt\n")
        if "worktree" in cmd:
            raise subprocess.TimeoutExpired(cmd, safety.DEFAULT_GIT_TIMEOUT_SECONDS)
        raise AssertionError(f"unexpected cmd: {cmd}")

    with patch("subprocess.run", side_effect=fake_run):
        res = safety.primary_checkout_root(tmp_path)
    assert res == tmp_path.resolve()


def test_list_repo_worktree_paths_passes_timeout(tmp_path: Path) -> None:
    fake = subprocess.CompletedProcess(
        ["git"], 0, stdout=f"worktree {tmp_path.resolve()}\nHEAD deadbeef\nbranch refs/heads/main\n"
    )
    with patch("subprocess.run", return_value=fake) as mock_run:
        res = safety.list_repo_worktree_paths(tmp_path)
    assert res == frozenset({tmp_path.resolve()})
    assert mock_run.call_args.kwargs.get("timeout") == safety.DEFAULT_GIT_TIMEOUT_SECONDS


def test_list_repo_worktree_paths_timeout_returns_frozenset_root(tmp_path: Path) -> None:
    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git", "worktree"], safety.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        res = safety.list_repo_worktree_paths(tmp_path)
    assert res == frozenset({tmp_path.resolve()})
