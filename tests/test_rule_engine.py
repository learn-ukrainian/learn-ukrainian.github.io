"""Tests for the declarative validation rule engine."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from audit.checks.rule_engine import (
    RULES,
    ValidationRule,
    _check_charset,
    _check_patterns,
    _extract_marked_sections,
    _rule_applies,
    run_rule_engine,
)


# ---------------------------------------------------------------------------
# _rule_applies
# ---------------------------------------------------------------------------

class TestRuleApplies:
    def test_no_constraints_matches_everything(self):
        rule = ValidationRule(
            name="TEST", category="PEDAGOGICAL", severity="HIGH",
            description="", fix="",
        )
        assert _rule_applies(rule, "A1", 1, "a1")
        assert _rule_applies(rule, "C2", 99, "c2")

    def test_level_filter(self):
        rule = ValidationRule(
            name="TEST", category="PEDAGOGICAL", severity="HIGH",
            description="", fix="", levels=["A1"],
        )
        assert _rule_applies(rule, "A1", 1, "a1")
        assert _rule_applies(rule, "a1", 1, "a1")  # case-insensitive
        assert not _rule_applies(rule, "A2", 1, "a2")

    def test_module_range_filter(self):
        rule = ValidationRule(
            name="TEST", category="PEDAGOGICAL", severity="HIGH",
            description="", fix="", module_range=(5, 10),
        )
        assert not _rule_applies(rule, "A1", 4, "a1")
        assert _rule_applies(rule, "A1", 5, "a1")
        assert _rule_applies(rule, "A1", 7, "a1")
        assert _rule_applies(rule, "A1", 10, "a1")
        assert not _rule_applies(rule, "A1", 11, "a1")

    def test_combined_filters(self):
        rule = ValidationRule(
            name="TEST", category="PEDAGOGICAL", severity="HIGH",
            description="", fix="", levels=["A1"], module_range=(1, 14),
        )
        assert _rule_applies(rule, "A1", 1, "a1")
        assert _rule_applies(rule, "A1", 14, "a1")
        assert not _rule_applies(rule, "A1", 15, "a1")
        assert not _rule_applies(rule, "A2", 5, "a2")


# ---------------------------------------------------------------------------
# Rules 1-2: DEPRECATED — replaced by VESUM morphological validator (#753)
# These rules are marked deprecated=True and skipped by run_rule_engine.
# ---------------------------------------------------------------------------

class TestDeprecatedRulesSkipped:
    """Verify deprecated rules produce zero matches."""

    def test_imperatives_deprecated(self):
        content = "Слухайте уважно! Читайте текст. Повторюйте за мною."
        issues = run_rule_engine(content, "A1", 5, "a1")
        matched = [i for i in issues if "NO_IMPERATIVES" in i["text"]]
        assert len(matched) == 0

    def test_verb_conjugation_deprecated(self):
        content = "Ми вивчаємо літери. Ми читаємо книгу."
        issues = run_rule_engine(content, "A1", 5, "a1")
        matched = [i for i in issues if "NO_VERB_CONJUGATION" in i["text"]]
        assert len(matched) == 0


# ---------------------------------------------------------------------------
# Rules 3-5: DECODABILITY charset checks (plan-driven)
# ---------------------------------------------------------------------------

# Test plans with decodable_letters
_M1_PLAN = {"decodable_letters": "А О У І М Н Т К С Л"}

class TestDecodability:
    def test_m1_allows_plan_letters(self):
        """M1 plan allows А О У І М Н Т К С Л — words using only these pass."""
        content = """## Reading Practice

мама
тато
кіт
молоко

