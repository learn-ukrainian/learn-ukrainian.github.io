"""Tests for the #5803-follow-up primary-integrity wiring in scripts/delegate.py.

- pre-dispatch gate: unrepaired primary drift blocks NEW write-capable
  dispatches (running ones are never touched)
- instructive fetch failure: no silent fallback to a stale local base
- worktree prompt tells workers to fetch from origin INSIDE the worktree
- GIT_CEILING_DIRECTORIES damage-reduction env for worker spawns
- #7522: the dispatch base SHA is pinned to the canonical GitHub remote,
  never to a lagging host-mirror origin
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


_GIT_REDIRECT = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_PREFIX",
    }
)


def _clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in _GIT_REDIRECT}


def _git(repo: Path, *args: str, check: bool = True, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=check,
        env=env or _clean_env(),
        timeout=30,
    )


def _init_repo(path: Path) -> Path:
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(path)],
        check=True,
        env=_clean_env(),
        timeout=30,
    )
    _git(path, "config", "user.email", "gate-test@example.com")
    _git(path, "config", "user.name", "gate-test")
    # Mirror the real repo's .gitignore so the watchdog's own state/log files
    # under data/telemetry/ (and dispatch state under batch_state/) do not
    # count as primary-checkout dirt.
    (path / ".gitignore").write_text("data/telemetry/\nbatch_state/\n.worktrees/\n")
    (path / "README.md").write_text("fixture\n")
    _git(path, "add", ".gitignore", "README.md")
    _git(path, "commit", "-q", "-m", "init")
    return path


# ---------------------------------------------------------------------------
# pre-dispatch gate
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# instructive fetch failure (no silent stale-base fallback)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# canonical GitHub base remote (#7522)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# worktree prompt removes the workflow reason to visit the primary
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# GIT_CEILING_DIRECTORIES damage reduction
# ---------------------------------------------------------------------------


def test_git_ceiling_keeps_linked_worktree_ops_working(tmp_path):
    """Integration proof for the comment in _apply_worktree_git_ceiling: with
    the ceiling at the worktree PARENT, git from the worktree root AND from a
    subdirectory still resolves the worktree's own repo."""
    repo = _init_repo(tmp_path / "primary")
    worktree = tmp_path / "dispatch" / "codex" / "task-1"
    worktree.parent.mkdir(parents=True)
    _git(repo, "worktree", "add", "-q", "-b", "codex/task-1", str(worktree))
    (worktree / "sub").mkdir()

    env = _clean_env()
    env["GIT_CEILING_DIRECTORIES"] = str(worktree.parent)

    top = _git(worktree, "rev-parse", "--show-toplevel", env=env)
    assert top.stdout.strip() == str(worktree)
    sub = _git(worktree / "sub", "rev-parse", "--show-toplevel", env=env)
    assert sub.stdout.strip() == str(worktree)
    # status works from a subdirectory too.
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=worktree / "sub",
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert status.returncode == 0


def test_git_ceiling_blocks_upward_discovery_to_primary(tmp_path):
    """If the worktree's .git pointer is gone, upward discovery must stop at
    the ceiling instead of silently binding to an ancestor repo."""
    repo = _init_repo(tmp_path / "primary")
    nested = repo / ".worktrees" / "dispatch" / "codex" / "task-1"
    nested.mkdir(parents=True)  # plain dir INSIDE the primary, no .git pointer

    env = _clean_env()
    env["GIT_CEILING_DIRECTORIES"] = str(nested.parent)
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=nested,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert proc.returncode != 0  # fails loudly…
    # …instead of discovering the primary checkout.
    assert str(repo) not in proc.stdout
