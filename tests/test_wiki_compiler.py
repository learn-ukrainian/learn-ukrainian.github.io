"""Tests for wiki compiler — prompt building, source formatting, index generation."""

import os
import sys
from unittest.mock import patch

import pytest

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))


# ── Tests: _format_sources ───────────────────────────────────────


class TestFormatSources:
    def test_formats_basic_chunks(self):
        from wiki.compiler import _format_sources

        sources = [
            {"chunk_id": "c1", "text": "First chunk text."},
            {"chunk_id": "c2", "text": "Second chunk text."},
        ]
        result = _format_sources(sources)
        assert "Source 1" in result
        assert "Source 2" in result
        assert "First chunk text." in result
        assert "Second chunk text." in result
        assert "`c1`" in result
        assert "`c2`" in result

    def test_includes_metadata(self):
        from wiki.compiler import _format_sources

        sources = [
            {
                "chunk_id": "lit1",
                "text": "Some text.",
                "work": "Kobzar",
                "author": "Shevchenko",
                "year": 1840,
                "genre": "poetry",
                "language_period": "modern",
            },
        ]
        result = _format_sources(sources)
        assert "Kobzar" in result
        assert "Shevchenko" in result
        assert "1840" in result
        assert "poetry" in result
        assert "modern" in result

    def test_includes_textbook_metadata(self):
        from wiki.compiler import _format_sources

        sources = [
            {
                "chunk_id": "tb1",
                "text": "Grammar text.",
                "grade": 7,
                "section_title": "Unit 5",
            },
        ]
        result = _format_sources(sources)
        assert "Grade 7" in result
        assert "Section: Unit 5" in result

    def test_empty_sources(self):
        from wiki.compiler import _format_sources

        result = _format_sources([])
        assert "No source material" in result

    def test_separates_with_hr(self):
        from wiki.compiler import _format_sources

        sources = [
            {"chunk_id": "c1", "text": "A"},
            {"chunk_id": "c2", "text": "B"},
        ]
        result = _format_sources(sources)
        assert "---" in result


# ── Tests: _build_prompt ─────────────────────────────────────────


class TestBuildPrompt:
    @pytest.fixture
    def prompt_template(self, tmp_path):
        """Create a minimal prompt template."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        template = (
            "# Compile: {topic}\n\n"
            "Slug: {slug}\n"
            "Domain: {domain}\n"
            "Tracks: {tracks}\n"
            "Date: {date}\n"
            "Source IDs: {source_ids}\n\n"
            "## Sources\n{sources}\n"
        )
        (prompts_dir / "compile_article.md").write_text(template)
        return prompts_dir

    def test_replaces_all_placeholders(self, prompt_template):
        from wiki.compiler import _build_prompt

        with patch("wiki.compiler.PROMPTS_DIR", prompt_template):
            result = _build_prompt(
                topic="Думи козацькі",
                slug="dumy-kozatski",
                domain="folk/genres",
                sources=[{"chunk_id": "c1", "text": "Test."}],
            )
        assert "Думи козацькі" in result
        assert "dumy-kozatski" in result
        assert "folk/genres" in result
        assert "c1" in result
        assert "{topic}" not in result
        assert "{slug}" not in result
        assert "{domain}" not in result

    def test_tracks_resolved_from_domain(self, prompt_template):
        from wiki.compiler import _build_prompt

        with patch("wiki.compiler.PROMPTS_DIR", prompt_template):
            result = _build_prompt(
                topic="Test",
                slug="test",
                domain="folk/genres",
                sources=[{"chunk_id": "c1", "text": "T"}],
            )
        # "folk" domain should resolve to "folk" track
        assert "folk" in result

    def test_unknown_domain_gets_general(self, prompt_template):
        from wiki.compiler import _build_prompt

        with patch("wiki.compiler.PROMPTS_DIR", prompt_template), \
             patch("wiki.compiler.TRACK_DOMAINS", {}):
            result = _build_prompt(
                topic="Test",
                slug="test",
                domain="unknown",
                sources=[],
            )
        assert "general" in result


# ── Tests: compile_article (skip logic, no Gemini) ──────────────


class TestCompileArticleSkipLogic:
    def test_skips_already_compiled(self, tmp_path):
        from wiki.compiler import compile_article

        wiki_dir = tmp_path / "wiki"
        state_dir = wiki_dir / ".state"

        with patch("wiki.compiler.WIKI_DIR", wiki_dir), \
             patch("wiki.compiler.is_compiled", return_value=True):
            result = compile_article(
                topic="Test",
                slug="test-slug",
                domain="folk/genres",
                sources=[],
                force=False,
            )
        # Returns the expected path (skipped, not compiled)
        assert result == wiki_dir / "folk" / "genres" / "test-slug.md"

    def test_dry_run_returns_none(self, tmp_path):
        from wiki.compiler import compile_article

        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "compile_article.md").write_text(
            "Prompt: {topic} {slug} {domain} {tracks} {sources} {source_ids} {date}"
        )

        with patch("wiki.compiler.PROMPTS_DIR", prompts_dir), \
             patch("wiki.compiler.WIKI_DIR", tmp_path / "wiki"), \
             patch("wiki.compiler.is_compiled", return_value=False):
            result = compile_article(
                topic="Test",
                slug="test",
                domain="folk",
                sources=[{"chunk_id": "c1", "text": "text"}],
                dry_run=True,
            )
        assert result is None


# ── Tests: update_index ──────────────────────────────────────────


class TestUpdateIndex:
    def test_generates_index(self, tmp_path):
        from wiki.compiler import update_index

        wiki_dir = tmp_path / "wiki"
        folk_dir = wiki_dir / "folk" / "genres"
        folk_dir.mkdir(parents=True)
        (folk_dir / "dumy.md").write_text(
            "# Думи козацькі\n\nContent about dumas.\n"
        )
        (folk_dir / "kazky.md").write_text(
            "# Чарівні казки\n\nContent about fairy tales.\n"
        )

        with patch("wiki.compiler.WIKI_DIR", wiki_dir), \
             patch("wiki.state.WIKI_DIR", wiki_dir):
            update_index()

        index = (wiki_dir / "index.md").read_text(encoding="utf-8")
        assert "Думи козацькі" in index
        assert "Чарівні казки" in index
        assert "Total articles:" in index
        assert "2" in index  # 2 articles

    def test_skips_state_dir(self, tmp_path):
        from wiki.compiler import update_index

        wiki_dir = tmp_path / "wiki"
        state_dir = wiki_dir / ".state"
        state_dir.mkdir(parents=True)
        (state_dir / "progress.yaml").write_text("articles: {}\n")

        folk_dir = wiki_dir / "folk"
        folk_dir.mkdir(parents=True)
        (folk_dir / "test.md").write_text("# Test\n\nContent.\n")

        with patch("wiki.compiler.WIKI_DIR", wiki_dir), \
             patch("wiki.state.WIKI_DIR", wiki_dir):
            update_index()

        index = (wiki_dir / "index.md").read_text(encoding="utf-8")
        assert "progress" not in index

    def test_no_articles_no_index(self, tmp_path):
        from wiki.compiler import update_index

        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir()

        with patch("wiki.compiler.WIKI_DIR", wiki_dir), \
             patch("wiki.state.WIKI_DIR", wiki_dir):
            update_index()

        # No index created when no articles
        assert not (wiki_dir / "index.md").exists()
