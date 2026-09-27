"""Collect one directory, and only the test modules named in a scope file.

Pytest re-scans every parent directory for each positional test-file
argument. The sparse-collection guard names about a hundred modules, and
that repeated scan — not importing those modules — was the per-PR cost.
The child sets ``SPARSE_COLLECTION_SCOPE_FILE`` to the absolute paths of
those modules and starts collection at their common parent. Each directory
that contains a named module is entered once; every other test file is
ignored. Unset, this plugin leaves collection unchanged.

When ``SPARSE_COLLECTION_OUTCOMES_FILE`` is set, the child writes one JSON
object: each scope path mapped to ``{"status": ..., "reason": ...}``, where
``status`` is ``collected`` (at least one item), ``skipped`` (a module-level
``pytest_collectreport`` with ``report.skipped``), or ``failed``. ``reason``
is the skip message (``report.longrepr``'s third element for a
``pytest.skip(..., allow_module_level=True)``, else its ``str()``) when
``status`` is ``skipped``, and ``None`` otherwise. ``--collect-only -q``
prints no node id for a module-level skip, so the parent cannot see that
outcome in the text and relies on this reason to decide whether the skip is
expected.
"""

from __future__ import annotations

import functools
import json
import os
from pathlib import Path

import pytest

SCOPE_FILE_ENV = "SPARSE_COLLECTION_SCOPE_FILE"
OUTCOMES_FILE_ENV = "SPARSE_COLLECTION_OUTCOMES_FILE"

_ROOT: Path | None = None
_FAILED: set[str] = set()
_SKIPPED: dict[str, str] = {}
_ITEM_COUNTS: dict[str, int] = {}
_WROTE = False


@functools.lru_cache(maxsize=1)
def _load_scope() -> tuple[frozenset[str], frozenset[str]] | None:
    """Return ``(files, ancestor directories)`` for this process, or ``None``."""
    raw = os.environ.get(SCOPE_FILE_ENV, "")
    if not raw:
        return None
    try:
        text = Path(raw).read_text(encoding="utf-8")
    except OSError as error:
        raise RuntimeError(f"{SCOPE_FILE_ENV}={raw!r} is set but unreadable: {error}") from error
    entries = [line.strip() for line in text.splitlines() if line.strip()]
    if not entries:
        raise RuntimeError(f"{SCOPE_FILE_ENV}={raw!r} is empty")
    files: set[str] = set()
    ancestors: set[str] = set()
    for entry in entries:
        path = Path(entry)
        if not path.name.startswith("test_") or path.suffix != ".py":
            raise RuntimeError(f"{SCOPE_FILE_ENV}={raw!r} has a malformed entry: {entry!r}")
        resolved = path.resolve().as_posix()
        files.add(resolved)
        parent = Path(resolved).parent
        while True:
            parent_text = parent.as_posix()
            if parent_text in ancestors:
                break
            ancestors.add(parent_text)
            if parent.parent == parent:
                break
            parent = parent.parent
    return frozenset(files), frozenset(ancestors)


@pytest.hookimpl(tryfirst=True)
def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool | None:
    """Ignore every test file the scope file does not name.

    ``tryfirst`` so a ``False`` result admits a parent directory before
    pytest's ``norecursedirs`` hook can hide it. Directories that contain
    no named module are ignored, which keeps collection on the path down to
    those modules.
    """
    scope = _load_scope()
    if scope is None:
        return None
    files, ancestors = scope
    try:
        resolved = collection_path.resolve().as_posix()
    except OSError:
        return True
    return not (resolved in ancestors or resolved in files)


def _scope_files() -> frozenset[str] | None:
    scope = _load_scope()
    if scope is None:
        return None
    return scope[0]


def _as_scope_target(path: Path) -> str | None:
    """Return the scope entry ``path`` names, or ``None``."""
    files = _scope_files()
    if files is None:
        return None
    candidate = path if path.is_absolute() or _ROOT is None else _ROOT / path
    try:
        resolved = candidate.resolve().as_posix()
    except OSError:
        return None
    if resolved in files:
        return resolved
    return None


def _record_items(session: pytest.Session) -> None:
    for item in session.items:
        target = _as_scope_target(Path(item.path))
        if target is None:
            continue
        _ITEM_COUNTS[target] = _ITEM_COUNTS.get(target, 0) + 1


def _outcomes() -> dict[str, dict[str, str | None]]:
    """One ``{"status": ..., "reason": ...}`` entry per scope file.

    A collection error wins, including a file that produced no report at
    all. Items win over a skip so a module that collected tests is not
    labeled skipped because a nested collector was.
    """
    files = _scope_files()
    if not files:
        return {}
    result: dict[str, dict[str, str | None]] = {}
    for target in sorted(files):
        if target in _FAILED:
            result[target] = {"status": "failed", "reason": None}
        elif _ITEM_COUNTS.get(target, 0) >= 1:
            result[target] = {"status": "collected", "reason": None}
        elif target in _SKIPPED:
            result[target] = {"status": "skipped", "reason": _SKIPPED[target]}
        else:
            result[target] = {"status": "failed", "reason": None}
    return result


def _write_outcomes() -> None:
    global _WROTE
    if _WROTE:
        return
    raw = os.environ.get(OUTCOMES_FILE_ENV, "")
    if not raw or _scope_files() is None:
        return
    Path(raw).write_text(json.dumps(_outcomes(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _WROTE = True


def pytest_configure(config: pytest.Config) -> None:
    global _ROOT
    _ROOT = Path(config.rootpath)


def _skip_reason(report: pytest.CollectReport) -> str:
    """Extract the skip message pytest attaches to a module-level skip.

    ``pytest.skip(..., allow_module_level=True)`` sets ``longrepr`` to
    ``(path, lineno, "Skipped: <reason>")``; fall back to ``str()`` for any
    other shape so a reason is always recorded.
    """
    longrepr = report.longrepr
    if isinstance(longrepr, tuple) and len(longrepr) == 3:
        return str(longrepr[2])
    return str(longrepr)


def pytest_collectreport(report: pytest.CollectReport) -> None:
    raw = getattr(report, "fspath", None)
    if raw is None or not str(raw):
        return
    target = _as_scope_target(Path(str(raw)))
    if target is None:
        return
    if report.failed:
        _FAILED.add(target)
    elif report.skipped:
        _SKIPPED[target] = _skip_reason(report)


def pytest_collection_finish(session: pytest.Session) -> None:
    _record_items(session)
    _write_outcomes()


def pytest_sessionfinish(session: pytest.Session) -> None:
    """Write the same file if collection never finished."""
    if _WROTE:
        return
    _record_items(session)
    _write_outcomes()
