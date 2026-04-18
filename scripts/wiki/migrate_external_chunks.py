#!/usr/bin/env python3
"""Schema migration entrypoint for the external articles corpus."""

from __future__ import annotations

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "sources.db"

EXTERNAL_COLUMN_SPECS = [
    ("channel_id", "TEXT DEFAULT ''"),
    ("speaker", "TEXT DEFAULT ''"),
    ("register_tag", "TEXT DEFAULT ''"),
    ("decolonization_tag", "TEXT DEFAULT ''"),
    ("quality_tier", "INTEGER DEFAULT 2"),
    ("publish_date", "TEXT DEFAULT ''"),
    ("duration_s", "INTEGER DEFAULT 0"),
    ("chunk_start_ts", "INTEGER"),
    ("chunk_end_ts", "INTEGER"),
    ("video_id", "TEXT DEFAULT ''"),
]


def ensure_external_schema(conn: sqlite3.Connection) -> list[str]:
    """Add the enriched external_articles columns and rebuild external FTS."""
    existing = {
        row[1]
        for row in conn.execute("PRAGMA table_info(external_articles)").fetchall()
    }
    added: list[str] = []

    for column, ddl in EXTERNAL_COLUMN_SPECS:
        if column in existing:
            continue
        conn.execute(f"ALTER TABLE external_articles ADD COLUMN {column} {ddl}")
        added.append(column)

    conn.execute("DROP TRIGGER IF EXISTS external_ai")
    conn.execute("DROP TABLE IF EXISTS external_fts")
    conn.execute(
        """CREATE VIRTUAL TABLE external_fts USING fts5(
            title, text, speaker,
            content='external_articles',
            content_rowid='id',
            tokenize='unicode61'
        )"""
    )
    conn.execute(
        """CREATE TRIGGER external_ai AFTER INSERT ON external_articles BEGIN
            INSERT INTO external_fts(rowid, title, text, speaker)
            VALUES (new.id, new.title, new.text, new.speaker);
        END;"""
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ext_url ON external_articles(url)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ext_url_norm ON external_articles(url_normalized)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ext_channel ON external_articles(channel_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ext_quality ON external_articles(quality_tier)")
    conn.execute("INSERT INTO external_fts(external_fts) VALUES ('rebuild')")
    return added


def main() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    added = ensure_external_schema(conn)
    conn.commit()
    conn.close()
    print(f"Schema ready: {', '.join(added) if added else 'no columns added'}")


if __name__ == "__main__":
    main()
