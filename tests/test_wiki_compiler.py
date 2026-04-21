"""Tests for wiki compiler — prompt building, source formatting, index generation."""

import os
import sys
from pathlib import Path
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

    def test_strips_duplicated_external_metadata_from_body(self):
        from wiki.compiler import _format_sources

        sources = [
            {
                "chunk_id": "ext1",
                "source_type": "external_article",
                "title": "Teaching Ukrainian Cases",
                "source_name": "ULP",
                "url": "https://example.test/cases",
                "text": (
                    "External article: Teaching Ukrainian Cases\n"
                    "Source: ULP\n"
                    "URL: https://example.test/cases\n\n"
                    "Actual pedagogical content."
                ),
            },
        ]
        result = _format_sources(sources)
        assert result.count("https://example.test/cases") == 1
        assert "Actual pedagogical content." in result
        assert "External article: Teaching Ukrainian Cases" not in result

    def test_formats_wikipedia_as_header_metadata(self):
        from wiki.compiler import _format_sources

        sources = [
            {
                "chunk_id": "wiki1",
                "source_type": "wikipedia",
                "title": "Українська мова",
                "url": "https://uk.wikipedia.org/wiki/example",
                "text": "Lead paragraph from the article.",
            },
        ]
        result = _format_sources(sources)
        assert "Wikipedia" in result
        assert "Title: Українська мова" in result
        assert "Lead paragraph from the article." in result


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

    def test_dry_run_ignores_compiled_skip(self, tmp_path):
        from wiki.compiler import compile_article

        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "compile_article.md").write_text(
            "Prompt: {topic} {slug} {domain} {tracks} {sources} {source_ids} {date}"
        )

        with patch("wiki.compiler.PROMPTS_DIR", prompts_dir), \
             patch("wiki.compiler.WIKI_DIR", tmp_path / "wiki"), \
             patch("wiki.compiler.is_compiled", return_value=True):
            result = compile_article(
                topic="Test",
                slug="test",
                domain="folk",
                sources=[{"chunk_id": "c1", "text": "text"}],
                dry_run=True,
            )
        assert result is None

    def test_compile_writes_sibling_sources_registry(self, tmp_path):
        from wiki.compiler import compile_article

        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "compile_article.md").write_text(
            "Prompt: {topic} {slug} {domain} {tracks} {sources} {source_ids} {date}"
        )
        wiki_dir = tmp_path / "wiki"

        with patch("wiki.compiler.PROMPTS_DIR", prompts_dir), \
             patch("wiki.compiler.WIKI_DIR", wiki_dir), \
             patch("wiki.compiler.is_compiled", return_value=False), \
             patch("wiki.compiler.mark_compiled"), \
             patch("wiki.compiler._call_gemini", return_value="# Title\n\nSentence [S1].\n"):
            result = compile_article(
                topic="Test",
                slug="test",
                domain="folk",
                sources=[{"chunk_id": "ext-foo-1", "text": "text"}],
            )

        assert result == wiki_dir / "folk" / "test.md"
        registry_text = (wiki_dir / "folk" / "test.sources.yaml").read_text(encoding="utf-8")
        assert "id: S1" in registry_text
        assert "file: ext-foo-1" in registry_text


