"""Tests for CF-before-build preflight."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from scripts.build import cf_preflight as cf


def test_evaluate_comment_bodies_approve_on_exact_head():
    head = "a" * 40
    bodies = [
        f"Reviewer verdict: APPROVE\nExact head: {head}\nLooks good.",
    ]
    result = cf.evaluate_comment_bodies(bodies, head=head)
    assert result.clear is True


def test_evaluate_comment_bodies_request_changes_blocks():
    head = "b" * 40
    bodies = [
        f"Reviewer verdict: APPROVE\nhead: {head}",
        f"Reviewer verdict: REQUEST_CHANGES\nExact head: {head}\nP2 remains.",
    ]
    result = cf.evaluate_comment_bodies(bodies, head=head)
    assert result.clear is False
    assert "REQUEST_CHANGES" in result.reason


def test_clearance_file_requires_matching_head(tmp_path: Path):
    head = "c" * 40
    path = tmp_path / "cf_clearance.json"
    path.write_text(json.dumps({"head": head, "verdict": "APPROVE"}), encoding="utf-8")
    ok = cf.load_clearance_file(path)
    assert ok.clear and ok.head == head

    bad = cf.check_cf_preflight(
        repo_root=tmp_path,
        head="d" * 40,
        clearance_path=path,
        allow_github=False,
    )
    assert bad.clear is False
    assert "!= build HEAD" in bad.reason


def test_check_cf_preflight_module_dir_clearance(tmp_path: Path):
    head = "e" * 40
    module = tmp_path / "module"
    module.mkdir()
    (module / "cf_clearance.json").write_text(
        json.dumps({"head": head, "verdict": "APPROVED"}),
        encoding="utf-8",
    )
    result = cf.check_cf_preflight(
        repo_root=tmp_path,
        head=head,
        module_dir=module,
        allow_github=False,
    )
    assert result.clear is True


def test_chronology_later_request_changes_comment_blocks_earlier_approve_review():
    head = "f" * 40
    t0 = datetime.fromisoformat("2026-09-17T11:00:00+00:00")
    t1 = datetime.fromisoformat("2026-09-17T12:00:00+00:00")
    events = [
        cf.CfEvidenceEvent("approve", head, t0, "review", state="APPROVED"),
        cf.CfEvidenceEvent("request_changes", head, t1, "comment"),
    ]
    result = cf.evaluate_evidence_events(events, head=head)
    assert result.clear is False


def test_chronology_later_approve_clears_earlier_request_changes():
    head = "1" * 40
    t0 = datetime.fromisoformat("2026-09-17T11:00:00+00:00")
    t1 = datetime.fromisoformat("2026-09-17T12:00:00+00:00")
    events = [
        cf.CfEvidenceEvent("request_changes", head, t0, "comment"),
        cf.CfEvidenceEvent("approve", head, t1, "review", state="APPROVED"),
    ]
    assert cf.evaluate_evidence_events(events, head=head).clear is True


def test_historical_head_in_prose_does_not_clear_build_head():
    build_head = "a" * 40
    reviewed_head = "b" * 40
    bodies = [
        f"Reviewer verdict: APPROVE\nExact head: {reviewed_head}\n"
        f"Previously reviewed head: {build_head}"
    ]
    result = cf.evaluate_comment_bodies(bodies, head=build_head)
    assert result.clear is False


def test_formal_approved_state_without_verdict_text_clears():
    head = "2" * 40
    events = cf.events_from_github_payloads(
        comments=[],
        reviews=[
            {
                "state": "APPROVED",
                "commit_id": head,
                "submitted_at": "2026-09-17T12:00:00Z",
                "body": "Looks good.",
            }
        ],
    )
    assert cf.evaluate_evidence_events(events, head=head).clear is True


def test_dismissed_approve_does_not_clear():
    head = "3" * 40
    events = cf.events_from_github_payloads(
        comments=[],
        reviews=[
            {
                "state": "DISMISSED",
                "commit_id": head,
                "submitted_at": "2026-09-17T12:00:00Z",
                "body": "Reviewer verdict: APPROVE\nExact head: " + head,
            }
        ],
    )
    assert cf.evaluate_evidence_events(events, head=head).clear is False


def test_mixed_channel_request_changes_comment_after_approve_review():
    head = "4" * 40
    events = cf.events_from_github_payloads(
        comments=[
            {
                "body": f"Reviewer verdict: REQUEST_CHANGES\nExact head: {head}",
                "created_at": "2026-09-17T12:00:00Z",
            }
        ],
        reviews=[
            {
                "state": "APPROVED",
                "commit_id": head,
                "submitted_at": "2026-09-17T11:00:00Z",
                "body": "ok",
            }
        ],
    )
    assert cf.evaluate_evidence_events(events, head=head).clear is False
