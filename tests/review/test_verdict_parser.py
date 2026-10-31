"""Incomplete review replies cannot authorize a merge (#12254)."""

import pytest

from scripts.review.record_cf_verdict import RecordError, normalize_verdict


def test_truncated_findings_block_beside_approve_is_inconclusive():
    """Defect class: a cut-off review reads as an approval."""
    reply = (
        'VERDICT: APPROVE\n\n```json\n'
        '{"schema_version":"code-review-findings.v1",'
        '"findings":[{"priority":"P1","body":"cut off'
    )
    with pytest.raises(RecordError, match=r"inconclusive.*findings"):
        normalize_verdict(reply)


def test_reply_stating_incomplete_review_is_inconclusive():
    """Defect class: an unfinished review reads as an approval."""
    reply = "VERDICT: APPROVE\n\nI could not finish checking the lesson activities."
    with pytest.raises(RecordError, match=r"inconclusive.*incomplete"):
        normalize_verdict(reply)
