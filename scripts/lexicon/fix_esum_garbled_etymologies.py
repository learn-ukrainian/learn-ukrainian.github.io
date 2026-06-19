#!/usr/bin/env python3
"""Re-fetch Горох etymology rows for curated garbled ЕСУМ entries."""

from __future__ import annotations

import argparse
from pathlib import Path

from scripts.ingest.goroh_etymology_ingest import DEFAULT_USER_AGENT, ingest_goroh_etymology
from scripts.lexicon.esum_garbled import load_garbled_esum_entries

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "sources.db"


def goroh_lemmas() -> list[str]:
    """Return curated lemmas that should be backed by Горох."""
    entries = load_garbled_esum_entries().values()
    return sorted(
        str(entry["lemma"])
        for entry in entries
        if entry.get("mode") == "goroh" and entry.get("lemma")
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch Горох etymology cache rows for curated garbled ЕСУМ lemmas.",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help=f"SQLite DB path. Default: {DEFAULT_DB}")
    parser.add_argument("--dry-run", action="store_true", help="Fetch/report rows but do not update SQLite.")
    parser.add_argument("--refresh", action="store_true", help="Re-fetch even when a Goroh row is cached.")
    parser.add_argument("--sleep", type=float, default=1.75, help="Seconds pause between Goroh requests.")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds.")
    parser.add_argument(
        "--max-text-chars",
        type=int,
        default=1200,
        help="Maximum Goroh etymology prose characters stored per row.",
    )
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT, help="HTTP User-Agent for Goroh requests.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    lemmas = goroh_lemmas()
    if not lemmas:
        print("No curated Goroh lemmas found.")
        return 2
    fetched, loaded = ingest_goroh_etymology(
        args.db,
        lemmas,
        refresh=args.refresh,
        dry_run=args.dry_run,
        sleep_s=max(0.0, args.sleep),
        user_agent=args.user_agent,
        timeout=max(1, args.timeout),
        max_text_chars=max(1, args.max_text_chars),
    )
    print(f"Fetched {fetched} Goroh page(s); loaded {loaded} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
