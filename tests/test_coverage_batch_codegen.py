"""Tests for batch dispatcher and codegen modules.

Covers:
  1. batch_dispatcher_helpers.py — track scanning, deps, priority, state mgmt
  2. batch_dispatcher.py — BatchDispatcher class methods
  3. generate_plan_markdown.py — YAML plan → markdown rendering
  4. generate_json.py — module → JSON conversion
  5. validate_direct.py — l2-uk-direct validation logic
  6. md_to_yaml.py — markdown → YAML activity conversion
  7. generate_mdx_direct_content.py — MDX content rendering
  8. generate_mdx_direct_renderers.py — activity renderers
"""

import json
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Ensure scripts/ is importable
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


# ═══════════════════════════════════════════════════════════════════════════════
# Module 8: generate_mdx_direct_renderers.py (no heavy deps)
# ═══════════════════════════════════════════════════════════════════════════════

from generate_mdx_direct_renderers import (
    dump_json_for_jsx,
    escape_jsx_string,
    render_activity,
)


class TestDumpJsonForJsx:
    def test_basic_dict(self):
        result = dump_json_for_jsx({"key": "value"})
        assert '"key"' in result
        assert '"value"' in result

    def test_escapes_backticks(self):
        result = dump_json_for_jsx({"text": "hello `world`"})
        assert "\\`" in result

    def test_escapes_dollar_brace(self):
        result = dump_json_for_jsx({"text": "cost ${5}"})
        assert "\\${" in result

    def test_unicode_preserved(self):
        result = dump_json_for_jsx({"uk": "привіт"})
        assert "привіт" in result

    def test_empty_dict(self):
        result = dump_json_for_jsx({})
        assert result.strip() == "{}"

    def test_list(self):
        result = dump_json_for_jsx([1, 2, 3])
        assert "1" in result
        assert "3" in result

    def test_nested(self):
        result = dump_json_for_jsx({"a": {"b": "c"}})
        assert '"b"' in result


class TestEscapeJsxString:
    def test_ampersand(self):
        assert escape_jsx_string("A & B") == "A &amp; B"

    def test_double_quotes(self):
        assert escape_jsx_string('say "hi"') == "say &quot;hi&quot;"

    def test_angle_brackets(self):
        assert escape_jsx_string("<div>") == "&lt;div&gt;"

    def test_no_change(self):
        assert escape_jsx_string("hello") == "hello"

    def test_combined(self):
        assert escape_jsx_string('a & "b" <c>') == 'a &amp; &quot;b&quot; &lt;c&gt;'


class TestRenderActivity:
    def test_unknown_type(self):
        result = render_activity({"type": "unknown_xyz"})
        assert "Unknown activity type" in result
        assert "unknown_xyz" in result

    def test_watch_and_repeat(self):
        act = {
            "type": "watch_and_repeat",
            "title": "Повтори",
            "items": [{"video": "https://www.youtube.com/watch?v=12345678901"}],
        }
        result = render_activity(act)
        assert "WatchAndRepeat" in result
        assert "client:load" in result

    def test_classify(self):
        act = {
            "type": "classify",
            "title": "Sort",
            "instruction": "Pick one",
            "categories": [{"label": "A", "items": ["x", "y"]}],
        }
        result = render_activity(act)
        assert "Classify" in result
        assert "instruction" in result

    def test_image_to_letter(self):
        act = {
            "type": "image_to_letter",
            "title": "Letters",
            "items": [{"emoji": "🍎", "answer": "Я", "distractors": ["А", "Б"]}],
        }
        result = render_activity(act)
        assert "ImageToLetter" in result

    def test_true_false(self):
        act = {
            "type": "true_false",
            "title": "T/F",
            "items": [{"statement": "Київ — столиця", "is_true": True}],
        }
        result = render_activity(act)
        assert "TrueFalse" in result

    def test_build_sentence(self):
        act = {
            "type": "build_sentence",
            "items": [{"words": ["я", "люблю"], "answer": "Я люблю"}],
        }
        result = render_activity(act)
        assert "Unjumble" in result

    def test_match_sound(self):
        act = {
            "type": "match_sound",
            "items": [{"letter": "А", "description": "голосний"}],
        }
        result = render_activity(act)
        assert "MatchUp" in result

    def test_pattern_drill(self):
        act = {
            "type": "pattern_drill",
            "prompt": "Утвори форму",
            "items": [{"given": "я", "answer": "мені"}],
        }
        result = render_activity(act)
        assert "FillIn" in result

    def test_riddle(self):
        act = {
            "type": "riddle",
            "items": [{"clue": "Хто?", "answer": "кіт", "options": ["кіт", "пес"]}],
        }
        result = render_activity(act)
        assert "Quiz" in result

    def test_tongue_twister(self):
        act = {
            "type": "tongue_twister",
            "items": [{"text": "Ішов Прокіп"}],
        }
        result = render_activity(act)
        assert "WatchAndRepeat" in result

    def test_reading(self):
        act = {
            "type": "reading",
            "title": "Прочитай",
            "text": "Текст",
        }
        result = render_activity(act)
        assert "ReadingActivity" in result

    def test_proverb_drill_true_false(self):
        act = {
            "type": "proverb_drill",
            "activity": {
                "type": "true_false",
                "items": [{"statement": "Прислів'я", "is_true": True}],
            },
        }
        result = render_activity(act)
        assert "TrueFalse" in result

    def test_empty_type(self):
        result = render_activity({})
        assert "Unknown activity type" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Module 7: generate_mdx_direct_content.py
# ═══════════════════════════════════════════════════════════════════════════════

from generate_mdx_direct_content import (
    render_script_foundation,
    render_communicative,
    render_vocabulary_module,
    render_grammar,
    render_checkpoint,
)


