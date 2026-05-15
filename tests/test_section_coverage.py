"""Tests for the textbook_sections coverage helper + ingester integration.

Covers:
- ``ensure_section_schema`` creates the table + parent_section_id column on
  a fresh DB (idempotent).
- ``link_lesson_sections`` writes section rows + links parent_section_id.
- Idempotency: re-running the helper does not duplicate sections.
- Ohoiko + ULP ingesters now produce 0 orphan chunks (regression for the
  2026-05-14 audit gap).
- Backfill script converts existing orphans into linked chunks.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from scripts.ingest import ohoiko_books_ingest as obi
from scripts.ingest import ulp_lesson_notes_ingest as ulp
from scripts.ingest._section_coverage import (
    NON_SCHOOL_GRADE,
    LessonSection,
    ensure_section_schema,
    link_lesson_sections,
)

# ---------------------------------------------------------------------------
# Minimal schema helpers
# ---------------------------------------------------------------------------


def _make_textbooks_db(path: Path, *, with_parent_col: bool = False) -> sqlite3.Connection:
    """Minimal textbooks-only schema (no FTS triggers; we test the
    INSERT layer)."""
    conn = sqlite3.connect(str(path))
    parent_col_sql = (
        ",\n        parent_section_id INTEGER REFERENCES textbook_sections(section_id)" if with_parent_col else ""
    )
    conn.executescript(
        f"""
        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            grade TEXT DEFAULT '',
            author TEXT DEFAULT '',
            author_uk TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0
            {parent_col_sql}
        );
        """
    )
    return conn


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------


def test_ensure_section_schema_creates_table_and_column(tmp_path: Path) -> None:
    """On a fresh DB with only ``textbooks``, the helper provisions both
    ``textbook_sections`` AND ``textbooks.parent_section_id``."""
    db = _make_textbooks_db(tmp_path / "fresh.db")
    ensure_section_schema(db)

    # textbook_sections exists with the right columns
    sect_cols = {r[1] for r in db.execute("PRAGMA table_info(textbook_sections)").fetchall()}
    assert "section_id" in sect_cols
    assert "source_file" in sect_cols
    assert "grade" in sect_cols
    assert "section_title" in sect_cols
    assert "full_text" in sect_cols

    # textbooks.parent_section_id exists
    tb_cols = {r[1] for r in db.execute("PRAGMA table_info(textbooks)").fetchall()}
    assert "parent_section_id" in tb_cols

    db.close()


def test_ensure_section_schema_idempotent(tmp_path: Path) -> None:
    """Running ``ensure_section_schema`` twice is a no-op the second
    time."""
    db = _make_textbooks_db(tmp_path / "x.db")
    ensure_section_schema(db)
    n_sect = db.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0]
    ensure_section_schema(db)
    assert db.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0] == n_sect
    db.close()


def _setup_db_with_chunks(tmp_path: Path) -> sqlite3.Connection:
    db = _make_textbooks_db(tmp_path / "x.db", with_parent_col=True)
    ensure_section_schema(db)
    # Manually insert two textbook chunks (no parent_section_id yet — orphans)
    db.execute(
        """INSERT INTO textbooks (chunk_id, title, text, source_file, char_count)
           VALUES ('test_l0001', 'Lesson 1: Hello', 'Hello world.', 'test', 12),
                  ('test_l0002', 'Lesson 2: Bye', 'Goodbye.', 'test', 8)"""
    )
    return db


def test_link_lesson_sections_writes_rows_and_links(tmp_path: Path) -> None:
    db = _setup_db_with_chunks(tmp_path)
    sections = [
        LessonSection(
            chunk_id="test_l0001",
            section_title="Lesson 1: Hello",
            section_number="1",
            full_text="Hello world.",
        ),
        LessonSection(
            chunk_id="test_l0002",
            section_title="Lesson 2: Bye",
            section_number="2",
            full_text="Goodbye.",
        ),
    ]
    inserted, linked = link_lesson_sections(db, source_file="test", sections=sections)
    db.commit()

    assert inserted == 2
    assert linked == 2
    # Both chunks now have parent_section_id
    rows = list(
        db.execute("SELECT chunk_id, parent_section_id FROM textbooks WHERE source_file='test' ORDER BY chunk_id")
    )
    assert all(r[1] is not None for r in rows), f"orphans remain: {rows}"
    # section_number is text-typed
    sec_rows = list(
        db.execute(
            "SELECT section_number, section_title, grade, chunk_count FROM textbook_sections "
            "WHERE source_file='test' ORDER BY section_number"
        )
    )
    assert sec_rows[0] == ("1", "Lesson 1: Hello", NON_SCHOOL_GRADE, 1)
    assert sec_rows[1] == ("2", "Lesson 2: Bye", NON_SCHOOL_GRADE, 1)
    db.close()


def test_link_lesson_sections_idempotent_on_unique_key(tmp_path: Path) -> None:
    """Re-running with the same (source_file, section_title) pairs must
    not duplicate section rows."""
    db = _setup_db_with_chunks(tmp_path)
    sections = [
        LessonSection(
            chunk_id="test_l0001",
            section_title="Lesson 1: Hello",
            section_number="1",
            full_text="Hello world.",
        ),
    ]
    link_lesson_sections(db, source_file="test", sections=sections)
    db.commit()
    link_lesson_sections(db, source_file="test", sections=sections)
    db.commit()
    n_sect = db.execute("SELECT COUNT(*) FROM textbook_sections WHERE source_file='test'").fetchone()[0]
    assert n_sect == 1, f"expected 1 section, got {n_sect}"
    db.close()


# ---------------------------------------------------------------------------
# Ingester integration tests (regression for the 2026-05-14 audit gap)
# ---------------------------------------------------------------------------


OHOIKO_FIXTURE = """1.    а                                               and, but
      Я люблю́ готува́ти, а ти?                       I like to cook, and you (informal)?
