"""
Tests for YAML activity parsing, validation, and conversion.
"""


# Add scripts to path
import json
import sys
from pathlib import Path

import jsonschema
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from yaml_activities import (
    ActivityParser,
    MatchPair,
    MatchUpActivity,
    QuizActivity,
    QuizItem,
    QuizOption,
    ValidationResult,
)

# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def parser():
    return ActivityParser()


@pytest.fixture
def sample_yaml_path():
    return Path(__file__).parent / 'fixtures' / 'sample.activities.yaml'


@pytest.fixture
def a2_activity_validator():
    schema_path = Path(__file__).parent.parent / "schemas" / "activities-a2.schema.json"
    return jsonschema.Draft7Validator(json.loads(schema_path.read_text(encoding="utf-8")))


@pytest.fixture
def valid_quiz():
    return QuizActivity(
        title="Test Quiz",
        items=[
            QuizItem(
                question=f"Question {i+1}?",
                options=[
                    QuizOption("Correct", True),
                    QuizOption("Wrong 1", False),
                    QuizOption("Wrong 2", False),
                    QuizOption("Wrong 3", False),
                ]
            )
            for i in range(8)  # B1 needs 8 items
        ]
    )


@pytest.fixture
def valid_match_up():
    return MatchUpActivity(
        title="Test Match",
        pairs=[
            MatchPair(left=f"Left {i+1}", right=f"Right {i+1}")
            for i in range(8)  # B1 needs 8 pairs
        ]
    )


# =============================================================================
# PARSING TESTS
# =============================================================================

