"""Runtime Sources-call gate for Ukrainian verdict publication (#10074)."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import pytest

from scripts.orchestration import integration_sweep as sweep
from scripts.orchestration import merge_queue_keeper as keeper
from scripts.review import record_cf_verdict as recorder
from scripts.review.ukrainian_seats import (
    UKRAINIAN_SEAT_FAMILIES,
    attested_author_families,
    required_ukrainian_seats,
)
from tests.test_record_cf_verdict import SHA, setup_record, write_task


def captured_source_trace(tasks, *, task_id="review-one", tool="verify_word", arguments=None, output="VESUM"):
    """A provider's completed Sources event, separate from the reviewer's reply."""
    path = tasks / "logs" / f"{task_id}.stdout.log"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({"event": "step_update", "step_update": {
        "state": "DONE", "step_index": 4, "step_type": "tool", "tool_name": "call_mcp_tool",
        "tool_info": {"name": "call_mcp_tool", "parameters": {
            "ServerName": "sources", "ToolName": tool, "Arguments": arguments or {"word": "example"},
        }, **({"output": output} if output is not None else {})},
    }}) + "\n")



@pytest.mark.parametrize("marker", ["trial_label", "trial_role", "trial_qualified_task"])
def test_trial_never_becomes_review_of_record(tmp_path, monkeypatch, marker):
    from scripts.review.review_lineage import review_records

    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    write_task(tasks, **{marker: "trial"})
    with pytest.raises(recorder.RecordError, match="MODEL_ROLE_TRIAL_REFUSED"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == [] and calls["posts"] == 0
    task = json.loads((tasks / "review-one.json").read_text())
    with pytest.raises(recorder.RecordError, match="MODEL_ROLE_TRIAL_REFUSED"):
        recorder.reviewer_identity(task)
    assert review_records(tasks, repository="owner/repo") == []


@pytest.fixture
def scanned_recorder(monkeypatch, tmp_path):
    """Exercise the supported publisher; fake only GitHub reads and transport."""
    from scripts.opsec import prepublish as gate
    from scripts.publish import github
    from tests.test_opsec_prepublish import real_tooling

    tooling = real_tooling()
    monkeypatch.setattr(gate, "private_tooling", lambda: tooling)
    real_json = recorder._run_json
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    bookkeeping = recorder._run_json
    sent = []

    def route(args, **kwargs):
        if isinstance(args, github.Request) and args.verb == "issue-comment-json":
            return real_json(args, **kwargs)
        return bookkeeping(args, **kwargs)

    def transport(argv, **kwargs):
        body = json.loads(Path(argv[argv.index("--input") + 1]).read_text())["body"]
        sent.append(body)
        posted = bookkeeping(github.Request("issue-comment-json", repo="owner/repo", number=42, body=body))
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(posted), stderr="")

    monkeypatch.setattr(recorder, "_run_json", route)
    monkeypatch.setattr(github, "_send", transport)
    return tasks, comments, calls, sent, tooling


@pytest.mark.parametrize("detail,rule", [
    ("2001:db8::42 SYNTHETIC-DETAIL", "2-ipv6"),
    ("credential stored SYNTHETIC-DETAIL", "5-credential-context"),
])
@pytest.mark.parametrize("verdict", ["APPROVED", "CHANGES_REQUESTED", "BLOCKED"])
def test_real_refusal_publishes_only_skeleton(scanned_recorder, tmp_path, detail, rule, verdict):
    from scripts.opsec import prepublish as gate

    tasks, comments, calls, sent, tooling = scanned_recorder
    reply = f"VERDICT: {verdict}\n{detail}\nHarmless reviewer sentence quoting `<!-- cf-verdict`.\n- A prose bullet."
    write_task(tasks, reply=reply)
    before = {suffix: (tasks / f"review-one.{suffix}").read_bytes() for suffix in ("json", "result")}
    with pytest.raises(gate.PublishBlocked, match=f"rule={rule}"):
        gate.check_texts("github.com/owner/repo", [reply], tooling=tooling, environment={})
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    body = comments[0]["body"]
    assert body == (
        f"### Cross-family review\nhead: {SHA}\nReviewer family: openai\nVERDICT: {verdict}\n"
        "Reviewer model: gpt-6.1-sol\nReview score: absent\nAuthored by: gemini-3.8-flash-high\n"
        "Task id: review-one\n\nWithheld findings: unknown\n"
        "Findings are held privately.\n\n"
        f"<!-- cf-verdict v1 sha={SHA} task=review-one started=2026-09-23T12:00:00.000001+00:00 "
        f"verdict={verdict} model=gpt-6.1-sol family=openai -->"
    )
    assert sent == [body]
    assert detail not in body and "SYNTHETIC-DETAIL" not in body
    assert "Harmless reviewer sentence" not in body and "&lt;!-- cf-verdict" not in body
    assert body.count(recorder.MARKER_PREFIX) == 1
    gate.check_texts("github.com/owner/repo", [body], tooling=tooling, environment={})
    assert result["verdict"] == verdict
    assert sweep.parse_marker(body)["sha"] == SHA
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == verdict
    assert keeper._recorded_approval_for_head(comments, SHA, "fleet") == (verdict == "APPROVED")
    assert not keeper._recorded_approval_for_head(comments, "b" * 40, "fleet")
    second = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert second["comment"] == "existing" and sent == [body]
    assert calls == {"posts": 1, "statuses": 2}
    assert before == {suffix: (tasks / f"review-one.{suffix}").read_bytes() for suffix in before}


def test_clean_publication_bytes_unchanged(scanned_recorder, tmp_path):
    tasks, comments, calls, sent, _ = scanned_recorder
    reply = "VERDICT: APPROVE\nSCORE: 8/10 one P3 nit.\nOrdinary reviewer text.\n\n  Preserve spacing.\n"
    write_task(tasks, reply=reply)
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    expected = (
        f"### Cross-family review\nhead: {SHA}\nReviewer family: openai\nVERDICT: APPROVED\n"
        "Reviewer model: gpt-6.1-sol\nReview score: 8/10\nAuthored by: gemini-3.8-flash-high\n"
        "Task id: review-one\n\n"
        "<details><summary>Reviewer's reply</summary>\n\n"
        + reply + "\n\n</details>\n\n"
        f"<!-- cf-verdict v1 sha={SHA} task=review-one started=2026-09-23T12:00:00.000001+00:00 "
        "verdict=APPROVED model=gpt-6.1-sol family=openai -->"
    )
    assert comments[0]["body"].encode() == expected.encode()
    assert sent == [expected] and calls == {"posts": 1, "statuses": 1}
    # The advisory score (C-3020) never changes the recorded verdict.
    assert result["score"] == 8 and sweep.parse_marker(expected)["verdict"] == "APPROVED"


def test_skeleton_scanner_rejection_has_no_write(scanned_recorder, tmp_path, monkeypatch, synthetic_opsec):
    from scripts.opsec import prepublish as gate
    from tests.opsec_fixtures import synthetic_rules

    tasks, comments, calls, sent, _ = scanned_recorder
    rules = synthetic_rules(rule="5-credential-context", level=5, pattern="credential stored")
    rules["1"] = {"patterns": [{"id": "synthetic-skeleton-refusal", "regex": "Findings are held privately"}]}
    rules["3"] = {"patterns": [{"id": "3-absolute-path", "regex": r"(?!)"}]}
    (synthetic_opsec / "rules.json").write_text(json.dumps(rules))
    monkeypatch.setattr(gate, "private_tooling", lambda: synthetic_opsec)
    write_task(tasks, reply="VERDICT: APPROVE\ncredential stored SYNTHETIC-DETAIL")
    with pytest.raises(recorder.RecordError, match="synthetic-skeleton-refusal"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == sent == [] and calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("failure", ["scanner_unavailable", "lookup_failed"])
def test_unrelated_failure_never_uses_skeleton(scanned_recorder, tmp_path, monkeypatch, failure):
    from scripts.opsec import prepublish as gate

    tasks, comments, calls, sent, _ = scanned_recorder
    scans = []

    def refuse(destination, texts, **kwargs):
        scans.extend(texts)
        if failure == "scanner_unavailable":
            raise gate.PublishBlocked("OPSEC: checker unavailable; write refused.")
        raise recorder.RecordError("GitHub lookup or publication unavailable")

    monkeypatch.setattr(recorder, "check_texts", refuse)
    with pytest.raises(recorder.RecordError, match="unavailable"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert len(scans) == 1 and "Withheld findings:" not in scans[0]
    assert comments == sent == [] and calls == {"posts": 0, "statuses": 0}


def structured_review(count):
    return {
        "schema_version": "code-review-findings.v1",
        "overall": {
            "correctness": "incorrect" if count else "correct",
            "explanation": "credential stored SYNTHETIC-DETAIL",
            "confidence": 0.9,
        },
        "findings": [{
            "id": f"F{number}", "title": "Synthetic finding", "body": "Synthetic finding body.",
            "priority": "P2", "confidence": 0.9, "category": "correctness",
            "location": {"path": "scripts/example.py", "start_line": number, "end_line": number,
                         "claim_type": "present"},
            "verbatim": "value = shared_state", "why_wrong": "The state is not reset.",
            "smallest_fix": "Rebuild the state for every call.", "sources": ["none"],
        } for number in range(1, count + 1)],
    }


@pytest.mark.parametrize("count", [0, 1, 3])
def test_validated_structured_count_in_skeleton(scanned_recorder, tmp_path, count):
    tasks, comments, calls, sent, _ = scanned_recorder
    reply = json.dumps(structured_review(count))
    write_task(tasks, reply=reply)
    before = (tasks / "review-one.result").read_bytes()
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    expected = "CHANGES_REQUESTED" if count else "APPROVED"
    assert result["verdict"] == sweep.lookup_verdict(comments, SHA, "fleet").state == expected
    assert f"Withheld findings: {count}\n" in comments[0]["body"]
    assert "SYNTHETIC-DETAIL" not in comments[0]["body"]
    assert "Synthetic finding" not in comments[0]["body"]
    assert (tasks / "review-one.result").read_bytes() == before
    assert sent == [comments[0]["body"]] and calls == {"posts": 1, "statuses": 1}


def test_approve_reply_with_one_p3_finding_records_approve_with_score(scanned_recorder, tmp_path):
    """A P3 finding is a follow-up, so the reply's APPROVE and its score are recorded (#12022)."""
    tasks, comments, _, sent, _ = scanned_recorder
    payload = structured_review(1)
    payload["overall"].update(
        correctness="correct", explanation="VERDICT: APPROVE. SCORE: 9/10.\n\nOne non-blocking P3 follow-up."
    )
    payload["findings"][0]["priority"] = "P3"
    write_task(tasks, reply=json.dumps(payload))
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    body = comments[0]["body"]
    assert sent == [body]
    assert result["verdict"] == sweep.lookup_verdict(comments, SHA, "fleet").state == "APPROVED"
    assert result["score"] == 9 and "VERDICT: APPROVED\n" in body and "Review score: 9/10\n" in body


