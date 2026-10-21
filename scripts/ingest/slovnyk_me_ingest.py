#!/usr/bin/env python3
"""Ingest bounded slovnyk.me per-word verification snapshots into sources.db."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sqlite3
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote, urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib.readonly_sqlite import SQLiteConnection, open_readonly
from scripts.storage.topology import is_network_filesystem_path
from scripts.wiki.slovnyk_me import (
    DEFAULT_SLOVNYK_ME_DICTS,
    DEFAULT_USER_AGENT,
    OVERLAP_BLOCKED_DICTS,
    SLOVNYK_ME_BASE,
    SLOVNYK_ME_DICTS,
    _classify_flags,
    _source_type,
    _truncate,
    db_row_values,
    dictionary_use_role,
    ensure_slovnyk_me_schema,
    fetch_entries,
    normalize_word,
    resolve_dict_slug,
)

REPO = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO / "data" / "sources.db"
DEFAULT_NOTES = REPO / "docs" / "audits" / "slovnyk-me-ingestion-feasibility.md"

IMPORTER_VERSION = "slovnyk-cache-ingest/2"
CACHE_LOCATOR_PARTS = ("data", "lexicon", "slovnyk_cache")

_ENTRY_COLUMNS = (
    "query", "word", "normalized_word", "dictionary_slug", "dictionary_label", "source_type",
    "source_url", "title", "snippet", "text", "is_modern", "is_dialect", "is_russianism",
    "sovietization_risk", "sovietization_keywords", "fetched_at",
    "use_role", "content_sha256", "cache_path", "importer_version",
)
_ENTRY_KEY = ("normalized_word", "dictionary_slug", "source_url")
INSERT_SQL = f"""
INSERT INTO slovnyk_me_entries ({", ".join(_ENTRY_COLUMNS)})
VALUES ({", ".join("?" for _ in _ENTRY_COLUMNS)})
ON CONFLICT({", ".join(_ENTRY_KEY)}) DO UPDATE SET
    {", ".join(f"{c} = excluded.{c}" for c in _ENTRY_COLUMNS if c not in _ENTRY_KEY)}
"""

_MISS_COLUMNS = (
    "query", "lookup_word", "normalized_word", "dictionary_slug", "dictionary_label",
    "lookup_status", "http_status", "source_url", "fetched_at",
    "use_role", "content_sha256", "cache_path", "importer_version",
)
_MISS_KEY = ("normalized_word", "dictionary_slug")
MISS_INSERT_SQL = f"""
INSERT INTO slovnyk_me_lookup_misses ({", ".join(_MISS_COLUMNS)})
VALUES ({", ".join("?" for _ in _MISS_COLUMNS)})
ON CONFLICT({", ".join(_MISS_KEY)}) DO UPDATE SET
    {", ".join(f"{c} = excluded.{c}" for c in _MISS_COLUMNS if c not in _MISS_KEY)}
