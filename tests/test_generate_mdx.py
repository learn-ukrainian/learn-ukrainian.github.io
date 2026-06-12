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
    convert_bad_form_markers,
    convert_callouts,
    dump_json_for_jsx,
    escape_jsx,
    fix_html_for_jsx,
    generate_mdx,
    normalize_mdx,
    parse_anagram,
    parse_cloze,
    parse_error_correction,
    parse_fill_in,
    parse_frontmatter,
    parse_group_sort,
    parse_match_up,
    parse_quiz,
    parse_translate,
    parse_true_false,
    parse_unjumble,
)
from yaml_activities import ActivityParser

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
        fm, _body = parse_frontmatter(content)
        assert fm == {}

    def test_empty_frontmatter(self):
        content = "---\n---\nBody"
        fm, body = parse_frontmatter(content)
        assert fm == {}
        assert body.strip() == "Body"


def test_v7_tab3_cross_refs_inline_activities_and_keeps_workbook_only(tmp_path):
    activities_yaml = tmp_path / "activities.yaml"
    activities_yaml.write_text(
        """
version: "1.0"
module: inline-aggregate
level: a1
inline:
  - id: act-1
    type: quiz
    title: act-1 inline greeting
    items:
      - question: Choose hello.
        options: ["привіт", "дякую"]
        answer: "привіт"
  - id: act-2
    type: quiz
    title: act-2 inline thanks
    items:
      - question: Choose thanks.
        options: ["привіт", "дякую"]
        answer: "дякую"
workbook:
  - id: act-3
    type: quiz
    title: act-3 workbook yes
    items:
      - question: Choose yes.
        options: ["так", "ні"]
        answer: "так"
  - id: act-4
    type: quiz
    title: act-4 workbook no
    items:
      - question: Choose no.
        options: ["так", "ні"]
        answer: "ні"
""",
        encoding="utf-8",
    )
    activities = ActivityParser().parse(activities_yaml)
    md_content = """---
title: Inline Aggregate
subtitle: Test
---
# Inline Aggregate

## Section One

Practice here.

<!-- INJECT_ACTIVITY: act-1 -->

## Section Two

Practice there.

<!-- INJECT_ACTIVITY: act-2 -->
"""

    mdx = generate_mdx(md_content, 1, yaml_activities=activities, level="a1")
    lesson_tab = mdx.split('<TabItem label="Vocabulary">')[0]
    tab3 = mdx.split('<TabItem label="Activities">', 1)[1].split("</TabItem>", 1)[0]

    assert "INJECT_ACTIVITY" not in lesson_tab
    assert "act-1 inline greeting" in lesson_tab
    assert "act-2 inline thanks" in lesson_tab

    assert "### act-1 inline greeting\n\n*(see lesson, §Section One)*" in tab3
    assert "### act-2 inline thanks\n\n*(see lesson, §Section Two)*" in tab3
    assert "### act-3 workbook yes\n\n<Quiz" in tab3
    assert "### act-4 workbook no\n\n<Quiz" in tab3
    assert "*(see lesson)*" not in tab3
    assert tab3.count("<Quiz") == 2


def test_v7_seminar_tabs_force_ukrainian_labels(tmp_path):
    activities_yaml = tmp_path / "activities.yaml"
    activities_yaml.write_text("[]\n", encoding="utf-8")
    activities = ActivityParser().parse(activities_yaml)
    md_content = """---
title: Seminar Labels
subtitle: Test
---
# Seminar Labels

## Розділ

Текст.
"""

    folk_mdx = generate_mdx(md_content, 1, yaml_activities=activities, level="folk")
    a1_mdx = generate_mdx(md_content, 1, yaml_activities=activities, level="a1")

    assert '<TabItem label="Урок">' in folk_mdx
    assert '<TabItem label="Словник">' in folk_mdx
    assert '<TabItem label="Вправи">' in folk_mdx
    assert '<TabItem label="Ресурси">' in folk_mdx
    assert '<TabItem label="Lesson">' in a1_mdx
    assert '<TabItem label="Vocabulary">' in a1_mdx
    assert '<TabItem label="Activities">' in a1_mdx
    assert '<TabItem label="Resources">' in a1_mdx