@pytest.mark.parametrize(("deep", "reason"), [
    (False, "contradicting a verdict line"),
    (True, "invalid findings block beside a verdict line: top-level blocks cannot be decided"),
], ids=["request-changes-envelope", "unterminated-deep-array-before-invalid-envelope"])
def test_approve_line_beside_top_level_request_changes_envelope_is_refused(deep, reason):
    """An outer APPROVE never outranks a top-level findings block that requests changes, or one that cannot be read (#12040)."""
    payload = structured_review(1)
    payload["findings"][0]["priority"] = "P1"
    block = "[" * 11000 + '0\n\n{"findings":"bad"}' if deep else json.dumps(payload, indent=2)
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.normalize_verdict("VERDICT: APPROVE\n\n" + block)


@pytest.mark.parametrize("update", [
    {"findings": "not a list"}, {"findings": [None]}, {"verdict": "APPROVED"},
    {"verdict": "INVALID"}, {"overall": {}},
    {"overall": {"correctness": "correct", "explanation": "", "confidence": 0.9}, "findings": []},
])
def test_invalid_structured_verdict_or_count_refuses(scanned_recorder, tmp_path, update):
    tasks, comments, calls, sent, _ = scanned_recorder
    payload = structured_review(1)
    payload.update(update)
    write_task(tasks, reply=json.dumps(payload))
    with pytest.raises(recorder.RecordError, match="structured review verdict or findings invalid"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == sent == [] and calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("beside_verdict_line", [True, False], ids=["verdict-line-and-block", "whole-json"])
def test_finding_with_extra_status_field_is_refused_naming_it(beside_verdict_line):
    """The recorder refuses a reply the closeout verifier would reject, naming the field (#12080)."""
    payload = structured_review(1)
    payload["overall"]["correctness"] = "correct"
    payload["findings"][0].update(priority="P3", status="open")
    block = json.dumps(payload, indent=2)
    reply = f"VERDICT: APPROVE\n\n```json\n{block}\n```\n" if beside_verdict_line else block
    with pytest.raises(recorder.RecordError, match=r"schema_violation:findings\.0:.*'status' was unexpected.*allowed"):
        recorder._review_verdict_and_count(reply)


def test_correct_reply_declaring_missing_capabilities_is_refused():
    """A reviewer that reports missing capabilities cannot approve (#12084)."""
    payload = structured_review(0)
    payload["overall"]["correctness"] = "correct"
    payload["missing_capabilities"] = ["test-execution"]
    with pytest.raises(recorder.RecordError, match=r"'missing_capabilities' was unexpected"):
        recorder._review_verdict_and_count(json.dumps(payload))


@pytest.mark.parametrize("payload,expected", [
    ("VERDICT: APPROVE\n- prose item\n- another prose item", "APPROVED"),
])
def test_unavailable_structured_count_is_unknown(payload, expected):
    reply = json.dumps(payload) if isinstance(payload, dict) else payload
    assert recorder._review_verdict_and_count(reply) == (expected, "unknown")


@pytest.mark.parametrize("metadata", [
    {"review_mode": "red_team", "unknown_history": ["b" * 40]},
    {"review_profile": "ukrainian", "sources_mcp_call_count": 3},
])
def test_skeleton_preserves_complete_marker_metadata(metadata):
    body = recorder.build_comment(
        sha=SHA, task_id="review-one", started="2026-09-23T12:00:00.000001+00:00",
        verdict="APPROVED", model="gpt-6.1-sol", family="openai", reply="",
        withheld_findings=2, **metadata,
    )
    marker = sweep.parse_marker(body)
    assert marker["sha"] == SHA and marker["verdict"] == "APPROVED"
    for name, value in metadata.items():
        assert marker["sources_calls" if name == "sources_mcp_call_count" else name] == value


def test_transport_failure_after_scan_never_retries_skeleton(scanned_recorder, tmp_path, monkeypatch):
    from scripts.publish import github

    tasks, comments, calls, sent, _ = scanned_recorder
    attempts = []

    def fail(argv, **kwargs):
        attempts.append(argv)
        raise OSError("synthetic transport failure")

    monkeypatch.setattr(github, "_send", fail)
    with pytest.raises(recorder.RecordError, match="publication unavailable"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert len(attempts) == 1
    assert comments == sent == [] and calls == {"posts": 0, "statuses": 0}


def test_head_movement_before_skeleton_write_refuses(scanned_recorder, tmp_path, monkeypatch):
    tasks, comments, calls, sent, _ = scanned_recorder
    write_task(tasks, reply="VERDICT: APPROVE\ncredential stored SYNTHETIC-DETAIL")
    heads = iter([SHA, "b" * 40])
    monkeypatch.setattr(recorder, "_pr", lambda *args: {
        "number": 42, "headRefName": "codex/42", "headRefOid": next(heads),
    })
    with pytest.raises(recorder.RecordError, match="PR head moved before publication"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == sent == [] and calls == {"posts": 0, "statuses": 0}


def test_edited_skeleton_cannot_reconcile(scanned_recorder, tmp_path):
    tasks, comments, calls, sent, _ = scanned_recorder
    write_task(tasks, reply="VERDICT: APPROVE\ncredential stored SYNTHETIC-DETAIL")
    recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    comments[0]["updated_at"] = "2026-09-23T14:00:00Z"
    with pytest.raises(recorder.RecordError, match="existing verdict marker was edited or conflicts"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert sent == [comments[0]["body"]] and calls == {"posts": 1, "statuses": 1}


@pytest.mark.parametrize("identity", [
    {"schema_version": 2, "worktree_branch": "claude/private-review", "review_branch": "codex/42", "pinned_head": SHA},
    {"worktree_branch": None, "review_branch": "codex/42", "pinned_head": SHA},
    {},  # Legacy attached record has no review_branch field.
    {"review_branch": "codex/42"},
    {"review_branch": "  codex/42  "},
])
def test_branch_identity_binds_supported_record(monkeypatch, tmp_path, identity):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    write_task(tasks, **identity)
    before = (tasks / "review-one.json").read_bytes()
    receipt = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert receipt["head"] == SHA
    assert receipt["verdict"] == "APPROVED"
    assert receipt["status"] == "posted"
    assert recorder.parse_marker(comments[0]["body"])["sha"] == SHA
    assert calls == {"posts": 1, "statuses": 1}
    assert (tasks / "review-one.json").read_bytes() == before


@pytest.mark.parametrize("identity,reason", [
    ({"schema_version": 2}, "not branch-pinned"),
    ({"schema_version": 2, "review_branch": None}, "not branch-pinned"),
    ({"worktree_branch": None}, "not branch-pinned"),
    ({"review_branch": "other/branch"}, "conflicting"),
    ({"worktree_branch": None, "review_branch": ""}, "invalid"),
    ({"worktree_branch": None, "review_branch": 42}, "invalid"),
    ({"worktree_branch": 42, "review_branch": "codex/42"}, "invalid"),
    *[({"worktree_branch": None, "review_branch": branch}, "invalid")
      for branch in ("unsafe..branch", "origin/codex/42", "refs/heads/codex/42", "bad:name")],
    *[({"worktree_branch": None, "review_branch": branch}, "protected") for branch in ("main", "master")],
])
def test_bad_branch_identity_refuses_before_network(monkeypatch, tmp_path, identity, reason):
    tasks = tmp_path / "tasks"
    write_task(tasks, **identity)

    def unexpected_network(*args, **kwargs):
        pytest.fail("invalid identity must refuse before network")

    monkeypatch.setattr(recorder, "_run_json", unexpected_network)
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", task_root=tasks, lock_root=tmp_path / "locks")


@pytest.mark.parametrize("pr,reason", [
    ({"branch": "other/branch"}, "branch does not match"),
    ({"head": "b" * 40}, "head moved"),
])
@pytest.mark.parametrize("checkout", [
    {"worktree_branch": None},
    {"schema_version": 2, "worktree_branch": "claude/private-review"},
])
def test_detached_review_refuses_wrong_pr_identity(monkeypatch, tmp_path, pr, reason, checkout):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path, **pr)
    write_task(tasks, review_branch="codex/42", **checkout)
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert not comments
    assert calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("updates,families,reason", [
    ({"status": "running"}, {"google"}, "not done"),
    ({"worktree_base_sha": None}, {"google"}, "reviewed SHA"),
    ({"pinned_head": "b" * 40}, {"google"}, "conflicts with pinned head"),
    ({"pinned_head": "a" * 7}, {"google"}, "conflicts with pinned head"),
    ({"agent": "grok", "model": "grok-4.7"}, {"google"}, "unattested"),
    ({"review_risk": "critical", "model": "claude-sonnet-5-5", "agent": "claude"},
     {"google"}, "not qualified"),
    ({}, {"openai"}, "equals an author family"),
])
def test_detached_identity_preserves_specific_review_refusals(monkeypatch, tmp_path, updates, families, reason):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path, families=families)
    write_task(tasks, worktree_branch=None, review_branch="codex/42", **updates)
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert not comments
    assert calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("risk", ["low", "medium"])
@pytest.mark.parametrize("profile", ["code", "ukrainian"])
def test_gemini_verdict_records_and_gate_accepts_exact_head(monkeypatch, tmp_path, risk, profile):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path, families={"openai"})
    write_task(tasks, agent="agy", model="gemini-3.8-flash-high", review_profile=profile,
               review_risk=risk, sources_mcp_call_count=3 if profile == "ukrainian" else None)
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert result["verdict"] == "APPROVED"
    marker = recorder.parse_marker(comments[0]["body"])
    assert marker["family"] == "google"
    assert marker["sha"] == SHA
    # An OpenAI author needs only this Gemini seat, on either profile.
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == "APPROVED"
    assert keeper._recorded_approval_for_head(comments, SHA, "fleet")
    assert not keeper._recorded_approval_for_head(comments, "b" * 40, "fleet")
    assert calls == {"posts": 1, "statuses": 1}


@pytest.mark.parametrize("risk,path", [("high", "ordinary.py"), ("critical", "ordinary.py"),
                                      ("low", "scripts/review/reviewer_resolver.py"),
                                      ("medium", ".github/workflows/ci.yml")])
def test_gemini_code_verdict_refused_before_publication(monkeypatch, tmp_path, risk, path):
    from tests.test_record_cf_verdict import facts_for

    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    monkeypatch.setattr(recorder, "pr_review_facts", lambda *_args, **_kwargs: facts_for({"anthropic"}, changed_paths=(path,)))
    write_task(tasks, agent="agy", model="gemini-3.8-flash-high", review_profile="code", review_risk=risk)
    with pytest.raises(recorder.RecordError, match="Gemini code review requires AGY at low/medium risk"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert not comments
    assert calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("head", ["a" * 7, "b" * 40])
def test_gemini_stale_or_short_head_refused(monkeypatch, tmp_path, head):
    tasks, _, calls = setup_record(monkeypatch, tmp_path, head=head)
    write_task(tasks, agent="agy", model="gemini-3.8-flash-high", review_risk="low")
    with pytest.raises(recorder.RecordError):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("sha", ["a" * 7, "a" * 39, "z" * 40])
def test_gemini_marker_requires_full_commit_sha(sha):
    with pytest.raises(recorder.RecordError, match="full 40-hex"):
        recorder.build_comment(sha=sha, task_id="gemini-review", started="2026-10-09T00:00:00Z",
                               verdict="APPROVED", model="gemini-3.8-flash-high", family="google", reply="VERDICT: APPROVE")


@pytest.fixture(autouse=True)
def recorder_matcher(synthetic_opsec):
    from tests.opsec_fixtures import synthetic_rules

    rules = synthetic_rules(rule="3-absolute-path", level=3, pattern=r"(?<![<\w:])/[A-Za-z][^\s`'\"<>),;\]}|*]*")
    (synthetic_opsec / "rules.json").write_text(json.dumps(rules))


@pytest.mark.parametrize("count", [1, 3])
@pytest.mark.parametrize(
    "classification",
    [
        {"review_profile": "ukrainian"},
        {"review_profile": " Ukrainian "},
        {"review_language_lane": True},
        {"language_lane": True},
        {"research_task_family": "ukrainian-review"},
        {"task_family": "ukrainian-authoring"},
    ],
)
def test_ukrainian_review_with_sources_calls_accepted(monkeypatch, tmp_path, count, classification):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    statuses = []
    original_status = recorder.post_commit_status

    def capture_status(**kwargs):
        statuses.append(kwargs)
        original_status(**kwargs)

    monkeypatch.setattr(recorder, "post_commit_status", capture_status)
    write_task(tasks, sources_mcp_call_count=count, **classification)
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert result["verdict"] == "APPROVED"
    assert result["status"] == "posted"
    assert len(comments) == 1
    assert calls == {"posts": 1, "statuses": 1}
    assert f"Sources MCP calls: {count}\n" in comments[0]["body"].split("<details>", 1)[0]
    assert f"sources_calls={count}" in comments[0]["body"].splitlines()[-1]
    marker = recorder.parse_marker(comments[0]["body"])
    assert marker["sources_calls"] == count
    assert marker["review_profile"] == "ukrainian"
    assert f"sources={count}" in statuses[0]["description"]
    # A Google author needs only this Sol seat, and the keeper can still revoke that approval.
    assert statuses[0]["state"] == "success"
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == "APPROVED"
    assert keeper._recorded_approval_for_head(comments, SHA, "fleet")
    recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert calls == {"posts": 1, "statuses": 2}


def record_seat(tasks, tmp_path, task_id, **seat):
    """Record one Ukrainian-profile review of SHA through the recorder."""
    write_task(tasks, task_id=task_id, review_profile="ukrainian", sources_mcp_call_count=3, **seat)
    recorder.record(task_id, pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")


def merge(monkeypatch, comments):
    """Run ``pr-merge`` on SHA with every check passing; only the recorded seats can refuse it."""
    from scripts.opsec import prepublish as gate
    from scripts.publish import github as pub
    from tests.opsec_fixtures import CATALOG

    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    monkeypatch.delenv("AGENT_NO_MERGE", raising=False)
    writes = []

    def spy(args, **kwargs):
        if args[1:3] == ["pr", "view"]:
            body = {"number": 42, "isDraft": False, "headRefOid": SHA}
        elif args[1:3] == ["pr", "checks"]:
            body = []
        elif args[1:5] == ["api", "--method", "POST", "graphql"]:
            body = {"data": {"repository": {"pullRequest": {
                "headRefOid": SHA, "isMergeQueueEnabled": False,
                "viewerMergeHeadlineText": "clean (#42)", "viewerMergeBodyText": "clean"}}}}
        elif args[1:4] == ["api", "--method", "GET"]:
            if "/issues/42/comments" in args[4]:
                body = [comments]
            elif "/pulls/42/files" in args[4]:
                body = [[{"filename": "scripts/example.py"}]]
            else:
                body = {"login": "fleet"}
        else:
            writes.append(args)
            return subprocess.CompletedProcess(args, 0, "", "")
        return subprocess.CompletedProcess(args, 0, json.dumps(body), "")

    pub.publish("pr-merge", repo="unit/public", number=42, runner=spy, env={})
    return writes


def test_one_ukrainian_seat_leaves_the_status_pending_and_the_merge_refused(monkeypatch, tmp_path):
    # An author outside OpenAI and Google still needs both Gemini and Sol.
    from scripts.opsec import prepublish as gate

    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"anthropic"})
    statuses = []
    monkeypatch.setattr(recorder, "post_commit_status", lambda **kwargs: statuses.append(kwargs))
    record_seat(tasks, tmp_path, "review-one", agent="agy", model="gemini-3.8-flash-high")
    assert statuses[-1]["state"] == "pending"
    assert statuses[-1]["description"].endswith("; awaiting Ukrainian seat: openai")
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == sweep.NEEDS_SEAT
    with pytest.raises(gate.PublishBlocked, match="Ukrainian review seat has not approved"):
        merge(monkeypatch, comments)


def test_two_eligible_ukrainian_seats_at_the_same_head_pass(monkeypatch, tmp_path):
    # An author outside OpenAI and Google is approved once Gemini and Sol have both approved.
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"anthropic"})
    statuses = []
    monkeypatch.setattr(recorder, "post_commit_status", lambda **kwargs: statuses.append(kwargs))
    record_seat(tasks, tmp_path, "review-one", agent="agy", model="gemini-3.8-flash-high")
    record_seat(tasks, tmp_path, "review-two", started_at="2026-09-23T12:00:01.000001+00:00")
    assert [status["state"] for status in statuses] == ["pending", "success"]
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == "APPROVED"
    assert len(merge(monkeypatch, comments)) == 1


