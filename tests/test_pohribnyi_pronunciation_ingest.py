"""Tests for scripts/ingest/pohribnyi_pronunciation_ingest.py.

The Pohribnyi 1992 source ships as a 28-page image-based PDF that we
OCR out-of-band into a single .txt with form-feed page separators. The
ingester's parsing surface is intentionally narrow — split on form-feed,
trim leading/trailing blanks, one chunk per page — so the tests focus
on:

- correct page count from a synthetic fixture mirroring the real OCR
  layout (leading form-feed before page 1, form-feeds between pages)
- empty-page handling (a stray form-feed should not introduce a phantom
  chunk)
- trimming behavior on the Page.render output
- round-trip into a minimal sqlite schema with the shared
  ``_section_coverage`` helper attached, so each chunk lands with a
  non-NULL ``parent_section_id`` pointing at a row in
  ``textbook_sections``
- idempotency (re-run = 0 inserted / N skipped)
- ``--force`` resets both textbooks and textbook_sections rows for the
  source_file

The synthetic fixture is short on purpose; the production data lives in
``docs/references/private/pohribnyi-ukrainska-literaturna-vymova-1992.txt``
and is exercised by the live ingest run whose evidence is captured in
the PR description per the determinism rule.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.ingest import pohribnyi_pronunciation_ingest as pohribnyi
from tests.pohribnyi_schema import open_schema_copy

# ---------------------------------------------------------------------------
# Fixtures — a 3-page synthetic fixture mirroring the real OCR layout
# (the real file leads with a form-feed and uses form-feed between pages)
# ---------------------------------------------------------------------------

FIXTURE_3_PAGES = (
    "\f"
    "2\n"
    "\n"
    "УКРАЇНСЬКА\n"
    "ЛІТЕРАТУРНА\n"
    "ВИМОВА\n"
    "\n"
    "МИКОЛА ПОГРІБНИЙ\n"
    "\f"
    "3\n"
    "\n"
    "ПЕРЕДМОВА\n"
    "\n"
    "Навчальний посібник 'Українська літературна вимова'.\n"
    "\f"
    "4\n"
    "\n"
    "ЗНАКИ ФОНЕТИЧНОГО АЛФАВІТУ\n"
    "\n"
    "[й] — голосний звук, проміжний між [е] і [и].\n"
)


# Fixture with a stray empty form-feed between content pages, to verify
# the parser doesn't emit a phantom chunk for the empty page.
FIXTURE_WITH_EMPTY_PAGE = (
    "\f"
    "Page A body.\n"
    "\f"
    "\f"
    "Page B body.\n"
)


def _write_fixture(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Parser-level tests
# ---------------------------------------------------------------------------


def test_parse_book_yields_one_page_per_form_feed(tmp_path: Path) -> None:
    txt = _write_fixture(tmp_path, "ok.txt", FIXTURE_3_PAGES)
    pages = pohribnyi.parse_book(txt)
    assert [p.number for p in pages] == [1, 2, 3]


def test_parse_book_drops_empty_pages(tmp_path: Path) -> None:
    """A stray form-feed with no content between two pages must not
    promote a phantom chunk."""
    txt = _write_fixture(tmp_path, "empty.txt", FIXTURE_WITH_EMPTY_PAGE)
    pages = pohribnyi.parse_book(txt)
    assert [p.number for p in pages] == [1, 2]
    assert "Page A body." in pages[0].render()
    assert "Page B body." in pages[1].render()


def test_parse_book_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        pohribnyi.parse_book(tmp_path / "does-not-exist.txt")


def test_page_render_strips_leading_and_trailing_blanks(tmp_path: Path) -> None:
    txt = _write_fixture(tmp_path, "ok.txt", FIXTURE_3_PAGES)
    pages = pohribnyi.parse_book(txt)
    rendered = pages[1].render()  # page 2 has leading "3\n\n" and content
    assert not rendered.startswith("\n"), "leading blank should be stripped"
    assert rendered.endswith("\n"), "trailing newline retained for delimiter cleanliness"
    # The page-number line ``3`` is OCR content for page 2 — it stays.
    assert rendered.startswith("3\n")


def test_page_render_preserves_internal_blanks(tmp_path: Path) -> None:
    """Blank lines between paragraphs are content structure, not stripped."""
    fixture = "\fParagraph A.\n\nParagraph B.\n"
    txt = _write_fixture(tmp_path, "p.txt", fixture)
    pages = pohribnyi.parse_book(txt)
    rendered = pages[0].render()
    assert "Paragraph A.\n\nParagraph B." in rendered


# ---------------------------------------------------------------------------
# DB round-trip tests
# ---------------------------------------------------------------------------


def _make_textbooks_db(path: Path) -> sqlite3.Connection:
    """Live textbook/section DDL including FTS and its source insert trigger."""
    return open_schema_copy(path)


def test_ingest_pages_round_trip_with_section_coverage(tmp_path: Path) -> None:
    """End-to-end: parse → ingest → verify chunks + sections + linkage."""
    txt = _write_fixture(tmp_path, "ok.txt", FIXTURE_3_PAGES)
    pages = pohribnyi.parse_book(txt)
    assert len(pages) == 3

    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    inserted, skipped = pohribnyi.ingest_pages(conn, pages)
    conn.commit()
    assert inserted == 3
    assert skipped == 0

    chunks = list(
        conn.execute(
            """SELECT chunk_id, title, source_file, author, char_count,
                      parent_section_id
                 FROM textbooks WHERE source_file = ? ORDER BY chunk_id""",
            (pohribnyi.SOURCE_FILE,),
        )
    )
    assert [c[0] for c in chunks] == [
        f"{pohribnyi.SOURCE_FILE}_p01",
        f"{pohribnyi.SOURCE_FILE}_p02",
        f"{pohribnyi.SOURCE_FILE}_p03",
    ]
    assert chunks[0][1] == "Pohribnyi 1992 (Ukrainian Literary Pronunciation), p. 1"
    assert chunks[2][1] == "Pohribnyi 1992 (Ukrainian Literary Pronunciation), p. 3"
    assert all(c[3] == pohribnyi.AUTHOR for c in chunks)
    assert all(c[4] > 0 for c in chunks)
    # CRITICAL: each chunk must be linked to a section row.
    assert all(c[5] is not None for c in chunks), (
        "ingester must populate parent_section_id via _section_coverage "
        "helper — None values mean the section coverage path didn't run"
    )

    sections = list(
        conn.execute(
            """SELECT section_id, source_file, grade, section_title, section_number, chunk_count
                 FROM textbook_sections WHERE source_file = ? ORDER BY section_id""",
            (pohribnyi.SOURCE_FILE,),
        )
    )
    assert len(sections) == 3
    # Sentinel grade=0 for non-school reference material.
    assert all(s[2] == 0 for s in sections)
    assert [s[4] for s in sections] == ["1", "2", "3"]
    assert all(s[5] == 1 for s in sections)  # 1:1 chunk:section mapping

    # Linkage is consistent: every chunk.parent_section_id resolves to a
    # row in textbook_sections.
    section_ids = {s[0] for s in sections}
    assert all(c[5] in section_ids for c in chunks)

    conn.close()


def test_ingest_pages_idempotent(tmp_path: Path) -> None:
    txt = _write_fixture(tmp_path, "ok.txt", FIXTURE_3_PAGES)
    pages = pohribnyi.parse_book(txt)

    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)

    first = pohribnyi.ingest_pages(conn, pages)
    conn.commit()
    second = pohribnyi.ingest_pages(conn, pages)
    conn.commit()
    assert first == (3, 0)
    assert second == (0, 3)

    total = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
    assert total == 3
    sections_total = conn.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0]
    assert sections_total == 3
    conn.close()


def test_ingest_pages_force_overwrites(tmp_path: Path) -> None:
    txt = _write_fixture(tmp_path, "ok.txt", FIXTURE_3_PAGES)
    pages = pohribnyi.parse_book(txt)

    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    pohribnyi.ingest_pages(conn, pages)
    conn.commit()

    inserted, skipped = pohribnyi.ingest_pages(conn, pages, force=True)
    conn.commit()
    assert inserted == 3
    assert skipped == 0

    # No drift in totals.
    total = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
    assert total == 3
    sections_total = conn.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0]
    assert sections_total == 3
    conn.close()


def test_ingest_pages_force_clears_orphan_sections(tmp_path: Path) -> None:
    """``--force`` must delete textbook_sections rows for the source
    BEFORE re-inserting; otherwise the unique (source_file, section_title)
    constraint hits and the helper skips section creation, leaving
    chunks unlinked.

    Regression guard: this is the failure mode #1982 was filed against
    when ingesters wrote chunks but no sections.
    """
    txt = _write_fixture(tmp_path, "ok.txt", FIXTURE_3_PAGES)
    pages = pohribnyi.parse_book(txt)

    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    pohribnyi.ingest_pages(conn, pages)
    conn.commit()
    # Simulate the legacy state: stale sections that pre-date this
    # ingester (the situation #1982 backfilled).
    inserted, _ = pohribnyi.ingest_pages(conn, pages, force=True)
    conn.commit()

    assert inserted == 3
    orphan_chunks = conn.execute(
        "SELECT COUNT(*) FROM textbooks "
        "WHERE source_file = ? AND parent_section_id IS NULL",
        (pohribnyi.SOURCE_FILE,),
    ).fetchone()[0]
    assert orphan_chunks == 0, "force must re-link sections, not leave orphans"
    conn.close()


def _adjudicated_fixture(text="[а]", **metadata):
    return {
        "rows": [
            {
                "page": 1,
                "paragraph": 1,
                "text": text,
                "underlining": [],
                "status": "adjudicated",
                "adjudicated_by": "fixture",
                **metadata,
            }
        ],
        "paragraph_counts": {"1": 1},
    }


def test_adjudicated_ingest_retains_layout_and_print_exceptions(tmp_path):
    from scripts.ingest.pohribnyi_tooling import load_notation

    conn = _make_textbooks_db(tmp_path / "copy.db")
    pohribnyi.ingest_pages(conn, [pohribnyi.Page(number=1, body="synthetic OCR")])
    data = _adjudicated_fixture(
        "[а", printed_anomaly=True, line_breaks=[{"offset": 2, "printed_hyphen": True}], withheld=[]
    )
    assert pohribnyi.ingest_adjudicated(conn, data, load_notation(), census_counts={"1": 1}) == (1, 0)
    assert pohribnyi.ingest_adjudicated(conn, data, load_notation(), census_counts={"1": 1}) == (0, 1)
    stored = conn.execute(
        "SELECT text, line_breaks_json, withheld_json, printed_anomaly FROM textbooks "
        "WHERE transcription_status='adjudicated'"
    ).fetchone()
    assert stored == ("[а", '[{"offset": 2, "printed_hyphen": true}]', "[]", 1)
    conn.close()


def test_adjudicated_ingest_retains_withheld_reason_and_rejects_metadata_conflicts(tmp_path):
    import copy
    import json

    from scripts.ingest.pohribnyi_tooling import load_notation

    conn = _make_textbooks_db(tmp_path / "copy.db")
    pohribnyi.ingest_pages(conn, [pohribnyi.Page(number=1, body="synthetic OCR")])
    data = _adjudicated_fixture("[\ufffc]", withheld=[{"start": 1, "end": 2, "reason": "uncertain"}])
    assert pohribnyi.ingest_adjudicated(conn, data, load_notation(), census_counts={"1": 1}) == (1, 0)
    stored = conn.execute("SELECT withheld_json FROM textbooks WHERE transcription_status='adjudicated'").fetchone()
    assert json.loads(stored[0]) == data["rows"][0]["withheld"]
    for change in (
        {"line_breaks": [{"offset": 2, "printed_hyphen": False}]},
        {"printed_anomaly": True},
        {"withheld": [{"start": 1, "end": 2, "reason": "different reason"}]},
    ):
        altered = copy.deepcopy(data)
        altered["rows"][0].update(change)
        with pytest.raises(ValueError, match="Conflicting"):
            pohribnyi.ingest_adjudicated(conn, altered, load_notation(), census_counts={"1": 1})
    assert conn.execute("SELECT COUNT(*) FROM textbooks WHERE transcription_status='adjudicated'").fetchone()[0] == 1
    conn.close()


def test_adjudicated_ingest_rejects_invalid_layout_before_mutation(tmp_path):
    from scripts.ingest.pohribnyi_tooling import load_notation

    conn = _make_textbooks_db(tmp_path / "copy.db")
    before = conn.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall()
    data = _adjudicated_fixture("[а‐б]", line_breaks=[{"offset": 3, "printed_hyphen": True}])
    with pytest.raises(ValueError, match=r"U\+2010"):
        pohribnyi.ingest_adjudicated(conn, data, load_notation(), census_counts={"1": 1})
    assert conn.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall() == before
    conn.close()


def test_ingest_help_names_the_frozen_default(capsys):
    with pytest.raises(SystemExit) as exc:
        pohribnyi.main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert "bundled frozen table" in help_text
    assert "bundled provisional" not in help_text


def test_metadata_absent_in_legacy_adjudicated_row_remains_idempotent(tmp_path):
    from scripts.ingest.pohribnyi_tooling import load_notation

    conn = _make_textbooks_db(tmp_path / "copy.db")
    pohribnyi.ingest_pages(conn, [pohribnyi.Page(number=1, body="synthetic OCR")])
    data = _adjudicated_fixture()
    table = load_notation()
    assert pohribnyi.ingest_adjudicated(conn, data, table, census_counts={"1": 1}) == (1, 0)
    # Model the NULL values introduced when adding columns to an older clean row.
    conn.execute(
        "UPDATE textbooks SET line_breaks_json=NULL, withheld_json=NULL, printed_anomaly=NULL "
        "WHERE transcription_status='adjudicated'"
    )
    assert pohribnyi.ingest_adjudicated(conn, data, table, census_counts={"1": 1}) == (0, 1)
    conn.close()


def test_adjudicated_packet_adapts_page_format_before_census_checks():
    from scripts.ingest.pohribnyi_tooling import load_notation

    data = {"rows": {"page": 1, "seat": "fixture-seat", "paragraphs": [
        {"n": 1, "text": "[а]", "underlines": [[1, 2]], "line_breaks": [], "withheld": [],
         "status": "adjudicated", "adjudicated_by": "fixture"}
    ]}, "paragraph_counts": {"1": 1}}
    before = data["rows"]["paragraphs"][0].copy()
    rows = pohribnyi.validate_adjudicated_packet(data, load_notation(), census_counts={"1": 1})
    assert rows[0]["page"] == 1 and rows[0]["paragraph"] == 1
    assert rows[0]["underlining"] == [{"start": 1, "end": 2}]
    assert data["rows"]["paragraphs"][0] == before
    with pytest.raises(ValueError, match="independent census"):
        pohribnyi.validate_adjudicated_packet(data, load_notation(), census_counts={"1": 2})
