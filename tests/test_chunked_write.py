"""Tests for section-by-section chunked generation (#998).

Tests the skeleton parsing, summary building, and chunking gate logic
without requiring LLM calls or filesystem state.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure scripts/ is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


SAMPLE_SKELETON = """\
## Діалоги (Dialogues) (~385 words total)

- P1 (~35 words): Brief scene-setting.
- Dialogue 1 (~90 words): Hostel check-in, informal.
- P2 (~25 words): Transition to formal.

## Мене звати... (My name is...) (~275 words total)

- P1 (~80 words): Explain Мене звати...
- P2 (~70 words): Asking the question.
- Exercise: fill-in — Complete self-introduction. (6 items)

## Це... (This is...) (~220 words total)

- P1 (~75 words): Це is the Swiss army knife.
- P2 (~70 words): Questions with Це.

## Підсумок (~150 words)

- P1 (~150 words): Recap key concepts.

Grand total: ~1030 words"""


MINIMAL_SKELETON = """\
## Only One Section (~500 words total)

- P1 (~500 words): Everything.
"""


class TestParseSkeletonSections:
    """Tests for _parse_skeleton_sections()."""

    def test_parses_multiple_sections(self):
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections(SAMPLE_SKELETON)
        assert len(sections) == 4

    def test_section_titles(self):
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections(SAMPLE_SKELETON)
        assert "Діалоги" in sections[0]["title"]
        assert "Мене звати" in sections[1]["title"]
        assert "Це..." in sections[2]["title"]
        assert "Підсумок" in sections[3]["title"]

    def test_word_budgets(self):
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections(SAMPLE_SKELETON)
        assert sections[0]["words"] == 385
        assert sections[1]["words"] == 275
        assert sections[2]["words"] == 220
        assert sections[3]["words"] == 150

    def test_section_bodies_contain_content(self):
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections(SAMPLE_SKELETON)
        assert "Brief scene-setting" in sections[0]["body"]
        assert "fill-in" in sections[1]["body"]

    def test_minimal_skeleton_single_section(self):
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections(MINIMAL_SKELETON)
        assert len(sections) == 1
        assert sections[0]["words"] == 500

    def test_empty_skeleton(self):
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections("")
        assert sections == []

    def test_no_h2_headings(self):
        from build.v6_build import _parse_skeleton_sections

        sections = _parse_skeleton_sections("Just some text\nwithout headings\n")
        assert sections == []


class TestExtractWordBudget:
    """Tests for _extract_word_budget()."""

    def test_standard_format(self):
        from build.v6_build import _extract_word_budget

        assert _extract_word_budget("Section (~275 words total)") == 275

    def test_no_budget(self):
        from build.v6_build import _extract_word_budget

        assert _extract_word_budget("Section without budget") == 0

    def test_words_without_tilde(self):
        from build.v6_build import _extract_word_budget

        # Should still match ~NNN words pattern
        assert _extract_word_budget("Section (~150 words)") == 150


class TestCanonicalSectionName:
    """Tests for stripping skeleton budget annotations from section titles."""

    def test_strips_words_total_suffix(self):
        from build.v6_build import _canonical_section_name

        assert _canonical_section_name("Діалоги (Dialogues) (~330 words total)") == "Діалоги (Dialogues)"

    def test_leaves_plain_title_unchanged(self):
        from build.v6_build import _canonical_section_name

        assert _canonical_section_name("Підсумок — Summary") == "Підсумок — Summary"


class TestBuildSectionSummary:
    """Tests for _build_section_summary()."""

    def test_empty_sections(self):
        from build.v6_build import _build_section_summary

        assert _build_section_summary([]) == ""

    def test_short_sections_not_truncated(self):
        from build.v6_build import _build_section_summary

        sections = ["First section content.", "Second section content."]
        result = _build_section_summary(sections)
        assert "First section content." in result
        assert "Second section content." in result

    def test_long_sections_truncated(self):
        from build.v6_build import _build_section_summary

        # Create sections with many words
        long_section = " ".join(["word"] * 600)
        result = _build_section_summary([long_section], max_words=100)
        assert len(result.split()) <= 110  # some overhead from truncation marker
        assert "truncated" in result


class TestChunkingGate:
    """Tests for the chunking trigger conditions.

    The gate triggers when:
    1. skeleton is provided
    2. no_chunk is False
    3. word_target >= 2000, or
    4. word_target >= 1200 with >= 4 H2 sections
    """

    def test_gate_triggers_for_large_module_with_sections(self):
        """word_target=4000, 4 sections -> should chunk."""
        from build.v6_build import _parse_skeleton_sections, _should_chunk_write

        sections = _parse_skeleton_sections(SAMPLE_SKELETON)
        assert _should_chunk_write(4000, sections, False) is True

    def test_gate_triggers_for_medium_four_section_module(self):
        """word_target=1200, 4 sections -> chunk to avoid oversized monolithic prompts."""
        from build.v6_build import _parse_skeleton_sections, _should_chunk_write

        sections = _parse_skeleton_sections(SAMPLE_SKELETON)
        assert _should_chunk_write(1200, sections, False) is True

    def test_gate_skips_for_small_two_section_module(self):
        """word_target=1200, 2 sections -> stay single-call."""
        from build.v6_build import _parse_skeleton_sections, _should_chunk_write

        two_section_skeleton = """\