2.    або́ = чи                                       or
      За́раз або́ ніко́ли.                            Now or never.
"""


ULP_FIXTURE = """                                            Lesson Notes № 1

       Greetings
                                         Link to audio: ukrainianlessons.com/episode1

Привіт!
"""


def _make_full_db(path: Path) -> sqlite3.Connection:
    """DB with textbooks + textbook_sections schema (full schema match
    for the ingesters which now write to both tables)."""
    conn = _make_textbooks_db(path, with_parent_col=True)
    ensure_section_schema(conn)
    return conn


def test_ohoiko_ingest_produces_zero_orphans(tmp_path: Path) -> None:
    """Regression: after the 2026-05-14 section-coverage fix, Ohoiko
    ingest must produce 0 orphan chunks."""
    fixture_path = tmp_path / "ohoiko-fixture.txt"
    fixture_path.write_text(OHOIKO_FIXTURE, encoding="utf-8")
    entries = obi.parse_book(fixture_path, max_entry_number=10)
    assert len(entries) == 2

    db_path = tmp_path / "sources.db"
    conn = _make_full_db(db_path)
    book = obi.BookConfig(
        slug="test",
        source_file="test-ohoiko",
        txt_filename="ohoiko-fixture.txt",
        author="Anna Ohoiko",
        author_uk="Анна Огоїко",
        grade="",
        max_entry_number=10,
    )
    obi.ingest_entries(conn, book, entries)
    conn.commit()

    n_orphan = conn.execute(
        "SELECT COUNT(*) FROM textbooks WHERE source_file=? AND parent_section_id IS NULL",
        (book.source_file,),
    ).fetchone()[0]
    assert n_orphan == 0, f"orphans remain: {n_orphan}"

    n_sec = conn.execute(
        "SELECT COUNT(*) FROM textbook_sections WHERE source_file=?",
        (book.source_file,),
    ).fetchone()[0]
    assert n_sec == 2  # 1:1 with chunks

    # Section title format check
    titles = sorted(
        r[0]
        for r in conn.execute(
            "SELECT section_title FROM textbook_sections WHERE source_file=?",
            (book.source_file,),
        )
    )
    assert titles[0].startswith("Entry 1: ")
    assert titles[1].startswith("Entry 2: ")
    conn.close()


def test_ulp_ingest_produces_zero_orphans(tmp_path: Path) -> None:
    """Regression: after the 2026-05-14 section-coverage fix, ULP
    ingest must produce 0 orphan chunks."""
    fixture_path = tmp_path / "ulp-fixture.txt"
    fixture_path.write_text(ULP_FIXTURE, encoding="utf-8")
    lessons = ulp.parse_book(fixture_path)
    assert len(lessons) == 1

    db_path = tmp_path / "sources.db"
    conn = _make_full_db(db_path)
    book = ulp.BookConfig(
        slug="test",
        source_file="test-ulp",
        txt_filename="ulp-fixture.txt",
        season=1,
    )
    ulp.ingest_lessons(conn, book, lessons)
    conn.commit()

    n_orphan = conn.execute(
        "SELECT COUNT(*) FROM textbooks WHERE source_file=? AND parent_section_id IS NULL",
        (book.source_file,),
    ).fetchone()[0]
    assert n_orphan == 0, f"orphans remain: {n_orphan}"

    # Section title matches the ULP convention.
    title = conn.execute(
        "SELECT section_title FROM textbook_sections WHERE source_file=?",
        (book.source_file,),
    ).fetchone()[0]
    assert title == "Lesson 1: Greetings"
    conn.close()


def test_ohoiko_force_rerun_keeps_zero_orphans(tmp_path: Path) -> None:
    """When --force is used, the ingester DELETEs and re-creates
    everything (textbooks + textbook_sections). Result must still be
    0 orphans, no leftover sections."""
    fixture_path = tmp_path / "f.txt"
    fixture_path.write_text(OHOIKO_FIXTURE, encoding="utf-8")
    entries = obi.parse_book(fixture_path, max_entry_number=10)

    db_path = tmp_path / "sources.db"
    conn = _make_full_db(db_path)
    book = obi.BookConfig(
        slug="t",
        source_file="t-ohoiko",
        txt_filename="f.txt",
        author="A",
        author_uk="А",
        grade="",
        max_entry_number=10,
    )
    obi.ingest_entries(conn, book, entries)
    conn.commit()
    # Re-run with force
    obi.ingest_entries(conn, book, entries, force=True)
    conn.commit()

    n_chunks = conn.execute(
        "SELECT COUNT(*) FROM textbooks WHERE source_file=?",
        (book.source_file,),
    ).fetchone()[0]
    n_sec = conn.execute(
        "SELECT COUNT(*) FROM textbook_sections WHERE source_file=?",
        (book.source_file,),
    ).fetchone()[0]
    n_orphan = conn.execute(
        "SELECT COUNT(*) FROM textbooks WHERE source_file=? AND parent_section_id IS NULL",
        (book.source_file,),
    ).fetchone()[0]
    assert n_chunks == 2
    assert n_sec == 2
    assert n_orphan == 0
    conn.close()


# ---------------------------------------------------------------------------
# Backfill script tests
# ---------------------------------------------------------------------------


def test_backfill_converts_existing_orphans(tmp_path: Path) -> None:
    """Simulate the pre-fix state: chunks present, no sections, all
    orphans. Run the backfill → 0 orphans, 1:1 sections."""
    from scripts.ingest import backfill_lesson_sections as bf

    db_path = tmp_path / "sources.db"
    conn = _make_full_db(db_path)
    # Pre-fix state: Ohoiko chunks exist but are unlinked
    conn.executemany(
        """INSERT INTO textbooks (chunk_id, title, text, source_file, grade, author, char_count)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                "anna-ohoiko-1000-words-2nd-ed_e0001",
                "а",
                "а — and",
                "anna-ohoiko-1000-words-2nd-ed",
                "",
                "Anna Ohoiko",
                8,
            ),
            (
                "anna-ohoiko-1000-words-2nd-ed_e0002",
                "або́",
                "або — or",
                "anna-ohoiko-1000-words-2nd-ed",
                "",
                "Anna Ohoiko",
                7,
            ),
            (
                "ulp-1-00-lesson-notes_l0001",
                "Lesson 1: Greetings",
                "Hi!",
                "ulp-1-00-lesson-notes",
                "",
                "Ukrainian Lessons Podcast",
                3,
            ),
        ],
    )
    conn.commit()

    # All 3 are orphans
    n_orphan_before = conn.execute("SELECT COUNT(*) FROM textbooks WHERE parent_section_id IS NULL").fetchone()[0]
    assert n_orphan_before == 3

    # Run backfill for the two source_files we know about
    bf.backfill_source_file(conn, "anna-ohoiko-1000-words-2nd-ed", dry_run=False)
    bf.backfill_source_file(conn, "ulp-1-00-lesson-notes", dry_run=False)
    conn.commit()

    n_orphan_after = conn.execute("SELECT COUNT(*) FROM textbooks WHERE parent_section_id IS NULL").fetchone()[0]
    assert n_orphan_after == 0, f"orphans remain: {n_orphan_after}"

    # Verify the section titles use the right format per source
    titles_oh = sorted(
        r[0]
        for r in conn.execute(
            "SELECT section_title FROM textbook_sections WHERE source_file='anna-ohoiko-1000-words-2nd-ed'"
        )
    )
    assert titles_oh == ["Entry 1: а", "Entry 2: або́"]
    titles_ulp = sorted(
        r[0]
        for r in conn.execute("SELECT section_title FROM textbook_sections WHERE source_file='ulp-1-00-lesson-notes'")
    )
    assert titles_ulp == ["Lesson 1: Greetings"]
    conn.close()