class TestCompileCommand:
    def test_compiled_article_is_ready_with_valid_sources_sidecar(self, tmp_path):
        from wiki.compile import _compiled_article_is_ready

        wiki_dir = tmp_path / "wiki"
        article_dir = wiki_dir / "pedagogy" / "a1"
        article_dir.mkdir(parents=True)
        (article_dir / "demo.md").write_text("# Demo\n\nSentence [S1].\n", encoding="utf-8")
        (article_dir / "demo.sources.yaml").write_text(
            "sources:\n"
            "  - id: S1\n"
            "    file: ext-demo-1\n"
            "    type: external\n",
            encoding="utf-8",
        )

        with patch("wiki.compile.WIKI_DIR", wiki_dir), \
             patch("wiki.state.is_compiled", return_value=True), \
             patch("wiki.compile._get_domain", return_value="pedagogy/a1"):
            assert _compiled_article_is_ready("a1", "demo") is True

    def test_compiled_article_is_not_ready_when_citations_lack_sidecar(self, tmp_path):
        from wiki.compile import _compiled_article_is_ready

        wiki_dir = tmp_path / "wiki"
        article_dir = wiki_dir / "pedagogy" / "a1"
        article_dir.mkdir(parents=True)
        (article_dir / "demo.md").write_text("# Demo\n\nSentence [S1].\n", encoding="utf-8")

        with patch("wiki.compile.WIKI_DIR", wiki_dir), \
             patch("wiki.state.is_compiled", return_value=True), \
             patch("wiki.compile._get_domain", return_value="pedagogy/a1"):
            assert _compiled_article_is_ready("a1", "demo") is False

    def test_skip_does_not_log_compile_or_update_index(self):
        from wiki.compile import cmd_compile_one

        with patch("wiki.compile._get_domain", return_value="pedagogy/a1"), \
             patch("wiki.compile._compiled_article_is_ready", return_value=True), \
             patch("wiki.compile.gather_discovery_sources") as gather_sources, \
             patch("wiki.compile.enrich_sources") as enrich_sources, \
             patch("wiki.compile.compile_article") as compile_article, \
             patch("wiki.compile.update_index") as update_index, \
             patch("wiki.compile.log_event") as log_event:
            ok = cmd_compile_one("a1", "demo")

        assert ok is True
        gather_sources.assert_not_called()
        enrich_sources.assert_not_called()
        compile_article.assert_not_called()
        update_index.assert_not_called()
        log_event.assert_not_called()

    def test_compile_all_skips_ready_articles_before_cmd_compile_one(self):
        from wiki.compile import cmd_compile_all

        with patch("wiki.compile.list_discovery_slugs", return_value=["done", "todo"]), \
             patch("wiki.compile._compiled_article_is_ready", side_effect=[True, False]), \
             patch("wiki.compile._get_domain", return_value="pedagogy/a1"), \
             patch("wiki.compile.cmd_compile_one", return_value=True) as compile_one:
            cmd_compile_all("a1")

        compile_one.assert_called_once_with(
            "a1",
            "todo",
            force=False,
            dry_run=False,
            review=False,
            dim_review=False,
        )

    def test_dim_review_flag_runs_shadow_review_and_writes_report(self):
        from wiki.compile import cmd_compile_one

        article_path = Path("wiki/pedagogy/a1/demo.md")

        with patch("wiki.compile._get_domain", return_value="pedagogy/a1"), \
             patch("wiki.compile.gather_discovery_sources", return_value={}), \
             patch("wiki.compile.enrich_sources", return_value=[{"chunk_id": "c1", "text": "text"}]), \
             patch("wiki.compile._slug_to_topic", return_value="Demo"), \
             patch("wiki.compile.compile_article", return_value=article_path), \
             patch("wiki.compile._dim_review_article") as dim_review, \
             patch("wiki.compile.update_index"), \
             patch("wiki.compile.log_event"), \
             patch("wiki.state.is_compiled", return_value=False):
            ok = cmd_compile_one("a1", "demo", dim_review=True)

        assert ok is True
        dim_review.assert_called_once_with(article_path, "a1", "demo")

    def test_build_review_prompt_includes_sources_registry(self, tmp_path):
        from wiki.compile import _build_review_prompt

        wiki_dir = tmp_path / "wiki"
        article_dir = wiki_dir / "periods"
        article_dir.mkdir(parents=True)
        (article_dir / "kyivan-rus.sources.yaml").write_text(
            "sources:\n"
            "  - id: S1\n"
            "    file: feaa5fa7_c0001\n"
            "    type: literary\n",
            encoding="utf-8",
        )

        with patch("wiki.compile.WIKI_DIR", wiki_dir), \
             patch("wiki.compile._get_domain", return_value="periods"):
            prompt = _build_review_prompt(
                "<!-- wiki-meta\nslug: kyivan-rus\n-->\n\n# Title\n\nText [S1].",
                "article",
                "hist",
                "kyivan-rus",
                "r1",
            )

        assert "## Sources registry" in prompt
        assert "id: S1" in prompt


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


# ── Tests: _parse_review_scores ────────────────────────────────


def _overall(text: str) -> float:
    """Helper: parse overall score from review text."""
    from wiki.compile import _parse_review_scores
    return _parse_review_scores(text)["overall"]


class TestParseReviewScore:
    """Tests for decimal score parsing — the critical bug that prevented 9/10."""

    def test_integer_score(self):
        assert _overall("**Overall: 9/10**") == 9.0

    def test_decimal_score(self):
        assert _overall("**Overall: 8.8/10**") == 8.8

    def test_decimal_score_95(self):
        assert _overall("**Overall: 9.5/10**") == 9.5

    def test_score_with_dimensions(self):
        """The overall score should be picked, not a dimension score."""
        text = (
            "1. **Factual: 9/10** — good\n"
            "2. **Language: 9/10** — clean\n"
            "3. **Decolonization: 10/10** — perfect\n"
            "4. **Completeness: 7/10** — gaps\n"
            "5. **Actionable: 9/10** — good\n\n"
            "**Overall: 8.8/10**"
        )
        assert _overall(text) == 8.8

    def test_score_variant_formats(self):
        assert _overall("Score: 7.5/10") == 7.5
        assert _overall("Verdict: **9/10**") == 9.0
        assert _overall("Підсумок: 8/10") == 8.0

    def test_fallback_last_score(self):
        """When no 'overall' label exists, take the last score."""
        assert _overall("Factual: 9/10\nLanguage: 8/10\n\n7.5/10") == 7.5

    def test_no_score_returns_zero(self):
        assert _overall("No scores here.") == 0.0

    def test_ten_out_of_ten(self):
        assert _overall("**Overall: 10/10**") == 10.0


