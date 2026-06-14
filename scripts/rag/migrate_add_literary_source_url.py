#!/usr/bin/env python3
"""One-shot idempotent migration: add source_url TEXT column to literary_texts
and backfill from on-disk data/literary_texts/*.jsonl keyed by chunk_id.

- ALTER guarded by PRAGMA table_info column-exists check (no drop/recreate).
- Defaults to NULL when JSONL record lacks source_url or the wave's JSONL is absent locally.
- For waves without local JSONL: leave NULL and log the wave (no fabrication of URLs).
- Public-domain izbornyk/litopys work-level URLs are taken ONLY from JSONL; no re-derive
  unless a deterministic manifest is present (none wired here; NULL otherwise).
- Run LOCALLY only (data/sources.db is gitignored 1.6 GB). CI cannot.

Audit note (per #2901): textbooks table has no source_url (and no equivalent URL col);
provenance for textbooks is via grade + source_file (structured extraction from known
textbook PDFs). In contrast, external_articles (url, url_normalized) and wikipedia
( url ) DO retain URLs. Textbooks gap is non-trivial to close (would touch extraction,
chunking, all inserts, indexes, and callers); not fixed here — follow-up issue if needed.

Usage:
    .venv/bin/python scripts/rag/migrate_add_literary_source_url.py
    .venv/bin/python scripts/rag/migrate_add_literary_source_url.py --db-path /tmp/test-sources.db
    .venv/bin/python scripts/rag/migrate_add_literary_source_url.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "sources.db"
LITERARY_DIR = PROJECT_ROOT / "data" / "literary_texts"


def _get_column_names(conn: sqlite3.Connection, table: str = "literary_texts") -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def ensure_source_url_column(conn: sqlite3.Connection) -> bool:
    """Idempotent: add source_url TEXT if missing. Returns True if added."""
    existing = _get_column_names(conn)
    if "source_url" in existing:
        return False
    conn.execute("ALTER TABLE literary_texts ADD COLUMN source_url TEXT")
    return True


def load_urls_by_chunk_id(lit_dir: Path) -> tuple[dict[str, str | None], set[str]]:
    """Scan local JSONL files. Return (chunk_id -> source_url_or_None, set of wave stems found)."""
    url_by_chunk: dict[str, str | None] = {}
    present_waves: set[str] = set()
    if not lit_dir or not lit_dir.exists():
        return url_by_chunk, present_waves
    for jsonl_path in sorted(lit_dir.glob("*.jsonl")):
        wave = jsonl_path.stem
        present_waves.add(wave)
        try:
            with open(jsonl_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        cid = rec.get("chunk_id")
                        if cid:
                            # Preserve None/empty as None; only store truthy URL
                            url = rec.get("source_url")
                            if url:
                                # Prefer explicit URL if multiple entries for same cid (rare)
                                url_by_chunk[str(cid)] = str(url).strip()
                            elif str(cid) not in url_by_chunk:
                                url_by_chunk[str(cid)] = None
                    except (json.JSONDecodeError, TypeError, KeyError):
                        continue
        except OSError:
            continue
    return url_by_chunk, present_waves


def backfill_from_jsonl(
    conn: sqlite3.Connection,
    url_by_chunk: dict[str, str | None],
    present_waves: set[str],
) -> dict[str, Any]:
    """Backfill source_url for rows whose chunk_id is in the map from local JSONL.
    Waves (source_file) absent from local JSONL are left NULL and reported.
    Returns stats dict for verification and logging.
    """
    # Collect DB waves (source_file) to identify absent ones
    db_rows = conn.execute(
        "SELECT id, chunk_id, source_file FROM literary_texts ORDER BY id"
    ).fetchall()
    total_rows = len(db_rows)

    db_waves: set[str] = {str(r[2]) for r in db_rows if r[2]}
    absent_waves = sorted(db_waves - present_waves)

    updated = 0
    null_reasons: dict[str, int] = defaultdict(int)

    # Update inside the caller's transaction
    for row_id, chunk_id, source_file in db_rows:
        cid = str(chunk_id) if chunk_id is not None else ""
        sf = str(source_file) if source_file is not None else ""

        if sf and sf in absent_waves:
            null_reasons[f"no local JSONL for wave {sf}"] += 1
            continue

        url = url_by_chunk.get(cid)
        if not url:
            if cid and cid in url_by_chunk:
                null_reasons["JSONL present for chunk but source_url absent/empty in record"] += 1
            else:
                null_reasons["chunk_id had no matching entry in any local JSONL"] += 1
            continue

        # Write only if different/NULL/empty
        cur = conn.execute(
            """
            UPDATE literary_texts
            SET source_url = ?
            WHERE id = ?
              AND (source_url IS NULL OR source_url = '' OR source_url != ?)
            """,
            (url, row_id, url),
        )
        if cur.rowcount:
            updated += cur.rowcount

    still_null = conn.execute(
        "SELECT COUNT(*) FROM literary_texts WHERE source_url IS NULL OR source_url = ''"
    ).fetchone()[0]

    return {
        "total_rows": total_rows,
        "updated": updated,
        "still_null": still_null,
        "absent_waves": absent_waves,
        "null_reasons": dict(null_reasons),
        "present_waves_count": len(present_waves),
    }


def run_migration(db_path: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Perform the column add (if needed) + backfill. Returns summary for tests/CI."""
    if not db_path.exists():
        return {"db_path": str(db_path), "existed": False, "added_column": False}

    conn = sqlite3.connect(str(db_path))
    try:
        added = False
        stats: dict[str, Any] = {}
        with conn:
            added = ensure_source_url_column(conn)
            # Show pragma for evidence (caller/test can capture)
            pragma_rows = conn.execute("PRAGMA table_info(literary_texts)").fetchall()

        print(f"[migrate] DB: {db_path}")
        print(f"[migrate] source_url column added this run: {added}")
        print("[migrate] PRAGMA table_info(literary_texts) [after ensure]:")
        for col in pragma_rows:
            print(" ", col)

        if dry_run:
            print("[migrate] --dry-run: backfill skipped")
            return {
                "db_path": str(db_path),
                "existed": True,
                "added_column": added,
                "dry_run": True,
                "pragma_after": pragma_rows,
            }

        url_by_chunk, present_waves = load_urls_by_chunk_id(LITERARY_DIR)
        print(f"[migrate] Loaded source_url for {len(url_by_chunk)} chunks from {len(present_waves)} local waves under {LITERARY_DIR}")

        with conn:
            stats = backfill_from_jsonl(conn, url_by_chunk, present_waves)

        print("\n[backfill] Results:")
        print(f"  total literary_texts rows: {stats['total_rows']}")
        print(f"  rows updated with source_url: {stats['updated']}")
        print(f"  rows left NULL/empty: {stats['still_null']}")
        if stats.get("absent_waves"):
            aw = stats["absent_waves"]
            print(f"  waves absent locally (rows left NULL for these): {', '.join(aw[:8])}{' ...' if len(aw) > 8 else ''} (total {len(aw)})")
        print("  NULL reasons (counts):")
        for reason, count in sorted(stats.get("null_reasons", {}).items(), key=lambda kv: -kv[1]):
            print(f"    {count}: {reason}")

        return {
            "db_path": str(db_path),
            "existed": True,
            "added_column": added,
            "stats": stats,
            "pragma_after": pragma_rows,
        }
    finally:
        conn.close()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Add source_url to literary_texts + backfill from JSONL")
    p.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Path to sources.db (default: data/sources.db)")
    p.add_argument("--dry-run", action="store_true", help="Add column if needed but skip UPDATE backfill")
    return p.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    result = run_migration(args.db_path, dry_run=args.dry_run)
    if result.get("stats"):
        s = result["stats"]
        print(f"\nDONE. updated={s['updated']} still_null={s['still_null']}")
    else:
        print("DONE.")
    sys.exit(0)
