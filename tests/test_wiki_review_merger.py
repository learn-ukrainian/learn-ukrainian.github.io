"""Tests for the deterministic wiki review fix-merger.

Covers the five rules in `scripts/wiki/review_merger.py`:

1. Non-conflict (unique find, single dim)
2. Identical-replace (multiple dims propose same find→replace)
3. Different-replace conflict (priority tiebreaker)
4. Span-overlap conflict (longest find wins)
5. Missing-find (find-string absent from article text)

Critical: the merger is code, not an LLM (ADR-001). Bugs here can
silently corrupt articles — keep the coverage thick.
"""

import os
import sys

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"),
)

import pytest
from wiki.review_merger import (
    DEFAULT_DIM_PRIORITY,
    Fix,
    apply_fixes,
    merge_fixes,
)

# ── Rule 1: non-conflict ───────────────────────────────────────────


class TestNonConflict:
    def test_single_fix_applies(self):
        article = "Переяславська рада 1653 року"
        fixes = [Fix(dim="factual_accuracy", find="1653", replace="1654")]
        report = merge_fixes(fixes, article)
        assert len(report.applied) == 1
        assert report.applied[0].replace == "1654"
        assert report.conflicts == []

    def test_multiple_distinct_fixes_all_apply(self):
        article = "Слово рахувати і на протязі тижня"
        fixes = [
            Fix(dim="register", find="рахувати", replace="вважати"),
            Fix(dim="register", find="на протязі", replace="протягом"),
        ]
        report = merge_fixes(fixes, article)
        assert len(report.applied) == 2
        assert report.conflicts == []

    def test_apply_fixes_produces_expected_text(self):
        article = "Слово рахувати і на протязі тижня"
        fixes = [
            Fix(dim="register", find="рахувати", replace="вважати"),
            Fix(dim="register", find="на протязі", replace="протягом"),
        ]
        report = merge_fixes(fixes, article)
        result = apply_fixes(article, report.applied)
        assert "рахувати" not in result
        assert "на протязі" not in result
        assert "вважати" in result
        assert "протягом" in result


# ── Rule 2: identical-replace ──────────────────────────────────────


class TestIdenticalReplace:
    def test_two_dims_agree_applies_once(self):
        article = "Відмінок в російській мові"
        fixes = [
            Fix(
                dim="ukrainian_perspective",
                find="в російській мові",
                replace="в українській мові",
            ),
            Fix(
                dim="factual_accuracy",
                find="в російській мові",
                replace="в українській мові",
            ),
        ]
        report = merge_fixes(fixes, article)
        assert len(report.applied) == 1
        assert report.conflicts == []

    def test_higher_priority_dim_credited(self):
        """When multiple dims agree, the highest-priority dim is credited."""
        article = "Переяславська рада 1653 року"
        fixes = [
            Fix(dim="register", find="1653", replace="1654"),
            Fix(dim="factual_accuracy", find="1653", replace="1654"),
        ]
        report = merge_fixes(fixes, article)
        assert len(report.applied) == 1
        # factual_accuracy is higher priority than register
        assert report.applied[0].dim == "factual_accuracy"


# ── Rule 3: different-replace conflict ─────────────────────────────


class TestDifferentReplaceConflict:
    def test_priority_tiebreaker_applied(self):
        article = "Шевченко — великий поет"
        fixes = [
            Fix(
                dim="register",
                find="великий поет",
                replace="славетний поет",
            ),
            Fix(
                dim="factual_accuracy",
                find="великий поет",
                replace="національний поет",
            ),
        ]
        report = merge_fixes(fixes, article)
        # Conflict recorded
        assert len(report.conflicts) == 1
        conflict = report.conflicts[0]
        assert conflict.kind == "DIFFERENT_REPLACE"
        # factual_accuracy wins over register per DEFAULT_DIM_PRIORITY
        assert conflict.chosen == "factual_accuracy"
        # Winner was applied
        assert len(report.applied) == 1
        assert report.applied[0].replace == "національний поет"

    def test_override_priority(self):
        article = "Шевченко — великий поет"
        fixes = [
            Fix(dim="register", find="великий поет", replace="A"),
            Fix(dim="factual_accuracy", find="великий поет", replace="B"),
        ]
        # Flipped priority
        report = merge_fixes(
            fixes,
            article,
            dim_priority=("register", "factual_accuracy"),
        )
        assert report.conflicts[0].chosen == "register"
        assert report.applied[0].replace == "A"


