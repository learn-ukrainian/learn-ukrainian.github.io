"""Crawl the Encyclopedia of Modern Ukraine (esu.com.ua) for RAG indexing.

Two-phase crawl:
  Phase 1 — Discover all article URLs via alphabetical letter pages
  Phase 2 — Fetch each article, extract text + metadata, output JSONL chunks

Usage:
    # Full crawl (discover + fetch + chunk)
    .venv/bin/python scripts/rag/crawl_esu.py

    # Discover article URLs only (fast, ~30 min)
    .venv/bin/python scripts/rag/crawl_esu.py --discover-only

    # Fetch articles using existing URL list (resumable)
    .venv/bin/python scripts/rag/crawl_esu.py --skip-discover

    # Limit to specific letters (for testing)
    .venv/bin/python scripts/rag/crawl_esu.py --letters а б в

Output:
    data/esu/urls.jsonl          — discovered article URLs + titles
    data/esu/articles.jsonl      — full article text + metadata
    data/esu/chunks.jsonl        — chunked for RAG ingestion
"""

import argparse
import hashlib
import json
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urljoin

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag.config import CHUNK_MAX_TOKENS, CHUNK_MIN_TOKENS, DATA_DIR

# ── Config ────────────────────────────────────────────────────────
ESU_BASE = "https://esu.com.ua"
ESU_DIR = DATA_DIR / "esu"
URLS_PATH = ESU_DIR / "urls.jsonl"
ARTICLES_PATH = ESU_DIR / "articles.jsonl"
CHUNKS_PATH = ESU_DIR / "chunks.jsonl"

CRAWL_DELAY = 0.2  # seconds between requests (shared across workers)
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

UKRAINIAN_LETTERS = list("абвгґдеєжзиіїйклмнопрстуфхцчшщьюя")

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "LearnUkrainianBot/1.0 (educational project; +https://github.com/learn-ukrainian)",
    "Accept-Language": "uk",
})


# ── HTTP helpers ──────────────────────────────────────────────────

