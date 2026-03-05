#!/usr/bin/env python3
"""Audit external_resources.yaml for dead/broken URLs.

Checks URL liveness with HEAD requests (falls back to GET).
Reports dead links, redirects, and duplicates.

Usage:
    .venv/bin/python scripts/audit_external_resources.py          # Full audit
    .venv/bin/python scripts/audit_external_resources.py --fix     # Remove dead links
    .venv/bin/python scripts/audit_external_resources.py --stats   # Stats only

GitHub issue: #725
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml

RESOURCES_FILE = Path(__file__).resolve().parent.parent / "docs" / "resources" / "external_resources.yaml"

# Timeout per request (seconds)
REQUEST_TIMEOUT = 15

# User-Agent to avoid bot blocks
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) learn-ukrainian-audit/1.0",
}


def load_resources() -> dict:
    with open(RESOURCES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def extract_urls(data: dict) -> list[dict]:
    """Extract all URLs with their module/category context."""
    results = []
    for module, categories in data.get("resources", {}).items():
        if not isinstance(categories, dict):
            continue
        for cat, items in categories.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict) and "url" in item:
                    results.append({
                        "module": module,
                        "category": cat,
                        "title": item.get("title", ""),
                        "url": item["url"],
                    })
    return results


def check_url(url: str) -> dict:
    """Check if a URL is alive. Returns status dict."""
    try:
        # Try HEAD first (faster)
        resp = requests.head(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if resp.status_code == 405:
            # HEAD not allowed, try GET
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True, stream=True)
            resp.close()

        return {
            "status": resp.status_code,
            "ok": resp.status_code < 400,
            "redirected": len(resp.history) > 0,
            "final_url": resp.url if len(resp.history) > 0 else None,
            "error": None,
        }
    except requests.exceptions.Timeout:
        return {"status": 0, "ok": False, "redirected": False, "final_url": None, "error": "timeout"}
    except requests.exceptions.ConnectionError:
        return {"status": 0, "ok": False, "redirected": False, "final_url": None, "error": "connection_error"}
    except requests.exceptions.TooManyRedirects:
        return {"status": 0, "ok": False, "redirected": True, "final_url": None, "error": "too_many_redirects"}
    except requests.exceptions.RequestException as e:
        return {"status": 0, "ok": False, "redirected": False, "final_url": None, "error": str(e)[:80]}


def find_duplicates(entries: list[dict]) -> dict[str, list[str]]:
    """Find URLs used across multiple modules."""
    url_modules: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        url_modules[entry["url"]].append(entry["module"])
    return {url: modules for url, modules in url_modules.items() if len(modules) > 1}


def remove_dead_links(data: dict, dead_urls: set[str]) -> int:
    """Remove dead URLs from the resources dict. Returns count removed."""
    removed = 0
    for module, categories in list(data.get("resources", {}).items()):
        if not isinstance(categories, dict):
            continue
        for cat, items in list(categories.items()):
            if not isinstance(items, list):
                continue
            original_len = len(items)
            categories[cat] = [
                item for item in items
                if not (isinstance(item, dict) and item.get("url") in dead_urls)
            ]
            removed += original_len - len(categories[cat])
        # Clean up empty categories
        empty_cats = [c for c, items in categories.items() if isinstance(items, list) and not items]
        for c in empty_cats:
            del categories[c]
    # Clean up empty modules
    empty_mods = [m for m, cats in data.get("resources", {}).items()
                  if isinstance(cats, dict) and not cats]
    for m in empty_mods:
        del data["resources"][m]
    return removed


def main():
    parser = argparse.ArgumentParser(description="Audit external_resources.yaml URLs")
    parser.add_argument("--fix", action="store_true", help="Remove dead links from the file")
    parser.add_argument("--stats", action="store_true", help="Show stats only (no URL checking)")
    parser.add_argument("--skip-youtube", action="store_true", help="Skip YouTube URLs (rate-limited)")
    args = parser.parse_args()

    data = load_resources()
    entries = extract_urls(data)
    unique_urls = list(set(e["url"] for e in entries))

    print(f"Total URL references: {len(entries)}")
    print(f"Unique URLs: {len(unique_urls)}")

    # Domain stats
    domains: dict[str, int] = defaultdict(int)
    for url in unique_urls:
        domains[urlparse(url).netloc] += 1
    print(f"\nTop domains:")
    for domain, count in sorted(domains.items(), key=lambda x: -x[1])[:10]:
        print(f"  {domain}: {count}")

    # Duplicates
    dupes = find_duplicates(entries)
    if dupes:
        print(f"\nDuplicate URLs (shared across modules): {len(dupes)}")

    if args.stats:
        return

    # Check URLs
    print(f"\nChecking {len(unique_urls)} unique URLs...\n")
    dead = []
    redirected = []

    for i, url in enumerate(sorted(unique_urls), 1):
        if args.skip_youtube and "youtube.com" in url:
            continue

        result = check_url(url)
        status_str = f"[{i}/{len(unique_urls)}]"

        if not result["ok"]:
            err_detail = f" ({result['error']})" if result["error"] else f" (HTTP {result['status']})"
            print(f"  {status_str} DEAD{err_detail}: {url}")
            dead.append({"url": url, **result})
        elif result["redirected"]:
            redirected.append({"url": url, "final_url": result["final_url"]})

        # Rate limit: small delay between requests
        if i % 10 == 0:
            time.sleep(0.5)

    # Summary
    print(f"\n{'='*60}")
    print(f"Results:")
    print(f"  Alive:      {len(unique_urls) - len(dead)}")
    print(f"  Dead:       {len(dead)}")
    print(f"  Redirected: {len(redirected)}")

    if dead:
        print(f"\nDead URLs ({len(dead)}):")
        for d in dead:
            err = d.get("error") or f"HTTP {d['status']}"
            # Find which modules use this URL
            modules = [e["module"] for e in entries if e["url"] == d["url"]]
            print(f"  [{err}] {d['url']}")
            print(f"    Used in: {', '.join(modules[:3])}{'...' if len(modules) > 3 else ''}")

    if redirected:
        print(f"\nRedirected URLs ({len(redirected)}):")
        for r in redirected[:20]:
            print(f"  {r['url']}")
            print(f"    -> {r['final_url']}")
        if len(redirected) > 20:
            print(f"  ... and {len(redirected) - 20} more")

    if args.fix and dead:
        dead_urls = {d["url"] for d in dead}
        removed = remove_dead_links(data, dead_urls)
        with open(RESOURCES_FILE, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"\nRemoved {removed} dead link references from {RESOURCES_FILE.name}")

    sys.exit(1 if dead else 0)


if __name__ == "__main__":
    main()
