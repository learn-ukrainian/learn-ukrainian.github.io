"""Run the dispatcher code of the primary checkout from any linked worktree."""

import os
import sys
from pathlib import Path

from scripts.common.repo_root import main_checkout_root

ENTRY = Path("scripts/dispatch.py")


def exec_primary(argv: list[str], *, entry: Path = ENTRY) -> None:
    """Replace this process with a primary-checkout entry point from a linked worktree.

    A worktree on an older branch would otherwise supervise tasks with stale dispatcher code.
    The default entry is the dispatcher; other gate CLIs can share this bootstrap.
    The caller's working directory and arguments are kept, so relative paths resolve as before.
    Returns in the primary checkout and in a checkout without Git metadata; exits 2 when a
    linked worktree's primary cannot be resolved.
    """
    root = Path(__file__).resolve().parents[2]
    try:
        primary = main_checkout_root(root).resolve()
    except ValueError as exc:  # undecodable metadata, or a NUL in its gitdir target
        _refuse(f"cannot resolve the primary checkout of linked worktree {root}: {exc}")
    if primary == root:
        if (root / ".git").is_file():
            _refuse(f"cannot resolve the primary checkout of linked worktree {root}")
        return
    entry = primary / entry
    if not entry.is_file():
        _refuse(f"primary checkout has no entry point: {entry}")
    os.execv(sys.executable, [sys.executable, str(entry), *argv])


def _refuse(message: str) -> None:
    print(f"dispatcher: {message}", file=sys.stderr)
    raise SystemExit(2)
