"""Tests for scripts/ingest/ohoiko_verbs_ingest.py.

Exercises the page-based parser against a synthetic fixture that
mirrors the real *500+ Ukrainian Verbs* layout quirks:

- Verb-page start marker handles both ``\\x0c№N`` (form-feed + no
  space, used for early pages) and ``\\x0c № N`` (form-feed + leading
  space + space) — the latter shape appears around verb #211 due to
  PDF column-alignment artifacts.
- Page furniture (``Back to Contents ...UkrainianLessons.com NNN``,
  running header ``Ukrainian Verb Conjugation Charts``, bare form-feed
  lines) must be stripped from verb bodies.
- The first non-empty body line after the start marker is captured as
  the headword pair (``імперф. | перф.``) and forms the title.
- ``Index of Ukrainian Verbs`` (appendix marker) terminates the last
  verb's body without absorbing the index content.
- Hard cap at ``MAX_VERB_NUMBER = 500`` rejects any marker beyond #500.
- Verified output (chunk_id, title, section_title, char_count) lands
  in textbooks + textbook_sections via the same code path as the live
  ingest. Zero orphans after ingest.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.ingest import ohoiko_verbs_ingest as ovi
from scripts.ingest._section_coverage import ensure_section_schema

FIXTURE_TXT = (
    "Some grammar guide content here.\nMore intro text.\n\n"
    "\x0c№1\n\n"
    "аналізува́ти | проаналізува́ти                                        Present / Future Stems: аналізу- | проаналізу-\n"
    "to analyze                                                                                            Conjugation: 1st (-ють)\n"
    "      ОСОБА                          НЕДОКОНАНИЙ ВИД                                                 ДОКОНАНИЙ ВИД\n"
    " я                   аналізу́ю\n"
    "+ accusative:\n"
    "Експе́рти аналізу́ють ситуа́цію.                                 Experts are analyzing the situation.\n"
    "\n"
    "  Back to Contents              Inspiring resources for learning Ukrainian — UkrainianLessons.com                          57\n"
    "\x0c№2\n\n"
    "атакува́ти | атакува́ти                                                                 Present / Future Stems: атаку- | атаку-\n"
    "to attack, to assault                                                              Two-Aspect Verb, Conjugation: 1st (-ють)\n"
    " я                      атаку́ю\n"
    "+ accusative:\n"
    "Воро́г атаку́є.                                                  The enemy attacks.\n"
    "\n"
    "Back to Contents                     Inspiring resources for learning Ukrainian — UkrainianLessons.com                              267\n"
    "  \x0c № 3\n\n"
    "ї́здити | з’ї́здити, пої́здити                                  Present / Future Stems: їждж-/їзд- | з’їждж-/з’їзд-\n"
    "to go by transport (multidirectional); to travel\n"
    " я                        ї́жджу\n"
    "\n"
    "Index of Ukrainian Verbs\n"
    "аналізувати .......... 56\n"
    "атакувати ............. 57\n"
)


def _write_fixture(tmp_path: Path) -> Path:
    p = tmp_path / "verbs-fixture.txt"
    p.write_text(FIXTURE_TXT, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Parser-level tests
# ---------------------------------------------------------------------------


def test_parse_book_finds_all_verb_pages(tmp_path: Path) -> None:
    verbs = ovi.parse_book(_write_fixture(tmp_path))
    nums = [v.number for v in verbs]
    assert nums == [1, 2, 3], f"expected [1, 2, 3], got {nums}"


def test_parse_book_handles_form_feed_no_space_marker(tmp_path: Path) -> None:
    """Markers like ``\\x0c№1`` (form-feed + no space) must open a
    new verb page."""
    verbs = ovi.parse_book(_write_fixture(tmp_path))
    assert verbs[0].number == 1
    assert "аналізу́ю" in verbs[0].render()


def test_parse_book_handles_space_marker(tmp_path: Path) -> None:
    """Markers like ``\\x0c № 3`` (form-feed + leading space + space)
    must also open a new verb page — this is the shape around verb
    #211 in the real source."""
    verbs = ovi.parse_book(_write_fixture(tmp_path))
    assert verbs[-1].number == 3
    assert "ї́жджу" in verbs[-1].render()