# ── Rule 4: span-overlap conflict ──────────────────────────────────


class TestSpanOverlap:
    def test_longer_find_wins(self):
        """One reviewer flags a superset span; the longer find wins."""
        article = "гетьман Тимошенко підписав універсал"
        fixes = [
            # factual says: replace the name
            Fix(
                dim="factual_accuracy",
                find="Тимошенко",
                replace="<!-- VERIFY -->",
            ),
            # another dim says: replace the whole phrase
            Fix(
                dim="ukrainian_perspective",
                find="гетьман Тимошенко підписав універсал",
                replace="український очільник підписав документ",
            ),
        ]
        report = merge_fixes(fixes, article)
        # The longer find should win
        assert len(report.applied) == 1
        assert report.applied[0].find == "гетьман Тимошенко підписав універсал"

    def test_after_apply_only_one_edit(self):
        article = "гетьман Тимошенко підписав універсал"
        fixes = [
            Fix(dim="factual_accuracy", find="Тимошенко", replace="X"),
            Fix(
                dim="ukrainian_perspective",
                find="гетьман Тимошенко підписав універсал",
                replace="REPLACED",
            ),
        ]
        report = merge_fixes(fixes, article)
        result = apply_fixes(article, report.applied)
        assert result == "REPLACED"

    def test_span_overlap_records_conflict_even_when_longest_uncontested(self):
        """Shorter overlapping variants must not silently disappear.

        Even when the longest find has a single proposer (no priority
        tiebreaker needed), the merger must still emit a SPAN_OVERLAP
        conflict so the discarded shorter proposals are traceable.
        """
        article = "гетьман Тимошенко підписав універсал"
        fixes = [
            Fix(dim="factual_accuracy", find="Тимошенко", replace="X"),
            Fix(
                dim="ukrainian_perspective",
                find="гетьман Тимошенко підписав універсал",
                replace="REPLACED",
            ),
        ]
        report = merge_fixes(fixes, article)
        assert len(report.conflicts) == 1
        c = report.conflicts[0]
        assert c.kind == "SPAN_OVERLAP"
        assert c.chosen == "ukrainian_perspective"
        # Both dims must show up in the conflict record
        assert set(c.dims) == {"factual_accuracy", "ukrainian_perspective"}

    def test_span_overlap_with_multi_dim_on_longest(self):
        """Longest has >1 proposer with different replacements — priority
        tiebreaker applies, SPAN_OVERLAP kind preserved."""
        article = "гетьман Тимошенко підписав універсал"
        longest = "гетьман Тимошенко підписав універсал"
        fixes = [
            Fix(dim="register", find="Тимошенко", replace="X"),
            Fix(dim="factual_accuracy", find=longest, replace="A"),
            Fix(dim="register", find=longest, replace="B"),
        ]
        report = merge_fixes(fixes, article)
        conflict_kinds = {c.kind for c in report.conflicts}
        assert "SPAN_OVERLAP" in conflict_kinds
        # factual_accuracy outranks register; winning replacement is A
        assert len(report.applied) == 1
        assert report.applied[0].replace == "A"

    def test_three_way_containment(self):
        """A ⊂ B ⊂ C — union-find captures the full chain; C wins."""
        article = "alpha beta gamma delta epsilon zeta"
        small = "beta"
        medium = "alpha beta gamma"
        large = "alpha beta gamma delta epsilon"
        fixes = [
            Fix(dim="register", find=small, replace="B"),
            Fix(dim="factual_accuracy", find=medium, replace="M"),
            Fix(dim="ukrainian_perspective", find=large, replace="L"),
        ]
        report = merge_fixes(fixes, article)
        assert len(report.applied) == 1
        assert report.applied[0].find == large
        assert report.applied[0].dim == "ukrainian_perspective"


