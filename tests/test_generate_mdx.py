"""Tests for generate_mdx.py — MDX generation utilities.

Covers:
- JSON/JSX escaping
- HTML to JSX conversion
- Frontmatter parsing
- Activity parsers (quiz, match-up, fill-in, true-false, unjumble, group-sort, anagram)

Issue: #783
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_mdx import (
    dump_json_for_jsx,
    escape_jsx,
    fix_html_for_jsx,
    parse_frontmatter,
    parse_quiz,
    parse_match_up,
    parse_fill_in,
    parse_true_false,
    parse_unjumble,
    parse_group_sort,
    parse_anagram,
)


# =============================================================================
# dump_json_for_jsx
# =============================================================================

class TestDumpJsonForJsx:
    def test_simple_dict(self):
        result = dump_json_for_jsx({"key": "value"})
        assert '"key"' in result
        assert '"value"' in result

    def test_escapes_backticks(self):
        result = dump_json_for_jsx({"text": "use `code` here"})
        assert "\\`" in result

    def test_escapes_template_interpolation(self):
        result = dump_json_for_jsx({"text": "${variable}"})
        assert "\\${" in result

    def test_preserves_unicode(self):
        result = dump_json_for_jsx({"word": "привіт"})
        assert "привіт" in result


# =============================================================================
# escape_jsx
# =============================================================================

class TestEscapeJsx:
    def test_empty_string(self):
        assert escape_jsx("") == ""

    def test_plain_text(self):
        assert escape_jsx("hello world") == "hello world"

    def test_escapes_backticks(self):
        assert "\\`" in escape_jsx("use `code`")

    def test_escapes_quotes(self):
        assert "&quot;" in escape_jsx('say "hello"')

    def test_escapes_angle_brackets(self):
        assert "&lt;" in escape_jsx("<tag>")
        assert "&gt;" in escape_jsx("<tag>")

    def test_escapes_template_interpolation(self):
        assert "\\${" in escape_jsx("${var}")

    def test_handles_non_string_input(self):
        assert escape_jsx(42) == "42"

    def test_escapes_backslashes(self):
        assert "\\\\" in escape_jsx("path\\to")


# =============================================================================
# fix_html_for_jsx
# =============================================================================

class TestFixHtmlForJsx:
    def test_br_tag(self):
        assert fix_html_for_jsx("<br>") == "<br />"

    def test_br_self_closing(self):
        assert fix_html_for_jsx("<br/>") == "<br />"

    def test_hr_tag(self):
        assert fix_html_for_jsx("<hr>") == "<hr />"

    def test_img_tag(self):
        result = fix_html_for_jsx('<img src="test.png">')
        assert result.endswith("/>")

    def test_img_already_self_closing(self):
        result = fix_html_for_jsx('<img src="test.png" />')
        assert result == '<img src="test.png" />'

    def test_preserves_other_html(self):
        assert fix_html_for_jsx("<div>text</div>") == "<div>text</div>"


# =============================================================================
# parse_frontmatter
# =============================================================================

class TestParseFrontmatter:
    def test_valid_frontmatter(self):
        content = "---\ntitle: Test\nlevel: A1\n---\nBody text here"
        fm, body = parse_frontmatter(content)
        assert fm["title"] == "Test"
        assert fm["level"] == "A1"
        assert body.strip() == "Body text here"

    def test_no_frontmatter(self):
        content = "Just body text"
        fm, body = parse_frontmatter(content)
        assert fm == {}
        assert body == "Just body text"

    def test_unclosed_frontmatter(self):
        content = "---\ntitle: Test\nBody text"
        fm, body = parse_frontmatter(content)
        assert fm == {}

    def test_empty_frontmatter(self):
        content = "---\n---\nBody"
        fm, body = parse_frontmatter(content)
        assert fm == {}
        assert body.strip() == "Body"


# =============================================================================
# parse_quiz
# =============================================================================

class TestParseQuiz:
    def test_numbered_format(self):
        content = """1. What is "привіт"?
