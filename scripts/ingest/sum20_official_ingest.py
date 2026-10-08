#!/usr/bin/env python3
"""Resumable, polite ingest for official СУМ-20 ``wordid`` article pages.

This foreground compatibility tool writes to its selected database. It is
bounded by default; limit zero is unbounded foreground work. For unattended
isolated staging use scripts.ingest.dictionary_acquisition.
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


class IngestCounts(dict[str, int]):
    """Keep legacy count keys while carrying a lossless control exit separately."""

    exit_code: int = 0


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
    counts = IngestCounts(ok=0, unchanged=0, not_found=0, transient_error=0, parse_error=0)
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
                delay_s=max(2.0, delay_s),
            )
            attempted += 1
            if outcome.status == "ok":
                try:
                    article = parse_sum20_article(outcome.document_html, wordid)
                except Sum20ParseError:
                    with conn:
                        record_crawl_outcome(conn, wordid=wordid, status="parse_error", error_text="unusable article")
                    counts["parse_error"] += 1
                    counts.exit_code = 4
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
                counts.exit_code = 4 if outcome.status == "parse_error" else (3 if outcome.terminal else 1)
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
            "Use for foreground direct-database ingestion; use dictionary_acquisition for unattended staging."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.ingest.sum20_official_ingest --db staging.db --start-wordid 5 --limit 8
  .venv/bin/python -m scripts.ingest.sum20_official_ingest --db staging.db --limit 100
Outputs: articles, four-status crawl outcomes and checkpoint written directly to --db; count summary.
Exit codes: 0 successful range; 1 ordinary failure; 2 usage; 3 terminal HTTP/access stop; 4 parse stop.
A terminal 3/4 outranks an earlier ordinary failure. Stops leave the failed checkpoint unchanged.
No durable terminal restart latch: never use an unconditional restart loop.
Related: scripts.ingest.dictionary_acquisition; docs/runbooks/dictionary-acquisition.md; #10003.
""",
    )
    parser.add_argument(
        "--db", type=Path, default=DEFAULT_DB, help="SQLite destination, e.g. staging.db (default: data/sources.db)."
    )
    parser.add_argument(
        "--start-wordid",
        type=int,
        help="Override the saved resume point; useful for a bounded fixture/probe run.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum sequential wordids to attempt (default: 100; 0 means unbounded foreground run).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Minimum seconds between requests (default: 2.0); observed robots crawl-delay always applies.",
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
    except (OSError, sqlite3.Error, ValueError):
        print("СУМ-20 ingest failed: input or storage error", file=sys.stderr)
        return 1
    print("СУМ-20 ingest: " + ", ".join(f"{status}={count}" for status, count in counts.items()))
    if counts["parse_error"]:
        return 4
    terminal = getattr(counts, "exit_code", 0)
    if terminal == 3:
        return 3
    return 1 if counts["transient_error"] else terminal


if __name__ == "__main__":
    raise SystemExit(main())
