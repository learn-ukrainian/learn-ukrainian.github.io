#!/usr/bin/env python3
"""Scrape PULS vocabulary profile (puls.peremova.org) — CEFR-tagged Ukrainian words.

Extracts ~10K words with CEFR levels (A1-C1), POS, and thematic categories
from the PULS Digital Learning Platform.

Source: https://puls.peremova.org (Ukrainian Catholic University)
Paper: eLex2025-29-Synchak_etal.pdf

Output: data/puls/entries.jsonl

Usage:
    .venv/bin/python scripts/rag/scrape_puls.py
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "puls"
OUTPUT_FILE = OUTPUT_DIR / "entries.jsonl"

BASE_URL = "https://puls.peremova.org/entries"
HEADERS = {
    "User-Agent": "LearnUkrainian/1.0 (curriculum project; contact: github.com/learn-ukrainian)",
}
DELAY = 1.0  # Be respectful — 1 second between requests


def fetch_page(url: str) -> str:
    """Fetch a page with proper headers and delay."""
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_entries_page(html: str) -> list[dict]:
    """Parse word entries from an HTML page.

    Each entry row has: word, guideword, CEFR level, POS.
    """
    entries = []

    # Row-by-row parsing
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL)
    for row in rows:
        # Extract cells
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
        if len(cells) < 4:
            continue

        # First cell has the link with word
        link_match = re.search(r'href="/entries/(\d+)"[^>]*>([^<]+)</a>', cells[0])
        if not link_match:
            continue

        entry_id = link_match.group(1)
        word = link_match.group(2).strip()

        # Clean HTML from other cells
        guideword = re.sub(r"<[^>]+>", "", cells[1]).strip()
        level = re.sub(r"<[^>]+>", "", cells[2]).strip()
        pos = re.sub(r"<[^>]+>", "", cells[3]).strip()

        # Validate CEFR level
        if not re.match(r"^[ABC][12]$", level):
            continue

        entries.append({
            "id": f"puls-{entry_id}",
            "word": word,
            "guideword": guideword,
            "level": level,
            "pos": pos,
            "source": "PULS (puls.peremova.org)",
        })

    return entries


def scrape_all():
    """Scrape all pages of the PULS vocabulary list."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Scraping PULS vocabulary profile (puls.peremova.org)...")

    all_entries = []
    page = 1

    while True:
        url = f"{BASE_URL}?page={page}" if page > 1 else BASE_URL
        print(f"  Page {page}...", end="", flush=True)

        try:
            html = fetch_page(url)
        except Exception as e:
            print(f" ERROR: {e}")
            break

        entries = parse_entries_page(html)
        if not entries:
            print(" (no entries — done)")
            break

        all_entries.extend(entries)
        print(f" {len(entries)} entries (total: {len(all_entries)})")

        # Check if there's a next page
        if f"page={page + 1}" not in html:
            print("  No more pages.")
            break

        page += 1
        time.sleep(DELAY)

    # Write JSONL
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for entry in all_entries:
            # Build searchable text
            entry["text"] = (
                f"{entry['word']} ({entry['level']}, {entry['pos']})"
                f"{': ' + entry['guideword'] if entry['guideword'] else ''}"
            )
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Also write a simple CSV for quick lookups
    csv_path = OUTPUT_DIR / "puls_cefr.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("word,level,pos,guideword\n")
        for entry in all_entries:
            gw = entry["guideword"].replace('"', '""')
            f.write(f'"{entry["word"]}",{entry["level"]},{entry["pos"]},"{gw}"\n')

    # Stats
    from collections import Counter
    levels = Counter(e["level"] for e in all_entries)
    print(f"\n✅ Scraped {len(all_entries)} entries → {OUTPUT_FILE.name}")
    print(f"   CSV also saved → {csv_path.name}")
    print(f"   By level: {dict(sorted(levels.items()))}")


if __name__ == "__main__":
    scrape_all()
