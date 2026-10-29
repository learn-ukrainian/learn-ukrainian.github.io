"""A review run that failed only for a missing capability: classification, event, lineage and recorder."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from scripts.guardrails.delegate_ownership import TERMINAL_TASK_STATUSES
from scripts.orchestration import integration_sweep as sweep
from scripts.review import capability_failure as cf
from scripts.review import record_cf_verdict as recorder
from scripts.review.review_lineage import LineageRefused, ReviewRun, check_lineage
from scripts.review.verdict_parser import recognized_verdicts
from tests.test_record_cf_verdict import BRANCH, OTHER, SHA, recorded_verdict, setup_record

EARLIER = "c" * 40
STARTED = "2026-09-23T10:00:00.000001+00:00"
UNIT_DIGEST = "d" * 64


@pytest.fixture
def opsec_rules(synthetic_opsec):
    """The synthetic scanner with the absolute-path rule the recorder's citation rewrite needs."""
    from tests.opsec_fixtures import synthetic_rules

    rules = synthetic_rules(rule="3-absolute-path", level=3, pattern=r"(?<![<\w:])/[A-Za-z][^\s`'\"<>),;\]}|*]*")
    (synthetic_opsec / "rules.json").write_text(json.dumps(rules))
    return synthetic_opsec


def structured(*, correctness="uncertain", findings=(), missing=("test-execution",)):
    payload = {
        "schema_version": "code-review-findings.v1",
        "overall": {"correctness": correctness, "explanation": "The targeted tests could not run.", "confidence": 0.5},
        "findings": list(findings),
    }
    if missing is not None:
        payload["missing_capabilities"] = list(missing)
    return json.dumps(payload)


FINDING = {
    "id": "F1",
    "title": "Unit finding",
    "body": "A unit finding body.",
    "priority": "P3",
    "confidence": 0.8,
    "category": "correctness",
    "location": {"path": "scripts/unit.py", "start_line": 1, "end_line": 1, "claim_type": "present"},
    "verbatim": "unit",
    "why_wrong": "It is a unit.",
    "smallest_fix": "Replace the unit.",
    "sources": ["none"],
}


def run_record(*, sha=EARLIER, reply=None, **updates):
    reply = structured() if reply is None else reply
    record = {
        "task_id": "review-blocked",
        "repository": "owner/repo",
        "review_branch": BRANCH,
        "schema_version": 2,
        "worktree_base_sha": sha,
        "pinned_head": sha,
        "model": "gpt-6.1-sol",
        "agent": "codex",
        "review_mode": "cross_family",
        "started_at": STARTED,
        "run_nonce": "nonce-one",
        "result_sha256": hashlib.sha256(reply.encode()).hexdigest(),
        "status": "done",
    }
    record.update(updates)
    return record, reply


def classify(record, reply, *, capability="test-execution", authority="claude-cto"):
    return cf.classify("review-blocked", record, reply, capability=capability, authority=authority)


def event_comment(failure, *, login="fleet", edited=False, body=None):
    stamp = "2026-09-23T10:30:00Z"
    return {
        "id": 900,
        "body": cf.build_comment(failure) if body is None else body,
        "user": {"login": login},
        "author_association": "MEMBER",
        "created_at": stamp,
        "updated_at": "2026-09-23T10:45:00Z" if edited else stamp,
    }


# 1. The shared classification.


def test_a_structured_blocked_with_zero_findings_and_a_declared_capability_qualifies():
    record, reply = run_record()
    failure = classify(record, reply)
    assert failure == cf.CapabilityFailure(
        task="review-blocked",
        started=STARTED,
        run="nonce-one",
        sha=EARLIER,
        result_sha256=record["result_sha256"],
        capability="test-execution",
        model="gpt-6.1-sol",
        family="openai",
        authority="claude-cto",
    )


def test_sources_mcp_is_evidenced_by_the_runtime_count_on_the_ukrainian_profile():
    record, reply = run_record(reply=structured(missing=None), review_profile="ukrainian", sources_mcp_call_count=0)
    assert classify(record, reply, capability="sources-mcp").capability == "sources-mcp"


@pytest.mark.parametrize(
    "updates",
    [
        {"review_profile": "code", "sources_mcp_call_count": 0},
        {"review_profile": "ukrainian", "sources_mcp_call_count": 3},
        {"review_profile": "ukrainian"},
        {"review_profile": "ukrainian", "sources_mcp_call_count": "0"},
    ],
    ids=["not-required", "calls-made", "count-unknown", "count-malformed"],
)
def test_sources_mcp_without_runtime_evidence_refuses(updates):
    # A reply declaring Sources missing is not runtime evidence.
    record, reply = run_record(reply=structured(missing=("sources-mcp",)), **updates)
    with pytest.raises(cf.CapabilityFailureRefused, match=r"\[capability\].*Sources MCP"):
        classify(record, reply, capability="sources-mcp")


