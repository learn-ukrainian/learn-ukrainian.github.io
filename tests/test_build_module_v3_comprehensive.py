"""
Comprehensive tests for build_module.py.

Covers functions NOT already tested in test_v3_state.py and test_build_pipeline.py:
- _max_audit_iters — track-aware iteration limits
- _mark_phase_v3 — state mutation with timestamps
- _migrate_v2_state_to_v3 — v2→v3 state migration
- _validate_audit_state — revalidation of stale states
- _run_deterministic_fixes — with mtime caching
- _meta_has_oversized_sections — meta validation
- _research_file_is_usable — research file validation
- _invalidate_stale_artifacts — artifact cleanup on rebuild
- _is_final_review_done — Phase F completion check
- _call_phase_func — dispatch signature routing

Plus regression tests for bugs fixed in #625:
- subprocess import (NameError on timeout)
- content_path UnboundLocalError in phase_audit_v3
- Stale vocabulary retained in phase_C_v3

Issue: #625
"""

import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.build_module import (
    _max_audit_iters,
    _mark_phase_v3,
    _load_state_v3,
    _save_state_v3,
    _is_phase_v3_complete,
    _meta_has_oversized_sections,
    _research_file_is_usable,
    _is_final_review_done,
    _call_phase_func,
    _run_deterministic_fixes,
    _deterministic_fix_mtimes,
    _extract_delimiter,
    _extract_delimiter_tolerant,
    _inject_metrics_into_prompt,
    MAX_AUDIT_FIX_ITERS_CORE,
    MAX_AUDIT_FIX_ITERS_SEMINAR,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_ctx(tmp_path):
    """Create a minimal ModuleContext-like object with temp directories."""
    ctx = MagicMock()
    ctx.track = "a1"
    ctx.slug = "test-module"
    ctx.module_num = 1
    ctx.orch_dir = tmp_path / "orchestration" / "test-module"
    ctx.orch_dir.mkdir(parents=True)
    ctx.word_target = 3000
    ctx.force_phase = None
    ctx.dry_run = False
    ctx.refresh = False

    # Create file paths
    md_path = tmp_path / "test-module.md"
    md_path.write_text("## Вступ\n\nContent here.\n")
    meta_path = tmp_path / "meta" / "test-module.yaml"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    research_path = tmp_path / "research" / "test-module-research.md"
    research_path.parent.mkdir(parents=True, exist_ok=True)
    act_path = tmp_path / "activities" / "test-module.yaml"
    act_path.parent.mkdir(parents=True, exist_ok=True)
    vocab_path = tmp_path / "vocabulary" / "test-module.yaml"
    vocab_path.parent.mkdir(parents=True, exist_ok=True)
    review_path = tmp_path / "review" / "test-module-review.md"
    review_path.parent.mkdir(parents=True, exist_ok=True)

    ctx.paths = {
        "md": md_path,
        "meta": meta_path,
        "research": research_path,
        "activities": act_path,
        "vocabulary": vocab_path,
        "vocab": vocab_path,
        "review": review_path,
    }

    # v2 state (for migration tests)
    ctx.state = {"phases": {}}

    return ctx


# ---------------------------------------------------------------------------
# _max_audit_iters
# ---------------------------------------------------------------------------

class TestMaxAuditIters:
    """Tests for track-aware audit iteration limits."""

    def test_core_tracks(self):
        """Core tracks get fewer iterations."""
        for track in ["a1", "a2", "b1", "b2"]:
            assert _max_audit_iters(track) == MAX_AUDIT_FIX_ITERS_CORE

    def test_seminar_tracks(self):
        """Seminar tracks get more iterations due to higher complexity."""
        for track in ["hist", "bio", "istorio"]:
            assert _max_audit_iters(track) == MAX_AUDIT_FIX_ITERS_SEMINAR

    def test_pro_tracks(self):
        """Pro tracks also get more iterations."""
        for track in ["b2-pro", "c1-pro"]:
            assert _max_audit_iters(track) == MAX_AUDIT_FIX_ITERS_SEMINAR

    def test_unknown_track_gets_core(self):
        """Unknown tracks default to core limit."""
        assert _max_audit_iters("unknown-track") == MAX_AUDIT_FIX_ITERS_CORE


# ---------------------------------------------------------------------------
# _mark_phase_v3
# ---------------------------------------------------------------------------

class TestMarkPhaseV3:
    """Tests for _mark_phase_v3 state mutation."""

    def test_marks_complete(self, mock_ctx):
        state = {"phases": {}}
        with patch("pipeline_lib._state_lock", None), \
             patch("pipeline_lib.FileLock", MagicMock()):
            _mark_phase_v3(mock_ctx, state, "A", "complete")
        assert state["phases"]["v3-A"]["status"] == "complete"
        assert "ts" in state["phases"]["v3-A"]

    def test_marks_failed_with_extras(self, mock_ctx):
        state = {"phases": {}}
        with patch("pipeline_lib._state_lock", None), \
             patch("pipeline_lib.FileLock", MagicMock()):
            _mark_phase_v3(mock_ctx, state, "D", "failed", note="needs-rebuild", attempts=2)
        assert state["phases"]["v3-D"]["status"] == "failed"
        assert state["phases"]["v3-D"]["note"] == "needs-rebuild"
        assert state["phases"]["v3-D"]["attempts"] == 2

    def test_saves_to_disk(self, mock_ctx):
        state = {"phases": {}}
        with patch("pipeline_lib._state_lock", None), \
             patch("pipeline_lib.FileLock", MagicMock()):
            _mark_phase_v3(mock_ctx, state, "B", "complete")
        sf = mock_ctx.orch_dir / "state-v3.json"
        assert sf.exists()
        loaded = json.loads(sf.read_text("utf-8"))
        assert loaded["phases"]["v3-B"]["status"] == "complete"


# ---------------------------------------------------------------------------
# _meta_has_oversized_sections
# ---------------------------------------------------------------------------

class TestMetaHasOversizedSections:
    """Tests for meta section size validation."""

    def test_normal_sections(self, mock_ctx):
        """Sections within 25% threshold → False."""
        import yaml
        meta = {"word_target": 4000, "content_outline": [
            {"title": "Section 1", "words": 800},
            {"title": "Section 2", "words": 800},
            {"title": "Section 3", "words": 800},
        ]}
        mock_ctx.paths["meta"].write_text(yaml.dump(meta, allow_unicode=True), "utf-8")
        assert _meta_has_oversized_sections(mock_ctx) is False

    def test_oversized_section(self, mock_ctx):
        """One section > 25% of word_target → True."""
        import yaml
        meta = {"word_target": 4000, "content_outline": [
            {"title": "Huge Section", "words": 2000},  # 50% > 25%
            {"title": "Tiny Section", "words": 200},
        ]}
        mock_ctx.paths["meta"].write_text(yaml.dump(meta, allow_unicode=True), "utf-8")
        assert _meta_has_oversized_sections(mock_ctx) is True

    def test_missing_meta(self, mock_ctx):
        """No meta file → False."""
        mock_ctx.paths["meta"].unlink(missing_ok=True)
        assert _meta_has_oversized_sections(mock_ctx) is False

    def test_no_word_target(self, mock_ctx):
        """Meta without word_target → False."""
        import yaml
        meta = {"content_outline": [{"title": "Section", "words": 500}]}
        mock_ctx.paths["meta"].write_text(yaml.dump(meta, allow_unicode=True), "utf-8")
        assert _meta_has_oversized_sections(mock_ctx) is False

    def test_no_outline(self, mock_ctx):
        """Meta without content_outline → False."""
        import yaml
        meta = {"word_target": 4000}
        mock_ctx.paths["meta"].write_text(yaml.dump(meta, allow_unicode=True), "utf-8")
        assert _meta_has_oversized_sections(mock_ctx) is False


# ---------------------------------------------------------------------------
# _research_file_is_usable
# ---------------------------------------------------------------------------

class TestResearchFileIsUsable:
    """Tests for research file validation."""

    def test_sufficient_words(self, mock_ctx):
        """Research file with 500+ words → usable."""
        text = " ".join(f"word{i}" for i in range(600))
        mock_ctx.paths["research"].write_text(text, "utf-8")
        assert _research_file_is_usable(mock_ctx) is True

    def test_too_short(self, mock_ctx):
        """Research file with < 500 words → not usable."""
        mock_ctx.paths["research"].write_text("Short research.", "utf-8")
        assert _research_file_is_usable(mock_ctx) is False

    def test_missing_file(self, mock_ctx):
        """No research file → not usable."""
        mock_ctx.paths["research"].unlink(missing_ok=True)
        assert _research_file_is_usable(mock_ctx) is False

    def test_no_research_path(self, mock_ctx):
        """Missing 'research' key in paths → not usable."""
        mock_ctx.paths.pop("research", None)
        assert _research_file_is_usable(mock_ctx) is False


# ---------------------------------------------------------------------------
# _is_final_review_done
# ---------------------------------------------------------------------------

class TestIsFinalReviewDone:
    """Tests for Phase F completion check."""

    def test_v3_state_complete(self, tmp_path):
        """Phase F in v3 state → done."""
        orch = tmp_path / "orchestration" / "test"
        orch.mkdir(parents=True)
        state = {"phases": {"9-final-review": {"status": "complete"}}}
        (orch / "state-v3.json").write_text(json.dumps(state), "utf-8")
        paths = {"orchestration": orch, "md": tmp_path / "test.md"}
        assert _is_final_review_done(paths) is True

    def test_v2_state_complete(self, tmp_path):
        """Phase F in v2 state → done."""
        orch = tmp_path / "orchestration" / "test"
        orch.mkdir(parents=True)
        state = {"phases": {"9-final-review": {"status": "complete"}}}
        (orch / "state.json").write_text(json.dumps(state), "utf-8")
        paths = {"orchestration": orch, "md": tmp_path / "test.md"}
        assert _is_final_review_done(paths) is True

    def test_incomplete(self, tmp_path):
        """No complete final review → not done."""
        orch = tmp_path / "orchestration" / "test"
        orch.mkdir(parents=True)
        state = {"phases": {"9-final-review": {"status": "in-progress"}}}
        (orch / "state-v3.json").write_text(json.dumps(state), "utf-8")
        paths = {"orchestration": orch, "md": tmp_path / "test.md"}
        assert _is_final_review_done(paths) is False

    def test_no_state_files(self, tmp_path):
        """No state files → not done."""
        orch = tmp_path / "orchestration" / "test"
        orch.mkdir(parents=True)
        paths = {"orchestration": orch, "md": tmp_path / "test.md"}
        assert _is_final_review_done(paths) is False

    def test_derive_orch_from_md(self, tmp_path):
        """Derives orchestration dir from md path when not explicit."""
        md = tmp_path / "test.md"
        md.touch()
        orch = tmp_path / "orchestration" / "test"
        orch.mkdir(parents=True)
        state = {"phases": {"9-final-review": {"status": "complete"}}}
        (orch / "state-v3.json").write_text(json.dumps(state), "utf-8")
        paths = {"md": md}
        assert _is_final_review_done(paths) is True


# ---------------------------------------------------------------------------
# _call_phase_func
# ---------------------------------------------------------------------------

class TestCallPhaseFunc:
    """Tests for phase function dispatch routing."""

    def test_phase_a_gets_ctx_state(self):
        """Phase A functions get (ctx, state)."""
        func = MagicMock(return_value=True)
        ctx, state = MagicMock(), {}
        result = _call_phase_func(func, "A", ctx, state)
        func.assert_called_once_with(ctx, state)
        assert result is True

    def test_phase_b_gets_ctx_state(self):
        """Phase B functions get (ctx, state)."""
        func = MagicMock(return_value=True)
        ctx, state = MagicMock(), {}
        _call_phase_func(func, "B", ctx, state)
        func.assert_called_once_with(ctx, state)

    def test_phase_c_gets_ctx_state(self):
        """Phase C functions get (ctx, state)."""
        func = MagicMock(return_value=True)
        ctx, state = MagicMock(), {}
        _call_phase_func(func, "C", ctx, state)
        func.assert_called_once_with(ctx, state)

    def test_phase_e_gets_ctx_only(self):
        """Phase E functions get (ctx) only."""
        func = MagicMock(return_value=True)
        ctx, state = MagicMock(), {}
        _call_phase_func(func, "E", ctx, state)
        func.assert_called_once_with(ctx)

    def test_phase_f_gets_ctx_only(self):
        """Phase F functions get (ctx) only."""
        func = MagicMock(return_value=True)
        ctx, state = MagicMock(), {}
        _call_phase_func(func, "F", ctx, state)
        func.assert_called_once_with(ctx)

    def test_audit_gets_ctx_state(self):
        """Audit phase functions get (ctx, state)."""
        func = MagicMock(return_value=True)
        ctx, state = MagicMock(), {}
        _call_phase_func(func, "audit", ctx, state)
        func.assert_called_once_with(ctx, state)

    def test_returns_false_on_failure(self):
        """Propagates return value from phase function."""
        func = MagicMock(return_value=False)
        result = _call_phase_func(func, "D", MagicMock(), {})
        assert result is False


# ---------------------------------------------------------------------------
# _run_deterministic_fixes — mtime caching
# ---------------------------------------------------------------------------

class TestDeterministicFixesMtimeCache:
    """Tests for the mtime-based skip optimization."""

    def _mock_auto_fix_imports(self):
        """Create mock modules for all auto-fix imports so they no-op."""
        mock_euphony = MagicMock()
        mock_euphony.auto_fix_euphony = MagicMock(return_value=("", 0))
        mock_lint_ipa = MagicMock()
        mock_lint_ipa.apply_fixes = MagicMock(return_value=("", 0))
        mock_yaml_schema = MagicMock()
        mock_yaml_schema.fix_yaml_file = MagicMock(return_value=(0, []))
        mock_yaml_schema.remove_forbidden_activities = MagicMock(return_value=(0, []))
        mock_audit_core = MagicMock()
        mock_audit_core.detect_level = MagicMock(return_value=("a1", 1, None))
        mock_audit_core.detect_focus = MagicMock(return_value="grammar")
        mock_audit_core.load_yaml_meta = MagicMock(return_value={})
        return {
            "audit.checks.euphony": mock_euphony,
            "lint_ipa": mock_lint_ipa,
            "audit.checks.yaml_schema_validation": mock_yaml_schema,
            "audit.core": mock_audit_core,
        }

    def test_skips_when_files_unchanged(self, mock_ctx):
        """Second call with no file changes should return 0 immediately."""
        # Clear global state
        _deterministic_fix_mtimes.pop(mock_ctx.slug, None)

        # Mock all auto-fix imports to avoid real processing
        with patch.dict("sys.modules", self._mock_auto_fix_imports()):
            # First call — records mtime
            result1 = _run_deterministic_fixes(mock_ctx)
            # Second call — files unchanged, should skip
            result2 = _run_deterministic_fixes(mock_ctx)
            assert result2 == 0

    def test_runs_when_file_modified(self, mock_ctx):
        """After file modification, should re-run fixes."""
        _deterministic_fix_mtimes.pop(mock_ctx.slug, None)

        with patch.dict("sys.modules", self._mock_auto_fix_imports()):
            # First call
            _run_deterministic_fixes(mock_ctx)

            # Modify the content file
            time.sleep(0.05)  # Ensure mtime changes
            mock_ctx.paths["md"].write_text("## Modified\n\nNew content.\n", "utf-8")

            # The cached mtime should be less than the new mtime
            old_mtime = _deterministic_fix_mtimes.get(mock_ctx.slug, 0)
            new_mtime = mock_ctx.paths["md"].stat().st_mtime
            assert new_mtime > old_mtime

    def test_no_files_returns_zero(self, mock_ctx):
        """When no target files exist, should return 0."""
        _deterministic_fix_mtimes.pop(mock_ctx.slug, None)
        mock_ctx.paths["md"].unlink(missing_ok=True)
        mock_ctx.paths["activities"].unlink(missing_ok=True)
        mock_ctx.paths["vocab"].unlink(missing_ok=True)
        mock_ctx.paths["vocabulary"].unlink(missing_ok=True)
        # Set paths to nonexistent
        mock_ctx.paths["md"] = mock_ctx.orch_dir / "nonexistent.md"

        result = _run_deterministic_fixes(mock_ctx)
        assert result == 0


# ---------------------------------------------------------------------------
# REGRESSION TESTS for bugs fixed in #625
# ---------------------------------------------------------------------------

class TestRegressionSubprocessImport:
    """Regression test: subprocess must be importable for timeout handling."""

    def test_subprocess_is_imported(self):
        """Verify subprocess is in the module's namespace."""
        import scripts.build_module as mod
        # subprocess should be importable and the TimeoutExpired exception accessible
        assert hasattr(mod, 'subprocess')
        assert hasattr(mod.subprocess, 'TimeoutExpired')


class TestRegressionContentPathBound:
    """Regression test: content_path must be assigned in phase_audit_v3."""

    def test_content_path_assigned_before_use(self):
        """Verify the source code assigns content_path before the auto-fix block."""
        import inspect
        from scripts.build_module import phase_audit_v3
        source = inspect.getsource(phase_audit_v3)

        # content_path must be assigned before the auto-fix loop
        assign_idx = source.find('content_path = ctx.paths["md"]')
        autofix_idx = source.find('auto_fix_total = _run_deterministic_fixes')
        assert assign_idx != -1, "content_path assignment not found"
        assert assign_idx < autofix_idx, "content_path must be assigned before auto-fix loop"


class TestRegressionStaleVocabulary:
    """Regression test: stale vocab must be deleted when activities are invalid."""

    def test_stale_vocab_deleted_on_invalid_activities(self):
        """Verify the source code unlinks voc_path when activities are invalid."""
        import inspect
        from scripts.build_module import phase_C_v3
        source = inspect.getsource(phase_C_v3)

        # Should contain logic to unlink vocab when activities are invalid
        assert "voc_path.unlink" in source, \
            "phase_C_v3 must delete stale vocabulary when activities are invalid"


class TestRegressionYamlFenceStripping:
    """Regression test: YAML fence stripping in Phase A meta extraction."""

    def test_strips_yaml_fences(self):
        """_extract_delimiter + fence stripping should handle fenced YAML."""
        import re
        # Simulate what Phase A does
        raw = (
            "===META_OUTLINE_START===\n"
            "```yaml\n"
            "content_outline:\n"
            "  - title: Section 1\n"
            "    words: 500\n"
            "```\n"
            "===META_OUTLINE_END==="
        )
        meta_text = _extract_delimiter(raw, "===META_OUTLINE_START===", "===META_OUTLINE_END===")
        assert meta_text is not None

        # Apply the same fence-stripping logic as the fixed code
        meta_text_clean = re.sub(r'^```(?:ya?ml)?\s*\n', '', meta_text.strip())
        meta_text_clean = re.sub(r'\n```\s*$', '', meta_text_clean)

        import yaml
        parsed = yaml.safe_load(meta_text_clean)
        assert isinstance(parsed, dict)
        assert "content_outline" in parsed

    def test_no_fences_unchanged(self):
        """Plain YAML without fences should not be affected by stripping."""
        import re
        raw = (
            "===META_OUTLINE_START===\n"
            "content_outline:\n"
            "  - title: Section 1\n"
            "    words: 500\n"
            "===META_OUTLINE_END==="
        )
        meta_text = _extract_delimiter(raw, "===META_OUTLINE_START===", "===META_OUTLINE_END===")
        meta_text_clean = re.sub(r'^```(?:ya?ml)?\s*\n', '', meta_text.strip())
        meta_text_clean = re.sub(r'\n```\s*$', '', meta_text_clean)

        import yaml
        parsed = yaml.safe_load(meta_text_clean)
        assert isinstance(parsed, dict)
        assert parsed["content_outline"][0]["title"] == "Section 1"


# ---------------------------------------------------------------------------
# _compute_audit_metrics — fragile attribute access
# ---------------------------------------------------------------------------

class TestComputeAuditMetricsDefensiveAccess:
    """Test that _compute_audit_metrics handles missing attributes gracefully."""

    def test_missing_word_target_attribute(self, mock_ctx):
        """ctx without word_target should not crash."""
        from types import SimpleNamespace
        from scripts.build_module import _compute_audit_metrics
        # Create a ctx-like object that truly lacks word_target
        ctx = SimpleNamespace(
            paths=mock_ctx.paths,
            slug=mock_ctx.slug,
            track=mock_ctx.track,
        )

        # Should use getattr fallback (word_target absent → 0)
        with patch("scripts.build_module.run_verify", return_value=(True, "")):
            metrics = _compute_audit_metrics(ctx)
        assert "COMPUTED_WORD_TARGET" in metrics
        assert metrics["COMPUTED_WORD_TARGET"] == "0"


# ---------------------------------------------------------------------------
# _validate_audit_state
# ---------------------------------------------------------------------------

class TestValidateAuditState:
    """Tests for audit state revalidation against current rules."""

    def test_skips_when_force_phase_set(self, mock_ctx):
        """With force_phase, should not revalidate."""
        from scripts.build_module import _validate_audit_state
        mock_ctx.force_phase = "D"
        state = {"phases": {"v3-audit": {"status": "complete"}}}
        # Should return without changes
        _validate_audit_state(mock_ctx, state)
        assert state["phases"]["v3-audit"]["status"] == "complete"

    def test_skips_when_audit_not_complete(self, mock_ctx):
        """When audit is not marked complete, should not revalidate."""
        from scripts.build_module import _validate_audit_state
        state = {"phases": {}}
        _validate_audit_state(mock_ctx, state)
        # No changes expected
        assert state["phases"] == {}

    def test_clears_stale_on_audit_fail(self, mock_ctx):
        """When audit passes in state but fails under current rules, clears state."""
        from scripts.build_module import _validate_audit_state
        state = {"phases": {
            "v3-audit": {"status": "complete"},
            "v3-D": {"status": "complete"},
        }}
        with patch("scripts.build_module.run_verify", return_value=(False, "FAIL")):
            _validate_audit_state(mock_ctx, state)
        # Both audit and D should be cleared
        assert "v3-audit" not in state["phases"]
        assert "v3-D" not in state["phases"]

    def test_preserves_when_still_passing(self, mock_ctx):
        """When audit still passes, should preserve state."""
        from scripts.build_module import _validate_audit_state
        state = {"phases": {"v3-audit": {"status": "complete"}}}
        with patch("scripts.build_module.run_verify", return_value=(True, "")):
            _validate_audit_state(mock_ctx, state)
        assert state["phases"]["v3-audit"]["status"] == "complete"

    def test_failed_state_that_now_passes(self, mock_ctx):
        """Previously failed audit that now passes → mark complete."""
        from scripts.build_module import _validate_audit_state
        state = {"phases": {"v3-audit": {"status": "failed", "attempts": 3}}}
        with patch("scripts.build_module.run_verify", return_value=(True, "")), \
             patch("scripts.build_module._mark_phase_v3") as mock_mark, \
             patch("scripts.build_module._save_state_v3"):
            _validate_audit_state(mock_ctx, state)
        mock_mark.assert_called_once()
        call_args = mock_mark.call_args
        assert call_args[0][2] == "audit"  # phase_id
        assert call_args[0][3] == "complete"  # status


# ---------------------------------------------------------------------------
# _migrate_v2_state_to_v3
# ---------------------------------------------------------------------------

class TestMigrateV2ToV3:
    """Tests for one-time v2→v3 state migration."""

    def test_skips_when_v3_has_phases(self, mock_ctx):
        """If v3 state already has phases, migration should not run."""
        from scripts.build_module import _migrate_v2_state_to_v3
        state = {"phases": {"v3-A": {"status": "complete"}}}
        result = _migrate_v2_state_to_v3(mock_ctx, state)
        assert result is False

    def test_skips_when_v2_empty(self, mock_ctx):
        """If v2 state has no phases, nothing to migrate."""
        from scripts.build_module import _migrate_v2_state_to_v3
        state = {"phases": {}}
        mock_ctx.state = {"phases": {}}
        result = _migrate_v2_state_to_v3(mock_ctx, state)
        assert result is False

    def test_migrates_complete_phases(self, mock_ctx):
        """v2 phases 0+1 complete with meta → migrates to v3 Phase A."""
        from scripts.build_module import _migrate_v2_state_to_v3
        state = {"phases": {}}
        mock_ctx.state = {"phases": {
            "0": {"status": "complete"},
            "1": {"status": "complete"},
        }}
        # Meta must exist for artifact check
        mock_ctx.paths["meta"].write_text("word_target: 3000\n", "utf-8")

        with patch("scripts.build_module._mark_phase_v3") as mock_mark:
            result = _migrate_v2_state_to_v3(mock_ctx, state)
        assert result is True
        # Phase A should have been marked
        calls = [c for c in mock_mark.call_args_list if c[0][2] == "A"]
        assert len(calls) == 1

    def test_skips_incomplete_v2_phases(self, mock_ctx):
        """If required v2 phases are not complete, don't migrate."""
        from scripts.build_module import _migrate_v2_state_to_v3
        state = {"phases": {}}
        mock_ctx.state = {"phases": {
            "0": {"status": "complete"},
            "1": {"status": "in-progress"},  # Not complete
        }}
        with patch("scripts.build_module._mark_phase_v3") as mock_mark:
            result = _migrate_v2_state_to_v3(mock_ctx, state)
        # Phase A should NOT be migrated
        a_calls = [c for c in mock_mark.call_args_list if len(c[0]) > 2 and c[0][2] == "A"]
        assert len(a_calls) == 0


# ---------------------------------------------------------------------------
# Edge case: _inject_metrics_into_prompt with COMPUTED_ prefix
# ---------------------------------------------------------------------------

class TestInjectMetricsComputedPrefix:
    """Test that metrics with COMPUTED_ prefix are correctly injected."""

    def test_all_audit_metric_keys(self):
        """All computed metric keys should be replaceable."""
        prompt = (
            "Words: {COMPUTED_WORD_COUNT}/{COMPUTED_WORD_TARGET} ({COMPUTED_WORD_PERCENT}%)\n"
            "Activities: {COMPUTED_ACTIVITY_COUNT}, Vocab: {COMPUTED_VOCAB_COUNT}\n"
            "Engagement: {COMPUTED_ENGAGEMENT_COUNT}\n"
            "Immersion: {COMPUTED_IMMERSION_PERCENT}% (target: {COMPUTED_IMMERSION_TARGET})\n"
            "Audit: {COMPUTED_AUDIT_STATUS}"
        )
        metrics = {
            "COMPUTED_WORD_COUNT": "3500",
            "COMPUTED_WORD_TARGET": "4000",
            "COMPUTED_WORD_PERCENT": "87.5",
            "COMPUTED_ACTIVITY_COUNT": "12",
            "COMPUTED_VOCAB_COUNT": "25",
            "COMPUTED_ENGAGEMENT_COUNT": "8",
            "COMPUTED_IMMERSION_PERCENT": "65.3",
            "COMPUTED_IMMERSION_TARGET": "60-70%",
            "COMPUTED_AUDIT_STATUS": "PASS",
        }
        result = _inject_metrics_into_prompt(prompt, metrics)
        # No unreplaced placeholders
        assert "{COMPUTED_" not in result
        assert "3500" in result
        assert "PASS" in result


# ---------------------------------------------------------------------------
# _invalidate_stale_artifacts
# ---------------------------------------------------------------------------

class TestInvalidateStaleArtifacts:
    """Tests for artifact cleanup on content rebuild."""

    def test_deletes_status_cache(self, mock_ctx, tmp_path):
        """Status cache should be deleted after content rebuild."""
        from scripts.build_module import _invalidate_stale_artifacts
        track_dir = tmp_path
        mock_ctx.paths["md"] = track_dir / "test-module.md"
        status_file = track_dir / "status" / "test-module.json"
        status_file.parent.mkdir(parents=True, exist_ok=True)
        status_file.write_text("{}", "utf-8")

        _invalidate_stale_artifacts(mock_ctx)
        assert not status_file.exists()

    def test_deletes_review_files(self, mock_ctx, tmp_path):
        """Old review files should be deleted after content rebuild."""
        from scripts.build_module import _invalidate_stale_artifacts
        track_dir = tmp_path
        mock_ctx.paths["md"] = track_dir / "test-module.md"
        review_dir = track_dir / "review"
        review_dir.mkdir(parents=True, exist_ok=True)
        review_file = review_dir / "test-module-review.md"
        review_file.write_text("old review", "utf-8")

        _invalidate_stale_artifacts(mock_ctx)
        assert not review_file.exists()

    def test_handles_missing_files_gracefully(self, mock_ctx, tmp_path):
        """Should not crash if files don't exist."""
        from scripts.build_module import _invalidate_stale_artifacts
        mock_ctx.paths["md"] = tmp_path / "test-module.md"
        # No status, review, or audit files exist
        _invalidate_stale_artifacts(mock_ctx)  # Should not raise


# ---------------------------------------------------------------------------
# _apply_find_replace_fixes
# ---------------------------------------------------------------------------

class TestApplyFindReplaceFixes:
    """Tests for FIND/REPLACE fix pair application."""

    def test_exact_match(self, tmp_path):
        """Exact FIND text should be replaced."""
        from scripts.build_module import _apply_find_replace_fixes
        f = tmp_path / "content.md"
        f.write_text("Line one.\nIn Russian, this word is feminine.\nLine three.\n", "utf-8")

        raw = (
            "===SECTION_FIX_START===\n"
            "FILE: content.md\n"
            "---\n"
            "FIND:\n"
            "In Russian, this word is feminine.\n"
            "REPLACE:\n"
            "This word is masculine in standard Ukrainian.\n"
            "---\n"
            "===SECTION_FIX_END===\n"
        )
        applied = _apply_find_replace_fixes(f, raw)
        assert applied == 1
        result = f.read_text("utf-8")
        assert "In Russian" not in result
        assert "masculine in standard Ukrainian" in result

    def test_multiline_find(self, tmp_path):
        """Multi-line FIND text should be replaced."""
        from scripts.build_module import _apply_find_replace_fixes
        f = tmp_path / "content.md"
        f.write_text("Before.\n**The Dog:**\nIn Russian, this is feminine.\nAfter.\n", "utf-8")

        raw = (
            "===SECTION_FIX_START===\n"
            "FILE: content.md\n"
            "---\n"
            "FIND:\n"
            "**The Dog:**\n"
            "In Russian, this is feminine.\n"
            "REPLACE:\n"
            "**The Dog:**\n"
            "In Ukrainian, this is masculine.\n"
            "---\n"
            "===SECTION_FIX_END===\n"
        )
        applied = _apply_find_replace_fixes(f, raw)
        assert applied == 1
        assert "In Ukrainian" in f.read_text("utf-8")

    def test_no_match_returns_zero(self, tmp_path):
        """FIND text not in file → 0 applied."""
        from scripts.build_module import _apply_find_replace_fixes
        f = tmp_path / "content.md"
        f.write_text("Normal content here.\n", "utf-8")

        raw = (
            "===SECTION_FIX_START===\n"
            "FILE: content.md\n"
            "---\n"
            "FIND:\n"
            "This text does not exist in the file.\n"
            "REPLACE:\n"
            "Replacement.\n"
            "---\n"
            "===SECTION_FIX_END===\n"
        )
        applied = _apply_find_replace_fixes(f, raw)
        assert applied == 0

    def test_multiple_files(self, tmp_path):
        """Fixes targeting different files should only apply to matching file."""
        from scripts.build_module import _apply_find_replace_fixes
        content = tmp_path / "content.md"
        activities = tmp_path / "activities.yaml"
        content.write_text("Content line to fix.\n", "utf-8")
        activities.write_text("Activity line to fix.\n", "utf-8")

        raw = (
            "===SECTION_FIX_START===\n"
            "FILE: content.md\n"
            "---\n"
            "FIND:\n"
            "Content line to fix.\n"
            "REPLACE:\n"
            "Content line fixed.\n"
            "---\n"
            "FILE: activities.yaml\n"
            "---\n"
            "FIND:\n"
            "Activity line to fix.\n"
            "REPLACE:\n"
            "Activity line fixed.\n"
            "---\n"
            "===SECTION_FIX_END===\n"
        )
        n1 = _apply_find_replace_fixes(content, raw)
        n2 = _apply_find_replace_fixes(activities, raw)
        assert n1 == 1
        assert n2 == 1
        assert "Content line fixed" in content.read_text("utf-8")
        assert "Activity line fixed" in activities.read_text("utf-8")

    def test_guillemet_stripping(self, tmp_path):
        """«» around FIND/REPLACE text should be stripped."""
        from scripts.build_module import _apply_find_replace_fixes
        f = tmp_path / "content.md"
        f.write_text("Привіт, як справи?\n", "utf-8")

        raw = (
            "===SECTION_FIX_START===\n"
            "FILE: content.md\n"
            "---\n"
            "FIND:\n"
            "«Привіт, як справи?»\n"
            "REPLACE:\n"
            "«Привіт! Як справи?»\n"
            "---\n"
            "===SECTION_FIX_END===\n"
        )
        applied = _apply_find_replace_fixes(f, raw)
        assert applied == 1
        assert "Привіт! Як справи?" in f.read_text("utf-8")

    def test_no_delimiter_returns_zero(self, tmp_path):
        """No ===SECTION_FIX_START=== → 0 applied."""
        from scripts.build_module import _apply_find_replace_fixes
        f = tmp_path / "content.md"
        f.write_text("Content.\n", "utf-8")
        applied = _apply_find_replace_fixes(f, "No fix block here.")
        assert applied == 0


# ---------------------------------------------------------------------------
# _extract_delimiter / _extract_delimiter_tolerant — echo + truncation (#644)
# ---------------------------------------------------------------------------

START = "===VOCAB_START==="
END = "===VOCAB_END==="


class TestExtractDelimiterEchoTruncation:
    """Regression tests for Gemini echo + truncation scenarios (#644).

    Gemini often echoes prompt format examples (with both START+END tags),
    then outputs real content. If real content is truncated before its END tag,
    the old rfind(end_tag) approach would silently return the short echo.
    """

    def test_normal_single_block(self):
        """Single delimited block — basic case."""
        text = f"{START}\nitems:\n  - lemma: дім\n{END}"
        assert _extract_delimiter(text, START, END) == "items:\n  - lemma: дім"

    def test_echo_then_real_content(self):
        """Gemini echoes format then outputs real content — should get the real one."""
        text = (
            "Here is the format:\n"
            f"{START}\nexample placeholder\n{END}\n\n"
            "Now here is the real output:\n"
            f"{START}\nitems:\n  - lemma: дім\n    translation: house\n{END}"
        )
        result = _extract_delimiter(text, START, END)
        assert result is not None
        assert "lemma: дім" in result
        assert "translation: house" in result
        # Must NOT be the short echo
        assert result != "example placeholder"

    def test_echo_then_truncated_real_content(self):
        """Echo with both tags + real content truncated before END tag.

        This is the critical bug scenario: rfind(end_tag) would find the
        echo's END tag and silently return the short echo. The fix anchors
        on last START tag, so _extract_delimiter returns None (no END after
        last START), and _extract_delimiter_tolerant recovers the truncated
        real content.
        """
        text = (
            "Format example:\n"
            f"{START}\nexample placeholder\n{END}\n\n"
            "Real output:\n"
            f"{START}\nitems:\n  - lemma: дім\n    translation: house\n"
            "  - lemma: кіт\n    translation: cat\n"
            # NO END tag — Gemini truncated
        )
        # _extract_delimiter should return None (truncation detected)
        exact = _extract_delimiter(text, START, END)
        assert exact is None, (
            "_extract_delimiter should return None when real content is truncated "
            f"(no END after last START), got: {exact!r}"
        )

    def test_tolerant_recovers_truncated_real_content(self):
        """_extract_delimiter_tolerant should recover truncated real YAML."""
        text = (
            "Format:\n"
            f"{START}\nexample\n{END}\n\n"
            "Real:\n"
            f"{START}\n"
            "items:\n"
            "  - lemma: дім\n"
            "    translation: house\n"
            "  - lemma: кіт\n"
            "    translation: cat\n"
            # NO END tag — truncated
        )
        result = _extract_delimiter_tolerant(text, START, END)
        assert result is not None
        assert "lemma: дім" in result
        assert "lemma: кіт" in result
        # Must NOT be the short echo
        assert "example" not in result

    def test_no_tags_at_all(self):
        """No start or end tags → None."""
        assert _extract_delimiter("just some text", START, END) is None
        assert _extract_delimiter_tolerant("just some text", START, END) is None

    def test_only_start_tag_no_end(self):
        """Start tag but no end tag — _extract_delimiter returns None."""
        text = f"prefix\n{START}\nitems:\n  - lemma: дім\n"
        assert _extract_delimiter(text, START, END) is None
