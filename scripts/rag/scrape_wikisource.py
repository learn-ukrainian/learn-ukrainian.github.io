"""Scrape works from Ukrainian Wikisource (uk.wikisource.org) for literary RAG.

Uses the MediaWiki API to fetch parsed HTML, converts to clean text,
and chunks into JSONL for Qdrant ingestion.

Usage:
    # Scrape a public-domain folk category into JSONL only
    .venv/bin/python scripts/rag/scrape_wikisource.py \
        --category "Категорія:Думи" --dry-run

    # Scrape + ingest a folk category into a local sources.db
    .venv/bin/python scripts/rag/scrape_wikisource.py \
        --category "Категорія:Думи" --ingest --db data/sources.db

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
import sqlite3
import sys
import time
from pathlib import Path
from urllib.parse import quote, urlencode

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag.config import CHUNK_MAX_TOKENS, DATA_DIR, LITERARY_DIR
from rag.scrape_ukrlib import (
    NAROD_AUTHOR,
    NAROD_PERIOD,
    NAROD_YEAR,
    audit_jsonl,
)
from rag.scrape_ukrlib import (
    chunk_text as chunk_folk_text,
)
from wiki.sources import build_literary_row, work_to_id

API = "https://uk.wikisource.org/w/api.php"
WIKI_BASE_URL = "https://uk.wikisource.org/wiki"
DEFAULT_FOLK_CATEGORY = "Категорія:Думи"
DEFAULT_DB_PATH = DATA_DIR / "sources.db"
DELAY_BETWEEN_WORKS = 0.5

FOLK_CATEGORY_GENRES = {
    "Думи": "Дума",
    "Колядки": "Колядка",
    "Казки": "Казка",
    "Легенди": "Легенда",
    "Пісні": "Пісня",
    "Прислів'я": "Прислів'я",
    "Приказки": "Приказка",
    "Щедрівки": "Щедрівка",
}

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


def _api_url(params: dict[str, str | int]) -> str:
    query = urlencode(params, doseq=True, quote_via=quote)
    return f"{API}?{query}"


def fetch_json(url: str, retries: int = 3) -> dict:
    """Fetch JSON from the Wikisource API with pacing, retries, and backoff."""
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        _pace_api_call()
        try:
            response = SESSION.get(url, timeout=30)
            if response.status_code == 429:
                wait = min(_BACKOFF_BASE_S * (2 ** (attempt - 1)), _BACKOFF_MAX_S)
                print(f"    rate-limited (429), sleeping {wait:.0f}s before retry {attempt}/{retries}")
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < retries:
                wait = attempt * 3
                print(f"    retry {attempt}/{retries} for Wikisource API after {type(exc).__name__}; sleeping {wait}s")
                time.sleep(wait)
    raise RuntimeError(f"Wikisource API fetch failed after {retries} attempts: {url}") from last_error


def _category_label(category: str) -> str:
    return category.split(":", 1)[-1].strip()


def _category_slug(category: str) -> str:
    return work_to_id(_category_label(category))


def genre_from_category(category: str) -> str:
    label = _category_label(category)
    if label in FOLK_CATEGORY_GENRES:
        return FOLK_CATEGORY_GENRES[label]
    if label.endswith("ки"):
        return f"{label[:-1]}а"
    if label.endswith("и"):
        return f"{label[:-1]}а"
    return label


def source_url_for_title(title: str) -> str:
    return f"{WIKI_BASE_URL}/{quote(title.replace(' ', '_'), safe='/:')}"


def discover_category_pages(category: str) -> list[str]:
    """List namespace-0 pages from a Wikisource category, following continuation."""
    titles: list[str] = []
    params: dict[str, str | int] = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmlimit": 500,
        "cmtype": "page",
        "cmnamespace": 0,
        "cmtitle": category,
    }

    while True:
        data = fetch_json(_api_url(params))
        for member in data.get("query", {}).get("categorymembers", []):
            title = str(member.get("title", "")).strip()
            if title:
                titles.append(title)

        continuation = data.get("continue", {})
        if "cmcontinue" not in continuation:
            break
        params["cmcontinue"] = continuation["cmcontinue"]
        params["continue"] = continuation.get("continue", "")

    return titles


def fetch_parse(title: str) -> tuple[str, str]:
    """Fetch wikitext and rendered HTML for a page through action=parse."""
    data = fetch_json(_api_url({
        "action": "parse",
        "format": "json",
        "formatversion": 2,
        "page": title,
        "prop": "wikitext|text",
    }))
    if "error" in data:
        code = data["error"].get("code", "unknown")
        info = data["error"].get("info", "")
        raise RuntimeError(f"parse API error for {title!r}: {code} {info}".strip())

    parsed = data.get("parse", {})
    wikitext = parsed.get("wikitext", "")
    html_text = parsed.get("text", "")
    if isinstance(wikitext, dict):
        wikitext = wikitext.get("*", "")
    if isinstance(html_text, dict):
        html_text = html_text.get("*", "")
    return str(wikitext or ""), str(html_text or "")


def _strip_templates(text: str) -> str:
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"\{\{[^{}]*\}\}", "", text, flags=re.DOTALL)
    return text


def _unwrap_wikilink(match: re.Match[str]) -> str:
    body = match.group(1).strip()
    lowered = body.lower()
    if lowered.startswith(("категорія:", "category:", "файл:", "file:", "зображення:", "image:")):
        return ""
    return body.split("|")[-1].strip()


def _version_target_title(wikitext: str) -> str | None:
    if not re.search(r"\{\{\s*версії\b", wikitext or "", flags=re.IGNORECASE):
        return None
    for link in re.findall(r"\[\[([^\]]+)\]\]", wikitext):
        target = link.split("|", 1)[0].strip()
        lowered = target.lower()
        if not target or lowered.startswith(("категорія:", "category:", "автор:", "author:", "файл:", "file:")):
            continue
        if target.startswith("#"):
            continue
        return target
    return None


def _normalize_extracted_text(text: str) -> str:
    text = html.unescape(text)
    lines: list[str] = []
    previous_blank = False
    for raw_line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if not line:
            if lines and not previous_blank:
                lines.append("")
            previous_blank = True
            continue
        lines.append(line)
        previous_blank = False
    return "\n".join(lines).strip()


def _clean_wikitext_fragment(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref\b[^/>]*/>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<ref\b[^>]*>.*?</ref>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\[\[\s*(?:Категорія|Category)\s*:[^\]]+\]\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"__[^_\n]+__", "", text)
    text = _strip_templates(text)
    text = re.sub(r"\[\[([^\]]+)\]\]", _unwrap_wikilink, text)
    text = re.sub(r"'''+", "", text)
    text = re.sub(r"''", "", text)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?(?:poem|nowiki|center|div|span|p)\b[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return _normalize_extracted_text(text)


def _extract_html_text(html_text: str) -> str:
    if not html_text:
        return ""

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_text, "html.parser")
    strip_selectors = [
        "span.mw-editsection",
        "sup.reference",
        "ol.references",
        "div.reflist",
        ".ws-noexport",
        "#headertemplate",
        "#ws-data",
        "div.printfooter",
        "div.catlinks",
        "table.metadata",
        "table.navbox",
        "style",
        "script",
        "noscript",
    ]
    for selector in strip_selectors:
        for element in soup.select(selector):
            element.decompose()

    for br in soup.find_all("br"):
        br.replace_with("\n")

    definition_lines = []
    for item in soup.select("dl dd"):
        line = _normalize_extracted_text(item.get_text(separator="\n", strip=False))
        if not line:
            continue
        if not definition_lines and item.find(["b", "strong"]) and len(line.split()) <= 8:
            continue
        definition_lines.append(line)
    if definition_lines:
        return "\n".join(definition_lines)

    poem_candidates = soup.select("div.poem, .poem")
    candidates = poem_candidates or soup.select("div.mw-parser-output")
    if not candidates:
        candidates = [soup]

    unique_candidates = []
    seen_candidate_ids = set()
    for candidate in candidates:
        candidate_id = id(candidate)
        if candidate_id not in seen_candidate_ids:
            unique_candidates.append(candidate)
            seen_candidate_ids.add(candidate_id)

    parts = []
    for candidate in unique_candidates:
        text = candidate.get_text(separator="\n", strip=False)
        if text.strip():
            parts.append(text)
    extracted = _normalize_extracted_text("\n\n".join(parts))
    if poem_candidates:
        return "\n".join(line for line in extracted.splitlines() if line.strip())
    return extracted


def extract_text(wikitext: str, html_text: str) -> str:
    """Extract clean verse, preferring explicit <poem> wikitext when present."""
    poem_blocks = re.findall(r"<poem\b[^>]*>(.*?)</poem>", wikitext or "", flags=re.IGNORECASE | re.DOTALL)
    if poem_blocks:
        return _normalize_extracted_text(
            "\n\n".join(_clean_wikitext_fragment(block) for block in poem_blocks if block.strip())
        )
    return _extract_html_text(html_text)


def _load_skip_titles(path: Path | None) -> set[str]:
    if path is None:
        return set()
    titles = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            title = line.split("#", 1)[0].strip()
            if title:
                titles.add(_title_key(title))
    return titles


def _title_key(title: str) -> str:
    return re.sub(r"\s+", " ", title.replace("_", " ")).strip().casefold()


def _is_skipped_title(title: str, skip_titles: set[str]) -> bool:
    if not skip_titles:
        return False
    return _title_key(title) in skip_titles or _title_key(f"{NAROD_AUTHOR}. {title}") in skip_titles


def build_worklist(
    category: str,
    *,
    skip_titles_file: Path | None = None,
    limit: int | None = None,
) -> list[dict]:
    pages = discover_category_pages(category)
    skip_titles = _load_skip_titles(skip_titles_file)
    worklist: list[dict] = []
    for title in pages:
        if _is_skipped_title(title, skip_titles):
            print(f"  [skip] {title} (skip-titles-file)")
            continue
        worklist.append({"title": title, "source_url": source_url_for_title(title)})
        if limit is not None and len(worklist) >= limit:
            break
    return worklist


def _incipit(text: str, max_lines: int = 3) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " / ".join(lines[:max_lines])


def _folk_output_path(category: str) -> Path:
    return LITERARY_DIR / f"wikisource-folk-{_category_slug(category)}.jsonl"


def _write_folk_jsonl(
    output_path: Path,
    worklist: list[dict],
    *,
    genre: str,
) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_chunks = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for index, work in enumerate(worklist, 1):
            title = work["title"]
            source_url = work["source_url"]
            print(f"  [{index}/{len(worklist)}] {title}")
            try:
                wikitext, html_text = fetch_parse(title)
                version_target = _version_target_title(wikitext)
                if version_target:
                    print(f"    versions page → {version_target}")
                    wikitext, html_text = fetch_parse(version_target)
                    source_url = source_url_for_title(version_target)
                text = extract_text(wikitext, html_text)
            except Exception as exc:
                print(f"    ERROR: {type(exc).__name__}: {exc}")
                continue

            if len(text) < 50:
                print(f"    Skipped: too short ({len(text)} chars)")
                continue

            incipit = _incipit(text)
            print(f"    incipit: {incipit}")

            work_title = f"{NAROD_AUTHOR}. {title}"
            chunks = chunk_folk_text(text, work_title, source_url, min_tokens=20)
            for chunk in chunks:
                chunk.update({
                    "title": title,
                    "work": work_title,
                    "author": NAROD_AUTHOR,
                    "year": NAROD_YEAR,
                    "genre": genre,
                    "language_period": NAROD_PERIOD,
                    "incipit": incipit,
                })
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            print(f"    {len(text):,} chars → {len(chunks)} chunks [{genre}]")
            total_chunks += len(chunks)
            if index < len(worklist):
                time.sleep(DELAY_BETWEEN_WORKS)
    return total_chunks


def ingest_jsonl(jsonl_path: Path, db_path: Path) -> int:
    source_file = jsonl_path.stem
    rows = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            rows.append(build_literary_row(entry, source_file=source_file, chunk_index=len(rows), warn=print))

    lit_sql = """INSERT INTO literary_texts
                 (chunk_id, title, text, source_file, source_url, author, work, work_id,
                  year, genre, language_period, char_count)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    conn = sqlite3.connect(str(db_path))
    try:
        with conn:
            conn.execute("DELETE FROM literary_texts WHERE source_file = ?", (source_file,))
            if rows:
                conn.executemany(lit_sql, rows)
            conn.execute("INSERT INTO literary_fts(literary_fts) VALUES('rebuild')")
    finally:
        conn.close()
    return len(rows)