@pytest.mark.parametrize(
    "reply,match",
    [
        # A prose reply's count is unknown, even when it names no finding.
        ("VERDICT: BLOCKED - sandbox prevents pytest.", r"\[findings\].*no known finding count"),
        # "No in-scope blocker" is not zero findings.
        ("VERDICT: BLOCKED\nNo in-scope blocker.\nF1 [P3] scripts/unit.py:1 a follow-up.", r"\[findings\]"),
        ("VERDICT: APPROVE", r"\[verdict\].*APPROVED, not BLOCKED"),
        (structured(correctness="incorrect", findings=[FINDING]), r"\[verdict\].*CHANGES_REQUESTED"),
        ('{"schema_version": "code-review-findings.v1", "overall": {}}', r"\[run\].*evidence refused"),
    ],
    ids=["prose-zero", "prose-findings", "approve", "structured-findings", "malformed"],
)
def test_a_reply_without_a_known_zero_finding_blocked_refuses(reply, match):
    record, reply = run_record(reply=reply)
    with pytest.raises(cf.CapabilityFailureRefused, match=match):
        classify(record, reply)


@pytest.mark.parametrize(
    "missing,capability,match",
    [
        (None, "test-execution", r"does not declare test-execution"),
        (("shell",), "test-execution", r"does not declare test-execution"),
        (("teleport",), "test-execution", r"must be a non-empty list"),
        ((), "test-execution", r"must be a non-empty list"),
        (("shell", "shell"), "shell", r"must be a non-empty list"),
        (("shell",), "teleport", r"'teleport' is not one of"),
    ],
)
def test_an_unevidenced_capability_refuses(missing, capability, match):
    record, reply = run_record(reply=structured(missing=missing))
    with pytest.raises(cf.CapabilityFailureRefused, match=rf"\[capability\].*{match}"):
        classify(record, reply, capability=capability)


@pytest.mark.parametrize(
    "updates,match",
    [
        ({"status": "failed"}, r"did not finish"),
        ({"run_nonce": None}, r"no recorded start and run nonce"),
        ({"started_at": "2026-09-23T10:00:00"}, r"no recorded start and run nonce"),
        ({"result_sha256": None}, r"no recorded reply digest"),
        ({"pinned_head": OTHER}, r"no single reviewed SHA"),
        ({"model": "unknown model"}, r"evidence refused"),
    ],
)
def test_a_run_without_its_bindings_refuses(updates, match):
    record, reply = run_record(**updates)
    with pytest.raises(cf.CapabilityFailureRefused, match=rf"\[run\].*{match}"):
        classify(record, reply)


def test_every_verdict_reader_sees_a_declared_reply_as_blocked():
    """Dispatch's verdict check reads the documented shape, so such a run can finish ``done``."""
    assert recognized_verdicts(structured()) == ["BLOCKED"]
    assert recognized_verdicts(structured(missing=("teleport",))) == ["BLOCKED"]


def test_a_reply_the_verdict_readers_disagree_on_refuses():
    reply = json.dumps({**json.loads(structured()), "unreviewed_key": True})
    assert recorder._review_verdict_and_count(reply) == ("BLOCKED", 0) and recognized_verdicts(reply) == []
    record, reply = run_record(reply=reply)
    with pytest.raises(cf.CapabilityFailureRefused, match=r"\[verdict\].*not read as one BLOCKED by every reader"):
        classify(record, reply)


def test_only_the_cto_seat_records_a_classification():
    record, reply = run_record()
    with pytest.raises(cf.CapabilityFailureRefused, match=r"\[authority\]"):
        classify(record, reply, authority="claude-cto-8a2cb6e8")


def test_the_event_carries_no_verdict_and_round_trips():
    record, reply = run_record()
    failure = classify(record, reply)
    body = cf.build_comment(failure)
    assert recorder.MARKER_PREFIX not in body
    assert not any(line.lstrip().upper().startswith("VERDICT:") for line in body.splitlines())
    assert cf.events([event_comment(failure)], "fleet") == [failure]


# 2. The lineage.


def lineage(*runs, comments, approved=SHA, exclude_head=None):
    return check_lineage(runs=list(runs), comments=comments, login="fleet", approved=approved, exclude_head=exclude_head)


