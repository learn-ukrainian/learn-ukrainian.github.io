"""Tests for activity_renderer — YAML → JSX transformation.

Issue: #1043
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure scripts/ on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build.activity_renderer import get_required_imports, render_activity_to_jsx

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

    def test_instruction_prop(self):
        act = {
            "type": "quiz",
            "instruction": "Choose one",
            "items": [{"question": "Q", "options": ["A", "B", "C"], "correct": 1}],
        }
        jsx = render_activity_to_jsx(act)
        assert "Choose one" in jsx


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

    def test_no_options(self):
        act = {
            "type": "fill-in",
            "instruction": "Fill in",
            "items": [{"sentence": "Я ____.", "answer": "працюю"}],
        }
        jsx = render_activity_to_jsx(act)
        parsed = _extract_prop(jsx, "items")
        assert "options" not in parsed[0]


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


class TestCloze:
    def test_basic(self):
        act = {
            "type": "cloze",
            "instruction": "Fill the gaps",
            "text": "Це {1} стіл.",
            "blanks": [{"id": 1, "answer": "мій", "options": ["мій", "моя", "моє"]}],
        }
        jsx = render_activity_to_jsx(act)
        assert "<Cloze" in jsx
        assert "passage" in jsx


class TestSelect:
    def test_basic(self):
        act = {
            "type": "select",
            "instruction": "Select all",
            "items": [
                {
                    "question": "Which are feminine?",
                    "options": [
                        {"text": "книга", "correct": True},
                        {"text": "стіл", "correct": False},
                    ],
                },
            ],
        }
        jsx = render_activity_to_jsx(act)
        assert "<Select" in jsx


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


class TestObserve:
    def test_basic(self):
        act = {
            "type": "observe",
            "examples": ["стіл → він", "книга → вона"],
            "prompt": "What pattern?",
        }
        jsx = render_activity_to_jsx(act)
        assert "<Observe" in jsx
        assert "What pattern?" in jsx


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


class TestEssayResponse:
    def test_basic(self):
        act = {
            "type": "essay-response",
            "instruction": "Write an essay",
            "prompt": "Порівняйте два описи...",
            "min_words": 150,
            "model_answer": "Example answer.",
            "evaluation_criteria": ["Аргументація", "Мова"],
        }
        jsx = render_activity_to_jsx(act)
        assert "<EssayResponse" in jsx
        assert "Порівняйте" in jsx


class TestSourceEvaluation:
    def test_with_metadata(self):
        act = {
            "type": "source-evaluation",
            "instruction": "Evaluate",
            "source_text": "Some historical text...",
            "source_metadata": {"author": "Hrushevsky", "date": "1904"},
            "criteria": ["reliability", "bias"],
            "guiding_questions": ["Who wrote this?"],
        }
        jsx = render_activity_to_jsx(act)
        assert "<SourceEvaluation" in jsx
        assert "Hrushevsky" in jsx


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


class TestEtymologyTrace:
    def test_stages_mapping(self):
        act = {
            "type": "etymology-trace",
            "instruction": "Trace",
            "stages": [
                {"period": "Old East Slavic", "form": "столъ", "notes": "From Proto-Slavic"},
                {"period": "Modern Ukrainian", "form": "стіл"},
            ],
        }
        jsx = render_activity_to_jsx(act)
        assert "<EtymologyTrace" in jsx


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


class TestUnknownType:
    def test_returns_comment(self):
        act = {"type": "nonexistent-type"}
        jsx = render_activity_to_jsx(act)
        assert jsx == "<!-- Unknown activity type: nonexistent-type -->"


# ---------------------------------------------------------------------------
# Import generation
# ---------------------------------------------------------------------------


class TestGetRequiredImports:
    def test_deduplicates(self):
        activities = [
            {"type": "quiz"},
            {"type": "quiz"},
            {"type": "fill-in"},
        ]
        imports = get_required_imports(activities)
        assert len(imports) == 2
        assert any("Quiz" in i for i in imports)
        assert any("FillIn" in i for i in imports)

    def test_sorted(self):
        activities = [{"type": "true-false"}, {"type": "anagram"}]
        imports = get_required_imports(activities)
        # Anagram < TrueFalse alphabetically
        assert imports[0] < imports[1]

    def test_unknown_type_skipped(self):
        activities = [{"type": "nonexistent"}]
        imports = get_required_imports(activities)
        assert len(imports) == 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_prop(jsx: str, prop_name: str):
    """Extract a JSON prop value from JSX string."""
    # Find prop_name={...} and parse the JSON

    pattern = rf'{prop_name}=\{{(.*)\}}'
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
        if jsx[i] == '{':
            depth += 1
        elif jsx[i] == '}':
            depth -= 1
        i += 1
    json_str = jsx[json_start:i - 1]
    return json.loads(json_str)
