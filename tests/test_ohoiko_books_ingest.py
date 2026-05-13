"""Tests for scripts/ingest/ohoiko_books_ingest.py.

Exercises the parser against a synthetic fixture that mirrors the
real Ohoiko book quirks identified during the 2026-05-14 ingest run:

- ``How to Use Anki`` numbered-instruction section (English-headed
  ``N.`` markers) must be filtered out.
- Hard cap at ``max_entry_number`` keeps crossword puzzle clues and
  blank-journal slots (1001+) out of the corpus.
- Monotonicity guard drops any backwards-jumping number that survives
  the cap.
- ``Кросворд`` / ``Find out more at`` section terminators stop body
  accumulation so the LAST real entry's body doesn't absorb back-matter.
- Verified output (chunk_id, title, char_count) lands in the textbooks
  table via the same code path as the live ingest.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.ingest import ohoiko_books_ingest as obi

FIXTURE_TXT = """Welcome page

How to Use Anki

1. Open Anki and create a new deck.
2. Anki uses a spaced repetition algorithm to show you cards.
3. Make sure to use the audio.

Most Useful Ukrainian Words

1.    а                                               and, but
      (contrast between sentences)
      Я люблю́ готува́ти, а ти?                       I like to cook, and you (informal)?
2.    або́ = чи                                       or
      За́раз або́ ніко́ли.                            Now or never.
3.    авто́бус                                        bus
      Сашко́ ї́здить в шко́лу                         Sashko goes to school
      авто́бусом.                                     by bus.



                 Inspiring resources for learning Ukrainian — UkrainianLessons.com         12
                                                                                            але́




4.    але́                                            but (contrast)
      Я хочу́, але́ не мо́жу.                         I want to, but I cannot.
5.    якщо́                                          if
      Якщо́ ти го́лодний, їж.                         If you're hungry, eat.
