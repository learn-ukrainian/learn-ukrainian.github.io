"""Scrape Ukrainian literary canon from ukrlib.com.ua.

Downloads full texts of works, chunks them, and saves as JSONL
compatible with the literary RAG pipeline.

Site structure:
    Author list:  /books/author.php?id={author_id}&page={N}
    Work text:    /books/printit.php?tid={work_id}&page={N}
    Encoding:     windows-1251
    Content:      <article class="prose" id="content">

Usage:
    # Scrape all P1 canon authors
    .venv/bin/python scripts/rag/scrape_ukrlib.py --priority P1

    # Scrape a specific author
    .venv/bin/python scripts/rag/scrape_ukrlib.py --author franko

    # Scrape a single work by tid
    .venv/bin/python scripts/rag/scrape_ukrlib.py --tid 645 --work "Захар Беркут" --author-name "Франко І."

    # List available authors
    .venv/bin/python scripts/rag/scrape_ukrlib.py --list

    # Dry run (show what would be scraped)
    .venv/bin/python scripts/rag/scrape_ukrlib.py --priority P1 --dry-run
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import ClassVar

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.config import CHUNK_MAX_TOKENS, CHUNK_MIN_TOKENS, LITERARY_DIR

BASE_URL = "https://www.ukrlib.com.ua"
DELAY_BETWEEN_PAGES = 0.5  # seconds
DELAY_BETWEEN_WORKS = 1.0

# ── Author/Work Definitions ─────────────────────────────────────────

# Priority 1: Core school canon (most referenced in curriculum)
P1_AUTHORS = {
    "franko": {
        "id": 2,
        "name": "Франко І.",
        "full_name": "Іван Франко",
        "years": "1856-1916",
        "genre_default": "prose",
        "period": "modern",
    },
    "lesya": {
        "id": 3,
        "name": "Українка Л.",
        "full_name": "Леся Українка",
        "years": "1871-1913",
        "genre_default": "poetry",
        "period": "modern",
    },
    "kotlyarevsky": {
        "id": 1,
        "name": "Котляревський І.",
        "full_name": "Іван Котляревський",
        "years": "1769-1838",
        "genre_default": "poetry",
        "period": "modern",
    },
    "kotsyubynsky": {
        "id": 4,
        "name": "Коцюбинський М.",
        "full_name": "Михайло Коцюбинський",
        "years": "1864-1913",
        "genre_default": "prose",
        "period": "modern",
    },
    "stefanyk": {
        "id": 11,
        "name": "Стефаник В.",
        "full_name": "Василь Стефаник",
        "years": "1871-1936",
        "genre_default": "prose",
        "period": "modern",
    },
}

# Priority 2: Extended canon
P2_AUTHORS = {
    "kvitka": {
        "id": 8,
        "name": "Квітка-Основ'яненко Г.",
        "full_name": "Григорій Квітка-Основ'яненко",
        "years": "1778-1843",
        "genre_default": "prose",
        "period": "modern",
    },
    "nechuy": {
        "id": 9,
        "name": "Нечуй-Левицький І.",
        "full_name": "Іван Нечуй-Левицький",
        "years": "1838-1918",
        "genre_default": "prose",
        "period": "modern",
    },
    "myrny": {
        "id": 10,
        "name": "Мирний П.",
        "full_name": "Панас Мирний",
        "years": "1849-1920",
        "genre_default": "prose",
        "period": "modern",
    },
    "vynnychenko": {
        "id": 14,
        "name": "Винниченко В.",
        "full_name": "Володимир Винниченко",
        "years": "1880-1951",
        "genre_default": "prose",
        "period": "modern",
    },
    "tychyna": {
        "id": 15,
        "name": "Тичина П.",
        "full_name": "Павло Тичина",
        "years": "1891-1967",
        "genre_default": "poetry",
        "period": "modern",
    },
    "rylsky": {
        "id": 16,
        "name": "Рильський М.",
        "full_name": "Максим Рильський",
        "years": "1895-1964",
        "genre_default": "poetry",
        "period": "modern",
    },
    "pidmohylny": {
        "id": 87,
        "name": "Підмогильний В.",
        "full_name": "Валер'ян Підмогильний",
        "years": "1901-1937",
        "genre_default": "prose",
        "period": "modern",
    },
    "kostenko": {
        "id": 5,
        "name": "Костенко Л.",
        "full_name": "Ліна Костенко",
        "years": "1930-",
        "genre_default": "poetry",
        "period": "modern",
    },
    "vovchok": {
        "id": 6,
        "name": "Вовчок М.",
        "full_name": "Марко Вовчок",
        "years": "1833-1907",
        "genre_default": "prose",
        "period": "modern",
    },
    "kobylyanska": {
        "id": 7,
        "name": "Кобилянська О.",
        "full_name": "Ольга Кобилянська",
        "years": "1863-1942",
        "genre_default": "prose",
        "period": "modern",
    },
}

# Priority 3: Розстріляне відродження + missing canon authors
P3_AUTHORS = {
    "khvylovy": {
        "id": 20,
        "name": "Хвильовий М.",
        "full_name": "Микола Хвильовий",
        "years": "1893-1933",
        "genre_default": "prose",
        "period": "modern",
    },
    "zerov": {
        "id": 187,
        "name": "Зеров М.",
        "full_name": "Микола Зеров",
        "years": "1890-1937",
        "genre_default": "poetry",
        "period": "modern",
    },
    "pluzhnyk": {
        "id": 244,
        "name": "Плужник Є.",
        "full_name": "Євген Плужник",
        "years": "1898-1936",
        "genre_default": "poetry",
        "period": "modern",
    },
    "antonych": {
        "id": 25,
        "name": "Антонич Б.-І.",
        "full_name": "Богдан-Ігор Антонич",
        "years": "1909-1937",
        "genre_default": "poetry",
        "period": "modern",
    },
    "vyshnya": {
        "id": 17,
        "name": "Вишня О.",
        "full_name": "Остап Вишня",
        "years": "1889-1956",
        "genre_default": "prose",
        "period": "modern",
    },
    "dovzhenko": {
        "id": 21,
        "name": "Довженко О.",
        "full_name": "Олександр Довженко",
        "years": "1894-1956",
        "genre_default": "prose",
        "period": "modern",
    },
    "oles": {
        "id": 18,
        "name": "Олесь О.",
        "full_name": "Олександр Олесь",
        "years": "1878-1944",
        "genre_default": "poetry",
        "period": "modern",
    },
    "stus": {
        "id": 106,
        "name": "Стус В.",
        "full_name": "Василь Стус",
        "years": "1938-1985",
        "genre_default": "poetry",
        "period": "modern",
    },
    "symonenko": {
        "id": 98,
        "name": "Симоненко В.",
        "full_name": "Василь Симоненко",
        "years": "1935-1963",
        "genre_default": "poetry",
        "period": "modern",
    },
    "bahryanyi": {
        "id": 29,
        "name": "Багряний І.",
        "full_name": "Іван Багряний",
        "years": "1906-1963",
        "genre_default": "prose",
        "period": "modern",
    },
    "yanovsky": {
        "id": 128,
        "name": "Яновський Ю.",
        "full_name": "Юрій Яновський",
        "years": "1902-1954",
        "genre_default": "prose",
        "period": "modern",
    },
    "drai_khmara": {
        "id": 199,
        "name": "Драй-Хмара М.",
        "full_name": "Михайло Драй-Хмара",
        "years": "1889-1939",
        "genre_default": "poetry",
        "period": "modern",
    },
    "hrinchenko": {
        "id": 48,
        "name": "Грінченко Б.",
        "full_name": "Борис Грінченко",
        "years": "1863-1910",
        "genre_default": "prose",
        "period": "modern",
    },
    "kulish": {
        "id": 19,
        "name": "Куліш П.",
        "full_name": "Пантелеймон Куліш",
        "years": "1819-1897",
        "genre_default": "prose",
        "period": "modern",
    },
    "sosyura": {
        "id": 104,
        "name": "Сосюра В.",
        "full_name": "Володимир Сосюра",
        "years": "1898-1965",
        "genre_default": "poetry",
        "period": "modern",
    },
    "honchar": {
        "id": 46,
        "name": "Гончар О.",
        "full_name": "Олесь Гончар",
        "years": "1918-1995",
        "genre_default": "prose",
        "period": "modern",
    },
    "tyutyunnyk": {
        "id": 110,
        "name": "Тютюнник Г.",
        "full_name": "Григір Тютюнник",
        "years": "1931-1980",
        "genre_default": "prose",
        "period": "modern",
    },
}

# Genre overrides for specific work title patterns
GENRE_PATTERNS = [
    (re.compile(r"вірш|поез|балад|гімн|думк", re.I), "poetry"),
    (re.compile(r"драм|комед|трагед|п['ʼ]єс", re.I), "drama"),
    (re.compile(r"казк|байк|леген", re.I), "fable"),
    (re.compile(r"повіст|оповідан|новел|нарис|роман", re.I), "prose"),
    (re.compile(r"стат|промов|лист|передмов|рецен", re.I), "letters"),
    (re.compile(r"біограф|життя|творч", re.I), "biography"),
]


def guess_genre(title: str, default: str) -> str:
    """Guess genre from work title."""
    for pattern, genre in GENRE_PATTERNS:
        if pattern.search(title):
            return genre
    return default


# ── HTML Parsing ─────────────────────────────────────────────────────

class UkrlibTextExtractor(HTMLParser):
    """Extract text from ukrlib.com.ua article pages.

    Handles both prose (<p> tags) and poetry (<br> line breaks).
    Skips noise divs (ads, "read also") and blockquote.cita (source metadata).
    """

    # CSS classes of noise divs inside <article> that should be skipped
    _NOISE_CLASSES: ClassVar[set[str]] = {"post-right-zagolovok", "google-auto-placed", "readalser",
                                         "movie-fixed", "paginator"}

    def __init__(self):
        super().__init__()
        self.text_parts: list[str] = []
        self._in_content = False
        self._content_depth = 0
        self._skip_depth = 0
        self._noise_depth = 0  # depth inside noise divs (skip their content)
        self._skip_tags = {"script", "style", "noscript", "nav"}

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self._skip_tags:
            self._skip_depth += 1
            return
        if self._skip_depth > 0:
            return

        # Detect content container: <article class="prose" id="content">
        if tag == "article":
            attrs_dict = dict(attrs)
            if "prose" in attrs_dict.get("class", "") or attrs_dict.get("id") == "content":
                self._in_content = True
                self._content_depth = 1
                return

        if not self._in_content:
            return

        # Track noise divs inside content (ads, "read also", etc.)
        if tag == "div":
            self._content_depth += 1
            css_class = dict(attrs).get("class", "")
            if any(nc in css_class for nc in self._NOISE_CLASSES) or self._noise_depth > 0:
                self._noise_depth += 1
            return

        # Skip blockquote.cita (source/edition metadata)
        if tag == "blockquote":
            css_class = dict(attrs).get("class", "")
            if "cita" in css_class:
                self._noise_depth += 1
                return

        if self._noise_depth > 0:
            return

        if tag in ("article", "section"):
            self._content_depth += 1
        elif tag == "br" or tag == "p":
            self.text_parts.append("\n")
        elif tag in ("h1", "h2", "h3", "h4"):
            self.text_parts.append("\n\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self._skip_tags and self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if not self._in_content:
            return

        if tag == "div":
            if self._noise_depth > 0:
                self._noise_depth -= 1
            self._content_depth -= 1
            if self._content_depth <= 0:
                self._in_content = False
            return

        if tag == "blockquote" and self._noise_depth > 0:
            self._noise_depth -= 1
            return

        if self._noise_depth > 0:
            return

        if tag in ("article", "section"):
            self._content_depth -= 1
            if self._content_depth <= 0:
                self._in_content = False
        elif tag == "p" or tag in ("h1", "h2", "h3", "h4"):
            self.text_parts.append("\n\n")

    def handle_data(self, data):
        if self._skip_depth > 0 or self._noise_depth > 0:
            return
        if self._in_content:
            self.text_parts.append(data)

    def get_text(self) -> str:
        raw = "".join(self.text_parts)
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


class AuthorPageParser(HTMLParser):
    """Extract work links from author listing page."""

    def __init__(self):
        super().__init__()
        self.works: list[dict] = []
        self.page_links: list[int] = []
        self._current_href = ""
        self._in_link = False
        self._link_text = ""

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if "printit.php" in href and "tid=" in href:
                self._in_link = True
                self._current_href = href
                self._link_text = ""
            elif "author.php" in href and "page=" in href:
                match = re.search(r"page=(\d+)", href)
                if match:
                    self.page_links.append(int(match.group(1)))

    def handle_endtag(self, tag):
        if tag == "a" and self._in_link:
            self._in_link = False
            match = re.search(r"tid=(\d+)", self._current_href)
            if match:
                title = self._link_text.strip()
                # Skip biography/criticism links
                if title and "Біографія" not in title and "Життя та творчість" not in title:
                    self.works.append({
                        "tid": int(match.group(1)),
                        "title": title,
                    })

    def handle_data(self, data):
        if self._in_link:
            self._link_text += data


# ── Fetching ─────────────────────────────────────────────────────────

def fetch_page(url: str, retries: int = 3) -> str:
    """Fetch a page handling windows-1251 encoding, with retries."""
    for attempt in range(1, retries + 1):
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "30", "--retry", "2",
             "-H", "Accept-Charset: windows-1251,utf-8",
             "-H", "User-Agent: Mozilla/5.0 (compatible; UkrLibScraper/1.0)",
             url],
            capture_output=True,
        )
        if result.returncode == 0 and result.stdout:
            break
        if attempt < retries:
            wait = attempt * 3
            print(f"    Retry {attempt}/{retries} for {url} (rc={result.returncode}), waiting {wait}s...")
            time.sleep(wait)
    else:
        raise RuntimeError(f"curl failed for {url} after {retries} attempts: rc={result.returncode} {result.stderr.decode()}")

    # Try windows-1251 first (ukrlib default)
    try:
        return result.stdout.decode("windows-1251")
    except UnicodeDecodeError:
        return result.stdout.decode("utf-8", errors="replace")


def get_author_works(author_id: int) -> list[dict]:
    """Get all works for an author (handles pagination)."""
    all_works = []
    page = 1
    max_pages_seen = 1

    while page <= max_pages_seen:
        url = f"{BASE_URL}/books/author.php?id={author_id}&page={page}"
        print(f"  Fetching author page {page}...", flush=True)
        html = fetch_page(url)

        parser = AuthorPageParser()
        parser.feed(html)

        all_works.extend(parser.works)

        if parser.page_links:
            max_pages_seen = max(max_pages_seen, max(parser.page_links))

        page += 1
        if page <= max_pages_seen:
            time.sleep(DELAY_BETWEEN_PAGES)

    # Deduplicate by tid
    seen = set()
    unique = []
    for w in all_works:
        if w["tid"] not in seen:
            seen.add(w["tid"])
            unique.append(w)

    return unique


def scrape_work_text(tid: int, max_pages: int = 50) -> tuple[str, str]:
    """Scrape the full text of a work. Returns (text, source_url)."""
    all_text = ""
    source_url = f"{BASE_URL}/books/printit.php?tid={tid}"
    page = 1

    while page <= max_pages:
        url = f"{BASE_URL}/books/printit.php?tid={tid}&page={page}"
        html = fetch_page(url)

        extractor = UkrlibTextExtractor()
        extractor.feed(html)
        page_text = extractor.get_text()

        if not page_text or len(page_text) < 50:
            # Empty or too short — likely no more pages
            if page > 1:
                break
            # Page 1 might have navigation but no content container
            # Try without article filter
            if not page_text:
                print(f"    Page {page}: no content found")
                break

        all_text += page_text + "\n\n"

        # Check if there's a next page link
        if f"page={page + 1}" not in html:
            break

        page += 1
        time.sleep(DELAY_BETWEEN_PAGES)

    return all_text.strip(), source_url


# ── Chunking (reused from scrape_litopys.py) ─────────────────────────

def chunk_text(
    text: str,
    work: str,
    source_url: str,
    min_tokens: int = CHUNK_MIN_TOKENS,
    max_tokens: int = CHUNK_MAX_TOKENS,
) -> list[dict]:
    """Split text into chunks at paragraph boundaries."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks = []
    current_text = ""
    chunk_idx = 0

    for para in paragraphs:
        current_tokens = len(current_text) // 4

        if current_tokens + len(para) // 4 > max_tokens and current_text:
            chunk_id = f"{hashlib.md5(work.encode(), usedforsecurity=False).hexdigest()[:8]}_c{chunk_idx:04d}"
            chunks.append({
                "chunk_id": chunk_id,
                "text": current_text.strip(),
                "source_url": source_url,
                "token_count": len(current_text.strip()) // 4,
            })
            chunk_idx += 1
            current_text = ""

        current_text += para + "\n\n"

    # Last chunk
    if current_text.strip() and len(current_text.strip()) // 4 >= min_tokens:
        chunk_id = f"{hashlib.md5(work.encode(), usedforsecurity=False).hexdigest()[:8]}_c{chunk_idx:04d}"
        chunks.append({
            "chunk_id": chunk_id,
            "text": current_text.strip(),
            "source_url": source_url,
            "token_count": len(current_text.strip()) // 4,
        })

    return chunks


