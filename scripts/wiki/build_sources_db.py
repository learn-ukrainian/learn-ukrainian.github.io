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
    # Preview what would happen (no destructive action)
    .venv/bin/python scripts/wiki/build_sources_db.py --dry-run

    # First-time build (no existing DB) — allowed unconditionally
    .venv/bin/python scripts/wiki/build_sources_db.py

    # Rebuild an existing populated DB — requires --force
    .venv/bin/python scripts/wiki/build_sources_db.py --force

    # Rebuild + wipe the wikipedia table too (destructive, rare)
    .venv/bin/python scripts/wiki/build_sources_db.py --force --no-preserve-wiki

By default, `--force` rebuilds everything EXCEPT the wikipedia and
wikipedia_negative_cache tables — those are populated separately by
scripts/wiki/fetch_wikipedia.py and are expensive to refetch (Wikipedia
API rate-limits). Pass --no-preserve-wiki to opt out of the preservation.
"""

import argparse
import contextlib
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GDRIVE_DATA = (
    Path.home()
    / "Library/CloudStorage/GoogleDrive-krisztian.koos@gmail.com"
    / "My Drive/Projects/learn-ukrainian-data"
)
EXTERNAL_DIR = PROJECT_ROOT / "data" / "external_articles"
DB_PATH = PROJECT_ROOT / "data" / "sources.db"
LOG_DIR = PROJECT_ROOT / "logs"

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from wiki.extract_sections import DEFAULT_REPORT_PATH, extract_sections
    from wiki.sources import build_literary_row
else:
    from .extract_sections import DEFAULT_REPORT_PATH, extract_sections
    from .sources import build_literary_row

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
    char_count INTEGER DEFAULT 0,
    channel_id TEXT DEFAULT '',
    speaker TEXT DEFAULT '',
    register_tag TEXT DEFAULT '',
    decolonization_tag TEXT DEFAULT '',
    quality_tier INTEGER DEFAULT 2,
    publish_date TEXT DEFAULT '',
    duration_s INTEGER DEFAULT 0,
    chunk_start_ts INTEGER,
    chunk_end_ts INTEGER,
    video_id TEXT DEFAULT ''
);
CREATE VIRTUAL TABLE IF NOT EXISTS external_fts USING fts5(
    title, text, speaker, content='external_articles', content_rowid='id', tokenize='unicode61'
);
CREATE TRIGGER IF NOT EXISTS external_ai AFTER INSERT ON external_articles BEGIN
    INSERT INTO external_fts(rowid, title, text, speaker)
    VALUES (new.id, new.title, new.text, new.speaker);
END;
CREATE INDEX IF NOT EXISTS idx_ext_url ON external_articles(url);
CREATE INDEX IF NOT EXISTS idx_ext_url_norm ON external_articles(url_normalized);
CREATE INDEX IF NOT EXISTS idx_ext_channel ON external_articles(channel_id);
CREATE INDEX IF NOT EXISTS idx_ext_quality ON external_articles(quality_tier);

CREATE TABLE IF NOT EXISTS literary_texts (
    id INTEGER PRIMARY KEY,
    chunk_id TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source_file TEXT NOT NULL DEFAULT '',
    author TEXT DEFAULT '',
    work TEXT DEFAULT '',
    work_id TEXT DEFAULT '',
    year INTEGER,
    genre TEXT DEFAULT '',
    language_period TEXT DEFAULT '',
    char_count INTEGER DEFAULT 0
);
CREATE VIRTUAL TABLE IF NOT EXISTS literary_fts USING fts5(
    title, text, content='literary_texts', content_rowid='id', tokenize='unicode61'
);
CREATE TRIGGER IF NOT EXISTS literary_ai AFTER INSERT ON literary_texts BEGIN
    INSERT INTO literary_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END;
CREATE INDEX IF NOT EXISTS idx_literary_period ON literary_texts(language_period);
CREATE INDEX IF NOT EXISTS idx_literary_work_id ON literary_texts(work_id);
CREATE INDEX IF NOT EXISTS idx_literary_period_genre ON literary_texts(language_period, genre);

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

-- === Wikipedia passthrough (populated by scripts/wiki/fetch_wikipedia.py) ===
--
-- These tables own the Wikipedia cache that the MCP sources server queries
-- for wiki enrichment. build_sources_db.py creates the schema here so a
-- rebuild produces a DB that fetch_wikipedia.py can populate — AND so
-- that --force rebuilds (with preserve_wiki=True) can snapshot and
-- restore the rows across the destroy/recreate cycle.

CREATE TABLE IF NOT EXISTS wikipedia (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    char_count INTEGER DEFAULT 0,
    fetched_at TEXT NOT NULL DEFAULT ''
);
CREATE VIRTUAL TABLE IF NOT EXISTS wikipedia_fts USING fts5(
    title, text, content='wikipedia', content_rowid='id', tokenize='unicode61'
);
CREATE TRIGGER IF NOT EXISTS wikipedia_ai AFTER INSERT ON wikipedia BEGIN
    INSERT INTO wikipedia_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END;
CREATE INDEX IF NOT EXISTS idx_wiki_title ON wikipedia(title);

CREATE TABLE IF NOT EXISTS wikipedia_negative_cache (
    topic TEXT PRIMARY KEY,
    tried_at TEXT NOT NULL DEFAULT ''
);
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


def _db_is_populated(db: Path) -> tuple[bool, int]:
    """True (plus row count) if the DB exists and has any rows in the
    main content tables. Returns (False, 0) for missing/empty DBs.
    """
    if not db.exists():
        return False, 0
    try:
        conn = sqlite3.connect(str(db))
        total = 0
        for tbl in ("textbooks", "literary_texts", "external_articles"):
            with contextlib.suppress(sqlite3.OperationalError):
                total += conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        conn.close()
        return total > 0, total
    except sqlite3.Error:
        return False, 0


def _extract_wikipedia_snapshot(db: Path) -> tuple[list[tuple], list[tuple]]:
    """Read all rows from wikipedia + wikipedia_negative_cache tables,
    returning them as list-of-tuples so we can re-insert after rebuild.
    Returns ([], []) if the tables don't exist or the DB is missing.
    """
    if not db.exists():
        return [], []
    try:
        conn = sqlite3.connect(str(db))
        wiki_rows: list[tuple] = []
        neg_rows: list[tuple] = []
        with contextlib.suppress(sqlite3.OperationalError):
            wiki_rows = list(conn.execute(
                "SELECT title, url, text, char_count, fetched_at FROM wikipedia"
            ))
        with contextlib.suppress(sqlite3.OperationalError):
            neg_rows = list(conn.execute(
                "SELECT topic, tried_at FROM wikipedia_negative_cache"
            ))
        conn.close()
        return wiki_rows, neg_rows
    except sqlite3.Error:
        return [], []


def _restore_wikipedia_snapshot(conn: sqlite3.Connection,
                                 wiki_rows: list[tuple],
                                 neg_rows: list[tuple]) -> None:
    """Re-insert wikipedia + negative cache rows into a freshly-built DB."""
    if wiki_rows:
        conn.executemany(
            """INSERT INTO wikipedia (title, url, text, char_count, fetched_at)
               VALUES (?, ?, ?, ?, ?)""",
            wiki_rows,
        )
    if neg_rows:
        conn.executemany(
            "INSERT OR IGNORE INTO wikipedia_negative_cache (topic, tried_at) VALUES (?, ?)",
            neg_rows,
        )


def format_literary_validation_report(conn: sqlite3.Connection) -> str:
    """Return the AC5 literary metadata validation report."""
    period_counts = dict(
        conn.execute(
            """
            SELECT language_period, COUNT(*)
            FROM literary_texts
            GROUP BY language_period
            ORDER BY language_period
            """
        ).fetchall()
    )
    work_id_count = conn.execute(
        "SELECT COUNT(DISTINCT work_id) FROM literary_texts"
    ).fetchone()[0]

    lines = ["Literary metadata validation report"]
    for period, count in period_counts.items():
        lines.append(f"{period}: {count}")
    lines.append(f"total: {sum(period_counts.values())}")
    lines.append(f"distinct work_id: {work_id_count}")
    return "\n".join(lines)


def write_literary_validation_report(report: str) -> Path:
    """Persist the AC5 literary metadata validation report under logs/."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    report_path = LOG_DIR / f"literary_metadata_restore_{datetime.now().strftime('%Y%m%d')}.txt"
    report_path.write_text(report + "\n", encoding="utf-8")
    return report_path


