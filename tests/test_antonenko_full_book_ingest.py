"""Tests for scripts/ingest/antonenko_full_book_ingest.py.

Mirrors the test shape of test_pohribnyi_pronunciation_ingest.py — the
two ingesters share the page-grained pdftotext-output pattern and the
``_section_coverage`` linkage. These tests exercise the form-feed split
on a synthetic fixture, the round-trip with section coverage, idempotency,
and the ``--force`` deletion path.

The full Antonenko book is exercised in the live ingest run captured in
the PR body per the determinism rule.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.ingest import antonenko_full_book_ingest as antonenko

# pdftotext emits page content directly followed by ``\f`` between pages,
# with a single trailing ``\f`` after the last page. The fixture mirrors
# that real-world shape, NOT the Pohribnyi shape (which had a leading
# form-feed because we generated it manually with a different pipeline).
FIXTURE_3_PAGES = (
    "Як ми говоримо\n"
    "Борис Антоненко-Давидович\n"
    "ПЕРЕДНЄ СЛОВО\n"
    "\f"
    'Мова – така ж давня, як і свідомість.\n'
    "\n"
    'Це окремий абзац.\n'
    "\f"
    "ІМЕННИКИ\n"
    "Називний відмінок у складеному присудку\n"
    "\f"
)


FIXTURE_WITH_EMPTY_PAGE = (
    "Page A body.\n"
    "\f"
    "\f"
    "Page B body.\n"
    "\f"
)


def _write_fixture(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


# --- Parser ---------------------------------------------------------------


def test_parse_book_assigns_sequential_page_numbers(tmp_path: Path) -> None:
    txt = _write_fixture(tmp_path, "ok.txt", FIXTURE_3_PAGES)
    pages = antonenko.parse_book(txt)
    assert [p.number for p in pages] == [1, 2, 3]


def test_parse_book_drops_empty_pages(tmp_path: Path) -> None:
    """An empty form-feed segment (e.g. trailing \\f or stray double \\f)
    must not produce a phantom chunk."""
    txt = _write_fixture(tmp_path, "empty.txt", FIXTURE_WITH_EMPTY_PAGE)
    pages = antonenko.parse_book(txt)
    assert [p.number for p in pages] == [1, 2]
    assert "Page A body." in pages[0].render()
    assert "Page B body." in pages[1].render()


def test_parse_book_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        antonenko.parse_book(tmp_path / "missing.txt")


def test_page_render_strips_leading_and_trailing_blanks(tmp_path: Path) -> None:
    """A page that's all blanks renders as empty string; non-blank pages
    drop their leading/trailing blank lines while keeping content."""
    fixture = "\n\n  Real content.  \n\n"
    txt = _write_fixture(tmp_path, "p.txt", fixture)
    pages = antonenko.parse_book(txt)
    assert len(pages) == 1
    rendered = pages[0].render()
    assert rendered.startswith("  Real content."), rendered
    assert rendered.endswith("\n")


def test_page_render_preserves_internal_blanks(tmp_path: Path) -> None:
    fixture = "Paragraph A.\n\nParagraph B.\n"
    txt = _write_fixture(tmp_path, "p.txt", fixture)
    pages = antonenko.parse_book(txt)
    assert "Paragraph A.\n\nParagraph B." in pages[0].render()


# --- DB round trip --------------------------------------------------------


def _make_textbooks_db(path: Path) -> sqlite3.Connection:
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
            author_uk TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0
        );
        """
    )
    return conn


