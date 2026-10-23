"""Phase 5: formal PR CF review without sealed target warns (not reject) (#5486)."""

from __future__ import annotations

import pytest

from scripts.ai_agent_bridge import _review_safety as safety


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
    # #7010: the direct ask IS the formal path now; the warning requires a
    # named target and must not steer to the retired sealed command.
    assert "review-pr retired" in err
    assert "head SHA" in err
    assert "prefer" not in err
    assert "warn-not-reject" in err or "not discarded" in err
