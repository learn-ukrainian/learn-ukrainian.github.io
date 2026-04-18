#!/usr/bin/env python3
"""Re-ingest the external articles corpus into chunked SQLite rows."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from wiki.channels import load_channels

DB_PATH = PROJECT_ROOT / "data" / "sources.db"
EXTERNAL_DIR = PROJECT_ROOT / "data" / "external_articles"
CHANNELS_PATH = EXTERNAL_DIR / "channels.yaml"

TARGET_CHARS = 2000
OVERLAP_CHARS = 200
VERIFY_QUERIES = ("козаки", "мова", "Україна")

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

INSERT_COLUMNS = [
    "chunk_id",
    "url",
    "url_normalized",
    "title",
    "text",
    "source_file",
    "domain",
    "char_count",
    "channel_id",
    "speaker",
    "register_tag",
    "decolonization_tag",
    "quality_tier",
    "publish_date",
    "duration_s",
    "chunk_start_ts",
    "chunk_end_ts",
    "video_id",
]

_PARAGRAPH_BREAK_RE = re.compile(r"\n\s*\n")
_SENTENCE_BREAK_RE = re.compile(r"[.!?…][\"'»”)]?\s+")


def normalize_url(url: str) -> str:
    return url.replace("://www.", "://")


def normalize_text(text: str) -> str:
    """Normalize whitespace while keeping paragraph structure."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00A0", " ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    normalized_lines: list[str] = []
    blank_pending = False
    for line in lines:
        if not line:
            blank_pending = True
            continue
        if blank_pending and normalized_lines:
            normalized_lines.append("")
        normalized_lines.append(line)
        blank_pending = False
    return "\n".join(normalized_lines).strip()


def ensure_external_schema(conn: sqlite3.Connection) -> list[str]:
    """Add the enriched external_articles columns and rebuild external FTS.

    Idempotent against three states: (a) fully-populated DB from a prior
    migration run, (b) baseline DB with the original columns only, and
    (c) **fresh-clone DB where the table doesn't exist at all** — Gemini
    review #354 (#1324) flagged that the previous ``ALTER TABLE`` loop
    would crash on (c). Mirror the canonical schema from
    ``scripts/wiki/build_sources_db.py`` so the migration self-bootstraps.
    """
    conn.execute(
        """
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
        )
        """
    )

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

    _ensure_external_fts(conn)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ext_url ON external_articles(url)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ext_url_norm ON external_articles(url_normalized)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ext_channel ON external_articles(channel_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ext_quality ON external_articles(quality_tier)")
    return added


def _ensure_external_fts(conn: sqlite3.Connection) -> bool:
    """Create or repair the external FTS table/trigger only when needed."""
    fts_columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(external_fts)").fetchall()
    }
    has_expected_fts = fts_columns == {"title", "text", "speaker"}
    has_trigger = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='trigger' AND name='external_ai'"
    ).fetchone() is not None

    if has_expected_fts and has_trigger:
        return False

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
    conn.execute("INSERT INTO external_fts(external_fts) VALUES ('rebuild')")
    return True


def _last_boundary(regex: re.Pattern[str], text: str) -> int | None:
    matches = list(regex.finditer(text))
    if not matches:
        return None
    return matches[-1].end()


def _last_whitespace_before(text: str, limit: int) -> int | None:
    idx = limit
    while idx > 0:
        if text[idx - 1].isspace():
            return idx
        idx -= 1
    return None


def _first_whitespace_after(text: str, limit: int) -> int | None:
    idx = limit
    while idx < len(text):
        if text[idx].isspace():
            return idx + 1
        idx += 1
    return None


