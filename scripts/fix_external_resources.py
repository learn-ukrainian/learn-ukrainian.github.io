#!/usr/bin/env python3
"""Audit and clean external_resources.yaml.

Detects and removes bad entries: YouTube search URLs, generic homepages,
overused URLs, HTTP/HTTPS duplicates, and within-module duplicates.

Usage:
    .venv/bin/python scripts/fix_external_resources.py --audit
    .venv/bin/python scripts/fix_external_resources.py --clean --dry-run
    .venv/bin/python scripts/fix_external_resources.py --clean --write
    .venv/bin/python scripts/fix_external_resources.py --clean --write --max-uses 5

Issue: #752
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import yaml

RESOURCES_PATH = Path(__file__).resolve().parent.parent / "docs" / "resources" / "external_resources.yaml"

# Categories of entries within a module
CATEGORIES = ("youtube", "articles", "podcasts", "books", "websites")

# ---------------------------------------------------------------------------
# Detection functions
# ---------------------------------------------------------------------------

# Domains where a bare path (just "/" or empty) means "generic homepage"
_HOMEPAGE_DOMAINS = {
    "www.youtube.com", "youtube.com",
    "uacorpus.org", "www.uacorpus.org",
    "lcorp.ulif.org.ua",
    "litopys.org.ua", "www.litopys.org.ua",
    "www.ukrainianlessons.com", "ukrainianlessons.com",
    "talkukrainian.com", "www.talkukrainian.com",
}


def is_youtube_search_url(url: str) -> bool:
    """URL is a YouTube search results page, not a specific video."""
    return "youtube.com/results?" in url or "youtube.com/results/" in url


def is_generic_homepage(url: str) -> bool:
    """URL points to a bare domain root with no meaningful path."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    # Bare channel pages like youtube.com/@channel are not homepages
    path = parsed.path.rstrip("/")
    if not path:
        return parsed.hostname in _HOMEPAGE_DOMAINS if parsed.hostname else False
    return False