# ── Progress Tracking ────────────────────────────────────────────────

PROGRESS_DIR = LITERARY_DIR / ".ukrlib_progress"


def is_done(author_slug: str) -> bool:
    return (PROGRESS_DIR / f"{author_slug}.done").exists()


def mark_done(author_slug: str):
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    (PROGRESS_DIR / f"{author_slug}.done").write_text("")


# ── Main Scraping Logic ─────────────────────────────────────────────

def scrape_author(slug: str, author_info: dict, dry_run: bool = False) -> int:
    """Scrape all works for one author. Returns total chunks saved."""
    author_id = author_info["id"]
    author_name = author_info["name"]
    genre_default = author_info["genre_default"]
    period = author_info["period"]

    if is_done(slug) and not dry_run:
        print(f"\n[{slug}] Already done (skip). Use --force to re-scrape.")
        return 0

    print(f"\n{'='*60}")
    print(f"[{slug}] {author_info['full_name']} ({author_info['years']})")
    print(f"{'='*60}")

    # Get work list
    works = get_author_works(author_id)
    print(f"  Found {len(works)} works")

    if dry_run:
        for w in works:
            print(f"    tid={w['tid']:6d}  {w['title']}")
        return 0

    total_chunks = 0
    output_path = LITERARY_DIR / f"ukrlib-{slug}.jsonl"

    all_chunks = []
    for i, work_info in enumerate(works, 1):
        tid = work_info["tid"]
        title = work_info["title"]
        genre = guess_genre(title, genre_default)

        print(f"\n  [{i}/{len(works)}] {title} (tid={tid}, genre={genre})")
        try:
            text, source_url = scrape_work_text(tid)
        except Exception as e:
            print(f"    ERROR: {e}")
            continue

        if not text or len(text) < 100:
            print(f"    Skipped: too short ({len(text)} chars)")
            continue

        work_title = f"{author_info['full_name']}. {title}"
        chunks = chunk_text(text, work_title, source_url)

        for chunk in chunks:
            chunk.update({
                "work": work_title,
                "author": author_name,
                "year": int(author_info["years"].split("-")[0]),
                "genre": genre,
                "language_period": period,
            })
        all_chunks.extend(chunks)

        print(f"    {len(text):,} chars → {len(chunks)} chunks")
        total_chunks += len(chunks)

        if i < len(works):
            time.sleep(DELAY_BETWEEN_WORKS)

    # Save all chunks for this author
    if all_chunks:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in all_chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
        print(f"\n  Saved {total_chunks} chunks to {output_path.name}")
        mark_done(slug)
    else:
        print(f"\n  No chunks generated for {slug}")

    return total_chunks