class TestParsing:
    """Test YAML file parsing."""

    def test_parse_sample_file(self, parser, sample_yaml_path):
        """Can parse the sample YAML file."""
        activities = parser.parse(sample_yaml_path)
        # sample.activities.yaml has 11 activities
        assert len(activities) == 11
        assert activities[0].type == 'quiz'

    def test_parse_preserves_titles(self, parser, sample_yaml_path):
        """Titles are preserved during parsing."""
        activities = parser.parse(sample_yaml_path)
        assert activities[0].title == "Перевірка розуміння"

    def test_parse_activity_types(self, parser, sample_yaml_path):
        """All 11 activity types are recognized."""
        activities = parser.parse(sample_yaml_path)
        types = [a.type for a in activities]
        expected = [
            'quiz', 'match-up', 'fill-in', 'true-false',
            'group-sort', 'unjumble', 'cloze', 'error-correction',
            'mark-the-words', 'select', 'translate'
        ]
        assert types == expected

    def test_parse_cloze_accepts_schema_text_field(self, parser, tmp_path):
        """B1 schema-style cloze activities can use text instead of passage."""
        activity_path = tmp_path / "activities.yaml"
        activity_path.write_text(
            """
- type: cloze
  title: Текст
  instruction: Заповніть пропуск.
  text: Я [1] текст.
  blanks:
  - id: 1
    answer: читаю
    options:
    - читаю
    - читав
""",
            encoding="utf-8",
        )

        activities = parser.parse(activity_path)

        assert len(activities) == 1
        assert activities[0].passage == "Я [1] текст."
        assert activities[0].blanks[0].answer == "читаю"

    def test_parse_mark_the_words_accepts_schema_target_words(self, parser, tmp_path):
        """Schema-valid mark-the-words activities render correctWords in MDX."""
        activity_path = tmp_path / "activities.yaml"
        activity_path.write_text(
            """
- type: mark-the-words
  title: Мішана група
  instruction: Позначте слова.
  text: Сторож узяв ключ і плащ.
  target_words:
  - Сторож
  - ключ
  - плащ
""",
            encoding="utf-8",
        )

        activities = parser.parse(activity_path)
        mdx = parser.to_mdx(activities)

        assert len(activities) == 1
        assert activities[0].answers == ["Сторож", "ключ", "плащ"]
        assert 'correctWords={JSON.parse(`["Сторож", "ключ", "плащ"]`)}' in mdx

    def test_parse_mark_the_words_accepts_targets_alias(self, parser, tmp_path):
        """A2 mark-the-words activities can use the existing targets alias."""
        activity_path = tmp_path / "activities.yaml"
        activity_path.write_text(
            """
- type: mark-the-words
  title: Фонетика
  instruction: Позначте слова.
  text: день місто люди синє рука
  targets:
  - день
  - місто
  - люди
  - синє
""",
            encoding="utf-8",
        )

        activities = parser.parse(activity_path)
        mdx = parser.to_mdx(activities)

        assert len(activities) == 1
        assert activities[0].answers == ["день", "місто", "люди", "синє"]
        assert 'correctWords={JSON.parse(`["день", "місто", "люди", "синє"]`)}' in mdx

    def test_parse_unjumble_accepts_correct_order(self, parser, tmp_path):
        """Schema-style unjumble activities can use correct_order for the answer."""
        activity_path = tmp_path / "activities.yaml"
        activity_path.write_text(
            """
- type: unjumble
  title: Речення
  instruction: Поставте слова в порядок.
  items:
  - words: ["буде", "Якщо", "дощ"]
    correct_order: ["Якщо", "буде", "дощ"]
""",
            encoding="utf-8",
        )

        activities = parser.parse(activity_path)
        mdx = parser.to_mdx(activities)

        assert activities[0].items[0].answer == "Якщо буде дощ"
        assert '"answer": "Якщо буде дощ"' in mdx

    def test_parse_error_correction_empty_error_as_no_error(self, parser, tmp_path):
        """Empty error fields render as the component's no-error sentinel."""
        activity_path = tmp_path / "activities.yaml"
        activity_path.write_text(
            """
- type: error-correction
  title: Перевірка
  instruction: Оберіть виправлене речення.
  items:
  - sentence: "Мій район тихіший за центр."
    error: ""
    correction: "Мій район тихіший за центр."
    options:
    - "Мій район тихіший за центр."
    - "Мій район тихіший ніж за центр."
""",
            encoding="utf-8",
        )

        activities = parser.parse(activity_path)
        mdx = parser.to_mdx(activities)

        assert activities[0].items[0].error is None
        assert '"errorWord": null' in mdx

    def test_parse_essay_response_preserves_object_rubric_and_peer_guidelines(self, parser, tmp_path):
        """A2 essay-response object rubrics and peer guidelines survive rendering."""
        activity_path = tmp_path / "activities.yaml"
        activity_path.write_text(
            """
- type: essay-response
  title: Міні-письмо
  instruction: Напишіть короткий текст.
  source_reading: "Модель показує процес і результат."
  prompt: "Напишіть 5-7 речень."
  model_answer: "У суботу я читав і написав листа."
  peer_review_guidelines:
  - "Позначте процес."
  - "Позначте результат."
  rubric:
    grammar: "Форми правильні."
    aspect: "Процес і результат розрізнено."
""",
            encoding="utf-8",
        )

        activities = parser.parse(activity_path)
        mdx = parser.to_mdx(activities, is_ukrainian_forced=True)

        assert activities[0].instruction == "Напишіть короткий текст."
        assert activities[0].peer_review_guidelines == ["Позначте процес.", "Позначте результат."]
        assert "Модель показує процес і результат." not in mdx
        assert "| grammar | Форми правильні. |  |" in mdx
        assert "#### Взаємоперевірка" in mdx
        assert "- Позначте результат." in mdx

    def test_parse_essay_response_preserves_colon_rubric_criteria(self, parser, tmp_path):
        """Colon-bearing rubric criteria survive YAML's implicit one-key mapping."""
        activity_path = tmp_path / "activities.yaml"
        activity_path.write_text(
            """
- type: essay-response
  title: Міні-письмо
  instruction: Напишіть короткий текст.
  prompt: "Напишіть 5-7 речень."
  model_answer: "Є теза і доказ."
  rubric:
    - Є конкретний доказ: фрагмент, репертуарний факт або класифікація.
""",
            encoding="utf-8",
        )

        activities = parser.parse(activity_path)
        mdx = parser.to_mdx(activities, is_ukrainian_forced=True)

        assert "| Є конкретний доказ: фрагмент, репертуарний факт або класифікація. | | |" in mdx
        assert "|  |  |  |" not in mdx

    def test_parse_essay_response_string_peer_guidelines_not_char_exploded(self, parser, tmp_path):
        """A bare-string peer_review_guidelines must become a single bullet, not one
        bullet per character (koliadky-shchedrivky exemplar bug, 2026-06-19)."""
        activity_path = tmp_path / "activities.yaml"
        activity_path.write_text(
            """
- type: essay-response
  title: Есе
  instruction: Напишіть есе.
  prompt: "Напишіть 8-10 речень."
  model_answer: "Зразок відповіді."
  peer_review_guidelines: Перевір, чи має есе чітку тезу.
  rubric:
  - Чітка теза
""",
            encoding="utf-8",
        )

        activities = parser.parse(activity_path)
        mdx = parser.to_mdx(activities, is_ukrainian_forced=True)

        # Coerced to a one-item list, not iterated character-by-character.
        assert activities[0].peer_review_guidelines == ["Перевір, чи має есе чітку тезу."]
        assert "- Перевір, чи має есе чітку тезу." in mdx
        # Regression guard: the char-explosion produced single-letter bullets like "- П".
        assert "\n- П\n" not in mdx
        assert "\n- е\n" not in mdx


