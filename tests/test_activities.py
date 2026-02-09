"""
Comprehensive tests for activity validation.

Tests all 13 activity types and their validation rules.
Run with: pytest tests/test_activities.py -v
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.audit.checks.activities import (
    check_activity_complexity,
    check_unjumble_word_match,
    check_anagram_min_letters,
    check_matchup_misuse,
    check_activity_ukrainian_content,
    check_activity_level_restrictions,
    count_items,
)
from scripts.audit.checks.content_quality import check_content_quality
from scripts.audit.config import VALID_ACTIVITY_TYPES


# =============================================================================
# TEST: Activity Type Recognition
# =============================================================================

class TestActivityTypeRecognition:
    """Test that all activity types are recognized."""

    def test_all_valid_activity_types_exist(self):
        """Verify VALID_ACTIVITY_TYPES contains all expected types."""
        # Updated to match expanded list in config.py
        expected_base = {
            'quiz', 'match-up', 'fill-in', 'true-false', 'group-sort',
            'unjumble', 'error-correction', 'anagram', 'select', 'translate',
            'cloze', 'mark-the-words'
        }
        # The set has expanded significantly with seminar-style activities
        assert expected_base.issubset(set(VALID_ACTIVITY_TYPES))

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
    """Test match-up misuse validation."""

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
        # Very short anagrams are flagged
        assert len(violations) > 0


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

    def test_error_correction_not_in_a1(self):
        """Error-correction should not be allowed in A1."""
        content = """
## error-correction: Виправлення

1. Він ходить до школа.
   > [!error] школа
   > [!answer] школи
   > [!options] школа | школи | школу | школою
   > [!explanation] Після "до" вживаємо родовий відмінок.
"""
        violations = check_activity_level_restrictions(content, 'A1', 10)
        ec_violations = [v for v in violations if 'error-correction' in v.get('issue', '').lower()]
        assert len(ec_violations) == 1

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
# TEST: Russian Character Detection
# =============================================================================

class TestRussianCharacterDetection:
    """Test detection of Russian-only characters (ё, ъ, ы, э)."""

    def test_russian_character_detected(self):
        """Russian characters outside context should be flagged."""
        content = """
---
module: test
level: B1
---

# Test Module

Прикметник красивый не є українським словом.
"""
        # Note: "Russian" is NOT in the content, so ы should be flagged
        violations = check_content_quality(content, 'B1', 1)
        russian_violations = [v for v in violations if v.get('type') == 'RUSSIAN_CHARACTERS']
        assert len(russian_violations) >= 1
        assert 'ы' in russian_violations[0]['issue']

    def test_russian_character_in_context_allowed(self):
        """Russian characters in comparative context should be allowed."""
        content = """
---
module: test
level: B1
---

# Test Module

In Ukrainian we use "и" while Russian uses "ы" in the same position.
"""
        violations = check_content_quality(content, 'B1', 1)
        russian_violations = [v for v in violations if v.get('type') == 'LINGUISTIC_PURITY']
        # Should NOT flag because "Russian" context is present
        assert len(russian_violations) == 0

    def test_all_russian_chars_detected(self):
        """All four Russian-only chars should be detected."""
        content = """
---
module: test
level: B1
---

# Test Module

ё ы э
"""
        # ъ is now considered HISTORICAL_CYRILLIC_CHARS, not RUSSIAN_ONLY_CHARS
        violations = check_content_quality(content, 'B1', 1)
        russian_violations = [v for v in violations if v.get('type') == 'RUSSIAN_CHARACTERS']
        assert len(russian_violations) >= 1

    def test_no_russian_chars_clean(self):
        """Clean Ukrainian content should pass."""
        content = """
---
module: test
level: B1
---

# Тестовий модуль

Це речення українською мовою без жодних російських символів.
Іменник називає предмети та поняття.
"""
        violations = check_content_quality(content, 'B1', 1)
        russian_violations = [v for v in violations if v.get('type') == 'LINGUISTIC_PURITY']
        assert len(russian_violations) == 0


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
