"""
Tests for ai_agent_bridge modules, audit checks, scoring, and quality finalization.

Targets 13 modules with 0% coverage:
- ai_agent_bridge: _config, _db, _broker, _messaging, _model, _prompts, _github
- audit/checks: content_quality_pipeline, template_compliance
- audit: naturalness_check
- scoring: sampling
- audit: generate_activity_quality_queue, finalize_activity_quality
"""

import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# 1. _config.py
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 2. _db.py
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 3. _broker.py
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 4. _messaging.py
# ---------------------------------------------------------------------------


    # -- resolve_thread (#4837 item 5: unified `ab thread <task-id|msg-id>`) --


# ---------------------------------------------------------------------------
# 5. _model.py
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 6. _prompts.py
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 7. _github.py
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 8. content_quality_pipeline.py
# ---------------------------------------------------------------------------

class TestContentQualityPipeline:
    """Tests for scripts/audit/checks/content_quality_pipeline.py."""

    def test_get_charset_upper_m1_with_plan(self):
        from scripts.audit.checks.content_quality_pipeline import _get_charset_upper
        plan = {"decodable_letters": "А О У І М Н Т К С Л"}
        chars = _get_charset_upper(1, plan)
        assert "А" in chars
        assert "М" in chars
        assert "К" in chars  # K is in plan's decodable_letters
        assert "І" in chars
        assert "Б" not in chars  # Not in plan

    def test_get_charset_upper_no_plan_fallback(self):
        from scripts.audit.checks.content_quality_pipeline import _get_charset_upper
        # Without plan, returns full alphabet (safe fallback)
        chars = _get_charset_upper(1)
        assert "А" in chars
        assert "Я" in chars  # Full alphabet

    def test_word_has_translation_after_parens(self):
        from scripts.audit.checks.content_quality_pipeline import _word_has_translation_after
        line = "Привіт (hello) to you"
        assert _word_has_translation_after(line, 6) is True  # after Привіт

    def test_word_is_in_translation_context(self):
        from scripts.audit.checks.content_quality_pipeline import _word_is_in_translation_context
        line = "(Привіт means hello)"
        assert _word_is_in_translation_context(line, 1) is True

    def test_check_untranslated_non_decodable_not_a1(self):
        from scripts.audit.checks.content_quality_pipeline import check_untranslated_non_decodable
        plan = {"decodable_letters": "А О У І М Н Т К С Л"}
        issues = check_untranslated_non_decodable("Привіт", module_num=1, level_code="B1", plan=plan)
        assert issues == []

    def test_check_untranslated_non_decodable_flags_word(self):
        from scripts.audit.checks.content_quality_pipeline import check_untranslated_non_decodable
        plan = {"decodable_letters": "А О У І М Н Т К С Л"}
        # "Привіт" has П, Р, В — not in plan's decodable_letters
        content = "---\ntitle: test\n---\nПривіт is a word"
        issues = check_untranslated_non_decodable(content, module_num=1, level_code="A1", plan=plan)
        assert len(issues) >= 1
        assert issues[0]["type"] == "UNTRANSLATED_NON_DECODABLE"

    def test_check_untranslated_non_decodable_translated_ok(self):
        from scripts.audit.checks.content_quality_pipeline import check_untranslated_non_decodable
        plan = {"decodable_letters": "А О У І М Н Т К С Л"}
        content = "---\ntitle: test\n---\nПривіт (hello) is a greeting"
        issues = check_untranslated_non_decodable(content, module_num=1, level_code="A1", plan=plan)
        assert len(issues) == 0

    def test_collect_failed_words_from_str(self):
        from scripts.audit.checks.content_quality_pipeline import _collect_failed_words_from_str
        failed = {"кот"}
        result = _collect_failed_words_from_str("кот і собака", failed)
        assert "кот" in result

    def test_scan_activity_answers(self):
        from scripts.audit.checks.content_quality_pipeline import _scan_activity_answers
        act = {"answer": "кот", "items": [{"text": "собака", "options": ["кот", "пес"]}]}
        failed = {"кот"}
        result = _scan_activity_answers(act, failed)
        assert "кот" in result


# ---------------------------------------------------------------------------
# 9. template_compliance.py
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 10. naturalness_check.py
# ---------------------------------------------------------------------------

