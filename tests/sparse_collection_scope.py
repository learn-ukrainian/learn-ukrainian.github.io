"""Collect one directory, and only the test modules named in a scope file.

Pytest re-scans every parent directory for each positional test-file
argument. The sparse-collection guard names about a hundred modules, and
that repeated scan — not importing those modules — was the per-PR cost.
The child sets ``SPARSE_COLLECTION_SCOPE_FILE`` to the absolute paths of
those modules and starts collection at their common parent. Each directory
that contains a named module is entered once; every other test file is
ignored. Unset, this plugin leaves collection unchanged.
"""

from __future__ import annotations

import functools
import os
from pathlib import Path

import pytest

SCOPE_FILE_ENV = "SPARSE_COLLECTION_SCOPE_FILE"


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