def test_a_ukrainian_seat_approving_an_older_head_does_not_count(monkeypatch, tmp_path):
    # Seats count only when they approved the head that would land.
    from scripts.opsec import prepublish as gate
    from tests.test_record_cf_verdict import OTHER

    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"anthropic"})
    statuses = []
    monkeypatch.setattr(recorder, "post_commit_status", lambda **kwargs: statuses.append(kwargs))
    older = recorder.build_comment(
        sha=OTHER, task_id="review-old", started="2026-09-23T11:00:00.000001+00:00", verdict="APPROVED",
        model="gpt-6.1-sol", family="openai", reply="VERDICT: APPROVE",
        review_profile="ukrainian", sources_mcp_call_count=3,
        author_models=("gemini-3.8-flash-high",),
    )
    stamp = "2026-09-23T12:30:00Z"
    comments.append({"id": 0, "body": older, "user": {"login": "fleet"}, "author_association": "MEMBER",
                     "created_at": stamp, "updated_at": stamp})
    record_seat(tasks, tmp_path, "review-one", agent="agy", model="gemini-3.8-flash-high")
    assert statuses[-1]["state"] == "pending"
    assert statuses[-1]["description"].endswith("; awaiting Ukrainian seat: openai")
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == sweep.NEEDS_SEAT
    with pytest.raises(gate.PublishBlocked, match="Ukrainian review seat has not approved"):
        merge(monkeypatch, comments)


