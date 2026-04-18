#!/usr/bin/env python3
"""Scrape Diasporiana PDF sources into literary JSONL chunks.

Targets public-domain Ukrainian historical works hosted on
``diasporiana.org.ua`` (and mirrors on ``elib.nlu.org.ua``).

Workflow:
1. Fetch the work page and resolve the PDF URL.
2. Probe for an embedded text layer via ``pdftotext -layout`` first.
3. If the text layer is empty / garbled, OCR each page with Tesseract.
4. Chunk the extracted text at paragraph boundaries and write JSONL with
   the same schema used by the litopys/izbornyk waves.

Usage:
    # Scrape Doroshenko vol. 1
    .venv/bin/python scripts/rag/scrape_diasporiana.py --vol 1

    # Scrape both volumes
    .venv/bin/python scripts/rag/scrape_diasporiana.py --vol 1 --vol 2

    # Scrape a custom Diasporiana URL
    .venv/bin/python scripts/rag/scrape_diasporiana.py \
        --url "https://diasporiana.org.ua/..." \
        --slug custom-slug --volume 1 \
        --work "Назва праці" --author "Автор А." --year 1932
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import BinaryIO
from urllib.parse import urljoin, urlparse

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag.config import CHUNK_MAX_TOKENS, LITERARY_DIR
from rag.scrape_wikisource import _DEFAULT_CYRILLIC_MIN, _cyrillic_ratio

ALLOWED_HOSTS = {"diasporiana.org.ua", "www.diasporiana.org.ua", "elib.nlu.org.ua"}
REQUEST_TIMEOUT_S = 60
RATE_LIMIT_MIN_S = 2.0
RATE_LIMIT_MAX_S = 3.0
TEXT_LAYER_MIN_CYRILLIC_PER_PAGE = 500
OCR_LANG = "ukr+rus"
OCR_DPI = 250
USER_AGENT = (
    "LearnUkrainianBot/1.0 "
    "(https://learn-ukrainian.github.io; educational project)"
)
GENRE = "scholarly"
LANGUAGE_PERIOD = "modern"


@dataclass(frozen=True)
class SourceSpec:
    slug: str
    volume: int
    url: str
    work: str
    author: str
    year: int
    genre: str = GENRE
    language_period: str = LANGUAGE_PERIOD

    @property
    def output_name(self) -> str:
        return f"wave13-{self.slug}.jsonl"


@dataclass(frozen=True)
class PageText:
    page: int
    volume: int
    author: str
    year: int
    work_title: str
    source_url: str
    text: str


PRESET_VOLUMES: dict[int, SourceSpec] = {
    1: SourceSpec(
        slug="doroshenko-narys-istoriyi-ukrayiny-t1",
        volume=1,
        url=(
            "https://diasporiana.org.ua/istoriya/"
            "doroshenko-d-narys-istoriyi-ukrayiny-t-1-do-polovyny-xvii-stolittya/"
        ),
        work="Дорошенко — Нарис історії України, том 1: До половини XVII століття",
        author="Дорошенко Д.",
        year=1932,
    ),
    2: SourceSpec(
        slug="doroshenko-narys-istoriyi-ukrayiny-t2",
        volume=2,
        url=(
            "https://diasporiana.org.ua/istoriya/"
            "doroshenko-d-narys-istoriyi-ukrayiny-t-2-vid-polovyny-xvii-stolittya/"
        ),
        work="Дорошенко — Нарис історії України, том 2: Від половини XVII століття",
        author="Дорошенко Д.",
        year=1933,
    ),
}

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})

_CYRILLIC_RE = re.compile(r"[А-Яа-яІіЇїЄєҐґ]")
_PAGE_NUMBER_RE = re.compile(r"^[—\-– ]*\d+[—\-– ]*$")


class PdfLinkParser(HTMLParser):
    """Find the first PDF link on a source page."""

    def __init__(self) -> None:
        super().__init__()
        self.pdf_url: str | None = None
        self._current_href: str | None = None
        self._capture_pdf_text = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attr_map = {k: v or "" for k, v in attrs}
        href = attr_map.get("href", "")
        if href.lower().endswith(".pdf"):
            self.pdf_url = href
            return
        self._current_href = href
        self._capture_pdf_text = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a":
            self._current_href = None
            self._capture_pdf_text = False

    def handle_data(self, data: str) -> None:
        if not self._capture_pdf_text or not self._current_href:
            return
        if "pdf" in data.lower():
            self.pdf_url = self._current_href


class RequestPacer:
    """Conservative per-domain pacing for slow single-host archives."""

    def __init__(self, low: float = RATE_LIMIT_MIN_S, high: float = RATE_LIMIT_MAX_S) -> None:
        self.low = low
        self.high = high
        self._seen_requests = 0

    def wait(self) -> None:
        if self._seen_requests == 0:
            self._seen_requests += 1
            return
        delay = random.uniform(self.low, self.high)
        time.sleep(delay)
        self._seen_requests += 1


def _validate_allowed_url(url: str) -> None:
    host = urlparse(url).netloc.lower()
    if host not in ALLOWED_HOSTS:
        raise ValueError(f"Unsupported host for Diasporiana scraper: {host}")


def _request(
    url: str,
    pacer: RequestPacer,
    *,
    stream: bool = False,
    max_retries: int = 3,
) -> requests.Response:
    _validate_allowed_url(url)
    backoff = 5.0
    last_error: Exception | None = None
    for attempt in range(max_retries):
        pacer.wait()
        try:
            response = SESSION.get(url, timeout=REQUEST_TIMEOUT_S, stream=stream)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt == max_retries - 1:
                break
            print(
                f"  [retry] {type(exc).__name__} for {url} "
                f"(attempt {attempt + 1}/{max_retries}), sleeping {backoff:.0f}s"
            )
            time.sleep(backoff)
            backoff *= 2
    raise RuntimeError(f"Failed to fetch {url}: {last_error}") from last_error


def resolve_pdf_url(source_url: str, pacer: RequestPacer) -> str:
    """Resolve a work page to its PDF URL, or pass through direct PDFs."""

    _validate_allowed_url(source_url)
    if source_url.lower().endswith(".pdf"):
        return source_url

    response = _request(source_url, pacer)
    parser = PdfLinkParser()
    parser.feed(response.text)
    if parser.pdf_url:
        pdf_url = urljoin(source_url, parser.pdf_url)
        _validate_allowed_url(pdf_url)
        return pdf_url

    match = re.search(r'href="([^"]+\.pdf)"', response.text, re.IGNORECASE)
    if match:
        pdf_url = urljoin(source_url, match.group(1))
        _validate_allowed_url(pdf_url)
        return pdf_url

    raise RuntimeError(f"No PDF link found on {source_url}")


def download_pdf(pdf_url: str, destination: Path, pacer: RequestPacer) -> None:
    response = _request(pdf_url, pacer, stream=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                handle.write(chunk)


def get_pdf_page_count(pdf_path: Path) -> int:
    result = subprocess.run(
        ["pdfinfo", str(pdf_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pdfinfo failed for {pdf_path}: {result.stderr.strip()}")
    match = re.search(r"^Pages:\s+(\d+)$", result.stdout, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Could not determine page count for {pdf_path}")
    return int(match.group(1))


def _run_pdftotext(pdf_path: Path) -> str | None:
    pdftotext_bin = shutil.which("pdftotext")
    if not pdftotext_bin:
        return None
    result = subprocess.run(
        [pdftotext_bin, "-layout", str(pdf_path), "-"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="replace")


def _run_pypdf(pdf_path: Path) -> str | None:
    if importlib.util.find_spec("pypdf") is None:
        return None
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\f".join(pages)


def _run_pdfminer(pdf_path: Path) -> str | None:
    if importlib.util.find_spec("pdfminer.high_level") is None:
        return None
    from pdfminer.high_level import extract_text

    return extract_text(str(pdf_path))


def extract_text_layer_pages(pdf_path: Path, spec: SourceSpec, pdf_url: str) -> list[PageText]:
    """Extract pages from an existing PDF text layer."""

    total_pages = get_pdf_page_count(pdf_path)
    raw_text = _run_pdftotext(pdf_path)
    if raw_text is None:
        raw_text = _run_pypdf(pdf_path)
    if raw_text is None:
        raw_text = _run_pdfminer(pdf_path)
    if raw_text is None:
        return []

    raw_pages = raw_text.split("\f")
    if len(raw_pages) < total_pages:
        raw_pages.extend([""] * (total_pages - len(raw_pages)))
    raw_pages = raw_pages[:total_pages]

    return [
        PageText(
            page=index + 1,
            volume=spec.volume,
            author=spec.author,
            year=spec.year,
            work_title=spec.work,
            source_url=f"{pdf_url}#page={index + 1}",
            text=normalize_page_text(raw_page),
        )
        for index, raw_page in enumerate(raw_pages)
    ]


def text_layer_is_substantial(pages: list[PageText], total_pages: int) -> tuple[bool, float]:
    total_cyrillic = sum(len(_CYRILLIC_RE.findall(page.text)) for page in pages)
    avg_per_page = total_cyrillic / max(total_pages, 1)
    return avg_per_page > TEXT_LAYER_MIN_CYRILLIC_PER_PAGE, avg_per_page


def ensure_tesseract_available() -> None:
    if not shutil.which("tesseract"):
        raise RuntimeError(
            "OCR required but `tesseract` is not installed. "
            "Install `tesseract` + Ukrainian language data (`tesseract-uk`)."
        )
    result = subprocess.run(
        ["tesseract", "--list-langs"],
        capture_output=True,
        text=True,
        check=False,
    )
    langs = set(result.stdout.splitlines()[1:]) if result.returncode == 0 else set()
    missing = {"ukr", "rus"} - langs
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise RuntimeError(
            f"OCR required but Tesseract language data is missing: {missing_list}. "
            "Install `tesseract-uk` and Russian language data."
        )


def render_page_image(pdf_path: Path, page_num: int, output_prefix: Path) -> Path:
    result = subprocess.run(
        [
            "pdftoppm",
            "-f",
            str(page_num),
            "-l",
            str(page_num),
            "-r",
            str(OCR_DPI),
            "-gray",
            "-png",
            "-singlefile",
            str(pdf_path),
            str(output_prefix),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"pdftoppm failed for page {page_num} of {pdf_path}: {result.stderr.strip()}"
        )
    image_path = output_prefix.with_suffix(".png")
    if not image_path.exists():
        raise RuntimeError(f"pdftoppm did not produce expected image: {image_path}")
    return image_path


def ocr_image(image_path: Path) -> str:
    result = subprocess.run(
        ["tesseract", str(image_path), "stdout", "-l", OCR_LANG, "--psm", "6", "quiet"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"tesseract failed for {image_path}: {result.stderr.decode('utf-8', 'replace')}")
    return result.stdout.decode("utf-8", errors="replace")


def ocr_pdf_pages(pdf_path: Path, spec: SourceSpec, pdf_url: str) -> list[PageText]:
    ensure_tesseract_available()
    total_pages = get_pdf_page_count(pdf_path)
    pages: list[PageText] = []

    with tempfile.TemporaryDirectory(prefix="diasporiana-ocr-") as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        for page_num in range(1, total_pages + 1):
            print(f"  [ocr] page {page_num}/{total_pages}")
            prefix = tmpdir / f"page-{page_num:04d}"
            image_path = render_page_image(pdf_path, page_num, prefix)
            raw_text = ocr_image(image_path)
            image_path.unlink(missing_ok=True)
            pages.append(
                PageText(
                    page=page_num,
                    volume=spec.volume,
                    author=spec.author,
                    year=spec.year,
                    work_title=spec.work,
                    source_url=f"{pdf_url}#page={page_num}",
                    text=normalize_page_text(raw_text),
                )
            )

    return pages


def normalize_page_text(raw_text: str) -> str:
    """Collapse OCR / layout line breaks into paragraph text."""

    text = raw_text.replace("\r\n", "\n").replace("\r", "\n").replace("\x0c", "")
    text = text.replace("\u00ad", "")
    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in text.splitlines()]

    paragraphs: list[str] = []
    current: list[str] = []

    def flush() -> None:
        if not current:
            return
        merged = current[0]
        for line in current[1:]:
            if merged.endswith("-"):
                merged = merged[:-1] + line
            else:
                merged += " " + line
        merged = re.sub(r"\s+", " ", merged).strip()
        if merged:
            paragraphs.append(merged)
        current.clear()

    for line in lines:
        if not line:
            flush()
            continue
        if _PAGE_NUMBER_RE.match(line):
            flush()
            continue
        current.append(line)
    flush()
    return "\n\n".join(paragraphs).strip()


def chunk_pages(
    pages: list[PageText],
    spec: SourceSpec,
    *,
    cyrillic_min: float = _DEFAULT_CYRILLIC_MIN,
) -> list[dict]:
    """Chunk page text at paragraph boundaries using the shared token cap."""

    chunks: list[dict] = []
    current_text = ""
    current_source_url = ""
    chunk_idx = 0
    dropped = 0
    chunk_prefix = hashlib.md5(spec.slug.encode(), usedforsecurity=False).hexdigest()[:8]

    def flush() -> None:
        nonlocal current_text, current_source_url, chunk_idx, dropped
        text = current_text.strip()
        if not text:
            return
        ratio = _cyrillic_ratio(text)
        if ratio < cyrillic_min:
            dropped += 1
            current_text = ""
            current_source_url = ""
            return
        chunks.append(
            {
                "chunk_id": f"{chunk_prefix}_c{chunk_idx:04d}",
                "text": text,
                "source_url": current_source_url,
                "token_count": len(text) // 4,
                "work": spec.work,
                "author": spec.author,
                "year": spec.year,
                "genre": spec.genre,
                "language_period": spec.language_period,
            }
        )
        chunk_idx += 1
        current_text = ""
        current_source_url = ""

    for page in pages:
        if not page.text:
            continue
        paragraphs = [part.strip() for part in page.text.split("\n\n") if part.strip()]
        for para in paragraphs:
            if len(para) // 4 > CHUNK_MAX_TOKENS:
                if current_text:
                    flush()
                sentences = re.split(r"(?<=[.!?])\s+", para)
                for sentence in sentences:
                    if not sentence:
                        continue
                    if not current_source_url:
                        current_source_url = page.source_url
                    if len(current_text) // 4 + len(sentence) // 4 > CHUNK_MAX_TOKENS and current_text:
                        flush()
                        current_source_url = page.source_url
                    current_text += sentence.strip() + " "
                continue

            if not current_source_url:
                current_source_url = page.source_url
            if len(current_text) // 4 + len(para) // 4 > CHUNK_MAX_TOKENS and current_text:
                flush()
                current_source_url = page.source_url
            current_text += para + "\n\n"

    flush()
    if dropped:
        print(f"  [filter] dropped {dropped} low-Cyrillic chunks")
    return chunks


def write_jsonl(chunks: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def scrape_spec(spec: SourceSpec, output_path: Path, pacer: RequestPacer) -> int:
    print(f"[diasporiana] {spec.work}")
    pdf_url = resolve_pdf_url(spec.url, pacer)
    print(f"  [pdf] {pdf_url}")

    with tempfile.TemporaryDirectory(prefix="diasporiana-pdf-") as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        pdf_path = tmpdir / f"{spec.slug}.pdf"
        download_pdf(pdf_url, pdf_path, pacer)

        total_pages = get_pdf_page_count(pdf_path)
        print(f"  [pdf] downloaded {total_pages} pages")

        text_pages = extract_text_layer_pages(pdf_path, spec, pdf_url)
        substantial, avg_cyr = text_layer_is_substantial(text_pages, total_pages)
        if substantial:
            extraction_method = "text-layer"
            pages = text_pages
            print(f"  [probe] text layer accepted ({avg_cyr:.1f} Cyrillic chars/page avg)")
        else:
            extraction_method = "ocr"
            print(f"  [probe] text layer rejected ({avg_cyr:.1f} Cyrillic chars/page avg)")
            pages = ocr_pdf_pages(pdf_path, spec, pdf_url)

        chunks = chunk_pages(pages, spec)
        write_jsonl(chunks, output_path)
        print(f"  [done] {len(chunks)} chunks via {extraction_method} -> {output_path}")
        return len(chunks)


def build_custom_spec(args: argparse.Namespace) -> SourceSpec:
    required = {
        "slug": args.slug,
        "volume": args.volume,
        "work": args.work,
        "author": args.author,
        "year": args.year,
    }
    missing = [name for name, value in required.items() if value in (None, "")]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"--url requires: {joined}")
    return SourceSpec(
        slug=args.slug,
        volume=args.volume,
        url=args.url,
        work=args.work,
        author=args.author,
        year=args.year,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape Diasporiana PDF sources")
    parser.add_argument("--vol", action="append", type=int, choices=sorted(PRESET_VOLUMES))
    parser.add_argument("--url", help="Custom Diasporiana / elib work URL or direct PDF URL")
    parser.add_argument("--slug", help="Slug for custom URL mode")
    parser.add_argument("--volume", type=int, help="Volume number for custom URL mode")
    parser.add_argument("--work", help="Work title for custom URL mode")
    parser.add_argument("--author", help="Author label for custom URL mode")
    parser.add_argument("--year", type=int, help="Publication year for custom URL mode")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file path; valid only when scraping one spec",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing JSONL")
    return parser.parse_args(argv)


def resolve_specs(args: argparse.Namespace) -> list[SourceSpec]:
    specs: list[SourceSpec] = []
    if args.url:
        specs.append(build_custom_spec(args))
    if args.vol:
        specs.extend(PRESET_VOLUMES[volume] for volume in args.vol)
    if not specs:
        specs = [PRESET_VOLUMES[1], PRESET_VOLUMES[2]]
    return specs


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    specs = resolve_specs(args)
    if args.output and len(specs) != 1:
        raise SystemExit("--output can only be used when scraping exactly one source")

    pacer = RequestPacer()
    total_chunks = 0
    for spec in specs:
        output_path = args.output or (LITERARY_DIR / spec.output_name)
        if output_path.exists() and not args.force:
            print(f"[skip] {output_path} already exists; use --force to overwrite")
            continue
        try:
            total_chunks += scrape_spec(spec, output_path, pacer)
        except RuntimeError as exc:
            print(f"[error] {exc}", file=sys.stderr)
            return 1

    print(f"[diasporiana] total new chunks: {total_chunks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
