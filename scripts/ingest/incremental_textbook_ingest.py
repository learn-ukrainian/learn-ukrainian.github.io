"""Incrementally ingest textbook chunk JSONL files into the live sources.db.

The #4593 wave-1 path (reused for wave 2+): no destructive ``--force``
rebuild — per the safe recipe in docs/corpus-inventory.md, each book is
DELETE-then-INSERT inside one transaction, followed by an external-content
FTS resync (the delete fires no FTS trigger, so a rebuild is mandatory).

Rows are built via ``build_sources_db._build_textbook_row`` so the subject
column and the author_uk strictness gate apply exactly as in a full rebuild.
JSONL entries carry ``author_uk: null`` (extraction emits Latin slugs only),
so entries are enriched from ``AUTHOR_UK`` first — canonical Cyrillic forms
title-probed from the source pages during wave-1 acquisition (2026-07-06).

Usage:
    .venv/bin/python scripts/ingest/incremental_textbook_ingest.py \
        --slugs 9-klas-khimiya-popel-2017 [...] \
        [--db data/sources.db] [--chunks-root GDRIVE/textbook_chunks] [--dry-run]
    .venv/bin/python scripts/ingest/incremental_textbook_ingest.py --wave1
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from wiki.build_sources_db import _build_textbook_row
from wiki.config import TEXTBOOK_CHUNKS_DIR
from wiki.extract_sections import (
    SectionAssignment,
    assign_sections,
    build_section_groups,
    ensure_schema,
    load_textbook_rows,
)
from wiki.textbook_subjects import AUTHOR_UK_BY_TRANSLIT

# The canonical chunk store is the Google Drive corpus mount. Keep this
# constant patchable for local fixtures, but do not assume the absent
# repo-local data/textbook_chunks directory is the production source.
CHUNKS_DIR = TEXTBOOK_CHUNKS_DIR
DEFAULT_DB = PROJECT_ROOT / "data" / "sources.db"

# Author map: single source of truth in wiki.textbook_subjects (PR #4650).
AUTHOR_UK = AUTHOR_UK_BY_TRANSLIT

WAVE1_SLUGS: tuple[str, ...] = (
    "5-klas-informatyka-ryvkind-2022",
    "5-klas-matematyka-ister-2022",
    "6-klas-informatyka-ryvkind-2023",
    "6-klas-matematyka-ister-2023",
    "7-klas-algebra-merzliak-2024",
    "7-klas-biolohiya-zadorozhnyi-2024",
    "7-klas-fizyka-bariakhtar-2024",
    "7-klas-heometriya-merzliak-2024",
    "7-klas-informatyka-ryvkind-2024",
    "7-klas-khimiya-hryhorovych-2024",
    "8-klas-algebra-merzliak-2025",
    "8-klas-biolohiya-anderson-2025",
    "8-klas-fizyka-bariakhtar-2025",
    "8-klas-heometriya-merzliak-2025",
    "8-klas-informatyka-ryvkind-2025",
    "8-klas-khimiya-hryhorovych-2025",
    "9-klas-algebra-merzliak-2017",
    "9-klas-biolohiya-zadorozhnyi-2026",
    "9-klas-fizyka-bariakhtar-2022",
    "9-klas-heometriya-merzliak-2017",
    "9-klas-informatyka-ryvkind-2017",
    "9-klas-khimiya-popel-2017",
)


class IngestError(RuntimeError):
    """Deterministic ingest failure."""


def find_jsonl(slug: str, *, chunks_root: Path | None = None) -> Path:
    """Resolve one source JSONL under the explicit or canonical chunk root."""
    grade = int(slug.split("-")[0])
    root = Path(chunks_root) if chunks_root is not None else CHUNKS_DIR
    path = root / f"grade-{grade:02d}" / f"{slug}.jsonl"
    if not path.is_file():
        raise IngestError(f"chunk file missing: {path}")
    return path


def enrich_author_uk(entry: dict, *, slug: str) -> dict:
    """Fill author_uk from the canonical mapping when extraction left it null."""
    author = str(entry.get("author") or "").strip()
    if author and not str(entry.get("author_uk") or "").strip():
        uk = AUTHOR_UK.get(author.lower())
        if uk is None:
            raise IngestError(
                f"{slug}: author {author!r} has no canonical Cyrillic form in "
                "AUTHOR_UK — add it (title-probed, never guessed) before ingest."
            )
        entry = {**entry, "author_uk": uk}
    return entry


def build_rows(slug: str, *, chunks_root: Path | None = None) -> list[tuple]:
    jsonl_path = find_jsonl(slug, chunks_root=chunks_root)
    grade = f"grade-{int(slug.split('-')[0]):02d}"
    rows: list[tuple] = []
    with open(jsonl_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entry = enrich_author_uk(json.loads(line), slug=slug)
            rows.append(
                _build_textbook_row(
                    entry,
                    source_file=slug,
                    grade=grade,
                    chunk_index=len(rows),
                )
            )
    if not rows:
        raise IngestError(f"{slug}: no chunks in {jsonl_path}")
    return rows


TB_SQL = """INSERT INTO textbooks
            (chunk_id, title, text, source_file, subject, grade, author,
             author_uk, char_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""


SECTION_INSERT_SQL = """INSERT INTO textbook_sections
    (source_file, grade, section_title, section_number, page_start, page_end,
     chunk_count, full_text)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""


FRONT_MATTER_SECTION = "Вступні матеріали"


def _assign_leading_front_matter(
    assignments: list[SectionAssignment],
) -> list[SectionAssignment]:
    """Assign a real parent to preface rows before the first detected heading.

    Title, imprint, contents, and author-preface pages commonly precede the
    first machine-detectable chapter. They belong to a bounded synthetic front
    matter section. A source with no detected heading at all still fails closed;
    this helper does not turn arbitrary unstructured content into a section.
    """
    first_assigned = next(
        (index for index, item in enumerate(assignments) if item.section_title is not None),
        None,
    )
    if first_assigned in {None, 0}:
        return assignments
    return [
        SectionAssignment(
            row=item.row,
            page_number=item.page_number,
            section_title=FRONT_MATTER_SECTION,
        )
        if index < first_assigned and item.section_title is None
        else item
        for index, item in enumerate(assignments)
    ]


def _rebuild_source_sections(conn: sqlite3.Connection, slug: str) -> tuple[int, int]:
    """Replace only one source's section rows and parent links.

    The existing extraction helpers provide deterministic assignment and
    grouping. This writer deliberately avoids ``persist_sections`` because
    that helper clears every textbook section and every parent link in the
    database, which is not safe for an incremental source replacement.
    """
    ensure_schema(conn)
    source_rows = [row for row in load_textbook_rows(conn) if row.source_file == slug]
    assignments = _assign_leading_front_matter(assign_sections(source_rows))
    sections = build_section_groups(assignments)

    # Null links before deleting section parents so this remains valid if a
    # caller has enabled foreign-key enforcement on the connection.
    conn.execute(
        "UPDATE textbooks SET parent_section_id = NULL WHERE source_file = ?",
        (slug,),
    )
    conn.execute("DELETE FROM textbook_sections WHERE source_file = ?", (slug,))

    section_id_by_row_id: dict[int, int] = {}
    for section in sections:
        cursor = conn.execute(
            SECTION_INSERT_SQL,
            (
                section.source_file,
                section.grade,
                section.section_title,
                section.section_number,
                section.page_start,
                section.page_end,
                section.chunk_count,
                section.full_text,
            ),
        )
        section_id = cursor.lastrowid
        for assignment in section.rows:
            section_id_by_row_id[assignment.row.id] = section_id

    links = [
        (section_id_by_row_id[assignment.row.id], assignment.row.id)
        for assignment in assignments
        if assignment.section_title is not None
    ]
    conn.executemany(
        "UPDATE textbooks SET parent_section_id = ? WHERE id = ?",
        links,
    )
    linked_rows = conn.execute(
        """SELECT COUNT(*) FROM textbooks
           WHERE source_file = ? AND parent_section_id IS NOT NULL""",
        (slug,),
    ).fetchone()[0]
    total_rows = len(source_rows)
    if linked_rows != total_rows:
        raise IngestError(
            f"{slug}: {total_rows - linked_rows} accepted school-textbook rows "
            "remain unlinked from textbook_sections"
        )
    return len(sections), linked_rows


def _fts_source_evidence(
    conn: sqlite3.Connection,
    slug: str,
    expected_rows: int,
) -> dict[str, object]:
    """Return and validate the source's external-content FTS row parity."""
    indexed_rows = conn.execute(
        """SELECT COUNT(*) FROM textbooks_fts AS f
           JOIN textbooks AS t ON t.id = f.rowid
           WHERE t.source_file = ?""",
        (slug,),
    ).fetchone()[0]
    evidence = {
        "source_file": slug,
        "expected_rows": expected_rows,
        "indexed_rows": indexed_rows,
        "parity": indexed_rows == expected_rows,
    }
    if not evidence["parity"]:
        raise IngestError(
            f"{slug}: textbooks/textbooks_fts parity failed "
            f"({indexed_rows} indexed, {expected_rows} rows)"
        )
    return evidence


def ingest(
    slugs: list[str],
    *,
    db_path: Path,
    dry_run: bool,
    chunks_root: Path | None = None,
) -> dict[str, int]:
    """Run the delete+insert+FTS-resync cycle for ``slugs``.

    Concurrency note (review, PR #4624): sources.db runs in WAL mode in
    production, so MCP readers are not blocked by this writer; still,
    prefer running while no build/review dispatch is mid-flight.
    """
    counts: dict[str, int] = {}
    receipts: dict[str, dict[str, object]] = {}
    per_slug_rows = {
        slug: build_rows(slug, chunks_root=chunks_root)
        for slug in slugs
    }  # fail fast, pre-tx
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN")
        for slug, rows in per_slug_rows.items():
            deleted = conn.execute(
                "DELETE FROM textbooks WHERE source_file = ?", (slug,)
            ).rowcount
            conn.executemany(TB_SQL, rows)
            section_rows, linked_rows = _rebuild_source_sections(conn, slug)
            counts[slug] = len(rows)
            receipts[slug] = {
                "source_file": slug,
                "deleted_rows": deleted,
                "inserted_rows": len(rows),
                "section_rows": section_rows,
                "linked_rows": linked_rows,
            }
            print(f"  {slug}: deleted {deleted}, inserted {len(rows)}, "
                  f"sections {section_rows}, links {linked_rows}")
        print("  resyncing textbooks_fts (external-content rebuild)…")
        conn.execute("INSERT INTO textbooks_fts(textbooks_fts) VALUES('rebuild')")
        for slug, rows in per_slug_rows.items():
            receipts[slug]["fts"] = _fts_source_evidence(conn, slug, len(rows))
            print(f"  FTS evidence: {json.dumps(receipts[slug]['fts'], ensure_ascii=False)}")
        if dry_run:
            conn.execute("ROLLBACK")
            print("  DRY-RUN: rolled back")
        else:
            conn.execute("COMMIT")
    except BaseException:
        # Explicit rollback (review, PR #4624): never leave the live DB with
        # an open write transaction on the error path.
        conn.rollback()
        raise
    finally:
        conn.close()
    for _slug, receipt in receipts.items():
        print(f"  receipt: {json.dumps(receipt, ensure_ascii=False, sort_keys=True)}")
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--slugs", nargs="+", help="Canonical source_file slugs")
    group.add_argument(
        "--wave1", action="store_true", help="Ingest the 22 #4593 wave-1 books"
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument(
        "--chunks-root",
        type=Path,
        default=CHUNKS_DIR,
        help="Canonical textbook chunk directory (Google Drive mount or fixture root)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    slugs = list(WAVE1_SLUGS) if args.wave1 else list(args.slugs)
    try:
        counts = ingest(
            slugs,
            db_path=args.db,
            dry_run=args.dry_run,
            chunks_root=args.chunks_root,
        )
    except (IngestError, ValueError) as exc:
        # ValueError: _build_textbook_row's strictness gates (author_uk,
        # unmapped subject) — surface cleanly instead of a traceback.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    total = sum(counts.values())
    print(f"OK: {len(counts)} books, {total} chunks{' (dry-run)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