def _find_split_point(text: str, target_chars: int) -> int:
    if len(text) <= target_chars:
        return len(text)

    window = text[:target_chars + 1]
    lower_bound = int(target_chars * 0.6)

    paragraph_split = _last_boundary(_PARAGRAPH_BREAK_RE, window)
    if paragraph_split is not None and paragraph_split >= lower_bound:
        return paragraph_split

    sentence_split = _last_boundary(_SENTENCE_BREAK_RE, window)
    if sentence_split is not None and sentence_split >= lower_bound:
        return sentence_split

    word_split = _last_whitespace_before(window, target_chars)
    if word_split is not None and word_split >= int(target_chars * 0.5):
        return word_split

    word_split = _first_whitespace_after(text, target_chars)
    if word_split is not None:
        return word_split

    return len(text)


def _split_main_chunks(text: str, target_chars: int = TARGET_CHARS) -> list[str]:
    remaining = normalize_text(text)
    if not remaining:
        return []

    chunks: list[str] = []
    while remaining:
        if len(remaining) <= target_chars:
            chunks.append(remaining.strip())
            break

        split_at = _find_split_point(remaining, target_chars)
        chunk = remaining[:split_at].strip()
        if not chunk:
            chunk = remaining.strip()
            chunks.append(chunk)
            break

        chunks.append(chunk)
        remaining = remaining[split_at:].lstrip()

    return [chunk for chunk in chunks if chunk]


def _overlap_prefix(previous_chunk: str, overlap_chars: int = OVERLAP_CHARS) -> str:
    if not previous_chunk or overlap_chars <= 0:
        return ""
    if len(previous_chunk) <= overlap_chars:
        return previous_chunk

    start = len(previous_chunk) - overlap_chars
    while start < len(previous_chunk):
        prev_char = previous_chunk[start - 1] if start > 0 else " "
        curr_char = previous_chunk[start]
        if not (prev_char.isalnum() and curr_char.isalnum()):
            break
        start += 1
    return previous_chunk[start:].lstrip()


def chunk_text(
    text: str,
    *,
    target_chars: int = TARGET_CHARS,
    overlap_chars: int = OVERLAP_CHARS,
    preserve_small: bool = False,
) -> list[str]:
    """Split text into ~2K chunks with overlap, preferring paragraph/sentence cuts."""
    normalized = normalize_text(text)
    if not normalized:
        return []
    if preserve_small:
        return [normalized]

    main_chunks = _split_main_chunks(normalized, target_chars=target_chars)
    if not main_chunks:
        return []

    chunks = [main_chunks[0]]
    for previous, current in itertools.pairwise(main_chunks):
        overlap = _overlap_prefix(previous, overlap_chars=overlap_chars)
        if overlap:
            chunks.append(f"{overlap}\n\n{current}")
        else:
            chunks.append(current)
    return chunks


def extract_video_id(url: str) -> str:
    """Extract a stable video/article identifier from a URL."""
    parsed = urlparse(url)
    if "youtube.com" in parsed.netloc:
        values = parse_qs(parsed.query).get("v")
        if values:
            return values[0]
    if parsed.netloc == "youtu.be":
        slug = parsed.path.strip("/")
        if slug:
            return slug
    return hashlib.sha1(normalize_url(url).encode("utf-8")).hexdigest()[:12]


