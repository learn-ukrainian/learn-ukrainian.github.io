"""Run the dispatcher code of the primary checkout from any linked worktree."""

import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import NoReturn

from scripts.common.repo_root import configured_interpreter, machinery_path, machinery_root, main_checkout_root

# The dispatcher entry point, relative to a checkout (the machinery package, whatever it is called).
ENTRY = machinery_path("dispatch.py").relative_to(machinery_root().parent)
# The checkout this dispatcher code runs from, read from this file.
RUNTIME_ROOT = Path(__file__).resolve().parents[2]


def _refuse(message: str) -> NoReturn:
    print(f"dispatcher: {message}", file=sys.stderr)
    raise SystemExit(2)


def exec_primary(
    argv: list[str], *, entry: Path = ENTRY, refuse: Callable[[str], NoReturn] = _refuse
) -> None:
    """Replace this process with a primary-checkout entry point from a linked worktree.

    A worktree on an older branch would otherwise supervise tasks with stale dispatcher code.
    The default entry is the dispatcher; other gate CLIs can share this bootstrap.
    The caller's working directory and arguments are kept, so relative paths resolve as before.
    Returns in the primary checkout and in a checkout without Git metadata; exits 2 when a
    linked worktree's primary cannot be resolved. A caller may supply a non-returning
    refusal handler to format the reason itself.

    The primary here is the running code's own primary, read from its Git metadata:
    the configured target primary (``LEARN_UKRAINIAN_PRIMARY_REPO_ROOT``) never
    chooses which dispatcher code runs. The re-exec uses the configured interpreter
    (``LEARN_UKRAINIAN_PYTHON``) when one is set, else this process's interpreter;
    an unusable configured interpreter also exits 2.
    """
    root = RUNTIME_ROOT
    try:
        primary = main_checkout_root(root).resolve()
    except ValueError as exc:  # undecodable metadata, or a NUL in its gitdir target
        refuse(f"cannot resolve the primary checkout of linked worktree {root}: {exc}")
    if primary == root:
        if (root / ".git").is_file():
            refuse(f"cannot resolve the primary checkout of linked worktree {root}")
        return
    entry = primary / entry
    if not entry.is_file():
        refuse(f"primary checkout has no entry point: {entry}")
    try:
        configured = configured_interpreter()
    except ValueError as exc:
        refuse(str(exc))
    if configured is not None and not configured.is_file():
        refuse(f"configured interpreter is not a file: {configured}")
    interpreter = sys.executable if configured is None else str(configured)
    os.execv(interpreter, [interpreter, str(entry), *argv])
