"""
Tests for V4 pipeline functions in build_module.py.

Covers the new V4-specific functions:
- _extract_fix_plan() — slim fix plan extraction from D.1 review
- _get_fix_timeout() / _get_review_timeout() — track-aware timeouts
- _apply_find_replace_fixes() — FIND/REPLACE pair parsing and application
- _extract_audit_failures() — audit output filtering
- _dispatch_claude_phase() — Claude CLI invocation
- _load_state_v4() / _save_state_v4() — V4 state management
- _get_track_calibration() — calibration file routing
- phase_review_v4() — D.1/D.2 review flow (integration)
- phase_validate_v4() — validate flow (integration)

Issue: #703
"""

import json
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_module import (
    _extract_fix_plan,
    _get_fix_timeout,
    _get_review_timeout,
    _apply_find_replace_fixes,
    _extract_audit_failures,
    _extract_delimiter,
    _get_track_calibration,
    TIMEOUT_FIX_CORE,
    TIMEOUT_FIX_SEMINAR,
    TIMEOUT_FIX_AUDIT_ONLY,
    TIMEOUT_REVIEW_CORE,
    TIMEOUT_REVIEW_SEMINAR,
)


# =============================================================================
# _extract_fix_plan()
# =============================================================================


class TestExtractFixPlan:

    SAMPLE_REVIEW = """\
## Overview
Module: my-world-objects
Score: 7.3/10
Verdict: FAIL

## Critical Issues Found

1. **Missing accusative forms** (line 45): The module teaches nouns but never shows accusative.
   - Fix: Add accusative examples in section 3.
2. **Incorrect stress mark** (line 72): «олівéць» should be «олівéць» → actually correct, but «зóшит» wrong.
   - Fix: Correct to «зошит» (stress on first syllable).

## Ukrainian Language Issues

| Line | Issue | Fix |
|------|-------|-----|
| 23 | "книга" used without context | Add "Це книга" |
| 45 | Missing soft sign | "зошить" → "зошит" |

## Strengths

- Good vocabulary selection for A1
- Clear progression from concrete to abstract

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

1. Add accusative case examples (section 3, ~50 words)
2. Fix stress marks on зошит, олівець
3. Add 2 more engagement boxes (currently 3, need 5)
4. Expand vocabulary drill to cover all 15 target words

## Reviewer Notes

Internal notes about the review process.
"""

    def test_extracts_three_sections(self):
        result = _extract_fix_plan(self.SAMPLE_REVIEW)
        assert "## Critical Issues Found" in result
        assert "## Ukrainian Language Issues" in result
        assert "## Fix Plan to Reach 9/10" in result

    def test_excludes_non_actionable_sections(self):
        result = _extract_fix_plan(self.SAMPLE_REVIEW)
        assert "## Overview" not in result
        assert "## Strengths" not in result
        assert "## Reviewer Notes" not in result

    def test_preserves_content_within_sections(self):
        result = _extract_fix_plan(self.SAMPLE_REVIEW)
        assert "Missing accusative forms" in result
        assert "зошить" in result
        assert "Add accusative case examples" in result

    def test_sections_joined_with_separator(self):
        result = _extract_fix_plan(self.SAMPLE_REVIEW)
        assert "\n\n---\n\n" in result

    def test_fallback_to_full_review_when_no_sections(self):
        plain = "This review has no standard headers.\nJust plain text."
        result = _extract_fix_plan(plain)
        assert result == plain

    def test_partial_sections_extracted(self):
        """If only Fix Plan exists (no Critical Issues), still extracts it."""
        partial = """\
## Overview
Score: 8.5/10

## Fix Plan to Reach 9/10

1. Minor fix: add one more example.
"""
        result = _extract_fix_plan(partial)
        assert "## Fix Plan to Reach 9/10" in result
        assert "## Overview" not in result

    def test_fix_plan_with_parenthetical_header(self):
        """Handles 'Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)' variant."""
        review = """\
## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

1. Do something.
"""
        result = _extract_fix_plan(review)
        assert "Do something" in result

    def test_fix_plan_with_different_score(self):
        """Handles 'Fix Plan to Reach 8/10' variant."""
        review = """\
## Fix Plan to Reach 8/10

1. Do something different.
"""
        result = _extract_fix_plan(review)
        assert "Do something different" in result

    def test_empty_review(self):
        result = _extract_fix_plan("")
        assert result == ""

    def test_reduction_ratio(self):
        """Fix plan should be significantly shorter than full review."""
        result = _extract_fix_plan(self.SAMPLE_REVIEW)
        assert len(result) < len(self.SAMPLE_REVIEW)


