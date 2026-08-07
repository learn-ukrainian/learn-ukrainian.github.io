"""Extract text from PDF textbooks into structured chunks.

Extraction is hybrid and page-aware:
- Native PyMuPDF text is retained when sampled coverage and per-page text are adequate.
- Missing/unusable pages use the bundled macOS PDFKit + Vision helper in memory.

Digital classification samples twelve evenly distributed pages with an explicit
coverage predicate; final JSONL and a page-coverage receipt are atomically written.

Usage:
    .venv/bin/python scripts/rag/extract_text.py data/textbooks/grade-03/3-klas-ukrainska-mova-vashulenko-2020-1.pdf
    .venv/bin/python scripts/rag/extract_text.py --all
    .venv/bin/python scripts/rag/extract_text.py --grade 1 3
    .venv/bin/python scripts/rag/extract_text.py --output-dir /path/to/textbook_chunks \
        data/textbooks/grade-03/3-klas-ukrainska-mova-vashulenko-2020-1.pdf
    .venv/bin/python scripts/rag/extract_text.py --force-ocr data/textbooks/grade-01/1-klas-bukvar-bolshakova-2025-1.pdf
"""

import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.chunk_quality import (
    DEFAULT_SYMBOL_NOISE_THRESHOLD,
    NoiseGateStats,
    apply_symbol_noise_gate,
)
from rag.config import (
    CHUNK_MAX_TOKENS,
    CHUNK_MIN_TOKENS,
    CHUNK_OVERLAP_TOKENS,
    CHUNKS_DIR,
    MIN_CLEAN_CHAR_RATIO,
    TEXTBOOKS_DIR,
    UKRAINIAN_CHARS,
    parse_pdf_metadata,
)

# The sample is deliberately larger than the old "two readable pages" rule.
# Twelve evenly distributed pages means a long image-only book cannot be
# classified as digital because of two front-matter pages with embedded text.
DIGITAL_SAMPLE_PAGE_COUNT = 12
DIGITAL_MIN_SAMPLE_COVERAGE = 0.60
DIGITAL_MIN_READABLE_SAMPLE_PAGES = 3

# A recovered page must contain enough actual text to count as content.  The
# thresholds are intentionally explicit so a receipt can explain why a book
# was accepted or rejected; they are not a Ukrainian-language quality claim.
MIN_USABLE_PAGE_CHARS = 80
MIN_CONTENT_PAGE_CHARS = 80
# A textbook with most pages missing is not acceptable extraction coverage.
# Sixty percent still permits covers, image-only separators, and short answer
# pages while failing closed on partial-book recovery.
MIN_CONTENT_PAGE_COVERAGE = 0.60
MIN_CONTENT_PAGES = 3
# OCR confidence is recognizer-native and language-neutral.  This is an
# alternate acceptance route for legitimate Latin-script textbooks; Ukrainian
# pages can instead pass the existing 0.80 clean-character ratio.
MIN_OCR_MEAN_CONFIDENCE = 0.75

SWIFT_OCR_SCRIPT = Path(__file__).with_name("apple_vision_ocr.swift")
SWIFT_OCR_SCHEMA = "apple-vision-ocr.v1"

_TERMINAL_PUNCTUATION = frozenset(".!?…")
_FORMULA_MARKERS = frozenset("=+*/^√∑≤≥≠∞$")
_MOJIBAKE_PASSTHROUGH = frozenset(
    {
        0x00A0,  # non-breaking space
        0x00AB,
        0x00BB,  # guillemets
        0x2018,
        0x2019,
        0x201C,
        0x201D,  # smart quotes
        0x2013,
        0x2014,  # en/em dash
        0x2022,  # bullet
        0x2026,  # ellipsis
    }
)


class ExtractionError(RuntimeError):
    """Raised when a deterministic extraction step cannot complete."""


class ExtractionQualityError(ExtractionError):
    """Raised when a PDF does not meet the minimum recovered-page floor."""

    def __init__(self, message: str, *, receipt: dict):
        super().__init__(message)
        self.receipt = receipt


@dataclass(frozen=True)
class PageCoverage:
    """Sampled native-text coverage used for digital-PDF classification."""

    total_pages: int
    sampled_pages: tuple[int, ...]
    readable_pages: tuple[int, ...]

    @property
    def coverage(self) -> float:
        return len(self.readable_pages) / len(self.sampled_pages) if self.sampled_pages else 0.0

    @property
    def required_readable_pages(self) -> int:
        return min(
            len(self.sampled_pages),
            max(1, DIGITAL_MIN_READABLE_SAMPLE_PAGES),
        )

    @property
    def accepted(self) -> bool:
        return (
            len(self.readable_pages) >= self.required_readable_pages
            and self.coverage >= DIGITAL_MIN_SAMPLE_COVERAGE
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "total_pages": self.total_pages,
            "sampled_pages": list(self.sampled_pages),
            "readable_pages": list(self.readable_pages),
            "readable_page_count": len(self.readable_pages),
            "sample_coverage": round(self.coverage, 4),
            "minimum_sample_coverage": DIGITAL_MIN_SAMPLE_COVERAGE,
            "minimum_readable_sample_pages": self.required_readable_pages,
            "accepted": self.accepted,
            "predicate": (
                "readable sampled pages >= 3 (or all sampled pages for shorter PDFs) "
                "and sampled coverage >= 60%"
            ),
        }


