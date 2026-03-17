"""Tests for semantic Russicism auto-fix in plan_autofix."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "tools"))

from plan_autofix import fix_russianisms_in_plan


class TestFixRussianismsInPlan:
    def test_fixes_город_city(self, tmp_path):
        plan = tmp_path / "plan.yaml"
        plan.write_text(
            "version: '2.0'\n"
            "vocabulary_hints:\n"
            "  required:\n"
            '  - "город (city) — demonstrates Г"\n'
            '  - "дім (house) — high-frequency"\n'
        )
        issues = [{"issue_type": "RUSSICISM", "problem": "город paired with 'city'",
                    "suggested_fix": "Replace город (city) with місто (city)"}]
        n, changelog = fix_russianisms_in_plan(plan, issues)
        assert n == 1
        assert "місто" in changelog[0]
        content = plan.read_text()
        assert "місто (city)" in content
        assert "город (city)" not in content
        # дім should be untouched
        assert "дім (house)" in content

    def test_fixes_лук_onion(self, tmp_path):
        plan = tmp_path / "plan.yaml"
        plan.write_text(
            "version: '1.0'\n"
            "vocabulary_hints:\n"
            "  required:\n"
            '  - "лук (onion) — food vocabulary"\n'
        )
        issues = [{"issue_type": "RUSSICISM", "problem": "лук paired with 'onion'",
                    "suggested_fix": "Replace лук (onion) with цибуля (onion)"}]
        n, _changelog = fix_russianisms_in_plan(plan, issues)
        assert n == 1
        content = plan.read_text()
        assert "цибуля (onion)" in content
        assert "лук (onion)" not in content

    def test_no_russicism_issues_returns_zero(self, tmp_path):
        plan = tmp_path / "plan.yaml"
        plan.write_text("version: '1.0'\nvocabulary_hints:\n  required:\n  - 'дім (house)'\n")
        issues = [{"issue_type": "CONTRADICTION", "problem": "something else"}]
        n, _changelog = fix_russianisms_in_plan(plan, issues)
        assert n == 0
        assert _changelog == []

    def test_empty_issues(self, tmp_path):
        plan = tmp_path / "plan.yaml"
        plan.write_text("version: '1.0'\n")
        n, _changelog = fix_russianisms_in_plan(plan, [])
        assert n == 0

    def test_version_bumped(self, tmp_path):
        plan = tmp_path / "plan.yaml"
        plan.write_text(
            "version: '2.0'\n"
            "vocabulary_hints:\n"
            "  required:\n"
            '  - "город (city) — test"\n'
        )
        issues = [{"issue_type": "RUSSICISM", "problem": "город paired with 'city'",
                    "suggested_fix": "fix it"}]
        fix_russianisms_in_plan(plan, issues)
        content = plan.read_text()
        assert "2.0.1" in content

    def test_nonexistent_plan(self, tmp_path):
        plan = tmp_path / "nonexistent.yaml"
        issues = [{"issue_type": "RUSSICISM", "problem": "город city"}]
        n, _changelog = fix_russianisms_in_plan(plan, issues)
        assert n == 0

    def test_warning_not_flagged_as_russicism(self, tmp_path):
        """If the issue type is not RUSSICISM, don't touch the plan."""
        plan = tmp_path / "plan.yaml"
        plan.write_text(
            "version: '1.0'\n"
            "vocabulary_hints:\n"
            "  required:\n"
            '  - "неділя (Sunday) — correct usage"\n'
        )
        issues = [{"issue_type": "MISSING_INSTRUCTION", "problem": "something about неділя"}]
        n, _changelog = fix_russianisms_in_plan(plan, issues)
        assert n == 0
        # Original untouched
        assert "неділя (Sunday)" in plan.read_text()
