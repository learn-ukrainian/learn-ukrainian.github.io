from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from scripts.build import linear_pipeline


def _seed_textbook_db(path: Path, rows: list[dict[str, Any]]) -> None:
    """Seed a textbooks table that matches the post-migration schema.

    Rows MUST provide ``author_uk`` (Cyrillic). The legacy Latin
    ``author`` field is optional and unused by the runtime matcher; it
    is kept for backwards compatibility with archived analytics.
    """
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
                author_uk TEXT DEFAULT '',
                char_count INTEGER DEFAULT 0,
                parent_section_id INTEGER
            )
            """
        )
        for index, row in enumerate(rows, start=1):
            conn.execute(
                """
                INSERT INTO textbooks (
                    id, chunk_id, title, text, source_file, grade, author, author_uk
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    index,
                    row["chunk_id"],
                    row.get("title", "Сторінка"),
                    row["text"],
                    row["source_file"],
                    row.get("grade", ""),
                    row.get("author", ""),
                    row["author_uk"],
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
                "author_uk": "Караман",
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
                "author_uk": "Захарійчук",
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
                "author_uk": "Захарійчук",
            },
            {
                "chunk_id": "4-klas-ukrmova-zaharijchuk_s0162",
                "title": "Сторінка 162",
                "text": "Дієслова на -ся. Зіставте їх вимову й правопис.",
                "source_file": "4-klas-ukrmova-zaharijchuk",
                "grade": "4",
                "author": "zaharijchuk",
                "author_uk": "Захарійчук",
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
                "author_uk": "Літвінова",
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


def test_seminar_textbook_miss_uses_literary_primary(monkeypatch) -> None:
    from wiki import sources_db

    search_sources_calls: list[tuple[str, str, int]] = []
    search_literary_calls: list[set[str]] = []

    def fake_search_sources(query: str, *, track: str, limit: int) -> list[dict]:
        search_sources_calls.append((query, track, limit))
        return [{"chunk_id": "external-hit", "source_type": "external", "text": "Not a primary."}]

    def fake_search_literary(keywords: set[str], max_total: int = 20) -> list[dict]:
        search_literary_calls.append(keywords)
        return [
            {
                "chunk_id": "chubynsky-koliadka_c0001",
                "corpus": "literary_texts",
                "source_type": "literary",
                "title": "Колядка",
                "text": "Коли не було з нащада світа, тоді не було неба ні землі.",
                "source_file": "chubynsky-koliadky",
            }
        ]

    monkeypatch.setattr(sources_db, "search_sources", fake_search_sources)
    monkeypatch.setattr(sources_db, "search_literary", fake_search_literary)
    plan = {
        "references": [{"title": "Чубинський колядки", "type": "primary"}],
        "title": "Колядки та щедрівки",
        "subtitle": "Міф про створення світу",
        "content_outline": [{"section": "Читання", "points": ["архаїчна колядка"]}],
    }

    context = linear_pipeline._build_textbook_excerpt_context(plan, "folk")

    assert search_sources_calls == [
        (
            "Чубинський колядки Колядки та щедрівки Міф про створення світу Читання архаїчна колядка",
            "folk",
            4,
        )
    ]
    assert search_literary_calls
    assert "Primary text (literary corpus)" in context
    assert "chunk_id: chubynsky-koliadka_c0001" in context
    assert "> Коли не було з нащада світа" in context
    assert "corpus_missing: true" not in context
    assert "corpus_missing" not in plan["references"][0]


def test_core_textbook_miss_does_not_call_literary(monkeypatch) -> None:
    from wiki import sources_db

    def fake_search_sources(query: str, *, track: str, limit: int) -> list[dict]:
        return []

    def fail_search_literary(keywords: set[str], max_total: int = 20) -> list[dict]:
        raise AssertionError("core levels must not query the literary corpus")

    monkeypatch.setattr(sources_db, "search_sources", fake_search_sources)
    monkeypatch.setattr(sources_db, "search_literary", fail_search_literary)
    plan = {
        "references": [{"title": "Чубинський колядки"}],
        "title": "Morning routine",
        "subtitle": "core sample",
        "content_outline": [{"section": "Practice", "points": ["verbs"]}],
    }

    context = linear_pipeline._build_textbook_excerpt_context(plan, "a1")

    assert "corpus_missing: true" in context
    assert plan["references"][0]["corpus_missing"] is True


_REPEATED_QUOTE = "Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо."
_REPEATED_CHUNK = {
    "chunk_id": "5-klas-ukrmova-avramenko-2022_s0073",
    "title": "Сторінка 73",
    "text": _REPEATED_QUOTE,
    "source_file": "5-klas-ukrmova-avramenko-2022",
    "source_type": "textbook",
    "corpus": "textbook_sections",
    "grade": "5",
    "author": "Авраменко",
}
def _excerpt_plan(titles: list[str], *, reference_type: str | None = None) -> dict[str, Any]:
    references: list[dict[str, Any]] = []
    for title in titles:
        reference: dict[str, Any] = {"title": title}
        if reference_type is not None:
            reference["type"] = reference_type
        references.append(reference)
    return {
        "references": references,
        "title": "Звуки",
        "subtitle": "літери",
        "content_outline": [{"section": "Читання", "points": ["букви", "звуки", "склад"]}],
    }


def _reference_sections(context: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    for part in context.split("\n### ")[1:]:
        title, _, body = part.partition("\n")
        sections.append((title.strip(), body.strip()))
    return sections


def _install_textbook_search(
    monkeypatch,
    by_title: dict[str, list[dict]],
) -> list[tuple[str, str, int]]:
    from wiki import sources_db

    calls: list[tuple[str, str, int]] = []

    def fake_search_sources(query: str, *, track: str, limit: int) -> list[dict]:
        calls.append((query, track, limit))
        for title, hits in by_title.items():
            if query == title or query.startswith(f"{title} "):
                return [dict(hit) for hit in hits]
        raise AssertionError(query)

    monkeypatch.setattr(sources_db, "search_sources", fake_search_sources)
    return calls


def test_distinct_textbook_chunks_are_both_quoted(tmp_path: Path, monkeypatch) -> None:
    """Two different chunks stay fully quoted, byte-for-byte with one reference each."""
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
                "author_uk": "Караман",
            },
            {
                "chunk_id": "7-klas-ukrmova-litvinova-2024_s0055",
                "title": "Сторінка 51",
                "text": "Лексика. Прочитайте текст і знайдіть синоніми.",
                "source_file": "7-klas-ukrmova-litvinova-2024",
                "grade": "7",
                "author": "litvinova",
                "author_uk": "Літвінова",
            },
        ],
    )
    monkeypatch.setattr(linear_pipeline, "TEXTBOOK_SOURCES_DB_PATH", db_path)
    titles = ["Караман Grade 10, p.187", "Літвінова Grade 7, p.55"]
    together = linear_pipeline._build_textbook_excerpt_context(_excerpt_plan(titles), "a1")
    sections = _reference_sections(together)

    assert [title for title, _body in sections] == titles
    assert "see " not in together
    for title in titles:
        alone = linear_pipeline._build_textbook_excerpt_context(_excerpt_plan([title]), "a1")
        assert _reference_sections(together)[_titles_index(sections, title)][1] == _reference_sections(alone)[0][1]
    assert together.count("> § 38 Розмовна, просторічна, емоційно забарвлена лексика.") == 1
    assert together.count("> Лексика. Прочитайте текст і знайдіть синоніми.") == 1


