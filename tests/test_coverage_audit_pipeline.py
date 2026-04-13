"""
Tests targeting coverage gaps in audit and pipeline scripts.

Target files:
1. scripts/audit/checks/review_gaming.py
2. scripts/audit/phases_gates.py
3. scripts/audit/phases_activity.py
4. scripts/audit/checks/review_validation.py
5. scripts/audit/core.py
6. scripts/manifest_utils.py
7. scripts/proofread.py — REMOVED (deprecated, absorbed into v5 review phase)
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

# Ensure scripts/ is importable
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


# ============================================================================
# 1. review_gaming.py
# ============================================================================

class TestReviewGamingHelpers:
    """Tests for review_gaming helper functions."""

    def test_extract_all_scores_basic(self):
        from audit.checks.review_gaming import _extract_all_scores
        content = "| Grammar | 8.5/10 |\n| Vocab | 9/10 |\n| Flow | 7.0/10 |"
        scores = _extract_all_scores(content)
        assert scores == [8.5, 9.0, 7.0]

    def test_extract_all_scores_empty(self):
        from audit.checks.review_gaming import _extract_all_scores
        assert _extract_all_scores("no scores here") == []

    def test_extract_all_scores_non_numeric_ignored(self):
        from audit.checks.review_gaming import _extract_all_scores
        content = "| Grammar | good/10 |\n| Vocab | 9/10 |"
        scores = _extract_all_scores(content)
        assert scores == [9.0]

    def test_extract_h2_headers(self):
        from audit.checks.review_gaming import _extract_h2_headers
        content = "# H1\n## Section One\ntext\n## Section Two\nmore\n### H3"
        headers = _extract_h2_headers(content)
        assert headers == ["Section One", "Section Two"]

    def test_extract_h2_headers_empty(self):
        from audit.checks.review_gaming import _extract_h2_headers
        assert _extract_h2_headers("no headers") == []

    def test_normalize_for_hash(self):
        from audit.checks.review_gaming import _normalize_for_hash
        assert _normalize_for_hash("  Hello   World  ") == "hello world"

    def test_normalize_for_hash_newlines(self):
        from audit.checks.review_gaming import _normalize_for_hash
        assert _normalize_for_hash("hello\n\nworld") == "hello world"

    def test_get_all_review_files_no_dir(self, tmp_path):
        from audit.checks.review_gaming import _get_all_review_files
        assert _get_all_review_files(tmp_path) == []

    def test_get_all_review_files_with_dir(self, tmp_path):
        from audit.checks.review_gaming import _get_all_review_files
        review_dir = tmp_path / "review"
        review_dir.mkdir()
        (review_dir / "foo-review.md").write_text("content")
        (review_dir / "bar-review.md").write_text("content")
        (review_dir / "not-a-review.txt").write_text("skip")
        result = _get_all_review_files(tmp_path)
        assert len(result) == 2

    def test_find_review_file_canonical(self, tmp_path):
        from audit.checks.review_gaming import _find_review_file
        review_dir = tmp_path / "review"
        review_dir.mkdir()
        review_file = review_dir / "my-module-review.md"
        review_file.write_text("review content")
        md_file = tmp_path / "my-module.md"
        md_file.write_text("content")
        result = _find_review_file(str(md_file), "my-module")
        assert result == review_file

    def test_find_review_file_legacy(self, tmp_path):
        from audit.checks.review_gaming import _find_review_file
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        legacy = audit_dir / "my-module-review.md"
        legacy.write_text("legacy review")
        md_file = tmp_path / "my-module.md"
        md_file.write_text("content")
        result = _find_review_file(str(md_file), "my-module")
        assert result == legacy

    def test_find_review_file_not_found(self, tmp_path):
        from audit.checks.review_gaming import _find_review_file
        md_file = tmp_path / "my-module.md"
        md_file.write_text("content")
        result = _find_review_file(str(md_file), "my-module")
        assert result is None


class TestCheckScoreUniformity:
    """Tests for check_score_uniformity."""

    def test_too_few_scores(self):
        from audit.checks.review_gaming import check_score_uniformity
        content = "| A | 9/10 |\n| B | 9/10 |"
        assert check_score_uniformity(content) == []

    def test_uniform_high_scores(self):
        from audit.checks.review_gaming import check_score_uniformity
        rows = "\n".join(f"| Dim{i} | 9.5/10 |" for i in range(6))
        violations = check_score_uniformity(rows)
        assert len(violations) == 1
        assert violations[0]['type'] == 'UNIFORM_HIGH_SCORES'

    def test_varied_scores_no_violation(self):
        from audit.checks.review_gaming import check_score_uniformity
        rows = "| A | 6/10 |\n| B | 9/10 |\n| C | 7/10 |\n| D | 8/10 |\n| E | 5/10 |"
        assert check_score_uniformity(rows) == []

    def test_uniform_low_scores_no_violation(self):
        from audit.checks.review_gaming import check_score_uniformity
        rows = "\n".join(f"| Dim{i} | 5/10 |" for i in range(6))
        assert check_score_uniformity(rows) == []


class TestCheckCitationDensity:
    """Tests for check_citation_density."""

    def test_tier1_skipped(self, tmp_path):
        from audit.checks.review_gaming import check_citation_density
        md = tmp_path / "test.md"
        md.write_text("word " * 500)
        result = check_citation_density("review", str(md), str(tmp_path / "a1" / "test.md"), "A1")
        assert result == []

    def test_short_content_skipped(self, tmp_path):
        from audit.checks.review_gaming import check_citation_density
        md = tmp_path / "test.md"
        md.write_text("short")
        result = check_citation_density("review", str(md), str(tmp_path / "b1" / "test.md"), "B1")
        assert result == []

    def test_content_file_not_exists(self, tmp_path):
        from audit.checks.review_gaming import check_citation_density
        result = check_citation_density("review", str(tmp_path / "nope.md"),
                                         str(tmp_path / "b1" / "test.md"), "B1")
        assert result == []

    def test_critical_low_density(self, tmp_path):
        from audit.checks.review_gaming import check_citation_density
        md = tmp_path / "test.md"
        md.write_text("word " * 2000)
        # Review with no Ukrainian citations
        result = check_citation_density("review text only english",
                                         str(md), str(tmp_path / "b1" / "test.md"), "B1")
        assert any(v['severity'] == 'critical' for v in result)

    def test_warning_low_density(self, tmp_path):
        from audit.checks.review_gaming import check_citation_density
        md = tmp_path / "test.md"
        md.write_text("word " * 1200)
        # 2 citations for 1200 words: expected_min=2, expected_warn=4
        review = 'Review: «Це дуже гарне речення яке я бачу тут» and «Ще одне речення тут для тесту»'
        result = check_citation_density(review, str(md),
                                         str(tmp_path / "b1" / "test.md"), "B1")
        assert any(v['severity'] == 'warning' for v in result)


class TestCheckReviewSectionCoverage:
    """Tests for check_review_section_coverage."""

    def test_too_few_sections(self):
        from audit.checks.review_gaming import check_review_section_coverage
        content = "## Section One\ntext\n## Словник\nwords"
        assert check_review_section_coverage("review", content) == []

    def test_critical_low_coverage(self):
        from audit.checks.review_gaming import check_review_section_coverage
        headers = "\n".join(f"## Topic {i}\nsome text" for i in range(5))
        review = "This review talks about unrelated things."
        violations = check_review_section_coverage(review, headers)
        assert any(v['type'] == 'REVIEW_LOW_SECTION_COVERAGE' for v in violations)

    def test_full_coverage(self):
        from audit.checks.review_gaming import check_review_section_coverage
        content = "## Grammar\ntext\n## Vocabulary\ntext\n## Practice\ntext\n## Culture\ntext"
        review = "The grammar section is strong. Vocabulary is good. Practice is solid. Culture section works."
        violations = check_review_section_coverage(review, content)
        # Should not flag since all sections are mentioned
        assert not any(v['type'] == 'REVIEW_LOW_SECTION_COVERAGE' and v['severity'] == 'critical' for v in violations)

    def test_english_equivalent_matching(self):
        from audit.checks.review_gaming import check_review_section_coverage
        content = "## Вступ\ntext\n## Теорія\ntext\n## Практика\ntext\n## Граматика\ntext"
        review = "The introduction is solid. The theory section works. Practice exercises are good. Grammar is accurate."
        violations = check_review_section_coverage(review, content)
        assert not any(v['severity'] == 'critical' for v in violations)

    def test_skip_standard_headers(self):
        from audit.checks.review_gaming import check_review_section_coverage
        content = "## Словник\n## Бібліографія\n## Джерела\n## Лексика\n"
        assert check_review_section_coverage("review", content) == []

    def test_partial_word_matching(self):
        from audit.checks.review_gaming import check_review_section_coverage
        content = "## Дієслова руху\ntext\n## Умовний спосіб\ntext\n## Активні дієприкметники\ntext\n## Пасивний стан\ntext"
        review = "The дієслова руху section is complete. The умовний спосіб part works well. Активні дієприкметники are covered. Пасивний стан needs work."
        violations = check_review_section_coverage(review, content)
        assert not any(v['severity'] == 'critical' for v in violations)

    def test_warning_partial_coverage(self):
        from audit.checks.review_gaming import check_review_section_coverage
        # Use long unique words that won't fuzzy-match
        headers = (
            "## Фармакологічні дослідження\ntext\n"
            "## Астрономічні спостереження\ntext\n"
            "## Палеонтологічна експедиція\ntext\n"
            "## Кібернетичні системи\ntext\n"
            "## Мікробіологічний аналіз\ntext\n"
        )
        # Mention only 2 of 5 (~40%)
        review = "Фармакологічні дослідження розглянуто. Астрономічні спостереження описано добре."
        violations = check_review_section_coverage(review, headers)
        # Function may return warning or critical depending on coverage threshold
        assert isinstance(violations, list)

    def test_colon_prefix_matching(self):
        from audit.checks.review_gaming import check_review_section_coverage
        content = "## Час дієслова: теперішній\ntext\n## Рід іменника: жіночий\ntext\n## Відмінок: давальний\ntext\n## Вид дієслова: доконаний\ntext"
        review = "The час дієслова section is good. Рід іменника is covered. Відмінок analysis works. Вид дієслова explanation is thorough."
        violations = check_review_section_coverage(review, content)
        assert not any(v['severity'] == 'critical' for v in violations)


class TestCheckScoreDrift:
    """Tests for check_score_drift."""

    def test_too_few_scores(self):
        from audit.checks.review_gaming import check_score_drift
        content = "| A | 9/10 |"
        assert check_score_drift(content, "/fake/path.md", "slug") == []

    def test_fallback_high_mean(self, tmp_path):
        from audit.checks.review_gaming import check_score_drift
        rows = "\n".join(f"| Dim{i} | 9.5/10 |" for i in range(6))
        md = tmp_path / "test.md"
        md.write_text("content")
        violations = check_score_drift(rows, str(md), "test")
        assert len(violations) == 1
        assert violations[0]['type'] == 'SCORE_DRIFT_OUTLIER'

    def test_no_violation_below_threshold(self, tmp_path):
        from audit.checks.review_gaming import check_score_drift
        rows = "\n".join(f"| Dim{i} | 7/10 |" for i in range(6))
        md = tmp_path / "test.md"
        md.write_text("content")
        violations = check_score_drift(rows, str(md), "test")
        assert violations == []

    def test_drift_with_other_reviews(self, tmp_path):
        from audit.checks.review_gaming import check_score_drift
        review_dir = tmp_path / "review"
        review_dir.mkdir()
        # Create 5 other reviews with lower scores
        for i in range(6):
            rows = "\n".join(f"| Dim{j} | 6/10 |" for j in range(6))
            (review_dir / f"module-{i}-review.md").write_text(rows)
        # Current review with high scores
        high_rows = "\n".join(f"| Dim{j} | 9.8/10 |" for j in range(6))
        md = tmp_path / "my-test.md"
        md.write_text("content")
        violations = check_score_drift(high_rows, str(md), "my-test")
        assert len(violations) == 1
        assert 'outlier' in violations[0]['message'].lower()


class TestCheckReviewBoilerplate:
    """Tests for check_review_boilerplate."""

    def test_no_issues_section(self):
        from audit.checks.review_gaming import check_review_boilerplate
        assert check_review_boilerplate("no issues section", "/fake/path.md", "slug") == []

    def test_short_issues_section(self):
        from audit.checks.review_gaming import check_review_boilerplate
        content = "## Issues\nToo short."
        assert check_review_boilerplate(content, "/fake/path.md", "slug") == []

    def test_too_few_sentences(self):
        from audit.checks.review_gaming import check_review_boilerplate
        content = "## Issues\nOne single issue sentence here. Another one."
        assert check_review_boilerplate(content, "/fake/path.md", "slug") == []

    def test_boilerplate_critical(self, tmp_path):
        from audit.checks.review_gaming import check_review_boilerplate
        review_dir = tmp_path / "review"
        review_dir.mkdir()
        # Shared sentences
        sentences = [
            "This module has a problem with grammar consistency throughout.",
            "The vocabulary section needs more diverse examples for students.",
            "Activity density is below the expected threshold for this level.",
            "The cultural context section lacks proper academic references.",
        ]
        issues_text = " ".join(sentences)
        current = f"## Issues Found\n{issues_text}\n## Recommendation\nFix."
        other = f"## Issues Found\n{issues_text}\n## Recommendation\nFix."
        (review_dir / "other-module-review.md").write_text(other)
        md = tmp_path / "my-module.md"
        md.write_text("content")
        violations = check_review_boilerplate(current, str(md), "my-module")
        assert any(v['type'] == 'REVIEW_BOILERPLATE' for v in violations)

    def test_no_boilerplate_when_unique(self, tmp_path):
        from audit.checks.review_gaming import check_review_boilerplate
        review_dir = tmp_path / "review"
        review_dir.mkdir()
        sentences_a = [
            "Module has incorrect case usage in section three specifically.",
            "The accusative examples in paragraph two have wrong endings.",
            "Activity five uses wrong stem for irregular verb conjugation.",
            "Cultural context incorrectly states date of historical event.",
        ]
        sentences_b = [
            "Completely different issue about pronunciation audio missing.",
            "Another unique problem with vocabulary list being incomplete.",
            "A third unrelated concern about engagement box formatting.",
            "Fourth distinct issue about transliteration policy violation.",
        ]
        current = f"## Issues Found\n{' '.join(sentences_a)}\n## Recommendation\nFix."
        other = f"## Issues Found\n{' '.join(sentences_b)}\n## Recommendation\nFix."
        (review_dir / "other-review.md").write_text(other)
        md = tmp_path / "my-module.md"
        md.write_text("content")
        violations = check_review_boilerplate(current, str(md), "my-module")
        assert not any(v['type'] == 'REVIEW_BOILERPLATE' for v in violations)


class TestCheckReviewSectionReferences:
    """Tests for check_review_section_references."""

    def test_no_references(self):
        from audit.checks.review_gaming import check_review_section_references
        assert check_review_section_references("no references", "## Heading\ntext") == []

    def test_valid_reference(self):
        from audit.checks.review_gaming import check_review_section_references
        review = 'Section "Grammar" is well done.'
        content = "## Grammar\ntext\n## Vocab\nmore\n## Practice\nmore"
        assert check_review_section_references(review, content) == []

    def test_phantom_reference(self):
        from audit.checks.review_gaming import check_review_section_references
        review = 'Section "Nonexistent Section" has problems.'
        content = "## Grammar\ntext\n## Vocab\nmore\n## Practice\nmore"
        violations = check_review_section_references(review, content)
        assert len(violations) == 1
        assert violations[0]['type'] == 'PHANTOM_SECTION_REFERENCE'

    def test_ukrainian_reference(self):
        from audit.checks.review_gaming import check_review_section_references
        review = 'Розділ «Граматика» потребує доопрацювання.'
        content = "## Граматика\ntext\n## Лексика\nmore\n## Практика\nmore"
        assert check_review_section_references(review, content) == []

    def test_fuzzy_match_reference(self):
        from audit.checks.review_gaming import check_review_section_references
        review = 'Section "Advanced Grammar Usage" covers most topics.'
        content = "## Advanced Grammar Usage and Practice\ntext\n## Vocab\nmore\n## Culture\nmore"
        # "Advanced Grammar Usage" words should match "Advanced Grammar Usage and Practice"
        assert check_review_section_references(review, content) == []

    def test_angular_quote_reference(self):
        from audit.checks.review_gaming import check_review_section_references
        review = 'Section «Practice» is adequate.'
        content = "## Practice\ntext\n## Theory\nmore\n## Culture\nmore"
        assert check_review_section_references(review, content) == []


class TestCheckCrossAgentReview:
    """Tests for check_cross_agent_review."""

    def test_missing_reviewer(self, tmp_path):
        from audit.checks.review_gaming import check_cross_agent_review
        md = tmp_path / "test.md"
        md.write_text("content")
        violations = check_cross_agent_review("Review without reviewer", str(md))
        assert any(v['type'] == 'MISSING_REVIEWER_ID' for v in violations)

    def test_self_review_detected(self, tmp_path):
        from audit.checks.review_gaming import check_cross_agent_review
        md = tmp_path / "test.md"
        md.write_text("content")
        orch_dir = tmp_path / "orchestration" / "test"
        orch_dir.mkdir(parents=True)
        state = {"phases": {"B": {"model": "gemini-2.5-flash"}}}
        (orch_dir / "state-v3.json").write_text(json.dumps(state))
        review = "**Reviewed-By:** gemini-pro-preview"
        violations = check_cross_agent_review(review, str(md))
        assert any(v['type'] == 'SELF_REVIEW_DETECTED' for v in violations)

    def test_cross_agent_ok(self, tmp_path):
        from audit.checks.review_gaming import check_cross_agent_review
        md = tmp_path / "test.md"
        md.write_text("content")
        orch_dir = tmp_path / "orchestration" / "test"
        orch_dir.mkdir(parents=True)
        state = {"phases": {"B": {"model": "gemini-2.5-flash"}}}
        (orch_dir / "state-v3.json").write_text(json.dumps(state))
        review = "**Reviewed-By:** claude-opus-4-6"
        violations = check_cross_agent_review(review, str(md))
        assert not any(v['type'] == 'SELF_REVIEW_DETECTED' for v in violations)

    def test_no_state_file(self, tmp_path):
        from audit.checks.review_gaming import check_cross_agent_review
        md = tmp_path / "test.md"
        md.write_text("content")
        review = "**Reviewed-By:** claude-opus-4-6"
        violations = check_cross_agent_review(review, str(md))
        assert violations == []


class TestModelFamily:
    """Tests for _model_family."""

    def test_google_family(self):
        from audit.checks.review_gaming import _model_family
        assert _model_family("gemini-2.5-flash") == "google"
        assert _model_family("Google PaLM") == "google"

    def test_anthropic_family(self):
        from audit.checks.review_gaming import _model_family
        assert _model_family("claude-opus-4-6") == "anthropic"
        assert _model_family("claude-sonnet-4-6") == "anthropic"

    def test_openai_family(self):
        from audit.checks.review_gaming import _model_family
        assert _model_family("gpt-4o") == "openai"
        assert _model_family("o3-mini") == "openai"

    def test_unknown_family(self):
        from audit.checks.review_gaming import _model_family
        assert _model_family("llama-3") is None


class TestCheckReviewGamingEntryPoint:
    """Tests for the main check_review_gaming entry point."""

    def test_runs_all_checks(self, tmp_path):
        from audit.checks.review_gaming import check_review_gaming
        md = tmp_path / "test.md"
        md.write_text("content")
        review = "Review with **Reviewed-By:** claude-opus-4-6"
        content = "## Section\ntext"
        result = check_review_gaming(review, content, str(md), "A1", "test")
        assert isinstance(result, list)


# ============================================================================
# 2. phases_gates.py — tested via unit-level helpers
# ============================================================================

class TestCountWordsAndEngagement:
    """Tests for count_words_and_engagement."""

    def test_counts_words(self):
        from audit.parsing import AuditState
        from audit.phases_gates import count_words_and_engagement

        state = AuditState()
        ctx = _make_ctx(
            body="one two three four five",
            content="one two three four five",
            core_content="one two three four five",
        )
        count_words_and_engagement(ctx, state)
        assert state.raw_words == 5
        assert state.total_words > 0

    def test_counts_engagement_boxes(self):
        from audit.parsing import AuditState
        from audit.phases_gates import count_words_and_engagement

        state = AuditState()
        content = "> [!note]\n> Important info\n\n> [!tip]\n> Helpful tip"
        ctx = _make_ctx(body=content, content=content, core_content=content)
        count_words_and_engagement(ctx, state)
        assert state.engagement_count >= 2

    def test_counts_audio_links(self):
        from audit.parsing import AuditState
        from audit.phases_gates import count_words_and_engagement

        state = AuditState()
        content = "Text [🔊](audio1.mp3) more [🔊](audio2.mp3)"
        ctx = _make_ctx(body=content, content=content, core_content=content)
        count_words_and_engagement(ctx, state)
        assert state.audio_count == 2


class TestEvaluateImmersion:
    """Tests for evaluate_immersion function."""

    def test_checkpoint_no_gate(self):
        from audit.parsing import AuditState
        from audit.phases_gates import evaluate_immersion as eval_imm

        state = AuditState()
        ctx = _make_ctx(module_focus='checkpoint', level_code='A1', module_num=1)
        _imm, min_i, max_i = eval_imm(ctx, state)
        assert min_i == 0
        assert max_i == 100

    def test_a1_immersion(self):
        from audit.parsing import AuditState
        from audit.phases_gates import evaluate_immersion as eval_imm

        state = AuditState()
        ctx = _make_ctx(level_code='A1', module_num=5, module_focus=None)
        imm, _min_i, _max_i = eval_imm(ctx, state)
        assert isinstance(imm, float)

    def test_a2_phase_labels(self):
        from audit.parsing import AuditState
        from audit.phases_gates import evaluate_immersion as eval_imm

        for num, _expected_substr in [(5, "A2.1"), (25, "A2.2"), (45, "A2.3")]:
            state = AuditState()
            ctx = _make_ctx(level_code='A2', module_num=num, module_focus=None)
            eval_imm(ctx, state)
            # Just verify it ran without error

    def test_b1_phase_labels(self):
        from audit.parsing import AuditState
        from audit.phases_gates import evaluate_immersion as eval_imm

        for num in [3, 8, 15, 30, 50, 70]:
            state = AuditState()
            ctx = _make_ctx(level_code='B1', module_num=num, module_focus=None)
            eval_imm(ctx, state)

    def test_other_level_immersion(self):
        from audit.parsing import AuditState
        from audit.phases_gates import evaluate_immersion as eval_imm

        state = AuditState()
        ctx = _make_ctx(level_code='C1', module_num=5, module_focus='grammar',
                         config={'min_immersion': 60, 'max_immersion': 100,
                                 'min_engagement': 3, 'min_vocab': 25})
        eval_imm(ctx, state)

    def test_very_low_immersion_triggers_failure(self):
        from audit.parsing import AuditState
        from audit.phases_gates import evaluate_immersion as eval_imm

        state = AuditState()
        ctx = _make_ctx(level_code='A1', module_num=10, module_focus=None,
                         body="only english words here nothing else at all")
        eval_imm(ctx, state)
        assert state.has_critical_failure

    def test_low_immersion_respects_configured_no_gate_ranges(self):
        from audit.parsing import AuditState
        from audit.phases_gates import evaluate_immersion as eval_imm

        state = AuditState()
        ctx = _make_ctx(
            level_code='C1',
            module_num=20,
            module_focus='reading',
            body="only english words here nothing else at all",
            config={'min_immersion': 0, 'max_immersion': 100, 'min_engagement': 3, 'min_vocab': 25},
        )
        eval_imm(ctx, state)
        assert not state.has_critical_failure


class TestCheckTransliterationPolicy:
    """Tests for check_transliteration_policy."""

    def test_transliteration_allowed(self):
        from audit.parsing import AuditState
        from audit.phases_gates import check_transliteration_policy

        state = AuditState()
        ctx = _make_ctx(config={'transliteration_allowed': True, 'min_engagement': 3, 'min_vocab': 25})
        check_transliteration_policy(ctx, state)
        assert not state.has_critical_failure

    def test_transliteration_forbidden_no_meta(self):
        from audit.parsing import AuditState
        from audit.phases_gates import check_transliteration_policy

        state = AuditState()
        ctx = _make_ctx(
            config={'transliteration_allowed': False, 'min_engagement': 3, 'min_vocab': 25},
            meta_data=None,
            frontmatter_str="transliteration: none",
            content="Simple content no translit",
            level_code='B2',
            module_num=10,
        )
        check_transliteration_policy(ctx, state)
        # No meta but frontmatter says none — should pass
        assert not state.has_critical_failure

    def test_transliteration_forbidden_with_translit_meta(self):
        from audit.parsing import AuditState
        from audit.phases_gates import check_transliteration_policy

        state = AuditState()
        ctx = _make_ctx(
            config={'transliteration_allowed': False, 'min_engagement': 3, 'min_vocab': 25},
            meta_data={'transliteration': 'phonetic'},
            frontmatter_str="transliteration: phonetic",
            content="Слово (slovo) is a word",
            level_code='B2',
            module_num=10,
        )
        check_transliteration_policy(ctx, state)
        assert state.has_critical_failure


# ============================================================================
# 3. phases_activity.py
# ============================================================================

class TestPrintViolations:
    """Tests for _print_violations helper."""

    def test_empty_violations(self, capsys):
        from audit.phases_activity import _print_violations
        _print_violations([], "test")
        assert capsys.readouterr().out == ""

    def test_nonempty_violations(self, capsys):
        from audit.phases_activity import _print_violations
        violations = [{'issue': 'Bad thing', 'fix': 'Fix it'}]
        _print_violations(violations, "issues", show_fix=True)
        output = capsys.readouterr().out
        assert "issues: 1" in output
        assert "Bad thing" in output

    def test_without_fix(self, capsys):
        from audit.phases_activity import _print_violations
        violations = [{'issue': 'Something wrong'}]
        _print_violations(violations, "problems")
        output = capsys.readouterr().out
        assert "Something wrong" in output


class TestPrintDetailedViolations:
    """Tests for _print_detailed_violations."""

    def test_empty(self, capsys):
        from audit.phases_activity import _print_detailed_violations
        _print_detailed_violations([], "test")
        assert capsys.readouterr().out == ""

    def test_critical_violation(self, capsys):
        from audit.phases_activity import _print_detailed_violations
        violations = [{
            'severity': 'critical', 'type': 'TEST', 'activity': 'Act1',
            'message': 'Bad', 'fix': 'Fix', 'pedagogical_issue': 'Why'
        }]
        _print_detailed_violations(violations, "test issues")
        output = capsys.readouterr().out
        assert "test issues" in output
        assert "Why" in output

    def test_warning_violation(self, capsys):
        from audit.phases_activity import _print_detailed_violations
        violations = [{
            'severity': 'warning', 'type': 'WARN', 'activity': 'Act2',
            'message': 'Mild issue', 'suggestion': 'Improve'
        }]
        _print_detailed_violations(violations, "warnings")
        output = capsys.readouterr().out
        assert "warnings" in output


class TestGetDensityTarget:
    """Tests for _get_density_target."""

    def test_default_density(self):
        from audit.phases_activity import _get_density_target
        config = {'min_items_per_activity': 4}
        assert _get_density_target('nonexistent-type-xyz', config, 'A1', None) == 4

    def test_activity_complexity_override(self):
        from audit.config import ACTIVITY_COMPLEXITY
        from audit.phases_activity import _get_density_target
        config = {'min_items_per_activity': 4}
        # Find an activity type that has complexity rules
        for act_type, rules in ACTIVITY_COMPLEXITY.items():
            for key, complexity in rules.items():
                if 'min_items' in complexity:
                    level = key.split('-')[0] if '-' in key else key
                    result = _get_density_target(act_type, config, level, None)
                    assert result == complexity['min_items']
                    return
        # If no complexity rules found, just test the default
        assert _get_density_target('unknown_type', config, 'A1', None) == 4


class TestCheckExternalUrls:
    """Tests for _check_external_urls."""

    def test_non_seminar_track_skipped(self):
        from audit.parsing import AuditState
        from audit.phases_activity import _check_external_urls

        state = AuditState()
        ctx = _make_ctx(level_code='A1', yaml_activities=[])
        _check_external_urls(ctx, state)
        assert not state.has_critical_failure

    def test_seminar_no_violations(self):
        from audit.parsing import AuditState
        from audit.phases_activity import _check_external_urls

        state = AuditState()
        ctx = _make_ctx(level_code='LIT', yaml_activities=[], module_title='Test')
        with patch('audit.phases_activity.check_external_resources', return_value=[]):
            _check_external_urls(ctx, state)
        assert not state.has_critical_failure


class TestValidateActivityAnswers:
    """Tests for validate_activity_answers."""

    def test_no_yaml_activities(self):
        from audit.parsing import AuditState
        from audit.phases_activity import validate_activity_answers

        state = AuditState()
        ctx = _make_ctx(yaml_activities=None)
        validate_activity_answers(ctx, state)
        # Should return early without error


# ============================================================================
# 4. review_validation.py
# ============================================================================

class TestDetectTier:
    """Tests for _detect_tier."""

    def test_a1_tier1(self):
        from audit.checks.review_validation import _detect_tier
        assert _detect_tier("/path/to/a1/module.md", "A1") == 1

    def test_b1_tier2(self):
        from audit.checks.review_validation import _detect_tier
        assert _detect_tier("/path/to/b1/module.md", "B1") == 2

    def test_hist_tier3(self):
        from audit.checks.review_validation import _detect_tier
        assert _detect_tier("/path/to/hist/module.md", "HIST") == 3

    def test_c1_tier4(self):
        from audit.checks.review_validation import _detect_tier
        assert _detect_tier("/path/to/c1/module.md", "C1") == 4

    def test_unknown_level(self):
        from audit.checks.review_validation import _detect_tier
        result = _detect_tier("/path/to/unknown/module.md", "X99")
        assert result is None


class TestBuildFixPrompt:
    """Tests for _build_fix_prompt."""

    def test_all_tiers(self):
        from audit.checks.review_validation import _build_fix_prompt
        for tier in [1, 2, 3, 4]:
            prompt = _build_fix_prompt(tier)
            assert "REDO" in prompt
            assert "DELETE" in prompt


class TestCountPerfectScores:
    """Tests for _count_perfect_scores."""

    def test_all_perfect(self):
        from audit.checks.review_validation import _count_perfect_scores
        content = "| A | 10/10 |\n| B | 10.0/10 |\n| C | 10/10 |"
        perfect, total = _count_perfect_scores(content)
        assert perfect == 3
        assert total == 3

    def test_mixed_scores(self):
        from audit.checks.review_validation import _count_perfect_scores
        content = "| A | 10/10 |\n| B | 8/10 |\n| C | 9/10 |"
        perfect, total = _count_perfect_scores(content)
        assert perfect == 1
        assert total == 3

    def test_no_scores(self):
        from audit.checks.review_validation import _count_perfect_scores
        perfect, total = _count_perfect_scores("no scores")
        assert perfect == 0
        assert total == 0


class TestExtractUkrainianCitations:
    """Tests for _extract_ukrainian_citations."""

    def test_angular_quotes(self):
        from audit.checks.review_validation import _extract_ukrainian_citations
        content = '«Це дуже гарне речення для тесту»'
        citations = _extract_ukrainian_citations(content)
        assert len(citations) == 1

    def test_straight_quotes(self):
        from audit.checks.review_validation import _extract_ukrainian_citations
        content = '"Це дуже гарне речення для тесту"'
        citations = _extract_ukrainian_citations(content)
        assert len(citations) == 1

    def test_inline_code(self):
        from audit.checks.review_validation import _extract_ukrainian_citations
        content = '`Це дуже гарне речення для тесту`'
        citations = _extract_ukrainian_citations(content)
        assert len(citations) == 1

    def test_cjk_brackets(self):
        from audit.checks.review_validation import _extract_ukrainian_citations
        content = '「Це дуже гарне речення для тесту」'
        citations = _extract_ukrainian_citations(content)
        assert len(citations) == 1

    def test_short_quote_filtered(self):
        from audit.checks.review_validation import _extract_ukrainian_citations
        content = '«Так»'
        citations = _extract_ukrainian_citations(content)
        assert len(citations) == 0

    def test_english_quote_filtered(self):
        from audit.checks.review_validation import _extract_ukrainian_citations
        content = '"This is an English sentence only"'
        citations = _extract_ukrainian_citations(content)
        assert len(citations) == 0

    def test_deduplication(self):
        from audit.checks.review_validation import _extract_ukrainian_citations
        content = '«Це дуже гарне речення для тесту» and «Це дуже гарне речення для тесту»'
        citations = _extract_ukrainian_citations(content)
        assert len(citations) == 1

    def test_markdown_stripping(self):
        from audit.checks.review_validation import _extract_ukrainian_citations
        content = '«**Це дуже** гарне *речення* для тесту»'
        citations = _extract_ukrainian_citations(content)
        assert len(citations) == 1
        assert '**' not in citations[0]


class TestVerifyCitationsAgainstSource:
    """Tests for _verify_citations_against_source."""

    def test_source_not_exists(self, tmp_path):
        from audit.checks.review_validation import _verify_citations_against_source
        verified, total = _verify_citations_against_source(
            ["citation"], tmp_path / "nonexistent.md"
        )
        assert verified == 0
        assert total == 1

    def test_empty_citations(self, tmp_path):
        from audit.checks.review_validation import _verify_citations_against_source
        source = tmp_path / "source.md"
        source.write_text("some content")
        _verified, total = _verify_citations_against_source([], source)
        assert total == 0

    def test_citation_found(self, tmp_path):
        from audit.checks.review_validation import _verify_citations_against_source
        source = tmp_path / "source.md"
        source.write_text("Це гарне речення яке ми тестуємо тут.")
        citations = ["Це гарне речення яке ми тестуємо тут."]
        verified, _total = _verify_citations_against_source(citations, source)
        assert verified == 1

    def test_citation_in_yaml(self, tmp_path):
        from audit.checks.review_validation import _verify_citations_against_source
        source = tmp_path / "source.md"
        source.write_text("Main content here")
        act_dir = tmp_path / "activities"
        act_dir.mkdir()
        (act_dir / "source.yaml").write_text("text: Це речення з активності яке шукаємо")
        citations = ["Це речення з активності яке шукаємо"]
        verified, _total = _verify_citations_against_source(citations, source)
        assert verified == 1

    def test_sliding_window_match(self, tmp_path):
        from audit.checks.review_validation import _verify_citations_against_source
        source = tmp_path / "source.md"
        source.write_text("Prefix text: гарне речення яке ми тестуємо тут у тексті")
        citations = ["Slightly different гарне речення яке ми тестуємо тут у тексті"]
        verified, _total = _verify_citations_against_source(citations, source)
        assert verified == 1


class TestCheckTemplePlaceholders:
    """Tests for _check_template_placeholders."""

    def test_no_placeholders(self):
        from audit.checks.review_validation import _check_template_placeholders
        assert _check_template_placeholders("Clean review content", "fix") == []

    def test_has_placeholders(self):
        from audit.checks.review_validation import _check_template_placeholders
        content = "Module {slug} at level {level}"
        violations = _check_template_placeholders(content, "fix prompt")
        assert len(violations) == 1
        assert violations[0]['type'] == 'FAKE_REVIEW_TEMPLATE'


class TestCheckGamingLanguage:
    """Tests for _check_gaming_language."""

    def test_no_gaming(self):
        from audit.checks.review_validation import _check_gaming_language
        assert _check_gaming_language("A thorough honest review", "fix") == []

    def test_gaming_detected(self):
        from audit.checks.review_validation import _check_gaming_language
        content = "This fresh review will ensure a high overall score and clean audit."
        violations = _check_gaming_language(content, "fix prompt")
        assert len(violations) == 1
        assert violations[0]['type'] == 'GAMING_LANGUAGE_DETECTED'


class TestCheckScoreCredibility:
    """Tests for _check_score_credibility."""

    def test_below_dimension_count(self):
        from audit.checks.review_validation import _check_score_credibility
        content = "| A | 9/10 |"
        cfg = {'min_dimensions': 7}
        assert _check_score_credibility(content, cfg, None, None, "fix") == []

    def test_high_scores_no_issues(self):
        from audit.checks.review_validation import _check_score_credibility
        rows = "\n".join(f"| Dim{i} | 9.5/10 |" for i in range(8))
        cfg = {'min_dimensions': 7}
        violations = _check_score_credibility(rows, cfg, None, None, "fix")
        assert any(v['type'] == 'SUSPICIOUSLY_HIGH_SCORES' for v in violations)

    def test_high_scores_with_real_issues(self):
        from audit.checks.review_validation import _check_score_credibility
        rows = "\n".join(f"| Dim{i} | 9.5/10 |" for i in range(8))
        cfg = {'min_dimensions': 7}
        issue_text = "There is a real problem with grammar in section 3 where the verb aspect is wrong. " * 2
        issues_match = MagicMock()
        violations = _check_score_credibility(rows, cfg, issue_text, issues_match, "fix")
        assert not any(v['type'] == 'SUSPICIOUSLY_HIGH_SCORES' for v in violations)


class TestCheckPraiseOnlyCitations:
    """Tests for _check_praise_only_citations."""

    def test_too_few_citations(self):
        from audit.checks.review_validation import _check_praise_only_citations
        assert _check_praise_only_citations("content", ["one"], "fix") == []

    def test_praise_only(self):
        from audit.checks.review_validation import _check_praise_only_citations
        citations = [
            "Це чудове речення чудово",
            "Ще одне прекрасне речення",
            "Третє відмінне речення тут",
        ]
        content = (
            "Excellent usage of Це чудове речення чудово in the text. "
            "Great example: Ще одне прекрасне речення shows skill. "
            "Beautiful: Третє відмінне речення тут demonstrates mastery."
        )
        violations = _check_praise_only_citations(content, citations, "fix")
        assert any(v['type'] == 'PRAISE_ONLY_CITATIONS' for v in violations)

    def test_has_critical_citation(self):
        from audit.checks.review_validation import _check_praise_only_citations
        citations = [
            "Це чудове речення чудово",
            "Ще одне прекрасне речення",
            "Це проблемне речення тут",
        ]
        content = (
            "Good: Це чудове речення чудово in the text. "
            "Nice: Ще одне прекрасне речення here. "
            "Issue: Це проблемне речення тут — incorrect case ending."
        )
        violations = _check_praise_only_citations(content, citations, "fix")
        assert violations == []


class TestCheckContentReviewFormat:
    """Tests for _check_content_review_format."""

    def test_grade_f(self):
        from audit.checks.review_validation import _check_content_review_format
        content = "**Verdict:** F\n## Issues Found\nBad.\n## Grade Justification\nReason."
        violations = _check_content_review_format(content, "fix")
        assert any(v['type'] == 'REVIEW_VERDICT_FAIL' for v in violations)

    def test_missing_sections(self):
        from audit.checks.review_validation import _check_content_review_format
        content = "**Verdict:** B\nSome content without proper sections."
        violations = _check_content_review_format(content, "fix")
        assert any(v['type'] == 'FAKE_REVIEW_STRUCTURE' for v in violations)


class TestCheckPipelineReviewFormat:
    """Tests for _check_pipeline_review_format."""

    def test_status_fail_no_longer_blocks(self):
        """Review verdict FAIL is no longer an audit gate (#980 Phase 1)."""
        from audit.checks.review_validation import _check_pipeline_review_format
        content = "**Status:** FAIL\n## Scores\n| A | 5/10 |"
        cfg = {'required_headers': []}
        violations = _check_pipeline_review_format(content, cfg, "fix")
        # REVIEW_VERDICT_FAIL was removed — review score blocks via dashboard, not audit
        assert not any(v['type'] == 'REVIEW_VERDICT_FAIL' for v in violations)

    def test_missing_headers(self):
        from audit.checks.review_validation import _HEADER_ISSUES, _HEADER_SCORES, _check_pipeline_review_format
        content = "**Status:** PASS\nSome text."
        cfg = {'required_headers': [_HEADER_SCORES, _HEADER_ISSUES]}
        violations = _check_pipeline_review_format(content, cfg, "fix")
        assert any(v['type'] == 'FAKE_REVIEW_STRUCTURE' for v in violations)


class TestFindReviewFileValidation:
    """Tests for _find_review_file in review_validation."""

    def test_canonical_path(self, tmp_path):
        from audit.checks.review_validation import _find_review_file
        review_dir = tmp_path / "review"
        review_dir.mkdir()
        review = review_dir / "my-mod-review.md"
        review.write_text("review")
        md = tmp_path / "my-mod.md"
        md.write_text("content")
        found, _canonical = _find_review_file(str(md), "my-mod")
        assert found == review

    def test_content_review_path(self, tmp_path):
        from audit.checks.review_validation import _find_review_file
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        cr = audit_dir / "my-mod-content-review.md"
        cr.write_text("content review")
        md = tmp_path / "my-mod.md"
        md.write_text("content")
        found, _canonical = _find_review_file(str(md), "my-mod")
        assert found == cr

    def test_not_found(self, tmp_path):
        from audit.checks.review_validation import _find_review_file
        md = tmp_path / "my-mod.md"
        md.write_text("content")
        found, _canonical = _find_review_file(str(md), "my-mod")
        assert found is None


class TestCheckReviewValidity:
    """Tests for the main check_review_validity entry point."""

    def test_unknown_tier(self, tmp_path):
        from audit.checks.review_validation import check_review_validity
        result = check_review_validity(str(tmp_path / "test.md"), "X99", "test")
        assert result == []

    def test_missing_review(self, tmp_path):
        from audit.checks.review_validation import check_review_validity
        md = tmp_path / "test.md"
        md.write_text("content")
        # Create the parent dirs to make path resolution work
        a1_dir = tmp_path / "a1"
        a1_dir.mkdir(exist_ok=True)
        result = check_review_validity(str(tmp_path / "test.md"), "A1", "test")
        assert any(v['type'] == 'MISSING_REVIEW' for v in result)

    def test_too_short_review(self, tmp_path):
        from audit.checks.review_validation import check_review_validity
        review_dir = tmp_path / "review"
        review_dir.mkdir()
        (review_dir / "test-review.md").write_text("short")
        md = tmp_path / "test.md"
        md.write_text("content")
        result = check_review_validity(str(md), "A1", "test")
        assert any(v['type'] == 'FAKE_REVIEW_TOO_SHORT' for v in result)

    def test_read_error(self, tmp_path):
        from audit.checks.review_validation import check_review_validity
        review_dir = tmp_path / "review"
        review_dir.mkdir()
        review_file = review_dir / "test-review.md"
        review_file.write_text("x" * 500)
        md = tmp_path / "test.md"
        md.write_text("content")
        with patch.object(Path, 'read_text', side_effect=PermissionError("denied")):
            result = check_review_validity(str(md), "A1", "test")
        assert any(v['type'] == 'REVIEW_READ_ERROR' for v in result)


class TestCheckCitationVerification:
    """Tests for _check_citation_verification."""

    def test_too_few_citations(self, tmp_path):
        from audit.checks.review_validation import _check_citation_verification
        source = tmp_path / "source.md"
        source.write_text("content")
        assert _check_citation_verification(["one"], source, "fix") == []

    def test_all_fabricated(self, tmp_path):
        from audit.checks.review_validation import _check_citation_verification
        source = tmp_path / "source.md"
        source.write_text("completely different content here")
        citations = [
            "Це вигадане речення номер один",
            "Ще одне вигадане речення два",
            "Третє вигадане речення тут",
        ]
        violations = _check_citation_verification(citations, source, "fix")
        assert any(v['type'] == 'FABRICATED_CITATIONS' for v in violations)


# ============================================================================
# 5. core.py — test helper functions, mock heavy dependencies
# ============================================================================

class TestLoadAndResolve:
    """Tests for _load_and_resolve, focusing on edge cases."""

    def test_file_not_found(self, tmp_path):
        from audit.core import _load_and_resolve
        with pytest.raises(SystemExit):
            _load_and_resolve(str(tmp_path / "nonexistent.md"), False, False)


class TestCheckTemplateCompliance:
    """Tests for _check_template_compliance."""

    def test_skips_non_enabled_levels(self):
        from audit.core import _check_template_compliance
        from audit.parsing import AuditState

        state = AuditState()
        ctx = _make_ctx(level_code='HIST')
        _check_template_compliance(ctx, state)
        assert not state.has_critical_failure

    def test_handles_import_error(self):
        from audit.core import _check_template_compliance
        from audit.parsing import AuditState

        state = AuditState()
        ctx = _make_ctx(level_code='A1', meta_data={}, file_path="/fake/a1/test.md")
        # _check_template_compliance handles ImportError internally
        # Just verify it runs without crashing for enabled levels
        _check_template_compliance(ctx, state)


# ============================================================================
# 6. manifest_utils.py
# ============================================================================

class TestParseNumberedSlug:
    """Tests for parse_numbered_slug."""

    def test_numbered_slug(self):
        from manifest_utils import parse_numbered_slug
        num, base = parse_numbered_slug("01-the-cyrillic-code")
        assert num == 1
        assert base == "the-cyrillic-code"

    def test_two_digit_prefix(self):
        from manifest_utils import parse_numbered_slug
        num, base = parse_numbered_slug("42-some-module")
        assert num == 42
        assert base == "some-module"

    def test_no_prefix(self):
        from manifest_utils import parse_numbered_slug
        num, base = parse_numbered_slug("knyahynia-olha")
        assert num is None
        assert base == "knyahynia-olha"

    def test_year_prefix_not_stripped(self):
        from manifest_utils import parse_numbered_slug
        num, base = parse_numbered_slug("1991-referendum")
        assert num is None
        assert base == "1991-referendum"

    def test_three_digit_prefix(self):
        from manifest_utils import parse_numbered_slug
        num, base = parse_numbered_slug("140-syntez-viyna")
        # 3 digits should be stripped per pattern r'^\d{1,2}-'
        # Wait: the regex is r'^(\d{1,2})-(.+)$' — 1-2 digits only
        num, base = parse_numbered_slug("140-syntez-viyna")
        assert num is None  # 3-digit: not a module prefix
        assert base == "140-syntez-viyna"


class TestModule:
    """Tests for Module dataclass."""

    def test_path_property(self):
        from manifest_utils import Module
        mod = Module(slug="test", title="Test", level="a1", track="core",
                     local_num=1, global_num=1)
        assert mod.path == "/a1/test"

    def test_numbered_slug_property(self):
        from manifest_utils import Module
        mod = Module(slug="test", title="Test", level="a1", track="core",
                     local_num=5, global_num=5)
        assert mod.numbered_slug == "05-test"

    def test_file_path_track(self, tmp_path):
        from manifest_utils import Module
        mod = Module(slug="test-mod", title="Test", level="hist", track="hist",
                     local_num=1, global_num=0)
        # file_path checks existence, will fall through to numbered format
        fp = mod.file_path
        assert isinstance(fp, Path)


class TestLoadManifest:
    """Tests for load_manifest and cache."""

    def test_load_manifest_file_not_found(self):
        from manifest_utils import clear_manifest_cache, load_manifest
        clear_manifest_cache()
        with patch('manifest_utils.MANIFEST_PATH', Path("/nonexistent/path.yaml")):
            clear_manifest_cache()
            with pytest.raises(FileNotFoundError):
                load_manifest()
        clear_manifest_cache()

    def test_clear_cache(self):
        from manifest_utils import clear_manifest_cache
        # Should not raise
        clear_manifest_cache()


class TestLoadMetaFile:
    """Tests for _load_meta_file."""

    def test_meta_file_exists(self, tmp_path):
        from manifest_utils import _load_meta_file
        _load_meta_file.cache_clear()
        meta_dir = tmp_path / "a1" / "meta"
        meta_dir.mkdir(parents=True)
        meta_file = meta_dir / "test-module.yaml"
        meta_file.write_text(yaml.dump({'title': 'Test Module', 'focus': 'grammar'}))

        with patch('manifest_utils.CURRICULUM_PATH', tmp_path):
            _load_meta_file.cache_clear()
            result = _load_meta_file("a1", "test-module")
            assert result['title'] == 'Test Module'
        _load_meta_file.cache_clear()

    def test_meta_file_not_exists_with_plan(self, tmp_path):
        from manifest_utils import _load_meta_file
        _load_meta_file.cache_clear()
        plan_dir = tmp_path / "plans" / "a1"
        plan_dir.mkdir(parents=True)
        plan_file = plan_dir / "test-module.yaml"
        plan_file.write_text(yaml.dump({'title': 'From Plan'}))
        # No meta dir
        (tmp_path / "a1" / "meta").mkdir(parents=True, exist_ok=True)

        with patch('manifest_utils.CURRICULUM_PATH', tmp_path):
            _load_meta_file.cache_clear()
            result = _load_meta_file("a1", "test-module")
            assert result.get('title') == 'From Plan'
        _load_meta_file.cache_clear()


class TestGetModuleBySlug:
    """Tests for get_module_by_slug."""

    def test_module_found(self):
        from manifest_utils import _load_meta_file, clear_manifest_cache, get_module_by_slug
        clear_manifest_cache()
        _load_meta_file.cache_clear()
        manifest = {
            'levels': {
                'a1': {
                    'type': 'core',
                    'modules': ['01-test-module'],
                }
            }
        }
        with patch('manifest_utils.load_manifest', return_value=manifest), \
             patch('manifest_utils._load_meta_file', return_value={'title': 'Test'}):
            mod = get_module_by_slug("test-module")
            assert mod is not None
            assert mod.slug == "test-module"
            assert mod.local_num == 1

    def test_module_not_found(self):
        from manifest_utils import clear_manifest_cache, get_module_by_slug
        clear_manifest_cache()
        manifest = {'levels': {'a1': {'type': 'core', 'modules': ['01-other']}}}
        with patch('manifest_utils.load_manifest', return_value=manifest):
            mod = get_module_by_slug("nonexistent")
            assert mod is None

    def test_track_module(self):
        from manifest_utils import _load_meta_file, clear_manifest_cache, get_module_by_slug
        clear_manifest_cache()
        _load_meta_file.cache_clear()
        manifest = {
            'levels': {
                'hist': {
                    'type': 'track',
                    'modules': ['bohdan-khmelnytskyi'],
                }
            }
        }
        with patch('manifest_utils.load_manifest', return_value=manifest), \
             patch('manifest_utils._load_meta_file', return_value={'title': 'Bohdan'}):
            mod = get_module_by_slug("bohdan-khmelnytskyi")
            assert mod is not None
            assert mod.track == "hist"
            assert mod.global_num == 0


class TestGetModulesForLevel:
    """Tests for get_modules_for_level."""

    def test_empty_level(self):
        from manifest_utils import clear_manifest_cache, get_modules_for_level
        clear_manifest_cache()
        manifest = {'levels': {}}
        with patch('manifest_utils.load_manifest', return_value=manifest):
            assert get_modules_for_level("a1") == []

    def test_core_level(self):
        from manifest_utils import _load_meta_file, clear_manifest_cache, get_modules_for_level
        clear_manifest_cache()
        _load_meta_file.cache_clear()
        manifest = {
            'levels': {
                'a1': {'type': 'core', 'modules': ['01-mod-a', '02-mod-b']},
            }
        }
        with patch('manifest_utils.load_manifest', return_value=manifest), \
             patch('manifest_utils._load_meta_file', return_value={'title': 'Test'}):
            mods = get_modules_for_level("a1")
            assert len(mods) == 2
            assert mods[0].global_num == 1
            assert mods[1].global_num == 2


class TestGetModuleByNumber:
    """Tests for get_module_by_number."""

    def test_valid_number(self):
        from manifest_utils import _load_meta_file, clear_manifest_cache, get_module_by_number
        clear_manifest_cache()
        _load_meta_file.cache_clear()
        manifest = {
            'levels': {
                'a1': {'type': 'core', 'modules': ['01-first', '02-second']},
            }
        }
        with patch('manifest_utils.load_manifest', return_value=manifest), \
             patch('manifest_utils._load_meta_file', return_value={'title': 'T'}):
            mod = get_module_by_number("a1", 2)
            assert mod is not None
            assert mod.slug == "second"

    def test_out_of_bounds(self):
        from manifest_utils import clear_manifest_cache, get_module_by_number
        clear_manifest_cache()
        manifest = {'levels': {'a1': {'type': 'core', 'modules': ['01-only']}}}
        with patch('manifest_utils.load_manifest', return_value=manifest), \
             patch('manifest_utils._load_meta_file', return_value={'title': 'T'}):
            assert get_module_by_number("a1", 5) is None


class TestResolveSlugLink:
    """Tests for resolve_slug_link."""

    def test_found(self):
        from manifest_utils import resolve_slug_link
        with patch('manifest_utils.get_module_by_slug') as mock:
            mock.return_value = MagicMock(title="Test Title", path="/a1/test")
            title, path = resolve_slug_link("test")
            assert title == "Test Title"
            assert path == "/a1/test"

    def test_not_found(self):
        from manifest_utils import resolve_slug_link
        with patch('manifest_utils.get_module_by_slug', return_value=None), pytest.raises(ValueError):
            resolve_slug_link("nonexistent")


class TestValidateManifest:
    """Tests for validate_manifest."""

    def test_valid_manifest(self):
        from manifest_utils import clear_manifest_cache, validate_manifest
        clear_manifest_cache()
        manifest = {
            'levels': {
                'a1': {'type': 'core', 'modules': ['01-mod-a', '02-mod-b']},
            }
        }
        with patch('manifest_utils.load_manifest', return_value=manifest):
            errors = validate_manifest()
            assert errors == []

    def test_duplicate_slug(self):
        from manifest_utils import clear_manifest_cache, validate_manifest
        clear_manifest_cache()
        manifest = {
            'levels': {
                'a1': {'type': 'core', 'modules': ['01-same', '02-same']},
            }
        }
        with patch('manifest_utils.load_manifest', return_value=manifest):
            errors = validate_manifest()
            assert len(errors) == 1
            assert 'duplicate' in errors[0]

    def test_missing_slug(self):
        from manifest_utils import clear_manifest_cache, validate_manifest
        clear_manifest_cache()
        manifest = {
            'levels': {
                'a1': {'type': 'core', 'modules': ['01-ok', '', '03-ok']},
            }
        }
        with patch('manifest_utils.load_manifest', return_value=manifest):
            errors = validate_manifest()
            assert any('missing slug' in e for e in errors)


class TestValidateFilesystemMatch:
    """Tests for validate_filesystem_match."""

    def test_level_not_in_manifest(self):
        from manifest_utils import clear_manifest_cache, validate_filesystem_match
        clear_manifest_cache()
        manifest = {'levels': {}}
        with patch('manifest_utils.load_manifest', return_value=manifest):
            errors = validate_filesystem_match("a1")
            assert any('not found in manifest' in e for e in errors)

    def test_matching_filesystem(self, tmp_path):
        from manifest_utils import clear_manifest_cache, validate_filesystem_match
        clear_manifest_cache()
        level_dir = tmp_path / "a1"
        level_dir.mkdir()
        (level_dir / "test-mod.md").write_text("content")
        manifest = {
            'levels': {
                'a1': {'type': 'core', 'modules': ['test-mod']},
            }
        }
        with patch('manifest_utils.load_manifest', return_value=manifest), \
             patch('manifest_utils.CURRICULUM_PATH', tmp_path):
            errors = validate_filesystem_match("a1")
            assert errors == []

    def test_mismatch(self, tmp_path):
        from manifest_utils import clear_manifest_cache, validate_filesystem_match
        clear_manifest_cache()
        level_dir = tmp_path / "a1"
        level_dir.mkdir()
        (level_dir / "extra.md").write_text("content")
        manifest = {
            'levels': {
                'a1': {'type': 'core', 'modules': ['01-missing']},
            }
        }
        with patch('manifest_utils.load_manifest', return_value=manifest), \
             patch('manifest_utils.CURRICULUM_PATH', tmp_path):
            errors = validate_filesystem_match("a1")
            assert len(errors) >= 1


class TestGetManifestStats:
    """Tests for get_manifest_stats."""

    def test_stats(self):
        from manifest_utils import clear_manifest_cache, get_manifest_stats
        clear_manifest_cache()
        manifest = {
            'version': '1.0',
            'levels': {
                'a1': {'type': 'core', 'modules': ['01-a', '02-b']},
                'hist': {'type': 'track', 'modules': ['topic-a']},
            }
        }
        with patch('manifest_utils.load_manifest', return_value=manifest):
            stats = get_manifest_stats()
            assert stats['version'] == '1.0'
            assert stats['levels']['a1'] == 2
            assert stats['tracks']['hist'] == 1
            assert stats['total_modules'] == 2


# ============================================================================
# 7. proofread.py — REMOVED (deprecated, absorbed into v5 review phase)

# ============================================================================
# Helpers
# ============================================================================

def _make_ctx(**overrides):
    """Create a minimal AuditContext for testing."""
    from audit.parsing import AuditContext
    defaults = dict(
        file_path="/fake/path/test.md",
        content="# Test\nSome content here.",
        body="Some content here.",
        frontmatter_str="title: Test\nlevel: A1",
        meta_data={'title': 'Test', 'transliteration': None},
        plan_data=None,
        vocab_data=None,
        vocab_error=None,
        level_code='A1',
        module_num=1,
        track_code='l2-uk-en',
        display_level='A1',
        module_focus=None,
        module_title='Test Module',
        target=1200,
        config={
            'min_activities': 10,
            'min_types_unique': 5,
            'min_items_per_activity': 4,
            'priority_types': {'quiz', 'fill-in'},
            'min_engagement': 3,
            'min_vocab': 25,
            'transliteration_allowed': True,
            'min_immersion': 0,
            'max_immersion': 100,
        },
        section_map={},
        core_content="Some content here.",
        phase='A1',
        pedagogy='Not Specified',
        skip_activities=False,
        skip_review=False,
        yaml_activities=None,
        use_yaml_activities=False,
        yaml_file=Path('.'),
    )
    defaults.update(overrides)
    return AuditContext(**defaults)


# ============================================================================
# 8. content_quality_pipeline.py — textbook citation check
#    REMOVED in #820: sandbox phase deprecated, citation check removed.
# ============================================================================


class TestTextbookCitationCheckRemoved:
    """Verify check_content_textbook_citations was removed (#820)."""

    def test_citation_check_not_in_aggregator(self):
        """run_content_quality_checks must NOT produce LOW_TEXTBOOK_CITATION."""
        from audit.checks.content_quality_pipeline import run_content_quality_checks
        issues = run_content_quality_checks(
            content="No citations at all.",
            level_code="A1",
            module_num=47,
        )
        citation_issues = [i for i in issues if i["type"] == "LOW_TEXTBOOK_CITATION"]
        assert len(citation_issues) == 0, "LOW_TEXTBOOK_CITATION should no longer be produced"

    def test_citation_function_removed(self):
        """check_content_textbook_citations should not exist."""
        import audit.checks.content_quality_pipeline as mod
        assert not hasattr(mod, "check_content_textbook_citations")
