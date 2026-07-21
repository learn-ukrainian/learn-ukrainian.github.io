#!/usr/bin/env python3
"""VPS Standalone Ingestion Script for Ukrainian Author & Dialect Dictionaries.

Designed to run independently on a remote VPS without consuming local workstation compute.
Enforces polite crawling standards (1.5s inter-request delay, educational User-Agent, exponential backoff)
to ensure zero server burden on public academic resources.

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
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

LEMKO_DICT_URL = "http://lemko.org/slownik/lesow.htm"
SHEVCHENKO_DICT_BASE_URL = "http://litopys.org.ua/shevchenko/shev.htm"

# Polite crawling defaults
DEFAULT_DELAY_SECONDS = 1.5
USER_AGENT = "LearnUkrainianEduBot/1.0 (+https://learn-ukrainian.github.io)"


@dataclass(frozen=True)
class DialectDictEntry:
    lemma: str
    source_name: str
    category: str  # e.g. "lemko", "shevchenko", "franko", "hutsul"
    definition: str
    sample_quote: str
    provenance_url: str


def fetch_url_text(url: str, timeout: int = 30, delay: float = DEFAULT_DELAY_SECONDS) -> str:
    """Fetch URL content politely with rate-limiting delay and exponential backoff."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    if delay > 0:
        time.sleep(delay)

    max_retries = 3
    backoff = 2.0

    # Primary attempt using standard TLS context
    standard_ctx = ssl.create_default_context()

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, context=standard_ctx, timeout=timeout) as resp:
                content = resp.read()
                try:
                    return content.decode("utf-8")
                except UnicodeDecodeError:
                    return content.decode("windows-1251", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < max_retries - 1:
                print(f"⚠️ Rate limited ({e.code}). Backing off {backoff}s...", file=sys.stderr)
                time.sleep(backoff)
                backoff *= 2.0
            else:
                raise
        except (urllib.error.URLError, ssl.SSLError):
            # Fallback for uncertified legacy academic sites (e.g. litopys.org.ua HTTP/TLS mismatch)
            if attempt == max_retries - 1:
                fallback_ctx = ssl.create_default_context()
                fallback_ctx.check_hostname = False
                fallback_ctx.verify_mode = ssl.CERT_NONE
                with urllib.request.urlopen(req, context=fallback_ctx, timeout=timeout) as resp:
                    content = resp.read()
                    try:
                        return content.decode("utf-8")
                    except UnicodeDecodeError:
                        return content.decode("windows-1251", errors="replace")

    raise RuntimeError(f"Failed to fetch {url} after {max_retries} attempts.")


def parse_lemko_org_dictionary() -> list[DialectDictEntry]:
    """Parse Lemko dialect dictionary entries from lemko.org politely."""
    print("🌐 Fetching Lemko dialect dictionary from lemko.org (polite mode)...")
    entries: list[DialectDictEntry] = []
    try:
        html = fetch_url_text(LEMKO_DICT_URL)
        lines = html.splitlines()
        for raw_line in lines:
            line_clean = re.sub(r"<[^>]+>", "", raw_line).strip()
            # Match strictly anchored Cyrillic headword - definition entries
            m = re.match(r"^([А-Яа-яІіЇїЄєҐґ'\-]+)\s*[-—]\s*(.+)", line_clean)
            if m:
                lemma = m.group(1).strip()
                definition = m.group(2).strip()
                if lemma and definition and len(lemma) < 50:
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
    """Parse Shevchenko concordance entries from Litopys.org.ua politely."""
    print("🌐 Fetching Shevchenko dictionary entries from Litopys.org.ua (polite mode)...")
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
