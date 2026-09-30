#!/usr/bin/env python3
"""Ingest bounded slovnyk.me per-word verification snapshots into sources.db."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.wiki.slovnyk_me import (
    DEFAULT_SLOVNYK_ME_DICTS,
    DEFAULT_USER_AGENT,
    OVERLAP_BLOCKED_DICTS,
    SLOVNYK_ME_DICTS,
    _classify_flags,
    _source_type,
    _truncate,
    db_row_values,
    ensure_slovnyk_me_schema,
    fetch_entries,
    resolve_dict_slug,
)

REPO = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO / "data" / "sources.db"
DEFAULT_NOTES = REPO / "docs" / "audits" / "slovnyk-me-ingestion-feasibility.md"

INSERT_SQL = """
INSERT INTO slovnyk_me_entries (
    query,
    word,
    normalized_word,
    dictionary_slug,
    dictionary_label,
    source_type,
    source_url,
    title,
    snippet,
    text,
    is_modern,
    is_dialect,
    is_russianism,
    sovietization_risk,
    sovietization_keywords,
    fetched_at
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(normalized_word, dictionary_slug, source_url) DO UPDATE SET
    query = excluded.query,
    word = excluded.word,
    dictionary_label = excluded.dictionary_label,
    source_type = excluded.source_type,
    title = excluded.title,
    snippet = excluded.snippet,
    text = excluded.text,
    is_modern = excluded.is_modern,
    is_dialect = excluded.is_dialect,
    is_russianism = excluded.is_russianism,
    sovietization_risk = excluded.sovietization_risk,
    sovietization_keywords = excluded.sovietization_keywords,
    fetched_at = excluded.fetched_at
"""


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
            conn.executemany(INSERT_SQL, [db_row_values(row) for row in rows])
        return len(rows)
    finally:
        conn.close()


def ingest_cache(
    db_path: Path, cache_dir: Path, *, words: list[str], dictionaries: list[str],
    dry_run: bool, max_text_chars: int,
) -> int:
    """Upsert bounded retained snapshots without fetching or changing the cache.

    Follows the #1715 per-word recipe; schema-v4 identifies current cache
    semantics. Original source URLs and fetched_at survive the import. Misses
    are omitted, malformed/stale snapshots refuse before any database writes.
    """
    if not cache_dir.is_dir():
        raise ValueError("cache directory unavailable")
    allowed = {resolve_dict_slug(slug) for slug in dictionaries} - OVERLAP_BLOCKED_DICTS.keys()
    selected = set(words)
    rows = []
    for path in sorted(cache_dir.glob("*.json")):
        cache = json.loads(path.read_text(encoding="utf-8"))
        if selected and cache.get("lemma") not in selected:
            continue
        if cache.get("schema_version") != 4 or not isinstance(cache.get("lookups"), dict):
            raise ValueError("cache snapshot needs schema_version 4 and lookups")
        for slug, lookup in cache["lookups"].items():
            if slug not in allowed or lookup is None:
                continue
            if not isinstance(lookup, dict) or lookup.get("dictionary_slug") != slug:
                raise ValueError("cache dictionary identity mismatch")
            if not all(isinstance(lookup.get(key), str) and lookup[key] for key in ("word", "text", "source_url")):
                raise ValueError("cache snapshot lacks word, text or source URL")
            url = urlparse(lookup["source_url"])
            if url.scheme != "https" or url.netloc != "slovnyk.me" or not url.path.startswith(f"/dict/{slug}/"):
                raise ValueError("cache source URL is not a direct dictionary entry")
            if not isinstance(cache.get("fetched_at"), str) or not cache["fetched_at"]:
                raise ValueError("cache snapshot lacks original fetch timestamp")
            text = _truncate(lookup["text"], max_text_chars)
            modern, dialect, russianism, risk, keywords = _classify_flags(slug, lookup["text"])
            rows.append({
                **lookup, "query": cache.get("lemma", lookup["word"]),
                "text": text, "snippet": text, "fetched_at": cache["fetched_at"],
                "is_modern": modern, "is_dialect": dialect, "is_russianism": russianism,
                "sovietization_risk": risk, "sovietization_keywords": keywords,
                "source_type": _source_type(slug, modern, dialect, russianism),
            })
    if dry_run:
        print(f"[dry-run] would upsert {len(rows)} cached row(s)")
        return len(rows)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        ensure_slovnyk_me_schema(conn)
        with conn:
            conn.executemany(INSERT_SQL, [db_row_values(row) for row in rows])
    finally:
        conn.close()
    return len(rows)


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
        "Positional words/--words-file optionally restrict the imported words.",
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
    dicts = args.dicts or list(DEFAULT_SLOVNYK_ME_DICTS)
    for slug in dicts:
        canonical = resolve_dict_slug(slug)
        if canonical in OVERLAP_BLOCKED_DICTS:
            print(
                f"Skipping slovnyk.me/{canonical}: use canonical local tool "
                f"`{OVERLAP_BLOCKED_DICTS[canonical]}` instead.",
                file=sys.stderr,
            )
    if args.cache_dir is not None:
        loaded = ingest_cache(
            args.db, args.cache_dir, words=words, dictionaries=dicts,
            dry_run=args.dry_run, max_text_chars=max(1, args.max_text_chars),
        )
        print(f"Loaded {loaded} cached slovnyk.me row(s).")
        return 0
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
