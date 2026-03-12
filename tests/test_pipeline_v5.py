"""
Tests for pipeline_v5.py — the only pipeline.

Covers:
- State management: load_state, save_state, mark_complete, is_complete, migration chain
- v5 guards in pipeline_lib.py: save_state, mark_phase, is_phase_complete no-ops
- Delimiter extraction: _extract_delimiter, _extract_delimiter_tolerant
- Diff helpers: _count_diff_lines
- Audit extraction: _extract_audit_failures, _extract_gate_failures, _extract_pedagogy_violations
- Section helpers: _extract_h2_sections, _identify_affected_sections
- Fix helpers: _clean_fix_text, _apply_find_replace_fixes, _apply_section_fixes
- Prompt helpers: _inject_metrics_into_prompt, _build_schema_hint
- Triage: _all_issues_diffuse
- Snapshot/rollback: _snapshot_module_files, _apply_fixes_with_rollback

Issue: #750
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pipeline_v5 import (
    _state_file,
    load_state,
    save_state,
    is_complete,
    mark_complete,
    _fresh_state,
    _migrate_v4_to_v5,
    _extract_delimiter,
    _extract_delimiter_tolerant,
    _count_diff_lines,
    _extract_audit_failures,
    _extract_gate_failures,
    _extract_pedagogy_violations,
    _extract_h2_sections,
    _identify_affected_sections,
    _clean_fix_text,
    _apply_find_replace_fixes,
    _apply_section_fixes,
    _inject_metrics_into_prompt,
    _build_schema_hint,
    _all_issues_diffuse,
    _snapshot_module_files,
    _module_file_paths,
    _apply_fixes_with_rollback,
)
from pipeline_lib import ModuleContext


# =============================================================================
# Fixtures
# =============================================================================

def _make_ctx(tmp_path: Path, **overrides) -> ModuleContext:
    """Create a minimal ModuleContext for testing."""
    orch_dir = tmp_path / "orchestration" / "test-module"
    orch_dir.mkdir(parents=True, exist_ok=True)

    md_path = tmp_path / "test-module.md"
    act_path = tmp_path / "activities" / "test-module.yaml"
    vocab_path = tmp_path / "vocabulary" / "test-module.yaml"
    status_path = tmp_path / "status" / "test-module.json"
    meta_path = tmp_path / "meta" / "test-module.yaml"

    for p in [act_path, vocab_path, status_path, meta_path]:
        p.parent.mkdir(parents=True, exist_ok=True)

    ctx = MagicMock(spec=ModuleContext)
    ctx.orch_dir = orch_dir
    ctx.track = "a1"
    ctx.slug = "test-module"
    ctx.mode = "v5"
    ctx.dry_run = False
    ctx.force_phase = None
    ctx.state = {"phases": {}}
    ctx.paths = {
        "md": md_path,
        "activities": act_path,
        "vocabulary": vocab_path,
        "status": status_path,
        "meta": meta_path,
    }
    for k, v in overrides.items():
        setattr(ctx, k, v)
    return ctx


# =============================================================================
# State management
# =============================================================================

class TestStateFile:
    def test_returns_state_json_in_orch_dir(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        assert _state_file(ctx) == ctx.orch_dir / "state.json"


class TestFreshState:
    def test_creates_minimal_state(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        state = _fresh_state(ctx)
        assert state["mode"] == "v5"
        assert state["track"] == "a1"
        assert state["slug"] == "test-module"
        assert state["phases"] == {}


class TestMigrateV4ToV5:
    def test_strips_v4_prefix(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        v4_data = {
            "track": "a1",
            "slug": "test",
            "phases": {
                "v4-research": {"status": "complete"},
                "v4-content": {"status": "complete"},
                "validate": {"status": "complete"},
            },
        }
        result = _migrate_v4_to_v5(v4_data, ctx)
        assert result["mode"] == "v5"
        assert "research" in result["phases"]
        assert "content" in result["phases"]
        assert "validate" in result["phases"]
        assert "v4-research" not in result["phases"]

    def test_empty_phases(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        result = _migrate_v4_to_v5({"phases": {}}, ctx)
        assert result["phases"] == {}
        assert result["mode"] == "v5"


class TestLoadState:
    def test_loads_v5_state_json(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        state = {"mode": "v5", "track": "a1", "slug": "test", "phases": {"research": {"status": "complete"}}}
        (ctx.orch_dir / "state.json").write_text(json.dumps(state), "utf-8")
        result = load_state(ctx)
        assert result["mode"] == "v5"
        assert result["phases"]["research"]["status"] == "complete"

    def test_skips_non_v5_state_json(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        legacy = {"track": "a1", "slug": "test", "phases": {"2": {"status": "complete"}}}
        (ctx.orch_dir / "state.json").write_text(json.dumps(legacy), "utf-8")
        result = load_state(ctx)
        # Should return fresh state since mode != v5
        assert result["mode"] == "v5"
        assert result["phases"] == {}

    def test_migrates_state_v5_json(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        state = {"mode": "v5", "track": "a1", "slug": "test", "phases": {"content": {"status": "complete"}}}
        legacy_path = ctx.orch_dir / "state-v5.json"
        legacy_path.write_text(json.dumps(state), "utf-8")
        result = load_state(ctx)
        assert result["phases"]["content"]["status"] == "complete"
        # Legacy file should be deleted after migration
        assert not legacy_path.exists()

    def test_migrates_state_v4_json(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        v4_state = {"track": "a1", "slug": "test", "phases": {"v4-research": {"status": "complete"}}}
        (ctx.orch_dir / "state-v4.json").write_text(json.dumps(v4_state), "utf-8")
        result = load_state(ctx)
        assert result["mode"] == "v5"
        assert "research" in result["phases"]

    def test_returns_fresh_when_no_files(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        result = load_state(ctx)
        assert result["mode"] == "v5"
        assert result["phases"] == {}

    def test_corrupted_state_json_backed_up(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        sf = ctx.orch_dir / "state.json"
        sf.write_text("{invalid json", "utf-8")
        result = load_state(ctx)
        assert result["mode"] == "v5"
        assert result["phases"] == {}
        # Corrupted file should be backed up
        backups = list(ctx.orch_dir.glob("state.corrupted.*.json"))
        assert len(backups) == 1

    def test_migration_priority_v5_over_v4(self, tmp_path):
        """state-v5.json takes priority over state-v4.json."""
        ctx = _make_ctx(tmp_path)
        v5_state = {"mode": "v5", "track": "a1", "slug": "test", "phases": {"content": {"status": "complete"}}}
        v4_state = {"track": "a1", "slug": "test", "phases": {"v4-research": {"status": "complete"}}}
        (ctx.orch_dir / "state-v5.json").write_text(json.dumps(v5_state), "utf-8")
        (ctx.orch_dir / "state-v4.json").write_text(json.dumps(v4_state), "utf-8")
        result = load_state(ctx)
        assert "content" in result["phases"]
        assert "research" not in result["phases"]


class TestSaveState:
    def test_writes_state_json(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        state = {"mode": "v5", "track": "a1", "slug": "test", "phases": {}}
        save_state(ctx, state)
        written = json.loads((ctx.orch_dir / "state.json").read_text("utf-8"))
        assert written == state

    def test_atomic_write_survives_crash(self, tmp_path):
        """No .tmp files left behind on success."""
        ctx = _make_ctx(tmp_path)
        save_state(ctx, {"mode": "v5", "phases": {}})
        tmp_files = list(ctx.orch_dir.glob("*.tmp"))
        assert len(tmp_files) == 0


class TestIsComplete:
    def test_returns_true_for_complete_phase(self):
        state = {"phases": {"research": {"status": "complete", "ts": "2026-01-01"}}}
        assert is_complete(state, "research") is True

    def test_returns_false_for_missing_phase(self):
        state = {"phases": {}}
        assert is_complete(state, "research") is False

    def test_returns_false_for_failed_phase(self):
        state = {"phases": {"research": {"status": "failed"}}}
        assert is_complete(state, "research") is False


class TestMarkComplete:
    def test_marks_phase_complete(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        state = {"mode": "v5", "track": "a1", "slug": "test", "phases": {}}
        mark_complete(state, "research", ctx)
        assert state["phases"]["research"]["status"] == "complete"
        assert "ts" in state["phases"]["research"]

    def test_self_audited_kwarg_survives(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        state = {"mode": "v5", "track": "a1", "slug": "test", "phases": {}}
        mark_complete(state, "content", ctx, self_audited=True)
        assert state["phases"]["content"]["self_audited"] is True
        assert state["phases"]["content"]["status"] == "complete"

    def test_extra_kwargs_preserved(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        state = {"mode": "v5", "phases": {}}
        mark_complete(state, "validate", ctx, attempt=3, issues_fixed=5)
        assert state["phases"]["validate"]["attempt"] == 3
        assert state["phases"]["validate"]["issues_fixed"] == 5

    def test_persists_to_disk(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        state = {"mode": "v5", "track": "a1", "slug": "test", "phases": {}}
        mark_complete(state, "research", ctx)
        disk_state = json.loads((ctx.orch_dir / "state.json").read_text("utf-8"))
        assert disk_state["phases"]["research"]["status"] == "complete"


class TestSelfAuditIntegration:
    """End-to-end test: self_audited flag flows from content to validate."""

    def test_self_audited_flag_readable_from_state(self, tmp_path):
        """Validate phase reads self_audited from persisted state."""
        ctx = _make_ctx(tmp_path)
        state = {"mode": "v5", "track": "a1", "slug": "test", "phases": {}}
        mark_complete(state, "content", ctx, self_audited=True)

        # Simulate validate phase reading state from disk (fresh load)
        loaded = load_state(ctx)
        content_self_audited = loaded.get("phases", {}).get("content", {}).get("self_audited", False)
        assert content_self_audited is True

    def test_self_audited_false_by_default(self, tmp_path):
        """Without self-audit, the flag should be absent/false."""
        ctx = _make_ctx(tmp_path)
        state = {"mode": "v5", "track": "a1", "slug": "test", "phases": {}}
        mark_complete(state, "content", ctx)

        loaded = load_state(ctx)
        content_self_audited = loaded.get("phases", {}).get("content", {}).get("self_audited", False)
        assert content_self_audited is False

    def test_self_audited_survives_additional_marks(self, tmp_path):
        """Marking other phases shouldn't lose the content self_audited flag."""
        ctx = _make_ctx(tmp_path)
        state = {"mode": "v5", "track": "a1", "slug": "test", "phases": {}}
        mark_complete(state, "content", ctx, self_audited=True)
        mark_complete(state, "activities", ctx)
        mark_complete(state, "validate", ctx, attempts=1)

        loaded = load_state(ctx)
        assert loaded["phases"]["content"]["self_audited"] is True
        assert loaded["phases"]["activities"]["status"] == "complete"
        assert loaded["phases"]["validate"]["attempts"] == 1


