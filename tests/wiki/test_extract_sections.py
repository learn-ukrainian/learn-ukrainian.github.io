from __future__ import annotations

import sqlite3

import pytest

from scripts.wiki.extract_sections import (
    assign_sections,
    build_section_groups,
    column_exists,
    ensure_schema,
    load_textbook_rows,
    persist_sections,
)
from scripts.wiki.rollback_sections import rebuild_textbooks_without_parent

TEXTBOOKS_SCHEMA_SQL = """
CREATE TABLE textbooks (
    id INTEGER PRIMARY KEY,
    chunk_id TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source_file TEXT NOT NULL DEFAULT '',
    grade TEXT DEFAULT '',
    author TEXT DEFAULT '',
    char_count INTEGER DEFAULT 0
)
"""

TEXTBOOKS_FTS_SQL = """
CREATE VIRTUAL TABLE textbooks_fts USING fts5(
    title, text, content='textbooks', content_rowid='id', tokenize='unicode61'
)
"""

TEXTBOOKS_TRIGGER_SQL = """
CREATE TRIGGER textbooks_ai AFTER INSERT ON textbooks BEGIN
    INSERT INTO textbooks_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END
"""


def make_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(TEXTBOOKS_SCHEMA_SQL)
    conn.execute(TEXTBOOKS_FTS_SQL)
    conn.execute(TEXTBOOKS_TRIGGER_SQL)
    conn.row_factory = sqlite3.Row
    return conn


def insert_textbook_rows(conn: sqlite3.Connection, rows: list[dict[str, str]]) -> None:
    conn.executemany(
        """
        INSERT INTO textbooks (chunk_id, title, text, source_file, grade, author, char_count)
        VALUES (:chunk_id, :title, :text, :source_file, :grade, :author, :char_count)
        """,
        rows,
    )


def sample_rows() -> list[dict[str, str]]:
    return [
        {
            "chunk_id": "grade5-main_s0000",
            "title": "Сторінка 1",
            "text": "1\nРозділ 1. Фонетика\n§ 1. Звуки мови\nВправи до першого параграфа.",
            "source_file": "grade5-main",
            "grade": "5",
            "author": "tester",
            "char_count": 72,
        },
        {
            "chunk_id": "grade5-main_s0001",
            "title": "Сторінка 2",
            "text": "2\nРозділ 1\nТут триває пояснення про голосні та приголосні.",
            "source_file": "grade5-main",
            "grade": "5",
            "author": "tester",
            "char_count": 70,
        },
        {
            "chunk_id": "grade5-main_s0002",
            "title": "Сторінка 3",
            "text": "3\n§ 2. Наголос\nПравила наголошування слів.",
            "source_file": "grade5-main",
            "grade": "5",
            "author": "tester",
            "char_count": 52,
        },
        {
            "chunk_id": "grade5-main_s0003",
            "title": "Сторінка 4",
            "text": "4\nЧергові приклади до теми про наголос і винятки.",
            "source_file": "grade5-main",
            "grade": "5",
            "author": "tester",
            "char_count": 56,
        },
        {
            "chunk_id": "grade8-roman_s0000",
            "title": "Сторінка 1",
            "text": "1\nIV. Хроніки\nОгляд подій середньовіччя.",
            "source_file": "grade8-roman",
            "grade": "8",
            "author": "tester",
            "char_count": 44,
        },
        {
            "chunk_id": "grade8-roman_s0001",
            "title": "Сторінка 2",
            "text": "2\nПродовження історичного матеріалу без нового заголовка.",
            "source_file": "grade8-roman",
            "grade": "8",
            "author": "tester",
            "char_count": 63,
        },
        {
            "chunk_id": "grade6-missing_s0000",
            "title": "Сторінка 1",
            "text": "1\nпросто продовження речення без помітного заголовка",
            "source_file": "grade6-missing",
            "grade": "6",
            "author": "tester",
            "char_count": 56,
        },
        {
            "chunk_id": "grade6-direct_s0000",
            "title": "§ 9. Пряма мова",
            "text": "Правила вживання прямої мови.",
            "source_file": "grade6-direct",
            "grade": "6",
            "author": "tester",
            "char_count": 32,
        },
        {
            "chunk_id": "grade6-direct_s0001",
            "title": "Сторінка 10",
            "text": "10\nРозбір прикладів із прямою мовою.",
            "source_file": "grade6-direct",
            "grade": "6",
            "author": "tester",
            "char_count": 41,
        },
    ]


