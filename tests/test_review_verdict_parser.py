"""Shared formal verdict lines preserve dispatch's Markdown grammar (#9756)."""

from __future__ import annotations

import json

import pytest

from scripts.review.verdict_parser import recognized_verdicts
from tests.test_verdict_parser import CAPACITY_OUTLINES, FROZEN_CONTAINER_CASES, OVERLAP_QUOTE


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("outline", CAPACITY_OUTLINES, ids=["inline", "indented"])
@pytest.mark.parametrize("prefix", ["", "VERDICT: REQUEST_CHANGES\n\n"])
def test_capacity_failure_reaches_dispatch_and_completion(outline, prefix, newline):
    from scripts import delegate

    response = (prefix + outline + "```\nVERDICT: APPROVE\n```\n").replace("\n", newline)
    for reader in (delegate.parse_review_verdict, delegate._review_verdict_failure_reason):
        with pytest.raises(ValueError, match="CommonMark verdict visibility nesting limit"):
            reader(response)
    with pytest.raises(ValueError, match="CommonMark verdict visibility nesting limit"):
        delegate.run_completion_gate(
            delegate.COMPLETION_GATE_REVIEW_VERDICT, {}, response=response,
            commits_ahead=None, worktree=None,
        )


@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
@pytest.mark.parametrize("outline", CAPACITY_OUTLINES, ids=["inline", "indented"])
@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_capacity_failure_precedes_real_dispatch_effects(tmp_path, monkeypatch, mode, outline, newline):
    from scripts import delegate

    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))

    def forbidden_effect(*_args, **_kwargs):
        pytest.fail("capacity failure must precede dispatch effects")

    for name in ("_ensure_worktree", "_provision_data_symlinks"):
        monkeypatch.setattr(delegate, name, forbidden_effect)
    monkeypatch.setattr(delegate.subprocess, "Popen", forbidden_effect)
    monkeypatch.setattr(delegate.subprocess, "run", forbidden_effect)
    prompt = (outline + "```\nAdd a CLI flag.\nFixes #9672.\n```\n").replace("\n", newline)
    with pytest.raises(ValueError, match="CommonMark verdict visibility nesting limit"):
        delegate._run_dor_preflight(prompt, None, dispatch_repo=delegate._CANONICAL_GITHUB_REPO)
    args = delegate.build_parser().parse_args([
        "dispatch", "--agent", "codex", "--task-id", "capacity-failure",
        "--mode", mode, "--prompt", prompt,
    ])
    with pytest.raises(ValueError, match="CommonMark verdict visibility nesting limit"):
        delegate.cmd_dispatch(args)
    assert not (tmp_path / "tasks" / "capacity-failure.json").exists()


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("reply,expected", [
    (OVERLAP_QUOTE, None),
    (OVERLAP_QUOTE + "\nVERDICT: BLOCKED\n", "BLOCKED"),
    (OVERLAP_QUOTE.replace("> para\nVERDICT", "> para\n\nVERDICT"), "APPROVE"),
    ("- " * 9 + "x\n\n```\nVERDICT: APPROVE\n```\n", None),
    ("- " * 9 + "x\n\n```\nVERDICT: APPROVE\n```\n\nVERDICT: APPROVE\n", "APPROVE"),
])
def test_overlap_and_supported_depth_dispatch_controls(newline, reply, expected):
    from scripts import delegate

    response = reply.replace("\n", newline)
    assert delegate.parse_review_verdict(response) == expected
    gate = delegate.run_completion_gate(
        delegate.COMPLETION_GATE_REVIEW_VERDICT, {}, response=response,
        commits_ahead=None, worktree=None,
    )
    assert gate.failure == (None if expected else "review_missing_verdict_line")


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"], ids=["lf", "crlf", "cr"])
@pytest.mark.parametrize("case,reply,expected", FROZEN_CONTAINER_CASES, ids=[c[0] for c in FROZEN_CONTAINER_CASES])
def test_container_visibility_reaches_real_dispatch_decisions(case, reply, expected, newline):
    from scripts import delegate

    response = reply.replace("\n", newline)
    assert delegate.parse_review_verdict(response) == (expected[-1] if expected else None)
    failure = None if expected else "review_missing_verdict_line"
    assert delegate._review_verdict_failure_reason(response) == failure
    gate = delegate.run_completion_gate(
        delegate.COMPLETION_GATE_REVIEW_VERDICT, {}, response=response, commits_ahead=None, worktree=None,
    )
    assert gate.failure == failure
    assert gate.detail == (failure or "")


