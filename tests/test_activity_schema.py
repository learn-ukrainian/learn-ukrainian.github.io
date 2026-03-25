"""
Tests for activity V2 JSON Schema validation.

Covers:
- Valid examples pass schema
- Invalid examples fail (missing required fields, wrong types)
- Each activity type has valid/invalid cases
- Inline activities require id field
- Semantic checks (duplicate ids)

Run with: .venv/bin/python -m pytest tests/test_activity_schema.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "activity-v2.schema.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def validator(schema) -> jsonschema.Draft7Validator:
    return jsonschema.Draft7Validator(schema)


def is_valid(validator: jsonschema.Draft7Validator, data: dict) -> bool:
    return validator.is_valid(data)


def get_errors(validator: jsonschema.Draft7Validator, data: dict) -> list[str]:
    return [e.message for e in validator.iter_errors(data)]


# ---------------------------------------------------------------------------
# Fixtures: minimal valid documents
# ---------------------------------------------------------------------------

MINIMAL_DOC = {"version": "1.0", "module": "test-module", "level": "a1"}


def _doc_with_inline(activities: list[dict]) -> dict:
    return {**MINIMAL_DOC, "inline": activities}


def _doc_with_workbook(activities: list[dict]) -> dict:
    return {**MINIMAL_DOC, "workbook": activities}


# ---------------------------------------------------------------------------
# Top-level structure tests
# ---------------------------------------------------------------------------


class TestTopLevel:
    def test_minimal_valid(self, validator):
        assert is_valid(validator, MINIMAL_DOC)

    def test_missing_version(self, validator):
        doc = {"module": "test", "level": "a1"}
        assert not is_valid(validator, doc)

    def test_missing_module(self, validator):
        doc = {"version": "1.0", "level": "a1"}
        assert not is_valid(validator, doc)

    def test_missing_level(self, validator):
        doc = {"version": "1.0", "module": "test"}
        assert not is_valid(validator, doc)

    def test_invalid_version_format(self, validator):
        doc = {**MINIMAL_DOC, "version": "v1"}
        assert not is_valid(validator, doc)

    def test_extra_properties_rejected(self, validator):
        doc = {**MINIMAL_DOC, "extra_field": "bad"}
        assert not is_valid(validator, doc)

    def test_empty_inline_array(self, validator):
        doc = {**MINIMAL_DOC, "inline": []}
        assert is_valid(validator, doc)

    def test_empty_workbook_array(self, validator):
        doc = {**MINIMAL_DOC, "workbook": []}
        assert is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Inline activities require id
# ---------------------------------------------------------------------------


class TestInlineId:
    def test_inline_with_id_valid(self, validator):
        doc = _doc_with_inline([{
            "id": "quiz-test",
            "type": "quiz",
            "instruction": "Test",
            "items": [{
                "question": "Q?",
                "options": ["a", "b", "c"],
                "correct": 0,
            }],
        }])
        assert is_valid(validator, doc)

    def test_inline_without_id_invalid(self, validator):
        doc = _doc_with_inline([{
            "type": "quiz",
            "instruction": "Test",
            "items": [{
                "question": "Q?",
                "options": ["a", "b", "c"],
                "correct": 0,
            }],
        }])
        assert not is_valid(validator, doc)

    def test_inline_id_pattern(self, validator):
        """Id must be lowercase alphanumeric with hyphens."""
        doc = _doc_with_inline([{
            "id": "UPPERCASE",
            "type": "quiz",
            "instruction": "Test",
            "items": [{
                "question": "Q?",
                "options": ["a", "b", "c"],
                "correct": 0,
            }],
        }])
        assert not is_valid(validator, doc)

    def test_workbook_without_id_valid(self, validator):
        """Workbook activities do NOT require id."""
        doc = _doc_with_workbook([{
            "type": "quiz",
            "instruction": "Test",
            "items": [{
                "question": "Q?",
                "options": ["a", "b", "c"],
                "correct": 0,
            }],
        }])
        assert is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------


class TestQuiz:
    def test_valid_quiz(self, validator):
        doc = _doc_with_workbook([{
            "type": "quiz",
            "instruction": "Оберіть правильний варіант",
            "items": [{
                "question": "_____ стіл",
                "options": ["мій", "моя", "моє"],
                "correct": 0,
            }],
        }])
        assert is_valid(validator, doc)

    def test_quiz_missing_items(self, validator):
        doc = _doc_with_workbook([{
            "type": "quiz",
            "instruction": "Test",
        }])
        assert not is_valid(validator, doc)

    def test_quiz_missing_instruction(self, validator):
        doc = _doc_with_workbook([{
            "type": "quiz",
            "items": [{
                "question": "Q?",
                "options": ["a", "b", "c"],
                "correct": 0,
            }],
        }])
        assert not is_valid(validator, doc)

    def test_quiz_correct_out_of_range_type(self, validator):
        doc = _doc_with_workbook([{
            "type": "quiz",
            "instruction": "Test",
            "items": [{
                "question": "Q?",
                "options": ["a", "b", "c"],
                "correct": "zero",  # should be integer
            }],
        }])
        assert not is_valid(validator, doc)

    def test_quiz_too_few_options(self, validator):
        doc = _doc_with_workbook([{
            "type": "quiz",
            "instruction": "Test",
            "items": [{
                "question": "Q?",
                "options": ["a", "b"],
                "correct": 0,
            }],
        }])
        assert not is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Fill-in
# ---------------------------------------------------------------------------


class TestFillIn:
    def test_valid_fill_in(self, validator):
        doc = _doc_with_workbook([{
            "type": "fill-in",
            "instruction": "Вставте слово",
            "items": [{
                "sentence": "Це ____ стіл.",
                "answer": "мій",
            }],
        }])
        assert is_valid(validator, doc)

    def test_fill_in_with_options(self, validator):
        doc = _doc_with_workbook([{
            "type": "fill-in",
            "instruction": "Вставте",
            "items": [{
                "sentence": "Це ____ кімната.",
                "answer": "моя",
                "options": ["мій", "моя", "моє"],
            }],
        }])
        assert is_valid(validator, doc)

    def test_fill_in_missing_sentence(self, validator):
        doc = _doc_with_workbook([{
            "type": "fill-in",
            "instruction": "Test",
            "items": [{"answer": "test"}],
        }])
        assert not is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Match-up
# ---------------------------------------------------------------------------


class TestMatchUp:
    def test_valid_match_up(self, validator):
        doc = _doc_with_workbook([{
            "type": "match-up",
            "instruction": "З'єднайте пари",
            "pairs": [
                {"left": "стіл", "right": "він"},
                {"left": "книга", "right": "вона"},
                {"left": "вікно", "right": "воно"},
            ],
        }])
        assert is_valid(validator, doc)

    def test_match_up_too_few_pairs(self, validator):
        doc = _doc_with_workbook([{
            "type": "match-up",
            "instruction": "Test",
            "pairs": [
                {"left": "a", "right": "b"},
                {"left": "c", "right": "d"},
            ],
        }])
        assert not is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Group-sort
# ---------------------------------------------------------------------------


class TestGroupSort:
    def test_valid_group_sort(self, validator):
        doc = _doc_with_workbook([{
            "type": "group-sort",
            "instruction": "Розподіліть",
            "groups": [
                {"label": "він", "items": ["стіл"]},
                {"label": "вона", "items": ["книга"]},
            ],
        }])
        assert is_valid(validator, doc)

    def test_group_sort_one_group_invalid(self, validator):
        doc = _doc_with_workbook([{
            "type": "group-sort",
            "instruction": "Test",
            "groups": [
                {"label": "він", "items": ["стіл"]},
            ],
        }])
        assert not is_valid(validator, doc)


# ---------------------------------------------------------------------------
# True-false
# ---------------------------------------------------------------------------


class TestTrueFalse:
    def test_valid_true_false(self, validator):
        doc = _doc_with_workbook([{
            "type": "true-false",
            "instruction": "Правда чи ні?",
            "items": [{
                "statement": "Стіл — жіночого роду.",
                "correct": False,
            }],
        }])
        assert is_valid(validator, doc)

    def test_true_false_correct_not_bool(self, validator):
        doc = _doc_with_workbook([{
            "type": "true-false",
            "instruction": "Test",
            "items": [{
                "statement": "Test",
                "correct": "yes",
            }],
        }])
        assert not is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Error-correction
# ---------------------------------------------------------------------------


class TestErrorCorrection:
    def test_valid_error_correction(self, validator):
        doc = _doc_with_workbook([{
            "type": "error-correction",
            "instruction": "Виправте",
            "items": [{
                "sentence": "Це моя стіл.",
                "error": "моя",
                "correction": "мій",
            }],
        }])
        assert is_valid(validator, doc)

    def test_error_correction_missing_correction(self, validator):
        doc = _doc_with_workbook([{
            "type": "error-correction",
            "instruction": "Test",
            "items": [{
                "sentence": "Test",
                "error": "test",
            }],
        }])
        assert not is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Anagram
# ---------------------------------------------------------------------------


class TestAnagram:
    def test_valid_anagram(self, validator):
        doc = _doc_with_workbook([{
            "type": "anagram",
            "instruction": "Складіть слово",
            "items": [{
                "letters": ["к", "н", "и", "г", "а"],
                "answer": "книга",
                "hint": "book",
            }],
        }])
        assert is_valid(validator, doc)

    def test_anagram_letters_not_array(self, validator):
        doc = _doc_with_workbook([{
            "type": "anagram",
            "instruction": "Test",
            "items": [{
                "letters": "кнга",
                "answer": "книга",
            }],
        }])
        assert not is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Translate
# ---------------------------------------------------------------------------


class TestTranslate:
    def test_valid_translate(self, validator):
        doc = _doc_with_workbook([{
            "type": "translate",
            "instruction": "Перекладіть",
            "items": [{"source": "my table"}],
        }])
        assert is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Unjumble
# ---------------------------------------------------------------------------


class TestUnjumble:
    def test_valid_unjumble(self, validator):
        doc = _doc_with_workbook([{
            "type": "unjumble",
            "instruction": "Складіть речення",
            "items": [{
                "words": ["це", "мій", "стіл"],
                "correct_order": ["Це", "мій", "стіл"],
            }],
        }])
        assert is_valid(validator, doc)

    def test_unjumble_too_few_words(self, validator):
        doc = _doc_with_workbook([{
            "type": "unjumble",
            "instruction": "Test",
            "items": [{
                "words": ["a", "b"],
                "correct_order": ["a", "b"],
            }],
        }])
        assert not is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Cloze
# ---------------------------------------------------------------------------


class TestCloze:
    def test_valid_cloze(self, validator):
        doc = _doc_with_workbook([{
            "type": "cloze",
            "instruction": "Заповніть",
            "text": "Це {{1}} стіл.",
            "blanks": [{
                "id": 1,
                "answer": "мій",
                "options": ["мій", "моя", "моє"],
            }],
        }])
        assert is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Select
# ---------------------------------------------------------------------------


class TestSelect:
    def test_valid_select(self, validator):
        doc = _doc_with_workbook([{
            "type": "select",
            "instruction": "Оберіть",
            "items": [{
                "question": "Оберіть правильні",
                "options": [
                    {"text": "A", "correct": True},
                    {"text": "B", "correct": False},
                    {"text": "C", "correct": True},
                ],
            }],
        }])
        assert is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Observe
# ---------------------------------------------------------------------------


class TestObserve:
    def test_valid_observe(self, validator):
        doc = _doc_with_workbook([{
            "type": "observe",
            "examples": ["стіл → він", "книга → вона"],
            "prompt": "What pattern do you see?",
        }])
        assert is_valid(validator, doc)

    def test_observe_missing_prompt(self, validator):
        doc = _doc_with_workbook([{
            "type": "observe",
            "examples": ["a", "b"],
        }])
        assert not is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Classify
# ---------------------------------------------------------------------------


class TestClassify:
    def test_valid_classify(self, validator):
        doc = _doc_with_workbook([{
            "type": "classify",
            "instruction": "Класифікуйте",
            "categories": [
                {"label": "він", "items": ["стіл"]},
                {"label": "вона", "items": ["книга"]},
            ],
        }])
        assert is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Mark-the-words
# ---------------------------------------------------------------------------


class TestMarkTheWords:
    def test_valid_mark_the_words(self, validator):
        doc = _doc_with_workbook([{
            "type": "mark-the-words",
            "instruction": "Знайдіть",
            "text": "Бажаючі студенти прийшли.",
            "target_words": ["Бажаючі"],
        }])
        assert is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Highlight-morphemes
# ---------------------------------------------------------------------------


class TestHighlightMorphemes:
    def test_valid_highlight_morphemes(self, validator):
        doc = _doc_with_workbook([{
            "type": "highlight-morphemes",
            "instruction": "Визначте морфеми",
            "items": [{
                "word": "прийшов",
                "morphemes": [
                    {"text": "при", "type": "prefix"},
                    {"text": "йш", "type": "root"},
                    {"text": "ов", "type": "suffix"},
                ],
            }],
        }])
        assert is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Image-to-letter
# ---------------------------------------------------------------------------


class TestImageToLetter:
    def test_valid_image_to_letter(self, validator):
        doc = _doc_with_workbook([{
            "type": "image-to-letter",
            "instruction": "Оберіть літеру",
            "items": [{
                "image": "apple-emoji",
                "letter": "Я",
                "options": ["А", "Я", "О"],
            }],
        }])
        assert is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Letter-grid
# ---------------------------------------------------------------------------


class TestLetterGrid:
    def test_valid_letter_grid(self, validator):
        doc = _doc_with_workbook([{
            "type": "letter-grid",
            "letters": [
                {"upper": "А", "lower": "а"},
                {"upper": "Б", "lower": "б", "name": "бе"},
            ],
        }])
        assert is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Phrase-table
# ---------------------------------------------------------------------------


class TestPhraseTable:
    def test_valid_phrase_table(self, validator):
        doc = _doc_with_workbook([{
            "type": "phrase-table",
            "groups": [{
                "label": "Привітання",
                "phrases": ["Привіт!", "Добрий день!"],
            }],
        }])
        assert is_valid(validator, doc)

    def test_phrase_table_object_phrases(self, validator):
        doc = _doc_with_workbook([{
            "type": "phrase-table",
            "groups": [{
                "label": "Привітання",
                "phrases": [
                    {"phrase": "Привіт!", "context": "informal"},
                ],
            }],
        }])
        assert is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Seminar types
# ---------------------------------------------------------------------------


class TestCriticalAnalysis:
    def test_valid(self, validator):
        doc = _doc_with_workbook([{
            "type": "critical-analysis",
            "prompt": "Проаналізуйте текст.",
            "evaluation_criteria": ["Аргументація"],
        }])
        assert is_valid(validator, doc)


class TestEssayResponse:
    def test_valid(self, validator):
        doc = _doc_with_workbook([{
            "type": "essay-response",
            "prompt": "Напишіть есе.",
            "min_words": 100,
        }])
        assert is_valid(validator, doc)

    def test_missing_prompt(self, validator):
        doc = _doc_with_workbook([{
            "type": "essay-response",
            "min_words": 100,
        }])
        assert not is_valid(validator, doc)


class TestSourceEvaluation:
    def test_valid(self, validator):
        doc = _doc_with_workbook([{
            "type": "source-evaluation",
            "source_text": "Джерело...",
            "criteria": ["достовірність"],
            "guiding_questions": ["Хто автор?"],
        }])
        assert is_valid(validator, doc)


class TestReading:
    def test_valid(self, validator):
        doc = _doc_with_workbook([{
            "type": "reading",
            "passage": "Текст для читання...",
            "questions": ["Про що текст?"],
        }])
        assert is_valid(validator, doc)


class TestComparativeStudy:
    def test_valid(self, validator):
        doc = _doc_with_workbook([{
            "type": "comparative-study",
            "items_to_compare": ["Текст A", "Текст B"],
            "criteria": ["стиль"],
            "prompt": "Порівняйте.",
        }])
        assert is_valid(validator, doc)


class TestAuthorialIntent:
    def test_valid(self, validator):
        doc = _doc_with_workbook([{
            "type": "authorial-intent",
            "excerpt": "Уривок тексту...",
            "questions": ["Що хотів сказати автор?"],
        }])
        assert is_valid(validator, doc)


class TestDebate:
    def test_valid(self, validator):
        doc = _doc_with_workbook([{
            "type": "debate",
            "debate_question": "Чи потрібна реформа?",
            "positions": [
                {"label": "За", "arguments": ["Аргумент 1"]},
                {"label": "Проти", "arguments": ["Аргумент 2"]},
            ],
        }])
        assert is_valid(validator, doc)


class TestEtymologyTrace:
    def test_valid(self, validator):
        doc = _doc_with_workbook([{
            "type": "etymology-trace",
            "instruction": "Прослідкуйте еволюцію",
            "stages": [
                {"period": "ДРС XI ст.", "form": "градъ"},
                {"period": "Сучасна", "form": "город"},
            ],
        }])
        assert is_valid(validator, doc)


class TestTranslationCritique:
    def test_valid(self, validator):
        doc = _doc_with_workbook([{
            "type": "translation-critique",
            "original": "Оригінальний текст",
            "translations": [
                {"text": "Переклад 1"},
                {"text": "Переклад 2", "quality": "good"},
            ],
        }])
        assert is_valid(validator, doc)


class TestTranscription:
    def test_valid(self, validator):
        doc = _doc_with_workbook([{
            "type": "transcription",
            "original": "ДРС текст",
            "answer": "Сучасний текст",
            "hints": ["підказка"],
        }])
        assert is_valid(validator, doc)


class TestPaleographyAnalysis:
    def test_valid(self, validator):
        doc = _doc_with_workbook([{
            "type": "paleography-analysis",
            "instruction": "Визначте риси",
            "image_url": "/images/manuscript.jpg",
            "hotspots": [{"x": 10, "y": 20, "label": "Устав"}],
        }])
        assert is_valid(validator, doc)


class TestDialectComparison:
    def test_valid(self, validator):
        doc = _doc_with_workbook([{
            "type": "dialect-comparison",
            "text_a": "Київський текст",
            "text_b": "Галицький текст",
            "label_a": "Київ",
            "label_b": "Львів",
            "features": [{
                "feature": "Рефлекс ě",
                "variant_a": "і",
                "variant_b": "і",
            }],
        }])
        assert is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Grammar-identify
# ---------------------------------------------------------------------------


class TestGrammarIdentify:
    def test_valid(self, validator):
        doc = _doc_with_workbook([{
            "type": "grammar-identify",
            "instruction": "Визначте рід",
            "items": [{
                "word": "стіл",
                "task": "Визначте рід",
                "options": ["чоловічий", "жіночий", "середній"],
            }],
        }])
        assert is_valid(validator, doc)


# ---------------------------------------------------------------------------
# Full file validation (things-have-gender.yaml)
# ---------------------------------------------------------------------------


class TestExampleFile:
    """Validate the reference implementation file."""

    def test_things_have_gender_passes(self, validator):
        path = (
            PROJECT_ROOT
            / "curriculum"
            / "l2-uk-en"
            / "a1"
            / "activities"
            / "things-have-gender.yaml"
        )
        if not path.exists():
            pytest.skip("Example file not yet created")

        with open(path) as f:
            data = yaml.safe_load(f)

        errors = get_errors(validator, data)
        assert not errors, f"Validation errors: {errors}"

    def test_c1_b2_review_bridge_passes(self, validator):
        path = (
            PROJECT_ROOT
            / "curriculum"
            / "l2-uk-en"
            / "c1"
            / "activities"
            / "b2-review-bridge.yaml"
        )
        if not path.exists():
            pytest.skip("C1 file not yet migrated")

        with open(path) as f:
            data = yaml.safe_load(f)

        errors = get_errors(validator, data)
        assert not errors, f"Validation errors: {errors}"


# ---------------------------------------------------------------------------
# Semantic validation (via validate_activities_v2.py)
# ---------------------------------------------------------------------------


class TestSemanticChecks:
    """Test the semantic validation functions from the script."""

    def test_duplicate_inline_ids_detected(self):
        """Import and test the duplicate id checker."""
        import sys
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from validate_activities_v2 import _check_duplicate_ids

        data = {
            "inline": [
                {"id": "quiz-1", "type": "quiz"},
                {"id": "quiz-1", "type": "fill-in"},
            ]
        }
        errors = _check_duplicate_ids(data)
        assert len(errors) == 1
        assert "duplicate id 'quiz-1'" in errors[0]

    def test_no_duplicate_ids(self):
        import sys
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from validate_activities_v2 import _check_duplicate_ids

        data = {
            "inline": [
                {"id": "quiz-1", "type": "quiz"},
                {"id": "quiz-2", "type": "fill-in"},
            ]
        }
        errors = _check_duplicate_ids(data)
        assert len(errors) == 0
