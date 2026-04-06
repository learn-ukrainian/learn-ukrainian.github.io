#!/usr/bin/env python3
"""Build SQLite FTS5 database from external article JSONL files.

Reads all JSONL files in data/external_articles/ and builds a searchable
database with full-text search index on title + text.

Usage:
    .venv/bin/python scripts/wiki/build_sources_db.py
"""

import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / "data" / "external_articles"
DB_PATH = CACHE_DIR / "sources.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL,
    url_normalized TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    domain TEXT DEFAULT '',
    video_id TEXT DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    char_count INTEGER DEFAULT 0,
    source_file TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
    title,
    text,
    content='articles',
    content_rowid='id',
    tokenize='unicode61'
);

CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
    INSERT INTO articles_fts(rowid, title, text)
    VALUES (new.id, new.title, new.text);
END;

CREATE INDEX IF NOT EXISTS idx_url ON articles(url);
CREATE INDEX IF NOT EXISTS idx_url_normalized ON articles(url_normalized);
CREATE INDEX IF NOT EXISTS idx_source_file ON articles(source_file);
"""


def _normalize_url(url: str) -> str:
    """Strip www. for consistent lookup."""
    return url.replace("://www.", "://")


def build(db_path: Path | None = None, source_dir: Path | None = None) -> Path:
    """Build the sources database from all JSONL files."""
    db = db_path or DB_PATH
    src = source_dir or CACHE_DIR

    if db.exists():
        db.unlink()
        print(f"  🗑️  Removed existing {db.name}")

    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)

    total = 0
    seen_urls: set[str] = set()

    jsonl_files = sorted(src.glob("*.jsonl"))
    if not jsonl_files:
        print("  ⚠️  No JSONL files found in data/external_articles/")
        conn.close()
        return db

    for jsonl_path in jsonl_files:
        source_file = jsonl_path.stem
        count = 0

        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                url = entry.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                conn.execute(
                    """INSERT INTO articles
                       (url, url_normalized, title, domain, video_id, text, char_count, source_file)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        url,
                        _normalize_url(url),
                        entry.get("title", ""),
                        entry.get("domain", ""),
                        entry.get("video_id", ""),
                        entry.get("text", ""),
                        entry.get("char_count", len(entry.get("text", ""))),
                        source_file,
                    ),
                )
                count += 1

        total += count
        size_kb = jsonl_path.stat().st_size / 1024
        print(f"  📥 {source_file}: {count} articles ({size_kb:.0f} KB)")

    conn.commit()
    conn.execute("PRAGMA optimize")
    conn.close()

    db_size = db.stat().st_size / 1024 / 1024
    print(f"  ✅ Built {db.name}: {total} articles, {db_size:.1f} MB")
    return db


if __name__ == "__main__":
    if not CACHE_DIR.exists():
        print(f"Error: {CACHE_DIR} does not exist", file=sys.stderr)
        sys.exit(1)

    print("🔨 Building external sources database...")
    build()