def _iter_jsonl_items(
    data_dir: Path,
    channels: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str], int, int]:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    input_count = 0
    deduped_count = 0
    # Dedup by normalized URL only (NOT (source_file, url)). Gemini review
    # #354 (#1324) flagged that the original tuple key let identical URLs
    # appearing in differently-named JSONL files (e.g., the historical
    # Latin- vs Cyrillic-named exports of the same channel) bypass
    # deduplication. The collision risk is also low because URLs in our
    # corpus are channel-scoped by domain.
    seen_urls: set[str] = set()

    for jsonl_path in sorted(data_dir.glob("*.jsonl")):
        source_file = jsonl_path.stem
        channel = channels.get(source_file)
        if channel is None:
            failures.append(f"{jsonl_path.name}: missing channel registry entry")
            continue

        with jsonl_path.open(encoding="utf-8") as handle:
            for lineno, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                input_count += 1
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError as exc:
                    failures.append(f"{jsonl_path.name}:{lineno}: {exc.msg}")
                    continue

                url = str(entry.get("url", "")).strip()
                title = str(entry.get("title", "")).strip()
                text = str(entry.get("text", "")).strip()
                if not url or not text:
                    failures.append(f"{jsonl_path.name}:{lineno}: missing url/text")
                    continue

                dedupe_key = normalize_url(url)
                if dedupe_key in seen_urls:
                    deduped_count += 1
                    continue
                seen_urls.add(dedupe_key)

                video_id = extract_video_id(url)
                chunks = chunk_text(
                    text,
                    target_chars=TARGET_CHARS,
                    overlap_chars=OVERLAP_CHARS,
                    preserve_small=(source_file == "ulp_blogs"),
                )
                if not chunks:
                    failures.append(f"{jsonl_path.name}:{lineno}: empty normalized text")
                    continue

                domain = str(entry.get("domain", "")).strip() or urlparse(url).netloc
                for chunk_idx, chunk in enumerate(chunks):
                    rows.append({
                        "chunk_id": f"ext-{source_file}-{video_id}-{chunk_idx:03d}",
                        "url": url,
                        "url_normalized": normalize_url(url),
                        "title": title,
                        "text": chunk,
                        "source_file": source_file,
                        "domain": domain,
                        "char_count": len(chunk),
                        "channel_id": source_file,
                        "speaker": str(channel["host"]).strip(),
                        "register_tag": str(channel["register_tag"]).strip(),
                        "decolonization_tag": str(channel["decolonization_tag"]).strip(),
                        "quality_tier": int(channel["quality_tier"]),
                        "publish_date": "",
                        "duration_s": 0,
                        "chunk_start_ts": None,
                        "chunk_end_ts": None,
                        "video_id": video_id,
                    })

    return rows, failures, input_count, deduped_count


