"""Scrape texts from litopys.org.ua / izbornyk.org.ua for the literary RAG.

Handles:
- windows-1251 → UTF-8 conversion
- HTML → clean text extraction
- Parallel text tables (original | modern Ukrainian)
- Multi-page works (follows "Наступна" links)
- Chunking at paragraph boundaries

Usage:
    # Scrape a single page
    .venv/bin/python scripts/rag/scrape_litopys.py \
        --url http://litopys.org.ua/slovo/slovo.htm \
        --work "Слово о полку Ігоревім" --author "Anonymous" \
        --year 1187 --genre poetry --period old_east_slavic

    # Scrape a multi-page work (follows "Наступна" links)
    .venv/bin/python scripts/rag/scrape_litopys.py \
        --url http://litopys.org.ua/samovyd/sam01.htm \
        --work "Літопис Самовидця" --author "Anonymous" \
        --year 1702 --genre chronicle --period middle_ukrainian \
        --follow-next --max-pages 30

    # Scrape parallel text (e.g., PVL Yaremenko)
    .venv/bin/python scripts/rag/scrape_litopys.py \
        --url http://litopys.org.ua/pvlyar/yar01.htm \
        --work "Повість временних літ (Яременко)" --author "Nestor" \
        --year 1113 --genre chronicle --period old_east_slavic \
        --parallel --follow-next --max-pages 50

Output: JSONL file in data/literary_texts/
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
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag.config import CHUNK_MAX_TOKENS, CHUNK_MIN_TOKENS, LITERARY_DIR


class HTMLTextExtractor(HTMLParser):
    """Extract text from HTML, handling parallel text tables.

    Filters litopys.org.ua navigation chrome by only extracting text from
    <div class="dop3"> content divs. Skips nav links (Попередня/Наступна/etc).
    """

    # Navigation link text to skip (inside dop3 but not content)
    _NAV_TEXTS: ClassVar[set[str]] = {"Попередня", "Головна", "Наступна", "ІЗБОРНИК"}

    def __init__(self, parallel: bool = False):
        super().__init__()
        self.parallel = parallel
        self.text_parts: list[str] = []
        self.parallel_pairs: list[tuple[str, str]] = []
        self._in_table = False
        self._in_td = False
        self._td_count = 0
        self._current_row: list[str] = []
        self._current_td_text = ""
        self._skip_tags = {"script", "style", "noscript"}
        self._skip_depth = 0
        self._in_heading = False
        # Content filtering: only extract from dop3 divs
        self._content_depth = 0  # >0 means inside a dop3 div
        self._div_depth_stack: list[bool] = []  # track which divs are dop3
        self._in_nav_link = False  # skip nav <a> text

    def _get_attr(self, attrs: list, name: str) -> str:
        for k, v in attrs:
            if k == name:
                return v or ""
        return ""

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self._skip_tags:
            self._skip_depth += 1
            return

        if tag == "div":
            css_class = self._get_attr(attrs, "class")
            is_content = "dop3" in css_class
            self._div_depth_stack.append(is_content)
            if is_content:
                self._content_depth += 1

        # Only process content tags when inside dop3
        if self._content_depth == 0:
            return

        if tag == "a":
            # Will check text in handle_data to skip nav links
            self._in_nav_link = True
        elif tag == "table" and self.parallel:
            self._in_table = True
        elif tag == "tr" and self._in_table:
            self._current_row = []
            self._td_count = 0
        elif tag == "td" and self._in_table:
            self._in_td = True
            self._current_td_text = ""
            self._td_count += 1
        elif tag in ("h1", "h2", "h3"):
            self._in_heading = True
        elif tag in ("p", "br") and not self._in_table:
            self.text_parts.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self._skip_tags and self._skip_depth > 0:
            self._skip_depth -= 1
            return

        if tag == "div" and self._div_depth_stack:
            was_content = self._div_depth_stack.pop()
            if was_content:
                self._content_depth -= 1
            return

        if self._content_depth == 0:
            return

        if tag == "a":
            self._in_nav_link = False
        elif tag == "table" and self._in_table:
            self._in_table = False
        elif tag == "td" and self._in_td:
            self._in_td = False
            self._current_row.append(self._current_td_text.strip())
        elif tag == "tr" and self._in_table:
            if len(self._current_row) >= 2:
                self.parallel_pairs.append(
                    (self._current_row[0], self._current_row[1])
                )
        elif tag in ("h1", "h2", "h3"):
            self._in_heading = False
            self.text_parts.append("\n\n")
        elif tag == "p" and not self._in_table:
            self.text_parts.append("\n\n")

    def handle_data(self, data):
        if self._skip_depth > 0:
            return
        if self._content_depth == 0:
            return
        # Skip navigation link text
        if self._in_nav_link and data.strip() in self._NAV_TEXTS:
            return
        if self._in_td:
            self._current_td_text += data
        else:
            self.text_parts.append(data)

    def get_text(self) -> str:
        raw = "".join(self.text_parts)
        # Normalize whitespace but keep paragraph breaks
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        # Remove litopys.org.ua chrome remnants
        lines = raw.split("\n")
        cleaned = []
        for line in lines:
            stripped = line.strip()
            # Skip nav arrows (‹›), copyright, empty, editorial metadata
            if not stripped:
                cleaned.append("")
                continue
            if stripped in ("‹", "›", "‹‹", "››", "&nbsp;"):
                continue
            if stripped.startswith("©") or stripped.startswith("Праці про"):
                continue
            if re.match(r"^\d+\.\w+\.\d{4}\b", stripped):
                continue  # Date stamps like "19.IX.2001"
            cleaned.append(line)
        return "\n".join(cleaned).strip()

    def get_parallel_text(self) -> str:
        """For parallel texts: return modern Ukrainian column (right side)."""
        if not self.parallel_pairs:
            return self.get_text()
        return "\n\n".join(modern.strip() for _, modern in self.parallel_pairs if modern.strip())

    def get_original_text(self) -> str:
        """For parallel texts: return original text column (left side)."""
        if not self.parallel_pairs:
            return ""
        return "\n\n".join(orig.strip() for orig, _ in self.parallel_pairs if orig.strip())


def fetch_page(url: str) -> str:
    """Fetch a page from litopys.org.ua handling windows-1251 encoding."""
    result = subprocess.run(
        ["curl", "-sL", "--max-time", "30",
         "-e", "http://litopys.org.ua/",  # Referer header (some sections block without it)
         url],
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed for {url}: {result.stderr.decode()}")

    # Try windows-1251 first (most litopys pages)
    try:
        return result.stdout.decode("windows-1251")
    except UnicodeDecodeError:
        return result.stdout.decode("utf-8", errors="replace")


def find_next_link(html: str, base_url: str) -> str | None:
    """Find the "Наступна" (Next) link in a litopys page."""
    # Common patterns: <a href="...">Наступна</a>
    match = re.search(
        r'<a\s+href="([^"]+)"[^>]*>\s*Наступна\s*</a>',
        html,
        re.IGNORECASE,
    )
    if match:
        return urljoin(base_url, match.group(1))
    return None


def chunk_text(
    text: str,
    work: str,
    source_url: str,
    min_tokens: int = CHUNK_MIN_TOKENS,
    max_tokens: int = CHUNK_MAX_TOKENS,
    original_text: str = "",
) -> list[dict]:
    """Split text into chunks at paragraph boundaries."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    # Also split original text for parallel alignment
    orig_paragraphs = []
    if original_text:
        orig_paragraphs = [p.strip() for p in original_text.split("\n\n") if p.strip()]

    chunks = []
    current_text = ""
    current_orig = ""
    chunk_idx = 0

    for i, para in enumerate(paragraphs):
        # Rough token estimate (Ukrainian ~1.5 chars per token)
        current_tokens = len(current_text) // 4

        if current_tokens + len(para) // 4 > max_tokens and current_text:
            # Save current chunk
            chunk_id = f"{hashlib.md5(work.encode()).hexdigest()[:8]}_c{chunk_idx:04d}"
            chunk = {
                "chunk_id": chunk_id,
                "text": current_text.strip(),
                "source_url": source_url,
                "token_count": len(current_text.strip()) // 4,
            }
            if current_orig:
                chunk["original_text"] = current_orig.strip()
            chunks.append(chunk)
            chunk_idx += 1
            current_text = ""
            current_orig = ""

        current_text += para + "\n\n"
        if i < len(orig_paragraphs):
            current_orig += orig_paragraphs[i] + "\n\n"

    # Don't forget the last chunk
    if current_text.strip() and len(current_text.strip()) // 4 >= min_tokens:
        chunk_id = f"{hashlib.md5(work.encode()).hexdigest()[:8]}_c{chunk_idx:04d}"
        chunk = {
            "chunk_id": chunk_id,
            "text": current_text.strip(),
            "source_url": source_url,
            "token_count": len(current_text.strip()) // 4,
        }
        if current_orig:
            chunk["original_text"] = current_orig.strip()
        chunks.append(chunk)

    return chunks


