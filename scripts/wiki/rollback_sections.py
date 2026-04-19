#!/usr/bin/env python3
"""Rollback textbook section schema additions."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from scripts.wiki.extract_sections import DEFAULT_DB_PATH, column_exists, table_exists

ORIGINAL_TEXTBOOKS_SCHEMA = """
CREATE TABLE textbooks (
    id INTEGER PRIMARY KEY,
    chunk_id TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source_file TEXT NOT NULL DEFAULT '',
    grade TEXT DEFAULT '',
    author TEXT DEFAULT '',
    char_count INTEGER DEFAULT 0
)
"""

TEXTBOOKS_TRIGGER_SQL = """
CREATE TRIGGER IF NOT EXISTS textbooks_ai AFTER INSERT ON textbooks BEGIN
    INSERT INTO textbooks_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END
"""


def rebuild_textbooks_without_parent(conn: sqlite3.Connection) -> None:
    """Fallback rollback path for SQLite builds without ALTER TABLE DROP COLUMN."""
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("DROP TRIGGER IF EXISTS textbooks_ai")
    conn.execute("ALTER TABLE textbooks RENAME TO textbooks__before_parent_rollback")
    conn.execute(ORIGINAL_TEXTBOOKS_SCHEMA)
    conn.execute(
        """
        INSERT INTO textbooks (id, chunk_id, title, text, source_file, grade, author, char_count)
        SELECT id, chunk_id, title, text, source_file, grade, author, char_count
        FROM textbooks__before_parent_rollback
        """
    )
    conn.execute("DROP TABLE textbooks__before_parent_rollback")
    conn.execute(TEXTBOOKS_TRIGGER_SQL)
    conn.execute("INSERT INTO textbooks_fts(textbooks_fts) VALUES ('rebuild')")
    conn.execute("PRAGMA foreign_keys = ON")


def rollback_schema(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Remove textbook_sections and the textbooks.parent_section_id column."""
    with sqlite3.connect(str(db_path)) as conn, conn:
        if table_exists(conn, "textbook_sections"):
            conn.execute("DROP TABLE textbook_sections")

        conn.execute("DROP INDEX IF EXISTS idx_textbooks_parent")

        if not column_exists(conn, "textbooks", "parent_section_id"):
            return

        try:
            conn.execute("ALTER TABLE textbooks DROP COLUMN parent_section_id")
            conn.execute("INSERT INTO textbooks_fts(textbooks_fts) VALUES ('rebuild')")
        except sqlite3.OperationalError:
            rebuild_textbooks_without_parent(conn)


def parse_args() -> argparse.Namespace:
    """Parse CLI flags for the rollback script."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to data/sources.db")
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint."""
    args = parse_args()
    rollback_schema(args.db)
    print("Rolled back textbook parent-section schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
