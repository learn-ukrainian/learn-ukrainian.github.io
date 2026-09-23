"""Hide sparse-excluded trees from one pytest process.

The collection guard loads this module with ``pytest -p`` in a child process
only, after setting ``SPARSE_TEST_FORCE_MISSING_TREES``. Importing it with
that variable unset does nothing, so a parent test run that imports the
module does not install the hook.

``os.stat`` and ``Path.exists`` have no audit event. ``tree_absent()`` covers
those existence checks; this hook covers ``open``, ``os.listdir``,
``os.scandir``, ``sqlite3.connect``, and ``glob.glob``.
"""

from __future__ import annotations

import errno
import os
import sys
import threading

from tests.sparse_trees import REPO_ROOT_ENV, forced_missing_trees

_EVENTS = frozenset(("open", "os.listdir", "os.scandir", "sqlite3.connect", "glob.glob"))
_BOUNDS: tuple[tuple[str, str], ...] = ()
_REPO_ABS = ""
_REPO_PREFIX = ""
_GUARD = threading.local()


def _absolute(text: str) -> str:
    if os.path.isabs(text):
        return os.path.normpath(text)
    return os.path.normpath(os.path.join(os.getcwd(), text))


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


def _hook(event: str, args: tuple[object, ...]) -> None:
    if event not in _EVENTS or not args or getattr(_GUARD, "busy", False):
        return
    _GUARD.busy = True
    try:
        parsed = _path_text(args[0])
        if parsed is None:
            return
        text, filename = parsed
        if not text or (os.path.isabs(text) and _REPO_ABS not in text):
            return
        absolute = _absolute(text)
        if absolute != _REPO_ABS and not absolute.startswith(_REPO_PREFIX):
            return
        for root, rooted in _BOUNDS:
            if absolute == root or absolute.startswith(rooted):
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)
    finally:
        _GUARD.busy = False


def _install() -> None:
    global _BOUNDS, _REPO_ABS, _REPO_PREFIX
    trees = forced_missing_trees()
    if not trees:
        return
    raw_root = os.environ.get(REPO_ROOT_ENV, "")
    if raw_root:
        repo = os.path.abspath(raw_root)
    else:
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    bounds: list[tuple[str, str]] = []
    for rel in sorted(trees):
        root = os.path.normpath(os.path.join(repo, *rel.split("/")))
        bounds.append((root, root + os.sep))
    _REPO_ABS = repo
    _REPO_PREFIX = repo + os.sep
    _BOUNDS = tuple(bounds)
    sys.addaudithook(_hook)


_install()
