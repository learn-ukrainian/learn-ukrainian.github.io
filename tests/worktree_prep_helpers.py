"""Shared fixtures for the #8663 worktree-prep ownership proof tests."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from scripts.orchestration import worktree_prep


def _git_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True, env=_git_env())
    return proc.stdout.strip()


def exited_process_identity() -> tuple[int, int]:
    """Return the (pid, start time) of a process, in its own group, that has exited."""
    proc = subprocess.Popen(["sleep", "30"], start_new_session=True)
    try:
        start = worktree_prep.process_identity(proc.pid)["start"]
    finally:
        proc.kill()
        proc.wait()
    assert isinstance(start, int)
    return proc.pid, start


def leave_half_built(worktree: Path, *, drop: tuple[str, ...] = ()) -> None:
    """Turn a finished worktree into what a killed ``git worktree add`` leaves.

    Git still holds its ``initializing`` lock, the index was never written,
    and the files in ``drop`` were never checked out.
    """
    admin = Path(_git(worktree, "rev-parse", "--absolute-git-dir"))
    (admin / "locked").write_text("initializing", encoding="utf-8")
    (admin / "index").unlink(missing_ok=True)
    for name in drop:
        (worktree / name).unlink()


def half_built_prep(worktree: Path, *, run_nonce: str, git: tuple[int, int] | None = None) -> dict[str, Any]:
    """The ``worktree_prep`` dispatch records for its own add at ``worktree``.

    ``git`` is the add's (pid, start); by default one that has exited. The
    dispatcher (``owner``) is this test process, which is alive.
    """
    git_pid, git_start = git if git is not None else exited_process_identity()
    dev, ino = worktree_prep.directory_identity(worktree) or (None, None)
    owner = worktree_prep.process_identity(os.getpid())
    return {
        "path": str(worktree),
        "run_nonce": run_nonce,
        "reserved_by_mkdir": True,
        "reserved_at": "2026-09-24T00:00:00+00:00",
        "dir_dev": dev,
        "dir_ino": ino,
        "base_sha": _git(worktree, "rev-parse", "HEAD"),
        "git_admin_dir": worktree_prep.read_git_admin_dir(worktree) or "",
        "git_pid": git_pid,
        "git_start": git_start,
        "owner_pid": owner["pid"],
        "owner_start": owner["start"],
    }
