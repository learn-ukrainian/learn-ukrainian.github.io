"""
Tests for YAML activity parsing, validation, and conversion.
"""


# Add scripts to path
import sys
from pathlib import Path

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
        assert 'questions={JSON.parse' in mdx


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

    def test_unknown_activity_type_skipped(self, parser, tmp_path):
        """Unknown activity types are silently skipped."""
        yaml_file = tmp_path / "unknown.yaml"
        yaml_file.write_text(
            "- type: nonexistent-type\n"
            "  title: Ghost\n"
        )
        activities = parser.parse(yaml_file)
        assert len(activities) == 0

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

    def test_parse_anagram_error_does_not_crash_other_activities(self, parser, tmp_path):
        """A bad activity should be skipped, not crash the whole file."""
        yaml_file = tmp_path / "mixed.yaml"
        yaml_file.write_text(
            "- type: quiz\n"
            "  items:\n"
            "    - question: Що це?\n"
            "      options: [кіт, собака]\n"
            "      correct: 0\n"
            "- type: anagram\n"
            "  items:\n"
            "    - bad_key: something_invalid\n"
            "      answer: кіт\n"
            "- type: true-false\n"
            "  items:\n"
            "    - statement: Кіт — тварина.\n"
            "      correct: true\n"
        )
        # Should parse quiz and true-false; anagram skipped with warning
        activities = parser.parse(yaml_file)
        types = [a.type for a in activities]
        assert "quiz" in types
        assert "true-false" in types
        # Anagram with bad key is skipped (no scrambled and no letters key)
        assert len(activities) == 2

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
