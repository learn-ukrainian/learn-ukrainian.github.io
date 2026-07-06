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
        --slugs 9-klas-khimiya-popel-2017 [...] [--db data/sources.db] [--dry-run]
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
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from wiki.build_sources_db import _build_textbook_row

CHUNKS_DIR = PROJECT_ROOT / "data" / "textbook_chunks"
DEFAULT_DB = PROJECT_ROOT / "data" / "sources.db"

# Canonical Cyrillic author forms, title-probed from source pages during
# wave-1 acquisition (#4593, 2026-07-06). Keep in sync with the migration
# mapping in scripts/migrations/2026-05-15-add-author-uk-to-textbooks.py.
AUTHOR_UK: dict[str, str] = {
    "ryvkind": "Ривкінд",
    "ister": "Істер",
    "merzliak": "Мерзляк",
    "zadorozhnyi": "Задорожний",
    "bariakhtar": "Бар'яхтар",
    "hryhorovych": "Григорович",
    "popel": "Попель",
    "anderson": "Андерсон",
}

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


def find_jsonl(slug: str) -> Path:
    grade = int(slug.split("-")[0])
    path = CHUNKS_DIR / f"grade-{grade:02d}" / f"{slug}.jsonl"
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


def build_rows(slug: str) -> list[tuple]:
    jsonl_path = find_jsonl(slug)
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


def ingest(slugs: list[str], *, db_path: Path, dry_run: bool) -> dict[str, int]:
    """Run the delete+insert+FTS-resync cycle for ``slugs``.

    Concurrency note (review, PR #4624): sources.db runs in WAL mode in
    production, so MCP readers are not blocked by this writer; still,
    prefer running while no build/review dispatch is mid-flight.
    """
    counts: dict[str, int] = {}
    per_slug_rows = {slug: build_rows(slug) for slug in slugs}  # fail fast, pre-tx
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    try:
        conn.execute("BEGIN")
        for slug, rows in per_slug_rows.items():
            deleted = conn.execute(
                "DELETE FROM textbooks WHERE source_file = ?", (slug,)
            ).rowcount
            conn.executemany(TB_SQL, rows)
            counts[slug] = len(rows)
            print(f"  {slug}: deleted {deleted}, inserted {len(rows)}")
        print("  resyncing textbooks_fts (external-content rebuild)…")
        conn.execute("INSERT INTO textbooks_fts(textbooks_fts) VALUES('rebuild')")
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
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--slugs", nargs="+", help="Canonical source_file slugs")
    group.add_argument(
        "--wave1", action="store_true", help="Ingest the 22 #4593 wave-1 books"
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    slugs = list(WAVE1_SLUGS) if args.wave1 else list(args.slugs)
    try:
        counts = ingest(slugs, db_path=args.db, dry_run=args.dry_run)
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
