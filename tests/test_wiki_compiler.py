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


# ── Tests: _parse_review_score ─────────────────────────────────


class TestParseReviewScore:
    """Tests for decimal score parsing — the critical bug that prevented 9/10."""

    def test_integer_score(self):
        from wiki.compile import _parse_review_score
        text = "**Overall: 9/10**"
        assert _parse_review_score(text) == 9.0

    def test_decimal_score(self):
        from wiki.compile import _parse_review_score
        text = "**Overall: 8.8/10**"
        assert _parse_review_score(text) == 8.8

    def test_decimal_score_95(self):
        from wiki.compile import _parse_review_score
        text = "**Overall: 9.5/10**"
        assert _parse_review_score(text) == 9.5

    def test_score_with_dimensions(self):
        """The overall score should be picked, not a dimension score."""
        from wiki.compile import _parse_review_score
        text = (
            "1. **Factual: 9/10** — good\n"
            "2. **Language: 9/10** — clean\n"
            "3. **Decolonization: 10/10** — perfect\n"
            "4. **Completeness: 7/10** — gaps\n"
            "5. **Actionable: 9/10** — good\n\n"
            "**Overall: 8.8/10**"
        )
        assert _parse_review_score(text) == 8.8

    def test_score_variant_formats(self):
        from wiki.compile import _parse_review_score
        # "Score:" label
        assert _parse_review_score("Score: 7.5/10") == 7.5
        # "verdict" label
        assert _parse_review_score("Verdict: **9/10**") == 9.0
        # Ukrainian label
        assert _parse_review_score("Підсумок: 8/10") == 8.0

    def test_fallback_last_score(self):
        """When no 'overall' label exists, take the last score."""
        from wiki.compile import _parse_review_score
        text = "Factual: 9/10\nLanguage: 8/10\n\n7.5/10"
        assert _parse_review_score(text) == 7.5

    def test_no_score_returns_zero(self):
        from wiki.compile import _parse_review_score
        assert _parse_review_score("No scores here.") == 0.0

    def test_ten_out_of_ten(self):
        from wiki.compile import _parse_review_score
        assert _parse_review_score("**Overall: 10/10**") == 10.0


# ── Tests: _extract_and_apply_fixes ────────────────────────────


