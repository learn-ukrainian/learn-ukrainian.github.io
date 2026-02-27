#!/usr/bin/env python3
"""Convert inline "..." quotes to «» guillemets in research files.

Targets the "Ключові факти та цитати" section where primary source quotes
live as `- **Label**: "quote text"`. Converts to `- **Label**: «quote text»`
so the research_quality scorer counts them as primary_quotes.

Also scans for blockquote-style quotes (> "...") and converts to (> «...»).

Usage:
    .venv/bin/python scripts/enrich_research_quotes.py --dry-run
    .venv/bin/python scripts/enrich_research_quotes.py --apply
    .venv/bin/python scripts/enrich_research_quotes.py --apply --tracks bio istoriohrafiia
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from research_quality import _count_blockquotes, _count_guillemet_quotes


def _convert_quotes_in_line(line: str) -> tuple[str, int]:
    """Convert "..." quotes with Cyrillic 20+ chars to «» on a single line.

    Returns (new_line, conversion_count).
    """
    count = 0

    def replacer(m: re.Match) -> str:
        nonlocal count
        inner = m.group(1)
        # Only convert if it contains Cyrillic and is 20+ chars
        if len(inner) >= 20 and re.search(r'[а-яіїєґА-ЯІЇЄҐ]', inner):
            count += 1
            return f'«{inner}»'
        return m.group(0)

    new_line = re.sub(r'"([^"]+)"', replacer, line)
    return new_line, count


def process_file(filepath: Path, dry_run: bool = True) -> tuple[int, int, int]:
    """Process one research file. Returns (quotes_before, quotes_after, conversions)."""
    text = filepath.read_text("utf-8")

    bq_before = _count_blockquotes(text)
    gq_before = _count_guillemet_quotes(text)
    total_before = bq_before + gq_before

    # Process line by line — only convert in the key quotes section
    # and in blockquote lines (> "...")
    lines = text.split("\n")
    new_lines = []
    in_quotes_section = False
    total_conversions = 0

    for line in lines:
        # Track which section we're in
        if re.match(r'^## ', line):
            section_title = line[3:].strip().lower()
            in_quotes_section = (
                'цитат' in section_title
                or 'факт' in section_title and 'цитат' in section_title
            )

        # Convert quotes in the "Ключові факти та цитати" section
        if in_quotes_section and '"' in line:
            new_line, n = _convert_quotes_in_line(line)
            total_conversions += n
            new_lines.append(new_line)
        # Also convert quotes in blockquote lines anywhere
        elif line.strip().startswith('>') and '"' in line:
            new_line, n = _convert_quotes_in_line(line)
            total_conversions += n
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    new_text = "\n".join(new_lines)

    bq_after = _count_blockquotes(new_text)
    gq_after = _count_guillemet_quotes(new_text)
    total_after = bq_after + gq_after

    if not dry_run and total_conversions > 0:
        filepath.write_text(new_text, "utf-8")

    return total_before, total_after, total_conversions


def main():
    parser = argparse.ArgumentParser(description="Convert research file quotes to «» format")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Preview changes without writing (default)")
    parser.add_argument("--apply", action="store_true", help="Apply changes")
    parser.add_argument("--tracks", nargs="+", default=["hist", "istoriohrafiia", "bio"],
                        help="Tracks to process (default: hist istoriohrafiia bio)")
    args = parser.parse_args()

    dry_run = not args.apply

    if dry_run:
        print("DRY RUN — no files will be modified\n")
    else:
        print("APPLYING changes\n")

    total_files = 0
    total_improved = 0
    total_conversions = 0
    still_below = []

    for track in args.tracks:
        research_dir = PROJECT_ROOT / "curriculum" / "l2-uk-en" / track / "research"
        if not research_dir.exists():
            print(f"  {track}: no research/ directory, skipping")
            continue

        files = sorted(research_dir.glob("*-research.md"))
        track_improved = 0

        for fp in files:
            before, after, conversions = process_file(fp, dry_run=dry_run)
            total_files += 1

            if conversions > 0:
                total_improved += 1
                track_improved += 1
                total_conversions += conversions
                slug = fp.stem.replace("-research", "")

                if before < 3 and after >= 3:
                    status = "FIXED"
                elif before < 3:
                    status = f"IMPROVED ({after}/3)"
                    still_below.append((track, slug, after))
                else:
                    status = "already OK"

                print(f"  {track}/{slug}: {before} → {after} quotes "
                      f"({conversions} converted) [{status}]")

        if track_improved == 0:
            print(f"  {track}: no files needed conversion")

    print(f"\n{'='*60}")
    print(f"Files processed: {total_files}")
    print(f"Files improved:  {total_improved}")
    print(f"Total conversions: {total_conversions}")

    if still_below:
        print(f"\nStill below 3 quotes ({len(still_below)} files):")
        for track, slug, count in still_below:
            print(f"  {track}/{slug}: {count}/3")

    if dry_run:
        print("\nRe-run with --apply to write changes.")


if __name__ == "__main__":
    main()
