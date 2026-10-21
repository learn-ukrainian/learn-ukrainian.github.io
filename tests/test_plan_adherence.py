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
    check_plan_adherence,
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

    def test_stress_normalized_match(self):
        """Word with stress mark in content should match unstressed hint."""
        plan = {"vocabulary_hints": {"required": ["мама (mom)"]}}
        content = "This is ма\u0301ма."
        issues = check_vocab_coverage(plan, content, "")
        assert issues == []


# ---------------------------------------------------------------------------
# Check 2: Structural elements
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Check 3: Activity counts
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Check 4: Activity focus
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Integration: check_plan_adherence
# ---------------------------------------------------------------------------


class TestCheckPlanAdherence:

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
