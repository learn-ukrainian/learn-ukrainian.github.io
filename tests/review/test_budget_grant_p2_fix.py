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
VERIFIED = f"VERDICT: APPROVE\nP2_FIX_DELTA: {DELTA} VERIFIED"


def finding(finding_id: str, priority: str = "P2") -> dict[str, object]:
    return {"id": finding_id, "title": f"[{priority}] {finding_id} retry path", "body": "The retry loses the lock.",
            "priority": priority, "confidence": 0.9, "category": "correctness",
            "location": {"path": "docs/readme.md", "start_line": 3, "end_line": 3, "claim_type": "present"},
            "verbatim": "retry()", "why_wrong": "Two writers race.", "smallest_fix": "Hold the lock.",
            "sources": ["docs/readme.md:3"]}


def reply(*findings: dict[str, object]) -> str:
    """A schema-bound rejection, the reply a code review of record returns."""
    return json.dumps({"schema_version": "code-review-findings.v1",
                       "overall": {"correctness": "incorrect", "explanation": "Changes needed.", "confidence": 0.9},
                       "findings": list(findings)})


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
    if request is not None:
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
    if case in {"earlier-p1-unresolved", "earlier-p1-incidental-closing-word"}:
        replies[0] = "VERDICT: REQUEST_CHANGES\nF1 [P1] docs/readme.md:3 two writers race on the lock."
        replies[1] = "VERDICT: REQUEST_CHANGES\nF2 [P2] docs/readme.md:4 the retry path still races."
        # A prose ledger that omits F1 is no resolution (a structured object that omits it would be).
        replies[2] = "VERDICT: REQUEST_CHANGES\nF3 [P2] docs/readme.md:5 the retry path drops the lease."
    if case == "earlier-p1-incidental-closing-word":  # A description word is not a disposition.
        replies[0] = "VERDICT: REQUEST_CHANGES\nF1 [P1] docs/readme.md:3 The fixed timeout lets any writer keep the lock."
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
    replies = ("VERDICT: REQUEST_CHANGES\nF1 [P1] docs/readme.md:3 two writers race on the lock.",
               "VERDICT: REQUEST_CHANGES\nF1 [P1] fixed with evidence.\n\nF2 [P2] docs/readme.md:4 retry races.",
               f"VERDICT: REQUEST_CHANGES\nSCORE: 7/10\n\n```json\n{reply(finding('F3'))}\n```")
    tasks, _comments, _calls = p2_case(monkeypatch, tmp_path, replies)
    approve = json.dumps({"schema_version": "code-review-findings.v1", "findings": [], "overall": {
        "correctness": "correct", "confidence": 0.9, "explanation": f"F3 fixed. P2_FIX_DELTA: {DELTA} VERIFIED"}})
    seat(tasks, approve)
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


def approve(explanation: str, *findings: dict[str, object]) -> str:
    return json.dumps({"schema_version": "code-review-findings.v1", "findings": list(findings), "overall": {
        "correctness": "correct", "confidence": 0.9, "explanation": explanation}})


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("VERDICT: APPROVE", id="missing"),
        pytest.param(f"VERDICT: APPROVE\nP2_FIX_DELTA: {DELTA} REFUTED", id="false"),
        pytest.param(f"VERDICT: APPROVE\nP2_FIX_DELTA: {DELTA} VERIFIED\nF3 still open: [P2] still races.", id="false-open"),
        pytest.param(f"VERDICT: APPROVE\nP2_FIX_DELTA: {'e' * 64} VERIFIED", id="mismatched"),
        pytest.param(approve(f"P2_FIX_DELTA: {DELTA} VERIFIED", finding("F3", "P3")), id="structured-still-listed"),
        pytest.param(approve("Looks right.", finding("F9", "P3") | {"verbatim": f"P2_FIX_DELTA: {DELTA} VERIFIED"}),
                     id="token-only-in-quoted-code"),
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


@pytest.mark.parametrize("text", ["VERDICT: APPROVE", reply(finding("F3", "P3"))], ids=["approve", "p3-residual"])
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
