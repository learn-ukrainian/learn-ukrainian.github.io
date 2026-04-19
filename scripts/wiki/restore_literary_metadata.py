#!/usr/bin/env python3
"""Restore literary metadata columns on already-built sources.db files."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GDRIVE_DATA = (
    Path.home()
    / "Library/CloudStorage/GoogleDrive-krisztian.koos@gmail.com"
    / "My Drive/Projects/learn-ukrainian-data"
)
DB_PATH = PROJECT_ROOT / "data" / "sources.db"

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from wiki.build_sources_db import (
        format_literary_validation_report,
        write_literary_validation_report,
    )
    from wiki.sources import build_literary_row
else:
    from .build_sources_db import (
        format_literary_validation_report,
        write_literary_validation_report,
    )
    from .sources import build_literary_row


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _sha256_text_hashes(conn: sqlite3.Connection) -> list[str]:
    return [
        hashlib.sha256(str(row[0]).encode("utf-8")).hexdigest()
        for row in conn.execute("SELECT text FROM literary_texts ORDER BY id")
    ]


def _discover_literary_dir(conn: sqlite3.Connection) -> Path:
    db_source_file_count = conn.execute(
        "SELECT COUNT(DISTINCT source_file) FROM literary_texts"
    ).fetchone()[0]
    local_dir = PROJECT_ROOT / "data" / "literary_texts"
    gdrive_dir = GDRIVE_DATA / "literary_texts"

    candidates = []
    for path in (local_dir, gdrive_dir):
        if not path.exists():
            continue
        file_count = len(list(path.glob("*.jsonl")))
        candidates.append((file_count, path))

    if not candidates:
        raise FileNotFoundError("no literary JSONL directory found")

    for file_count, path in sorted(candidates, reverse=True):
        if file_count >= db_source_file_count:
            return path
    return max(candidates)[1]


def _ensure_columns_and_indexes(conn: sqlite3.Connection) -> list[str]:
    existing = _column_names(conn, "literary_texts")
    added_columns: list[str] = []
    required_columns = {
        "work": "TEXT",
        "work_id": "TEXT",
        "year": "INTEGER",
        "language_period": "TEXT",
    }
    for column, column_type in required_columns.items():
        if column in existing:
            continue
        conn.execute(f"ALTER TABLE literary_texts ADD COLUMN {column} {column_type}")
        added_columns.append(column)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_literary_period ON literary_texts(language_period)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_literary_work_id ON literary_texts(work_id)")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_literary_period_genre "
        "ON literary_texts(language_period, genre)"
    )
    return added_columns


def _load_metadata_rows(literary_dir: Path) -> tuple[dict[tuple[str, str], tuple], dict[str, tuple]]:
    rows_by_chunk_and_source: dict[tuple[str, str], tuple] = {}
    rows_by_chunk_id: dict[str, list[tuple]] = {}
    for jsonl_path in sorted(literary_dir.glob("*.jsonl")):
        source_file = jsonl_path.stem
        with open(jsonl_path, encoding="utf-8") as handle:
            for chunk_index, line in enumerate(handle):
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                row = build_literary_row(
                    entry,
                    source_file=source_file,
                    chunk_index=chunk_index,
                    warn=print,
                )
                rows_by_chunk_and_source[(row[0], source_file)] = row
                rows_by_chunk_id.setdefault(row[0], []).append(row)

    unique_rows_by_chunk_id = {
        chunk_id: rows[0]
        for chunk_id, rows in rows_by_chunk_id.items()
        if len(rows) == 1
    }
    return rows_by_chunk_and_source, unique_rows_by_chunk_id


def restore_literary_metadata(
    db_path: Path,
    *,
    literary_dir: Path | None = None,
) -> dict[str, object]:
    conn = sqlite3.connect(str(db_path))
    try:
        before_hashes = _sha256_text_hashes(conn)
        effective_literary_dir = literary_dir or _discover_literary_dir(conn)
        added_columns = _ensure_columns_and_indexes(conn)
        metadata_rows_by_key, unique_rows_by_chunk_id = _load_metadata_rows(effective_literary_dir)

        updated_rows = 0
        missing_chunk_ids: list[str] = []
        with conn:
            for row_id, chunk_id, source_file in conn.execute(
                "SELECT id, chunk_id, source_file FROM literary_texts ORDER BY id"
            ).fetchall():
                chunk_id = str(chunk_id)
                source_file = str(source_file)
                row = metadata_rows_by_key.get((chunk_id, source_file))
                if row is None:
                    row = unique_rows_by_chunk_id.get(chunk_id)
                if row is None:
                    missing_chunk_ids.append(f"{source_file}:{chunk_id}")
                    continue

                cursor = conn.execute(
                    """
                    UPDATE literary_texts
                    SET work = ?, work_id = ?, year = ?, genre = ?, language_period = ?
                    WHERE id = ?
                      AND (
                          work IS NOT ?
                          OR work_id IS NOT ?
                          OR year IS NOT ?
                          OR genre IS NOT ?
                          OR language_period IS NOT ?
                      )
                    """,
                    (
                        row[5],
                        row[6],
                        row[7],
                        row[8],
                        row[9],
                        row_id,
                        row[5],
                        row[6],
                        row[7],
                        row[8],
                        row[9],
                    ),
                )
                updated_rows += cursor.rowcount

        if missing_chunk_ids:
            preview = ", ".join(missing_chunk_ids[:5])
            raise RuntimeError(
                f"could not backfill {len(missing_chunk_ids)} literary rows from {effective_literary_dir}: "
                f"{preview}"
            )

        remaining_missing = conn.execute(
            """
            SELECT COUNT(*)
            FROM literary_texts
            WHERE work IS NULL OR work = ''
               OR work_id IS NULL OR work_id = ''
               OR language_period IS NULL OR language_period = ''
            """
        ).fetchone()[0]
        if remaining_missing:
            raise RuntimeError(f"{remaining_missing} literary rows remain missing restored metadata")

        after_hashes = _sha256_text_hashes(conn)
        if before_hashes != after_hashes:
            raise AssertionError("migration modified text column")

        report = format_literary_validation_report(conn)
        report_path = write_literary_validation_report(report)
        return {
            "db_path": db_path,
            "literary_dir": effective_literary_dir,
            "added_columns": added_columns,
            "updated_rows": updated_rows,
            "report": report,
            "report_path": report_path,
            "hashes_unchanged": True,
        }
    finally:
        conn.close()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restore literary metadata on sources.db.")
    parser.add_argument("--db-path", type=Path, default=DB_PATH)
    parser.add_argument("--literary-dir", type=Path, default=None)
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    result = restore_literary_metadata(
        args.db_path,
        literary_dir=args.literary_dir,
    )
    print(f"Restored literary metadata in {result['db_path']}")
    print(f"Literary source dir: {result['literary_dir']}")
    print(f"Added columns: {', '.join(result['added_columns']) or 'none'}")
    print(f"Updated rows: {result['updated_rows']}")
    print(f"SHA256 text immutability: {'PASS' if result['hashes_unchanged'] else 'FAIL'}")
    print(result["report"])
    print(f"Validation log: {result['report_path']}")
