#!/usr/bin/env python3
"""Ingest the FULL text of Борис Антоненко-Давидович *«Як ми говоримо»*
into ``data/sources.db`` textbooks table (page-grained).

Context
-------

The project already has 342 structured entries from this book in the
``style_guide`` table (used by ``mcp__sources__search_style_guide`` for
calque / Russianism lookups by headword). Those entries cover the
high-value usage notes but represent only ~50% of the actual book —
foreword, afterword, section preambles, and many discussion paragraphs
that don't fit the "one headword, one warning" entry pattern are
absent. Issue #1663 tracked the completion gap.

Closing the gap by extracting MORE structured entries from the PDF/HTML
turned out to be a real parser engineering problem (the HTML source
only contains 279 entries; the PDF text via the V7
``dictionary_ingest.py`` parser produces 170; neither path improves on
the 342 already present). The book itself has prose sections,
multi-word lemmas, and entry-less commentary that don't reliably fit
the dictionary-row shape.

This ingester takes the simpler-and-more-useful path: drop the FULL
book content into the textbooks table as page-grained chunks (169
chunks, one per page). That makes every word of the book searchable
via ``mcp__sources__search_text`` while the existing 342 ``style_guide``
entries continue to serve ``search_style_guide`` for headword lookups.

Both retrieval surfaces remain in service:
- ``search_style_guide`` — 342 structured entries (existing, untouched)
- ``search_text`` over textbooks — full 169-page book (new)

Schema fit
----------
- 169 chunks (one per page) into ``textbooks``
- 169 sections (1:1 chunk:section) into ``textbook_sections`` via the
  shared ``_section_coverage`` helper (PR #1982 / #1986 pattern)
- ``author = 'Borys Antonenko-Davydovych'``
- ``source_file = 'antonenko-davydovych-yak-my-hovorymo'``
- ``title`` = ``Antonenko-Davydovych «Як ми говоримо», p. N``
- ``text`` = the page body (pdftotext output, untouched)
- ``grade`` = ``''`` (sentinel 0 used by sections)
- ``chunk_id`` = ``{source_file}_p{NNN}``

Idempotent on chunk_id. ``--force`` clears both ``textbooks`` and
``textbook_sections`` rows for the source before re-insert.

Source preparation (one-time, out-of-band)
------------------------------------------
The PDF is text-extractable (mPDF-produced; no OCR needed):

    pdftotext docs/references/private/antonenko-davydovych-yak-my-hovorymo-1991.pdf \\
              docs/references/private/antonenko-davydovych-yak-my-hovorymo-1991.txt

pdftotext emits ``\\f`` form-feed between pages. This ingester splits
on form-feed and assigns each non-empty part a sequential page number.

Usage
-----
    .venv/bin/python -m scripts.ingest.antonenko_full_book_ingest
    .venv/bin/python -m scripts.ingest.antonenko_full_book_ingest --dry-run
    .venv/bin/python -m scripts.ingest.antonenko_full_book_ingest --force
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

from scripts.ingest._section_coverage import (
    LessonSection,
    ensure_section_schema,
    link_lesson_sections,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "sources.db"
REFERENCES_DIR = PROJECT_ROOT / "docs" / "references" / "private"

SOURCE_FILE = "antonenko-davydovych-yak-my-hovorymo"
TXT_FILENAME = "antonenko-davydovych-yak-my-hovorymo-1991.txt"
AUTHOR = "Borys Antonenko-Davydovych"
EXPECTED_PAGES = 169


@dataclass
class Page:
    number: int
    body: str = ""

    def render(self) -> str:
        """Render the page chunk text. Strip leading and trailing blank
        lines; preserve internal blanks (paragraph separators)."""
        lines = self.body.splitlines()
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        return "\n".join(lines) + "\n" if lines else ""


def parse_book(txt_path: Path) -> list[Page]:
    """Split the pdftotext output on form-feed. Each non-empty part is
    a page assigned a sequential 1-based number. Empty leading or
    trailing parts (split artifacts) are dropped.

    Raises FileNotFoundError if ``txt_path`` doesn't exist.
    """
    if not txt_path.exists():
        raise FileNotFoundError(f"Source not found: {txt_path}")

    raw = txt_path.read_text(encoding="utf-8")
    parts = raw.split("\f")
    pages: list[Page] = []
    for body in parts:
        page_number = len(pages) + 1
        page = Page(number=page_number, body=body)
        if not page.render():
            continue  # empty page (e.g. trailing form-feed) — no number assigned
        pages.append(page)
    return pages


def ingest_pages(
    conn: sqlite3.Connection,
    pages: list[Page],
    *,
    force: bool = False,
) -> tuple[int, int]:
    """Insert each page as one row in textbooks + one row in
    textbook_sections (1:1). Returns (inserted, skipped).

    Idempotent on ``chunk_id``. ``force=True`` DELETEs existing rows
    for this source_file (both textbook_sections + textbooks) before
    re-insert.
    """
    ensure_section_schema(conn)

    cur = conn.cursor()
    existing_ids: set[str] = set()
    if force:
        cur.execute(
            "DELETE FROM textbook_sections WHERE source_file = ?",
            (SOURCE_FILE,),
        )
        cur.execute(
            "DELETE FROM textbooks WHERE source_file = ?",
            (SOURCE_FILE,),
        )
    else:
        rows = cur.execute(
            "SELECT chunk_id FROM textbooks WHERE source_file = ?",
            (SOURCE_FILE,),
        ).fetchall()
        existing_ids = {r[0] for r in rows}

    inserted = 0
    skipped = 0
    batch: list[tuple] = []
    new_sections: list[LessonSection] = []
    for page in pages:
        chunk_id = f"{SOURCE_FILE}_p{page.number:03d}"
        if chunk_id in existing_ids:
            skipped += 1
            continue
        text = page.render()
        title = f"Antonenko-Davydovych «Як ми говоримо», p. {page.number}"
        batch.append(
            (chunk_id, title, text, SOURCE_FILE, "", AUTHOR, len(text))
        )
        new_sections.append(
            LessonSection(
                chunk_id=chunk_id,
                section_title=title,
                section_number=str(page.number),
                full_text=text,
            )
        )
        inserted += 1

    if batch:
        cur.executemany(
            """INSERT INTO textbooks
                  (chunk_id, title, text, source_file, grade, author, char_count)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            batch,
        )
        link_lesson_sections(
            conn,
            source_file=SOURCE_FILE,
            sections=new_sections,
        )

    return inserted, skipped


