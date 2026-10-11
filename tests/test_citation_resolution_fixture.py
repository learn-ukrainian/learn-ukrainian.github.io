"""CI fixture-backed guard ensuring citation resolution logic functions without sources.db.

EPIC #6321 / Issue #8403 AC-04.
"""

from __future__ import annotations

import os
import sqlite3
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))

from wiki.source_attribution import registry_entry_resolves_to_sources_db
from wiki.sources_schema import WikiSourceEntry


def test_citation_resolution_fixture_guard() -> None:
    """CI fixture-backed guard ensuring citation resolution logic functions without sources.db."""
    with sqlite3.connect(":memory:") as conn:
        conn.execute(
            """
            CREATE TABLE textbooks (
                id INTEGER PRIMARY KEY,
                chunk_id TEXT NOT NULL DEFAULT '',
                source_file TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL DEFAULT ''
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE textbook_sections (
                section_id INTEGER PRIMARY KEY,
                source_file TEXT NOT NULL,
                section_title TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE literary_texts (
                id INTEGER PRIMARY KEY,
                chunk_id TEXT NOT NULL DEFAULT '',
                source_file TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL DEFAULT ''
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE external_articles (
                id INTEGER PRIMARY KEY,
                chunk_id TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT ''
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE wikipedia (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT ''
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE ukrainian_wiki (
                id INTEGER PRIMARY KEY,
                passage_id TEXT NOT NULL DEFAULT '',
                article_slug TEXT NOT NULL DEFAULT '',
                article_title TEXT NOT NULL DEFAULT '',
                section_path TEXT NOT NULL DEFAULT ''
            );
            """
        )
        conn.execute(
            "INSERT INTO textbooks (id, chunk_id, source_file, title) VALUES (1, '10-klas-ukrmova-karaman-2018_s0408', '10-klas-ukrmova-karaman-2018', 'Тема 7')"
        )
        conn.execute(
            "INSERT INTO textbook_sections (section_id, source_file, section_title) VALUES (50263, '10-klas-ukrmova-karaman-2018', 'Сторінка 231')"
        )
        conn.execute(
            "INSERT INTO literary_texts (id, chunk_id, source_file, title) VALUES (1, 'shevchenko-zapovit_c0001', 'shevchenko-zapovit', 'Заповіт')"
        )
        conn.execute(
            "INSERT INTO external_articles (id, chunk_id, url) VALUES (1, 'ext-article-1', 'https://example.com/article')"
        )
        conn.execute(
            "INSERT INTO wikipedia (id, title, url) VALUES (1, 'Мова', 'https://uk.wikipedia.org/wiki/Мова')"
        )

        # Valid textbook chunk resolves
        entry_tb = WikiSourceEntry(id="S1", file="10-klas-ukrmova-karaman-2018_s0408", type="textbook")
        assert registry_entry_resolves_to_sources_db(entry_tb, conn) is True

        # Valid textbook section resolves
        entry_sec = WikiSourceEntry(id="S2", file="10-klas-ukrmova-karaman-2018_s50263", type="textbook")
        assert registry_entry_resolves_to_sources_db(entry_sec, conn) is True

        # Valid literary chunk resolves
        entry_lit = WikiSourceEntry(id="S3", file="shevchenko-zapovit_c0001", type="literary")
        assert registry_entry_resolves_to_sources_db(entry_lit, conn) is True

        # Valid external URL resolves
        entry_ext = WikiSourceEntry(id="S4", file="https://example.com/article", type="external")
        assert registry_entry_resolves_to_sources_db(entry_ext, conn) is True

        # Valid wikipedia resolves
        entry_wiki = WikiSourceEntry(id="S5", file="wikipedia/Мова", type="wikipedia")
        assert registry_entry_resolves_to_sources_db(entry_wiki, conn) is True

        # Dangling textbook chunk is rejected
        dangling_tb = WikiSourceEntry(id="S6", file="10-klas-ukrmova-karaman-2018_s9999", type="textbook")
        assert registry_entry_resolves_to_sources_db(dangling_tb, conn) is False

        # Cross-source collision: suffix matching another book's row/section must be rejected
        collision_sec = WikiSourceEntry(id="S7", file="nonexistent-book_s50263", type="textbook")
        assert registry_entry_resolves_to_sources_db(collision_sec, conn) is False

        collision_chunk = WikiSourceEntry(id="S8", file="nonexistent-book_c0001", type="textbook")
        assert registry_entry_resolves_to_sources_db(collision_chunk, conn) is False

        # Empty-prefix and bare-section lookups must be rejected
        empty_prefix = WikiSourceEntry(id="S9", file="_s50263", type="textbook")
        assert registry_entry_resolves_to_sources_db(empty_prefix, conn) is False

        bare_sec = WikiSourceEntry(id="S10", file="S50263", type="textbook")
        assert registry_entry_resolves_to_sources_db(bare_sec, conn) is False

        # Same book row id collision (row 1 is _s0408, not _c0001) must be rejected
        same_book_row = WikiSourceEntry(id="S11", file="10-klas-ukrmova-karaman-2018_c0001", type="textbook")
        assert registry_entry_resolves_to_sources_db(same_book_row, conn) is False
