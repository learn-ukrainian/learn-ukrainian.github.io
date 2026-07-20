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


def test_agy_endpoint_not_formal_review_eligible() -> None:
    from scripts.fleet_comms.endpoints import load_endpoint_registry

    registry = load_endpoint_registry()
    endpoint, _ = registry.resolve("agy")
    assert endpoint.formal_review_eligible is False