def test_sol_authored_gemini_approval_passes_and_gemini_author_needs_sol(monkeypatch, tmp_path):
    """A Sol-authored Ukrainian head with one Gemini APPROVE passes; a Gemini-authored one needs Sol."""
    from scripts.opsec import prepublish as gate

    sol_root = tmp_path / "sol"
    tasks, comments, _ = setup_record(monkeypatch, sol_root, families={"openai"})
    statuses = []
    monkeypatch.setattr(recorder, "post_commit_status", lambda **kwargs: statuses.append(kwargs))
    record_seat(tasks, sol_root, "review-gemini", agent="agy", model="gemini-3.8-flash-high")
    assert statuses[-1]["state"] == "success"
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == "APPROVED"
    assert len(merge(monkeypatch, comments)) == 1

    gemini_root = tmp_path / "gemini"
    _tasks, comments, _calls = setup_record(monkeypatch, gemini_root, families={"google"})
    body = recorder.build_comment(
        sha=SHA, task_id="review-gemini", started="2026-09-23T12:00:00.000001+00:00",
        verdict="APPROVED", model="gemini-3.8-flash-high", family="google", reply="VERDICT: APPROVE",
        review_profile="ukrainian", sources_mcp_call_count=3,
        author_models=("gemini-3.8-flash-high",),
    )
    stamp = "2026-09-23T13:00:00Z"
    comments.append({
        "id": 1, "body": body, "user": {"login": "fleet"}, "author_association": "MEMBER",
        "created_at": stamp, "updated_at": stamp,
    })
    verdict = sweep.lookup_verdict(comments, SHA, "fleet")
    assert verdict.state == sweep.NEEDS_SEAT
    assert verdict.ukrainian_seats == ("google",)
    with pytest.raises(gate.PublishBlocked, match="Ukrainian review seat has not approved"):
        merge(monkeypatch, comments)