class TestA2ActivitySchema:
    """Contract checks for A2 schema forms consumed by ActivityParser."""

    def test_quiz_string_options_require_correct_answer_signal(self, a2_activity_validator):
        activity = {
            "type": "quiz",
            "instruction": "Оберіть.",
            "items": [{
                "prompt": "Питання?",
                "options": ["а", "б", "в"],
            }],
        }

        assert not a2_activity_validator.is_valid([activity])

    def test_quiz_answer_and_object_options_are_valid(self, a2_activity_validator):
        string_answer_activity = {
            "type": "quiz",
            "instruction": "Оберіть.",
            "items": [{
                "prompt": "Питання?",
                "options": ["а", "б", "в"],
                "answer": "б",
            }],
        }
        object_options_activity = {
            "type": "quiz",
            "instruction": "Оберіть.",
            "items": [{
                "prompt": "Питання?",
                "options": [
                    {"text": "а", "correct": False},
                    {"text": "б", "correct": True},
                ],
            }],
        }

        assert a2_activity_validator.is_valid([string_answer_activity])
        assert a2_activity_validator.is_valid([object_options_activity])

    def test_essay_response_object_rubric_is_valid(self, a2_activity_validator):
        activity = {
            "type": "essay-response",
            "prompt": "Напишіть короткий текст.",
            "peer_review_guidelines": ["Позначте процес."],
            "rubric": {
                "grammar": "Форми правильні.",
                "aspect": "Процес і результат розрізнено.",
            },
        }

        assert a2_activity_validator.is_valid([activity])


# =============================================================================
# MDX GENERATION TESTS
# =============================================================================