def scrape_work(
    url: str,
    work: str,
    author: str,
    year: int,
    genre: str,
    period: str,
    parallel: bool = False,
    follow_next: bool = False,
    max_pages: int = 100,
) -> list[dict]:
    """Scrape a complete work from litopys.org.ua.

    Returns list of chunk dicts ready for JSONL output.
    """
    all_text = ""
    all_original = ""
    pages_scraped = 0
    current_url = url
    visited_urls: set[str] = set()

    while current_url and pages_scraped < max_pages:
        # Loop detection: skip already-visited URLs
        if current_url in visited_urls:
            print(f"  [loop] Already visited {current_url}, stopping.")
            break
        visited_urls.add(current_url)

        print(f"  Fetching page {pages_scraped + 1}: {current_url}")
        html = fetch_page(current_url)

        extractor = HTMLTextExtractor(parallel=parallel)
        extractor.feed(html)

        if parallel:
            page_text = extractor.get_parallel_text()
            page_orig = extractor.get_original_text()
            all_original += page_orig + "\n\n"
        else:
            page_text = extractor.get_text()

        all_text += page_text + "\n\n"
        pages_scraped += 1

        if follow_next:
            current_url = find_next_link(html, current_url)
            if current_url:
                time.sleep(0.5)  # Be polite
        else:
            current_url = None

    print(f"  Scraped {pages_scraped} pages, ~{len(all_text)} chars")

    # Chunk
    chunks = chunk_text(
        all_text, work, url,
        original_text=all_original if parallel else "",
    )

    # Add metadata to each chunk
    for chunk in chunks:
        chunk.update({
            "work": work,
            "author": author,
            "year": year,
            "genre": genre,
            "language_period": period,
        })

    print(f"  Generated {len(chunks)} chunks")
    return chunks


