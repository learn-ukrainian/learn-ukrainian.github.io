"""Shielded formal CF is retired in production (operator 2026-08-07)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.ai_agent_bridge import _review_pr as review_pr
from scripts.review import isolation


def test_handle_review_pr_refuses_when_formal_disabled(monkeypatch, capsys) -> None:
    monkeypatch.delenv("LU_FORMAL_SHIELDED_CF", raising=False)
    # Autouse conftest enables the flag — clear it for this production-path check.
    monkeypatch.setenv("LU_FORMAL_SHIELDED_CF", "")
    code = review_pr.handle_review_pr(
        SimpleNamespace(
            list_eligible=False,
            pr="9999",
            reviewer="codex",
            initiator="test",
            author_model="grok-4.5",
            author_family="xai",
        )
    )
    captured = capsys.readouterr()
    assert code == 2
    assert "RETIRED" in captured.err
    assert "review-pr" in captured.err


def test_create_review_temp_root_refuses_lu_prefix_when_formal_disabled(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("LU_FORMAL_SHIELDED_CF", "")
    with pytest.raises(OSError, match="retired"):
        isolation.create_review_temp_root(prefix="lu-review-snap-", dir=tmp_path)


def test_create_review_temp_root_allows_when_formal_enabled_for_tests(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("LU_FORMAL_SHIELDED_CF", "1")
    root = isolation.create_review_temp_root(prefix="lu-review-snap-", dir=tmp_path)
    assert root.is_dir()
    isolation.remove_review_temp_tree(root)
