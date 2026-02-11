"""
Tests for audit core helper functions.

Tests pure helper functions in scripts/audit/core.py (no file I/O).

Run with: pytest tests/test_audit_core_helpers.py -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.audit.core import (
    parse_frontmatter,
    detect_level,
    parse_sections,
    check_typography,
)


# =============================================================================
# TEST: parse_frontmatter
# =============================================================================

class TestParseFrontmatter:
    def test_valid_frontmatter(self):
        content = "---\nmodule: 1\ntitle: Test\n---\n\n# Body content"
        fm, body = parse_frontmatter(content)
        assert 'module: 1' in fm
        assert '# Body content' in body

    def test_no_frontmatter(self):
        content = "# Just a heading\n\nSome content."
        fm, body = parse_frontmatter(content)
        assert fm == ""
        assert body == content

    def test_empty_frontmatter(self):
        content = "---\n---\n\nBody"
        fm, body = parse_frontmatter(content)
        assert fm == ""
        assert 'Body' in body

    def test_multiline_frontmatter(self):
        content = "---\nmodule: 5\ntitle: Тест\nlevel: B1\npedagogy: PPP\n---\n\n# Зміст"
        fm, body = parse_frontmatter(content)
        assert 'module: 5' in fm
        assert 'level: B1' in fm
        assert '# Зміст' in body


# =============================================================================
# TEST: detect_level
# =============================================================================

class TestDetectLevel:
    def test_b1_from_path(self):
        level, num, track = detect_level(
            '/curriculum/l2-uk-en/b1/05-test.md', 'level: B1'
        )
        assert level == 'B1'
        assert num == 5

    def test_c1_bio_from_path(self):
        level, num, track = detect_level(
            '/curriculum/l2-uk-en/c1-bio/taras-shevchenko.md', 'level: C1'
        )
        assert level == 'C1'
        assert 'BIO' in track.upper()

    def test_b2_hist_from_path(self):
        level, num, track = detect_level(
            '/curriculum/l2-uk-en/b2-hist/01-trypilska.md', 'level: B2'
        )
        assert level == 'B2'
        assert 'HIST' in track.upper()
        assert num == 1

    def test_lit_from_path(self):
        level, num, track = detect_level(
            '/curriculum/l2-uk-en/lit/01-shevchenko.md', 'phase: LIT'
        )
        assert level == 'LIT'

    def test_module_number_extraction(self):
        level, num, track = detect_level(
            '/curriculum/l2-uk-en/a1/12-alphabet.md', ''
        )
        assert num == 12

    def test_no_number_in_filename(self):
        level, num, track = detect_level(
            '/curriculum/l2-uk-en/c1-bio/taras-shevchenko.md', ''
        )
        assert num == 999  # Default when no number found


# =============================================================================
# TEST: parse_sections
# =============================================================================

class TestParseSections:
    def test_h2_splitting(self):
        body = "\n## Section One\nContent 1\n## Section Two\nContent 2"
        sections = parse_sections(body)
        assert 'Section One' in sections
        assert 'Section Two' in sections

    def test_intro_section(self):
        body = "Intro text here.\n\n## First Section\nContent"
        sections = parse_sections(body)
        assert 'Intro/Narrative' in sections
        assert 'First Section' in sections

    def test_empty_body(self):
        sections = parse_sections("")
        assert len(sections) == 0

    def test_mixed_h1_h2(self):
        body = "\n# Main Section\nContent A\n## Sub Section\nContent B"
        sections = parse_sections(body)
        assert 'Main Section' in sections
        assert 'Sub Section' in sections


# =============================================================================
# TEST: check_typography
# =============================================================================

class TestCheckTypography:
    def test_clean_content(self):
        """Typography check is disabled, should always return empty."""
        errors = check_typography("Content with 'quotes' and \"double quotes\"")
        assert errors == []

    def test_with_issues(self):
        """Even with ASCII quotes, should return empty (disabled check)."""
        errors = check_typography('He said "hello" and \'goodbye\'.')
        assert errors == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