def _sample_page_numbers(total_pages: int, sample_pages: int) -> tuple[int, ...]:
    """Return deterministic, one-based, evenly distributed sample pages."""
    if total_pages <= 0:
        return ()
    if sample_pages <= 0:
        raise ValueError("sample_pages must be positive")
    count = min(total_pages, sample_pages)
    if count == 1:
        return (1,)
    return tuple(
        sorted(
            {
                1 + round(index * (total_pages - 1) / (count - 1))
                for index in range(count)
            }
        )
    )


def _is_usable_page_text(text: str) -> bool:
    """Return whether text is substantial enough for native-page retention."""
    normalized = text.strip()
    if len(normalized) < MIN_USABLE_PAGE_CHARS:
        return False
    return sum(character.isalpha() for character in normalized) >= 10


def _is_content_page_text(text: str) -> bool:
    """Return whether text counts toward the post-extraction content floor."""
    normalized = text.strip()
    if len(normalized) < MIN_CONTENT_PAGE_CHARS:
        return False
    return sum(character.isalpha() for character in normalized) >= 10


def _page_coverage_from_texts(
    page_texts: dict[int, str],
    *,
    total_pages: int,
    sample_pages: int,
) -> PageCoverage:
    sampled = _sample_page_numbers(total_pages, sample_pages)
    readable = tuple(
        page_number
        for page_number in sampled
        if _is_usable_page_text(page_texts.get(page_number, ""))
    )
    return PageCoverage(
        total_pages=total_pages,
        sampled_pages=sampled,
        readable_pages=readable,
    )


def assess_digital_pdf(pdf_path: Path, sample_pages: int = DIGITAL_SAMPLE_PAGE_COUNT) -> PageCoverage:
    """Measure sampled native-text coverage for deterministic mode selection.

    The predicate is deliberately coverage-based: at least 60% of twelve
    evenly distributed pages (or all pages for shorter PDFs) must contain at
    least ``MIN_USABLE_PAGE_CHARS`` of selectable text, and at least three
    sampled pages must be readable for a longer PDF.  This rejects a 273-page
    scan whose first two pages happen to contain front matter text.
    """
    pages = extract_native_pages(pdf_path)
    total_pages = len(pages)
    sampled = _sample_page_numbers(total_pages, sample_pages)
    by_number = {int(page["page_number"]): str(page["text"]) for page in pages}
    page_texts = {page_number: by_number.get(page_number, "") for page_number in sampled}
    return _page_coverage_from_texts(
        page_texts,
        total_pages=total_pages,
        sample_pages=sample_pages,
    )


def is_digital_pdf(pdf_path: Path, sample_pages: int = DIGITAL_SAMPLE_PAGE_COUNT) -> bool:
    """Return whether sampled native text meets the documented coverage predicate."""
    return assess_digital_pdf(pdf_path, sample_pages=sample_pages).accepted


def _repair_cp1251_mojibake(text: str) -> str:
    """Fix CP1251-as-Latin-1 mojibake in extracted PDF text.

    Some PDFs store Ukrainian text in CP1251 encoding, but PyMuPDF reads
    it as Latin-1, producing garbled output (e.g., "Òîìì³" instead of
    "Томмі"). This function detects and repairs the encoding mismatch.

    Suspicious Latin-1 runs are considered independently. A candidate is
    accepted only when CP1251 decoding clearly increases Cyrillic content and
    removes suspicious bytes; clean Cyrillic and ordinary accented Latin words
    remain unchanged.
    """
    def suspicious(character: str) -> bool:
        code = ord(character)
        return 0x80 <= code <= 0xFF and code not in _MOJIBAKE_PASSTHROUGH

    def cyrillic_count(value: str) -> int:
        return sum("\u0400" <= character <= "\u04FF" for character in value)

    def candidate_for(run: str, start: int, end: int) -> str | None:
        if len(run) < 2:
            return None
        try:
            candidate = bytes(ord(character) for character in run).decode("cp1251")
        except (UnicodeDecodeError, ValueError):
            return None

        candidate_cyrillic = cyrillic_count(candidate)
        if candidate_cyrillic < 2:
            return None
        candidate_letters = sum(character.isalpha() for character in candidate)
        candidate_ratio = candidate_cyrillic / candidate_letters if candidate_letters else 0.0
        if candidate_ratio < 0.75:
            return None

        # A run of one or two accented Latin letters inside an ordinary word
        # is much more likely to be a genuine word (café, naïve) than broken
        # CP1251.  Isolated two-byte runs remain eligible when token-bounded;
        # longer runs must still beat the same score gate.
        left = text[start - 1] if start else ""
        right = text[end] if end < len(text) else ""
        if len(run) < 3 and (
            (left.isascii() and left.isalpha())
            or (right.isascii() and right.isalpha())
        ):
            return None

        source_cyrillic = cyrillic_count(run)
        source_letters = sum(character.isalpha() for character in run)
        source_ratio = source_cyrillic / source_letters if source_letters else 0.0
        source_suspicious = sum(suspicious(character) for character in run)
        candidate_suspicious = sum(suspicious(character) for character in candidate)
        if candidate_ratio <= source_ratio + 0.25:
            return None
        if candidate_suspicious >= source_suspicious:
            return None
        if any(character.isalpha() and not ("\u0400" <= character <= "\u04FF") for character in candidate):
            return None
        return candidate

    result: list[str] = []
    index = 0
    while index < len(text):
        if not suspicious(text[index]):
            result.append(text[index])
            index += 1
            continue
        end = index + 1
        while end < len(text) and suspicious(text[end]):
            end += 1
        run = text[index:end]
        result.append(candidate_for(run, index, end) or run)
        index = end
    return "".join(result)


