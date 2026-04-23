from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from wiki import source_attribution, sources_db


def _make_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            grade TEXT DEFAULT '',
            author TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0,
            parent_section_id INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE VIRTUAL TABLE textbooks_fts USING fts5(
            title, text, content='textbooks', content_rowid='id', tokenize='unicode61'
        )
        """
    )
    conn.execute(
        """
        CREATE TRIGGER textbooks_ai AFTER INSERT ON textbooks BEGIN
            INSERT INTO textbooks_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
        END
        """
    )
    conn.execute(
        """
        CREATE TABLE textbook_sections (
            section_id INTEGER PRIMARY KEY,
            source_file TEXT NOT NULL,
            grade INTEGER NOT NULL,
            section_title TEXT NOT NULL,
            section_number TEXT,
            page_start INTEGER,
            page_end INTEGER,
            chunk_count INTEGER NOT NULL,
            full_text TEXT NOT NULL
        )
        """
    )
    return conn


def _seed_search_db(conn: sqlite3.Connection) -> None:
    conn.executemany(
        """
        INSERT INTO textbook_sections (
            section_id, source_file, grade, section_title, section_number,
            page_start, page_end, chunk_count, full_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                101,
                "11-klas-ukrmova-avramenko-2019",
                11,
                "Апостроф і наголос",
                "§ 1",
                123,
                124,
                2,
                "Апостроф і наголос. Чергування у-в і м'які приголосні.",
            ),
        ],
    )
    conn.executemany(
        """
        INSERT INTO textbooks (
            id, chunk_id, title, text, source_file, grade, author, char_count, parent_section_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                1,
                "11-klas-ukrmova-avramenko-2019_c0001",
                "Сторінка 1",
                "Апостроф і наголос у слові.",
                "11-klas-ukrmova-avramenko-2019",
                "11",
                "Авраменко",
                40,
                101,
            ),
            (
                2,
                "11-klas-ukrmova-avramenko-2019_c0002",
                "Сторінка 2",
                "Чергування у-в і м'які приголосні.",
                "11-klas-ukrmova-avramenko-2019",
                "11",
                "Авраменко",
                38,
                101,
            ),
        ],
    )


@pytest.fixture
def textbook_sections_db(tmp_path, monkeypatch):
    conn = _make_conn()
    _seed_search_db(conn)

    db_path = tmp_path / "sources.db"
    disk_conn = sqlite3.connect(str(db_path))
    disk_conn.execute(
        """
        CREATE TABLE textbook_sections (
            section_id INTEGER PRIMARY KEY,
            source_file TEXT NOT NULL,
            grade INTEGER NOT NULL,
            section_title TEXT NOT NULL,
            page_start INTEGER
        )
        """
    )
    disk_conn.execute(
        """
        INSERT INTO textbook_sections(section_id, source_file, grade, section_title, page_start)
        VALUES (?, ?, ?, ?, ?)
        """,
        (101, "11-klas-ukrmova-avramenko-2019", 11, "Апостроф і наголос", 123),
    )
    disk_conn.commit()
    disk_conn.close()

    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)
    monkeypatch.setattr(source_attribution, "DEFAULT_DB_PATH", db_path)
    yield conn
    conn.close()


def test_search_sections_fts5_emits_textbook_sections_corpus(textbook_sections_db) -> None:
    results = sources_db._search_sections_fts5(
        ['"апостроф і наголос"'],
        {"апостроф", "наголос", "чергування"},
        track="b1",
        max_chunk_candidates=10,
        max_sections=10,
    )

    assert results
    assert results[0].get("corpus") == "textbook_sections"
    assert results[0].get("unit_key") == "textbook_sections:S101"


def test_search_sections_fts5_results_route_to_textbook_attribution(textbook_sections_db) -> None:
    results = sources_db._search_sections_fts5(
        ['"апостроф і наголос"'],
        {"апостроф", "наголос", "чергування"},
        track="b1",
        max_chunk_candidates=10,
        max_sections=10,
    )

    attribution = source_attribution.resolve_chunk_attribution(
        results[0]["chunk_id"],
        results[0]["corpus"],
    )

    assert attribution["type"] == "textbook"
    assert re.fullmatch(r"^\d+-klas-.+_s\d+$", attribution["file"])
