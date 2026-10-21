"""Tests for wiki context provider — relevance scoring, budget, meta stripping."""

import os
import sys

import pytest

pytestmark = pytest.mark.reads_content

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))


# ── Fixtures ──────────────────────────────────────────────────────


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
