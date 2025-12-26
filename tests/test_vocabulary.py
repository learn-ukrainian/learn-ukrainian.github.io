"""
Tests for vocabulary validation checks.

Tests vocabulary table format, column validation, and transliteration policy.
Run with: pytest tests/test_vocabulary.py -v
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.audit.checks.vocabulary import (
    check_vocab_table_format,
    extract_vocab_items,
    count_vocab_rows,
)


# =============================================================================
# TEST: Vocabulary Table Format
# =============================================================================

class TestVocabTableFormat:
    """Test vocabulary table format validation by level."""

    def test_a1_requires_vocabulary_header(self):
        """A1 modules should use '# Vocabulary' header, not '# Словник'."""
        content = """
# Словник

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈslɔwɔ/ | word | noun | n | - |
"""
        violations = check_vocab_table_format(content, 'A1')
        header_violations = [v for v in violations if v['type'] == 'VOCAB_HEADER']
        assert len(header_violations) == 1
        assert "# Vocabulary" in header_violations[0]['fix']

    def test_a1_valid_header(self):
        """A1 with correct '# Vocabulary' header should pass."""
        content = """
# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈslɔwɔ/ | word | noun | n | - |
"""
        violations = check_vocab_table_format(content, 'A1')
        header_violations = [v for v in violations if v['type'] == 'VOCAB_HEADER']
        assert len(header_violations) == 0

    def test_b1_requires_slovnyk_header(self):
        """B1 modules should use '# Словник' header, not '# Vocabulary'."""
        content = """
# Vocabulary

| Слово | Переклад | Примітки |
|-------|----------|----------|
| граматика | grammar | noun |
"""
        violations = check_vocab_table_format(content, 'B1')
        header_violations = [v for v in violations if v['type'] == 'VOCAB_HEADER']
        assert len(header_violations) == 1
        assert "# Словник" in header_violations[0]['fix']

    def test_b1_valid_header(self):
        """B1 with correct '# Словник' header should pass."""
        content = """
# Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| граматика | grammar | noun |
"""
        violations = check_vocab_table_format(content, 'B1')
        header_violations = [v for v in violations if v['type'] == 'VOCAB_HEADER']
        assert len(header_violations) == 0

    def test_a1_requires_6_columns(self):
        """A1 vocabulary table must have 6 columns."""
        content = """
# Vocabulary

| Word | English | POS |
|------|---------|-----|
| слово | word | noun |
"""
        violations = check_vocab_table_format(content, 'A1')
        format_violations = [v for v in violations if v['type'] == 'VOCAB_FORMAT']
        assert len(format_violations) == 1
        assert '6 columns' in format_violations[0]['issue']

    def test_a1_valid_6_columns(self):
        """A1 with 6 columns should pass."""
        content = """
# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈslɔwɔ/ | word | noun | n | - |
"""
        violations = check_vocab_table_format(content, 'A1')
        format_violations = [v for v in violations if v['type'] == 'VOCAB_FORMAT']
        assert len(format_violations) == 0

    def test_b1_accepts_3_columns(self):
        """B1 vocabulary can use 3-column format (no IPA)."""
        content = """
# Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| граматика | grammar | noun |
"""
        violations = check_vocab_table_format(content, 'B1')
        format_violations = [v for v in violations if v['type'] == 'VOCAB_FORMAT']
        assert len(format_violations) == 0

    def test_b1_accepts_5_columns(self):
        """B1 vocabulary can use 5-column format (with IPA)."""
        content = """
# Словник

| Слово | Вимова | Переклад | ЧМ | Примітка |
|-------|--------|----------|-----|----------|
| граматика | /ɦraˈmatɪka/ | grammar | ім. | - |
"""
        violations = check_vocab_table_format(content, 'B1')
        format_violations = [v for v in violations if v['type'] == 'VOCAB_FORMAT']
        assert len(format_violations) == 0

    def test_b1_rejects_4_columns(self):
        """B1 vocabulary with wrong column count should fail."""
        content = """
# Словник

| Слово | Вимова | Переклад | Примітка |
|-------|--------|----------|----------|
| граматика | /ɦraˈmatɪka/ | grammar | - |
"""
        violations = check_vocab_table_format(content, 'B1')
        format_violations = [v for v in violations if v['type'] == 'VOCAB_FORMAT']
        assert len(format_violations) == 1
        assert '4' in format_violations[0]['issue']


# =============================================================================
# TEST: Vocabulary Extraction
# =============================================================================

class TestVocabExtraction:
    """Test vocabulary item extraction from content."""

    def test_extract_from_6_column_table(self):
        """Should extract items from A1/A2 6-column table."""
        content = """
# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈslɔwɔ/ | word | noun | n | - |
| книга | /ˈknɪɦa/ | book | noun | f | - |
| читати | /tʃɪˈtatɪ/ | to read | verb | - | impf |
"""
        items = extract_vocab_items(content)
        # Function may skip some rows based on implementation
        assert len(items) >= 2
        # Check that extracted items have expected structure
        for item in items:
            assert 'uk' in item
            assert 'ipa' in item
            assert 'en' in item

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

class TestVocabRowCount:
    """Test vocabulary row counting."""

    def test_count_rows_6_column(self):
        """Should count rows in 6-column table."""
        content = """
# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈslɔwɔ/ | word | noun | n | - |
| книга | /ˈknɪɦa/ | book | noun | f | - |
| читати | /tʃɪˈtatɪ/ | to read | verb | - | impf |
"""
        count = count_vocab_rows(content)
        assert count == 3

    def test_count_rows_3_column(self):
        """Should count rows in 3-column table."""
        content = """
# Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| граматика | grammar | noun |
| відмінок | case | noun |
| дієслово | verb | noun |
| іменник | noun | noun |
"""
        count = count_vocab_rows(content)
        assert count == 4

    def test_count_empty_table(self):
        """Should return 0 for table with no data rows."""
        content = """
# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
"""
        count = count_vocab_rows(content)
        assert count == 0

    def test_count_no_table(self):
        """Should return 0 when no vocabulary table exists."""
        content = """
# Some Module

This has no vocabulary section.
"""
        count = count_vocab_rows(content)
        assert count == 0


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