def test_a_blank_author_beside_an_attested_marker_still_needs_both_seats():
    """One missing attestation is not dropped when another marker names an author."""
    known = {"author_models": ("gpt-6.1-sol",)}
    blanks = (
        {},
        {"author_models": None},
        {"author_models": ()},
        {"author_models": []},
        {"author_models": ""},
        {"author_models": {}},
        {"author_models": 0},
        {"author_models": False},
    )
    for blank in blanks:
        assert required_ukrainian_seats(attested_author_families([blank, known])) == UKRAINIAN_SEAT_FAMILIES

    def comment(body, number):
        stamp = "2026-09-23T13:00:00Z"
        return {
            "id": number, "body": body, "user": {"login": "fleet"}, "author_association": "MEMBER",
            "created_at": stamp, "updated_at": stamp,
        }

    bare = recorder.build_comment(
        sha=SHA, task_id="review-bare", started="2026-09-23T12:00:00.000001+00:00",
        verdict="APPROVED", model="gemini-3.8-flash-high", family="google", reply="VERDICT: APPROVE",
        review_profile="ukrainian", sources_mcp_call_count=3,
    )
    named = recorder.build_comment(
        sha=SHA, task_id="review-named", started="2026-09-23T12:00:01.000001+00:00",
        verdict="APPROVED", model="gemini-3.8-flash-high", family="google", reply="VERDICT: APPROVE",
        review_profile="ukrainian", sources_mcp_call_count=3, author_models=("gpt-6.1-sol",),
    )
    alone = sweep.lookup_verdict([comment(bare, 1)], SHA, "fleet")
    assert alone.state == sweep.NEEDS_SEAT
    combined = sweep.lookup_verdict([comment(bare, 1), comment(named, 2)], SHA, "fleet")
    assert combined.state == sweep.NEEDS_SEAT
    assert combined.ukrainian_seats == ("google",)


@pytest.mark.parametrize("alias", [
    {"review_language_lane": True},
    {"language_lane": True},
    {"research_task_family": "ukrainian-review"},
    {"research_task_family": "ukrainian-authoring"},
    {"task_family": "ukrainian-review"},
    {"task_family": "ukrainian-authoring"},
])
def test_a_claude_ukrainian_alias_cannot_record_a_verdict(monkeypatch, tmp_path, alias):
    """A code-profile task that the lane still classifies as Ukrainian needs a seat."""
    tasks, comments, calls = setup_record(monkeypatch, tmp_path, families={"openai"})
    write_task(
        tasks, reply="VERDICT: REQUEST_CHANGES", agent="claude", model="claude-opus-5-5",
        review_profile="code", sources_mcp_call_count=3, **alias,
    )
    with pytest.raises(recorder.RecordError, match="Gemini or Sol"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert not comments
    assert calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("verdict", ["APPROVE", "REQUEST_CHANGES", "BLOCKED"])
@pytest.mark.parametrize("count", [0, None, -1, True, "1", 1.0])
def test_ukrainian_review_without_known_positive_count_refused_before_network(
    monkeypatch, tmp_path, verdict, count
):
    tasks = tmp_path / "tasks"
    write_task(tasks, reply=f"VERDICT: {verdict}", review_profile="ukrainian", sources_mcp_call_count=count)

    def unexpected_network(*args, **kwargs):
        pytest.fail("Sources evidence must be checked before GitHub lookup or publication")

    monkeypatch.setattr(recorder, "_run_json", unexpected_network)
    reason = "zero Sources MCP calls" if count == 0 else "call count unknown"
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", task_root=tasks, lock_root=tmp_path / "locks")


def test_missing_runtime_count_cannot_be_replaced_by_reviewer_prose(tmp_path):
    tasks = tmp_path / "tasks"
    write_task(tasks, review_profile="ukrainian", reply="Used mcp__sources__verify_words.\nVERDICT: APPROVE")
    with pytest.raises(recorder.RecordError, match="call count unknown"):
        recorder.record("review-one", task_root=tasks, lock_root=tmp_path / "locks")


@pytest.mark.parametrize("count", [0, None])
@pytest.mark.parametrize(
    "classification",
    [
        {"review_language_lane": True},
        {"language_lane": True},
        {"research_task_family": "ukrainian-review"},
        {"task_family": "ukrainian-authoring"},
    ],
)
def test_task_classification_cannot_bypass_sources_gate(tmp_path, count, classification):
    tasks = tmp_path / "tasks"
    write_task(tasks, review_profile="code", sources_mcp_call_count=count, **classification)
    with pytest.raises(recorder.RecordError, match="Ukrainian review"):
        recorder.record("review-one", task_root=tasks, lock_root=tmp_path / "locks")


@pytest.mark.parametrize("mode", ["cross_family", "red_team"])
@pytest.mark.parametrize("profile,count", [("code", None), ("code", 0), ("code", 4), ("ukrainian", 4)])
def test_parse_marker_extracts_optional_integer_count(mode, profile, count):
    body = recorder.build_comment(
        sha=SHA, task_id="review-one", started="2026-09-23T12:00:00.000001+00:00",
        verdict="APPROVED", model="gpt-6.1-sol", family="openai", reply="VERDICT: APPROVE",
        review_mode=mode, review_profile=profile, sources_mcp_call_count=count,
    )
    marker = recorder.parse_marker(body)
    assert marker["sources_calls"] == count
    assert count is None or type(marker["sources_calls"]) is int


@pytest.mark.parametrize("mode", ["cross_family", "red_team"])
@pytest.mark.parametrize("verdict", ["APPROVED", "APPROVE"])
@pytest.mark.parametrize("count", [None, "0", "-1", "unknown", "True", "1.0"])
def test_ukrainian_marker_without_positive_count_refused(monkeypatch, tmp_path, mode, verdict, count):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path)
    write_task(tasks, review_profile="ukrainian", sources_mcp_call_count=3)
    recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    valid = comments[0]
    body = recorder.build_comment(
        sha=SHA, task_id="later", started="2026-09-23T12:00:01.000001+00:00",
        verdict=verdict, model="gpt-6.1-sol", family="openai", reply=f"VERDICT: {verdict}",
        review_mode=mode, review_profile="ukrainian", sources_mcp_call_count=3,
    )
    body = body.replace(" sources_calls=3", "" if count is None else f" sources_calls={count}")
    body = body.replace("Sources MCP calls: 3\n", "" if count is None else f"Sources MCP calls: {count}\n")
    invalid = {**valid, "body": body}
    assert recorder.parse_marker(body) is None
    assert sweep.lookup_verdict([valid, invalid], SHA, "fleet").state == "unknown"
    assert not keeper._recorded_approval_for_head([invalid], SHA, "fleet")
    assert not keeper._ever_approved([invalid], "fleet")


@pytest.mark.parametrize("replacement", ["sources_calls=2", "sources_calls=3 sources_calls=3"])
def test_sources_marker_must_match_published_count(replacement):
    body = recorder.build_comment(
        sha=SHA, task_id="review-one", started="2026-09-23T12:00:00.000001+00:00",
        verdict="APPROVED", model="gpt-6.1-sol", family="openai", reply="VERDICT: APPROVE",
        review_profile="ukrainian", sources_mcp_call_count=3,
    ).replace("sources_calls=3", replacement)
    assert recorder.parse_marker(body) is None