def build(db_path: Path | None = None,
          external_dir: Path | None = None,
          textbook_dir: Path | None = None,
          gdrive_dir: Path | None = None,
          *,
          force: bool = False,
          dry_run: bool = False,
          preserve_wiki: bool = True) -> Path:
    """Build the unified sources database.

    Safety:
    - If the DB exists and is populated, requires `force=True` to proceed.
      Without it, prints the row count and exits without touching anything.
    - `dry_run=True` stops after the safety check and prints the plan.
    - `preserve_wiki=True` (default) snapshots the wikipedia +
      wikipedia_negative_cache tables before dropping the DB and re-inserts
      them into the fresh schema — wikipedia API data is expensive to
      refetch.
    """
    db = db_path or DB_PATH
    ext_dir = external_dir or EXTERNAL_DIR
    tb_dir = textbook_dir or (gdrive_dir or GDRIVE_DATA) / "textbook_chunks"
    gd = gdrive_dir or GDRIVE_DATA

    populated, total = _db_is_populated(db)
    if populated and not force:
        print(f"  ⚠️  {db.name} already populated ({total:,} rows across main tables).")
        print("     Refusing to destroy it without --force. Use:")
        print("       .venv/bin/python scripts/wiki/build_sources_db.py --force")
        print("     or add --dry-run to preview what would happen.")
        return db

    if dry_run:
        print(f"  🔍 DRY RUN: would rebuild {db.name}")
        if populated:
            print(f"     existing populated DB: {total:,} rows")
        else:
            print("     no existing populated DB (fresh build)")
        print(f"     sources: {ext_dir}, {tb_dir}, {gd}")
        print(f"     preserve wikipedia: {preserve_wiki}")
        return db

    # Snapshot wikipedia data BEFORE destroying the DB
    wiki_rows: list[tuple] = []
    neg_rows: list[tuple] = []
    if preserve_wiki:
        wiki_rows, neg_rows = _extract_wikipedia_snapshot(db)
        if wiki_rows or neg_rows:
            print(f"  💾 Preserving wikipedia snapshot: "
                  f"{len(wiki_rows)} articles, {len(neg_rows)} negative-cache entries")

    if db.exists():
        db.unlink()
        # Also drop stale WAL/SHM sidecars that can cause SQLite I/O errors
        # on the freshly-created DB (seen in practice: rebuilding right
        # after a restore would fail at executescript() with 'disk I/O
        # error' because the old .db-wal was still present).
        for sidecar in (db.parent / f"{db.name}-wal", db.parent / f"{db.name}-shm"):
            if sidecar.exists():
                sidecar.unlink()
        print(f"  🗑️  Removed existing {db.name} (+ WAL/SHM sidecars)")

    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")
    conn.executescript(SCHEMA)

    if preserve_wiki and (wiki_rows or neg_rows):
        _restore_wikipedia_snapshot(conn, wiki_rows, neg_rows)
        conn.commit()
        print(f"  ✅ Restored {len(wiki_rows)} wikipedia articles + "
              f"{len(neg_rows)} negative-cache entries")

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
                 (chunk_id, title, text, source_file, author, work, work_id,
                  year, genre, language_period, char_count)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    if lit_dir.exists():
        for jsonl_path in sorted(lit_dir.glob("*.jsonl")):
            source_file = jsonl_path.stem
            batch: list[tuple] = []
            with open(jsonl_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    batch.append(
                        build_literary_row(
                            entry,
                            source_file=source_file,
                            chunk_index=len(batch),
                            warn=print,
                        )
                    )
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
    literary_report = format_literary_validation_report(conn)
    report_path = write_literary_validation_report(literary_report)
    print(f"\n{literary_report}")
    print(f"\n  📝 Validation report: {report_path}")
    conn.execute("PRAGMA optimize")
    conn.close()

    section_report = extract_sections(db, report_path=DEFAULT_REPORT_PATH)
    print("\n🧩 Textbook section extraction")
    print(
        "  ✅ Extracted "
        f"{len(section_report.sections)} sections from {section_report.total_chunks:,} chunks; "
        f"assigned {section_report.assigned_chunks:,} ({section_report.assigned_rate:.2%}), "
        f"unassigned {section_report.unassigned_chunks:,} ({section_report.unassigned_rate:.2%})"
    )
    print(f"  📝 Validation report: {DEFAULT_REPORT_PATH}")

    db_size = db.stat().st_size / 1024 / 1024
    print(f"\n  ✅ Built {db.name}: {total:,} entries, {db_size:.1f} MB")
    return db


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the unified sources.db (textbooks + literary + "
                    "dictionaries + wikipedia passthrough).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "By default, refuses to destroy an existing populated DB. "
            "Use --force to rebuild. --dry-run shows the plan without "
            "touching anything. --no-preserve-wiki also wipes the "
            "wikipedia table (use sparingly — refetching is slow)."
        ),
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Destroy and rebuild an existing populated DB. Required when "
             "sources.db already has rows in textbooks/literary_texts/"
             "external_articles.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the plan without touching the filesystem or the DB.",
    )
    parser.add_argument(
        "--no-preserve-wiki", action="store_true",
        help="Also wipe the wikipedia and wikipedia_negative_cache tables. "
             "Default is to snapshot and restore them across the rebuild.",
    )
    parser.add_argument(
        "--db-path", type=Path, default=None,
        help="Override the default data/sources.db path (testing only).",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    print("🔨 Building unified sources database...")
    result = build(
        db_path=args.db_path,
        force=args.force,
        dry_run=args.dry_run,
        preserve_wiki=not args.no_preserve_wiki,
    )
    if args.dry_run:
        sys.exit(0)
    # If the build was refused for safety (not forced, DB populated),
    # exit with code 2 so scripts calling this in CI notice.
    populated, _ = _db_is_populated(result)
    if populated and not args.force:
        sys.exit(2)