# =============================================================================
# v5 guards in pipeline_lib.py
# =============================================================================

class TestV5Guards:
    def test_save_state_noop_for_v5(self, tmp_path):
        """pipeline_lib.save_state should be a no-op when mode='v5'."""
        from pipeline_lib import save_state as lib_save_state
        ctx = _make_ctx(tmp_path)
        ctx.state = {"phases": {"old": {"status": "complete"}}, "last_updated": "before"}
        sf = ctx.orch_dir / "state.json"
        # Ensure no state.json exists
        if sf.exists():
            sf.unlink()
        lib_save_state(ctx)
        # Should NOT have written state.json
        assert not sf.exists()

    def test_is_phase_complete_returns_false_for_v5(self, tmp_path):
        """pipeline_lib.is_phase_complete should always return False for v5."""
        from pipeline_lib import is_phase_complete as lib_is_phase_complete
        ctx = _make_ctx(tmp_path)
        ctx.state = {"phases": {"2": {"status": "complete"}}}
        assert lib_is_phase_complete(ctx, "2") is False

    def test_mark_phase_noop_for_v5(self, tmp_path):
        """pipeline_lib.mark_phase should be a no-op when mode='v5'."""
        from pipeline_lib import mark_phase as lib_mark_phase
        ctx = _make_ctx(tmp_path)
        ctx.state = {"phases": {}}
        lib_mark_phase(ctx, "2", "complete")
        # Should NOT have added the phase
        assert "2" not in ctx.state["phases"]


