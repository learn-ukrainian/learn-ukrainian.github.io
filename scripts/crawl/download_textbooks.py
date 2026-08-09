#!/usr/bin/env python3
"""Download selected Ukrainian school textbooks from pidruchnyk.com.ua.

Reads the selection from docs/l2-uk-direct/textbook-selection.yaml,
visits each book page, extracts PDF links, and downloads them.

Usage:
    .venv/bin/python scripts/crawl/download_textbooks.py [--dry-run] [--only GRADE]
"""

import argparse
import hashlib
import os
import re
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
import yaml
from bs4 import BeautifulSoup

try:
    from scripts.wiki.textbook_subjects import (
        AUTHOR_UK_BY_TRANSLIT,
        normalize_subject_slug,
        subject_for_source_file,
    )
except ModuleNotFoundError:
    # Preserve the documented direct-script entry point as well as ``-m``.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.wiki.textbook_subjects import (
        AUTHOR_UK_BY_TRANSLIT,
        normalize_subject_slug,
        subject_for_source_file,
    )

BASE_URL = "https://pidruchnyk.com.ua"
SELECTION_FILE = Path("docs/l2-uk-direct/textbook-selection.yaml")
OUTPUT_DIR = Path("data/textbooks")
PDF_SIGNATURE = b"%PDF-"
DOWNLOAD_CHUNK_SIZE = 1024 * 1024

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


class DownloadValidationError(ValueError):
    """Raised when a streamed response cannot be retained as a PDF."""

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


def find_retained_book_pdfs(retained_store: Path, book: dict) -> list[Path]:
    """Find canonical retained PDFs matching explicit book metadata.

    This is filename-only and therefore does not hydrate cloud-backed file
    contents.  Ambiguous matches are returned for the readiness audit to
    resolve; any match prevents an automatic duplicate acquisition.
    """
    try:
        grade = int(book["grade"])
        year = int(book["year"])
    except (KeyError, TypeError, ValueError):
        return []
    subject = normalize_subject_slug(str(book.get("subject") or ""))
    author = normalize_whitespace(str(book.get("author") or ""))
    author_tokens = {
        latin.casefold()
        for latin, cyrillic in AUTHOR_UK_BY_TRANSLIT.items()
        if normalize_whitespace(cyrillic) in author
    }
    if not subject or not author_tokens:
        return []

    matches: list[Path] = []
    for path in sorted(retained_store.rglob("*.pdf")):
        stem = path.stem.casefold().replace("_", "-")
        grade_match = re.search(r"(?:^|-)(\d{1,2})(?:-(\d{1,2}))?-klas(?:-|$)", stem)
        if grade_match is None:
            continue
        first_grade = int(grade_match.group(1))
        last_grade = int(grade_match.group(2) or first_grade)
        if not first_grade <= grade <= last_grade:
            continue
        retained_subject = subject_for_source_file(stem)
        if retained_subject != subject and not (
            grade == 1 and subject == "ukrmova" and retained_subject == "bukvar"
        ):
            continue
        if not any(re.search(rf"(?:^|-){re.escape(token)}(?:-|$)", stem) for token in author_tokens):
            continue
        years = {int(value) for value in re.findall(r"(?<!\d)(20\d{2})(?!\d)", stem)}
        if years and year not in years:
            continue
        matches.append(path)
    return matches


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

    # 2. Discover Google Drive mirrors in both anchors and iframes.  When a
    # page exposes one direct PDF and one Drive copy, they are alternate
    # transports for one logical book, not two volumes to retain separately.
    drive_candidates: list[dict[str, str]] = []
    seen_drive_ids: set[str] = set()
    drive_urls = [str(tag.get("href", "")) for tag in soup.find_all("a", href=True)]
    drive_urls.extend(
        str(tag.get("src", "")) for tag in soup.find_all("iframe", src=True)
    )
    for drive_url in drive_urls:
        drive_id = _google_drive_id(drive_url)
        if drive_id is None or drive_id in seen_drive_ids:
            continue
        seen_drive_ids.add(drive_id)
        drive_candidates.append(
            {
                "url": f"https://docs.google.com/uc?export=download&id={drive_id}",
                "label": "Google Drive mirror",
                "filename": f"{drive_id}.pdf",
                "gdrive_id": drive_id,
            }
        )

    if not all_pdfs:
        all_pdfs = drive_candidates
    elif len(all_pdfs) == 1 and drive_candidates:
        all_pdfs[0]["alternate_downloads"] = drive_candidates

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