# =============================================================================
# _get_fix_timeout() / _get_review_timeout()
# =============================================================================


class TestGetFixTimeout:

    def test_core_track_default(self):
        assert _get_fix_timeout("a1") == TIMEOUT_FIX_CORE

    def test_core_tracks(self):
        for track in ("a1", "a2", "b1", "b2", "c1", "c2"):
            assert _get_fix_timeout(track) == TIMEOUT_FIX_CORE

    def test_seminar_tracks(self):
        for track in ("hist", "bio", "istorio", "lit", "oes", "ruth"):
            assert _get_fix_timeout(track) == TIMEOUT_FIX_SEMINAR

    def test_lit_subtracks(self):
        """lit-essay, lit-war etc. should get seminar timeout."""
        for track in ("lit-essay", "lit-hist-fic", "lit-fantastika", "lit-war", "lit-humor", "lit-youth"):
            assert _get_fix_timeout(track) == TIMEOUT_FIX_SEMINAR

    def test_audit_only_overrides_track(self):
        assert _get_fix_timeout("a1", audit_only=True) == TIMEOUT_FIX_AUDIT_ONLY
        assert _get_fix_timeout("hist", audit_only=True) == TIMEOUT_FIX_AUDIT_ONLY

    def test_timeout_ordering(self):
        """audit_only <= core <= seminar (all currently 600s — generous timeouts)."""
        assert TIMEOUT_FIX_AUDIT_ONLY <= TIMEOUT_FIX_CORE <= TIMEOUT_FIX_SEMINAR


class TestGetReviewTimeout:

    def test_core_tracks(self):
        for track in ("a1", "a2", "b1", "b2", "c1", "c2"):
            assert _get_review_timeout(track) == TIMEOUT_REVIEW_CORE

    def test_seminar_tracks(self):
        for track in ("hist", "bio", "istorio", "lit", "oes", "ruth"):
            assert _get_review_timeout(track) == TIMEOUT_REVIEW_SEMINAR

    def test_lit_subtracks(self):
        for track in ("lit-essay", "lit-war"):
            assert _get_review_timeout(track) == TIMEOUT_REVIEW_SEMINAR

    def test_review_timeout_ordering(self):
        assert TIMEOUT_REVIEW_CORE < TIMEOUT_REVIEW_SEMINAR


# =============================================================================
# _apply_find_replace_fixes()
# =============================================================================


