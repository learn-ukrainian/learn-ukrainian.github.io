"""Shared CommonMark fence syntax and caller-specific unclosed policy (#9672)."""

import pytest

from scripts.review.verdict_parser import _code_fence_spans, _without_code_fences, recognized_verdicts


@pytest.mark.parametrize("fence", ["```", "~~~"])
@pytest.mark.parametrize("indent", range(4))
def test_commonmark_scanner_reports_closed_and_unclosed_spans(fence, indent):
    lines = ["Context", " " * indent + fence + "markdown", "Example", "   " + fence + " \t", fence, "Tail"]
    assert list(_code_fence_spans(lines)) == [(1, 4, True), (4, 6, False)]
    text = "\n".join(lines)
    assert _without_code_fences(text, keep_unclosed=True) == "Context\n\n" + fence + "\nTail"
    assert _without_code_fences(text, keep_unclosed=False) == "Context\n\n\n"


@pytest.mark.parametrize(
    "opener,invalid_closer",
    [
        ("```", "~~~"), ("~~~", "```"),
        ("````", "```"), ("~~~~", "~~~"),
        ("```", "```python"), ("~~~", "~~~text"),
        ("```", "    ```"), ("~~~", "\t~~~"),
        ("```", "```\u00a0"), ("~~~", "~~~\u00a0"),
    ],
)
def test_commonmark_invalid_closer_stays_content_until_valid_close(opener, invalid_closer):
    lines = [opener, invalid_closer, "VERDICT: APPROVE", opener + " \t", "VERDICT: BLOCKED"]
    assert list(_code_fence_spans(lines)) == [(0, 4, True)]
    assert recognized_verdicts("\n".join(lines)) == ["BLOCKED"]
    assert list(_code_fence_spans(lines[:3])) == [(0, 3, False)]
    assert recognized_verdicts("\n".join(lines[:3])) == []


@pytest.mark.parametrize("opener", ["```info`", "    ```", "\t~~~", "- ```", "> ~~~", "``", "~~"])
def test_commonmark_non_openers_preserve_existing_top_level_behavior(opener):
    lines = [opener, "VERDICT: BLOCKED"]
    assert list(_code_fence_spans(lines)) == []
    assert recognized_verdicts("\n".join(lines)) == ["BLOCKED"]


def test_commonmark_tilde_info_can_contain_backticks():
    text = "~~~info`\nVERDICT: APPROVE\n~~~~\nVERDICT: REQUEST_CHANGES"
    assert recognized_verdicts(text) == ["REQUEST_CHANGES"]


def test_commonmark_preserves_non_fenced_crlf_text_and_eof_closer():
    text = "Context\r\n```\r\nVERDICT: APPROVE\r\n```\r\nVERDICT: BLOCKED"
    assert _without_code_fences(text, keep_unclosed=True) == "Context\r\n\nVERDICT: BLOCKED"
    assert recognized_verdicts(text) == ["BLOCKED"]
    assert recognized_verdicts("~~~\nVERDICT: APPROVE\n~~~") == []
    assert list(_code_fence_spans([])) == []
