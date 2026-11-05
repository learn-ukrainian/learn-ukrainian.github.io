"""A review that could not happen charges no round, once per lineage (#12717).

CTO grant 808f602f99794a59b644feb4f9a9f8b4 approved these cases; each docstring names the defect
class it catches. The sealed capability-charge adjustment cases went with the budget grant.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from scripts.review import capability_failure as cf
from scripts.review import record_cf_verdict as recorder
from scripts.review.review_lineage import ReviewRun, capability_exemption, dispatched_rounds
from tests.test_record_cf_verdict import (
    BRANCH,
    REPOSITORY,
    recorded_verdict,
    recorder_matcher,  # noqa: F401 - autouse publication scanner rules
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


# Positive cases.


def test_ci_logs_is_a_declarable_capability():
    """Defect class: a reviewer that cannot read CI or execution logs has no capability to declare."""
    reply = blocked_reply()
    failure = cf.classify("r3", r3_record(reply), reply, capability="ci-logs", authority="claude-cto")
    assert failure.capability == "ci-logs" and failure.sha == H3


def exempt_r3():
    return {"task": "r3", "started": R3_STARTED, "run_nonce": "r3-run", "head": H3, "seat": ("openai", "code")}


def test_the_one_replacement_must_be_the_exempt_runs_seat():
    """Defect class: another reviewer takes the replacement round freed for the seat that lacked a capability."""
    comments = [recorded_verdict(H1, "CHANGES_REQUESTED", task_id="round-1"),
                recorded_verdict(H2, "CHANGES_REQUESTED", task_id="round-2")]

    def decide(seat):
        return recorder.require_review_round_within_budget(
            comments, NEXT, "fleet", budget=3, pr=42, exemption=exempt_r3, recording_seat=seat,
        )

    with pytest.raises(recorder.RecordError, match="CAPABILITY_REPLACEMENT_REFUSED"):
        decide(("anthropic", "code"))
    assert decide(("openai", "code"))["capability_exemption"]["task"] == "r3"


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


def test_once_the_replacement_ran_at_a_new_head_no_further_head_or_exempt_head_retry_is_admitted():
    """Defect class: head churn, or a retry at the exempt head admitted by the recorded-head dedup, replenishes it."""
    comments = [recorded_verdict(H1, "CHANGES_REQUESTED", task_id="round-1"),
                recorded_verdict(H2, "CHANGES_REQUESTED", task_id="round-2"),
                recorded_verdict(NEXT, "CHANGES_REQUESTED", task_id="review-one")]

    def decide(head):
        return recorder.require_review_round_within_budget(
            comments, head, "fleet", budget=3, pr=42, exemption=exempt_r3, recording_seat=("openai", "code"),
        )

    with pytest.raises(recorder.RecordError, match=r"REVIEW_BUDGET_EXHAUSTED.*capability failure of r3 consumes no round"):
        decide("5" * 40)
    # The exempt head carries no verdict, so it is no already reviewed head that a retry may reuse for free.
    with pytest.raises(recorder.RecordError, match="REVIEW_BUDGET_EXHAUSTED"):
        decide(H3)


# 3. Concurrent claims.


@pytest.mark.parametrize("order", [1, -1], ids=["arrival", "reversed"])
def test_competing_claims_resolve_to_one_exemption_whatever_their_order(order):
    """Defect class: concurrent events each uncharge a run, so a lineage gains two free rounds."""
    early = run("early", H1, "2026-09-23T10:00:00.000001+00:00")
    late = run("late", H2, "2026-09-23T12:00:00.000001+00:00")
    claims = [event(late), event(early)][::order]
    assert capability_exemption(runs=[late, early][::order], comments=claims, login="fleet") == (
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


# 4. Security refusals.


def test_a_non_pass_security_verdict_in_a_decoded_string_is_never_a_capability_failure():
    """Defect class: a security FAIL hidden behind a JSON escape is classified as a capability failure."""
    # The raw reply never spells SECURITY_VERDICT: only its decoded string does.
    reply = blocked_reply(explanation="Logs unreadable. SECURITY_VERDICT: FAIL").replace("SECURITY_", "SECURITY\\u005f")
    assert "SECURITY_VERDICT" not in reply
    with pytest.raises(cf.CapabilityFailureRefused, match=r"\[substance\].*security verdict that is not PASS"):
        cf.classify("r3", r3_record(reply), reply, capability="ci-logs", authority="claude-cto")
