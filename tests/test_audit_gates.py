"""
Tests for audit gate evaluation functions.

Tests all gate functions in scripts/audit/gates.py.
These are pure functions with no I/O dependencies.

Run with: pytest tests/test_audit_gates.py -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.audit.gates import (
    GateResult,
    evaluate_word_count,
    evaluate_activity_count,
    evaluate_density,
    evaluate_unique_types,
    evaluate_priority_types,
    evaluate_engagement,
    evaluate_audio,
    evaluate_vocab,
    evaluate_structure,
    evaluate_lint,
    evaluate_pedagogy,
    evaluate_immersion,
    evaluate_naturalness,
    evaluate_content_heavy,
    compute_recommendation,
)


# =============================================================================
# TEST: evaluate_word_count
# =============================================================================

class TestEvaluateWordCount:
    def test_pass_at_target(self):
        result = evaluate_word_count(3000, 3000)
        assert result.status == 'PASS'
        assert '3000/3000' in result.msg

    def test_pass_above_target(self):
        result = evaluate_word_count(3500, 3000)
        assert result.status == 'PASS'

    def test_warn_slightly_below(self):
        result = evaluate_word_count(2950, 3000)
        assert result.status == 'WARN'
        assert '50 short' in result.msg

    def test_fail_far_below(self):
        result = evaluate_word_count(2800, 3000)
        assert result.status == 'FAIL'

    def test_raw_words_displayed(self):
        result = evaluate_word_count(2500, 3000, raw_words=2800)
        assert 'raw: 2800' in result.msg

    def test_raw_words_not_shown_when_equal(self):
        result = evaluate_word_count(3000, 3000, raw_words=3000)
        assert 'raw' not in result.msg


# =============================================================================
# TEST: evaluate_activity_count
# =============================================================================

class TestEvaluateActivityCount:
    def test_pass_at_target(self):
        result = evaluate_activity_count(6, 6)
        assert result.status == 'PASS'

    def test_pass_above_target(self):
        result = evaluate_activity_count(10, 6)
        assert result.status == 'PASS'

    def test_fail_below_target(self):
        result = evaluate_activity_count(3, 6)
        assert result.status == 'FAIL'
        assert '3/6' in result.msg


# =============================================================================
# TEST: evaluate_density
# =============================================================================

class TestEvaluateDensity:
    def test_pass_all_above_threshold(self):
        result = evaluate_density(0, 6, 5, 6)
        assert result.status == 'PASS'

    def test_fail_some_below(self):
        result = evaluate_density(2, 6, 5, 6)
        assert result.status == 'FAIL'
        assert '2' in result.msg

    def test_pass_zero_target(self):
        """Zero activity target with zero total = PASS."""
        result = evaluate_density(0, 0, 5, 0)
        assert result.status == 'PASS'


# =============================================================================
# TEST: evaluate_unique_types
# =============================================================================

class TestEvaluateUniqueTypes:
    def test_pass_enough_types(self):
        result = evaluate_unique_types(5, 4)
        assert result.status == 'PASS'

    def test_fail_too_few(self):
        result = evaluate_unique_types(2, 4)
        assert result.status == 'FAIL'
        assert '2/4' in result.msg


# =============================================================================
# TEST: evaluate_priority_types
# =============================================================================

class TestEvaluatePriorityTypes:
    def test_pass_with_priority_used(self):
        result = evaluate_priority_types({'quiz', 'fill-in'}, {'quiz', 'match-up'})
        assert result.status == 'PASS'
        assert 'Priority types used' in result.msg

    def test_fail_no_priority(self):
        result = evaluate_priority_types({'cloze', 'fill-in'}, {'quiz', 'match-up'})
        assert result.status == 'FAIL'

    def test_pass_empty_priority_set(self):
        """Empty priority set = N/A (e.g., LIT track)."""
        result = evaluate_priority_types({'quiz'}, set())
        assert result.status == 'PASS'
        assert 'N/A' in result.msg


# =============================================================================
# TEST: evaluate_engagement
# =============================================================================

class TestEvaluateEngagement:
    def test_pass_at_target(self):
        result = evaluate_engagement(5, 5)
        assert result.status == 'PASS'

    def test_fail_below_target(self):
        result = evaluate_engagement(2, 5)
        assert result.status == 'FAIL'


# =============================================================================
# TEST: evaluate_audio
# =============================================================================

class TestEvaluateAudio:
    def test_info_with_audio(self):
        result = evaluate_audio(3)
        assert result.status == 'INFO'
        assert '3 links' in result.msg

    def test_info_without_audio(self):
        result = evaluate_audio(0)
        assert result.status == 'INFO'
        assert 'No audio' in result.msg


# =============================================================================
# TEST: evaluate_vocab
# =============================================================================

class TestEvaluateVocab:
    def test_pass_at_target(self):
        result = evaluate_vocab(15, 15)
        assert result.status == 'PASS'

    def test_warn_below_soft_target(self):
        result = evaluate_vocab(8, 15)
        assert result.status == 'WARN'
        assert 'soft target' in result.msg


# =============================================================================
# TEST: evaluate_structure
# =============================================================================

class TestEvaluateStructure:
    def test_pass_valid_structure(self):
        result = evaluate_structure(
            has_summary=True, has_vocab=True, has_vocab_table=True
        )
        assert result.status == 'PASS'
        assert 'Valid Structure' in result.msg

    def test_fail_missing_summary(self):
        result = evaluate_structure(
            has_summary=False, has_vocab=True, has_vocab_table=True
        )
        assert result.status == 'FAIL'
        assert 'Summary' in result.msg

    def test_a2_plus_variant(self):
        """A2+ uses sidecar checks (activities + vocab) instead of table check."""
        result = evaluate_structure(
            has_summary=True, has_vocab=True, has_vocab_table=False,
            has_activities=True, is_a2_plus=True
        )
        assert result.status == 'PASS'

    def test_a2_plus_missing_activities(self):
        result = evaluate_structure(
            has_summary=True, has_vocab=True, has_vocab_table=False,
            has_activities=False, is_a2_plus=True
        )
        assert result.status == 'FAIL'
        assert 'Activities' in result.msg

    def test_legacy_missing_vocab_table(self):
        result = evaluate_structure(
            has_summary=True, has_vocab=True, has_vocab_table=False
        )
        assert result.status == 'FAIL'
        assert 'Vocab Table' in result.msg


# =============================================================================
# TEST: evaluate_lint
# =============================================================================

class TestEvaluateLint:
    def test_pass_clean(self):
        result = evaluate_lint(0)
        assert result.status == 'PASS'
        assert 'Clean' in result.msg

    def test_fail_with_errors(self):
        result = evaluate_lint(5)
        assert result.status == 'FAIL'
        assert '5' in result.msg


# =============================================================================
# TEST: evaluate_pedagogy
# =============================================================================

class TestEvaluatePedagogy:
    def test_pass_clean(self):
        result = evaluate_pedagogy(0)
        assert result.status == 'PASS'

    def test_fail_with_violations(self):
        result = evaluate_pedagogy(3)
        assert result.status == 'FAIL'
        assert '3' in result.msg


# =============================================================================
# TEST: evaluate_immersion
# =============================================================================

class TestEvaluateImmersion:
    def test_pass_in_range(self):
        result = evaluate_immersion(65.0, 50, 80)
        assert result.status == 'PASS'
        assert '65.0%' in result.msg

    def test_fail_too_low(self):
        result = evaluate_immersion(30.0, 50, 80)
        assert result.status == 'FAIL'
        assert 'LOW' in result.msg

    def test_fail_too_high(self):
        result = evaluate_immersion(90.0, 50, 80)
        assert result.status == 'FAIL'
        assert 'HIGH' in result.msg

    def test_pass_no_range(self):
        """When min_imm=0, always passes."""
        result = evaluate_immersion(95.0, 0, 0)
        assert result.status == 'PASS'

    def test_phase_label_included(self):
        result = evaluate_immersion(65.0, 50, 80, phase_label=" [Phase 2]")
        assert 'Phase 2' in result.msg


# =============================================================================
# TEST: evaluate_naturalness
# =============================================================================

class TestEvaluateNaturalness:
    def test_pass_high_score(self):
        result = evaluate_naturalness(9, 'PASS')
        assert result.status == 'PASS'
        assert '9/10' in result.msg

    def test_fail_score_7(self):
        """Score 7 with PASS status still fails (below 8 target)."""
        result = evaluate_naturalness(7, 'PASS')
        assert result.status == 'FAIL'
        assert 'below 8/10' in result.msg

    def test_info_pending(self):
        result = evaluate_naturalness(0, 'PENDING')
        assert result.status == 'INFO'
        assert 'PENDING' in result.msg

    def test_info_pending_with_score(self):
        result = evaluate_naturalness(8, 'PENDING')
        assert result.status == 'INFO'
        assert '8/10' in result.msg

    def test_none_score_handled(self):
        """None score should not crash."""
        result = evaluate_naturalness(None, None)
        assert result.status == 'INFO'  # None status → 'PENDING'

    def test_fail_low_score_with_status(self):
        result = evaluate_naturalness(5, 'FAIL')
        assert result.status == 'FAIL'
        assert 'Requires rewrite' in result.msg


# =============================================================================
# TEST: evaluate_content_heavy
# =============================================================================

class TestEvaluateContentHeavy:
    def test_na_for_standard_module(self):
        result = evaluate_content_heavy(False, 6, [])
        assert result.status == 'INFO'
        assert 'N/A' in result.msg

    def test_pass_content_heavy_ok(self):
        result = evaluate_content_heavy(True, 10, [])
        assert result.status == 'PASS'
        assert '10 activities' in result.msg

    def test_warn_too_many_activities(self):
        result = evaluate_content_heavy(True, 15, [])
        assert result.status == 'WARN'
        assert 'Too many' in result.msg

    def test_warn_too_few_activities(self):
        result = evaluate_content_heavy(True, 5, [])
        assert result.status == 'WARN'
        assert 'Too few' in result.msg

    def test_warn_recall_violations(self):
        violations = [{'type': 'CONTENT_RECALL'}, {'type': 'CONTENT_RECALL'}]
        result = evaluate_content_heavy(True, 10, violations)
        assert result.status == 'WARN'
        assert '2 content recall' in result.msg


# =============================================================================
# TEST: compute_recommendation
# =============================================================================

class TestComputeRecommendation:
    def test_pass_no_issues(self):
        rec, reasons, severity = compute_recommendation(
            pedagogical_violations=[],
            lint_errors=[],
            results={},
            immersion_score=65.0,
            min_imm=50,
            max_imm=80,
            level_code='B1',
        )
        assert rec == 'PASS'
        assert severity == 0
        assert len(reasons) == 0

    def test_update_minor_violations(self):
        violations = [{'type': 'GRAMMAR'} for _ in range(2)]
        rec, reasons, severity = compute_recommendation(
            pedagogical_violations=violations,
            lint_errors=[],
            results={},
            immersion_score=65.0,
            min_imm=50,
            max_imm=80,
            level_code='B1',
        )
        assert rec == 'UPDATE'
        assert severity > 0

    def test_rewrite_severe_issues(self):
        """Many violations + immersion deviation + structure failure = REWRITE."""
        violations = [{'type': 'GRAMMAR'} for _ in range(15)]
        structure = GateResult('FAIL', '❌', 'Missing Summary')
        rec, reasons, severity = compute_recommendation(
            pedagogical_violations=violations,
            lint_errors=['e'] * 10,
            results={'structure': structure, 'activities': GateResult('FAIL', '❌', '0/6')},
            immersion_score=10.0,
            min_imm=50,
            max_imm=80,
            level_code='B1',
        )
        assert rec == 'REWRITE'
        assert severity >= 75

    def test_severity_clamped_at_100(self):
        """Severity cannot exceed 100."""
        violations = [{'type': 'GRAMMAR'} for _ in range(50)]
        rec, reasons, severity = compute_recommendation(
            pedagogical_violations=violations,
            lint_errors=['e'] * 20,
            results={
                'structure': GateResult('FAIL', '❌', 'Missing'),
                'activities': GateResult('FAIL', '❌', '0/6'),
                'density': GateResult('FAIL', '❌', 'low'),
            },
            immersion_score=5.0,
            min_imm=50,
            max_imm=80,
            level_code='B1',
        )
        assert severity <= 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
