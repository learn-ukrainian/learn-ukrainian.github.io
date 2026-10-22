"""
Tests for live activity-validation helpers and content-purity detection.

Markdown-only check_activity_complexity cases were removed (#6990): that
helper short-circuits to [] without yaml_activities. YAML complexity lives
in tests/test_yaml_activities.py and activity_validator.

Run with: pytest tests/test_activities.py -v
"""

import os
import sys

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.audit.checks.activities import (
    check_activity_ukrainian_content,
    check_unjumble_word_match,
)

# =============================================================================
# TEST: Activity Type Recognition
# =============================================================================

class TestActivityTypeRecognition:
    """Test that all 12 activity types are recognized."""

    def test_content_section_not_recognized_as_activity(self):
        """Content sections with colons should NOT be flagged."""
        content = """
## Punctuation: Пунктуація

This is explanatory content about punctuation rules in Ukrainian.
Крапка ставиться в кінці речення. Кома розділяє частини речення.
More English explanation here about how punctuation works.
"""
        # Should NOT trigger NO_UKRAINIAN_CONTENT since it's not an activity
        violations = check_activity_ukrainian_content(content, 'B1', 1)
        assert len(violations) == 0, f"False positive: {violations}"

    def test_valid_activity_is_checked(self):
        """Real activities should be validated."""
        content = """
## quiz: Test Quiz

1. This is an English-only question with no Ukrainian?
   - [ ] Option A
   - [x] Option B
"""
        # Should trigger NO_UKRAINIAN_CONTENT for quiz with <20% Ukrainian
        violations = check_activity_ukrainian_content(content, 'B1', 1)
        assert len(violations) == 1
        assert violations[0]['type'] == 'NO_UKRAINIAN_CONTENT'


# =============================================================================
# TEST: Match-up Validation
# =============================================================================


# =============================================================================
# TEST: Unjumble Validation
# =============================================================================

class TestUnjumbleValidation:
    """Test unjumble answer matching."""

    def test_unjumble_answer_mismatch(self):
        """Unjumble answer must use same words as scrambled version."""
        content = """
## unjumble: Речення

1. я / люблю / Україну
   > [!answer] Я люблю Київ.
"""
        violations = check_unjumble_word_match(content)
        # Detects both: answer has 'київ' not in jumbled, and jumbled has 'україну' not in answer
        assert len(violations) >= 1
        assert all(v['type'] == 'UNJUMBLE_WORD_MISMATCH' for v in violations)

    def test_unjumble_answer_matches(self):
        """Valid unjumble where answer uses same words."""
        content = """
## unjumble: Речення

1. я / люблю / Україну
   > [!answer] Я люблю Україну.
"""
        violations = check_unjumble_word_match(content)
        assert len(violations) == 0


# =============================================================================
# TEST: Anagram Validation
# =============================================================================


# =============================================================================
# TEST: Item Counting
# =============================================================================


# =============================================================================
# TEST: Level Restrictions
# =============================================================================


# =============================================================================
# TEST: Ukrainian Content Ratio
# =============================================================================

class TestUkrainianContent:
    """Test Ukrainian content validation in activities."""

    def test_activity_with_sufficient_ukrainian(self):
        """Activity with enough Ukrainian should pass."""
        content = """
## quiz: Частини мови

1. Яка частина мови називає предмети та поняття в українській граматиці?
   - [x] Іменник
   - [ ] Дієслово
   - [ ] Прикметник
   - [ ] Прислівник
"""
        violations = check_activity_ukrainian_content(content, 'B1', 1)
        assert len(violations) == 0


# =============================================================================
# TEST: Content purity / redundancy
# =============================================================================


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