class TestExtractAndApplyFixes:
    def test_applies_fixes(self):
        from wiki.compile import _extract_and_apply_fixes
        review = (
            "Review text...\n"
            "<fixes>\n"
            "old: bad text\n"
            "new: good text\n"
            "</fixes>"
        )
        article = "Some bad text here."
        updated, total, applied = _extract_and_apply_fixes(review, article)
        assert updated == "Some good text here."
        assert total == 1
        assert applied == 1

    def test_no_fixes_block(self):
        from wiki.compile import _extract_and_apply_fixes
        review = "Perfect article. <fixes></fixes>"
        article = "Original text."
        updated, total, applied = _extract_and_apply_fixes(review, article)
        assert updated == "Original text."
        assert total == 0
        assert applied == 0

    def test_fix_not_matching(self):
        from wiki.compile import _extract_and_apply_fixes
        review = (
            "<fixes>\n"
            "old: text that does not exist\n"
            "new: replacement\n"
            "</fixes>"
        )
        article = "Original article content."
        updated, total, applied = _extract_and_apply_fixes(review, article)
        assert updated == "Original article content."
        assert total == 1
        assert applied == 0

    def test_ignores_prompt_template_fixes(self):
        """Takes the LAST <fixes> block, ignoring earlier ones (prompt template echo)."""
        from wiki.compile import _extract_and_apply_fixes
        review = (
            "Prompt template echo:\n"
            "<fixes>\n"
            "old: exact text to find in the article\n"
            "new: replacement text\n"
            "</fixes>\n\n"
            "Actual review:\n"
            "<fixes>\n"
            "old: real problem\n"
            "new: real fix\n"
            "</fixes>"
        )
        article = "Contains real problem to fix."
        updated, total, applied = _extract_and_apply_fixes(review, article)
        assert "real fix" in updated
        assert total == 1
        assert applied == 1

    def test_code_fences_stripped(self):
        """Code fences around <fixes> shouldn't break parsing."""
        from wiki.compile import _extract_and_apply_fixes
        review = (
            "```\n"
            "<fixes>\n"
            "old: broken\n"
            "new: fixed\n"
            "</fixes>\n"
            "```"
        )
        article = "This is broken content."
        updated, _total, applied = _extract_and_apply_fixes(review, article)
        assert "fixed" in updated
        assert applied == 1

    def test_insert_after_directive(self):
        """INSERT AFTER: should add new content after anchor text."""
        from wiki.compile import _extract_and_apply_fixes
        review = (
            "<fixes>\n"
            "INSERT AFTER: ## Section One\n"
            "NEW TEXT: Added paragraph after section one.\n"
            "</fixes>"
        )
        article = "## Section One\n\nExisting content.\n\n## Section Two\n"
        updated, total, applied = _extract_and_apply_fixes(review, article)
        assert "Added paragraph after section one." in updated
        assert "## Section One" in updated
        assert updated.index("Added paragraph") < updated.index("Existing content")
        assert total == 1
        assert applied == 1

    def test_mixed_fixes_and_inserts(self):
        """Both old:/new: and INSERT AFTER: in the same <fixes> block."""
        from wiki.compile import _extract_and_apply_fixes
        review = (
            "<fixes>\n"
            "old: bad word\n"
            "new: good word\n"
            "---\n"
            "INSERT AFTER: ## Header\n"
            "NEW TEXT: New paragraph here.\n"
            "</fixes>"
        )
        article = "## Header\n\nSome bad word here.\n"
        updated, total, applied = _extract_and_apply_fixes(review, article)
        assert "good word" in updated
        assert "New paragraph here." in updated
        assert total == 2
        assert applied == 2

    def test_fuzzy_whitespace_matching(self):
        """Extra whitespace in old: text should still match via fuzzy fallback."""
        from wiki.compile import _extract_and_apply_fixes
        review = (
            "<fixes>\n"
            "old: text  with   extra spaces\n"
            "new: text with normal spaces\n"
            "</fixes>"
        )
        # Article has single spaces — exact match fails, fuzzy should work
        article = "Some text with extra spaces here."
        updated, total, applied = _extract_and_apply_fixes(review, article)
        assert "text with normal spaces" in updated
        assert total == 1
        assert applied == 1


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


# ── Tests: _needs_structural_rewrite ───────────────────────────


class TestNeedsStructuralRewrite:
    def test_all_high_no_rewrite(self):
        from wiki.compile import _needs_structural_rewrite
        scores = {"factual": 9, "language": 9, "decolonization": 10,
                  "completeness": 8, "actionable": 9, "overall": 9}
        assert not _needs_structural_rewrite(scores)

    def test_one_dimension_below_8(self):
        from wiki.compile import _needs_structural_rewrite
        scores = {"factual": 9, "language": 9, "decolonization": 10,
                  "completeness": 7, "actionable": 9, "overall": 8.8}
        assert _needs_structural_rewrite(scores)

    def test_overall_below_8(self):
        from wiki.compile import _needs_structural_rewrite
        scores = {"factual": 8, "language": 8, "decolonization": 8,
                  "completeness": 8, "actionable": 8, "overall": 7.5}
        assert _needs_structural_rewrite(scores)

    def test_boundary_exactly_8(self):
        from wiki.compile import _needs_structural_rewrite
        scores = {"factual": 8, "language": 8, "decolonization": 8,
                  "completeness": 8, "actionable": 8, "overall": 8}
        assert not _needs_structural_rewrite(scores)


# ── Tests: _parse_insert_directives ────────────────────────────


