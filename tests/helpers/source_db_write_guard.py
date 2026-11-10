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
from lu_machinery.common.repo_root import main_checkout_root

_WORKTREE = Path(__file__).resolve().parents[2]
DATA_ROOTS = frozenset({(_WORKTREE / "data").resolve(), (main_checkout_root(_WORKTREE) / "data").resolve()})
# SQLite stores listed by registry/projects/open_model_data/sources/holdings_manifest.yaml
# (generated from scripts/projects/open_model_data/holdings_manifest.py:HOLDINGS).
# The remaining holding, ua-gec, is file-based. VESUM activation additionally
# stages lexicon stores as data/vesum_shadow_*.db (scripts/rag/activate_vesum_db.py).
SOURCE_DB_NAMES = frozenset({"sources.db", "vesum.db"})
SOURCE_DB_PATTERNS = ("vesum_shadow_*.db",)
# data/sources.db is a relative symlink selector into this directory, which holds
# every Sources store generation (agents_extensions/shared/rules/storage-topology.md,
# "Sources store generations").
SOURCE_GENERATIONS_DIR = "sources-generations"
_MAX_SYMLINK_HOPS = 40  # Linux SYMLOOP_MAX


def _is_source_db(path: Path) -> bool:
    if path.parent in DATA_ROOTS:
        return path.name in SOURCE_DB_NAMES or any(fnmatchcase(path.name, pattern) for pattern in SOURCE_DB_PATTERNS)
    return (
        path.parent.name == SOURCE_GENERATIONS_DIR
        and path.parent.parent in DATA_ROOTS
        and fnmatchcase(path.name, "*.db")
    )


def _reaches_source_db(named: Path) -> bool:
    """Judge every name the path passes through, from the name as given to the final target.

    Each hop keeps its own final component (its directory resolved), so a selector or
    an alias is judged by its name as well as by every symlink it leads through.
    No database is opened; only links are read.
    """
    path = named
    for _ in range(_MAX_SYMLINK_HOPS):
        path = path.parent.resolve() / path.name
        if _is_source_db(path):
            return True
        if not path.is_symlink():
            return False
        path = path.parent / os.readlink(path)
    return True  # fail closed on a looping or over-long chain (SQLite cannot open one either)


def refuse_writable_source_db(event: str, args: tuple[object, ...]) -> None:
    """Fail before SQLite opens a repository source store without explicit mode=ro."""
    if event != "sqlite3.connect" or not args or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    raw = os.fsdecode(os.fspath(args[0]))
    readonly = False
    if raw.startswith("file:"):
        parts = urlsplit(raw)
        named = Path(unquote(parts.path)).absolute()
        readonly = parse_qs(parts.query).get("mode") == ["ro"]
    else:
        named = Path(raw).absolute()
    if not readonly and _reaches_source_db(named):
        pytest.fail(
            "Writable SQLite open of a repository source database is forbidden; use mode=ro or a fixture DB",
            pytrace=False,
        )


sys.addaudithook(refuse_writable_source_db)
