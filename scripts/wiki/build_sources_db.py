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
import os
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXTERNAL_DIR = PROJECT_ROOT / "data" / "external_articles"
DB_PATH = PROJECT_ROOT / "data" / "sources.db"
LOG_DIR = PROJECT_ROOT / "logs"

# File-size primary guard for `_db_is_populated()` — see #1563.
# A real populated sources.db is hundreds of MB to a few GB. A
# `sqlite3.connect()` on a fresh path creates a <1 KB file. Anything
# above this threshold is treated as populated regardless of whether
# COUNT(*) queries succeed, because the historical wipe failure mode
# was: COUNT errored transiently → populated returned False →
# `db.unlink()` ran without --force. Don't depend on opening sqlite
# to decide whether the file holds real data.
MIN_PROTECTED_DB_BYTES = 1 * 1024 * 1024  # 1 MB

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from wiki.config import GDRIVE_DATA
    from wiki.extract_sections import DEFAULT_REPORT_PATH, extract_sections
    from wiki.sources import build_literary_row
    from wiki.textbook_subjects import AUTHOR_UK_BY_TRANSLIT, subject_for_source_file
    from wiki.ukrainian_wiki_corpus import ensure_ukrainian_wiki_manifest, ensure_ukrainian_wiki_schema
else:
    from .config import GDRIVE_DATA
    from .extract_sections import DEFAULT_REPORT_PATH, extract_sections
    from .sources import build_literary_row
    from .textbook_subjects import AUTHOR_UK_BY_TRANSLIT, subject_for_source_file
    from .ukrainian_wiki_corpus import ensure_ukrainian_wiki_manifest, ensure_ukrainian_wiki_schema

