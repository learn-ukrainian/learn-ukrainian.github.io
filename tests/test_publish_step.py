"""Tests for the PUBLISH step — injection, workbook, resources, 4-tab output.

Issue: #1043
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import yaml

# Ensure scripts/ on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build.v6_build import (
    _build_resources_tab,
    _build_workbook_tab,
    _inject_inline_activities,
    _load_activities,
)

# ---------------------------------------------------------------------------
# _inject_inline_activities
# ---------------------------------------------------------------------------


class TestInjectInlineActivities:
    def test_replaces_marker(self):
        content = "Some prose.\n\n<!-- INJECT_ACTIVITY: quiz-genders -->\n\nMore prose."
        inline = [
            {
                "id": "quiz-genders",
                "type": "quiz",
                "instruction": "Test",
                "items": [{"question": "Q?", "options": ["A", "B", "C"], "correct": 0}],
            }
        ]
        result, unmatched = _inject_inline_activities(content, inline)
        assert "<!-- INJECT_ACTIVITY: quiz-genders -->" not in result
        assert "<Quiz" in result
        assert len(unmatched) == 0

    def test_unmatched_goes_to_workbook(self):
        content = "No markers here."
        inline = [
            {
                "id": "missing-marker",
                "type": "fill-in",
                "instruction": "Fill",
                "items": [{"sentence": "A ___.", "answer": "B"}],
            }
        ]
        result, unmatched = _inject_inline_activities(content, inline)
        assert result == content  # unchanged
        assert len(unmatched) == 1
        assert unmatched[0]["id"] == "missing-marker"

    def test_multiple_markers(self):
        content = (
            "Section 1\n\n<!-- INJECT_ACTIVITY: act-1 -->\n\n"
            "Section 2\n\n<!-- INJECT_ACTIVITY: act-2 -->\n"
        )
        inline = [
            {"id": "act-1", "type": "quiz", "instruction": "Q1",
             "items": [{"question": "?", "options": ["A", "B", "C"], "correct": 0}]},
            {"id": "act-2", "type": "fill-in", "instruction": "F1",
             "items": [{"sentence": "___", "answer": "X"}]},
        ]
        result, unmatched = _inject_inline_activities(content, inline)
        assert "<Quiz" in result
        assert "<FillIn" in result
        assert len(unmatched) == 0

    def test_mixed_matched_and_unmatched(self):
        content = "Prose\n\n<!-- INJECT_ACTIVITY: found -->\n\nEnd."
        inline = [
            {"id": "found", "type": "quiz", "instruction": "Q",
             "items": [{"question": "?", "options": ["A", "B", "C"], "correct": 0}]},
            {"id": "not-found", "type": "fill-in", "instruction": "F",
             "items": [{"sentence": "___", "answer": "X"}]},
        ]
        result, unmatched = _inject_inline_activities(content, inline)
        assert "<Quiz" in result
        assert len(unmatched) == 1


# ---------------------------------------------------------------------------
# _build_workbook_tab
# ---------------------------------------------------------------------------


class TestBuildWorkbookTab:
    def test_empty_shows_placeholder(self):
        result = _build_workbook_tab([])
        assert "в розро" in result  # "в розробці"
        assert ":::note" in result

    def test_renders_activities(self):
        activities = [
            {
                "type": "match-up",
                "instruction": "Match",
                "pairs": [{"left": "A", "right": "B"}, {"left": "C", "right": "D"}, {"left": "E", "right": "F"}],
            },
            {
                "type": "true-false",
                "instruction": "T/F",
                "items": [{"statement": "True?", "correct": True}],
            },
        ]
        result = _build_workbook_tab(activities)
        assert "<MatchUp" in result
        assert "<TrueFalse" in result


# ---------------------------------------------------------------------------
# _build_resources_tab
# ---------------------------------------------------------------------------


class TestBuildResourcesTab:
    def test_no_plan_no_resources(self, tmp_path):
        """When plan and external resources don't exist, show placeholder."""
        # Patch CURRICULUM_ROOT and PROJECT_ROOT to tmp_path
        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path), \
             patch("build.v6_build.PROJECT_ROOT", tmp_path):
            result = _build_resources_tab("a1", "nonexistent-module")
            assert "References" in result

    def test_with_plan_references(self, tmp_path):
        """Plan references are included in output."""
        plans_dir = tmp_path / "plans" / "a1"
        plans_dir.mkdir(parents=True)
        plan = {
            "title": "Test",
            "references": [
                "Пономарова Grade 3, p.86",
                {"title": "ULP Episode 6", "url": "https://example.com", "note": "Gender"},
            ],
        }
        (plans_dir / "test-mod.yaml").write_text(
            yaml.dump(plan, allow_unicode=True), "utf-8"
        )

        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path), \
             patch("build.v6_build.PROJECT_ROOT", tmp_path):
            result = _build_resources_tab("a1", "test-mod")
            assert "Пономарова" in result
            assert "ULP Episode 6" in result
            assert "https://example.com" in result


# ---------------------------------------------------------------------------
# _load_activities
# ---------------------------------------------------------------------------


class TestLoadActivities:
    def test_missing_file_returns_none(self, tmp_path):
        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path):
            result = _load_activities("a1", "nonexistent")
            assert result is None

    def test_valid_yaml(self, tmp_path):
        activities_dir = tmp_path / "a1" / "activities"
        activities_dir.mkdir(parents=True)
        data = {
            "version": "1.0",
            "module": "test",
            "level": "a1",
            "inline": [{"id": "q1", "type": "quiz", "instruction": "Q",
                         "items": [{"question": "?", "options": ["A", "B", "C"], "correct": 0}]}],
            "workbook": [],
        }
        (activities_dir / "test.yaml").write_text(
            yaml.dump(data, allow_unicode=True), "utf-8"
        )

        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path):
            result = _load_activities("a1", "test")
            assert result is not None
            assert len(result["inline"]) == 1

    def test_invalid_yaml_returns_none(self, tmp_path):
        activities_dir = tmp_path / "a1" / "activities"
        activities_dir.mkdir(parents=True)
        (activities_dir / "bad.yaml").write_text("not: [valid: yaml: {{", "utf-8")

        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path):
            result = _load_activities("a1", "bad")
            assert result is None


# ---------------------------------------------------------------------------
# Backward compatibility: no activities.yaml → legacy behavior
# ---------------------------------------------------------------------------


class TestBackwardCompat:
    def test_no_activities_file_falls_through(self, tmp_path):
        """When no activities/{slug}.yaml exists, the publish step should
        still work with just DSL→MDX conversion (tested via _load_activities)."""
        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path):
            result = _load_activities("a1", "missing-module")
            assert result is None
