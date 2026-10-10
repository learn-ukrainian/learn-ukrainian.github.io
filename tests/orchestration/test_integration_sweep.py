"""Report-only sweep and exact-SHA comment verdict tests (#8509)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.github_check_rollup import group_collapsed_by_name
from scripts.orchestration import integration_sweep as sweep
from scripts.review.record_cf_verdict import build_comment

SHA = "a" * 40
OTHER = "b" * 40
START = "2026-09-23T12:00:00.000001+00:00"


def comment(
    *, sha=SHA, task="review-one", started=START, verdict="APPROVED", login="fleet", association="MEMBER", edited=False,
    review_mode="cross_family", family="openai",
):
    body = build_comment(
        sha=sha,
        task_id=task,
        started=started,
        verdict=verdict,
        model="gpt-6.1-sol",
        family=family,
        reply="VERDICT: APPROVE",
        review_mode=review_mode,
    )
    return {
        "id": task,
        "body": body,
        "user": {"login": login},
        "author_association": association,
        "created_at": "2026-09-23T13:00:00Z",
        "updated_at": "2026-09-23T13:01:00Z" if edited else "2026-09-23T13:00:00Z",
    }


@pytest.mark.parametrize("mode", ["cross_family", "red_team"])
def test_review_mode_round_trip_and_legacy_marker(mode):
    item = comment(review_mode=mode)
    marker = sweep.parse_marker(item["body"])
    assert marker is not None
    assert marker.get("review_mode", "cross_family") == mode
    verdict = sweep.lookup_verdict([item], SHA, "fleet")
    assert verdict.state == "APPROVED"
    assert verdict.review_mode == mode
    assert sweep.classify_pr(pr(), verdict, queued=False, observed_at=START).state == "ready"


@pytest.mark.parametrize("case", ["missing_mode", "wrong_heading", "wrong_label", "invalid_mode", "duplicate_mode"])
def test_red_team_marker_tampering_is_unknown(case):
    item = comment(review_mode="red_team")
    replacements = {
        "missing_mode": (" review_mode=red_team", ""),
        "wrong_heading": ("### Adversarial red-team review", "### Cross-family review"),
        "wrong_label": ("Review mode: red_team", "Review mode: cross_family"),
        "invalid_mode": ("review_mode=red_team", "review_mode=anything"),
        "duplicate_mode": ("review_mode=red_team", "review_mode=red_team review_mode=red_team"),
    }
    item["body"] = item["body"].replace(*replacements[case])
    assert sweep.parse_marker(item["body"]) is None
    assert sweep.lookup_verdict([item], SHA, "fleet").state == "unknown"


@pytest.mark.parametrize("mode", ["cross_family", "red_team"])
def test_unknown_reviewer_marker_never_approves(mode):
    assert sweep.lookup_verdict([comment(review_mode=mode, family="unknown")], SHA, "fleet").state == "unknown"


def test_red_team_keeps_trust_head_and_latest_rejection_gates():
    assert sweep.lookup_verdict([comment(review_mode="red_team", login="outsider")], SHA, "fleet").state == "needs-CF"
    assert sweep.lookup_verdict([comment(review_mode="red_team", sha=OTHER)], SHA, "fleet").state == "CF-stale"
    assert sweep.lookup_verdict([comment(review_mode="red_team", edited=True)], SHA, "fleet").state == "unknown"
    rows = [comment(review_mode="red_team"),
            comment(task="later", started="2026-09-23T12:00:01.000001+00:00", verdict="BLOCKED")]
    assert sweep.lookup_verdict(rows, SHA, "fleet").state == "BLOCKED"


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


def test_keeper_format_approve_token_reads_as_approved():
    item = comment(verdict="APPROVE")
    assert item["body"].endswith("verdict=APPROVE model=gpt-6.1-sol family=openai -->")
    assert sweep.parse_marker(item["body"])["verdict"] == "APPROVED"
    assert sweep.lookup_verdict([item], SHA, "fleet").state == "APPROVED"
    later = "2026-09-23T12:00:01.000001+00:00"
    rows = [comment(verdict="APPROVE"), comment(task="later", started=later, verdict="BLOCKED")]
    assert sweep.lookup_verdict(rows, SHA, "fleet").state == "BLOCKED"
    assert sweep.lookup_verdict([comment(verdict="APPROVE", edited=True)], SHA, "fleet").state == "unknown"


PR_10095_SHA = "b5a18af03c961fa4b228a3ea6669f2c11ef5f532"
PR_10095_TRAILER = (
    f"<!-- cf-verdict v1 sha={PR_10095_SHA} task=pravopys-9638-cf-basefix "
    "started=2026-10-08T08:24:21.755967+00:00 verdict=APPROVE model=claude-opus-5-5 family=anthropic -->"
)


def unformatted(trailer=PR_10095_TRAILER, edited=False):
    return {
        "id": 6055900811,
        "body": f"Exact-head review of the base fix.\n\nNo blocking findings.\n\n{trailer}",
        "user": {"login": "fleet"},
        "author_association": "MEMBER",
        "created_at": "2026-10-08T08:40:00Z",
        "updated_at": "2026-10-08T08:41:00Z" if edited else "2026-10-08T08:40:00Z",
    }


def test_unformatted_approve_trailer_neither_poisons_nor_approves():
    assert sweep.parse_marker(unformatted()["body"]) is None
    readable = comment(sha=PR_10095_SHA, task="later-review", started="2026-10-08T09:00:00.000001+00:00")
    assert sweep.lookup_verdict([unformatted(), readable], PR_10095_SHA, "fleet").state == "APPROVED"
    assert sweep.lookup_verdict([unformatted()], PR_10095_SHA, "fleet").state == "needs-CF"
    with_prose = unformatted()
    with_prose["body"] = "VERDICT: APPROVE\n" + with_prose["body"]
    assert sweep.lookup_verdict([with_prose], PR_10095_SHA, "fleet").state == "CF-unrecorded"
    assert sweep.lookup_verdict([unformatted(edited=True), readable], PR_10095_SHA, "fleet").state == "unknown"


@pytest.mark.parametrize("token", ["APPROVES", "approve", "MAYBE", "BLOCKED", "CHANGES_REQUESTED"])
def test_unformatted_non_approve_trailer_still_poisons_the_head(token):
    item = unformatted(PR_10095_TRAILER.replace("verdict=APPROVE", f"verdict={token}"))
    readable = comment(sha=PR_10095_SHA, task="later-review", started="2026-10-08T09:00:00.000001+00:00")
    assert sweep.lookup_verdict([item], PR_10095_SHA, "fleet").state == "unknown"
    assert sweep.lookup_verdict([item, readable], PR_10095_SHA, "fleet").state == "unknown"


@pytest.mark.parametrize("token", ["APPROVES", "approve", "MAYBE"])
def test_keeper_format_unknown_token_stays_unreadable(token):
    keeper = comment(verdict=token)
    assert sweep.parse_marker(keeper["body"]) is None
    assert sweep.lookup_verdict([keeper, comment(task="other")], SHA, "fleet").state == "unknown"


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


def test_cross_workflow_in_progress_is_pending():
    """Nightly still running must not read green beside a SUCCESS of the same name."""
    item = pr(
        statusCheckRollup=[
            {
                "name": "CI Gate",
                "status": "IN_PROGRESS",
                "workflowName": "Nightly",
                "startedAt": "2026-09-23T13:00:00Z",
            },
            _gate("SUCCESS", "2026-09-23T12:00:00Z", "CI"),
        ]
    )
    assert sweep._check_blockers(item) == ["CI pending CI Gate"]


def test_single_green_row_without_timestamp_is_green():
    item = pr(
        statusCheckRollup=[{"name": "CI Gate", "status": "COMPLETED", "conclusion": "SUCCESS", "workflowName": "CI"}]
    )
    assert sweep._check_blockers(item) == []


def test_row_with_neither_status_nor_conclusion_is_unknown():
    item = pr(statusCheckRollup=[{"name": "CI Gate", "workflowName": "CI", "startedAt": "2026-09-23T12:00:00Z"}])
    assert sweep._check_blockers(item) == ["CI unknown CI Gate"]


def test_group_collapsed_by_name_drops_blanks_matrix_and_keeps_survivors():
    blank_name = {"name": "  ", "status": "COMPLETED", "conclusion": "SUCCESS", "workflowName": "CI"}
    empty_name = {"name": "", "conclusion": "FAILURE"}
    blank_context = {"context": "   "}
    matrix = {
        "name": "pytest (${{ matrix.shard }})",
        "conclusion": "CANCELLED",
        "workflowName": "CI",
        "startedAt": "2026-09-23T12:00:00Z",
    }
    nightly = {
        "name": "CI Gate",
        "status": "IN_PROGRESS",
        "workflowName": "Nightly",
        "startedAt": "2026-09-23T13:00:00Z",
    }
    ci = _gate("SUCCESS", "2026-09-23T12:00:00Z", "CI")
    named, other = group_collapsed_by_name(
        [blank_name, empty_name, blank_context, matrix, "not-a-dict", 7, nightly, ci]
    )
    assert list(named) == ["CI Gate"]
    assert named["CI Gate"] == [nightly, ci]
    assert other == [blank_name, empty_name, blank_context, "not-a-dict", 7]
    assert all("${{" not in str(row.get("name") or "") for row in other if isinstance(row, dict))


def test_ci_red_pending_and_ready():
    approved = sweep.Verdict("APPROVED")
    red = pr(
        statusCheckRollup=[{"name": "CI Gate", "status": "COMPLETED", "conclusion": "FAILURE", "startedAt": START}]
    )
    pending = pr(statusCheckRollup=[])
    assert sweep.classify_pr(red, approved, queued=False, observed_at=START).state == "CI-red CI Gate"
    assert sweep.classify_pr(pending, approved, queued=False, observed_at=START).state == "CI-pending"
    assert sweep.classify_pr(pr(), approved, queued=False, observed_at=START).state == "ready"


@pytest.mark.parametrize("name", ["Component shadow (advisory)"])
@pytest.mark.parametrize("status,conclusion", [("COMPLETED", "FAILURE"), ("IN_PROGRESS", ""), ("", "")])
def test_advisory_checks_do_not_block_readiness(name, status, conclusion):
    item = pr()
    item["statusCheckRollup"].append({"name": name, "status": status, "conclusion": conclusion, "workflowName": "CI"})
    report = sweep.classify_pr(item, sweep.Verdict("APPROVED"), queued=False, observed_at=START)
    assert report.state == "ready"
    assert report.blockers == ()


def test_advisory_failure_does_not_hide_other_blockers():
    advisory = {"name": "Component shadow (advisory)", "status": "COMPLETED", "conclusion": "FAILURE", "workflowName": "CI"}
    assert sweep._check_blockers(pr(statusCheckRollup=[advisory])) == ["CI pending CI Gate"]
    item = pr()
    item["statusCheckRollup"].extend([
        advisory,
        {"name": "Build", "status": "COMPLETED", "conclusion": "FAILURE"},
    ])
    report = sweep.classify_pr(item, sweep.Verdict("APPROVED"), queued=False, observed_at=START)
    assert report.state == "CI-red Build"
    assert report.blockers == ("CI red Build",)


def test_moved_head_between_observation_and_queue_lookup_reports_unknown():
    def runner(args):
        if isinstance(args, sweep.Request) and args.verb == "read-membership-head":
            return json.dumps({"data": {"repository": {"pullRequest": {"headRefOid": OTHER, "isInMergeQueue": False}}}})
        raise AssertionError(args)

    adapter = sweep.GitHubAdapter(Path.cwd(), runner=runner)
    with pytest.raises(sweep.SweepError, match="head moved"):
        adapter.queue_membership("owner/repo", pr())


def test_paged_comments_reject_unpaginated_response():
    adapter = sweep.GitHubAdapter(Path.cwd(), runner=lambda args: json.dumps([comment()]))
    with pytest.raises(sweep.SweepError, match="pagination"):
        adapter.comments("owner/repo", 42)


def test_apply_refused(capsys):
    assert sweep.main(["--repo", "owner/repo", "--apply"]) == 2
    assert "report-only" in capsys.readouterr().out


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
