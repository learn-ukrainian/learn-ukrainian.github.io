"""Repository root and project-interpreter resolvers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Directory and final-component symlink hops followed while identifying a venv
# entrypoint. POSIX SYMLOOP_MAX is commonly 40; longer chains fail closed.
_MAX_SYMLINK_HOPS = 40


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


def _absolute_text(path: Path) -> str:
    text = os.fspath(path)
    if os.path.isabs(text):
        return text
    return os.path.join(os.getcwd(), text)


def _lexical_absolute(path: Path) -> Path:
    """Absolute path with ``.`` and ``..`` collapsed, without resolving symlinks."""
    return Path(os.path.normpath(_absolute_text(path)))


def _realpath(path: Path) -> Path:
    """``os.path.realpath`` of ``path``, or a normalized absolute path if that fails."""
    text = _absolute_text(path)
    try:
        resolved = os.path.realpath(text)
    except OSError:
        resolved = os.path.normpath(text)
    return Path(resolved)


def _symlink_target(path: Path) -> Path | None:
    """Target of ``path`` when it is a symlink, else ``None``.

    A path that cannot be inspected (``PermissionError`` and other
    ``OSError``s, or a link replaced between the check and the read) raises
    ``FileNotFoundError`` so callers see the named refusal they handle
    instead of an uncaught error or a silently accepted interpreter.
    """
    try:
        if not path.is_symlink():
            return None
        return path.readlink()
    except OSError as exc:
        raise FileNotFoundError(f"project interpreter path cannot be inspected: {path}: {exc}") from exc


def _first_parent_symlink_hop(parent: Path) -> Path | None:
    """Expand the first directory symlink in an absolute parent path, if any.

    Keep the remaining components for the next pass so every intermediate
    ``<checkout>/.venv/bin`` view is classified before another hop is taken.
    """
    prefix = Path(parent.anchor)
    for index, part in enumerate(parent.parts[1:], start=1):
        if part == "..":
            prefix = prefix.parent
            continue
        next_path = prefix / part
        target = _symlink_target(next_path)
        if target is not None:
            if not target.is_absolute():
                target = prefix / target
            return target.joinpath(*parent.parts[index + 1 :])
        prefix = next_path
    return None


def _venv_python(checkout: Path) -> Path:
    """Path of ``checkout``'s project interpreter, whether or not the file exists."""
    # Resolver definition: this join names that checkout's interpreter.
    return checkout / ".venv" / "bin" / "python"


def _venv_bin_checkout(candidate: Path) -> Path | None:
    """Checkout that owns ``candidate`` when it sits directly in that checkout's ``.venv/bin``."""
    if candidate.parent.name != "bin":
        return None
    venv = candidate.parent.parent
    if venv.name != ".venv":
        return None
    return venv.parent


def _venv_owners(interpreter: Path) -> set[Path]:
    """Checkouts that own ``interpreter`` as a ``<checkout>/.venv/bin`` entrypoint.

    Any direct child of ``.venv/bin`` counts: ``python``, ``python3``, versioned
    ``python3.N``, and every other executable there. Each path is classified
    at every directory symlink hop, so both ``other/.venv -> venv-store`` and
    ``venv-alias -> other/.venv -> venv-store`` name ``other``. Owners are
    compared after ``realpath``. A later check refuses the interpreter when
    any owner is outside the requested checkout and its primary.

    A file-symlink hop is followed only when no directory view names a checkout, so
    a link that lands in ``.venv/bin`` counts even when the link's own path
    does not. The entrypoint is recognized before that hop is followed, so
    ``python3.12`` still counts when it points at a toolchain binary outside
    the venv. A toolchain interpreter such as ``hostedtoolcache/.../bin/python``
    names no checkout.
    """
    candidate = Path(_absolute_text(interpreter))
    seen: set[Path] = set()
    owners: set[Path] = set()
    for _ in range(_MAX_SYMLINK_HOPS + 1):
        view_u = _lexical_absolute(candidate)
        if candidate in seen:
            raise FileNotFoundError(f"project interpreter symlink loop: {interpreter}")
        seen.add(candidate)
        checkout = _venv_bin_checkout(view_u)
        if checkout is not None:
            owners.add(_realpath(checkout))
        parent_hop = _first_parent_symlink_hop(candidate.parent)
        if parent_hop is not None:
            candidate = parent_hop / candidate.name
            continue
        if owners:
            return owners
        target = _symlink_target(candidate)
        if target is None:
            return set()
        if not target.is_absolute():
            target = candidate.parent / target
        candidate = target
    raise FileNotFoundError(f"project interpreter symlink chain exceeds {_MAX_SYMLINK_HOPS} hops: {interpreter}")


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
       project ``.venv``. The executable is classified at each directory
       symlink hop. A view containing ``<X>/.venv/bin/<entry>`` names ``X``
       (compared after ``realpath``), including ``python3.N``, a file symlink
       that resolves into that directory, a directory symlink such as
       ``venv-alias -> other/.venv -> venv-store``. The final executable symlink is not
       resolved: ``python3.N`` points at the toolchain binary, and following it
       would drop ``.venv``. If any named checkout is neither the requested
       checkout nor its primary checkout, the interpreter is refused. It is
       accepted when every named checkout is one of those two, and when no
       view names a checkout (hosted CI Python). Symlink loops, path
       components that cannot be inspected, and a link that changes between
       the check and the read fail closed with ``FileNotFoundError``.
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
    owners = _venv_owners(current)
    if owners:
        allowed = {_realpath(repo), _realpath(primary_root)}
        if not owners.issubset(allowed):
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