SCHEMA = """
-- === FTS5 tables (prose — full-text search) ===

CREATE TABLE IF NOT EXISTS textbooks (
    id INTEGER PRIMARY KEY,
    chunk_id TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source_file TEXT NOT NULL DEFAULT '',
    -- subject: canonical ASCII slug from scripts/wiki/textbook_subjects.py.
    -- Used by search_text(subject=...) and back-filled by
    -- scripts/migrations/2026-07-06-add-subject-to-textbooks.py.
    subject TEXT DEFAULT '',
    grade TEXT DEFAULT '',
    author TEXT DEFAULT '',
    -- author_uk: canonical Cyrillic form of the author. Populated by
    -- ingestion or back-filled via scripts/migrations/2026-05-15-add-author-uk-to-textbooks.py.
    -- Matcher queries this column directly (Cyrillic-native).
    author_uk TEXT DEFAULT '',
    char_count INTEGER DEFAULT 0
);
CREATE VIRTUAL TABLE IF NOT EXISTS textbooks_fts USING fts5(
    title, text, content='textbooks', content_rowid='id', tokenize='unicode61'
);
CREATE TRIGGER IF NOT EXISTS textbooks_ai AFTER INSERT ON textbooks BEGIN
    INSERT INTO textbooks_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END;
CREATE INDEX IF NOT EXISTS idx_textbooks_subject ON textbooks(subject);

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
    source_url TEXT DEFAULT '',
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


def _enrich_author_uk(entry: dict, *, slug: str) -> dict:
    """Fill author_uk from the canonical mapping when extraction left it null."""
    author = str(entry.get("author") or "").strip()
    if author and not str(entry.get("author_uk") or "").strip():
        uk = AUTHOR_UK_BY_TRANSLIT.get(author.lower())
        if uk is None:
            from ingest.incremental_textbook_ingest import IngestError
            raise IngestError(
                f"{slug}: author {author!r} has no canonical Cyrillic form in "
                "AUTHOR_UK — add it (title-probed, never guessed) before ingest."
            )
        entry = {**entry, "author_uk": uk}
    return entry


def _build_textbook_row(
    entry: dict,
    *,
    source_file: str,
    grade: str,
    chunk_index: int,
) -> tuple:
    """Assemble a textbooks-table row tuple from a JSONL entry.

    Requires ``author_uk`` (canonical Cyrillic author form) in every entry
    that supplies a non-empty ``author``. Raises ``ValueError`` otherwise.
    The matcher in ``scripts/build/linear_pipeline.py`` queries
    ``author_uk`` directly — silently inserting rows with empty
    ``author_uk`` would break textbook citation resolution.
    """
    subject = subject_for_source_file(source_file)
    if subject is None:
        raise ValueError(
            f"Textbook source_file={source_file!r} has no canonical subject "
            "mapping. Add it to scripts/wiki/textbook_subjects.py before "
            "ingesting."
        )
    author = str(entry.get("author") or "").strip()
    author_uk = str(entry.get("author_uk") or "").strip()
    if author and not author_uk:
        raise ValueError(
            f"Textbook entry in {source_file} (chunk {chunk_index}) has "
            f"author={author!r} but no author_uk. Ingestion paths must "
            "supply the canonical Cyrillic author form. See ADR "
            "docs/decisions/2026-05-15-cyrillic-native-matcher.md."
        )
    return (
        entry.get("chunk_id", f"tb-{source_file}-{chunk_index}"),
        entry.get("section_title", ""),
        entry.get("text", ""),
        source_file,
        subject,
        entry.get("grade", grade),
        author,
        author_uk,
        entry.get("token_count", len(entry.get("text", ""))),
    )


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


def _ingest_external_articles(conn: sqlite3.Connection, ext_dir: Path) -> int:
    """Ingest data/external_articles/*.jsonl into the external_articles table.

    The external_articles schema has 16 columns; older blog JSONLs only
    populate (url, title, text, char_count). Newer audio/video JSONLs
    (e.g. ``pohribnyi_pronunciation``, future YT channels) also carry
    ``channel_id`` / ``speaker`` / ``video_id`` / ``publish_date`` /
    ``duration_s``.

    Channel-id policy:
    - Always derive ``channel_id`` from the JSONL filename stem (canonical
      identifier used by ``channels.yaml`` registry + retrieval filters).
      The filename stem wins over the per-record ``channel_id`` field,
      which can drift in punctuation between ingestion runs (Codex's
      2026-05-13 pohribnyi ingest wrote ``pohribnyi-pronunciation`` with
      a hyphen while the filename used an underscore — picking the
      filename keeps retrieval keys stable).
    - Audio/video metadata is surfaced when present; otherwise the fields
      stay empty / 0 so older blog rows are unchanged.

    Returns the count of rows inserted. URL dedup is per-call (a single
    ``seen_urls`` set across all JSONLs in this directory) to preserve the
    historical behaviour of the inline loop.

    See ``data/sources.db`` 2026-05-14 audit: all 1199 pre-existing rows
    had ``channel_id=''`` because the prior 8-column INSERT silently
    dropped the field.
    """
    ext_sql = """INSERT INTO external_articles
                 (chunk_id, url, url_normalized, title, text,
                  source_file, domain, char_count,
                  channel_id, speaker, video_id,
                  publish_date, duration_s)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    ext_files = sorted(ext_dir.glob("*.jsonl")) if ext_dir.exists() else []
    seen_urls: set[str] = set()
    total = 0
    for jsonl_path in ext_files:
        source_file = jsonl_path.stem
        channel_id = source_file  # canonical: filename stem is the channel id
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
                    channel_id,
                    entry.get("speaker", "") or "",
                    entry.get("video_id", "") or "",
                    entry.get("publish_date", "") or "",
                    entry.get("duration_s", 0) or 0,
                ))
        if batch:
            conn.executemany(ext_sql, batch)
        total += len(batch)
        print(f"  📥 {source_file}: {len(batch)} entries "
              f"(channel_id={channel_id!r})")
    return total



def _db_is_populated(db: Path) -> tuple[bool, int]:
    """True (plus row count) if the DB exists and has real content.

    File-size primary guard (#1563): if the file is larger than
    ``MIN_PROTECTED_DB_BYTES`` (1 MB), it is treated as populated even
    when the COUNT(*) queries fail or return 0. This guards against the
    failure mode that wiped data/sources.db on 2026-04-25: a transient
    SQLite error during the count caused this function to return
    (False, 0), which led `build()` to proceed without `--force` and
    `db.unlink()` the file. The file-size check is read directly from
    the filesystem and does not depend on opening sqlite.

    For files <1 MB, fall back to the original COUNT-based logic. A
    file that small is almost certainly a fresh `sqlite3.connect()`
    init or corruption — destructive rebuild without `--force` is the
    intended behavior.
    """
    if not db.exists():
        return False, 0

    # Primary guard: file size. Reading st_size doesn't open sqlite, so
    # it cannot trigger transient lock or I/O errors that mimic an empty DB.
    file_size = db.stat().st_size
    if file_size > MIN_PROTECTED_DB_BYTES:
        # Big file → real content. Try to count for a useful diagnostic
        # display, but do NOT let a sqlite error flip the verdict.
        total = 0
        try:
            conn = sqlite3.connect(str(db))
            for tbl in ("textbooks", "literary_texts", "external_articles"):
                with contextlib.suppress(sqlite3.OperationalError):
                    total += conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            conn.close()
        except sqlite3.Error:
            # Big file + sqlite error = high suspicion of real content
            # we just can't query right now. Fail closed: still populated.
            pass
        return True, total

    # File too small to plausibly hold real corpora. Trust the count and
    # treat any sqlite error as "not populated" (legacy behavior).
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


class BuildValidationError(RuntimeError):
    """Raised when a freshly-built temp DB fails validation before swap.

    Any raise of this (or anything else) during the build must leave the
    live DB untouched — see the temp-DB + atomic-swap design in
    ``build()`` (#4859).
    """


def _validate_build(conn: sqlite3.Connection, expected_counts: dict[str, int]) -> None:
    """Validate a freshly-built temp DB before it is allowed to replace the live one.

    Checks (#4859 acceptance criteria):
    - Row counts for every table we just populated match what the
      ingestion loop actually counted.
    - ``PRAGMA integrity_check`` passes.
    - Every FTS5 content-linked table's shadow index matches its source
      table (the ``integrity-check`` command — raises on mismatch).
    """
    for table, expected in expected_counts.items():
        actual = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if actual != expected:
            raise BuildValidationError(
                f"{table} has {actual} rows, expected {expected} from ingestion"
            )

    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise BuildValidationError(f"PRAGMA integrity_check returned {integrity!r}")

    for fts_table in ("textbooks_fts", "external_fts", "literary_fts", "wikipedia_fts"):
        conn.execute(f"INSERT INTO {fts_table}({fts_table}) VALUES ('integrity-check')")


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

    Failure-atomicity (#4859): the rebuild is ingested and validated in a
    sibling temp file next to `db_path` (same filesystem, so the final
    swap is a single atomic `Path.replace()`). The live `db_path` is never
    unlinked, truncated, or otherwise touched until that temp file has
    passed validation — any exception raised while ingesting, extracting
    sections, or validating leaves the pre-existing `db_path` (and its
    WAL/SHM sidecars, if any) exactly as it was; only the temp file and
    its own sidecars are discarded.
    """
    db = db_path or DB_PATH
    ext_dir = external_dir or EXTERNAL_DIR
    tb_dir = textbook_dir or (gdrive_dir or GDRIVE_DATA) / "textbook_chunks"
    gd = gdrive_dir or GDRIVE_DATA

    populated, total = _db_is_populated(db)
    if populated and not force:
        # Use file size as the primary diagnostic — `total` may be 0 when
        # the file is large but the main-table COUNT query errored
        # transiently (the #1563 failure mode). File size doesn't lie.
        size_mb = db.stat().st_size / (1024 * 1024) if db.exists() else 0.0
        print(
            f"  ⚠️  {db.name} already populated "
            f"({size_mb:,.1f} MB on disk, {total:,} rows across main tables)."
        )
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

    # Snapshot wikipedia data BEFORE touching anything on disk. `db` is
    # not modified until the validated atomic swap at the end, so this
    # read against the live file is always safe.
    wiki_rows: list[tuple] = []
    neg_rows: list[tuple] = []
    if preserve_wiki:
        wiki_rows, neg_rows = _extract_wikipedia_snapshot(db)
        if wiki_rows or neg_rows:
            print(f"  💾 Preserving wikipedia snapshot: "
                  f"{len(wiki_rows)} articles, {len(neg_rows)} negative-cache entries")

    db.parent.mkdir(parents=True, exist_ok=True)

    # Build + validate into a sibling temp file on the same filesystem as
    # `db` so the final swap is one atomic rename (#4859). Nothing below
    # this point may touch `db` itself until validation passes.
    tmp_fd, tmp_name = tempfile.mkstemp(dir=db.parent, prefix=f".{db.name}.", suffix=".building")
    os.close(tmp_fd)
    tmp_db = Path(tmp_name)

    def _cleanup_tmp() -> None:
        for path in (tmp_db, tmp_db.parent / f"{tmp_db.name}-wal", tmp_db.parent / f"{tmp_db.name}-shm"):
            if path.exists():
                path.unlink()

    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(str(tmp_db))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=OFF")
        # No FOREIGN KEY constraints exist in SCHEMA or UKRAINIAN_WIKI_SCHEMA
        # today (#4859 audit), so this is currently a no-op — set anyway so
        # any FK added later is enforced by default rather than silently
        # ignored (SQLite defaults foreign_keys OFF per-connection).
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(SCHEMA)
        ensure_ukrainian_wiki_schema(conn)

        expected_counts: dict[str, int] = {
            "wikipedia": len(wiki_rows),
            "wikipedia_negative_cache": len(neg_rows),
        }
        if preserve_wiki and (wiki_rows or neg_rows):
            _restore_wikipedia_snapshot(conn, wiki_rows, neg_rows)
            conn.commit()
            print(f"  ✅ Restored {len(wiki_rows)} wikipedia articles + "
                  f"{len(neg_rows)} negative-cache entries")

        total = 0

        # --- External articles ---
        print("\n📰 External articles")
        expected_counts["external_articles"] = _ingest_external_articles(conn, ext_dir)
        total += expected_counts["external_articles"]

        # --- Textbook chunks ---
        print("\n📖 Textbooks")
        tb_sql = """INSERT INTO textbooks
                    (chunk_id, title, text, source_file, subject, grade, author,
                     author_uk, char_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        tb_total = 0
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
                            entry = _enrich_author_uk(entry, slug=source_file)
                            batch.append(_build_textbook_row(
                                entry,
                                source_file=source_file,
                                grade=grade,
                                chunk_index=len(batch),
                            ))
                    if batch:
                        conn.executemany(tb_sql, batch)
                    tb_total += len(batch)
                    print(f"  📖 {grade}/{source_file}: {len(batch)} chunks")
        expected_counts["textbooks"] = tb_total
        total += tb_total

        # --- Literary texts ---
        print("\n📚 Literary texts")
        lit_dir = gd / "literary_texts"
        lit_sql = """INSERT INTO literary_texts
                     (chunk_id, title, text, source_file, source_url, author, work, work_id,
                      year, genre, language_period, char_count)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        lit_total = 0
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
                lit_total += len(batch)
                print(f"  📚 {source_file}: {len(batch)} chunks")
        expected_counts["literary_texts"] = lit_total
        total += lit_total

        # --- Dictionaries ---
        print("\n📕 Dictionaries")
        expected_counts["sum11"] = _ingest_jsonl(
            conn, "sum11", gd / "sum11" / "chunks.jsonl",
            ["word", "definition", "text", "source"], "СУМ-11")
        expected_counts["grinchenko"] = _ingest_jsonl(
            conn, "grinchenko", gd / "grinchenko" / "chunks.jsonl",
            ["word", "definition", "source"], "Грінченко")
        expected_counts["balla_en_uk"] = _ingest_jsonl(
            conn, "balla_en_uk", gd / "balla-en-uk" / "chunks.jsonl",
            ["word", "definition", "text", "source"], "Балла EN→UK")
        expected_counts["dmklinger_uk_en"] = _ingest_jsonl(
            conn, "dmklinger_uk_en", gd / "dmklinger-uk-en" / "chunks.jsonl",
            ["word", "pos", "translations", "text", "source"], "DMKlinger UK→EN")
        expected_counts["ukrajinet"] = _ingest_jsonl(
            conn, "ukrajinet", gd / "ukrajinet" / "chunks.jsonl",
            ["synset_id", "words", "text", "source"], "Ukrajinet WordNet")
        expected_counts["wiktionary"] = _ingest_jsonl(
            conn, "wiktionary", gd / "wiktionary" / "chunks.jsonl",
            ["word", "definitions", "synonyms", "antonyms", "text", "source"],
            "Wiktionary UK")
        expected_counts["frazeolohichnyi"] = _ingest_jsonl(
            conn, "frazeolohichnyi", gd / "frazeolohichnyi" / "chunks.jsonl",
            ["word", "definition", "text", "source"], "Фразеологічний")
        expected_counts["style_guide"] = _ingest_jsonl(
            conn, "style_guide", gd / "antonenko-davydovych" / "chunks.jsonl",
            ["word", "section", "text", "source"], "Антоненко-Давидович")

        # --- CEFR vocabulary (local) ---
        expected_counts["puls_cefr"] = _ingest_jsonl(
            conn, "puls_cefr", PROJECT_ROOT / "data" / "puls" / "entries.jsonl",
            ["word", "guideword", "level", "pos", "type", "text", "source"],
            "PULS CEFR")

        for key in ("sum11", "grinchenko", "balla_en_uk", "dmklinger_uk_en",
                    "ukrajinet", "wiktionary", "frazeolohichnyi", "style_guide",
                    "puls_cefr"):
            total += expected_counts[key]

        conn.commit()
        literary_report = format_literary_validation_report(conn)
        report_path = write_literary_validation_report(literary_report)
        print(f"\n{literary_report}")
        print(f"\n  📝 Validation report: {report_path}")

        # Row-count + schema + FTS integrity validation BEFORE this temp
        # DB is allowed anywhere near the live path (#4859 acceptance).
        _validate_build(conn, expected_counts)
        # The FTS integrity-check command is syntactically an INSERT, so
        # Python's sqlite3 module opened an implicit transaction for it —
        # commit before switching journal mode (SQLite refuses to change
        # out of WAL mode from within an open transaction).
        conn.commit()

        # Fold the WAL back into the main file and drop back to DELETE
        # journal mode so the temp DB is a single self-contained file with
        # no sidecars to carry across the swap.
        conn.execute("PRAGMA journal_mode=DELETE")
        conn.execute("PRAGMA optimize")
        conn.close()
        conn = None

        section_report = extract_sections(tmp_db, report_path=DEFAULT_REPORT_PATH)
        print("\n🧩 Textbook section extraction")
        print(
            "  ✅ Extracted "
            f"{len(section_report.sections)} sections from {section_report.total_chunks:,} chunks; "
            f"assigned {section_report.assigned_chunks:,} ({section_report.assigned_rate:.2%}), "
            f"unassigned {section_report.unassigned_chunks:,} ({section_report.unassigned_rate:.2%})"
        )
        print(f"  📝 Validation report: {DEFAULT_REPORT_PATH}")
    except BaseException:
        if conn is not None:
            with contextlib.suppress(sqlite3.Error):
                conn.close()
        _cleanup_tmp()
        raise

    # Validated — atomically replace the live DB. `db` and its sidecars
    # are untouched up to this point; the old sidecars are dropped only
    # now, immediately before the rename, so a crash here can at worst
    # leave a stray `.building` temp file (harmless — never mistaken for
    # a live DB, and cleaned up by the next successful build) rather than
    # a half-written live DB.
    try:
        for sidecar in (db.parent / f"{db.name}-wal", db.parent / f"{db.name}-shm"):
            if sidecar.exists():
                sidecar.unlink()
        tmp_db.replace(db)
    except BaseException:
        _cleanup_tmp()
        raise
    print(f"  🔁 Atomically replaced {db.name} with the validated rebuild")

    db_size = db.stat().st_size / 1024 / 1024
    ensure_ukrainian_wiki_manifest(PROJECT_ROOT / "data" / "embeddings" / "manifest.db")
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
