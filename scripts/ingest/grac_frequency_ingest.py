#!/usr/bin/env python3
"""Polite, resumable GRAC wordlist snapshot (#9969).

Frequency windows always request ``wlpage=1``. Fetch the final tie in full
before continuing below it: unstable equal-frequency ordering cannot skip an
item. Verified with an exact-frequency window and the entire floor-5 lemma tie
(147,011 distinct items). Rows, retrieval provenance and the cursor commit
atomically. Legacy offset checkpoints replay without losing rows or provenance.
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
CREATE TABLE IF NOT EXISTS frequency_cursor (
    attr TEXT PRIMARY KEY, next_max_freq INTEGER NOT NULL, expected_total INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS request_bounds (
    attr TEXT NOT NULL, page INTEGER NOT NULL,
    min_freq INTEGER NOT NULL, max_freq INTEGER, requested_items INTEGER NOT NULL,
    PRIMARY KEY (attr, page)
);
"""


class GracIngestHalted(RuntimeError):
    """An operator stop condition that must bypass the transient retry loop."""


def parse_page(data: Any) -> list[tuple[str, int, float]]:
    """Refuse error/malformed/unsorted responses rather than checkpointing misses."""
    if not isinstance(data, dict) or data.get("error") or not isinstance(data.get("Items"), list):
        raise ValueError("GRAC response lacks a valid Items list")
    if not data.get("api_version") or not data.get("manatee_version") or data.get("lastpage") not in (0, 1):
        raise ValueError("GRAC response lacks version or lastpage metadata")
    if type(data.get("total")) is not int or data["total"] < 0:
        raise ValueError("GRAC response lacks a nonnegative integer total")
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
    if not rows and not data["lastpage"]:
        raise ValueError("GRAC returned an empty page without lastpage=1; checkpoint unchanged")
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
    Legacy checkpoints replay from the top, deduplicating existing rows and
    retaining their original provenance. max_pages counts committed frequency
    bands, each of which may require additional requests to finish its last tie.
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

        def fetch(attr: str, floor: int, ceiling: int | None, size: int, prior: tuple | None, page: int) -> tuple[dict, list, str]:
            nonlocal requested
            params = {
                "corpname": GRAC_CORPUS, "wltype": "simple", "wlattr": attr,
                "wlsort": "frq", "wlnums": "frq", "wlminfreq": floor,
                "wlmaxitems": size, "wlpage": 1, "format": "json",
            }
            if ceiling is not None:
                params["wlmaxfreq"] = ceiling
            for attempt in range(retries + 1):
                if requested:
                    sleep(delay if not attempt else max(delay, min(300.0, retry_backoff * 2 ** (attempt - 1))))
                requested = True
                try:
                    response = session.get(
                        f"{GRAC_BASE}/wordlist", params=params,
                        headers={"User-Agent": USER_AGENT}, timeout=60,
                    )
                    if response.status_code == 429:
                        retry_after = response.headers.get("Retry-After")
                        wait = f"; honour Retry-After: {retry_after}" if retry_after else ""
                        raise GracIngestHalted(
                            f"HTTP 429: operator should wait before resuming{wait}; checkpoint unchanged"
                        )
                    if response.status_code == 403:
                        raise GracIngestHalted("HTTP 403: operator should stop; checkpoint unchanged")
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
            # This also catches wholesale repeats from an earlier band: its
            # frequencies exceed the now-exclusive upper cursor.
            if any(row[1] < floor or (ceiling is not None and row[1] > ceiling) for row in rows):
                raise ValueError("GRAC repeated an earlier page or ignored frequency bounds; checkpoint unchanged")
            return data, rows, datetime.now(UTC).isoformat()

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
            cursor = conn.execute(
                "SELECT next_max_freq, expected_total FROM frequency_cursor WHERE attr=?", (attr,)
            ).fetchone()
            # Offset paging cannot certify old coverage, even for an old complete
            # checkpoint. Replay once and keep every existing item/provenance row.
            if saved and saved[1] and not cursor:
                with conn:
                    conn.execute("UPDATE checkpoint SET complete=0 WHERE attr=?", (attr,))
            stored = conn.execute("SELECT COUNT(*) FROM items WHERE attr=?", (attr,)).fetchone()[0]
            if cursor and ((saved and saved[1]) or cursor[0] < min_freq):
                if stored != cursor[1]:
                    with conn:
                        conn.execute("UPDATE checkpoint SET complete=0 WHERE attr=?", (attr,))
                    raise ValueError(f"{attr}: reconciliation gap={cursor[1] - stored}; "
                                     f"stored={stored} total={cursor[1]}; incomplete")
                print(f"{attr}: already complete; stored={stored} total={cursor[1]}", flush=True)
                continue
            upper = cursor[0] if cursor else None
            expected_total = cursor[1] if cursor else None
            # Provenance page is a durable receipt ID, not the remote wlpage.
            page = saved[0] + 1 if saved else 1
            completed = 0

            while not max_pages or completed < max_pages:
                data, rows, retrieved_at = fetch(attr, min_freq, upper, page_size, prior, page)
                versions = (data["api_version"], data["manatee_version"])
                # Within a band the source's version must remain fixed too.
                prior = (GRAC_CORPUS, min_freq, page_size, *versions)
                if expected_total is None:
                    expected_total = data["total"]
                receipts = [(data, rows, retrieved_at, min_freq, upper, page_size)]
                terminal = bool(data["lastpage"])
                if not terminal:
                    boundary = rows[-1][1]
                    tie, tied_rows, tied_at = fetch(attr, boundary, boundary, page_size, prior, page)
                    receipts.append((tie, tied_rows, tied_at, boundary, boundary, page_size))
                    if len(tied_rows) < tie["total"]:
                        full, full_rows, full_at = fetch(attr, boundary, boundary, tie["total"], prior, page)
                        receipts.append((full, full_rows, full_at, boundary, boundary, tie["total"]))
                        if full["total"] != tie["total"]:
                            raise ValueError("GRAC tie total changed; checkpoint unchanged")
                        tie, tied_rows = full, full_rows
                    if len(tied_rows) != tie["total"] or not tie["lastpage"]:
                        raise ValueError(f"GRAC split tie incomplete: stored={len(tied_rows)} "
                                         f"total={tie['total']}; checkpoint unchanged")
                    by_string = {row[0]: row for row in tied_rows}
                    if any(by_string.get(row[0]) != row
                           for receipt in receipts for row in receipt[1] if row[1] == boundary):
                        raise ValueError("GRAC tie changed or omitted a returned item; checkpoint unchanged")
                    # Every higher frequency is fully in the first page; replace
                    # its partial final tie with the complete exact-frequency set.
                    band = [row for row in rows if row[1] > boundary] + tied_rows
                    next_upper = boundary - 1
                    terminal = next_upper < min_freq or len(band) == data["total"]
                    if terminal:
                        next_upper = min_freq - 1
                else:
                    band = rows
                    next_upper = min_freq - 1
                with conn:
                    inserted = 0
                    for _receipt_data, receipt_rows, timestamp, floor, ceiling, size in receipts:
                        before = conn.total_changes
                        conn.executemany(
                            "INSERT INTO items (attr,str,frq,relfreq,page) VALUES (?,?,?,?,?) "
                            "ON CONFLICT(attr,str) DO NOTHING",
                            [(attr, *row, page) for row in receipt_rows],
                        )
                        inserted += conn.total_changes - before
                        conn.execute(
                            "INSERT INTO provenance VALUES (?,?,?,?,?,?,?,?,?)",
                            (attr, page, GRAC_CORPUS, *versions, min_freq, page_size, timestamp, len(receipt_rows)),
                        )
                        conn.execute("INSERT INTO request_bounds VALUES (?,?,?,?,?)",
                                     (attr, page, floor, ceiling, size))
                        page += 1
                    stored = conn.execute("SELECT COUNT(*) FROM items WHERE attr=?", (attr,)).fetchone()[0]
                    # 'total' on a bounded request counts the remaining window.
                    # Reconcile its complete band and unvisited remainder against
                    # the original unbounded denominator, detecting source drift.
                    above = conn.execute("SELECT COUNT(*) FROM items WHERE attr=? AND frq>?",
                                         (attr, upper)).fetchone()[0] if upper is not None else 0
                    gap = expected_total - stored if terminal else expected_total - above - data["total"]
                    complete = terminal and gap == 0
                    conn.execute(
                        "INSERT INTO checkpoint VALUES (?,?,?) ON CONFLICT(attr) DO UPDATE SET "
                        "last_completed_page=excluded.last_completed_page, complete=excluded.complete",
                        (attr, page - 1, int(complete)),
                    )
                    conn.execute("INSERT INTO frequency_cursor VALUES (?,?,?) ON CONFLICT(attr) DO UPDATE SET "
                                 "next_max_freq=excluded.next_max_freq, expected_total=excluded.expected_total",
                                 (attr, next_upper, expected_total))
                counts[attr] += inserted
                completed += 1
                print(f"{attr}: page={page - 1} rows={len(band)} run_rows={counts[attr]} "
                      f"stored={stored} total={expected_total} complete={complete}", flush=True)
                if gap:
                    raise ValueError(f"{attr}: reconciliation gap={gap}; "
                                     f"stored={stored} total={expected_total}; incomplete")
                if terminal:
                    break
                upper = next_upper
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
HTTP 429 halts immediately: wait before resuming and honour Retry-After when supplied.
HTTP 403 halts immediately: stop. Empty pages without lastpage=1 use bounded retries.
Frequency windows finish their last tie in full; completion requires stored distinct items = server total.
Legacy offset checkpoints replay once, retaining existing rows and retrieval provenance.
Related: #10087; #9969; scripts/rag/source_query.py; sources MCP query_grac.
""",
    )
    parser.add_argument("--db", type=Path, help="Local SQLite destination (default: resolved data/grac_frequency.db); e.g. scratch.db")
    parser.add_argument("--attr", choices=("lemma", "word"), action="append", help="Attribute to ingest; repeat for both (default: lemma and word)")
    parser.add_argument("--min-freq", type=int, default=5, help="Inclusive frequency floor (default: 5); e.g. 10")
    parser.add_argument("--page-size", type=int, default=1000, help="Items per page, wlmaxitems (default: 1000); e.g. 100")
    parser.add_argument("--max-pages", type=int, default=0, help="Frequency bands per attribute this run; tie recovery may add requests (default: 0 = unbounded); e.g. 2")
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
    except (GracIngestHalted, OSError, sqlite3.Error, requests.RequestException, ValueError) as exc:
        print(f"GRAC ingest halted: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"GRAC ingest: {counts}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
