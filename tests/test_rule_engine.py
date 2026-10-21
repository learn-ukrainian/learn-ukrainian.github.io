"""Tests for the declarative validation rule engine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from audit.checks.rule_engine import (
    run_rule_engine,
)

# ---------------------------------------------------------------------------
# _rule_applies
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Rules 1-2: DEPRECATED — replaced by VESUM morphological validator (#753)
# These rules are marked deprecated=True and skipped by run_rule_engine.
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Rule 6: SELF_CHECK_NEEDS_ENGLISH
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Integration: run_rule_engine
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# _extract_marked_sections
# ---------------------------------------------------------------------------
