"""Scrape works from Ukrainian Wikisource (uk.wikisource.org) for literary RAG.

Uses the MediaWiki API to fetch parsed HTML, converts to clean text,
and chunks into JSONL for Qdrant ingestion.

Usage:
    # Scrape all works by an author
    .venv/bin/python scripts/rag/scrape_wikisource.py \
        --author "Хвильовий" --author-full "Хвильовий Микола" \
        --year-range 1923-1933 --genre prose --period modern

    # Scrape a specific work
    .venv/bin/python scripts/rag/scrape_wikisource.py \
        --pages "Зачарована Десна" \
        --author-full "Довженко Олександр" \
        --year 1956 --genre prose --period modern

    # Dry run (list pages, don't scrape)
    .venv/bin/python scripts/rag/scrape_wikisource.py \
        --author "Антонич" --dry-run

Output: data/literary_texts/wikisource-{author}.jsonl
"""

import argparse
import html
import json
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag.config import CHUNK_MAX_TOKENS, LITERARY_DIR

API = "https://uk.wikisource.org/w/api.php"

# ── Rate limiting + 429 backoff ──────────────────────────────────────
# Wikisource uses the same MediaWiki infrastructure as Wikipedia. The
# polite ceiling is ~10 req/sec for logged-out bots, but rate limiters
# vary by endpoint and time of day. Stay well under it.
#
# Same pattern we use in scripts/wiki/fetch_wikipedia.py (79291ce6d):
# centralized pacing BEFORE every call (regardless of outcome) + 429
# detection with exponential backoff. The old scrape_wikisource.py had
# the bug that `CRAWL_DELAY` was only sleep'd in some code paths —
# search_author_works() and get_page_links() had NO pacing at all.

_MIN_INTERVAL_S = 0.8             # ~1.25 req/sec — conservative
_BACKOFF_BASE_S = 30.0            # first backoff after 429
_BACKOFF_MAX_S = 600.0            # cap at 10 minutes
_MAX_429_RETRIES = 4              # total attempts per call before giving up

_last_call_ts: float = 0.0        # module-level; tracks the last API hit

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "LearnUkrainianBot/1.0 "
        "(https://learn-ukrainian.github.io; educational project)"
    ),
})


def _pace_api_call() -> None:
    """Sleep just enough to guarantee _MIN_INTERVAL_S since the last
    Wikisource API call. Called BEFORE every request so that even
    FAILED requests count toward the rate budget — the old bug was
    that failures skipped the sleep and fired immediate retries."""
    global _last_call_ts
    now = time.monotonic()
    gap = now - _last_call_ts
    if gap < _MIN_INTERVAL_S:
        time.sleep(_MIN_INTERVAL_S - gap)
    _last_call_ts = time.monotonic()


def api_get(params: dict) -> dict:
    """Make a MediaWiki API request with pacing + 429 backoff.

    Returns the decoded JSON on success. Returns {} (empty dict) on
    any terminal failure (non-429 error, exhausted retries) so callers
    can treat it as 'no results' without crashing mid-crawl.
    """
    params["format"] = "json"
    for attempt in range(_MAX_429_RETRIES):
        _pace_api_call()
        try:
            r = SESSION.get(API, params=params, timeout=30)
            if r.status_code == 429:
                wait = min(_BACKOFF_BASE_S * (2 ** attempt), _BACKOFF_MAX_S)
                print(f"    ⏳ rate-limited (429), sleeping {wait:.0f}s "
                      f"(attempt {attempt + 1}/{_MAX_429_RETRIES})")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError as e:
            print(f"    ⚠️  HTTP {e.response.status_code} from Wikisource API")
            return {}
        except requests.exceptions.RequestException as e:
            print(f"    ⚠️  network error: {type(e).__name__}: {str(e)[:80]}")
            return {}
    print(f"    ❌ giving up after {_MAX_429_RETRIES} 429 retries")
    return {}


def search_author_works(author_name: str, limit: int = 100) -> list[dict]:
    """Search Wikisource for works by an author.

    Returns list of {title, snippet} dicts. Pacing is handled inside
    api_get() so callers never need a manual sleep.
    """
    results = []
    params = {
        "action": "query",
        "list": "search",
        "srsearch": author_name,
        "srnamespace": "0",
        "srlimit": str(min(limit, 50)),
    }
    data = api_get(params)
    for item in data.get("query", {}).get("search", []):
        results.append({
            "title": item["title"],
            "snippet": re.sub(r"<[^>]+>", "", item.get("snippet", "")),
        })
    return results


