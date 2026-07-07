#!/usr/bin/env python3
"""Download selected Ukrainian school textbooks from pidruchnyk.com.ua.

Reads the selection from docs/l2-uk-direct/textbook-selection.yaml,
visits each book page, extracts PDF links, and downloads them.

Usage:
    .venv/bin/python scripts/crawl/download_textbooks.py [--dry-run] [--only GRADE]
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


class TitleGuardError(Exception):
    """Raised when the fetched page's title does not match selection criteria."""

    pass


def transliterate_ua(text: str) -> str:
    """Transliterate Ukrainian Cyrillic characters to Latin equivalents."""
    rules = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "h",
        "ґ": "g",
        "д": "d",
        "е": "e",
        "є": "ye",
        "ж": "zh",
        "з": "z",
        "и": "y",
        "і": "i",
        "ї": "yi",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "kh",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "shch",
        "ь": "",
        "ю": "yu",
        "я": "ya",
        "'": "",
    }
    res = []
    for char in text.lower():
        res.append(rules.get(char, char))
    return "".join(res)


def share_substring(s1: str, s2: str, min_len: int = 4) -> bool:
    """Check if s1 and s2 share a common substring of length >= min_len."""
    for i in range(len(s1) - min_len + 1):
        sub = s1[i : i + min_len]
        if sub in s2:
            return True
    return False


def check_filename_overlap(filename: str, subject: str, author: str) -> bool:
    """Check if the filename has overlap with the subject/author tokens (warn-only)."""
    fn_clean = filename.lower()
    # Check if check is feasible (e.g. not a google drive ID or hash)
    if len(fn_clean) > 20 and not any(c in fn_clean for c in "-_"):
        return True

    # Remove extension
    if fn_clean.endswith(".pdf"):
        fn_clean = fn_clean[:-4]

    # Tokenize subject
    subject_clean = subject.replace("_", " ").replace("-", " ").lower()
    sub_tokens = set(subject_clean.split())
    # Common subject abbreviations/translations
    if "mova" in subject_clean:
        sub_tokens.update(["ukr", "mova", "ukrmova", "bukvar", "chytannya", "chytannja"])
    if "literatura" in subject_clean or "zarlit" in subject_clean:
        sub_tokens.update(["ukr", "lit", "ukrlit", "zar", "zarlit", "literatura"])
    if "istoriia" in subject_clean:
        sub_tokens.update(["ist", "hist", "istor", "istoriya", "istorii"])
    if "vsesvitnia" in subject_clean:
        sub_tokens.update(["vsesv"])
    if "matematyka" in subject_clean:
        sub_tokens.update(["mat", "math"])
    if "khimiya" in subject_clean:
        sub_tokens.update(["khim", "chim"])
    if "biolohiia" in subject_clean:
        sub_tokens.update(["bio"])
    if "heohrafiya" in subject_clean or "heohrafia" in subject_clean or "geografiia" in subject_clean:
        sub_tokens.update(["heo", "geo"])
    if "fizyka" in subject_clean:
        sub_tokens.update(["fiz"])
    if "informatyka" in subject_clean:
        sub_tokens.update(["inf"])
    if "mystetstvo" in subject_clean:
        sub_tokens.update(["mys", "art", "mystectvo"])
    if "etyka" in subject_clean:
        sub_tokens.update(["ety"])
    if "zdorovia" in subject_clean:
        sub_tokens.update(["zdo", "zdorov"])
    if "pryroda" in subject_clean:
        sub_tokens.update(["pry", "piznaiemo"])

    # Check if there is any overlap with subject tokens
    subject_match = False
    for t in sub_tokens:
        if len(t) >= 4:
            if share_substring(t, fn_clean, 4):
                subject_match = True
                break
        else:
            if t in fn_clean:
                subject_match = True
                break

    # Tokenize author
    author_clean = author.lower()

    author_match = False
    for part in author_clean.split():
        part_trans = transliterate_ua(part)
        if len(part) >= 4:
            if share_substring(part, fn_clean, 4) or share_substring(part_trans, fn_clean, 4):
                author_match = True
                break
        else:
            if (part in fn_clean) or (part_trans in fn_clean):
                author_match = True
                break

    # Check overlap
    if not (subject_match and author_match):
        reasons = []
        if not subject_match:
            reasons.append("subject")
        if not author_match:
            reasons.append("author")
        print(
            f"  WARNING: PDF filename '{filename}' lacks overlap with {' and '.join(reasons)} (subject: '{subject}', author: '{author}')"
        )
        return False

    return True


def load_selection() -> list[dict]:
    """Load the book selection YAML."""
    with open(SELECTION_FILE) as f:
        data = yaml.safe_load(f)
    return data["books"]


def normalize_whitespace(text: str) -> str:
    """Normalize and collapse all whitespace (including NBSP) to single spaces in lowercase."""
    return " ".join(text.replace("\xa0", " ").split()).lower()


