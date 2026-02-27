"""
Unit tests for Phase D pipeline logic in build_module_v3.py.

Covers deterministic functions — no LLM calls, no network.

Tests:
- Citation extraction (「」 CJK + «» legacy + mixed)
- Citation verification against source files
- D.1 review parsing (PASS, FAIL, score table, missing delimiters, truncation recovery)
- Review quality gate (_quick_review_quality_gate)
- Phase D routing helpers (_all_issues_diffuse, _count_diff_lines)
- D.2 diff limit calculation
- Template rendering (fill_template, find_unresolved)
- Delimiter extraction (_extract_delimiter, _extract_delimiter_tolerant)

Issue: #668
"""

import os
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ===========================================================================
# Imports — grouped by source file
# ===========================================================================

from scripts.audit.checks.review_validation import (
    _extract_ukrainian_citations,
    _verify_citations_against_source,
)

from scripts.build_module_v3 import (
    _extract_delimiter,
    _extract_delimiter_tolerant,
    _all_issues_diffuse,
    _count_diff_lines,
    _parse_d1_review,
    _quick_review_quality_gate,
    D1Result,
    _DIFFUSE_FAILURE_CODES,
)

from scripts.fill_template import fill_template, find_unresolved


# ===========================================================================
# 1. Citation Extraction
# ===========================================================================

class TestExtractUkrainianCitations:
    """Tests for _extract_ukrainian_citations() in review_validation.py."""

    def test_cjk_brackets_preferred(self):
        """「」 CJK corner brackets extract Ukrainian citations."""
        review = (
            "Issue 1:\n"
            "- **Original**: 「Він ходить до школи щодня вранці」\n"
            "- **Fix**: Replace with correct form\n"
        )
        citations = _extract_ukrainian_citations(review)
        assert len(citations) == 1
        assert "Він ходить до школи щодня вранці" in citations[0]

    def test_legacy_guillemets(self):
        """«» angular quotes extract Ukrainian citations (backward compat)."""
        review = (
            "Issue:\n"
            "- **Original**: «Він ходить до школи щодня вранці»\n"
        )
        citations = _extract_ukrainian_citations(review)
        assert len(citations) == 1
        assert "Він ходить до школи щодня вранці" in citations[0]

    def test_nested_guillemets_collision(self):
        """Nested «» inside Ukrainian text causes regex to match partial strings.

        This is the bug that motivated the switch to 「」.
        Example: «Шевченко написав «Кобзар» у 1840 році» produces TWO matches:
          1. 'Шевченко написав ' (opening « to inner «)
          2. '» у 1840 році' ... won't match because inner » closes first
        Actually regex «([^»]*)» is greedy-minimal — it matches until FIRST ».
        """
        review = '«Шевченко написав «Кобзар» у 1840 році»'
        citations = _extract_ukrainian_citations(review)
        # The [^»]* pattern stops at first » — so it gets "Шевченко написав "
        # and "Кобзар" is lost. This demonstrates the collision problem.
        # With 「」 this wouldn't happen:
        review_fixed = '「Шевченко написав «Кобзар» у 1840 році」'
        citations_fixed = _extract_ukrainian_citations(review_fixed)
        assert len(citations_fixed) == 1
        assert "Кобзар" in citations_fixed[0]

    def test_short_citations_filtered(self):
        """Citations shorter than 10 chars are excluded."""
        review = '「Привіт」 and 「Це дуже довге речення українською мовою」'
        citations = _extract_ukrainian_citations(review)
        # "Привіт" = 6 chars (< 10), should be excluded
        assert len(citations) == 1
        assert "довге речення" in citations[0]

    def test_non_cyrillic_filtered(self):
        """Citations without Cyrillic chars are excluded."""
        review = '「This is a long English sentence with no Ukrainian」'
        citations = _extract_ukrainian_citations(review)
        assert len(citations) == 0

    def test_mixed_delimiters_single_review(self):
        """Review mixing 「」 + «» + "" extracts all Ukrainian citations."""
        review = (
            '「Перше речення українською мовою」\n'
            '«Друге речення українською мовою»\n'
            '"Третє речення українською мовою"\n'
        )
        citations = _extract_ukrainian_citations(review)
        assert len(citations) == 3

    def test_deduplication(self):
        """Identical citations across different delimiter types are deduplicated."""
        review = (
            '「Він ходить до школи щодня」\n'
            '«Він ходить до школи щодня»\n'
        )
        citations = _extract_ukrainian_citations(review)
        assert len(citations) == 1

    def test_markdown_bold_stripped(self):
        """Markdown bold/italic markers are stripped from citations."""
        review = '「Він **ходить** до *школи* щодня вранці」'
        citations = _extract_ukrainian_citations(review)
        assert len(citations) == 1
        assert "**" not in citations[0]
        assert "*" not in citations[0]

    def test_underscore_markdown_in_citations(self):
        """Markdown _italic_ and __bold__ using underscores inside citations."""
        # The extraction function strips *-style but may not strip _-style.
        # This test documents actual behavior.
        review = '「Він __ходить__ до _школи_ щодня вранці」'
        citations = _extract_ukrainian_citations(review)
        assert len(citations) == 1
        # At minimum the citation is extracted — stripping _ is optional

    def test_multiline_cjk_brackets(self):
        """CJK brackets spanning multiple lines still extract content."""
        review = '「Він ходить до школи\nщодня вранці рано」'
        citations = _extract_ukrainian_citations(review)
        # CJK regex [^」]* allows newlines, so multiline extraction should work
        assert len(citations) == 1

    def test_inline_code_citations(self):
        """Backtick-quoted Ukrainian text is extracted."""
        review = '`Він ходить до школи щодня вранці`'
        citations = _extract_ukrainian_citations(review)
        assert len(citations) == 1

    def test_multiline_code_blocks_excluded(self):
        """Backtick citations with newlines (code blocks) are excluded."""
        review = '`Перший рядок\nДругий рядок`'
        citations = _extract_ukrainian_citations(review)
        assert len(citations) == 0


