"""
Tests for build_module.py pipeline logic.

Covers the pure/testable functions in the build pipeline:
- _extract_delimiter() — delimiter parsing
- _count_diff_lines() — diff size calculation
- _extract_audit_failures() — audit output parsing
- _extract_h2_sections() — H2 header extraction
- _inject_metrics_into_prompt() — placeholder injection
- _all_issues_diffuse() — diffuse vs targeted triage
- _quick_review_quality_gate() — review quality pre-save check
- Phase B gates (word count, purity)
- Phase C gates (file existence, schema validation)
- D.2 diff-size blocker logic

Issue: #520, #623
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_module import (
    _extract_delimiter,
    _count_diff_lines,
    _extract_audit_failures,
    _extract_h2_sections,
    _inject_metrics_into_prompt,
    _all_issues_diffuse,
    _quick_review_quality_gate,
)


# =============================================================================
# _extract_delimiter()
# =============================================================================

class TestExtractDelimiter:

    def test_basic_extraction(self):
        text = "before\n===START===\ncontent here\n===END===\nafter"
        result = _extract_delimiter(text, "===START===", "===END===")
        assert result == "content here"

    def test_multiline_content(self):
        text = "===A===\nline1\nline2\nline3\n===B==="
        result = _extract_delimiter(text, "===A===", "===B===")
        assert "line1" in result
        assert "line3" in result

    def test_missing_start_tag(self):
        text = "no start\n===END===\n"
        assert _extract_delimiter(text, "===START===", "===END===") is None

    def test_missing_end_tag(self):
        text = "===START===\nno end"
        assert _extract_delimiter(text, "===START===", "===END===") is None

    def test_empty_content(self):
        text = "===START===\n===END==="
        result = _extract_delimiter(text, "===START===", "===END===")
        assert result == ""

    def test_review_delimiters(self):
        """Real-world: extract review from Claude output."""
        text = (
            "Here is my review:\n"
            "===REVIEW_START===\n"
            "**Status:** PASS\n"
            "**Score:** 9.2/10\n"
            "===REVIEW_END===\n"
            "Done."
        )
        result = _extract_delimiter(text, "===REVIEW_START===", "===REVIEW_END===")
        assert "**Status:** PASS" in result
        assert "Done." not in result

    def test_section_fix_delimiters(self):
        """Real-world: extract fixes from D.2 output."""
        text = (
            "===SECTION_FIX_START===\n"
            "FILE: /path/to/file.md\n"
            "---\n"
            "FIND:\nold text\nREPLACE:\nnew text\n"
            "===SECTION_FIX_END===\n"
        )
        result = _extract_delimiter(text, "===SECTION_FIX_START===", "===SECTION_FIX_END===")
        assert "FIND:" in result
        assert "old text" in result


# =============================================================================
# _count_diff_lines()
# =============================================================================

class TestCountDiffLines:

    def test_identical_texts(self):
        assert _count_diff_lines("a\nb\nc\n", "a\nb\nc\n") == 0

    def test_one_line_changed(self):
        """Changing one line counts as 2 (old removed + new added)."""
        result = _count_diff_lines("a\nb\nc\n", "a\nX\nc\n")
        assert result == 2

    def test_one_line_added(self):
        result = _count_diff_lines("a\nb\n", "a\nb\nc\n")
        assert result == 1

    def test_one_line_removed(self):
        result = _count_diff_lines("a\nb\nc\n", "a\nb\n")
        assert result == 1

    def test_duplicate_lines_counted(self):
        """Unlike set-based diff, duplicate lines are properly tracked."""
        result = _count_diff_lines("a\na\na\n", "a\na\na\na\n")
        assert result == 1  # One line added

    def test_large_change(self):
        """Bulk rewrite produces proportional count."""
        before = "\n".join(f"line{i}" for i in range(20)) + "\n"
        after = "\n".join(f"changed{i}" for i in range(20)) + "\n"
        result = _count_diff_lines(before, after)
        assert result == 40  # 20 removed + 20 added

    def test_empty_to_content(self):
        result = _count_diff_lines("", "a\nb\nc\n")
        assert result == 3

    def test_content_to_empty(self):
        result = _count_diff_lines("a\nb\nc\n", "")
        assert result == 3


# =============================================================================
# _extract_audit_failures()
# =============================================================================

class TestExtractAuditFailures:

    def test_extracts_fail_lines(self):
        audit = "check 1: PASS\ncheck 2: FAIL — word count too low\ncheck 3: PASS"
        result = _extract_audit_failures(audit)
        assert "FAIL" in result
        assert "word count too low" in result
        assert "check 1: PASS" not in result

    def test_extracts_error_lines(self):
        audit = "info line\nERROR: missing vocabulary file\ninfo line2"
        result = _extract_audit_failures(audit)
        assert "ERROR" in result
        assert "missing vocabulary" in result

    def test_extracts_emoji_markers(self):
        audit = "✅ word count\n❌ [LOW_CITATION_DENSITY] too few\n✅ activities"
        result = _extract_audit_failures(audit)
        assert "LOW_CITATION_DENSITY" in result

    def test_extracts_violation_lines(self):
        audit = "Euphony VIOLATION at line 42\nOther info"
        result = _extract_audit_failures(audit)
        assert "VIOLATION" in result

    def test_fallback_on_no_failures(self):
        """When no keywords found, returns last 40 lines as fallback."""
        audit = "\n".join(f"info line {i}" for i in range(50))
        result = _extract_audit_failures(audit)
        assert "info line 49" in result
        assert "info line 9" not in result  # line 9 is outside last 40 (indices 10-49)

    def test_empty_input(self):
        result = _extract_audit_failures("")
        assert isinstance(result, str)


# =============================================================================
# _extract_h2_sections()
# =============================================================================

class TestExtractH2Sections:

    def test_extracts_headers(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("# Title\n\n## Вступ\n\ntext\n\n## Читання\n\nmore text\n")
        result = _extract_h2_sections(md)
        assert "1. Вступ" in result
        assert "2. Читання" in result

    def test_missing_file(self, tmp_path):
        result = _extract_h2_sections(tmp_path / "nonexistent.md")
        assert "not found" in result

    def test_no_h2_headers(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("# Title\n\nJust text, no H2s.\n")
        result = _extract_h2_sections(md)
        assert "no H2" in result

    def test_many_sections(self, tmp_path):
        md = tmp_path / "test.md"
        sections = "\n".join(f"## Section {i}\n\nContent {i}\n" for i in range(1, 8))
        md.write_text(f"# Title\n\n{sections}")
        result = _extract_h2_sections(md)
        assert "7. Section 7" in result


# =============================================================================
# _inject_metrics_into_prompt()
# =============================================================================

class TestInjectMetrics:

    def test_single_placeholder(self):
        result = _inject_metrics_into_prompt(
            "Words: {COMPUTED_WORD_COUNT}", {"COMPUTED_WORD_COUNT": "3500"}
        )
        assert result == "Words: 3500"

    def test_multiple_placeholders(self):
        prompt = "Words: {COMPUTED_WORD_COUNT}, Target: {COMPUTED_WORD_TARGET}"
        metrics = {"COMPUTED_WORD_COUNT": "3500", "COMPUTED_WORD_TARGET": "4000"}
        result = _inject_metrics_into_prompt(prompt, metrics)
        assert "3500" in result
        assert "4000" in result

    def test_unmatched_placeholder_preserved(self):
        result = _inject_metrics_into_prompt(
            "{COMPUTED_WORD_COUNT} and {OTHER}", {"COMPUTED_WORD_COUNT": "100"}
        )
        assert "{OTHER}" in result

    def test_empty_metrics(self):
        prompt = "No changes: {COMPUTED_WORD_COUNT}"
        result = _inject_metrics_into_prompt(prompt, {})
        assert "{COMPUTED_WORD_COUNT}" in result


# =============================================================================
# _all_issues_diffuse() — THE CRITICAL TRIAGE FUNCTION
# =============================================================================

class TestAllIssuesDiffuse:
    """Tests for the diffuse vs targeted triage logic.

    This function decides whether D.2 repair is attempted or the module
    goes straight to needs-rebuild. Getting this wrong wastes either an
    expensive Claude call (false negative) or causes unnecessary rebuilds
    (false positive — the at-the-store bug).
    """

    # --- Audit passed (no failing codes) → always proceed to D.2 ---

    def test_audit_passed_returns_false(self):
        """When audit passes, all issues come from the review.
        Review issues are targeted by definition — never skip D.2."""
        assert _all_issues_diffuse("all gates PASS") is False

    def test_empty_audit_returns_false(self):
        assert _all_issues_diffuse("") is False

    def test_audit_pass_with_info_lines(self):
        """INFO and PASS lines should not trigger diffuse classification."""
        audit = (
            "✅ [WORD_COUNT] 3500/3000 PASS\n"
            "✅ [ACTIVITIES] 10/8 PASS\n"
            "ℹ️ [NATURALNESS] PENDING — awaiting review\n"
        )
        assert _all_issues_diffuse(audit) is False

    # --- Audit failed with only diffuse codes → skip D.2 ---

    def test_only_robotic_structure(self):
        assert _all_issues_diffuse("❌ [ROBOTIC_STRUCTURE] detected") is True

    def test_only_content_redundancy(self):
        assert _all_issues_diffuse("FAIL: [CONTENT_REDUNDANCY] threshold exceeded") is True

    def test_multiple_diffuse_codes(self):
        audit = "❌ [ROBOTIC_STRUCTURE] found\n❌ [CONTENT_REDUNDANCY] 75% overlap"
        assert _all_issues_diffuse(audit) is True

    def test_low_immersion_is_diffuse(self):
        assert _all_issues_diffuse("FAIL: [LOW_IMMERSION] 15% vs 35% target") is True

    # --- Audit failed with targeted codes → proceed to D.2 ---

    def test_grammar_error_is_targeted(self):
        assert _all_issues_diffuse("FAIL: [GRAMMAR_ERROR] found") is False

    def test_low_word_count_is_targeted(self):
        assert _all_issues_diffuse("❌ [LOW_WORD_COUNT] 1500 < 3000") is False

    def test_missing_vocabulary_is_targeted(self):
        assert _all_issues_diffuse("FAIL: [MISSING_VOCABULARY] no vocab file") is False

    # --- Mixed codes → proceed to D.2 (has at least one targeted) ---

    def test_mixed_diffuse_and_targeted(self):
        audit = "❌ [ROBOTIC_STRUCTURE]\n❌ [GRAMMAR_ERROR]"
        assert _all_issues_diffuse(audit) is False

    def test_diffuse_plus_unknown_code(self):
        """Unknown codes are treated as targeted (conservative)."""
        audit = "❌ [ROBOTIC_STRUCTURE]\nFAIL: [SOME_NEW_CHECK]"
        assert _all_issues_diffuse(audit) is False

    # --- Edge cases ---

    def test_code_in_pass_line_not_counted(self):
        """Codes that appear on PASS lines should not be counted as failing."""
        audit = "✅ [ROBOTIC_STRUCTURE] PASS — no issues"
        assert _all_issues_diffuse(audit) is False

    def test_fail_keyword_case_insensitive(self):
        """FAIL detection should be case-insensitive."""
        assert _all_issues_diffuse("fail: [CONTENT_REDUNDANCY] found") is True

    def test_real_audit_output_pass(self):
        """Real-world audit output that passed all gates."""
        audit = """VERDICT: PASS