def get_page_links(title: str) -> list[str]:
    """Get all internal links from a page (for index/collection pages)."""
    params = {
        "action": "query",
        "titles": title,
        "prop": "links",
        "pllimit": "500",
        "plnamespace": "0",
    }
    data = api_get(params)
    pages = data.get("query", {}).get("pages", {})
    links = []
    for page in pages.values():
        for link in page.get("links", []):
            links.append(link["title"])
    return links


def get_page_text(title: str) -> str | None:
    """Fetch a page's parsed HTML and convert to clean text.

    Uses BeautifulSoup to walk the DOM intelligently instead of
    regex-stripping — critical for Wikisource pages that wrap primary
    content in layout tables (parallel Latin/Ukrainian translations,
    poem verses, etc.). The old regex-only stripper removed ALL tables,
    which on pages like "Конституція Пилипа Орлика" ate ~89% of the
    actual content.

    Strips only NAVIGATION chrome: mw-heading, mw-editsection,
    references, infoboxes, navboxes, TOCs, category links. Everything
    else — including content-carrying tables — is kept and flattened
    to text.
    """
    from bs4 import BeautifulSoup, Tag

    params = {
        "action": "parse",
        "page": title,
        "prop": "text",
    }
    data = api_get(params)
    if not data or "error" in data:
        return None

    raw_html = data.get("parse", {}).get("text", {}).get("*", "")
    if not raw_html:
        return None

    soup = BeautifulSoup(raw_html, "html.parser")

    # Strip navigation / editorial chrome. Be specific so we don't
    # also strip content tables that happen to contain the word 'nav'
    # in some unrelated class.
    strip_selectors = [
        "span.mw-editsection",           # [edit] links
        "sup.reference",                  # footnote markers
        "div.mw-heading",                 # wiki heading wrappers (keep h1/h2 children via get_text)
        "table.infobox",                  # infoboxes
        "table.navbox",                   # bottom navigation boxes
        "table.metadata",                 # metadata tables
        "div.toc",                        # table of contents
        "div#toc",
        "div.navbox",
        "div.printfooter",                # "Retrieved from..." footer
        "div.catlinks",                   # category links at bottom
        "div.hatnote",                    # disambiguation hats
        "noscript",
        "style",
        "script",
    ]
    for sel in strip_selectors:
        for el in soup.select(sel):
            el.decompose()

    # Extract flat text. BeautifulSoup's get_text handles tables,
    # lists, divs, and paragraphs uniformly — each element's content
    # flows as text with a separator.
    text = soup.get_text(separator="\n", strip=False)

    # Normalize whitespace but preserve paragraph breaks
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    # Skip pages that are just redirects or disambiguation
    if len(text) < 100:
        return None

    # Strip pages that are mostly navigation arrows (works like "►" and "◄")
    if text.count("►") > 5 or text.count("◄") > 5:
        lines = [line for line in text.split("\n") if "►" not in line and "◄" not in line]
        text = "\n".join(lines).strip()

    return text


def is_skip_page(title: str) -> bool:
    """Check if a page should be skipped (non-content)."""
    skip_patterns = [
        "Категорія:", "Автор:", "Вікіджерела:", "Обговорення:",
        "Словарь української мови",
        "Письменники Радянської",
        "Питання літератури",
    ]
    return any(pattern in title for pattern in skip_patterns)


def expand_collection_pages(title: str, author_short: str, depth: int = 0) -> list[str]:
    """Recursively expand collection/index pages into content subpages.

    Wikisource organizes works as:
      Твори (Author, year)/volume/work_title
    This follows links to find the actual content pages.
    """
    if depth > 2 or is_skip_page(title):
        return []

    # Pacing is handled inside api_get() → get_page_links(); no manual sleep needed
    links = get_page_links(title)

    content_pages = []
    index_pages = []

    for link in links:
        if is_skip_page(link):
            continue
        # A subpage of the current page is likely a content page
        if link.startswith(title + "/"):
            # Check if it has further subpages (it's another index)
            # Simple heuristic: if the link has 2+ slashes after the base, it's content
            sub_depth = link[len(title):].count("/")
            if sub_depth >= 2:
                content_pages.append(link)
            else:
                index_pages.append(link)
        elif author_short.lower() in link.lower():
            content_pages.append(link)

    # Expand index pages one level deeper
    for idx_page in index_pages:
        content_pages.extend(expand_collection_pages(idx_page, author_short, depth + 1))

    return content_pages


