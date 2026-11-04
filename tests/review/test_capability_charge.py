"""A review that could not happen charges no round, once per lineage (#12717).

CTO grant 808f602f99794a59b644feb4f9a9f8b4 approved exactly these cases; each docstring names
the defect class it catches. Grant 996d835caec54f5a92abbcf4a7948039 asked for the schema-digest case.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from scripts.review import budget_grant
from scripts.review import capability_failure as cf
from scripts.review import record_cf_verdict as recorder
from scripts.review.review_contract import SCHEMA_RELATIVE_PATH
from scripts.review.review_lineage import ReviewRun, capability_exemption, dispatched_rounds
from tests.test_record_cf_verdict import (
    BRANCH,
    GRANT_REQUEST,
    REPOSITORY,
    facts_for,
    move_head,
    recorded_verdict,
    recorder_matcher,  # noqa: F401 - autouse publication scanner rules
    setup_record,
    write_grant,
    write_task,
)

H1, H2, H3, NEXT = "1" * 40, "2" * 40, "3" * 40, "4" * 40
R3_STARTED = "2026-09-23T10:00:00.000001+00:00"
STAMP = "2026-09-23T10:30:00Z"


def blocked_reply(*, missing=("ci-logs",), explanation="CI run 41768361838 succeeded; its logs could not be read.",
                  findings=()):
    payload = {
        "schema_version": "code-review-findings.v1",
        "overall": {"correctness": "uncertain", "explanation": explanation, "confidence": 0.9},
        "findings": list(findings),
    }
    if missing is not None:
        payload["missing_capabilities"] = list(missing)
    return json.dumps(payload)


def r3_record(reply, **updates):
    record = {
        "task_id": "r3", "repository": REPOSITORY, "review_branch": BRANCH, "schema_version": 2, "pr": 42,
        "worktree_base_sha": H3, "pinned_head": H3, "model": "gpt-6.1-sol", "agent": "codex",
        "review_mode": "cross_family", "started_at": R3_STARTED, "run_nonce": "r3-run",
        "result_sha256": hashlib.sha256(reply.encode()).hexdigest(), "status": "done", "mode": "read-only",
    }
    record.update(updates)
    return record


def published(sha, task_id, started, verdict, reply, *, edited=False, comment_id=3):
    body = recorder.build_comment(sha=sha, task_id=task_id, started=started, verdict=verdict, model="gpt-6.1-sol",
                                  family="openai", reply=reply)
    return {"id": comment_id, "body": body, "user": {"login": "fleet"}, "author_association": "MEMBER",
            "created_at": STAMP, "updated_at": "2026-09-23T10:45:00Z" if edited else STAMP}


def charge_request(reply, **run):
    bound = {"task_id": "r3", "run_nonce": "r3-run", "reviewed_sha": H3,
             "reply_sha256": hashlib.sha256(reply.encode()).hexdigest(), **run}
    return {**GRANT_REQUEST, "finding_id": None, "blocker_class": budget_grant.CAPABILITY_CHARGE,
            "p2_fix_verification": None, "owner_request": None,
            "withheld_capability": {"capability": "ci-logs", "uncharged_run": bound}}


def spent_case(monkeypatch, tmp_path, *, reply=None, grant=True, request=None, edited=False, **replacement):
    """PR 12704's shape: rounds at H1 and H2, a published capability-only BLOCKED at H3, and the head at SHA."""
    reply = blocked_reply() if reply is None else reply
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    monkeypatch.setattr(recorder, "pr_review_facts", lambda *_a, **_k: facts_for({"google"}, changed_paths=("docs/readme.md",)))
    comments.extend([recorded_verdict(H1, "CHANGES_REQUESTED", task_id="round-1"),
                     recorded_verdict(H2, "APPROVED", task_id="round-2"),
                     published(H3, "r3", R3_STARTED, recorder._review_verdict_and_count(reply)[0], reply, edited=edited)])
    (tasks / "r3.json").write_text(json.dumps(r3_record(reply)))
    (tasks / "r3.result").write_text(reply)
    if grant:
        write_grant(tasks, request or charge_request(reply), task_id="charge-approval",
                    decision={"admission_exclusion_attestation": budget_grant.CHARGE_ATTESTATION})
    write_task(tasks, task_id="review-one", review_mode="cross_family", run_nonce="review-one-run", **replacement)
    return tasks, comments, calls