def _google_drive_id(url: str) -> str | None:
    for pattern in (r"/file/d/([a-zA-Z0-9_-]+)", r"[?&]id=([a-zA-Z0-9_-]+)"):
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _fallback_for_component(
    fallback_pdfs: list[dict],
    *,
    primary_count: int,
    component_index: int,
) -> dict:
    """Match a fallback volume by deterministic component position."""
    if len(fallback_pdfs) != primary_count:
        raise DownloadValidationError(
            "fallback page volume count does not match the primary edition"
        )
    try:
        return fallback_pdfs[component_index]
    except IndexError as exc:
        raise DownloadValidationError("fallback component index is out of range") from exc


def extract_shkola_pdf_links(
    page_url: str,
    *,
    author: str,
    grade: int,
    target_year: int | None = None,
) -> list[dict]:
    """Resolve Shkola's download forms without retaining the PDF response.

    Shkola exposes an opaque ``vslink`` form value and returns the actual PDF
    or Google Drive locator as an HTTP redirect.  Only the redirect is
    resolved here; the bounded streaming downloader remains responsible for
    fetching and validating content.
    """
    parsed = urlparse(page_url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
        "shkola.in.ua",
        "www.shkola.in.ua",
    }:
        raise ValueError("Shkola resolver requires a shkola.in.ua page URL")

    session = requests.Session()
    session.headers.update(HEADERS)
    response = session.get(page_url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else ""
    title_norm = normalize_whitespace(title_text)
    if (
        normalize_whitespace(author) not in title_norm
        or normalize_whitespace(f"{grade} клас") not in title_norm
    ):
        raise TitleGuardError(
            f"Expected author '{author}' and '{grade} клас' in title. Got '{title_text}'"
        )

    resolved: list[dict] = []
    for form in soup.find_all("form"):
        button = form.find(attrs={"name": "vslink"})
        if button is None or not button.get("value"):
            continue
        label = " ".join(
            value
            for value in (
                button.get("title", ""),
                button.get_text(" ", strip=True),
            )
            if value
        )
        candidate_years = {int(value) for value in re.findall(r"(?<!\d)(20\d{2})(?!\d)", label)}
        if target_year is not None and candidate_years and target_year not in candidate_years:
            continue

        endpoint = urljoin(getattr(response, "url", page_url), form.get("action") or "")
        redirect = session.post(
            endpoint,
            data={"vslink": button["value"]},
            timeout=30,
            stream=True,
            allow_redirects=False,
        )
        try:
            redirect.raise_for_status()
            locator = redirect.headers.get("Location", "")
        finally:
            _safe_close(redirect)
        if not locator:
            continue
        locator = urljoin(endpoint, locator)
        drive_id = _google_drive_id(locator)
        item = {
            "url": locator,
            "label": label or "Shkola download",
            "filename": f"{drive_id}.pdf" if drive_id else locator.rsplit("/", 1)[-1],
        }
        if drive_id:
            item["gdrive_id"] = drive_id
        if item not in resolved:
            resolved.append(item)
    return resolved


def _safe_close(response: object) -> None:
    """Close a requests response when the response double supports it."""
    close = getattr(response, "close", None)
    if callable(close):
        close()


def _header(response: object, name: str) -> str:
    """Read a response header from real or minimal test response objects."""
    headers = getattr(response, "headers", {}) or {}
    if hasattr(headers, "get"):
        value = headers.get(name)
        if value is not None:
            return str(value)
        lower_name = name.lower()
        for key, candidate in headers.items():
            if str(key).lower() == lower_name:
                return str(candidate)
    return ""


def _validate_max_size(max_size_bytes: int | None) -> None:
    if max_size_bytes is not None and max_size_bytes <= 0:
        raise ValueError("max_size_bytes must be positive")


def _declared_size(response: object) -> int | None:
    value = _header(response, "Content-Length").strip()
    if not value:
        return None
    try:
        size = int(value)
    except ValueError:
        return None
    return size if size >= 0 else None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(DOWNLOAD_CHUNK_SIZE), b""):
            digest.update(block)
    return digest.hexdigest()