def test_v7_seminar_tab3_inline_cross_refs_use_ukrainian(tmp_path):
    activities_yaml = tmp_path / "activities.yaml"
    activities_yaml.write_text(
        """
- id: act-1
  type: quiz
  title: Перевірка понять
  items:
    - question: Оберіть поняття.
      options: [обряд, дата]
      answer: обряд
- id: act-2
  type: quiz
  title: Робоча вправа
  items:
    - question: Оберіть слово.
      options: [мотив, помилка]
      answer: мотив
""",
        encoding="utf-8",
    )
    activities = ActivityParser().parse(activities_yaml)
    md_content = """---
title: Семінар
subtitle: Test
---
# Семінар

## Постановка проблеми

Текст.

<!-- INJECT_ACTIVITY: act-1 -->
"""

    mdx = generate_mdx(md_content, 1, yaml_activities=activities, level="folk")
    tab3 = mdx.split('<TabItem label="Вправи">', 1)[1].split("</TabItem>", 1)[0]

    assert "### Перевірка понять\n\n*(див. урок, §Постановка проблеми)*" in tab3
    assert "### Робоча вправа\n\n<Quiz" in tab3
    assert tab3.count("<Quiz") == 1


def test_a2_2_preview_tabs_force_ukrainian_zoshyt_labels(tmp_path):
    activities_yaml = tmp_path / "activities.yaml"
    activities_yaml.write_text("[]\n", encoding="utf-8")
    activities = ActivityParser().parse(activities_yaml)
    md_content = """---
title: A2.2 Labels
subtitle: Test
---
# A2.2 Labels

## Розділ

Текст.
"""

    a2_bridge_mdx = generate_mdx(md_content, 1, yaml_activities=activities, level="a2")
    a2_2_mdx = generate_mdx(md_content, 9, yaml_activities=activities, level="a2")

    assert '<TabItem label="Lesson">' in a2_bridge_mdx
    assert '<TabItem label="Activities">' in a2_bridge_mdx
    assert '<TabItem label="Урок">' in a2_2_mdx
    assert '<TabItem label="Словник">' in a2_2_mdx
    assert '<TabItem label="Зошит">' in a2_2_mdx
    assert '<TabItem label="Ресурси">' in a2_2_mdx


def test_b1_tabs_force_ukrainian_labels_from_m1(tmp_path):
    activities_yaml = tmp_path / "activities.yaml"
    activities_yaml.write_text("[]\n", encoding="utf-8")
    activities = ActivityParser().parse(activities_yaml)
    md_content = """---
title: B1 Labels
subtitle: Test
---
# B1 Labels

## Розділ

Текст.
"""

    mdx = generate_mdx(md_content, 1, yaml_activities=activities, level="b1")

    assert '<TabItem label="Урок">' in mdx
    assert '<TabItem label="Словник">' in mdx
    assert '<TabItem label="Вправи">' in mdx
    assert '<TabItem label="Ресурси">' in mdx
    assert '<TabItem label="Lesson">' not in mdx


def test_generated_tabs_include_hash_target_sync_script():
    md_content = """---
title: Hash Tab Test
subtitle: Test
---
# Hash Tab Test

Lesson body.
"""

    mdx = generate_mdx(md_content, 1, level="a1")

    assert "import HashTabSync from '@site/src/components/HashTabSync';" in mdx
    assert "<HashTabSync />" in mdx


def test_v7_tab3_omits_missing_id_duplicate_of_inline_activity(tmp_path):
    activities_yaml = tmp_path / "activities.yaml"
    activities_yaml.write_text(
        """
- id: act-1
  type: fill-in
  title: Inline fill duplicate
  items:
    - sentence: Я ___ о сьомій.
      answer: прокидаюся
      options: [прокидаюся, снідаю]
- type: fill-in
  title: Inline fill duplicate
  items:
    - sentence: Я ___ о сьомій.
      answer: прокидаюся
      options: [прокидаюся, снідаю]
- id: act-2
  type: quiz
  title: Workbook-only quiz
  items:
    - question: Choose breakfast.
      options: [сніданок, ранок]
      answer: сніданок
""",
        encoding="utf-8",
    )
    activities = ActivityParser().parse(activities_yaml)
    md_content = """---
title: Missing ID Duplicate
subtitle: Test
---
# Missing ID Duplicate

Practice here.

<!-- INJECT_ACTIVITY: act-1 -->
"""

    mdx = generate_mdx(md_content, 1, yaml_activities=activities, level="a1")
    lesson_tab = mdx.split('<TabItem label="Vocabulary">')[0]
    tab3 = mdx.split('<TabItem label="Activities">', 1)[1].split("</TabItem>", 1)[0]

    assert "Inline fill duplicate" in lesson_tab
    assert "<FillIn" in lesson_tab
    assert "### Inline fill duplicate\n\n*(see lesson tab)*" in tab3
    assert tab3.count("Inline fill duplicate") == 1
    assert "<FillIn" not in tab3
    assert "Workbook-only quiz" in tab3
    assert "<Quiz" in tab3


