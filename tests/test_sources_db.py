"""Tests for wiki/sources_db.py and wiki/build_sources_db.py."""

import json
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))


@pytest.fixture()
def sample_jsonl(tmp_path):
    """Create sample JSONL files for testing."""
    articles_dir = tmp_path / "data" / "external_articles"
    articles_dir.mkdir(parents=True)

    # Blog entries
    blogs = [
        {"url": "https://example.com/genitive", "title": "Родовий відмінок",
         "domain": "example.com", "text": "Родовий відмінок вживається для позначення володіння. Село має свою історію.", "char_count": 80},
        {"url": "https://example.com/dative", "title": "Давальний відмінок",
         "domain": "example.com", "text": "Давальний відмінок вказує на адресата дії.", "char_count": 50},
        {"url": "https://example.com/verbs", "title": "Ukrainian Verbs",
         "domain": "example.com", "text": "Basic verb conjugation patterns.", "char_count": 30},
    ]
    with open(articles_dir / "test_blogs.jsonl", "w") as f:
        for entry in blogs:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # YouTube entries
    videos = [
        {"video_id": "abc123", "url": "https://youtube.com/watch?v=abc123",
         "title": "Відмінки української мови", "language": "uk",
         "text": "Родовий відмінок — один з найчастіших відмінків.", "char_count": 55},
    ]
    with open(articles_dir / "test_youtube.jsonl", "w") as f:
        for entry in videos:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return articles_dir


class TestBuildSourcesDb:
    def test_builds_database(self, sample_jsonl):
        """Ingest JSONL files into SQLite database."""
        from wiki.build_sources_db import build

        db_path = sample_jsonl / "sources.db"
        result = build(db_path, external_dir=sample_jsonl, textbook_dir=sample_jsonl / "no_textbooks")
        assert result.exists()

        conn = sqlite3.connect(str(result))
        count = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        assert count == 4  # 3 blogs + 1 video

        # Check FTS index works
        fts_count = conn.execute(
            "SELECT COUNT(*) FROM sources_fts WHERE sources_fts MATCH '\"родовий\"'"
        ).fetchone()[0]
        assert fts_count >= 2  # Blog + YouTube both mention родовий

        conn.close()

    def test_deduplicates_urls(self, sample_jsonl):
        """Duplicate URLs across files are ingested only once."""
        from wiki.build_sources_db import build

        # Add duplicate entry to a second file
        dup = {"url": "https://example.com/genitive", "title": "Duplicate",
               "domain": "dup.com", "text": "Duplicate content.", "char_count": 10}
        with open(sample_jsonl / "dup_blogs.jsonl", "w") as f:
            f.write(json.dumps(dup, ensure_ascii=False) + "\n")

        db_path = sample_jsonl / "sources.db"
        build(db_path, external_dir=sample_jsonl, textbook_dir=sample_jsonl / "no_textbooks")

        conn = sqlite3.connect(str(db_path))
        count = conn.execute(
            "SELECT COUNT(*) FROM sources WHERE url = 'https://example.com/genitive'"
        ).fetchone()[0]
        assert count == 1
        conn.close()

    def test_rebuilds_from_scratch(self, sample_jsonl):
        """Running build twice replaces the database."""
        from wiki.build_sources_db import build

        db_path = sample_jsonl / "sources.db"
        build(db_path, external_dir=sample_jsonl, textbook_dir=sample_jsonl / "no_textbooks")
        build(db_path, external_dir=sample_jsonl, textbook_dir=sample_jsonl / "no_textbooks")  # Should not fail or double entries

        conn = sqlite3.connect(str(db_path))
        count = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        assert count == 4
        conn.close()


class TestSourcesDb:
    def test_search_articles(self, sample_jsonl, monkeypatch):
        """FTS5 search returns relevant articles."""
        from wiki.build_sources_db import build

        db_path = sample_jsonl / "sources.db"
        build(db_path, external_dir=sample_jsonl, textbook_dir=sample_jsonl / "no_textbooks")

        import wiki.sources_db as sdb
        monkeypatch.setattr(sdb, "SOURCES_DB_PATH", db_path)
        monkeypatch.setattr(sdb, "_conn", None)

        results = sdb.search_external({"родовий", "відмінок", "володіння"}, max_total=10)
        assert len(results) >= 1
        assert results[0]["source_type"] == "external"
        assert "chunk_id" in results[0]
        assert "_kw_score" in results[0]

    def test_search_excludes_urls(self, sample_jsonl, monkeypatch):
        """Excluded URLs are filtered from results."""
        from wiki.build_sources_db import build

        db_path = sample_jsonl / "sources.db"
        build(db_path, external_dir=sample_jsonl, textbook_dir=sample_jsonl / "no_textbooks")

        import wiki.sources_db as sdb
        monkeypatch.setattr(sdb, "SOURCES_DB_PATH", db_path)
        monkeypatch.setattr(sdb, "_conn", None)

        results = sdb.search_external(
            {"родовий", "відмінок"},
            exclude_urls={"https://example.com/genitive"},
        )
        urls_in_results = [r["text"] for r in results]
        assert not any("example.com/genitive" in t for t in urls_in_results)

    def test_lookup_by_url(self, sample_jsonl, monkeypatch):
        """URL lookup returns correct article."""
        from wiki.build_sources_db import build

        db_path = sample_jsonl / "sources.db"
        build(db_path, external_dir=sample_jsonl, textbook_dir=sample_jsonl / "no_textbooks")

        import wiki.sources_db as sdb
        monkeypatch.setattr(sdb, "SOURCES_DB_PATH", db_path)
        monkeypatch.setattr(sdb, "_conn", None)

        result = sdb.lookup_by_url("https://example.com/genitive")
        assert result is not None
        assert result["title"] == "Родовий відмінок"

    def test_lookup_www_normalization(self, sample_jsonl, monkeypatch):
        """URL lookup handles www/non-www variants."""
        from wiki.build_sources_db import build

        db_path = sample_jsonl / "sources.db"
        build(db_path, external_dir=sample_jsonl, textbook_dir=sample_jsonl / "no_textbooks")

        import wiki.sources_db as sdb
        monkeypatch.setattr(sdb, "SOURCES_DB_PATH", db_path)
        monkeypatch.setattr(sdb, "_conn", None)

        # Original URL has no www, lookup with www should still work
        result = sdb.lookup_by_url("https://www.example.com/genitive")
        assert result is not None

    def test_missing_db_returns_empty(self, tmp_path, monkeypatch):
        """Missing database returns empty results, not crash."""
        import wiki.sources_db as sdb
        monkeypatch.setattr(sdb, "SOURCES_DB_PATH", tmp_path / "nonexistent.db")
        monkeypatch.setattr(sdb, "_conn", None)

        assert sdb.search_external({"test"}) == []
        assert sdb.lookup_by_url("https://example.com") is None
        assert sdb.source_count() == 0