Кросворд №1
1. бана́н
2. ві́кно
3. сонце
"""


def _write_fixture(tmp_path: Path) -> Path:
    p = tmp_path / "fixture.txt"
    p.write_text(FIXTURE_TXT, encoding="utf-8")
    return p


def test_parse_book_filters_english_instruction_steps(tmp_path: Path) -> None:
    """The Anki instructions (English-headed) must NOT enter the entry list."""
    entries = obi.parse_book(_write_fixture(tmp_path), max_entry_number=10)
    headwords = [e.headword for e in entries]
    # Only Cyrillic headwords land in the result.
    for h in headwords:
        assert obi._is_cyrillic_headword(h), (
            f"non-Cyrillic headword leaked through: {h!r}"
        )
    # First real entry is 'а', not 'Open Anki and create a new deck.'
    assert entries[0].headword == "а"


def test_parse_book_caps_at_max_entry_number(tmp_path: Path) -> None:
    """Entries with num > max_entry_number must be dropped."""
    # Cap at 5: real entries are #1-#5 in the fixture; crossword answers
    # (also #1, #2, #3) must NOT land because they're below cap but
    # monotonicity guards them, AND they sit behind the Кросворд marker.
    entries = obi.parse_book(_write_fixture(tmp_path), max_entry_number=5)
    nums = [e.number for e in entries]
    assert nums == [1, 2, 3, 4, 5], f"expected #1..#5, got {nums}"


def test_parse_book_drops_monotonicity_violations(tmp_path: Path) -> None:
    """A backwards number jump (crossword answer reset) must be dropped."""
    # With max=20 (above all fixture numbers), the crossword "1./2./3."
    # answers would otherwise be captured. The monotonicity guard
    # rejects them because they restart numbering after entry #5.
    entries = obi.parse_book(_write_fixture(tmp_path), max_entry_number=20)
    nums = [e.number for e in entries]
    assert nums == [1, 2, 3, 4, 5], f"expected #1..#5, got {nums}"


def test_parse_book_section_terminator_stops_body(tmp_path: Path) -> None:
    """``Кросворд`` inside an entry body finalizes the entry without
    absorbing the marker line into its text."""
    entries = obi.parse_book(_write_fixture(tmp_path), max_entry_number=10)
    last = entries[-1]
    assert last.number == 5
    assert last.headword == "якщо́"
    body_blob = last.full_text()
    # The "Кросворд №1" header must not appear in the last entry's body
    # and neither must any crossword answer.
    assert "Кросворд" not in body_blob
    assert "бана́н" not in body_blob
    assert "сонце" not in body_blob
    # But the entry's real example sentence stays.
    assert "Якщо́ ти го́лодний" in body_blob


def test_parse_book_full_text_renders_clean_header(tmp_path: Path) -> None:
    """full_text() yields ``<headword>  —  <english>`` followed by examples."""
    entries = obi.parse_book(_write_fixture(tmp_path), max_entry_number=10)
    a = entries[0]
    blob = a.full_text()
    assert blob.startswith("а  —  and, but\n"), blob[:40]
    assert "Я люблю́ готува́ти" in blob


def _make_textbooks_db(path: Path) -> sqlite3.Connection:
    """Minimal textbooks schema for round-trip tests (no FTS triggers
    needed — we exercise the INSERT layer, not retrieval)."""
    conn = sqlite3.connect(str(path))
    conn.executescript(
        """
        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            grade TEXT DEFAULT '',
            author TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0
        );
        """
    )
    return conn


def test_ingest_entries_round_trip(tmp_path: Path) -> None:
    """End-to-end: parse → ingest → SELECT confirms rows are written
    with correct metadata."""
    txt = _write_fixture(tmp_path)
    entries = obi.parse_book(txt, max_entry_number=10)
    assert len(entries) == 5

    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    book = obi.BookConfig(
        slug="test-fixture",
        source_file="test-fixture-source",
        txt_filename="fixture.txt",
        author="Anna Ohoiko",
        grade="",
        max_entry_number=10,
    )
    inserted, skipped = obi.ingest_entries(conn, book, entries)
    conn.commit()
    assert inserted == 5
    assert skipped == 0

    rows = list(conn.execute(
        """SELECT chunk_id, title, source_file, author, char_count
             FROM textbooks WHERE source_file = ? ORDER BY chunk_id""",
        (book.source_file,),
    ))
    assert len(rows) == 5
    # chunk_id format: <source_file>_e<NNNN>
    assert rows[0][0] == "test-fixture-source_e0001"
    assert rows[-1][0] == "test-fixture-source_e0005"
    assert rows[0][1] == "а"
    assert all(r[2] == "test-fixture-source" for r in rows)
    assert all(r[3] == "Anna Ohoiko" for r in rows)
    assert all(r[4] > 0 for r in rows)
    conn.close()


def test_ingest_entries_idempotent(tmp_path: Path) -> None:
    """Running the ingest twice on the same source should NOT duplicate
    rows; the second call returns (0 inserted, N skipped)."""
    txt = _write_fixture(tmp_path)
    entries = obi.parse_book(txt, max_entry_number=10)

    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    book = obi.BookConfig(
        slug="t",
        source_file="t",
        txt_filename="fixture.txt",
        author="A",
        grade="",
        max_entry_number=10,
    )

    first = obi.ingest_entries(conn, book, entries)
    conn.commit()
    second = obi.ingest_entries(conn, book, entries)
    conn.commit()
    assert first == (5, 0)
    assert second == (0, 5)
    total = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
    assert total == 5
    conn.close()


def test_ingest_entries_force_overwrites(tmp_path: Path) -> None:
    """With force=True, existing rows are deleted before re-insert."""
    txt = _write_fixture(tmp_path)
    entries = obi.parse_book(txt, max_entry_number=10)

    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    book = obi.BookConfig(
        slug="t",
        source_file="t",
        txt_filename="fixture.txt",
        author="A",
        grade="",
        max_entry_number=10,
    )
    obi.ingest_entries(conn, book, entries)
    conn.commit()
    inserted, skipped = obi.ingest_entries(conn, book, entries, force=True)
    conn.commit()
    assert inserted == 5
    assert skipped == 0
    total = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
    assert total == 5
    conn.close()


@pytest.mark.parametrize(
    "headword,expected",
    [
        ("а", True),
        ("або́ = чи", True),
        ("'а́", True),
        ("Open Anki and create a new deck.", False),
        ("Anki uses a spaced repetition algorithm", False),
        ("", False),
        ("   ", False),
    ],
)
def test_is_cyrillic_headword(headword: str, expected: bool) -> None:
    assert obi._is_cyrillic_headword(headword) is expected
