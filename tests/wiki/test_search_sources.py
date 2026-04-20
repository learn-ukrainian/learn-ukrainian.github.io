from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki import sources_db


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


def _seed_conn(conn: sqlite3.Connection) -> None:
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
                "grade1-book",
                1,
                "Апостроф і наголос",
                "§ 1",
                1,
                2,
                2,
                "Апостроф і наголос. Чергування у-в і м'які приголосні.",
            ),
            (
                202,
                "grade5-book",
                5,
                "Гортань",
                "§ 2",
                3,
                4,
                2,
                "Гортань, голосові зв'язки та оглушення.",
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
            (1, "grade1-book_s0001", "Сторінка 1", "Апостроф і наголос у слові.", "grade1-book", "1", "tester", 40, 101),
            (2, "grade1-book_s0002", "Сторінка 2", "Чергування у-в і м'які приголосні.", "grade1-book", "1", "tester", 38, 101),
            (3, "grade5-book_s0001", "Сторінка 5", "Гортань і голосові зв'язки.", "grade5-book", "5", "tester", 34, 202),
            (4, "grade5-book_s0002", "Сторінка 6", "Оглушення в кінці слова.", "grade5-book", "5", "tester", 28, 202),
        ],
    )


def test_search_sections_fts5_groups_chunks_and_applies_fixed_weights(monkeypatch):
    conn = _make_conn()
    _seed_conn(conn)
    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)

    results = sources_db._search_sections_fts5(
        ['"апостроф і наголос"'],
        {"апостроф", "наголос", "чергування"},
        track="a1",
        max_chunk_candidates=10,
        max_sections=10,
    )

    assert [row["section_id"] for row in results] == [101]
    assert results[0]["bucket_a_hits"] == 1
    assert results[0]["bucket_b_hits"] == 2
    assert results[0]["section_score"] == 5
    assert results[0]["chunk_id"] == "S101"
    assert results[0]["text"] == results[0]["full_text"]


def test_search_sources_uses_query_builder_and_dense_rerank(monkeypatch, tmp_path):
    conn = _make_conn()
    _seed_conn(conn)
    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)
    monkeypatch.setattr(sources_db, "_CORPORA", ("textbook_sections",))
    monkeypatch.setattr(
        sources_db,
        "build_query_buckets",
        lambda query, track: (['"апостроф і наголос"'], {"апостроф", "наголос"}),
    )
    monkeypatch.setattr(
        sources_db,
        "rerank_candidates",
        lambda query, sections, corpus, limit=10, **kwargs: sorted(
            sections,
            key=lambda row: -row["section_score"],
        )[:limit],
    )

    discovery_path = tmp_path / "demo.yaml"
    discovery_path.write_text("query_keywords: []\n", encoding="utf-8")

    results = sources_db.search_sources(discovery_path, track="a1", limit=5)

    assert len(results) == 1
    assert results[0]["grade"] == 1
    assert results[0]["section_title"] == "Апостроф і наголос"


def test_search_sources_archaic_strategy_is_reserved(tmp_path):
    discovery_path = tmp_path / "demo.yaml"
    discovery_path.write_text("query_keywords: []\n", encoding="utf-8")

    result = {
        "corpus": "archaic_literary",
        "chunk_id": "lit-1",
        "full_text": "Архаїчний уривок.",
        "text": "Архаїчний уривок.",
    }
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(sources_db, "_search_archaic_metadata", lambda *args, **kwargs: [result])
        results = sources_db.search_sources(discovery_path, track="ruth", strategy="archaic_metadata")

    assert results == [result]