def _existing_pdf_hashes(
    retained_store: Path,
    *,
    size_bytes: int,
    exclude: Path | None = None,
) -> set[str]:
    """Hash only retained PDFs whose byte size can match the candidate.

    The retained store may be cloud-backed.  Reading every PDF would hydrate
    the whole library locally for each acquisition; unequal sizes already
    prove unequal content, so those files are never opened.
    """
    if not retained_store.exists():
        return set()
    excluded = exclude.resolve(strict=False) if exclude is not None else None
    hashes: set[str] = set()
    for path in sorted(
        candidate for candidate in retained_store.rglob("*") if candidate.suffix.casefold() == ".pdf"
    ):
        if (
            not path.is_file()
            or path.stat().st_size != size_bytes
            or (excluded is not None and path.resolve(strict=False) == excluded)
        ):
            continue
        hashes.add(_sha256_file(path))
    return hashes


def resolve_retained_store(path: Path) -> Path:
    """Resolve the configured retained store, including a Drive symlink.

    The downloader never creates a repository-local fallback store.  The
    caller must provide the existing retained location (the legacy default is
    still accepted for CLI compatibility and is resolved before use).
    """
    candidate = Path(path).expanduser()
    if not candidate.exists() or not candidate.is_dir():
        raise ValueError(f"retained store must be an existing directory: {candidate}")
    return candidate.resolve(strict=False)


def _invalid_pdf_title(path: Path) -> str:
    """Extract a bounded diagnostic title from an invalid response body."""
    try:
        html = path.read_bytes().decode("utf-8", errors="ignore")
    except OSError:
        return "No Title Found"
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else "No Title Found"
    return " ".join(title.split())


def _retain_response(
    response: object,
    dest: Path,
    *,
    retained_store: Path | None = None,
    max_size_bytes: int | None = None,
    invalid_detail: Callable[[Path], str] | None = None,
) -> bool:
    """Stream one response to a same-filesystem temp file, then retain it atomically.

    The response is never written to ``dest`` until its SHA-256, size, and PDF
    signature have passed validation.  The temporary file is removed on every
    path, including iterator, validation, duplicate, and rename failures.
    """
    _validate_max_size(max_size_bytes)
    declared_size = _declared_size(response)
    if max_size_bytes is not None and declared_size is not None and declared_size > max_size_bytes:
        raise DownloadValidationError(
            f"declared response size {declared_size} exceeds limit {max_size_bytes}"
        )

    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        dir=str(dest.parent),
        prefix=f".{dest.name}.",
        suffix=".part",
    )
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        digest = hashlib.sha256()
        total = 0
        first_nonempty = b""
        with temporary.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                if not chunk:
                    continue
                if isinstance(chunk, str):
                    raise DownloadValidationError("response yielded text instead of bytes")
                if not first_nonempty:
                    first_nonempty = bytes(chunk)
                total += len(chunk)
                if max_size_bytes is not None and total > max_size_bytes:
                    raise DownloadValidationError(
                        f"response size exceeds limit {max_size_bytes}"
                    )
                handle.write(chunk)
                digest.update(chunk)
            handle.flush()
            os.fsync(handle.fileno())

        if total == 0 or not first_nonempty.startswith(PDF_SIGNATURE):
            detail = invalid_detail(temporary) if invalid_detail is not None else ""
            suffix = f" HTML Title: {detail}" if detail else ""
            raise DownloadValidationError(f"Downloaded payload is not a PDF.{suffix}")

        retained_root = resolve_retained_store(retained_store or dest.parent)
        if digest.hexdigest() in _existing_pdf_hashes(
            retained_root,
            size_bytes=total,
            exclude=dest,
        ):
            print(f"  SKIP (duplicate content already retained): {dest.name}")
            return False

        # A concurrent or earlier caller may have created the canonical name
        # while this response was streaming.  Do not replace that final file.
        if dest.exists():
            size_mb = dest.stat().st_size / (1024 * 1024)
            print(f"  SKIP (exists, {size_mb:.1f} MB): {dest.name}")
            return False

        os.replace(temporary, dest)
        size_mb = total / (1024 * 1024)
        print(f"  OK ({size_mb:.1f} MB): {dest.name}")
        return True
    finally:
        if temporary.exists():
            temporary.unlink()


