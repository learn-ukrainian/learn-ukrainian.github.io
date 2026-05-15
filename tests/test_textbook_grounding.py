from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from scripts.build import linear_pipeline


def _seed_textbook_db(path: Path, rows: list[dict[str, Any]]) -> None:
    with sqlite3.connect(str(path)) as conn:
        conn.execute(
            """
            CREATE TABLE textbooks (
                id INTEGER PRIMARY KEY,
                chunk_id TEXT NOT NULL,
                title TEXT NOT NULL,
                text TEXT NOT NULL,
                source_file TEXT NOT NULL,
                grade TEXT,
                author TEXT,
                char_count INTEGER DEFAULT 0,
                parent_section_id INTEGER
            )
            """
        )
        for index, row in enumerate(rows, start=1):
            conn.execute(
                """
                INSERT INTO textbooks (
                    id, chunk_id, title, text, source_file, grade, author
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    index,
                    row["chunk_id"],
                    row.get("title", "Сторінка"),
                    row["text"],
                    row["source_file"],
                    row.get("grade", ""),
                    row.get("author", ""),
                ),
            )


def test_karaman_grade10_p187_resolves_to_chunk(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Reproducer from #1975: matcher must find the existing chunk."""
    db_path = tmp_path / "sources.db"
    _seed_textbook_db(
        db_path,
        [
            {
                "chunk_id": "10-klas-ukrmova-karaman-2018_s0187",
                "title": "Сторінка 105",
                "text": "§ 38 Розмовна, просторічна, емоційно забарвлена лексика.",
                "source_file": "10-klas-ukrmova-karaman-2018",
                "grade": "10",
                "author": "karaman",
            }
        ],
    )
    monkeypatch.setattr(linear_pipeline, "TEXTBOOK_SOURCES_DB_PATH", db_path)

    hits = linear_pipeline._search_textbook_hits(
        "Караман Grade 10, p.187 ",
        level="a1",
        limit=1,
    )

    assert len(hits) == 1
    assert hits[0]["chunk_id"] == "10-klas-ukrmova-karaman-2018_s0187"


def test_zakhariychuk_grade4_p162_reports_corpus_missing_deterministically(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """A missing page should not fall through to topic FTS and a false hit."""
    db_path = tmp_path / "sources.db"
    _seed_textbook_db(
        db_path,
        [
            {
                "chunk_id": "4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0161",
                "title": "Сторінка 161",
                "text": "Сусідня сторінка є в корпусі.",
                "source_file": "4-klas-ukrayinska-mova-zaharijchuk-2021-1",
                "grade": "4",
                "author": "zaharijchuk",
            }
        ],
    )
    monkeypatch.setattr(linear_pipeline, "TEXTBOOK_SOURCES_DB_PATH", db_path)

    hits = linear_pipeline._search_textbook_hits(
        "Захарійчук Grade 4, p.162 ",
        level="a1",
        limit=1,
    )

    assert hits == []


def test_zakhariychuk_grade4_p162_matches_source_file_without_suffix(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Author slugs may end at the author token, without a trailing suffix."""
    db_path = tmp_path / "sources.db"
    _seed_textbook_db(
        db_path,
        [
            {
                "chunk_id": "4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0161",
                "title": "Сторінка 161",
                "text": "Сусідня сторінка є в корпусі.",
                "source_file": "4-klas-ukrayinska-mova-zaharijchuk-2021-1",
                "grade": "4",
                "author": "zaharijchuk",
            },
            {
                "chunk_id": "4-klas-ukrmova-zaharijchuk_s0162",
                "title": "Сторінка 162",
                "text": "Дієслова на -ся. Зіставте їх вимову й правопис.",
                "source_file": "4-klas-ukrmova-zaharijchuk",
                "grade": "4",
                "author": "zaharijchuk",
            },
        ],
    )
    monkeypatch.setattr(linear_pipeline, "TEXTBOOK_SOURCES_DB_PATH", db_path)

    hits = linear_pipeline._search_textbook_hits(
        "Захарійчук Grade 4, p.162 ",
        level="a1",
        limit=1,
    )

    assert len(hits) == 1
    assert hits[0]["chunk_id"] == "4-klas-ukrmova-zaharijchuk_s0162"


def test_free_form_title_falls_back_to_fts5(monkeypatch) -> None:
    """Titles without 'Grade N, p.M' format use the existing FTS5 path."""
    from wiki import sources_db

    calls: list[tuple[str, str, int]] = []

    def fake_search_sources(query: str, *, track: str, limit: int) -> list[dict]:
        calls.append((query, track, limit))
        return [
            {
                "chunk_id": "fallback-textbook-hit",
                "source_type": "textbook_sections",
                "text": "Fallback textbook excerpt.",
            },
            {
                "chunk_id": "external-hit",
                "source_type": "external",
                "text": "External excerpt.",
            },
        ]

    monkeypatch.setattr(sources_db, "search_sources", fake_search_sources)

    hits = linear_pipeline._search_textbook_hits(
        "free-form source title morning routine",
        level="a1",
        limit=1,
    )

    assert calls == [("free-form source title morning routine", "a1", 4)]
    assert [hit["chunk_id"] for hit in hits] == ["fallback-textbook-hit"]


def test_textbook_excerpt_context_uses_reference_title_for_direct_lookup(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "sources.db"
    _seed_textbook_db(
        db_path,
        [
            {
                "chunk_id": "10-klas-ukrmova-karaman-2018_s0187",
                "title": "Сторінка 105",
                "text": "§ 38 Розмовна, просторічна, емоційно забарвлена лексика.",
                "source_file": "10-klas-ukrmova-karaman-2018",
                "grade": "10",
                "author": "karaman",
            }
        ],
    )
    monkeypatch.setattr(linear_pipeline, "TEXTBOOK_SOURCES_DB_PATH", db_path)
    plan = {
        "references": [{"title": "Караман Grade 10, p.187"}],
        "title": "ranok",
        "subtitle": "routine morning",
        "content_outline": [
            {"section": "ranok routine", "points": ["morning", "breakfast"]}
        ],
    }

    context = linear_pipeline._build_textbook_excerpt_context(plan, "a1")

    assert "10-klas-ukrmova-karaman-2018" in context
    assert "corpus_missing: true" not in context