def fetch(url: str) -> str:
    """Fetch a URL with retry and backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = SESSION.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            return resp.text
        except (requests.RequestException, ConnectionError) as e:
            if attempt < MAX_RETRIES - 1:
                wait = 2 ** (attempt + 1)
                print(f"  [retry] {e} — waiting {wait}s")
                time.sleep(wait)
            else:
                raise
    return ""  # unreachable


# ── Dedup helpers ────────────────────────────────────────────────

def _dedup_jsonl(path: Path) -> int:
    """Deduplicate a JSONL file by 'id' field in-place. Returns unique count."""
    seen: set[int] = set()
    tmp = path.with_suffix(".tmp")
    with open(path, encoding="utf-8") as fin, open(tmp, "w", encoding="utf-8") as fout:
        for line in fin:
            rec = json.loads(line)
            if rec["id"] not in seen:
                seen.add(rec["id"])
                fout.write(line)
    tmp.replace(path)
    return len(seen)


def _dedup_by_id(items: list[dict]) -> list[dict]:
    """Deduplicate a list of dicts by 'id' field, preserving order."""
    seen: set[int] = set()
    result = []
    for item in items:
        if item["id"] not in seen:
            seen.add(item["id"])
            result.append(item)
    return result


# ── Phase 1: Discover article URLs ───────────────────────────────

class LetterPageParser(HTMLParser):
    """Extract article links from a letter listing page."""

    def __init__(self):
        super().__init__()
        self.articles: list[dict] = []  # [{url, title}]
        self.total_pages: int = 0
        self._in_link = False
        self._current_href = ""
        self._current_text = ""

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if "article-" in href:
                self._in_link = True
                self._current_href = href
                self._current_text = ""

    def handle_data(self, data):
        if self._in_link:
            self._current_text += data
        # Look for "Стор. X із Y" pagination text
        m = re.search(r"із\s+(\d+)", data)
        if m:
            self.total_pages = max(self.total_pages, int(m.group(1)))

    def handle_endtag(self, tag):
        if tag == "a" and self._in_link:
            self._in_link = False
            title = self._current_text.strip()
            href = self._current_href
            if title and href:
                # Normalize URL
                if not href.startswith("http"):
                    href = ESU_BASE + "/" + href.lstrip("/")
                # Extract article ID
                m = re.search(r"article-(\d+)", href)
                article_id = int(m.group(1)) if m else 0
                self.articles.append({
                    "id": article_id,
                    "url": href,
                    "title": title,
                })


def discover_letter(letter: str, urls_file) -> int:
    """Discover all article URLs for a given letter. Returns count."""
    encoded = quote(letter)
    # Fetch first page to get total page count
    url = f"{ESU_BASE}/letter.php?s={encoded}&page=1"
    html = fetch(url)

    parser = LetterPageParser()
    parser.feed(html)

    total_pages = parser.total_pages or 1
    count = 0

    # Write first page results
    for art in parser.articles:
        art["letter"] = letter
        urls_file.write(json.dumps(art, ensure_ascii=False) + "\n")
        count += 1

    # Fetch remaining pages
    for page in range(2, total_pages + 1):
        time.sleep(CRAWL_DELAY)
        url = f"{ESU_BASE}/letter.php?s={encoded}&page={page}"
        try:
            html = fetch(url)
        except Exception as e:
            print(f"  [error] Letter {letter} page {page}: {e}")
            continue

        parser = LetterPageParser()
        parser.feed(html)

        for art in parser.articles:
            art["letter"] = letter
            urls_file.write(json.dumps(art, ensure_ascii=False) + "\n")
            count += 1

        if page % 20 == 0:
            print(f"    Page {page}/{total_pages} ({count} articles)")
            urls_file.flush()

    return count


def run_discover(letters: list[str] | None = None):
    """Phase 1: discover all article URLs via letter pages."""
    letters = letters or UKRAINIAN_LETTERS
    ESU_DIR.mkdir(parents=True, exist_ok=True)

    # Load already-discovered letters for resumability
    done_letters: set[str] = set()
    if URLS_PATH.exists():
        with open(URLS_PATH, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                done_letters.add(rec.get("letter", ""))

    total = 0
    mode = "a" if done_letters else "w"
    with open(URLS_PATH, mode, encoding="utf-8") as f:
        for letter in letters:
            if letter in done_letters:
                # Count existing
                existing = sum(
                    1 for line in open(URLS_PATH, encoding="utf-8")
                    if json.loads(line).get("letter") == letter
                )
                print(f"[discover] Letter «{letter}» — skip ({existing} already discovered)")
                total += existing
                continue

            print(f"[discover] Letter «{letter}»...")
            time.sleep(CRAWL_DELAY)
            try:
                count = discover_letter(letter, f)
                f.flush()
                print(f"  → {count} articles")
                total += count
            except Exception as e:
                print(f"  [error] Letter «{letter}»: {e}")

    # Deduplicate urls.jsonl by article ID (same article appears under multiple letters)
    unique_count = _dedup_jsonl(URLS_PATH)
    if unique_count < total:
        print(f"\n[discover] Deduplicated: {total} → {unique_count} unique articles → {URLS_PATH}")
    else:
        print(f"\n[discover] Total: {total} article URLs → {URLS_PATH}")
    return unique_count


# ── Phase 2: Fetch articles ──────────────────────────────────────

class ArticleParser(HTMLParser):
    """Extract article body and metadata from an ESU article page."""

    def __init__(self):
        super().__init__()
        self.body_parts: list[str] = []
        self.json_ld: str = ""
        self._in_body = False
        self._body_depth = 0
        self._in_script = False
        self._script_type = ""
        self._script_content = ""
        self._skip_tags = {"style", "noscript", "nav", "footer", "header"}
        self._skip_depth = 0
        self._in_heading = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag = tag.lower()

        if tag in self._skip_tags:
            self._skip_depth += 1
            return

        if tag == "script":
            self._in_script = True
            self._script_type = attrs_dict.get("type", "")
            self._script_content = ""
            return

        # Detect articleBody content
        if attrs_dict.get("itemprop") == "articleBody":
            self._in_body = True
            self._body_depth = 1
            return

        if self._in_body:
            # Track nesting depth inside articleBody
            if tag in ("div", "section", "article"):
                self._body_depth += 1
            if tag in ("h1", "h2", "h3", "h4"):
                self._in_heading = True
                self.body_parts.append("\n\n## ")
            elif tag == "p":
                self.body_parts.append("\n\n")
            elif tag == "br":
                self.body_parts.append("\n")
            elif tag == "li":
                self.body_parts.append("\n- ")

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in self._skip_tags and self._skip_depth > 0:
            self._skip_depth -= 1
            return

        if tag == "script" and self._in_script:
            self._in_script = False
            if "application/ld+json" in self._script_type:
                self.json_ld = self._script_content
            return

        if self._in_body:
            if tag in ("div", "section", "article"):
                self._body_depth -= 1
                if self._body_depth <= 0:
                    self._in_body = False
            if tag in ("h1", "h2", "h3", "h4"):
                self._in_heading = False
                self.body_parts.append("\n\n")
            elif tag == "p":
                self.body_parts.append("\n")

    def handle_data(self, data):
        if self._in_script:
            self._script_content += data
            return
        if self._skip_depth > 0:
            return
        if self._in_body:
            self.body_parts.append(data)

    def get_text(self) -> str:
        raw = "".join(self.body_parts)
        # Normalize whitespace
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()

    def get_metadata(self) -> dict:
        """Parse JSON-LD structured data."""
        if not self.json_ld:
            return {}
        try:
            data = json.loads(self.json_ld)
            # Extract author name(s) — can be dict, list of dicts, or string
            raw_author = data.get("author", "")
            if isinstance(raw_author, list):
                author = ", ".join(
                    a.get("name", "") if isinstance(a, dict) else str(a)
                    for a in raw_author
                )
            elif isinstance(raw_author, dict):
                author = raw_author.get("name", "")
            else:
                author = str(raw_author)

            raw_pub = data.get("publisher", "")
            publisher = raw_pub.get("name", "") if isinstance(raw_pub, dict) else str(raw_pub)

            return {
                "title": data.get("name", ""),
                "description": data.get("description", ""),
                "keywords": data.get("keywords", ""),
                "author": author,
                "date_published": data.get("datePublished", ""),
                "publisher": publisher,
            }
        except (json.JSONDecodeError, AttributeError):
            return {}


def fetch_article(article_id: int, url: str, title: str, letter: str) -> dict | None:
    """Fetch and parse a single ESU article."""
    try:
        html = fetch(url)
    except Exception as e:
        print(f"  [error] article-{article_id}: {e}")
        return None

    parser = ArticleParser()
    parser.feed(html)

    text = parser.get_text()
    if not text or len(text) < 50:
        return None

    metadata = parser.get_metadata()

    return {
        "id": article_id,
        "url": url,
        "title": metadata.get("title") or title,
        "letter": letter,
        "text": text,
        "author": metadata.get("author", ""),
        "date_published": metadata.get("date_published", ""),
        "keywords": metadata.get("keywords", ""),
        "description": metadata.get("description", ""),
        "char_count": len(text),
    }


def run_fetch(workers: int = 1):
    """Phase 2: fetch all discovered articles (resumable)."""
    if not URLS_PATH.exists():
        print("[fetch] No URLs file found. Run --discover-only first.")
        return 0

    # Load URLs
    urls = []
    with open(URLS_PATH, encoding="utf-8") as f:
        for line in f:
            urls.append(json.loads(line))

    # Deduplicate URLs by article ID (same article appears under multiple letters)
    unique_urls = _dedup_by_id(urls)
    if len(urls) != len(unique_urls):
        print(f"  Deduplicated: {len(urls)} → {len(unique_urls)} unique articles")
    urls = unique_urls

    print(f"[fetch] {len(urls)} articles to fetch")

    # Load already-fetched IDs for resumability
    fetched_ids: set[int] = set()
    if ARTICLES_PATH.exists():
        with open(ARTICLES_PATH, encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    fetched_ids.add(rec["id"])
                except (json.JSONDecodeError, KeyError):
                    continue
    if fetched_ids:
        print(f"  Resuming — {len(fetched_ids)} already fetched")

    # Filter to remaining work
    remaining = [e for e in urls if e["id"] not in fetched_ids]
    print(f"  {len(remaining)} remaining, {workers} worker(s)")

    if workers > 1:
        return _fetch_parallel(remaining, fetched_ids, workers)
    return _fetch_sequential(remaining, fetched_ids)


def _fetch_sequential(remaining: list[dict], fetched_ids: set[int]) -> int:
    """Single-threaded fetch."""
    fetched = len(fetched_ids)
    failed = 0
    with open(ARTICLES_PATH, "a", encoding="utf-8") as f:
        for i, entry in enumerate(remaining):
            time.sleep(CRAWL_DELAY)
            article = fetch_article(entry["id"], entry["url"], entry["title"], entry.get("letter", ""))

            if article:
                f.write(json.dumps(article, ensure_ascii=False) + "\n")
                fetched += 1
            else:
                failed += 1

            if (i + 1) % 100 == 0:
                f.flush()
                print(f"  [{i + 1}/{len(remaining)}] fetched={fetched} failed={failed}")

    print(f"\n[fetch] Done: {fetched} articles, {failed} failed → {ARTICLES_PATH}")
    return fetched


def _fetch_parallel(remaining: list[dict], fetched_ids: set[int], workers: int) -> int:
    """Multi-threaded fetch with shared rate limiter.

    Workers share a single lock that enforces CRAWL_DELAY between
    any two requests, regardless of which worker makes them.
    With 4 workers and 0.5s delay: ~2 req/s throughput while
    each request still has 0.5s spacing from the previous one.
    """
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed

    fetched = len(fetched_ids)
    failed = 0
    write_lock = threading.Lock()
    rate_lock = threading.Lock()
    last_request_time = [0.0]  # mutable container for closure

    f = open(ARTICLES_PATH, "a", encoding="utf-8")

    def rate_limited_fetch(entry: dict) -> dict | None:
        # Wait for rate limit
        with rate_lock:
            elapsed = time.monotonic() - last_request_time[0]
            if elapsed < CRAWL_DELAY:
                time.sleep(CRAWL_DELAY - elapsed)
            last_request_time[0] = time.monotonic()
        return fetch_article(entry["id"], entry["url"], entry["title"], entry.get("letter", ""))

    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(rate_limited_fetch, entry): i for i, entry in enumerate(remaining)}

            done_count = 0
            for fut in as_completed(futures):
                done_count += 1
                article = fut.result()
                with write_lock:
                    if article:
                        f.write(json.dumps(article, ensure_ascii=False) + "\n")
                        fetched += 1
                    else:
                        failed += 1

                    if done_count % 100 == 0:
                        f.flush()
                        print(f"  [{done_count}/{len(remaining)}] fetched={fetched} failed={failed}")
    finally:
        f.flush()
        f.close()

    print(f"\n[fetch] Done: {fetched} articles, {failed} failed → {ARTICLES_PATH}")
    return fetched


# ── Phase 3: Chunk articles ──────────────────────────────────────

def _split_long_paragraph(para: str, max_tokens: int) -> list[str]:
    """Split a paragraph that exceeds max_tokens at sentence boundaries."""
    sentences = re.split(r"(?<=[.!?])\s+", para)
    if len(sentences) <= 1:
        return [para]  # Can't split further

    parts = []
    current = ""
    for sent in sentences:
        if len(current) // 4 + len(sent) // 4 > max_tokens and current:
            parts.append(current.strip())
            current = ""
        current += sent + " "
    if current.strip():
        parts.append(current.strip())
    return parts


def chunk_article(article: dict) -> list[dict]:
    """Split article text into chunks at paragraph boundaries."""
    text = article["text"]
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    # Expand paragraphs that exceed max tokens
    expanded = []
    for para in paragraphs:
        if len(para) // 4 > CHUNK_MAX_TOKENS:
            expanded.extend(_split_long_paragraph(para, CHUNK_MAX_TOKENS))
        else:
            expanded.append(para)

    chunks = []
    current_text = ""
    chunk_idx = 0
    id_prefix = f"esu_{article['id']}"

    def _flush():
        nonlocal current_text, chunk_idx
        if not current_text.strip():
            return
        chunk_id = f"{id_prefix}_c{chunk_idx:03d}"
        chunks.append({
            "chunk_id": chunk_id,
            "text": current_text.strip(),
            "token_count": len(current_text.strip()) // 4,
            "article_id": article["id"],
            "title": article["title"],
            "url": article["url"],
            "letter": article["letter"],
            "author": article["author"],
            "keywords": article["keywords"],
        })
        chunk_idx += 1
        current_text = ""

    for para in expanded:
        current_tokens = len(current_text) // 4

        if current_tokens + len(para) // 4 > CHUNK_MAX_TOKENS and current_text:
            _flush()

        current_text += para + "\n\n"

    # Last chunk — keep even if under min (short articles are still valuable)
    _flush()

    return chunks


def run_chunk():
    """Phase 3: chunk all fetched articles."""
    if not ARTICLES_PATH.exists():
        print("[chunk] No articles file found. Run fetch first.")
        return 0

    total_chunks = 0
    total_articles = 0

    with open(ARTICLES_PATH, encoding="utf-8") as fin, \
         open(CHUNKS_PATH, "w", encoding="utf-8") as fout:
        for line in fin:
            try:
                article = json.loads(line)
            except json.JSONDecodeError:
                continue

            chunks = chunk_article(article)
            for chunk in chunks:
                fout.write(json.dumps(chunk, ensure_ascii=False) + "\n")

            total_chunks += len(chunks)
            total_articles += 1

    print(f"[chunk] {total_articles} articles → {total_chunks} chunks → {CHUNKS_PATH}")
    return total_chunks


# ── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Crawl ESU (esu.com.ua) for RAG indexing"
    )
    parser.add_argument(
        "--discover-only", action="store_true",
        help="Only discover article URLs (Phase 1)"
    )
    parser.add_argument(
        "--skip-discover", action="store_true",
        help="Skip URL discovery, use existing urls.jsonl"
    )
    parser.add_argument(
        "--fetch-only", action="store_true",
        help="Only fetch articles (Phase 2), skip chunking"
    )
    parser.add_argument(
        "--chunk-only", action="store_true",
        help="Only chunk existing articles (Phase 3)"
    )
    parser.add_argument(
        "--letters", nargs="+",
        help="Limit discovery to specific letters (e.g., --letters а б в)"
    )
    parser.add_argument(
        "--workers", type=int, default=1,
        help="Number of parallel fetch workers (default 1)"
    )
    args = parser.parse_args()

    ESU_DIR.mkdir(parents=True, exist_ok=True)

    if args.chunk_only:
        run_chunk()
        return

    if not args.skip_discover and not args.fetch_only:
        run_discover(args.letters)
        if args.discover_only:
            return

    if not args.discover_only:
        run_fetch(workers=args.workers)
        if not args.fetch_only:
            run_chunk()


if __name__ == "__main__":
    main()
