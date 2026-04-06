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


# ── Tests: _clean_rewrite_response ──────────────────────────────


class TestCleanRewriteResponse:
    """Tests for the rewrite response extraction / cleaning logic."""

    def test_clean_simple_response(self):
        from wiki.compile import _clean_rewrite_response
        # Must be >100 chars to pass minimum length check
        response = (
            "# My Title\n\n## Section 1\n"
            "Content here with enough text to pass the minimum length check. "
            "This needs to be over one hundred characters total."
        )
        result = _clean_rewrite_response(response)
        assert result is not None
        assert result.startswith("# My Title")

    def test_strips_prompt_echo(self):
        """Gemini echoes prompt instructions before the article."""
        from wiki.compile import _clean_rewrite_response
        response = (
            "Sure, here's the rewrite:\n\n"
            "## Instructions\n"
            "1. Read the critique.\n"
            "2. Fix the sections.\n\n"
            "# Побудова галузевої експертизи\n\n"
            "## Section 1\nGood content here.\n"
        )
        result = _clean_rewrite_response(response)
        assert result is not None
        assert result.startswith("# Побудова")
        assert "## Instructions" not in result
        assert "Read the critique" not in result

    def test_takes_last_title_on_duplicate(self):
        """When old article title is echoed, take the LAST occurrence."""
        from wiki.compile import _clean_rewrite_response
        response = (
            "# Побудова галузевої експертизи\n\n"
            "Old truncated content професі\n\n"
            "## Instructions\n1. Fix it.\n\n"
            "# Побудова галузевої експертизи\n\n"
            "## Section 1\nNew good content.\n"
        )
        result = _clean_rewrite_response(response)
        assert result is not None
        assert "Old truncated content" not in result
        assert "New good content" in result

    def test_rejects_truncated_response(self):
        """Reject responses that end mid-word (truncated output)."""
        from wiki.compile import _clean_rewrite_response
        response = (
            "# Title\n\n"
            "## Section\n"
            "Content with enough text to pass length checks but then it "
            "discusses important topics like linguistics and then trunca"
        )
        result = _clean_rewrite_response(response)
        assert result is None

    def _pad(self, text: str) -> str:
        """Pad short text to pass the 100-char minimum."""
        padding = "\n\nPadding text to meet minimum length requirement for test. " * 2
        return text + padding

    def test_accepts_response_ending_with_period(self):
        from wiki.compile import _clean_rewrite_response
        response = self._pad(
            "# Title\n\n"
            "## Section\n"
            "Content that ends properly."
        )
        result = _clean_rewrite_response(response)
        assert result is not None

    def test_accepts_response_ending_with_table_row(self):
        from wiki.compile import _clean_rewrite_response
        response = self._pad(
            "# Title\n\n"
            "## Section\n"
            "| cell1 | cell2 |"
        )
        result = _clean_rewrite_response(response)
        assert result is not None

    def test_accepts_response_ending_with_list_item(self):
        from wiki.compile import _clean_rewrite_response
        response = self._pad(
            "# Title\n\n"
            "## Section\n"
            "- A valid list item"
        )
        result = _clean_rewrite_response(response)
        assert result is not None

    def test_rejects_empty_response(self):
        from wiki.compile import _clean_rewrite_response
        assert _clean_rewrite_response("") is None
        assert _clean_rewrite_response("short") is None

    def test_rejects_no_markdown_headings(self):
        from wiki.compile import _clean_rewrite_response
        response = "Just plain text without any markdown headings. " * 10
        result = _clean_rewrite_response(response)
        assert result is None

    def test_accepts_section_headings_without_title(self):
        """Accept articles that have ## sections but no # title."""
        from wiki.compile import _clean_rewrite_response
        response = self._pad(
            "## Академічний контекст\n"
            "Content here about academic context.\n\n"
            "## Основний зміст\n"
            "More content here with enough length."
        )
        result = _clean_rewrite_response(response)
        assert result is not None

    def test_real_world_prompt_leak(self):
        """Reproduces the actual bug from C2 building-domain-expertise."""
        from wiki.compile import _clean_rewrite_response
        response = (
            "# Майстерність C2: Побудова галузевої експертизи\n\n"
            "<!-- wiki-meta\nslug: building-domain-expertise\n-->\n\n"
            "## Академічний контекст\n"
            "Content that gets cut off here професі\n\n"
            "## Instructions\n"
            "1. Read the critique carefully.\n"
            "2. Identify which SPECIFIC sections need rewriting.\n"
            "3. Output the COMPLETE article.\n\n"
            "## Current article\n\n"
            "# Майстерність C2: Побудова галузевої експертізи\n\n"
            "<!-- wiki-meta\nslug: building-domain-expertise\n-->\n\n"
            "## Академічний контекст\n"
            "The REAL rewritten content here.\n\n"
            "## Типові помилки L2\n"
            "Error pairs and good content."
        )
        result = _clean_rewrite_response(response)
        assert result is not None
        assert "REAL rewritten content" in result
        assert "## Instructions" not in result
        assert "Read the critique" not in result

    def test_strips_agent_bridge_metadata(self):
        """Agent bridge stdout leaks into response — must be stripped."""
        from wiki.compile import _clean_rewrite_response
        response = (
            "# Article Title\n\n"
            "## Section 1\n"
            "Good content about Ukrainian grammar with enough text to pass "
            "the minimum length check and make this a proper article.\n\n"
            "## Section 2\n"
            "More content about decolonization and pedagogy.\n"
            "\n"
            "✅ Gemini finished (5340 chars)\n"
            "✅ Message sent to Claude (ID: 28311)\n"
            "✓ Message 28311 acknowledged\n"
            "   Auto-acknowledged reply #28311\n"
        )
        result = _clean_rewrite_response(response)
        assert result is not None
        assert "Gemini finished" not in result
        assert "Message 28311" not in result
        assert "Auto-acknowledged" not in result
        assert "Good content" in result

    def test_strips_code_fence_wrapper(self):
        """Gemini wraps response in ```markdown ... ```."""
        from wiki.compile import _clean_rewrite_response
        response = (
            "```markdown\n"
            "# Article Title\n\n"
            "## Section 1\n"
            "Content inside code fence with enough text to pass length checks "
            "and demonstrate the code fence stripping works properly.\n"
            "```"
        )
        result = _clean_rewrite_response(response)
        assert result is not None
        assert result.startswith("# Article Title")
        assert "```" not in result

    def test_accepts_ending_with_parenthesis(self):
        """Response ending with ) from a markdown link should not be truncated."""
        from wiki.compile import _clean_rewrite_response
        response = self._pad(
            "# Title\n\n"
            "## Section\n"
            "See [Правопис 2019](https://2019.pravopys.net)"
        )
        result = _clean_rewrite_response(response)
        assert result is not None

    def test_accepts_ending_with_quotation(self):
        """Response ending with " should not be truncated."""
        from wiki.compile import _clean_rewrite_response
        response = self._pad(
            '# Title\n\n'
            '## Section\n'
            'Як писав Шевченко: "Борітеся — поборете"'
        )
        result = _clean_rewrite_response(response)
        assert result is not None

    def test_prompt_fragment_to_h2(self):
        """When article starts with ## (no H1), prompt echo should still be stripped."""
        from wiki.compile import _clean_rewrite_response
        response = (
            "## Instructions\n"
            "1. Fix the sections.\n\n"
            "## Академічний контекст\n"
            "Real content about academic context with enough text to meet "
            "the minimum length requirements for the function.\n\n"
            "## Основний зміст\n"
            "More real content here."
        )
        result = _clean_rewrite_response(response)
        assert result is not None
        assert "## Академічний контекст" in result
        assert "Fix the sections" not in result


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
