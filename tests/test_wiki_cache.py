"""Tests for Wikipedia cache and new Wikipedia query modes.

Tests wiki_cache.py (SQLite cache) and new source_query.py functions
(wikipedia_extract, wikipedia_section_text, _strip_wikitext).
No network calls — all API responses are mocked.
"""

from __future__ import annotations

import sqlite3
import sys
import time
from contextlib import closing
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


# ── WikiCache unit tests ─────────────────────────────────────────


class TestWikiCache:
    """Test SQLite cache operations."""

    @pytest.fixture(autouse=True)
    def _setup_cache(self, tmp_path, request):
        from rag.wiki_cache import WikiCache

        self.db_path = tmp_path / "wiki_cache.db"
        self.cache = WikiCache(db_path=self.db_path, ttl=3600)
        request.addfinalizer(self.cache.close)

    def test_put_and_get(self):
        self.cache.put("summary", "Тарас Шевченко", '{"title": "Шевченко"}')
        result = self.cache.get("summary", "Тарас Шевченко")
        assert result == '{"title": "Шевченко"}'

    def test_miss_returns_none(self):
        assert self.cache.get("summary", "Не існує") is None

    def test_expired_returns_none(self, request):
        from rag.wiki_cache import WikiCache

        # Create cache with 1-second TTL
        short_cache = WikiCache(db_path=self.db_path, ttl=1)
        request.addfinalizer(short_cache.close)
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
            "INSERT OR REPLACE INTO wiki_cache (mode, title, section, response, fetched_at) VALUES (?, ?, ?, ?, ?)",
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

    def test_negative_cache_expires_after_negative_ttl(self, request):
        """Negative entries expire after negative_ttl, while positive entries persist (#9016)."""
        from rag.wiki_cache import NEGATIVE_SENTINEL, WikiCache

        cache = WikiCache(db_path=self.db_path, ttl=30 * 86400, negative_ttl=10)
        request.addfinalizer(cache.close)
        cache.put("summary", "Positive", "valid article")
        cache.put_negative("summary", "Negative")

        assert cache.get("summary", "Positive") == "valid article"
        assert cache.get("summary", "Negative") == NEGATIVE_SENTINEL

        # Backdate both by 60 seconds (> negative_ttl 10s, but << positive_ttl 30d)
        cache._conn.execute(
            "UPDATE wiki_cache SET fetched_at = ?",
            (int(time.time()) - 60,),
        )
        cache._conn.commit()

        # Negative entry is expired and returns None (triggers re-validation)
        assert cache.get("summary", "Negative") is None
        # Positive entry remains valid
        assert cache.get("summary", "Positive") == "valid article"

        # clear_expired deletes the stale negative entry but preserves the positive entry
        deleted = cache.clear_expired()
        assert deleted == 1
        assert cache.get("summary", "Positive") == "valid article"

    def test_default_negative_ttl_expiry(self, tmp_path, request):
        """Default-constructed WikiCache() expires negative entries after DEFAULT_NEGATIVE_TTL (#9016)."""
        from rag.wiki_cache import DEFAULT_NEGATIVE_TTL, NEGATIVE_SENTINEL, WikiCache

        db_file = tmp_path / "default_wiki_cache.db"
        cache = WikiCache(db_path=db_file)
        request.addfinalizer(cache.close)
        assert cache.negative_ttl == DEFAULT_NEGATIVE_TTL
        assert cache.negative_ttl == 3600

        cache.put("summary", "Positive", "valid article")
        cache.put_negative("summary", "Negative")

        assert cache.get("summary", "Positive") == "valid article"
        assert cache.get("summary", "Negative") == NEGATIVE_SENTINEL

        # Backdate both entries by DEFAULT_NEGATIVE_TTL + 10s (> 1h, but << 30d)
        now = int(time.time())
        cache._conn.execute(
            "UPDATE wiki_cache SET fetched_at = ?",
            (now - (DEFAULT_NEGATIVE_TTL + 10),),
        )
        cache._conn.commit()

        # Negative entry is expired under production default negative TTL
        assert cache.get("summary", "Negative") is None
        # Positive entry remains valid
        assert cache.get("summary", "Positive") == "valid article"

        # clear_expired deletes stale negative entry, keeps positive
        deleted = cache.clear_expired()
        assert deleted == 1
        assert cache.get("summary", "Positive") == "valid article"

    @pytest.mark.parametrize("response", ["first test", "second test"])
    def test_database_and_sidecars_stay_in_test_directory(self, tmp_path, request, response):
        """Real simultaneous caches keep their files and data isolated (#9702)."""
        from rag.wiki_cache import WikiCache

        peer_path = tmp_path / "peer" / "wiki_cache.db"
        peer = WikiCache(db_path=peer_path, ttl=3600)
        request.addfinalizer(peer.close)

        assert self.cache.get("summary", "Isolation") is None
        self.cache.put("summary", "Isolation", response)
        peer.put("summary", "Isolation", "peer response")
        assert self.cache.get("summary", "Isolation") == response
        assert peer.get("summary", "Isolation") == "peer response"

        for cache, db_path, expected in (
            (self.cache, tmp_path / "wiki_cache.db", response),
            (peer, peer_path, "peer response"),
        ):
            actual_path = Path(cache._conn.execute("PRAGMA database_list").fetchone()[2])
            assert actual_path == db_path
            assert actual_path.is_relative_to(tmp_path)
            assert cache._conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
            for suffix in ("", "-wal", "-shm"):
                assert Path(f"{db_path}{suffix}").is_file()
            with closing(sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True)) as reader:
                assert reader.execute(
                    "SELECT response FROM wiki_cache WHERE title = ?", ("Isolation",)
                ).fetchone() == (expected,)

            cache.close()
            with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
                cache._conn.execute("SELECT 1")
            assert db_path.is_file()
            assert not Path(f"{db_path}-wal").exists()
            assert not Path(f"{db_path}-shm").exists()


# ── source_query new functions ───────────────────────────────────


class TestStripWikitext:
    """Test wikitext → plaintext conversion."""

    def setup_method(self):
        from rag.source_query import _strip_wikitext

        self.strip_wt = _strip_wikitext

    def test_links(self):
        assert self.strip_wt("[[Київ]]") == "Київ"
        assert self.strip_wt("[[Київ|столиця]]") == "столиця"

    def test_bold_italic(self):
        assert self.strip_wt("'''Тарас''' ''Шевченко''") == "Тарас Шевченко"

    def test_references(self):
        text = "Факт<ref name='a'>джерело</ref> тут."
        assert "<ref" not in self.strip_wt(text)
        assert "Факт" in self.strip_wt(text)

    def test_templates(self):
        text = "Текст {{lang|uk|слово}} далі."
        result = self.strip_wt(text)
        assert "{{" not in result

    def test_section_headers(self):
        text = "== Біографія ==\nТекст біографії."
        result = self.strip_wt(text)
        assert "Біографія" in result
        assert "==" not in result

    def test_html_comments(self):
        assert "коментар" not in self.strip_wt("текст <!-- коментар --> далі")


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
        mock_response.json.return_value = {"query": {"pages": {"-1": {"missing": ""}}}}
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