def approving_run():
    """A finished run whose APPROVE at ``SHA`` is published, as ``recorded_verdict`` posts it."""
    record = {
        "task_id": "review-approve",
        "worktree_base_sha": SHA,
        "model": "claude-opus-5-5",
        "agent": "claude",
        "started_at": "2026-09-23T11:00:00.000001+00:00",
        "status": "done",
    }
    return ReviewRun("review-approve", record, "VERDICT: APPROVED"), recorded_verdict(
        SHA, "APPROVED", task_id="review-approve"
    )


def blocked_run(*, capability="test-execution", **updates):
    record, reply = run_record(**updates)
    return ReviewRun("review-blocked", record, reply), classify(record, reply, capability=capability)


def test_a_capability_failure_without_its_event_still_refuses_the_lineage():
    approve, verdict = approving_run()
    blocked, _failure = blocked_run()
    with pytest.raises(LineageRefused, match="review task review-blocked finished but its verdict is unpublished"):
        lineage(approve, blocked, comments=[verdict])


def test_a_published_capability_failure_lets_the_lineage_pass_and_fills_no_seat():
    approve, verdict = approving_run()
    blocked, failure = blocked_run()
    assert lineage(approve, blocked, comments=[verdict, event_comment(failure)]) == ["anthropic"]


def test_a_capability_failure_waives_no_required_seat():
    """A Ukrainian change still needs two approving seats; a capability failure at its head fills none."""
    approve, _ = approving_run()
    approve.record.update(review_profile="ukrainian", sources_mcp_call_count=4)
    verdict = recorded_verdict(SHA, "APPROVED", task_id="review-approve")
    verdict["body"] = recorder.build_comment(
        sha=SHA,
        task_id="review-approve",
        started="2026-09-23T11:00:00.000001+00:00",
        verdict="APPROVED",
        model="claude-opus-5-5",
        family="anthropic",
        reply="VERDICT: APPROVED",
        review_profile="ukrainian",
        sources_mcp_call_count=4,
    )
    blocked, failure = blocked_run(
        capability="sources-mcp", sha=SHA, reply=structured(missing=None), review_profile="ukrainian",
        sources_mcp_call_count=0,
    )
    # The keeper's own reading already lacks the second seat (#12020).
    with pytest.raises(LineageRefused, match=r"reads as needs-seat, not APPROVED"):
        lineage(approve, blocked, comments=[verdict, event_comment(failure)])


@pytest.mark.parametrize("status", sorted(TERMINAL_TASK_STATUSES - {"done"}))
@pytest.mark.parametrize("missing", [("test-execution",), ("teleport",), "shell"], ids=["valid", "unknown", "malformed"])
def test_a_declaration_never_hides_an_unfinished_runs_verdict(status, missing):
    """A run that did not finish keeps refusing the lineage when its reply has a verdict (round 1, F1)."""
    approve, verdict = approving_run()
    reply = json.dumps({**json.loads(structured(correctness="incorrect", findings=[FINDING])), "missing_capabilities": missing})
    record, reply = run_record(reply=reply, status=status)
    with pytest.raises(LineageRefused, match=rf"review task review-blocked \({status}\) carries an unpublished verdict"):
        lineage(approve, ReviewRun("review-blocked", record, reply), comments=[verdict])


def test_a_blocked_with_a_finding_keeps_todays_treatment_even_with_an_event():
    approve, verdict = approving_run()
    reply = "VERDICT: BLOCKED\nF1 [P1] scripts/unit.py:1 a real defect."
    record, reply = run_record(reply=reply)
    forged = cf.CapabilityFailure(
        "review-blocked", STARTED, "nonce-one", EARLIER, record["result_sha256"], "test-execution",
        "gpt-6.1-sol", "openai", "claude-cto",
    )
    with pytest.raises(LineageRefused, match=r"evidence refused: CAPABILITY_FAILURE_REFUSED\[findings\]"):
        lineage(approve, ReviewRun("review-blocked", record, reply), comments=[verdict, event_comment(forged)])


@pytest.mark.parametrize(
    "change,match",
    [
        ({"result_sha256": UNIT_DIGEST}, r"conflicts with its task record"),
        ({"sha": OTHER}, r"conflicts with its task record"),
        ({"run": "nonce-two"}, r"conflicts with its task record"),
        ({"model": "gpt-6-luna"}, r"conflicts with its task record"),
        ({"capability": "shell"}, r"does not declare shell"),
        ({"authority": "someone-else"}, r"\[authority\]"),
    ],
)
def test_an_event_its_run_does_not_re_derive_refuses(change, match):
    approve, verdict = approving_run()
    blocked, failure = blocked_run()
    with pytest.raises(LineageRefused, match=match):
        lineage(approve, blocked, comments=[verdict, event_comment(replace(failure, **change))])