# ── Rule 5: missing-find ───────────────────────────────────────────


class TestMissingFind:
    def test_hallucinated_find_produces_conflict(self):
        article = "Шевченко — великий поет"
        fixes = [
            Fix(
                dim="factual_accuracy",
                find="this text is not in the article",
                replace="X",
            ),
        ]
        report = merge_fixes(fixes, article)
        assert report.applied == []
        assert len(report.conflicts) == 1
        assert report.conflicts[0].kind == "MISSING"

    def test_apply_fixes_skips_missing(self):
        article = "Hello world"
        report_applied = [
            Fix(dim="register", find="Hello", replace="Привіт"),
            Fix(dim="register", find="MISSING", replace="X"),
        ]
        result = apply_fixes(article, report_applied)
        assert result == "Привіт world"  # missing skipped cleanly


# ── Rule 6: ambiguous-find (multiple occurrences) ──────────────────


class TestAmbiguousFind:
    def test_multi_occurrence_find_not_applied(self):
        """str.replace(..., 1) would patch the wrong occurrence — refuse."""
        article = "У 1991 році відбулося X. У 1991 році відбулося Y."
        fixes = [
            Fix(
                dim="factual_accuracy",
                find="У 1991 році",
                replace="У 1990 році",
            ),
        ]
        report = merge_fixes(fixes, article)
        assert report.applied == []
        assert len(report.conflicts) == 1
        assert report.conflicts[0].kind == "AMBIGUOUS"
        assert "2×" in report.conflicts[0].reason
        assert report.has_unresolvable_conflicts is True

    def test_disambiguated_find_applies(self):
        """Widening find-string with surrounding context makes it unique."""
        article = "У 1991 році відбулося X. У 1991 році відбулося Y."
        fixes = [
            Fix(
                dim="factual_accuracy",
                find="У 1991 році відбулося X",
                replace="У 1990 році відбулося X",
            ),
        ]
        report = merge_fixes(fixes, article)
        assert len(report.applied) == 1
        assert report.conflicts == []


# ── Fix-construction guards ────────────────────────────────────────


class TestFixGuards:
    def test_empty_find_rejected(self):
        with pytest.raises(ValueError, match="non-empty"):
            Fix(dim="register", find="", replace="X")

    def test_empty_replace_allowed(self):
        """Deletion is a legitimate fix."""
        f = Fix(dim="register", find="bad word", replace="")
        assert f.replace == ""


# ── Default priority sanity ────────────────────────────────────────


class TestDefaultPriority:
    def test_default_priority_covers_all_four_dims(self):
        assert set(DEFAULT_DIM_PRIORITY) == {
            "factual_accuracy",
            "source_grounding",
            "register",
            "ukrainian_perspective",
        }

    def test_factual_accuracy_is_highest(self):
        """Per design §9 Q3 placeholder: factual errors are highest prio."""
        assert DEFAULT_DIM_PRIORITY[0] == "factual_accuracy"


# ── Unresolvable-conflict flag ─────────────────────────────────────


class TestUnresolvableFlag:
    def test_flag_set_on_missing(self):
        article = "no match here"
        fixes = [Fix(dim="register", find="ABSENT", replace="X")]
        report = merge_fixes(fixes, article)
        assert report.has_unresolvable_conflicts is True

    def test_flag_clear_on_simple_apply(self):
        article = "hello world"
        fixes = [Fix(dim="register", find="hello", replace="hi")]
        report = merge_fixes(fixes, article)
        assert report.has_unresolvable_conflicts is False

    def test_flag_clear_on_resolvable_different_replace(self):
        """DIFFERENT_REPLACE conflict with `chosen` set must NOT trip the
        unresolvable flag — the tiebreaker resolved it."""
        article = "великий поет"
        fixes = [
            Fix(dim="register", find="великий поет", replace="A"),
            Fix(dim="factual_accuracy", find="великий поет", replace="B"),
        ]
        report = merge_fixes(fixes, article)
        assert len(report.conflicts) == 1
        assert report.conflicts[0].chosen == "factual_accuracy"
        assert report.has_unresolvable_conflicts is False
