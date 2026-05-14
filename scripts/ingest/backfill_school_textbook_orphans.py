#!/usr/bin/env python3
"""One-shot backfill: add textbook_sections rows for school-textbook
front-matter chunks that ``extract_sections.py`` left orphaned.

Context
-------

Audit on 2026-05-14 (post PR #1986) found 280 chunks across 30 school
textbooks where ``textbooks.parent_section_id IS NULL``. They are
overwhelmingly the front-matter pages — title page, table of contents,
"how to use this book" — that come BEFORE the first ``§`` or
``Розділ N`` marker in the body. ``scripts/wiki/extract_sections.py``
detects sections by those structural markers; pages without one stay
unsectioned, which makes them invisible to ``_search_sections_fts5`` in
``scripts/wiki/sources_db.py``.

Empirically verified: 280 / 280 orphan chunks have ``title = 'Сторінка N'``
(page title from the chunker), so synthesising a 1:1 page → section
mapping is mechanical:

- For each orphan, create a ``textbook_sections`` row with
  ``section_title = chunk.title`` (e.g. ``Сторінка 3``),
  ``section_number = N`` (parsed from the title or chunk_id suffix),
  ``grade = <grade-from-source_file>`` (1-11; school books use the
  natural grade, NOT the sentinel 0 used for refbooks),
  ``full_text = chunk.text``.
- Link ``textbooks.parent_section_id`` to the new section.

After the backfill, ``_search_sections_fts5`` can return these chunks
as page-grained section hits — particularly relevant for textbook_grounding
gates that cite ``p. N`` of a textbook.

Distinct from ``backfill_lesson_sections.py`` (PR #1982): that script
fixed lesson-style refbook ingests; this one fixes school-textbook
front matter. Different chunk_id suffix shape (``_sNNNN`` vs ``_lNNNN``),
different grade source (parsed from source_file vs sentinel 0),
different title source (chunk's own ``Сторінка N`` title vs synthesised
``Lesson N: …`` / ``Entry N: …``).

Idempotent: ``link_lesson_sections`` uses ``INSERT OR IGNORE`` on the
unique ``(source_file, section_title)`` key. Re-runs are no-ops once
applied.

Usage
-----
    .venv/bin/python -m scripts.ingest.backfill_school_textbook_orphans
    .venv/bin/python -m scripts.ingest.backfill_school_textbook_orphans --dry-run
    .venv/bin/python -m scripts.ingest.backfill_school_textbook_orphans --source-file 4-klas-ukrayinska-mova-zaharijchuk-2021-1

Determinism evidence (BEFORE / AFTER / SAMPLE) prints to stdout per
the 2026-05-14 ingest rule.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path

from scripts.ingest._section_coverage import (
    LessonSection,
    ensure_section_schema,
    link_lesson_sections,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "sources.db"

# School-textbook chunk_id suffix: ``_sNNNN`` (s = section/page).
# We capture the digits to use as a fallback section_number when the
# chunk's ``title`` doesn't parse.
_CHUNK_SUFFIX_RE = re.compile(r"_s(\d+)$")

# Chunk title shape: ``Сторінка N`` (page N) — the chunker's natural
# page title for school-textbook scans.
_PAGE_TITLE_RE = re.compile(r"^Сторінка\s+(\d+)$")

# School-textbook source_file shape: ``<grade>-klas-...`` (Ukrainian
# orthography of "klas" = "клас" = "grade"). Capture the leading
# integer for the section's ``grade`` column.
_SCHOOL_GRADE_RE = re.compile(r"^(\d+)-klas-")


def _section_number_for(chunk_title: str, chunk_id: str) -> str:
    """Derive section_number string.

    Priority:
    1. ``Сторінка N`` extracted from chunk's own title (the canonical
       page number that matches how curriculum references cite the
       textbook).
    2. Numeric suffix from chunk_id (``_sNNNN``) as a defensive fallback
       — chunk_id ordering is monotonic with page order in the chunker.
    3. Empty string if neither parses (shouldn't happen on the current
       data; section_number is TEXT-typed and may be empty).
    """
    title_match = _PAGE_TITLE_RE.match(chunk_title.strip())
    if title_match:
        return title_match.group(1)
    suffix_match = _CHUNK_SUFFIX_RE.search(chunk_id)
    if suffix_match:
        # chunk_id _s0000 → numeric 0; treat as "page 1" for human-
        # friendly numbering by adding 1. Empirically, _s0000 is
        # always the first content page.
        return str(int(suffix_match.group(1)) + 1)
    return ""


def _grade_for(source_file: str) -> int:
    """Extract textbook grade (1-11) from source_file slug.

    ``4-klas-ukrayinska-mova-zaharijchuk-2021-1`` → 4

    Falls back to 0 (the non-school sentinel used by refbook ingesters)
    only if the slug doesn't start with the canonical
    ``<digit>-klas-`` pattern — defensive guard.
    """
    match = _SCHOOL_GRADE_RE.match(source_file)
    if not match:
        return 0
    return int(match.group(1))


def backfill_source_file(
    conn: sqlite3.Connection,
    source_file: str,
    *,
    dry_run: bool,
) -> tuple[int, int, int]:
    """Backfill orphans for a single source_file.

    Returns ``(orphans_found, sections_inserted, chunks_linked)``.
    """
    cur = conn.cursor()
    orphans = cur.execute(
        """SELECT chunk_id, title, text
             FROM textbooks
            WHERE source_file = ? AND parent_section_id IS NULL
            ORDER BY chunk_id""",
        (source_file,),
    ).fetchall()
    n_orphans = len(orphans)
    if n_orphans == 0:
        return 0, 0, 0

    sections: list[LessonSection] = []
    for chunk_id, chunk_title, chunk_text in orphans:
        section_number = _section_number_for(chunk_title or "", chunk_id)
        sections.append(
            LessonSection(
                chunk_id=chunk_id,
                # Use chunk_title verbatim as section_title so MCP
                # section-level queries find it under the same
                # ``Сторінка N`` label the curriculum already cites.
                section_title=chunk_title or chunk_id,
                section_number=section_number,
                full_text=chunk_text or "",
            )
        )

    if dry_run:
        return n_orphans, 0, 0

    inserted, linked = link_lesson_sections(
        conn,
        source_file=source_file,
        sections=sections,
        grade=_grade_for(source_file),
    )
    return n_orphans, inserted, linked


def list_target_sources(conn: sqlite3.Connection) -> list[str]:
    """Enumerate all school-textbook source_files that currently have
    orphan chunks. Determines the work to do dynamically; the script
    has no hard-coded list (unlike backfill_lesson_sections which knew
    its 7 targets ahead of time)."""
    rows = conn.execute(
        """SELECT DISTINCT source_file
             FROM textbooks
            WHERE parent_section_id IS NULL
              AND source_file LIKE '%-klas-%'
            ORDER BY source_file"""
    ).fetchall()
    return [r[0] for r in rows]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill textbook_sections rows for school-textbook front-matter "
            "chunks (those without § / Розділ markers that the chunker left "
            "orphaned)."
        ),
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DB_PATH,
        help="Override target DB path (testing only).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would happen, do not write.",
    )
    parser.add_argument(
        "--source-file",
        action="append",
        default=None,
        help=(
            "Limit backfill to this source_file. Repeat to target several. "
            "Defaults to every school-textbook source_file that currently "
            "has orphan chunks."
        ),
    )
    args = parser.parse_args(argv)

    conn = sqlite3.connect(str(args.db))
    try:
        ensure_section_schema(conn)

        targets = (
            list(args.source_file)
            if args.source_file
            else list_target_sources(conn)
        )
        if not targets:
            print("✅ No orphan school-textbook chunks. Nothing to do.")
            return 0

        # BEFORE evidence
        print(f"🗃️  Target DB: {args.db}")
        total_orphans_before = conn.execute(
            f"""SELECT COUNT(*) FROM textbooks
                 WHERE source_file IN ({",".join("?" * len(targets))})
                   AND parent_section_id IS NULL""",
            targets,
        ).fetchone()[0]
        total_sections_before = conn.execute(
            "SELECT COUNT(*) FROM textbook_sections"
        ).fetchone()[0]
        print(
            f"\nBEFORE: {total_orphans_before:,} orphan chunks across "
            f"{len(targets)} school-textbook source_files; "
            f"total textbook_sections rows: {total_sections_before:,}"
        )

        total_inserted = 0
        total_linked = 0
        for sf in targets:
            n_orphan, inserted, linked = backfill_source_file(
                conn, sf, dry_run=args.dry_run
            )
            grade = _grade_for(sf)
            print(
                f"   {sf} (grade {grade}): "
                f"orphans={n_orphan}, sections inserted={inserted}, "
                f"chunks linked={linked}"
            )
            total_inserted += inserted
            total_linked += linked

        if not args.dry_run:
            conn.commit()

        # AFTER evidence
        total_orphans_after = conn.execute(
            f"""SELECT COUNT(*) FROM textbooks
                 WHERE source_file IN ({",".join("?" * len(targets))})
                   AND parent_section_id IS NULL""",
            targets,
        ).fetchone()[0]
        total_sections_after = conn.execute(
            "SELECT COUNT(*) FROM textbook_sections"
        ).fetchone()[0]
        print(
            f"\nAFTER: {total_orphans_after:,} orphan chunks remain "
            f"across {len(targets)} source_files; "
            f"total textbook_sections rows: {total_sections_after:,} "
            f"(delta +{total_sections_after - total_sections_before})"
        )

        if not args.dry_run and total_inserted > 0:
            print("\n--- SAMPLE backfilled sections (one per source_file) ---")
            for sf in targets[:5]:
                row = conn.execute(
                    """SELECT s.section_id, s.section_title, s.section_number,
                              s.grade, t.chunk_id, t.parent_section_id
                         FROM textbook_sections s
                         JOIN textbooks t ON t.parent_section_id = s.section_id
                        WHERE s.source_file = ?
                        ORDER BY CAST(s.section_number AS INTEGER) LIMIT 1""",
                    (sf,),
                ).fetchone()
                if row:
                    print(
                        f"   {sf}: section_id={row[0]} "
                        f"title={row[1]!r} num={row[2]!r} grade={row[3]} "
                        f"chunk={row[4]} parent={row[5]}"
                    )

        return 0 if total_orphans_after == 0 or args.dry_run else 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
