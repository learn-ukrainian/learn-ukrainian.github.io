"""Tests for pointer-only review-pr entrypoint."""

from __future__ import annotations

import pytest
from ai_agent_bridge import _review_pr as review_pr
from ai_agent_bridge._review_safety import ReviewSafetyError


def test_parse_pr_number() -> None:
    assert review_pr.parse_pr_number("5443") == 5443
    assert review_pr.parse_pr_number("#99") == 99
    with pytest.raises(ReviewSafetyError):
        review_pr.parse_pr_number("not-a-pr")


def test_resolve_reviewer_auto() -> None:
    assert review_pr.resolve_reviewer("auto", claude_available=None) == "codex"
    assert review_pr.resolve_reviewer("auto", claude_available=False) == "glm"
    assert review_pr.resolve_reviewer("glm") == "glm"


def test_build_review_pr_prompt_has_contract_and_cap() -> None:
    model, effort = review_pr.formal_cf_pin("codex")
    prompt = review_pr.build_review_pr_prompt(
        5443,
        reviewer="codex",
        model=model,
        effort=effort,
    )
    assert "READ-ONLY REVIEW CONTRACT" in prompt
    assert "pull/5443" in prompt
    assert "VERDICT:" in prompt
    assert "gpt-5.6-terra" in prompt
    assert "effort=high" in prompt