class TestMDXGeneration:
    """Test MDX output generation."""

    def test_generates_mdx_string(self, parser, sample_yaml_path):
        """to_mdx produces non-empty string."""
        activities = parser.parse(sample_yaml_path)
        mdx = parser.to_mdx(activities)
        assert isinstance(mdx, str)
        assert len(mdx) > 1000

    def test_mdx_contains_component_tags(self, parser, sample_yaml_path):
        """MDX contains React component tags."""
        activities = parser.parse(sample_yaml_path)
        mdx = parser.to_mdx(activities)
        assert '<Quiz' in mdx
        assert '<MatchUp' in mdx
        assert '<FillIn' in mdx

    def test_quiz_mdx_format(self, parser, valid_quiz):
        """Quiz generates correct MDX format."""
        mdx = parser._quiz_to_mdx(valid_quiz)
        assert '<Quiz' in mdx
        assert '### Test Quiz' in mdx # H3 Header check

    def test_core_activity_mdx_receives_ukrainian_flag(self, parser, valid_quiz):
        """Forced-Ukrainian modules pass localized UI labels to core activities."""
        mdx = parser._quiz_to_mdx(valid_quiz, is_ukrainian_forced=True)
        assert "isUkrainian={true}" in mdx
        assert 'questions={JSON.parse' in mdx

    def test_error_correction_mdx_keeps_instruction_and_legacy_anchor(self, parser, tmp_path):
        """Error-correction activities can preserve student instructions and old anchors."""
        yaml_file = tmp_path / 'error_correction_anchor.yaml'
        yaml_file.write_text(
            "- id: act-7\n"
            "  type: error-correction\n"
            "  title: Choose the Ukrainian sentence\n"
            "  anchor_id: fix-common-l2-traps\n"
            "  instruction: Choose the safer Ukrainian line.\n"
            "  items:\n"
            "    - sentence: Я є студент.\n"
            "      error: Я є студент.\n"
            "      correction: Я студент.\n"
            "      options:\n"
            "        - Я студент.\n"
            "        - Я є студент.\n"
            "      explanation: Present identity lines skip English-style am.\n",
            encoding='utf-8',
        )

        mdx = parser.to_mdx(parser.parse(yaml_file))

        assert '<span id="fix-common-l2-traps"></span>' in mdx
        assert '### Choose the Ukrainian sentence' in mdx
        assert 'instruction="Choose the safer Ukrainian line."' in mdx
        assert "items={JSON.parse(`" in mdx
        assert '"sentence": "Я є студент."' in mdx
        assert "<ErrorCorrectionItem" not in mdx

    def test_error_correction_mdx_uses_replacement_spans(self, parser, tmp_path):
        """The generated embed gives the UI forms, not full sentence variants."""
        yaml_file = tmp_path / "error_correction_replacement.yaml"
        yaml_file.write_text(
            "- type: error-correction\n"
            "  title: Виправлення\n"
            "  items:\n"
            "    - sentence: Вона вчителька.\n"
            "      error: вчителька\n"
            "      correction: Вона вчитель.\n"
            "      options:\n"
            "        - Вона вчитель.\n"
            "        - Вона вчителька.\n"
            "        - вчитель\n",
            encoding="utf-8",
        )

        mdx = parser.to_mdx(parser.parse(yaml_file))

        assert '"correctForm": "вчитель"' in mdx
        assert '"options": ["вчитель", "вчителька", "вчитель"]' in mdx


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """End-to-end integration tests."""

    def test_parse_generate(self, parser, sample_yaml_path):
        """Full pipeline: parse -> generate."""
        # Parse
        activities = parser.parse(sample_yaml_path)
        assert len(activities) > 0

        # Generate
        mdx = parser.to_mdx(activities)
        assert len(mdx) > 1000  # Should be substantial

    def test_round_trip_data_integrity(self, parser, valid_quiz):
        """Data survives round trip through MDX generation."""
        # Generate MDX
        mdx = parser._quiz_to_mdx(valid_quiz)

        # Check data is present
        assert "Test Quiz" in mdx
        assert "Question 1?" in mdx
        assert "Correct" in mdx


# =============================================================================
# VALIDATION RESULT TESTS
# =============================================================================

class TestValidationResult:
    def test_fresh_result_is_ok(self):
        result = ValidationResult()
        assert result.ok is True
        assert result.errors == []
        assert result.warnings == []

    def test_add_error_sets_ok_false(self):
        result = ValidationResult()
        result.add_error("root", "something broke")
        assert result.ok is False
        assert len(result.errors) == 1
        assert result.errors[0].message == "something broke"

    def test_add_warning_keeps_ok_true(self):
        result = ValidationResult()
        result.add_warning("root", "minor issue")
        assert result.ok is True
        assert len(result.warnings) == 1


# =============================================================================
# PARSER EDGE CASES
# =============================================================================