class TestRenderScriptFoundation:
    def test_abetka_with_letters(self):
        data = {
            "module": "abetka",
            "letters": [
                {"upper": "А", "lower": "а", "sound_type": "vowel",
                 "key_word": "абетка", "emoji": "🔤"},
            ],
        }
        result = render_script_foundation(data)
        assert "Голосні" in result
        assert "LetterGrid" in result

    def test_generic_script_foundation(self):
        data = {
            "module": "sklad",
            "syllable_rule": {
                "text": "A syllable has one vowel",
                "vowels": ["А", "Е", "И"],
                "examples": [
                    {"word": "мама", "split": "ма-ма", "syllables": 2, "emoji": "👩"},
                ],
            },
        }
        result = render_script_foundation(data)
        assert "Що таке склад?" in result
        assert "мама" in result

    def test_empty_data(self):
        result = render_script_foundation({})
        assert isinstance(result, str)

    def test_syllable_table_cv(self):
        data = {
            "module": "sklad",
            "syllable_tables": [
                {
                    "title": "Таблиця",
                    "type": "cv",
                    "consonants": ["Б"],
                    "vowels": ["А", "О"],
                },
            ],
        }
        result = render_script_foundation(data)
        assert "Таблиця" in result
        assert "Ба" in result

    def test_syllable_table_vc(self):
        data = {
            "module": "sklad",
            "syllable_tables": [
                {
                    "title": "VC",
                    "type": "vc",
                    "vowels": ["А"],
                    "consonants": ["Б"],
                },
            ],
        }
        result = render_script_foundation(data)
        assert "аб" in result

    def test_soft_consonants(self):
        data = {
            "module": "sklad",
            "soft_consonants": {
                "rule": "Ь пом'якшує",
                "examples": [{"hard": "н", "soft": "нь", "note": "soft"}],
                "words": [{"word": "день", "emoji": "☀️", "note": "day"}],
            },
        }
        result = render_script_foundation(data)
        assert "М'які приголосні" in result

    def test_apostrophe_abetka(self):
        data = {
            "module": "abetka",
            "letters": [
                {"upper": "А", "lower": "а", "sound_type": "vowel",
                 "key_word": "абетка", "emoji": "🔤"},
            ],
            "apostrophe": {"symbol": "'", "note": "роз'єднує", "example_word": "м'яч", "emoji": "⚽"},
        }
        result = render_script_foundation(data)
        assert "Апостроф" in result
        assert "м'яч" in result

    def test_digraphs(self):
        data = {
            "module": "abetka",
            "letters": [
                {"upper": "А", "lower": "а", "sound_type": "vowel",
                 "key_word": "абетка", "emoji": "🔤"},
            ],
            "digraphs": [
                {"letters": "дж", "note": "один звук", "key_word": "джміль", "emoji": "🐝"},
            ],
        }
        result = render_script_foundation(data)
        assert "Буквосполучення" in result

    def test_stress_abetka(self):
        data = {
            "module": "abetka",
            "letters": [],
            "stress": {
                "rule": "Наголос вільний",
                "marker": "´",
                "examples": [{"word": "мáма", "stressed_syllable": "ма"}],
            },
        }
        result = render_script_foundation(data)
        assert "Наголос" in result

    def test_generic_apostrophe(self):
        data = {
            "module": "sklad",
            "apostrophe": {
                "rule": "Апостроф after consonants",
                "examples": [{"word": "м'яч", "split": "м'-яч", "emoji": "⚽"}],
            },
        }
        result = render_script_foundation(data)
        assert "Апостроф" in result

    def test_generic_stress(self):
        data = {
            "module": "sklad",
            "stress": {
                "rule": "вільний",
                "marker": "´",
                "meaning_change": {
                    "note": "Зміна значення",
                    "pairs": [
                        {"word1": "зáмок", "meaning1": "castle", "emoji1": "🏰",
                         "word2": "замóк", "meaning2": "lock", "emoji2": "🔒"},
                    ],
                },
            },
        }
        result = render_script_foundation(data)
        assert "Наголос" in result
        assert "Зміна значення" in result

    def test_syllable_count_suffix(self):
        """Test correct Ukrainian suffix for syllable counts."""
        data = {
            "module": "sklad",
            "syllable_rule": {
                "text": "rule",
                "examples": [
                    {"word": "і", "split": "і", "syllables": 1, "emoji": ""},
                    {"word": "мама", "split": "ма-ма", "syllables": 2, "emoji": ""},
                    {"word": "аеропорт", "split": "а-е-ро-порт-по-рт", "syllables": 5, "emoji": ""},
                ],
            },
        }
        result = render_script_foundation(data)
        assert "склад" in result
        assert "склади" in result
        assert "складів" in result


class TestRenderCommunicative:
    def test_phrases(self):
        data = {
            "phrases": [
                {
                    "function": "greeting",
                    "items": [{"phrase": "Привіт", "context": "informal", "emoji": "👋"}],
                }
            ]
        }
        result = render_communicative(data)
        assert "PhraseTable" in result

    def test_dialogues(self):
        data = {
            "dialogues": [
                {
                    "title": "У кафе",
                    "exchanges": [
                        {"speaker": "A", "text": "Привіт!", "emoji": "👋"},
                    ],
                }
            ]
        }
        result = render_communicative(data)
        assert "DialogueBox" in result
        assert "У кафе" in result

    def test_empty(self):
        result = render_communicative({})
        assert result == ""


class TestRenderVocabularyModule:
    def test_with_words(self):
        data = {
            "vocabulary": [
                {"word": "кіт", "emoji": "🐱", "pronunciation_video": None,
                 "examples": ["Кіт спить"], "category": "тварини", "question": ""},
            ]
        }
        result = render_vocabulary_module(data)
        assert "VocabCard" in result

    def test_empty(self):
        assert render_vocabulary_module({}) == ""


class TestRenderGrammar:
    def test_patterns(self):
        data = {
            "patterns": [
                {
                    "title": "Давальний відмінок",
                    "question_word": "Кому?",
                    "explanation": "shows recipient",
                    "examples": ["Я дав мамі"],
                }
            ]
        }
        result = render_grammar(data)
        assert "Давальний відмінок" in result
        assert "Кому?" in result

    def test_empty(self):
        assert render_grammar({}) == ""


class TestRenderCheckpoint:
    def test_with_summary_and_refs(self):
        data = {
            "summary": "Review everything",
            "references": ["Module 1", "Module 2"],
        }
        result = render_checkpoint(data)
        assert "Review everything" in result
        assert "Повторення" in result

    def test_empty(self):
        assert render_checkpoint({}) == ""


# ═══════════════════════════════════════════════════════════════════════════════
# Module 6: md_to_yaml.py — markdown → YAML conversion
# ═══════════════════════════════════════════════════════════════════════════════

from md_to_yaml import (
    parse_quiz,
    parse_match_up,
    parse_fill_in,
    parse_true_false,
    parse_group_sort,
    parse_unjumble,
    parse_anagram,
    parse_error_correction,
    parse_cloze,
    parse_mark_the_words,
    parse_select,
    parse_translate,
    extract_activities_section,
    parse_activities_section,
    strip_activities_from_md,
)


class TestParseQuiz:
    def test_basic_quiz(self):
        content = textwrap.dedent("""\
            1. What is Kyiv?
            - [ ] A river
            - [x] The capital of Ukraine
            - [ ] A mountain
            > It's the capital city.
        """)
        items = parse_quiz(content)
        assert len(items) == 1
        assert items[0]["question"] == "What is Kyiv?"
        assert len(items[0]["options"]) == 3
        assert items[0]["options"][1]["correct"] is True
        assert items[0]["explanation"] == "It's the capital city."

    def test_multiple_questions(self):
        content = textwrap.dedent("""\
            1. Q1?
            - [x] A
            - [ ] B

            2. Q2?
            - [ ] C
            - [x] D
        """)
        items = parse_quiz(content)
        assert len(items) == 2

    def test_empty(self):
        assert parse_quiz("") == []

    def test_no_options(self):
        content = "1. Question without options\nsome text"
        items = parse_quiz(content)
        assert len(items) == 0  # needs >= 2 options


class TestParseMatchUp:
    def test_table_format(self):
        content = textwrap.dedent("""\
            | Ukrainian | English |
            |-----------|---------|
            | кіт | cat |
            | пес | dog |
        """)
        pairs = parse_match_up(content)
        assert len(pairs) == 2
        assert pairs[0]["left"] == "кіт"
        assert pairs[0]["right"] == "cat"

    def test_separator_format(self):
        content = "кіт :: cat\nпес :: dog\n"
        pairs = parse_match_up(content)
        assert len(pairs) == 2

    def test_empty(self):
        assert parse_match_up("") == []

    def test_header_skipped(self):
        content = "| Ukrainian | English |\n|---|---|\n| слово | word |"
        pairs = parse_match_up(content)
        assert len(pairs) == 1
        assert pairs[0]["left"] == "слово"


class TestParseFillIn:
    def test_basic(self):
        content = textwrap.dedent("""\
            1. Я ___ воду.
            > [!options] п'ю | їм | сплю
            > [!answer] п'ю
        """)
        items = parse_fill_in(content)
        assert len(items) == 1
        assert items[0]["sentence"] == "Я ___ воду."
        assert items[0]["answer"] == "п'ю"
        assert "п'ю" in items[0]["options"]

    def test_with_explanation(self):
        content = textwrap.dedent("""\
            1. Sentence ___
            > [!options] a | b
            > [!answer] a
            > Because grammar
        """)
        items = parse_fill_in(content)
        assert len(items) == 1
        assert items[0]["explanation"] == "Because grammar"

    def test_empty(self):
        assert parse_fill_in("") == []