def extract_pdf_links(slug: str, author: str, grade: int, target_year: int | None = None) -> list[dict]:
    """Visit a book page, verify title guard, and extract PDF download links.

    Each page may contain multiple editions (e.g., 2025 + 2018) and multiple
    parts (Part 1, Part 2). We filter by target_year if provided, keeping only
    the PDFs whose filename contains that year. If target_year is None, return all.
    """
    url = f"{BASE_URL}/{slug}.html"
    print(f"  Fetching: {url}")

    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Title guard (hard)
    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else ""

    title_norm = normalize_whitespace(title_text)
    author_norm = normalize_whitespace(author)
    grade_class_norm = normalize_whitespace(f"{grade} клас")

    if author_norm not in title_norm or grade_class_norm not in title_norm:
        print(f"  Title Guard Mismatch for slug '{slug}':")
        print(f"    Expected author '{author}' and '{grade} клас' in title")
        print(f"    Actual title: '{title_text}'")
        raise TitleGuardError(f"Expected author '{author}' and '{grade} клас' in title. Got '{title_text}'")

    all_pdfs = []
    # 1. Search for normal pdf links
    for link in soup.find_all("a", href=re.compile(r"\.pdf$")):
        href = link["href"]
        if not href.startswith("http"):
            href = f"{BASE_URL}{href}" if href.startswith("/") else f"{BASE_URL}/{href}"
        text = link.get_text(strip=True)
        filename = href.split("/")[-1]
        all_pdfs.append({"url": href, "label": text, "filename": filename})

    # 2. Search for drive iframes if no pdf links found
    if not all_pdfs:
        for iframe in soup.find_all("iframe", src=re.compile(r"drive\.google\.com")):
            src = iframe.get("src", "")
            match = re.search(r"/file/d/([a-zA-Z0-9_-]+)", src)
            if not match:
                match = re.search(r"id=([a-zA-Z0-9_-]+)", src)
            if match:
                drive_id = match.group(1)
                all_pdfs.append(
                    {
                        "url": f"https://docs.google.com/uc?export=download&id={drive_id}",
                        "label": "Google Drive iframe",
                        "filename": f"{drive_id}.pdf",
                        "gdrive_id": drive_id,
                    }
                )

    if not target_year or not all_pdfs:
        return all_pdfs

    # Filter: keep only PDFs whose filename contains the target year OR GDrive PDFs
    filtered = [p for p in all_pdfs if p.get("gdrive_id") or str(target_year) in p["filename"]]

    # If no match for the exact year and no GDrive PDF, try the newest available
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
            if chunk:
                f.write(chunk)
                total += len(chunk)

    size_mb = total / (1024 * 1024)
    print(f"  OK ({size_mb:.1f} MB): {dest.name}")
    return True