def save_chunks(chunks: list[dict], output_path: Path):
    """Save chunks as JSONL."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"  Saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Scrape litopys.org.ua texts for RAG")
    parser.add_argument("--url", required=True, help="Starting URL")
    parser.add_argument("--work", required=True, help="Work title (Ukrainian)")
    parser.add_argument("--author", required=True, help="Author name")
    parser.add_argument("--year", type=int, required=True, help="Year of composition")
    parser.add_argument("--genre", required=True,
                        choices=["chronicle", "poetry", "prose", "drama", "legal",
                                 "grammar", "religious", "scholarly", "lexicon",
                                 "fable", "interlude", "letter", "manual",
                                 "anthology", "polemic", "philosophy", "encyclopedia",
                                 "hagiography", "rhetoric", "travelogue", "diary",
                                 "memoir", "biography", "letters", "documents",
                                 "reference", "ethnography"],
                        help="Text genre")
    parser.add_argument("--period", required=True,
                        choices=["old_east_slavic", "middle_ukrainian",
                                 "early_modern", "modern"],
                        help="Language period")
    parser.add_argument("--parallel", action="store_true",
                        help="Parse as parallel text (original | modern in table)")
    parser.add_argument("--follow-next", action="store_true",
                        help="Follow 'Наступна' links for multi-page works")
    parser.add_argument("--max-pages", type=int, default=100,
                        help="Max pages to follow (default: 100)")
    parser.add_argument("--output", type=str, help="Output JSONL path (auto-generated if omitted)")
    args = parser.parse_args()

    print(f"\n[scrape] Scraping: {args.work}")
    print(f"  URL: {args.url}")
    print(f"  Mode: {'parallel' if args.parallel else 'single'}, "
          f"follow={'yes' if args.follow_next else 'no'}")

    chunks = scrape_work(
        url=args.url,
        work=args.work,
        author=args.author,
        year=args.year,
        genre=args.genre,
        period=args.period,
        parallel=args.parallel,
        follow_next=args.follow_next,
        max_pages=args.max_pages,
    )

    if not chunks:
        print("  No chunks generated!")
        return

    # Auto-generate output path from work title
    if args.output:
        output_path = Path(args.output)
    else:
        slug = re.sub(r"[^\w\s-]", "", args.work.lower())
        slug = re.sub(r"[\s]+", "-", slug)[:60]
        output_path = LITERARY_DIR / f"{slug}.jsonl"

    save_chunks(chunks, output_path)
    print(f"\n[scrape] Done! {len(chunks)} chunks saved.")


if __name__ == "__main__":
    main()