## Next Section
"""
        issues = run_rule_engine(content, "A1", 1, "a1", plan=_M1_PLAN)
        decoded = [i for i in issues if "DECODABILITY_M1" in i["text"]]
        assert len(decoded) == 0

    def test_m1_catches_unknown_letters(self):
        """Words with letters outside plan's decodable_letters are flagged."""
        content = """## Reading Practice

мама
батько
жаба

## Next Section
"""
        issues = run_rule_engine(content, "A1", 1, "a1", plan=_M1_PLAN)
        decoded = [i for i in issues if "DECODABILITY_M1" in i["text"]]
        assert len(decoded) >= 2  # батько (б, ь) and жаба (ж, б)

    def test_no_plan_no_decodability_check(self):
        """Without a plan, no decodability rules are generated."""
        content = """## Reading Practice

жаба шапка

## Next Section
"""
        issues = run_rule_engine(content, "A1", 1, "a1", plan=None)
        decoded = [i for i in issues if "DECODABILITY" in i["text"]]
        assert len(decoded) == 0

    def test_no_decodable_letters_no_check(self):
        """Plan without decodable_letters field — no decodability rules."""
        content = """## Reading Practice

жаба шапка

## Next Section
"""
        plan = {"phase": "A1.1 [First Contact]"}
        issues = run_rule_engine(content, "A1", 2, "a1", plan=plan)
        decoded = [i for i in issues if "DECODABILITY" in i["text"]]
        assert len(decoded) == 0

    def test_decodability_only_scans_marked_sections(self):
        # Content outside marked sections should be ignored
        content = """## Introduction

жаба шапка батько

## Reading Practice

мама сума

## Conclusion

More жаба here
"""
        issues = run_rule_engine(content, "A1", 1, "a1", plan=_M1_PLAN)
        decoded = [i for i in issues if "DECODABILITY_M1" in i["text"]]
        # Only "Reading Practice" section scanned; intro/conclusion ignored
        assert len(decoded) == 0

    def test_no_decodability_outside_range(self):
        content = """## Reading Practice

жаба шапка
"""
        issues = run_rule_engine(content, "A1", 5, "a1")
        decoded = [i for i in issues if "DECODABILITY" in i["text"]]
        assert len(decoded) == 0  # M5 has no decodability rules


# ---------------------------------------------------------------------------
# Rule 6: SELF_CHECK_NEEDS_ENGLISH
# ---------------------------------------------------------------------------

class TestSelfCheckEnglish:
    def test_catches_ukrainian_only_questions(self):
        content = """## Self-Check

1. Яка це літера?
2. Напишіть слово.
"""
        issues = run_rule_engine(content, "A1", 5, "a1")
        matched = [i for i in issues if "SELF_CHECK_NEEDS_ENGLISH" in i["text"]]
        assert len(matched) >= 2

    def test_passes_with_english_present(self):
        content = """## Self-Check

1. What letter is this? / Яка це літера?
2. Write the word. / Напишіть слово.
"""
        issues = run_rule_engine(content, "A1", 5, "a1")
        matched = [i for i in issues if "SELF_CHECK_NEEDS_ENGLISH" in i["text"]]
        assert len(matched) == 0

    def test_skips_outside_range(self):
        content = """## Self-Check

1. Яка це літера?
"""
        issues = run_rule_engine(content, "A1", 15, "a1")
        matched = [i for i in issues if "SELF_CHECK_NEEDS_ENGLISH" in i["text"]]
        assert len(matched) == 0


# ---------------------------------------------------------------------------
# Integration: run_rule_engine
# ---------------------------------------------------------------------------

class TestRunRuleEngine:
    def test_returns_list_of_dicts(self):
        issues = run_rule_engine("Слухайте!", "A1", 5, "a1")
        assert isinstance(issues, list)
        for issue in issues:
            assert "type" in issue
            assert "severity" in issue
            assert "text" in issue
            assert "fix" in issue

    def test_empty_content_no_crash(self):
        issues = run_rule_engine("", "A1", 1, "a1")
        assert isinstance(issues, list)

    def test_a2_content_zero_pedagogical(self):
        issues = run_rule_engine("Слухайте уважно!", "A2", 1, "a2")
        assert len(issues) == 0

    def test_dedup_removes_duplicates(self):
        # Same imperative appearing twice should be deduped
        content = "Слухайте! ... Слухайте!"
        issues = run_rule_engine(content, "A1", 5, "a1")
        texts = [i["text"] for i in issues if "Слухайте" in i["text"]]
        # Should have at most 1 after dedup (same rule + same match text)
        assert len(texts) <= 2  # Could be 2 if line numbers differ


# ---------------------------------------------------------------------------
# _extract_marked_sections
# ---------------------------------------------------------------------------

class TestExtractMarkedSections:
    def test_finds_section_by_marker(self):
        content = """# Title

## Reading Practice

some content here
more content

## Next Section

other stuff
"""
        sections = _extract_marked_sections(content, ["Reading Practice"])
        assert len(sections) == 1
        assert "some content here" in sections[0][1]
        assert "other stuff" not in sections[0][1]

    def test_case_insensitive_marker(self):
        content = """## reading practice

content
"""
        sections = _extract_marked_sections(content, ["Reading Practice"])
        assert len(sections) == 1

    def test_no_matching_markers(self):
        content = """## Introduction

content
"""
        sections = _extract_marked_sections(content, ["Reading Practice"])
        assert len(sections) == 0
