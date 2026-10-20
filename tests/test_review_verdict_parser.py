"""Shared formal verdict lines preserve dispatch's Markdown grammar (#9756)."""

from __future__ import annotations

import subprocess
import sys

import pytest

from scripts.review.verdict_parser import recognized_verdicts
from tests.test_verdict_parser import FROZEN_CONTAINER_CASES


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
    "```text\n~~~\nVERDICT: APPROVE\n```",
    "~~~\n```\nVERDICT: APPROVE\n~~~",
    "````\n```\nVERDICT: APPROVE\n````",
    "```\n```python\nVERDICT: APPROVE\n```",
    "```\nVERDICT: APPROVE", "```\nprose\nVERDICT: APPROVE",
])
def test_examples_and_invalid_tokens_are_not_formal_verdicts(reply):
    assert recognized_verdicts(reply) == []


def test_scanner_import_has_no_heavyweight_delegate_dependency():
    result = subprocess.run([
        sys.executable, "-c",
        "import sys; from scripts.review.verdict_parser import recognized_verdicts; "
        "assert recognized_verdicts('VERDICT: APPROVE') == ['APPROVE']; "
        "assert 'scripts.delegate' not in sys.modules and 'delegate' not in sys.modules; "
        "assert 'scripts.review.record_cf_verdict' not in sys.modules",
    ], capture_output=True, text=True, check=False, timeout=30)
    assert result.returncode == 0, result.stderr
