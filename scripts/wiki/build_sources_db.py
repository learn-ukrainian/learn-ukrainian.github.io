#!/usr/bin/env python3
"""Build unified SQLite database from ALL source JSONL files.

Ingests:
1. External articles (ULP blogs, other blogs, YouTube subtitles)
2. Textbook chunks (grades 1-11)
3. Dictionary collections (СУМ-11, Грінченко, Балла, etc.)
4. Literary texts (chronicles, poetry, legal texts)
5. CEFR vocabulary (PULS)
6. Style guide (Антоненко-Давидович)

Replaces Qdrant vector DB entirely. All content searchable via SQLite FTS5
for prose and B-TREE indexes for dictionary headword lookups.

Usage:
    .venv/bin/python scripts/wiki/build_sources_db.py
"""

import json
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GDRIVE_DATA = (
    Path.home()
    / "Library/CloudStorage/GoogleDrive-krisztian.koos@gmail.com"
    / "My Drive/Projects/learn-ukrainian-data"
)
EXTERNAL_DIR = PROJECT_ROOT / "data" / "external_articles"
DB_PATH = PROJECT_ROOT / "data" / "sources.db"

SCHEMA = """
-- === FTS5 tables (prose — full-text search) ===

CREATE TABLE IF NOT EXISTS textbooks (
    id INTEGER PRIMARY KEY,
    chunk_id TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source_file TEXT NOT NULL DEFAULT '',
    grade TEXT DEFAULT '',
    author TEXT DEFAULT '',
    char_count INTEGER DEFAULT 0
);
CREATE VIRTUAL TABLE IF NOT EXISTS textbooks_fts USING fts5(
    title, text, content='textbooks', content_rowid='id', tokenize='unicode61'
);
CREATE TRIGGER IF NOT EXISTS textbooks_ai AFTER INSERT ON textbooks BEGIN
    INSERT INTO textbooks_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END;

CREATE TABLE IF NOT EXISTS external_articles (
    id INTEGER PRIMARY KEY,
    chunk_id TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    url_normalized TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source_file TEXT NOT NULL DEFAULT '',
    domain TEXT DEFAULT '',
    char_count INTEGER DEFAULT 0
);
CREATE VIRTUAL TABLE IF NOT EXISTS external_fts USING fts5(
    title, text, content='external_articles', content_rowid='id', tokenize='unicode61'
);
CREATE TRIGGER IF NOT EXISTS external_ai AFTER INSERT ON external_articles BEGIN
    INSERT INTO external_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END;
CREATE INDEX IF NOT EXISTS idx_ext_url ON external_articles(url);
CREATE INDEX IF NOT EXISTS idx_ext_url_norm ON external_articles(url_normalized);

CREATE TABLE IF NOT EXISTS literary_texts (
    id INTEGER PRIMARY KEY,
    chunk_id TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source_file TEXT NOT NULL DEFAULT '',
    author TEXT DEFAULT '',
    genre TEXT DEFAULT '',
    char_count INTEGER DEFAULT 0
);
CREATE VIRTUAL TABLE IF NOT EXISTS literary_fts USING fts5(
    title, text, content='literary_texts', content_rowid='id', tokenize='unicode61'
);
CREATE TRIGGER IF NOT EXISTS literary_ai AFTER INSERT ON literary_texts BEGIN
    INSERT INTO literary_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END;

-- === Standard indexed tables (dictionaries — headword lookup) ===

CREATE TABLE IF NOT EXISTS sum11 (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    definition TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_sum11_word ON sum11(word COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS grinchenko (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    definition TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_grinchenko_word ON grinchenko(word COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS balla_en_uk (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    definition TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_balla_word ON balla_en_uk(word COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS dmklinger_uk_en (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    pos TEXT DEFAULT '',
    translations TEXT DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_dmklinger_word ON dmklinger_uk_en(word COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS ukrajinet (
    id INTEGER PRIMARY KEY,
    synset_id TEXT DEFAULT '',
    words TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_ukrajinet_words ON ukrajinet(words COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS wiktionary (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    definitions TEXT DEFAULT '',
    synonyms TEXT DEFAULT '',
    antonyms TEXT DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_wiktionary_word ON wiktionary(word COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS frazeolohichnyi (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    definition TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_fraz_word ON frazeolohichnyi(word COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS puls_cefr (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    guideword TEXT DEFAULT '',
    level TEXT DEFAULT '',
    pos TEXT DEFAULT '',
    type TEXT DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_puls_word ON puls_cefr(word COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_puls_level ON puls_cefr(level);

CREATE TABLE IF NOT EXISTS style_guide (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    section TEXT DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_style_word ON style_guide(word COLLATE NOCASE);
"""


def _normalize_url(url: str) -> str:
    return url.replace("://www.", "://")


def _ingest_jsonl(conn: sqlite3.Connection, table: str, jsonl_path: Path,
                  columns: list[str], label: str) -> int:
    """Ingest a JSONL file into a table. Returns row count."""
    if not jsonl_path.exists():
        print(f"  ⚠️  Missing: {jsonl_path}")
        return 0
    placeholders = ", ".join("?" * len(columns))
    col_names = ", ".join(columns)
    sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
    batch: list[tuple] = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            row = tuple(
                json.dumps(v, ensure_ascii=False) if isinstance(v := entry.get(c, ""), (list, dict)) else v
                for c in columns
            )
            batch.append(row)
    if batch:
        conn.executemany(sql, batch)
    print(f"  📥 {label}: {len(batch)} entries")
    return len(batch)