class TestParseTrueFalse:
    def test_numbered_format(self):
        content = textwrap.dedent("""\
            1. Київ — столиця.
            - [x] Правда
            - [ ] Неправда
            > Так, Київ — столиця України.
        """)
        items = parse_true_false(content)
        assert len(items) == 1
        assert items[0]["correct"] is True
        assert items[0]["explanation"] == "Так, Київ — столиця України."

    def test_bullet_format(self):
        content = textwrap.dedent("""\
            - [x] True statement.
            > Explanation.
            - [ ] False statement.
        """)
        items = parse_true_false(content)
        assert len(items) == 2
        assert items[0]["correct"] is True
        assert items[1]["correct"] is False

    def test_false_item(self):
        content = textwrap.dedent("""\
            1. Earth is flat.
            - [ ] Правда
            - [x] Неправда
        """)
        items = parse_true_false(content)
        assert len(items) == 1
        assert items[0]["correct"] is False

    def test_empty(self):
        assert parse_true_false("") == []


class TestParseGroupSort:
    def test_basic(self):
        content = textwrap.dedent("""\
            ### Тварини
            - кіт
            - пес
            ### Їжа
            - хліб
        """)
        groups = parse_group_sort(content)
        assert len(groups) == 2
        assert groups[0]["name"] == "Тварини"
        assert len(groups[0]["items"]) == 2

    def test_empty(self):
        assert parse_group_sort("") == []


class TestParseUnjumble:
    def test_basic(self):
        content = textwrap.dedent("""\
            1. люблю / я / Україну
            > [!answer] Я люблю Україну
        """)
        items = parse_unjumble(content)
        assert len(items) == 1
        assert items[0]["answer"] == "Я люблю Україну"
        assert len(items[0]["words"]) == 3

    def test_empty(self):
        assert parse_unjumble("") == []


class TestParseAnagram:
    def test_basic(self):
        content = textwrap.dedent("""\
            1. т і к
            > [!answer] кіт
            > (тварина)
        """)
        items = parse_anagram(content)
        assert len(items) == 1
        assert items[0]["answer"] == "кіт"
        assert items[0]["hint"] == "тварина"

    def test_no_hint(self):
        content = "1. а м а м\n> [!answer] мама\n"
        items = parse_anagram(content)
        assert len(items) == 1
        assert "hint" not in items[0]

    def test_empty(self):
        assert parse_anagram("") == []


class TestParseErrorCorrection:
    def test_basic(self):
        content = textwrap.dedent("""\
            1. Я ходю до школа.
            > [!error] школа
            > [!answer] школи
            > [!options] школи | школу | школою
            > [!explanation] Genitive case needed.
        """)
        items = parse_error_correction(content)
        assert len(items) == 1
        assert items[0]["error"] == "школа"
        assert items[0]["answer"] == "школи"

    def test_empty(self):
        assert parse_error_correction("") == []


class TestParseCloze:
    def test_basic(self):
        content = textwrap.dedent("""\
            Я [___:1] воду щодня.

            1. п'ю | їм | сплю | читаю
            > [!answer] п'ю
        """)
        result = parse_cloze(content)
        assert "{п'ю" in result
        assert "[___:1]" not in result

    def test_no_blanks(self):
        content = "Just a passage."
        result = parse_cloze(content)
        assert "Just a passage." in result


class TestParseMarkTheWords:
    def test_bracket_format(self):
        content = "Я [люблю] Україну."
        result = parse_mark_the_words(content)
        assert "*люблю*" in result

    def test_bold_format(self):
        content = "Я **люблю** Україну."
        result = parse_mark_the_words(content)
        assert "*люблю*" in result

    def test_skip_callout(self):
        content = "> Hint line\nActual text [word]"
        result = parse_mark_the_words(content)
        assert "Hint line" not in result
        assert "*word*" in result


class TestParseSelect:
    def test_basic(self):
        content = textwrap.dedent("""\
            1. Pick the verbs:
            - [x] бігти
            - [ ] стіл
            - [x] їсти
        """)
        items = parse_select(content)
        assert len(items) == 1
        assert len(items[0]["options"]) == 3
        correct = [o for o in items[0]["options"] if o["correct"]]
        assert len(correct) == 2

    def test_empty(self):
        assert parse_select("") == []


class TestParseTranslate:
    def test_basic(self):
        content = textwrap.dedent("""\
            1. I love Ukraine
            - [x] Я люблю Україну
            - [ ] Я їм Україну
        """)
        items = parse_translate(content)
        assert len(items) == 1
        assert items[0]["source"] == "I love Ukraine"

    def test_empty(self):
        assert parse_translate("") == []


class TestExtractActivitiesSection:
    def test_finds_activities(self):
        md = "# Intro\nText.\n# Activities\n## quiz: Q\ncontent\n# Summary\nend"
        result = extract_activities_section(md)
        assert result is not None
        assert "quiz" in result

    def test_finds_vpravy(self):
        md = "# Вступ\n# Вправи\n## quiz: Q\ncontent"
        result = extract_activities_section(md)
        assert result is not None

    def test_no_activities(self):
        md = "# Intro\nJust content."
        assert extract_activities_section(md) is None


class TestParseActivitiesSection:
    def test_single_quiz(self):
        section = textwrap.dedent("""\
            ## quiz: Knowledge Check
            1. What color?
            - [x] blue
            - [ ] red
        """)
        activities = parse_activities_section(section)
        assert len(activities) == 1
        assert activities[0]["type"] == "quiz"
        assert activities[0]["title"] == "Knowledge Check"

    def test_multiple_activities(self):
        section = textwrap.dedent("""\
            ## quiz: Q1
            1. Q?
            - [x] A
            - [ ] B

            ## match-up: Pairs
            | Left | Right |
            |------|-------|
            | a | b |
        """)
        activities = parse_activities_section(section)
        assert len(activities) == 2

    def test_cloze_type(self):
        section = "## cloze: Fill\nPassage [___:1] text.\n1. a | b\n> [!answer] a\n"
        activities = parse_activities_section(section)
        assert len(activities) == 1
        assert "passage" in activities[0]

    def test_mark_the_words_type(self):
        section = "## mark-the-words: Mark\nText [word] here.\n"
        activities = parse_activities_section(section)
        assert len(activities) == 1
        assert "text" in activities[0]


class TestStripActivitiesFromMd:
    def test_strips(self):
        md = "# Intro\nContent\n# Activities\nstuff\n# Summary\nEnd"
        result = strip_activities_from_md(md)
        assert "# Intro" in result
        assert "# Summary" in result
        assert "# Activities" not in result

    def test_no_activities(self):
        md = "# Intro\nContent\n# Summary\nEnd"
        assert strip_activities_from_md(md) == md

    def test_activities_at_end(self):
        md = "# Intro\nContent\n# Activities\nstuff"
        result = strip_activities_from_md(md)
        assert "# Intro" in result
        assert "stuff" not in result


# ═══════════════════════════════════════════════════════════════════════════════
# Module 5: validate_direct.py — l2-uk-direct validation
# ═══════════════════════════════════════════════════════════════════════════════

from validate_direct import (
    ValidationResult,
    check_header,
    check_video_url,
    check_letters,
    check_vocabulary,
    check_activities,
    count_vocab_items,
    validate_file,
    UKRAINIAN_ALPHABET,
)


class TestValidationResult:
    def test_pass_when_no_errors(self):
        r = ValidationResult(Path("test.yaml"))
        r.warn("minor thing")
        r.info("note")
        assert r.passed is True

    def test_fail_with_error(self):
        r = ValidationResult(Path("test.yaml"))
        r.error("broken")
        assert r.passed is False

    def test_print_report(self, capsys):
        r = ValidationResult(Path("test.yaml"))
        r.error("bad")
        r.warn("ehh")
        r.info("fyi")
        r.print_report()
        out = capsys.readouterr().out
        assert "FAIL" in out
        assert "bad" in out