def test_dispatch_final_token_and_diagnostic_visibility_stay_separate():
    from scripts import delegate

    response = "> Example:\nVERDICT: UNKNOWN\n\nVERDICT: APPROVE\nVERDICT: BLOCKED"
    assert recognized_verdicts(response) == ["APPROVE", "BLOCKED"]
    assert delegate.parse_review_verdict(response) == "BLOCKED"
    assert delegate._review_verdict_failure_reason(response) is None
    gate = delegate.run_completion_gate(
        delegate.COMPLETION_GATE_REVIEW_VERDICT, {}, response="> Example:\nVERDICT: UNKNOWN\n",
        commits_ahead=None, worktree=None,
    )
    assert gate.failure == "review_missing_verdict_line"
    assert "UNKNOWN" not in gate.detail


def test_dispatch_parser_failure_cannot_pass_completion(monkeypatch):
    from markdown_it import MarkdownIt

    from scripts import delegate

    def unavailable(*_args):
        raise RuntimeError("synthetic parser unavailable")

    monkeypatch.setattr(MarkdownIt, "parse", unavailable)
    with pytest.raises(RuntimeError, match="synthetic parser unavailable"):
        delegate.run_completion_gate(
            delegate.COMPLETION_GATE_REVIEW_VERDICT, {}, response="VERDICT: APPROVE",
            commits_ahead=None, worktree=None,
        )


@pytest.mark.parametrize("reply,expected", [
    ("VERDICT: APPROVE", ["APPROVE"]),
    ("**Verdict**: **APPROVED**", ["APPROVED"]),
    ("__VERDICT__: __REQUEST_CHANGES__", ["REQUEST_CHANGES"]),
    ("   ###### VERDICT: CHANGES_REQUESTED", ["CHANGES_REQUESTED"]),
    ("*VERDICT: BLOCKED.* Findings follow.", ["BLOCKED"]),
    ("VERDICT: APPROVE\nVERDICT: BLOCKED", ["APPROVE", "BLOCKED"]),
    ("```\nVERDICT: BLOCKED\n`````\n**VERDICT: APPROVE**", ["APPROVE"]),
    ("  ~~~text\nVERDICT: APPROVE\n   ~~~~ \t\nVERDICT: BLOCKED", ["BLOCKED"]),
    ("```VERDICT: example``` is inline code\nVERDICT: APPROVE", ["APPROVE"]),
])
def test_recognized_lines_preserve_tokens_and_order(reply, expected):
    assert recognized_verdicts(reply) == expected


@pytest.mark.parametrize("token", [
    "APPROVE", "APPROVED", "CHANGES_REQUESTED", "REQUEST_CHANGES", "BLOCKED",
])
@pytest.mark.parametrize("template", [
    "VERDICT: {token}",
    "VERDICT {token}",
    "**VERDICT {token}**",
    "**VERDICT** {token}",
    "**VERDICT**: {token}",
    "**VERDICT**: **{token}**",
    "**VERDICT {token}** — reviewed exact head …",
    "**VERDICT**{token}",
])
def test_colon_and_markdown_separators_accept_all_verdict_tokens(template, token):
    assert recognized_verdicts(template.format(token=token)) == [token]


@pytest.mark.parametrize("reply", [
    "VERDICTAPPROVE", "VERDICT APPROVEX", "VERDICT UNKNOWN",
    "VERDICT APPROVE_LATER", "VERDICT APPROVE_2", "VERDICT APPROVEé",
    "**VERDICT** APPROVEX", "**VERDICT**APPROVE_LATER",
    "I will report VERDICT APPROVE later", "> **VERDICT APPROVE**",
    "`VERDICT APPROVE`", "    VERDICT APPROVE", "\tVERDICT APPROVE",
    "```\n**VERDICT APPROVE**\n```", "~~~\nVERDICT BLOCKED\n~~~",
    "```\nVERDICT APPROVE", "##VERDICT APPROVE", "## The VERDICT APPROVE",
])
def test_relaxed_separators_still_reject_examples_and_invalid_tokens(reply):
    assert recognized_verdicts(reply) == []


