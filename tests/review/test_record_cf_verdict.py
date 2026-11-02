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


def test_changes_requested_with_only_p3_findings_records_approval(scanned_recorder, tmp_path, monkeypatch):
    """REQUEST_CHANGES whose open findings are all P3 records as APPROVED, status success, reply verbatim."""
    tasks, comments, _, sent, _ = scanned_recorder
    payload = structured_review(2)
    payload["overall"].update(
        correctness="incorrect",
        explanation="VERDICT: REQUEST_CHANGES. SCORE: 6/10. The only open findings are P3 regressions.",
    )
    for finding in payload["findings"]:
        finding["priority"] = "P3"
    reply = json.dumps(payload)
    write_task(tasks, reply=reply)
    statuses = []
    monkeypatch.setattr(recorder, "post_commit_status", lambda **fields: statuses.append(fields))
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    body = comments[0]["body"]
    assert reply in body and "Residuals: F1 (P3), F2 (P3)" in body
    assert result["verdict"] == "APPROVED" and result["residuals"] == ["F1", "F2"]
    assert "p3_downgrade_refused" not in result
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == "APPROVED"
    assert statuses == [{
        "repository": "owner/repo",
        "head_sha": SHA,
        "state": "success",
        "context": "fleet/cross-family-review",
        "description": "VERDICT: APPROVED openai review-one",
    }]
    assert sent == [body]


@pytest.mark.parametrize("blocking", ["P0", "P1", "P2"])
def test_pure_findings_object_with_a_blocking_entry_records_rejection(scanned_recorder, tmp_path, monkeypatch, blocking):
    """One P0 to P2 entry beside P3 entries keeps REQUEST_CHANGES and names why (#12409)."""
    tasks, comments, _, _, _ = scanned_recorder
    payload = structured_review(2)
    payload["overall"]["explanation"] = "VERDICT: REQUEST_CHANGES. One finding blocks."
    payload["findings"][0]["priority"] = "P3"
    payload["findings"][1]["priority"] = blocking
    write_task(tasks, reply=json.dumps(payload))
    statuses = []
    monkeypatch.setattr(recorder, "post_commit_status", lambda **fields: statuses.append(fields))
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    body = comments[0]["body"]
    assert result["verdict"] == "CHANGES_REQUESTED" and "residuals" not in result
    assert result["p3_downgrade_refused"] == recorder.P3_BLOCKING_FINDING
    assert "Residuals:" not in body
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == "CHANGES_REQUESTED"
    assert statuses[0]["state"] == "failure"


def test_security_verdict_fail_keeps_changes_requested(scanned_recorder, tmp_path, monkeypatch):
    """SECURITY_VERDICT FAIL with only P3 findings stays CHANGES_REQUESTED and status failure."""
    tasks, comments, _, _, _ = scanned_recorder
    reply = (
        "VERDICT: REQUEST_CHANGES\n"
        "SCORE: 4/10 the security verdict stands.\n"
        "SECURITY_VERDICT FAIL\n"
        "F1 [P3] scripts/example.py:10 the check is skipped. Impact: a refused input is accepted. "
        "Required behaviour: the refusal stays.\n"
    )
    write_task(tasks, reply=reply)
    statuses = []
    monkeypatch.setattr(recorder, "post_commit_status", lambda **fields: statuses.append(fields))
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    body = comments[0]["body"]
    assert result["verdict"] == "CHANGES_REQUESTED" and "residuals" not in result
    assert "Residuals:" not in body and reply in body
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == "CHANGES_REQUESTED"
    assert statuses[0]["state"] == "failure" and statuses[0]["context"] == "fleet/cross-family-review"
    assert statuses[0]["description"] == "VERDICT: CHANGES_REQUESTED openai review-one"


def _all_p3_object(*, indent=None):
    payload = structured_review(1)
    payload["overall"]["explanation"] = "One P3 residual."
    payload["findings"][0]["priority"] = "P3"
    return json.dumps(payload, indent=indent)