def main():
    parser = argparse.ArgumentParser(description="Scrape Ukrainian literary canon from ukrlib.com.ua")
    parser.add_argument("--priority", choices=["P1", "P2", "P3", "all"], help="Scrape authors by priority")
    parser.add_argument("--author", type=str, help="Scrape a specific author by slug")
    parser.add_argument("--tid", type=int, help="Scrape a single work by tid")
    parser.add_argument("--work", type=str, help="Work title (for --tid)")
    parser.add_argument("--author-name", type=str, help="Author name (for --tid)")
    parser.add_argument("--list", action="store_true", help="List available authors")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be scraped")
    parser.add_argument("--force", action="store_true", help="Re-scrape even if already done")
    args = parser.parse_args()

    if args.list:
        for label, authors in [("P1 (Core Canon)", P1_AUTHORS), ("P2 (Extended Canon)", P2_AUTHORS), ("P3 (Розстріляне відродження + missing)", P3_AUTHORS)]:
            print(f"{label}:")
            for slug, info in authors.items():
                done = " [DONE]" if is_done(slug) else ""
                print(f"  {slug:20s} id={info['id']:3d}  {info['full_name']} ({info['years']}){done}")
            print()
        return

    if args.force and PROGRESS_DIR.exists():
        for f in PROGRESS_DIR.glob("*.done"):
            f.unlink()
        print("Cleared progress markers.")

    if args.tid:
        # Single work mode
        if not args.work:
            args.work = f"Невідомий твір (tid={args.tid})"
        if not args.author_name:
            args.author_name = "Невідомий"

        print(f"Scraping single work: {args.work} (tid={args.tid})")
        text, source_url = scrape_work_text(args.tid)
        if not text:
            print("No text extracted!")
            return

        chunks = chunk_text(text, args.work, source_url)
        for chunk in chunks:
            chunk.update({
                "work": args.work,
                "author": args.author_name,
                "year": 0,
                "genre": "prose",
                "language_period": "modern",
            })

        slug = re.sub(r"[^\w\s-]", "", args.work.lower())
        slug = re.sub(r"[\s]+", "-", slug)[:60]
        output_path = LITERARY_DIR / f"ukrlib-single-{slug}.jsonl"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
        print(f"\n{len(text):,} chars → {len(chunks)} chunks → {output_path.name}")
        return

    # Determine which authors to scrape
    all_authors = {}
    if args.author:
        combined = {**P1_AUTHORS, **P2_AUTHORS, **P3_AUTHORS}
        if args.author not in combined:
            print(f"Unknown author '{args.author}'. Use --list to see available.")
            return
        all_authors = {args.author: combined[args.author]}
    elif args.priority == "P1":
        all_authors = P1_AUTHORS
    elif args.priority == "P2":
        all_authors = P2_AUTHORS
    elif args.priority == "P3":
        all_authors = P3_AUTHORS
    elif args.priority == "all":
        all_authors = {**P1_AUTHORS, **P2_AUTHORS, **P3_AUTHORS}
    else:
        parser.print_help()
        return

    # Scrape
    t0 = time.time()
    grand_total = 0
    for slug, info in all_authors.items():
        n = scrape_author(slug, info, dry_run=args.dry_run)
        grand_total += n

    elapsed = time.time() - t0
    if not args.dry_run:
        print(f"\n{'='*60}")
        print(f"Grand total: {grand_total:,} chunks in {elapsed:.0f}s")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
