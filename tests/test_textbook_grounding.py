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


def test_litvinova_grade7_p55_resolves_to_chunk(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Audit citation: `Літвінова Grade 7, p.55` (a1-a2-plan-references-2026-05-15, how-many)."""
    db_path = tmp_path / "sources.db"
    _seed_textbook_db(
        db_path,
        [
            {
                "chunk_id": "7-klas-ukrmova-litvinova-2024_s0055",
                "title": "Сторінка 51",
                "text": "Лексика. Прочитайте текст і знайдіть синоніми.",
                "source_file": "7-klas-ukrmova-litvinova-2024",
                "grade": "7",
                "author": "litvinova",
            }
        ],
    )
    monkeypatch.setattr(linear_pipeline, "TEXTBOOK_SOURCES_DB_PATH", db_path)

    hits = linear_pipeline._search_textbook_hits(
        "Літвінова Grade 7, p.55",
        level="a1",
        limit=1,
    )

    assert len(hits) == 1
    assert hits[0]["chunk_id"] == "7-klas-ukrmova-litvinova-2024_s0055"


def test_litvinova_cyrillic_variant_resolves_same_as_primary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Cyrillic spelling variant `Литвінова` must resolve identically to `Літвінова`.

    Audit citation: `Литвінова Grade 5, p.104` (a2 metalanguage-syntax-cases).
    """
    db_path = tmp_path / "sources.db"
    _seed_textbook_db(
        db_path,
        [
            {
                "chunk_id": "5-klas-ukrmova-litvinova-2022_s0104",
                "title": "Сторінка 100",
                "text": "Синтаксис. Розгляньте речення.",
                "source_file": "5-klas-ukrmova-litvinova-2022",
                "grade": "5",
                "author": "litvinova",
            }
        ],
    )
    monkeypatch.setattr(linear_pipeline, "TEXTBOOK_SOURCES_DB_PATH", db_path)

    hits = linear_pipeline._search_textbook_hits(
        "Литвінова Grade 5, p.104",
        level="a2",
        limit=1,
    )

    assert len(hits) == 1
    assert hits[0]["chunk_id"] == "5-klas-ukrmova-litvinova-2022_s0104"


def test_golub_grade6_p179_resolves_to_chunk(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Audit citation: `Голуб Grade 6, с. 179` (a2 checkpoint-instrumental).

    Tested with `p.` form because `_parse_textbook_reference_title` accepts that
    syntax; the audit script normalises `с.`/`p.` upstream.
    """
    db_path = tmp_path / "sources.db"
    _seed_textbook_db(
        db_path,
        [
            {
                "chunk_id": "6-klas-ukrmova-golub-2023_s0179",
                "title": "Сторінка 176",
                "text": "Іменники в орудному відмінку. Виконайте вправу.",
                "source_file": "6-klas-ukrmova-golub-2023",
                "grade": "6",
                "author": "golub",
            }
        ],
    )
    monkeypatch.setattr(linear_pipeline, "TEXTBOOK_SOURCES_DB_PATH", db_path)

    hits = linear_pipeline._search_textbook_hits(
        "Голуб Grade 6, p.179",
        level="a2",
        limit=1,
    )

    assert len(hits) == 1
    assert hits[0]["chunk_id"] == "6-klas-ukrmova-golub-2023_s0179"


def test_varzatska_grade4_p38_resolves_to_chunk(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Audit citation: `Варзацька Grade 4, с. 38` (a2 checkpoint-cases)."""
    db_path = tmp_path / "sources.db"
    _seed_textbook_db(
        db_path,
        [
            {
                "chunk_id": "4-klas-ukrayinska-mova-varzatska-2021-1_s0038",
                "title": "Сторінка 40",
                "text": "Відмінки іменників. Знайдіть закінчення.",
                "source_file": "4-klas-ukrayinska-mova-varzatska-2021-1",
                "grade": "4",
                "author": "varzatska",
            }
        ],
    )
    monkeypatch.setattr(linear_pipeline, "TEXTBOOK_SOURCES_DB_PATH", db_path)

    hits = linear_pipeline._search_textbook_hits(
        "Варзацька Grade 4, p.38",
        level="a2",
        limit=1,
    )

    assert len(hits) == 1
    assert (
        hits[0]["chunk_id"]
        == "4-klas-ukrayinska-mova-varzatska-2021-1_s0038"
    )


def test_ponomarova_grade3_p86_resolves_to_chunk(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Audit citation: `Пономарова Grade 3, p.86` (a1 many-things)."""
    db_path = tmp_path / "sources.db"
    _seed_textbook_db(
        db_path,
        [
            {
                "chunk_id": "3-klas-ukrainska-mova-ponomarova-2020-1_s0086",
                "title": "Сторінка 87",
                "text": "Прочитайте текст і дайте відповіді на запитання.",
                "source_file": "3-klas-ukrainska-mova-ponomarova-2020-1",
                "grade": "3",
                "author": "ponomarova",
            }
        ],
    )
    monkeypatch.setattr(linear_pipeline, "TEXTBOOK_SOURCES_DB_PATH", db_path)

    hits = linear_pipeline._search_textbook_hits(
        "Пономарова Grade 3, p.86",
        level="a1",
        limit=1,
    )

    assert len(hits) == 1
    assert (
        hits[0]["chunk_id"]
        == "3-klas-ukrainska-mova-ponomarova-2020-1_s0086"
    )


def test_ponomarova_cyrillic_variant_resolves_same_as_primary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Cyrillic spelling variant `Пономарьова` must resolve identically to `Пономарова`.

    Audit citation: `Пономарьова Grade 4, с. 53` (a2 instrumental-accompaniment).
    """
    db_path = tmp_path / "sources.db"
    _seed_textbook_db(
        db_path,
        [
            {
                "chunk_id": "4-klas-ukrayinska-mova-ponomarova-2021-1_s0053",
                "title": "Сторінка 54",
                "text": "Іменники з прийменниками. Прочитайте.",
                "source_file": "4-klas-ukrayinska-mova-ponomarova-2021-1",
                "grade": "4",
                "author": "ponomarova",
            }
        ],
    )
    monkeypatch.setattr(linear_pipeline, "TEXTBOOK_SOURCES_DB_PATH", db_path)

    hits = linear_pipeline._search_textbook_hits(
        "Пономарьова Grade 4, p.53",
        level="a2",
        limit=1,
    )

    assert len(hits) == 1
    assert (
        hits[0]["chunk_id"]
        == "4-klas-ukrayinska-mova-ponomarova-2021-1_s0053"
    )


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