_DOLLAR_HYPHEN_RE = re.compile(r"([а-яіїєґА-ЯІЇЄҐ])\$([а-яіїєґА-ЯІЇЄҐ])")


def _repair_dollar_hyphen(text: str) -> str:
    """Fix 2017-era font mapping where '$' stands in for a compound hyphen.

    Live-measured on 9-klas-khimiya-popel-2017 (#4593 wave 1): 22 intra-word
    occurrences like "фізико$хімічні"/"гідроксид$іонів" — the PDF font maps
    the discretionary/compound hyphen glyph to '$'. Only rewrites '$' BETWEEN
    Cyrillic letters, so prices and code snippets are untouched.
    """
    return _DOLLAR_HYPHEN_RE.sub(r"\1-\2", text)


def _native_page_record(page_number: int, text: str) -> dict[str, object]:
    """Build a page record from PDFKit-independent native text extraction."""
    normalized = _repair_dollar_hyphen(_repair_cp1251_mojibake(text.strip()))
    return {
        "page_number": page_number,
        "text": normalized,
        "extraction_mode": "native_text",
        "layout": {
            "line_breaks_preserved": True,
            "formula_structure": "lossy",
            "latex_preserved": False,
            "mathml_preserved": False,
            "source_order": "PyMuPDF text blocks",
        },
    }


def extract_native_pages(pdf_path: Path) -> list[dict[str, object]]:
    """Extract every PDF page natively, retaining empty/unusable page records."""
    try:
        import pymupdf
    except ModuleNotFoundError:
        return run_apple_pdfkit_native(pdf_path)

    doc = pymupdf.open(str(pdf_path))
    try:
        return [_native_page_record(i + 1, doc[i].get_text()) for i in range(len(doc))]
    finally:
        doc.close()