class TestCheckHeader:
    def test_valid_header(self):
        r = ValidationResult(Path("t"))
        data = {"module": "test", "track": "l2-uk-direct", "level": "a1",
                "type": "vocabulary", "title": "Test"}
        check_header(data, r)
        assert r.passed

    def test_missing_field(self):
        r = ValidationResult(Path("t"))
        check_header({"track": "l2-uk-direct"}, r)
        assert not r.passed

    def test_wrong_track(self):
        r = ValidationResult(Path("t"))
        data = {"module": "m", "track": "wrong", "level": "a1",
                "type": "vocabulary", "title": "T"}
        check_header(data, r)
        assert not r.passed

    def test_invalid_level(self):
        r = ValidationResult(Path("t"))
        data = {"module": "m", "track": "l2-uk-direct", "level": "c2",
                "type": "vocabulary", "title": "T"}
        check_header(data, r)
        assert not r.passed

    def test_invalid_type(self):
        r = ValidationResult(Path("t"))
        data = {"module": "m", "track": "l2-uk-direct", "level": "a1",
                "type": "invalid_type", "title": "T"}
        check_header(data, r)
        assert not r.passed


class TestCheckVideoUrl:
    def test_none_allowed(self):
        r = ValidationResult(Path("t"))
        check_video_url(None, "ctx", r)
        assert r.passed

    def test_valid_url(self):
        r = ValidationResult(Path("t"))
        check_video_url("https://www.youtube.com/watch?v=12345678901", "ctx", r)
        assert r.passed

    def test_invalid_url(self):
        r = ValidationResult(Path("t"))
        check_video_url("https://bad-url.com", "ctx", r)
        assert not r.passed

    def test_non_string(self):
        r = ValidationResult(Path("t"))
        check_video_url(123, "ctx", r)
        assert not r.passed


class TestCheckLetters:
    def test_valid_letters(self):
        r = ValidationResult(Path("t"))
        data = {"letters": [
            {"upper": "А", "lower": "а", "sound_type": "vowel",
             "key_word": "абетка", "emoji": "📚", "pronunciation_video": None},
        ]}
        check_letters(data, r)
        assert r.passed

    def test_missing_field(self):
        r = ValidationResult(Path("t"))
        data = {"letters": [{"upper": "А"}]}
        check_letters(data, r)
        assert not r.passed

    def test_duplicate_emoji(self):
        r = ValidationResult(Path("t"))
        data = {"letters": [
            {"upper": "А", "lower": "а", "sound_type": "vowel",
             "key_word": "а", "emoji": "🔤", "pronunciation_video": None},
            {"upper": "Б", "lower": "б", "sound_type": "consonant",
             "key_word": "б", "emoji": "🔤", "pronunciation_video": None},
        ]}
        check_letters(data, r)
        assert not r.passed  # duplicate emoji

    def test_no_letters(self):
        r = ValidationResult(Path("t"))
        check_letters({}, r)
        assert r.passed  # just a warning
        assert len(r.warnings) > 0


class TestCheckVocabulary:
    def test_grouped_format(self):
        r = ValidationResult(Path("t"))
        data = {"vocabulary": [
            {"category": "food", "items": [
                {"word": "хліб"}, {"word": "вода"},
            ]},
        ]}
        check_vocabulary(data, r)
        assert r.passed

    def test_flat_format_valid(self):
        r = ValidationResult(Path("t"))
        data = {"vocabulary": [
            {"word": "кіт", "pronunciation_video": None, "category": "тварини",
             "examples": ["Кіт спить.", "Мій кіт."]},
        ]}
        check_vocabulary(data, r)
        assert r.passed

    def test_flat_format_too_few_examples(self):
        r = ValidationResult(Path("t"))
        data = {"vocabulary": [
            {"word": "кіт", "pronunciation_video": None, "category": "тварини",
             "examples": ["one"]},
        ]}
        check_vocabulary(data, r)
        assert not r.passed

    def test_empty_vocab(self):
        r = ValidationResult(Path("t"))
        check_vocabulary({}, r)
        assert r.passed

    def test_latin_in_example_warns(self):
        r = ValidationResult(Path("t"))
        data = {"vocabulary": [
            {"word": "кіт", "pronunciation_video": None, "category": "animals",
             "examples": ["The cat sleeps", "It is a cat"]},
        ]}
        check_vocabulary(data, r)
        assert len(r.warnings) > 0


class TestCheckActivities:
    def test_valid_activity(self):
        r = ValidationResult(Path("t"))
        data = {"activities": [{"type": "true_false", "items": [
            {"statement": "S1", "answer": True},
            {"statement": "S2", "answer": False},
            {"statement": "S3", "answer": True},
        ]}]}
        check_activities(data, r)
        assert r.passed

    def test_missing_activities(self):
        r = ValidationResult(Path("t"))
        check_activities({}, r)
        assert not r.passed

    def test_unknown_type(self):
        r = ValidationResult(Path("t"))
        data = {"activities": [{"type": "nonexistent"}]}
        check_activities(data, r)
        assert not r.passed

    def test_pre_literacy_rejects_post_literacy(self):
        r = ValidationResult(Path("t"))
        data = {"module": "abetka", "activities": [
            {"type": "build_sentence", "sentences": [
                {"words": ["a"], "correct": "a"},
                {"words": ["b"], "correct": "b"},
                {"words": ["c"], "correct": "c"},
            ]},
        ]}
        check_activities(data, r)
        assert not r.passed

    def test_classify_needs_categories(self):
        r = ValidationResult(Path("t"))
        data = {"activities": [{"type": "classify"}]}
        check_activities(data, r)
        assert not r.passed

    def test_riddle_needs_answer_and_clues(self):
        r = ValidationResult(Path("t"))
        data = {"activities": [{"type": "riddle"}]}
        check_activities(data, r)
        assert not r.passed

    def test_tongue_twister_needs_text(self):
        r = ValidationResult(Path("t"))
        data = {"activities": [{"type": "tongue_twister"}]}
        check_activities(data, r)
        assert not r.passed

    def test_proverb_drill_needs_content(self):
        r = ValidationResult(Path("t"))
        data = {"activities": [{"type": "proverb_drill"}]}
        check_activities(data, r)
        assert not r.passed

    def test_watch_and_repeat_no_items(self):
        r = ValidationResult(Path("t"))
        data = {"activities": [{"type": "watch_and_repeat", "items": []}]}
        check_activities(data, r)
        assert not r.passed

    def test_image_to_letter_few_items_warns(self):
        r = ValidationResult(Path("t"))
        data = {"activities": [{"type": "image_to_letter", "items": [
            {"emoji": "🍎", "answer": "Я", "distractors": ["А"]},
        ]}]}
        check_activities(data, r)
        assert len(r.warnings) > 0

    def test_image_to_letter_duplicate_emoji(self):
        r = ValidationResult(Path("t"))
        data = {"activities": [{"type": "image_to_letter", "items": [
            {"emoji": "🍎", "answer": "Я", "distractors": ["А"]},
            {"emoji": "🍎", "answer": "Б", "distractors": ["В"]},
        ]}]}
        check_activities(data, r)
        assert not r.passed

    def test_true_false_non_bool_answer(self):
        r = ValidationResult(Path("t"))
        data = {"activities": [{"type": "true_false", "items": [
            {"statement": "S1", "answer": "yes"},
            {"statement": "S2", "answer": True},
            {"statement": "S3", "answer": False},
        ]}]}
        check_activities(data, r)
        assert not r.passed

    def test_pattern_drill_missing_fields(self):
        r = ValidationResult(Path("t"))
        data = {"activities": [{"type": "pattern_drill", "items": [
            {"given": "x"},  # missing answer
        ]}]}
        check_activities(data, r)
        assert not r.passed

    def test_build_sentence_missing_fields(self):
        r = ValidationResult(Path("t"))
        data = {"activities": [{"type": "build_sentence", "sentences": [
            {"words": ["a"]},  # missing correct
        ]}]}
        check_activities(data, r)
        assert not r.passed

    def test_reading_no_text(self):
        r = ValidationResult(Path("t"))
        data = {"activities": [{"type": "reading"}]}
        check_activities(data, r)
        assert not r.passed


