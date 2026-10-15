"""Explicit positive-path registrations for the real AGY startup gate."""

import json
import os
import subprocess
from pathlib import Path

from scripts.agent_runtime.agy_hook_config import GUARD_NAME, guard_registration


def register_agy_hooks(cwd: Path, *, home: Path | None = None) -> None:
    paths = [cwd / ".agents/hooks.json"]
    if home is not None:
        paths.append(home / ".gemini/config/hooks.json")
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({GUARD_NAME: guard_registration()}), encoding="utf-8")


def _git(repo: Path, *args: str) -> None:
    # A git hook exports GIT_DIR and friends for the repository being pushed;
    # they would redirect these commands away from the throwaway repository.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, env=env, timeout=30)


def linked_dispatch_worktree(parent: Path, *, agent: str = "agy", task: str = "task") -> Path:
    """Create a real primary checkout and a linked worktree at ``.worktrees/dispatch/<agent>/<task>``.

    The AGY installer writes only into such a worktree, so a ``git init``
    primary alone cannot show whether a plan mutates the checkout (#10511).
    """
    primary = parent / "primary"
    primary.mkdir(parents=True)
    _git(primary, "init", "-q", "-b", "main")
    identity = ("-c", "user.name=Test", "-c", "user.email=test@example.invalid")
    _git(primary, *identity, "commit", "-q", "--allow-empty", "-m", "init")
    worktree = primary / ".worktrees" / "dispatch" / agent / task
    _git(primary, "worktree", "add", "-q", "-b", f"{agent}/{task}", str(worktree))
    return worktree


def tree_snapshot(root: Path) -> tuple[tuple[str, str, bytes], ...]:
    """Every path below ``root`` with its kind and bytes (link target for symlinks)."""
    rows: list[tuple[str, str, bytes]] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        base = Path(dirpath)
        for name in (*dirnames, *filenames):
            path = base / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                rows.append((relative, "symlink", os.readlink(path).encode()))
            elif path.is_dir():
                rows.append((relative, "dir", b""))
            else:
                rows.append((relative, "file", path.read_bytes()))
    return tuple(sorted(rows))