class TestParseInsertDirectives:
    def test_single_insert(self):
        from wiki.compile import _parse_insert_directives
        text = "INSERT AFTER: anchor text\nNEW TEXT: new content"
        pairs = _parse_insert_directives(text)
        assert len(pairs) == 1
        assert pairs[0] == ("anchor text", "new content")

    def test_multiple_inserts(self):
        from wiki.compile import _parse_insert_directives
        text = (
            "INSERT AFTER: first anchor\n"
            "NEW TEXT: first addition\n"
            "---\n"
            "INSERT AFTER: second anchor\n"
            "NEW TEXT: second addition"
        )
        pairs = _parse_insert_directives(text)
        assert len(pairs) == 2

    def test_multiline_new_text(self):
        from wiki.compile import _parse_insert_directives
        text = (
            "INSERT AFTER: ## Section\n"
            "NEW TEXT: Line one\n"
            "Line two\n"
            "Line three"
        )
        pairs = _parse_insert_directives(text)
        assert len(pairs) == 1
        assert pairs[0][1] == "Line one\nLine two\nLine three"

    def test_ignores_old_new_pairs(self):
        """INSERT AFTER parser should not pick up old:/new: pairs."""
        from wiki.compile import _parse_insert_directives
        text = (
            "old: some text\n"
            "new: replacement\n"
            "---\n"
            "INSERT AFTER: anchor\n"
            "NEW TEXT: addition"
        )
        pairs = _parse_insert_directives(text)
        assert len(pairs) == 1
        assert pairs[0][0] == "anchor"


# ── Tests: _normalize_whitespace ───────────────────────────────


class TestNormalizeWhitespace:
    def test_collapses_multiple_spaces(self):
        from wiki.compile import _normalize_whitespace
        assert _normalize_whitespace("hello   world") == "hello world"

    def test_strips_trailing_whitespace(self):
        from wiki.compile import _normalize_whitespace
        assert _normalize_whitespace("hello   \nworld  ") == "hello\nworld"

    def test_preserves_newlines(self):
        from wiki.compile import _normalize_whitespace
        assert _normalize_whitespace("line1\n\nline2") == "line1\n\nline2"


# ── Tests: _fuzzy_replace (direct) ────────────────────────────


class TestFuzzyReplace:
    """Direct tests for fuzzy whitespace-normalized replacement."""

    def test_extra_spaces_in_article(self):
        from wiki.compile import _fuzzy_replace
        article = "Hello  world  here."
        result = _fuzzy_replace(article, "Hello world here.", "Fixed.")
        assert result == "Fixed."

    def test_match_at_position_zero(self):
        """Critical edge case: match at start of article."""
        from wiki.compile import _fuzzy_replace
        article = "Bad  text  at start. Rest of article."
        result = _fuzzy_replace(article, "Bad text at start.", "Good text.")
        assert result is not None
        assert result.startswith("Good text.")
        assert "Rest of article." in result

    def test_match_at_end(self):
        from wiki.compile import _fuzzy_replace
        article = "Start. End  with  spaces"
        result = _fuzzy_replace(article, "End with spaces", "End clean")
        assert result is not None
        assert result == "Start. End clean"

    def test_no_match_returns_none(self):
        from wiki.compile import _fuzzy_replace
        result = _fuzzy_replace("Hello world", "Goodbye world", "X")
        assert result is None

    def test_trailing_whitespace_in_article(self):
        from wiki.compile import _fuzzy_replace
        article = "Line one   \nLine two"
        result = _fuzzy_replace(article, "Line one\nLine two", "Merged")
        assert result is not None
        assert result == "Merged"

    def test_exact_match_still_works(self):
        """Fuzzy replace should work even when exact match would succeed."""
        from wiki.compile import _fuzzy_replace
        article = "Exact text here."
        result = _fuzzy_replace(article, "Exact text here.", "Replaced.")
        assert result == "Replaced."

    def test_preserves_surrounding_content(self):
        from wiki.compile import _fuzzy_replace
        article = "Before.  Middle  text  here.  After."
        result = _fuzzy_replace(article, "Middle text here.", "Fixed middle.")
        assert result is not None
        assert result.startswith("Before.")
        assert result.endswith("After.")
