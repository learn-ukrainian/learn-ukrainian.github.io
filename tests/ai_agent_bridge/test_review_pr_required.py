"""Phase 5: formal PR CF review without sealed target warns (not reject) (#5486)."""

from __future__ import annotations

import pytest
from ai_agent_bridge import _review_safety as safety


def test_looks_like_pr_cf_review_detects_github_pr_url() -> None:
    body = "Please review https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/5480"
    assert safety.looks_like_pr_cf_review(body) is True


def test_assert_pr_cf_review_warns_without_target(capsys: pytest.CaptureFixture[str]) -> None:
    body = (
        "Formal cross-family PR review for "
        "https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/5480\n"
        "VERDICT: APPROVED"
    )
    # Warn-not-reject: agent work is not discarded.
    assert (
        safety.assert_formal_review_ask_payload(
            body,
            msg_type="review",
            task_id="review-pr-5480-manual",
            review=True,
            has_target=False,
        )
        is True
    )
    err = capsys.readouterr().err
    assert "prefer" in err and "review-pr" in err
    assert "warn-not-reject" in err or "not discarded" in err


def test_assert_pr_cf_review_allows_with_target(capsys: pytest.CaptureFixture[str]) -> None:
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
    assert "prefer" not in capsys.readouterr().err


def test_content_review_without_pr_url_still_allowed(capsys: pytest.CaptureFixture[str]) -> None:
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
    assert "prefer" not in capsys.readouterr().err


def test_legacy_escape_silences_pr_url_warning(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
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
    assert "prefer" not in capsys.readouterr().err
    monkeypatch.delenv("BRIDGE_ALLOW_LEGACY_REVIEW_ASK", raising=False)