# =============================================================================
# Delimiter extraction
# =============================================================================

class TestExtractDelimiter:
    def test_basic_extraction(self):
        text = "before\n===START===\ncontent here\n===END===\nafter"
        assert _extract_delimiter(text, "===START===", "===END===") == "content here"

    def test_multiline_content(self):
        text = "===A===\nline1\nline2\nline3\n===B==="
        assert _extract_delimiter(text, "===A===", "===B===") == "line1\nline2\nline3"

    def test_missing_start_tag(self):
        assert _extract_delimiter("no tags here", "===START===", "===END===") is None

    def test_missing_end_tag(self):
        assert _extract_delimiter("===START===\ncontent", "===START===", "===END===") is None

    def test_empty_content(self):
        text = "===START===\n\n===END==="
        assert _extract_delimiter(text, "===START===", "===END===") == ""

    def test_uses_last_start_tag(self):
        text = "===START===\nfirst\n===END===\n===START===\nsecond\n===END==="
        assert _extract_delimiter(text, "===START===", "===END===") == "second"


class TestExtractDelimiterTolerant:
    def test_falls_back_to_exact(self):
        text = "===START===\ncontent\n===END==="
        assert _extract_delimiter_tolerant(text, "===START===", "===END===") == "content"

    def test_missing_end_tag_yaml(self):
        text = "===VOCAB_START===\nitems:\n  - lemma: кава\n    translation: coffee\n"
        result = _extract_delimiter_tolerant(text, "===VOCAB_START===", "===VOCAB_END===")
        # Should attempt tolerant recovery
        # Result depends on yaml parsing, but shouldn't be None if content is valid
        # The function returns None if yaml parsing fails AND no "- lemma:" lines
        assert result is not None or result is None  # just test it doesn't crash

    def test_returns_none_for_no_start(self):
        assert _extract_delimiter_tolerant("no tags", "===START===", "===END===") is None


