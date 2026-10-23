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
from unittest.mock import patch

import pytest
import yaml

pytestmark = pytest.mark.reads_content

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


class TestCheckScoreUniformity:
    """Tests for check_score_uniformity."""

    def test_uniform_high_scores(self):
        from audit.checks.review_gaming import check_score_uniformity
        rows = "\n".join(f"| Dim{i} | 9.5/10 |" for i in range(6))
        violations = check_score_uniformity(rows)
        assert len(violations) == 1
        assert violations[0]['type'] == 'UNIFORM_HIGH_SCORES'


class TestCheckCitationDensity:
    """Tests for check_citation_density."""

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

    def test_critical_low_coverage(self):
        from audit.checks.review_gaming import check_review_section_coverage
        headers = "\n".join(f"## Topic {i}\nsome text" for i in range(5))
        review = "This review talks about unrelated things."
        violations = check_review_section_coverage(review, headers)
        assert any(v['type'] == 'REVIEW_LOW_SECTION_COVERAGE' for v in violations)

    def test_partial_word_matching(self):
        from audit.checks.review_gaming import check_review_section_coverage
        content = "## Дієслова руху\ntext\n## Умовний спосіб\ntext\n## Активні дієприкметники\ntext\n## Пасивний стан\ntext"
        review = "The дієслова руху section is complete. The умовний спосіб part works well. Активні дієприкметники are covered. Пасивний стан needs work."
        violations = check_review_section_coverage(review, content)
        assert not any(v['severity'] == 'critical' for v in violations)


class TestCheckScoreDrift:
    """Tests for check_score_drift."""

    def test_fallback_high_mean(self, tmp_path):
        from audit.checks.review_gaming import check_score_drift
        rows = "\n".join(f"| Dim{i} | 9.5/10 |" for i in range(6))
        md = tmp_path / "test.md"
        md.write_text("content")
        violations = check_score_drift(rows, str(md), "test")
        assert len(violations) == 1
        assert violations[0]['type'] == 'SCORE_DRIFT_OUTLIER'

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


class TestCheckReviewSectionReferences:
    """Tests for check_review_section_references."""

    def test_phantom_reference(self):
        from audit.checks.review_gaming import check_review_section_references
        review = 'Section "Nonexistent Section" has problems.'
        content = "## Grammar\ntext\n## Vocab\nmore\n## Practice\nmore"
        violations = check_review_section_references(review, content)
        assert len(violations) == 1
        assert violations[0]['type'] == 'PHANTOM_SECTION_REFERENCE'


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


class TestModelFamily:
    """Tests for _model_family."""

    def test_anthropic_family(self):
        from audit.checks.review_gaming import _model_family
        assert _model_family("claude-opus-4-6") == "anthropic"
        assert _model_family("claude-sonnet-4-6") == "anthropic"

    def test_unknown_family(self):
        from audit.checks.review_gaming import _model_family
        assert _model_family("llama-3") is None


# ============================================================================
# 2. phases_gates.py — tested via unit-level helpers
# ============================================================================


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
            # Just verify it ran without error

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
        # Should return early without error


# ============================================================================
# 4. review_validation.py
# ============================================================================


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

    def test_has_placeholders(self):
        from audit.checks.review_validation import _check_template_placeholders
        content = "Module {slug} at level {level}"
        violations = _check_template_placeholders(content, "fix prompt")
        assert len(violations) == 1
        assert violations[0]['type'] == 'FAKE_REVIEW_TEMPLATE'


class TestCheckGamingLanguage:
    """Tests for _check_gaming_language."""

    def test_gaming_detected(self):
        from audit.checks.review_validation import _check_gaming_language
        content = "This fresh review will ensure a high overall score and clean audit."
        violations = _check_gaming_language(content, "fix prompt")
        assert len(violations) == 1
        assert violations[0]['type'] == 'GAMING_LANGUAGE_DETECTED'


class TestCheckScoreCredibility:
    """Tests for _check_score_credibility."""

    def test_high_scores_no_issues(self):
        from audit.checks.review_validation import _check_score_credibility
        rows = "\n".join(f"| Dim{i} | 9.5/10 |" for i in range(8))
        cfg = {'min_dimensions': 7}
        violations = _check_score_credibility(rows, cfg, None, None, "fix")
        assert any(v['type'] == 'SUSPICIOUSLY_HIGH_SCORES' for v in violations)


class TestCheckPraiseOnlyCitations:
    """Tests for _check_praise_only_citations."""

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


class TestCheckReviewValidity:
    """Tests for the main check_review_validity entry point."""

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


# ============================================================================
# 6. manifest_utils.py
# ============================================================================


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