def test_v7_tab3_all_inline_activities_renders_empty_workbook_message(tmp_path):
    activities_yaml = tmp_path / "activities.yaml"
    activities_yaml.write_text(
        """
- id: act-1
  type: quiz
  title: Inline one
  items:
    - question: Choose hello.
      options: [привіт, дякую]
      answer: привіт
- id: act-2
  type: quiz
  title: Inline two
  items:
    - question: Choose thanks.
      options: [привіт, дякую]
      answer: дякую
""",
        encoding="utf-8",
    )
    activities = ActivityParser().parse(activities_yaml)
    md_content = """---
title: All Inline
subtitle: Test
---
# All Inline

<!-- INJECT_ACTIVITY: act-1 -->

<!-- INJECT_ACTIVITY: act-2 -->
"""

    mdx = generate_mdx(md_content, 1, yaml_activities=activities, level="a1")
    tab3 = mdx.split('<TabItem label="Activities">', 1)[1].split("</TabItem>", 1)[0]

    assert "No workbook activities for this module; see the Lesson tab." not in tab3
    assert "### Inline one\n\n*(see lesson tab)*" in tab3
    assert "### Inline two\n\n*(see lesson tab)*" in tab3
    assert "<Quiz" not in tab3
    assert "*(see lesson)*" not in tab3


def test_error_correction_renders_structured_items_for_client_interactivity(tmp_path):
    activities_yaml = tmp_path / "activities.yaml"
    activities_yaml.write_text(
        """
- id: act-1
  type: error-correction
  title: Fix identity trap
  instruction: Choose the safer sentence.
  items:
    - sentence: Я є студент.
      error: є
      correction: Я студент.
      options:
        - Я студент.
        - Я є студент.
      explanation: Present identity usually omits є.
""",
        encoding="utf-8",
    )
    activities = ActivityParser().parse(activities_yaml)
    md_content = """---
title: Error Correction
subtitle: Test
---
# Error Correction

<!-- INJECT_ACTIVITY: act-1 -->
"""

    mdx = generate_mdx(md_content, 1, yaml_activities=activities, level="a1")

    assert "<ErrorCorrection client:only='react'" in mdx
    assert "items={JSON.parse(`" in mdx
    assert "<ErrorCorrectionItem" not in mdx
    assert '"errorWord": "є"' in mdx


def test_v7_inline_activity_missing_id_reference_fails_loudly(tmp_path):
    activities_yaml = tmp_path / "activities.yaml"
    activities_yaml.write_text(
        """
- id: act-1
  type: quiz
  title: Existing activity
  items:
    - question: Choose hello.
      options: [привіт, дякую]
      answer: привіт
""",
        encoding="utf-8",
    )
    activities = ActivityParser().parse(activities_yaml)
    md_content = """---
title: Broken Marker
subtitle: Test
---
# Broken Marker

<!-- INJECT_ACTIVITY: act-404 -->
"""

    with pytest.raises(ValueError, match="Unresolved INJECT_ACTIVITY id: act-404"):
        generate_mdx(md_content, 1, yaml_activities=activities, level="a1")


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


# =============================================================================
# parse_error_correction
# =============================================================================

class TestParseErrorCorrection:
    def test_basic_error_correction(self):
        content = """1. Я читаю книгу кожний день.
> [!error] кожний
> [!answer] кожного
> [!options] кожного | кожний | кожному
> [!explanation] Genitive case needed here"""
        items = parse_error_correction(content)
        assert len(items) == 1
        assert items[0].errorWord == "кожний"
        assert items[0].correctForm == "кожного"
        assert len(items[0].options) >= 2
        assert items[0].explanation != ""

    def test_multiple_items(self):
        content = """1. Він ходить у школа.
> [!error] школа
> [!answer] школу
> [!options] школу | школа | школі

2. Вона купила нова сукня.
> [!error] нова
> [!answer] нову
> [!options] нову | нова | нової"""
        items = parse_error_correction(content)
        assert len(items) == 2

    def test_empty_content(self):
        assert parse_error_correction("") == []

    def test_correct_in_options(self):
        content = """1. Sentence with помилка.
> [!error] помилка
> [!answer] помилку
> [!options] помилку | помилка | помилці"""
        items = parse_error_correction(content)
        assert "помилку" in [o["text"] if isinstance(o, dict) else o for o in items[0].options]


