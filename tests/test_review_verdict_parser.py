"""Shared formal verdict lines preserve dispatch's Markdown grammar (#9756)."""

from __future__ import annotations

import subprocess
import sys

import pytest

from scripts.review.verdict_parser import recognized_verdicts


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