class TestNaturalnessCheck:
    """Tests for scripts/audit/naturalness_check.py."""

    @pytest.fixture(autouse=True)
    def _unit_test_interpreter(self, monkeypatch):
        """These file helpers do not spawn providers or require a checkout venv."""
        monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
        from lu_machinery.common import repo_root

        monkeypatch.setattr(repo_root, "project_interpreter", lambda root=None: Path(sys.executable))

    def test_update_meta_naturalness(self, tmp_path):
        import yaml

        from scripts.audit.naturalness_check import update_meta_naturalness
        meta_file = tmp_path / "test.yaml"
        meta_file.write_text("version: 1\n")
        update_meta_naturalness(meta_file, 9, "PASS", "Good", "2026-01-01")
        data = yaml.safe_load(meta_file.read_text())
        assert data["naturalness"]["score"] == 9
        assert data["naturalness"]["status"] == "PASS"
        # Should not raise


# ---------------------------------------------------------------------------
# 11. scoring/sampling.py
# ---------------------------------------------------------------------------

class TestSampling:
    """Tests for scripts/scoring/sampling.py."""

    def test_determine_tier_low_naturalness(self):
        from scripts.scoring.sampling import determine_tier
        data = {"naturalness": {"score": 6}}
        assert determine_tier(data) == "llm-verified"

    def test_determine_tier_high_naturalness(self):
        from scripts.scoring.sampling import determine_tier
        data = {"naturalness": {"score": 9}, "tags": []}
        assert determine_tier(data) == "automated"

    def test_determine_tier_sensitive_tags(self):
        from scripts.scoring.sampling import determine_tier
        data = {"naturalness": {"score": 9}, "tags": ["politics", "economy"]}
        assert determine_tier(data) == "llm-verified"

    def test_should_sample_deterministic(self):
        from scripts.scoring.sampling import should_sample
        # Same slug always gives same result
        r1 = should_sample("test-slug")
        r2 = should_sample("test-slug")
        assert r1 == r2

    def test_should_sample_rate_1(self):
        from scripts.scoring.sampling import should_sample
        assert should_sample("anything", sample_rate=1.0) is True

    def test_get_sampling_candidates(self):
        from scripts.scoring.sampling import get_sampling_candidates
        modules = [
            {"slug": "mod1", "naturalness": {"score": 5}, "tags": []},
            {"slug": "mod2", "naturalness": {"score": 9}, "tags": [], "validation_tier": "llm-verified"},
            {"slug": "mod3", "naturalness": {"score": 9}, "tags": ["war"]},
        ]
        candidates = get_sampling_candidates(modules)
        assert "mod1" in candidates
        assert "mod2" not in candidates  # Already verified
        assert "mod3" in candidates


# ---------------------------------------------------------------------------
# 12. generate_activity_quality_queue.py
# ---------------------------------------------------------------------------

class TestGenerateActivityQualityQueue:
    """Tests for scripts/audit/generate_activity_quality_queue.py."""

    def test_extract_options_quiz(self):
        from scripts.audit.generate_activity_quality_queue import extract_options
        activity = {"type": "quiz", "items": [
            {"options": [{"text": "A", "correct": True}, {"text": "B", "correct": False}]}
        ]}
        options, correct = extract_options(activity)
        assert options == ["A", "B"]
        assert correct == "A"


# ---------------------------------------------------------------------------
# 13. finalize_activity_quality.py
# ---------------------------------------------------------------------------

class TestFinalizeActivityQuality:
    """Tests for scripts/audit/finalize_activity_quality.py."""

    def test_evaluate_quality_gates_a1_pass(self):
        from scripts.audit.finalize_activity_quality import evaluate_quality_gates
        scores = {"naturalness_avg": 2.0}
        result = evaluate_quality_gates(scores, "A1")
        assert result["result"] == "PASS"  # A1 has no strict gates

    def test_evaluate_quality_gates_b1_pass(self):
        from scripts.audit.finalize_activity_quality import evaluate_quality_gates
        scores = {
            "naturalness_avg": 4.0, "engagement_avg": 4.0,
            "distractor_quality_avg": 4.5, "variety_avg": 70,
            "difficulty_inappropriate_pct": 0.1
        }
        result = evaluate_quality_gates(scores, "B1")
        assert result["result"] == "PASS"

    def test_evaluate_quality_gates_b1_fail_naturalness(self):
        from scripts.audit.finalize_activity_quality import evaluate_quality_gates
        scores = {
            "naturalness_avg": 2.0, "engagement_avg": 4.0,
            "distractor_quality_avg": 4.5, "variety_avg": 70,
            "difficulty_inappropriate_pct": 0.1
        }
        result = evaluate_quality_gates(scores, "B1")
        assert result["result"] == "FAIL"
        assert any(g["dimension"] == "naturalness" for g in result["failed_gates"])
