"""Report-only sweep and exact-SHA comment verdict tests (#8509)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.orchestration import integration_sweep as sweep
from scripts.review.record_cf_verdict import build_comment

SHA = "a" * 40
OTHER = "b" * 40
START = "2026-09-23T12:00:00.000001+00:00"


def comment(
    *, sha=SHA, task="review-one", started=START, verdict="APPROVED", login="fleet", association="MEMBER", edited=False
):
    body = build_comment(
        sha=sha,
        task_id=task,
        started=started,
        verdict=verdict,
        model="gpt-6-sol",
        family="openai",
        reply="VERDICT: APPROVE",
    )
    return {
        "id": task,
        "body": body,
        "user": {"login": login},
        "author_association": association,
        "created_at": "2026-09-23T13:00:00Z",
        "updated_at": "2026-09-23T13:01:00Z" if edited else "2026-09-23T13:00:00Z",
    }


def pr(**updates):
    data = {
        "number": 42,
        "headRefOid": SHA,
        "headRefName": "codex/42",
        "baseRefName": "main",
        "isDraft": False,
        "autoMergeRequest": None,
        "mergeable": "MERGEABLE",
        "statusCheckRollup": [
            {"name": "CI Gate", "status": "COMPLETED", "conclusion": "SUCCESS", "startedAt": "2026-09-23T12:00:00Z"}
        ],
    }
    data.update(updates)
    return data


def test_latest_started_rejects_approval_then_rejection():
    rows = [
        comment(),
        comment(task="review-two", started="2026-09-23T12:00:01.000001+00:00", verdict="CHANGES_REQUESTED"),
    ]
    assert sweep.lookup_verdict(rows, SHA, "fleet").state == "CHANGES_REQUESTED"


def test_late_recorded_older_approval_does_not_overwrite_rejection():
    rows = [
        comment(task="reject", started="2026-09-23T12:00:01.000001+00:00", verdict="BLOCKED"),
        comment(task="old-approval"),
    ]
    assert sweep.lookup_verdict(rows, SHA, "fleet").state == "BLOCKED"


def test_same_second_microseconds_and_tie_rejection():
    later = "2026-09-23T12:00:00.000002+00:00"
    assert (
        sweep.lookup_verdict([comment(verdict="BLOCKED"), comment(task="later", started=later)], SHA, "fleet").state
        == "APPROVED"
    )
    assert sweep.lookup_verdict([comment(), comment(task="tie", verdict="BLOCKED")], SHA, "fleet").state == "BLOCKED"


@pytest.mark.parametrize("bad", ["edited", "malformed"])
def test_edited_or_unparseable_marker_makes_sha_unknown(bad):
    item = comment(edited=bad == "edited")
    if bad == "malformed":
        item["body"] = item["body"].replace("verdict=APPROVED", "verdict=MAYBE")
    assert sweep.lookup_verdict([item], SHA, "fleet").state == "unknown"


def test_lookup_failure_and_partial_data_unknown():
    assert sweep.lookup_verdict(None, SHA, "fleet").state == "unknown"
    assert sweep.lookup_verdict([comment()], SHA, "fleet", complete=False).state == "unknown"
    assert sweep.lookup_verdict([[comment()]], SHA, "fleet").state == "unknown"


def test_legacy_unmarked_comment_never_approves():
    old = {"body": f"### Cross-family review\nhead: {SHA}\nVERDICT: APPROVED"}
    assert sweep.lookup_verdict([old], SHA, "fleet").state == "CF-unrecorded"
    assert sweep.lookup_verdict([{"body": "VERDICT: APPROVE"}], SHA, "fleet").state == "CF-unrecorded"
    assert sweep.lookup_verdict([comment(sha=OTHER)], SHA, "fleet").state == "CF-stale"


@pytest.mark.parametrize("login,association", [("outsider", "MEMBER"), ("fleet", "NONE"), ("fleet", "CONTRIBUTOR")])
def test_untrusted_marker_ignored_and_listed(login, association):
    verdict = sweep.lookup_verdict([comment(login=login, association=association)], SHA, "fleet")
    assert verdict.state == "needs-CF"
    assert verdict.untrusted_markers == ("review-one",)


def test_untrusted_other_head_marker_does_not_claim_stale_review():
    verdict = sweep.lookup_verdict([comment(sha=OTHER, login="outsider")], SHA, "fleet")
    assert verdict.state == "needs-CF"
    assert verdict.untrusted_markers == ("review-one",)


def test_state_preserves_blockers_even_when_queued_or_armed():
    verdict = sweep.Verdict("CHANGES_REQUESTED")
    queued = sweep.classify_pr(pr(isDraft=True), verdict, queued=True, observed_at=START)
    armed = sweep.classify_pr(pr(autoMergeRequest={"enabledAt": START}), verdict, queued=False, observed_at=START)
    assert queued.state == "blocked draft"
    assert "CHANGES_REQUESTED" in queued.blockers
    assert armed.state == "armed"
    assert "CHANGES_REQUESTED" in armed.blockers


def _gate(conclusion: str, started_at: str, workflow: str | None) -> dict:
    row = {"name": "CI Gate", "status": "COMPLETED", "conclusion": conclusion, "startedAt": started_at}
    if workflow is not None:
        row["workflowName"] = workflow
    return row


def test_cross_workflow_failure_is_not_hidden_by_a_later_success():
    item = pr(
        statusCheckRollup=[
            _gate("FAILURE", "2026-09-23T12:00:00Z", "CI"),
            _gate("SUCCESS", "2026-09-23T13:00:00Z", "Nightly"),
        ]
    )
    assert sweep._check_blockers(item) == ["CI red CI Gate"]


def test_timestamp_tie_failure_is_not_hidden_by_list_order():
    item = pr(
        statusCheckRollup=[
            _gate("FAILURE", "2026-09-23T13:00:00Z", "CI"),
            _gate("SUCCESS", "2026-09-23T13:00:00Z", "CI"),
        ]
    )
    assert sweep._check_blockers(item) == ["CI red CI Gate"]


def test_named_check_without_workflow_keeps_a_red_row():
    item = pr(
        statusCheckRollup=[
            _gate("FAILURE", "2026-09-23T12:00:00Z", None),
            _gate("SUCCESS", "2026-09-23T13:00:00Z", None),
        ]
    )
    assert sweep._check_blockers(item) == ["CI red CI Gate"]


def test_ci_red_pending_and_ready():
    approved = sweep.Verdict("APPROVED")
    red = pr(
        statusCheckRollup=[{"name": "CI Gate", "status": "COMPLETED", "conclusion": "FAILURE", "startedAt": START}]
    )
    pending = pr(statusCheckRollup=[])
    assert sweep.classify_pr(red, approved, queued=False, observed_at=START).state == "CI-red CI Gate"
    assert sweep.classify_pr(pending, approved, queued=False, observed_at=START).state == "CI-pending"
    assert sweep.classify_pr(pr(), approved, queued=False, observed_at=START).state == "ready"


def test_moved_head_between_observation_and_queue_lookup_reports_unknown():
    def runner(args):
        if args[:3] == ["gh", "api", "graphql"]:
            return json.dumps({"data": {"repository": {"pullRequest": {"headRefOid": OTHER, "isInMergeQueue": False}}}})
        raise AssertionError(args)

    adapter = sweep.GitHubAdapter(Path.cwd(), runner=runner)
    with pytest.raises(sweep.SweepError, match="head moved"):
        adapter.queue_membership("owner/repo", pr())


def test_paged_comments_reject_unpaginated_response():
    adapter = sweep.GitHubAdapter(Path.cwd(), runner=lambda args: json.dumps([comment()]))
    with pytest.raises(sweep.SweepError, match="pagination"):
        adapter.comments("owner/repo", 42)


def test_apply_refused_and_workflow_is_report_only(capsys):
    assert sweep.main(["--repo", "owner/repo", "--apply"]) == 2
    assert "report-only" in capsys.readouterr().out
    workflow = Path(".github/workflows/integration-sweep.yml").read_text()
    assert "--apply" not in workflow
    assert "workflow_dispatch:\n    inputs:" not in workflow
    assert "GITHUB_STEP_SUMMARY" in workflow


def test_run_lookup_failure_is_unknown_with_queue_blocker():
    class Adapter:
        def list_open_prs(self, repository):
            return [pr()]

        def identity(self):
            return "fleet"

        def comments(self, repository, number):
            raise sweep.SweepError("failure")

        def queue_membership(self, repository, item):
            raise sweep.SweepError("failure")

    rows = sweep.run(Adapter(), "owner/repo", now=datetime(2026, 9, 23, tzinfo=UTC))
    assert rows[0].state == "CF-unknown"
    assert "queue lookup unknown" in rows[0].blockers