def test_parse_book_strips_page_furniture(tmp_path: Path) -> None:
    """Page footer ``Back to Contents ...UkrainianLessons.com NNN`` must
    NOT appear in any verb body."""
    verbs = ovi.parse_book(_write_fixture(tmp_path))
    for v in verbs:
        body = v.render()
        assert "Back to Contents" not in body
        assert "Inspiring resources for learning Ukrainian" not in body


def test_parse_book_captures_headword_pair_as_title(tmp_path: Path) -> None:
    """Title comes from the first non-empty body line, trimmed at the
    first run of 2+ spaces (which separates the headword pair from the
    stems/conjugation metadata in the PDF column layout)."""
    verbs = ovi.parse_book(_write_fixture(tmp_path))
    assert verbs[0].title == "аналізува́ти | проаналізува́ти"
    assert verbs[1].title == "атакува́ти | атакува́ти"
    assert verbs[2].title.startswith("ї́здити | з’ї́здити")


def test_parse_book_terminates_at_index_marker(tmp_path: Path) -> None:
    """``Index of Ukrainian Verbs`` (appendix start) finalizes the last
    verb and stops accumulation."""
    verbs = ovi.parse_book(_write_fixture(tmp_path))
    last_body = verbs[-1].render()
    assert "Index of Ukrainian Verbs" not in last_body
    assert "аналізувати .......... 56" not in last_body
    # But real content for verb #3 stays:
    assert "ї́жджу" in last_body


def test_parse_book_rejects_marker_beyond_max(tmp_path: Path) -> None:
    """Hard cap: numbers > MAX_VERB_NUMBER are dropped (defensive
    against appendix material that might incidentally carry a №N
    pattern)."""
    fixture = (
        "\x0c№1\n\nаналізува́ти | проаналізува́ти\nto analyze\n\x0c№600\n\nЩось після кінця\nsomething after the end\n"
    )
    p = tmp_path / "f.txt"
    p.write_text(fixture, encoding="utf-8")
    verbs = ovi.parse_book(p)
    nums = [v.number for v in verbs]
    assert nums == [1], f"expected [1], got {nums}"


def test_parse_book_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ovi.parse_book(tmp_path / "does-not-exist.txt")


# ---------------------------------------------------------------------------
# DB round-trip tests
# ---------------------------------------------------------------------------


