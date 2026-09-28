"""Repository root and project-interpreter resolvers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_VENV_PYTHON_NAMES = frozenset({"python", "python3"})


def main_checkout_root(repo_root: Path) -> Path:
    """Return the primary checkout root that owns the shared ``.git`` dir.

    Only a ``gitdir:`` target with Git's exact ``.git/worktrees/<name>`` shape
    redirects a path. Primary checkouts, release snapshots, and every other
    malformed or non-Git root remain anchored to themselves.
    """
    git_path = repo_root / ".git"
    if git_path.is_dir():
        return repo_root
    if not git_path.is_file():
        return repo_root

    try:
        first_line = git_path.read_text().splitlines()[0]
    except (IndexError, OSError):
        return repo_root
    prefix = "gitdir:"
    if not first_line.startswith(prefix):
        return repo_root

    git_dir = Path(first_line[len(prefix) :].strip())
    if not git_dir.is_absolute():
        git_dir = repo_root / git_dir
    git_dir = git_dir.resolve()
    if git_dir.parent.name != "worktrees":
        return repo_root
    common_git_dir = git_dir.parent.parent
    if common_git_dir.name != ".git":
        return repo_root
    return common_git_dir.parent


def _lexical_absolute(path: Path) -> Path:
    """Absolute path with ``.`` and ``..`` collapsed, without resolving symlinks."""
    return Path(os.path.normpath(os.fspath(path.absolute())))


def _venv_python(checkout: Path) -> Path:
    """Path of ``checkout``'s project interpreter, whether or not the file exists."""
    # Resolver definition: this join names that checkout's interpreter.
    return checkout / ".venv" / "bin" / "python"


def _venv_checkout_of(interpreter: Path) -> Path | None:
    """Checkout that owns ``interpreter`` when it is that checkout's venv entrypoint.

    ``python`` and ``python3`` under ``<checkout>/.venv/bin`` count. A toolchain
    interpreter such as ``hostedtoolcache/.../bin/python`` does not.
    """
    candidate = _lexical_absolute(interpreter)
    if candidate.name not in _VENV_PYTHON_NAMES or candidate.parent.name != "bin":
        return None
    venv = candidate.parent.parent
    if venv.name != ".venv":
        return None
    return venv.parent


def project_interpreter(root: Path | None = None) -> Path:
    """Return the project interpreter for ``root`` or this checkout.

    Called when a spawn needs the interpreter, not while this module is
    imported. Import therefore succeeds when no project interpreter can be
    found; this function raises ``FileNotFoundError`` at the call.

    Resolution order for the requested checkout:

    1. The primary checkout's ``.venv/bin/python`` when the file exists.
       The primary is the git common-dir checkout ``main_checkout_root``
       finds for a linked worktree, and the checkout itself otherwise.
       Dispatch worktrees share that interpreter even when the worktree
       also has a ``.venv``.
    2. Otherwise that checkout's own ``.venv/bin/python`` when the file exists.
    3. Otherwise ``sys.executable``. This is the CI case: the runner has no
       project ``.venv``. ``sys.executable`` is refused only when it lives in
       some other checkout's ``.venv`` — a foreign project interpreter must
       not be returned for a checkout that asked for its own.
    """
    repo = Path(__file__).resolve().parents[2] if root is None else Path(root)
    primary_root = main_checkout_root(repo)
    primary = _venv_python(primary_root)
    if primary.is_file():
        return primary
    own = _venv_python(repo)
    if primary_root != repo and own.is_file():
        return own
    current = Path(sys.executable)
    owner = _venv_checkout_of(current)
    if owner is not None:
        allowed = {_lexical_absolute(repo), _lexical_absolute(primary_root)}
        if owner not in allowed:
            raise FileNotFoundError(
                "project interpreter not found: "
                f"{primary} does not exist and {own} does not exist and "
                f"sys.executable ({current}) "
                "is not the requested checkout's .venv or its primary checkout's .venv"
            )
    return current


def resolve_repo_root(script_path: Path, parents: int) -> Path:
    """Anchor all dispatch state to the PRIMARY checkout, never a worktree copy.

    Every dispatch worktree carries its own copy of this script; running that
    copy used to anchor batch_state/ and .worktrees/ to the WORKTREE root,
    nesting worktrees and hiding tasks from the Monitor API (#5171).

    Consequence: sys.path inserts and relative-path resolution (e.g. a
    relative --cwd) also anchor to the primary checkout — a worktree copy
    of this script lazy-imports the PRIMARY's scripts/* modules, not the
    worktree branch's. Intentional: dispatch infrastructure is ground truth
    in the primary; cross-cutting changes to delegate.py plus its lazy deps
    must land on main before they steer live dispatches.
    """
    return main_checkout_root(script_path.resolve().parents[parents])
