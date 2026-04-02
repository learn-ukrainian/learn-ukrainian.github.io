"""Tests for Wikipedia cache and new Wikipedia query modes.

Tests wiki_cache.py (SQLite cache) and new source_query.py functions
(wikipedia_extract, wikipedia_section_text, _strip_wikitext).
No network calls — all API responses are mocked.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


# ── WikiCache unit tests ─────────────────────────────────────────

class TestWikiCache:
    """Test SQLite cache operations."""

    def setup_method(self, method):
        from rag.wiki_cache import WikiCache
        # Use temp file for each test
        self.db_path = Path(f"/tmp/test_wiki_cache_{id(method)}.db")
        self.cache = WikiCache(db_path=self.db_path, ttl=3600)

    def teardown_method(self, method):
        self.cache.close()
        self.db_path.unlink(missing_ok=True)

    def test_put_and_get(self):
        self.cache.put("summary", "Тарас Шевченко", '{"title": "Шевченко"}')
        result = self.cache.get("summary", "Тарас Шевченко")
        assert result == '{"title": "Шевченко"}'

    def test_miss_returns_none(self):
        assert self.cache.get("summary", "Не існує") is None

    def test_expired_returns_none(self):
        from rag.wiki_cache import WikiCache
        # Create cache with 1-second TTL
        short_cache = WikiCache(db_path=self.db_path, ttl=1)
        short_cache.put("summary", "Test", "data")
        # Manually backdate the entry
        short_cache._conn.execute(
            "UPDATE wiki_cache SET fetched_at = ? WHERE title = ?",
            (int(time.time()) - 10, "Test"),
        )
        short_cache._conn.commit()
        assert short_cache.get("summary", "Test") is None

    def test_negative_cache(self):
        from rag.wiki_cache import NEGATIVE_SENTINEL
        self.cache.put_negative("summary", "Fake Article")
        result = self.cache.get("summary", "Fake Article")
        assert result == NEGATIVE_SENTINEL
        assert self.cache.is_negative(result)

    def test_is_negative_false_for_normal(self):
        assert not self.cache.is_negative("some data")
        assert not self.cache.is_negative(None)

    def test_title_normalization(self):
        """Spaces→underscores, first letter capitalized."""
        self.cache.put("summary", "тарас шевченко", "data1")
        # Should find it with different spacing/case
        assert self.cache.get("summary", "Тарас_шевченко") == "data1"
        assert self.cache.get("summary", "тарас шевченко") == "data1"

    def test_composite_key_no_collision(self):
        """Different modes for same title don't collide."""
        self.cache.put("summary", "Київ", "summary data")
        self.cache.put("extract", "Київ", "extract data")
        assert self.cache.get("summary", "Київ") == "summary data"
        assert self.cache.get("extract", "Київ") == "extract data"

    def test_section_key(self):
        """Section parameter is part of the key."""
        self.cache.put("section", "Київ", "section 1 data", section="1")
        self.cache.put("section", "Київ", "section 2 data", section="2")
        assert self.cache.get("section", "Київ", "1") == "section 1 data"
        assert self.cache.get("section", "Київ", "2") == "section 2 data"

    def test_clear_expired(self):
        self.cache.put("summary", "Fresh", "data")
        # Manually backdate one entry
        self.cache._conn.execute(
            "INSERT OR REPLACE INTO wiki_cache (mode, title, section, response, fetched_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("summary", "Old", "", "old data", int(time.time()) - 7200),
        )
        self.cache._conn.commit()
        deleted = self.cache.clear_expired()
        assert deleted == 1
        assert self.cache.get("summary", "Fresh") == "data"

    def test_stats(self):
        self.cache.put("summary", "A", "data")
        self.cache.put_negative("summary", "B")
        stats = self.cache.stats()
        assert stats["total_entries"] == 2
        assert stats["negative_entries"] == 1

    def test_overwrite(self):
        """Put with same key overwrites."""
        self.cache.put("summary", "Київ", "old")
        self.cache.put("summary", "Київ", "new")
        assert self.cache.get("summary", "Київ") == "new"


# ── source_query new functions ───────────────────────────────────

class TestStripWikitext:
    """Test wikitext → plaintext conversion."""

    def setup_method(self):
        from rag.source_query import _strip_wikitext
        self.strip = _strip_wikitext

    def test_links(self):
        assert self.strip("[[Київ]]") == "Київ"
        assert self.strip("[[Київ|столиця]]") == "столиця"

    def test_bold_italic(self):
        assert self.strip("'''Тарас''' ''Шевченко''") == "Тарас Шевченко"

    def test_references(self):
        text = "Факт<ref name='a'>джерело</ref> тут."
        assert "<ref" not in self.strip(text)
        assert "Факт" in self.strip(text)

    def test_templates(self):
        text = "Текст {{lang|uk|слово}} далі."
        result = self.strip(text)
        assert "{{" not in result

    def test_section_headers(self):
        text = "== Біографія ==\nТекст біографії."
        result = self.strip(text)
        assert "Біографія" in result
        assert "==" not in result

    def test_html_comments(self):
        assert "коментар" not in self.strip("текст <!-- коментар --> далі")


class TestWikipediaExtract:
    """Test wikipedia_extract with mocked API."""

    def setup_method(self):
        from rag.source_query import wikipedia_extract
        self.extract = wikipedia_extract

    def test_returns_extract(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "12345": {
                        "title": "Тарас Шевченко",
                        "extract": "Тарас Григорович Шевченко — український поет.",
                        "fullurl": "https://uk.wikipedia.org/wiki/Тарас_Шевченко",
                    }
                }
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("rag.source_query._get", return_value=mock_response):
            result = self.extract("Тарас Шевченко")
        assert result is not None
        assert result["title"] == "Тарас Шевченко"
        assert "поет" in result["extract"]

    def test_not_found(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {"pages": {"-1": {"missing": ""}}}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("rag.source_query._get", return_value=mock_response):
            result = self.extract("Не існує стаття")
        assert result is None

    def test_truncation(self):
        long_text = "А" * 60000
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {"pages": {"1": {"title": "Test", "extract": long_text, "fullurl": "url"}}}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("rag.source_query._get", return_value=mock_response):
            result = self.extract("Test", max_chars=50000)
        assert result is not None
        assert len(result["extract"]) < 60000
        assert "[... truncated ...]" in result["extract"]


class TestWikipediaSectionText:
    """Test wikipedia_section_text with mocked API."""

    def setup_method(self):
        from rag.source_query import wikipedia_section_text
        self.section_text = wikipedia_section_text

    def test_returns_section(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "parse": {
                "title": "Тарас Шевченко",
                "wikitext": {"*": "== Біографія ==\n'''Тарас''' народився [[1814]] року."},
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("rag.source_query._get", return_value=mock_response):
            result = self.section_text("Тарас Шевченко", 1)
        assert result is not None
        assert "Тарас" in result["text"]
        assert "[[" not in result["text"]  # wikitext stripped

    def test_error_returns_none(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": {"code": "nosuchsection"}}
        mock_response.raise_for_status = MagicMock()

        with patch("rag.source_query._get", return_value=mock_response):
            result = self.section_text("Test", 999)
        assert result is None
