"""
Tests for YAML activity parsing, validation, and conversion.
"""

import pytest
from pathlib import Path
import json

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
