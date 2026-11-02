"""One sealed P2 fix-verification round after three spent rounds (#12548)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from scripts.review import budget_grant
from scripts.review import record_cf_verdict as recorder
from tests.test_record_cf_verdict import (
    _REAL_BUDGET_GRANT,
    GRANT_REQUEST,
    SHA,
    facts_for,
    move_head,
    recorder_matcher,  # noqa: F401 - autouse publication scanner rules
    setup_record,
    verdict_with_reply,
    write_grant,
    write_task,
)

REJECTED_HEAD = "3" * 40
NEXT = "4" * 40
DELTA = "d" * 64
P2_REQUEST = {
    **GRANT_REQUEST,
    "finding_id": "F3",
    "blocker_class": budget_grant.P2_FIX,
    "p2_fix_verification": {"rejected_head": REJECTED_HEAD, "candidate_head": SHA, "delta_sha256": DELTA,
                            "finding_ids": ["F3"]},
}


def finding(finding_id: str, priority: str = "P2") -> dict[str, object]:
    return {"id": finding_id, "title": f"[{priority}] {finding_id} retry path", "body": "The retry loses the lock.",
            "priority": priority, "confidence": 0.9, "category": "correctness",
            "location": {"path": "docs/readme.md", "start_line": 3, "end_line": 3, "claim_type": "present"},
            "verbatim": "retry()", "why_wrong": "Two writers race.", "smallest_fix": "Hold the lock.",
            "sources": ["docs/readme.md:3"]}


def reply(*findings: dict[str, object], correctness: str = "incorrect", explanation: str = "Changes needed.") -> str:
    """A schema-bound reply, as a code review of record returns it."""
    return json.dumps({"schema_version": "code-review-findings.v1", "findings": list(findings),
                       "overall": {"correctness": correctness, "explanation": explanation, "confidence": 0.9}})


def approve(explanation: str, *findings: dict[str, object]) -> str:
    return reply(*findings, correctness="correct", explanation=explanation)


VERIFIED = approve(f"P2_FIX_DELTA: {DELTA} VERIFIED\nF3 fixed: the retry holds the lock.")
# PR 1117's shape: three rounds, each a rejection raising one new P2 (F1, F2, F3) after fixing the last.
PR_1117 = (reply(finding("F1")), reply(finding("F2")), reply(finding("F3")))


def p2_case(monkeypatch, tmp_path, replies=PR_1117, verdicts=("CHANGES_REQUESTED",) * 3, request=P2_REQUEST):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    monkeypatch.setattr(recorder, "_budget_grant", _REAL_BUDGET_GRANT)
    monkeypatch.setattr(recorder, "pr_review_facts", lambda *_a, **_k: facts_for({"google"}, changed_paths=("docs/readme.md",)))
    monkeypatch.setattr(budget_grant, "_delta_sha256", lambda _root, rejected, candidate: DELTA)
    monkeypatch.setattr(budget_grant, "_lineage_links", lambda _repository, _number: ([12548], []))
    for index, (text, verdict) in enumerate(zip(replies, verdicts, strict=True), start=1):
        comments.append(verdict_with_reply(str(index) * 40, verdict, text, task_id=f"round-{index}"))
    write_grant(tasks, request)
    return tasks, comments, calls


def seat(tasks, text, task_id="review-one", **updates):
    """A finished review run of this lineage, with the run identity the recorder exempts while recording it."""
    write_task(tasks, task_id=task_id, reply=text, review_mode="cross_family", run_nonce=f"{task_id}-run", **updates)


def record(tasks, tmp_path, task_id="review-one"):
    return recorder.record(task_id, pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")


def refused(tasks, tmp_path, reason, task_id="review-one"):
    with pytest.raises(recorder.RecordError, match=rf"REVIEW_BUDGET_EXHAUSTED.*BUDGET_GRANT_REFUSED\[(?:{reason})\]"):
        record(tasks, tmp_path, task_id)


def receipts(tmp_path):
    return sorted((tmp_path / budget_grant.P2_RECEIPT_DIR).glob("*.json"))


def test_pr_1117_replay_admits_exactly_one_round_four_and_refuses_a_second(monkeypatch, tmp_path):
    tasks, _comments, calls = p2_case(monkeypatch, tmp_path)
    # Round 4 verifies F3 fixed but, like rounds 1-3, finds a new P2 (F4).
    seat(tasks, reply(finding("F4")))
    result = record(tasks, tmp_path)
    grant = result["budget_grant"]
    assert result["verdict"] == "CHANGES_REQUESTED" and grant["round_allowance"] == 4
    assert grant["blocker_class"] == "p2-fix-verification" and grant["advisor_model"] == "gpt-6.1-sol"
    sealed = grant["p2_fix_round"]
    assert (sealed["rejected_head"], sealed["candidate_head"], sealed["delta_sha256"], sealed["finding_ids"]) == (
        REJECTED_HEAD, SHA, DELTA, ["F3"])
    assert sealed["grant_task"] == "grant-approval" and len(receipts(tmp_path)) == 3  # PR, branch and issue keys
    # The same ledger shape again: a reissued grant for round 5 is refused, the lineage's round is spent.
    write_grant(tasks, {**p2(rejected_head=SHA, candidate_head=NEXT, finding_ids=["F4"]), "finding_id": "F4"},
                task_id="grant-two")
    move_head(monkeypatch, NEXT)
    write_task(tasks, task_id="round-five", worktree_base_sha=NEXT, reply=VERIFIED)
    with pytest.raises(recorder.RecordError, match=r"round 5; BUDGET_GRANT_REFUSED.*used its one p2 fix round") as refusal:
        record(tasks, tmp_path, "round-five")
    print(f"replay: round 4 admitted {sealed}; round 5 refused: {refusal.value}")
    assert calls["posts"] == 1


def p2(**changes):
    return {**P2_REQUEST, "p2_fix_verification": {**P2_REQUEST["p2_fix_verification"], **changes}}


@pytest.mark.parametrize(
    "case,reason",
    [
        ("latest-approved", "blocker"),
        ("latest-p1", "blocker"),
        ("latest-p2-and-p3", "blocker"),
        ("latest-no-findings", "blocker"),
        ("earlier-p1-unresolved", "blocker"),
        ("earlier-p1-incidental-closing-word", "blocker"),
        ("earlier-p1-fenced-example-disposition", "blocker"),
        ("latest-duplicate-findings-key", "blocker"),
        ("latest-duplicate-findings-key-cr-fence", "blocker"),
        ("candidate-head-unpublished-seat", "evidence"),
        ("lineage-spans-prs", "evidence"),
        ("earlier-security-fail", "blocker"),
        ("earlier-blocked", "blocker"),
        ("earlier-edited", "blocker"),
        ("unpublished-run", "evidence"),
        ("rejected-head", "binding"),
        ("candidate-head", "binding"),
        ("finding-ids", "binding"),
        ("delta", "binding"),
        ("spent-by-replaced-pr", "spent"),
        ("p2-object-missing", "request"),
        ("p2-object-on-other-class", "request"),
    ],
)
def test_p2_round_refusals(monkeypatch, tmp_path, case, reason):
    replies, verdicts = list(PR_1117), ["CHANGES_REQUESTED"] * 3
    if case == "latest-approved":
        verdicts[2] = "APPROVED"
    replies[2] = {"latest-p1": reply(finding("F3", "P1")), "latest-p2-and-p3": reply(finding("F3"), finding("F4", "P3")),
                  "latest-no-findings": reply()}.get(case, replies[2])
    if case in {"earlier-p1-unresolved", "earlier-p1-incidental-closing-word", "earlier-p1-fenced-example-disposition"}:
        replies[0] = "VERDICT: REQUEST_CHANGES\nF1 [P1] docs/readme.md:3 two writers race on the lock."
        replies[1] = "VERDICT: REQUEST_CHANGES\nF2 [P2] docs/readme.md:4 the retry path still races."
        # A prose ledger that omits F1 is no resolution (a structured object that omits it would be).
        replies[2] = "VERDICT: REQUEST_CHANGES\nF3 [P2] docs/readme.md:5 the retry path drops the lease."
    if case == "earlier-p1-incidental-closing-word":  # A description word is not a disposition.
        replies[0] = "VERDICT: REQUEST_CHANGES\nF1 [P1] Fixed-size buffer allows out-of-bounds writes."
    if case == "earlier-p1-fenced-example-disposition":
        replies[1] += "\n\nExample:\n\n```text\nF1 [P1] fixed with evidence.\n```"
    if case.startswith("latest-duplicate"):  # A P1 the canonical parser drops by keeping the last key.
        doubled = reply(finding("F7", "P1"))[:-1] + f', "findings": [{json.dumps(finding("F3"))}]}}'
        replies[2] = f"```json\r{doubled}\r```" if case.endswith("cr-fence") else "\r" + doubled
    if case == "earlier-security-fail":
        replies[0] = "VERDICT: REQUEST_CHANGES\nF1 [P2] docs/readme.md:3 race.\nSECURITY_VERDICT: FAIL"
    if case == "earlier-blocked":
        verdicts[1] = "BLOCKED"
    request = {
        "rejected-head": p2(rejected_head="2" * 40), "candidate-head": p2(candidate_head="9" * 40),
        "finding-ids": p2(finding_ids=["F2", "F3"]), "p2-object-missing": {**P2_REQUEST, "p2_fix_verification": None},
        "p2-object-on-other-class": {**P2_REQUEST, "blocker_class": "state-concurrency"},
    }.get(case, P2_REQUEST)
    tasks, comments, calls = p2_case(monkeypatch, tmp_path, replies, verdicts, request)
    if case == "earlier-edited":
        comments[0]["updated_at"] = "2026-09-23T11:59:00Z"
    if case == "unpublished-run":
        # Rule 5: a round-3 rerun whose verdict was never recorded (the author pushed first) earns no credit.
        write_task(tasks, task_id="round-3-rerun", worktree_base_sha=REJECTED_HEAD, reply=PR_1117[2],
                   review_mode="cross_family")
    if case == "candidate-head-unpublished-seat":
        seat(tasks, reply(finding("F9", "P1")), task_id="other-seat", worktree_base_sha=SHA)
    if case == "lineage-spans-prs":
        monkeypatch.setattr(budget_grant, "_lineage_links", lambda _repository, _number: ([12548], [41]))
    if case == "delta":
        monkeypatch.setattr(budget_grant, "_delta_sha256", lambda *_a: "e" * 64)
    if case == "spent-by-replaced-pr":
        held = {"schema": budget_grant.P2_RECEIPT_SCHEMA, "repository": "owner/repo", "pr": 41, "candidate_head": "9" * 40}
        root = tmp_path / budget_grant.P2_RECEIPT_DIR
        root.mkdir()
        from scripts.review.repair_round import _receipt_path

        _receipt_path(root, "issue:owner/repo#12548").write_text(json.dumps(held))
    seat(tasks, VERIFIED)
    refused(tasks, tmp_path, reason)
    assert calls == {"posts": 0, "statuses": 0} and (case == "spent-by-replaced-pr" or not receipts(tmp_path))


def test_earlier_p1_with_recorded_resolution_admits(monkeypatch, tmp_path):
    # A prose entry never closes F1; the later structured object that no longer lists it does.
    replies = ("VERDICT: REQUEST_CHANGES\nF1 [P1] docs/readme.md:3 two writers race on the lock.",
               "VERDICT: REQUEST_CHANGES\nF1 [P1] fixed with evidence.\n\nF2 [P2] docs/readme.md:4 retry races.",
               f"VERDICT: REQUEST_CHANGES\nSCORE: 7/10\n\n```json\n{reply(finding('F3'))}\n```")
    tasks, _comments, _calls = p2_case(monkeypatch, tmp_path, replies)
    seat(tasks, VERIFIED)
    result = record(tasks, tmp_path)
    assert result["verdict"] == "APPROVED" and result["budget_grant"]["cited_verdict_head"] == REJECTED_HEAD


@pytest.mark.parametrize("change", ["reissued-grant", "new-reviewer"])
def test_failed_verification_spends_the_round(monkeypatch, tmp_path, change):
    tasks, _comments, calls = p2_case(monkeypatch, tmp_path)
    seat(tasks, reply(finding("F3")))
    assert record(tasks, tmp_path)["verdict"] == "CHANGES_REQUESTED"
    write_grant(tasks, p2(rejected_head=SHA, candidate_head=NEXT), task_id="grant-two")
    move_head(monkeypatch, NEXT)
    extra = {"model": "claude-opus-5-5", "agent": "claude"} if change == "new-reviewer" else {}
    write_task(tasks, task_id="retry", worktree_base_sha=NEXT, reply=VERIFIED, **extra)
    with pytest.raises(recorder.RecordError, match=r"round 5; .*used its one p2 fix round at PR #42"):
        record(tasks, tmp_path, "retry")
    # Without the receipts the allowance still refuses round 5.
    for path in receipts(tmp_path):
        path.unlink()
    with pytest.raises(recorder.RecordError, match=r"BUDGET_GRANT_REFUSED\[allowance\]: grant allows 4 rounds"):
        record(tasks, tmp_path, "retry")
    assert calls["posts"] == 1


@pytest.mark.parametrize(
    "text",
    [
        pytest.param(approve("F3 fixed."), id="missing"),
        pytest.param(approve(f"P2_FIX_DELTA: {DELTA} REFUTED"), id="false"),
        pytest.param(approve(f"P2_FIX_DELTA: {'e' * 64} VERIFIED"), id="mismatched"),
        pytest.param(approve(f"P2_FIX_DELTA: {DELTA} VERIFIED", finding("F3", "P3")), id="structured-still-listed"),
        pytest.param(approve("Looks right.", finding("F9", "P3") | {"verbatim": f"P2_FIX_DELTA: {DELTA} VERIFIED"}),
                     id="token-only-in-quoted-code"),
        pytest.param(approve(f"Example syntax only:\nP2_FIX_DELTA: {DELTA} VERIFIED"), id="example-in-explanation"),
        pytest.param(approve(f"I cannot attest P2_FIX_DELTA: {DELTA} VERIFIED"), id="negated"),
        pytest.param(approve(f"P2_FIX_DELTA: {DELTA} VERIFIED\nExample: P2_FIX_DELTA: {DELTA} VERIFIED"),
                     id="second-mention"),
        pytest.param(f"VERDICT: APPROVE\nP2_FIX_DELTA: {DELTA} VERIFIED", id="prose-cannot-attest"),
    ],
)
def test_approve_needs_positive_delta_attestation(monkeypatch, tmp_path, text):
    tasks, _comments, calls = p2_case(monkeypatch, tmp_path)
    seat(tasks, text)
    with pytest.raises(recorder.RecordError, match=r"BUDGET_GRANT_REFUSED\[verification\]"):
        record(tasks, tmp_path)
    # Consumed although the APPROVE was refused; that refused claim is a rejection, so no other seat approves.
    assert len(receipts(tmp_path)) == 3 and calls["posts"] == 0
    seat(tasks, VERIFIED, task_id="second-seat", model="claude-opus-5-5", agent="claude")
    refused(tasks, tmp_path, "evidence", "second-seat")


@pytest.mark.parametrize(
    "text",
    ["VERDICT: APPROVE", reply(finding("F3", "P3")),
     reply(finding("F9", "P3")).replace("Changes needed.", f"Example syntax only:\\nP2_FIX_DELTA: {DELTA} VERIFIED")],
    ids=["approve", "p3-residual", "p3-residual-example-attestation"],
)
def test_every_seat_at_the_candidate_head_must_attest(monkeypatch, tmp_path, text):
    tasks, _comments, calls = p2_case(monkeypatch, tmp_path)
    seat(tasks, VERIFIED)
    assert record(tasks, tmp_path)["verdict"] == "APPROVED"
    seat(tasks, text, task_id="second-seat", model="claude-opus-5-5", agent="claude")
    if text.startswith("VERDICT"):
        with pytest.raises(recorder.RecordError, match=r"BUDGET_GRANT_REFUSED\[verification\]"):
            record(tasks, tmp_path, "second-seat")
    else:  # A P3-only reply keeps its rejection instead of becoming an approval with residuals.
        assert record(tasks, tmp_path, "second-seat")["p3_downgrade_refused"] == recorder.P3_REPAIR_WITHHELD
    assert calls["posts"] == 1 + (not text.startswith("VERDICT"))


def test_dispatch_spends_the_round_before_the_reviewer_runs(monkeypatch, tmp_path):
    from scripts.dispatcher import checks

    sealed = {"schema": budget_grant.P2_RECEIPT_SCHEMA, "repository": "owner/repo", "pr": 42, "candidate_head": SHA,
              "lineage_keys": ["branch:owner/repo:codex/42", "pr:owner/repo#42"]}
    decision = {"budget_grant": {"p2_fix_round": sealed}}
    tasks = tmp_path / "tasks"
    monkeypatch.setattr(checks.store, "tasks_dir", lambda: tasks)
    monkeypatch.setattr(recorder, "dispatch_budget_check", lambda *_a, **_k: decision)
    args = SimpleNamespace(pr=42, branch="codex/42")
    checks.check_review_budget(args, {"github": "owner/repo"}, SHA)
    assert len(receipts(tmp_path)) == 2
    checks.check_review_budget(args, {"github": "owner/repo"}, SHA)  # a retry at the same head is the same round
    decision["budget_grant"]["p2_fix_round"] = {**sealed, "candidate_head": NEXT}
    with pytest.raises(ValueError, match=r"review dispatch refused: .*BUDGET_GRANT_REFUSED\[spent\]"):
        checks.check_review_budget(args, {"github": "owner/repo"}, NEXT)


def test_rulings_sealed_before_the_field_stay_valid():
    legacy = {key: value for key, value in GRANT_REQUEST.items() if key != "withheld_capability"}
    for request in (GRANT_REQUEST, legacy, {**GRANT_REQUEST, "p2_fix_verification": None}):
        assert budget_grant.parse_request(dict(request), "ruling") == request


# A seat's unpublished run that its own later published verdict supersedes (#12563). The ledger's markers are
# anthropic runs started 11:00; this seat's earlier run ("orphan") never published, and round-2 is its witness.
ANTHROPIC = {"model": "claude-opus-5-5", "agent": "claude"}


def superseded_case(monkeypatch, tmp_path, orphan_reply, *, replies=PR_1117, orphan_started="2026-09-23T10:00:00.000001+00:00",
                    orphan_status="done", witness=2):
    tasks, comments, calls = p2_case(monkeypatch, tmp_path, replies)
    # The witness: a later round's published verdict, re-derived from its own run record. The orphan ran at
    # round 1's head, so its head is a round already counted.
    write_task(tasks, task_id=f"round-{witness}", worktree_base_sha=str(witness) * 40,
               started_at="2026-09-23T11:00:00.000001+00:00", reply=replies[witness - 1], review_mode="cross_family",
               **ANTHROPIC)
    write_task(tasks, task_id="orphan", worktree_base_sha="1" * 40, started_at=orphan_started, reply=orphan_reply,
               status=orphan_status, review_mode="cross_family", **ANTHROPIC)
    seat(tasks, VERIFIED)
    return tasks, comments, calls


@pytest.mark.parametrize("orphan_reply", [reply(finding("F0")), reply(finding("F0", "P1")), "VERDICT: APPROVE"],
                         ids=["p2", "p1-resolved-by-a-later-structured-verdict", "approve"])
def test_a_superseded_unpublished_run_is_admitted(monkeypatch, tmp_path, orphan_reply):
    tasks, _comments, _calls = superseded_case(monkeypatch, tmp_path, orphan_reply)
    result = record(tasks, tmp_path)
    assert result["verdict"] == "APPROVED" and result["budget_grant"]["cited_verdict_head"] == REJECTED_HEAD


def test_an_unpublished_run_its_seat_never_superseded_is_refused(monkeypatch, tmp_path):
    # Started after every published verdict of its seat, so no later same-seat verdict exists.
    tasks, _comments, calls = superseded_case(monkeypatch, tmp_path, reply(finding("F0")),
                                              orphan_started="2026-09-23T13:00:00.000001+00:00")
    refused(tasks, tmp_path, "evidence")
    assert calls["posts"] == 0 and not receipts(tmp_path)


@pytest.mark.parametrize(
    "orphan_reply,reason",
    [(reply(finding("F0", "P1")), "blocker"), ("VERDICT: BLOCKED", "blocker"),
     ("VERDICT: REQUEST_CHANGES\nF0 [P2] docs/readme.md:3 race.\nSECURITY_VERDICT: FAIL", "blocker")],
    ids=["open-p1", "blocked", "security-fail"],
)
def test_a_superseded_run_still_counts_for_the_ledger_rules(monkeypatch, tmp_path, orphan_reply, reason):
    # Prose verdicts never close a finding, so the superseded run's P1 stays open: supersession resolves none.
    prose = tuple(f"VERDICT: REQUEST_CHANGES\nF{n} [P2] docs/readme.md:{n} the retry path races." for n in (1, 2, 3))
    tasks, _comments, calls = superseded_case(monkeypatch, tmp_path, orphan_reply, replies=prose)
    refused(tasks, tmp_path, reason)
    assert calls["posts"] == 0 and not receipts(tmp_path)


@pytest.mark.parametrize("variant", ["no-reply", "not-done-with-verdict"])
def test_the_other_rule_five_refusals_stay_for_a_seat_with_a_later_verdict(monkeypatch, tmp_path, variant):
    tasks, _comments, _calls = superseded_case(monkeypatch, tmp_path, reply(finding("F0")))
    if variant == "no-reply":
        (tasks / "orphan.result").unlink()
    else:
        write_task(tasks, task_id="orphan", worktree_base_sha="1" * 40, started_at="2026-09-23T10:00:00.000001+00:00",
                   reply=reply(finding("F0")), status="failed", review_mode="cross_family", **ANTHROPIC)
    refused(tasks, tmp_path, "evidence")


def restart(comments, index, replies, started):
    """Re-post round ``index + 1``'s marker with another start time, as a verdict from a run begun then."""
    comments[index]["body"] = recorder.build_comment(
        sha=str(index + 1) * 40, task_id=f"round-{index + 1}", started=started, verdict="CHANGES_REQUESTED",
        model="claude-opus-5-5", family="anthropic", reply=replies[index])


