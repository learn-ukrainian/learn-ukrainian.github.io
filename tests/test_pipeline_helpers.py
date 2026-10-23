"""Tests for pipeline_lib helper functions.

Covers: _parse_section, _build_section_budget_table, _check_archive_fits_outline,
get_level_constraints, get_activity_config, get_item_minimums_table,
bilingualify_section_titles, get_pedagogical_constraints,
get_structural_rules, get_h3_word_range, get_expansion_method, get_track_skill,
get_immersion_rule, get_level_label, track_to_level_focus, load_state,
v5 phase terminology (no legacy Phase 2: labels), SELF_AUDIT_SNIPPET CONTENT_PATH resolution.

Issue: #817
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, "scripts")


# Minimal context matching the real dataclass
@dataclass
class FakeContext:
    track: str = "a1"
    module_num: int = 1
    slug: str = "test-module"
    content_outline: list = field(default_factory=list)
    plan: dict = field(default_factory=dict)
    archive_dir: Path | None = None


# ============================================================================
# _parse_section
# ============================================================================


# ============================================================================
# _build_section_budget_table
# ============================================================================


# ============================================================================
# _check_archive_fits_outline
# ============================================================================

class TestCheckArchiveFitsOutline:
    def test_archive_covers_all_sections(self, tmp_path):
        from pipeline_lib import _check_archive_fits_outline
        archive_file = tmp_path / "test-module.md"
        archive_file.write_text("# Title\n\n## Intro\nsome text\n\n## Main\nmore text\n")
        ctx = FakeContext(
            slug="test-module",
            archive_dir=tmp_path,
            content_outline=[
                {"section": "Intro", "words": 300},
                {"section": "Main", "words": 500},
            ],
        )
        fits, matched, missing = _check_archive_fits_outline(ctx)
        assert fits is True
        assert len(matched) == 2
        assert len(missing) == 0

    def test_archive_below_70_percent_coverage(self, tmp_path):
        from pipeline_lib import _check_archive_fits_outline
        archive_file = tmp_path / "test-module.md"
        archive_file.write_text("# Title\n\n## Intro\nsome text\n")
        ctx = FakeContext(
            slug="test-module",
            archive_dir=tmp_path,
            content_outline=[
                {"section": "Intro", "words": 300},
                {"section": "Main", "words": 300},
                {"section": "Practice", "words": 200},
                {"section": "Summary", "words": 200},
            ],
        )
        fits, matched, missing = _check_archive_fits_outline(ctx)
        assert fits is False  # 1/4 = 25% < 70%
        assert "Intro" in matched
        assert len(missing) == 3

    def test_archive_exactly_70_percent(self, tmp_path):
        from pipeline_lib import _check_archive_fits_outline
        archive_file = tmp_path / "test-module.md"
        archive_file.write_text(
            "# Title\n\n## Section A\ntext\n\n## Section B\ntext\n\n"
            "## Section C\ntext\n\n## Section D\ntext\n\n"
            "## Section E\ntext\n\n## Section F\ntext\n\n"
            "## Section G\ntext\n"
        )
        ctx = FakeContext(
            slug="test-module",
            archive_dir=tmp_path,
            content_outline=[
                {"section": f"Section {c}", "words": 100}
                for c in "ABCDEFGHIJ"  # 10 sections, archive has 7 = 70%
            ],
        )
        fits, matched, missing = _check_archive_fits_outline(ctx)
        assert fits is True  # 7/10 = 70% >= 70%
        assert len(matched) == 7
        assert len(missing) == 3

    def test_no_outline_uses_word_threshold(self, tmp_path):
        from pipeline_lib import ARCHIVE_WORD_THRESHOLD, _check_archive_fits_outline
        archive_file = tmp_path / "test-module.md"
        archive_file.write_text("word " * (ARCHIVE_WORD_THRESHOLD + 100))
        ctx = FakeContext(slug="test-module", archive_dir=tmp_path, content_outline=[])
        fits, _, _ = _check_archive_fits_outline(ctx)
        assert fits is True

    def test_no_outline_below_threshold(self, tmp_path):
        from pipeline_lib import _check_archive_fits_outline
        archive_file = tmp_path / "test-module.md"
        archive_file.write_text("short text")  # ~2 words
        ctx = FakeContext(slug="test-module", archive_dir=tmp_path, content_outline=[])
        fits, _, _ = _check_archive_fits_outline(ctx)
        assert fits is False


# ============================================================================
# get_level_constraints
# ============================================================================


# ============================================================================
# get_activity_config
# ============================================================================


# ============================================================================
# bilingualify_section_titles
# ============================================================================


# ============================================================================
# get_pedagogical_constraints
# ============================================================================


    # Decodable vocabulary tests removed in #841 — system was dropped.


# ============================================================================
# _get_prompt_tier — tier-aware shared rules (#841)
# ============================================================================


# ============================================================================
# _clean_textbook_text (#841)
# ============================================================================


# ============================================================================
# get_h3_word_range
# ============================================================================


# ============================================================================
# get_expansion_method
# ============================================================================


# ============================================================================
# get_track_skill
# ============================================================================


# ============================================================================
# get_immersion_rule
# ============================================================================


# ============================================================================
# get_level_label
# ============================================================================


# ============================================================================
# track_to_level_focus
# ============================================================================


# ============================================================================
# load_state
# ============================================================================

class TestLoadState:
    def test_existing_file_loaded(self, tmp_path):
        import json

        from pipeline_lib import ModuleContext, load_state
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({
            "slug": "loaded", "track": "b1", "module_num": 3,
            "mode": "v5", "phases": {"research": {"status": "complete"}},
            "last_updated": "2026-01-01T00:00:00Z",
        }))
        ctx = ModuleContext(
            track="b1", module_num=3, slug="loaded", mode="full",
            orch_dir=tmp_path,
        )
        state = load_state(ctx)
        assert state["slug"] == "loaded"
        assert state["phases"]["research"]["status"] == "complete"

    def test_corrupt_json_returns_fresh(self, tmp_path):
        from pipeline_lib import ModuleContext, load_state
        state_file = tmp_path / "state.json"
        state_file.write_text("{bad json")
        ctx = ModuleContext(
            track="a1", module_num=1, slug="corrupt", mode="full",
            orch_dir=tmp_path,
        )
        state = load_state(ctx)
        assert state["slug"] == "corrupt"
        assert state["phases"] == {}


# ============================================================================
# SELF_AUDIT_SNIPPET nested CONTENT_PATH resolution — Issue #817
# ============================================================================

class TestSelfAuditSnippetContentPath:
    """The SELF_AUDIT_SNIPPET value must have {CONTENT_PATH} resolved before storage.

    fill_template does a single pass: when a snippet is injected via {SELF_AUDIT_SNIPPET},
    any {CONTENT_PATH} inside it would remain unresolved. The fix pre-resolves {CONTENT_PATH}
    in the snippet text inside build_placeholders, before storing it in the placeholders dict.
    """

    def test_pipeline_lib_resolves_content_path_in_snippet(self):
        """Verify pipeline core contains the resolution logic for SELF_AUDIT_SNIPPET."""
        # Real code now in pipeline/core.py (pipeline_lib.py is a backward-compat stub)
        pipeline_core_path = Path("scripts/pipeline/core.py")
        source = pipeline_core_path.read_text(encoding="utf-8")

        # The fix must include a .replace("{CONTENT_PATH}", ...) applied to the snippet
        assert '"{CONTENT_PATH}"' in source or "'{CONTENT_PATH}'" in source, (
            "Expected {CONTENT_PATH} resolution in pipeline/core.py"
        )
        # Specifically: the SELF_AUDIT_SNIPPET assignment must resolve nested {CONTENT_PATH}
        assert "SELF_AUDIT_SNIPPET" in source
        # The snippet line must be followed by a .replace call
        lines = source.splitlines()
        for i, line in enumerate(lines):
            if "SELF_AUDIT_SNIPPET" in line and "_self_audit_raw" in line:
                # Check that surrounding lines contain the resolution
                context = "\n".join(lines[max(0, i - 2):i + 5])
                assert "replace" in context and "CONTENT_PATH" in context, (
                    f"Expected .replace(CONTENT_PATH) near SELF_AUDIT_SNIPPET assignment:\n{context}"
                )
                break


# ============================================================================
# Bukvar REQUIRED_TYPES for A1 M1-4 + dict activity_hints parsing
# ============================================================================