class TestParserEdgeCases:
    def test_parse_empty_file(self, parser, tmp_path):
        """Empty YAML file returns empty list."""
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("")
        assert parser.parse(yaml_file) == []

    def test_parse_activities_wrapper(self, parser, tmp_path):
        """Parser handles both bare list and activities: wrapper."""
        yaml_file = tmp_path / "wrapped.yaml"
        yaml_file.write_text(
            "activities:\n"
            "  - type: quiz\n"
            "    title: Test\n"
            "    items:\n"
            "      - question: Q1?\n"
            "        options: [A, B, C, D]\n"
            "        answer: A\n"
        )
        activities = parser.parse(yaml_file)
        assert len(activities) == 1
        assert activities[0].type == "quiz"

    def test_parse_non_list_raises(self, parser, tmp_path):
        """Non-list YAML raises ValueError."""
        yaml_file = tmp_path / "scalar.yaml"
        yaml_file.write_text("just a string")
        with pytest.raises(ValueError, match="Expected list"):
            parser.parse(yaml_file)

    def test_unknown_activity_type_raises(self, parser, tmp_path):
        """Unknown activity types fail loudly."""
        yaml_file = tmp_path / "unknown.yaml"
        yaml_file.write_text(
            "- id: ghost-act\n"
            "  type: nonexistent-type\n"
            "  title: Ghost\n"
        )
        with pytest.raises(ValueError, match=r"ghost-act.*unknown activity type 'nonexistent-type'"):
            parser.parse(yaml_file)

    def test_parse_true_false(self, parser, tmp_path):
        yaml_file = tmp_path / "tf.yaml"
        yaml_file.write_text(
            "- type: true-false\n"
            "  title: TF Test\n"
            "  items:\n"
            "    - statement: The sky is blue\n"
            "      correct: true\n"
            "    - statement: Cats are fish\n"
            "      correct: false\n"
        )
        activities = parser.parse(yaml_file)
        assert len(activities) == 1
        assert activities[0].type == "true-false"
        assert len(activities[0].items) == 2
        assert activities[0].items[0].correct is True
        assert activities[0].items[1].correct is False

    def test_parse_fill_in(self, parser, tmp_path):
        yaml_file = tmp_path / "fi.yaml"
        yaml_file.write_text(
            "- type: fill-in\n"
            "  title: Fill Test\n"
            "  items:\n"
            "    - sentence: Я ___ вдома\n"
            "      answer: був\n"
        )
        activities = parser.parse(yaml_file)
        assert len(activities) == 1
        assert activities[0].type == "fill-in"
        assert activities[0].items[0].answer == "був"

    def test_parse_match_up(self, parser, tmp_path):
        yaml_file = tmp_path / "mu.yaml"
        yaml_file.write_text(
            "- type: match-up\n"
            "  title: Match Test\n"
            "  pairs:\n"
            "    - left: кіт\n"
            "      right: cat\n"
            "    - left: собака\n"
            "      right: dog\n"
        )
        activities = parser.parse(yaml_file)
        assert len(activities) == 1
        assert activities[0].type == "match-up"
        assert len(activities[0].pairs) == 2

    def test_parse_translate(self, parser, tmp_path):
        yaml_file = tmp_path / "tr.yaml"
        yaml_file.write_text(
            "- type: translate\n"
            "  title: Translate Test\n"
            "  items:\n"
            "    - source: Hello\n"
            "      target: Привіт\n"
        )
        activities = parser.parse(yaml_file)
        assert len(activities) == 1
        assert activities[0].type == "translate"


class TestUnjumbleParsing:
    def test_parse_unjumble_list_shape_round_trips_to_mdx(self, parser, tmp_path):
        yaml_file = tmp_path / "unjumble_list.yaml"
        yaml_file.write_text(
            "- id: act-7\n"
            "  type: unjumble\n"
            "  title: Складіть речення\n"
            "  items:\n"
            "    - jumbled: [о, я, прокидаюся, сьомій]\n"
            "      answer: Я прокидаюся о сьомій\n"
        )
        activities = parser.parse(yaml_file)
        mdx = parser.to_mdx(activities)
        assert "о / я / прокидаюся / сьомій" in mdx
        assert "Я прокидаюся о сьомій" in mdx

    def test_parse_unjumble_string_shape_still_round_trips_to_mdx(self, parser, tmp_path):
        yaml_file = tmp_path / "unjumble_string.yaml"
        yaml_file.write_text(
            "- id: legacy-unjumble\n"
            "  type: unjumble\n"
            "  title: Складіть речення\n"
            "  items:\n"
            "    - jumbled: Я / вранці / читаю\n"
            "      answer: Я читаю вранці\n"
        )
        activities = parser.parse(yaml_file)
        mdx = parser.to_mdx(activities)
        assert "Я / вранці / читаю" in mdx
        assert "Я читаю вранці" in mdx

    def test_parse_unjumble_bad_shape_raises_with_context(self, parser, tmp_path):
        yaml_file = tmp_path / "unjumble_bad.yaml"
        yaml_file.write_text(
            "- id: bad-unjumble\n"
            "  type: unjumble\n"
            "  title: Bad\n"
            "  items:\n"
            "    - jumbled: 42\n"
            "      answer: Я читаю вранці\n"
        )
        with pytest.raises(ValueError, match=r"bad-unjumble.*field 'jumbled'.*str or list.*int"):
            parser.parse(yaml_file)


