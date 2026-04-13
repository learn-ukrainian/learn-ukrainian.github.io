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
    _build_resources_tab_full,
    _build_slovnyk_tab,
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


# ---------------------------------------------------------------------------
# _build_slovnyk_tab (#1124)
# ---------------------------------------------------------------------------


class TestBuildSlovnykTab:
    def test_from_vocabulary_yaml(self, tmp_path):
        """Словник tab built from vocabulary/{slug}.yaml when available."""
        vocab_dir = tmp_path / "a1" / "vocabulary"
        vocab_dir.mkdir(parents=True)
        vocab_data = {
            "vocabulary": [
                {"word": "мама", "translation": "mother", "pos": "ім.", "gender": "ж."},
                {"word": "тато", "translation": "father", "pos": "ім.", "gender": "ч."},
            ]
        }
        (vocab_dir / "test-mod.yaml").write_text(
            yaml.dump(vocab_data, allow_unicode=True), "utf-8"
        )

        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path):
            result = _build_slovnyk_tab("a1", "test-mod")
            # build_slovnyk_markdown adds stress marks (ма́ма), so strip for comparison
            result_stripped = result.replace("\u0301", "")
            assert "мама" in result_stripped
            assert "тато" in result_stripped
            assert "mother" in result

    def test_fallback_to_plan(self, tmp_path):
        """Falls back to plan vocabulary_hints when no vocabulary YAML exists."""
        plans_dir = tmp_path / "plans" / "a1"
        plans_dir.mkdir(parents=True)
        plan = {
            "title": "Test",
            "level": "a1",
            "vocabulary_hints": {
                "required": ["привіт (hello)", "так (yes)"],
            },
        }
        (plans_dir / "test-mod.yaml").write_text(
            yaml.dump(plan, allow_unicode=True), "utf-8"
        )

        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path), \
             patch("build.enrich._CURRICULUM_ROOT", tmp_path):
            result = _build_slovnyk_tab("a1", "test-mod")
            assert "привіт" in result
            assert "hello" in result

    def test_no_vocab_returns_empty(self, tmp_path):
        """Returns empty string when no vocabulary source exists."""
        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path):
            result = _build_slovnyk_tab("a1", "nonexistent-mod")
            assert result == ""


# ---------------------------------------------------------------------------
# _build_resources_tab_full (#1124)
# ---------------------------------------------------------------------------


class TestBuildResourcesTabFull:
    def test_with_plan_references(self, tmp_path):
        """Full resources tab includes plan references."""
        plans_dir = tmp_path / "plans" / "a1"
        plans_dir.mkdir(parents=True)
        plan = {
            "title": "Test",
            "references": [
                {"title": "ULP Episode 1", "url": "https://example.com"},
            ],
        }
        (plans_dir / "test-mod.yaml").write_text(
            yaml.dump(plan, allow_unicode=True), "utf-8"
        )

        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path), \
             patch("build.v6_build.PROJECT_ROOT", tmp_path), \
             patch("build.enrich._PROJECT_ROOT", tmp_path):
            result = _build_resources_tab_full("a1", "test-mod")
            assert "ULP Episode 1" in result
            assert "https://example.com" in result

    def test_no_plan_falls_back(self, tmp_path):
        """Shows the localized placeholder when no resources exist."""
        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path), \
             patch("build.v6_build.PROJECT_ROOT", tmp_path):
            result = _build_resources_tab_full("a1", "nonexistent-mod")
            assert result == "_Ресурси будуть додані пізніше._"