def run_apple_pdfkit_native(
    pdf_path: Path,
    *,
    helper_path: Path = SWIFT_OCR_SCRIPT,
) -> list[dict[str, object]]:
    """Extract all native page strings with bundled macOS PDFKit.

    This dependency-free path is used when the optional PyMuPDF package is not
    installed. It emits text only through captured JSON stdout and creates no
    page images or temporary source copies.
    """
    helper_path = Path(helper_path)
    if not helper_path.is_file():
        raise ExtractionError(f"Apple PDFKit helper missing: {helper_path}")
    command = [
        "swift",
        str(helper_path),
        "--pdf",
        str(Path(pdf_path)),
        "--pages",
        "all",
        "--mode",
        "native",
    ]
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise ExtractionError("Swift is required for the macOS PDFKit fallback") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()
        raise ExtractionError(
            f"Apple PDFKit extraction failed with exit code {exc.returncode}: "
            f"{detail or 'no diagnostic'}"
        ) from exc
    try:
        payload = json.loads(completed.stdout)
        pages = payload["pages"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ExtractionError("Apple PDFKit helper emitted invalid JSON") from exc
    if payload.get("schema_version") != SWIFT_OCR_SCHEMA or not isinstance(pages, list):
        raise ExtractionError("Apple PDFKit helper schema mismatch")
    numbers = [int(page.get("page_number", -1)) for page in pages]
    if numbers != list(range(1, len(pages) + 1)):
        raise ExtractionError("Apple PDFKit pages are not complete and ordered")
    records = []
    for page in pages:
        record = _native_page_record(int(page["page_number"]), str(page.get("text") or ""))
        record["layout"]["source_order"] = "PDFKit page.string"
        record["native_runtime"] = payload.get("metadata", {}).get("runtime", {})
        records.append(record)
    return records


def extract_text_fast(pdf_path: Path) -> str:
    """Extract native text as the legacy page-marked markdown string."""
    pages = extract_native_pages(pdf_path)
    return "\n\n".join(
        f"## Сторінка {page['page_number']}\n\n{page['text']}"
        for page in pages
        if str(page["text"]).strip()
    )


def _validate_ocr_page(page: dict, *, requested_pages: set[int]) -> dict[str, object]:
    """Validate and normalize one page from the Swift JSON contract."""
    try:
        page_number = int(page["page_number"])
        text = str(page.get("text") or "")
        observation_count = int(page.get("observation_count", 0))
        mean_confidence = float(page.get("mean_confidence", 0.0))
        line_break_count = int(page.get("line_break_count", 0) or 0)
    except (KeyError, TypeError, ValueError) as exc:
        raise ExtractionError("Apple Vision OCR returned an invalid page record") from exc
    if page_number not in requested_pages:
        raise ExtractionError(f"Apple Vision OCR returned unexpected page {page_number}")
    if observation_count < 0 or line_break_count < 0 or not 0.0 <= mean_confidence <= 1.0:
        raise ExtractionError(f"Apple Vision OCR returned invalid confidence metadata for page {page_number}")
    return {
        "page_number": page_number,
        "text": _repair_dollar_hyphen(_repair_cp1251_mojibake(text.strip())),
        "extraction_mode": "apple_vision_ocr",
        "ocr": {
            "observation_count": observation_count,
            "mean_confidence": round(mean_confidence, 6),
            "runtime": page.get("runtime", {}),
            "recognizer": page.get("recognizer", {}),
        },
        "layout": {
            "line_breaks_preserved": bool(line_break_count),
            "line_break_count": line_break_count,
            "formula_structure": "lossy",
            "latex_preserved": False,
            "mathml_preserved": False,
            "source_order": "Vision bounding-box order",
        },
    }


def run_apple_vision_ocr(
    pdf_path: Path,
    page_numbers: list[int] | tuple[int, ...],
    *,
    helper_path: Path = SWIFT_OCR_SCRIPT,
) -> list[dict[str, object]]:
    """Run the bundled, offline, one-page-at-a-time macOS OCR helper.

    The subprocess contract is one JSON object on stdout with schema
    ``apple-vision-ocr.v1`` and no diagnostic text on stdout.  The helper
    renders pages in memory, so this path does not write page images or source
    text to logs and never installs/downloads an OCR model.
    """
    requested = tuple(sorted(set(int(page) for page in page_numbers)))
    if not requested:
        return []
    if any(page <= 0 for page in requested):
        raise ValueError("page_numbers must be one-based positive integers")
    helper_path = Path(helper_path)
    if not helper_path.is_file():
        raise ExtractionError(f"Apple Vision OCR helper missing: {helper_path}")
    command = [
        "swift",
        str(helper_path),
        "--pdf",
        str(Path(pdf_path)),
        "--pages",
        ",".join(str(page) for page in requested),
        "--mode",
        "ocr",
    ]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise ExtractionError("Swift is required for the macOS Vision OCR fallback") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()
        raise ExtractionError(
            f"Apple Vision OCR failed with exit code {exc.returncode}: {detail or 'no diagnostic'}"
        ) from exc
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ExtractionError("Apple Vision OCR emitted invalid JSON on stdout") from exc
    if not isinstance(payload, dict):
        raise ExtractionError("Apple Vision OCR payload must be a JSON object")
    if payload.get("schema_version") != SWIFT_OCR_SCHEMA:
        raise ExtractionError("Apple Vision OCR schema version mismatch")
    pages = payload.get("pages")
    metadata = payload.get("metadata", {})
    if not isinstance(pages, list) or not isinstance(metadata, dict):
        raise ExtractionError("Apple Vision OCR payload must contain pages and metadata")
    try:
        page_numbers = [int(page.get("page_number", -1)) for page in pages]
    except (AttributeError, TypeError, ValueError) as exc:
        raise ExtractionError("Apple Vision OCR page numbers are invalid") from exc
    if page_numbers != list(requested):
        raise ExtractionError("Apple Vision OCR pages are not ordered or complete")
    normalized_pages = []
    for page in pages:
        normalized = _validate_ocr_page(page, requested_pages=set(requested))
        normalized["ocr"]["runtime"] = metadata.get("runtime", {})
        normalized["ocr"]["recognizer"] = metadata.get("recognizer", {})
        normalized_pages.append(normalized)
    return normalized_pages


def _content_page_requirement(total_pages: int) -> int:
    """Return the explicit minimum number of recovered content pages."""
    if total_pages <= 0:
        return 0
    return min(
        total_pages,
        max(MIN_CONTENT_PAGES, math.ceil(total_pages * MIN_CONTENT_PAGE_COVERAGE)),
    )


def _is_content_page_record(page: dict[str, object]) -> bool:
    """Return whether one recovered page is substantial and usable.

    Native text keeps the existing explicit character predicate. OCR text must
    additionally pass either the repository's Ukrainian clean-text threshold
    or a language-neutral recognizer-confidence floor. This prevents dense
    Latin-lookalike garbage from satisfying coverage merely by being long.
    """
    text = str(page.get("text") or "")
    if not _is_content_page_text(text):
        return False
    if page.get("extraction_mode") != "apple_vision_ocr":
        return True
    is_clean, _ratio = check_quality(text)
    ocr = page.get("ocr")
    mean_confidence = (
        float(ocr.get("mean_confidence", 0.0))
        if isinstance(ocr, dict)
        else 0.0
    )
    return is_clean or mean_confidence >= MIN_OCR_MEAN_CONFIDENCE


def _page_coverage_receipt(
    page_records: list[dict[str, object]],
    *,
    total_pages: int,
    digital_coverage: PageCoverage,
    ocr_requested_pages: list[int],
) -> dict[str, object]:
    content_pages = [
        int(page["page_number"])
        for page in page_records
        if _is_content_page_record(page)
    ]
    rejected_ocr_pages = [
        int(page["page_number"])
        for page in page_records
        if page.get("extraction_mode") == "apple_vision_ocr"
        and _is_content_page_text(str(page.get("text") or ""))
        and not _is_content_page_record(page)
    ]
    required_pages = _content_page_requirement(total_pages)
    coverage = len(content_pages) / total_pages if total_pages else 0.0
    receipt = {
        "schema_version": "textbook-page-coverage.v1",
        "total_pages": total_pages,
        "recovered_pages": len(page_records),
        "content_pages": content_pages,
        "content_page_count": len(content_pages),
        "content_page_coverage": round(coverage, 4),
        "minimum_content_page_coverage": MIN_CONTENT_PAGE_COVERAGE,
        "minimum_content_pages": required_pages,
        "native_pages": sum(page["extraction_mode"] == "native_text" for page in page_records),
        "ocr_requested_pages": ocr_requested_pages,
        "ocr_recovered_pages": [
            int(page["page_number"])
            for page in page_records
            if page["extraction_mode"] == "apple_vision_ocr"
        ],
        "ocr_quality_rejected_pages": rejected_ocr_pages,
        "minimum_ocr_mean_confidence": MIN_OCR_MEAN_CONFIDENCE,
        "digital_detection": digital_coverage.as_dict(),
        "status": (
            "pass"
            if len(content_pages) >= required_pages and coverage >= MIN_CONTENT_PAGE_COVERAGE
            else "fail"
        ),
        "predicate": (
            f"at least {MIN_CONTENT_PAGE_COVERAGE:.0%} of all PDF pages and "
            f"at least {MIN_CONTENT_PAGES} content pages (capped by PDF length), "
            f"where a content page has >= {MIN_CONTENT_PAGE_CHARS} characters; "
            "OCR pages additionally require the clean-text ratio or mean "
            f"confidence >= {MIN_OCR_MEAN_CONFIDENCE:.2f}"
        ),
    }
    return receipt


def extract_page_records(
    pdf_path: Path,
    *,
    force_ocr: bool = False,
    ocr_runner: Callable[[Path, list[int]], list[dict[str, object]]] | None = None,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Extract native pages and OCR only missing/unusable pages.

    Native text is retained whenever it passes the usable-page predicate.
    Other pages are handed to the Swift helper in one call; the helper itself
    processes and orders one PDF page at a time.  The returned receipt is
    fail-closed by raising ``ExtractionQualityError`` when too few content
    pages are recovered.
    """
    native_pages = extract_native_pages(pdf_path)
    total_pages = len(native_pages)
    native_texts = {
        int(page["page_number"]): str(page.get("text") or "")
        for page in native_pages
    }
    digital_coverage = _page_coverage_from_texts(
        native_texts,
        total_pages=total_pages,
        sample_pages=DIGITAL_SAMPLE_PAGE_COUNT,
    )
    if force_ocr:
        ocr_requested_pages = list(range(1, total_pages + 1))
    else:
        ocr_requested_pages = [
            int(page["page_number"])
            for page in native_pages
            if not _is_usable_page_text(str(page.get("text") or ""))
        ]

    ocr_pages: dict[int, dict[str, object]] = {}
    if ocr_requested_pages:
        runner = ocr_runner or run_apple_vision_ocr
        for page in runner(Path(pdf_path), ocr_requested_pages):
            page_number = int(page["page_number"])
            if page_number in ocr_pages:
                raise ExtractionError(f"OCR returned duplicate page {page_number}")
            ocr_pages[page_number] = page

    selected_pages: list[dict[str, object]] = []
    for native_page in native_pages:
        page_number = int(native_page["page_number"])
        native_text = str(native_page.get("text") or "")
        ocr_page = ocr_pages.get(page_number)
        if ocr_page is not None:
            ocr_text = str(ocr_page.get("text") or "")
            if force_ocr or _is_usable_page_text(ocr_text) or not _is_usable_page_text(native_text):
                selected = ocr_page
            else:
                selected = native_page
        else:
            selected = native_page
        if str(selected.get("text") or "").strip():
            selected_pages.append(selected)

    selected_pages.sort(key=lambda page: int(page["page_number"]))
    receipt = _page_coverage_receipt(
        selected_pages,
        total_pages=total_pages,
        digital_coverage=digital_coverage,
        ocr_requested_pages=ocr_requested_pages,
    )
    if receipt["status"] != "pass":
        raise ExtractionQualityError(
            "Textbook extraction failed closed: recovered content-page coverage "
            f"{receipt['content_page_coverage']:.2%} does not meet the explicit floor",
            receipt=receipt,
        )
    return selected_pages, receipt


def extract_markdown_ocr(pdf_path: Path) -> str:
    """Return the Swift Vision fallback output in the legacy markdown shape."""
    native_pages = extract_native_pages(pdf_path)
    pages = run_apple_vision_ocr(pdf_path, list(range(1, len(native_pages) + 1)))
    return "\n\n".join(
        f"## Сторінка {page['page_number']}\n\n{page['text']}"
        for page in pages
        if str(page["text"]).strip()
    )


def split_into_sections(markdown: str) -> list[dict]:
    """Split markdown into sections at H1/H2 boundaries.

    Returns list of {title, level, text, page_hint} dicts.
    """
    sections = []
    # Split on H1 or H2 headings
    pattern = r'^(#{1,2})\s+(.+)$'
    parts = re.split(pattern, markdown, flags=re.MULTILINE)

    # First part is text before any heading
    if parts[0].strip():
        sections.append({
            "title": "Вступ",
            "level": 0,
            "text": parts[0].strip(),
        })

    # Process heading + content pairs (groups of 3: marker, title, content)
    i = 1
    while i < len(parts) - 2:
        heading_marker = parts[i]
        heading_title = parts[i + 1].strip()
        content = parts[i + 2].strip() if i + 2 < len(parts) else ""

        sections.append({
            "title": heading_title,
            "level": len(heading_marker),
            "text": content,
        })
        i += 3

    return sections


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~1.5 chars per token for Ukrainian Cyrillic."""
    return max(1, len(text) // 4)


def chunk_text(text: str, section_title: str) -> list[dict]:
    """Split text into overlapping chunks respecting paragraph boundaries.

    Returns list of {text, token_count} dicts.
    """
    if not text.strip():
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks = []
    current_parts = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = estimate_tokens(para)

        # If single paragraph exceeds max, force-split it
        if para_tokens > CHUNK_MAX_TOKENS:
            # Flush current buffer first
            if current_parts:
                chunk_text_joined = "\n\n".join(current_parts)
                chunks.append({
                    "text": chunk_text_joined,
                    "token_count": estimate_tokens(chunk_text_joined),
                })
                current_parts = []
                current_tokens = 0

            # Split long paragraph by sentences
            sentences = re.split(r'(?<=[.!?])\s+', para)
            sent_buf = []
            sent_tokens = 0
            for sent in sentences:
                st = estimate_tokens(sent)
                if sent_tokens + st > CHUNK_MAX_TOKENS and sent_buf:
                    chunk_text_joined = " ".join(sent_buf)
                    chunks.append({
                        "text": chunk_text_joined,
                        "token_count": estimate_tokens(chunk_text_joined),
                    })
                    # Overlap: keep last sentence
                    sent_buf = sent_buf[-1:] if CHUNK_OVERLAP_TOKENS > 0 else []
                    sent_tokens = estimate_tokens(" ".join(sent_buf))
                sent_buf.append(sent)
                sent_tokens += st
            if sent_buf:
                chunk_text_joined = " ".join(sent_buf)
                chunks.append({
                    "text": chunk_text_joined,
                    "token_count": estimate_tokens(chunk_text_joined),
                })
            continue

        # Would adding this paragraph exceed max?
        if current_tokens + para_tokens > CHUNK_MAX_TOKENS and current_parts:
            chunk_text_joined = "\n\n".join(current_parts)
            chunks.append({
                "text": chunk_text_joined,
                "token_count": estimate_tokens(chunk_text_joined),
            })
            # Overlap: keep last paragraph
            if CHUNK_OVERLAP_TOKENS > 0 and current_parts:
                last = current_parts[-1]
                current_parts = [last]
                current_tokens = estimate_tokens(last)
            else:
                current_parts = []
                current_tokens = 0

        current_parts.append(para)
        current_tokens += para_tokens

    # Flush remaining
    if current_parts:
        chunk_text_joined = "\n\n".join(current_parts)
        tokens = estimate_tokens(chunk_text_joined)
        # Merge tiny remainder into previous chunk if possible
        if tokens < CHUNK_MIN_TOKENS and chunks:
            prev = chunks[-1]
            merged = prev["text"] + "\n\n" + chunk_text_joined
            chunks[-1] = {
                "text": merged,
                "token_count": estimate_tokens(merged),
            }
        else:
            chunks.append({
                "text": chunk_text_joined,
                "token_count": tokens,
            })

    return chunks


def check_quality(text: str) -> tuple[bool, float]:
    """Check if chunk text is clean Ukrainian.

    Returns (is_clean, ratio) where ratio is the fraction of
    recognized Ukrainian characters.
    """
    if not text:
        return False, 0.0

    clean_count = 0
    total_count = 0
    for ch in text:
        if unicodedata.category(ch).startswith("C"):  # Control chars
            continue
        total_count += 1
        if ch in UKRAINIAN_CHARS:
            clean_count += 1

    if total_count == 0:
        return False, 0.0

    ratio = clean_count / total_count
    return ratio >= MIN_CLEAN_CHAR_RATIO, ratio


def _ends_without_terminal_punctuation(text: str) -> bool:
    """Return whether a chunk ends without sentence-terminal punctuation."""
    stripped = text.rstrip()
    while stripped and stripped[-1] in ")]}>»”'":
        stripped = stripped[:-1].rstrip()
    return not stripped or stripped[-1] not in _TERMINAL_PUNCTUATION


def _starts_with_lowercase_token(text: str) -> bool:
    """Return whether the first alphabetic token starts with a lowercase letter."""
    for character in text.lstrip():
        if character.isalpha():
            return character.islower()
    return False


def _looks_like_formula(text: str) -> bool:
    """Detect math-layout chunks that must remain retrievable when flattened."""
    marker_count = sum(character in _FORMULA_MARKERS for character in text)
    digit_count = sum(character.isdigit() for character in text)
    return marker_count >= 1 and digit_count >= 1


def _mark_continuations(chunks: list[dict[str, object]]) -> None:
    """Mark only deterministic page/chunk continuation pairs, never merge them."""
    for chunk in chunks:
        chunk["continuation"] = False
        chunk["continuation_of_previous"] = False
    for current, following in pairwise(chunks):
        is_continuation = (
            _ends_without_terminal_punctuation(str(current.get("text") or ""))
            and _starts_with_lowercase_token(str(following.get("text") or ""))
        )
        if is_continuation:
            current["continuation"] = True
            following["continuation_of_previous"] = True


def _atomic_write(path: Path, payload: str) -> None:
    """Atomically replace one output file and remove temp files on every path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    """Write JSONL through the common atomic path."""
    content = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        for record in records
    )
    _atomic_write(path, content)


def process_pdf(
    pdf_path: Path,
    output_dir: Path | None = None,
    force_ocr: bool = False,
    symbol_noise_threshold: float = DEFAULT_SYMBOL_NOISE_THRESHOLD,
    ocr_runner: Callable[[Path, list[int]], list[dict[str, object]]] | None = None,
) -> dict:
    """Process one PDF into page-provenant chunks and a coverage receipt."""
    pdf_path = Path(pdf_path)
    meta = parse_pdf_metadata(pdf_path)

    if output_dir is None:
        output_dir = CHUNKS_DIR / f"grade-{meta['grade']:02d}"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{meta['pdf_stem']}.jsonl"
    receipt_file = output_dir / f"{meta['pdf_stem']}.receipt.json"

    print(f"[extract] Processing {pdf_path.name}...")
    print(f"  Metadata: grade={meta['grade']}, author={meta['author']}, "
          f"year={meta['year']}, trust_tier={meta['trust_tier']}")

    # Step 1: Native extraction plus bounded, per-page Vision fallback.
    try:
        page_records, coverage_receipt = extract_page_records(
            pdf_path,
            force_ocr=force_ocr,
            ocr_runner=ocr_runner,
        )
    except ExtractionQualityError as exc:
        # A failed quality gate leaves an auditable receipt but never a
        # partially accepted JSONL source.
        _atomic_write(
            receipt_file,
            json.dumps(
                {
                    "pdf": pdf_path.name,
                    "source_file": meta["pdf_stem"],
                    "page_coverage": exc.receipt,
                    "status": "fail",
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
        )
        raise
    mode = "apple_vision_ocr" if force_ocr else (
        "hybrid" if coverage_receipt["ocr_requested_pages"] else "native_text"
    )
    extracted_chars = sum(len(str(page["text"])) for page in page_records)
    print(f"  Mode: {mode}")
    print(f"  Extracted text: {extracted_chars} chars from {len(page_records)} pages")
    print(f"  Page coverage: {json.dumps(coverage_receipt, ensure_ascii=False, sort_keys=True)}")

    # Step 2: Chunk each recovered page independently.  This retains page
    # identity even when a long page must be split; no arbitrary page merge is
    # performed.  Section inference can later use the page title/body pair.
    raw_chunks = []
    quality_stats = {"clean": 0, "flagged": 0}

    # The coverage gate records low-confidence OCR pages for auditability, but
    # rejected OCR must never become retrieval or training chunks. Native math
    # and formula pages remain eligible even when the language cleanliness
    # heuristic flags them; the extra predicate applies only to OCR fallback.
    chunkable_pages = [
        page
        for page in page_records
        if page.get("extraction_mode") != "apple_vision_ocr"
        or _is_content_page_record(page)
    ]

    for page in chunkable_pages:
        page_number = int(page["page_number"])
        chunks = chunk_text(str(page["text"]), f"Сторінка {page_number}")
        for _i, chunk in enumerate(chunks):
            raw_chunks.append({
                "text": chunk["text"],
                "token_count": chunk["token_count"],
                "section_title": f"Сторінка {page_number}",
                "section_level": 0,
                "page_start": page_number,
                "page_end": page_number,
                "page_extraction_mode": page["extraction_mode"],
                "layout": page.get("layout", {}),
                "ocr": page.get("ocr", {}),
            })

    for order, chunk in enumerate(raw_chunks):
        chunk["_order"] = order
    formula_chunks = [chunk for chunk in raw_chunks if _looks_like_formula(chunk["text"])]
    gate_candidates = [chunk for chunk in raw_chunks if chunk not in formula_chunks]
    kept_candidates, gate_stats = apply_symbol_noise_gate(
        gate_candidates,
        source_file=meta["pdf_stem"],
        threshold=symbol_noise_threshold,
        warn=lambda message: print(f"  {message}"),
    )
    for chunk in formula_chunks:
        layout = dict(chunk.get("layout", {}))
        layout["formula_structure"] = "lossy"
        layout["formula_gate_override"] = True
        chunk["layout"] = layout
    kept_chunks = sorted(
        [*kept_candidates, *formula_chunks],
        key=lambda chunk: int(chunk["_order"]),
    )
    noise_stats = NoiseGateStats(
        source_file=gate_stats.source_file,
        chunks_kept=gate_stats.chunks_kept + len(formula_chunks),
        chunks_dropped_noise=gate_stats.chunks_dropped_noise,
    )
    print(f"  Noise gate: {json.dumps(noise_stats.manifest_record(), ensure_ascii=False)}")

    all_chunks = []
    for chunk in kept_chunks:
        is_clean, ratio = check_quality(chunk["text"])

        chunk_record = {
            "chunk_id": f"{meta['pdf_stem']}_s{len(all_chunks):04d}",
            "text": chunk["text"],
            "token_count": chunk["token_count"],
            "section_title": chunk["section_title"],
            "section_level": chunk["section_level"],
            "page_start": chunk["page_start"],
            "page_end": chunk["page_end"],
            "page_extraction_mode": chunk["page_extraction_mode"],
            "extraction_mode": chunk["page_extraction_mode"],
            "layout": chunk["layout"],
            "ocr": chunk["ocr"],
            "quality": {
                "is_clean": is_clean,
                "clean_ratio": round(ratio, 3),
            },
            **{k: v for k, v in meta.items() if k != "pdf_stem"},
            "pdf_stem": meta["pdf_stem"],
        }
        all_chunks.append(chunk_record)

        if is_clean:
            quality_stats["clean"] += 1
        else:
            quality_stats["flagged"] += 1

    _mark_continuations(all_chunks)

    if not all_chunks:
        raise ExtractionError(
            f"{pdf_path.name}: symbol-noise gate removed every recovered page chunk"
        )

    # Save chunks and the receipt through separate same-directory atomic
    # replacements.  Temporary files are cleaned even when serialization,
    # fsync, or rename fails; the final JSONL is never partially written.
    _atomic_write_jsonl(output_file, all_chunks)
    _atomic_write(
        receipt_file,
        json.dumps(
            {
                "pdf": pdf_path.name,
                "source_file": meta["pdf_stem"],
                "page_coverage": coverage_receipt,
                "chunks": len(all_chunks),
                "chunked_pages": [int(page["page_number"]) for page in chunkable_pages],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )

    summary = {
        "pdf": pdf_path.name,
        "total_chunks": len(all_chunks),
        "source_file": meta["pdf_stem"],
        "chunks_kept": noise_stats.chunks_kept,
        "chunks_dropped_noise": noise_stats.chunks_dropped_noise,
        "drop_ratio": round(noise_stats.drop_ratio, 3),
        "symbol_noise_threshold": symbol_noise_threshold,
        "clean_chunks": quality_stats["clean"],
        "flagged_chunks": quality_stats["flagged"],
        "pages_recovered": len(page_records),
        "pages_chunked": len(chunkable_pages),
        "page_coverage": coverage_receipt,
        "output_file": str(output_file),
        "receipt_file": str(receipt_file),
    }
    print(f"  Result: {summary['total_chunks']} chunks "
          f"({summary['clean_chunks']} clean, {summary['flagged_chunks']} flagged)")
    print(f"  Saved to {output_file}")

    return summary


def find_pdfs(grades: list[int] | None = None) -> list[Path]:
    """Find all PDF files, optionally filtered by grade."""
    pdfs = []
    for grade_dir in sorted(TEXTBOOKS_DIR.iterdir()):
        if not grade_dir.is_dir() or not grade_dir.name.startswith("grade-"):
            continue
        grade_num = int(grade_dir.name.split("-")[1])
        if grades and grade_num not in grades:
            continue
        for pdf in sorted(grade_dir.glob("*.pdf")):
            pdfs.append(pdf)
    return pdfs


def main():
    parser = argparse.ArgumentParser(description="Extract text from PDF textbooks")
    parser.add_argument("pdf", nargs="?", help="Path to a single PDF file")
    parser.add_argument("--all", action="store_true", help="Process all PDFs")
    parser.add_argument("--grade", type=int, nargs="+", help="Process specific grades")
    parser.add_argument("--force-ocr", action="store_true",
                        help="Force the offline macOS Vision helper for every page")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for the atomically-written JSONL and page-coverage receipt",
    )
    parser.add_argument(
        "--noise-threshold",
        type=float,
        default=DEFAULT_SYMBOL_NOISE_THRESHOLD,
        help="Drop chunks whose symbol-noise density exceeds this fraction",
    )
    args = parser.parse_args()

    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"Error: {pdf_path} not found", file=sys.stderr)
            sys.exit(1)
        summary = process_pdf(
            pdf_path,
            output_dir=args.output_dir,
            force_ocr=args.force_ocr,
            symbol_noise_threshold=args.noise_threshold,
        )
        print(f"\nDone: {json.dumps(summary, indent=2)}")

    elif args.all or args.grade:
        pdfs = find_pdfs(args.grade)
        if not pdfs:
            print("No PDFs found", file=sys.stderr)
            sys.exit(1)
        print(f"Found {len(pdfs)} PDFs to process\n")
        summaries = []
        for pdf in pdfs:
            summary = process_pdf(
                pdf,
                output_dir=args.output_dir,
                force_ocr=args.force_ocr,
                symbol_noise_threshold=args.noise_threshold,
            )
            summaries.append(summary)
            print()
        total_chunks = sum(s["total_chunks"] for s in summaries)
        total_flagged = sum(s["flagged_chunks"] for s in summaries)
        total_dropped_noise = sum(s["chunks_dropped_noise"] for s in summaries)
        print(f"=== Total: {total_chunks} chunks from {len(pdfs)} PDFs "
              f"({total_flagged} flagged, {total_dropped_noise} noise-dropped) ===")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
