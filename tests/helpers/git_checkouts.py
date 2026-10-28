"""Hermetic Git repository fixtures shared by orchestration tests."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from scripts.common.git_context import sanitized_git_env


def sanitize_git_env_for_test(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in tuple(os.environ):
        if key.startswith(("GIT_", "PRE_COMMIT")):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("AGENT_NO_MERGE", raising=False)
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    monkeypatch.setenv("GIT_ALLOW_PROTOCOL", "file")


def add_local_bare_origin(main: Path) -> Path:
    remote = main.parent / "origin.git"
    for args in (["clone", "--bare", str(main), str(remote)], ["remote", "add", "origin", str(remote)]):
        subprocess.run(
            ["git", *args], cwd=main, check=True, capture_output=True, text=True,
            env=sanitized_git_env(), timeout=30,
        )
    return remote


def init_repo_with_worktree(tmp_path: Path) -> tuple[Path, Path]:
    env = sanitized_git_env()

    def run(repo: Path, *args: str) -> None:
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, env=env, timeout=30)

    main = tmp_path / "main"
    main.mkdir()
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(main)], check=True, capture_output=True, text=True,
        env=env, timeout=30,
    )
    run(main, "config", "user.email", "test@example.com")
    run(main, "config", "user.name", "Test")
    (main / ".gitignore").write_text(".worktrees/\nlocal_state/\n")
    (main / "tracked.txt").write_text("x\n")
    run(main, "add", "-A")
    run(main, "commit", "-q", "-m", "init")
    run(main, "update-ref", "refs/remotes/origin/main", "HEAD")
    dispatch_wt = main / ".worktrees" / "dispatch" / "codex" / "task-1"
    run(main, "worktree", "add", "-q", "-b", "codex/task-1", str(dispatch_wt))
    return main.resolve(), dispatch_wt.resolve()
