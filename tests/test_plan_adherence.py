"""Tests for plan adherence checker (scripts/audit/checks/plan_adherence.py).

Issue: #849
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from audit.checks.plan_adherence import (
    _count_activity_items,
    _extract_sections,
    _extract_word_from_hint,
    _section_has_structural_element,
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

    def test_no_stress_unchanged(self):
        assert _strip_stress("мама") == "мама"

    def test_multiple_stress_marks(self):
        assert _strip_stress("молоко\u0301") == "молоко"

    def test_empty_string(self):
        assert _strip_stress("") == ""


class TestExtractWordFromHint:
    def test_basic_hint(self):
        assert _extract_word_from_hint("мама (mom) — decodable") == "мама"

    def test_stressed_word(self):
        assert _extract_word_from_hint("ма\u0301ма (mom)") == "ма\u0301ма"

    def test_empty(self):
        assert _extract_word_from_hint("") == ""

    def test_single_word(self):
        assert _extract_word_from_hint("кіт") == "кіт"


class TestExtractSections:
    def test_basic_sections(self):
        md = textwrap.dedent("""\
            # Title
            Intro text.

            ## Section One
            Content one.

            ## Section Two
            Content two.
        """)
        sections = _extract_sections(md)
        assert "Section One" in sections
        assert "Section Two" in sections
        assert "Content one." in sections["Section One"]

    def test_empty_content(self):
        assert _extract_sections("") == {}


class TestSectionHasStructuralElement:
    def test_has_table(self):
        text = "Some text.\n\n| Col1 | Col2 |\n|------|------|\n| a | b |\n"
        assert _section_has_structural_element(text) is True

    def test_has_bullet_list(self):
        text = "Some text.\n\n- Item one\n- Item two\n"
        assert _section_has_structural_element(text) is True

    def test_prose_only(self):
        text = "Some text. More text. Even more text."
        assert _section_has_structural_element(text) is False

    def test_star_bullet(self):
        text = "Text.\n* Item one\n* Item two\n"
        assert _section_has_structural_element(text) is True

    def test_numbered_list(self):
        text = "Text.\n1. First\n2. Second\n3. Third\n"
        assert _section_has_structural_element(text) is True


class TestCountActivityItems:
    def test_items_key(self):
        assert _count_activity_items({"items": [1, 2, 3]}) == 3

    def test_pairs_key(self):
        assert _count_activity_items({"pairs": [{"left": "a", "right": "b"}]}) == 1

    def test_groups_key(self):
        act = {"groups": [{"items": ["a", "b"]}, {"items": ["c"]}]}
        assert _count_activity_items(act) == 3

    def test_categories_key(self):
        act = {"categories": [{"items": ["a", "b", "c"]}]}
        assert _count_activity_items(act) == 3

    def test_empty(self):
        assert _count_activity_items({}) == 0


# ---------------------------------------------------------------------------
# Check 1: Vocab coverage
# ---------------------------------------------------------------------------


class TestCheckVocabCoverage:
    def test_all_present(self):
        plan = {"vocabulary_hints": {"required": ["мама (mom)", "тато (dad)"]}}
        content = "This is мама and тато."
        issues = check_vocab_coverage(plan, content, "")
        assert issues == []

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

    def test_found_in_activities(self):
        plan = {"vocabulary_hints": {"required": ["кіт (cat)"]}}
        content = "No cat here."
        activities = "answer: кіт"
        issues = check_vocab_coverage(plan, content, activities)
        assert issues == []

    def test_no_hints(self):
        plan = {}
        issues = check_vocab_coverage(plan, "text", "")
        assert issues == []

    def test_substring_does_not_match(self):
        """'кіт' should not match inside 'кімната'."""
        plan = {"vocabulary_hints": {"required": ["кіт (cat)"]}}
        content = "У кімнаті було тепло."
        issues = check_vocab_coverage(plan, content, "")
        assert len(issues) == 1
        assert issues[0].check_type == "VOCAB_NOT_IN_CONTENT"

    def test_word_with_punctuation_matches(self):
        """'кіт' should match even when followed by punctuation."""
        plan = {"vocabulary_hints": {"required": ["кіт (cat)"]}}
        content = "Це кіт, а не собака."
        issues = check_vocab_coverage(plan, content, "")
        assert issues == []


# ---------------------------------------------------------------------------
# Check 2: Structural elements
# ---------------------------------------------------------------------------


class TestCheckStructuralElements:
    def test_chart_keyword_with_table(self):
        plan = {
            "content_outline": [{
                "section": "Вступ — Introduction",
                "points": ["Show the full 33-letter alphabet chart as a reference map"],
            }]
        }
        content = "## Вступ — Introduction\nText here.\n\n| Letter | Sound |\n|--------|-------|\n| А | a |\n"
        issues = check_structural_elements(plan, content)
        assert issues == []

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

    def test_list_keyword_with_bullets(self):
        plan = {
            "content_outline": [{
                "section": "Vowels",
                "points": ["List all 10 vowel letters"],
            }]
        }
        content = "## Vowels\nHere are the vowels:\n- А\n- О\n- У\n"
        issues = check_structural_elements(plan, content)
        assert issues == []

    def test_no_visual_keywords(self):
        """Points without visual keywords should not trigger checks."""
        plan = {
            "content_outline": [{
                "section": "Intro",
                "points": ["Explain the concept of phonetics"],
            }]
        }
        content = "## Intro\nPhonetics is the study of sounds.\n"
        issues = check_structural_elements(plan, content)
        assert issues == []

    def test_show_keyword_triggers_check(self):
        plan = {
            "content_outline": [{
                "section": "Overview",
                "points": ["Show the letter categories"],
            }]
        }
        content = "## Overview\nThere are vowels and consonants.\n"
        issues = check_structural_elements(plan, content)
        assert len(issues) == 1

    def test_display_keyword_triggers_check(self):
        plan = {
            "content_outline": [{
                "section": "Grammar",
                "points": ["Display the conjugation paradigm"],
            }]
        }
        content = "## Grammar\nThe verb conjugates regularly.\n"
        issues = check_structural_elements(plan, content)
        assert len(issues) == 1


# ---------------------------------------------------------------------------
# Check 3: Activity counts
# ---------------------------------------------------------------------------


class TestCheckActivityCounts:
    def test_sufficient_items(self):
        plan = {"activity_hints": [{"type": "quiz", "items": 6}]}
        activities = [{"type": "quiz", "items": [1, 2, 3, 4, 5, 6]}]
        issues = check_activity_counts(plan, activities)
        assert issues == []

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

    def test_no_hints(self):
        plan = {}
        issues = check_activity_counts(plan, [])
        assert issues == []

    def test_pairs_counted(self):
        plan = {"activity_hints": [{"type": "match-up", "items": 6}]}
        activities = [{"type": "match-up", "pairs": [{"left": "a", "right": "b"}] * 6}]
        issues = check_activity_counts(plan, activities)
        assert issues == []


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

    def test_false_friend_properly_implemented(self):
        plan = {
            "activity_hints": [{
                "type": "match-up",
                "focus": "Match letter to sound for false friends",
                "items": 6,
            }]
        }
        activities = [{
            "type": "match-up",
            "pairs": [
                {"left": "Н", "right": "/n/ sound"},
                {"left": "С", "right": "/s/ sound"},
            ],
        }]
        issues = check_activity_focus(plan, activities)
        assert issues == []

    def test_no_focus_no_check(self):
        plan = {"activity_hints": [{"type": "quiz", "items": 6}]}
        activities = [{"type": "quiz", "items": [1, 2, 3, 4, 5, 6]}]
        issues = check_activity_focus(plan, activities)
        assert issues == []


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

    def test_passing_module(self, tmp_path):
        plan = {
            "vocabulary_hints": {"required": ["мама (mom)"]},
            "content_outline": [{
                "section": "Intro",
                "points": ["Explain the concept"],
            }],
            "activity_hints": [{"type": "quiz", "items": 3}],
        }
        plan_path = tmp_path / "plan.yaml"
        plan_path.write_text(yaml.dump(plan, allow_unicode=True), encoding="utf-8")

        md_path = tmp_path / "module.md"
        md_path.write_text("## Intro\nWelcome! мама is a word.\n", encoding="utf-8")

        activities_path = tmp_path / "activities.yaml"
        activities = [{"type": "quiz", "items": [{"q": i} for i in range(3)]}]
        activities_path.write_text(yaml.dump(activities, allow_unicode=True), encoding="utf-8")

        result = check_plan_adherence(md_path, plan_path, activities_path)
        assert result.passed

    def test_missing_plan_file(self, tmp_path):
        md_path = tmp_path / "module.md"
        md_path.write_text("content", encoding="utf-8")
        result = check_plan_adherence(md_path, tmp_path / "nope.yaml", tmp_path / "nope.yaml")
        assert result.checks_run == 0
        assert result.passed


# ---------------------------------------------------------------------------
# Pipeline integration: _run_plan_adherence_check
# ---------------------------------------------------------------------------


class TestRunPlanAdherenceCheck:
    """Test the pipeline wrapper that formats plan adherence issues."""

    def test_returns_empty_when_no_issues(self, tmp_path, monkeypatch):
        from types import SimpleNamespace

        plan = {"vocabulary_hints": {"required": ["мама (mom)"]}}
        plan_path = tmp_path / "plan.yaml"
        plan_path.write_text(yaml.dump(plan, allow_unicode=True), encoding="utf-8")

        md_path = tmp_path / "module.md"
        md_path.write_text("## Intro\nмама is here.\n", encoding="utf-8")

        activities_path = tmp_path / "activities.yaml"
        activities_path.write_text("[]", encoding="utf-8")

        ctx = SimpleNamespace(
            paths={"plan": plan_path, "md": md_path, "activities": activities_path},
            slug="test-module",
        )

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from build.pipeline_v5 import _run_plan_adherence_check

        result = _run_plan_adherence_check(ctx)
        assert result == ""

    def test_returns_formatted_text_for_high_issues(self, tmp_path):
        from types import SimpleNamespace

        plan = {
            "vocabulary_hints": {"required": ["кіт (cat)"]},
            "content_outline": [{
                "section": "Intro",
                "points": ["Show the alphabet chart"],
            }],
        }
        plan_path = tmp_path / "plan.yaml"
        plan_path.write_text(yaml.dump(plan, allow_unicode=True), encoding="utf-8")

        md_path = tmp_path / "module.md"
        md_path.write_text("## Intro\nJust prose, no table.\n", encoding="utf-8")

        activities_path = tmp_path / "activities.yaml"
        activities_path.write_text("[]", encoding="utf-8")

        ctx = SimpleNamespace(
            paths={"plan": plan_path, "md": md_path, "activities": activities_path},
            slug="test-module",
        )

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from build.pipeline_v5 import _run_plan_adherence_check

        result = _run_plan_adherence_check(ctx)
        assert "Plan Adherence Issues" in result
        assert "VOCAB_NOT_IN_CONTENT" in result
        assert "MISSING_STRUCTURAL_ELEMENT" in result
        assert "MUST FIX" in result
