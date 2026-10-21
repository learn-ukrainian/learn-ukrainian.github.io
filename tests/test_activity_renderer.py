"""Tests for activity_renderer — YAML → JSX transformation.

Issue: #1043
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure scripts/ on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build.activity_renderer import render_activity_to_jsx

# ---------------------------------------------------------------------------
# Core activity types
# ---------------------------------------------------------------------------


class TestQuiz:
    def test_basic(self):
        act = {
            "type": "quiz",
            "instruction": "Оберіть правильний варіант",
            "items": [
                {
                    "question": "_____ стіл",
                    "options": ["мій", "моя", "моє"],
                    "correct": 0,
                },
            ],
        }
        jsx = render_activity_to_jsx(act)
        assert "<Quiz" in jsx
        assert 'client:only="react"' in jsx
        assert '"correct": true' in jsx or '"correct":true' in jsx
        # First option is correct
        parsed = _extract_prop(jsx, "questions")
        assert parsed[0]["options"][0]["correct"] is True
        assert parsed[0]["options"][1]["correct"] is False


class TestFillIn:
    def test_basic(self):
        act = {
            "type": "fill-in",
            "instruction": "Вставте правильне слово",
            "items": [
                {"sentence": "Це ____ кімната.", "answer": "моя", "options": ["мій", "моя", "моє"]},
            ],
        }
        jsx = render_activity_to_jsx(act)
        assert "<FillIn" in jsx
        parsed = _extract_prop(jsx, "items")
        assert parsed[0]["answer"] == "моя"
        assert parsed[0]["options"] == ["мій", "моя", "моє"]


class TestMatchUp:
    def test_basic(self):
        act = {
            "type": "match-up",
            "instruction": "З'єднайте пари",
            "pairs": [
                {"left": "стіл", "right": "він"},
                {"left": "книга", "right": "вона"},
            ],
        }
        jsx = render_activity_to_jsx(act)
        assert "<MatchUp" in jsx
        parsed = _extract_prop(jsx, "pairs")
        assert len(parsed) == 2
        assert parsed[0]["left"] == "стіл"


class TestGroupSort:
    def test_groups_as_dict(self):
        """GroupSort React expects groups as {label: items[]} dict."""
        act = {
            "type": "group-sort",
            "instruction": "Sort",
            "groups": [
                {"label": "Masculine", "items": ["стіл", "зошит"]},
                {"label": "Feminine", "items": ["книга"]},
            ],
        }
        jsx = render_activity_to_jsx(act)
        assert "<GroupSort" in jsx
        parsed = _extract_prop(jsx, "groups")
        assert isinstance(parsed, dict)
        assert parsed["Masculine"] == ["стіл", "зошит"]


class TestTrueFalse:
    def test_correct_to_is_true(self):
        """YAML uses 'correct' bool, React uses 'isTrue'."""
        act = {
            "type": "true-false",
            "instruction": "True or false?",
            "items": [
                {"statement": "Стіл — жіночого роду.", "correct": False, "explanation": "Ні."},
            ],
        }
        jsx = render_activity_to_jsx(act)
        assert "<TrueFalse" in jsx
        parsed = _extract_prop(jsx, "items")
        assert parsed[0]["isTrue"] is False
        assert parsed[0]["explanation"] == "Ні."


class TestErrorCorrection:
    def test_basic(self):
        act = {
            "type": "error-correction",
            "instruction": "Fix the error",
            "items": [
                {
                    "sentence": "Це моя стіл.",
                    "error": "моя",
                    "correction": "мій",
                    "options": ["мій", "моє", "моя"],
                    "explanation": "Стіл — чоловічого роду.",
                },
            ],
        }
        jsx = render_activity_to_jsx(act)
        assert "<ErrorCorrection" in jsx
        parsed = _extract_prop(jsx, "items")
        assert parsed[0]["errorWord"] == "моя"
        assert parsed[0]["correctForm"] == "мій"

    def test_derives_word_and_sentence_shaped_options(self):
        act = {
            "type": "error-correction",
            "items": [
                {
                    "sentence": "Вона вчителька.",
                    "error": "вчителька",
                    "correction": "Вона вчитель.",
                    "options": [
                        "Вона вчитель.",
                        "Вона вчителька.",
                        "вчитель",
                    ],
                }
            ],
        }

        parsed = _extract_prop(render_activity_to_jsx(act), "items")
        assert parsed[0]["correctForm"] == "вчитель"
        # Sentence variants that reduce to the same form render as one chip.
        assert parsed[0]["options"] == ["вчитель", "вчителька"]

    def test_derives_phrase_replacement(self):
        act = {
            "type": "error-correction",
            "items": [
                {
                    "sentence": "Моє ім'я є Олена.",
                    "error": "Моє ім'я є",
                    "correction": "Мене звати Олена.",
                }
            ],
        }

        parsed = _extract_prop(render_activity_to_jsx(act), "items")
        assert parsed[0]["correctForm"] == "Мене звати"

    def test_preserves_shared_error_boundary_words(self):
        act = {
            "type": "error-correction",
            "items": [
                {
                    "sentence": "Я бачу гарна дівчину.",
                    "error": "гарна дівчину",
                    "correction": "Я бачу гарну дівчину.",
                }
            ],
        }

        parsed = _extract_prop(render_activity_to_jsx(act), "items")
        assert parsed[0]["correctForm"] == "гарну дівчину"

    def test_punctuation_and_non_derivable_items_pass_through(self):
        act = {
            "type": "error-correction",
            "items": [
                {
                    "sentence": "Вона вчителька?",
                    "error": "?",
                    "correction": "Вона вчителька.",
                },
                {
                    "sentence": "Вона вчителька?",
                    "error": "?",
                    "correction": ".",
                },
                {
                    "sentence": "Вона вчителька.",
                    "error": "вчителька",
                    "correction": "Учитель працює.",
                },
            ],
        }

        parsed = _extract_prop(render_activity_to_jsx(act), "items")
        assert parsed[0]["correctForm"] == "Вона вчителька."
        assert parsed[1]["correctForm"] == "."
        assert parsed[2]["correctForm"] == "Учитель працює."


class TestAnagram:
    def test_letters_joined(self):
        """YAML letters[] → React scrambled (space-separated string)."""
        act = {
            "type": "anagram",
            "instruction": "Unscramble",
            "items": [{"letters": ["к", "н", "и", "г", "а"], "answer": "книга", "hint": "book"}],
        }
        jsx = render_activity_to_jsx(act)
        assert "<Anagram" in jsx
        parsed = _extract_prop(jsx, "items")
        assert parsed[0]["scrambled"] == "к н и г а"
        assert parsed[0]["hint"] == "book"


class TestTranslate:
    def test_with_options(self):
        act = {
            "type": "translate",
            "instruction": "Translate",
            "items": [
                {
                    "source": "my table",
                    "options": [
                        {"text": "мій стіл", "correct": True},
                        {"text": "моя стіл", "correct": False},
                    ],
                },
            ],
        }
        jsx = render_activity_to_jsx(act)
        assert "<Translate" in jsx
        parsed = _extract_prop(jsx, "questions")
        assert parsed[0]["source"] == "my table"


class TestUnjumble:
    def test_words_and_order(self):
        act = {
            "type": "unjumble",
            "instruction": "Build sentence",
            "items": [
                {
                    "words": ["є", "мене", "у", "стіл"],
                    "correct_order": ["у", "мене", "є", "стіл"],
                },
            ],
        }
        jsx = render_activity_to_jsx(act)
        assert "<Unjumble" in jsx
        parsed = _extract_prop(jsx, "items")
        assert parsed[0]["words"] == "є / мене / у / стіл"
        assert parsed[0]["answer"] == "у мене є стіл"
class TestGrammarIdentify:
    def test_field_mapping(self):
        act = {
            "type": "grammar-identify",
            "instruction": "Визначте рід",
            "items": [{"word": "стіл", "task": "Визначте рід", "answer": "чоловічий"}],
        }
        jsx = render_activity_to_jsx(act)
        assert "<GrammarIdentify" in jsx
        parsed = _extract_prop(jsx, "items")
        assert parsed[0]["text"] == "стіл"
        assert parsed[0]["form"] == "Визначте рід"


class TestOddOneOut:
    def test_options_answer_alias_mapping(self):
        act = {
            "type": "odd-one-out",
            "instruction": "Оберіть зайве.",
            "items": [
                {
                    "options": ["сильніший", "молодший", "більш цікавий", "дорожчий"],
                    "answer": "більш цікавий",
                    "explanation": "Це складена форма, решта прості.",
                },
            ],
        }
        jsx = render_activity_to_jsx(act)
        parsed = _extract_prop(jsx, "items")
        assert parsed[0]["words"] == [
            "сильніший",
            "молодший",
            "більш цікавий",
            "дорожчий",
        ]
        assert parsed[0]["correct"] == 2


class TestHighlightMorphemes:
    def test_answer_alias_mapping(self):
        act = {
            "type": "highlight-morphemes",
            "instruction": "Позначте суфікс.",
            "items": [{"word": "сильніший", "answer": "-іш-"}],
        }
        jsx = render_activity_to_jsx(act)
        parsed = _extract_prop(jsx, "items")
        assert parsed[0]["morphemes"] == [{"text": "-іш-", "type": "suffix"}]


class TestObserve:
    def test_instruction_prop(self):
        from scripts.build.fresh.assemble import component_props_from_jsx

        instruction = 'Compare "first" and second.'
        jsx = render_activity_to_jsx(
            {
                "type": "observe",
                "examples": ["first", "second"],
                "prompt": "What pattern?",
                "instruction": instruction,
            }
        )
        assert component_props_from_jsx(jsx)["instruction"] == instruction


class TestClassify:
    def test_symbol_hint(self):
        act = {
            "type": "classify",
            "instruction": "Classify",
            "categories": [
                {"label": "Vowels", "symbol_hint": "V", "items": ["а", "е"]},
                {"label": "Consonants", "items": ["б", "в"]},
            ],
        }
        jsx = render_activity_to_jsx(act)
        assert "<Classify" in jsx
        parsed = _extract_prop(jsx, "categories")
        assert parsed[0]["symbolHint"] == "V"
        assert "symbolHint" not in parsed[1]


# ---------------------------------------------------------------------------
# Seminar activity types
# ---------------------------------------------------------------------------
class TestDebate:
    def test_positions_mapping(self):
        act = {
            "type": "debate",
            "instruction": "Analyze",
            "debate_question": "Was X correct?",
            "positions": [
                {"label": "Pro", "arguments": ["Arg 1", "Arg 2"]},
                {"label": "Con", "arguments": ["Against 1"]},
            ],
        }
        jsx = render_activity_to_jsx(act)
        assert "<Debate" in jsx
        parsed = _extract_prop(jsx, "positions")
        assert parsed[0]["name"] == "Pro"
        assert "Arg 1" in parsed[0]["argument"]
class TestDialectComparison:
    def test_features_mapping(self):
        act = {
            "type": "dialect-comparison",
            "instruction": "Compare",
            "text_a": "Text A",
            "text_b": "Text B",
            "label_a": "Полтавська",
            "label_b": "Галицька",
            "features": [
                {
                    "feature": "Vowel reduction",
                    "variant_a": "о→а",
                    "variant_b": "о→о",
                    "explanation": "Differs in unstressed position",
                },
            ],
        }
        jsx = render_activity_to_jsx(act)
        assert "<DialectComparison" in jsx
        parsed = _extract_prop(jsx, "features")
        assert parsed[0]["featureName"] == "Vowel reduction"
        assert parsed[0]["valueA"] == "о→а"


# ---------------------------------------------------------------------------
# Unknown type
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Import generation
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_prop(jsx: str, prop_name: str):
    """Extract a JSON prop value from JSX string."""
    # Find prop_name={...} and parse the JSON

    pattern = rf"{prop_name}=\{{(.*)\}}"
    # Try to find the prop — greedy but we need to handle nested braces
    # Simple approach: find start of prop, then balance braces
    start_marker = f"{prop_name}={{"
    idx = jsx.find(start_marker)
    if idx < 0:
        raise ValueError(f"Prop {prop_name} not found in: {jsx[:200]}")

    json_start = idx + len(start_marker)
    # Balance braces
    depth = 1
    i = json_start
    while i < len(jsx) and depth > 0:
        if jsx[i] == "{":
            depth += 1
        elif jsx[i] == "}":
            depth -= 1
        i += 1
    json_str = jsx[json_start : i - 1]
    return json.loads(json_str)
