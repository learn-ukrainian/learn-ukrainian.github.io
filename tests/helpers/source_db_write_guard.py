"""Refuse test-process writable SQLite opens of real repository data/*.db.

The audit event covers connect aliases and Connection constructors before any
database is opened. Fixture databases outside the checkout remain writable.
Subprocesses need their own isolation; this is a test-process boundary.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import pytest

from scripts.common.repo_root import main_checkout_root

_WORKTREE = Path(__file__).resolve().parents[2]
DATA_ROOTS = frozenset({(_WORKTREE / "data").resolve(), (main_checkout_root(_WORKTREE) / "data").resolve()})


def refuse_writable_source_db(event: str, args: tuple[object, ...]) -> None:
    """Fail before SQLite opens a repository database without explicit mode=ro."""
    if event != "sqlite3.connect" or not args or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    raw = os.fsdecode(os.fspath(args[0]))
    readonly = False
    if raw.startswith("file:"):
        parts = urlsplit(raw)
        path = Path(unquote(parts.path)).resolve()
        readonly = parse_qs(parts.query).get("mode") == ["ro"]
    else:
        path = Path(raw).resolve()
    if path.suffix == ".db" and any(path.is_relative_to(root) for root in DATA_ROOTS) and not readonly:
        pytest.fail(
            "Writable SQLite open of a repository data/*.db is forbidden; use mode=ro or a fixture DB", pytrace=False
        )


sys.addaudithook(refuse_writable_source_db)