def test_backfill_dry_run_makes_no_changes(tmp_path: Path) -> None:
    """``--dry-run`` reports orphans but writes nothing."""
    from scripts.ingest import backfill_lesson_sections as bf

    db_path = tmp_path / "sources.db"
    conn = _make_full_db(db_path)
    conn.execute(
        """INSERT INTO textbooks (chunk_id, title, text, source_file, char_count)
           VALUES ('ulp-1-00-lesson-notes_l0001', 'Lesson 1: X', 'body', 'ulp-1-00-lesson-notes', 4)"""
    )
    conn.commit()

    n_orphan, inserted, linked = bf.backfill_source_file(conn, "ulp-1-00-lesson-notes", dry_run=True)
    assert n_orphan == 1
    assert inserted == 0
    assert linked == 0
    # DB unchanged
    n_sec = conn.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0]
    assert n_sec == 0
    conn.close()


def test_backfill_idempotent(tmp_path: Path) -> None:
    """Running backfill twice must not duplicate sections."""
    from scripts.ingest import backfill_lesson_sections as bf

    db_path = tmp_path / "sources.db"
    conn = _make_full_db(db_path)
    conn.execute(
        """INSERT INTO textbooks (chunk_id, title, text, source_file, char_count)
           VALUES ('anna-ohoiko-1000-words-2nd-ed_e0001', 'а', 'а — and', 'anna-ohoiko-1000-words-2nd-ed', 8)"""
    )
    conn.commit()

    bf.backfill_source_file(conn, "anna-ohoiko-1000-words-2nd-ed", dry_run=False)
    conn.commit()
    bf.backfill_source_file(conn, "anna-ohoiko-1000-words-2nd-ed", dry_run=False)
    conn.commit()

    n_sec = conn.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0]
    n_orphan = conn.execute("SELECT COUNT(*) FROM textbooks WHERE parent_section_id IS NULL").fetchone()[0]
    assert n_sec == 1
    assert n_orphan == 0
    conn.close()