def test_assign_sections_covers_clean_missing_mixed_and_roman_cases() -> None:
    conn = make_connection()
    insert_textbook_rows(conn, sample_rows())

    assignments = assign_sections(load_textbook_rows(conn))
    by_chunk = {assignment.row.chunk_id: assignment.section_title for assignment in assignments}

    assert by_chunk["grade5-main_s0000"] == "§ 1. Звуки мови"
    assert by_chunk["grade5-main_s0001"] == "§ 1. Звуки мови"
    assert by_chunk["grade5-main_s0002"] == "§ 2. Наголос"
    assert by_chunk["grade5-main_s0003"] == "§ 2. Наголос"
    assert by_chunk["grade8-roman_s0000"] == "IV. Хроніки"
    assert by_chunk["grade8-roman_s0001"] == "IV. Хроніки"
    assert by_chunk["grade6-missing_s0000"] is None
    assert by_chunk["grade6-direct_s0000"] == "§ 9. Пряма мова"
    assert by_chunk["grade6-direct_s0001"] == "§ 9. Пряма мова"


def test_assign_sections_rejects_sources_that_span_grade_boundaries() -> None:
    rows = [
        {
            "chunk_id": "boundary-source_s0000",
            "title": "Сторінка 1",
            "text": "1\n§ 1. Повторення\nТекст.",
            "source_file": "boundary-source",
            "grade": "5",
            "author": "tester",
            "char_count": 24,
        },
        {
            "chunk_id": "boundary-source_s0001",
            "title": "Сторінка 2",
            "text": "2\nТекст без нового заголовка.",
            "source_file": "boundary-source",
            "grade": "6",
            "author": "tester",
            "char_count": 29,
        },
    ]
    conn = make_connection()
    insert_textbook_rows(conn, rows)

    with pytest.raises(ValueError, match="boundary-source spans multiple grades"):
        assign_sections(load_textbook_rows(conn))


def test_schema_persist_is_idempotent_and_backfills_parent_ids() -> None:
    conn = make_connection()
    insert_textbook_rows(conn, sample_rows())

    rows = load_textbook_rows(conn)
    assignments = assign_sections(rows)
    sections = build_section_groups(assignments)

    with conn:
        ensure_schema(conn)
        persist_sections(conn, sections, assignments)

    first_section_count = conn.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0]
    first_backfilled = conn.execute(
        "SELECT COUNT(*) FROM textbooks WHERE parent_section_id IS NOT NULL"
    ).fetchone()[0]

    with conn:
        ensure_schema(conn)
        persist_sections(conn, sections, assignments)

    second_section_count = conn.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0]
    second_backfilled = conn.execute(
        "SELECT COUNT(*) FROM textbooks WHERE parent_section_id IS NOT NULL"
    ).fetchone()[0]
    direct_chunk_parent = conn.execute(
        "SELECT parent_section_id FROM textbooks WHERE chunk_id = 'grade6-direct_s0000'"
    ).fetchone()[0]

    assert column_exists(conn, "textbooks", "parent_section_id")
    assert first_section_count == second_section_count == 4
    assert first_backfilled == second_backfilled == 8
    assert direct_chunk_parent is not None


def test_rollback_rebuild_removes_parent_column_and_preserves_rows() -> None:
    conn = make_connection()
    insert_textbook_rows(conn, sample_rows())
    assignments = assign_sections(load_textbook_rows(conn))
    sections = build_section_groups(assignments)

    with conn:
        ensure_schema(conn)
        persist_sections(conn, sections, assignments)

    assert column_exists(conn, "textbooks", "parent_section_id")
    assert conn.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0] == 4

    with conn:
        conn.execute("DROP TABLE textbook_sections")
        conn.execute("DROP INDEX IF EXISTS idx_textbooks_parent")
        rebuild_textbooks_without_parent(conn)

    assert not column_exists(conn, "textbooks", "parent_section_id")
    assert conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0] == len(sample_rows())