def download_pdf(
    url: str,
    dest: Path,
    dry_run: bool = False,
    *,
    retained_store: Path | None = None,
    retained_root: Path | None = None,
    max_size_bytes: int | None = None,
) -> bool:
    """Download one PDF with streamed validation and atomic retention.

    Returns True when a new file is retained and False when the canonical name
    or exact content is already retained.
    """
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
    try:
        resp.raise_for_status()
        return _retain_response(
            resp,
            dest,
            retained_store=retained_store or retained_root,
            max_size_bytes=max_size_bytes,
        )
    finally:
        _safe_close(resp)


def download_from_gdrive(
    drive_id: str,
    dest: Path,
    dry_run: bool = False,
    *,
    retained_store: Path | None = None,
    retained_root: Path | None = None,
    max_size_bytes: int | None = None,
) -> bool:
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
    confirm_url = url
    content_type = resp.headers.get("Content-Type", "")
    if "text/html" in content_type:
        html_content = resp.text

        # 1. Parse HTML using BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        download_form = soup.find("form")
        if download_form and download_form.get("action"):
            confirm_url = urljoin(getattr(resp, "url", url), download_form.get("action"))

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
            form = download_form
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
        _safe_close(resp)
        resp = session.get(confirm_url, params=params, stream=True, timeout=120)
        resp.raise_for_status()

    try:
        return _retain_response(
            resp,
            dest,
            retained_store=retained_store or retained_root,
            max_size_bytes=max_size_bytes,
            invalid_detail=_invalid_pdf_title,
        )
    finally:
        _safe_close(resp)