def _make_full_db(path: Path) -> sqlite3.Connection:
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
            char_count INTEGER DEFAULT 0,
            parent_section_id INTEGER REFERENCES textbook_sections(section_id)
        );
        """
    )
    ensure_section_schema(conn)
    return conn


def test_ingest_verbs_round_trip(tmp_path: Path) -> None:
    """End-to-end: parse → ingest → SELECT confirms rows are written
    with correct metadata and zero orphans."""
    txt = _write_fixture(tmp_path)
    verbs = ovi.parse_book(txt)
    assert len(verbs) == 3

    db_path = tmp_path / "sources.db"
    conn = _make_full_db(db_path)
    inserted, skipped = ovi.ingest_verbs(conn, verbs)
    conn.commit()

    assert inserted == 3
    assert skipped == 0

    rows = list(
        conn.execute(
            """SELECT chunk_id, title, source_file, author, char_count, parent_section_id
                 FROM textbooks WHERE source_file = ? ORDER BY chunk_id""",
            (ovi.SOURCE_FILE,),
        )
    )
    assert len(rows) == 3
    assert rows[0][0] == f"{ovi.SOURCE_FILE}_v0001"
    assert rows[-1][0] == f"{ovi.SOURCE_FILE}_v0003"
    assert all(r[2] == ovi.SOURCE_FILE for r in rows)
    assert all(r[3] == ovi.AUTHOR for r in rows)
    assert all(r[4] > 0 for r in rows)
    # Zero orphans
    assert all(r[5] is not None for r in rows), f"orphans remain: {rows}"

    # Section coverage check
    n_sec = conn.execute(
        "SELECT COUNT(*) FROM textbook_sections WHERE source_file = ?",
        (ovi.SOURCE_FILE,),
    ).fetchone()[0]
    assert n_sec == 3  # 1:1

    # Section title format: ``Verb N: <headword_pair>``
    titles = sorted(
        r[0]
        for r in conn.execute(
            "SELECT section_title FROM textbook_sections WHERE source_file = ?",
            (ovi.SOURCE_FILE,),
        )
    )
    assert titles[0].startswith("Verb 1: ")
    assert "аналізува́ти" in titles[0]
    conn.close()


def test_ingest_verbs_idempotent(tmp_path: Path) -> None:
    """Running the ingest twice on the same source should NOT
    duplicate rows; the second call returns (0 inserted, N skipped)."""
    txt = _write_fixture(tmp_path)
    verbs = ovi.parse_book(txt)

    db_path = tmp_path / "sources.db"
    conn = _make_full_db(db_path)

    first = ovi.ingest_verbs(conn, verbs)
    conn.commit()
    second = ovi.ingest_verbs(conn, verbs)
    conn.commit()
    assert first == (3, 0)
    assert second == (0, 3)
    total = conn.execute(
        "SELECT COUNT(*) FROM textbooks WHERE source_file = ?",
        (ovi.SOURCE_FILE,),
    ).fetchone()[0]
    assert total == 3
    n_sec = conn.execute(
        "SELECT COUNT(*) FROM textbook_sections WHERE source_file = ?",
        (ovi.SOURCE_FILE,),
    ).fetchone()[0]
    assert n_sec == 3
    conn.close()


def test_ingest_verbs_force_overwrites(tmp_path: Path) -> None:
    """With force=True, existing rows AND sections are deleted before
    re-insert."""
    txt = _write_fixture(tmp_path)
    verbs = ovi.parse_book(txt)

    db_path = tmp_path / "sources.db"
    conn = _make_full_db(db_path)
    ovi.ingest_verbs(conn, verbs)
    conn.commit()
    inserted, skipped = ovi.ingest_verbs(conn, verbs, force=True)
    conn.commit()
    assert inserted == 3
    assert skipped == 0
    n_chunks = conn.execute(
        "SELECT COUNT(*) FROM textbooks WHERE source_file = ?",
        (ovi.SOURCE_FILE,),
    ).fetchone()[0]
    n_sec = conn.execute(
        "SELECT COUNT(*) FROM textbook_sections WHERE source_file = ?",
        (ovi.SOURCE_FILE,),
    ).fetchone()[0]
    n_orphan = conn.execute(
        "SELECT COUNT(*) FROM textbooks WHERE source_file = ? AND parent_section_id IS NULL",
        (ovi.SOURCE_FILE,),
    ).fetchone()[0]
    assert n_chunks == 3
    assert n_sec == 3
    assert n_orphan == 0
    conn.close()


# ---------------------------------------------------------------------------
# Furniture-recognizer parametric tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "line,expected",
    [
        # Page footer (the single-line shape that's typical in this book)
        (
            "  Back to Contents              Inspiring resources for learning Ukrainian — UkrainianLessons.com                          57",
            True,
        ),
        (
            "Back to Contents                     Inspiring resources for learning Ukrainian — UkrainianLessons.com                              267",
            True,
        ),
        # Running section header
        ("            Ukrainian Verb Conjugation Charts", True),
        ("Ukrainian Verb Conjugation Charts", True),
        # Bare form-feed
        ("\x0c", True),
        # NOT furniture: regular content
        ("аналізува́ти | проаналізува́ти", False),
        ("+ accusative:", False),
        ("Експе́рти аналізу́ють ситуа́цію.", False),
        # NOT furniture: the verb-start marker itself (handled by parser, not
        # furniture-recognizer)
        ("№1", False),
        ("\x0c№1", False),
        (" № 211", False),
    ],
)
def test_is_furniture(line: str, expected: bool) -> None:
    assert ovi._is_furniture(line) is expected