def record(tasks, tmp_path, task_id="review-one"):
    return recorder.record(task_id, pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")


# Positive cases.


def test_one_sealed_adjustment_frees_exactly_one_round_for_a_published_capability_blocked(monkeypatch, tmp_path):
    """Defect class: a published capability-only empty-findings BLOCKED spends the last round, so no review can follow."""
    tasks, comments, _calls = spent_case(monkeypatch, tmp_path, grant=False)
    with pytest.raises(recorder.RecordError, match="REVIEW_BUDGET_EXHAUSTED"):
        record(tasks, tmp_path)
    tasks, comments, calls = spent_case(monkeypatch, tmp_path / "granted")
    before = [dict(item) for item in comments]
    result = record(tasks, tmp_path)
    exemption = result["capability_exemption"]
    assert (exemption["task"], exemption["head"], exemption["source"]) == ("r3", H3, "charge-adjustment")
    assert exemption["adjustment"]["grant_task"] == "charge-approval" and calls["posts"] == 1
    # Append-only: the published BLOCKED and every earlier comment stay exactly as they were.
    assert comments[: len(before)] == before


def test_ci_logs_is_a_declarable_capability():
    """Defect class: a reviewer that cannot read CI or execution logs has no capability to declare."""
    reply = blocked_reply()
    failure = cf.classify("r3", r3_record(reply), reply, capability="ci-logs", authority="claude-cto")
    assert failure.capability == "ci-logs" and failure.sha == H3


def test_the_one_replacement_must_be_the_exempt_runs_seat(monkeypatch, tmp_path):
    """Defect class: another reviewer takes the replacement round freed for the seat that lacked a capability."""
    tasks, _comments, calls = spent_case(monkeypatch, tmp_path, model="claude-opus-5-5", agent="claude")
    with pytest.raises(recorder.RecordError, match="CAPABILITY_REPLACEMENT_REFUSED"):
        record(tasks, tmp_path)
    assert calls["posts"] == 0


def test_a_run_dispatched_under_the_pre_change_schema_stays_schema_bound():
    """Defect class: adding ci-logs to the schema unbinds every earlier structured run from the grant readers."""
    path = f"/repo/{SCHEMA_RELATIVE_PATH}"
    [prior] = budget_grant.PRIOR_SCHEMA_SHA256
    assert budget_grant._findings_schema_bound({"output_schema_path": path, "output_schema_sha256": prior}) is True
    assert budget_grant._findings_schema_bound({"output_schema_path": path, "output_schema_sha256": "0" * 64}) is None


# 1. Repeated BLOCKED replies.


def run(task_id, head, started, reply=None):
    reply = blocked_reply() if reply is None else reply
    record = r3_record(reply, task_id=task_id, worktree_base_sha=head, pinned_head=head, started_at=started,
                       run_nonce=f"{task_id}-run")
    return ReviewRun(task_id, record, reply)


def event(item):
    failure = cf.classify(item.task_id, item.record, item.reply, capability="ci-logs", authority="claude-cto")
    return {"id": hash(item.task_id) % 1000, "body": cf.build_comment(failure), "user": {"login": "fleet"},
            "author_association": "MEMBER", "created_at": STAMP, "updated_at": STAMP}


def test_a_second_capability_failure_in_the_lineage_stays_charged():
    """Defect class: repeated capability-only BLOCKED replies, each classified, never spend a round."""
    first = run("first", H1, "2026-09-23T10:00:00.000001+00:00")
    replacement = run("replacement", H1, "2026-09-23T11:00:00.000001+00:00")
    later = run("later", H2, "2026-09-23T12:00:00.000001+00:00")
    comments = [event(first), event(replacement), event(later)]
    # The failed replacement charges the original head, and the later head stays charged too.
    assert dispatched_rounds(runs=[first, replacement, later], comments=comments, login="fleet") == {
        H1: ["replacement"], H2: ["later"]}


# 2. Head churn.


def test_once_the_replacement_ran_at_a_new_head_no_further_head_or_exempt_head_retry_is_admitted(
    monkeypatch, tmp_path
):
    """Defect class: head churn, or a retry at the exempt head admitted by the recorded-head dedup, replenishes it."""
    tasks, _comments, _calls = spent_case(monkeypatch, tmp_path)
    record(tasks, tmp_path)
    move_head(monkeypatch, NEXT)
    write_task(tasks, task_id="round-five", worktree_base_sha=NEXT, review_mode="cross_family", run_nonce="five")
    with pytest.raises(recorder.RecordError, match=r"REVIEW_BUDGET_EXHAUSTED.*capability failure of r3 consumes no round"):
        record(tasks, tmp_path, "round-five")
    # The exempt head's only verdict is r3's, so it is no already reviewed head that a retry may reuse for free.
    move_head(monkeypatch, H3)
    write_task(tasks, task_id="retry-h3", worktree_base_sha=H3, reply="VERDICT: REQUEST_CHANGES",
               review_mode="cross_family", run_nonce="retry")
    with pytest.raises(recorder.RecordError, match="REVIEW_BUDGET_EXHAUSTED"):
        record(tasks, tmp_path, "retry-h3")


# 3. Concurrent claims.


@pytest.mark.parametrize("order", [1, -1], ids=["arrival", "reversed"])
def test_competing_claims_resolve_to_one_exemption_whatever_their_order(order):
    """Defect class: concurrent events and rulings each uncharge a run, so a lineage gains two free rounds."""
    early = run("early", H1, "2026-09-23T10:00:00.000001+00:00")
    late = run("late", H2, "2026-09-23T12:00:00.000001+00:00")
    claims = [event(late), event(early)][::order]
    adjusted = [("late", late.record["started_at"]), ("early", early.record["started_at"])][::order]
    assert capability_exemption(runs=[late, early][::order], comments=claims, login="fleet") == (
        "early", early.record["started_at"])
    assert capability_exemption(runs=[late, early], comments=(), login="fleet", adjusted=adjusted) == (
        "early", early.record["started_at"])


def test_the_dispatcher_defers_an_exempt_only_head_to_the_full_check(monkeypatch, tmp_path):
    """Defect class: the dispatcher reads no comments and admits a run at the exempt head as a free retry."""
    tasks = tmp_path / "tasks"
    for task_id, head, reply in (("round-1", H1, "VERDICT: REQUEST_CHANGES"), ("round-2", H2, "VERDICT: APPROVE")):
        write_task(tasks, task_id=task_id, worktree_base_sha=head, reply=reply, review_mode="cross_family")
    reply = blocked_reply()
    (tasks / "r3.json").write_text(json.dumps(r3_record(reply)))
    (tasks / "r3.result").write_text(reply)
    deferred = []
    monkeypatch.setattr(recorder, "budget_check", lambda *_a, **kwargs: deferred.append(kwargs["head"]) or {})
    assert recorder.dispatch_budget_check(REPOSITORY, number=42, branch=BRANCH, head=H2, task_root=tasks) is None
    assert deferred == []
    assert recorder.dispatch_budget_check(REPOSITORY, number=42, branch=BRANCH, head=H3, task_root=tasks) == {}
    assert deferred == [H3]


# 4. Tampered evidence.


@pytest.mark.parametrize(
    "case,reason",
    [
        ("run-nonce", "evidence"),
        ("reviewed-head", "evidence"),
        ("reply-digest", "evidence"),
        ("edited-publication", "evidence"),
        ("prose-with-finding", "blocker"),
        ("severity-in-prose", "blocker"),
        ("other-capability", "capability"),
        ("attestation", "approval"),
    ],
)
def test_a_tampered_adjustment_adjusts_nothing(monkeypatch, tmp_path, case, reason):
    """Defect class: an adjustment whose bindings, publication, reply or attestation do not hold still uncharges a run."""
    reply = blocked_reply()
    request = None
    edited = False
    if case in ("run-nonce", "reviewed-head", "reply-digest"):
        field, value = {"run-nonce": ("run_nonce", "other-run"), "reviewed-head": ("reviewed_sha", NEXT),
                        "reply-digest": ("reply_sha256", "e" * 64)}[case]
        request = charge_request(reply, **{field: value})
    elif case == "edited-publication":
        edited = True
    elif case == "prose-with-finding":
        # Only a structured object proves zero findings; a prose BLOCKED's count is unknown.
        reply = "VERDICT: BLOCKED (missing capability: ci-logs)\nF1 [P3] docs/readme.md:1 a follow-up."
    elif case == "severity-in-prose":
        reply = blocked_reply(explanation="Logs unreadable; the retry path may also hide a P1 race.")
    elif case == "other-capability":
        reply = blocked_reply(missing=("shell",))
    tasks, _comments, calls = spent_case(monkeypatch, tmp_path, reply=reply, request=request, edited=edited)
    if case == "attestation":
        write_grant(tasks, charge_request(reply), task_id="charge-approval",
                    decision={"admission_exclusion_attestation": {**budget_grant.CHARGE_ATTESTATION,
                                                                  "no_security_fail": False}})
    with pytest.raises(recorder.RecordError,
                       match=rf"REVIEW_BUDGET_EXHAUSTED.*capability charge adjustment refused: "
                             rf"BUDGET_GRANT_REFUSED\[{reason}\]"):
        record(tasks, tmp_path)
    assert calls["posts"] == 0


# 5. Security refusals.


def test_a_non_pass_security_verdict_in_a_decoded_string_stays_charged_and_blocking(monkeypatch, tmp_path):
    """Defect class: a security FAIL hidden behind a JSON escape is classified or adjusted as a capability failure."""
    # The raw reply never spells SECURITY_VERDICT: only its decoded string does.
    reply = blocked_reply(explanation="Logs unreadable. SECURITY_VERDICT: FAIL").replace("SECURITY_", "SECURITY\\u005f")
    assert "SECURITY_VERDICT" not in reply
    with pytest.raises(cf.CapabilityFailureRefused, match=r"\[substance\].*security verdict that is not PASS"):
        cf.classify("r3", r3_record(reply), reply, capability="ci-logs", authority="claude-cto")
    tasks, _comments, calls = spent_case(monkeypatch, tmp_path, reply=reply)
    with pytest.raises(recorder.RecordError, match=r"capability charge adjustment refused: BUDGET_GRANT_REFUSED\[blocker\]"):
        record(tasks, tmp_path)
    assert calls["posts"] == 0
