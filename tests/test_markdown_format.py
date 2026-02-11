"""
Tests for markdown format validation checks.

Tests scripts/audit/checks/markdown_format.py functions.

Run with: pytest tests/test_markdown_format.py -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.audit.checks.markdown_format import (
    check_frontmatter_spacing,
    check_heading_levels,
    check_table_column_consistency,
    check_forbidden_headers,
)


# =============================================================================
# TEST: check_frontmatter_spacing
# =============================================================================

class TestCheckFrontmatterSpacing:
    def test_with_blank_line(self):
        content = "---\nmodule: 1\n---\n\n# Title"
        violations = check_frontmatter_spacing(content)
        assert len(violations) == 0

    def test_without_blank_line(self):
        content = "---\nmodule: 1\n---\n# Title"
        violations = check_frontmatter_spacing(content)
        assert len(violations) == 1
        assert violations[0]['type'] == 'FRONTMATTER_SPACING'

    def test_no_frontmatter(self):
        content = "# Just a title\n\nContent here."
        violations = check_frontmatter_spacing(content)
        assert len(violations) == 0


# =============================================================================
# TEST: check_heading_levels
# =============================================================================

class TestCheckHeadingLevels:
    def test_valid_hierarchy(self):
        content = "---\nmodule: 1\n---\n\n# Title\n\n## Subsection\n\n### Detail"
        violations = check_heading_levels(content)
        # Title is first H1 (valid), rest are H2/H3 (valid)
        stray_h1 = [v for v in violations if 'Non-standard H1' in v.get('issue', '')]
        assert len(stray_h1) == 0

    def test_stray_h1(self):
        content = "---\nmodule: 1\n---\n\n# Title\n\n# Random Section\n\nContent"
        violations = check_heading_levels(content)
        stray_h1 = [v for v in violations if 'Non-standard H1' in v.get('issue', '')]
        assert len(stray_h1) >= 1

    def test_seminar_track_allows_h2_summary(self):
        """Seminar tracks use flat H2 for Підсумок."""
        content = "---\nmodule: 1\n---\n\n# Title\n\n## Підсумок\n\nContent"
        violations = check_heading_levels(content, level_code='c1-bio')
        # Should NOT flag Підсумок as needing H1 in seminar tracks
        summary_violations = [v for v in violations if 'підсумок' in v.get('issue', '').lower()]
        assert len(summary_violations) == 0


# =============================================================================
# TEST: check_table_column_consistency
# =============================================================================

class TestCheckTableColumnConsistency:
    def test_valid_table(self):
        content = "| A | B | C |\n|---|---|---|\n| 1 | 2 | 3 |\n| 4 | 5 | 6 |"
        violations = check_table_column_consistency(content)
        assert len(violations) == 0

    def test_mismatched_columns(self):
        content = "| A | B | C |\n|---|---|\n| 1 | 2 | 3 |"
        violations = check_table_column_consistency(content)
        assert len(violations) >= 1
        assert violations[0]['type'] == 'TABLE_COLUMN_MISMATCH'

    def test_no_tables(self):
        content = "Just plain text with no tables at all."
        violations = check_table_column_consistency(content)
        assert len(violations) == 0


# =============================================================================
# TEST: check_forbidden_headers
# =============================================================================

class TestCheckForbiddenHeaders:
    def test_forbidden_activities_header(self):
        content = "---\nmodule: 1\n---\n\n# Title\n\n## Activities\n\nContent"
        violations = check_forbidden_headers(content)
        assert len(violations) == 1
        assert violations[0]['type'] == 'FORBIDDEN_HEADER'
        assert 'Activities' in violations[0]['issue']

    def test_forbidden_vocabulary_header(self):
        content = "---\nmodule: 1\n---\n\n# Title\n\n## Словник\n\nContent"
        violations = check_forbidden_headers(content)
        assert len(violations) == 1
        assert 'Словник' in violations[0]['issue']

    def test_allowed_headers(self):
        content = "---\nmodule: 1\n---\n\n# Title\n\n## Presentation\n\n## Practice"
        violations = check_forbidden_headers(content)
        assert len(violations) == 0

    def test_forbidden_in_frontmatter_ignored(self):
        """Headers inside frontmatter should not trigger."""
        content = "---\nmodule: 1\ntitle: Activities\n---\n\n# Title\n\nContent"
        violations = check_forbidden_headers(content)
        assert len(violations) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
