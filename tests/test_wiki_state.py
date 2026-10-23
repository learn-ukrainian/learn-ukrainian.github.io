"""Tests for wiki state management — list_wiki_articles, progress edge cases."""

import os
import sys
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.reads_content

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))


# ── Tests: list_wiki_articles ────────────────────────────────────


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

    def test_save_progress_persists_per_article_timestamp(self, tmp_path):
        """``save_progress`` writes a ``compiled_at`` timestamp per article.

        The global ``last_updated`` key was retired when wiki state
        moved from YAML to SQLite — ``load_progress`` now always
        returns ``last_updated=None`` and relies on per-article
        ``compiled_at`` columns. This test therefore checks the
        replacement contract: every persisted article has a non-empty
        ``compiled_at`` after ``save_progress``.
        """
        from wiki.state import load_progress, save_progress

        state_dir = tmp_path / ".state"
        with patch("wiki.state.WIKI_STATE_DIR", state_dir), \
             patch("wiki.state.WIKI_DIR", tmp_path):
            progress = load_progress()
            progress["articles"]["test/a"] = {"status": "compiled", "word_count": 100}
            save_progress(progress)

            reloaded = load_progress()
        article = reloaded["articles"]["test/a"]
        assert article["word_count"] == 100
        assert article.get("compiled_at"), (
            f"compiled_at must be set after save_progress, got {article}"
        )

    def test_is_compiled_false_for_non_compiled_status(self, tmp_path):
        from wiki.state import is_compiled, load_progress, save_progress

        state_dir = tmp_path / ".state"
        with patch("wiki.state.WIKI_STATE_DIR", state_dir), \
             patch("wiki.state.WIKI_DIR", tmp_path):
            progress = load_progress()
            progress["articles"]["test/x"] = {"status": "failed", "word_count": 0}
            save_progress(progress)
            # Even with the .md present, status="failed" must short-circuit
            # to False — the file-existence check is an AND, not an OR.
            article = tmp_path / "test" / "x.md"
            article.parent.mkdir(parents=True, exist_ok=True)
            article.write_text("# X\n", encoding="utf-8")

            assert not is_compiled("test/x")