# ── Tests: _parse_review_scores (dimension parsing) ───────────


class TestParseReviewScores:
    """Tests for full dimension score parsing."""

    def test_all_dimensions_parsed(self):
        from wiki.compile import _parse_review_scores
        text = (
            "1. **Factual: 9/10** — evidence\n"
            "2. **Language: 8.5/10** — clean\n"
            "3. **Decolonization: 10/10** — perfect\n"
            "4. **Completeness: 7/10** — gaps\n"
            "5. **Actionable: 9/10** — useful\n\n"
            "**Overall: 8.7/10**"
        )
        scores = _parse_review_scores(text)
        assert scores["factual"] == 9.0
        assert scores["language"] == 8.5
        assert scores["decolonization"] == 10.0
        assert scores["completeness"] == 7.0
        assert scores["actionable"] == 9.0
        assert scores["overall"] == 8.7

    def test_missing_dimensions_default_zero(self):
        from wiki.compile import _parse_review_scores
        scores = _parse_review_scores("**Overall: 8/10**")
        assert scores["factual"] == 0.0
        assert scores["overall"] == 8.0

    def test_overall_independent_of_dimensions(self):
        """Overall is parsed from explicit label, not averaged."""
        from wiki.compile import _parse_review_scores
        text = (
            "Factual: 10/10\n"
            "Language: 10/10\n"
            "Decolonization: 10/10\n"
            "Completeness: 10/10\n"
            "Actionable: 10/10\n\n"
            "**Overall: 9/10**"  # Reviewer chose lower overall
        )
        scores = _parse_review_scores(text)
        assert scores["overall"] == 9.0  # Not 10


# ── Tests: log_event / read_log ─────────────────────────────────


class TestBuildLog:
    def test_log_and_read_roundtrip(self, tmp_path):
        """log_event writes JSONL, read_log reads it back."""
        from unittest.mock import patch

        from wiki.state import log_event, read_log

        with patch("wiki.state.WIKI_STATE_DIR", tmp_path):
            log_event("a2", "genitive-intro", "compile", words=1500, sources=40)
            log_event("a2", "genitive-intro", "review_round", round=1, score=8.4)
            log_event("a2", "genitive-intro", "review_pass", score=9.2, rounds=2)

            entries = read_log()
            assert len(entries) == 3
            assert entries[0]["event"] == "compile"
            assert entries[0]["words"] == 1500
            assert entries[1]["score"] == 8.4
            assert entries[2]["event"] == "review_pass"

    def test_read_log_filter_by_track(self, tmp_path):
        from unittest.mock import patch

        from wiki.state import log_event, read_log

        with patch("wiki.state.WIKI_STATE_DIR", tmp_path):
            log_event("a2", "slug1", "compile")
            log_event("b1", "slug2", "compile")
            log_event("a2", "slug3", "compile")

            a2_entries = read_log(track="a2")
            assert len(a2_entries) == 2
            assert all(e["track"] == "a2" for e in a2_entries)

    def test_read_log_empty(self, tmp_path):
        from unittest.mock import patch

        from wiki.state import read_log

        with patch("wiki.state.WIKI_STATE_DIR", tmp_path):
            assert read_log() == []


class TestReviewExisting:
    def test_reviews_only_track_owned_articles(self, tmp_path):
        from unittest.mock import patch

        from wiki.compile import cmd_review_existing

        wiki_dir = tmp_path / "wiki"
        periods = wiki_dir / "periods"
        figures = wiki_dir / "figures"
        periods.mkdir(parents=True)
        figures.mkdir(parents=True)
        target = periods / "kyivan-rus.md"
        other = figures / "shevchenko.md"
        target.write_text("# Kyivan Rus\n", encoding="utf-8")
        other.write_text("# Shevchenko\n", encoding="utf-8")

        reviewed = []
        with (
            patch("wiki.compile.list_discovery_slugs_readonly", return_value=["kyivan-rus"]),
            patch("wiki.config.WIKI_DIR", wiki_dir),
            patch("wiki.compile._get_domain", side_effect=lambda track, slug: "periods" if slug == "kyivan-rus" else "figures"),
            patch("wiki.compile._review_article", side_effect=lambda path, track, slug: reviewed.append(path)),
        ):
            cmd_review_existing("hist")

        assert reviewed == [target]