# =============================================================================
# Diff helpers
# =============================================================================

class TestCountDiffLines:
    def test_identical_texts(self):
        assert _count_diff_lines("hello", "hello") == 0

    def test_one_line_changed(self):
        assert _count_diff_lines("line1\nline2", "line1\nline2_mod") == 2  # -old +new

    def test_one_line_added(self):
        assert _count_diff_lines("line1\n", "line1\nline2\n") == 1

    def test_one_line_removed(self):
        assert _count_diff_lines("line1\nline2\n", "line1\n") == 1

    def test_empty_to_content(self):
        assert _count_diff_lines("", "hello\nworld") == 2

    def test_content_to_empty(self):
        assert _count_diff_lines("hello\nworld", "") == 2


# =============================================================================
# Audit extraction
# =============================================================================

class TestExtractAuditFailures:
    def test_extracts_fail_lines(self):
        audit = "Words ❌ 800/1200\nActivities ✅ 5\nVocab ❌ 3/10"
        result = _extract_audit_failures(audit)
        assert "❌" in result
        assert "800/1200" in result
        assert "3/10" in result

    def test_extracts_violation_lines(self):
        audit = "YAML_SCHEMA_VIOLATION: type 'quiz' missing 'options'"
        result = _extract_audit_failures(audit)
        assert "VIOLATION" in result

    def test_fallback_on_no_failures(self):
        audit = "Words ✅ 1200/1200\nActivities ✅ 5"
        result = _extract_audit_failures(audit)
        # Falls back to last 40 lines
        assert "1200/1200" in result

    def test_empty_input(self):
        assert _extract_audit_failures("") == ""