def chunk_text(text: str, work_title: str, metadata: dict) -> list[dict]:
    """Split text into chunks at paragraph boundaries."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks = []
    current_text = ""
    chunk_idx = 0
    work_id = re.sub(r'[^\w]', '_', work_title)[:50]
    id_prefix = f"ws_{work_id}"

    def _flush():
        nonlocal current_text, chunk_idx
        if not current_text.strip():
            return
        chunk_id = f"{id_prefix}_c{chunk_idx:03d}"
        chunks.append({
            "chunk_id": chunk_id,
            "text": current_text.strip(),
            "token_count": len(current_text.strip()) // 4,
            **metadata,
        })
        chunk_idx += 1
        current_text = ""

    for para in paragraphs:
        # Split oversized paragraphs at sentence boundaries
        if len(para) // 4 > CHUNK_MAX_TOKENS:
            if current_text:
                _flush()
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sent in sentences:
                if len(current_text) // 4 + len(sent) // 4 > CHUNK_MAX_TOKENS and current_text:
                    _flush()
                current_text += sent + " "
            continue

        if len(current_text) // 4 + len(para) // 4 > CHUNK_MAX_TOKENS and current_text:
            _flush()
        current_text += para + "\n\n"

    _flush()
    return chunks


def scrape_author(
    author_short: str,
    author_full: str,
    year: int = 0,
    year_range: str = "",
    genre: str = "prose",
    period: str = "modern",
    dry_run: bool = False,
    pages: list[str] | None = None,
) -> int:
    """Scrape all works by an author from Wikisource."""
    LITERARY_DIR.mkdir(parents=True, exist_ok=True)
    outfile = LITERARY_DIR / f"wikisource-{author_short.lower()}.jsonl"

    if pages:
        work_pages = pages
    else:
        # Search for works
        print(f"[wikisource] Searching for '{author_short}'...")
        results = search_author_works(author_short, limit=100)
        work_pages = []

        for r in results:
            title = r["title"]
            if is_skip_page(title):
                continue
            if author_short.lower() not in title.lower():
                continue
            # Try expanding collection pages (Твори/volume → subpages)
            subpages = expand_collection_pages(title, author_short)
            if subpages:
                print(f"  Expanded '{title}' → {len(subpages)} subpages")
                work_pages.extend(subpages)
            else:
                work_pages.append(title)

        work_pages = list(dict.fromkeys(work_pages))  # deduplicate, preserve order
        print(f"  Found {len(work_pages)} content pages")

    if dry_run:
        for p in work_pages:
            print(f"  {p}")
        return 0

    # Parse year range
    year_start, year_end = 0, 0
    if year_range and "-" in year_range:
        parts = year_range.split("-")
        year_start, year_end = int(parts[0]), int(parts[1])

    total_chunks = 0
    with open(outfile, "w", encoding="utf-8") as f:
        for i, title in enumerate(work_pages):
            # Pacing is handled inside get_page_text() → api_get(); no manual sleep
            print(f"  [{i+1}/{len(work_pages)}] {title}...", end=" ")

            text = get_page_text(title)
            if not text:
                print("skip (no content)")
                continue

            work_year = year
            # Try to extract year from title
            year_match = re.search(r'\b(1[89]\d{2}|20[012]\d)\b', title)
            if year_match:
                work_year = int(year_match.group(1))
            elif year_start:
                work_year = (year_start + year_end) // 2

            metadata = {
                "work": title,
                "author": author_full,
                "year": work_year,
                "genre": genre,
                "language_period": period,
                "source": "uk.wikisource.org",
            }

            chunks = chunk_text(text, title, metadata)
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            total_chunks += len(chunks)
            print(f"{len(chunks)} chunks ({len(text)} chars)")

    print(f"\n[wikisource] {author_full}: {total_chunks} chunks → {outfile}")
    return total_chunks


def main():
    parser = argparse.ArgumentParser(description="Scrape Ukrainian Wikisource for literary RAG")
    parser.add_argument("--author", required=True, help="Short author name for search (e.g., 'Хвильовий')")
    parser.add_argument("--author-full", required=True, help="Full author name for metadata (e.g., 'Хвильовий М.')")
    parser.add_argument("--year", type=int, default=0, help="Publication year (for single works)")
    parser.add_argument("--year-range", default="", help="Year range (e.g., '1923-1933')")
    parser.add_argument("--genre", default="prose", help="Genre: prose, poetry, drama, essay (default: prose)")
    parser.add_argument("--period", default="modern", help="Language period (default: modern)")
    parser.add_argument("--pages", nargs="+", help="Specific page titles to scrape")
    parser.add_argument("--dry-run", action="store_true", help="List pages without scraping")
    args = parser.parse_args()

    scrape_author(
        author_short=args.author,
        author_full=args.author_full,
        year=args.year,
        year_range=args.year_range,
        genre=args.genre,
        period=args.period,
        dry_run=args.dry_run,
        pages=args.pages,
    )


if __name__ == "__main__":
    main()
