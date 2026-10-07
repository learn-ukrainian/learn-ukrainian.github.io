#!/usr/bin/env python3
"""Polite, resumable GRAC wordlist snapshot (#9969).

Page numbers are one-based ``wlpage``; ``wlmaxitems`` sets the page size.
Verified against open-5.71.15 with two distinct live lemma pages. Rows,
retrieval provenance and the completed-page checkpoint commit atomically.
"""

from __future__ import annotations

import argparse
import math
import sqlite3
import sys
import time
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.rag.source_query import GRAC_BASE, GRAC_CORPUS, grac_db_path
from scripts.storage.topology import is_network_filesystem_path

USER_AGENT = "learn-ukrainian-grac-frequency/1.0 (noncommercial educational; resumable wordlist snapshot)"
SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    attr TEXT NOT NULL, str TEXT NOT NULL, frq INTEGER NOT NULL, relfreq REAL NOT NULL, page INTEGER NOT NULL,
    PRIMARY KEY (attr, str)
);
CREATE TABLE IF NOT EXISTS checkpoint (
    attr TEXT PRIMARY KEY, last_completed_page INTEGER NOT NULL,
    complete INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS provenance (
    attr TEXT NOT NULL, page INTEGER NOT NULL, corpus TEXT NOT NULL,
    api_version TEXT NOT NULL, manatee_version TEXT NOT NULL,
    min_freq INTEGER NOT NULL, page_size INTEGER NOT NULL,
    retrieved_at TEXT NOT NULL, item_count INTEGER NOT NULL,
    PRIMARY KEY (attr, page)
);
"""


def parse_page(data: Any) -> list[tuple[str, int, float]]:
    """Refuse error/malformed/unsorted responses rather than checkpointing misses."""
    if not isinstance(data, dict) or data.get("error") or not isinstance(data.get("Items"), list):
        raise ValueError("GRAC response lacks a valid Items list")
    if not data.get("api_version") or not data.get("manatee_version") or data.get("lastpage") not in (0, 1):
        raise ValueError("GRAC response lacks version or lastpage metadata")
    rows = []
    previous = math.inf
    for item in data["Items"]:
        if not isinstance(item, dict) or not isinstance(item.get("str"), str) or not item["str"]:
            raise ValueError("GRAC item lacks a string")
        frq = item.get("frq")
        relfreq = item.get("relfreq")
        if type(frq) is not int or frq < 0 or frq > previous:
            raise ValueError("GRAC frequencies must be nonnegative integers in descending order")
        if not isinstance(relfreq, (int, float)) or not math.isfinite(relfreq) or relfreq < 0:
            raise ValueError("GRAC item lacks a valid relative frequency")
        rows.append((item["str"], frq, float(relfreq)))
        previous = frq
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError("GRAC page repeats an item")
    return rows


def ingest(
    db_path: Path,
    *,
    attrs: Sequence[str] = ("lemma", "word"),
    min_freq: int = 5,
    page_size: int = 1000,
    max_pages: int = 0,
    delay: float = 3.0,
    retries: int = 3,
    retry_backoff: float = 2.0,
    transport: Any = None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, int]:
    """Resume each attribute; max_pages bounds successful pages per attribute/run.

    Exhausted retries raise without saving that page. Changing the floor, page
    size, corpus or API versions refuses resume; use a separate DB instead.
    """
    if not attrs or any(attr not in ("lemma", "word") for attr in attrs) or len(set(attrs)) != len(attrs):
        raise ValueError("attrs must contain distinct lemma/word attributes")
    if min_freq < 1 or page_size < 1 or max_pages < 0 or retries < 0:
        raise ValueError("floor/page size must be positive; page cap/retries must be nonnegative")
    if any(not math.isfinite(value) or value < 0 for value in (delay, retry_backoff)):
        raise ValueError("delays must be finite and nonnegative")
    if is_network_filesystem_path(db_path):
        raise ValueError("GRAC snapshot SQLite must use local storage")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    session = transport if transport is not None else requests.Session()
    counts = dict.fromkeys(attrs, 0)
    requested = False
    try:
        conn.executescript(SCHEMA)
        for attr in attrs:
            prior = conn.execute(
                "SELECT corpus, min_freq, page_size, api_version, manatee_version FROM provenance WHERE attr=? LIMIT 1",
                (attr,),
            ).fetchone()
            if prior and prior[:3] != (GRAC_CORPUS, min_freq, page_size):
                raise ValueError("Resume settings differ from snapshot; use a separate --db")
            saved = conn.execute(
                "SELECT last_completed_page, complete FROM checkpoint WHERE attr=?", (attr,)
            ).fetchone()
            if saved and saved[1]:
                print(f"{attr}: already complete at page={saved[0]}", flush=True)
                continue
            page = saved[0] + 1 if saved else 1
            completed = 0
            while not max_pages or completed < max_pages:
                params = {
                    "corpname": GRAC_CORPUS, "wltype": "simple", "wlattr": attr,
                    "wlsort": "frq", "wlnums": "frq", "wlminfreq": min_freq,
                    "wlmaxitems": page_size, "wlpage": page, "format": "json",
                }
                for attempt in range(retries + 1):
                    if requested:
                        sleep(delay if not attempt else max(delay, min(300.0, retry_backoff * 2 ** (attempt - 1))))
                    requested = True
                    try:
                        response = session.get(
                            f"{GRAC_BASE}/wordlist", params=params,
                            headers={"User-Agent": USER_AGENT}, timeout=60,
                        )
                        response.raise_for_status()
                        data = response.json()
                        rows = parse_page(data)
                        break
                    except (requests.RequestException, ValueError):
                        if attempt == retries:
                            raise
                        print(f"{attr}: page={page} retry={attempt + 1}/{retries}; checkpoint unchanged", flush=True)
                versions = (data["api_version"], data["manatee_version"])
                if prior and prior[3:] != versions:
                    raise ValueError("GRAC versions changed; use a separate --db")
                if rows and conn.execute(
                    "SELECT 1 FROM items WHERE attr=? AND str=?", (attr, rows[0][0])
                ).fetchone():
                    raise ValueError("GRAC repeated an earlier page; checkpoint unchanged")
                kept = [row for row in rows if row[1] >= min_freq]
                complete = bool(data["lastpage"] or not rows or len(kept) < len(rows))
                retrieved_at = datetime.now(UTC).isoformat()
                with conn:
                    conn.executemany(
                        "INSERT INTO items (attr,str,frq,relfreq,page) VALUES (?,?,?,?,?)",
                        [(attr, *row, page) for row in kept],
                    )
                    conn.execute(
                        "INSERT INTO provenance VALUES (?,?,?,?,?,?,?,?,?)",
                        (attr, page, GRAC_CORPUS, *versions, min_freq, page_size, retrieved_at, len(kept)),
                    )
                    conn.execute(
                        "INSERT INTO checkpoint VALUES (?,?,?) ON CONFLICT(attr) DO UPDATE SET "
                        "last_completed_page=excluded.last_completed_page, complete=excluded.complete",
                        (attr, page, int(complete)),
                    )
                prior = (GRAC_CORPUS, min_freq, page_size, *versions)
                counts[attr] += len(kept)
                completed += 1
                print(f"{attr}: page={page} rows={len(kept)} run_rows={counts[attr]} complete={complete}", flush=True)
                if complete:
                    break
                page += 1
        return counts
    finally:
        conn.close()
        if transport is None:
            session.close()


def build_parser() -> argparse.ArgumentParser:
    """CLI contract, including bounded probes and resumable operator runs."""
    parser = argparse.ArgumentParser(
        description="Pull GRAC lemma and word frequencies into a resumable local SQLite snapshot.\n"
        "Use for offline frequency lookups; use --max-pages for probes, never for concordance or collocations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.ingest.grac_frequency_ingest
  .venv/bin/python -m scripts.ingest.grac_frequency_ingest --attr lemma --max-pages 2 --db scratch.db
  .venv/bin/python -m scripts.ingest.grac_frequency_ingest --min-freq 10 --db data/grac-10.db
Outputs: SQLite items, per-attribute checkpoints and per-page retrieval provenance; progress on stdout.
Exit codes: 0 = complete or requested page cap reached; 1 = failure (resume checkpoint preserved);
            130 = interrupted (resume on next invocation).
Related: #9969; scripts/rag/source_query.py; sources MCP query_grac.
""",
    )
    parser.add_argument("--db", type=Path, help="Local SQLite destination (default: resolved data/grac_frequency.db); e.g. scratch.db")
    parser.add_argument("--attr", choices=("lemma", "word"), action="append", help="Attribute to ingest; repeat for both (default: lemma and word)")
    parser.add_argument("--min-freq", type=int, default=5, help="Inclusive frequency floor (default: 5); e.g. 10")
    parser.add_argument("--page-size", type=int, default=1000, help="Items per page, wlmaxitems (default: 1000); e.g. 100")
    parser.add_argument("--max-pages", type=int, default=0, help="Successful pages per attribute this run (default: 0 = unbounded); e.g. 2")
    parser.add_argument("--delay", type=float, default=3.0, help="Minimum seconds between requests, including retries (default: 3.0); e.g. 5")
    parser.add_argument("--retries", type=int, default=3, help="Retries after each failed request (default: 3); e.g. 1")
    parser.add_argument("--retry-backoff", type=float, default=2.0, help="Initial exponential backoff in seconds, capped at 300 (default: 2.0); e.g. 10")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run in the foreground; failures never pretend to be successful completion."""
    args = build_parser().parse_args(argv)
    try:
        counts = ingest(
            args.db or grac_db_path(), attrs=args.attr or ("lemma", "word"),
            min_freq=args.min_freq, page_size=args.page_size, max_pages=args.max_pages,
            delay=args.delay, retries=args.retries, retry_backoff=args.retry_backoff,
        )
    except KeyboardInterrupt:
        print("GRAC interrupted; last completed page preserved", file=sys.stderr)
        return 130
    except (OSError, sqlite3.Error, requests.RequestException, ValueError) as exc:
        print(f"GRAC ingest halted: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"GRAC ingest: {counts}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