def test_ingest_pages_round_trip_with_section_coverage(tmp_path: Path) -> None:
    txt = _write_fixture(tmp_path, "ok.txt", FIXTURE_3_PAGES)
    pages = antonenko.parse_book(txt)
    assert len(pages) == 3

    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    inserted, skipped = antonenko.ingest_pages(conn, pages)
    conn.commit()
    assert inserted == 3
    assert skipped == 0

    chunks = list(
        conn.execute(
            """SELECT chunk_id, title, source_file, author, char_count,
                      parent_section_id
                 FROM textbooks WHERE source_file = ? ORDER BY chunk_id""",
            (antonenko.SOURCE_FILE,),
        )
    )
    assert [c[0] for c in chunks] == [
        f"{antonenko.SOURCE_FILE}_p001",
        f"{antonenko.SOURCE_FILE}_p002",
        f"{antonenko.SOURCE_FILE}_p003",
    ]
    assert chunks[0][1] == "Antonenko-Davydovych «Як ми говоримо», p. 1"
    assert chunks[2][1] == "Antonenko-Davydovych «Як ми говоримо», p. 3"
    assert all(c[3] == antonenko.AUTHOR for c in chunks)
    assert all(c[4] > 0 for c in chunks)
    # CRITICAL: every chunk must be linked to a section row.
    assert all(c[5] is not None for c in chunks)

    sections = list(
        conn.execute(
            """SELECT section_id, grade, section_title, section_number, chunk_count
                 FROM textbook_sections WHERE source_file = ? ORDER BY section_id""",
            (antonenko.SOURCE_FILE,),
        )
    )
    assert len(sections) == 3
    assert all(s[1] == 0 for s in sections)  # non-school sentinel grade
    assert [s[3] for s in sections] == ["1", "2", "3"]
    assert all(s[4] == 1 for s in sections)

    section_ids = {s[0] for s in sections}
    assert all(c[5] in section_ids for c in chunks)
    conn.close()


def test_ingest_pages_uses_three_digit_page_number(tmp_path: Path) -> None:
    """169 pages — the chunk_id padding must be 3 digits so chunks sort
    correctly. Regression check: 2-digit padding would produce
    ``_p10`` < ``_p2`` under string sort."""
    # Synthesize 12 pages so the padding-needs gap is exercised.
    fixture = "\f".join(f"Body of page {i}\n" for i in range(1, 13)) + "\f"
    txt = _write_fixture(tmp_path, "many.txt", fixture)
    pages = antonenko.parse_book(txt)
    assert len(pages) == 12

    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    antonenko.ingest_pages(conn, pages)
    conn.commit()
    chunk_ids = [
        r[0]
        for r in conn.execute(
            "SELECT chunk_id FROM textbooks WHERE source_file = ? ORDER BY chunk_id",
            (antonenko.SOURCE_FILE,),
        )
    ]
    # Sorted string order matches numeric page order — three-digit padding works.
    assert chunk_ids == [
        f"{antonenko.SOURCE_FILE}_p{i:03d}" for i in range(1, 13)
    ]
    conn.close()


def test_ingest_pages_idempotent(tmp_path: Path) -> None:
    txt = _write_fixture(tmp_path, "ok.txt", FIXTURE_3_PAGES)
    pages = antonenko.parse_book(txt)

    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    first = antonenko.ingest_pages(conn, pages)
    conn.commit()
    second = antonenko.ingest_pages(conn, pages)
    conn.commit()
    assert first == (3, 0)
    assert second == (0, 3)
    assert conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0] == 3
    assert conn.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0] == 3
    conn.close()


def test_ingest_pages_force_clears_orphan_sections(tmp_path: Path) -> None:
    """``--force`` must DELETE existing textbook_sections rows for the
    source before re-inserting. Without that step, the unique
    (source_file, section_title) constraint hits, the helper silently
    skips section creation, and chunks land orphaned. Regression guard
    against the failure mode #1982 was filed for."""
    txt = _write_fixture(tmp_path, "ok.txt", FIXTURE_3_PAGES)
    pages = antonenko.parse_book(txt)

    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    antonenko.ingest_pages(conn, pages)
    conn.commit()
    inserted, _ = antonenko.ingest_pages(conn, pages, force=True)
    conn.commit()
    assert inserted == 3
    orphan = conn.execute(
        "SELECT COUNT(*) FROM textbooks "
        "WHERE source_file = ? AND parent_section_id IS NULL",
        (antonenko.SOURCE_FILE,),
    ).fetchone()[0]
    assert orphan == 0
    conn.close()
