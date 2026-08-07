"""AGY sealed formal review is fail-closed with a substitute path."""

from __future__ import annotations

import pytest

from scripts.ai_agent_bridge import _agy


def test_ask_agy_refuses_review_flag_before_send() -> None:
    with pytest.raises(ValueError, match="agy_isolated_review_unsupported"):
        _agy.ask_agy("please review this PR", review=True, task_id="t")


def test_ask_agy_refuses_review_pr_number() -> None:
    with pytest.raises(ValueError, match="review-pr"):
        _agy.ask_agy("review", review_pr_number=5547, task_id="t")


def test_agy_endpoint_formal_review_eligible_for_pinned_models() -> None:
    """Operator 2026-08-06: AGY formal eligible; catalog pins Opus 4.6 only."""
    from scripts.fleet_comms.endpoints import load_endpoint_registry
    from scripts.review.reviewer_resolver import REVIEW_CANDIDATES

    registry = load_endpoint_registry()
    endpoint, _ = registry.resolve("agy")
    assert endpoint.formal_review_eligible is True
    # ask-agy still refuses sealed review flag; formal CF is review-pr path only.
    opus = REVIEW_CANDIDATES["claude-opus-4.6-thinking"]
    assert opus.route == "agy"
    assert opus.formal_review_eligible is True
    gemini = REVIEW_CANDIDATES["gemini-3.6-flash"]
    assert gemini.route == "agy"
    assert gemini.formal_review_eligible is False
