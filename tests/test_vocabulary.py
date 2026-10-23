"""
Tests for vocabulary validation checks.

Tests vocabulary table format, column validation, and transliteration policy.
Run with: pytest tests/test_vocabulary.py -v
"""

import os
import sys

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.audit.checks.vocabulary import (
    check_vocab_matches_plan,
    extract_vocab_items,
)

# =============================================================================
# TEST: Vocabulary Table Format
# =============================================================================


# =============================================================================
# TEST: Vocabulary Extraction
# =============================================================================

class TestVocabExtraction:
    """Test vocabulary item extraction from content."""

    def test_extract_from_3_column_table(self):
        """Should extract items from B1 3-column table."""
        content = """
# Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| граматика | grammar | noun |
| відмінок | case | noun |
"""
        items = extract_vocab_items(content)
        assert len(items) == 2
        assert items[0]['uk'] == 'граматика'
        assert items[0]['en'] == 'grammar'


# =============================================================================
# TEST: Vocabulary Row Counting
# =============================================================================


class TestPlanVocabMatching:
    """Test curriculum-plan vocabulary enforcement."""

    def test_vocab_plan_missing_is_blocking(self, monkeypatch, tmp_path):
        plan_path = tmp_path / "A1-CURRICULUM-PLAN.md"
        plan_path.write_text("placeholder", "utf-8")

        monkeypatch.setattr(
            "scripts.audit.checks.vocabulary.get_plan_path",
            lambda level: plan_path,
        )
        monkeypatch.setattr(
            "scripts.audit.checks.vocabulary.parse_plan_vocabulary",
            lambda path, module_num: {"природа", "місто"},
        )
        monkeypatch.setattr(
            "scripts.audit.checks.vocabulary.get_cumulative_vocab",
            lambda level, module_num: set(),
        )

        violations = check_vocab_matches_plan("module.md", "A1", 3, {"місто"})

        assert len(violations) == 1
        assert violations[0]["type"] == "VOCAB_PLAN_MISSING"
        assert violations[0]["blocking"] is True


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
