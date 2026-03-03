"""
Tests for D.2 pipeline fixes (commit 5e3d006) and /simplify helpers.

Covers:
1. Vocab YAML indent bug auto-fix via _run_deterministic_fixes()
2. load_yaml_vocab() returns "YAML parse error" not "Missing sidecar"
3. _extract_gate_blockers() reads status JSON blocking_issues
4. _extract_vesum_failures() reads screen-result.json vesum_not_found
5. rag_batch_verify uses rag/query.get_vesum_conn (no duplicate)
6. _module_file_paths() / _snapshot_module_files() / _apply_module_fixes()
7. _apply_fixes_with_rollback() rollback on oversized diff
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ctx(tmp_path, slug="test-module"):
    """Build a minimal ModuleContext mock with real filesystem paths."""
    level_dir = tmp_path / "a1"
    level_dir.mkdir(parents=True, exist_ok=True)

    md = level_dir / f"{slug}.md"
    md.write_text("---\ntitle: Test\n---\n\n# Intro\nHello world.\n\n## Summary\nDone.\n", "utf-8")

    act_dir = level_dir / "activities"
    act_dir.mkdir(exist_ok=True)
    act_file = act_dir / f"{slug}.yaml"
    act_file.write_text("- type: quiz\n  title: Test Quiz\n", "utf-8")

    vocab_dir = level_dir / "vocabulary"
    vocab_dir.mkdir(exist_ok=True)
    vocab_file = vocab_dir / f"{slug}.yaml"
    vocab_file.write_text("- lemma: тест\n  translation: test\n", "utf-8")

    orch_dir = level_dir / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)

    status_dir = level_dir / "status"
    status_dir.mkdir(exist_ok=True)

    ctx = MagicMock()
    ctx.slug = slug
    ctx.track = "a1"
    ctx.orch_dir = orch_dir
    ctx.paths = {
        "md": md,
        "activities": act_file,
        "vocabulary": vocab_file,
        "status": status_dir / f"{slug}.json",
        "meta": level_dir / "meta" / f"{slug}.yaml",
        "review": level_dir / "review" / f"{slug}-review.md",
    }
    return ctx


# =============================================================================
# Fix 1: Vocab YAML indent bug auto-fix
# =============================================================================


class TestVocabYamlIndentFix:
    """fix_raw_yaml_text() should fix the first-entry indent bug."""

    def test_first_entry_indent_fixed(self):
        from audit.checks.yaml_schema_validation import fix_raw_yaml_text

        broken = "  - lemma: кіт\n  translation: cat\n- lemma: собака\n  translation: dog\n"
        fixed, msgs = fix_raw_yaml_text(broken)
        assert fixed.startswith("- lemma: кіт"), f"Expected root-level entry, got: {fixed[:30]}"
        assert any("indent" in m.lower() for m in msgs)

    def test_already_correct_no_fix(self):
        from audit.checks.yaml_schema_validation import fix_raw_yaml_text

        correct = "- lemma: кіт\n  translation: cat\n- lemma: собака\n  translation: dog\n"
        fixed, msgs = fix_raw_yaml_text(correct)
        assert fixed == correct
        assert not any("indent" in m.lower() for m in msgs)


# =============================================================================
# Fix 2: _extract_gate_blockers() reads status JSON
# =============================================================================


class TestExtractGateBlockers:

    def test_extracts_blocking_issues(self, tmp_path):
        from build_module import _extract_gate_blockers

        ctx = _make_ctx(tmp_path)
        status = {
            "overall": {
                "status": "FAIL",
                "blocking_issues": [
                    "Words: 1500/2000",
                    "Structure: Missing '## Vocabulary'",
                ],
            }
        }
        ctx.paths["status"].write_text(json.dumps(status), "utf-8")

        result = _extract_gate_blockers(ctx)
        assert "GATE BLOCKER: Words: 1500/2000" in result
        assert "GATE BLOCKER: Structure: Missing '## Vocabulary'" in result

    def test_no_status_file_returns_empty(self, tmp_path):
        from build_module import _extract_gate_blockers

        ctx = _make_ctx(tmp_path)
        # status file doesn't exist by default
        result = _extract_gate_blockers(ctx)
        assert result == ""

    def test_no_blocking_issues_returns_empty(self, tmp_path):
        from build_module import _extract_gate_blockers

        ctx = _make_ctx(tmp_path)
        status = {"overall": {"status": "PASS", "blocking_issues": []}}
        ctx.paths["status"].write_text(json.dumps(status), "utf-8")

        result = _extract_gate_blockers(ctx)
        assert result == ""


# =============================================================================
# Fix 3: load_yaml_vocab() returns parse error, not "Missing sidecar"
# =============================================================================


class TestLoadYamlVocab:

    def test_valid_vocab_returns_data(self, tmp_path):
        from audit.core import load_yaml_vocab

        md = tmp_path / "test.md"
        md.write_text("# Test", "utf-8")
        vocab_dir = tmp_path / "vocabulary"
        vocab_dir.mkdir()
        vocab_file = vocab_dir / "test.yaml"
        vocab_file.write_text("- lemma: кіт\n  translation: cat\n", "utf-8")

        data, error = load_yaml_vocab(str(md))
        assert data is not None
        assert error is None
        assert len(data) == 1
        assert data[0]["lemma"] == "кіт"

    def test_missing_vocab_returns_none_none(self, tmp_path):
        from audit.core import load_yaml_vocab

        md = tmp_path / "test.md"
        md.write_text("# Test", "utf-8")
        # No vocabulary/ directory

        data, error = load_yaml_vocab(str(md))
        assert data is None
        assert error is None  # Not found, not an error

    def test_malformed_vocab_returns_parse_error(self, tmp_path):
        from audit.core import load_yaml_vocab

        md = tmp_path / "test.md"
        md.write_text("# Test", "utf-8")
        vocab_dir = tmp_path / "vocabulary"
        vocab_dir.mkdir()
        vocab_file = vocab_dir / "test.yaml"
        vocab_file.write_text("- lemma: кіт\n  bad: [unclosed\n  :\n", "utf-8")

        data, error = load_yaml_vocab(str(md))
        assert data is None
        assert error is not None
        assert "parse error" in error.lower() or "yaml" in error.lower()


# =============================================================================
# Fix 4: _extract_vesum_failures() reads screen-result.json
# =============================================================================


class TestExtractVesumFailures:

    def test_extracts_not_found_words(self, tmp_path):
        from build_module import _extract_vesum_failures

        ctx = _make_ctx(tmp_path)
        screen_result = {
            "vesum_stats": {"total": 100, "vesum_hits": 95, "not_found": 5},
            "vesum_not_found": [
                {"original": "кошка", "clean": "кошка", "source": "prose", "status": "❌"},
                {"original": "хорошо", "clean": "хорошо", "source": "prose", "status": "❌"},
            ],
        }
        (ctx.orch_dir / "screen-result.json").write_text(
            json.dumps(screen_result, ensure_ascii=False), "utf-8"
        )

        result = _extract_vesum_failures(ctx)
        assert "VESUM WORD VERIFICATION FAILURES" in result
        assert "кошка" in result
        assert "хорошо" in result

    def test_no_screen_result_returns_empty(self, tmp_path):
        from build_module import _extract_vesum_failures

        ctx = _make_ctx(tmp_path)
        result = _extract_vesum_failures(ctx)
        assert result == ""

    def test_empty_not_found_returns_empty(self, tmp_path):
        from build_module import _extract_vesum_failures

        ctx = _make_ctx(tmp_path)
        screen_result = {
            "vesum_stats": {"total": 100, "vesum_hits": 100, "not_found": 0},
            "vesum_not_found": [],
        }
        (ctx.orch_dir / "screen-result.json").write_text(
            json.dumps(screen_result), "utf-8"
        )

        result = _extract_vesum_failures(ctx)
        assert result == ""


# =============================================================================
# Fix 5: rag_batch_verify uses rag/query.get_vesum_conn (no duplicate)
# =============================================================================


class TestVesumDedup:

    def test_rag_batch_verify_imports_from_rag_query(self):
        """rag_batch_verify should use get_vesum_conn from rag.query, not its own."""
        import inspect
        import rag_batch_verify

        source = inspect.getsource(rag_batch_verify)

        # Should import from rag.query
        assert "from rag.query import get_vesum_conn" in source

        # Should NOT have its own _get_vesum or vesum_lookup standalone
        assert "def _get_vesum(" not in source
        assert "def vesum_lookup(" not in source


# =============================================================================
# /simplify: _module_file_paths, _snapshot_module_files, _apply_module_fixes
# =============================================================================


class TestModuleFileHelpers:

    def test_module_file_paths_returns_three_entries(self, tmp_path):
        from build_module import _module_file_paths

        ctx = _make_ctx(tmp_path)
        paths = _module_file_paths(ctx)
        assert len(paths) == 3
        labels = [label for label, _ in paths]
        assert labels == ["md", "activities", "vocabulary"]

    def test_snapshot_captures_all_files(self, tmp_path):
        from build_module import _snapshot_module_files

        ctx = _make_ctx(tmp_path)
        snap = _snapshot_module_files(ctx)
        assert "md" in snap
        assert "activities" in snap
        assert "vocabulary" in snap
        assert "title: Test" in snap["md"]
        assert "quiz" in snap["activities"]
        assert "тест" in snap["vocabulary"]

    def test_snapshot_skips_missing_files(self, tmp_path):
        from build_module import _snapshot_module_files

        ctx = _make_ctx(tmp_path)
        ctx.paths["activities"].unlink()  # Remove activities file
        snap = _snapshot_module_files(ctx)
        assert "md" in snap
        assert "activities" not in snap
        assert "vocabulary" in snap

    def test_apply_module_fixes_no_delimiters(self, tmp_path):
        from build_module import _apply_module_fixes

        ctx = _make_ctx(tmp_path)
        n = _apply_module_fixes(ctx, "No fix blocks here")
        assert n == 0

    def test_apply_module_fixes_with_fix_block(self, tmp_path):
        from build_module import _apply_module_fixes

        ctx = _make_ctx(tmp_path)
        raw = (
            "===SECTION_FIX_START===\n"
            "FILE: test-module.md\n"
            "FIND:\n"
            "Hello world.\n"
            "REPLACE:\n"
            "Hello Ukraine.\n"
            "===SECTION_FIX_END===\n"
        )
        n = _apply_module_fixes(ctx, raw)
        assert n >= 1
        assert "Hello Ukraine." in ctx.paths["md"].read_text("utf-8")


# =============================================================================
# /simplify: _apply_fixes_with_rollback
# =============================================================================


class TestApplyFixesWithRollback:

    def test_no_fix_delimiters_accepted(self, tmp_path):
        from build_module import _apply_fixes_with_rollback

        ctx = _make_ctx(tmp_path)
        accepted, n = _apply_fixes_with_rollback(ctx, "No fixes", "test")
        assert accepted is True
        assert n == 0

    def test_small_fix_accepted(self, tmp_path):
        from build_module import _apply_fixes_with_rollback

        ctx = _make_ctx(tmp_path)
        raw = (
            "===SECTION_FIX_START===\n"
            "FILE: test-module.md\n"
            "FIND:\n"
            "Hello world.\n"
            "REPLACE:\n"
            "Hello Ukraine.\n"
            "===SECTION_FIX_END===\n"
        )
        accepted, n = _apply_fixes_with_rollback(ctx, raw, "test")
        assert accepted is True
        assert "Hello Ukraine." in ctx.paths["md"].read_text("utf-8")

    def test_massive_change_rolled_back(self, tmp_path):
        from build_module import _apply_fixes_with_rollback

        ctx = _make_ctx(tmp_path)
        # Write a large file so we can make a massive replacement
        big_content = "Line A\n" * 200
        ctx.paths["md"].write_text(big_content, "utf-8")

        # Replace everything with completely different content
        raw = (
            "===SECTION_FIX_START===\n"
            "FILE: test-module.md\n"
            "FIND:\n"
            + big_content
            + "REPLACE:\n"
            + "Completely different line\n" * 200
            + "===SECTION_FIX_END===\n"
        )
        accepted, n = _apply_fixes_with_rollback(ctx, raw, "test")
        # Should be rolled back — 200 lines changed for 1 FIND pair (max 25)
        assert accepted is False
        # File should be restored
        assert ctx.paths["md"].read_text("utf-8") == big_content


# =============================================================================
# _clean_fix_text: strip LLM formatting artifacts from FIND/REPLACE text
# =============================================================================


class TestCleanFixText:

    def test_strips_section_line_header(self):
        from build_module import _clean_fix_text

        text = 'Section: "Практика", Line 269\nYou cannot say "one furniture"'
        assert _clean_fix_text(text) == 'You cannot say "one furniture"'

    def test_strips_triple_backticks(self):
        from build_module import _clean_fix_text

        text = "```markdown\nHello world\n```"
        assert _clean_fix_text(text) == "Hello world"

    def test_strips_backticks_and_metadata_combined(self):
        from build_module import _clean_fix_text

        text = (
            'Section: "Вступ", Line 42\n'
            "```\n"
            "Привіт, як справи?\n"
            "```"
        )
        assert _clean_fix_text(text) == "Привіт, як справи?"

    def test_strips_guillemet_wrapper(self):
        from build_module import _clean_fix_text

        assert _clean_fix_text("«some text»") == "some text"

    def test_preserves_inline_guillemets(self):
        from build_module import _clean_fix_text

        text = "Слово «привіт» означає hello"
        assert _clean_fix_text(text) == text

    def test_no_op_on_clean_text(self):
        from build_module import _clean_fix_text

        text = "Це звичайний текст без форматування."
        assert _clean_fix_text(text) == text

    def test_multiline_section_header_variations(self):
        from build_module import _clean_fix_text

        # Curly quotes
        text = 'Section: \u201cПрактика\u201d, Line 10\nreal content'
        assert _clean_fix_text(text) == "real content"

        # «» quotes
        text = 'Section: «Теорія», Line 5\nreal content'
        assert _clean_fix_text(text) == "real content"


# =============================================================================
# _apply_find_replace_fixes: end-to-end with LLM artifacts
# =============================================================================


class TestApplyFixesWithArtifacts:

    def test_finds_match_after_stripping_metadata(self, tmp_path):
        from build_module import _apply_find_replace_fixes

        f = tmp_path / "test.md"
        f.write_text("Hello world.\nGoodbye world.\n", "utf-8")

        raw = (
            "===SECTION_FIX_START===\n"
            "FILE: test.md\n"
            "---\n"
            "FIND:\n"
            'Section: "Intro", Line 1\n'
            "```\n"
            "Hello world.\n"
            "```\n"
            "REPLACE:\n"
            "Hello Ukraine.\n"
            "---\n"
            "===SECTION_FIX_END===\n"
        )
        n = _apply_find_replace_fixes(f, raw)
        assert n == 1
        assert "Hello Ukraine." in f.read_text("utf-8")

    def test_clean_find_still_works(self, tmp_path):
        from build_module import _apply_find_replace_fixes

        f = tmp_path / "test.md"
        f.write_text("Hello world.\n", "utf-8")

        raw = (
            "===SECTION_FIX_START===\n"
            "FIND:\n"
            "Hello world.\n"
            "REPLACE:\n"
            "Hello Ukraine.\n"
            "===SECTION_FIX_END===\n"
        )
        n = _apply_find_replace_fixes(f, raw)
        assert n == 1


# =============================================================================
# /simplify: "vocab" key bug fix in pipeline_lib
# =============================================================================


class TestVocabKeyFix:

    def test_no_vocab_key_in_paths(self):
        """ctx.paths should use 'vocabulary', never 'vocab'."""
        # Check that get_module_paths from batch_gemini_config uses "vocabulary"
        from batch_gemini_config import get_module_paths

        paths = get_module_paths("a1", "test-module")
        assert "vocabulary" in paths
        assert "vocab" not in paths
