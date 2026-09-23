"""Hide sparse-excluded trees from one pytest process.

The collection guard loads this module with ``pytest -p`` in a child process
only, after setting ``SPARSE_TEST_FORCE_MISSING_TREES``. Importing it with
that variable unset does nothing, so a parent test run that imports the
module does not install the hook.

Every path is resolved with ``os.path.realpath(..., strict=False)`` and
compared to the realpath of each tree root. Roots are computed once, before
the wrappers are installed. An absolute path outside ``/proc`` is remembered
only when it exists (``os.lstat`` of the resolved path succeeds) and realpath
returns that same spelling. A missing path, a symlink, a relative path, and
anything under ``/proc`` (cwd, directory fds) is resolved again on every
call. ``os.symlink``, ``os.link``, ``os.rename`` (also ``os.replace``),
``os.remove``, ``os.rmdir``, and ``os.mkdir`` clear those remembered paths,
so a name checked while absent cannot be served after it is created.

``os.path.realpath`` calls ``os.lstat``. A ``threading.local`` flag makes
those nested calls use the saved ``os.stat`` / ``os.lstat`` so resolution
does not re-enter the guard.

``open``, ``os.listdir``, ``os.scandir``, ``sqlite3.connect``, and
``glob.glob`` go through the audit hook. That ``open`` event is
``(path, mode, flags)`` and does not include ``dir_fd``, so ``os.open`` is
wrapped too. A relative path plus ``dir_fd`` is resolved against
``os.readlink("/proc/self/fd/<dir_fd>")``, or against cwd if that readlink
fails. ``os.stat`` and ``os.lstat`` have no audit event and are wrapped.
``os.lstat`` and ``follow_symlinks=False`` resolve only the parent directory
and leave the final component unresolved, so ``os.lstat("/proc/self/cwd")``
returns the symlink itself when cwd is a hidden root.
"""

from __future__ import annotations

import errno
import os
import sys
import threading

from tests.sparse_trees import REPO_ROOT_ENV, forced_missing_trees

_EVENTS = frozenset(("open", "os.listdir", "os.scandir", "sqlite3.connect", "glob.glob"))
# Python 3.12 audit events (docs.python.org/3.12/library/audit_events.html)
# that change which file a name refers to. Each of these drops the identity
# cache. os.replace is not its own event; it raises os.rename
# (src, dst, src_dir_fd, dst_dir_fd). os.truncate (fd, length) changes size,
# not the directory entry, and is not listed.
#   os.symlink  src, dst, dir_fd
#   os.link     src, dst, src_dir_fd, dst_dir_fd
#   os.rename   src, dst, src_dir_fd, dst_dir_fd
#   os.remove   path, dir_fd
#   os.rmdir    path, dir_fd
#   os.mkdir    path, mode, dir_fd
_NAMESPACE_MUTATIONS = frozenset(
    ("os.symlink", "os.link", "os.rename", "os.remove", "os.rmdir", "os.mkdir")
)
_BOUNDS: tuple[tuple[str, str], ...] = ()
_GUARD = threading.local()
_ORIG_STAT = os.stat
_ORIG_LSTAT = os.lstat
_ORIG_OPEN = os.open
_FOLLOWED_FINALS = frozenset(("", ".", ".."))
# Absolute spellings that exist and that realpath did not rewrite.
_UNCHANGED: dict[str, str] = {}


def _path_text(value: object) -> tuple[str, str | bytes] | None:
    """Return ``(decoded, filename)`` for a path argument.

    An integer file descriptor is not a path. ``os.stat(fd)`` stays unguarded:
    the descriptor was produced by an earlier open, and that open was already
    checked.
    """
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


def _anchored(text: str, dir_fd: int | None) -> str:
    """Join a relative path to the directory ``dir_fd`` names.

    Linux exposes that directory as a symlink at ``/proc/self/fd/<dir_fd>``.
    If the readlink fails, the path is joined to cwd, which is what the
    kernel uses when ``dir_fd`` is absent.
    """
    if dir_fd is None or os.path.isabs(text):
        return text
    try:
        base = os.readlink(f"/proc/self/fd/{dir_fd}")
    except OSError:
        base = os.getcwd()
    return os.path.join(base, text)


