#!/usr/bin/env python3
"""Build data/pidruchnyk_urls.yaml from pidruchnyk.com.ua index pages.

Contact: https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
import yaml
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "sources.db"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "pidruchnyk_urls.yaml"
BASE_URL = "https://pidruchnyk.com.ua"
REQUEST_DELAY_S = 0.5
USER_AGENT = (
    "learn-ukrainian textbook mapper/1.0 "
    "(https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues)"
)

AUTHOR_NAMES = {
    "avramenko": "Авраменко",
    "betsa": "Беца",
    "bolshakova": "Большакова",
    "borzenko": "Борзенко",
    "burnejko": "Бурнейко",
    "burneyko": "Бурнейко",
    "galimov": "Галімов",
    "gisem": "Гісем",
    "glazova": "Глазова",
    "glazov": "Глазова",
    "golub": "Голуб",
    "hlibovska": "Хлібовська",
    "karaman": "Караман",
    "khlibovska": "Хлібовська",
    "kovalenko": "Коваленко",
    "kravcova": "Кравцова",
    "kravtsova": "Кравцова",
    "litvinova": "Літвінова",
    "mishhenko": "Міщенко",
    "onatiy": "Онатій",
    "ponomarova": "Пономарьова",
    "pometun": "Пометун",
    "savchenko": "Савченко",
    "schupak": "Щупак",
    "shchupak": "Щупак",
    "uhor": "Угор",
    "varzatska": "Варзацька",
    "vashulenko": "Вашуленко",
    "voron": "Ворон",
    "zabolotnij": "Заболотний",
    "zabolotnyi": "Заболотний",
    "zaharijchuk": "Захарійчук",
}


def source_file_author(source_file: str) -> str:
    """Resolve a Ukrainian surname from a source_file."""
    for key, label in AUTHOR_NAMES.items():
        if key in source_file:
            return label
    return source_file


def source_file_year(source_file: str) -> str | None:
    """Extract textbook year from source_file."""
    parts = source_file.split("-")
    for part in reversed(parts):
        if part.isdigit() and len(part) == 4:
            return part
    return None


def source_file_category(source_file: str) -> str | None:
    """Map a source_file to the pidruchnyk index path that should contain it."""
    grade = source_file.split("-", 1)[0]

    if "bukvar" in source_file:
        return f"/{grade}klas/bukvar/"
    if "ukrlit" in source_file or "ukrajinska-literatura" in source_file:
        return f"/{grade}klas/ukr_literatura{grade}/"
    if "istori" in source_file:
        if grade == "5":
            return "/5klas/istoria_ukrainy5/"
        if grade == "6":
            return "/6klas/istorija_starodav6/"
        return f"/{grade}klas/istorija_ukrainy{grade}/"
    if grade == "2":
        return "/2klas/ukrainska/"
    if grade == "3":
        return "/3klas/ukrainska3/"
    if grade == "4":
        return "/4klas/ridna_mova4/"
    return f"/{grade}klas/ukrainska{grade}/"


def load_source_files(db_path: Path) -> list[str]:
    """Load the distinct textbook source_file IDs from SQLite."""
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT DISTINCT source_file FROM textbooks ORDER BY source_file"
        ).fetchall()
    finally:
        conn.close()
    return [row[0] for row in rows]


def load_existing_mapping(path: Path) -> dict[str, str]:
    """Load an existing YAML mapping if present."""
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text("utf-8")) or {}
    return {
        str(source_file): str(url)
        for source_file, url in data.items()
        if isinstance(source_file, str) and isinstance(url, str)
    }


def fetch_category_books(session: requests.Session, category_path: str) -> list[dict[str, str]]:
    """Fetch one category page and extract linked textbook cards."""
    response = session.get(urljoin(BASE_URL, category_path), timeout=30)
    response.raise_for_status()
    time.sleep(REQUEST_DELAY_S)

    soup = BeautifulSoup(response.text, "html.parser")
    books: dict[str, dict[str, str]] = {}

    for anchor in soup.select("a[href$='.html']"):
        href = anchor.get("href", "").strip()
        title = " ".join(anchor.get_text(" ", strip=True).split())
        if not href or not title or "клас" not in title.lower():
            continue
        url = urljoin(BASE_URL, href)
        books[url] = {"title": title, "url": url}

    return [books[url] for url in sorted(books)]


def match_book(source_file: str, books: list[dict[str, str]]) -> dict[str, str] | None:
    """Find a confident pidruchnyk page match for one source_file."""
    author = source_file_author(source_file)
    year = source_file_year(source_file)
    author_matches = [
        book
        for book in books
        if author.lower() in book["title"].lower()
    ]
    if not author_matches:
        return None

    if year is not None:
        author_matches = [
            book for book in author_matches if year in book["title"]
        ]
        if not author_matches:
            return None

    if source_file.endswith("-prof"):
        prof_matches = [book for book in author_matches if "проф" in book["title"].lower()]
        if len(prof_matches) == 1:
            return prof_matches[0]
    else:
        standard_matches = [book for book in author_matches if "проф" not in book["title"].lower()]
        if len(standard_matches) == 1:
            return standard_matches[0]

    if len(author_matches) == 1:
        return author_matches[0]
    return None


def validate_url(session: requests.Session, url: str) -> bool:
    """Require a clean HTTP 200 HEAD response."""
    response = session.head(url, allow_redirects=True, timeout=30)
    time.sleep(REQUEST_DELAY_S)
    return response.status_code == 200


def build_mapping(db_path: Path, output_path: Path, force: bool) -> int:
    """Build or update the pidruchnyk mapping file."""
    source_files = load_source_files(db_path)
    existing = {} if force else load_existing_mapping(output_path)
    pending = [source_file for source_file in source_files if source_file not in existing]

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    categories = sorted(
        {
            category
            for source_file in pending
            for category in [source_file_category(source_file)]
            if category is not None
        }
    )
    books_by_category = {
        category: fetch_category_books(session, category)
        for category in categories
    }

    mapping = dict(existing)
    skipped: list[str] = []

    for source_file in pending:
        category = source_file_category(source_file)
        books = books_by_category.get(category or "", [])
        match = match_book(source_file, books)
        if match is None:
            skipped.append(source_file)
            continue
        if not validate_url(session, match["url"]):
            skipped.append(source_file)
            continue
        mapping[source_file] = match["url"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        yaml.safe_dump(dict(sorted(mapping.items())), allow_unicode=True, sort_keys=False),
        "utf-8",
    )

    for source_file in skipped:
        print(source_file, file=sys.stderr)

    return len(mapping)


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--force", action="store_true", help="Refresh all entries")
    args = parser.parse_args()

    count = build_mapping(args.db, args.output, args.force)
    print(f"Wrote {count} pidruchnyk URLs to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
