#!/usr/bin/env python3
"""Resumable, polite ingest for official СУМ-20 ``wordid`` article pages.

This tool is intentionally bounded by default.  A detached operational run
may opt in to a larger ``--limit`` only after the fixtures and parser are
validated; normal builds query the resulting SQLite collection offline.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from scripts.wiki.sum20_official import (
        Sum20ParseError,
        advance_crawl_checkpoint,
        crawl_resume_wordid,
        ensure_sum20_official_schema,
        fetch_sum20_wordid,
        parse_sum20_article,
        record_crawl_outcome,
        upsert_sum20_article,
    )
except ImportError:  # pragma: no cover - direct script execution
    from wiki.sum20_official import (
        Sum20ParseError,
        advance_crawl_checkpoint,
        crawl_resume_wordid,
        ensure_sum20_official_schema,
        fetch_sum20_wordid,
        parse_sum20_article,
        record_crawl_outcome,
        upsert_sum20_article,
    )

REPO = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO / "data" / "sources.db"


def ingest_wordids(
    db_path: Path,
    *,
    start_wordid: int | None = None,
    limit: int = 100,
    delay_s: float = 2.0,
    retries: int = 3,
    retry_backoff_s: float = 2.0,
    sleep: callable = time.sleep,
) -> dict[str, int]:
    """Ingest a sequential bounded range and preserve a safe resume point.

    ``transient_error`` and ``parse_error`` halt the run without checkpointing
    that wordid.  Thus neither can become a negative cache entry and the next
    invocation retries exactly the failed wordid.
    """
    if limit < 0:
        raise ValueError("limit must be zero (unbounded) or a positive integer")
    if start_wordid is not None and start_wordid < 1:
        raise ValueError("start_wordid must be at least 1")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    counts = {"ok": 0, "unchanged": 0, "not_found": 0, "transient_error": 0, "parse_error": 0}
    try:
        ensure_sum20_official_schema(conn)
        wordid = start_wordid if start_wordid is not None else crawl_resume_wordid(conn)
        attempted = 0
        while limit == 0 or attempted < limit:
            outcome = fetch_sum20_wordid(
                wordid,
                retries=retries,
                retry_backoff_s=retry_backoff_s,
                sleep=sleep,
            )
            attempted += 1
            if outcome.status == "ok":
                try:
                    article = parse_sum20_article(outcome.document_html, wordid)
                except Sum20ParseError as exc:
                    with conn:
                        record_crawl_outcome(conn, wordid=wordid, status="parse_error", error_text=str(exc))
                    counts["parse_error"] += 1
                    break
                with conn:
                    changed = upsert_sum20_article(conn, article)
                    record_crawl_outcome(
                        conn,
                        wordid=wordid,
                        status="ok",
                        content_sha256=article.content_sha256,
                    )
                    advance_crawl_checkpoint(conn, wordid)
                counts["ok" if changed else "unchanged"] += 1
            elif outcome.status == "not_found":
                with conn:
                    record_crawl_outcome(conn, wordid=wordid, status="not_found")
                    advance_crawl_checkpoint(conn, wordid)
                counts["not_found"] += 1
            else:
                with conn:
                    record_crawl_outcome(
                        conn,
                        wordid=wordid,
                        status=outcome.status,
                        error_text=outcome.error_text,
                    )
                counts[outcome.status] += 1
                break
            wordid += 1
            if (limit == 0 or attempted < limit) and delay_s > 0:
                sleep(delay_s)
        return counts
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest official sum20ua.com sequential wordid pages into sources.db. "
            "Resumes from the durable checkpoint and never treats network failures as misses."
        )
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help=f"SQLite destination (default: {DEFAULT_DB})")
    parser.add_argument(
        "--start-wordid",
        type=int,
        help="Override the saved resume point; useful for a bounded fixture/probe run.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum sequential wordids to attempt (default: 100; 0 means unbounded detached run).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Minimum seconds between requests (default: 2.0).",
    )
    parser.add_argument("--retries", type=int, default=3, help="Retries after transient failures (default: 3).")
    parser.add_argument(
        "--retry-backoff",
        type=float,
        default=2.0,
        help="Initial exponential-backoff delay in seconds (default: 2.0).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        counts = ingest_wordids(
            args.db,
            start_wordid=args.start_wordid,
            limit=args.limit,
            delay_s=max(0.0, args.delay),
            retries=max(0, args.retries),
            retry_backoff_s=max(0.0, args.retry_backoff),
        )
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"СУМ-20 ingest failed: {exc}", file=sys.stderr)
        return 1
    print("СУМ-20 ingest: " + ", ".join(f"{status}={count}" for status, count in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