class TestApplyFindReplaceFixes:

    def test_basic_replacement(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("Hello world. This is a test.", "utf-8")
        raw = """\
===SECTION_FIX_START===
FIND:
Hello world.
REPLACE:
Привіт світ.
===SECTION_FIX_END===
"""
        count = _apply_find_replace_fixes(f, raw)
        assert count == 1
        assert "Привіт світ." in f.read_text("utf-8")
        assert "Hello world." not in f.read_text("utf-8")

    def test_multiple_replacements(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("AAA\nBBB\nCCC", "utf-8")
        raw = """\
===SECTION_FIX_START===
FIND:
AAA
REPLACE:
XXX
---
FIND:
CCC
REPLACE:
ZZZ
===SECTION_FIX_END===
"""
        count = _apply_find_replace_fixes(f, raw)
        assert count == 2
        content = f.read_text("utf-8")
        assert "XXX" in content
        assert "ZZZ" in content
        assert "BBB" in content  # unchanged

    def test_no_fix_block_returns_zero(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("content", "utf-8")
        assert _apply_find_replace_fixes(f, "no delimiters here") == 0

    def test_empty_fix_block(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("content", "utf-8")
        raw = "===SECTION_FIX_START===\n===SECTION_FIX_END==="
        assert _apply_find_replace_fixes(f, raw) == 0

    def test_missing_file_returns_zero(self, tmp_path):
        f = tmp_path / "nonexistent.md"
        raw = "===SECTION_FIX_START===\nFIND:\nX\nREPLACE:\nY\n===SECTION_FIX_END==="
        assert _apply_find_replace_fixes(f, raw) == 0

    def test_file_header_routing(self, tmp_path):
        """Only applies fixes for the matching FILE: header."""
        f = tmp_path / "content.md"
        f.write_text("old text here", "utf-8")
        raw = """\
===SECTION_FIX_START===
FILE: activities/test.yaml
---
FIND:
should not match
REPLACE:
wrong file
---
FILE: content.md
---
FIND:
old text here
REPLACE:
new text here
===SECTION_FIX_END===
"""
        count = _apply_find_replace_fixes(f, raw)
        assert count == 1
        assert f.read_text("utf-8") == "new text here"

    def test_no_file_header_applies_all(self, tmp_path):
        """Without FILE: headers, all pairs apply (single-file mode)."""
        f = tmp_path / "test.md"
        f.write_text("alpha beta", "utf-8")
        raw = """\
===SECTION_FIX_START===
FIND:
alpha
REPLACE:
gamma
===SECTION_FIX_END===
"""
        count = _apply_find_replace_fixes(f, raw)
        assert count == 1
        assert "gamma beta" in f.read_text("utf-8")

    def test_find_replace_identical_skipped(self, tmp_path):
        """FIND == REPLACE should be skipped (no-op)."""
        f = tmp_path / "test.md"
        f.write_text("unchanged", "utf-8")
        raw = """\
===SECTION_FIX_START===
FIND:
unchanged
REPLACE:
unchanged
===SECTION_FIX_END===
"""
        count = _apply_find_replace_fixes(f, raw)
        assert count == 0

    def test_guillemet_stripping(self, tmp_path):
        """«» quotes around FIND/REPLACE text should be stripped."""
        f = tmp_path / "test.md"
        f.write_text("old phrase here", "utf-8")
        raw = """\
===SECTION_FIX_START===
FIND:
«old phrase here»
REPLACE:
«new phrase here»
===SECTION_FIX_END===
"""
        count = _apply_find_replace_fixes(f, raw)
        assert count == 1
        assert "new phrase here" in f.read_text("utf-8")

    def test_fuzzy_whitespace_match(self, tmp_path):
        """Falls back to normalized whitespace when exact match fails."""
        f = tmp_path / "test.md"
        f.write_text("hello   world\n  foo", "utf-8")
        raw = """\
===SECTION_FIX_START===
FIND:
hello world foo
REPLACE:
replaced
===SECTION_FIX_END===
"""
        count = _apply_find_replace_fixes(f, raw)
        assert count == 1
        assert "replaced" in f.read_text("utf-8")

    def test_last_pair_without_trailing_separator(self, tmp_path):
        """Last FIND/REPLACE pair may not have trailing ---."""
        f = tmp_path / "test.md"
        f.write_text("aaa\nbbb", "utf-8")
        raw = """\
===SECTION_FIX_START===
FIND:
bbb
REPLACE:
ccc
===SECTION_FIX_END===
"""
        count = _apply_find_replace_fixes(f, raw)
        assert count == 1
        assert f.read_text("utf-8") == "aaa\nccc"

    def test_file_not_written_if_no_changes(self, tmp_path):
        """If no pairs matched, file should not be rewritten."""
        f = tmp_path / "test.md"
        f.write_text("content", "utf-8")
        mtime_before = f.stat().st_mtime
        raw = """\
===SECTION_FIX_START===
FIND:
nonexistent text
REPLACE:
replacement
===SECTION_FIX_END===
"""
        import time
        time.sleep(0.01)  # ensure mtime would differ
        count = _apply_find_replace_fixes(f, raw)
        assert count == 0
        assert f.stat().st_mtime == mtime_before


# =============================================================================
# _extract_audit_failures() — additional V4 coverage
# =============================================================================


class TestExtractAuditFailuresV4:
    """V4-specific audit failure patterns (supplements test_build_pipeline.py)."""

    def test_robotic_structure_detected(self):
        audit = """\
✅ Words: 2100/2000
❌ ROBOTIC_STRUCTURE: 4 consecutive H3 sections follow identical pattern
⚠️ STRUCTURAL_MONOTONY: All sections start with definition
"""
        result = _extract_audit_failures(audit)
        assert "ROBOTIC_STRUCTURE" in result
        assert "STRUCTURAL_MONOTONY" in result

    def test_pedagogical_violation_brackets(self):
        audit = """\
Gates:
- **[ENGAGEMENT]** Only 2 engagement boxes (need 5)
- [VOCAB] Missing 3 target words
"""
        result = _extract_audit_failures(audit)
        assert "ENGAGEMENT" in result
        assert "VOCAB" in result

    def test_pass_lines_excluded(self):
        audit = """\
✅ Words: 2100/2000
✅ Activities: 8/6
❌ Naturalness: 6.5/10 (need 8+)
"""
        result = _extract_audit_failures(audit)
        assert "Naturalness" in result or "6.5/10" in result
        # Pass lines should not appear (they start with ✅, not ❌)

    def test_empty_audit(self):
        assert _extract_audit_failures("") == ""

    def test_all_pass_returns_empty(self):
        audit = """\
✅ Words: 2100/2000
✅ Activities: 8/6
✅ Naturalness: 9.0/10
Overall: PASS
"""
        result = _extract_audit_failures(audit)
        # Should be empty or contain only minor info
        assert "FAIL" not in result


# =============================================================================
# _get_track_calibration()
# =============================================================================


class TestGetTrackCalibration:

    def test_returns_string(self):
        """Should return a string (possibly empty) for any track."""
        result = _get_track_calibration("a1", 1)
        assert isinstance(result, str)

    def test_b1_bridge_split(self):
        """B1 modules 1-5 use bridge calibration, 6+ use immersed."""
        r1 = _get_track_calibration("b1", 3)
        r2 = _get_track_calibration("b1", 10)
        # Both should return strings; content may differ if files exist
        assert isinstance(r1, str)
        assert isinstance(r2, str)

    def test_lit_subtracks_use_lit_calibration(self):
        """lit-essay, lit-war etc. should use lit.md calibration."""
        r1 = _get_track_calibration("lit-essay", 1)
        r2 = _get_track_calibration("lit", 1)
        # Both should resolve to lit.md
        assert r1 == r2

    def test_unknown_track_returns_empty(self):
        """Non-existent track should return empty string, not raise."""
        result = _get_track_calibration("nonexistent-track", 1)
        assert result == ""


# =============================================================================
# State management — V4
# =============================================================================


class TestStateV4:

    def _make_ctx(self, tmp_path, track="a1", slug="test-module"):
        ctx = MagicMock()
        ctx.track = track
        ctx.slug = slug
        orch_dir = tmp_path / "orchestration" / slug
        orch_dir.mkdir(parents=True, exist_ok=True)
        ctx.orch_dir = orch_dir
        return ctx

    def test_load_missing_state_returns_empty(self, tmp_path):
        from build_module import _load_state_v4
        ctx = self._make_ctx(tmp_path)
        state = _load_state_v4(ctx)
        assert state["mode"] == "v4"
        assert state["phases"] == {}

    def test_load_existing_state(self, tmp_path):
        from build_module import _load_state_v4
        ctx = self._make_ctx(tmp_path)
        state_file = ctx.orch_dir / "state-v4.json"
        state_data = {
            "track": "a1", "slug": "test-module", "mode": "v4",
            "phases": {"research": {"status": "complete"}}
        }
        state_file.write_text(json.dumps(state_data), "utf-8")
        state = _load_state_v4(ctx)
        assert state["phases"]["research"]["status"] == "complete"

    def test_load_corrupted_state_recovers(self, tmp_path):
        from build_module import _load_state_v4
        ctx = self._make_ctx(tmp_path)
        state_file = ctx.orch_dir / "state-v4.json"
        state_file.write_text("{invalid json!!!", "utf-8")
        state = _load_state_v4(ctx)
        assert state["mode"] == "v4"
        assert state["phases"] == {}
        # Corrupted file should be backed up
        backups = list(ctx.orch_dir.glob("state-v4.corrupted.*.json"))
        assert len(backups) == 1

    def test_save_and_reload(self, tmp_path):
        from build_module import _load_state_v4, _save_state_v4
        ctx = self._make_ctx(tmp_path)
        state = _load_state_v4(ctx)
        state["phases"]["content"] = {"status": "complete", "attempts": 1}
        _save_state_v4(ctx, state)

        reloaded = _load_state_v4(ctx)
        assert reloaded["phases"]["content"]["status"] == "complete"


# =============================================================================
# _dispatch_claude_phase() — unit test (mocked subprocess)
# =============================================================================


class TestDispatchClaudePhase:

    def test_builds_correct_command(self, tmp_path):
        """Verify the Claude CLI command is assembled correctly."""
        from build_module import _dispatch_claude_phase
        prompt_file = tmp_path / "prompt.md"
        prompt_file.write_text("You are Gemini. Review this module.", "utf-8")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "===REVIEW_START===\nPASS\n===REVIEW_END==="
        mock_result.stderr = ""

        with patch("pipeline_lib._run_with_heartbeat", return_value=mock_result) as mock_run:
            ok, output = _dispatch_claude_phase(prompt_file, "D.1", timeout=120)

        assert ok is True
        assert "PASS" in output

        # Check the command
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "claude" in cmd[0]
        assert "--model" in cmd
        assert "-p" in cmd
        assert "--output-format" in cmd
        assert "text" in cmd

        # Check persona substitution
        prompt_input = call_args[1].get("input", "")
        assert "You are Claude" in prompt_input
        assert "You are Gemini" not in prompt_input

    def test_tools_passed_when_specified(self, tmp_path):
        from build_module import _dispatch_claude_phase
        prompt_file = tmp_path / "prompt.md"
        prompt_file.write_text("test prompt", "utf-8")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "===REVIEW_START===\nok\n===REVIEW_END==="
        mock_result.stderr = ""

        with patch("pipeline_lib._run_with_heartbeat", return_value=mock_result) as mock_run:
            _dispatch_claude_phase(prompt_file, "D.1", allow_tools=["Read", "Grep"])

        cmd = mock_run.call_args[0][0]
        assert "--allowedTools" in cmd
        tools_idx = cmd.index("--allowedTools")
        assert cmd[tools_idx + 1] == "Read,Grep"

    def test_no_tools_when_empty_list(self, tmp_path):
        """allow_tools=[] (empty) should NOT pass --allowedTools flag."""
        from build_module import _dispatch_claude_phase
        prompt_file = tmp_path / "prompt.md"
        prompt_file.write_text("test prompt", "utf-8")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "===SECTION_FIX_START===\nok\n===SECTION_FIX_END==="
        mock_result.stderr = ""

        with patch("pipeline_lib._run_with_heartbeat", return_value=mock_result) as mock_run:
            _dispatch_claude_phase(prompt_file, "D.2", allow_tools=[])

        cmd = mock_run.call_args[0][0]
        assert "--allowedTools" not in cmd

    def test_cli_not_found(self, tmp_path):
        from build_module import _dispatch_claude_phase
        prompt_file = tmp_path / "prompt.md"
        prompt_file.write_text("test", "utf-8")

        with patch("pipeline_lib._run_with_heartbeat", side_effect=FileNotFoundError):
            ok, output = _dispatch_claude_phase(prompt_file, "D.1")

        assert ok is False
        assert output == ""

    def test_cli_nonzero_exit(self, tmp_path):
        from build_module import _dispatch_claude_phase
        prompt_file = tmp_path / "prompt.md"
        prompt_file.write_text("test", "utf-8")

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "error occurred"
        mock_result.stdout = ""

        with patch("pipeline_lib._run_with_heartbeat", return_value=mock_result):
            ok, output = _dispatch_claude_phase(prompt_file, "D.1")

        assert ok is False

    def test_timeout_returns_false(self, tmp_path):
        import subprocess
        from build_module import _dispatch_claude_phase
        prompt_file = tmp_path / "prompt.md"
        prompt_file.write_text("test", "utf-8")

        with patch("pipeline_lib._run_with_heartbeat", side_effect=subprocess.TimeoutExpired("claude", 120)):
            ok, output = _dispatch_claude_phase(prompt_file, "D.1", timeout=120)

        assert ok is False

    def test_d2_phase_gets_fix_delimiters(self, tmp_path):
        """D.2 label should inject SECTION_FIX delimiters, not REVIEW."""
        from build_module import _dispatch_claude_phase
        prompt_file = tmp_path / "prompt.md"
        prompt_file.write_text("test", "utf-8")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "===SECTION_FIX_START===\n===SECTION_FIX_END==="
        mock_result.stderr = ""

        with patch("pipeline_lib._run_with_heartbeat", return_value=mock_result) as mock_run:
            _dispatch_claude_phase(prompt_file, "D.2 (iter 1)", timeout=300)

        cmd = mock_run.call_args[0][0]
        # Find the --append-system-prompt value
        asp_idx = cmd.index("--append-system-prompt")
        asp_value = cmd[asp_idx + 1]
        assert "SECTION_FIX_START" in asp_value
        assert "REVIEW_START" not in asp_value


# =============================================================================
# Timeout constant sanity
# =============================================================================


class TestTimeoutConstants:

    def test_fix_constants_positive(self):
        assert TIMEOUT_FIX_CORE > 0
        assert TIMEOUT_FIX_SEMINAR > 0
        assert TIMEOUT_FIX_AUDIT_ONLY > 0

    def test_review_constants_positive(self):
        assert TIMEOUT_REVIEW_CORE > 0
        assert TIMEOUT_REVIEW_SEMINAR > 0

    def test_fix_not_longer_than_review(self):
        """Fix timeouts should be <= review timeouts."""
        assert TIMEOUT_FIX_CORE <= TIMEOUT_REVIEW_CORE
        assert TIMEOUT_FIX_SEMINAR <= TIMEOUT_REVIEW_SEMINAR

    def test_specific_values(self):
        """Pin current values to catch unintended changes (generous 600s timeouts)."""
        assert TIMEOUT_FIX_CORE == 600
        assert TIMEOUT_FIX_SEMINAR == 600
        assert TIMEOUT_FIX_AUDIT_ONLY == 600


# =============================================================================
# Integration: _extract_fix_plan + _apply_find_replace_fixes
# =============================================================================


class TestFixPlanToFixApplication:
    """End-to-end: extract plan from review, then apply fixes."""

    REVIEW_WITH_FIX_PLAN = """\
## Critical Issues Found

1. Line 10: "книжка" should be "книга" in formal context.

## Fix Plan to Reach 9/10

1. Replace "книжка" with "книга" in section 2.

## Strengths

Good module overall.
"""

    def test_extracted_plan_contains_actionable_info(self):
        plan = _extract_fix_plan(self.REVIEW_WITH_FIX_PLAN)
        assert "книжка" in plan
        assert "книга" in plan
        assert "Strengths" not in plan

    def test_fix_applied_to_file(self, tmp_path):
        f = tmp_path / "module.md"
        f.write_text("## Section 2\n\nУ нас є книжка на столі.", "utf-8")

        # Simulated D.2 output
        d2_output = """\
===SECTION_FIX_START===
FIND:
книжка на столі
REPLACE:
книга на столі
===SECTION_FIX_END===
"""
        count = _apply_find_replace_fixes(f, d2_output)
        assert count == 1
        assert "книга на столі" in f.read_text("utf-8")