def test_removing_profile_marker_cannot_hide_missing_sources_count():
    body = recorder.build_comment(
        sha=SHA, task_id="review-one", started="2026-09-23T12:00:00.000001+00:00",
        verdict="APPROVED", model="gpt-6.1-sol", family="openai", reply="VERDICT: APPROVE",
        review_profile="ukrainian", sources_mcp_call_count=3,
    ).replace(" review_profile=ukrainian sources_calls=3", "")
    assert recorder.parse_marker(body) is None


def test_changed_runtime_count_conflicts_with_existing_marker(monkeypatch, tmp_path):
    tasks, _, calls = setup_record(monkeypatch, tmp_path)
    write_task(tasks, review_profile="ukrainian", sources_mcp_call_count=3)
    recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    write_task(tasks, review_profile="ukrainian", sources_mcp_call_count=4)
    with pytest.raises(recorder.RecordError, match="conflicts with task"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert calls == {"posts": 1, "statuses": 1}


@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029"], ids=["NEL", "LS", "PS"])
def test_commit_headers_split_only_on_physical_newlines(tmp_path, separator):
    # #9556: a free-text author name must not forge a parent header line.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args], check=True, capture_output=True, text=True, env=env, timeout=30
        ).stdout.strip()

    git("init", "-q", "-b", "main")
    git("config", "user.email", "test@example.invalid")
    forged = "f" * 40
    git("config", "user.name", f"Name{separator}parent {forged}")
    git("commit", "-q", "--allow-empty", "-m", "subject")
    sha = git("rev-parse", "HEAD")

    [entry] = recorder._read_commit_entries(tmp_path, [sha], deadline=time.monotonic() + 30)

    assert entry["parents"] == []
    assert entry["commit"]["tree"]["sha"] == git("rev-parse", "HEAD^{tree}")


@pytest.mark.parametrize("score_line,score", [
    ("SCORE: 4/10 open P1 on the parser.", 4),
    ("SCORE: 4.5/10", None),
    ("", None),
])
def test_recorded_round_stores_score_with_reviewer_and_author_models(scanned_recorder, tmp_path, score_line, score):
    """C-3020: the score is advisory; a missing or malformed one is recorded as absent."""
    tasks, comments, _, sent, _ = scanned_recorder
    write_task(tasks, reply=f"VERDICT: REQUEST_CHANGES\n{score_line}\nF1 [P1] a.py:1 fails.\n")
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    body = comments[0]["body"]
    assert sent == [body]
    assert result["score"] == score and result["verdict"] == "CHANGES_REQUESTED"
    assert (
        "Reviewer family: openai\nVERDICT: CHANGES_REQUESTED\nReviewer model: gpt-6.1-sol\n"
        f"Review score: {f'{score}/10' if score else 'absent'}\nAuthored by: gemini-3.8-flash-high\n"
    ) in body
    marker = sweep.parse_marker(body)
    assert (marker["verdict"], marker["model"], marker["family"]) == ("CHANGES_REQUESTED", "gpt-6.1-sol", "openai")


