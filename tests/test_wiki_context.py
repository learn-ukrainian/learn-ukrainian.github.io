"""Tests for wiki context provider — relevance scoring, budget, meta stripping."""

import os
import sys
from unittest.mock import patch

import pytest

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def wiki_dir(tmp_path):
    """Create a sample wiki directory with articles in multiple domains."""
    wiki = tmp_path / "wiki"

    # folk/genres — two articles
    genres_dir = wiki / "folk" / "genres"
    genres_dir.mkdir(parents=True)
    (genres_dir / "dumy-lytsarski.md").write_text(
        "<!-- wiki-meta domain=folk/genres slug=dumy-lytsarski -->\n"
        "# Думи лицарські\n\n"
        "Думи лицарські оспівують подвиги козаків.\n"
        "Самійло Кішка — один із головних героїв лицарських дум.\n",
        encoding="utf-8",
    )
    (genres_dir / "charivni-kazky.md").write_text(
        "# Чарівні казки\n\n"
        "Чарівні казки — жанр усної народної творчості.\n",
        encoding="utf-8",
    )

    # folk/ritual — one article
    ritual_dir = wiki / "folk" / "ritual"
    ritual_dir.mkdir(parents=True)
    (ritual_dir / "koliadky-shchedrivky.md").write_text(
        "# Колядки та щедрівки\n\n"
        "Колядки — обрядові пісні зимового циклу.\n",
        encoding="utf-8",
    )

    # periods — for hist track
    periods_dir = wiki / "periods"
    periods_dir.mkdir(parents=True)
    (periods_dir / "kozatska-doba.md").write_text(
        "# Козацька доба\n\n"
        "Козацька доба в історії України.\n",
        encoding="utf-8",
    )

    # index.md — should be skipped
    (wiki / "index.md").write_text("# Index\n", encoding="utf-8")

    return wiki


# ── Tests: _relevance_score ──────────────────────────────────────


class TestRelevanceScore:
    def test_exact_slug_match(self, wiki_dir):
        from wiki.context import _relevance_score

        path = wiki_dir / "folk" / "genres" / "dumy-lytsarski.md"
        score = _relevance_score(path, "dumy-lytsarski", "folk")
        assert score > 100  # Exact match bonus

    def test_partial_word_overlap(self, wiki_dir):
        from wiki.context import _relevance_score

        path = wiki_dir / "folk" / "genres" / "charivni-kazky.md"
        score = _relevance_score(path, "kazky-pro-tvaryn", "folk")
        # "kazky" overlaps
        assert score > 1

    def test_no_overlap_gets_baseline(self, wiki_dir):
        from wiki.context import _relevance_score

        path = wiki_dir / "folk" / "ritual" / "koliadky-shchedrivky.md"
        score = _relevance_score(path, "dumy-lytsarski", "folk")
        # No word overlap — baseline only
        assert score == 1

    def test_partial_slug_in_stem(self, wiki_dir):
        from wiki.context import _relevance_score

        path = wiki_dir / "folk" / "genres" / "dumy-lytsarski.md"
        # "dumy" is a word >3 chars and appears in stem
        score = _relevance_score(path, "dumy-nevilnytski", "folk")
        assert score > 10  # "dumy" word overlap + partial match


# ── Tests: _strip_meta ───────────────────────────────────────────


class TestStripMeta:
    def test_strips_meta_comment(self):
        from wiki.context import _strip_meta

        content = (
            "<!-- wiki-meta domain=folk/genres slug=test -->\n"
            "# Article Title\n\n"
            "Content here.\n"
        )
        result = _strip_meta(content)
        assert "wiki-meta" not in result
        assert "# Article Title" in result
        assert "Content here." in result

    def test_strips_multiline_meta(self):
        from wiki.context import _strip_meta

        content = (
            "<!-- wiki-meta\n"
            "  domain=folk/genres\n"
            "  slug=test\n"
            "-->\n"
            "# Title\n"
        )
        result = _strip_meta(content)
        assert "wiki-meta" not in result
        assert "# Title" in result

    def test_no_meta_returns_unchanged(self):
        from wiki.context import _strip_meta

        content = "# Title\n\nContent.\n"
        assert _strip_meta(content) == content.strip()

    def test_preserves_non_meta_comments(self):
        from wiki.context import _strip_meta

        content = "<!-- regular comment -->\n# Title\n"
        result = _strip_meta(content)
        assert "regular comment" in result