class TestAnagramParsing:
    """Tests for anagram activity parsing — both V2 (letters array) and legacy (scrambled string)."""

    @pytest.fixture
    def parser(self):
        return ActivityParser()

    def test_parse_anagram_letters_format(self, parser, tmp_path):
        """V2 schema: letters as array of chars → joined as space-separated scrambled string."""
        yaml_file = tmp_path / "anagram.yaml"
        yaml_file.write_text(
            "- type: anagram\n"
            "  instruction: Rearrange the letters.\n"
            "  items:\n"
            "    - letters: [м, о, л, о, к, о]\n"
            "      answer: молоко\n"
            "      hint: milk\n"
            "    - letters: [к, і, т]\n"
            "      answer: кіт\n"
        )
        activities = parser.parse(yaml_file)
        assert len(activities) == 1
        act = activities[0]
        assert act.type == "anagram"
        assert len(act.items) == 2
        assert act.items[0].scrambled == "м о л о к о"
        assert act.items[0].answer == "молоко"
        assert act.items[0].hint == "milk"
        assert act.items[1].scrambled == "к і т"
        assert act.items[1].answer == "кіт"

    def test_parse_anagram_scrambled_format(self, parser, tmp_path):
        """Legacy V1 format: scrambled as a string (e.g., from older builds)."""
        yaml_file = tmp_path / "anagram_legacy.yaml"
        yaml_file.write_text(
            "- type: anagram\n"
            "  items:\n"
            "    - scrambled: к і т\n"
            "      answer: кіт\n"
        )
        activities = parser.parse(yaml_file)
        assert len(activities) == 1
        assert activities[0].items[0].scrambled == "к і т"
        assert activities[0].items[0].answer == "кіт"

    def test_parse_anagram_error_raises_with_context(self, parser, tmp_path):
        """A bad activity should fail loudly instead of being dropped."""
        yaml_file = tmp_path / "mixed.yaml"
        yaml_file.write_text(
            "- type: quiz\n"
            "  items:\n"
            "    - question: Що це?\n"
            "      options: [кіт, собака]\n"
            "      correct: 0\n"
            "- id: bad-anagram\n"
            "  type: anagram\n"
            "  items:\n"
            "    - bad_key: something_invalid\n"
            "      answer: кіт\n"
            "- type: true-false\n"
            "  items:\n"
            "    - statement: Кіт — тварина.\n"
            "      correct: true\n"
        )
        with pytest.raises(ValueError, match=r"bad-anagram.*missing both 'letters' and 'scrambled'"):
            parser.parse(yaml_file)

    def test_parse_v2_activities_file_with_anagram(self, parser, tmp_path):
        """V2 format (inline/workbook split) with anagram in workbook parses all sections."""
        yaml_file = tmp_path / "v2.yaml"
        yaml_file.write_text(
            "version: '1.0'\n"
            "module: test-module\n"
            "level: a1\n"
            "inline:\n"
            "  - type: quiz\n"
            "    items:\n"
            "      - question: Що це?\n"
            "        options: [кіт, собака]\n"
            "        correct: 0\n"
            "workbook:\n"
            "  - type: anagram\n"
            "    items:\n"
            "      - letters: [к, і, т]\n"
            "        answer: кіт\n"
        )
        activities = parser.parse(yaml_file)
        assert len(activities) == 2
        types = {a.type for a in activities}
        assert types == {"quiz", "anagram"}