def test_quote_mismatch_voids_chunk_coverage(monkeypatch, tmp_path):
    """A quote that is not a literal substring of the frozen item does not count as coverage."""
    from scripts.review.review_contract import build_item_packet, render_item_packet

    tasks, comments, _ = setup_record(monkeypatch, tmp_path)
    captured_source_trace(tasks)
    packet = build_item_packet([{"id": "card-a", "text": "привіт"}, {"id": "card-b", "text": "друг"}])
    prompt = tmp_path / "brief.md"
    prompt.write_bytes(render_item_packet(packet).encode())
    reply = (
        "VERDICT: APPROVE\n"
        "```ukrainian-item-judgments\n"
        + json.dumps(
            {
                "schema": "ukrainian-item-judgments.v1",
                "items": [
                    {
                        "id": "card-a",
                        "verdict": "APPROVE",
                        "finding": "",
                        "sources": "VESUM",
                        "quote": "немає",
                    }
                ],
            },
            ensure_ascii=False,
        )
        + "\n```\n"
    )
    assert "немає" not in packet["items"][0]["text"]
    write_task(
        tasks,
        reply=reply,
        review_profile="ukrainian",
        sources_mcp_call_count=3,
        prompt_file=str(prompt),
        prompt_sha256=hashlib.sha256(prompt.read_bytes()).hexdigest(),
    )
    recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    marker = sweep.parse_marker(comments[0]["body"])
    assert marker["void"] == "quote-mismatch"
    assert marker["coverage"] == []
    assert marker["denominator"] == ["card-a", "card-b"]
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == sweep.NEEDS_COVERAGE

    hidden = reply.replace(
        '"quote": "немає"',
        '"finding": "Frozen input quote: \\"немає\\"."',
    )
    write_task(
        tasks,
        task_id="review-hidden",
        reply=hidden,
        review_profile="ukrainian",
        sources_mcp_call_count=3,
        prompt_file=str(prompt),
        prompt_sha256=hashlib.sha256(prompt.read_bytes()).hexdigest(),
    )
    captured_source_trace(tasks, task_id="review-hidden")
    recorder.record("review-hidden", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    hidden_marker = sweep.parse_marker(comments[1]["body"])
    assert hidden_marker["void"] == "quote-mismatch"
    assert hidden_marker["coverage"] == []

    single = reply.replace(
        '"quote": "немає"',
        '"finding": "Frozen input quote: \'немає\'."',
    )
    write_task(
        tasks,
        task_id="review-single",
        reply=single,
        review_profile="ukrainian",
        sources_mcp_call_count=3,
        prompt_file=str(prompt),
        prompt_sha256=hashlib.sha256(prompt.read_bytes()).hexdigest(),
    )
    captured_source_trace(tasks, task_id="review-single")
    recorder.record("review-single", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    single_marker = sweep.parse_marker(comments[2]["body"])
    assert single_marker["void"] == "quote-mismatch"
    assert single_marker["coverage"] == []

    apostrophe = reply.replace(
        '"quote": "немає"',
        '"finding": "Frozen input quote: \'м\'ясо\'."',
    )
    write_task(
        tasks,
        task_id="review-apostrophe",
        reply=apostrophe,
        review_profile="ukrainian",
        sources_mcp_call_count=3,
        prompt_file=str(prompt),
        prompt_sha256=hashlib.sha256(prompt.read_bytes()).hexdigest(),
    )
    captured_source_trace(tasks, task_id="review-apostrophe")
    recorder.record("review-apostrophe", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    apostrophe_marker = sweep.parse_marker(comments[3]["body"])
    assert apostrophe_marker["void"] == "quote-mismatch"
    assert apostrophe_marker["coverage"] == []

    spaces = reply.replace(
        '"quote": "немає"',
        '"finding": "Frozen input quote: \' \'. "',
    )
    write_task(
        tasks,
        task_id="review-spaces",
        reply=spaces,
        review_profile="ukrainian",
        sources_mcp_call_count=3,
        prompt_file=str(prompt),
        prompt_sha256=hashlib.sha256(prompt.read_bytes()).hexdigest(),
    )
    captured_source_trace(tasks, task_id="review-spaces")
    recorder.record("review-spaces", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    spaces_marker = sweep.parse_marker(comments[4]["body"])
    assert spaces_marker["void"] == "quote-mismatch"
    assert spaces_marker["coverage"] == []


def test_item_judgments_unknown_verdict_leaves_coverage_incomplete(monkeypatch, tmp_path):
    """An item with verdict 'unknown' is unreviewed and does not count as coverage."""
    from scripts.review.review_contract import build_item_packet, render_item_packet

    tasks, comments, _ = setup_record(monkeypatch, tmp_path)
    captured_source_trace(tasks)
    packet = build_item_packet([{"id": "card-a", "text": "привіт"}, {"id": "card-b", "text": "друг"}])
    prompt = tmp_path / "brief.md"
    prompt.write_bytes(render_item_packet(packet).encode())
    reply = (
        "VERDICT: APPROVE\n"
        "```ukrainian-item-judgments\n"
        + json.dumps(
            {
                "schema": "ukrainian-item-judgments.v1",
                "items": [
                    {
                        "id": "card-a",
                        "verdict": "APPROVE",
                        "finding": "",
                        "sources": "VESUM",
                        "quote": "привіт",
                    },
                    {
                        "id": "card-b",
                        "verdict": "unknown",
                        "finding": "Evidence inconclusive",
                        "sources": "none",
                    },
                ],
            },
            ensure_ascii=False,
        )
        + "\n```\n"
    )
    write_task(
        tasks,
        reply=reply,
        review_profile="ukrainian",
        sources_mcp_call_count=3,
        prompt_file=str(prompt),
        prompt_sha256=hashlib.sha256(prompt.read_bytes()).hexdigest(),
    )
    recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    marker = sweep.parse_marker(comments[0]["body"])
    assert marker["denominator"] == ["card-a", "card-b"]
    assert marker["coverage"] == ["card-a"]
    assert "card-b" not in marker["coverage"]
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == sweep.NEEDS_COVERAGE


def test_code_review_with_evidence_yields_reviewer_bookkeeping_empty_coverage():
    """Code profile rejects evidence in item judgments as reviewer bookkeeping, returning empty coverage."""
    from scripts.review.review_contract import VOID_REVIEWER_BOOKKEEPING, build_item_packet, judge_item_reply

    packet = build_item_packet([{"id": "item-1", "text": "def test(): pass"}])
    reply = (
        "VERDICT: APPROVE\n"
        "```ukrainian-item-judgments\n"
        + json.dumps({
            "schema": "ukrainian-item-judgments.v1",
            "items": [
                {
                    "id": "item-1",
                    "verdict": "APPROVE",
                    "finding": "Looks good",
                    "sources": "none",
                    "quote": "def test(): pass",
                    "evidence": [{"receipt": "rr-1", "quote": "pass"}],
                }
            ],
        })
        + "\n```\n"
    )
    chunk = judge_item_reply(packet, reply, stated="APPROVED", ukrainian=False)
    assert chunk.void == VOID_REVIEWER_BOOKKEEPING
    assert chunk.coverage == ()


@pytest.mark.parametrize("claim,output,placement", [
    ("Example Reference page 7", "Different Reference page 2", "sources"),
    ("Rule 8 classifies this suffix as soft-group.", "Rule 8 classifies this suffix as hard-group.", "finding"),
    ("VESUM tag noun:inanim:f:v_naz for example", "VESUM tag noun:anim:f:v_naz for example", "sources"),
    ("check_russian_shadow for example returned confidence 0.0", "check_russian_shadow for other returned 0.0", "sources"),
    ("Example Reference page 7", None, "sources"),
    ("СУМ-20 подає цю форму як нормативну, с. 45", "VESUM", "finding"),
    ("verify_stress returned stress on the second syllable", "VESUM", "finding"),
    ("с. 45", "VESUM", "finding"),
    ("Example Reference page 7", "Example Reference page 75", "sources"),
    ("Rule 8", "Rule 81", "finding"),
    ("noun:inanim:f:v_naz", "noun:anim:f:v_naz", "finding"),
    ("ВТС подає це значення як основне", "VESUM", "finding"),
    ("стор. 45", "VESUM", "finding"),
    ("Заболотний подає цю форму", "VESUM", "finding"),
    ("Вікіпедія подає цю форму", "VESUM", "finding"),
    ("Wikipedia reports this form", "VESUM", "finding"),
], ids=["source-page", "rule", "tag", "check", "missing-output", "ukrainian-source", "tool-name", "ukrainian-page",
        "page-prefix", "rule-prefix", "bare-tag", "vts", "page-abbreviation", "author-cyrillic", "wikipedia-uk", "wikipedia-en"])
@pytest.mark.parametrize("reply_format", ["items", "overall", "finding", "title", "smallest_fix", "body", "prose",
                                         "verbatim", "nested", "top-notes", "fenced-summary", "fenced-quote", "fenced-list",
                                         "key-json", "plain-mapping", "nested-control", "non-row-item"])
def test_unbound_ukrainian_source_claims_refused_before_publication(
    monkeypatch, tmp_path, claim, output, placement, reply_format,
):
    """An unbound review must not publish a source assertion missing from its own outputs."""
    from scripts.review.review_contract import build_item_packet, render_item_packet

    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    packet = build_item_packet([{"id": "item-a", "text": "example"}])
    prompt = tmp_path / "brief.md"
    prompt.write_text(render_item_packet(packet))
    row = {"id": "item-a", "verdict": "APPROVE", "finding": "Appropriate activity.", "sources": "none"}
    row[placement] = claim
    reply = "VERDICT: APPROVE\n```ukrainian-item-judgments\n" + json.dumps({
        "schema": "ukrainian-item-judgments.v1", "items": [row],
    }) + "\n```\n"
    audit_id, audit_field = "item-a", placement
    audit_claim = claim
    if reply_format == "key-json":
        reply = "VERDICT: APPROVE\n```json\n" + json.dumps({claim: "Uncited wording."}) + "\n```\n"
        audit_id, audit_field = None, claim + ".__key__"
    elif reply_format == "plain-mapping":
        reply = "VERDICT: APPROVE\n" + claim + ": Uncited wording.\n"
        audit_id, audit_field = "review-prose", "finding"
        audit_claim = "VERDICT: APPROVE\n" + claim + ": Uncited wording."
    elif reply_format == "nested-control":
        payload = {"notes": {"category": claim, "outcome": claim, "id": claim,
                             "location": {"path": claim}, "receipt_id": claim}}
        reply = "VERDICT: APPROVE\n```json\n" + json.dumps(payload) + "\n```\n"
        audit_id, audit_field = None, "notes.category"
    elif reply_format == "non-row-item":
        reply = "VERDICT: APPROVE\n```json\n" + json.dumps({"items": [claim]}) + "\n```\n"
        audit_id, audit_field = None, "items"
    elif reply_format in {"fenced-summary", "fenced-quote", "fenced-list"}:
        field = "quote" if reply_format == "fenced-quote" else "summary"
        body = "- " + claim if reply_format == "fenced-list" else json.dumps({field: claim})
        tag = "yaml" if reply_format == "fenced-list" else "json"
        reply = f"VERDICT: APPROVE\n```{tag}\n{body}\n```\n"
        if reply_format == "fenced-list":
            audit_id, audit_field = "review-prose", "finding"
            audit_claim = "VERDICT: APPROVE\n\n\n" + body
        else:
            audit_id, audit_field = None, field
    elif reply_format in {"nested", "top-notes"}:
        row[placement] = "none"
        payload = {"schema": "ukrainian-item-judgments.v1", "items": [row]}
        if reply_format == "nested":
            row["extra"] = {"notes": [claim]}
            audit_id, audit_field = "item-a", "extra.notes"
        else:
            payload["notes"] = claim
            audit_id, audit_field = None, "notes"
        reply = "VERDICT: APPROVE\n```ukrainian-item-judgments\n" + json.dumps(payload) + "\n```\n"
    elif reply_format == "prose":
        row[placement] = "none"
        reply = claim + ";\nVERDICT: APPROVE\n```ukrainian-item-judgments\n" + json.dumps({
            "schema": "ukrainian-item-judgments.v1", "items": [row],
        }) + "\n```\n"
        audit_id, audit_field = "review-prose", "finding"
    elif reply_format != "items":
        payload = structured_review(0 if reply_format == "overall" else 1)
        payload["overall"]["correctness"] = "correct"
        if reply_format == "overall":
            payload["overall"]["explanation"] = claim
            audit_id, audit_field = None, "overall.explanation"
        else:
            payload["overall"]["explanation"] = "Appropriate activity."
            payload["findings"][0].update(priority="P3", body="Advisory wording.", sources=["none"])
            audit_field = "sources" if reply_format == "finding" else reply_format
            payload["findings"][0][audit_field] = [claim] if audit_field == "sources" else claim
            audit_id = "F1"
        reply = json.dumps(payload)
    captured_source_trace(tasks, arguments={"query": claim}, output=output)
    write_task(tasks, reply=reply, review_profile="ukrainian", sources_mcp_call_count=75,
               prompt_file=str(prompt), prompt_sha256=hashlib.sha256(prompt.read_bytes()).hexdigest())
    raw = (tasks / "review-one.result").read_bytes()

    def no_network(*args, **kwargs):
        pytest.fail("Unsupported review reached the publication/network boundary")

    monkeypatch.setattr(recorder, "_pr", no_network)
    with pytest.raises(recorder.RecordError, match="UKRAINIAN_CLAIMS_UNSUPPORTED") as refused:
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    audit = json.loads(str(refused.value).split(": ", 1)[1])
    assert audit[0]["item_id"] == audit_id
    assert audit[0]["claim"] == {audit_field: audit_claim}
    assert audit[0]["reason"] == "claim_not_in_captured_output"
    assert audit[0]["captured_event_ids"] == ["step-4"]
    assert audit[0]["uncaptured_event_ids"] == (["step-4"] if output is None else [])
    if reply_format == "nested-control":
        assert {next(iter(entry["claim"])) for entry in audit} == {
            "notes.category", "notes.outcome", "notes.id", "notes.location.path", "notes.receipt_id",
        }
    assert comments == [] and calls == {"posts": 0, "statuses": 0}
    assert (tasks / "review-one.result").read_bytes() == raw


@pytest.mark.parametrize("capture", ["agy", "codex", "claude", "bound"])
@pytest.mark.parametrize("finding", ["Appropriate activity.", "Вправа правильно перевіряє форму", "Вправа передає сум"])
@pytest.mark.parametrize("bad_quote", ["uncaptured quote", "Rule 8", "category: Rule 8", "outcome: Rule 8"])
def test_ukrainian_supported_claim_remains_recordable(monkeypatch, tmp_path, capture, finding, bad_quote):
    """A supported exact-head review must not be over-rejected, including quoted source output."""
    import yaml

    from scripts.dispatcher import store
    from scripts.review.receipts import ledger
    from scripts.review.review_contract import build_item_packet, render_item_packet, validate_ukrainian_reply_claims

    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    claim = 'VESUM reports "attested" for the example.'
    packet = build_item_packet([{"id": "item-a", "text": "example"}])
    prompt = tmp_path / "brief.md"
    prompt.write_text(render_item_packet(packet))
    binding = None
    if capture == "bound":
        binding = {"review_id": "review", "attempt_id": "attempt", "manifest_sha256": "a" * 64}
        root = tmp_path / "review-receipts"
        monkeypatch.setattr(store, "receipts_root", lambda: root)
        path = root / "review" / "attempt.jsonl"
        receipt = ledger.append(path, **binding, tool="verify_word", arguments={"word": "example"},
                                result=claim + "; Rule 81", server_version="test", snapshots={}, status="ok")
        rejected = structured_review(1)
        rejected["overall"].update(correctness="correct", explanation="Appropriate activity.")
        rejected["findings"][0].update(
            priority="P3", body=claim, sources=["none"], evidence={"receipt": receipt, "quote": bad_quote},
        )
        metadata = bad_quote.split(": ", 1) if ": " in bad_quote else None
        if metadata:
            rejected["findings"][0]["evidence"].update(quote=claim, **{metadata[0]: metadata[1]})
        tag = "yaml" if metadata else "json"
        candidate = ("VERDICT: APPROVE\n" if metadata else "") + f"```{tag}\n" + json.dumps(rejected) + "\n```"
        sanitized, checked = validate_ukrainian_reply_claims(candidate, ledger_path=path, binding=binding)
        assert checked.claims_unsupported == (1 if metadata else 2)
        body = sanitized.split(f"```{tag}\n")[1].split("\n```")[0]
        sanitized_finding = (yaml.safe_load(body) if metadata else json.loads(body))["findings"][0]
        if metadata:
            assert sanitized_finding["evidence"][metadata[0]] == metadata[1]
        else:
            assert "evidence" not in sanitized_finding
        write_task(tasks, reply=sanitized, review_profile="ukrainian", sources_mcp_call_count=1,
                   review_attempt=binding, claims_unsupported=checked.claims_unsupported,
                   dropped_claims=list(checked.dropped_claims))
        with monkeypatch.context() as guarded:
            def no_network(*args, **kwargs):
                pytest.fail("Sanitized unsupported attempt reached publication")
            guarded.setattr(recorder, "_pr", no_network)
            with pytest.raises(recorder.RecordError, match="UKRAINIAN_CLAIMS_UNSUPPORTED") as refused:
                recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
        assert (metadata[1] if metadata else bad_quote) in str(refused.value)
        assert comments == [] and calls == {"posts": 0, "statuses": 0}
    else:
        captured_source_trace(tasks, output=claim)
        receipt = "step-4"
        if capture != "agy":
            path = tasks / "logs" / "review-one.stdout.log"
            if capture == "codex":
                events = [{"type": "response_item", "payload": {
                    "type": "function_call", "call_id": "call-1", "name": "mcp__sources__verify_word",
                    "arguments": json.dumps({"word": "example"}),
                }}, {"type": "response_item", "payload": {
                    "type": "function_call_output", "call_id": "call-1", "output": claim,
                }}]
            else:
                events = [{"type": "assistant", "message": {"content": [{
                    "type": "tool_use", "id": "call-1", "name": "mcp__sources__verify_word",
                    "input": {"word": "example"},
                }]}}, {"type": "user", "message": {"content": [{
                    "type": "tool_result", "tool_use_id": "call-1", "content": claim,
                }]}}]
            path.write_text("\n".join(json.dumps(event) for event in events) + "\n")
            receipt = "runtime-0"
    reply = "VERDICT: APPROVE\n```ukrainian-item-judgments\n" + json.dumps({
        "schema": "ukrainian-item-judgments.v1", "items": [{
            "id": "item-a", "verdict": "APPROVE", "finding": finding,
            "sources": claim, "evidence": [{"receipt": receipt, "quote": claim}],
        }],
    }) + "\n```\n"
    write_task(tasks, reply=reply, review_profile="ukrainian", sources_mcp_call_count=1,
               prompt_file=str(prompt), prompt_sha256=hashlib.sha256(prompt.read_bytes()).hexdigest(),
               **({"review_attempt": binding} if binding else {}))
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert result["verdict"] == "APPROVED"
    assert calls == {"posts": 1, "statuses": 1}
    marker = sweep.parse_marker(comments[0]["body"])
    assert marker["coverage"] == marker["denominator"] == ["item-a"]
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == "APPROVED"
