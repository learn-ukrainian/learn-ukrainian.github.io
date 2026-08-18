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
    check_activity_level_restrictions,
    check_activity_ukrainian_content,
    check_anagram_min_letters,
    check_unjumble_word_match,
    count_items,
)
from scripts.audit.checks.content_purity import check_content_purity
from scripts.audit.config import VALID_ACTIVITY_TYPES

# =============================================================================
# TEST: Activity Type Recognition
# =============================================================================

class TestActivityTypeRecognition:
    """Test that all 12 activity types are recognized."""

    def test_all_valid_activity_types_exist(self):
        """Verify VALID_ACTIVITY_TYPES contains core + extended types."""
        core_types = {
            'quiz', 'match-up', 'fill-in', 'true-false', 'group-sort',
            'unjumble', 'error-correction', 'anagram', 'select', 'translate',
            'cloze', 'mark-the-words'
        }
        # Core types must be a subset of VALID_ACTIVITY_TYPES
        assert core_types.issubset(set(VALID_ACTIVITY_TYPES)), \
            f"Missing core types: {core_types - set(VALID_ACTIVITY_TYPES)}"
        # Extended types may exist (seminar tracks)
        assert len(VALID_ACTIVITY_TYPES) >= 12

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

class TestMatchupValidation:
    """Test match-up content validation still enforced on markdown."""

    def test_matchup_misuse_english_pairs(self):
        """Match-ups with English-only pairs are detected by ukrainian content check."""
        content = """
## match-up: Grammar Terms

| English | Definition |
|---------|------------|
| noun | a person, place, or thing |
| verb | an action word |
| adjective | describes a noun |
"""
        # check_matchup_misuse looks for specific patterns
        # Low Ukrainian content is caught by check_activity_ukrainian_content
        violations = check_activity_ukrainian_content(content, 'B1', 1)
        assert len(violations) >= 1
        assert violations[0]['type'] == 'NO_UKRAINIAN_CONTENT'


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

class TestAnagramValidation:
    """Test anagram letter matching and level restrictions."""

    def test_anagram_only_allowed_a1_early(self):
        """Anagram should only be allowed in A1 M01-M10."""
        content = """
## anagram: Літери

1. ОЛКСО
   > [!answer] СЛОВО
"""
        # A2 should not allow anagram
        violations = check_activity_level_restrictions(content, 'A2', 10)
        anagram_violations = [v for v in violations if 'anagram' in v.get('issue', '').lower()]
        assert len(anagram_violations) == 1

    def test_anagram_allowed_a1_module_5(self):
        """Anagram should be allowed in A1 M01-10."""
        content = """
## anagram: Літери

1. ОЛКСО
   > [!answer] СЛОВО
"""
        violations = check_activity_level_restrictions(content, 'A1', 5)
        anagram_violations = [v for v in violations if 'anagram' in v.get('issue', '').lower()]
        assert len(anagram_violations) == 0

    def test_anagram_min_letters(self):
        """Anagram should require minimum letter count."""
        content = """
## anagram: Літери

1. ТІ
   > [!answer] ТИ
"""
        violations = check_anagram_min_letters(content)
        short = [v for v in violations if v.get('type') == 'ANAGRAM_TOO_SHORT']
        assert len(short) >= 1


# =============================================================================
# TEST: Item Counting
# =============================================================================

class TestItemCounting:
    """Test the count_items helper function."""

    def test_count_numbered_items(self):
        """Should count numbered list items."""
        text = """
1. First item
2. Second item
3. Third item
"""
        assert count_items(text) == 3

    def test_count_bulleted_items(self):
        """Should count bulleted items."""
        text = """
- First item
- Second item
- Third item
- Fourth item
"""
        assert count_items(text) == 4

    def test_count_table_rows(self):
        """Should count table rows."""
        text = """
| A | B |
|---|---|
| 1 | one |
| 2 | two |
| 3 | three |
"""
        # Counts data rows, not header
        count = count_items(text)
        assert count >= 3


# =============================================================================
# TEST: Level Restrictions
# =============================================================================

class TestLevelRestrictions:
    """Test that activities are restricted to appropriate levels."""

    def test_cloze_not_in_a1(self):
        """Cloze should not be allowed in A1."""
        content = """
## cloze: Заповніть

Це {речення} про {граматику}.
"""
        violations = check_activity_level_restrictions(content, 'A1', 10)
        cloze_violations = [v for v in violations if 'cloze' in v.get('issue', '').lower()]
        assert len(cloze_violations) == 1

    def test_basic_activities_allowed_all_levels(self):
        """Quiz, match-up, fill-in should work at all levels."""
        content = """
## quiz: Тест

1. Яке це слово?
   - [x] слово
   - [ ] буква
"""
        violations = check_activity_level_restrictions(content, 'A1', 1)
        quiz_violations = [v for v in violations if 'quiz' in v.get('issue', '').lower()]
        assert len(quiz_violations) == 0


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

    def test_activity_with_insufficient_ukrainian(self):
        """Activity with too little Ukrainian should fail."""
        content = """
## quiz: Grammar Test

1. Which part of speech names objects and concepts in grammar?
   - [x] Noun
   - [ ] Verb
   - [ ] Adjective
   - [ ] Adverb
"""
        violations = check_activity_ukrainian_content(content, 'B1', 1)
        assert len(violations) == 1
        assert violations[0]['type'] == 'NO_UKRAINIAN_CONTENT'


# =============================================================================
# TEST: Content purity / redundancy
# =============================================================================

class TestContentPurity:
    """Test content purity checks (duplicate sentences, robotic structure)."""

    def test_clean_content_passes(self):
        """Distinct lesson sentences must not emit CONTENT_REDUNDANCY."""
        content = (
            "Українська мова має багату історію та складну фонетичну систему.\n"
            "Граматика цієї мови цікава своїми сімома відмінками."
        )
        violations = check_content_purity(content)
        redundancy = [v for v in violations if v.get('type') == 'CONTENT_REDUNDANCY']
        assert redundancy == []

    def test_short_sentence_overlap_below_threshold_does_not_flag(self):
        """#969: short sentences (<15 unique >3-char words) need >0.85 overlap."""
        # 9 unique long words each; intersection/union = 8/10 = 0.80 < 0.85
        s1 = (
            "Українська граматика включає складні правила відмінювання "
            "іменників у різних контекстах."
        )
        s2 = (
            "Українська граматика включає складні правила відмінювання "
            "прикметників у різних контекстах."
        )
        violations = check_content_purity(f"{s1} {s2}")
        redundancy = [v for v in violations if v.get('type') == 'CONTENT_REDUNDANCY']
        assert redundancy == []

    def test_redundancy_detection(self):
        """Long sentences (>=15 unique >3-char words) with >0.7 overlap flag."""
        # 16 unique long words each; intersection/union = 15/17 ≈ 0.88 > 0.7
        s1 = (
            "Українська граматика включає складні правила відмінювання "
            "іменників у різних контекстах навчання і потребує уваги "
            "кожного студента на першому рівні."
        )
        s2 = (
            "Українська граматика включає складні правила відмінювання "
            "прикметників у різних контекстах навчання і потребує уваги "
            "кожного студента на першому рівні."
        )
        violations = check_content_purity(f"{s1} {s2}")
        redundancy = [v for v in violations if v.get('type') == 'CONTENT_REDUNDANCY']
        assert len(redundancy) >= 1


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
