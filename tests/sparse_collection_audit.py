"""Hide sparse-excluded trees from one pytest process.

The collection guard loads this module with ``pytest -p`` in a child process
only, after setting ``SPARSE_TEST_FORCE_MISSING_TREES``. Importing it with
that variable unset does nothing, so a parent test run that imports the
module does not install the hook.

Every path is resolved with ``os.path.realpath`` (relative paths against
``os.getcwd()``) and compared to the realpath of each tree root. A symlink,
``..`` component, or ``/proc/self/cwd`` spelling therefore cannot step around
the check. ``open``, ``os.listdir``, ``os.scandir``, ``sqlite3.connect``, and
``glob.glob`` go through the audit hook. ``os.stat`` and ``os.lstat`` have no
audit event, so this same child wraps them and raises ``FileNotFoundError``
for a resolved path inside a hidden tree. Tree roots are resolved before
those wrappers are installed: ``os.path.realpath`` itself calls ``os.lstat``.
"""

from __future__ import annotations

import errno
import os
import stat
import sys
import threading

from tests.sparse_trees import REPO_ROOT_ENV, forced_missing_trees

_EVENTS = frozenset(("open", "os.listdir", "os.scandir", "sqlite3.connect", "glob.glob"))
_BOUNDS: tuple[tuple[str, str], ...] = ()
_GUARD = threading.local()
_UNRESOLVED = object()
_RESOLVE_CACHE: dict[str, str | None] = {os.sep: os.sep}
_ORIG_STAT = os.stat
_ORIG_LSTAT = os.lstat


def _path_text(value: object) -> tuple[str, str | bytes] | None:
    """Return ``(decoded, filename)`` for a path argument, ignoring fds."""
    if isinstance(value, int) or value is None:
        return None
    if isinstance(value, str):
        return value, value
    if isinstance(value, bytes):
        return os.fsdecode(value), value
    if isinstance(value, os.PathLike):
        raw = os.fspath(value)
        if isinstance(raw, bytes):
            return os.fsdecode(raw), raw
        if isinstance(raw, str):
            return raw, raw
    return None


def _in_bounds(resolved: str) -> bool:
    return any(resolved == root or resolved.startswith(rooted) for root, rooted in _BOUNDS)


def _walk(path: str, rest: str, seen: dict[str, str | None]) -> str:
    """``os.path.realpath`` walk using the original ``lstat``, with a prefix cache.

    ``..`` is applied to the resolved prefix, not the spelling, so a symlink
    followed by ``..`` cannot leave the hidden tree unnoticed. Component
    results are cached; the stat wrappers are not on this path.
    """
    if os.path.isabs(rest):
        rest = rest[1:]
        path = os.sep
    while rest:
        name, _, rest = rest.partition(os.sep)
        if not name or name == ".":
            continue
        if name == "..":
            if path:
                path, popped = os.path.split(path)
                if popped == "..":
                    path = os.path.join(path, "..", "..")
            else:
                path = ".."
            continue
        newpath = os.path.join(path, name)
        cached = _RESOLVE_CACHE.get(newpath, _UNRESOLVED)
        if cached is not _UNRESOLVED:
            if cached is None:
                return os.path.join(newpath, rest) if rest else newpath
            path = cached
            continue
        try:
            is_link = stat.S_ISLNK(_ORIG_LSTAT(newpath).st_mode)
        except OSError:
            is_link = False
        if not is_link:
            _RESOLVE_CACHE[newpath] = newpath
            path = newpath
            continue
        if newpath in seen:
            prior = seen[newpath]
            if prior is not None:
                path = prior
                continue
            return os.path.join(newpath, rest) if rest else newpath
        seen[newpath] = None
        path = _walk(path, os.readlink(newpath), seen)
        seen[newpath] = path
        _RESOLVE_CACHE[newpath] = path
    return path


def _resolve(text: str) -> str | None:
    """Canonical path of ``text``, or None when it cannot be resolved.

    Relative paths are joined to ``os.getcwd()``. The busy flag stays set for
    the walk so a nested ``os.stat`` delegates to the original and does not
    hide an intermediate component.
    """
    if not text:
        return None
    candidate = text if os.path.isabs(text) else os.path.join(os.getcwd(), text)
    cached = _RESOLVE_CACHE.get(candidate, _UNRESOLVED)
    if cached is not _UNRESOLVED:
        return cached
    was_busy = getattr(_GUARD, "busy", False)
    _GUARD.busy = True
    try:
        try:
            resolved = os.path.abspath(_walk("", candidate, {}))
        except (OSError, ValueError):
            resolved = None
    finally:
        _GUARD.busy = was_busy
    _RESOLVE_CACHE[candidate] = resolved
    return resolved


def _hidden_filename(path: object, *, dir_fd: int | None) -> str | bytes | None:
    """Filename to report when ``path`` resolves inside a hidden tree."""
    if getattr(_GUARD, "busy", False):
        return None
    parsed = _path_text(path)
    if parsed is None:
        return None
    text, filename = parsed
    if not text:
        return None
    if dir_fd is not None and not os.path.isabs(text):
        base = _resolve(f"/proc/self/fd/{dir_fd}")
        if not base:
            return None
        text = os.path.join(base, text)
    resolved = _resolve(text)
    if resolved is not None and _in_bounds(resolved):
        return filename
    return None


def _guarded_stat(path: object, *, dir_fd: int | None = None, follow_symlinks: bool = True):
    filename = _hidden_filename(path, dir_fd=dir_fd)
    if filename is not None:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)
    return _ORIG_STAT(path, dir_fd=dir_fd, follow_symlinks=follow_symlinks)


def _guarded_lstat(path: object, *, dir_fd: int | None = None):
    filename = _hidden_filename(path, dir_fd=dir_fd)
    if filename is not None:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)
    return _ORIG_LSTAT(path, dir_fd=dir_fd)


def _hook(event: str, args: tuple[object, ...]) -> None:
    if event not in _EVENTS or not args or getattr(_GUARD, "busy", False):
        return
    _GUARD.busy = True
    try:
        parsed = _path_text(args[0])
        if parsed is None:
            return
        text, filename = parsed
        resolved = _resolve(text)
        if resolved is not None and _in_bounds(resolved):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)
    finally:
        _GUARD.busy = False


def _install() -> None:
    global _BOUNDS
    trees = forced_missing_trees()
    if not trees:
        return
    raw_root = os.environ.get(REPO_ROOT_ENV, "")
    repo = raw_root or os.path.join(os.path.dirname(__file__), os.pardir)
    # Resolve roots before replacing os.lstat. os.path.realpath calls it, and
    # the wrappers raise for these trees.
    bounds: list[tuple[str, str]] = []
    for rel in sorted(trees):
        root = os.path.realpath(os.path.join(repo, *rel.split("/")))
        bounds.append((root, root + os.sep))
    _BOUNDS = tuple(bounds)
    os.stat = _guarded_stat
    os.lstat = _guarded_lstat
    sys.addaudithook(_hook)


_install()
