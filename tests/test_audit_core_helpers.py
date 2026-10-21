"""
Tests for audit core helper functions.

Tests pure helper functions in scripts/audit/core.py (no file I/O).

Run with: pytest tests/test_audit_core_helpers.py -v
"""

import os
import sys

import pytest

pytestmark = pytest.mark.reads_content

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.audit.core import (
    parse_frontmatter,
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


# =============================================================================
# TEST: detect_level
# =============================================================================


# =============================================================================
# TEST: parse_sections
# =============================================================================


# =============================================================================
# TEST: check_typography
# =============================================================================


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
