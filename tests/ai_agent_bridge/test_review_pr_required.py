"""Phase 5: formal PR CF review without sealed target is refused (#5486)."""

from __future__ import annotations

import pytest
from ai_agent_bridge import _review_safety as safety


def test_looks_like_pr_cf_review_detects_github_pr_url() -> None:
    body = "Please review https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/5480"
    assert safety.looks_like_pr_cf_review(body) is True


def test_assert_pr_cf_review_refuses_without_target() -> None:
    body = (
        "Formal cross-family PR review for "
        "https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/5480\n"
        "VERDICT: APPROVED"
    )
    with pytest.raises(safety.ReviewSafetyError, match="formal_pr_review_requires_review_pr"):
        safety.assert_formal_review_ask_payload(
            body,
            msg_type="review",
            task_id="review-pr-5480-manual",
            review=True,
            has_target=False,
        )


def test_assert_pr_cf_review_allows_with_target() -> None:
    body = "https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/5480 thin pointer"
    assert (
        safety.assert_formal_review_ask_payload(
            body,
            msg_type="review",
            task_id="review-pr-5480",
            review=True,
            has_target=True,
        )
        is True
    )


def test_content_review_without_pr_url_still_allowed() -> None:
    body = "Please review this curriculum module for calques and naturalness."
    assert (
        safety.assert_formal_review_ask_payload(
            body,
            msg_type="review",
            task_id="content-review-bio-1",
            review=True,
            has_target=False,
        )
        is True
    )


def test_legacy_escape_allows_pr_url_without_target(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRIDGE_ALLOW_LEGACY_REVIEW_ASK", "1")
    body = "https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/1"
    assert (
        safety.assert_formal_review_ask_payload(
            body,
            msg_type="review",
            task_id="review-legacy",
            review=True,
            has_target=False,
        )
        is True
    )
    monkeypatch.delenv("BRIDGE_ALLOW_LEGACY_REVIEW_ASK", raising=False)
