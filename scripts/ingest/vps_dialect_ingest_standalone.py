#!/usr/bin/env python3
"""VPS Standalone Ingestion Script for Ukrainian Author & Dialect Dictionaries.

Designed to run independently on a remote VPS without consuming local workstation compute.
Scrapes, parses, and structures dialect and author concordances from public academic sources:
- Lemko Dialect Dictionary (lemko.org)
- Shevchenko Concordance (Litopys.org.ua)

Outputs a compressed JSONL artifact `data/ingest/vps_dialect_dicts.jsonl.gz` that can
be rsynced into the local `data/sources.db` database.

Usage on VPS
------------
    python3 vps_dialect_ingest_standalone.py --sources all --output vps_dialect_dicts.jsonl.gz
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import ssl
import sys
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

LEMKO_DICT_URL = "http://lemko.org/slownik/lesow.htm"
SHEVCHENKO_DICT_BASE_URL = "http://litopys.org.ua/shevchenko/shev.htm"


@dataclass(frozen=True)
class DialectDictEntry:
    lemma: str
    source_name: str
    category: str  # e.g. "lemko", "shevchenko", "franko", "hutsul"
    definition: str
    sample_quote: str
    provenance_url: str


def fetch_url_text(url: str, timeout: int = 30) -> str:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
        content = resp.read()
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("windows-1251", errors="replace")


def parse_lemko_org_dictionary() -> list[DialectDictEntry]:
    """Parse Lemko dialect dictionary entries from lemko.org."""
    print("🌐 Fetching Lemko dialect dictionary from lemko.org...")
    entries: list[DialectDictEntry] = []
    try:
        html = fetch_url_text(LEMKO_DICT_URL)
        lines = html.splitlines()
        for raw_line in lines:
            line_clean = re.sub(r"<[^>]+>", "", raw_line).strip()
            # Match word - definition format
            if "-" in line_clean or "—" in line_clean:
                parts = re.split(r"\s*[-—]\s*", line_clean, maxsplit=1)
                if len(parts) == 2:
                    lemma = parts[0].strip()
                    definition = parts[1].strip()
                    # Validate Cyrillic lemma and reasonable headword length
                    if lemma and definition and len(lemma) < 50 and re.search(r"[\u0400-\u04FF]", lemma):
                        entries.append(
                            DialectDictEntry(
                                lemma=lemma,
                                source_name="Короткий словник лемківських говірок",
                                category="lemko",
                                definition=definition,
                                sample_quote="",
                                provenance_url=LEMKO_DICT_URL,
                            )
                        )
    except Exception as e:
        print(f"⚠️ Error fetching Lemko dictionary: {e}", file=sys.stderr)

    print(f"✅ Parsed {len(entries)} Lemko dialect entries.")
    return entries


def parse_shevchenko_concordance() -> list[DialectDictEntry]:
    """Parse Shevchenko concordance entries from Litopys.org.ua."""
    print("🌐 Fetching Shevchenko dictionary entries from Litopys.org.ua...")
    entries: list[DialectDictEntry] = []
    try:
        html = fetch_url_text(SHEVCHENKO_DICT_BASE_URL)
        # Extract dictionary links or bold headword terms
        matches = re.findall(r'<b[^>]*>(.*?)</b>\s*[-—]?\s*(.*?)(?=<br|<p|</td)', html, re.DOTALL)
        for lemma_raw, def_raw in matches:
            lemma = re.sub(r"<[^>]+>", "", lemma_raw).strip()
            definition = re.sub(r"<[^>]+>", "", def_raw).strip()
            if lemma and definition and len(lemma) < 50 and re.search(r"[\u0400-\u04FF]", lemma):
                entries.append(
                    DialectDictEntry(
                        lemma=lemma,
                        source_name="Словник мови Шевченка (1964)",
                        category="shevchenko",
                        definition=definition,
                        sample_quote="",
                        provenance_url=SHEVCHENKO_DICT_BASE_URL,
                    )
                )
    except Exception as e:
        print(f"⚠️ Error fetching Shevchenko concordance: {e}", file=sys.stderr)

    print(f"✅ Parsed {len(entries)} Shevchenko concordance entries.")
    return entries


def run_vps_ingestion(output_path: Path, sources: list[str]) -> int:
    all_entries: list[DialectDictEntry] = []

    if "all" in sources or "lemko" in sources:
        all_entries.extend(parse_lemko_org_dictionary())

    if "all" in sources or "shevchenko" in sources:
        all_entries.extend(parse_shevchenko_concordance())

    if not all_entries:
        print("❌ Error: Zero entries were scraped. Failing ingestion run.", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"💾 Saving {len(all_entries)} parsed dictionary entries to {output_path}...")

    with gzip.open(output_path, "wt", encoding="utf-8") as f:
        for entry in all_entries:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

    print("🎉 Ingestion complete!")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VPS Standalone Ingest for Dialect & Author Dictionaries")
    parser.add_argument("--output", type=Path, default=Path("data/ingest/vps_dialect_dicts.jsonl.gz"))
    parser.add_argument("--sources", nargs="+", default=["all"], help="Sources to scrape: lemko, shevchenko, all")
    args = parser.parse_args(argv)

    return run_vps_ingestion(args.output, args.sources)


if __name__ == "__main__":
    raise SystemExit(main())
