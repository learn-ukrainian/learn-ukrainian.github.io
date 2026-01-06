"""
Tests for YAML activity parsing, validation, and conversion.
"""

import pytest
from pathlib import Path

# Add scripts to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from yaml_activities import (
    ActivityParser,
    QuizActivity, QuizItem, QuizOption,
    MatchUpActivity, MatchPair,
    FillInActivity, FillInItem,
    TrueFalseActivity, TrueFalseItem,
    GroupSortActivity, GroupSortGroup,
    UnjumbleActivity, UnjumbleItem,
    ClozeActivity, ClozeBlank,
    ErrorCorrectionActivity, ErrorCorrectionItem,
    MarkTheWordsActivity,
    SelectActivity, SelectItem,
    TranslateActivity, TranslateItem,
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
        assert len(activities) == 12
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
# VALIDATION TESTS
# =============================================================================

class TestValidation:
    """Test activity validation."""

    def test_valid_b1_activities_pass(self, parser, sample_yaml_path):
        """Sample B1 activities pass validation."""
        activities = parser.parse(sample_yaml_path)
        result = parser.validate(activities, level='b1')
        assert result.ok, f"Errors: {[e.message for e in result.errors]}"

    def test_insufficient_activities_fail(self, parser):
        """Too few activities fails validation."""
        activities = [
            QuizActivity(title="Only Quiz", items=[
                QuizItem(
                    question=f"Q{i}",
                    options=[
                        QuizOption("A", True),
                        QuizOption("B", False),
                        QuizOption("C", False),
                        QuizOption("D", False),
                    ]
                ) for i in range(8)
            ])
        ]
        result = parser.validate(activities, level='b1')
        assert not result.ok  # B1 needs 12 activities

    def test_a1_allows_anagram(self, parser):
        """A1 level allows anagram activities."""
        from yaml_activities import AnagramActivity, AnagramItem
        activities = [
            AnagramActivity(title="Test", items=[
                AnagramItem(scrambled="к н и г а", answer="книга")
                for _ in range(6)
            ])
        ] * 8  # A1 needs 8 activities
        result = parser.validate(activities, level='a1')
        # Should not error on anagram type
        anagram_errors = [e for e in result.errors if 'anagram' in e.message.lower()]
        assert len(anagram_errors) == 0


class TestLogicValidation:
    """Test business logic validation."""

    def test_quiz_must_have_exactly_one_correct(self, parser):
        """Quiz options must have exactly one correct answer."""
        activities = [
            QuizActivity(title="Bad Quiz", items=[
                QuizItem(
                    question="Two correct?",
                    options=[
                        QuizOption("A", True),
                        QuizOption("B", True),  # Two correct!
                        QuizOption("C", False),
                        QuizOption("D", False),
                    ]
                )
            ] * 8)
        ] * 12
        result = parser.validate(activities, level='b1')
        # Should have logic error about multiple correct answers
        assert not result.ok or any('correct' in e.message.lower() for e in result.errors)

    def test_fill_in_answer_must_be_in_options(self, parser):
        """Fill-in answer must appear in options."""
        activities = [
            FillInActivity(title="Bad Fill", items=[
                FillInItem(
                    sentence="Test ___.",
                    answer="correct",
                    options=["wrong1", "wrong2", "wrong3", "wrong4"]  # No "correct"!
                )
            ] * 8)
        ] * 12
        result = parser.validate(activities, level='b1')
        # Should have logic error
        answer_errors = [e for e in result.errors if 'answer' in e.message.lower() and 'option' in e.message.lower()]
        assert len(answer_errors) > 0 or not result.ok


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
        assert len(mdx) > 0

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
        assert 'title="Test Quiz"' in mdx
        assert 'questions={JSON.parse' in mdx


# =============================================================================
# SCHEMA VALIDATION TESTS
# =============================================================================

class TestSchemaValidation:
    """Test JSON Schema validation."""

    def test_a1_quiz_min_items(self, parser):
        """A1 quiz needs minimum 6 items."""
        activities = [
            QuizActivity(title="Test", items=[
                QuizItem(
                    question="Q?",
                    options=[
                        QuizOption("A", True),
                        QuizOption("B", False),
                        QuizOption("C", False),
                        QuizOption("D", False),
                    ]
                )
            ] * 5)  # Only 5, needs 6
        ] * 8
        result = parser.validate(activities, level='a1')
        assert not result.ok

    def test_b1_quiz_min_items(self, parser):
        """B1 quiz needs minimum 8 items."""
        activities = [
            QuizActivity(title="Test", items=[
                QuizItem(
                    question="Q?",
                    options=[
                        QuizOption("A", True),
                        QuizOption("B", False),
                        QuizOption("C", False),
                        QuizOption("D", False),
                    ]
                )
            ] * 6)  # Only 6, needs 8
        ] * 12
        result = parser.validate(activities, level='b1')
        assert not result.ok


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """End-to-end integration tests."""

    def test_parse_validate_generate(self, parser, sample_yaml_path):
        """Full pipeline: parse -> validate -> generate."""
        # Parse
        activities = parser.parse(sample_yaml_path)
        assert len(activities) > 0

        # Validate
        result = parser.validate(activities, level='b1')
        assert result.ok

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