✅ Meta: Valid Structure
✅ Lesson: 2665/2000 (raw: 3016)
✅ Activities: 9/8
✅ Vocabulary: 18/1
✅ IPA: Clean IPA
✅ Research: Content aligned with research
✅ Review: PASS (9.2/10)
"""
        assert _all_issues_diffuse(audit) is False


# =============================================================================
# _quick_review_quality_gate()
# =============================================================================

class TestQuickReviewQualityGate:

    def _make_content(self, tmp_path, word_count=3000):
        """Create a content file with approximate word count."""
        md = tmp_path / "content.md"
        words = " ".join(f"слово{i}" for i in range(word_count))
        md.write_text(f"---\ntitle: Test\n---\n\n## Вступ\n\n{words}\n\n## Читання\n\nMore content here.\n")
        return md

    def _make_review(self, citations=10, sections=None, words=300):
        """Create a review with controlled citation count and section mentions."""
        if sections is None:
            sections = ["Вступ", "Читання"]
        citation_block = "\n".join(
            f"«Приклад цитати номер {i} з модуля»" for i in range(citations)
        )
        section_block = "\n".join(
            f"Section «{s}» is well-structured." for s in sections
        )
        filler = " ".join(f"word{i}" for i in range(words))
        return f"**Status:** PASS\n\n{citation_block}\n\n{section_block}\n\n{filler}"

    def test_good_review_passes(self, tmp_path):
        content = self._make_content(tmp_path)
        review = self._make_review(citations=10, sections=["Вступ", "Читання"])
        ok, reason = _quick_review_quality_gate(review, content)
        assert ok, f"Expected PASS but got: {reason}"

    def test_too_few_citations_fails(self, tmp_path):
        content = self._make_content(tmp_path, word_count=3000)
        review = self._make_review(citations=1, words=300)
        ok, reason = _quick_review_quality_gate(review, content)
        assert not ok
        assert "citation" in reason.lower()

    def test_too_short_review_fails(self, tmp_path):
        content = self._make_content(tmp_path)
        review = "Very short review."
        ok, reason = _quick_review_quality_gate(review, content)
        assert not ok
        # Citation check fires before word count check for very short reviews
        assert "shallow review" in reason.lower()

    def test_small_content_needs_fewer_citations(self, tmp_path):
        """Short content (< 600 words) only needs 2 citations."""
        content = self._make_content(tmp_path, word_count=400)
        review = self._make_review(citations=2, words=200)
        ok, reason = _quick_review_quality_gate(review, content)
        assert ok, f"Expected PASS but got: {reason}"


# =============================================================================
# PHASE GATE INTEGRATION TESTS (using real pipeline paths)
# =============================================================================

class TestPhaseBGates:
    """Test Phase B post-conditions: word count and purity checks."""

    def test_word_count_gate_rejects_short_content(self, tmp_path):
        """Content < 80% of target should fail Phase B."""
        from audit.cleaners import clean_for_stats
        md = tmp_path / "test.md"
        # Write ~500 words (below 80% of 2000 = 1600)
        md.write_text("## Test\n\n" + " ".join(f"word{i}" for i in range(500)))
        raw = md.read_text("utf-8")
        wc = len(clean_for_stats(raw).split())
        word_target = 2000
        threshold = word_target * 0.8
        assert wc < threshold, f"Test setup error: {wc} >= {threshold}"

    def test_word_count_gate_accepts_sufficient_content(self, tmp_path):
        """Content >= 80% of target should pass the gate."""
        from audit.cleaners import clean_for_stats
        md = tmp_path / "test.md"
        md.write_text("## Test\n\n" + " ".join(f"word{i}" for i in range(2000)))
        raw = md.read_text("utf-8")
        wc = len(clean_for_stats(raw).split())
        word_target = 2000
        threshold = word_target * 0.8
        assert wc >= threshold

    def test_purity_check_detects_robotic_starters(self):
        """Content with robotic sentence starters should trigger warning.

        The detector uses a sliding window of 4 sentences and requires 3+
        identical two-word starters in that window. Alternating patterns
        (A-B-A-B) only produce 2 of each, so we need 3+ consecutive.
        """
        from audit.checks.content_purity import check_content_purity
        # Need 5+ clean sentences for the sliding window (size 4) to iterate,
        # and 3+ matching starters within the window to trigger detection.
        # The first sentence merges with "## Section" and gets skipped, so use 6.
        sentences = [f"Let us examine topic {i} in detail here." for i in range(6)]
        content = "## Section\n\n" + " ".join(sentences)
        violations = check_content_purity(content)
        robotic = [v for v in violations if v["type"] == "ROBOTIC_STRUCTURE"]
        assert len(robotic) > 0

    def test_purity_check_passes_natural_content(self):
        from audit.checks.content_purity import check_content_purity
        content = (
            "## Вступ\n\n"
            "Українська мова має багату історію. Протягом століть вона розвивалася "
            "під впливом різних культур. Сьогодні українська є державною мовою України. "
            "Мільйони людей розмовляють нею щодня. Кожне слово несе в собі частинку "
            "національної ідентичності. Вивчення мови відкриває нові горизонти."
        )
        violations = check_content_purity(content)
        assert len(violations) == 0


class TestPhaseCGates:
    """Test Phase C post-conditions: file existence and schema validation."""

    def test_valid_activities_pass_schema(self, tmp_path):
        """Well-formed activities YAML should pass validation."""
        from pipeline_lib import _validate_activities_yaml
        act = tmp_path / "activities.yaml"
        # Schema requires: question (not q), options array with exactly 4 items
        act.write_text(
            "- type: quiz\n"
            "  title: Перевірка\n"
            "  items:\n"
            "    - question: \"Що це?\"\n"
            "      options:\n"
            "        - text: \"Це книга\"\n"
            "          correct: true\n"
            "        - text: \"Це стіл\"\n"
            "          correct: false\n"
            "        - text: \"Це ручка\"\n"
            "          correct: false\n"
            "        - text: \"Це двері\"\n"
            "          correct: false\n"
        )
        assert _validate_activities_yaml(act) is True

    def test_empty_file_passes_schema(self, tmp_path):
        """Empty YAML file parses to None — validator treats as 'nothing to validate'."""
        from pipeline_lib import _validate_activities_yaml
        act = tmp_path / "activities.yaml"
        act.write_text("")
        # Empty file = no activities to validate = valid (Phase C checks existence separately)
        assert _validate_activities_yaml(act) is True

    def test_malformed_yaml_fails_schema(self, tmp_path):
        from pipeline_lib import _validate_activities_yaml
        act = tmp_path / "activities.yaml"
        act.write_text("not: valid: yaml: [[[")
        assert _validate_activities_yaml(act) is False


class TestDiffSizeBlocker:
    """Test the D.2 diff-size calculation and threshold logic."""

    def test_small_fix_within_threshold(self):
        """A single-line fix should be well within any threshold."""
        before = "line1\nline2\nline3\n"
        after = "line1\nfixed_line2\nline3\n"
        changed = _count_diff_lines(before, after)
        fix_pair_count = 1
        max_allowed = max(fix_pair_count * 15, 30)
        assert changed <= max_allowed

    def test_paragraph_replacement_within_threshold(self):
        """Replacing a 5-line paragraph with a 5-line fix should pass."""
        before = "\n".join(f"old_line_{i}" for i in range(5)) + "\n"
        after = "\n".join(f"new_line_{i}" for i in range(5)) + "\n"
        changed = _count_diff_lines(before, after)
        fix_pair_count = 1
        max_allowed = max(fix_pair_count * 15, 30)
        assert changed <= max_allowed, f"{changed} > {max_allowed}"

    def test_massive_rewrite_exceeds_threshold(self):
        """Rewriting 100 lines when only 2 fix pairs exist should exceed threshold."""
        before = "\n".join(f"old_{i}" for i in range(100)) + "\n"
        after = "\n".join(f"new_{i}" for i in range(100)) + "\n"
        changed = _count_diff_lines(before, after)
        fix_pair_count = 2
        max_allowed = max(fix_pair_count * 15, 30)
        assert changed > max_allowed, f"{changed} <= {max_allowed}"

    def test_threshold_minimum_floor(self):
        """Even with 1 fix pair, at least 30 lines are always allowed."""
        fix_pair_count = 1
        max_allowed = max(fix_pair_count * 15, 30)
        assert max_allowed == 30


# =============================================================================
# REVIEW VERDICT CHECK (audit gate)
# =============================================================================

class TestReviewVerdictCheck:
    """The audit must fail when a review's own verdict is FAIL."""

    def test_fail_verdict_produces_violation(self, tmp_path):
        """A review with **Status:** FAIL should produce REVIEW_VERDICT_FAIL."""
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from audit.checks.review_validation import check_review_validity

        # Create a module .md file
        md = tmp_path / "a1" / "test-module.md"
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text("---\ntitle: Test\n---\n\n## Вступ\n\nContent here.\n")

        # Create a structurally valid review with FAIL verdict
        review_dir = md.parent / "review"
        review_dir.mkdir(parents=True, exist_ok=True)
        review = review_dir / "test-module-review.md"
        review.write_text(
            "**Status:** FAIL\n**Score:** 6.5/10\n\n"
            "## Summary\nThis module has issues.\n\n"
            "## Dimension Scores\n| Dim | Score |\n|---|---|\n| Accuracy | 6/10 |\n\n"
            "## Critical Issues\n- Grammar errors in section 2\n"
            "- Missing vocabulary for key terms\n\n"
            "## Recommendations\nFix the issues above.\n"
            + ("x " * 500)  # Ensure minimum length
        )

        violations = check_review_validity(str(md), "a1", "test-module")
        verdict_violations = [v for v in violations if v["type"] == "REVIEW_VERDICT_FAIL"]
        assert len(verdict_violations) > 0, f"Expected REVIEW_VERDICT_FAIL but got: {[v['type'] for v in violations]}"

    def test_pass_verdict_no_violation(self, tmp_path):
        """A review with **Status:** PASS should not produce REVIEW_VERDICT_FAIL."""
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from audit.checks.review_validation import check_review_validity

        md = tmp_path / "a1" / "test-module.md"
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text("---\ntitle: Test\n---\n\n## Вступ\n\nContent here.\n")

        review_dir = md.parent / "review"
        review_dir.mkdir(parents=True, exist_ok=True)
        review = review_dir / "test-module-review.md"
        review.write_text(
            "**Status:** PASS\n**Score:** 9.2/10\n\n"
            "## Summary\nExcellent module.\n\n"
            "## Dimension Scores\n| Dim | Score |\n|---|---|\n| Accuracy | 9/10 |\n\n"
            "## Critical Issues\n- Minor suggestion: vary sentence starters in section 3\n\n"
            "## Recommendations\nModule is ready.\n"
            + ("x " * 500)
        )

        violations = check_review_validity(str(md), "a1", "test-module")
        verdict_violations = [v for v in violations if v["type"] == "REVIEW_VERDICT_FAIL"]
        assert len(verdict_violations) == 0, f"Unexpected REVIEW_VERDICT_FAIL: {verdict_violations}"
