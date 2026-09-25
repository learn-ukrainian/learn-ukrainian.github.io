#!/usr/bin/env python3
"""Move ULIF raw bodies from sources.db to the independent cache DB.

Use only in a fenced offline window after a verified backup; never run during a crawl.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.lexicon import ulif_raw_cache
from scripts.wiki import sources_db

GIB = 1024**3
BATCH_SIZE = 10_000
RAW_TABLE = ulif_raw_cache.RAW_TABLE
DEFAULT_DB = Path(__file__).resolve().parents[3] / "data/sources.db"


def _table_counts(conn: sqlite3.Connection, *, exclude_raw: bool = False) -> dict[str, int]:
    names = [
        str(row[0])
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    return {
        name: int(conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
        for name in names
        if not (exclude_raw and name == RAW_TABLE)
    }


def _no_holders(db: Path) -> None:
    paths = [str(p) for p in (db, Path(f"{db}-wal"), Path(f"{db}-shm")) if p.exists()]
    try:
        result = subprocess.run(["lsof", "-t", "--", *paths], capture_output=True, text=True, check=False, timeout=30)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("lsof preflight timed out") from exc
    if result.returncode == 0 or result.stdout.strip():
        raise RuntimeError("sources.db has open holders; stop services and writers")
    if result.returncode != 1:
        raise RuntimeError(f"lsof preflight failed (exit {result.returncode})")


def _checkpoint(conn: sqlite3.Connection, db: Path) -> None:
    busy, _log, _done = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    if busy or (Path(f"{db}-wal").exists() and Path(f"{db}-wal").stat().st_size):
        raise RuntimeError("sources.db checkpoint is busy or WAL is not empty")


def _preflight(db: Path) -> dict[str, int]:
    if not db.is_file():
        raise RuntimeError(f"sources database missing: {db}")
    _no_holders(db)
    conn = sqlite3.connect(db, timeout=0)
    try:
        if RAW_TABLE not in _table_counts(conn):
            raise RuntimeError("legacy ULIF raw table is missing")
        _checkpoint(conn, db)
        raw_bytes = int(conn.execute(f"SELECT COALESCE(SUM(LENGTH(body)), 0) FROM {RAW_TABLE}").fetchone()[0])
        raw_pages = int(
            conn.execute("SELECT COALESCE(SUM(pgsize), 0) FROM dbstat WHERE name = ?", (RAW_TABLE,)).fetchone()[0]
        )
        compact_estimate = max(0, db.stat().st_size - raw_pages)
        free = shutil.disk_usage(db.parent).free
        required = raw_bytes + compact_estimate + 2 * GIB
        if free < required:
            raise RuntimeError(f"insufficient free space: {free} < {required} bytes")
        if db.with_name(f"{db.name}.new").exists() or db.with_name(f"{db.name}.pre-8800").exists():
            raise RuntimeError("migration output or rollback copy already exists")
        return {
            "raw_bytes": raw_bytes,
            "estimated_compact_bytes": compact_estimate,
            "free_bytes": free,
            "required_bytes": required,
            "raw_rows": int(conn.execute(f"SELECT COUNT(*) FROM {RAW_TABLE}").fetchone()[0]),
        }
    finally:
        conn.close()


def migrate(db: Path, cache: Path) -> dict:
    report: dict = {"source": str(db), "cache": str(cache), "preflight": _preflight(db)}
    conn = sqlite3.connect(db, timeout=0)
    raw = ulif_raw_cache.open_cache(cache)
    new = db.with_name(f"{db.name}.new")
    old = db.with_name(f"{db.name}.pre-8800")
    try:
        before = _table_counts(conn, exclude_raw=True)
        cursor = conn.execute(
            f"SELECT response_sha256, body, content_type, stored_at FROM {RAW_TABLE} ORDER BY response_sha256"
        )
        copied = 0
        while batch := cursor.fetchmany(BATCH_SIZE):
            for sha, body, content_type, stored_at in batch:
                ulif_raw_cache.put(sha, bytes(body), content_type, stored_at, conn=raw)
            raw.commit()
            if raw.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0]:
                raise RuntimeError("cache checkpoint busy")
            copied += len(batch)
        cache_count = int(raw.execute(f"SELECT COUNT(*) FROM {RAW_TABLE}").fetchone()[0])
        if copied != report["preflight"]["raw_rows"] or cache_count != copied:
            raise RuntimeError("raw row counts differ between source and cache")
        for sha, body in raw.execute(f"SELECT response_sha256, body FROM {RAW_TABLE}"):
            if hashlib.sha256(body).hexdigest() != sha:
                raise RuntimeError(f"cache body hash mismatch: {sha}")
        if raw.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("cache integrity_check failed")
        report["copied_rows"] = copied
        raw.close()
        raw = None

        conn.execute(f"DROP TABLE {RAW_TABLE}")
        conn.commit()
        conn.execute("VACUUM INTO ?", (str(new),))
        compact = sqlite3.connect(f"file:{new}?mode=ro", uri=True)
        try:
            if compact.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("compact database integrity_check failed")
            after = _table_counts(compact)
            if after != before:
                raise RuntimeError("other table counts changed during migration")
        finally:
            compact.close()
        _checkpoint(conn, db)
    finally:
        conn.close()
        if raw is not None:
            raw.close()
    _no_holders(db)
    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{db}{suffix}")
        if sidecar.exists():
            sidecar.unlink()
    db.rename(old)
    try:
        new.rename(db)
    except OSError:
        old.rename(db)
        raise
    report["compact_bytes"] = db.stat().st_size
    report["tables_preserved"] = before
    report["rollback_copy"] = str(old)
    return report


def _lookup_sample(db: Path) -> list[str]:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        rows = list(
            conn.execute(
                "SELECT DISTINCT e.normalized_query, e.status, s.kind "
                "FROM ulif_dictua_entries e LEFT JOIN ulif_dictua_sections s ON s.entry_id=e.id"
            )
        )
    finally:
        conn.close()
    strata: dict[str, set[str]] = {}
    for word, status, kind in rows:
        strata.setdefault(f"status:{status}", set()).add(word)
        if kind:
            strata.setdefault(f"kind:{kind}", set()).add(word)
    ordered = {
        key: sorted(words, key=lambda value: hashlib.sha256(value.encode()).digest())
        for key, words in sorted(strata.items())
    }
    selected: list[str] = []
    seen: set[str] = set()
    for rank in range(200):
        for words in ordered.values():
            if len(selected) == 200:
                break
            if rank < len(words) and words[rank] not in seen:
                seen.add(words[rank])
                selected.append(words[rank])
        if len(selected) == 200:
            break
    for word in sorted({row[0] for row in rows}, key=lambda value: hashlib.sha256(value.encode()).digest()):
        if len(selected) == 200:
            break
        if word not in seen:
            selected.append(word)
            seen.add(word)
    return selected


def _lookups(db: Path, words: list[str]) -> list[dict]:
    return [
        {
            "word": word,
            "entry": sources_db.get_ulif_dictua_entry(word, db_path=db),
            "sections": {
                kind: sources_db.search_ulif_dictua_sections(word, kind, db_path=db)
                for kind in sources_db.ULIF_DICTUA_SECTION_KINDS
            },
        }
        for word in words
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Move verified ULIF raw bodies into a local cache DB.\nUse only in a fenced offline window after a restore-tested backup.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/lexicon/tools/migrate_ulif_raw.py --check
  .venv/bin/python scripts/lexicon/tools/migrate_ulif_raw.py --record-lookups lookups.json
  .venv/bin/python scripts/lexicon/tools/migrate_ulif_raw.py --execute
  .venv/bin/python scripts/lexicon/tools/migrate_ulif_raw.py --compare-lookups lookups.json
Outputs: JSON preflight/report on stdout; optional lookup file; cache DB and swapped sources.db on execute.
Exit codes: 0 success; 1 precondition, integrity, or lookup mismatch.
Related: issue #8800 Plan v3 and backup issue #8811.""",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Sources SQLite path (default: data/sources.db)")
    parser.add_argument(
        "--cache", type=Path, default=None, help="Raw cache SQLite path (default: data/lexicon/cache/ulif_raw.sqlite)"
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--check", action="store_true", help="Check writer, checkpoint, and disk preconditions (default: off)"
    )
    action.add_argument("--execute", action="store_true", help="Copy, verify, compact, and swap (default: off)")
    action.add_argument(
        "--record-lookups",
        metavar="FILE",
        type=Path,
        help="Write up to 200 fixed stratified ULIF lookup outputs (JSON)",
    )
    action.add_argument(
        "--compare-lookups", metavar="FILE", type=Path, help="Compare ULIF lookup outputs with a recorded JSON file"
    )
    args = parser.parse_args(argv)
    db = args.db.resolve()
    cache = args.cache or ulif_raw_cache.cache_path(db)
    try:
        if args.check:
            result = _preflight(db)
        elif args.execute:
            result = migrate(db, cache)
        elif args.record_lookups:
            words = _lookup_sample(db)
            payload = {"words": words, "lookups": _lookups(db, words)}
            args.record_lookups.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
            result = {"recorded": len(words), "file": str(args.record_lookups)}
        else:
            expected = json.loads(args.compare_lookups.read_text(encoding="utf-8"))
            actual = _lookups(db, expected["words"])
            if actual != expected["lookups"]:
                raise RuntimeError("ULIF lookup outputs differ from recorded sample")
            result = {"compared": len(actual), "identical": True}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, sqlite3.Error, RuntimeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