def test_conflicting_or_orphaned_publications_refuse():
    approve, verdict = approving_run()
    blocked, failure = blocked_run()
    other = replace(failure, capability="shell")
    with pytest.raises(LineageRefused, match="conflicting capability-failure events"):
        lineage(approve, blocked, comments=[verdict, event_comment(failure), event_comment(other)])
    published = recorded_verdict(EARLIER, "BLOCKED", task_id="review-blocked")
    published["body"] = published["body"].replace("started=2026-09-23T11:00:00.000001+00:00", f"started={STARTED}")
    with pytest.raises(LineageRefused, match="both a published verdict and a capability failure"):
        lineage(approve, blocked, comments=[verdict, published, event_comment(failure)])
    with pytest.raises(LineageRefused, match="capability failure of task review-blocked has no finished review run"):
        lineage(approve, comments=[verdict, event_comment(failure)])
    unfinished = ReviewRun("review-blocked", {**blocked.record, "status": "failed"}, "The run stopped early.")
    with pytest.raises(LineageRefused, match="has no finished review run"):
        lineage(approve, unfinished, comments=[verdict, event_comment(failure)])


def test_damaged_or_untrusted_events_never_classify():
    approve, verdict = approving_run()
    blocked, failure = blocked_run()
    with pytest.raises(LineageRefused, match=r"event in comment 900 was edited"):
        lineage(approve, blocked, comments=[verdict, event_comment(failure, edited=True)])
    altered = cf.build_comment(failure).replace("Missing capability: test-execution", "Missing capability: none")
    with pytest.raises(LineageRefused, match="was altered"):
        lineage(approve, blocked, comments=[verdict, event_comment(failure, body=altered)])
    with pytest.raises(LineageRefused, match="unreadable capability-failure event"):
        lineage(approve, blocked, comments=[verdict, event_comment(failure, body=f"{cf.EVENT_PREFIX} v1 sha=x -->")])
    # Another login's event is not an event: the run stays unpublished.
    with pytest.raises(LineageRefused, match="verdict is unpublished"):
        lineage(approve, blocked, comments=[verdict, event_comment(failure, login="someone")])
    # A reviewer quoting the prefix mid-reply is not an event.
    quoted = recorded_verdict(SHA, "APPROVED", task_id="review-approve")
    quoted["body"] = quoted["body"].replace("VERDICT: APPROVED\n\n", f"VERDICT: APPROVED\n\n{cf.EVENT_PREFIX} quoted\n\n", 1)
    assert cf.events([quoted], "fleet") == []


def test_the_round_being_recorded_drops_its_own_events():
    approve, verdict = approving_run()
    blocked, failure = blocked_run(sha=OTHER)
    blocked.record["pinned_head"] = OTHER
    assert lineage(approve, blocked, comments=[verdict, event_comment(failure)], exclude_head=OTHER) == ["anthropic"]


# 3. Round counting, approval validity and rejection handling read only verdicts.


def test_a_capability_failure_opens_no_round():
    _, failure = blocked_run()
    comments = [recorded_verdict(SHA, "CHANGES_REQUESTED", task_id="r1"), event_comment(failure)]
    assert recorder._trusted_verdict_shas(comments, "fleet") == {SHA}
    assert recorder.require_review_round_within_budget(comments, OTHER, "fleet", budget=2, pr=42) == {}


def test_a_capability_failure_neither_approves_nor_rejects_its_head():
    _, failure = blocked_run(sha=SHA)
    alone = [event_comment(failure)]
    assert sweep.lookup_verdict(alone, SHA, "fleet").state == "needs-CF"
    approved = [recorded_verdict(SHA, "APPROVED", task_id="review-approve"), event_comment(failure)]
    assert sweep.lookup_verdict(approved, SHA, "fleet").state == "APPROVED"
    # A same-head APPROVE after a capability failure is no approval after a rejection.
    recorder.require_no_same_head_rejection(alone, SHA, "fleet", "APPROVED")