def scrape_category(
    category: str = DEFAULT_FOLK_CATEGORY,
    *,
    dry_run: bool = False,
    ingest: bool = False,
    skip_titles_file: Path | None = None,
    limit: int | None = None,
    genre: str | None = None,
    db_path: Path = DEFAULT_DB_PATH,
) -> int:
    """Scrape one Wikisource folk category to JSONL, optionally replacing DB rows."""
    output_path = _folk_output_path(category)
    worklist = build_worklist(category, skip_titles_file=skip_titles_file, limit=limit)
    resolved_genre = genre or genre_from_category(category)

    print(f"[wikisource-folk] {category}: {len(worklist)} pages → {output_path}")
    total_chunks = _write_folk_jsonl(output_path, worklist, genre=resolved_genre)

    ok, errors = audit_jsonl(output_path)
    if not ok:
        print("[wikisource-folk] JSONL audit failed:")
        for error in errors:
            print(f"  {error}")
        raise RuntimeError(f"JSONL audit failed for {output_path}")
    print(f"[wikisource-folk] JSONL audit passed: {output_path}")

    if dry_run:
        print("[wikisource-folk] dry-run: wrote JSONL only; no DB changes")
        return total_chunks

    if ingest:
        inserted = ingest_jsonl(output_path, db_path)
        print(f"[wikisource-folk] ingested {inserted} rows into {db_path}")

    return total_chunks


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
    from bs4 import BeautifulSoup

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