# =============================================================================
# parse_cloze
# =============================================================================

class TestParseCloze:
    def test_basic_cloze(self):
        content = """Я ___(1) студент. Він ___(2) книгу.

1. є | маю | буду
> [!answer] є

2. читає | пише | малює
> [!answer] читає"""
        result = parse_cloze(content)
        assert result.passage != ""
        assert len(result.blanks) == 2
        assert result.blanks[0]["answer"] == "є"
        assert result.blanks[1]["answer"] == "читає"

    def test_empty_content(self):
        result = parse_cloze("")
        assert result.passage == ""
        assert result.blanks == []

    def test_passage_preserved(self):
        content = """Україна — красива країна ___(1).

1. велика | мала | гарна
> [!answer] велика"""
        result = parse_cloze(content)
        assert "Україна" in result.passage


# =============================================================================
# parse_translate
# =============================================================================

class TestParseTranslate:
    def test_checkbox_format(self):
        content = """1. Translate "hello"
- [x] Привіт
- [ ] Дякую
- [ ] Так"""
        items = parse_translate(content)
        assert len(items) == 1
        assert len(items[0].options) == 3
        assert items[0].options[0]["correct"] is True
        assert items[0].options[1]["correct"] is False

    def test_callout_format(self):
        content = """1. Translate "thank you"
> [!answer] Дякую
> [!options] Дякую | Привіт | Так"""
        items = parse_translate(content)
        assert len(items) == 1
        assert items[0].options[0]["correct"] is True

    def test_multiple_items(self):
        content = """1. Translate "yes"
- [x] Так
- [ ] Ні

2. Translate "no"
- [x] Ні
- [ ] Так"""
        items = parse_translate(content)
        assert len(items) == 2

    def test_empty(self):
        assert parse_translate("") == []


# =============================================================================
# convert_bad_form_markers
# =============================================================================

class TestConvertBadFormMarkers:
    def test_prose_case(self):
        content = "Avoid using <!-- bad -->завтрак<!-- /bad --> in Ukrainian."
        result = convert_bad_form_markers(content)
        assert result == "Avoid using <del>завтрак</del> in Ukrainian."

    def test_whitespace_variant(self):
        content = "Avoid using <!--  bad  -->завтрак<!--  /bad  -->."
        result = convert_bad_form_markers(content)
        assert result == "Avoid using <del>завтрак</del>."

    def test_strip_only(self):
        content = '{"label": "Not <!-- bad -->завтрак<!-- /bad -->"}'
        result = convert_bad_form_markers(content, strip_only=True)
        assert result == '{"label": "Not завтрак"}'

    def test_orphan_marker_stripped(self):
        content = "Some text <!-- bad --> orphaned marker."
        result = convert_bad_form_markers(content)
        assert result == "Some text  orphaned marker."
        content2 = "Some text <!-- /bad --> orphaned end marker."
        result2 = convert_bad_form_markers(content2)
        assert result2 == "Some text  orphaned end marker."

# =============================================================================
# convert_callouts
# =============================================================================

class TestConvertCallouts:
    def test_note_callout(self):
        content = "> [!NOTE]\n> This is a note."
        result = convert_callouts(content)
        assert ":::" in result
        assert "note" in result.lower()

    def test_tip_callout(self):
        content = "> [!TIP]\n> Helpful tip here."
        result = convert_callouts(content)
        assert ":::" in result
        assert "tip" in result.lower()

    def test_warning_callout(self):
        content = "> [!WARNING]\n> Be careful."
        result = convert_callouts(content)
        assert ":::" in result

    def test_preserves_non_callout_content(self):
        content = "Regular paragraph.\n\nAnother paragraph."
        result = convert_callouts(content)
        assert "Regular paragraph." in result
        assert "Another paragraph." in result

    def test_empty_string(self):
        result = convert_callouts("")
        assert result == ""

    def test_multiline_callout(self):
        content = "> [!NOTE]\n> Line 1\n> Line 2\n> Line 3"
        result = convert_callouts(content)
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result


# =============================================================================
# normalize_mdx
# =============================================================================

