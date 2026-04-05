"""Tests for wiki state management — list_wiki_articles, progress edge cases."""

import os
import sys
from unittest.mock import patch

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))


# ── Tests: list_wiki_articles ────────────────────────────────────


class TestListWikiArticles:
    def test_finds_articles_in_subdirs(self, tmp_path):
        from wiki.state import list_wiki_articles

        wiki = tmp_path / "wiki"
        genres = wiki / "folk" / "genres"
        genres.mkdir(parents=True)
        (genres / "dumy.md").write_text("# Думи\n\nContent here.\n")
        (genres / "kazky.md").write_text("# Казки\n\nMore content.\n")

        with patch("wiki.state.WIKI_DIR", wiki):
            articles = list_wiki_articles()
        assert len(articles) == 2
        paths = {a["path"] for a in articles}
        assert "folk/genres/dumy.md" in paths
        assert "folk/genres/kazky.md" in paths

    def test_extracts_title_from_h1(self, tmp_path):
        from wiki.state import list_wiki_articles

        wiki = tmp_path / "wiki"
        d = wiki / "folk"
        d.mkdir(parents=True)
        (d / "test.md").write_text("# Думи лицарські\n\nContent.\n")

        with patch("wiki.state.WIKI_DIR", wiki):
            articles = list_wiki_articles()
        assert articles[0]["title"] == "Думи лицарські"

    def test_empty_title_when_no_h1(self, tmp_path):
        from wiki.state import list_wiki_articles

        wiki = tmp_path / "wiki"
        d = wiki / "folk"
        d.mkdir(parents=True)
        (d / "notitle.md").write_text("No heading here.\n")

        with patch("wiki.state.WIKI_DIR", wiki):
            articles = list_wiki_articles()
        assert articles[0]["title"] == ""

    def test_calculates_word_count(self, tmp_path):
        from wiki.state import list_wiki_articles

        wiki = tmp_path / "wiki"
        d = wiki / "folk"
        d.mkdir(parents=True)
        (d / "test.md").write_text("# Title\n\none two three four five\n")

        with patch("wiki.state.WIKI_DIR", wiki):
            articles = list_wiki_articles()
        assert articles[0]["word_count"] == 7  # "#", "Title", "one", "two", "three", "four", "five"

    def test_skips_state_dir(self, tmp_path):
        from wiki.state import list_wiki_articles

        wiki = tmp_path / "wiki"
        state = wiki / ".state"
        state.mkdir(parents=True)
        (state / "progress.yaml").write_text("test\n")

        d = wiki / "folk"
        d.mkdir(parents=True)
        (d / "real.md").write_text("# Real\n")

        with patch("wiki.state.WIKI_DIR", wiki):
            articles = list_wiki_articles()
        assert len(articles) == 1
        assert articles[0]["path"] == "folk/real.md"

    def test_skips_index_files(self, tmp_path):
        from wiki.state import list_wiki_articles

        wiki = tmp_path / "wiki"
        d = wiki / "folk"
        d.mkdir(parents=True)
        (d / "index.md").write_text("# Index\n")
        (d / "real.md").write_text("# Real Article\n")

        with patch("wiki.state.WIKI_DIR", wiki):
            articles = list_wiki_articles()
        assert len(articles) == 1
        assert "index" not in articles[0]["path"]

    def test_returns_empty_when_no_articles(self, tmp_path):
        from wiki.state import list_wiki_articles

        wiki = tmp_path / "wiki"
        wiki.mkdir()

        with patch("wiki.state.WIKI_DIR", wiki):
            articles = list_wiki_articles()
        assert articles == []


# ── Tests: state edge cases ──────────────────────────────────────


class TestStateEdgeCases:
    def test_load_progress_creates_state_dir(self, tmp_path):
        from wiki.state import load_progress

        state_dir = tmp_path / ".state"
        with patch("wiki.state.WIKI_STATE_DIR", state_dir), \
             patch("wiki.state.WIKI_DIR", tmp_path):
            progress = load_progress()
        assert state_dir.exists()
        assert progress == {"articles": {}, "last_updated": None}

    def test_load_progress_handles_empty_yaml(self, tmp_path):
        from wiki.state import load_progress

        state_dir = tmp_path / ".state"
        state_dir.mkdir()
        (state_dir / "progress.yaml").write_text("")
        (state_dir / ".gitignore").write_text("*\n")

        with patch("wiki.state.WIKI_STATE_DIR", state_dir), \
             patch("wiki.state.WIKI_DIR", tmp_path):
            progress = load_progress()
        assert progress["articles"] == {}

    def test_save_progress_adds_timestamp(self, tmp_path):
        from wiki.state import load_progress, save_progress

        state_dir = tmp_path / ".state"
        with patch("wiki.state.WIKI_STATE_DIR", state_dir), \
             patch("wiki.state.WIKI_DIR", tmp_path):
            progress = load_progress()
            progress["articles"]["test/a"] = {"status": "compiled", "word_count": 100}
            save_progress(progress)

            reloaded = load_progress()
        assert reloaded["last_updated"] is not None
        assert reloaded["articles"]["test/a"]["word_count"] == 100

    def test_is_compiled_false_for_non_compiled_status(self, tmp_path):
        from wiki.state import is_compiled, load_progress, save_progress

        state_dir = tmp_path / ".state"
        with patch("wiki.state.WIKI_STATE_DIR", state_dir), \
             patch("wiki.state.WIKI_DIR", tmp_path):
            progress = load_progress()
            progress["articles"]["test/x"] = {"status": "failed", "word_count": 0}
            save_progress(progress)

            assert not is_compiled("test/x")

    def test_status_summary_excludes_non_compiled(self, tmp_path):
        from wiki.state import get_status_summary, load_progress, save_progress

        state_dir = tmp_path / ".state"
        with patch("wiki.state.WIKI_STATE_DIR", state_dir), \
             patch("wiki.state.WIKI_DIR", tmp_path):
            progress = load_progress()
            progress["articles"]["folk/a"] = {"status": "compiled", "word_count": 500}
            progress["articles"]["folk/b"] = {"status": "failed", "word_count": 0}
            save_progress(progress)

            summary = get_status_summary()
        assert summary["total_compiled"] == 1
        assert summary["total_words"] == 500