class TestCountVocabItems:
    def test_grouped(self):
        data = {"vocabulary": [
            {"items": [{"word": "a"}, {"word": "b"}]},
            {"items": [{"word": "c"}]},
        ]}
        assert count_vocab_items(data) == 3

    def test_flat(self):
        data = {"vocabulary": [{"word": "a"}, {"word": "b"}]}
        assert count_vocab_items(data) == 2

    def test_empty(self):
        assert count_vocab_items({}) == 0


class TestValidateFile:
    def test_nonexistent_file(self):
        r = validate_file(Path("/nonexistent/file.yaml"))
        assert not r.passed

    def test_valid_file(self, tmp_path):
        import yaml
        data = {
            "module": "test",
            "track": "l2-uk-direct",
            "level": "a1",
            "type": "vocabulary",
            "title": "Test",
            "vocabulary": [
                {"word": "кіт", "pronunciation_video": None,
                 "category": "тварини", "examples": ["Кіт спить.", "Мій кіт."]},
            ],
            "activities": [{"type": "true_false", "items": [
                {"statement": "S1", "answer": True},
                {"statement": "S2", "answer": False},
                {"statement": "S3", "answer": True},
            ]}],
        }
        p = tmp_path / "test.yaml"
        p.write_text(yaml.dump(data, allow_unicode=True))
        r = validate_file(p)
        assert r.passed

    def test_invalid_yaml(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text("{{invalid yaml")
        r = validate_file(p)
        assert not r.passed

    def test_non_dict_yaml(self, tmp_path):
        p = tmp_path / "list.yaml"
        p.write_text("- item1\n- item2")
        r = validate_file(p)
        assert not r.passed

    def test_vocab_target_check(self, tmp_path):
        import yaml
        data = {
            "module": "test", "track": "l2-uk-direct", "level": "a1",
            "type": "vocabulary", "title": "T",
            "vocabulary": [{"word": "a", "pronunciation_video": None,
                          "category": "c", "examples": ["e1", "e2"]}],
            "activities": [{"type": "classify", "categories": [{"label": "A", "items": ["x"]}]}],
        }
        p = tmp_path / "t.yaml"
        p.write_text(yaml.dump(data, allow_unicode=True))
        r = validate_file(p, vocab_target=10)
        assert len(r.warnings) > 0  # below target


class TestUkrainianAlphabet:
    def test_33_letters(self):
        assert len(UKRAINIAN_ALPHABET) == 33


# ═══════════════════════════════════════════════════════════════════════════════
# Module 4: generate_json.py — module → JSON conversion
# ═══════════════════════════════════════════════════════════════════════════════

from generate_json import (
    parse_frontmatter,
    parse_sections,
    parse_vocabulary,
    parse_module,
    infer_module_type,
    get_immersion_level,
    render_vibe_json,
    SECTION_TYPES,
)


class TestParseFrontmatter:
    def test_basic(self):
        content = "---\ntitle: Test\nlevel: A1\n---\nBody text"
        fm, body = parse_frontmatter(content)
        assert fm["title"] == "Test"
        assert "Body text" in body

    def test_no_frontmatter(self):
        content = "Just body text"
        fm, body = parse_frontmatter(content)
        assert fm == {}
        assert body == content

    def test_invalid_yaml(self):
        content = "---\n{{bad\n---\nbody"
        fm, body = parse_frontmatter(content)
        assert fm == {}


class TestParseSections:
    def test_basic(self):
        content = "# Introduction\nIntro text\n# Lesson\nLesson text"
        sections = parse_sections(content)
        assert len(sections) == 2
        assert sections[0]["type"] == "intro"
        assert sections[1]["type"] == "content"

    def test_vocabulary_section(self):
        content = "# Vocabulary\n| word | ipa | meaning |"
        sections = parse_sections(content)
        assert sections[0]["type"] == "vocabulary"

    def test_ukrainian_headings(self):
        content = "# Вступ\ntext\n# Урок\ntext2"
        sections = parse_sections(content)
        assert sections[0]["type"] == "intro"
        assert sections[1]["type"] == "content"

    def test_empty_content(self):
        assert parse_sections("") == []

    def test_summary_section(self):
        content = "# Summary\nSummary text"
        sections = parse_sections(content)
        assert sections[0]["type"] == "summary"


class TestParseVocabulary:
    def test_basic_table(self):
        content = textwrap.dedent("""\
            # Vocabulary
            | Ukrainian | IPA | English | POS | Gender | Note |
            |-----------|-----|---------|-----|--------|------|
            | кіт | kit | cat | noun | m | animal |
        """)
        words = parse_vocabulary(content)
        assert len(words) == 1
        assert words[0]["uk"] == "кіт"
        assert words[0]["en"] == "cat"
        assert words[0]["gender"] == "m"

    def test_no_vocabulary_section(self):
        assert parse_vocabulary("# Intro\ntext") == []

    def test_minimal_columns(self):
        content = "# Vocabulary\n| uk | ipa | en |\n|---|---|---|\n| слово | slovo | word |\n"
        words = parse_vocabulary(content)
        assert len(words) == 1

    def test_feminine_gender(self):
        content = "# Vocabulary\n| uk | ipa | en | pos | ж | |\n|---|---|---|---|---|---|\n| кішка | k | cat | n | ж | |\n"
        words = parse_vocabulary(content)
        assert words[0]["gender"] == "f"


class TestInferModuleType:
    def test_checkpoint(self):
        assert infer_module_type(["checkpoint"]) == "checkpoint"

    def test_history(self):
        assert infer_module_type(["history"]) == "history"

    def test_grammar_default(self):
        assert infer_module_type(["unknown"]) == "grammar"

    def test_empty_tags(self):
        assert infer_module_type([]) == "grammar"

    def test_culture(self):
        assert infer_module_type(["culture"]) == "culture"

    def test_case_insensitive(self):
        assert infer_module_type(["HISTORY"]) == "history"


class TestGetImmersionLevel:
    def test_a1(self):
        assert get_immersion_level("A1") == 0.30

    def test_c2(self):
        assert get_immersion_level("C2") == 0.98

    def test_unknown(self):
        assert get_immersion_level("X9") == 0.50

    def test_lowercase(self):
        assert get_immersion_level("b1") == 0.60


class TestParseModule:
    def test_basic(self):
        content = "---\ntitle: Test Module\ntags: [grammar]\n---\n# Introduction\nHello"
        parsed = parse_module(content, "a1", 1)
        assert parsed["frontmatter"]["title"] == "Test Module"
        assert parsed["frontmatter"]["level"] == "A1"
        assert parsed["frontmatter"]["module"] == 1
        assert len(parsed["sections"]) == 1

    def test_defaults(self):
        content = "---\n---\n# Lesson\nContent"
        parsed = parse_module(content, "b1", 5)
        assert parsed["frontmatter"]["title"] == "Module 5"
        assert parsed["frontmatter"]["duration"] == 45
        assert parsed["frontmatter"]["pedagogy"] == "PPP"


class TestRenderVibeJson:
    def test_basic_render(self):
        content = "---\ntitle: Test\ntags: [grammar]\n---\n# Introduction\nHello"
        parsed = parse_module(content, "a1", 1)
        result = render_vibe_json(parsed, "l2-uk-en")
        assert "lesson" in result
        assert "activities" in result
        assert "vocabulary" in result
        assert result["lesson"]["targetLevel"] == "A1"

    def test_with_external_resources(self):
        content = "---\ntitle: Test\ntags: []\n---\n"
        parsed = parse_module(content, "a1", 1)
        resources = {
            "podcasts": [
                {"title": "B", "priority": 2, "relevance": "low"},
                {"title": "A", "priority": 1, "relevance": "high"},
            ],
            "youtube": [],
        }
        result = render_vibe_json(parsed, "l2-uk-en", resources)
        assert "external_resources" in result
        # Priority 1 should come first
        assert result["external_resources"]["podcasts"][0]["title"] == "A"

    def test_no_resources(self):
        content = "---\ntitle: T\ntags: []\n---\n"
        parsed = parse_module(content, "a1", 1)
        result = render_vibe_json(parsed, "l2-uk-en")
        assert "external_resources" not in result


# ═══════════════════════════════════════════════════════════════════════════════
# Module 3: generate_plan_markdown.py — rendering functions
# ═══════════════════════════════════════════════════════════════════════════════

from generate_plan_markdown import (
    _render_header,
    _render_overview,
    _render_phase,
    _render_statistics,
    _render_module_detail,
    _build_slug_to_num,
    _load_module_plans,
    _load_meta_files,
)


class TestRenderHeader:
    def test_basic(self):
        plan = {"track": "history", "prerequisite": "B1",
                "vocabulary_target": 500, "immersion": 0.85}
        lines = _render_header(plan, "hist", 10)
        text = "\n".join(lines)
        assert "HIST" in text
        assert "10 module meta" in text
        assert "85%" in text

    def test_list_prerequisites(self):
        plan = {"overview": {"prerequisites": ["a1", "a2"]}}
        lines = _render_header(plan, "b1", 5)
        text = "\n".join(lines)
        assert "A1" in text and "A2" in text

    def test_no_immersion(self):
        plan = {}
        lines = _render_header(plan, "a1", 0)
        text = "\n".join(lines)
        assert "N/A" in text


class TestRenderOverview:
    def test_with_notes(self):
        plan = {"notes": "Track overview text."}
        lines = _render_overview(plan)
        assert any("Track Overview" in l for l in lines)

    def test_with_vocab_focus(self):
        plan = {"vocabulary": {"focus_areas": ["grammar", "idioms"]}}
        lines = _render_overview(plan)
        assert any("grammar" in l for l in lines)

    def test_with_pedagogy(self):
        plan = {"pedagogy_notes": {
            "approach": "immersive",
            "structure": ["step1"],
            "decolonization": ["note1"],
        }}
        lines = _render_overview(plan)
        assert any("immersive" in l for l in lines)

    def test_empty(self):
        assert _render_overview({}) == []


class TestRenderPhase:
    def test_basic(self):
        phase = {"id": "I", "name": "Foundation", "modules": [1, 5], "focus": "basics"}
        slug_to_num = {"intro": 1, "greetings": 2}
        plans = {"intro": {"title": "Intro", "word_target": 1200, "objectives": ["obj1"]}}
        meta = {}
        lines = _render_phase(phase, slug_to_num, plans, meta)
        text = "\n".join(lines)
        assert "Phase I" in text
        assert "Foundation" in text
        assert "Intro" in text

    def test_empty_phase(self):
        phase = {"name": "Empty", "modules": [100, 200]}
        lines = _render_phase(phase, {}, {}, {})
        text = "\n".join(lines)
        assert "no modules found" in text

    def test_with_author(self):
        phase = {"name": "Lit", "modules": [1, 1], "author": "Shevchenko", "key_works": ["Kobzar"]}
        lines = _render_phase(phase, {}, {}, {})
        text = "\n".join(lines)
        assert "Shevchenko" in text
        assert "Kobzar" in text


class TestRenderStatistics:
    def test_basic(self):
        plans = {
            "mod1": {"word_target": 1000, "content_outline": [{}], "objectives": ["a", "b"]},
            "mod2": {"word_target": 2000, "objectives": ["c"]},
        }
        lines = _render_statistics(plans, {})
        text = "\n".join(lines)
        assert "3,000" in text
        assert "3" in text  # objectives

    def test_meta_fallback(self):
        plans = {}
        meta = {"mod1": {"word_target": 500, "objectives": ["a"]}}
        lines = _render_statistics(plans, meta)
        text = "\n".join(lines)
        assert "500" in text


class TestRenderModuleDetail:
    def test_basic(self):
        plan = {
            "title": "Test Module",
            "subtitle": "A subtitle",
            "objectives": ["Learn X", "Practice Y"],
            "content_outline": [{"section": "Intro", "words": 500}],
            "word_target": 1000,
            "grammar": [{"point": "dative case"}],
        }
        lines = _render_module_detail(1, "test-module", plan)
        text = "\n".join(lines)
        assert "M01: Test Module" in text
        assert "A subtitle" in text
        assert "Learn X" in text
        assert "dative case" in text

    def test_minimal(self):
        lines = _render_module_detail(5, "slug", {})
        text = "\n".join(lines)
        assert "M05:" in text


class TestBuildSlugToNum:
    def test_from_meta(self):
        meta = {"intro": {"id": "hist-01"}}
        result = _build_slug_to_num(meta, {}, Path("/nonexistent"))
        assert result["intro"] == 1

    def test_from_plan_module_field(self):
        plans = {"test": {"module": "bio-15"}}
        result = _build_slug_to_num({}, plans, Path("/nonexistent"))
        assert result["test"] == 15

    def test_empty(self):
        result = _build_slug_to_num({}, {}, Path("/nonexistent"))
        assert result == {}


class TestLoadModulePlans:
    def test_nonexistent_dir(self):
        result = _load_module_plans(Path("/nonexistent"))
        assert result == {}

    def test_loads_yaml(self, tmp_path):
        import yaml
        p = tmp_path / "test.yaml"
        p.write_text(yaml.dump({"slug": "test-mod", "title": "Test"}))
        result = _load_module_plans(tmp_path)
        assert "test-mod" in result


class TestLoadMetaFiles:
    def test_nonexistent_dir(self):
        assert _load_meta_files(Path("/nonexistent")) == {}

    def test_loads_meta(self, tmp_path):
        import yaml
        p = tmp_path / "meta.yaml"
        p.write_text(yaml.dump({"slug": "my-mod", "title": "My Module"}))
        result = _load_meta_files(tmp_path)
        assert "my-mod" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Module 1: batch_dispatcher_helpers.py — pure logic functions
# ═══════════════════════════════════════════════════════════════════════════════

from batch_dispatcher_config import TrackState, TRACKS, TRACK_BY_NAME


class TestCheckDependencies:
    """Test check_dependencies from helpers."""

    def test_no_deps(self):
        from batch_dispatcher_helpers import check_dependencies
        # a1 has no dependencies
        ok, unmet = check_dependencies("a1", {})
        assert ok is True
        assert unmet == []

    def test_deps_met(self):
        from batch_dispatcher_helpers import check_dependencies
        scans = {"a1": {"pass_rate": 0.85}}
        ok, unmet = check_dependencies("a2", scans)
        assert ok is True

    def test_deps_not_met(self):
        from batch_dispatcher_helpers import check_dependencies
        scans = {"a1": {"pass_rate": 0.50}}
        ok, unmet = check_dependencies("a2", scans)
        assert ok is False
        assert len(unmet) == 1

    def test_deps_not_scanned(self):
        from batch_dispatcher_helpers import check_dependencies
        ok, unmet = check_dependencies("a2", {})
        assert ok is False
        assert "not scanned" in unmet[0]

    def test_unknown_track(self):
        from batch_dispatcher_helpers import check_dependencies
        ok, unmet = check_dependencies("nonexistent_track", {})
        assert ok is False


class TestSelectStrategy:
    def test_unbuilt_modules(self):
        from batch_dispatcher_helpers import select_strategy
        scan = {"unbuilt": 5, "failed": 0}
        mode, args = select_strategy("a1", scan)
        assert mode == "auto"

    def test_failed_modules(self):
        from batch_dispatcher_helpers import select_strategy
        scan = {"unbuilt": 0, "failed": 3}
        mode, args = select_strategy("a1", scan)
        assert mode == "auto"

    def test_all_passing(self):
        from batch_dispatcher_helpers import select_strategy
        scan = {"unbuilt": 0, "failed": 0}
        mode, args = select_strategy("a1", scan)
        assert mode == "fix"


class TestDetectProgress:
    def test_progress_made(self):
        from batch_dispatcher_helpers import detect_progress
        before = {"passed": 10, "failed": 5, "unbuilt": 3}
        after = {"passed": 12, "failed": 4, "unbuilt": 2}
        progress = detect_progress("a1", before, after)
        assert progress["delta_passed"] == 2
        assert progress["made_progress"] is True

    def test_no_progress(self):
        from batch_dispatcher_helpers import detect_progress
        before = {"passed": 10, "failed": 5, "unbuilt": 0}
        after = {"passed": 10, "failed": 5, "unbuilt": 0}
        progress = detect_progress("a1", before, after)
        assert progress["made_progress"] is False

    def test_unbuilt_reduced(self):
        from batch_dispatcher_helpers import detect_progress
        before = {"passed": 10, "failed": 5, "unbuilt": 5}
        after = {"passed": 10, "failed": 6, "unbuilt": 3}
        progress = detect_progress("a1", before, after)
        assert progress["delta_unbuilt"] == 2
        assert progress["made_progress"] is True


class TestReadBatchState:
    def test_nonexistent(self, tmp_path):
        from batch_dispatcher_helpers import read_batch_state
        with patch("batch_dispatcher_helpers.BATCH_STATE_DIR", tmp_path):
            result = read_batch_state("a1")
            assert result is None

    def test_valid_json(self, tmp_path):
        from batch_dispatcher_helpers import read_batch_state
        state_file = tmp_path / "state_a1.json"
        state_file.write_text(json.dumps({"summary": {"processed": 10, "passed": 8}}))
        with patch("batch_dispatcher_helpers.BATCH_STATE_DIR", tmp_path):
            result = read_batch_state("a1")
            assert result["summary"]["processed"] == 10

    def test_invalid_json(self, tmp_path):
        from batch_dispatcher_helpers import read_batch_state
        state_file = tmp_path / "state_a1.json"
        state_file.write_text("not json")
        with patch("batch_dispatcher_helpers.BATCH_STATE_DIR", tmp_path):
            result = read_batch_state("a1")
            assert result is None


class TestLoadDispatcherState:
    def test_fresh_state(self, tmp_path):
        from batch_dispatcher_helpers import load_dispatcher_state
        state = load_dispatcher_state(tmp_path / "state.json")
        assert "started" in state
        assert state["tracks"] == {}

    def test_existing_state(self, tmp_path):
        from batch_dispatcher_helpers import load_dispatcher_state
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"started": "2026-01-01", "tracks": {"a1": {}},
                                           "dispatch_history": [], "stats": {}}))
        state = load_dispatcher_state(state_file)
        assert "a1" in state["tracks"]

    def test_corrupt_state(self, tmp_path):
        from batch_dispatcher_helpers import load_dispatcher_state
        state_file = tmp_path / "state.json"
        state_file.write_text("corrupt")
        state = load_dispatcher_state(state_file)
        assert state["tracks"] == {}


