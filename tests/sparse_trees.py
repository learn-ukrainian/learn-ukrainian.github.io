"""Shared sparse-worktree tree-absence predicate (issue #8581).

Dispatch worktrees sparse-checkout away ``curriculum/``, ``wiki/``,
``data/projects/``, and ``data/lexicon/``. Test modules and
``tests/conftest.py`` share this predicate so a skip happens only when the
whole sparse-excluded tree is absent — never when the tree is present but a
single file inside it is missing (that case must keep failing, as it did
before lazy reads were introduced).

``SPARSE_TEST_FORCE_MISSING_TREES`` is a comma-separated, test-only override
that makes the listed trees read as absent. The sparse collection guard uses
it to exercise the absent-tree collection paths in a subprocess without
copying the checkout.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FORCE_MISSING_TREES_ENV = "SPARSE_TEST_FORCE_MISSING_TREES"


def _normalize(rel_tree: str) -> str:
    return rel_tree.replace("\\", "/").lstrip("./").rstrip("/")


def forced_missing_trees() -> frozenset[str]:
    raw = os.environ.get(FORCE_MISSING_TREES_ENV, "")
    return frozenset(_normalize(item.strip()) for item in raw.split(",") if item.strip())


def tree_absent(rel_tree: str) -> bool:
    """True when a sparse-excluded tree reads as absent from this worktree."""
    normalized = _normalize(rel_tree)
    if normalized in forced_missing_trees():
        return True
    return not (REPO_ROOT / normalized).is_dir()
