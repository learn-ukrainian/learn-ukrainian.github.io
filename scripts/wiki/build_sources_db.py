#!/usr/bin/env python3
"""Build SQLite FTS5 database from ALL source JSONL files.

Ingests:
1. External articles (ULP blogs, other blogs, YouTube subtitles)
2. Textbook chunks (grades 1-11, ukrmova + bukvar + ukrlit)

All content goes into a single FTS5-indexed table for fast keyword search.

Usage:
    .venv/bin/python scripts/wiki/build_sources_db.py
"""

import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXTERNAL_DIR = PROJECT_ROOT / "data" / "external_articles"
TEXTBOOK_DIR = (
    Path.home()
    / "Library/CloudStorage/GoogleDrive-krisztian.koos@gmail.com"
    / "My Drive/Projects/learn-ukrainian-data/textbook_chunks"
)
DB_PATH = EXTERNAL_DIR / "sources.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY,
    chunk_id TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    url_normalized TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL,
    source_file TEXT NOT NULL,
    grade TEXT DEFAULT '',
    author TEXT DEFAULT '',
    domain TEXT DEFAULT '',
    char_count INTEGER DEFAULT 0
);

CREATE VIRTUAL TABLE IF NOT EXISTS sources_fts USING fts5(
    title,
    text,
    content='sources',
    content_rowid='id',
    tokenize='unicode61'
);

CREATE TRIGGER IF NOT EXISTS sources_ai AFTER INSERT ON sources BEGIN
    INSERT INTO sources_fts(rowid, title, text)
    VALUES (new.id, new.title, new.text);
END;

CREATE INDEX IF NOT EXISTS idx_url ON sources(url);
CREATE INDEX IF NOT EXISTS idx_url_normalized ON sources(url_normalized);
CREATE INDEX IF NOT EXISTS idx_source_type ON sources(source_type);
CREATE INDEX IF NOT EXISTS idx_source_file ON sources(source_file);
CREATE INDEX IF NOT EXISTS idx_chunk_id ON sources(chunk_id);
"""


def _normalize_url(url: str) -> str:
    """Strip www. for consistent lookup."""
    return url.replace("://www.", "://")


def build(db_path: Path | None = None,
          external_dir: Path | None = None,
          textbook_dir: Path | None = None) -> Path:
    """Build the sources database from all JSONL files."""
    db = db_path or DB_PATH
    ext_dir = external_dir or EXTERNAL_DIR
    tb_dir = textbook_dir or TEXTBOOK_DIR

    if db.exists():
        db.unlink()
        print(f"  🗑️  Removed existing {db.name}")

    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")  # Speed up bulk insert
    conn.executescript(SCHEMA)

    total = 0

    # --- External articles ---
    seen_urls: set[str] = set()
    ext_files = sorted(ext_dir.glob("*.jsonl")) if ext_dir.exists() else []
    for jsonl_path in ext_files:
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
                    """INSERT INTO sources
                       (chunk_id, url, url_normalized, title, text,
                        source_type, source_file, domain, char_count)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        f"ext-{source_file}-{count}",
                        url,
                        _normalize_url(url),
                        entry.get("title", ""),
                        entry.get("text", ""),
                        "external",
                        source_file,
                        entry.get("domain", ""),
                        entry.get("char_count", len(entry.get("text", ""))),
                    ),
                )
                count += 1
        total += count
        size_kb = jsonl_path.stat().st_size / 1024
        print(f"  📥 external/{source_file}: {count} entries ({size_kb:.0f} KB)")

    # --- Textbook chunks ---
    if tb_dir.exists():
        grade_dirs = sorted(tb_dir.glob("grade-*"))
        for grade_dir in grade_dirs:
            grade = grade_dir.name  # e.g. "grade-05"
            for jsonl_path in sorted(grade_dir.glob("*.jsonl")):
                source_file = jsonl_path.stem
                count = 0
                with open(jsonl_path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        entry = json.loads(line)
                        chunk_id = entry.get("chunk_id", f"tb-{source_file}-{count}")
                        conn.execute(
                            """INSERT INTO sources
                               (chunk_id, url, url_normalized, title, text,
                                source_type, source_file, grade, author, char_count)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                chunk_id,
                                "",  # Textbooks don't have URLs
                                "",
                                entry.get("section_title", ""),
                                entry.get("text", ""),
                                "textbook",
                                source_file,
                                entry.get("grade", grade),
                                entry.get("author", ""),
                                entry.get("token_count", len(entry.get("text", ""))),
                            ),
                        )
                        count += 1
                total += count
                print(f"  📖 {grade}/{source_file}: {count} chunks")
    else:
        print(f"  ⚠️  Textbook dir not found: {tb_dir}")

    conn.commit()
    conn.execute("PRAGMA optimize")
    conn.close()

    db_size = db.stat().st_size / 1024 / 1024
    print(f"  ✅ Built {db.name}: {total} entries, {db_size:.1f} MB")
    return db


if __name__ == "__main__":
    print("🔨 Building unified sources database...")
    build()