def _titles_index(sections: list[tuple[str, str]], title: str) -> int:
    return [item[0] for item in sections].index(title)


def test_corpus_missing_is_unchanged_when_another_reference_repeats(monkeypatch) -> None:
    calls = _install_textbook_search(
        monkeypatch,
        {
            "немає в корпусі": [],
            "Звуки і букви": [_REPEATED_CHUNK],
            "Абетка": [_REPEATED_CHUNK],
        },
    )
    plan = _excerpt_plan(["немає в корпусі", "Звуки і букви", "Абетка"])

    context = linear_pipeline._build_textbook_excerpt_context(plan, "a1")

    assert len(calls) == 3
    sections = _reference_sections(context)
    assert sections[0][1].splitlines() == [
        "*No textbook excerpt found for this reference.*",
        "corpus_missing: true",
    ]
    assert plan["references"][0]["corpus_missing"] is True
    assert "corpus_missing" not in plan["references"][1]
    assert "corpus_missing" not in plan["references"][2]
    assert f"> {_REPEATED_QUOTE}" in sections[1][1]
    assert sections[2][1] == "see Звуки і букви"


def test_identical_text_without_identity_is_not_collapsed(monkeypatch) -> None:
    """Same truncated text from two unidentified hits is not one chunk."""
    anonymous = {"source_type": "textbook", "text": _REPEATED_QUOTE, "title": "Уривок"}
    _install_textbook_search(
        monkeypatch,
        {"Перше джерело": [anonymous], "Друге джерело": [dict(anonymous)]},
    )

    context = linear_pipeline._build_textbook_excerpt_context(
        _excerpt_plan(["Перше джерело", "Друге джерело"]),
        "a1",
    )

    assert context.count(f"> {_REPEATED_QUOTE}") == 2
    assert "see " not in context