class TestNormalizeMdx:
    def test_strips_trailing_whitespace(self):
        result = normalize_mdx("hello   \nworld  \n")
        assert "   \n" not in result
        assert "  \n" not in result

    def test_normalizes_list_markers(self):
        result = normalize_mdx("* item 1\n* item 2\n")
        assert "- item 1" in result
        assert "- item 2" in result

    def test_collapses_excessive_newlines(self):
        result = normalize_mdx("Line 1\n\n\n\nLine 2\n")
        assert "\n\n\n" not in result
        assert "Line 1" in result
        assert "Line 2" in result

    def test_ensures_trailing_newline(self):
        result = normalize_mdx("content")
        assert result.endswith("\n")

    def test_blank_lines_around_headings(self):
        result = normalize_mdx("text\n## Heading\nmore text\n")
        # Should have blank line before heading
        lines = result.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("## ") and i > 0:
                    assert lines[i - 1].strip() == "", f"Expected blank line before heading, got '{lines[i-1]}'"

    def test_preserves_code_blocks(self):
        result = normalize_mdx("```\n* not a list\n  trailing spaces   \n```\n")
        assert "* not a list" in result

    def test_empty_string(self):
        result = normalize_mdx("")
        assert result == "\n" or result == ""

    def test_emphasis_normalization(self):
        result = normalize_mdx("Use _italic_ text\n")
        assert "*italic*" in result or "_italic_" in result


# =============================================================================
# YouTube embed conversion
# =============================================================================

from generate_mdx.resources import embed_youtube_video_links


class TestEmbedYoutubeVideoLinks:
    """Test all YouTube link formats are converted to <YouTubeVideo> components."""

    def test_markdown_link(self):
        body = '[Watch this](https://www.youtube.com/watch?v=hvB3VpcR3ZE)'
        result = embed_youtube_video_links(body)
        assert '<YouTubeVideo' in result
        assert 'url="https://www.youtube.com/watch?v=hvB3VpcR3ZE"' in result
        assert 'label="Watch this"' in result

    def test_plain_bullet_url(self):
        body = '- Літера А: https://www.youtube.com/watch?v=hvB3VpcR3ZE'
        result = embed_youtube_video_links(body)
        assert '<YouTubeVideo' in result
        assert 'url="https://www.youtube.com/watch?v=hvB3VpcR3ZE"' in result
        assert 'label="Літера А"' in result

    def test_multiple_plain_bullet_urls(self):
        body = (
            '- Літера А: https://www.youtube.com/watch?v=hvB3VpcR3ZE\n'
            '- Літера О: https://www.youtube.com/watch?v=gJFxRIPRZbI\n'
        )
        result = embed_youtube_video_links(body)
        assert result.count('<YouTubeVideo') == 2
        assert 'label="Літера А"' in result
        assert 'label="Літера О"' in result

    def test_jinja_template(self):
        body = '{% youtubeVideo "https://www.youtube.com/watch?v=hvB3VpcR3ZE" %}'
        result = embed_youtube_video_links(body)
        assert '<YouTubeVideo' in result

    def test_jinja_id_template(self):
        body = '{% youtubeVideo id="hvB3VpcR3ZE" %}'
        result = embed_youtube_video_links(body)
        assert '<YouTubeVideo' in result

    def test_playlist_url_not_embedded(self):
        body = '- Full Playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3ml'
        result = embed_youtube_video_links(body)
        assert '<YouTubeVideo' not in result

    def test_bare_url_on_line(self):
        body = 'https://www.youtube.com/watch?v=hvB3VpcR3ZE'
        result = embed_youtube_video_links(body)
        assert '<YouTubeVideo' in result
        assert 'label="Video"' in result

    def test_non_youtube_url_unchanged(self):
        body = '- Some link: https://www.example.com/watch?v=hvB3VpcR3ZE'
        result = embed_youtube_video_links(body)
        assert '<YouTubeVideo' not in result

    def test_url_with_params(self):
        body = '- Video: https://youtu.be/hvB3VpcR3ZE?si=xyz123'
        result = embed_youtube_video_links(body)
        assert '<YouTubeVideo' in result
        assert '?si=xyz123' in result

    def test_url_with_timestamp(self):
        body = '- Video: https://www.youtube.com/watch?v=hvB3VpcR3ZE&t=42s'
        result = embed_youtube_video_links(body)
        assert '<YouTubeVideo' in result

    def test_youtu_be_short_url(self):
        body = '- Short: https://youtu.be/hvB3VpcR3ZE'
        result = embed_youtube_video_links(body)
        assert '<YouTubeVideo' in result