_P3_PREFIX = "VERDICT: REQUEST_CHANGES\nF1 [P3] scripts/example.py:10 count is high.\n"
_P3_OBJECT = _all_p3_object()
_P3_FENCED = "```json\n" + _all_p3_object(indent=2) + "\n```\n"
# A plain decoder keeps the last "findings" key, which would hide the P1 list before it.
_P3_DUPLICATE = _P3_OBJECT.replace(
    '"findings": ', '"findings": ' + json.dumps(structured_review(1)["findings"]).replace("P2", "P1") + ', "findings": ', 1
)
# Every reply form that hid an open P0 to P2 finding from PR #12379's prose matchers (rounds 2 to 6).
_P3_REFUSED = {
    "prose-only": _P3_PREFIX,
    "r2-nested-quoted-fence": _P3_PREFIX + ">> ```\n>> F2 scripts/example.py:20 missing priority.\n>> ```\n",
    "r2-nested-quoted-indent": _P3_PREFIX + ">>\n>>     F2 scripts/example.py:20 missing priority.\n",
    "r2-quoted-fence": _P3_PREFIX + "> ```\n> F2 scripts/example.py:20 missing priority.\n> ```\n",
    "r2-fenced-resolved-question": _P3_PREFIX + "```\nF2 resolved? scripts/example.py:20 still open.\n```\n",
    "r2-indented-resolved-question": _P3_PREFIX + "\n    F2 resolved? scripts/example.py:20 still open.\n",
    "r3-long-resolution-window": (
        _P3_PREFIX + "```\nF2 resolved after checking the patch? scripts/example.py:20 still open.\n```\n"
    ),
    "r3-fixed-long-window": _P3_PREFIX + "F2 fixed after checking the patch? scripts/example.py:20 still open.\n",
    "r3-later-negation": _P3_PREFIX + "F2 resolved after checking the patch, not actually fixed.\n",
    "r3-padded-question": _P3_PREFIX + "F2 resolved after checking the patch ? scripts/example.py:20 still open.\n",
    "r3-next-sentence": _P3_PREFIX + "F2 resolved. This is not a blocker.\n",
    "r4-i.e.": _P3_PREFIX + "F2 resolved, i.e. not actually fixed.\n",
    "r4-e.g.": _P3_PREFIX + "F2 fixed, e.g. not actually fixed.\n",
    "r4-e.g.-mid-clause": _P3_PREFIX + "F2 resolved in e.g. scripts/example.py:20, but not actually fixed.\n",
    "r4-emphasis": _P3_PREFIX + "F2 resolved **successfully.** This is not a blocker.\n",
    "r5-colon-i.e.": _P3_PREFIX + "```\nF2: resolved, i.e. not actually fixed.\n```\n",
    "r5-colon-e.g.": _P3_PREFIX + "F2: fixed, e.g. not actually fixed.\n",
    "r5-colon-unprioritized": _P3_PREFIX + "    F2: scripts/example.py:20 missing priority.\n",
    "r6-verdict-line-p1-prose-fenced-object": (
        "VERDICT: REQUEST_CHANGES\nF2 [P1] scripts/a.py:3 auth bypass, blocker.\n\n" + _P3_FENCED
    ),
    "r6-unprioritized-prose-fenced-object": "VERDICT: REQUEST_CHANGES\nF2 scripts/a.py:3 auth bypass.\n\n" + _P3_FENCED,
    "r6-p0-prose-bare-object": "VERDICT: REQUEST_CHANGES\nF2 [P0] scripts/a.py:3 data loss.\n\n" + _P3_OBJECT,
    "r6-verdict-line-only-object": "VERDICT: REQUEST_CHANGES\n\n" + _P3_OBJECT,
    "fenced-object-alone": _P3_FENCED,
    "object-then-prose": _P3_OBJECT + "\n\nF2 [P2] scripts/a.py:3 still open.\n",
    "two-objects": _P3_OBJECT + "\n" + _P3_OBJECT,
    "duplicate-findings-key": _P3_DUPLICATE,
    "nan-confidence": _P3_OBJECT.replace('"confidence": 0.9', '"confidence": NaN', 1),
    "infinity-confidence": _P3_OBJECT.replace('"confidence": 0.9', '"confidence": Infinity', 1),
    "escaped-security-fail": _P3_OBJECT.replace("One P3 residual.", "\\u0053ECURITY_VERDICT: FAIL"),
    "escaped-security-underscore": _P3_OBJECT.replace("One P3 residual.", "SECURITY\\u005fVERDICT: FAIL"),
}
_P3_REASONS = {
    "duplicate-findings-key": recorder.P3_DUPLICATE_KEY,
    "escaped-security-fail": recorder.P3_SECURITY_NOT_PASS,
    "escaped-security-underscore": recorder.P3_SECURITY_NOT_PASS,
}


@pytest.mark.parametrize("name", list(_P3_REFUSED))
def test_p3_downgrade_refuses_every_reply_but_one_findings_object(name):
    """Only a whole-reply findings object is read for P3 residuals; prose keeps the rejection (#12409)."""
    reply = _P3_REFUSED[name]
    reading = recorder.p3_reading(reply)
    assert reading == recorder.P3Reading(reason=_P3_REASONS.get(name, recorder.P3_NOT_ONE_OBJECT))
    body = recorder.build_comment(
        sha=SHA, task_id="review-one", started="2026-09-23T12:00:00+00:00", verdict="CHANGES_REQUESTED",
        model="gpt-6.1-sol", family="openai", reply=reply,
    )
    assert sweep.recorded_p3_residuals(body) is None
    assert sweep.recorded_p3_residuals(body.replace(reply, _P3_OBJECT)) == ("F1",)


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
    recorder.record("review-spaces", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    spaces_marker = sweep.parse_marker(comments[4]["body"])
    assert spaces_marker["void"] == "quote-mismatch"
    assert spaces_marker["coverage"] == []


def test_block_only_ukrainian_reply_records_full_coverage(monkeypatch, tmp_path):
    """Defect class (#12417): a contract-only judgment block with a frozen packet is refused for lack of a verdict line."""
    from scripts.review.review_contract import build_item_packet, render_item_packet

    tasks, comments, _ = setup_record(monkeypatch, tmp_path)
    packet = build_item_packet([{"id": "card-a", "text": "привіт"}, {"id": "card-b", "text": "друг"}])
    prompt = tmp_path / "brief.md"
    prompt.write_bytes(render_item_packet(packet).encode())
    items = [
        {"id": item_id, "verdict": "APPROVE", "finding": "", "sources": "VESUM", "quote": text}
        for item_id, text in (("card-a", "привіт"), ("card-b", "друг"))
    ]
    reply = (
        "```ukrainian-item-judgments\n"
        + json.dumps({"schema": "ukrainian-item-judgments.v1", "items": items}, ensure_ascii=False)
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
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    marker = sweep.parse_marker(comments[0]["body"])
    assert result["verdict"] == marker["verdict"] == "APPROVED"
    assert marker["denominator"] == marker["coverage"] == ["card-a", "card-b"]
    assert marker.get("void") is None


def test_item_judgments_unknown_verdict_leaves_coverage_incomplete(monkeypatch, tmp_path):
    """An item with verdict 'unknown' is unreviewed and does not count as coverage."""
    from scripts.review.review_contract import build_item_packet, render_item_packet

    tasks, comments, _ = setup_record(monkeypatch, tmp_path)
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
