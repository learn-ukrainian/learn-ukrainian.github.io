#!/usr/bin/env python3
"""Ingest Mykola Pohribnyi *"Українська літературна вимова"* (1992) into
``data/sources.db`` textbooks table.

The book is a 28-page Ukrainian-pronunciation textbook authored by
Микола Іванович Погрібний (lexicographer of «Словника наголосів» and
«Орфоепічного словника») and published 1992 in Dnipropetrovsk by the
"TRANSFORM" Agency, distributed as a printed booklet alongside a set
of LPs / audio cassettes. Topics: phonetic transcription, vowel and
consonant pronunciation norms, common assimilation rules, and the
pronunciation of select grammatical forms.

Source: 51 MB image-based PDF (CorelDRAW 11.0, 28 pages, A5 format)
laid out as scanned plates with no embedded text. OCR is performed
out-of-band with Tesseract 5 + ``-l ukr`` on 300 dpi PNGs derived via
``pdftoppm``; the concatenated OCR output ships alongside the PDF as
``pohribnyi-ukrainska-literaturna-vymova-1992.txt`` in
``docs/references/private/`` (gitignored).

Schema fit:
- One row per page (28 chunks total). The book is short and structurally
  cohesive enough that page-grained chunks are the natural retrieval
  unit. Per-headword chunking would require entry-boundary detection
  inside dense paragraph prose where OCR is imperfect; that work is
  filed for a follow-up.
- ``author = 'Mykola Pohribnyi'``
- ``source_file = 'pohribnyi-ukrainska-literaturna-vymova-1992'``
- ``title`` = ``Pohribnyi 1992 (Ukrainian Literary Pronunciation), p. N``
- ``text`` = the page body (OCR output, untouched)
- ``grade`` = ``''`` (CEFR mapping is downstream; sections use sentinel 0)
- ``chunk_id`` = ``{source_file}_p{NN}`` (``p`` for page)

Section coverage: writes ``textbook_sections`` rows natively via the
shared ``_section_coverage`` helper so the chunks are visible to
section-level retrieval (``_search_sections_fts5``). Mirrors the pattern
established in PR #1982 (Ohoiko + ULP).

Idempotent: each page's chunk_id is checked against the DB and skipped
when present. Re-running on an unchanged source produces zero new
inserts; use ``--force`` to delete existing rows for the source_file
(both ``textbooks`` and ``textbook_sections``) before re-insert.

Deterministic verification: prints BEFORE / AFTER row counts and three
sample rows per call. Mirrors the evidence convention required by the
2026-05-14 determinism rule (see
``docs/best-practices/deterministic-over-hallucination.md``).

Usage:
    .venv/bin/python -m scripts.ingest.pohribnyi_pronunciation_ingest
    .venv/bin/python -m scripts.ingest.pohribnyi_pronunciation_ingest --dry-run
    .venv/bin/python -m scripts.ingest.pohribnyi_pronunciation_ingest --force

Source file (gitignored, in ``docs/references/private/``):
    ``pohribnyi-ukrainska-literaturna-vymova-1992.txt`` (OCR output)
    ``pohribnyi-ukrainska-literaturna-vymova-1992.pdf`` (original 28 pp.)

Re-OCR (only if source PDF replaced or OCR output lost):
    mkdir -p /tmp/pohribnyi-ocr && cd /tmp/pohribnyi-ocr
    pdftoppm -r 300 -png docs/references/private/pohribnyi-*.pdf page
    ls page-*.png | xargs -n1 -P4 -I{} sh -c \\
        'tesseract "$1" "${1%.png}" -l ukr 2>/dev/null' _ {}
    : > all.txt
    for i in $(seq -w 1 28); do printf '\\f' >> all.txt; cat page-$i.txt >> all.txt; done
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

SOURCE_FILE = "pohribnyi-ukrainska-literaturna-vymova-1992"
TXT_FILENAME = "pohribnyi-ukrainska-literaturna-vymova-1992.txt"
AUTHOR = "Mykola Pohribnyi"
# Canonical Cyrillic author; populates textbooks.author_uk so the
# Cyrillic-native matcher resolves citations.
AUTHOR_UK = "Микола Погрібний"
EXPECTED_PAGES = 28  # Verified against pdfinfo of the 1992 booklet.


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Page:
    number: int
    body: str = ""

    def render(self) -> str:
        """Render the page chunk text. The OCR output already contains
        the page number as its first line plus the body; we trim a
        leading run of blank lines and a trailing run of blank lines but
        preserve internal blank lines (they separate paragraphs)."""
        lines = self.body.splitlines()
        # Strip leading blanks
        while lines and not lines[0].strip():
            lines.pop(0)
        # Strip trailing blanks
        while lines and not lines[-1].strip():
            lines.pop()
        return "\n".join(lines) + "\n" if lines else ""


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def parse_book(txt_path: Path) -> list[Page]:
    """Split the concatenated OCR output into one Page per form-feed.

    Convention: the OCR pipeline prepends ``\\f`` (form-feed) before each
    page-N body. After splitting on form-feed, position 0 is empty (the
    file starts with ``\\f``), positions 1..N are page bodies.

    Empty pages (after trimming) are dropped from the result; a parsed
    page list shorter than EXPECTED_PAGES is permitted but should be
    flagged by the caller.
    """
    if not txt_path.exists():
        raise FileNotFoundError(f"Source not found: {txt_path}")

    raw = txt_path.read_text(encoding="utf-8")
    parts = raw.split("\f")
    pages: list[Page] = []
    for idx, body in enumerate(parts):
        if idx == 0 and not body.strip():
            # Leading split-artifact: the file starts with \f.
            continue
        page_number = len(pages) + 1
        page = Page(number=page_number, body=body)
        if not page.render():
            # Empty page (form-feed with no content). Don't number it.
            continue
        pages.append(page)
    return pages


# ---------------------------------------------------------------------------
# DB ingest
# ---------------------------------------------------------------------------


def ingest_pages(
    conn: sqlite3.Connection,
    pages: list[Page],
    *,
    force: bool = False,
) -> tuple[int, int]:
    """Insert each page as one row in textbooks + one row in
    textbook_sections (1:1 chunk:section mapping). Returns
    ``(inserted, skipped)``.

    Idempotent on ``chunk_id``. ``force=True`` DELETEs existing rows
    for this source_file (both textbook_sections + textbooks) before
    re-insert so re-runs are deterministic.
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
        chunk_id = f"{SOURCE_FILE}_p{page.number:02d}"
        if chunk_id in existing_ids:
            skipped += 1
            continue
        text = page.render()
        title = f"Pohribnyi 1992 (Ukrainian Literary Pronunciation), p. {page.number}"
        batch.append(
            (
                chunk_id,
                title,
                text,
                SOURCE_FILE,
                "",  # grade (TEXT-typed on textbooks; sections use sentinel 0)
                AUTHOR,
                AUTHOR_UK,
                len(text),
            )
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
                  (chunk_id, title, text, source_file, grade, author,
                   author_uk, char_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            batch,
        )
        link_lesson_sections(
            conn,
            source_file=SOURCE_FILE,
            sections=new_sections,
        )

    return inserted, skipped


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _run(*, db_path: Path, dry_run: bool, force: bool) -> int:
    txt_path = REFERENCES_DIR / TXT_FILENAME
    if not txt_path.exists():
        print(
            f"❌ Source file not found: {txt_path}\n"
            "   Run the OCR pipeline (see module docstring) and place the\n"
            "   concatenated output as the filename above before re-running.",
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
            f"{EXPECTED_PAGES} — likely an OCR artifact (empty page or "
            f"form-feed missing). Inspect before proceeding.",
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
            "SELECT COUNT(*) FROM textbooks WHERE source_file = ? AND parent_section_id IS NULL",
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
            "Ingest Mykola Pohribnyi 1992 'Ukrainian Literary Pronunciation' "
            "into data/sources.db (28 pages → 28 chunks → 28 sections)."
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