def is_youtube_channel_page(url: str) -> bool:
    """URL is a YouTube channel/user page, not a specific video."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.hostname not in ("www.youtube.com", "youtube.com"):
        return False
    path = parsed.path.rstrip("/")
    return path.startswith("/@") or path.startswith("/c/") or path.startswith("/channel/")


def normalize_url(url: str) -> str:
    """Normalize HTTP→HTTPS and strip trailing slashes for comparison."""
    url = url.strip()
    if url.startswith("http://"):
        url = "https://" + url[7:]
    return url.rstrip("/")


def build_url_usage_map(resources: dict) -> Counter:
    """Count how many modules each normalized URL appears in."""
    usage: Counter = Counter()
    for _slug, module in resources.items():
        if not isinstance(module, dict):
            continue
        seen_in_module: set[str] = set()
        for cat in CATEGORIES:
            entries = module.get(cat, [])
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                norm = normalize_url(entry.get("url", ""))
                if norm:
                    seen_in_module.add(norm)
        usage.update(seen_in_module)
    return usage


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

def audit(resources: dict, max_uses: int = 10) -> dict:
    """Analyze resources and return report dict."""
    url_usage = build_url_usage_map(resources)

    report = {
        "youtube_search": [],
        "generic_homepage": [],
        "channel_page": [],
        "overused": [],
        "within_module_dupes": [],
        "http_entries": [],
        "total_entries": 0,
        "total_modules": 0,
    }

    for slug, module in resources.items():
        if not isinstance(module, dict):
            continue
        report["total_modules"] += 1
        seen_urls: set[str] = set()

        for cat in CATEGORIES:
            entries = module.get(cat, [])
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                report["total_entries"] += 1
                url = entry.get("url", "")
                norm = normalize_url(url)

                if is_youtube_search_url(url):
                    report["youtube_search"].append((slug, cat, url))
                if is_generic_homepage(url):
                    report["generic_homepage"].append((slug, cat, url))
                if is_youtube_channel_page(url):
                    report["channel_page"].append((slug, cat, url))
                if url.startswith("http://"):
                    report["http_entries"].append((slug, cat, url))
                if norm in seen_urls:
                    report["within_module_dupes"].append((slug, cat, url))
                seen_urls.add(norm)

    # Overused: URLs exceeding max_uses threshold
    for url, count in url_usage.most_common():
        if count <= max_uses:
            break
        report["overused"].append((url, count))

    return report


def print_audit(report: dict) -> None:
    """Print human-readable audit report."""
    print(f"\n{'='*60}")
    print("External Resources Audit")
    print(f"{'='*60}")
    print(f"Total entries: {report['total_entries']}")
    print(f"Total modules with entries: {report['total_modules']}")

    sections = [
        ("YouTube search URLs (not real videos)", "youtube_search"),
        ("Generic homepage URLs", "generic_homepage"),
        ("YouTube channel pages (not specific videos)", "channel_page"),
        ("HTTP (should be HTTPS)", "http_entries"),
        ("Within-module duplicates", "within_module_dupes"),
    ]

    total_bad = 0
    for title, key in sections:
        items = report[key]
        total_bad += len(items)
        print(f"\n--- {title}: {len(items)} ---")
        for item in items[:10]:
            if len(item) == 3:
                slug, cat, url = item
                print(f"  [{slug}] ({cat}) {url}")
            else:
                print(f"  {item}")
        if len(items) > 10:
            print(f"  ... and {len(items) - 10} more")

    overused = report["overused"]
    print(f"\n--- Overused URLs (5+ modules): {len(overused)} distinct URLs ---")
    for url, count in overused[:15]:
        print(f"  [{count:3d} modules] {url[:80]}")
    if len(overused) > 15:
        print(f"  ... and {len(overused) - 15} more")
    total_bad += sum(count for _, count in overused)

    print(f"\n{'='*60}")
    print(f"Total problematic entries: ~{total_bad}")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------

def clean(resources: dict, max_uses: int = 10) -> tuple[dict, dict]:
    """Remove bad entries from resources dict.

    Returns (cleaned_resources, stats).
    """
    url_usage = build_url_usage_map(resources)
    stats = {
        "removed_search": 0,
        "removed_homepage": 0,
        "removed_channel": 0,
        "removed_overused": 0,
        "removed_dupes": 0,
        "normalized_http": 0,
        "removed_empty_modules": 0,
        "total_removed": 0,
        "total_remaining": 0,
    }

    cleaned = {}
    for slug, module in resources.items():
        if not isinstance(module, dict):
            continue

        cleaned_module: dict[str, list] = {}
        seen_urls: set[str] = set()

        for cat in CATEGORIES:
            entries = module.get(cat, [])
            if not isinstance(entries, list):
                continue

            kept: list[dict] = []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                url = entry.get("url", "")
                norm = normalize_url(url)

                # Remove YouTube search URLs
                if is_youtube_search_url(url):
                    stats["removed_search"] += 1
                    stats["total_removed"] += 1
                    continue

                # Remove generic homepages
                if is_generic_homepage(url):
                    stats["removed_homepage"] += 1
                    stats["total_removed"] += 1
                    continue

                # Remove channel pages
                if is_youtube_channel_page(url):
                    stats["removed_channel"] += 1
                    stats["total_removed"] += 1
                    continue

                # Remove overused URLs
                if url_usage.get(norm, 0) > max_uses:
                    stats["removed_overused"] += 1
                    stats["total_removed"] += 1
                    continue

                # Deduplicate within module
                if norm in seen_urls:
                    stats["removed_dupes"] += 1
                    stats["total_removed"] += 1
                    continue
                seen_urls.add(norm)

                # Normalize HTTP → HTTPS
                if url.startswith("http://"):
                    entry = {**entry, "url": norm}
                    stats["normalized_http"] += 1

                kept.append(entry)
                stats["total_remaining"] += 1

            if kept:
                cleaned_module[cat] = kept

        if cleaned_module:
            cleaned[slug] = cleaned_module
        else:
            stats["removed_empty_modules"] += 1

    return cleaned, stats


def print_stats(stats: dict) -> None:
    """Print cleaning stats."""
    print(f"\n{'='*60}")
    print("Cleaning Results")
    print(f"{'='*60}")
    print(f"Removed YouTube search URLs:    {stats['removed_search']}")
    print(f"Removed generic homepages:      {stats['removed_homepage']}")
    print(f"Removed channel pages:          {stats['removed_channel']}")
    print(f"Removed overused (>{stats.get('max_uses', 10)} modules): {stats['removed_overused']}")
    print(f"Removed within-module dupes:    {stats['removed_dupes']}")
    print(f"Normalized HTTP→HTTPS:          {stats['normalized_http']}")
    print(f"Removed empty modules:          {stats['removed_empty_modules']}")
    print("---")
    print(f"Total removed:                  {stats['total_removed']}")
    print(f"Total remaining:                {stats['total_remaining']}")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Audit and clean external_resources.yaml")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--audit", action="store_true", help="Report problems without changes")
    group.add_argument("--clean", action="store_true", help="Remove bad entries")
    parser.add_argument("--write", action="store_true",
                        help="Actually write changes (default is dry-run)")
    parser.add_argument("--max-uses", type=int, default=10,
                        help="Remove URLs appearing in more than N modules (default: 10)")
    parser.add_argument("--file", type=Path, default=RESOURCES_PATH,
                        help="Path to external_resources.yaml")

    args = parser.parse_args()

    if not args.file.exists():
        print(f"ERROR: {args.file} not found", file=sys.stderr)
        return 1

    data = yaml.safe_load(args.file.read_text("utf-8"))
    resources = data.get("resources", {})

    if args.audit:
        report = audit(resources, max_uses=args.max_uses)
        print_audit(report)
        return 0

    if args.clean:
        cleaned, stats = clean(resources, max_uses=args.max_uses)
        stats["max_uses"] = args.max_uses
        print_stats(stats)

        if not args.write:
            print("DRY-RUN — no changes written. Use --write to apply.\n")
            return 0

        # Write back
        new_data = {
            "version": _bump_version(data.get("version", "3.0")),
            "generated_at": data.get("generated_at", "unknown"),
            "cleaned_at": datetime.now(UTC).strftime("%Y-%m-%d"),
            "resources": cleaned,
        }
        args.file.write_text(
            yaml.dump(new_data, allow_unicode=True, default_flow_style=False, sort_keys=False),
            "utf-8",
        )
        print(f"Written to {args.file}")
        return 0

    return 1


def _bump_version(version: str) -> str:
    """Bump minor version: 3.0 → 3.1, 3.1 → 3.2, etc."""
    parts = version.split(".")
    if len(parts) == 2:
        return f"{parts[0]}.{int(parts[1]) + 1}"
    return f"{version}.1"


if __name__ == "__main__":
    sys.exit(main())