"""
# One row per (word x dictionary): a positive entry supersedes a recorded miss.
MISS_SUPERSEDED_SQL = """
DELETE FROM slovnyk_me_lookup_misses
WHERE EXISTS (
    SELECT 1 FROM slovnyk_me_entries AS e
    WHERE e.normalized_word = slovnyk_me_lookup_misses.normalized_word
      AND e.dictionary_slug = slovnyk_me_lookup_misses.dictionary_slug
)
"""


def _entry_values(row: dict) -> tuple:
    """Insert values for INSERT_SQL: the shared 16 columns plus provenance."""
    return (
        *db_row_values(row),
        dictionary_use_role(row.get("dictionary_slug", "")),
        row.get("content_sha256", ""),
        row.get("cache_path", ""),
        row.get("importer_version", IMPORTER_VERSION),
    )


def _miss_values(row: dict) -> tuple:
    return tuple(row[column] for column in _MISS_COLUMNS)


def _read_words(args: argparse.Namespace) -> list[str]:
    words: list[str] = []
    for word in args.words:
        cleaned = word.strip()
        if cleaned:
            words.append(cleaned)
    if args.words_file:
        with args.words_file.open(encoding="utf-8") as fh:
            for line in fh:
                cleaned = line.strip()
                if cleaned and not cleaned.startswith("#"):
                    words.append(cleaned)
    deduped: list[str] = []
    seen: set[str] = set()
    for word in words:
        lowered = word.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(word)
    return deduped


def ingest_words(
    db_path: Path,
    words: list[str],
    *,
    dictionaries: list[str],
    dry_run: bool,
    sleep_s: float,
    user_agent: str,
    max_text_chars: int,
) -> int:
    rows: list[dict] = []
    for index, word in enumerate(words):
        if index and sleep_s > 0:
            time.sleep(sleep_s)
        outages: list[dict] = []
        fetched = fetch_entries(
            word,
            dictionaries=dictionaries,
            limit=len(dictionaries),
            user_agent=user_agent,
            max_text_chars=max_text_chars,
            outages=outages,
        )
        rows.extend(fetched)
        note = ""
        if outages:
            # #9005: a failed fetch is not "no entry"; say so rather than print a bare count.
            failed = sorted({f"{o['dictionary_slug']} ({o['error']})" for o in outages})
            note = f" — UNAVAILABLE: {', '.join(failed)}"
        print(f"{word}: {len(fetched)} slovnyk.me row(s){note}")

    if dry_run:
        print(f"[dry-run] would upsert {len(rows)} row(s) into {db_path}")
        return len(rows)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        ensure_slovnyk_me_schema(conn)
        with conn:
            conn.executemany(INSERT_SQL, [_entry_values(row) for row in rows])
        return len(rows)
    finally:
        conn.close()


@dataclass
class CacheImportReport:
    """What a cache import read (and, unless dry-run, wrote)."""

    files: int = 0
    entries: Counter = field(default_factory=Counter)  # positive rows per dictionary
    misses: Counter = field(default_factory=Counter)  # observed-404 rows per dictionary
    unproven: Counter = field(default_factory=Counter)  # nulls without 404 evidence: not recorded
    inserted: int = 0  # new slovnyk_me_entries rows; the rest of `entries` upserted existing keys
    inserted_misses: int = 0
    backup_path: Path | None = None

    def summary(self) -> str:
        lines = [
            f"files={self.files} entries={sum(self.entries.values())} "
            f"not_found={sum(self.misses.values())} unproven_null={sum(self.unproven.values())}"
        ]
        for slug in sorted(self.entries.keys() | self.misses.keys()):
            lines.append(f"  {slug}: entries={self.entries[slug]} not_found={self.misses[slug]}")
        return "\n".join(lines)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _cache_locator(cache_dir: Path, path: Path) -> str:
    """Repo-relative locator for the canonical cache; the directory name otherwise."""
    canonical = cache_dir.resolve().parts[-len(CACHE_LOCATOR_PARTS):] == CACHE_LOCATOR_PARTS
    return f"{'/'.join(CACHE_LOCATOR_PARTS) if canonical else cache_dir.name}/{path.name}"


def _check_cache_shape(cache: object, name: str) -> dict:
    """Accept the schema-v4 snapshot and the v4 VTS mirror shape (provenance block, no version)."""
    if not isinstance(cache, dict) or not isinstance(cache.get("lookups"), dict):
        raise ValueError(f"{name}: cache snapshot needs schema_version 4 and lookups")
    provenance = cache.get("provenance")
    mirror = "schema_version" not in cache and isinstance(provenance, dict) and isinstance(provenance.get("mirror"), str)
    if cache.get("schema_version") != 4 and not mirror:
        raise ValueError(f"{name}: cache snapshot needs schema_version 4 and lookups")
    return cache


def _snapshot_fetched_at(cache: dict) -> str:
    stamp = cache.get("fetched_at")
    if not (isinstance(stamp, str) and stamp) and isinstance(cache.get("provenance"), dict):
        stamp = cache["provenance"].get("updated_at")
    return stamp if isinstance(stamp, str) else ""


def _positive_row(slug: str, lookup: dict, cache: dict, *, name: str, locator: str, fetched_at: str,
                  lemma: str, max_text_chars: int) -> dict:
    if lookup.get("dictionary_slug") != slug or slug not in SLOVNYK_ME_DICTS:
        raise ValueError(f"{name}: cache dictionary identity mismatch for {slug}")
    if not all(isinstance(lookup.get(key), str) and lookup[key] for key in ("word", "text", "source_url")):
        raise ValueError(f"{name}: cache snapshot lacks word, text or source URL for {slug}")
    url = urlparse(lookup["source_url"])
    if url.scheme != "https" or url.netloc != "slovnyk.me" or not url.path.startswith(f"/dict/{slug}/"):
        raise ValueError(f"{name}: cache source URL is not a direct dictionary entry for {slug}")
    if not fetched_at:
        raise ValueError(f"{name}: cache snapshot lacks original fetch timestamp")
    text = _truncate(lookup["text"], max_text_chars)
    modern, dialect, russianism, risk, keywords = _classify_flags(slug, lookup["text"])
    return {
        **lookup, "query": lemma, "text": text, "snippet": text, "fetched_at": fetched_at,
        "is_modern": modern, "is_dialect": dialect, "is_russianism": russianism,
        "sovietization_risk": risk, "sovietization_keywords": keywords,
        "source_type": _source_type(slug, modern, dialect, russianism),
        "content_sha256": _sha256(lookup["text"]), "cache_path": locator,
        "importer_version": IMPORTER_VERSION,
    }


def _miss_row(slug: str, evidence: dict, *, locator: str, fetched_at: str, lemma: str) -> dict:
    word = evidence["lookup_word"]
    return {
        "query": lemma, "lookup_word": word, "normalized_word": normalize_word(word),
        "dictionary_slug": slug, "dictionary_label": SLOVNYK_ME_DICTS[slug],
        "lookup_status": "not_found", "http_status": 404,
        "source_url": f"{SLOVNYK_ME_BASE}/dict/{slug}/{quote(word, safe='')}",
        "fetched_at": fetched_at, "use_role": dictionary_use_role(slug),
        "content_sha256": _sha256(json.dumps(evidence, sort_keys=True, ensure_ascii=False)),
        "cache_path": locator, "importer_version": IMPORTER_VERSION,
    }


def read_cache(
    cache_dir: Path, *, words: list[str], dictionaries: list[str] | None, max_text_chars: int,
) -> tuple[list[dict], list[dict], CacheImportReport]:
    """Validate every snapshot and return (entries, misses, report); nothing is written.

    A miss is recorded only with the cache's identity-bound observed-404 evidence
    (``lookups[slug] is None`` plus ``not_found[slug] == {http_status: 404, lookup_word}``).
    A bare null is unproven (the builder refetches it), so it is counted, never stored.
    """
    if not cache_dir.is_dir():
        raise ValueError("cache directory unavailable")
    allowed = {resolve_dict_slug(slug) for slug in dictionaries} if dictionaries else None
    selected = set(words)
    report = CacheImportReport()
    entries: list[dict] = []
    misses: list[dict] = []
    for path in sorted(cache_dir.glob("*.json")):
        cache = _check_cache_shape(json.loads(path.read_text(encoding="utf-8")), path.name)
        lemma = cache["lemma"] if isinstance(cache.get("lemma"), str) and cache["lemma"] else path.stem
        if selected and lemma not in selected:
            continue
        report.files += 1
        locator = _cache_locator(cache_dir, path)
        fetched_at = _snapshot_fetched_at(cache)
        observed = cache.get("not_found") if isinstance(cache.get("not_found"), dict) else {}
        for slug, lookup in cache["lookups"].items():
            if allowed is not None and slug not in allowed:
                continue
            if lookup is not None:
                if not isinstance(lookup, dict):
                    raise ValueError(f"{path.name}: cache dictionary identity mismatch for {slug}")
                entries.append(_positive_row(
                    slug, lookup, cache, name=path.name, locator=locator, fetched_at=fetched_at,
                    lemma=lemma, max_text_chars=max_text_chars,
                ))
                report.entries[slug] += 1
                continue
            evidence = observed.get(slug)
            proven = (
                slug in SLOVNYK_ME_DICTS and fetched_at and isinstance(evidence, dict)
                and evidence.get("http_status") == 404
                and isinstance(evidence.get("lookup_word"), str) and evidence["lookup_word"]
            )
            if proven:
                misses.append(_miss_row(slug, evidence, locator=locator, fetched_at=fetched_at, lemma=lemma))
                report.misses[slug] += 1
            else:
                report.unproven[slug] += 1
    return entries, misses, report


def backup_database(conn: SQLiteConnection, db_path: Path, backup_dir: Path | None = None) -> Path:
    """Consistent copy of the open (possibly live, WAL) store via ``VACUUM INTO``."""
    backup_dir = backup_dir or db_path.parent / "backups"
    if is_network_filesystem_path(backup_dir):
        raise ValueError("sources.db backups must stay on local storage")
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    target = backup_dir / f"{db_path.stem}.pre-slovnyk-cache-ingest.{stamp}.db"
    conn.execute("VACUUM INTO ?", (str(target),))
    probe = "SELECT count(*) FROM sqlite_master"
    copy = open_readonly(target)
    try:
        if copy.execute(probe).fetchone() != conn.execute(probe).fetchone():
            raise ValueError(f"backup {target.name} does not match its source")
    finally:
        copy.close()
    return target


def _table_count(conn: SQLiteConnection, table: str) -> int:
    return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def ingest_cache(
    db_path: Path, cache_dir: Path, *, words: list[str], dictionaries: list[str] | None,
    dry_run: bool, max_text_chars: int, backup_dir: Path | None = None,
) -> CacheImportReport:
    """Upsert every cached dictionary lookup (one row per word x dictionary), offline.

    Follows the #1715 per-word recipe; the cache is read, never fetched or changed.
    Original source URLs and fetched_at survive, each row names its cache file, the
    full-text SHA-256 and the importer version, and observed 404s become rows in
    ``slovnyk_me_lookup_misses``. A malformed snapshot refuses before any write; an
    existing database is backed up first and must be on local storage.
    """
    entries, misses, report = read_cache(
        cache_dir, words=words, dictionaries=dictionaries, max_text_chars=max_text_chars,
    )
    if dry_run:
        return report
    if is_network_filesystem_path(db_path):
        raise ValueError("sources.db must stay on local storage")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    existed = db_path.exists()
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA busy_timeout = 60000")
        if existed:
            report.backup_path = backup_database(conn, db_path, backup_dir)
        ensure_slovnyk_me_schema(conn)
        entries_before = _table_count(conn, "slovnyk_me_entries")
        misses_before = _table_count(conn, "slovnyk_me_lookup_misses")
        with conn:
            conn.executemany(INSERT_SQL, [_entry_values(row) for row in entries])
            conn.executemany(MISS_INSERT_SQL, [_miss_values(row) for row in misses])
            conn.execute(MISS_SUPERSEDED_SQL)
        report.inserted = _table_count(conn, "slovnyk_me_entries") - entries_before
        report.inserted_misses = _table_count(conn, "slovnyk_me_lookup_misses") - misses_before
    finally:
        conn.close()
    return report


def build_parser() -> argparse.ArgumentParser:
    dict_list = ", ".join(DEFAULT_SLOVNYK_ME_DICTS)
    parser = argparse.ArgumentParser(
        description=(
            "Fetch explicit slovnyk.me direct-entry pages and store bounded verification snapshots.\n"
            "Use for a curated word list; do NOT use as a sitemap crawler or full-dictionary mirror."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""Examples:
  .venv/bin/python scripts/ingest/slovnyk_me_ingest.py блакитний кобета гаразд
  .venv/bin/python scripts/ingest/slovnyk_me_ingest.py --words-file data/slovnyk-me-seed.txt --dict newsum --dict slang_lviv
  .venv/bin/python scripts/ingest/slovnyk_me_ingest.py --dry-run --dict newsum блакитний
  .venv/bin/python scripts/ingest/slovnyk_me_ingest.py --cache-dir data/lexicon/slovnyk_cache --dry-run
  .venv/bin/python scripts/ingest/slovnyk_me_ingest.py --cache-dir data/lexicon/slovnyk_cache --dict vts

Outputs:
  Creates/updates the slovnyk_me_entries table plus FTS5 index in data/sources.db by default.
  Stores bounded snippets/text for explicit words only; no /search crawl and no sitemap ingest.

Exit codes:
  0 on successful ingest; 2 when no words are supplied; >=1 on network, SQLite, or argument errors.

Related:
  GitHub issue #1715; feasibility notes: {DEFAULT_NOTES}
  Default dictionaries: {dict_list}
""",
    )
    parser.add_argument(
        "words",
        nargs="*",
        help="Explicit Ukrainian headwords to fetch, e.g. блакитний кобета гаразд.",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Import existing schema-v4 per-word JSON snapshots offline; no network requests. "
        "Every cached dictionary is imported unless --dict narrows it; observed 404s are stored "
        "in slovnyk_me_lookup_misses. Positional words/--words-file optionally restrict the words.",
    )
    parser.add_argument(
        "--words-file",
        type=Path,
        help="UTF-8 file with one headword per line; blank lines and # comments are ignored.",
    )
    parser.add_argument(
        "--dict",
        dest="dicts",
        action="append",
        choices=sorted(SLOVNYK_ME_DICTS),
        help=(
            "slovnyk.me dictionary slug to query; repeatable. "
            f"Default: {dict_list}."
        ),
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"SQLite sources.db path to update. Default: {DEFAULT_DB}",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        help="Where --cache-dir writes the pre-import copy of an existing --db. Default: <db dir>/backups.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report fetched or cached rows without creating/updating SQLite. Default: false.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.75,
        help="Seconds to pause between words for polite per-word fetching. Default: 0.75.",
    )
    parser.add_argument(
        "--max-text-chars",
        type=int,
        default=200,
        help="Maximum entry text characters stored per row. Default: 200.",
    )
    parser.add_argument(
        "--user-agent",
        default=DEFAULT_USER_AGENT,
        help=f"HTTP User-Agent for direct-entry requests. Default: {DEFAULT_USER_AGENT}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    words = _read_words(args)
    if not words and args.cache_dir is None:
        print("No words supplied. Pass positional words or --words-file.", file=sys.stderr)
        return 2
    if args.cache_dir is not None:
        report = ingest_cache(
            args.db, args.cache_dir, words=words, dictionaries=args.dicts,
            dry_run=args.dry_run, max_text_chars=max(1, args.max_text_chars),
            backup_dir=args.backup_dir,
        )
        print(report.summary())
        if args.dry_run:
            print("[dry-run] nothing written")
        else:
            print(
                f"Loaded {sum(report.entries.values())} cached slovnyk.me row(s) "
                f"({report.inserted} new) and {report.inserted_misses} new not_found row(s) into {args.db}; "
                f"backup: {report.backup_path or 'none (database did not exist)'}"
            )
        return 0
    dicts = args.dicts or list(DEFAULT_SLOVNYK_ME_DICTS)
    for slug in dicts:
        canonical = resolve_dict_slug(slug)
        if canonical in OVERLAP_BLOCKED_DICTS:
            print(
                f"Skipping slovnyk.me/{canonical}: use canonical local tool "
                f"`{OVERLAP_BLOCKED_DICTS[canonical]}` instead.",
                file=sys.stderr,
            )
    loaded = ingest_words(
        args.db,
        words,
        dictionaries=dicts,
        dry_run=args.dry_run,
        sleep_s=max(0.0, args.sleep),
        user_agent=args.user_agent,
        max_text_chars=max(1, args.max_text_chars),
    )
    print(f"Loaded {loaded} slovnyk.me row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
