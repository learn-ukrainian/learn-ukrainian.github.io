"""Tests for scripts/review/findings.py — append-only adjudication ledger.

Named distinctly from tests/test_review_findings.py, which covers the
unrelated curriculum-content pipeline.review_findings module.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.review.findings import FindingsLedger, FindingsLedgerError


def test_raise_finding_then_list_all_ids():
    ledger = FindingsLedger()
    ledger.raise_finding("F1", summary="bug one", source="reviewer:deepseek")
    ledger.raise_finding("F2", summary="bug two", source="reviewer:deepseek")
    assert ledger.all_finding_ids() == ("F1", "F2")


def test_duplicate_raise_rejected():
    ledger = FindingsLedger()
    ledger.raise_finding("F1", summary="bug one", source="reviewer:deepseek")
    with pytest.raises(FindingsLedgerError):
        ledger.raise_finding("F1", summary="different bug reusing the id", source="reviewer:grok")


def test_adjudicate_unknown_finding_rejected():
    ledger = FindingsLedger()
    with pytest.raises(FindingsLedgerError):
        ledger.adjudicate("ghost", disposition="follow_up", rationale="n/a")


def test_adjudicate_requires_non_empty_rationale():
    ledger = FindingsLedger()
    ledger.raise_finding("F1", summary="bug", source="reviewer:grok")
    with pytest.raises(FindingsLedgerError):
        ledger.adjudicate("F1", disposition="follow_up", rationale="   ")


def test_apply_requires_adjudication_first():
    """The core anti-'apply as-is' guard: no adjudication, no apply."""
    ledger = FindingsLedger()
    ledger.raise_finding("F1", summary="bug", source="reviewer:grok")
    with pytest.raises(FindingsLedgerError):
        ledger.apply("F1")


def test_apply_requires_in_scope_blocker_disposition():
    ledger = FindingsLedger()
    ledger.raise_finding("F1", summary="bug", source="reviewer:grok")
    ledger.adjudicate("F1", disposition="follow_up", rationale="not urgent, track separately")
    with pytest.raises(FindingsLedgerError):
        ledger.apply("F1")


def test_apply_succeeds_after_in_scope_blocker_adjudication():
    ledger = FindingsLedger()
    ledger.raise_finding("F1", summary="bug", source="reviewer:grok")
    ledger.adjudicate("F1", disposition="in_scope_blocker", rationale="breaks the acceptance criteria")
    ledger.apply("F1")
    assert ledger.is_applied("F1") is True


def test_stop_and_escalate_cannot_be_applied():
    ledger = FindingsLedger()
    ledger.raise_finding("F1", summary="bug", source="reviewer:grok")
    ledger.adjudicate("F1", disposition="stop_and_escalate", rationale="fix crosses owner boundary")
    with pytest.raises(FindingsLedgerError):
        ledger.apply("F1")


def test_re_adjudication_preserves_prior_history_not_overwrite():
    ledger = FindingsLedger()
    ledger.raise_finding("F1", summary="bug", source="reviewer:grok")
    ledger.adjudicate("F1", disposition="follow_up", rationale="initial pass: looked minor")
    ledger.adjudicate("F1", disposition="in_scope_blocker", rationale="cycle 2: actually blocks acceptance criteria")
    adjudications = [e for e in ledger.events() if e.finding_id == "F1" and e.event == "adjudicated"]
    assert len(adjudications) == 2
    assert adjudications[0].rationale == "initial pass: looked minor"
    assert adjudications[1].rationale == "cycle 2: actually blocks acceptance criteria"
    # latest_disposition reflects the most recent, but the first is not erased.
    assert ledger.latest_disposition("F1") == "in_scope_blocker"


def test_skip_requires_raised_and_rationale():
    ledger = FindingsLedger()
    with pytest.raises(FindingsLedgerError):
        ledger.skip("ghost", rationale="n/a")
    ledger.raise_finding("F1", summary="bug", source="reviewer:grok")
    with pytest.raises(FindingsLedgerError):
        ledger.skip("F1", rationale="")
    ledger.skip("F1", rationale="deferred to follow-up ticket #9999")
    assert any(e.event == "skipped" for e in ledger.events())


def test_unadjudicated_surfaces_findings_with_no_verdict():
    """Simulates 'challenger/reviewer unavailable' — the finding must show up,
    not vanish from the report."""
    ledger = FindingsLedger()
    ledger.raise_finding("F1", summary="reviewer was down for this one", source="self-review")
    ledger.raise_finding("F2", summary="this one got adjudicated", source="reviewer:grok")
    ledger.adjudicate("F2", disposition="follow_up", rationale="minor style nit")
    assert ledger.unadjudicated() == ("F1",)


def test_render_report_includes_every_finding_and_full_history():
    ledger = FindingsLedger()
    ledger.raise_finding("F1", summary="unadjudicated finding", source="self-review")
    ledger.raise_finding("F2", summary="applied finding", source="reviewer:grok")
    ledger.adjudicate("F2", disposition="in_scope_blocker", rationale="real bug")
    ledger.apply("F2")
    ledger.raise_finding("F3", summary="skipped finding", source="reviewer:grok")
    ledger.skip("F3", rationale="false positive, writer's choice was correct")

    report = ledger.render_report()
    assert "F1" in report and "UNADJUDICATED" in report
    assert "F2" in report and "applied" in report
    assert "F3" in report and "skipped" in report and "false positive" in report


def test_render_report_empty_ledger():
    ledger = FindingsLedger()
    assert ledger.render_report() == "(no findings raised)"


def test_render_report_raised_then_skipped_still_shows_unadjudicated():
    """A skip is not an adjudication — latest_disposition stays None, so the
    report must still flag the finding as UNADJUDICATED even though it also
    carries a skip rationale. Before the fix, render_report only checked
    ``len(history) == 1``, so a raised-then-skipped finding (history length 2)
    silently lost its UNADJUDICATED marker."""
    ledger = FindingsLedger()
    ledger.raise_finding("F1", summary="raised then skipped, never adjudicated", source="self-review")
    ledger.skip("F1", rationale="deferred without a reviewer verdict")

    assert ledger.latest_disposition("F1") is None
    report = ledger.render_report()
    assert "F1" in report
    assert "skipped: deferred without a reviewer verdict" in report
    assert "UNADJUDICATED" in report