- [x] Hello
- [ ] Goodbye
- [ ] Thank you

2. What is "дякую"?
- [ ] Hello
- [x] Thank you
- [ ] Goodbye"""
        questions = parse_quiz(content)
        assert len(questions) == 2
        assert questions[0].question == 'What is "привіт"?'
        assert len(questions[0].options) == 3
        assert questions[0].options[0]["correct"] is True
        assert questions[0].options[1]["correct"] is False

    def test_separator_format(self):
        content = """What is "так"?
- [x] Yes
- [ ] No

---

What is "ні"?
- [ ] Yes
- [x] No"""
        questions = parse_quiz(content)
        assert len(questions) == 2

    def test_empty_content(self):
        assert parse_quiz("") == []


# =============================================================================
# parse_match_up
# =============================================================================

class TestParseMatchUp:
    def test_double_colon_format(self):
        content = """- привіт :: hello
- дякую :: thank you
- так :: yes"""
        pairs = parse_match_up(content)
        assert len(pairs) == 3
        assert pairs[0].left == "привіт"
        assert pairs[0].right == "hello"

    def test_table_format(self):
        content = """| Ukrainian | English |
|-----------|---------|
| привіт | hello |
| так | yes |"""
        pairs = parse_match_up(content)
        assert len(pairs) == 2
        assert pairs[0].left == "привіт"
        assert pairs[0].right == "hello"

    def test_empty(self):
        assert parse_match_up("nothing here") == []


# =============================================================================
# parse_fill_in
# =============================================================================

class TestParseFillIn:
    def test_basic_fill_in(self):
        content = """1. Я ___ студент.
> [!answer] є
> [!options] є | маю | буду

2. Він ___ книгу.
> [!answer] читає
> [!options] читає | пише | малює"""
        items = parse_fill_in(content)
        assert len(items) == 2
        assert items[0].sentence == "Я ___ студент."
        assert items[0].answer == "є"
        assert len(items[0].options) == 3

    def test_empty(self):
        assert parse_fill_in("") == []


# =============================================================================
# parse_true_false
# =============================================================================

class TestParseTrueFalse:
    def test_basic_true_false(self):
        content = """- [x] "Привіт" means "hello"
> This is the standard greeting
- [ ] "Так" means "no"
> "Так" means "yes" """
        items = parse_true_false(content)
        assert len(items) == 2
        assert items[0].is_true is True
        assert items[0].explanation.strip() != ""
        assert items[1].is_true is False

    def test_without_explanations(self):
        content = """- [x] Statement one
- [ ] Statement two"""
        items = parse_true_false(content)
        assert len(items) == 2
        assert items[0].explanation == ""


# =============================================================================
# parse_unjumble
# =============================================================================

class TestParseUnjumble:
    def test_basic_unjumble(self):
        content = """1. студент Я є
> [!answer] Я є студент

2. книгу читає Він
> [!answer] Він читає книгу"""
        items = parse_unjumble(content)
        assert len(items) == 2
        assert items[0].jumbled == "студент Я є"
        assert items[0].answer == "Я є студент"


# =============================================================================
# parse_group_sort
# =============================================================================

class TestParseGroupSort:
    def test_basic_group_sort(self):
        content = """### Masculine
- кіт
- стіл
- дім

### Feminine
- книга
- вода"""
        result = parse_group_sort(content)
        assert "Masculine" in result.groups
        assert "Feminine" in result.groups
        assert len(result.groups["Masculine"]) == 3
        assert len(result.groups["Feminine"]) == 2
        assert "кіт" in result.groups["Masculine"]


# =============================================================================
# parse_anagram
# =============================================================================

class TestParseAnagram:
    def test_basic_anagram(self):
        content = """1. тівпир
> [!answer] привіт
> [!hint] A greeting

2. юкядя
> [!answer] дякую"""
        items = parse_anagram(content)
        assert len(items) == 2
        assert items[0].scrambled == "тівпир"
        assert items[0].answer == "привіт"
        assert items[0].hint == "A greeting"
        assert items[1].hint == ""