# ── Tests: get_wiki_context ──────────────────────────────────────


class TestGetWikiContext:
    def test_returns_relevant_articles(self, wiki_dir):
        from wiki.context import get_wiki_context

        with patch("wiki.context.WIKI_DIR", wiki_dir):
            ctx = get_wiki_context("folk", "dumy-lytsarski")
        assert "<wiki_context>" in ctx
        assert "Думи лицарські" in ctx

    def test_empty_for_missing_wiki_dir(self, tmp_path):
        from wiki.context import get_wiki_context

        with patch("wiki.context.WIKI_DIR", tmp_path / "nonexistent"):
            ctx = get_wiki_context("folk", "dumy-lytsarski")
        assert ctx == ""

    def test_empty_for_unknown_track(self, wiki_dir):
        from wiki.context import get_wiki_context

        with patch("wiki.context.WIKI_DIR", wiki_dir), \
             patch("wiki.context.TRACK_DOMAINS", {}):
            ctx = get_wiki_context("unknown-track", "something")
        assert ctx == ""

    def test_empty_when_no_articles_in_domain(self, wiki_dir):
        from wiki.context import get_wiki_context

        # Use a track whose domains don't exist in our fixture
        with patch("wiki.context.WIKI_DIR", wiki_dir), \
             patch("wiki.context.TRACK_DOMAINS", {"istorio": ["historiography"]}):
            ctx = get_wiki_context("istorio", "some-debate")
        assert ctx == ""

    def test_respects_budget_cap(self, wiki_dir):
        from wiki.context import get_wiki_context

        # Create a huge article that exceeds budget
        huge_dir = wiki_dir / "folk" / "huge"
        huge_dir.mkdir(parents=True)
        (huge_dir / "big-article.md").write_text(
            "# Big Article\n\n" + ("слово " * 50_000),
            encoding="utf-8",
        )

        with patch("wiki.context.WIKI_DIR", wiki_dir), \
             patch("wiki.context.WIKI_CONTEXT_BUDGET", 1000):
            ctx = get_wiki_context("folk", "big-article")
        # Should be truncated
        assert len(ctx) < 2000
        assert "скорочено" in ctx

    def test_sorts_by_relevance_exact_match_first(self, wiki_dir):
        from wiki.context import get_wiki_context

        with patch("wiki.context.WIKI_DIR", wiki_dir):
            ctx = get_wiki_context("folk", "dumy-lytsarski")
        # The exact match article should appear before others
        dumy_pos = ctx.find("Думи лицарські")
        kazky_pos = ctx.find("Чарівні казки")
        if kazky_pos != -1:
            assert dumy_pos < kazky_pos

    def test_skips_index_files(self, wiki_dir):
        from wiki.context import get_wiki_context

        # Add an index.md inside a domain dir
        (wiki_dir / "folk" / "index.md").write_text("# Folk Index\n")

        with patch("wiki.context.WIKI_DIR", wiki_dir):
            ctx = get_wiki_context("folk", "dumy-lytsarski")
        assert "Folk Index" not in ctx

    def test_hist_track_uses_periods_domain(self, wiki_dir):
        from wiki.context import get_wiki_context

        with patch("wiki.context.WIKI_DIR", wiki_dir):
            ctx = get_wiki_context("hist", "kozatska-doba")
        assert "Козацька доба" in ctx