def build(db_path: Path | None = None,
          external_dir: Path | None = None,
          textbook_dir: Path | None = None,
          gdrive_dir: Path | None = None) -> Path:
    """Build the unified sources database."""
    db = db_path or DB_PATH
    ext_dir = external_dir or EXTERNAL_DIR
    tb_dir = textbook_dir or (gdrive_dir or GDRIVE_DATA) / "textbook_chunks"
    gd = gdrive_dir or GDRIVE_DATA

    if db.exists():
        db.unlink()
        print(f"  🗑️  Removed existing {db.name}")

    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")
    conn.executescript(SCHEMA)

    total = 0

    # --- External articles ---
    print("\n📰 External articles")
    seen_urls: set[str] = set()
    ext_sql = """INSERT INTO external_articles
                 (chunk_id, url, url_normalized, title, text,
                  source_file, domain, char_count)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
    ext_files = sorted(ext_dir.glob("*.jsonl")) if ext_dir.exists() else []
    for jsonl_path in ext_files:
        source_file = jsonl_path.stem
        batch: list[tuple] = []
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
                batch.append((
                    f"ext-{source_file}-{len(batch)}",
                    url, _normalize_url(url),
                    entry.get("title", ""), entry.get("text", ""),
                    source_file, entry.get("domain", ""),
                    entry.get("char_count", len(entry.get("text", ""))),
                ))
        if batch:
            conn.executemany(ext_sql, batch)
        total += len(batch)
        print(f"  📥 {source_file}: {len(batch)} entries")

    # --- Textbook chunks ---
    print("\n📖 Textbooks")
    tb_sql = """INSERT INTO textbooks
                (chunk_id, title, text, source_file, grade, author, char_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)"""
    if tb_dir.exists():
        for grade_dir in sorted(tb_dir.glob("grade-*")):
            grade = grade_dir.name
            for jsonl_path in sorted(grade_dir.glob("*.jsonl")):
                source_file = jsonl_path.stem
                batch = []
                with open(jsonl_path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        entry = json.loads(line)
                        batch.append((
                            entry.get("chunk_id", f"tb-{source_file}-{len(batch)}"),
                            entry.get("section_title", ""),
                            entry.get("text", ""),
                            source_file,
                            entry.get("grade", grade),
                            entry.get("author", ""),
                            entry.get("token_count", len(entry.get("text", ""))),
                        ))
                if batch:
                    conn.executemany(tb_sql, batch)
                total += len(batch)
                print(f"  📖 {grade}/{source_file}: {len(batch)} chunks")

    # --- Literary texts ---
    print("\n📚 Literary texts")
    lit_dir = gd / "literary_texts"
    lit_sql = """INSERT INTO literary_texts
                 (chunk_id, title, text, source_file, author, char_count)
                 VALUES (?, ?, ?, ?, ?, ?)"""
    if lit_dir.exists():
        for jsonl_path in sorted(lit_dir.glob("*.jsonl")):
            source_file = jsonl_path.stem
            batch = []
            with open(jsonl_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    batch.append((
                        entry.get("chunk_id", f"lit-{source_file}-{len(batch)}"),
                        entry.get("section_title", entry.get("title", "")),
                        entry.get("text", ""),
                        source_file,
                        entry.get("author", ""),
                        len(entry.get("text", "")),
                    ))
            if batch:
                conn.executemany(lit_sql, batch)
            total += len(batch)
            print(f"  📚 {source_file}: {len(batch)} chunks")

    # --- Dictionaries ---
    print("\n📕 Dictionaries")
    total += _ingest_jsonl(conn, "sum11", gd / "sum11" / "chunks.jsonl",
                           ["word", "definition", "text", "source"], "СУМ-11")
    total += _ingest_jsonl(conn, "grinchenko", gd / "grinchenko" / "chunks.jsonl",
                           ["word", "definition", "source"], "Грінченко")
    total += _ingest_jsonl(conn, "balla_en_uk", gd / "balla-en-uk" / "chunks.jsonl",
                           ["word", "definition", "text", "source"], "Балла EN→UK")
    total += _ingest_jsonl(conn, "dmklinger_uk_en", gd / "dmklinger-uk-en" / "chunks.jsonl",
                           ["word", "pos", "translations", "text", "source"], "DMKlinger UK→EN")
    total += _ingest_jsonl(conn, "ukrajinet", gd / "ukrajinet" / "chunks.jsonl",
                           ["synset_id", "words", "text", "source"], "Ukrajinet WordNet")
    total += _ingest_jsonl(conn, "wiktionary", gd / "wiktionary" / "chunks.jsonl",
                           ["word", "definitions", "synonyms", "antonyms", "text", "source"],
                           "Wiktionary UK")
    total += _ingest_jsonl(conn, "frazeolohichnyi", gd / "frazeolohichnyi" / "chunks.jsonl",
                           ["word", "definition", "text", "source"], "Фразеологічний")
    total += _ingest_jsonl(conn, "style_guide", gd / "antonenko-davydovych" / "chunks.jsonl",
                           ["word", "section", "text", "source"], "Антоненко-Давидович")

    # --- CEFR vocabulary (local) ---
    total += _ingest_jsonl(conn, "puls_cefr", PROJECT_ROOT / "data" / "puls" / "entries.jsonl",
                           ["word", "guideword", "level", "pos", "type", "text", "source"],
                           "PULS CEFR")

    conn.commit()
    conn.execute("PRAGMA optimize")
    conn.close()

    db_size = db.stat().st_size / 1024 / 1024
    print(f"\n  ✅ Built {db.name}: {total:,} entries, {db_size:.1f} MB")
    return db


if __name__ == "__main__":
    print("🔨 Building unified sources database...")
    build()
