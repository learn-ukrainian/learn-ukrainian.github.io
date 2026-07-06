"""Add canonical ``subject`` column to ``textbooks`` and back-fill it.

The textbook corpus historically encoded subject only in ``source_file``
tokens such as ``ukrmova``, ``ukrlit``, ``istoriya``, and ``bukvar``.
STEM ingestion needs a first-class filterable column so callers can query
``search_text(subject=...)`` without brittle filename matching.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DEFAULT_DB = PROJECT_ROOT / "data" / "sources.db"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from wiki.textbook_subjects import subject_for_source_file


class UnmappedTextbookSubjectsError(RuntimeError):
    """Raised when any existing ``source_file`` cannot be assigned a subject."""

    def __init__(self, source_files: list[str]) -> None:
        self.source_files = sorted(source_files)
        super().__init__(
            "Unmapped textbooks.source_file values: "
            + ", ".join(repr(value) for value in self.source_files)
        )


@dataclass
class MigrationStatus:
    column_added: bool = False
    rows_updated: int = 0
    total_rows: int = 0
    populated_subject: int = 0
    subject_counts: dict[str, int] = field(default_factory=dict)


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def _ensure_column(conn: sqlite3.Connection, *, dry_run: bool) -> bool:
    """Add ``subject`` column if missing. Returns True if it was/would be added."""
    if _has_column(conn, "textbooks", "subject"):
        return False
    if not dry_run:
        conn.execute("ALTER TABLE textbooks ADD COLUMN subject TEXT")
    return True


def _ensure_index(conn: sqlite3.Connection, *, dry_run: bool) -> None:
    if not dry_run:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_textbooks_subject ON textbooks(subject)"
        )


def _distinct_source_files(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT DISTINCT source_file
        FROM textbooks
        ORDER BY source_file
        """
    ).fetchall()
    return ["" if row[0] is None else str(row[0]) for row in rows]


def _subject_map(conn: sqlite3.Connection) -> dict[str, str]:
    mapped: dict[str, str] = {}
    unmapped: list[str] = []
    for source_file in _distinct_source_files(conn):
        subject = subject_for_source_file(source_file)
        if subject is None:
            unmapped.append(source_file)
        else:
            mapped[source_file] = subject
    if unmapped:
        raise UnmappedTextbookSubjectsError(unmapped)
    return mapped


def _count_rows_for_source(
    conn: sqlite3.Connection,
    *,
    source_file: str,
    subject: str,
    column_exists: bool,
) -> int:
    if column_exists:
        sql = """
            SELECT COUNT(*) FROM textbooks
            WHERE source_file = ?
              AND (subject IS NULL OR subject = '' OR subject != ?)
        """
        params = (source_file, subject)
    else:
        sql = "SELECT COUNT(*) FROM textbooks WHERE source_file = ?"
        params = (source_file,)
    return int(conn.execute(sql, params).fetchone()[0])


def _backfill(
    conn: sqlite3.Connection,
    *,
    dry_run: bool,
    column_exists: bool,
    subjects_by_source: dict[str, str],
) -> tuple[int, dict[str, int]]:
    updated_total = 0
    subject_counts = dict.fromkeys(sorted(set(subjects_by_source.values())), 0)
    for source_file, subject in subjects_by_source.items():
        count_total = int(
            conn.execute(
                "SELECT COUNT(*) FROM textbooks WHERE source_file = ?",
                (source_file,),
            ).fetchone()[0]
        )
        subject_counts[subject] += count_total

        count_update = _count_rows_for_source(
            conn,
            source_file=source_file,
            subject=subject,
            column_exists=column_exists,
        )
        if count_update == 0:
            continue
        if not dry_run:
            conn.execute(
                """
                UPDATE textbooks
                SET subject = ?
                WHERE source_file = ?
                  AND (subject IS NULL OR subject = '' OR subject != ?)
                """,
                (subject, source_file, subject),
            )
        updated_total += count_update
    return updated_total, subject_counts


def apply(conn: sqlite3.Connection, *, dry_run: bool = False) -> MigrationStatus:
    """Apply the migration idempotently."""
    subjects_by_source = _subject_map(conn)
    had_column_before = _has_column(conn, "textbooks", "subject")
    column_added = _ensure_column(conn, dry_run=dry_run)
    column_exists_for_count = had_column_before or (column_added and not dry_run)
    rows_updated, subject_counts = _backfill(
        conn,
        dry_run=dry_run,
        column_exists=column_exists_for_count,
        subjects_by_source=subjects_by_source,
    )
    _ensure_index(conn, dry_run=dry_run)
    if not dry_run:
        conn.commit()

    total_rows = int(conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0])
    if column_exists_for_count:
        populated_subject = int(
            conn.execute(
                """
                SELECT COUNT(*) FROM textbooks
                WHERE subject IS NOT NULL AND subject != ''
                """
            ).fetchone()[0]
        )
    else:
        populated_subject = 0

    return MigrationStatus(
        column_added=column_added,
        rows_updated=rows_updated,
        total_rows=total_rows,
        populated_subject=populated_subject,
        subject_counts=subject_counts,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing.",
    )
    args = parser.parse_args(argv)

    if not args.db.exists():
        raise SystemExit(f"Sources DB not found: {args.db}")

    try:
        with sqlite3.connect(str(args.db)) as conn:
            status = apply(conn, dry_run=args.dry_run)
    except UnmappedTextbookSubjectsError as exc:
        print("ERROR: unmapped textbooks.source_file values:", file=sys.stderr)
        for source_file in exc.source_files:
            print(f"  - {source_file}", file=sys.stderr)
        return 1

    prefix = "[dry-run] " if args.dry_run else ""
    print(f"{prefix}column_added={status.column_added}")
    print(f"{prefix}rows_updated={status.rows_updated}")
    print(
        f"{prefix}populated_subject={status.populated_subject}/"
        f"{status.total_rows} (rows with subject / total textbook rows)"
    )
    print(f"{prefix}subject_counts:")
    for subject, count in sorted(status.subject_counts.items()):
        print(f"{prefix}  {subject}: {count}")
    print(f"{prefix}all distinct source_file values mapped to subjects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