def test_the_recorder_refuses_a_verdict_for_a_classified_run(monkeypatch, tmp_path, opsec_rules):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    failure = cf.CapabilityFailure(
        "review-one", "2026-09-23T12:00:00.000001+00:00", "nonce-one", SHA, UNIT_DIGEST, "test-execution",
        "gpt-6.1-sol", "openai", "claude-cto",
    )
    comments.append(event_comment(failure))
    with pytest.raises(cf.CapabilityFailureRefused, match="recorded as a capability failure; it has no verdict"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert calls == {"posts": 0, "statuses": 0}


# 4. The recording verb.


def verb_case(monkeypatch, tmp_path, *, reply=None, **updates):
    """A finished BLOCKED run at an earlier head of PR #42, whose head has since moved to ``SHA``."""
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    record, reply = run_record(reply=reply, **updates)
    (tasks / "review-blocked.json").write_text(json.dumps(record))
    (tasks / "review-blocked.result").write_text(reply)
    return tasks, comments, calls


def record_failure(tasks, tmp_path, **kwargs):
    arguments = {"pr_number": 42, "capability": "test-execution", "authority": "claude-cto", **kwargs}
    return cf.record_capability_failure("review-blocked", task_root=tasks, lock_root=tmp_path / "locks", **arguments)


def test_the_verb_appends_one_event_and_is_idempotent(monkeypatch, tmp_path, opsec_rules):
    tasks, comments, calls = verb_case(monkeypatch, tmp_path)
    before = {suffix: (tasks / f"review-blocked.{suffix}").read_bytes() for suffix in ("json", "result")}
    receipt = record_failure(tasks, tmp_path)
    assert receipt["comment"] == "posted" and receipt["sha"] == EARLIER and receipt["capability"] == "test-execution"
    assert calls == {"posts": 1, "statuses": 0}
    [event] = cf.events(comments, "fleet")
    assert event.task == "review-blocked" and event.result_sha256 == receipt["result_sha256"]
    assert record_failure(tasks, tmp_path)["comment"] == "existing" and calls["posts"] == 1
    # The run's record and reply are never edited.
    assert before == {suffix: (tasks / f"review-blocked.{suffix}").read_bytes() for suffix in ("json", "result")}


def test_the_verb_refuses_an_ineligible_run_before_any_post(monkeypatch, tmp_path, opsec_rules):
    tasks, comments, calls = verb_case(monkeypatch, tmp_path, reply="VERDICT: BLOCKED - sandbox prevents pytest.")
    with pytest.raises(cf.CapabilityFailureRefused, match=r"\[findings\]"):
        record_failure(tasks, tmp_path)
    tasks, comments, calls = verb_case(monkeypatch, tmp_path / "two")
    (tasks / "review-blocked.result").write_text(structured(missing=("shell",)))
    with pytest.raises(recorder.RecordError, match="terminal_result_digest_mismatch"):
        record_failure(tasks, tmp_path)
    assert comments == [] and calls["posts"] == 0


def test_the_verb_never_replaces_a_published_verdict_or_another_event(monkeypatch, tmp_path, opsec_rules):
    tasks, comments, calls = verb_case(monkeypatch, tmp_path)
    published = recorded_verdict(EARLIER, "BLOCKED", task_id="review-blocked")
    published["body"] = published["body"].replace("started=2026-09-23T11:00:00.000001+00:00", f"started={STARTED}")
    comments.append(published)
    with pytest.raises(cf.CapabilityFailureRefused, match="already has a published verdict"):
        record_failure(tasks, tmp_path)
    comments.clear()
    record, reply = run_record(reply=structured(missing=("shell", "test-execution")))
    (tasks / "review-blocked.json").write_text(json.dumps(record))
    (tasks / "review-blocked.result").write_text(reply)
    record_failure(tasks, tmp_path, capability="shell")
    with pytest.raises(cf.CapabilityFailureRefused, match="already has a different capability-failure event"):
        record_failure(tasks, tmp_path)
    assert calls["posts"] == 1


def test_the_verb_is_reachable_from_the_recorder_cli(monkeypatch, tmp_path, opsec_rules, capsys):
    tasks, comments, _calls = verb_case(monkeypatch, tmp_path)
    monkeypatch.setattr(cf.recorder, "_repo_root", lambda: tmp_path)
    (tmp_path / "batch_state").mkdir()
    tasks.rename(tmp_path / "batch_state" / "tasks")
    argv = ["capability-failure", "--task-id", "review-blocked", "--pr", "42", "--capability", "test-execution"]
    assert recorder.main([*argv, "--authority", "claude-cto"]) == 0
    assert json.loads(capsys.readouterr().out)["comment"] == "posted" and len(comments) == 1
    assert recorder.main([*argv, "--authority", "operator"]) == 1
    assert "CAPABILITY_FAILURE_REFUSED[authority]" in capsys.readouterr().out
