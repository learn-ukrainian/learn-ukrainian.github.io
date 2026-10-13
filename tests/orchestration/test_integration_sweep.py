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


def test_same_second_microseconds_and_tie_rejection():
    # #10501: a later same-head approval no longer clears an earlier rejection.
    later = "2026-09-23T12:00:00.000002+00:00"
    assert (
        sweep.lookup_verdict([comment(verdict="BLOCKED"), comment(task="later", started=later)], SHA, "fleet").state
        == "BLOCKED"
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

    rows = sweep.run(Adapter(), "owner/repo", tasks_dir=Path("unused"), now=datetime(2026, 9, 23, tzinfo=UTC))
    assert rows[0].state == "CF-unknown"
    assert "queue lookup unknown" in rows[0].blockers


# --- #10501: recorder receipts, rejection order, start clamping, in-flight reviews ---

REPO = "owner/repo"
FUTURE = "2030-01-01T00:00:00.000001+00:00"


def published(*, comment_id=101, task="review-one", sha=SHA, verdict="APPROVED", started=START,
              review_mode="cross_family", created="2026-09-23T13:00:00Z", family="openai"):
    item = comment(sha=sha, task=task, started=started, verdict=verdict, review_mode=review_mode, family=family)
    item.update(id=comment_id, created_at=created, updated_at=created)
    return item


def bind(tasks, item, *, pr_number=42, archive=False, record_updates=None, **receipt_updates):
    """Write the review task record and the receipt the recorder binds for ``item``."""
    marker = sweep.parse_marker(item["body"])
    record = {"task_id": marker["task"], "run_nonce": "nonce-1", "status": "done", "repository": REPO}
    receipt = sweep.build_receipt(
        repository=REPO, pr=pr_number, head_sha=marker["sha"], task_id=marker["task"], run_nonce="nonce-1",
        model=marker["model"], family=marker["family"], verdict=marker["verdict"],
        review_mode=marker.get("review_mode", "cross_family"), comment_id=item["id"], body=item["body"],
    )
    receipt.update(receipt_updates)
    record[sweep.RECEIPT_FIELD] = receipt
    record.update(record_updates or {})
    directory = tasks / "archive" if archive else tasks
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{marker['task']}.json").write_text(json.dumps(record))
    return record


def lookup(rows, tasks, sha=SHA, number=42):
    return sweep.lookup_verdict(rows, sha, "fleet", evidence=sweep.ReviewLedger(tasks, REPO).evidence(number))


@pytest.fixture
def tasks(tmp_path):
    path = tmp_path / "tasks"
    path.mkdir()
    return path


def test_receipted_approval_is_the_only_queue_approval(tasks):
    item = published()
    assert lookup([item], tasks).state == sweep.UNRECEIPTED
    bind(tasks, item)
    verdict = lookup([item], tasks)
    assert verdict.state == "APPROVED" and verdict.task == "review-one"
    assert sweep.classify_pr(pr(), verdict, queued=False, observed_at=START).state == "ready"


def test_unreceipted_and_in_flight_states_never_read_ready():
    for state in (sweep.UNRECEIPTED, sweep.IN_FLIGHT):
        report = sweep.classify_pr(pr(), sweep.Verdict(state), queued=False, observed_at=START)
        assert report.state == state and state in report.blockers


@pytest.mark.parametrize(
    "field,value",
    [
        ("head_sha", OTHER), ("task_id", "review-two"), ("run_nonce", "nonce-2"), ("model", "gpt-6-luna"),
        ("family", "anthropic"), ("repository", "github.com/owner/other"), ("review_mode", "red_team"),
        ("pr", 43), ("verdict", "CHANGES_REQUESTED"), ("comment_id", 102), ("comment_sha256", "0" * 64),
        ("schema", "cf-recording.v0"), ("extra", "field"),
    ],
)
def test_every_receipt_identity_mismatch_never_approves(tasks, field, value):
    item = published()
    bind(tasks, item, **{field: value})
    assert lookup([item], tasks).state == sweep.UNRECEIPTED


@pytest.mark.parametrize(
    "updates", [{"run_nonce": "nonce-2"}, {"task_id": "other"}, {"run_nonce": None}, {"run_nonce": ""}]
)
def test_redispatched_or_unbound_record_voids_its_receipt(tasks, updates):
    item = published()
    bind(tasks, item, record_updates=updates)
    assert lookup([item], tasks).state == sweep.UNRECEIPTED


def test_receipt_binds_the_exact_comment_body_and_id(tasks):
    item = published()
    bind(tasks, item)
    forged = dict(item, id=999)
    assert lookup([forged], tasks).state == sweep.UNRECEIPTED
    no_id = {key: value for key, value in item.items() if key != "id"}
    assert lookup([no_id], tasks).state == sweep.UNRECEIPTED
    altered = dict(item, body=item["body"].replace("VERDICT: APPROVE\n\n</details>", "VERDICT: APPROVE!\n\n</details>"))
    assert sweep.parse_marker(altered["body"]) is not None
    assert lookup([altered], tasks).state == sweep.UNRECEIPTED
    # The genuine comment still approves beside a forged duplicate.
    assert lookup([forged, item], tasks).state == "APPROVED"


def test_red_team_receipt_cannot_clear_a_cross_family_marker(tasks):
    red = published(review_mode="red_team")
    bind(tasks, red)
    cross = published()  # Same task, same id, cross-family body.
    assert lookup([cross], tasks).state == sweep.UNRECEIPTED
    verdict = lookup([red], tasks)
    assert verdict.state == "APPROVED" and verdict.review_mode == "red_team"


def test_archived_review_record_still_supplies_its_receipt(tasks):
    item = published()
    bind(tasks, item, archive=True)
    assert lookup([item], tasks).state == "APPROVED"


@pytest.mark.parametrize("where", ["hot", "archive"])
@pytest.mark.parametrize("content", ["{", "[]", "not json"])
def test_malformed_review_record_is_unknown(tasks, where, content):
    item = published()
    directory = tasks / "archive" if where == "archive" else tasks
    directory.mkdir(exist_ok=True)
    (directory / "review-one.json").write_text(content)
    assert lookup([item], tasks).state == "unknown"


def test_non_object_receipt_and_unreadable_record_are_unknown(tasks, monkeypatch):
    item = published()
    bind(tasks, item)
    record = json.loads((tasks / "review-one.json").read_text())
    record[sweep.RECEIPT_FIELD] = ["not", "a", "receipt"]
    (tasks / "review-one.json").write_text(json.dumps(record))
    assert lookup([item], tasks).state == "unknown"
    bind(tasks, item)
    original = Path.read_text

    def unreadable(path, *args, **kwargs):
        if path.name == "review-one.json":
            raise PermissionError("denied")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", unreadable)
    assert lookup([item], tasks).state == "unknown"


def test_missing_ledger_is_unknown(tmp_path):
    item = published()
    assert lookup([item], tmp_path / "absent").state == "unknown"


@pytest.mark.parametrize("order", ["approval-first", "rejection-first"])
@pytest.mark.parametrize("rejection", ["CHANGES_REQUESTED", "BLOCKED"])
def test_future_dated_approval_never_overrides_an_earlier_rejection(tasks, order, rejection):
    approval = published(comment_id=1, task="approve", started=FUTURE)
    rejected = published(comment_id=2, task="reject", verdict=rejection)
    bind(tasks, approval)
    rows = [approval, rejected] if order == "approval-first" else [rejected, approval]
    assert lookup(rows, tasks).state == rejection
    assert sweep.lookup_verdict(rows, SHA, "fleet").state == rejection


def test_rejection_needs_no_receipt_and_survives_an_unreadable_ledger(tmp_path):
    rows = [published(comment_id=1), published(comment_id=2, task="reject", verdict="BLOCKED")]
    assert lookup(rows, tmp_path / "absent").state == "BLOCKED"


def test_rejection_wins_over_malformed_evidence_in_either_order(tasks):
    malformed = published(comment_id=1, task="bad")
    malformed["body"] = malformed["body"].replace("verdict=APPROVED", "verdict=MAYBE")
    rejected = published(comment_id=2, task="reject", verdict="CHANGES_REQUESTED")
    assert lookup([malformed, rejected], tasks).state == "CHANGES_REQUESTED"
    assert lookup([rejected, malformed], tasks).state == "CHANGES_REQUESTED"
    assert lookup([malformed, published(comment_id=3)], tasks).state == "unknown"


def test_marker_start_is_clamped_to_comment_creation(tasks):
    item = published(started=FUTURE, created="2026-09-23T13:00:00Z")
    bind(tasks, item)
    verdict = lookup([item], tasks)
    assert verdict.state == "APPROVED"
    assert verdict.started == datetime(2026, 9, 23, 13, tzinfo=UTC)


def test_missing_comment_creation_time_is_unknown(tasks):
    item = published()
    bind(tasks, item)
    del item["created_at"]
    assert lookup([item], tasks).state == "unknown"


def active(tasks, task_id="active-review", **fields):
    record = {"task_id": task_id, "status": "running", "repository": REPO, "type": "review", **fields}
    (tasks / f"{task_id}.json").write_text(json.dumps(record))


@pytest.mark.parametrize("field", ["pinned_head", "worktree_base_sha", "review_head_sha", "head_sha"])
def test_active_outside_review_blocks_a_receipted_approval(tasks, field):
    item = published()
    bind(tasks, item)
    active(tasks, **{field: SHA})
    assert lookup([item], tasks).state == sweep.IN_FLIGHT


def test_preparing_dispatch_blocks_and_unrelated_activity_does_not(tasks):
    item = published()
    bind(tasks, item)
    active(tasks, "other-head", pinned_head=OTHER)
    active(tasks, "red-team", pinned_head=SHA, review_mode="red_team")
    active(tasks, "other-repo", pinned_head=SHA, repository="owner/else")
    active(tasks, "finished", pinned_head=SHA, status="done")
    assert lookup([item], tasks).state == "APPROVED"
    (tasks / "prep.json").write_text(json.dumps({"status": "spawning", "worktree_prep": {"base_sha": SHA.upper()}}))
    assert lookup([item], tasks).state == sweep.IN_FLIGHT


def test_malformed_active_review_head_is_unknown(tasks):
    item = published()
    bind(tasks, item)
    active(tasks, pinned_head=["not", "a", "sha"])
    assert lookup([item], tasks).state == "unknown"


def test_moved_head_takes_fresh_review_and_keeps_old_head_rejection(tasks):
    old = published(comment_id=1, task="old-reject", verdict="BLOCKED")
    new = published(comment_id=2, task="new-approve", sha=OTHER)
    bind(tasks, new)
    rows = [old, new]
    assert lookup(rows, tasks, sha=OTHER).state == "APPROVED"
    assert lookup(rows, tasks, sha=SHA).state == "BLOCKED"


def test_historical_evidence_ignores_active_reviews_but_not_receipts(tasks):
    item = published()
    active(tasks, pinned_head=SHA)
    history = sweep.ReviewLedger(tasks, REPO).evidence(42, historical=True)
    assert sweep.lookup_verdict([item], SHA, "fleet", evidence=history).state == sweep.UNRECEIPTED
    bind(tasks, item)
    assert sweep.lookup_verdict([item], SHA, "fleet", evidence=history).state == "APPROVED"


def test_ledger_scans_active_reviews_once_per_snapshot(tasks, monkeypatch):
    calls = []
    original = sweep.active_review_heads
    monkeypatch.setattr(sweep, "active_review_heads", lambda *args: calls.append(args) or original(*args))
    item = published()
    bind(tasks, item)
    ledger = sweep.ReviewLedger(tasks, REPO)
    for _ in range(3):
        assert sweep.lookup_verdict([item], SHA, "fleet", evidence=ledger.evidence(42)).state == "APPROVED"
    assert len(calls) == 1


def test_sweep_run_requires_receipts(tasks):
    item = published()

    class Adapter:
        def list_open_prs(self, repository):
            return [pr()]

        def identity(self):
            return "fleet"

        def comments(self, repository, number):
            return [item]

        def queue_membership(self, repository, row):
            return False

    observed = datetime(2026, 9, 23, tzinfo=UTC)
    assert sweep.run(Adapter(), REPO, tasks_dir=tasks, now=observed)[0].state == sweep.UNRECEIPTED
    bind(tasks, item)
    assert sweep.run(Adapter(), REPO, tasks_dir=tasks, now=observed)[0].state == "ready"
    active(tasks, pinned_head=SHA)
    assert sweep.run(Adapter(), REPO, tasks_dir=tasks, now=observed)[0].state == sweep.IN_FLIGHT


def test_main_reads_the_named_ledger_and_refuses_an_unknown_one(tasks, monkeypatch, capsys, tmp_path):
    seen = {}

    def fake_run(adapter, repository, *, tasks_dir, now=None):
        seen["tasks_dir"] = tasks_dir
        return []

    monkeypatch.setattr(sweep, "run", fake_run)
    assert sweep.main(["--repo", REPO, "--tasks-dir", str(tasks)]) == 0
    assert seen["tasks_dir"] == tasks
    assert sweep.main(["--repo", REPO, "--repo-root", str(tmp_path / "not-a-checkout")]) == 1
    assert "task ledger location unknown" in capsys.readouterr().out


def test_default_ledger_is_the_primary_checkout_of_a_linked_worktree(tmp_path):
    import subprocess

    primary = tmp_path / "primary"
    subprocess.run(["git", "init", "-q", str(primary)], check=True, timeout=30)
    subprocess.run(
        ["git", "-C", str(primary), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
         "commit", "-q", "--allow-empty", "-m", "seed"],
        check=True, timeout=30,
    )
    linked = tmp_path / "linked"
    subprocess.run(["git", "-C", str(primary), "worktree", "add", "-q", str(linked)], check=True, timeout=30)
    assert sweep.default_tasks_dir(linked) == primary.resolve() / "batch_state" / "tasks"


def test_unreadable_comment_body_is_unknown_but_never_hides_a_rejection(tasks):
    item = published()
    bind(tasks, item)
    broken = {"id": 7, "body": None, "user": {"login": "fleet"}, "author_association": "MEMBER"}
    assert lookup([item, broken], tasks).state == "unknown"
    assert lookup([broken, published(comment_id=2, task="reject", verdict="BLOCKED")], tasks).state == "BLOCKED"
    assert lookup(["not-a-comment", item], tasks).state == "unknown"