# Minimum fraction of Cyrillic letters (out of letters total) for a chunk
# to be kept. Wikisource hosts a lot of trilingual / parallel-text pages
# (e.g. Конституція Пилипа Орлика has Latin original + book Ukrainian +
# modern Ukrainian in three columns). A naive paragraph-chunker will
# emit chunks that are 30-50% Latin, polluting FTS5 search and the wiki
# agent's "real Ukrainian content" filter. Default 0.6 keeps anything
# majority-Cyrillic; --cyrillic-min on the CLI can override.
_DEFAULT_CYRILLIC_MIN = 0.6
_CYRILLIC_RE = re.compile(r"[а-яіїєґА-ЯІЇЄҐ]")
_LATIN_RE = re.compile(r"[a-zA-Z]")


def _cyrillic_ratio(text: str) -> float:
    """Fraction of letter characters that are Cyrillic. 1.0 = all Ukrainian,
    0.0 = all Latin / no letters at all."""
    cyr = len(_CYRILLIC_RE.findall(text))
    lat = len(_LATIN_RE.findall(text))
    total = cyr + lat
    return (cyr / total) if total else 0.0


def chunk_text(
    text: str,
    work_title: str,
    metadata: dict,
    cyrillic_min: float = _DEFAULT_CYRILLIC_MIN,
) -> list[dict]:
    """Split text into chunks at paragraph boundaries.

    Chunks below `cyrillic_min` letter ratio are dropped — this filters
    out Latin-heavy passages from trilingual Wikisource pages.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks = []
    current_text = ""
    chunk_idx = 0
    dropped = 0
    work_id = re.sub(r'[^\w]', '_', work_title)[:50]
    id_prefix = f"ws_{work_id}"

    def _flush():
        nonlocal current_text, chunk_idx, dropped
        if not current_text.strip():
            return
        ratio = _cyrillic_ratio(current_text)
        if ratio < cyrillic_min:
            dropped += 1
            current_text = ""
            return
        chunk_id = f"{id_prefix}_c{chunk_idx:03d}"
        chunks.append({
            "chunk_id": chunk_id,
            "text": current_text.strip(),
            "token_count": len(current_text.strip()) // 4,
            "cyrillic_ratio": round(ratio, 2),
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
    cyrillic_min: float = _DEFAULT_CYRILLIC_MIN,
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

            chunks = chunk_text(text, title, metadata, cyrillic_min=cyrillic_min)
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            total_chunks += len(chunks)
            print(f"{len(chunks)} chunks ({len(text)} chars)")

    print(f"\n[wikisource] {author_full}: {total_chunks} chunks → {outfile}")
    return total_chunks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scrape Ukrainian Wikisource for literary RAG")
    parser.add_argument("--category", default=DEFAULT_FOLK_CATEGORY, help="Folk category to scrape")
    parser.add_argument("--skip-titles-file", type=Path, help="Newline list of titles already hosted/in corpus")
    parser.add_argument("--limit", type=int, help="Limit page count for smoke tests")
    parser.add_argument("--ingest", action="store_true", help="Replace rows for this JSONL in a sources.db")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="SQLite sources DB for --ingest")
    parser.add_argument("--author", help="Short author name for search (e.g., 'Хвильовий')")
    parser.add_argument("--author-full", help="Full author name for metadata (e.g., 'Хвильовий М.')")
    parser.add_argument("--year", type=int, default=0, help="Publication year (for single works)")
    parser.add_argument("--year-range", default="", help="Year range (e.g., '1923-1933')")
    parser.add_argument("--genre", help="Genre override; author mode defaults to prose")
    parser.add_argument("--period", default="modern", help="Language period (default: modern)")
    parser.add_argument("--pages", nargs="+", help="Specific page titles to scrape")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Category mode: write JSONL only, no DB changes. Author mode: list pages without scraping.",
    )
    parser.add_argument(
        "--cyrillic-min", type=float, default=_DEFAULT_CYRILLIC_MIN,
        help=(
            "Minimum Cyrillic letter fraction for a chunk to be kept (0.0-1.0). "
            "Defaults to 0.6 — drops chunks that are mostly Latin/Greek, which "
            "happens on trilingual / parallel-text pages like the Orlyk "
            "Constitution. Set to 0.0 to keep everything."
        ),
    )
    args = parser.parse_args(argv)

    if args.author:
        if not args.author_full:
            parser.error("--author-full is required with --author")
        if args.ingest or args.skip_titles_file or args.limit is not None:
            parser.error("--ingest, --skip-titles-file, and --limit are only supported in category mode")
        scrape_author(
            author_short=args.author,
            author_full=args.author_full,
            year=args.year,
            year_range=args.year_range,
            genre=args.genre or "prose",
            period=args.period,
            dry_run=args.dry_run,
            pages=args.pages,
            cyrillic_min=args.cyrillic_min,
        )
        return 0

    if args.pages:
        parser.error("--pages is only supported with --author")
    if args.year or args.year_range or args.period != "modern" or args.cyrillic_min != _DEFAULT_CYRILLIC_MIN:
        parser.error("--year, --year-range, --period, and --cyrillic-min are only supported with --author")
    if args.dry_run and args.ingest:
        parser.error("--dry-run and --ingest are mutually exclusive")
    if not args.dry_run and not args.ingest:
        parser.error("category mode requires --dry-run or --ingest")

    scrape_category(
        category=args.category,
        dry_run=args.dry_run,
        ingest=args.ingest,
        skip_titles_file=args.skip_titles_file,
        limit=args.limit,
        genre=args.genre,
        db_path=args.db,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