class TestSaveDispatcherState:
    def test_saves(self, tmp_path):
        from batch_dispatcher_helpers import save_dispatcher_state
        state_file = tmp_path / "state.json"
        state = {"tracks": {}, "stats": {}}
        with patch("batch_dispatcher_helpers.atomic_write_json") as mock_write:
            save_dispatcher_state(state, state_file)
            mock_write.assert_called_once()
            assert "last_updated" in state


class TestGetTrackDstate:
    def test_creates_new(self):
        from batch_dispatcher_helpers import get_track_dstate
        state = {"tracks": {}}
        dstate = get_track_dstate(state, "a1")
        assert dstate["state"] == TrackState.PENDING
        assert "a1" in state["tracks"]

    def test_returns_existing(self):
        from batch_dispatcher_helpers import get_track_dstate
        state = {"tracks": {"a1": {"state": TrackState.DONE, "stall_count": 0,
                                     "last_dispatch": None, "last_result": None,
                                     "cooldown_until": None, "dispatches": 5,
                                     "last_passed": 60, "last_failed": 0}}}
        dstate = get_track_dstate(state, "a1")
        assert dstate["state"] == TrackState.DONE
        assert dstate["dispatches"] == 5


class TestDispatchTrack:
    @patch("batch_dispatcher_helpers.subprocess.run")
    def test_success(self, mock_run):
        from batch_dispatcher_helpers import dispatch_track
        mock_run.return_value = MagicMock(
            returncode=0, stderr="", stdout="done"
        )
        result = dispatch_track("a1", "auto", [])
        assert result["success"] is True
        assert result["quota_hit"] is False

    @patch("batch_dispatcher_helpers.subprocess.run")
    def test_quota_hit(self, mock_run):
        from batch_dispatcher_helpers import dispatch_track
        mock_run.return_value = MagicMock(
            returncode=1, stderr="429 rate limit exceeded", stdout=""
        )
        result = dispatch_track("a1", "auto", [])
        assert result["quota_hit"] is True

    @patch("batch_dispatcher_helpers.subprocess.run")
    def test_timeout(self, mock_run):
        import subprocess
        from batch_dispatcher_helpers import dispatch_track
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=10)
        result = dispatch_track("a1", "auto", [], timeout=1)
        assert result["success"] is False
        assert result["returncode"] == -1

    @patch("batch_dispatcher_helpers.subprocess.run")
    def test_exception(self, mock_run):
        from batch_dispatcher_helpers import dispatch_track
        mock_run.side_effect = OSError("broken")
        result = dispatch_track("a1", "auto", [])
        assert result["success"] is False
        assert result["returncode"] == -2


