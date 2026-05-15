"""Tests for scripts/ingest/backfill_school_textbook_orphans.py.

Verifies the front-matter backfill correctly:
- Discovers orphan school-textbook chunks dynamically
- Parses section_number from chunk's ``Сторінка N`` title (canonical)
  with chunk_id-suffix as a defensive fallback
- Extracts the school grade from the source_file slug
- Synthesizes 1:1 chunk→section rows that pass the unique
  ``(source_file, section_title)`` constraint
- Is idempotent (re-run = no new inserts)
- Doesn't touch chunks that already have a parent_section_id
- Doesn't touch refbook (non-school) sources
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from scripts.ingest import backfill_school_textbook_orphans as backfill

# --- Unit-level parsing helpers -------------------------------------------


def test_grade_for_school_slug() -> None:
    assert backfill._grade_for("4-klas-ukrayinska-mova-zaharijchuk-2021-1") == 4
    assert backfill._grade_for("11-klas-istoriya-ukr-gisem-2024") == 11
    assert backfill._grade_for("2-klas-ukrmova-bolshakova-2019-2") == 2


def test_grade_for_non_school_returns_zero() -> None:
    """Refbook ingests (Ohoiko, ULP) don't match the school slug pattern.
    Defensive fallback to 0 (the non-school sentinel)."""
    assert backfill._grade_for("anna-ohoiko-1000-words-2nd-ed") == 0
    assert backfill._grade_for("ulp-1-00-lesson-notes") == 0
    assert backfill._grade_for("pohribnyi-ukrainska-literaturna-vymova-1992") == 0


def test_section_number_from_storinka_title() -> None:
    """Primary path: ``Сторінка N`` extracted from chunk's own title."""
    assert backfill._section_number_for("Сторінка 7", "anything_s0006") == "7"
    assert backfill._section_number_for("  Сторінка 42  ", "x_s0041") == "42"


def test_section_number_falls_back_to_chunk_id_suffix() -> None:
    """Defensive fallback: numeric suffix from chunk_id + 1 (chunk_id
    offsets are 0-indexed)."""
    assert (
        backfill._section_number_for("Untitled", "4-klas-ukrmova_s0042")
        == "43"
    )


def test_section_number_unparseable_returns_empty_string() -> None:
    """Neither title nor chunk_id matched → empty string. The TEXT column
    permits empty values; this is a defensive guard, not expected on
    production data."""
    assert backfill._section_number_for("Untitled", "no-suffix") == ""


# --- DB round-trip --------------------------------------------------------


def _make_textbooks_db(path: Path) -> sqlite3.Connection:
    """Minimal schema mirroring the production textbooks + textbook_sections
    columns the helper writes to. Distinct from the lesson-ingest test
    schema in that we seed pre-existing orphan rows to exercise the
    backfill path."""
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


def _seed_orphan_chunks(
    conn: sqlite3.Connection,
    source_file: str,
    pages: list[tuple[str, str]],  # (chunk_id_suffix, title)
) -> None:
    cur = conn.cursor()
    for suffix, title in pages:
        chunk_id = f"{source_file}_{suffix}"
        cur.execute(
            """INSERT INTO textbooks
                  (chunk_id, title, text, source_file, grade)
               VALUES (?, ?, ?, ?, ?)""",
            (chunk_id, title, f"body of {chunk_id}", source_file, str(0)),
        )
    conn.commit()


def test_backfill_creates_one_section_per_orphan(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    backfill.ensure_section_schema(conn)
    _seed_orphan_chunks(
        conn,
        "4-klas-ukrayinska-mova-zaharijchuk-2021-1",
        [("s0000", "Сторінка 2"), ("s0001", "Сторінка 3"), ("s0002", "Сторінка 4")],
    )

    n_orphan, inserted, linked = backfill.backfill_source_file(
        conn,
        "4-klas-ukrayinska-mova-zaharijchuk-2021-1",
        dry_run=False,
    )
    conn.commit()
    assert (n_orphan, inserted, linked) == (3, 3, 3)

    sections = list(
        conn.execute(
            """SELECT section_id, section_title, section_number, grade
                 FROM textbook_sections
                WHERE source_file = ?
                ORDER BY section_id""",
            ("4-klas-ukrayinska-mova-zaharijchuk-2021-1",),
        )
    )
    assert [s[1] for s in sections] == ["Сторінка 2", "Сторінка 3", "Сторінка 4"]
    assert [s[2] for s in sections] == ["2", "3", "4"]
    # School grade picked up from source_file slug, NOT the non-school sentinel.
    assert all(s[3] == 4 for s in sections)

    # All chunks linked.
    orphan_after = conn.execute(
        "SELECT COUNT(*) FROM textbooks "
        "WHERE source_file = ? AND parent_section_id IS NULL",
        ("4-klas-ukrayinska-mova-zaharijchuk-2021-1",),
    ).fetchone()[0]
    assert orphan_after == 0
    conn.close()


def test_backfill_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    backfill.ensure_section_schema(conn)
    _seed_orphan_chunks(
        conn,
        "5-klas-ukrmova-litvinova-2022",
        [("s0000", "Сторінка 2"), ("s0001", "Сторінка 3")],
    )

    first = backfill.backfill_source_file(
        conn, "5-klas-ukrmova-litvinova-2022", dry_run=False
    )
    conn.commit()
    second = backfill.backfill_source_file(
        conn, "5-klas-ukrmova-litvinova-2022", dry_run=False
    )
    conn.commit()
    # First run inserts 2 sections + links 2 chunks; second finds 0
    # orphans (all already linked) so returns (0, 0, 0).
    assert first == (2, 2, 2)
    assert second == (0, 0, 0)
    assert (
        conn.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0]
        == 2
    )
    conn.close()


