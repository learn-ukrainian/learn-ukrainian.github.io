"""Tests for scripts.rag.config._resolve_vesum_db_path (#6542 review finding).

The fallback used to hardcode one operator's absolute path
(``/Users/krisztiankoos/projects/learn-ukrainian``) so that a dispatch
worktree — which excludes ``data/`` via ``worktree.sparsePaths`` — could
still find the primary checkout's ``vesum.db``. That broke for every other
operator/machine. This resolves the primary root from the shared ``.git``
common dir instead (`scripts.guardrails.worktree_containment.resolve_main_root`).
"""
from __future__ import annotations

from pathlib import Path

from scripts.guardrails.worktree_containment import NotAGitRepositoryError
from scripts.rag.config import _resolve_vesum_db_path


def test_returns_default_when_it_already_exists(tmp_path: Path) -> None:
    default_path = tmp_path / "worktree" / "data" / "vesum.db"
    default_path.parent.mkdir(parents=True)
    default_path.write_bytes(b"db")

    resolved = _resolve_vesum_db_path(default_path, tmp_path / "worktree")

    assert resolved == default_path


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


def test_falls_back_to_default_when_primary_copy_also_missing(
    tmp_path: Path, monkeypatch
) -> None:
    default_path = tmp_path / "worktree" / "data" / "vesum.db"  # never created
    primary_root = tmp_path / "primary"  # data/vesum.db never created either

    monkeypatch.setattr(
        "scripts.guardrails.worktree_containment.resolve_main_root",
        lambda start: primary_root,
    )

    resolved = _resolve_vesum_db_path(default_path, tmp_path / "worktree")

    assert resolved == default_path


def test_falls_back_to_default_outside_a_git_repository(
    tmp_path: Path, monkeypatch
) -> None:
    default_path = tmp_path / "worktree" / "data" / "vesum.db"

    def _raise(start: Path) -> Path:
        raise NotAGitRepositoryError(f"{start} is not inside a git repository")

    monkeypatch.setattr(
        "scripts.guardrails.worktree_containment.resolve_main_root", _raise
    )

    resolved = _resolve_vesum_db_path(default_path, tmp_path / "worktree")

    assert resolved == default_path
