"""Tests for scripts/slug_utils.py — slug stripping and path construction."""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.slug_utils import (
    to_bare_slug,
    review_path,
    audit_report_path,
    grammar_path,
    quality_path,
    status_path,
)


class TestToBareSlag:
    """to_bare_slug() edge cases."""

    def test_two_digit_prefix(self):
        assert to_bare_slug("01-the-cyrillic-code-i") == "the-cyrillic-code-i"

    def test_two_digit_prefix_high(self):
        assert to_bare_slug("44-a1-final-exam") == "a1-final-exam"

    def test_three_digit_prefix(self):
        """B2-HIST has 140 modules — must handle 3-digit prefixes."""
        assert to_bare_slug("140-syntez-viyna") == "syntez-viyna"

    def test_bare_slug_noop(self):
        """Already bare slug should pass through unchanged."""
        assert to_bare_slug("knyahynia-olha") == "knyahynia-olha"

    def test_with_md_extension(self):
        assert to_bare_slug("01-the-cyrillic-code-i.md") == "the-cyrillic-code-i"

    def test_with_yaml_extension(self):
        assert to_bare_slug("05-my-world-objects.yaml") == "my-world-objects"

    def test_bare_slug_with_extension(self):
        assert to_bare_slug("knyahynia-olha.yaml") == "knyahynia-olha"

    def test_single_digit_prefix(self):
        assert to_bare_slug("1-intro") == "intro"

    def test_slug_starting_with_digits_no_hyphen(self):
        """Slug like '2pac' should NOT have prefix stripped (no hyphen after digits)."""
        assert to_bare_slug("2pac") == "2pac"

    def test_empty_string(self):
        assert to_bare_slug("") == ""

    def test_just_number_prefix(self):
        """Edge: '01-' should produce empty string."""
        assert to_bare_slug("01-") == ""


class TestPathConstructors:
    """Path helper functions."""

    def setup_method(self):
        self.track_dir = Path("/fake/curriculum/l2-uk-en/b1")

    def test_review_path_from_numbered_slug(self):
        result = review_path(self.track_dir, "06-the-living-verb-i")
        assert result == self.track_dir / "review" / "the-living-verb-i-review.md"

    def test_review_path_from_bare_slug(self):
        result = review_path(self.track_dir, "knyahynia-olha")
        assert result == self.track_dir / "review" / "knyahynia-olha-review.md"

    def test_audit_report_path(self):
        result = audit_report_path(self.track_dir, "01-the-cyrillic-code-i")
        assert result == self.track_dir / "audit" / "the-cyrillic-code-i-audit.md"

    def test_grammar_path(self):
        result = grammar_path(self.track_dir, "01-the-cyrillic-code-i")
        assert result == self.track_dir / "audit" / "the-cyrillic-code-i-grammar.yaml"

    def test_quality_path(self):
        result = quality_path(self.track_dir, "01-the-cyrillic-code-i")
        assert result == self.track_dir / "audit" / "the-cyrillic-code-i-quality.md"

    def test_status_path(self):
        result = status_path(self.track_dir, "01-the-cyrillic-code-i")
        assert result == self.track_dir / "status" / "the-cyrillic-code-i.json"

    def test_status_path_three_digit(self):
        result = status_path(self.track_dir, "140-syntez-viyna")
        assert result == self.track_dir / "status" / "syntez-viyna.json"

    def test_review_path_with_extension(self):
        """Passing a filename with extension should still work."""
        result = review_path(self.track_dir, "01-the-cyrillic-code-i.md")
        assert result == self.track_dir / "review" / "the-cyrillic-code-i-review.md"
