"""Deterministic isolation coverage for primary-root ACP compatibility calls."""

from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.ai_agent_bridge._acp_execution import acp_execution_cwd
from scripts.guardrails.worktree_containment import classify_repo_path


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True, timeout=30,
    )


def test_primary_root_call_uses_and_removes_detached_no_checkout_worktree(
    tmp_path: Path,
) -> None:
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init", "-b", "main")
    _git(primary, "config", "user.name", "ACP Test")
    _git(primary, "config", "user.email", "acp@example.invalid")
    (primary / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    _git(primary, "add", "tracked.txt")
    _git(primary, "commit", "-m", "fixture")

    with acp_execution_cwd(primary, task_id="task-6243") as workspace:
        assert workspace != primary
        assert workspace.is_relative_to(primary / ".worktrees" / "dispatch" / "acp")
        assert classify_repo_path(workspace, cwd=workspace) == "dispatch_worktree"
        assert {item.name for item in workspace.iterdir()} == {".git"}
        listed = _git(primary, "worktree", "list", "--porcelain").stdout
        assert str(workspace) in listed
        assert "locked active ACP execution task-6243" in listed

        _git(primary, "worktree", "prune", "--expire", "now")
        after_prune = _git(primary, "worktree", "list", "--porcelain").stdout
        assert str(workspace) in after_prune
        assert workspace.exists()

    assert not workspace.exists()
    listed = _git(primary, "worktree", "list", "--porcelain").stdout
    assert str(workspace) not in listed
