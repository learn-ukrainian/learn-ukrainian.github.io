#!/usr/bin/env python3
"""Load processed ЕСУМ JSONL into the sources.db FTS5 store."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
DEFAULT_JSONL = REPO / "data" / "processed" / "esum_vol1.jsonl"
DEFAULT_DB = REPO / "data" / "sources.db"
MIGRATION = REPO / "migrations" / "add_esum_table.sql"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            for key in ("lemma", "vol", "page", "etymology_text"):
                if key not in row:
                    raise ValueError(f"{path}:{line_no}: missing required key {key!r}")
            rows.append(row)
    return rows


def _apply_migration(conn: sqlite3.Connection) -> None:
    conn.executescript(MIGRATION.read_text(encoding="utf-8"))


def load_esum(jsonl: Path, db: Path) -> int:
    rows = _load_jsonl(jsonl)
    conn = sqlite3.connect(str(db))
    try:
        _apply_migration(conn)
        with conn:
            conn.executemany(
                """
                INSERT INTO esum_etymology_meta
                    (lemma, vol, page, etymology_text, cognates, source)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(lemma, vol, page) DO UPDATE SET
                    etymology_text = excluded.etymology_text,
                    cognates = excluded.cognates,
                    source = excluded.source
                """,
                [
                    (
                        str(row["lemma"]),
                        int(row["vol"]),
                        int(row["page"]),
                        str(row["etymology_text"]),
                        json.dumps(row.get("cognates", []), ensure_ascii=False),
                        "ЕСУМ vol. 1",
                    )
                    for row in rows
                ],
            )
            conn.execute("DELETE FROM esum_etymology")
            conn.execute(
                """
                INSERT INTO esum_etymology(rowid, lemma, etymology_text, cognates, vol, page)
                SELECT id, lemma, etymology_text, cognates, vol, page
                FROM esum_etymology_meta
                ORDER BY vol, page, lemma
                """
            )
        return len(rows)
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Load processed ЕСУМ JSONL into data/sources.db FTS5 tables.\n"
            "Use after scripts/ingest/esum_ingest.py; do not run against unrelated JSONL schemas."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""Examples:
  .venv/bin/python scripts/ingest/esum_load.py --jsonl data/processed/esum_vol1.jsonl --db data/sources.db
  .venv/bin/python scripts/ingest/esum_load.py --jsonl {DEFAULT_JSONL} --db {DEFAULT_DB}

Outputs:
  Applies migrations/add_esum_table.sql and updates esum_etymology_meta plus esum_etymology FTS rows.

Exit codes:
  0 on successful load; >=1 on missing input, invalid JSONL, missing DB, or SQLite failure.

Related:
  GitHub issue #1662; query loaded data through search_esum.
""",
    )
    parser.add_argument(
        "--jsonl",
        type=Path,
        default=DEFAULT_JSONL,
        help=f"Processed ЕСУМ JSONL to load. Default: {DEFAULT_JSONL}",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"SQLite sources.db path to update. Default: {DEFAULT_DB}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.jsonl.exists():
        print(f"JSONL file not found: {args.jsonl}", file=sys.stderr)
        return 1
    if not args.db.exists():
        print(f"SQLite DB not found: {args.db}", file=sys.stderr)
        return 1
    if not MIGRATION.exists():
        print(f"Migration file not found: {MIGRATION}", file=sys.stderr)
        return 1
    loaded = load_esum(args.jsonl, args.db)
    print(f"Loaded {loaded:,} ЕСУМ entries into {args.db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