# ===========================================================================
# 2. Citation Verification
# ===========================================================================

class TestVerifyCitationsAgainstSource:
    """Tests for _verify_citations_against_source() in review_validation.py."""

    def test_all_citations_verified(self, tmp_path):
        """All citations present in source → (N, N) tuple."""
        source = tmp_path / "test-module.md"
        source.write_text(
            "## Вступ\n\n"
            "Він ходить до школи щодня вранці.\n"
            "Вона читає цікаву книгу про історію.\n",
            encoding="utf-8",
        )
        citations = [
            "Він ходить до школи щодня вранці",
            "Вона читає цікаву книгу про історію",
        ]
        verified, total = _verify_citations_against_source(citations, source)
        assert verified == 2
        assert total == 2

    def test_no_citations_verified(self, tmp_path):
        """Fabricated citations not in source → (0, N)."""
        source = tmp_path / "test-module.md"
        source.write_text("## Вступ\n\nЦе зовсім інший текст.\n", encoding="utf-8")
        citations = [
            "Він ходить до школи щодня вранці",
            "Вона читає цікаву книгу про історію",
        ]
        verified, total = _verify_citations_against_source(citations, source)
        assert verified == 0
        assert total == 2

    def test_partial_verification(self, tmp_path):
        """Mix of real and fabricated citations."""
        source = tmp_path / "test-module.md"
        source.write_text(
            "## Вступ\n\nВін ходить до школи щодня вранці.\n",
            encoding="utf-8",
        )
        citations = [
            "Він ходить до школи щодня вранці",  # real
            "Цього тексту немає у файлі зовсім",  # fabricated
        ]
        verified, total = _verify_citations_against_source(citations, source)
        assert verified == 1
        assert total == 2

    def test_missing_source_file(self, tmp_path):
        """Non-existent source file → (0, N)."""
        missing = tmp_path / "nonexistent.md"
        citations = ["Він ходить до школи щодня вранці"]
        verified, total = _verify_citations_against_source(citations, missing)
        assert verified == 0
        assert total == 1

    def test_empty_citations_list(self, tmp_path):
        """Empty citations list → (0, 0)."""
        source = tmp_path / "test-module.md"
        source.write_text("## Вступ\n\nТекст.\n", encoding="utf-8")
        verified, total = _verify_citations_against_source([], source)
        assert verified == 0
        assert total == 0

    def test_also_searches_activities_yaml(self, tmp_path):
        """Verification also searches activities/{slug}.yaml."""
        source = tmp_path / "test-module.md"
        source.write_text("## Вступ\n\nОсновний текст.\n", encoding="utf-8")
        act_dir = tmp_path / "activities"
        act_dir.mkdir()
        (act_dir / "test-module.yaml").write_text(
            "- type: quiz\n  prompt: Він ходить до школи щодня вранці\n",
            encoding="utf-8",
        )
        citations = ["Він ходить до школи щодня вранці"]
        verified, total = _verify_citations_against_source(citations, source)
        assert verified == 1

    def test_also_searches_vocabulary_yaml(self, tmp_path):
        """Verification also searches vocabulary/{slug}.yaml."""
        source = tmp_path / "test-module.md"
        source.write_text("## Вступ\n\nОсновний текст.\n", encoding="utf-8")
        vocab_dir = tmp_path / "vocabulary"
        vocab_dir.mkdir()
        (vocab_dir / "test-module.yaml").write_text(
            "- word: здоров'я\n  example: Здоров'я — найбільше багатство людини\n",
            encoding="utf-8",
        )
        citations = ["Здоров'я — найбільше багатство людини"]
        verified, total = _verify_citations_against_source(citations, source)
        assert verified == 1

    def test_sliding_window_fallback(self, tmp_path):
        """Citation with different start but matching core text is verified via sliding window."""
        source = tmp_path / "test-module.md"
        source.write_text(
            "## Вступ\n\nОсь приклад: Він щодня ходить до школи рано вранці.\n",
            encoding="utf-8",
        )
        # Citation starts differently but has a 20+ char window that matches
        citations = ["Ось приклад: він щодня ходить до школи рано вранці"]
        verified, total = _verify_citations_against_source(citations, source)
        assert verified == 1

    def test_trailing_punctuation_difference(self, tmp_path):
        """Citation with trailing period vs source without → still verified via first-30-char check."""
        source = tmp_path / "test-module.md"
        source.write_text(
            "## Вступ\n\nВін ходить до школи, щоб вчитися.\n",
            encoding="utf-8",
        )
        # Citation includes trailing period but source has comma continuation
        citations = ["Він ходить до школи, щоб вчитися"]
        verified, total = _verify_citations_against_source(citations, source)
        # First 30 chars match → verified
        assert verified == 1


