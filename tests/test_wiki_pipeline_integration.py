"""Tests for wiki/knowledge packet integration in the V6 build pipeline.

Architecture: Wiki context is loaded in step_research for seminar tracks
and included in the knowledge packet. No separate wiki injection in
step_write or chunk prompts �� one source of truth.

Issue: #1136
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


# ── Tests: _is_seminar_track ──────────────────────────────────────────


class TestIsSeminarTrack:
    """Test the seminar track detection helper."""

    def test_core_seminar_tracks(self):
        from build.v6_build import _is_seminar_track

        for track in ("hist", "bio", "istorio", "lit", "folk", "oes", "ruth"):
            assert _is_seminar_track(track), f"{track} should be seminar"

    def test_lit_subtracks(self):
        from build.v6_build import _is_seminar_track

        for track in ("lit-essay", "lit-war", "lit-humor", "lit-drama",
                       "lit-youth", "lit-hist-fic", "lit-fantastika",
                       "lit-doc", "lit-crimea"):
            assert _is_seminar_track(track), f"{track} should be seminar"

    def test_core_tracks_not_seminar(self):
        from build.v6_build import _is_seminar_track

        for track in ("a1", "a2", "b1", "b2", "c1", "c2", "b2-pro", "c1-pro"):
            assert not _is_seminar_track(track), f"{track} should NOT be seminar"

    def test_case_insensitive(self):
        from build.v6_build import _is_seminar_track

        assert _is_seminar_track("HIST")
        assert _is_seminar_track("Folk")
        assert _is_seminar_track("LIT-essay")


# ── Tests: _build_seminar_packet ──────────────────────────────────────


class TestBuildSeminarPacket:
    """Test knowledge packet generation for seminar tracks."""

    def test_includes_wiki_context(self, tmp_path):
        from build.v6_build import _build_seminar_packet

        # Create minimal plan
        plans_dir = tmp_path / "plans" / "folk"
        plans_dir.mkdir(parents=True)
        (plans_dir / "test-slug.yaml").write_text(
            "title: Test Module\nslug: test-slug\n", "utf-8"
        )

        fake_wiki = "<wiki_context>\nCompiled knowledge\n</wiki_context>"

        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path), \
             patch("wiki.context.get_wiki_context", return_value=fake_wiki):
            result = _build_seminar_packet("folk", "test-slug")

        assert "Compiled knowledge" in result
        assert "wiki_context" in result

    def test_includes_discovery_literary(self, tmp_path):
        from build.v6_build import _build_seminar_packet

        plans_dir = tmp_path / "plans" / "folk"
        plans_dir.mkdir(parents=True)
        (plans_dir / "test-slug.yaml").write_text(
            "title: Test\nslug: test-slug\n", "utf-8"
        )

        disc_dir = tmp_path / "folk" / "discovery"
        disc_dir.mkdir(parents=True)
        (disc_dir / "test-slug.yaml").write_text(textwrap.dedent("""\
            rag_literary:
              - chunk_id: abc123
                text: "Це текст з літературного джерела, достатнь�� довгий для перевірки."
                score: 0.8
            rag_chunks: []
        """), "utf-8")

        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path), \
             patch("wiki.context.get_wiki_context", return_value=""):
            result = _build_seminar_packet("folk", "test-slug")

        assert "abc123" in result
        assert "Literary Sources" in result

    def test_includes_plan_references(self, tmp_path):
        from build.v6_build import _build_seminar_packet

        plans_dir = tmp_path / "plans" / "hist"
        plans_dir.mkdir(parents=True)
        (plans_dir / "test-slug.yaml").write_text(textwrap.dedent("""\
            title: Test History Module
            slug: test-slug
            references:
              - type: primary
                author: Грушевський М.
                work: Ілюстрована історія України
                note: Classic reference
        """), "utf-8")

        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path), \
             patch("wiki.context.get_wiki_context", return_value=""):
            result = _build_seminar_packet("hist", "test-slug")

        assert "Грушевський" in result
        assert "Plan References" in result

    def test_graceful_without_wiki(self, tmp_path):
        from build.v6_build import _build_seminar_packet

        plans_dir = tmp_path / "plans" / "folk"
        plans_dir.mkdir(parents=True)
        (plans_dir / "test-slug.yaml").write_text(
            "title: Test\nslug: test-slug\n", "utf-8"
        )

        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path), \
             patch("wiki.context.get_wiki_context", side_effect=ImportError("no wiki")):
            result = _build_seminar_packet("folk", "test-slug")

        assert "Knowledge Packet" in result  # Still produces a packet


# ── Tests: _get_knowledge_packet_for_rewrite ──────────────────────────


class TestGetKnowledgePacketForRewrite:
    """Test knowledge packet loading for section rewrites."""

    def test_loads_existing_packet(self, tmp_path):
        from build.v6_build import _get_knowledge_packet_for_rewrite

        research_dir = tmp_path / "folk" / "research"
        research_dir.mkdir(parents=True)
        (research_dir / "test-slug-knowledge-packet.md").write_text(
            "# Knowledge Packet\nWiki content here.\n", "utf-8"
        )

        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path):
            result = _get_knowledge_packet_for_rewrite("folk", "test-slug")

        assert "Wiki content here" in result

    def test_returns_empty_when_no_packet(self, tmp_path):
        from build.v6_build import _get_knowledge_packet_for_rewrite

        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path):
            result = _get_knowledge_packet_for_rewrite("folk", "nonexistent")

        assert result == ""

    def test_truncates_large_packets(self, tmp_path):
        from build.v6_build import _get_knowledge_packet_for_rewrite

        research_dir = tmp_path / "folk" / "research"
        research_dir.mkdir(parents=True)
        large_content = "x" * 50_000
        (research_dir / "test-slug-knowledge-packet.md").write_text(large_content, "utf-8")

        with patch("build.v6_build.CURRICULUM_ROOT", tmp_path):
            result = _get_knowledge_packet_for_rewrite("folk", "test-slug")

        assert len(result) <= 31_000  # 30K + truncation message
        assert "truncated" in result


# ── Tests: Seminar write template ─────────────────────────────────────


class TestSeminarWriteTemplate:
    """Verify the seminar write prompt template is correct."""

    def test_no_dsl_exercise_instructions(self):
        """Template must NOT tell writer to embed DSL exercises."""
        phases_dir = SCRIPTS_DIR / "build" / "phases"
        template = (phases_dir / "v6-write-seminar.md").read_text("utf-8")
        assert ":::quiz" not in template
        assert ":::fill-in" not in template
        assert ":::note" not in template

    def test_has_inject_activity_markers(self):
        """Template must instruct writer to place activity injection markers."""
        phases_dir = SCRIPTS_DIR / "build" / "phases"
        template = (phases_dir / "v6-write-seminar.md").read_text("utf-8")
        assert "INJECT_ACTIVITY" in template

    def test_no_wiki_context_placeholder(self):
        """Wiki context is in the knowledge packet, not a separate placeholder."""
        phases_dir = SCRIPTS_DIR / "build" / "phases"
        template = (phases_dir / "v6-write-seminar.md").read_text("utf-8")
        assert "{WIKI_CONTEXT}" not in template

    def test_has_skeleton_and_correction_placeholders(self):
        """Template must have placeholders that step_write replaces."""
        phases_dir = SCRIPTS_DIR / "build" / "phases"
        template = (phases_dir / "v6-write-seminar.md").read_text("utf-8")
        assert "{SKELETON_SECTION}" in template
        assert "{CORRECTION_SECTION}" in template

    def test_has_knowledge_packet_placeholder(self):
        """Template must include the knowledge packet."""
        phases_dir = SCRIPTS_DIR / "build" / "phases"
        template = (phases_dir / "v6-write-seminar.md").read_text("utf-8")
        assert "{KNOWLEDGE_PACKET}" in template

    def test_has_exact_section_titles(self):
        """Template must include section titles from the plan."""
        phases_dir = SCRIPTS_DIR / "build" / "phases"
        template = (phases_dir / "v6-write-seminar.md").read_text("utf-8")
        assert "{EXACT_SECTION_TITLES}" in template
