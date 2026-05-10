"""Tests for dashboard data generation and HTML validation."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import ClassVar

import pytest

ROOT = Path(__file__).resolve().parent.parent
DASHBOARDS_DIR = ROOT / "dashboards"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "generate_mdx"))

from generate_dashboard_data import (
    parse_activity_count,
    parse_naturalness,
    parse_word_count,
)


class TestParseWordCount:
    """Tests for parse_word_count helper."""

    def test_standard_format(self):
        msg = "3375/3000 (raw: 3539)"
        count, target = parse_word_count(msg)
        assert count == 3375
        assert target == 3000

    def test_simple_format(self):
        msg = "500/1000"
        count, target = parse_word_count(msg)
        assert count == 500
        assert target == 1000

    def test_invalid_returns_zero(self):
        msg = "invalid"
        count, target = parse_word_count(msg)
        assert count == 0
        assert target == 0

    def test_empty_returns_zero(self):
        assert parse_word_count("") == (0, 0)


class TestParseActivityCount:
    """Tests for parse_activity_count helper."""

    def test_standard(self):
        assert parse_activity_count("13/8") == 13
        assert parse_activity_count("8/8") == 8

    def test_invalid(self):
        assert parse_activity_count("invalid") == 0
        assert parse_activity_count("") == 0


class TestParseNaturalness:
    """Tests for parse_naturalness helper."""

    def test_standard(self):
        assert parse_naturalness("9/10 (High)") == 9

    def test_low_score(self):
        assert parse_naturalness("4/10 (Low)") == 4

    def test_invalid(self):
        assert parse_naturalness("invalid") == 0
        assert parse_naturalness("") == 0


class TestDashboardHtml:
    """Validation of generated dashboard HTML structure."""

    HTML_FILES: ClassVar[list[str]] = [
        "index.html",
        "artifacts.html",
        "dashboard-module-status.html",
    ]

    @pytest.mark.parametrize("filename", HTML_FILES)
    def test_html_well_formed(self, filename):
        path = DASHBOARDS_DIR / filename
        if not path.exists():
            pytest.skip(f"{filename} not built yet")

        content = path.read_text(encoding="utf-8")
        assert content.strip().startswith("<!DOCTYPE html>")
        assert "</html>" in content
        assert "<head>" in content
        assert "<body>" in content

    @pytest.mark.parametrize("filename", HTML_FILES)
    def test_no_broken_placeholders(self, filename):
        path = DASHBOARDS_DIR / filename
        if not path.exists():
            pytest.skip(f"{filename} not built yet")

        content = path.read_text(encoding="utf-8")
        # Check for unreplaced template variables like {{ ... }}
        # Exclude common JS syntax or CSS rules
        placeholders = re.findall(r"\{\{[A-Za-z0-9_]+\}\}", content)
        assert not placeholders, f"Found unreplaced placeholders in {filename}: {placeholders}"

    def test_module_status_dashboard_has_data_script(self):
        path = DASHBOARDS_DIR / "dashboard-module-status.html"
        if not path.exists():
            pytest.skip("dashboard-module-status.html not built yet")

        content = path.read_text(encoding="utf-8")
        assert "const LEVELS_DATA =" in content
        assert "renderLevels()" in content