class TestDispatchClaudeFix:
    @patch("batch_dispatcher_helpers.subprocess.run")
    def test_success(self, mock_run):
        from batch_dispatcher_helpers import dispatch_claude_fix
        mock_run.return_value = MagicMock(returncode=0, stdout="fixed")
        result = dispatch_claude_fix("hist", "some-slug", 5)
        assert result["success"] is True

    @patch("batch_dispatcher_helpers.subprocess.run")
    def test_with_failure_data(self, mock_run):
        from batch_dispatcher_helpers import dispatch_claude_fix
        mock_run.return_value = MagicMock(returncode=0, stdout="ok")
        failure_data = {
            "failed_gates": {"words": {"message": "too short"}},
            "blocking_issues": ["word count"],
            "actions_tried": [{"diagnosis": "added words"}],
        }
        result = dispatch_claude_fix("hist", "slug", 1, failure_data=failure_data)
        assert result["success"] is True

    @patch("batch_dispatcher_helpers.subprocess.run")
    def test_timeout(self, mock_run):
        import subprocess
        from batch_dispatcher_helpers import dispatch_claude_fix
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="c", timeout=10)
        result = dispatch_claude_fix("hist", "slug", 1, timeout=1)
        assert result["success"] is False

    @patch("batch_dispatcher_helpers.subprocess.run")
    def test_seminar_vs_core(self, mock_run):
        from batch_dispatcher_helpers import dispatch_claude_fix
        mock_run.return_value = MagicMock(returncode=0, stdout="ok")
        # hist is seminar
        dispatch_claude_fix("hist", "slug", 1)
        cmd = mock_run.call_args[0][0]
        prompt = " ".join(cmd)
        assert "full-rebuild" in prompt


