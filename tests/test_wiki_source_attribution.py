"""Tests for corpus-aware wiki source attribution."""

from __future__ import annotations

import os
import sqlite3
import sys

import pytest

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))


@pytest.fixture
def attribution_db(tmp_path, monkeypatch):
    from wiki import source_attribution

    db_path = tmp_path / "sources.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE textbook_sections (
            section_id INTEGER PRIMARY KEY,
            source_file TEXT NOT NULL,
            grade INTEGER NOT NULL,
            section_title TEXT NOT NULL,
            page_start INTEGER
        );

        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            grade TEXT DEFAULT '',
            author TEXT DEFAULT ''
        );

        CREATE TABLE literary_texts (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            author TEXT DEFAULT '',
            work TEXT DEFAULT ''
        );

        CREATE TABLE external_articles (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            url TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            domain TEXT DEFAULT '',
            video_id TEXT DEFAULT '',
            chunk_start_ts INTEGER,
            chunk_end_ts INTEGER
        );

        CREATE TABLE wikipedia (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE ukrainian_wiki (
            id INTEGER PRIMARY KEY,
            passage_id TEXT NOT NULL UNIQUE,
            article_slug TEXT NOT NULL,
            article_title TEXT NOT NULL DEFAULT '',
            section_path TEXT NOT NULL DEFAULT ''
        );
        """
    )
    conn.executemany(
        "INSERT INTO textbook_sections(section_id, source_file, grade, section_title, page_start) VALUES (?, ?, ?, ?, ?)",
        [
            (77, "11-klas-ukrmova-avramenko-2019", 11, "Складне речення", 123),
        ],
    )
    conn.executemany(
        "INSERT INTO textbooks(id, chunk_id, title, source_file, grade, author) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (402, "raw-402", "Складнопідрядні речення", "11-klas-ukrmova-avramenko-2019", "11", "Авраменко"),
        ],
    )
    conn.executemany(
        "INSERT INTO literary_texts(id, chunk_id, title, source_file, author, work) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (12, "4f2a9abc_c0012", "Енеїда, уривок", "eneida", "Іван Котляревський", "Енеїда"),
        ],
    )
    conn.executemany(
        """
        INSERT INTO external_articles(
            id, chunk_id, url, title, source_file, domain, video_id, chunk_start_ts, chunk_end_ts
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                1,
                "ext-ulp-yt-001",
                "https://www.youtube.com/watch?v=abc123",
                "Podcast episode",
                "ulp_youtube",
                "youtube.com",
                "abc123",
                15,
                29,
            ),
            (
                2,
                "ext-blog-001",
                "https://example.com/article",
                "Article",
                "ulp_blogs",
                "example.com",
                "",
                None,
                None,
            ),
        ],
    )
    conn.execute(
        "INSERT INTO wikipedia(id, title, url) VALUES (?, ?, ?)",
        (1, "Українська мова", "https://uk.wikipedia.org/wiki/%D0%A3%D0%BA%D1%80%D0%B0%D1%97%D0%BD%D1%81%D1%8C%D0%BA%D0%B0_%D0%BC%D0%BE%D0%B2%D0%B0"),
    )
    conn.execute(
        """
        INSERT INTO ukrainian_wiki(id, passage_id, article_slug, article_title, section_path)
        VALUES (?, ?, ?, ?, ?)
        """,
        (1, "uw-1", "academic-writing", "Academic Writing", "Style / Evidence"),
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(source_attribution, "DEFAULT_DB_PATH", db_path)
    return db_path


def test_resolve_chunk_attribution_for_textbook_sections(attribution_db) -> None:
    from wiki.source_attribution import resolve_chunk_attribution

    result = resolve_chunk_attribution("S77", "textbook_sections")

    assert result == {
        "file": "11-klas-ukrmova-avramenko-2019_s0077",
        "type": "textbook",
        "title": "Складне речення",
        "grade": 11,
        "page": 123,
    }


def test_resolve_chunk_attribution_for_textbooks(attribution_db) -> None:
    from wiki.source_attribution import resolve_chunk_attribution

    result = resolve_chunk_attribution("raw-402", "textbooks")

    assert result == {
        "file": "11-klas-ukrmova-avramenko-2019_c0402",
        "type": "textbook",
        "title": "Складнопідрядні речення",
        "grade": 11,
        "author": "Авраменко",
    }


def test_resolve_chunk_attribution_for_literary_texts(attribution_db) -> None:
    from wiki.source_attribution import resolve_chunk_attribution

    result = resolve_chunk_attribution("4f2a9abc_c0012", "modern_literary")

    assert result == {
        "file": "eneida_c0012",
        "type": "literary",
        "title": "Енеїда",
        "author": "Іван Котляревський",
    }


def test_resolve_chunk_attribution_for_external_video(attribution_db) -> None:
    from wiki.source_attribution import resolve_chunk_attribution

    result = resolve_chunk_attribution("ext-ulp-yt-001", "external_articles")

    assert result == {
        "file": "https://www.youtube.com/watch?v=abc123&t=15s",
        "type": "external",
        "title": "Podcast episode",
        "url": "https://www.youtube.com/watch?v=abc123&t=15s",
        "domain": "youtube.com",
        "video_id": "abc123",
        "ts_start": 15,
        "ts_end": 29,
    }


def test_resolve_chunk_attribution_for_external_article_without_video(attribution_db) -> None:
    from wiki.source_attribution import resolve_chunk_attribution

    result = resolve_chunk_attribution("ext-blog-001", "external")

    assert result == {
        "file": "https://example.com/article",
        "type": "external",
        "title": "Article",
        "url": "https://example.com/article",
        "domain": "example.com",
        "video_id": None,
        "ts_start": None,
        "ts_end": None,
    }


def test_resolve_chunk_attribution_for_wikipedia(attribution_db) -> None:
    from wiki.source_attribution import resolve_chunk_attribution

    result = resolve_chunk_attribution("Українська мова", "wikipedia")

    assert result == {
        "file": "wikipedia/Українська мова",
        "type": "wikipedia",
        "title": "Українська мова",
        "url": "https://uk.wikipedia.org/wiki/%D0%A3%D0%BA%D1%80%D0%B0%D1%97%D0%BD%D1%81%D1%8C%D0%BA%D0%B0_%D0%BC%D0%BE%D0%B2%D0%B0",
    }


def test_resolve_chunk_attribution_for_ukrainian_wiki(attribution_db) -> None:
    from wiki.source_attribution import resolve_chunk_attribution

    result = resolve_chunk_attribution("uw-1", "ukrainian_wiki")

    assert result == {
        "file": "ukrainian_wiki/academic-writing_Style-Evidence",
        "type": "ukrainian_wiki",
        "title": "Academic Writing",
        "section_path": "Style / Evidence",
    }


def test_resolve_chunk_attribution_falls_back_to_inferred_type_for_filename_shaped_ids(attribution_db) -> None:
    from wiki.source_attribution import resolve_chunk_attribution

    result = resolve_chunk_attribution("11-klas-ukrmova-avramenko-2019_s0077", "")

    assert result == {
        "file": "11-klas-ukrmova-avramenko-2019_s0077",
        "type": "textbook",
        "title": "11-klas-ukrmova-avramenko-2019_s0077",
    }