## First (~600 words total)

- P1 (~300 words): first

## Second (~600 words total)

- P1 (~300 words): second
"""
        sections = _parse_skeleton_sections(two_section_skeleton)
        assert _should_chunk_write(1200, sections, False) is False

    def test_gate_skips_when_no_chunk_flag(self):
        """--no-chunk flag disables chunking."""
        from build.v6_build import _parse_skeleton_sections, _should_chunk_write

        sections = _parse_skeleton_sections(SAMPLE_SKELETON)
        assert _should_chunk_write(4000, sections, True) is False

    def test_gate_skips_for_single_section(self):
        """Only 1 section -> should NOT chunk."""
        from build.v6_build import _parse_skeleton_sections, _should_chunk_write

        sections = _parse_skeleton_sections(MINIMAL_SKELETON)
        assert _should_chunk_write(4000, sections, False) is False


# ---------------------------------------------------------------------------
# Chunk cache invalidation (#1381)
# ---------------------------------------------------------------------------

class TestChunkCacheInvalidation:
    """Tests for _invalidate_chunk_cache_if_needed and fingerprint helpers.

    Catches the #1381 regression class: chunks reused across changes in
    skeleton, plan YAML, writer template override, or writer backend.
    """

    @staticmethod
    def _seed_cache(tmp_path, skeleton_hash, plan_hash, writer_mode, *, chunks=2):
        """Create a fake orch_dir with N chunk files + cache meta."""
        import json

        for i in range(1, chunks + 1):
            (tmp_path / f"chunk-{i:02d}.md").write_text(f"chunk {i}\n", "utf-8")
        meta = {
            "skeleton_hash": skeleton_hash,
            "plan_hash": plan_hash,
            "writer_mode": writer_mode,
        }
        (tmp_path / "chunk-cache-meta.json").write_text(json.dumps(meta), "utf-8")

    def test_no_chunks_no_invalidation(self, tmp_path):
        from build.v6_build import _invalidate_chunk_cache_if_needed

        # Cold cache: nothing to clear, just returns fresh fingerprints
        sk, pl, wm = _invalidate_chunk_cache_if_needed(
            tmp_path, "skeleton text",
            plan_content="plan: yaml",
            writer_mode="gemini||core",
        )
        assert sk and pl and wm == "gemini||core"
        assert list(tmp_path.glob("chunk-*.md")) == []

    def test_all_fingerprints_match_keeps_chunks(self, tmp_path):
        from build.v6_build import (
            _hash_plan_content,
            _hash_skeleton,
            _invalidate_chunk_cache_if_needed,
        )

        skeleton = "## One\n- P1: stuff\n"
        plan = "word_target: 1200\n"
        writer_mode = "gemini||core"
        self._seed_cache(
            tmp_path,
            _hash_skeleton(skeleton),
            _hash_plan_content(plan),
            writer_mode,
        )

        _invalidate_chunk_cache_if_needed(
            tmp_path, skeleton, plan_content=plan, writer_mode=writer_mode,
        )
        # All chunks preserved
        assert len(list(tmp_path.glob("chunk-*.md"))) == 2

    def test_skeleton_change_invalidates(self, tmp_path):
        from build.v6_build import (
            _hash_plan_content,
            _hash_skeleton,
            _invalidate_chunk_cache_if_needed,
        )

        plan = "word_target: 1200\n"
        writer_mode = "gemini||core"
        self._seed_cache(
            tmp_path,
            _hash_skeleton("old skeleton"),
            _hash_plan_content(plan),
            writer_mode,
        )

        _invalidate_chunk_cache_if_needed(
            tmp_path, "NEW skeleton", plan_content=plan, writer_mode=writer_mode,
        )
        assert list(tmp_path.glob("chunk-*.md")) == []

    def test_plan_change_invalidates(self, tmp_path):
        """#1381: plan YAML edit must invalidate chunks (word_target, vocab hints, etc)."""
        from build.v6_build import (
            _hash_plan_content,
            _hash_skeleton,
            _invalidate_chunk_cache_if_needed,
        )

        skeleton = "## One\n- P1: stuff\n"
        writer_mode = "gemini||core"
        self._seed_cache(
            tmp_path,
            _hash_skeleton(skeleton),
            _hash_plan_content("word_target: 1200\n"),
            writer_mode,
        )

        _invalidate_chunk_cache_if_needed(
            tmp_path, skeleton,
            plan_content="word_target: 4000\n",  # plan changed
            writer_mode=writer_mode,
        )
        assert list(tmp_path.glob("chunk-*.md")) == []

    def test_writer_mode_change_invalidates(self, tmp_path):
        """#1381: switching writer backend or template override must regenerate."""
        from build.v6_build import (
            _hash_plan_content,
            _hash_skeleton,
            _invalidate_chunk_cache_if_needed,
        )

        skeleton = "## One\n- P1: stuff\n"
        plan = "word_target: 1200\n"
        self._seed_cache(
            tmp_path,
            _hash_skeleton(skeleton),
            _hash_plan_content(plan),
            "gemini||core",  # seeded writer mode
        )

        _invalidate_chunk_cache_if_needed(
            tmp_path, skeleton,
            plan_content=plan,
            writer_mode="gemini-tools||core",  # writer backend changed
        )
        assert list(tmp_path.glob("chunk-*.md")) == []

    def test_legacy_v1_cache_treated_as_stale(self, tmp_path):
        """Legacy chunk-cache-meta.json with only skeleton_hash invalidates."""
        import json

        from build.v6_build import _hash_skeleton, _invalidate_chunk_cache_if_needed

        skeleton = "## One\n- P1: stuff\n"
        (tmp_path / "chunk-01.md").write_text("stale\n", "utf-8")
        # v1 schema: only skeleton_hash, no plan_hash or writer_mode
        legacy = {"skeleton_hash": _hash_skeleton(skeleton)}
        (tmp_path / "chunk-cache-meta.json").write_text(json.dumps(legacy), "utf-8")

        _invalidate_chunk_cache_if_needed(
            tmp_path, skeleton,
            plan_content="word_target: 1200\n",
            writer_mode="gemini||core",
        )
        assert list(tmp_path.glob("chunk-*.md")) == []

    def test_corrupt_meta_file_treated_as_stale(self, tmp_path):
        from build.v6_build import _invalidate_chunk_cache_if_needed

        (tmp_path / "chunk-01.md").write_text("stale\n", "utf-8")
        (tmp_path / "chunk-cache-meta.json").write_text("{not valid json", "utf-8")

        _invalidate_chunk_cache_if_needed(
            tmp_path, "skel",
            plan_content="plan",
            writer_mode="gemini||core",
        )
        assert list(tmp_path.glob("chunk-*.md")) == []