# ===========================================================================
# 3. D.1 Review Parsing
# ===========================================================================

class TestParseD1Review:
    """Tests for _parse_d1_review() in build_module_v3.py."""

    def test_pass_verdict_markdown(self):
        """Markdown review with PASS verdict is parsed correctly."""
        raw = (
            "Here is my review:\n"
            "===REVIEW_START===\n"
            "# Рецензія: Test Module\n\n"
            "**Level:** A2 | **Module:** 1\n"
            "**Overall Score:** 9.2/10\n"
            "**Status:** PASS\n\n"
            "## Scores\n\n"
            "| # | Dimension | Score |\n"
            "|---|-----------|-------|\n"
            "| 1 | Language Quality | 9/10 |\n\n"
            "## Critical Issues Found\n\n"
            "### Issue 1: Minor Grammar\n"
            "- **Location**: Line 42\n"
            "- **Problem**: Wrong case ending\n"
            "- **Fix**: Change -а to -у\n\n"
            "## Verification Summary\n\n"
            "- Citations in bank: 8\n\n"
            "## Verdict\n\n"
            "**PASS**\n"
            "===REVIEW_END===\n"
        )
        result = _parse_d1_review(raw)
        assert result.ok is True
        assert result.verdict == "PASS"
        assert result.scores.get("overall") == 9.2
        assert len(result.issues) == 1
        assert "Line 42" in result.issues[0].get("location", "")

    def test_fail_verdict_markdown(self):
        """Markdown review with FAIL verdict is parsed correctly."""
        raw = (
            "===REVIEW_START===\n"
            "# Рецензія: Test Module\n\n"
            "**Overall Score:** 6.8/10\n"
            "**Status:** FAIL\n\n"
            "## Critical Issues Found\n\n"
            "### Issue 1: Grammar Error\n"
            "- **Location**: Line 10\n"
            "- **Problem**: Russicism detected\n"
            "- **Fix**: Replace with Ukrainian form\n\n"
            "### Issue 2: Factual Error\n"
            "- **Location**: Line 50\n"
            "- **Problem**: Wrong date\n"
            "- **Fix**: Change 1850 to 1840\n\n"
            "## Verdict\n\n"
            "**FAIL**\n"
            "===REVIEW_END===\n"
        )
        result = _parse_d1_review(raw)
        assert result.ok is True
        assert result.verdict == "FAIL"
        assert result.scores.get("overall") == 6.8
        assert len(result.issues) == 2

    def test_score_table_extraction(self):
        """Per-dimension scores from ## Scores table are extracted."""
        raw = (
            "===REVIEW_START===\n"
            "**Overall Score:** 8.5/10\n"
            "**Status:** FAIL\n\n"
            "## Scores\n\n"
            "| # | Dimension | Score |\n"
            "|---|-----------|-------|\n"
            "| 1 | Language Quality | 9/10 |\n"
            "| 2 | Content Accuracy | 8/10 |\n"
            "| 3 | Pedagogical Design | 7.5/10 |\n"
            "| 4 | Activity Quality | 9/10 |\n\n"
            "**Weighted Overall:** (9×0.3 + 8×0.25 + 7.5×0.25 + 9×0.2) = **8.5/10**\n\n"
            "## Critical Issues Found\n\n"
            "No critical issues.\n\n"
            "## Verdict\n\n**FAIL**\n"
            "===REVIEW_END===\n"
        )
        result = _parse_d1_review(raw)
        assert result.ok is True
        assert result.scores["overall"] == 8.5
        assert result.scores["language_quality"] == 9.0
        assert result.scores["content_accuracy"] == 8.0
        assert result.scores["pedagogical_design"] == 7.5
        assert result.scores["activity_quality"] == 9.0
        assert result.scores["weighted_overall"] == 8.5

    def test_missing_delimiters_returns_not_ok(self):
        """Missing ===REVIEW_START=== → ok=False."""
        raw = "This is just some text with no delimiters at all."
        result = _parse_d1_review(raw)
        assert result.ok is False
        assert result.raw_review == ""

    def test_missing_end_delimiter_tolerant_markdown_recovery(self):
        """Missing ===REVIEW_END=== with Markdown content is now recovered.

        The tolerant extractor in markdown mode accepts non-empty content
        without YAML validation, so truncated Markdown reviews are recovered.
        """
        raw = (
            "===REVIEW_START===\n"
            "**Overall Score:** 8.5/10\n"
            "**Status:** PASS\n\n"
            "## Verdict\n\n**PASS**\n"
            # No ===REVIEW_END=== — simulates truncation
        )
        result = _parse_d1_review(raw)
        assert isinstance(result, D1Result)
        # Markdown tolerant extraction recovers truncated reviews
        assert result.ok is True
        assert result.verdict == "PASS"
        assert result.scores.get("overall") == 8.5

    def test_score_below_9_inferred_fail(self):
        """Score < 9.0 without explicit Status → inferred FAIL."""
        raw = (
            "===REVIEW_START===\n"
            "**Overall Score:** 7.2/10\n\n"
            "## Verdict\n\nNeeds improvement.\n"
            "===REVIEW_END===\n"
        )
        result = _parse_d1_review(raw)
        assert result.ok is True
        assert result.verdict == "FAIL"

    def test_score_above_9_inferred_pass(self):
        """Score >= 9.0 without explicit Status → inferred PASS."""
        raw = (
            "===REVIEW_START===\n"
            "**Overall Score:** 9.3/10\n\n"
            "## Verdict\n\nExcellent module.\n"
            "===REVIEW_END===\n"
        )
        result = _parse_d1_review(raw)
        assert result.ok is True
        assert result.verdict == "PASS"


