#!/usr/bin/env python3
"""Download selected Ukrainian school textbooks from pidruchnyk.com.ua.

Reads the selection from docs/l2-uk-direct/textbook-selection.yaml,
visits each book page, extracts PDF links, and downloads them.

Usage:
    .venv/bin/python scripts/download_textbooks.py [--dry-run] [--only GRADE]
"""

import argparse
import re
import time
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup

BASE_URL = "https://pidruchnyk.com.ua"
SELECTION_FILE = Path("docs/l2-uk-direct/textbook-selection.yaml")
OUTPUT_DIR = Path("data/textbooks")

# Polite crawl delay (seconds between requests)
CRAWL_DELAY = 2.0

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def load_selection() -> list[dict]:
    """Load the book selection YAML."""
    with open(SELECTION_FILE) as f:
        data = yaml.safe_load(f)
    return data["books"]


def extract_pdf_links(slug: str, target_year: int | None = None) -> list[dict]:
    """Visit a book page and extract PDF download links.

    Each page may contain multiple editions (e.g., 2025 + 2018) and multiple
    parts (Part 1, Part 2). We filter by target_year if provided, keeping only
    the PDFs whose filename contains that year. If target_year is None, return all.
    """
    url = f"{BASE_URL}/{slug}.html"
    print(f"  Fetching: {url}")

    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    all_pdfs = []
    for link in soup.find_all("a", href=re.compile(r"\.pdf$")):
        href = link["href"]
        if not href.startswith("http"):
            href = f"{BASE_URL}{href}" if href.startswith("/") else f"{BASE_URL}/{href}"
        text = link.get_text(strip=True)
        filename = href.split("/")[-1]
        all_pdfs.append({"url": href, "label": text, "filename": filename})

    if not target_year or not all_pdfs:
        return all_pdfs

    # Filter: keep only PDFs whose filename contains the target year
    filtered = [p for p in all_pdfs if str(target_year) in p["filename"]]

    # If no match for the exact year, try the newest available
    if not filtered:
        # Extract years from filenames and pick the newest
        year_re = re.compile(r"(\d{4})")
        years_seen = set()
        for p in all_pdfs:
            m = year_re.search(p["filename"])
            if m:
                years_seen.add(int(m.group(1)))
        if years_seen:
            newest = max(years_seen)
            filtered = [p for p in all_pdfs if str(newest) in p["filename"]]
            print(f"  NOTE: Year {target_year} not found in PDFs, using {newest} instead")
        else:
            # No year in filenames at all — return all
            filtered = all_pdfs

    return filtered


def download_pdf(url: str, dest: Path, dry_run: bool = False) -> bool:
    """Download a PDF file. Returns True if downloaded, False if skipped."""
    if dest.exists():
        size_mb = dest.stat().st_size / (1024 * 1024)
        print(f"  SKIP (exists, {size_mb:.1f} MB): {dest.name}")
        return False

    if dry_run:
        print(f"  DRY-RUN would download: {url}")
        print(f"    -> {dest}")
        return False

    print(f"  Downloading: {dest.name}...")
    resp = requests.get(url, headers=HEADERS, timeout=120, stream=True)
    resp.raise_for_status()

    dest.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
            total += len(chunk)

    size_mb = total / (1024 * 1024)
    print(f"  OK ({size_mb:.1f} MB): {dest.name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Download selected textbook PDFs")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded")
    parser.add_argument("--only", type=int, help="Only download for this grade")
    parser.add_argument(
        "--all-editions",
        action="store_true",
        help="Download ALL editions (not just the target year)",
    )
    args = parser.parse_args()

    books = load_selection()
    if args.only:
        books = [b for b in books if b["grade"] == args.only]

    print(f"Selected {len(books)} books to process")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    total_downloaded = 0
    total_skipped = 0
    total_failed = 0

    for book in books:
        book_id = book["id"]
        grade = book["grade"]
        slug = book["slug"]
        author = book["author"]

        print(f"\n{'='*60}")
        print(f"[{book_id}] Grade {grade} — {author}")
        print(f"{'='*60}")

        if book.get("status") == "needs_manual_pdf":
            print("  SKIP — needs manual PDF link (not yet available)")
            total_skipped += 1
            continue

        # Check for override_pdfs (manual PDF URLs when page is broken)
        override_pdfs = book.get("override_pdfs")
        if override_pdfs:
            pdfs = [
                {"url": url, "label": url.split("/")[-1], "filename": url.split("/")[-1]}
                for url in override_pdfs
            ]
            print(f"  Using {len(pdfs)} override PDF(s)")
        else:
            target_year = None if args.all_editions else book.get("year")
            try:
                pdfs = extract_pdf_links(slug, target_year=target_year)
            except Exception as e:
                print(f"  ERROR fetching page: {e}")
                total_failed += 1
                time.sleep(CRAWL_DELAY)
                continue

            if not pdfs:
                print("  WARNING: No PDF links found on this page!")
                total_failed += 1
                time.sleep(CRAWL_DELAY)
                continue

        print(f"  Found {len(pdfs)} PDF(s)")

        grade_dir = OUTPUT_DIR / f"grade-{grade:02d}"

        for _i, pdf_info in enumerate(pdfs):
            pdf_url = pdf_info["url"]
            # Use the filename from the URL
            filename = pdf_url.split("/")[-1]
            dest = grade_dir / filename

            try:
                downloaded = download_pdf(pdf_url, dest, dry_run=args.dry_run)
                if downloaded:
                    total_downloaded += 1
                else:
                    total_skipped += 1
            except Exception as e:
                print(f"  ERROR downloading {filename}: {e}")
                total_failed += 1

            time.sleep(CRAWL_DELAY)

        time.sleep(CRAWL_DELAY)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Downloaded: {total_downloaded}")
    print(f"Skipped (exist): {total_skipped}")
    print(f"Failed: {total_failed}")


if __name__ == "__main__":
    main()