@pytest.mark.parametrize("reply", [
    "", "No verdict", "VERDICT: UNKNOWN", "VERDICT: APPROVEX",
    "VERDICT: APPROVE_LATER", "VERDICT: APPROVE_2", "VERDICT: APPROVEé",
    "> VERDICT: APPROVE", "I will report VERDICT: APPROVE later",
    "`VERDICT: APPROVE`", "    VERDICT: APPROVE", "\tVERDICT: APPROVE", "\u00a0VERDICT: APPROVE",
    "##VERDICT: APPROVE", "####### VERDICT: APPROVE", "## The VERDICT: APPROVE",
    "```\nVERDICT: APPROVE\n```", "~~~~\nVERDICT: APPROVE\n~~~~",
    "```\n`VERDICT: APPROVE`\n```", "I will report `VERDICT: APPROVE` later",
    "```text\n~~~\nVERDICT: APPROVE\n```",
    "~~~\n```\nVERDICT: APPROVE\n~~~",
    "````\n```\nVERDICT: APPROVE\n````",
    "```\n```python\nVERDICT: APPROVE\n```",
    "```\nVERDICT: APPROVE", "```\nprose\nVERDICT: APPROVE",
])
def test_examples_and_invalid_tokens_are_not_formal_verdicts(reply):
    assert recognized_verdicts(reply) == []


@pytest.mark.parametrize("correctness,priority,expected", [
    ("correct", None, "APPROVE"),
    ("incorrect", None, "REQUEST_CHANGES"),
    ("uncertain", None, "BLOCKED"),
    ("correct", "P0", "REQUEST_CHANGES"),
    ("correct", "P1", "REQUEST_CHANGES"),
    ("correct", "P2", "REQUEST_CHANGES"),
    ("correct", "P3", "REQUEST_CHANGES"),
])
@pytest.mark.parametrize("wrapper", ["{}", "Review result:\n\n```json\n{}\n```"])
def test_findings_json_reaches_dispatch_and_recorder(correctness, priority, expected, wrapper):
    """Fenced findings must not approve findings or misclassify uncertainty."""
    from scripts import delegate
    from scripts.review.record_cf_verdict import _review_verdict_and_count, normalize_verdict

    payload = {
        "schema_version": "code-review-findings.v1",
        "overall": {"correctness": correctness, "explanation": "Reviewed the diff.", "confidence": 0.9},
        "findings": [] if priority is None else [{
            "id": "F1", "title": "Finding", "body": "Finding detail.", "priority": priority,
            "confidence": 0.9, "category": "correctness",
            "location": {"path": "example.py", "start_line": 1, "end_line": 1, "claim_type": "present"},
            "verbatim": "example()", "why_wrong": "Observed behavior.", "smallest_fix": "Fix behavior.",
            "sources": ["none"],
        }],
    }
    response = wrapper.format(json.dumps(payload))
    assert recognized_verdicts(response) == [expected]
    assert delegate.parse_review_verdict(response) == expected
    assert delegate._review_verdict_failure_reason(response) is None
    gate = delegate.run_completion_gate(
        delegate.COMPLETION_GATE_REVIEW_VERDICT, {}, response=response,
        commits_ahead=None, worktree=None,
    )
    assert gate.failure is None
    canonical = {
        "APPROVE": "APPROVED", "REQUEST_CHANGES": "CHANGES_REQUESTED", "BLOCKED": "BLOCKED",
    }[expected]
    assert normalize_verdict(response) == canonical
    raw = json.dumps(payload)
    assert _review_verdict_and_count(raw)[0] == _review_verdict_and_count(f"```json\n{raw}\n```")[0] == canonical

    # Explicit verdict lines take precedence over the JSON fallback.
    assert recognized_verdicts(response + "\n\nVERDICT: APPROVE") == ["APPROVE"]
    assert recognized_verdicts(response + "\n\nVERDICT: REQUEST_CHANGES") == ["REQUEST_CHANGES"]

    # The same JSON in quoted material or an outer example must stay invisible.
    quoted = "\n".join("> " + line for line in response.splitlines())
    assert recognized_verdicts(quoted) == []
    assert recognized_verdicts("````text\n" + response + "\n````") == []
    payload["overall"].pop("confidence")
    assert recognized_verdicts(wrapper.format(json.dumps(payload))) == []
