"""Tests for generate_mdx/parsers.py — pure string parsers for activity content."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_mdx.parsers import (
    has_morpheme_patterns,
    parse_cloze,
    parse_error_correction,
    parse_fill_in,
    parse_group_sort,
    parse_mark_the_words,
    parse_match_up,
    parse_quiz,
    parse_select,
    parse_translate,
    parse_true_false,
    parse_unjumble,
)


class TestParseQuiz:
    def test_numbered_format(self):
        content = (
            "1. Що означає слово «кіт»?\n"
            "- [ ] dog\n"
            "- [x] cat\n"
            "- [ ] fish\n"
            "- [ ] bird\n"
        )
        questions = parse_quiz(content)
        assert len(questions) >= 1
        correct = [o for o in questions[0].options if o.get("correct")]
        assert len(correct) >= 1

    def test_separator_format(self):
        content = (
            "Яка столиця України?\n"
            "- [ ] Львів\n"
            "- [x] Київ\n"
            "- [ ] Одеса\n"
            "\n---\n\n"
            "Яке місто найбільше?\n"
            "- [x] Київ\n"
            "- [ ] Харків\n"
            "- [ ] Дніпро\n"
        )
        questions = parse_quiz(content)
        assert len(questions) == 2

    def test_empty_content(self):
        assert parse_quiz("") == []
        assert parse_quiz("   \n   ") == []


class TestParseMatchUp:
    def test_double_colon_format(self):
        content = "кіт :: cat\nсобака :: dog\nптах :: bird\n"
        pairs = parse_match_up(content)
        assert len(pairs) == 3
        assert pairs[0].left == "кіт"
        assert pairs[0].right == "cat"

    def test_table_format(self):
        content = "| Ukrainian | English |\n|---|---|\n| кіт | cat |\n| собака | dog |\n"
        pairs = parse_match_up(content)
        assert len(pairs) == 2

    def test_empty_content(self):
        assert parse_match_up("") == []


class TestParseFillIn:
    def test_numbered_with_answer_callout(self):
        content = (
            "1. Я ___ вдома.\n"
            "> [!answer] був\n"
            "2. Він ___ у школі.\n"
            "> [!answer] був\n"
        )
        items = parse_fill_in(content)
        assert len(items) == 2
        assert items[0].answer == "був"

    def test_empty_content(self):
        assert parse_fill_in("") == []


class TestParseTrueFalse:
    def test_basic_statements(self):
        content = "- [x] Київ — столиця України.\n- [ ] Львів — столиця України.\n"
        items = parse_true_false(content)
        assert len(items) == 2
        assert items[0].is_true is True
        assert items[1].is_true is False

    def test_with_explanation(self):
        content = "- [x] Київ — столиця.\n> Правильно!\n- [ ] Львів — столиця.\n> Неправильно!\n"
        items = parse_true_false(content)
        assert len(items) == 2
        assert items[0].explanation == "Правильно!"

    def test_empty_content(self):
        assert parse_true_false("") == []


class TestParseUnjumble:
    def test_numbered_with_answer(self):
        content = (
            "1. люблю / я / Україну\n"
            "> [!answer] Я люблю Україну\n"
        )
        items = parse_unjumble(content)
        assert len(items) == 1
        assert "/" in items[0].jumbled or " " in items[0].jumbled
        assert items[0].answer == "Я люблю Україну"

    def test_empty_content(self):
        assert parse_unjumble("") == []


class TestParseGroupSort:
    def test_basic_groups(self):
        content = (
            "### Їжа\n"
            "- хліб\n"
            "- молоко\n"
            "\n"
            "### Напої\n"
            "- вода\n"
            "- сік\n"
        )
        data = parse_group_sort(content)
        assert len(data.groups) == 2
        assert "Їжа" in data.groups
        assert data.groups["Їжа"] == ["хліб", "молоко"]

    def test_empty_content(self):
        data = parse_group_sort("")
        assert len(data.groups) == 0


class TestParseCloze:
    def test_inline_format(self):
        content = (
            "Я [___:1] Україну. Ми [___:2] в Києві.\n\n"
            "1. люблю | кохаю | хочу\n"
            "> [!answer] люблю\n"
            "2. живемо | ходимо | їмо\n"
            "> [!answer] живемо\n"
        )
        data = parse_cloze(content)
        assert len(data.blanks) == 2

    def test_no_blanks(self):
        data = parse_cloze("No blanks here.")
        assert len(data.blanks) == 0


class TestParseSelect:
    def test_numbered_select(self):
        content = (
            "1. Оберіть правильне слово:\n"
            "- [ ] кот\n"
            "- [x] кіт\n"
            "- [ ] кат\n"
        )
        questions = parse_select(content)
        assert len(questions) >= 1

    def test_empty_content(self):
        assert parse_select("") == []


class TestParseTranslate:
    def test_numbered_translate(self):
        content = (
            "1. Hello\n"
            "- [ ] Привет\n"
            "- [x] Привіт\n"
            "- [ ] Вітаю\n"
        )
        items = parse_translate(content)
        assert len(items) >= 1

    def test_empty_content(self):
        assert parse_translate("") == []


class TestParseMarkTheWords:
    def test_marked_words(self):
        content = "Я [люблю](correct) Україну і [живу](correct) в Києві."
        items = parse_mark_the_words(content)
        assert len(items) >= 1
        assert "люблю" in items[0].correctWords
        assert "живу" in items[0].correctWords

    def test_empty_content(self):
        assert parse_mark_the_words("") == []


class TestParseErrorCorrection:
    def test_numbered_format(self):
        content = (
            "1. Я ходив в магазін.\n"
            "> [!error] в\n"
            "> [!correct] до\n"
        )
        items = parse_error_correction(content)
        assert len(items) >= 1

    def test_empty_content(self):
        assert parse_error_correction("") == []


class TestHasMorphemePatterns:
    def test_prefix_pattern(self):
        # *prefix*rest where Cyrillic touches asterisk
        assert has_morpheme_patterns("*при*йшов") is True

    def test_suffix_pattern(self):
        assert has_morpheme_patterns("чит*ач*") is True

    def test_mark_the_words_not_matched(self):
        # space *word* space = mark-the-words, NOT morpheme
        assert has_morpheme_patterns(" *другові* ") is False

    def test_without_morphemes(self):
        assert has_morpheme_patterns("just a regular sentence") is False

    def test_empty(self):
        assert has_morpheme_patterns("") is False
