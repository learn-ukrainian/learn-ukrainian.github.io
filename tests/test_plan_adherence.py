"""Tests for plan adherence checker (scripts/audit/checks/plan_adherence.py).

Issue: #849
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from audit.checks.plan_adherence import (
    _strip_stress,
    check_activity_counts,
    check_activity_focus,
    check_plan_adherence,
    check_structural_elements,
    check_vocab_coverage,
)

# ---------------------------------------------------------------------------
# Utility tests
# ---------------------------------------------------------------------------


class TestStripStress:
    def test_removes_combining_acute(self):
        assert _strip_stress("ма\u0301ма") == "мама"


# ---------------------------------------------------------------------------
# Check 1: Vocab coverage
# ---------------------------------------------------------------------------


class TestCheckVocabCoverage:
    def test_missing_word(self):
        plan = {"vocabulary_hints": {"required": ["мама (mom)", "кіт (cat)"]}}
        content = "This is мама."
        issues = check_vocab_coverage(plan, content, "")
        assert len(issues) == 1
        assert issues[0].check_type == "VOCAB_NOT_IN_CONTENT"
        assert "кіт" in issues[0].expected

    def test_stress_normalized_match(self):
        """Word with stress mark in content should match unstressed hint."""
        plan = {"vocabulary_hints": {"required": ["мама (mom)"]}}
        content = "This is ма\u0301ма."
        issues = check_vocab_coverage(plan, content, "")
        assert issues == []

    def test_substring_does_not_match(self):
        """'кіт' should not match inside 'кімната'."""
        plan = {"vocabulary_hints": {"required": ["кіт (cat)"]}}
        content = "У кімнаті було тепло."
        issues = check_vocab_coverage(plan, content, "")
        assert len(issues) == 1
        assert issues[0].check_type == "VOCAB_NOT_IN_CONTENT"


# ---------------------------------------------------------------------------
# Check 2: Structural elements
# ---------------------------------------------------------------------------


class TestCheckStructuralElements:
    def test_chart_keyword_without_table(self):
        plan = {
            "content_outline": [{
                "section": "Вступ — Introduction",
                "points": ["Show the full 33-letter alphabet chart as a reference map"],
            }]
        }
        content = "## Вступ — Introduction\nThe alphabet has 33 letters. They are phonetic.\n"
        issues = check_structural_elements(plan, content)
        assert len(issues) == 1
        assert issues[0].check_type == "MISSING_STRUCTURAL_ELEMENT"
        assert issues[0].severity == "HIGH"


# ---------------------------------------------------------------------------
# Check 3: Activity counts
# ---------------------------------------------------------------------------


class TestCheckActivityCounts:
    def test_undercount(self):
        plan = {"activity_hints": [{"type": "watch-and-repeat", "items": 10}]}
        activities = [{"type": "watch-and-repeat", "items": [1, 2, 3, 4]}]
        issues = check_activity_counts(plan, activities)
        assert len(issues) == 1
        assert issues[0].check_type == "ACTIVITY_UNDERCOUNT"
        assert issues[0].severity == "HIGH"
        assert "6 more" in issues[0].fix_hint

    def test_missing_type(self):
        plan = {"activity_hints": [{"type": "classify", "items": 10}]}
        activities = [{"type": "quiz", "items": [1, 2, 3]}]
        issues = check_activity_counts(plan, activities)
        assert len(issues) == 1
        assert issues[0].check_type == "ACTIVITY_TYPE_MISSING"
        assert issues[0].severity == "HIGH"


# ---------------------------------------------------------------------------
# Check 4: Activity focus
# ---------------------------------------------------------------------------


class TestCheckActivityFocus:
    def test_false_friend_detected_as_mismatch(self):
        plan = {
            "activity_hints": [{
                "type": "match-up",
                "focus": "Match Ukrainian letter to its sound (for false friends: Н≠H, С≠C)",
                "items": 6,
            }]
        }
        # Built activity does word→translation instead
        activities = [{
            "type": "match-up",
            "pairs": [{"left": "мама", "right": "mom"}, {"left": "тато", "right": "dad"}],
        }]
        issues = check_activity_focus(plan, activities)
        assert len(issues) == 1
        assert issues[0].check_type == "ACTIVITY_FOCUS_MISMATCH"


# ---------------------------------------------------------------------------
# Integration: check_plan_adherence
# ---------------------------------------------------------------------------


class TestCheckPlanAdherence:
    def test_full_check_with_files(self, tmp_path):
        # Create plan YAML
        plan = {
            "vocabulary_hints": {"required": ["мама (mom)", "кіт (cat)"]},
            "content_outline": [{
                "section": "Intro",
                "points": ["Show the alphabet chart"],
            }],
            "activity_hints": [{"type": "quiz", "items": 6}],
        }
        plan_path = tmp_path / "plan.yaml"
        plan_path.write_text(yaml.dump(plan, allow_unicode=True), encoding="utf-8")

        # Create content with мама but missing кіт, and no table
        md_path = tmp_path / "module.md"
        md_path.write_text("## Intro\nWelcome! мама is here.\n", encoding="utf-8")

        # Create activities with enough items
        activities_path = tmp_path / "activities.yaml"
        activities = [{"type": "quiz", "items": [{"q": i} for i in range(6)]}]
        activities_path.write_text(yaml.dump(activities, allow_unicode=True), encoding="utf-8")

        result = check_plan_adherence(md_path, plan_path, activities_path)
        assert result.checks_run == 4

        # Should find: VOCAB_NOT_IN_CONTENT (кіт) + MISSING_STRUCTURAL_ELEMENT
        types = {i.check_type for i in result.issues}
        assert "VOCAB_NOT_IN_CONTENT" in types
        assert "MISSING_STRUCTURAL_ELEMENT" in types
        assert not result.passed  # HIGH issues present

    def test_v2_activity_undercount_is_detected(self, tmp_path):
        plan = {"activity_hints": [{"type": "quiz", "items": 4}]}
        plan_path = tmp_path / "plan.yaml"
        plan_path.write_text(yaml.safe_dump(plan), encoding="utf-8")

        md_path = tmp_path / "module.md"
        md_path.write_text("## Вступ\nТекст модуля.\n", encoding="utf-8")

        activities = {
            "version": 2,
            "module": "test-module",
            "inline": [{"type": "quiz", "items": [{}, {}, {}]}],
            "workbook": [],
        }
        activities_path = tmp_path / "activities.yaml"
        activities_path.write_text(yaml.safe_dump(activities), encoding="utf-8")

        result = check_plan_adherence(md_path, plan_path, activities_path)

        assert any(issue.check_type == "ACTIVITY_UNDERCOUNT" for issue in result.issues)
        assert not result.passed
