"""Runtime Sources-call gate for Ukrainian verdict publication (#10074)."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import delegate
from scripts.orchestration import integration_sweep as sweep
from scripts.orchestration import merge_queue_keeper as keeper
from scripts.review import record_cf_verdict as recorder
from scripts.review.language_lane import is_ukrainian_review
from tests.test_record_cf_verdict import SHA, setup_record, write_task


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
    reply = f"VERDICT: {verdict}\n{detail}\nHarmless reviewer sentence.\n- A prose bullet."
    write_task(tasks, reply=reply)
    before = {suffix: (tasks / f"review-one.{suffix}").read_bytes() for suffix in ("json", "result")}
    with pytest.raises(gate.PublishBlocked, match=f"rule={rule}"):
        gate.check_texts("github.com/owner/repo", [reply], tooling=tooling, environment={})
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    body = comments[0]["body"]
    assert body == (
        f"### Cross-family review\nhead: {SHA}\nReviewer family: openai\nVERDICT: {verdict}\n"
        "Reviewer model: gpt-6.1-sol\nTask id: review-one\n\nWithheld findings: unknown\n"
        "Findings are held privately.\n\n"
        f"<!-- cf-verdict v1 sha={SHA} task=review-one started=2026-09-23T12:00:00.000001+00:00 "
        f"verdict={verdict} model=gpt-6.1-sol family=openai -->"
    )
    assert sent == [body]
    assert detail not in body and "SYNTHETIC-DETAIL" not in body
    gate.check_texts("github.com/owner/repo", [body], tooling=tooling, environment={})
    assert result["verdict"] == verdict
    assert sweep.parse_marker(body)["sha"] == SHA
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == verdict
    assert keeper._recorded_approval_for_head(comments, SHA, "fleet") == (verdict == "APPROVED")
    assert not keeper._recorded_approval_for_head(comments, "b" * 40, "fleet")
    second = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert second["comment"] == "existing" and sent == [body]
    assert calls == {"posts": 1, "statuses": 2}
    assert (tasks / "review-one.result").read_bytes() == before["result"]
    # The recorder adds its receipt; private findings and every existing task field stay unchanged.
    original = json.loads(before["json"])
    after = json.loads((tasks / "review-one.json").read_text())
    receipt = after.pop(sweep.RECEIPT_FIELD)
    assert after == original
    assert receipt["comment_id"] == comments[0]["id"]
    assert receipt["comment_sha256"] == hashlib.sha256(body.encode()).hexdigest()
    assert receipt["head_sha"] == SHA
    assert receipt["run_nonce"] == original["run_nonce"]


def test_clean_publication_bytes_unchanged(scanned_recorder, tmp_path):
    tasks, comments, calls, sent, _ = scanned_recorder
    reply = "VERDICT: APPROVE\nOrdinary reviewer text.\n\n  Preserve spacing.\n"
    write_task(tasks, reply=reply)
    recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    expected = (
        f"### Cross-family review\nhead: {SHA}\nReviewer family: openai\nVERDICT: APPROVED\n"
        "Reviewer model: gpt-6.1-sol\nTask id: review-one\n\n"
        "<details><summary>Reviewer's reply</summary>\n\n"
        + reply + "\n\n</details>\n\n"
        f"<!-- cf-verdict v1 sha={SHA} task=review-one started=2026-09-23T12:00:00.000001+00:00 "
        "verdict=APPROVED model=gpt-6.1-sol family=openai -->"
    )
    assert comments[0]["body"].encode() == expected.encode()
    assert sent == [expected] and calls == {"posts": 1, "statuses": 1}


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


@pytest.mark.parametrize("update", [
    {"findings": "not a list"}, {"findings": [None]}, {"verdict": "APPROVED"},
    {"verdict": "INVALID"}, {"overall": {}},
])
def test_invalid_structured_verdict_or_count_refuses(scanned_recorder, tmp_path, update):
    tasks, comments, calls, sent, _ = scanned_recorder
    payload = structured_review(1)
    payload.update(update)
    write_task(tasks, reply=json.dumps(payload))
    with pytest.raises(recorder.RecordError, match="structured review verdict or findings invalid"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == sent == [] and calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("payload,expected", [
    ({"schema_version": "code-review-findings.v1", "overall": {
        "correctness": "correct", "explanation": "", "confidence": 0.9}, "findings": []}, "BLOCKED"),
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


def test_real_rule_rejecting_skeleton_metadata_has_no_write(scanned_recorder, tmp_path):
    tasks, comments, calls, sent, _ = scanned_recorder
    write_task(tasks, task_id="credential-permission", reply="VERDICT: APPROVE\nOrdinary review text.")
    with pytest.raises(recorder.RecordError, match="rule=5-credential-context"):
        recorder.record("credential-permission", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
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
    # Only the recorder receipt is added; every other field is kept (#10501).
    after = json.loads((tasks / "review-one.json").read_text())
    assert after.pop(sweep.RECEIPT_FIELD)["comment_id"] == comments[0]["id"]
    assert after == json.loads(before)


@pytest.mark.parametrize("identity,reason", [
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
def test_detached_review_refuses_wrong_pr_identity(monkeypatch, tmp_path, pr, reason):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path, **pr)
    write_task(tasks, worktree_branch=None, review_branch="codex/42")
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
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == "APPROVED"
    assert keeper._recorded_approval_for_head(comments, SHA, "fleet")
    recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert calls == {"posts": 1, "statuses": 2}


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


@pytest.mark.parametrize("count", [0, None])
def test_non_ukrainian_reviews_unaffected(monkeypatch, tmp_path, count):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    write_task(tasks, review_profile="code", sources_mcp_call_count=count)
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert result["status"] == "posted"
    assert len(comments) == 1
    assert calls == {"posts": 1, "statuses": 1}


@pytest.mark.parametrize(
    "runtime,expected",
    [
        ({"tool_calls_total": 2, "tool_calls": [{"name": "mcp__sources__verify_words"}, {"name": "shell"}]}, 1),
        ({"tool_calls_total": 1, "tool_calls": [{"name": "mcp_sources_search_text"}]}, 1),
        ({"tool_calls_total": 0, "tool_calls": []}, 0),
        ({"tool_calls_total": 1, "tool_calls": [{"name": "mcp__other__verify_words"}]}, 0),
        ({"tool_calls_total": 1, "tool_calls": [{"name": "mcp__sources_fake__verify_words"}]}, 0),
        ({"tool_calls_total": 1, "tool_calls": [{"name": "mcp__sources__"}]}, 0),
        ({"tool_calls_total": None, "tool_calls": [{"name": "mcp__sources__verify_words"}]}, None),
        ({"tool_calls_total": 1, "tool_calls": []}, None),
        ({"tool_calls_total": True, "tool_calls": [{"name": "mcp__sources__verify_words"}]}, None),
        ({"tool_calls_total": 1, "tool_calls": [None]}, None),
        ({"tool_calls_total": 1, "tool_calls": [{}]}, None),
        ({}, None),
    ],
)
def test_sources_count_comes_from_runtime_tool_names(runtime, expected):
    assert delegate._sources_mcp_call_count(SimpleNamespace(**runtime)) == expected


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


@pytest.mark.parametrize("classification,expected", [
    ({"review_profile": " Ukrainian "}, True),
    ({"review_language_lane": True}, True),
    ({"language_lane": True}, True),
    ({"research_task_family": " UKRAINIAN-REVIEW "}, True),
    ({"task_family": "ukrainian-authoring"}, True),
    ({"research_task_family": "generic"}, False),
    ({}, False),
])
def test_shared_ukrainian_classification(classification, expected):
    assert is_ukrainian_review(classification) is expected
