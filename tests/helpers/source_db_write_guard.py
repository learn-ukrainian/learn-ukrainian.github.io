"""Refuse test-process writable SQLite opens of repository source/lexicon stores.

The audit event covers connect aliases and Connection constructors before any
database is opened. Runtime databases under data/ and fixture databases outside
the checkout remain writable. Subprocesses need their own isolation; this is a
test-process boundary.
"""

from __future__ import annotations

import os
import sys
from fnmatch import fnmatchcase
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import pytest

from scripts.common.repo_root import main_checkout_root

_WORKTREE = Path(__file__).resolve().parents[2]
DATA_ROOTS = frozenset({(_WORKTREE / "data").resolve(), (main_checkout_root(_WORKTREE) / "data").resolve()})
# SQLite stores listed by registry/projects/open_model_data/sources/holdings_manifest.yaml
# (generated from scripts/projects/open_model_data/holdings_manifest.py:HOLDINGS).
# The remaining holding, ua-gec, is file-based. VESUM activation additionally
# stages lexicon stores as data/vesum_shadow_*.db (scripts/rag/activate_vesum_db.py).
SOURCE_DB_NAMES = frozenset({"sources.db", "vesum.db"})
SOURCE_DB_PATTERNS = ("vesum_shadow_*.db",)


def refuse_writable_source_db(event: str, args: tuple[object, ...]) -> None:
    """Fail before SQLite opens a repository source store without explicit mode=ro."""
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
    if (
        path.parent in DATA_ROOTS
        and (path.name in SOURCE_DB_NAMES or any(fnmatchcase(path.name, pattern) for pattern in SOURCE_DB_PATTERNS))
        and not readonly
    ):
        pytest.fail(
            "Writable SQLite open of a repository source database is forbidden; use mode=ro or a fixture DB",
            pytrace=False,
        )


sys.addaudithook(refuse_writable_source_db)
