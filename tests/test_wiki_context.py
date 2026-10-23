"""Tests for wiki context provider — relevance scoring, budget, meta stripping."""

import os
import sys
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.reads_content

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
    (genres_dir / "dumy-lytsarski.sources.yaml").write_text(
        "sources:\n"
        "  - id: S1\n"
        "    file: feaa5fa7_c0001\n"
        "    type: literary\n",
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


# ── Tests: _strip_meta ───────────────────────────────────────────


class TestStripMeta:

    def test_malformed_meta_does_not_swallow_following_comment(self):
        """Regression for #1323 review msg #348 (Gemini blocker).

        Earlier `.*?` regex would greedily span into the next HTML comment
        when `-->` is missing on the wiki-meta block, silently deleting
        every line of prose between them. The current bounded match must
        leave the prose intact.
        """
        from wiki.context import _strip_meta

        content = (
            "<!-- wiki-meta\n"
            "  domain=folk\n"  # no closing -->
            "# Important Title\n\n"
            "Critical prose that must survive.\n"
            "<!-- VERIFY -->\n"
        )
        result = _strip_meta(content)
        assert "Important Title" in result
        assert "Critical prose that must survive." in result

    def test_meta_with_lt_in_yaml_value_still_strips(self):
        """Regression for #1323 review msg #350 (Gemini partial-pass).

        The earlier ``[^<]*?`` body forbade any ``<`` inside wiki-meta —
        so a valid block with ``description: "A < B"`` failed to match
        and the whole metadata leaked into reviewer context. The current
        tempered repetition allows bare ``<`` while still refusing to
        cross into another comment opener.
        """
        from wiki.context import _strip_meta

        content = (
            "<!-- wiki-meta\n"
            '  description: "A < B comparison"\n'
            "  slug=relations\n"
            "-->\n"
            "# Title\n\n"
            "Body.\n"
        )
        result = _strip_meta(content)
        assert "wiki-meta" not in result
        assert "description" not in result
        assert "# Title" in result
        assert "Body." in result


# ── Tests: get_wiki_context ──────────────────────────────────────


class TestGetWikiContext:

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

    def test_can_include_sources_registry_summary(self, wiki_dir):
        from wiki.context import get_wiki_context

        with patch("wiki.context.WIKI_DIR", wiki_dir):
            ctx = get_wiki_context("folk", "dumy-lytsarski", include_sources_registry=True)

        assert "Sources: S1=feaa5fa7_c0001" in ctx
