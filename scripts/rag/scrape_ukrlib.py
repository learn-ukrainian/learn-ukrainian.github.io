"""Scrape Ukrainian literary canon from ukrlib.com.ua.

Downloads full texts of works, chunks them, and saves as JSONL
compatible with the literary RAG pipeline.

Site structure:
    Author list:  /books/author.php?id={author_id}&page={N}
    Work text:    /books/printit.php?tid={work_id}&page={N}
    Bio text:     /bio/printit.php?tid={work_id}&page={N}
    Encoding:     windows-1251
    Content:      <article class="prose" id="content">

Usage:
    # Scrape all P1 canon authors
    .venv/bin/python scripts/rag/scrape_ukrlib.py --priority P1

    # Scrape a specific author (with bios)
    .venv/bin/python scripts/rag/scrape_ukrlib.py --author franko --include-bios

    # Scrape a single work by tid
    .venv/bin/python scripts/rag/scrape_ukrlib.py --tid 645 --work "Захар Беркут" --author-name "Франко І."

    # List available authors
    .venv/bin/python scripts/rag/scrape_ukrlib.py --list

    # Dry run (show what would be scraped)
    .venv/bin/python scripts/rag/scrape_ukrlib.py --priority P1 --dry-run

    # Audit existing JSONL files (no network)
    .venv/bin/python scripts/rag/scrape_ukrlib.py --audit-only

    # Scrape + audit
    .venv/bin/python scripts/rag/scrape_ukrlib.py --priority P1 --audit
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
DELAY_BETWEEN_PAGES = 0.3  # seconds
DELAY_BETWEEN_WORKS = 0.5

# ── Author/Work Definitions ─────────────────────────────────────────
# All IDs verified against live ukrlib author.php pages (2026-03-08)
#
# BLACKLISTED IDs — ukrlib database serves wrong works for these author pages.
# The correct data comes from reattributed files (scripts/rag/reattribute_ukrlib.py).
# See #807.
BLACKLISTED_IDS = {8, 9, 10, 13, 15, 16, 38, 65}

# Priority 1: Core school canon (most referenced in curriculum)
P1_AUTHORS = {
    "shevchenko": {
        "id": 1,
        "name": "Шевченко Т.",
        "full_name": "Тарас Шевченко",
        "years": "1814-1861",
        "genre_default": "poetry",
        "period": "modern",
    },
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
    "skovoroda": {
        "id": 4,
        "name": "Сковорода Г.",
        "full_name": "Григорій Сковорода",
        "years": "1722-1794",
        "genre_default": "prose",
        "period": "early_modern",
    },
    "stefanyk": {
        "id": 11,
        "name": "Стефаник В.",
        "full_name": "Василь Стефаник",
        "years": "1871-1936",
        "genre_default": "prose",
        "period": "modern",
    },
    # kotsyubynsky (id=8) REMOVED — broken ukrlib mapping, data from reattributed files
    # kotlyarevsky (id=10) REMOVED — broken ukrlib mapping, data from reattributed files
}

# Priority 2: Extended canon
P2_AUTHORS = {
    # kvitka (id=65) REMOVED — broken ukrlib mapping, data from reattributed files
    # nechuy (id=16) REMOVED — broken ukrlib mapping, data from reattributed files
    # myrny (id=15) REMOVED — broken ukrlib mapping, data from reattributed files
    # tychyna (id=9) REMOVED — broken ukrlib mapping, data from reattributed files
    # rylsky (id=13) REMOVED — broken ukrlib mapping, data from reattributed files
    "karpenko_karyi": {
        "id": 14,
        "name": "Карпенко-Карий І.",
        "full_name": "Іван Карпенко-Карий",
        "years": "1845-1907",
        "genre_default": "drama",
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
    "zhadan": {
        "id": 358,
        "name": "Жадан С.",
        "full_name": "Сергій Жадан",
        "years": "1974-",
        "genre_default": "poetry",
        "period": "contemporary",
    },
    "andrukhovych": {
        "id": 138,
        "name": "Андрухович Ю.",
        "full_name": "Юрій Андрухович",
        "years": "1960-",
        "genre_default": "prose",
        "period": "contemporary",
    },
    "zabuzhko": {
        "id": 282,
        "name": "Забужко О.",
        "full_name": "Оксана Забужко",
        "years": "1960-",
        "genre_default": "prose",
        "period": "contemporary",
    },
    # vynnychenko (id=38) REMOVED — broken ukrlib mapping, data from reattributed files
}

# Priority 3: Розстріляне відродження + curriculum-referenced authors
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
    # New curriculum-referenced authors (verified on ukrlib 2026-03-08)
    "bazhan": {
        "id": 30,
        "name": "Бажан М.",
        "full_name": "Микола Бажан",
        "years": "1904-1983",
        "genre_default": "poetry",
        "period": "modern",
    },
    "vinhranovskyi": {
        "id": 35,
        "name": "Вінграновський М.",
        "full_name": "Микола Вінграновський",
        "years": "1936-2004",
        "genre_default": "poetry",
        "period": "modern",
    },
    "voronyi": {
        "id": 40,
        "name": "Вороний М.",
        "full_name": "Микола Вороний",
        "years": "1871-1938",
        "genre_default": "poetry",
        "period": "modern",
    },
    "lepkyi": {
        "id": 72,
        "name": "Лепкий Б.",
        "full_name": "Богдан Лепкий",
        "years": "1872-1941",
        "genre_default": "prose",
        "period": "modern",
    },
    "malaniuk": {
        "id": 74,
        "name": "Маланюк Є.",
        "full_name": "Євген Маланюк",
        "years": "1897-1968",
        "genre_default": "poetry",
        "period": "modern",
    },
    "malyshko": {
        "id": 76,
        "name": "Малишко А.",
        "full_name": "Андрій Малишко",
        "years": "1912-1970",
        "genre_default": "poetry",
        "period": "modern",
    },
    "olzhych": {
        "id": 84,
        "name": "Ольжич О.",
        "full_name": "Олег Ольжич",
        "years": "1907-1944",
        "genre_default": "poetry",
        "period": "modern",
    },
    "osmachka": {
        "id": 85,
        "name": "Осьмачка Т.",
        "full_name": "Тодось Осьмачка",
        "years": "1895-1962",
        "genre_default": "poetry",
        "period": "modern",
    },
    "samchuk": {
        "id": 95,
        "name": "Самчук У.",
        "full_name": "Улас Самчук",
        "years": "1905-1987",
        "genre_default": "prose",
        "period": "modern",
    },
    "semenko": {
        "id": 96,
        "name": "Семенко М.",
        "full_name": "Михайль Семенко",
        "years": "1892-1937",
        "genre_default": "poetry",
        "period": "modern",
    },
    "khotkevych": {
        "id": 115,
        "name": "Хоткевич Г.",
        "full_name": "Гнат Хоткевич",
        "years": "1877-1938",
        "genre_default": "prose",
        "period": "modern",
    },
    "andiyevska": {
        "id": 137,
        "name": "Андієвська Е.",
        "full_name": "Емма Андієвська",
        "years": "1931-2024",
        "genre_default": "poetry",
        "period": "modern",
    },
    "holoborodko": {
        "id": 142,
        "name": "Голобородько В.",
        "full_name": "Василь Голобородько",
        "years": "1945-",
        "genre_default": "poetry",
        "period": "modern",
    },
    "yohansen": {
        "id": 204,
        "name": "Йогансен М.",
        "full_name": "Майк Йогансен",
        "years": "1895-1937",
        "genre_default": "prose",
        "period": "modern",
    },
    "dziuba": {
        "id": 205,
        "name": "Дзюба І.",
        "full_name": "Іван Дзюба",
        "years": "1931-2022",
        "genre_default": "prose",
        "period": "modern",
    },
    "kalynets": {
        "id": 289,
        "name": "Калинець І.",
        "full_name": "Ігор Калинець",
        "years": "1939-",
        "genre_default": "poetry",
        "period": "modern",
    },
    "prokhasko": {
        "id": 297,
        "name": "Прохасько Т.",
        "full_name": "Тарас Прохасько",
        "years": "1968-",
        "genre_default": "prose",
        "period": "contemporary",
    },
    "kobrynska": {
        "id": 415,
        "name": "Кобринська Н.",
        "full_name": "Наталія Кобринська",
        "years": "1855-1920",
        "genre_default": "prose",
        "period": "modern",
    },
    "matios": {
        "id": 491,
        "name": "Матіос М.",
        "full_name": "Марія Матіос",
        "years": "1959-",
        "genre_default": "prose",
        "period": "contemporary",
    },
}

# Authors with broken ukrlib IDs — excluded from scraping
# Correct IDs TBD (see #807)
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
    """Extract work and bio links from author listing page."""

    def __init__(self):
        super().__init__()
        self.works: list[dict] = []
        self.bios: list[dict] = []
        self.page_links: list[int] = []
        self._current_href = ""
        self._in_link = False
        self._link_text = ""
        self._is_bio = False

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if "printit.php" in href and "tid=" in href:
                self._in_link = True
                self._current_href = href
                self._link_text = ""
                self._is_bio = "/bio/" in href
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
                if title:
                    entry = {
                        "tid": int(match.group(1)),
                        "title": title,
                    }
                    if self._is_bio:
                        self.bios.append(entry)
                    else:
                        self.works.append(entry)

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


def get_author_works(author_id: int) -> tuple[list[dict], list[dict]]:
    """Get all works and bios for an author (handles pagination).

    Returns (works, bios) — both deduplicated by tid.
    """
    all_works = []
    all_bios = []
    page = 1
    max_pages_seen = 1

    while page <= max_pages_seen:
        url = f"{BASE_URL}/books/author.php?id={author_id}&page={page}"
        print(f"  Fetching author page {page}...", flush=True)
        html = fetch_page(url)

        parser = AuthorPageParser()
        parser.feed(html)

        all_works.extend(parser.works)
        all_bios.extend(parser.bios)

        if parser.page_links:
            max_pages_seen = max(max_pages_seen, max(parser.page_links))

        page += 1
        if page <= max_pages_seen:
            time.sleep(DELAY_BETWEEN_PAGES)

    # Deduplicate by tid
    def dedup(items):
        seen = set()
        unique = []
        for w in items:
            if w["tid"] not in seen:
                seen.add(w["tid"])
                unique.append(w)
        return unique

    return dedup(all_works), dedup(all_bios)


def scrape_work_text(tid: int, max_pages: int = 50, is_bio: bool = False) -> tuple[str, str]:
    """Scrape the full text of a work or bio. Returns (text, source_url)."""
    path_prefix = "bio" if is_bio else "books"
    all_text = ""
    source_url = f"{BASE_URL}/{path_prefix}/printit.php?tid={tid}"
    page = 1

    while page <= max_pages:
        url = f"{BASE_URL}/{path_prefix}/printit.php?tid={tid}&page={page}"
        html = fetch_page(url)

        extractor = UkrlibTextExtractor()
        extractor.feed(html)
        page_text = extractor.get_text()

        if not page_text or len(page_text) < 50:
            if page > 1:
                break
            if not page_text:
                print(f"    Page {page}: no content found")
                break

        all_text += page_text + "\n\n"

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


def mark_done(author_slug: str, work_count: int = 0):
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    (PROGRESS_DIR / f"{author_slug}.done").write_text(f"works={work_count}")


def get_done_tids(output_path: Path) -> set[int]:
    """Extract already-scraped tids from existing JSONL file."""
    tids = set()
    if not output_path.exists():
        return tids
    with open(output_path, encoding="utf-8") as f:
        for line in f:
            try:
                chunk = json.loads(line)
                url = chunk.get("source_url", "")
                match = re.search(r"tid=(\d+)", url)
                if match:
                    tids.add(int(match.group(1)))
            except json.JSONDecodeError:
                continue
    return tids


# ── Audit ────────────────────────────────────────────────────────────

def audit_jsonl(path: Path, author_info: dict | None = None) -> tuple[bool, list[str]]:
    """Audit a JSONL file for data quality issues.

    Returns (passed, list_of_errors).
    """
    errors = []
    required_fields = {"chunk_id", "text", "source_url", "work", "author", "year", "genre", "language_period"}
    chunk_ids = set()
    total_chars = 0
    works = set()
    genres = set()
    chunk_count = 0

    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"Line {line_no}: invalid JSON: {e}")
                continue

            chunk_count += 1
            chunk_id = chunk.get("chunk_id", f"line_{line_no}")

            # Check required fields
            missing = required_fields - set(chunk.keys())
            if missing:
                errors.append(f"Chunk {chunk_id}: missing fields: {missing}")

            # Check for empty text
            text = chunk.get("text", "")
            if not text or len(text) < 10:
                errors.append(f"Chunk {chunk_id}: empty or very short text ({len(text)} chars)")

            # Check alphabetic ratio (skip very short chunks)
            # Some authors (Skovoroda) wrote in Latin and Greek, so we check
            # total alphabetic content, not just Cyrillic
            if len(text) > 200:
                alpha = sum(1 for c in text if c.isalpha())
                alpha_ratio = alpha / len(text) if text else 0
                if alpha_ratio < 0.3:
                    errors.append(f"Chunk {chunk_id}: low alphabetic ratio ({alpha_ratio:.1%}) — possible HTML garbage")

            # Check for duplicate chunk_ids
            if chunk_id in chunk_ids:
                errors.append(f"Chunk {chunk_id}: duplicate chunk_id")
            chunk_ids.add(chunk_id)

            # Check author metadata matches
            if author_info:
                expected_author = author_info["name"]
                actual_author = chunk.get("author", "")
                if actual_author != expected_author:
                    errors.append(f"Chunk {chunk_id}: author mismatch: '{actual_author}' != '{expected_author}'")

            total_chars += len(text)
            works.add(chunk.get("work", ""))
            genres.add(chunk.get("genre", ""))

    # Print summary
    print(f"\n── Audit: {path.name} ──")
    print(f"   Chunks: {chunk_count}")
    print(f"   Works:  {len(works)}")
    print(f"   Genres: {', '.join(sorted(genres))}")
    print(f"   Chars:  {total_chars:,}")

    if errors:
        print(f"   ❌ FAIL ({len(errors)} errors):")
        for e in errors[:20]:
            print(f"      - {e}")
        if len(errors) > 20:
            print(f"      ... and {len(errors) - 20} more")
    else:
        print(f"   ✅ PASS")

    return len(errors) == 0, errors


def audit_cross_contamination(data_dir: Path) -> tuple[bool, list[str]]:
    """Detect cross-author contamination across all JSONL files.

    Flags files where >50% of work titles also appear in another author's file.
    Returns (passed, list_of_errors).
    """
    # Build work-title → set of filenames
    work_files: dict[str, set[str]] = {}
    file_works: dict[str, set[str]] = {}

    for path in sorted(data_dir.glob("ukrlib-*.jsonl")):
        titles = set()
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    c = json.loads(line)
                    w = c.get("work", "")
                    if ". " in w:
                        title = w.split(". ", 1)[1]
                        titles.add(title)
                        if title not in work_files:
                            work_files[title] = set()
                        work_files[title].add(path.name)
                except json.JSONDecodeError:
                    continue
        file_works[path.name] = titles

    errors = []
    for fname, titles in sorted(file_works.items()):
        if not titles:
            continue
        foreign = 0
        for title in titles:
            other_files = work_files[title] - {fname}
            if other_files:
                foreign += 1
        pct = 100 * foreign / len(titles)
        if pct > 50:
            errors.append(f"{fname}: {foreign}/{len(titles)} works ({pct:.0f}%) also appear in other author files — likely contaminated")

    print(f"\n── Cross-Author Contamination Check ──")
    if errors:
        print(f"   ❌ FAIL ({len(errors)} contaminated files):")
        for e in errors:
            print(f"      - {e}")
    else:
        print(f"   ✅ PASS — no cross-contamination detected")

    return len(errors) == 0, errors


# ── Main Scraping Logic ─────────────────────────────────────────────

def scrape_author(slug: str, author_info: dict, dry_run: bool = False,
                  include_bios: bool = False) -> int:
    """Scrape all works for one author with work-level resume.

    Returns total chunks in the output file (not just new ones).
    """
    author_id = author_info["id"]
    if author_id in BLACKLISTED_IDS:
        print(f"\n[{slug}] SKIPPED — author id={author_id} is blacklisted (broken ukrlib mapping)")
        return 0
    author_name = author_info["name"]
    genre_default = author_info["genre_default"]
    period = author_info["period"]

    output_path = LITERARY_DIR / f"ukrlib-{slug}.jsonl"

    if is_done(slug) and not dry_run:
        existing = 0
        if output_path.exists():
            with open(output_path, encoding="utf-8") as f:
                existing = sum(1 for _ in f)
        print(f"\n[{slug}] Already done ({existing} chunks). Use --force to re-scrape.")
        return existing

    print(f"\n{'='*60}")
    print(f"[{slug}] {author_info['full_name']} ({author_info['years']})")
    print(f"{'='*60}")

    # Get work list
    works, bios = get_author_works(author_id)
    print(f"  Found {len(works)} works, {len(bios)} bios")

    if dry_run:
        for w in works:
            print(f"    tid={w['tid']:6d}  {w['title']}")
        if include_bios:
            for b in bios:
                print(f"    tid={b['tid']:6d}  [BIO] {b['title']}")
        return 0

    # Work-level resume: check which tids are already scraped
    done_tids = get_done_tids(output_path)
    pending_works = [w for w in works if w["tid"] not in done_tids]
    pending_bios = [b for b in bios if b["tid"] not in done_tids] if include_bios else []

    if done_tids:
        print(f"  Resume: {len(done_tids)} tids already scraped, {len(pending_works)} works + {len(pending_bios)} bios pending")

    total_items = pending_works + pending_bios
    if not total_items:
        existing = 0
        if output_path.exists():
            with open(output_path, encoding="utf-8") as f:
                existing = sum(1 for _ in f)
        print(f"  All works already scraped ({existing} chunks in file)")
        mark_done(slug, len(works) + len(bios))
        return existing

    new_chunks = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Append mode for resume
    with open(output_path, "a", encoding="utf-8") as f:
        for i, work_info in enumerate(total_items, 1):
            tid = work_info["tid"]
            title = work_info["title"]
            is_bio = work_info in pending_bios
            genre = "biography" if is_bio else guess_genre(title, genre_default)

            label = "[BIO] " if is_bio else ""
            print(f"\n  [{i}/{len(total_items)}] {label}{title} (tid={tid}, genre={genre})")
            try:
                text, source_url = scrape_work_text(tid, is_bio=is_bio)
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
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

            print(f"    {len(text):,} chars → {len(chunks)} chunks")
            new_chunks += len(chunks)

            if i < len(total_items):
                time.sleep(DELAY_BETWEEN_WORKS)

    # Count total chunks in file
    total_in_file = 0
    if output_path.exists():
        with open(output_path, encoding="utf-8") as f:
            total_in_file = sum(1 for _ in f)

    if new_chunks > 0:
        print(f"\n  Added {new_chunks} new chunks (total in file: {total_in_file})")
    mark_done(slug, len(works) + (len(bios) if include_bios else 0))

    return total_in_file


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
    parser.add_argument("--include-bios", action="store_true", help="Also scrape biography pages")
    parser.add_argument("--audit", action="store_true", help="Run audit after scraping")
    parser.add_argument("--audit-only", action="store_true", help="Audit existing files (no network)")
    args = parser.parse_args()

    all_defined = {**P1_AUTHORS, **P2_AUTHORS, **P3_AUTHORS}

    if args.list:
        for label, authors in [("P1 (Core Canon)", P1_AUTHORS), ("P2 (Extended Canon)", P2_AUTHORS),
                                ("P3 (Розстріляне відродження + curriculum)", P3_AUTHORS)]:
            print(f"\n{label}:")
            for slug, info in authors.items():
                done = " [DONE]" if is_done(slug) else ""
                print(f"  {slug:20s} id={info['id']:3d}  {info['full_name']} ({info['years']}){done}")
        print(f"\nTotal: {len(all_defined)} authors")
        return

    # Audit-only mode: no network, just validate existing JSONL files
    if args.audit_only:
        files = sorted(LITERARY_DIR.glob("ukrlib-*.jsonl"))
        if not files:
            print("No ukrlib JSONL files found.")
            return

        passed = 0
        failed = 0
        for path in files:
            slug = path.stem.replace("ukrlib-", "")
            author_info = all_defined.get(slug)
            ok, _ = audit_jsonl(path, author_info)
            if ok:
                passed += 1
            else:
                failed += 1

        # Cross-contamination check
        cross_ok, _ = audit_cross_contamination(LITERARY_DIR)
        if not cross_ok:
            failed += 1

        print(f"\n{'='*60}")
        print(f"Audit complete: {passed} passed, {failed} failed out of {len(files)} files")
        print(f"{'='*60}")
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
    target_authors = {}
    if args.author:
        if args.author not in all_defined:
            print(f"Unknown author '{args.author}'. Use --list to see available.")
            return
        target_authors = {args.author: all_defined[args.author]}
    elif args.priority == "P1":
        target_authors = P1_AUTHORS
    elif args.priority == "P2":
        target_authors = P2_AUTHORS
    elif args.priority == "P3":
        target_authors = P3_AUTHORS
    elif args.priority == "all":
        target_authors = all_defined
    else:
        parser.print_help()
        return

    # Scrape
    t0 = time.time()
    grand_total = 0
    for slug, info in target_authors.items():
        n = scrape_author(slug, info, dry_run=args.dry_run, include_bios=args.include_bios)
        grand_total += n

    elapsed = time.time() - t0
    if not args.dry_run:
        print(f"\n{'='*60}")
        print(f"Grand total: {grand_total:,} chunks in {elapsed:.0f}s")
        print(f"{'='*60}")

    # Post-scrape audit
    if args.audit and not args.dry_run:
        print(f"\n{'='*60}")
        print(f"Running post-scrape audit...")
        print(f"{'='*60}")
        passed = 0
        failed = 0
        for slug in target_authors:
            path = LITERARY_DIR / f"ukrlib-{slug}.jsonl"
            if path.exists():
                ok, _ = audit_jsonl(path, target_authors[slug])
                if ok:
                    passed += 1
                else:
                    failed += 1

        # Cross-contamination check
        cross_ok, _ = audit_cross_contamination(LITERARY_DIR)
        if not cross_ok:
            failed += 1

        print(f"\nAudit: {passed} passed, {failed} failed")


if __name__ == "__main__":
    main()
