#!/usr/bin/env python3
"""Ingest ЕСУМ OCR text into JSONL entries.

OCR inspection notes for ЕСУМ volume 1 (`archive.org/details/etslukrmov1`):
- The requested `/stream/..._djvu.txt` URL can return an Archive.org HTML
  wrapper with the plain OCR inside `<pre>`; the raw file is available from
  `/download/etslukrmov1/tom 1 (А - Г)_djvu.txt`.
- The text includes title pages, foreword, abbreviation bibliography, the
  А-Г dictionary body, a Russian summary, colophon, and errata. The first real
  entry begins with `а 1 (` after the bibliography; the dictionary body ends
  before `АКАДЕМИЯ НАУК УКРАИНСКОЙ ССР`.
- Line-break hyphenation is common. The OCR uses both the not-sign glyph `¬`
  and occasional trailing hyphens for split words; these are joined during
  cleanup.
- Page artifacts are standalone page numbers plus repeated two-column page
  headers. Standalone page numbers are stripped while preserving the current
  page for subsequent entries. Header fragments are filtered by requiring entry
  paragraphs to contain dictionary punctuation and enough body text.
- Footnote-like artifacts and homonym markers appear as inline digits. Homonym
  markers in headwords are preserved in the entry body but stripped from the
  normalized `lemma` value.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO / "data" / "raw" / "esum" / "vol1.txt"
DEFAULT_OUTPUT = REPO / "data" / "processed" / "esum_vol1.jsonl"

BODY_START_RE = re.compile(r"^а\s*1\s*\(")
BODY_END_RE = re.compile(r"^АКАДЕМИЯ НАУК УКРАИНСКОЙ ССР$")
PAGE_RE = re.compile(r"^\d{1,3}$")
WORD_SPLIT_RE = re.compile(r"(?<=[А-Яа-яІіЇїЄєҐґA-Za-z])[-¬]\s*$")
SPACED_WORD_SPLIT_RE = re.compile(r"(?<=[А-Яа-яІіЇїЄєҐґA-Za-z])\s+[-¬]\s*$")
SPACE_RE = re.compile(r"[ \t]+")
ENTRY_PUNCT_RE = re.compile(r"[;—]")
HEAD_END_RE = re.compile(r"[,;(—«]")
LANG_MARKERS = (
    "псл.",
    "іє.",
    "дінд.",
    "ав.",
    "лит.",
    "лтс.",
    "прус.",
    "гр.",
    "лат.",
    "гот.",
    "двн.",
    "стел.",
    "др.",
    "р.",
    "бр.",
    "п.",
    "ч.",
    "слц.",
    "болг.",
    "схв.",
    "слн.",
    "тюрк.",
    "тур.",
    "тат.",
    "перс.",
)
LEADING_LANGUAGE_ABBREVIATIONS = {
    "р.",
    "бр.",
    "др.",
    "п.",
    "ч.",
    "слц.",
    "болг.",
    "м.",
    "схв.",
    "слн.",
    "стел.",
    "гр.",
    "лат.",
    "лит.",
    "тюрк.",
}


def _extract_pre_if_html(text: str) -> str:
    """Return `<pre>` content when Archive.org serves an HTML wrapper."""
    if "<pre" not in text[:10_000].lower():
        return text
    match = re.search(r"<pre[^>]*>(.*?)</pre>", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return text
    return html.unescape(match.group(1))


def _strip_front_and_back_matter(lines: list[str]) -> list[str]:
    start = 0
    for index, line in enumerate(lines):
        if index > 3_000 and BODY_START_RE.match(line.strip()):
            start = index
            break
    end = len(lines)
    for index in range(start, len(lines)):
        if BODY_END_RE.match(lines[index].strip()):
            end = index
            break
    return lines[start:end]


def _clean_lines(lines: Iterable[str]) -> list[tuple[int | None, str]]:
    cleaned: list[tuple[int | None, str]] = []
    current_page: int | None = 37
    carry = ""

    for raw_line in lines:
        line = SPACE_RE.sub(" ", raw_line.rstrip()).strip()
        if PAGE_RE.match(line):
            page = int(line)
            if 1 <= page <= 700:
                current_page = page
                continue

        if not line:
            if carry:
                cleaned.append((current_page, carry.strip()))
                carry = ""
            cleaned.append((current_page, ""))
            continue

        if carry:
            if WORD_SPLIT_RE.search(carry) or SPACED_WORD_SPLIT_RE.search(carry):
                carry = SPACED_WORD_SPLIT_RE.sub("", WORD_SPLIT_RE.sub("", carry)) + line
            else:
                carry = f"{carry} {line}"
        else:
            carry = line

        if not WORD_SPLIT_RE.search(carry):
            cleaned.append((current_page, carry.strip()))
            carry = ""

    if carry:
        cleaned.append((current_page, carry.strip()))
    return cleaned


def _paragraphs(cleaned_lines: Iterable[tuple[int | None, str]]) -> list[tuple[int, str]]:
    paragraphs: list[tuple[int, str]] = []
    parts: list[str] = []
    page: int | None = None

    def flush() -> None:
        nonlocal parts, page
        if parts:
            text = SPACE_RE.sub(" ", " ".join(parts)).strip()
            if text:
                paragraphs.append((page or 0, text))
        parts = []
        page = None

    for line_page, line in cleaned_lines:
        if not line:
            flush()
            continue
        if page is None and line_page is not None:
            page = line_page
        parts.append(line)
    flush()
    return paragraphs


def _canonical_lemma(head: str) -> str:
    first = head.split(",", 1)[0].strip()
    first = first.strip("[]() ")
    first = re.sub(r"\s+[0-9]+$", "", first)
    return SPACE_RE.sub(" ", first).strip().lower()


def _extract_headword(paragraph: str) -> str | None:
    match = HEAD_END_RE.search(paragraph)
    if not match:
        return None
    head = paragraph[: match.start()].strip()
    if not 1 <= len(head) <= 80:
        return None
    lemma = _canonical_lemma(head)
    if not lemma:
        return None
    if "«" in head or "»" in head:
        return None
    if any(lemma.startswith(prefix) for prefix in LEADING_LANGUAGE_ABBREVIATIONS):
        return None
    if len(lemma.split()) > 4:
        return None
    if not re.match(r"^[\[\(]?[абвгґАБВГҐ]", lemma):
        return None
    return lemma


def _looks_like_entry_start(paragraph: str) -> bool:
    if len(paragraph) < 20:
        return False
    if not ENTRY_PUNCT_RE.search(paragraph):
        return False
    return _extract_headword(paragraph) is not None


def _looks_like_cross_reference_entry(paragraph: str) -> bool:
    return (
        "див." in paragraph
        and ENTRY_PUNCT_RE.search(paragraph) is not None
        and _extract_headword(paragraph) is not None
    )


def _looks_like_head_candidate(line: str) -> bool:
    if _is_page_header_fragment(line):
        return False
    head = re.split(r"[,;(—]", line, maxsplit=1)[0].strip()
    lemma = _canonical_lemma(head)
    if not lemma or len(lemma.split()) > 4:
        return False
    if any(lemma.startswith(prefix) for prefix in LEADING_LANGUAGE_ABBREVIATIONS):
        return False
    return bool(re.match(r"^[\[\(]?[абвгґАБВГҐ]", lemma))


def _looks_like_complete_entry(paragraph: str) -> bool:
    if len(paragraph) >= 80:
        return _looks_like_entry_start(paragraph)
    return _looks_like_cross_reference_entry(paragraph)


def _is_page_header_fragment(paragraph: str) -> bool:
    if len(paragraph) > 40:
        return False
    if ENTRY_PUNCT_RE.search(paragraph):
        return False
    if paragraph.lower().startswith(("ще ", "див. ", "пор. ")):
        return False
    if "," in paragraph or "." in paragraph:
        return False
    return bool(re.match(r"^[\[А-Яа-яІіЇїЄєҐґ'’0-9., ]+$", paragraph))


def _extract_cognate_markers(text: str) -> list[str]:
    found = [marker for marker in LANG_MARKERS if marker in text]
    return sorted(set(found), key=found.index)


def parse_esum(text: str, vol: int) -> list[dict[str, object]]:
    text = _extract_pre_if_html(text)
    lines = _strip_front_and_back_matter(text.splitlines())
    cleaned_lines = _clean_lines(lines)

    merged: list[tuple[int, str]] = []
    current_page = 37
    current_parts: list[str] = []
    after_blank = True

    def flush_current() -> None:
        nonlocal current_parts
        if current_parts:
            merged.append((current_page, SPACE_RE.sub(" ", " ".join(current_parts)).strip()))
        current_parts = []

    for page, line in cleaned_lines:
        if not line:
            after_blank = True
            continue
        if after_blank and (
            _looks_like_entry_start(line)
            or _looks_like_cross_reference_entry(line)
            or _looks_like_head_candidate(line)
        ):
            flush_current()
            current_page = page or current_page
            current_parts = [line]
        elif current_parts and not _is_page_header_fragment(line):
            current_parts.append(line)
        after_blank = False
    flush_current()

    entries: list[dict[str, object]] = []
    for page, paragraph in merged:
        if not _looks_like_complete_entry(paragraph):
            continue
        lemma = _extract_headword(paragraph)
        if lemma is None:
            continue
        entries.append(
            {
                "lemma": lemma,
                "vol": vol,
                "page": page,
                "etymology_text": paragraph,
                "cognates": _extract_cognate_markers(paragraph),
            }
        )
    return entries


def write_jsonl(entries: Iterable[dict[str, object]], output: Path) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Parse ЕСУМ plain-text OCR into one JSONL record per etymology entry.\n"
            "Use this for ЕСУМ volume ingestion; do not use it for non-ЕСУМ dictionaries without reviewing segmentation."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""Examples:
  .venv/bin/python scripts/ingest/esum_ingest.py --input data/raw/esum/vol1.txt --output data/processed/esum_vol1.jsonl --vol 1
  .venv/bin/python scripts/ingest/esum_ingest.py --input {DEFAULT_INPUT} --output {DEFAULT_OUTPUT} --vol 1

Outputs:
  Writes JSONL with lemma, volume, page, etymology_text, and cognate marker fields.

Exit codes:
  0 on successful parse with at least one entry; >=1 on missing input, parse failure, or write failure.

Related:
  GitHub issue #1662; load output with scripts/ingest/esum_load.py.
""",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Path to ЕСУМ plain-text OCR input. Default: {DEFAULT_INPUT}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Path to write processed JSONL output. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--vol",
        type=int,
        required=True,
        help="ЕСУМ volume number to store in each JSONL row. Example: 1",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.input.exists():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 1
    text = args.input.read_text(encoding="utf-8")
    entries = parse_esum(text, args.vol)
    if not entries:
        print("No ЕСУМ entries parsed; inspect OCR and segmentation rules.", file=sys.stderr)
        return 1
    count = write_jsonl(entries, args.output)
    print(f"Parsed {count:,} ЕСУМ vol {args.vol} entries -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
