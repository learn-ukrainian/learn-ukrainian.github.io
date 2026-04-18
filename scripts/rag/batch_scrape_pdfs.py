#!/usr/bin/env python3
"""Batch scrape PDF-based literary sources.

Wave 13 currently contains Doroshenko's two-volume
``Нарис історії України`` from Diasporiana.
"""

from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path

WAVE_13_DIASPORIANA = [
    {
        "slug": "doroshenko-narys-istoriyi-ukrayiny-t1",
        "vol": 1,
        "output": Path("data/literary_texts/wave13-doroshenko-narys-istoriyi-ukrayiny-t1.jsonl"),
    },
    {
        "slug": "doroshenko-narys-istoriyi-ukrayiny-t2",
        "vol": 2,
        "output": Path("data/literary_texts/wave13-doroshenko-narys-istoriyi-ukrayiny-t2.jsonl"),
    },
]

ALL_WAVES = {13: WAVE_13_DIASPORIANA}


def scrape_entry(entry: dict, dry_run: bool = False) -> int:
    output = entry["output"]
    if output.exists() and output.stat().st_size > 100:
        with output.open(encoding="utf-8") as handle:
            count = sum(1 for _ in handle)
        print(f"  [skip] {entry['slug']} already exists ({count} chunks)")
        return 0

    cmd = [
        ".venv/bin/python",
        "scripts/rag/scrape_diasporiana.py",
        "--vol",
        str(entry["vol"]),
    ]

    if dry_run:
        print(f"  [dry-run] Would scrape: {entry['slug']}")
        return 0

    print(f"  [scrape] {entry['slug']}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "unknown error"
        print(f"    [ERROR] {stderr[-400:]}")
        return 0

    if output.exists():
        with output.open(encoding="utf-8") as handle:
            count = sum(1 for _ in handle)
        print(f"    -> {count} chunks")
        return count
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch scrape PDF literary waves")
    parser.add_argument("--wave", type=int, nargs="+", default=[13], help="Wave(s) to scrape")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be scraped")
    parser.add_argument("--delay", type=float, default=3.0, help="Seconds between entries")
    args = parser.parse_args()

    total = 0
    for wave_num in args.wave:
        entries = ALL_WAVES.get(wave_num, [])
        if not entries:
            print(f"Wave {wave_num}: no entries defined")
            continue

        print(f"\n{'=' * 60}")
        print(f"WAVE {wave_num}: {len(entries)} PDF sources")
        print(f"{'=' * 60}")

        for entry in entries:
            count = scrape_entry(entry, dry_run=args.dry_run)
            total += count
            if count > 0 and not args.dry_run:
                time.sleep(args.delay)

    print(f"\n{'=' * 60}")
    print(f"TOTAL: {total} new chunks scraped")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