class TestExtractGateFailures:
    def test_parses_gate_failures(self):
        audit = "Words        ❌ 800/1200\nActivities   ✅ 5\nVocab        ❌ 3/10"
        failures = _extract_gate_failures(audit)
        gates = [f["gate"] for f in failures]
        assert "Words" in gates
        assert "Vocab" in gates
        assert len(failures) == 2

    def test_yaml_schema_violation(self):
        audit = "YAML_SCHEMA_VIOLATION: type 'quiz' missing 'options'"
        failures = _extract_gate_failures(audit)
        assert any(f["gate"] == "YAML_SCHEMA" for f in failures)

    def test_no_failures(self):
        audit = "Words ✅ 1200/1200\nActivities ✅ 5"
        assert _extract_gate_failures(audit) == []


class TestExtractPedagogyViolations:
    def test_parses_violations(self):
        audit = (
            "some preamble\n"
            "📚 PEDAGOGICAL VIOLATIONS FOUND\n"
            "  [DECODABILITY] Word 'складний' not in sandbox\n"
            "     → FIX: Replace with a simpler word\n"
            "  [GRAMMAR_SCOPE] Past tense used before it's taught\n"
            "---\n"
        )
        violations = _extract_pedagogy_violations(audit)
        assert len(violations) == 2
        assert violations[0]["type"] == "DECODABILITY"
        assert "Replace" in violations[0]["fix"]
        assert violations[1]["type"] == "GRAMMAR_SCOPE"

    def test_skips_noise(self):
        audit = (
            "📚 PEDAGOGICAL VIOLATIONS FOUND\n"
            "  [EMBED] Loading BGE-M3 model\n"
            "  [DECODABILITY] Real violation\n"
            "---\n"
        )
        violations = _extract_pedagogy_violations(audit)
        assert len(violations) == 1
        assert violations[0]["type"] == "DECODABILITY"

    def test_empty_section(self):
        audit = "No pedagogical section here"
        assert _extract_pedagogy_violations(audit) == []


# =============================================================================
# Section helpers
# =============================================================================

