#!/usr/bin/env python3
"""One-shot backfill: add textbook_sections rows for orphaned chunks.

Context: audit on 2026-05-14 (after PR #1981 merged) found 1,240
fully-orphaned chunks across 7 source_files:

    anna-ohoiko-1000-words-2nd-ed: 1000 chunks
    ulp-1-00-lesson-notes:          40 chunks
    ulp-2-00-lesson-notes:          40 chunks
    ulp-3-00-lesson-notes:          40 chunks
    ulp-4-00-lesson-notes:          40 chunks
    ulp-5-00-lesson-notes:          40 chunks
    ulp-6-00-lesson-notes:          40 chunks

All seven are reference-material ingests (Anna Ohoiko's word list +
Ukrainian Lessons Podcast lesson notes) whose original ingesters wrote
to ``textbooks`` only — never to ``textbook_sections``. Without sections,
``_search_sections_fts5`` in scripts/wiki/sources_db.py skips these
chunks entirely (it filters ``parent_section_id IS NOT NULL``).

This script reads each orphaned chunk and synthesises a 1:1 section
row, then links ``textbooks.parent_section_id``. Section title is
reconstructed from the existing chunk's ``title`` column. Section
number is derived from the chunk_id suffix (``_e0001`` → ``1`` for
Ohoiko, ``_l0001`` → ``1`` for ULP).

After both ingesters have been updated (same PR) to write sections
natively, this backfill is a one-shot remediation. Re-running is
idempotent (the helper uses ``INSERT OR IGNORE`` on the unique
(source_file, section_title) key).

Usage:
    .venv/bin/python -m scripts.ingest.backfill_lesson_sections
    .venv/bin/python -m scripts.ingest.backfill_lesson_sections --dry-run

Determinism evidence (BEFORE / AFTER / SAMPLE) printed to stdout per
the 2026-05-14 ingest rule. The orchestrator captures this in the PR
body.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path

from scripts.ingest._section_coverage import (
    LessonSection,
    ensure_section_schema,
    link_lesson_sections,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "sources.db"

# Source_files we expect to backfill, with how to derive section_number
# from the chunk_id suffix. The suffix format is the chunk_id's tail
# after the last ``_`` (e.g. ``e0001`` or ``l0042``); we strip the
# alpha prefix and parse the digits.
TARGETED_SOURCE_FILES = (
    "anna-ohoiko-1000-words-2nd-ed",
    "ulp-1-00-lesson-notes",
    "ulp-2-00-lesson-notes",
    "ulp-3-00-lesson-notes",
    "ulp-4-00-lesson-notes",
    "ulp-5-00-lesson-notes",
    "ulp-6-00-lesson-notes",
)

# chunk_id format: ``<source_file>_<prefix><digits>`` where prefix is
# one of ``e`` (entry) for Ohoiko and ``l`` (lesson) for ULP.
_CHUNK_SUFFIX_RE = re.compile(r"_([elv])(\d+)$")


def _section_title_for(source_file: str, chunk_title: str, number: int) -> str:
    """Match the natural title format that the live ingesters now write.

    - Ohoiko 1000-words: ``Entry N: <headword>``
    - ULP lesson notes:  ``Lesson N: <Title>`` (already in chunk_title)
    """
    if source_file.startswith("anna-ohoiko-"):
        return f"Entry {number}: {chunk_title}"
    # ULP chunk_title is already ``Lesson N: <title>`` from the ingester.
    return chunk_title


def backfill_source_file(
    conn: sqlite3.Connection,
    source_file: str,
    *,
    dry_run: bool,
) -> tuple[int, int, int]:
    """Backfill orphans for a single source_file.

    Returns ``(n_orphans_before, n_sections_inserted, n_chunks_linked)``.
    Dry-run skips the writes.
    """
    cur = conn.cursor()
    orphans = cur.execute(
        """SELECT id, chunk_id, title, text
             FROM textbooks
            WHERE source_file = ? AND parent_section_id IS NULL
            ORDER BY chunk_id""",
        (source_file,),
    ).fetchall()
    n_orphans = len(orphans)
    if n_orphans == 0:
        return 0, 0, 0

    sections: list[LessonSection] = []
    for _, chunk_id, chunk_title, chunk_text in orphans:
        m = _CHUNK_SUFFIX_RE.search(chunk_id)
        if not m:
            print(
                f"   ⚠️  skipping {chunk_id!r}: cannot derive section_number "
                f"(suffix doesn't match {_CHUNK_SUFFIX_RE.pattern!r})",
                file=sys.stderr,
            )
            continue
        number = int(m.group(2))
        sections.append(
            LessonSection(
                chunk_id=chunk_id,
                section_title=_section_title_for(source_file, chunk_title, number),
                section_number=str(number),
                full_text=chunk_text,
            )
        )

    if dry_run:
        return n_orphans, 0, 0

    inserted, linked = link_lesson_sections(
        conn,
        source_file=source_file,
        sections=sections,
    )
    return n_orphans, inserted, linked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Backfill textbook_sections rows for orphaned lesson/entry chunks",
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
            "Limit backfill to this source_file. Repeat to target several. Defaults to all 7 known orphan source_files."
        ),
    )
    args = parser.parse_args(argv)

    conn = sqlite3.connect(str(args.db))
    try:
        ensure_section_schema(conn)

        targets = tuple(args.source_file) if args.source_file else TARGETED_SOURCE_FILES

        # BEFORE evidence
        print(f"🗃️  Target DB: {args.db}")
        total_orphans_before = conn.execute(
            f"""SELECT COUNT(*) FROM textbooks
                 WHERE source_file IN ({",".join("?" * len(targets))})
                   AND parent_section_id IS NULL""",
            targets,
        ).fetchone()[0]
        total_sections_before = conn.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0]
        print(
            f"\nBEFORE: {total_orphans_before:,} orphan chunks across "
            f"{len(targets)} source_files; total textbook_sections rows: "
            f"{total_sections_before:,}"
        )

        # Per-source backfill
        total_inserted = 0
        total_linked = 0
        for sf in targets:
            print(f"\n📚 {sf}")
            n_orphan, inserted, linked = backfill_source_file(conn, sf, dry_run=args.dry_run)
            print(f"   orphans found: {n_orphan}")
            print(f"   sections inserted: {inserted}")
            print(f"   chunks linked: {linked}")
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
        total_sections_after = conn.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0]
        print(
            f"\nAFTER: {total_orphans_after:,} orphan chunks remain across "
            f"{len(targets)} source_files; total textbook_sections rows: "
            f"{total_sections_after:,} "
            f"(delta +{total_sections_after - total_sections_before})"
        )

        # SAMPLE rows for the largest source
        if not args.dry_run and total_inserted > 0:
            print("\n--- SAMPLE backfilled sections ---")
            for sf in targets:
                row = conn.execute(
                    """SELECT s.section_id, s.section_title, s.section_number, s.grade,
                              t.chunk_id, t.parent_section_id
                         FROM textbook_sections s
                         JOIN textbooks t ON t.parent_section_id = s.section_id
                        WHERE s.source_file = ?
                        ORDER BY CAST(s.section_number AS INTEGER) LIMIT 1""",
                    (sf,),
                ).fetchone()
                if row:
                    print(
                        f"   {sf}: section_id={row[0]} title={row[1]!r} "
                        f"num={row[2]!r} grade={row[3]} chunk={row[4]} "
                        f"parent={row[5]}"
                    )

        return 0 if total_orphans_after == 0 or args.dry_run else 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