def main():
    parser = argparse.ArgumentParser(description="Download selected textbook PDFs")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded")
    parser.add_argument("--only", type=int, help="Only download for this grade")
    parser.add_argument(
        "--ids",
        nargs="+",
        help="Only process these exact selection ids (useful for a bounded acquisition packet)",
    )
    parser.add_argument(
        "--retained-store",
        "--output-dir",
        dest="retained_store",
        type=Path,
        default=OUTPUT_DIR,
        help="Existing retained PDF store; symlinks (including Google Drive) are resolved before use",
    )
    parser.add_argument(
        "--max-size-bytes",
        type=int,
        default=None,
        help="Optional hard limit for one streamed PDF response",
    )
    parser.add_argument(
        "--all-editions",
        action="store_true",
        help="Download ALL editions (not just the target year)",
    )
    args = parser.parse_args()

    books = load_selection()
    if args.only:
        books = [b for b in books if b["grade"] == args.only]
    if args.ids:
        requested = set(args.ids)
        known = {str(book["id"]) for book in books}
        unknown = sorted(requested - known)
        if unknown:
            parser.error("unknown selection id(s): " + ", ".join(unknown))
        books = [book for book in books if str(book["id"]) in requested]

    retained_store = resolve_retained_store(args.retained_store)
    print(f"Selected {len(books)} books to process")
    print(f"Output directory: {retained_store}")
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

        retained_matches = find_retained_book_pdfs(retained_store, book)
        if retained_matches:
            print(
                "  SKIP — retained source already matches metadata: "
                + ", ".join(path.name for path in retained_matches)
            )
            total_skipped += len(retained_matches)
            continue

        canonical_source = str(book.get("canonical_source") or "").strip()
        if not canonical_source:
            print("  ERROR — missing canonical_source for an unretained acquisition")
            total_failed += 1
            continue

        if book.get("status") == "needs_manual_pdf" and not (book.get("slug") or book.get("gdrive_id")):
            print("  SKIP — needs manual PDF link (not yet available)")
            total_skipped += 1
            continue

        # Check for override_pdfs (manual PDF URLs when page is broken)
        override_pdfs = book.get("override_pdfs")
        gdrive_id = book.get("gdrive_id")
        target_year = None if args.all_editions else book.get("year")

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
            pdfs = []
            try:
                pdfs = extract_pdf_links(slug, author=author, grade=grade, target_year=target_year)
            except TitleGuardError:
                # Expected-vs-actual warning printed inside extract_pdf_links
                time.sleep(CRAWL_DELAY)
            except Exception as e:
                print(f"  ERROR fetching page: {e}")
                time.sleep(CRAWL_DELAY)
            for fallback_page_url in book.get("fallback_page_urls", []):
                if pdfs:
                    break
                try:
                    pdfs = extract_shkola_pdf_links(
                        fallback_page_url,
                        author=author,
                        grade=grade,
                        target_year=target_year,
                    )
                    if pdfs:
                        print(f"  Using Shkola fallback: {fallback_page_url}")
                except Exception as exc:
                    print(f"  WARNING: fallback page failed: {exc}")

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

        grade_dir = retained_store / f"grade-{grade:02d}"

        for i, pdf_info in enumerate(pdfs):
            pdf_url = pdf_info["url"]
            pdf_gdrive_id = pdf_info.get("gdrive_id")

            # Check overlap heuristic
            check_filename_overlap(pdf_info["filename"], book["subject"], author)

            # Canonical naming
            filename = (
                f"{canonical_source}.pdf"
                if len(pdfs) == 1
                else f"{canonical_source}-{i + 1}.pdf"
            )
            dest = grade_dir / filename

            try:
                if pdf_gdrive_id:
                    downloaded = download_from_gdrive(
                        pdf_gdrive_id,
                        dest,
                        dry_run=args.dry_run,
                        retained_store=retained_store,
                        max_size_bytes=args.max_size_bytes,
                    )
                else:
                    downloaded = download_pdf(
                        pdf_url,
                        dest,
                        dry_run=args.dry_run,
                        retained_store=retained_store,
                        max_size_bytes=args.max_size_bytes,
                    )
            except Exception as e:
                print(f"  WARNING: primary download failed for {filename}: {e}")
                downloaded = None
                for alternate in pdf_info.get("alternate_downloads", []):
                    try:
                        alternate_drive_id = alternate.get("gdrive_id")
                        if alternate_drive_id:
                            downloaded = download_from_gdrive(
                                alternate_drive_id,
                                dest,
                                dry_run=args.dry_run,
                                retained_store=retained_store,
                                max_size_bytes=args.max_size_bytes,
                            )
                        else:
                            downloaded = download_pdf(
                                alternate["url"],
                                dest,
                                dry_run=args.dry_run,
                                retained_store=retained_store,
                                max_size_bytes=args.max_size_bytes,
                            )
                        print(f"  Used same-page mirror: {alternate['label']}")
                        break
                    except Exception as alternate_error:
                        print(f"  WARNING: same-page mirror failed: {alternate_error}")
                if downloaded is None:
                    for fallback_page_url in book.get("fallback_page_urls", []):
                        try:
                            fallback_pdfs = extract_shkola_pdf_links(
                                fallback_page_url,
                                author=author,
                                grade=grade,
                                target_year=target_year,
                            )
                            fallback = _fallback_for_component(
                                fallback_pdfs,
                                primary_count=len(pdfs),
                                component_index=i,
                            )
                            fallback_drive_id = fallback.get("gdrive_id")
                            if fallback_drive_id:
                                downloaded = download_from_gdrive(
                                    fallback_drive_id,
                                    dest,
                                    dry_run=args.dry_run,
                                    retained_store=retained_store,
                                    max_size_bytes=args.max_size_bytes,
                                )
                            else:
                                downloaded = download_pdf(
                                    fallback["url"],
                                    dest,
                                    dry_run=args.dry_run,
                                    retained_store=retained_store,
                                    max_size_bytes=args.max_size_bytes,
                                )
                            print(f"  Used Shkola fallback: {fallback_page_url}")
                            break
                        except Exception as fallback_error:
                            print(f"  WARNING: fallback download failed: {fallback_error}")
                if downloaded is None:
                    print(f"  ERROR downloading {filename}: all configured sources failed")
                    total_failed += 1
                    time.sleep(CRAWL_DELAY)
                    continue

            if downloaded:
                total_downloaded += 1
            else:
                total_skipped += 1

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