def _insert_rows(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    placeholders = ", ".join("?" for _ in INSERT_COLUMNS)
    sql = f"INSERT INTO external_articles ({', '.join(INSERT_COLUMNS)}) VALUES ({placeholders})"
    batch = [tuple(row[column] for column in INSERT_COLUMNS) for row in rows]
    conn.executemany(sql, batch)


def _row_tuple(row: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(row[column] for column in INSERT_COLUMNS)


def _existing_row_tuples(conn: sqlite3.Connection) -> list[tuple[Any, ...]]:
    sql = f"SELECT {', '.join(INSERT_COLUMNS)} FROM external_articles ORDER BY chunk_id"
    return [tuple(row) for row in conn.execute(sql).fetchall()]


def _verify_roundtrip(conn: sqlite3.Connection) -> dict[str, list[str]]:
    results: dict[str, list[str]] = {}
    for query in VERIFY_QUERIES:
        fts_query = " ".join(f'"{token}"' for token in query.split())
        rows = conn.execute(
            """SELECT s.chunk_id, s.title
               FROM external_fts
               JOIN external_articles s ON s.id = external_fts.rowid
               WHERE external_fts MATCH ?
               ORDER BY bm25(external_fts)
               LIMIT 3""",
            (fts_query,),
        ).fetchall()
        results[query] = [f"{row[0]} | {row[1]}" for row in rows]
    return results


def migrate_external_chunks(
    *,
    db_path: Path = DB_PATH,
    data_dir: Path = EXTERNAL_DIR,
    channels_path: Path = CHANNELS_PATH,
    dry_run: bool = False,
    verify: bool = False,
) -> dict[str, Any]:
    """Re-ingest external JSONL files into chunked DB rows."""
    channels = load_channels(channels_path, reload=True)
    rows, failures, input_count, deduped_count = _iter_jsonl_items(data_dir, channels)
    avg_chunk_size = round(sum(row["char_count"] for row in rows) / len(rows), 2) if rows else 0.0

    stats: dict[str, Any] = {
        "input_jsonl_count": input_count,
        "rows_planned": len(rows),
        "rows_inserted": len(rows),
        "rows_changed": len(rows),
        "avg_chunk_size": avg_chunk_size,
        "items_failed": failures,
        "items_deduped": deduped_count,
        "preview_chunks": rows[:5],
        "schema_columns_added": [],
        "rows_before": None,
        "rows_after": None,
        "verify_results": {},
        "noop": False,
    }

    if dry_run:
        return stats

    conn = sqlite3.connect(str(db_path))
    # Bootstrap schema FIRST — on a fresh clone the table doesn't exist yet,
    # so the rows_before COUNT(*) below would crash. Gemini review #354
    # (#1324) item 1 + the regression test
    # ``test_migration_bootstraps_on_fresh_clone_without_table``.
    stats["schema_columns_added"] = ensure_external_schema(conn)
    stats["rows_before"] = conn.execute("SELECT COUNT(*) FROM external_articles").fetchone()[0]

    planned_rows = sorted((_row_tuple(row) for row in rows), key=lambda item: item[0])
    existing_rows = _existing_row_tuples(conn)
    if existing_rows == planned_rows:
        stats["rows_inserted"] = 0
        stats["rows_changed"] = 0
        stats["rows_after"] = stats["rows_before"]
        stats["noop"] = True
        if verify:
            stats["verify_results"] = _verify_roundtrip(conn)
        conn.commit()
        conn.close()
        return stats

    conn.execute("DELETE FROM external_articles")
    _insert_rows(conn, rows)
    conn.execute("INSERT INTO external_fts(external_fts) VALUES ('rebuild')")
    stats["rows_after"] = conn.execute("SELECT COUNT(*) FROM external_articles").fetchone()[0]
    stats["rows_changed"] = stats["rows_after"]
    if verify:
        stats["verify_results"] = _verify_roundtrip(conn)
    conn.commit()
    conn.close()
    return stats


def _print_stats(stats: dict[str, Any], *, dry_run: bool) -> None:
    mode = "DRY RUN" if dry_run else "MIGRATION"
    print(f"[{mode}] input JSONL items: {stats['input_jsonl_count']}")
    print(f"[{mode}] rows planned: {stats['rows_planned']}")
    print(f"[{mode}] rows inserted: {stats['rows_inserted']}")
    print(f"[{mode}] rows changed: {stats['rows_changed']}")
    print(f"[{mode}] avg chunk size: {stats['avg_chunk_size']}")
    if stats["schema_columns_added"]:
        print(f"[{mode}] schema columns added: {', '.join(stats['schema_columns_added'])}")
    if stats["rows_before"] is not None:
        print(f"[{mode}] rows before/after: {stats['rows_before']} -> {stats['rows_after']}")
    if stats["noop"]:
        print(f"[{mode}] no-op: existing rows already match the chunk plan")
    if stats["items_failed"]:
        print(f"[{mode}] failures ({len(stats['items_failed'])}):")
        for item in stats["items_failed"]:
            print(f"  - {item}")
    else:
        print(f"[{mode}] failures: none")
    print(f"[{mode}] deduped input items: {stats['items_deduped']}")

    if dry_run:
        print("[DRY RUN] first 5 chunks:")
        for chunk in stats["preview_chunks"]:
            print(f"  - {chunk['chunk_id']} ({chunk['char_count']} chars) :: {chunk['title']}")

    if stats["verify_results"]:
        print("[VERIFY] sample FTS roundtrip:")
        for query, hits in stats["verify_results"].items():
            print(f"  {query}: {len(hits)} hit(s)")
            for hit in hits:
                print(f"    - {hit}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Preview chunk output and stats without writing to the DB")
    parser.add_argument("--verify", action="store_true", help="Run sample FTS5 roundtrip checks after migration")
    args = parser.parse_args()

    stats = migrate_external_chunks(dry_run=args.dry_run, verify=args.verify)
    _print_stats(stats, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