def test_a_verdict_started_before_a_superseded_run_cannot_close_its_finding(monkeypatch, tmp_path):
    # The orphan (10:00) raises a P1. A structured verdict that omits it but started at 09:00, though published
    # later, never saw it; the rejections that did see it are prose, which close nothing.
    prose = tuple(f"VERDICT: REQUEST_CHANGES\nF{n} [P2] docs/readme.md:{n} the retry path races." for n in (1, 3))
    replies = (prose[0], reply(finding("F3")), prose[1])
    tasks, comments, calls = superseded_case(monkeypatch, tmp_path, reply(finding("F9", "P1")), replies=replies,
                                              witness=3)
    restart(comments, 1, replies, "2026-09-23T09:00:00.000001+00:00")
    refused(tasks, tmp_path, "blocker")
    assert calls["posts"] == 0 and not receipts(tmp_path)


def test_a_superseded_run_that_nothing_closed_must_be_among_the_sealed_ids(monkeypatch, tmp_path):
    # An unresolved P2 of the superseded run (F9) is an open finding: the sealed set names only F3.
    prose = tuple(f"VERDICT: REQUEST_CHANGES\nF{n} [P2] docs/readme.md:{n} the retry path races." for n in (1, 2, 3))
    tasks, _comments, calls = superseded_case(monkeypatch, tmp_path, reply(finding("F9")), replies=prose)
    refused(tasks, tmp_path, "binding")
    assert calls["posts"] == 0 and not receipts(tmp_path)