def test_backfill_skips_already_linked_chunks(tmp_path: Path) -> None:
    """A textbook source_file may have a mix of orphan + already-sectioned
    chunks (e.g. body pages from extract_sections.py + front-matter
    orphans). The backfill must touch ONLY the orphans."""
    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    backfill.ensure_section_schema(conn)

    # Pre-existing section row + linked chunk (simulates what
    # extract_sections.py produced for the body).
    sf = "6-klas-ukrmova-zabolotnyi-2020"
    conn.execute(
        """INSERT INTO textbook_sections
              (source_file, grade, section_title, section_number,
               page_start, page_end, chunk_count, full_text)
           VALUES (?, ?, ?, ?, NULL, NULL, 1, ?)""",
        (sf, 6, "§ 1. Вступ", "1", "section 1 body"),
    )
    pre_section_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        """INSERT INTO textbooks
              (chunk_id, title, text, source_file, parent_section_id)
           VALUES (?, ?, ?, ?, ?)""",
        (f"{sf}_s0050", "§ 1. Вступ", "body", sf, pre_section_id),
    )

    # Add 2 orphans (front-matter pages).
    _seed_orphan_chunks(
        conn, sf, [("s0000", "Сторінка 2"), ("s0001", "Сторінка 3")]
    )
    conn.commit()

    n_orphan, inserted, linked = backfill.backfill_source_file(
        conn, sf, dry_run=False
    )
    conn.commit()
    assert n_orphan == 2
    assert inserted == 2
    assert linked == 2

    # Pre-existing section count grew by exactly 2.
    sections_after = conn.execute(
        "SELECT COUNT(*) FROM textbook_sections WHERE source_file = ?", (sf,)
    ).fetchone()[0]
    assert sections_after == 3

    # The pre-existing linked chunk is still linked to its ORIGINAL section.
    pre_chunk_parent = conn.execute(
        "SELECT parent_section_id FROM textbooks WHERE chunk_id = ?",
        (f"{sf}_s0050",),
    ).fetchone()[0]
    assert pre_chunk_parent == pre_section_id
    conn.close()


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    backfill.ensure_section_schema(conn)
    _seed_orphan_chunks(
        conn,
        "7-klas-ukrmova-litvinova-2024",
        [("s0000", "Сторінка 2")],
    )

    n_orphan, inserted, linked = backfill.backfill_source_file(
        conn, "7-klas-ukrmova-litvinova-2024", dry_run=True
    )
    assert n_orphan == 1
    assert inserted == 0
    assert linked == 0
    sections = conn.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0]
    assert sections == 0
    # Chunk still orphaned.
    orphan = conn.execute(
        "SELECT parent_section_id FROM textbooks WHERE source_file = ?",
        ("7-klas-ukrmova-litvinova-2024",),
    ).fetchone()[0]
    assert orphan is None
    conn.close()


def test_list_target_sources_returns_only_school_orphans(tmp_path: Path) -> None:
    """Dynamic target discovery must include school textbooks with
    orphans and exclude refbook (non-school) sources."""
    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    backfill.ensure_section_schema(conn)
    # School textbook with orphan
    _seed_orphan_chunks(
        conn, "4-klas-ukrmova-test-2024", [("s0000", "Сторінка 2")]
    )
    # Non-school orphan (refbook) — should NOT appear in the targets
    _seed_orphan_chunks(
        conn, "anna-ohoiko-test-book", [("e0001", "Entry 1: word")]
    )
    # School with NO orphans — should NOT appear
    conn.execute(
        """INSERT INTO textbooks
              (chunk_id, title, text, source_file, parent_section_id)
           VALUES (?, ?, ?, ?, ?)""",
        ("8-klas-clean_s0000", "Сторінка 2", "x", "8-klas-clean", 1),
    )
    conn.commit()
    targets = backfill.list_target_sources(conn)
    assert targets == ["4-klas-ukrmova-test-2024"]
    conn.close()
