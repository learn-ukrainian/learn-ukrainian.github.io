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


@pytest.mark.parametrize("fence", ["```", "~~~"])
@pytest.mark.parametrize("indent", [1, 2, 3])
def test_commonmark_indented_top_level_fence_allows_unindented_data(fence, indent):
    text = (
        "Review this example.\n"
        f"{' ' * indent}{fence}text\n"
        "Fix the parser. #8886\nVERDICT: APPROVE\n"
        f"{' ' * indent}{fence}\n"
        "VERDICT: BLOCKED\n"
    )
    assert _without_code_fences(text, keep_unclosed=True) == "Review this example.\n\nVERDICT: BLOCKED\n"
    assert recognized_verdicts(text) == ["BLOCKED"]


@pytest.mark.parametrize(
    "text",
    [
        "1. Old example:\n   ```py\n   x = 1\n2. Fix #8886.\n3. New example:\n   ```\n",
        "- Old example:\n  ~~~py\n  x = 1\n- Fix #8886.\n- New example:\n  ~~~\n",
        "- Old example:\n\n  ```py\n  x = 1\nFix #8886.\n  ```\n",
        "1. Old example:\n\n   ```py\n   x = 1\n\n2. Fix #8886.\n\n3. New example:\n   ```\n",
        "- Old example:\n  ```py\n  Fix #8886.\n  ```\n",
    ],
)
def test_commonmark_container_fences_stay_visible_to_safety_consumers(text):
    assert _without_code_fences(text, keep_unclosed=True) == text
    # Verdict extraction retains its conservative lexical suppression policy.
    assert recognized_verdicts(text.replace("Fix #8886.", "VERDICT: APPROVE")) == []


def test_commonmark_container_span_does_not_prevent_later_top_level_data_removal():
    text = "- Example:\n  ```\n  x = 1\n  ```\n\n```\nFix #8886.\n```\nOutside #9672.\n"
    assert _without_code_fences(text, keep_unclosed=True) == (
        "- Example:\n  ```\n  x = 1\n  ```\n\n\nOutside #9672.\n"
    )