def _run(*, db_path: Path, dry_run: bool, force: bool) -> int:
    txt_path = REFERENCES_DIR / TXT_FILENAME
    if not txt_path.exists():
        print(
            f"❌ Source file not found: {txt_path}\n"
            "   Generate via:\n"
            "   pdftotext docs/references/private/"
            "antonenko-davydovych-yak-my-hovorymo-1991.pdf {txt_path}",
            file=sys.stderr,
        )
        return 2

    print(f"\n📚 Parsing {TXT_FILENAME}")
    pages = parse_book(txt_path)
    print(f"   parsed pages: {len(pages)} (expected: {EXPECTED_PAGES})")
    if pages:
        body_chars = sum(len(p.render()) for p in pages)
        print(f"   page range: {pages[0].number}..{pages[-1].number}")
        print(f"   total body chars: {body_chars:,}")
    if len(pages) != EXPECTED_PAGES:
        print(
            f"   ⚠️  parsed page count {len(pages)} differs from expected "
            f"{EXPECTED_PAGES} — inspect before proceeding.",
            file=sys.stderr,
        )

    if dry_run:
        print("\n--- DRY-RUN sample (first / middle / last page) ---")
        if not pages:
            print("   (no pages parsed)")
            return 0
        samples = [pages[0], pages[len(pages) // 2], pages[-1]]
        for sample in samples:
            print(f"\n### page #{sample.number} ###")
            text = sample.render()
            print(text[:400] + ("…" if len(text) > 400 else ""))
        return 0

    print(f"\n🗃️  Writing to {db_path}")
    conn = sqlite3.connect(str(db_path))
    try:
        before = conn.execute(
            "SELECT COUNT(*) FROM textbooks WHERE source_file = ?",
            (SOURCE_FILE,),
        ).fetchone()[0]
        total_before = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
        sections_before = conn.execute(
            "SELECT COUNT(*) FROM textbook_sections WHERE source_file = ?",
            (SOURCE_FILE,),
        ).fetchone()[0]
        print(
            f"   BEFORE: {before} chunks for {SOURCE_FILE!r} "
            f"({sections_before} sections; textbooks total: {total_before:,})"
        )

        inserted, skipped = ingest_pages(conn, pages, force=force)
        conn.commit()

        after = conn.execute(
            "SELECT COUNT(*) FROM textbooks WHERE source_file = ?",
            (SOURCE_FILE,),
        ).fetchone()[0]
        total_after = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
        sections_after = conn.execute(
            "SELECT COUNT(*) FROM textbook_sections WHERE source_file = ?",
            (SOURCE_FILE,),
        ).fetchone()[0]
        orphans = conn.execute(
            "SELECT COUNT(*) FROM textbooks "
            "WHERE source_file = ? AND parent_section_id IS NULL",
            (SOURCE_FILE,),
        ).fetchone()[0]

        print(f"   inserted: {inserted}, skipped: {skipped}")
        print(
            f"   AFTER: {after} chunks for {SOURCE_FILE!r} "
            f"({sections_after} sections; textbooks total: {total_after:,}, "
            f"delta +{total_after - total_before})"
        )
        print(f"   section-orphan chunks for {SOURCE_FILE!r}: {orphans} (expected 0)")

        sample = conn.execute(
            """SELECT chunk_id, title, char_count, substr(text, 1, 80) AS snippet
                 FROM textbooks WHERE source_file = ? ORDER BY chunk_id LIMIT 3""",
            (SOURCE_FILE,),
        ).fetchall()
        print("\n--- AFTER sample rows ---")
        for row in sample:
            print(f"  chunk_id={row[0]}")
            print(f"    title={row[1]!r}")
            print(f"    char_count={row[2]}")
            print(f"    snippet={row[3]!r}")
    finally:
        conn.close()

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest the full text of Антоненко-Давидович «Як ми говоримо» "
            "(169 pages → 169 chunks → 169 sections). Complements the existing "
            "342 structured style_guide entries."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse + report, do not write to DB.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-insert: DELETE existing rows for this source_file before INSERT.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DB_PATH,
        help="Override target DB path (testing only).",
    )
    args = parser.parse_args(argv)
    return _run(db_path=args.db, dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