class TestComputePriorityScore:
    @patch("batch_dispatcher_helpers.read_batch_state", return_value=None)
    def test_basic(self, mock_state):
        from batch_dispatcher_helpers import compute_priority_score
        scan = {"total": 100, "passed": 80, "stale": 5, "failed": 10, "unbuilt": 5}
        score = compute_priority_score("a1", scan, {}, {})
        assert isinstance(score, float)

    @patch("batch_dispatcher_helpers.read_batch_state")
    def test_with_history(self, mock_state):
        from batch_dispatcher_helpers import compute_priority_score
        mock_state.return_value = {"summary": {"processed": 20, "passed": 18}}
        scan = {"total": 64, "passed": 60, "stale": 0, "failed": 4, "unbuilt": 0}
        score = compute_priority_score("a1", scan, {}, {})
        assert isinstance(score, float)


# ═══════════════════════════════════════════════════════════════════════════════
# Module 2: batch_dispatcher.py — BatchDispatcher class
# ═══════════════════════════════════════════════════════════════════════════════


class TestBatchDispatcherInit:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "t", "tracks": {}, "dispatch_history": [], "stats": {}
    })
    def test_defaults(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher()
        assert d.one_shot is False
        assert d.dry_run is False
        assert d.include_tracks is None
        assert d.exclude_tracks == set()

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "t", "tracks": {}, "dispatch_history": [], "stats": {}
    })
    def test_with_filters(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(include_tracks=["a1", "a2"], exclude_tracks=["b1"])
        assert d.include_tracks == {"a1", "a2"}
        assert "b1" in d.exclude_tracks


class TestBatchDispatcherShouldInclude:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "t", "tracks": {}, "dispatch_history": [], "stats": {}
    })
    def test_exclude_filter(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(exclude_tracks=["a1"])
        assert d._should_include_track("a1") is False
        assert d._should_include_track("a2") is True

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "t", "tracks": {}, "dispatch_history": [], "stats": {}
    })
    def test_include_filter(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(include_tracks=["a1"])
        assert d._should_include_track("a1") is True
        assert d._should_include_track("a2") is False

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "t", "tracks": {}, "dispatch_history": [], "stats": {}
    })
    def test_no_filter(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher()
        assert d._should_include_track("a1") is True


class TestBatchDispatcherRuntimeExceeded:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "t", "tracks": {}, "dispatch_history": [], "stats": {}
    })
    def test_no_limit(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher()
        assert d._runtime_exceeded() is False

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "t", "tracks": {}, "dispatch_history": [], "stats": {}
    })
    def test_not_exceeded(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(max_runtime_hours=10)
        assert d._runtime_exceeded() is False

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "t", "tracks": {}, "dispatch_history": [], "stats": {}
    })
    def test_exceeded(self, mock_load):
        import time
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(max_runtime_hours=0.0001)
        # Simulate time passing
        d.start_time = time.monotonic() - 3600
        assert d._runtime_exceeded() is True


class TestBatchDispatcherCountEscalated:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "t", "tracks": {}, "dispatch_history": [], "stats": {}
    })
    def test_no_failures_dir(self, mock_load, tmp_path):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher()
        with patch("batch_dispatcher.BATCH_STATE_DIR", tmp_path):
            assert d._count_escalated("a1") == 0

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "t", "tracks": {}, "dispatch_history": [], "stats": {}
    })
    def test_with_escalated(self, mock_load, tmp_path):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher()
        failures_dir = tmp_path / "failures" / "a1"
        failures_dir.mkdir(parents=True)
        (failures_dir / "mod1.json").write_text(json.dumps({"escalated": True}))
        (failures_dir / "mod2.json").write_text(json.dumps({"escalated": False}))
        with patch("batch_dispatcher.BATCH_STATE_DIR", tmp_path):
            assert d._count_escalated("a1") == 1


class TestBatchDispatcherGetEscalatedModules:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "t", "tracks": {}, "dispatch_history": [], "stats": {}
    })
    def test_returns_escalated(self, mock_load, tmp_path):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher()
        failures_dir = tmp_path / "a1"
        failures_dir.mkdir(parents=True)
        (failures_dir / "mod1.json").write_text(json.dumps({"slug": "intro", "escalated": True}))
        (failures_dir / "mod2.json").write_text(json.dumps({"slug": "other", "escalated": False}))
        with patch("batch_dispatcher.FAILURES_DIR", tmp_path):
            results = d._get_escalated_modules("a1")
            assert len(results) == 1
            assert results[0]["slug"] == "intro"


class TestBatchDispatcherPickTrack:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "t", "tracks": {}, "dispatch_history": [], "stats": {}
    })
    @patch("batch_dispatcher.compute_priority_score", return_value=5.0)
    def test_force_track(self, mock_score, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(force_track="a1")
        result = d._pick_track({})
        assert result == "a1"

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "t", "tracks": {}, "dispatch_history": [], "stats": {}
    })
    @patch("batch_dispatcher.compute_priority_score", return_value=5.0)
    def test_force_track_done(self, mock_score, mock_load):
        from batch_dispatcher import BatchDispatcher, get_track_dstate
        d = BatchDispatcher(force_track="a1")
        dstate = get_track_dstate(d.state, "a1")
        dstate["state"] = TrackState.DONE
        result = d._pick_track({})
        assert result is None

    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "t", "tracks": {}, "dispatch_history": [], "stats": {}
    })
    @patch("batch_dispatcher.compute_priority_score", return_value=5.0)
    def test_no_eligible(self, mock_score, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(include_tracks=["a1"])
        # All tracks BLOCKED
        d.state["tracks"]["a1"] = {"state": TrackState.BLOCKED, "stall_count": 0,
                                    "last_dispatch": None, "last_result": None,
                                    "cooldown_until": None, "dispatches": 0,
                                    "last_passed": 0, "last_failed": 0}
        result = d._pick_track({"a1": {}})
        assert result is None


class TestBatchDispatcherFormatTrackTable:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "t", "tracks": {}, "dispatch_history": [], "stats": {}
    })
    @patch("batch_dispatcher.compute_priority_score", return_value=3.5)
    def test_produces_table(self, mock_score, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(include_tracks=["a1"])
        d._count_escalated = MagicMock(return_value=0)
        scans = {"a1": {"total": 64, "passed": 50, "failed": 10, "stale": 2,
                        "unbuilt": 2, "pass_rate": 0.81}}
        table = d._format_track_table(scans)
        assert "a1" in table
        assert "81%" in table


class TestBatchDispatcherPrintSummary:
    @patch("batch_dispatcher.load_dispatcher_state", return_value={
        "started": "t", "tracks": {}, "dispatch_history": [],
        "stats": {"total_dispatches": 5, "total_cooldowns": 1,
                  "total_stalls": 0, "rotations_completed": 2}
    })
    def test_prints(self, mock_load):
        from batch_dispatcher import BatchDispatcher
        d = BatchDispatcher(include_tracks=["a1"])
        # Just confirm it doesn't crash
        d._print_summary()
