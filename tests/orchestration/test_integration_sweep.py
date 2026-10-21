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


@pytest.fixture(autouse=True)
def _advisory_fixture_workflow(monkeypatch):
    """The real ci.yml has no advisory job; cover the rule with a fixture workflow."""
    from scripts.ci import advisory_checks

    monkeypatch.setattr(
        advisory_checks,
        "CI_WORKFLOW_PATH",
        Path(__file__).resolve().parents[2] / "tests/fixtures/ci_advisory_workflow.yml",
    )


def comment(
    *,
    sha=SHA,
    task="review-one",
    started=START,
    verdict="APPROVED",
    login="fleet",
    association="MEMBER",
    edited=False,
    review_mode="cross_family",
    family="openai",
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


def test_unknown_history_marker_round_trip_and_missing_fields_refuse():
    item = comment(review_mode="red_team")
    item["body"] = build_comment(
        sha=SHA,
        task_id="review-one",
        started=START,
        verdict="APPROVED",
        model="gpt-6.1-sol",
        family="openai",
        reply="VERDICT: APPROVE",
        review_mode="red_team",
        unknown_history=[OTHER],
    )
    assert sweep.parse_marker(item["body"])["unknown_history"] == [OTHER]
    verdict = sweep.lookup_verdict([item], SHA, "fleet")
    assert verdict.review_mode == "red_team" and verdict.unknown_history == (OTHER,)
    for field in (" review_mode=red_team", f" unknown_history={OTHER}", f"Unknown history: {OTHER}\n"):
        altered = {**item, "body": item["body"].replace(field, "")}
        assert sweep.parse_marker(altered["body"]) is None
        assert sweep.lookup_verdict([altered], SHA, "fleet").state == "unknown"


def test_verified_app_bot_marker_round_trip_and_missing_fields_refuse():
    """#10531: the bot class is stated twice and never carries an author model."""
    item = comment()
    item["body"] = build_comment(
        sha=SHA,
        task_id="review-one",
        started=START,
        verdict="APPROVED",
        model="gpt-6.1-sol",
        family="openai",
        reply="VERDICT: APPROVE",
        app_bot=True,
    )
    marker = sweep.parse_marker(item["body"])
    assert marker["authorship"] == "verified_app_bot" and marker["model"] == "gpt-6.1-sol"
    assert "Authorship: verified_app_bot\nNo author model assumed.\n" in item["body"]
    assert sweep.lookup_verdict([item], SHA, "fleet").state == "APPROVED"
    assert "authorship" not in sweep.parse_marker(comment()["body"])
    for field in (" authorship=verified_app_bot", "Authorship: verified_app_bot\n", "No author model assumed.\n"):
        altered = {**item, "body": item["body"].replace(field, "")}
        assert sweep.parse_marker(altered["body"]) is None
        assert sweep.lookup_verdict([altered], SHA, "fleet").state == "unknown"
    forged = item["body"].replace("authorship=verified_app_bot", "authorship=dependabot")
    assert sweep.parse_marker(forged) is None


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
    rows = [
        comment(review_mode="red_team"),
        comment(task="later", started="2026-09-23T12:00:01.000001+00:00", verdict="BLOCKED"),
    ]
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


PR_10947_SHA = "19c9b39eb2eef93e2e2ae29178787d9105078120"


def posted(item, created_at):
    return {**item, "created_at": created_at, "updated_at": created_at}


def test_later_posted_rejection_beats_approval_with_later_start():
    """#10973: the #10947 rejection started 0.24 s before the approval but was posted 25 minutes after it."""
    approval = posted(
        comment(sha=PR_10947_SHA, task="approve", started="2026-10-18T17:17:37.175425+00:00"),
        "2026-10-18T17:19:35Z",
    )
    rejection = posted(
        comment(
            sha=PR_10947_SHA,
            task="reject",
            started="2026-10-18T17:17:36.933735+00:00",
            verdict="CHANGES_REQUESTED",
        ),
        "2026-10-18T17:44:00Z",
    )
    for rows in ([approval, rejection], [rejection, approval]):
        verdict = sweep.lookup_verdict(rows, PR_10947_SHA, "fleet")
        assert (verdict.state, verdict.task) == ("CHANGES_REQUESTED", "reject")
        assert verdict.started == datetime(2026, 10, 18, 17, 17, 36, 933735, tzinfo=UTC)


def test_approval_started_and_posted_after_rejection_supersedes_it():
    rejection = posted(comment(task="reject", verdict="BLOCKED"), "2026-09-23T13:00:00Z")
    approval = posted(comment(task="re-review", started="2026-09-23T12:30:00.000001+00:00"), "2026-09-23T13:10:00Z")
    assert sweep.lookup_verdict([rejection, approval], SHA, "fleet").state == "APPROVED"
    assert sweep.lookup_verdict([approval, rejection], SHA, "fleet").state == "APPROVED"


def test_rejection_stands_unless_one_approval_follows_it_in_both_orders():
    # One approval started later but was posted earlier; the other was posted later but started earlier.
    started_late = posted(
        comment(task="early-post", started="2026-09-23T12:10:00.000001+00:00"), "2026-09-23T12:11:00Z"
    )
    rejection = posted(
        comment(task="reject", started="2026-09-23T12:05:00.000001+00:00", verdict="BLOCKED"), "2026-09-23T12:12:00Z"
    )
    posted_late = posted(comment(task="late-post", started="2026-09-23T12:01:00.000001+00:00"), "2026-09-23T12:13:00Z")
    verdict = sweep.lookup_verdict([started_late, rejection, posted_late], SHA, "fleet")
    assert (verdict.state, verdict.task) == ("BLOCKED", "reject")


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
    advisory = {
        "name": "Component shadow (advisory)",
        "status": "COMPLETED",
        "conclusion": "FAILURE",
        "workflowName": "CI",
    }
    assert sweep._check_blockers(pr(statusCheckRollup=[advisory])) == ["CI pending CI Gate"]
    item = pr()
    item["statusCheckRollup"].extend(
        [
            advisory,
            {"name": "Build", "status": "COMPLETED", "conclusion": "FAILURE"},
        ]
    )
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


@pytest.mark.parametrize("history", [False, True])
@pytest.mark.parametrize(
    "line,replacement",
    [
        ("Authorship: verified_app_bot", "Not Authorship: verified_app_bot"),
        ("Authorship: verified_app_bot", "Prefix Authorship: verified_app_bot"),
        ("Authorship: verified_app_bot", "Authorship: verified_app_bot suffix"),
        ("Authorship: verified_app_bot", "Authorship: verified_app_bot\nAuthorship: verified_app_bot"),
        ("Authorship: verified_app_bot", "Authorship: human\nAuthorship: verified_app_bot"),
        ("Authorship: verified_app_bot", "authorship: human\nAuthorship: verified_app_bot"),
        ("No author model assumed.", "False: No author model assumed."),
        ("No author model assumed.", "No author model assumed. false"),
        ("No author model assumed.", "No author model assumed.\nNo author model assumed."),
        ("No author model assumed.", "An author model was assumed.\nNo author model assumed."),
    ],
)
def test_corrupt_readable_bot_authorship_refuses_through_parser(history, line, replacement):
    item = comment()
    body = build_comment(
        sha=SHA,
        task_id="review-one",
        started=START,
        verdict="APPROVED",
        model="gpt-6.1-sol",
        family="openai",
        reply="VERDICT: APPROVE",
        app_bot=True,
        review_mode="red_team" if history else "cross_family",
        unknown_history=[OTHER] if history else (),
    )
    assert sweep.lookup_verdict([{**item, "body": body}], SHA, "fleet").state == "APPROVED"
    altered = body.replace(line + "\n", replacement + "\n")
    assert sweep.parse_marker(altered) is None
    assert sweep.lookup_verdict([{**item, "body": altered}], SHA, "fleet").state == "unknown"


# Issue #11127: PR #11095 had a valid exact-head approval, but two hand-written markers for
# older heads failed the parser and revoked it from the merge queue with no stated reason.
CURRENT_11095 = "d5b35951" + "4e0c7a91b2f36d58e0a7c4b19f2d6e83"
OLDER_ONE = "71f0c2a9e4b85d36c1a07e92f4b6d8c3a5e1f709"
OLDER_TWO = "3b9e6d1f0a7c42e85b1d9f3a6c0e7b24d8f5a196"
LATER = "2026-09-23T12:00:01.000001+00:00"


def hand_written(body, comment_id):
    """A trusted comment whose marker ``record_cf_verdict`` did not write."""
    return {
        "id": comment_id,
        "body": body,
        "user": {"login": "fleet"},
        "author_association": "MEMBER",
        "created_at": "2026-09-23T12:30:00Z",
        "updated_at": "2026-09-23T12:30:00Z",
    }


def issue_11127_markers():
    no_started = (
        "Older head needs work.\n\nVERDICT: REQUEST_CHANGES\n\n"
        f"<!-- cf-verdict v1 sha={OLDER_ONE} task=hand-one verdict=REQUEST_CHANGES model=gpt-6.1-sol family=openai -->"
    )
    no_microseconds = (
        f"### Cross-family review\nReview profile: ukrainian\nhead: {OLDER_TWO}\nReviewer family: openai\n"
        "VERDICT: APPROVED\nReviewer model: gpt-6.1-sol\nTask id: hand-two\n\n"
        f"<!-- cf-verdict v1 sha={OLDER_TWO} task=hand-two started=2026-09-23T11:00:00+00:00 "
        "verdict=APPROVED model=gpt-6.1-sol family=openai review_profile=ukrainian -->"
    )
    return [hand_written(no_started, 9001), hand_written(no_microseconds, 9002)]


def recorded(comment_id, **fields):
    return {**comment(sha=CURRENT_11095, **fields), "id": comment_id}


def test_issue_11127_malformed_older_head_markers_do_not_poison_current_approval():
    markers = issue_11127_markers()
    assert all(sweep.parse_marker(item["body"]) is None for item in markers)
    verdict = sweep.lookup_verdict([*markers, recorded(5000)], CURRENT_11095, "fleet")
    assert (verdict.state, verdict.reason, verdict.comment_id) == ("APPROVED", None, None)
    assert verdict.superseded_markers == ("9001", "9002")
    report = sweep.classify_pr(pr(headRefOid=CURRENT_11095), verdict, queued=False, observed_at=START)
    assert report.state == "ready" and report.superseded_markers == ("9001", "9002")
    # The #10973 rejection rule still governs the current head; old markers alone leave it stale.
    rejection = recorded(5001, task="later", started=LATER, verdict="CHANGES_REQUESTED")
    assert sweep.lookup_verdict([*markers, recorded(5000), rejection], CURRENT_11095, "fleet").state == (
        "CHANGES_REQUESTED"
    )
    assert sweep.lookup_verdict(markers, CURRENT_11095, "fleet").state == "CF-stale"


@pytest.mark.parametrize(
    "old,new",
    [
        (f"started={START} ", ""),
        ("verdict=APPROVED ", "verdict=REQUEST_CHANGES "),
        (START, "2026-09-23T12:00:00+00:00"),
        ("### Cross-family review\n", ""),
        ("family=openai -->", "family=openai sources_calls=x -->"),
    ],
)
def test_malformed_current_head_marker_stays_unknown_with_reason_and_comment(old, new):
    item = recorded(5150)
    item["body"] = item["body"].replace(old, new)
    assert sweep.parse_marker(item["body"]) is None
    rows = [recorded(5000, task="valid", started=LATER), item]
    verdict = sweep.lookup_verdict(rows, CURRENT_11095, "fleet")
    assert (verdict.state, verdict.reason, verdict.comment_id) == (
        "unknown",
        sweep.MARKER_MALFORMED_CURRENT_HEAD,
        "5150",
    )


@pytest.mark.parametrize(
    "marker",
    [
        "<!-- cf-verdict v1 task=hand verdict=BLOCKED model=m family=openai -->",
        f"<!-- cf-verdict v1 sha={OLDER_ONE} sha={OLDER_TWO} verdict=BLOCKED -->",
        f"<!-- cf-verdict v1 sha={OLDER_ONE[:12]} verdict=BLOCKED -->",
        f"<!-- cf-verdict v1 sha={OLDER_ONE.upper()} verdict=BLOCKED -->",
        f"<!-- cf-verdict v1 sha={OLDER_ONE} verdict=BLOCKED",
        f"<!-- cf-verdict v1 sha={OLDER_ONE} -->\n<!-- cf-verdict v1 sha={OLDER_TWO} -->",
        f"<!-- cf-verdict v1 verdict=BLOCKED --> sha={OLDER_ONE}",
    ],
)
def test_unattributable_malformed_marker_poisons_every_head(marker):
    item = hand_written(f"VERDICT: BLOCKED\n\n{marker}", 6100)
    verdict = sweep.lookup_verdict([recorded(5000), item], CURRENT_11095, "fleet")
    assert (verdict.state, verdict.reason, verdict.comment_id) == ("unknown", sweep.MARKER_UNATTRIBUTABLE, "6100")


@pytest.mark.parametrize(
    "body",
    [
        f"Blocks {CURRENT_11095[:7]} too.\n\n<!-- cf-verdict v1 sha={OLDER_ONE} verdict=BLOCKED -->",
        f"<!-- cf-verdict v1 sha={OLDER_ONE} verdict=BLOCKED unknown_history={CURRENT_11095} -->",
        f"head: {CURRENT_11095.upper()}\n<!-- cf-verdict v1 sha={OLDER_ONE} verdict=BLOCKED -->",
    ],
)
def test_older_head_malformed_marker_citing_current_head_poisons_it(body):
    verdict = sweep.lookup_verdict([recorded(5000), hand_written(body, 6200)], CURRENT_11095, "fleet")
    assert (verdict.state, verdict.reason, verdict.comment_id) == (
        "unknown",
        sweep.MARKER_MENTIONS_CURRENT_HEAD,
        "6200",
    )
    # A different current head the body never cites treats the same marker as superseded.
    other = sweep.lookup_verdict([hand_written(body, 6200)], "e" * 40, "fleet")
    assert (other.state, other.superseded_markers) == ("CF-stale", ("6200",))


def test_every_unknown_verdict_carries_a_typed_reason():
    edited = {**recorded(7001), "updated_at": "2026-09-23T13:05:00Z"}
    cases = [
        (sweep.lookup_verdict(None, CURRENT_11095, "fleet"), sweep.COMMENTS_UNAVAILABLE, None),
        (sweep.lookup_verdict([recorded(1)], CURRENT_11095, "fleet", complete=False), sweep.COMMENTS_UNAVAILABLE, None),
        (
            sweep.lookup_verdict([recorded(1), [recorded(2)]], CURRENT_11095, "fleet"),
            sweep.COMMENT_MALFORMED,
            "index-1",
        ),
        (sweep.lookup_verdict([{"id": 7000, "body": None}], CURRENT_11095, "fleet"), sweep.COMMENT_MALFORMED, "7000"),
        (sweep.lookup_verdict([recorded(1)], CURRENT_11095[:12], "fleet"), sweep.HEAD_INVALID, None),
        (sweep.lookup_verdict([recorded(1)], CURRENT_11095, None), sweep.IDENTITY_UNAVAILABLE, None),
        (sweep.lookup_verdict([edited], CURRENT_11095, "fleet"), sweep.MARKER_EDITED, "7001"),
        (
            sweep.lookup_verdict([recorded(7002, family="unknown")], CURRENT_11095, "fleet"),
            sweep.REVIEWER_UNATTESTED,
            "7002",
        ),
    ]
    for verdict, reason, comment_id in cases:
        assert (verdict.state, verdict.reason, verdict.comment_id) == ("unknown", reason, comment_id)


def test_verdict_reason_codes_are_a_stable_closed_list():
    assert sweep.UNKNOWN_REASONS == (
        "comments-unavailable",
        "head-invalid",
        "identity-unavailable",
        "comment-malformed",
        "marker-unattributable",
        "marker-malformed-current-head",
        "marker-mentions-current-head",
        "marker-edited",
        "reviewer-unattested",
    )
    with pytest.raises(ValueError):
        sweep.Verdict("unknown")
    with pytest.raises(ValueError):
        sweep.Verdict("unknown", reason="because")
    with pytest.raises(ValueError):
        sweep.Verdict("APPROVED", reason=sweep.MARKER_EDITED)


def test_report_names_unknown_reason_and_comment_without_bodies(monkeypatch, capsys):
    malformed = recorded(5150)
    malformed["body"] = malformed["body"].replace("verdict=APPROVED ", "verdict=REQUEST_CHANGES ")

    class Adapter:
        def __init__(self, root):
            pass

        def list_open_prs(self, repository):
            return [pr(headRefOid=CURRENT_11095)]

        def identity(self):
            return "fleet"

        def comments(self, repository, number):
            return [*issue_11127_markers(), recorded(5000), malformed]

        def queue_membership(self, repository, item):
            return False

    monkeypatch.setattr(sweep, "GitHubAdapter", Adapter)
    assert sweep.main(["--repo", "owner/repo"]) == 0
    text = capsys.readouterr().out
    assert "state=CF-unknown" in text
    assert text.rstrip().endswith(" cf-unknown=marker-malformed-current-head comment=5150 superseded-marker=9001,9002")
    assert "REQUEST_CHANGES" not in text and "Cross-family review" not in text
    assert sweep.main(["--repo", "owner/repo", "--json"]) == 0
    row = json.loads(capsys.readouterr().out)[0]
    assert (row["verdict_reason"], row["verdict_comment"]) == ("marker-malformed-current-head", "5150")
    assert row["superseded_markers"] == ["9001", "9002"]
