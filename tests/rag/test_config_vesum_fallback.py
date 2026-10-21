"""Tests for scripts.rag.config._resolve_vesum_db_path (#6542 review finding).

The fallback used to hardcode one operator's absolute path
(``.``) so that a dispatch
worktree — which excludes ``data/`` via ``worktree.sparsePaths`` — could
still find the primary checkout's ``vesum.db``. That broke for every other
operator/machine. This resolves the primary root from the shared ``.git``
common dir instead (`scripts.guardrails.worktree_containment.resolve_main_root`).
"""
from __future__ import annotations

from pathlib import Path

from scripts.rag.config import _resolve_vesum_db_path


def test_missing_default_uses_primary_checkout_copy(tmp_path: Path, monkeypatch) -> None:
    default_path = tmp_path / "worktree" / "data" / "vesum.db"  # never created
    primary_root = tmp_path / "primary"
    primary_db = primary_root / "data" / "vesum.db"
    primary_db.parent.mkdir(parents=True)
    primary_db.write_bytes(b"db")

    monkeypatch.setattr(
        "scripts.guardrails.worktree_containment.resolve_main_root",
        lambda start: primary_root,
    )

    resolved = _resolve_vesum_db_path(default_path, tmp_path / "worktree")

    assert resolved == primary_db