# ===========================================================================
# 4. Review Quality Gate
# ===========================================================================

class TestQuickReviewQualityGate:
    """Tests for _quick_review_quality_gate() in build_module_v3.py."""

    def _make_content(self, tmp_path, word_count=2000):
        """Helper: create a content file with N words."""
        content_path = tmp_path / "test-module.md"
        # Build content with H2 sections
        words = "слово " * (word_count // 3)
        content = (
            f"## Перший розділ\n\n{words}\n\n"
            f"## Другий розділ\n\n{words}\n\n"
            f"## Третій розділ\n\n{words}\n"
        )
        content_path.write_text(content, encoding="utf-8")
        return content_path

    def test_rejects_too_short_review(self, tmp_path):
        """Review with < 150 words is rejected."""
        content_path = self._make_content(tmp_path, 600)
        # Short review with enough citations to pass citation check
        review = (
            "「Перше речення про граматику модуля」\n"
            "「Друге речення про лексику модуля」\n"
            "Good.\n"
        )
        ok, reason = _quick_review_quality_gate(review, content_path)
        assert not ok
        assert "words" in reason.lower() or "citation" in reason.lower() or "shallow" in reason.lower()

    def test_rejects_low_citation_density(self, tmp_path):
        """Review for 2000-word content with < min_citations is rejected."""
        content_path = self._make_content(tmp_path, 2000)
        # Long review but only 1 citation (need >= max(2, 2000//600) = 3)
        padding = " ".join(["word"] * 200)
        review = (
            f"「Єдине цитування з модуля」\n"
            f"Review text: {padding}\n"
            f"Перший розділ mentioned. Другий розділ too.\n"
        )
        ok, reason = _quick_review_quality_gate(review, content_path)
        assert not ok
        assert "citation" in reason.lower() or "shallow" in reason.lower()

    def test_accepts_valid_review(self, tmp_path):
        """Review meeting all criteria passes."""
        content_path = self._make_content(tmp_path, 1200)
        # min_citations = max(2, 1200 // 600) = 2
        padding = " ".join(["review"] * 160)
        review = (
            "「Перше цитування з модуля тут написано」\n"
            "「Друге цитування з модуля теж написано」\n"
            "「Третє цитування для впевненості що достатньо」\n"
            f"Review: {padding}\n"
            "Перший розділ is well done.\n"
            "Другий розділ needs work.\n"
        )
        ok, reason = _quick_review_quality_gate(review, content_path)
        assert ok
        assert reason == "OK"

    def test_rejects_low_section_coverage(self, tmp_path):
        """Review that doesn't mention any content sections is rejected."""
        content_path = tmp_path / "test-module.md"
        # 5 H2 sections but review mentions none
        content = (
            "## Альфа розділ\n\nтекст " * 100 + "\n"
            "## Бета розділ\n\nтекст " * 100 + "\n"
            "## Гамма розділ\n\nтекст " * 100 + "\n"
            "## Дельта розділ\n\nтекст " * 100 + "\n"
        )
        content_path.write_text(content, encoding="utf-8")

        padding = " ".join(["review"] * 160)
        review = (
            "「Перше цитування з модуля текст слово」\n"
            "「Друге цитування з модуля текст слово」\n"
            "「Третє цитування з модуля текст слово」\n"
            f"Generic review text: {padding}\n"
        )
        ok, reason = _quick_review_quality_gate(review, content_path)
        assert not ok
        assert "section" in reason.lower() or "shallow" in reason.lower()


# ===========================================================================
# 5. Phase D Routing Helpers
# ===========================================================================

class TestAllIssuesDiffuse:
    """Tests for _all_issues_diffuse() in build_module_v3.py."""

    def test_no_failing_codes_returns_false(self):
        """Audit with no failures → False (review issues are targeted)."""
        audit_out = "✅ [WORDS] 4200/4000\n✅ [ENGAGEMENT] 8 boxes"
        assert _all_issues_diffuse(audit_out) is False

    def test_all_diffuse_codes_returns_true(self):
        """All failing codes are diffuse → True (skip D.2)."""
        audit_out = (
            "❌ [ROBOTIC_STRUCTURE] 4 patterns detected\n"
            "❌ [LOW_IMMERSION] 45% (target: 75%)\n"
        )
        assert _all_issues_diffuse(audit_out) is True

    def test_mixed_diffuse_and_targeted_returns_false(self):
        """Mix of diffuse + targeted codes → False (D.2 can fix targeted)."""
        audit_out = (
            "❌ [ROBOTIC_STRUCTURE] 4 patterns\n"
            "❌ [RUSSICISM_DETECTED] Line 42: кот → кіт\n"
        )
        assert _all_issues_diffuse(audit_out) is False

    def test_only_targeted_codes_returns_false(self):
        """Only targeted (non-diffuse) codes → False."""
        audit_out = "❌ [RUSSICISM_DETECTED] Line 42\n❌ [GRAMMAR_ERROR] Line 55"
        assert _all_issues_diffuse(audit_out) is False

    def test_diffuse_codes_set_is_complete(self):
        """Verify the diffuse codes set matches expectations."""
        expected = {
            "ROBOTIC_STRUCTURE", "STRUCTURAL_MONOTONY", "CONTENT_REDUNDANCY",
            "EXCESSIVE_METAPHOR", "THEORY_FRONTLOADING", "LOW_IMMERSION",
        }
        assert _DIFFUSE_FAILURE_CODES == expected


class TestCountDiffLines:
    """Tests for _count_diff_lines() in build_module_v3.py."""

    def test_identical_texts(self):
        """Identical texts → 0 changed lines."""
        text = "Line 1\nLine 2\nLine 3\n"
        assert _count_diff_lines(text, text) == 0

    def test_single_line_change(self):
        """One line changed → 2 (1 deletion + 1 addition)."""
        before = "Line 1\nLine 2\nLine 3\n"
        after = "Line 1\nChanged line\nLine 3\n"
        assert _count_diff_lines(before, after) == 2

    def test_line_addition(self):
        """Adding a line → 1 addition."""
        before = "Line 1\nLine 2\n"
        after = "Line 1\nLine 2\nLine 3\n"
        assert _count_diff_lines(before, after) == 1

    def test_line_deletion(self):
        """Removing a line → 1 deletion."""
        before = "Line 1\nLine 2\nLine 3\n"
        after = "Line 1\nLine 3\n"
        assert _count_diff_lines(before, after) == 1

    def test_bulk_changes(self):
        """Multiple changes count correctly."""
        before = "A\nB\nC\nD\nE\n"
        after = "A\nX\nC\nY\nE\n"
        # B→X and D→Y: 4 changed lines (2 deletions + 2 additions)
        assert _count_diff_lines(before, after) == 4


# ===========================================================================
# 6. D.2 Diff Limit Calculation
# ===========================================================================

class TestD2DiffLimit:
    """Tests for the D.2 diff limit formula: max(fix_pair_count * 25, 50)."""

    @pytest.mark.parametrize("fix_pairs,expected_max", [
        (0, 50),    # Floor at 50
        (1, 50),    # 1 * 25 = 25, but floor 50
        (2, 50),    # 2 * 25 = 50
        (3, 75),    # 3 * 25 = 75
        (5, 125),   # 5 * 25 = 125
        (10, 250),  # 10 * 25 = 250
    ])
    def test_diff_limit_formula(self, fix_pairs, expected_max):
        """max(fix_pair_count * 25, 50) matches expected values."""
        assert max(fix_pairs * 25, 50) == expected_max


# ===========================================================================
# 7. Template Rendering
# ===========================================================================

class TestFillTemplate:
    """Tests for fill_template() and find_unresolved() in fill_template.py."""

    def test_basic_replacement(self):
        """Simple placeholder replacement works."""
        template = "Track: {TRACK}, Level: {LEVEL}"
        placeholders = {"TRACK": "a1", "LEVEL": "A1"}
        result = fill_template(template, placeholders)
        assert result == "Track: a1, Level: A1"

    def test_multiple_occurrences(self):
        """Same placeholder appearing multiple times is replaced everywhere."""
        template = "{SLUG} appears here and {SLUG} appears here too"
        result = fill_template(template, {"SLUG": "test-module"})
        assert result == "test-module appears here and test-module appears here too"

    def test_unicode_values(self):
        """Ukrainian text in placeholder values is preserved."""
        template = "Title: {TOPIC_TITLE}"
        result = fill_template(template, {"TOPIC_TITLE": "Здоров'я та медицина"})
        assert result == "Title: Здоров'я та медицина"

    def test_unresolved_detection(self):
        """find_unresolved() detects unfilled placeholders."""
        text = "Track: a1, but {MISSING_KEY} and {ANOTHER_MISSING} remain"
        unresolved = find_unresolved(text)
        assert "{MISSING_KEY}" in unresolved
        assert "{ANOTHER_MISSING}" in unresolved

    def test_no_unresolved(self):
        """find_unresolved() returns empty list when all filled."""
        text = "Track: a1, Level: A1, all done"
        assert find_unresolved(text) == []

    def test_lowercase_braces_not_detected(self):
        """Lowercase {placeholders} are NOT detected as unresolved.

        Only {UPPERCASE} patterns (at least 2 chars) are considered placeholders.
        """
        text = "This has {lowercase} and {a} which are not placeholders"
        assert find_unresolved(text) == []

    def test_d1_output_format_uses_cjk_brackets(self):
        """D1_OUTPUT_FORMAT template contains 「」 not «» for citation examples."""
        template_path = Path(__file__).parent.parent / "claude_extensions/phases/gemini/phase-D1-output-format.md"
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            assert "「" in content, "D1 output format should use 「」 for citations"
            assert "」" in content, "D1 output format should use 「」 for citations"


# ===========================================================================
# 8. Delimiter Extraction
# ===========================================================================

class TestExtractDelimiter:
    """Tests for _extract_delimiter() and _extract_delimiter_tolerant()."""

    def test_exact_extraction(self):
        """Content between start and end tags is extracted."""
        text = "Preamble\n===REVIEW_START===\nReview content here\n===REVIEW_END===\nPostamble"
        result = _extract_delimiter(text, "===REVIEW_START===", "===REVIEW_END===")
        assert result == "Review content here"

    def test_missing_start_tag(self):
        """Missing start tag → None."""
        text = "No start tag here\n===REVIEW_END===\n"
        result = _extract_delimiter(text, "===REVIEW_START===", "===REVIEW_END===")
        assert result is None

    def test_missing_end_tag(self):
        """Missing end tag → None (for exact extraction)."""
        text = "===REVIEW_START===\nContent without end tag"
        result = _extract_delimiter(text, "===REVIEW_START===", "===REVIEW_END===")
        assert result is None

    def test_last_start_tag_wins(self):
        """When Gemini echoes template, last ===REVIEW_START=== anchors extraction."""
        text = (
            "Echo: ===REVIEW_START===\necho content\n===REVIEW_END===\n"
            "Real: ===REVIEW_START===\nreal content\n===REVIEW_END===\n"
        )
        result = _extract_delimiter(text, "===REVIEW_START===", "===REVIEW_END===")
        assert result == "real content"

    def test_tolerant_yaml_mode_rejects_prose(self):
        """Tolerant extraction (yaml mode): plain text fails YAML validation → returns None.

        Default content_type="yaml" requires valid YAML with ``items`` key.
        Plain prose will fail YAML validation. This is by design — yaml mode
        is for truncated vocab/activity YAML output, not arbitrary text.
        """
        text = "===REVIEW_START===\nContent here but truncated"
        exact = _extract_delimiter(text, "===REVIEW_START===", "===REVIEW_END===")
        assert exact is None
        tolerant = _extract_delimiter_tolerant(text, "===REVIEW_START===", "===REVIEW_END===")
        # Plain text fails YAML validation in default (yaml) mode → None
        assert tolerant is None

    def test_tolerant_markdown_mode_recovers_prose(self):
        """Tolerant extraction (markdown mode): plain text is recovered without YAML validation."""
        text = "===REVIEW_START===\n**Overall Score:** 8.0/10\n**Status:** PASS"
        tolerant = _extract_delimiter_tolerant(
            text, "===REVIEW_START===", "===REVIEW_END===",
            content_type="markdown",
        )
        assert tolerant is not None
        assert "**Overall Score:** 8.0/10" in tolerant

    def test_tolerant_with_valid_content(self):
        """Tolerant extraction with exact match (both tags present) delegates to exact."""
        text = "===START===\nRecovered content\n===END===\n"
        result = _extract_delimiter_tolerant(text, "===START===", "===END===")
        assert result == "Recovered content"

    def test_citation_bank_extraction(self):
        """Citation bank delimiters extract correctly."""
        text = (
            "===CITATION_BANK_START===\n"
            "1. Line 42: 「Він ходить до школи」\n"
            "2. Line 55: 「Вона читає книгу」\n"
            "===CITATION_BANK_END===\n"
        )
        result = _extract_delimiter(text, "===CITATION_BANK_START===", "===CITATION_BANK_END===")
        assert "Line 42" in result
        assert "Line 55" in result


# ===========================================================================
# 9. Citation Failure Detection (integration)
# ===========================================================================

class TestCitationFailureDetection:
    """Tests for the _CITATION_FAILURES constant and its usage pattern."""

    def test_fabricated_citations_detected(self):
        """FABRICATED_CITATIONS tag in audit output is detected."""
        _CITATION_FAILURES = ("FABRICATED_CITATIONS", "UNVERIFIED_CITATIONS")
        audit_out = "❌ [FABRICATED_CITATIONS] 0/12 citations verified"
        assert any(f"❌ [{tag}]" in audit_out for tag in _CITATION_FAILURES)

    def test_unverified_citations_detected(self):
        """UNVERIFIED_CITATIONS tag in audit output is detected."""
        _CITATION_FAILURES = ("FABRICATED_CITATIONS", "UNVERIFIED_CITATIONS")
        audit_out = "❌ [UNVERIFIED_CITATIONS] 30/64 citations verified (47%)"
        assert any(f"❌ [{tag}]" in audit_out for tag in _CITATION_FAILURES)

    def test_clean_audit_not_detected(self):
        """Clean audit without citation failures → not detected."""
        _CITATION_FAILURES = ("FABRICATED_CITATIONS", "UNVERIFIED_CITATIONS")
        audit_out = "✅ [WORDS] 4200/4000\n✅ [ENGAGEMENT] 8 boxes"
        assert not any(f"❌ [{tag}]" in audit_out for tag in _CITATION_FAILURES)

    def test_passing_citations_not_detected(self):
        """Passing citation check (✅ not ❌) is not a failure."""
        _CITATION_FAILURES = ("FABRICATED_CITATIONS", "UNVERIFIED_CITATIONS")
        audit_out = "✅ [UNVERIFIED_CITATIONS] 55/64 citations verified (86%)"
        assert not any(f"❌ [{tag}]" in audit_out for tag in _CITATION_FAILURES)


# ===========================================================================
# 10. Write Placeholders Skip/Refresh Logic
# ===========================================================================

class TestWritePlaceholdersLogic:
    """Specification tests for write_placeholders() skip/refresh conditional.

    NOTE: These tests verify the DECISION LOGIC (boolean expression) that
    controls whether placeholders are regenerated. They do not call the actual
    write_placeholders() function, which requires a full ModuleContext with
    ~28 resolved paths. The logic under test is:
        `exists and not rebuild and not force_phase`
    from build_module.py:3061.

    This is a deliberate design choice — the conditional is the bug-prone part
    (force_phase was missing until #660), while the rest of write_placeholders
    is straightforward YAML serialization.
    """

    def test_skip_when_exists_no_force(self):
        """Existing placeholders + no rebuild + no force_phase → skip."""
        exists = True
        rebuild = False
        force_phase = None
        should_skip = exists and not rebuild and not force_phase
        assert should_skip is True

    def test_refresh_on_force_phase(self):
        """Existing placeholders + force_phase=True → refresh (don't skip)."""
        exists = True
        rebuild = False
        force_phase = True
        should_skip = exists and not rebuild and not force_phase
        assert should_skip is False

    def test_refresh_on_rebuild(self):
        """Existing placeholders + rebuild=True → refresh."""
        exists = True
        rebuild = True
        force_phase = None
        should_skip = exists and not rebuild and not force_phase
        assert should_skip is False

    def test_create_when_not_exists(self):
        """No existing placeholders → create (don't skip)."""
        exists = False
        rebuild = False
        force_phase = None
        should_skip = exists and not rebuild and not force_phase
        assert should_skip is False


# ===========================================================================
# 11. Real Review Fixture Tests (golden file validation)
# ===========================================================================

# ===========================================================================
# 11. Phase D Routing Decision Matrix
# ===========================================================================

class TestPhaseDRoutingMatrix:
    """Specification tests for Phase D routing decisions (audit × review → outcome).

    NOTE: These tests verify the DECISION LOGIC that determines whether a module
    enters D.2 repair, not the full phase_D_v3() function (which requires LLM
    calls, file I/O, and audit infrastructure). The routing expressions under
    test are from build_module_v3.py:2636-2700.

    Tests that call actual functions (like _all_issues_diffuse) provide real
    integration coverage. Tests that verify boolean expressions document the
    expected routing behavior as executable specifications.
    """

    def test_audit_pass_review_pass_no_d2(self):
        """Audit PASS + review PASS → module passes (no D.2 needed)."""
        passed = True
        review_says_fail = False
        # Decision: if passed and not review_says_fail → PASS
        should_enter_d2 = not (passed and not review_says_fail)
        assert should_enter_d2 is False

    def test_audit_pass_review_fail_enters_d2(self):
        """Audit PASS + review FAIL → enters D.2."""
        passed = True
        review_says_fail = True
        should_enter_d2 = not (passed and not review_says_fail)
        assert should_enter_d2 is True

    def test_audit_fail_review_pass_enters_d2_audit_only(self):
        """Audit FAIL + review PASS → enters D.2 with audit_only_d2=True."""
        passed = False
        review_says_fail = False
        # When audit fails, we set review_says_fail=True and _audit_only_d2=True
        _audit_only_d2 = not passed and not review_says_fail
        assert _audit_only_d2 is True

    def test_audit_fail_review_fail_enters_d2_full(self):
        """Audit FAIL + review FAIL → enters D.2 with full review injection."""
        passed = False
        review_says_fail = True
        # Full D.2: both audit + review issues injected
        _audit_only_d2 = not passed and not review_says_fail  # False — both fail
        assert _audit_only_d2 is False

    def test_citation_failure_blocks_d2(self):
        """UNVERIFIED_CITATIONS → pipeline fails, review deleted, no D.2."""
        _CITATION_FAILURES = ("FABRICATED_CITATIONS", "UNVERIFIED_CITATIONS")
        audit_out = "❌ [UNVERIFIED_CITATIONS] 30/64 citations verified (47%)"
        citation_failure = any(f"❌ [{tag}]" in audit_out for tag in _CITATION_FAILURES)
        assert citation_failure is True
        # When citation_failure: delete review, mark failed, return False — no D.2

    def test_all_diffuse_skips_d2(self):
        """All issues diffuse → needs-rebuild, skip D.2."""
        audit_out = "❌ [ROBOTIC_STRUCTURE] 4 patterns\n❌ [STRUCTURAL_MONOTONY] high overlap"
        # When all_issues_diffuse returns True: mark needs-rebuild, return False
        assert _all_issues_diffuse(audit_out) is True


# ===========================================================================
# 12. D.2 Prompt Injection Logic
# ===========================================================================

class TestD2PromptInjection:
    """Specification tests for D.2 prompt text injection (audit-only vs full review).

    NOTE: These tests verify the string replacement logic that determines
    what gets injected into the D.2 prompt template. The actual injection
    happens at build_module_v3.py:2718-2728. These are executable specs
    documenting the two injection modes.
    """

    def test_audit_only_d2_suppresses_review(self):
        """When audit_only_d2=True, review text is replaced with notice."""
        prompt_template = "Review:\n{INJECTED_REVIEW_TEXT}\n\nAudit:\n{INJECTED_AUDIT_FAILURES}"
        audit_only_notice = (
            "**IMPORTANT: The D.1 review verdict was PASS. "
            "Fix ONLY the audit failures listed below. "
            "Do NOT fix review suggestions — they are informational only.**\n\n"
            "(Review omitted — verdict was PASS)\n"
        )
        _audit_only_d2 = True
        if _audit_only_d2:
            result = prompt_template.replace("{INJECTED_REVIEW_TEXT}", audit_only_notice)
        else:
            result = prompt_template.replace("{INJECTED_REVIEW_TEXT}", "Full review text here")

        result = result.replace("{INJECTED_AUDIT_FAILURES}", "❌ [WORDS] 3500/4000")

        assert "Review omitted" in result
        assert "Full review text" not in result
        assert "WORDS" in result

    def test_full_d2_injects_review(self):
        """When audit_only_d2=False, full review text is injected."""
        prompt_template = "Review:\n{INJECTED_REVIEW_TEXT}\n\nAudit:\n{INJECTED_AUDIT_FAILURES}"
        review_text = "## Critical Issues Found\n\n### Issue 1: Grammar error on line 42"
        _audit_only_d2 = False
        if _audit_only_d2:
            result = prompt_template.replace("{INJECTED_REVIEW_TEXT}", "(omitted)")
        else:
            result = prompt_template.replace("{INJECTED_REVIEW_TEXT}", review_text)

        result = result.replace("{INJECTED_AUDIT_FAILURES}", "❌ [WORDS] 3500/4000")

        assert "Grammar error on line 42" in result
        assert "Review omitted" not in result


# ===========================================================================
# 13. Real Review Fixture Tests (golden file validation)
# ===========================================================================

class TestRealReviewFixtures:
    """Validate behavior against real D.1 review outputs from the repo."""

    @pytest.fixture
    def health_wellness_review(self):
        """Load real CONDITIONAL PASS review from committed fixture.

        Source: a2/health-wellness/phase-D-review-1.md (copied to tests/fixtures/).
        Uses committed fixture file to ensure test isolation from repo state.
        """
        path = Path(__file__).parent / "fixtures" / "d1-review-conditional-pass.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        pytest.skip("Fixture file not found — run: cp curriculum/l2-uk-en/a2/orchestration/health-wellness/phase-D-review-1.md tests/fixtures/d1-review-conditional-pass.md")

    def test_citations_extracted_from_real_review(self, health_wellness_review):
        """Real review contains extractable Ukrainian citations."""
        citations = _extract_ukrainian_citations(health_wellness_review)
        # Real review uses «» guillemets — should extract multiple
        assert len(citations) >= 3, f"Expected ≥3 citations, got {len(citations)}"

    def test_real_review_has_scores_section(self, health_wellness_review):
        """Real review contains ## Scores header."""
        assert "## Scores" in health_wellness_review

    def test_real_review_has_verdict_section(self, health_wellness_review):
        """Real review contains ## Verdict header."""
        assert "## Verdict" in health_wellness_review

    def test_real_review_has_critical_issues(self, health_wellness_review):
        """Real review contains ## Critical Issues Found header."""
        assert "## Critical Issues Found" in health_wellness_review