def download_from_gdrive(drive_id: str, dest: Path, dry_run: bool = False) -> bool:
    """Download a file from Google Drive via uc?export=download.

    Handles the large-file confirmation warning if encountered.
    """
    if dest.exists():
        size_mb = dest.stat().st_size / (1024 * 1024)
        print(f"  SKIP (exists, {size_mb:.1f} MB): {dest.name}")
        return False

    if dry_run:
        print(f"  DRY-RUN would download from Google Drive ID: {drive_id}")
        print(f"    -> {dest}")
        return False

    print(f"  Downloading Google Drive ID {drive_id} to {dest.name}...")

    url = "https://docs.google.com/uc"
    session = requests.Session()
    session.headers.update(HEADERS)

    # Step 1: Initial request
    resp = session.get(url, params={"export": "download", "id": drive_id}, stream=True, timeout=120)
    resp.raise_for_status()

    # Check if we got the confirmation page
    confirm_token = None
    uuid_token = None
    content_type = resp.headers.get("Content-Type", "")
    if "text/html" in content_type:
        html_content = resp.text

        # 1. Parse HTML using BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Look for input fields
        confirm_input = soup.find("input", {"name": "confirm"})
        if confirm_input:
            confirm_token = confirm_input.get("value")
        uuid_input = soup.find("input", {"name": "uuid"})
        if uuid_input:
            uuid_token = uuid_input.get("value")

        # 2. Look in form actions or links
        if not confirm_token or not uuid_token:
            urls_to_check = []
            form = soup.find("form")
            if form and form.get("action"):
                urls_to_check.append(form.get("action"))
            for a in soup.find_all("a", href=True):
                urls_to_check.append(a["href"])

            for u in urls_to_check:
                confirm_match = re.search(r"[?&]confirm=([^&\"'\s>]+)", u)
                uuid_match = re.search(r"[?&]uuid=([^&\"'\s>]+)", u)
                if confirm_match and not confirm_token:
                    confirm_token = confirm_match.group(1)
                if uuid_match and not uuid_token:
                    uuid_token = uuid_match.group(1)

        # 3. Raw regex fallback
        if not confirm_token:
            match = re.search(r'confirm=([^&"\']+)', html_content)
            if match:
                confirm_token = match.group(1)
        if not uuid_token:
            match = re.search(r'uuid=([^&"\']+)', html_content)
            if match:
                uuid_token = match.group(1)

        # 4. Try cookie backup if confirm_token still not found
        if not confirm_token:
            for key, value in session.cookies.items():
                if key.startswith("download_warning"):
                    confirm_token = value
                    break

    # Step 2: Request again with token
    if confirm_token:
        if uuid_token:
            print(f"  Confirming large file download (confirm: {confirm_token}, uuid: {uuid_token})...")
        else:
            print(f"  Confirming large file download (token: {confirm_token})...")
        params = {"export": "download", "id": drive_id, "confirm": confirm_token}
        if uuid_token:
            params["uuid"] = uuid_token
        resp = session.get(url, params=params, stream=True, timeout=120)
        resp.raise_for_status()

    # Step 3: Write response content to file
    dest.parent.mkdir(parents=True, exist_ok=True)

    # We inspect the first chunk of the response to ensure it's a PDF
    chunks_iter = resp.iter_content(chunk_size=8192)
    try:
        first_chunk = next(chunks_iter)
    except StopIteration:
        first_chunk = b""

    # A real PDF starts with %PDF- magic bytes
    if not first_chunk.startswith(b"%PDF-"):
        # Not a PDF. Let's read the rest of the chunks to get the full HTML content.
        html_bytes = first_chunk
        for chunk in chunks_iter:
            if chunk:
                html_bytes += chunk

        # Parse title from HTML
        html_text = html_bytes.decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html_text, "html.parser")
        title = soup.title.string.strip() if (soup.title and soup.title.string) else "No Title Found"
        title = " ".join(title.split())

        print(f"  Google Drive returned non-PDF page. HTML Title: {title}")

        # Ensure no dest file remains
        if dest.exists():
            dest.unlink()

        raise ValueError(f"Downloaded payload is not a PDF. HTML Title: {title}")

    # It's a valid PDF. Write first chunk and stream the rest.
    total = 0
    with open(dest, "wb") as f:
        if first_chunk:
            f.write(first_chunk)
            total += len(first_chunk)
        for chunk in chunks_iter:
            if chunk:
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

        print(f"\n{'=' * 60}")
        print(f"[{book_id}] Grade {grade} — {author}")
        print(f"{'=' * 60}")

        if book.get("status") == "needs_manual_pdf" and not (book.get("slug") or book.get("gdrive_id")):
            print("  SKIP — needs manual PDF link (not yet available)")
            total_skipped += 1
            continue

        # Check for override_pdfs (manual PDF URLs when page is broken)
        override_pdfs = book.get("override_pdfs")
        gdrive_id = book.get("gdrive_id")

        if override_pdfs:
            pdfs = [{"url": url, "label": url.split("/")[-1], "filename": url.split("/")[-1]} for url in override_pdfs]
            print(f"  Using {len(pdfs)} override PDF(s)")
        elif gdrive_id and not slug:
            pdfs = [
                {
                    "url": f"https://docs.google.com/uc?export=download&id={gdrive_id}",
                    "label": "Google Drive (Registry)",
                    "filename": f"{gdrive_id}.pdf",
                    "gdrive_id": gdrive_id,
                }
            ]
            print("  Using registry Google Drive ID")
        else:
            target_year = None if args.all_editions else book.get("year")
            try:
                pdfs = extract_pdf_links(slug, author=author, grade=grade, target_year=target_year)
            except TitleGuardError:
                # Expected-vs-actual warning printed inside extract_pdf_links
                total_failed += 1
                time.sleep(CRAWL_DELAY)
                continue
            except Exception as e:
                print(f"  ERROR fetching page: {e}")
                total_failed += 1
                time.sleep(CRAWL_DELAY)
                continue

            if not pdfs:
                if gdrive_id:
                    pdfs = [
                        {
                            "url": f"https://docs.google.com/uc?export=download&id={gdrive_id}",
                            "label": "Google Drive (Registry Fallback)",
                            "filename": f"{gdrive_id}.pdf",
                            "gdrive_id": gdrive_id,
                        }
                    ]
                    print("  No PDFs on page, falling back to registry Google Drive ID")
                else:
                    print("  WARNING: No PDF links or iframes found on this page!")
                    total_failed += 1
                    time.sleep(CRAWL_DELAY)
                    continue

        print(f"  Found {len(pdfs)} PDF(s)")

        grade_dir = OUTPUT_DIR / f"grade-{grade:02d}"

        for i, pdf_info in enumerate(pdfs):
            pdf_url = pdf_info["url"]
            pdf_gdrive_id = pdf_info.get("gdrive_id")

            # Check overlap heuristic
            check_filename_overlap(pdf_info["filename"], book["subject"], author)

            # Canonical naming
            filename = f"{slug}.pdf" if len(pdfs) == 1 else f"{slug}-{i + 1}.pdf"
            dest = grade_dir / filename

            try:
                if pdf_gdrive_id:
                    downloaded = download_from_gdrive(pdf_gdrive_id, dest, dry_run=args.dry_run)
                else:
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

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"Downloaded: {total_downloaded}")
    print(f"Skipped (exist): {total_skipped}")
    print(f"Failed: {total_failed}")


if __name__ == "__main__":
    main()
