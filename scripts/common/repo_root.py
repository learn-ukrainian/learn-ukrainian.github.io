"""Repository root and project-interpreter resolvers."""

from __future__ import annotations

import sys
from pathlib import Path


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


def _is_project_venv_python(path: Path) -> bool:
    """True when ``path`` is a checkout's ``.venv/bin/python`` entrypoint."""
    return path.parts[-3:] == (".venv", "bin", "python")


def project_interpreter(root: Path | None = None) -> Path:
    """Return the project interpreter for ``root`` or this checkout.

    Called when a spawn needs the interpreter, not while this module is
    imported. Import therefore succeeds when no project interpreter can be
    found; this function raises ``FileNotFoundError`` at the call.

    ``main_checkout_root`` follows a worktree ``.git`` gitdir to the shared
    git directory and returns that primary checkout. Its ``.venv/bin/python``
    is the project interpreter. A dispatch worktree has no local virtualenv,
    so the worktree path is not a candidate. When the primary file is missing,
    ``sys.executable`` is accepted only when it is itself a project
    ``.venv/bin/python``. Otherwise this raises ``FileNotFoundError``.
    """
    repo = Path(__file__).resolve().parents[2] if root is None else root
    # Resolver definition: this join is the primary checkout's interpreter.
    primary = main_checkout_root(repo) / ".venv" / "bin" / "python"
    if primary.is_file():
        return primary
    current = Path(sys.executable)
    if current.is_file() and _is_project_venv_python(current):
        return current
    raise FileNotFoundError(
        "project interpreter not found: "
        f"{primary} does not exist and sys.executable ({current}) "
        "is not a project .venv/bin/python"
    )


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
