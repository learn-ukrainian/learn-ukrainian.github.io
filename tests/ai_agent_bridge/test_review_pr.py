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
    assert review_pr.resolve_reviewer("auto", claude_available=None) == "glm"
    assert review_pr.resolve_reviewer("auto", claude_available=False) == "glm"
    assert review_pr.resolve_reviewer("glm") == "glm"


def test_formal_review_authority_key_is_bounded_and_opaque() -> None:
    key = review_pr._formal_review_authority_key(
        "learn-ukrainian/learn-ukrainian.github.io",
        6191,
        "a" * 40,
        "b" * 64,
    )
    assert key.startswith("formal-review:")
    assert len(key) == len("formal-review:") + 64
    assert "/" not in key


def test_canonical_review_response_unwraps_only_single_json_object() -> None:
    payload = '{"schema_version":"code-review-findings.v1"}'
    assert review_pr._canonical_review_response_text(f"```json\n{payload}\n```") == payload
    leading_text = f"Reviewed the exact head.\n{payload}"
    assert review_pr._canonical_review_response_text(leading_text) == payload
    with_extra_text = f"Here is the verdict:\n```json\n{payload}\n```"
    assert review_pr._canonical_review_response_text(with_extra_text) == with_extra_text
    trailing_text = f"{payload}\nThis is extra."
    assert review_pr._canonical_review_response_text(trailing_text) == trailing_text


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
    assert "code-review-findings.v1" in prompt
    assert "gpt-5.6-terra" in prompt
    assert "effort=high" in prompt
    assert "confidence` value MUST be a JSON number" in prompt
    assert 'correctness":"correct"' in prompt
    assert 'enum aliases such as `"pass"`' in prompt