class TestWriterModeFingerprint:
    """Tests for _compute_writer_mode()."""

    def test_core_no_override(self):
        from build.v6_build import _compute_writer_mode
        assert _compute_writer_mode(
            "gemini", template_override=None, is_seminar=False,
        ) == "gemini||core"

    def test_seminar_differs_from_core(self):
        from build.v6_build import _compute_writer_mode
        core = _compute_writer_mode("gemini", template_override=None, is_seminar=False)
        sem = _compute_writer_mode("gemini", template_override=None, is_seminar=True)
        assert core != sem

    def test_template_override_differs(self):
        from build.v6_build import _compute_writer_mode
        default = _compute_writer_mode("gemini", template_override=None, is_seminar=False)
        uk = _compute_writer_mode(
            "gemini", template_override="v6-write-uk.md", is_seminar=False,
        )
        assert default != uk

    def test_writer_backend_differs(self):
        from build.v6_build import _compute_writer_mode
        plain = _compute_writer_mode("gemini", template_override=None, is_seminar=False)
        tools = _compute_writer_mode("gemini-tools", template_override=None, is_seminar=False)
        assert plain != tools


class TestWriteStepForcesNoChunkOnOverride:
    """#1381: V6_WRITER_TEMPLATE must force single-call write.

    The chunked path builds prompts inline and does not read any writer
    template file, so the override would silently no-op without this guard.
    This is a structural test: verify the env check happens before the
    chunking gate in step_write().
    """

    def test_override_check_precedes_chunking_gate_in_source(self):
        """Structural: override branch appears before the chunking gate."""
        import inspect

        from build.v6_build import step_write

        source = inspect.getsource(step_write)
        override_pos = source.find("V6_WRITER_TEMPLATE")
        chunking_pos = source.find("Chunking gate")
        assert override_pos != -1, "V6_WRITER_TEMPLATE check missing"
        assert chunking_pos != -1, "Chunking gate marker missing"
        assert override_pos < chunking_pos, (
            "V6_WRITER_TEMPLATE must be read BEFORE the chunking gate so "
            "the override can force no_chunk (#1381)"
        )

    def test_override_forces_no_chunk_flag(self):
        """Override branch sets no_chunk = True."""
        import inspect

        from build.v6_build import step_write

        source = inspect.getsource(step_write)
        # The override branch should flip no_chunk; grep for the assignment
        # within the override-detection block. Pattern generalized in #1385
        # to cover both V6_WRITER_TEMPLATE and V6_PHASE_SUITE overrides:
        # ``if template_source != "default" and not no_chunk:``
        lines = source.splitlines()
        in_override_block = False
        found_no_chunk_assignment = False
        for line in lines:
            if 'template_source != "default"' in line and "not no_chunk" in line:
                in_override_block = True
                continue
            if in_override_block:
                if "no_chunk = True" in line:
                    found_no_chunk_assignment = True
                    break
                # Don't allow the block to span past the next top-level block
                if line and not line.startswith((" ", "\t")):
                    break
        assert found_no_chunk_assignment, (
            "Override branch must set no_chunk = True so chunked path is "
            "skipped when V6_WRITER_TEMPLATE or V6_PHASE_SUITE forces a "
            "non-default writer template (#1381 / #1385)"
        )