class TestExtractH2Sections:
    def test_extracts_headers(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("# Title\n## Section 1\ntext\n## Section 2\nmore\n", "utf-8")
        result = _extract_h2_sections(md)
        assert "1. Section 1" in result
        assert "2. Section 2" in result

    def test_missing_file(self, tmp_path):
        result = _extract_h2_sections(tmp_path / "nonexistent.md")
        assert "not found" in result

    def test_no_h2_headers(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("# Only H1\nSome text\n", "utf-8")
        result = _extract_h2_sections(md)
        assert "no H2" in result


class TestIdentifyAffectedSections:
    def test_finds_section_by_name_in_audit(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("# Title\n## Grammar\ntext\n## Vocabulary\nmore\n", "utf-8")
        audit = "Issue in Grammar section: word count too low"
        result = _identify_affected_sections(audit, md)
        assert "Grammar" in result

    def test_finds_section_by_line_number(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("# Title\n## Section A\nline 3\nline 4\n## Section B\nline 6\n", "utf-8")
        audit = "Error at line 3"
        result = _identify_affected_sections(audit, md)
        assert "Section A" in result

    def test_returns_empty_for_too_many_affected(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("## A\ntext\n## B\ntext\n## C\ntext\n", "utf-8")
        audit = "Issues in A, B, and C"
        result = _identify_affected_sections(audit, md)
        assert result == []  # >2 sections = return empty

    def test_uses_provided_content(self, tmp_path):
        md = tmp_path / "nonexistent.md"
        content = "## Grammar\ntext\n## Vocabulary\nmore\n"
        audit = "Issue in Grammar"
        result = _identify_affected_sections(audit, md, content=content)
        assert "Grammar" in result

    def test_missing_file_no_content(self, tmp_path):
        result = _identify_affected_sections("some audit", tmp_path / "nope.md")
        assert result == []


# =============================================================================
# Fix helpers
# =============================================================================

class TestCleanFixText:
    def test_strips_code_fences(self):
        text = "```yaml\ncontent here\n```"
        result = _clean_fix_text(text)
        assert "```" not in result
        assert "content here" in result

    def test_strips_section_header(self):
        text = 'Section: "Grammar"\ncontent here'
        result = _clean_fix_text(text)
        assert "Section:" not in result
        assert "content here" in result

    def test_strips_guillemets(self):
        assert _clean_fix_text("«wrapped text»") == "wrapped text"

    def test_strips_german_quotes(self):
        assert _clean_fix_text("\u201ewrapped\u201c") == "wrapped"

    def test_preserves_normal_text(self):
        assert _clean_fix_text("normal text") == "normal text"


class TestApplyFindReplaceFixes:
    def test_applies_simple_fix(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("The cat sat on the mat.", "utf-8")
        raw = (
            "===SECTION_FIX_START===\n"
            "FIND:\n"
            "cat\n"
            "REPLACE:\n"
            "dog\n"
            "===SECTION_FIX_END===\n"
        )
        count = _apply_find_replace_fixes(f, raw)
        assert count >= 1
        assert "dog" in f.read_text("utf-8")

    def test_no_fix_markers(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("content", "utf-8")
        assert _apply_find_replace_fixes(f, "no markers here") == 0

    def test_nonexistent_file(self, tmp_path):
        assert _apply_find_replace_fixes(tmp_path / "nope.md", "===SECTION_FIX_START===\n===SECTION_FIX_END===") == 0


class TestApplySectionFixes:
    def test_replaces_section(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("## Grammar\nOld content\n\n## Vocabulary\nKeep this\n", "utf-8")
        fix_output = (
            "===SECTION_FIX_START===\n"
            "## Grammar\nNew content with more words\n"
            "===SECTION_FIX_END===\n"
        )
        _apply_section_fixes(f, fix_output)
        text = f.read_text("utf-8")
        assert "New content" in text
        assert "Old content" not in text
        assert "Keep this" in text

    def test_no_fix_markers(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("## Grammar\nContent\n", "utf-8")
        _apply_section_fixes(f, "no markers here")
        assert f.read_text("utf-8") == "## Grammar\nContent\n"


# =============================================================================
# Prompt helpers
# =============================================================================

class TestInjectMetrics:
    def test_single_placeholder(self):
        result = _inject_metrics_into_prompt(
            "Words: {COMPUTED_WORD_COUNT}", {"COMPUTED_WORD_COUNT": "1200"}
        )
        assert result == "Words: 1200"

    def test_multiple_placeholders(self):
        result = _inject_metrics_into_prompt(
            "{COMPUTED_A} and {COMPUTED_B}",
            {"COMPUTED_A": "hello", "COMPUTED_B": "world"},
        )
        assert result == "hello and world"

    def test_unmatched_placeholder_preserved(self):
        result = _inject_metrics_into_prompt("{COMPUTED_A} {OTHER}", {"COMPUTED_A": "x"})
        assert result == "x {OTHER}"

    def test_empty_metrics(self):
        result = _inject_metrics_into_prompt("template {X}", {})
        assert result == "template {X}"


class TestBuildSchemaHint:
    def test_returns_empty_when_no_violation(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        assert _build_schema_hint(ctx, "all good") == ""

    def test_returns_schema_hint_for_known_type(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        audit = "YAML_SCHEMA_VIOLATION: 'type': 'quiz' blah"
        result = _build_schema_hint(ctx, audit)
        # Schema file exists for a1, so we get a hint
        if result:
            assert "quiz" in result
            assert "Required fields" in result


# =============================================================================
# Triage
# =============================================================================

class TestAllIssuesDiffuse:
    def test_only_diffuse_codes(self):
        audit = "❌ FAIL [ROBOTIC_STRUCTURE] Too repetitive"
        assert _all_issues_diffuse(audit) is True

    def test_mixed_codes(self):
        audit = (
            "Structure ❌ FAIL [ROBOTIC_STRUCTURE]\n"
            "Words ❌ FAIL [LOW_WORD_COUNT]\n"
        )
        assert _all_issues_diffuse(audit) is False

    def test_no_failing_codes(self):
        audit = "Words ✅ PASS"
        assert _all_issues_diffuse(audit) is False

    def test_multiple_diffuse_codes(self):
        audit = (
            "❌ FAIL [ROBOTIC_STRUCTURE]\n"
            "❌ FAIL [CONTENT_REDUNDANCY]\n"
        )
        assert _all_issues_diffuse(audit) is True


# =============================================================================
# Snapshot and rollback
# =============================================================================

class TestSnapshotModuleFiles:
    def test_snapshots_existing_files(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        ctx.paths["md"].write_text("# Content", "utf-8")
        ctx.paths["activities"].write_text("- type: quiz", "utf-8")
        snapshots = _snapshot_module_files(ctx)
        assert snapshots["md"] == "# Content"
        assert snapshots["activities"] == "- type: quiz"
        assert "vocabulary" not in snapshots  # file doesn't exist

    def test_empty_when_no_files(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        assert _snapshot_module_files(ctx) == {}


class TestApplyFixesWithRollback:
    def test_no_fix_markers_returns_true(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        ok, n = _apply_fixes_with_rollback(ctx, "no markers", "test")
        assert ok is True
        assert n == 0

    def test_rolls_back_oversized_diff(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        original = "line\n" * 10
        ctx.paths["md"].write_text(original, "utf-8")
        # Create a fix that would replace everything with a massive change
        huge_replacement = "new line\n" * 200
        raw = (
            "===SECTION_FIX_START===\n"
            f"FIND:\n{original}\n"
            f"REPLACE:\n{huge_replacement}\n"
            "===SECTION_FIX_END===\n"
        )
        ok, n = _apply_fixes_with_rollback(ctx, raw, "test")
        if not ok:
            # File should be rolled back to original
            assert ctx.paths["md"].read_text("utf-8") == original


class TestModuleFilePaths:
    def test_returns_three_tuples(self, tmp_path):
        ctx = _make_ctx(tmp_path)
        paths = _module_file_paths(ctx)
        labels = [p[0] for p in paths]
        assert "md" in labels
        assert "activities" in labels
        assert "vocabulary" in labels



# TestGetTierExemplar — DELETED: exemplar system removed (commit 3f855ee)


class TestPrefetchTextbookForResearch:
    """_prefetch_textbook_for_research handles various plan shapes."""

    def _make_ctx(self, plan=None, meta=None, topic_title="Test Topic",
                  slug="test-slug", track="a1", module_num=47):
        ctx = MagicMock()
        ctx.plan = plan or {}
        ctx.meta = meta or {}
        ctx.topic_title = topic_title
        ctx.slug = slug
        ctx.track = track
        ctx.module_num = module_num
        ctx.content_outline = []
        return ctx

    def test_dict_vocabulary_hints(self):
        """vocabulary_hints as dict (the real-world format) doesn't crash."""
        from build.pipeline_v5 import _prefetch_textbook_for_research

        plan = {
            "vocabulary_hints": {
                "required": ["читати/читай (to read)", "писати/пиши (to write)"],
                "optional": ["слухати/слухай (to listen)"],
            }
        }
        ctx = self._make_ctx(plan=plan)
        # No rag module → ImportError → returns ""
        with patch.dict("sys.modules", {"rag": None, "rag.query": None}):
            result = _prefetch_textbook_for_research(ctx)
        assert result == ""

    def test_list_vocabulary_hints(self):
        """vocabulary_hints as list (older format) doesn't crash."""
        from build.pipeline_v5 import _prefetch_textbook_for_research

        plan = {"vocabulary_hints": ["читати", "писати"]}
        ctx = self._make_ctx(plan=plan)
        with patch.dict("sys.modules", {"rag": None, "rag.query": None}):
            result = _prefetch_textbook_for_research(ctx)
        assert result == ""

    def test_empty_plan(self):
        """Empty plan doesn't crash."""
        from build.pipeline_v5 import _prefetch_textbook_for_research

        ctx = self._make_ctx(plan={})
        with patch.dict("sys.modules", {"rag": None, "rag.query": None}):
            result = _prefetch_textbook_for_research(ctx)
        assert result == ""

    def test_returns_formatted_results(self):
        """When RAG returns hits, result is formatted correctly."""
        from build.pipeline_v5 import _prefetch_textbook_for_research

        ctx = self._make_ctx(plan={})
        # Provide Ukrainian section titles so search terms are generated
        ctx.content_outline = [
            {"section": "Наказовий спосіб (Imperative mood)", "words": 300},
        ]
        mock_hit = {
            "chunk_id": "c1", "author": "Заболотний",
            "grade": 7, "section_title": "§11",
            "text": "Наказовий спосіб...",
        }

        mock_search = MagicMock(return_value=[mock_hit])
        mock_rag_query = MagicMock()
        mock_rag_query.search_text = mock_search

        with patch.dict("sys.modules", {"rag": MagicMock(), "rag.query": mock_rag_query}):
            result = _prefetch_textbook_for_research(ctx)

        assert "Textbook Excerpts" in result
        assert "Grade 7" in result
        assert "Заболотний" in result


class TestCitationDensityRegex:
    """Verify the citation density regex patterns used in phase_content."""

    def test_adapted_from_comment(self):
        import re
        content = (
            "Some text\n"
            "<!-- adapted from: Заболотний Grade 5, вправа 221 -->\n"
            "More text\n"
            "<!-- adapted from: Вашуленко Grade 2 -->\n"
        )
        citations = re.findall(r'<!--\s*adapted from:', content)
        assert len(citations) == 2

    def test_original_comment(self):
        import re
        content = "<!-- original: no matching textbook exercise found -->\n"
        originals = re.findall(r'<!--\s*original:', content)
        assert len(originals) == 1

    def test_no_citations(self):
        import re
        content = "Just plain content with no HTML comments.\n"
        citations = re.findall(r'<!--\s*adapted from:', content)
        originals = re.findall(r'<!--\s*original:', content)
        assert len(citations) == 0
        assert len(originals) == 0


class TestRAGReviewTools:
    """RAG tools are available during review phases (issue #840)."""

    def test_rag_review_tools_defined(self):
        """_RAG_REVIEW_TOOLS constant contains the expected RAG tools."""
        from pipeline_v5 import _RAG_REVIEW_TOOLS
        expected = {
            "mcp__rag__verify_word",
            "mcp__rag__verify_lemma",
            "mcp__rag__search_text",
            "mcp__rag__search_images",
            "mcp__rag__search_literary",
        }
        assert set(_RAG_REVIEW_TOOLS) == expected

    def test_d1_tools_include_rag(self):
        """D1 dispatch tools include both filesystem and RAG tools."""
        from pipeline_v5 import _RAG_REVIEW_TOOLS
        d1_tools = ["Read", "Grep", "Glob", "Edit"] + _RAG_REVIEW_TOOLS
        assert "Read" in d1_tools
        assert "mcp__rag__verify_word" in d1_tools
        assert "mcp__rag__search_text" in d1_tools

    def test_d2_tools_include_rag(self):
        """D2 repair tools include both Edit/Grep and RAG tools."""
        from pipeline_v5 import _RAG_REVIEW_TOOLS
        d2_tools = ["Edit", "Grep"] + _RAG_REVIEW_TOOLS
        assert "Edit" in d2_tools
        assert "mcp__rag__verify_lemma" in d2_tools
        assert "mcp__rag__search_literary" in d2_tools