def _rememberable(text: str) -> bool:
    return os.path.isabs(text) and not text.startswith("/proc/")


def _exists(resolved: str) -> bool:
    """True when ``os.lstat`` of the already-resolved path succeeds."""
    try:
        _ORIG_LSTAT(resolved)
    except OSError:
        return False
    return True


def _realpath(text: str) -> str | None:
    if _rememberable(text):
        cached = _UNCHANGED.get(text)
        if cached is not None:
            return cached
    try:
        resolved = os.path.realpath(text, strict=False)
    except (OSError, ValueError):
        return None
    # A missing path's realpath (strict=False) equals its spelling. Remember
    # it only after lstat succeeds, so a later symlink is not served the
    # absent answer.
    if (
        resolved is not None
        and _rememberable(text)
        and resolved == os.path.normpath(text)
        and _exists(resolved)
    ):
        _UNCHANGED[text] = resolved
    return resolved


def _resolve(text: str, *, follow_symlinks: bool) -> str | None:
    """Canonical path of ``text``.

    With ``follow_symlinks`` false, only the parent is canonicalized. The
    final component stays as written, matching ``os.lstat`` and
    ``follow_symlinks=False`` (a trailing slash, ``.``, or ``..`` still
    follows, because the kernel does).
    """
    if not text:
        return None
    parent, name = os.path.split(text)
    if follow_symlinks or name in _FOLLOWED_FINALS:
        return _realpath(text)
    parent_resolved = _realpath(parent if parent else ".")
    if parent_resolved is None:
        return None
    return os.path.normpath(os.path.join(parent_resolved, name))


def _hidden_filename(
    path: object,
    *,
    dir_fd: int | None,
    follow_symlinks: bool,
) -> str | bytes | None:
    """Filename to report when ``path`` resolves inside a hidden tree."""
    if getattr(_GUARD, "busy", False):
        return None
    parsed = _path_text(path)
    if parsed is None:
        return None
    text, filename = parsed
    if not text:
        return None
    # realpath's own lstat must not re-enter the wrappers.
    _GUARD.busy = True
    try:
        resolved = _resolve(_anchored(text, dir_fd), follow_symlinks=follow_symlinks)
    finally:
        _GUARD.busy = False
    if resolved is not None and _in_bounds(resolved):
        return filename
    return None


def _guarded_stat(path: object, *, dir_fd: int | None = None, follow_symlinks: bool = True):
    if not getattr(_GUARD, "busy", False):
        filename = _hidden_filename(path, dir_fd=dir_fd, follow_symlinks=follow_symlinks)
        if filename is not None:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)
    return _ORIG_STAT(path, dir_fd=dir_fd, follow_symlinks=follow_symlinks)


def _guarded_lstat(path: object, *, dir_fd: int | None = None):
    if not getattr(_GUARD, "busy", False):
        filename = _hidden_filename(path, dir_fd=dir_fd, follow_symlinks=False)
        if filename is not None:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)
    return _ORIG_LSTAT(path, dir_fd=dir_fd)


def _guarded_open(path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None):
    if getattr(_GUARD, "busy", False):
        return _ORIG_OPEN(path, flags, mode, dir_fd=dir_fd)
    filename = _hidden_filename(path, dir_fd=dir_fd, follow_symlinks=True)
    if filename is not None:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)
    # The audit hook sees the path without dir_fd. Skip it: this wrapper
    # already applied the directory fd.
    _GUARD.busy = True
    try:
        return _ORIG_OPEN(path, flags, mode, dir_fd=dir_fd)
    finally:
        _GUARD.busy = False


def _hook(event: str, args: tuple[object, ...]) -> None:
    if event in _NAMESPACE_MUTATIONS:
        _UNCHANGED.clear()
        return
    if event not in _EVENTS or not args or getattr(_GUARD, "busy", False):
        return
    filename = _hidden_filename(args[0], dir_fd=None, follow_symlinks=True)
    if filename is not None:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)


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
        root = os.path.realpath(os.path.join(repo, *rel.split("/")), strict=False)
        bounds.append((root, root + os.sep))
    _BOUNDS = tuple(bounds)
    os.stat = _guarded_stat
    os.lstat = _guarded_lstat
    os.open = _guarded_open
    sys.addaudithook(_hook)


_install()
