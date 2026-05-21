#!/usr/bin/env python3
"""Stream ЕСУМ ABBYY FineReader XML into JSONL entries.

Source format: ABBYY FineReader XML, FineReader10-schema-v1
(`https://support.abbyy.com/hc/en-us/articles/360017269940`). Internet
Archive provides this structured OCR for ЕСУМ volumes 1, 2, 3, and 6 as
`*_abbyy.gz`.

Entry-boundary heuristic:
- A dictionary entry starts at a `<par>` with a positive ABBYY
  `startIndent` and a plausible headword before `,`, `;`, `(`, `—`, or
  `«`. Example: vol. 1 p. 37 has `а1 (сполучник...)`, with `startIndent`
  1900 and a bold leading `а`.
- Continuation paragraphs have no `startIndent` and are appended to the
  active entry, including ABBYY overflow links across columns/pages. Example:
  `а-, ан- ...` starts at the bottom of p. 37 and continues in the next
  column with a paragraph marked `hasOverflowedHead`.
- Page running headers and footers are ignored by coordinates and shape.
  Example: p. 38 begins with header blocks `абе` and `абревіатура`, then the
  real entries `[абе]`, `абетка`, and `абзац` appear as indented paragraphs.

Page tracking uses the 1-based `<page>` index, not the printed footer. In the
IA ABBYY files, the page index matches the printed dictionary page for the
body, and the index is less fragile than OCRing footer text.

The output schema intentionally matches `data/processed/esum_vol*.jsonl`:
`lemma`, `vol`, `page`, `etymology_text`, and `cognates`.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from lxml import etree

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.ingest.esum_ingest import (
    HEAD_END_RE,
    LEADING_LANGUAGE_ABBREVIATIONS,
    PAGE_RE,
    SPACE_RE,
    SPACED_WORD_SPLIT_RE,
    WORD_SPLIT_RE,
    _extract_cognate_markers,
    _looks_like_ocr_garbage,
)

REPO = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO / "data" / "raw" / "esum" / "ia-abbyy-xml" / "vol1-abbyy.xml"
DEFAULT_OUTPUT = REPO / "data" / "processed" / "esum_vol1_abbyy.jsonl"

ABBYY_NS = "http://www.abbyy.com/FineReader_xml/FineReader10-schema-v1.xml"
NS = f"{{{ABBYY_NS}}}"

CYRILLIC_RE = r"А-ЯҐІЇЄа-яґіїє"
HOMONYM_DIGIT_RE = re.compile(rf"(?<=[{CYRILLIC_RE}])\s*\d+$")
ENTRY_PUNCT_RE = re.compile(r"[;—]")
BODY_START_RE_BY_VOL = {
    1: re.compile(r"^а\s*1\s*\(", re.IGNORECASE),
    2: re.compile(r"^да\s*1\s*[«(]", re.IGNORECASE),
    3: re.compile(r"^кора[,;(—«]", re.IGNORECASE),
    6: re.compile(r"^у\s*1\s*\(", re.IGNORECASE),
}
BODY_END_PREFIXES = (
    "ЗТИМОЛОГИЧЕСКИЙ",
    "ЗТИМОЛОГИЧЕСКИЙ СЛОВАРЬ",
    "ЭТИМОЛОГИЧЕСКИЙ",
    "ЭТИМОЛОГИЧЕСКИЙ СЛОВАРЬ",
    "АКАДЕМІЯ НАУК УКРАЇНСЬКОЇ",
    "АКАДЕМИЯ НАУК УКРАИНСКОЙ",
    "ПОМІЧЕНІ ПОМИЛКИ",
    "ПОМИЛКИ",
)

MIN_ENTRY_START_INDENT = 900
MIN_VISUAL_ENTRY_INDENT = 120
HEADER_FOOTER_MAX_HEIGHT = 360
HEADER_FOOTER_EDGE_BAND = 900


@dataclass(frozen=True)
class AbbyyTextRun:
    text: str
    bold: bool
    italic: bool


@dataclass(frozen=True)
class AbbyyLine:
    text: str
    runs: tuple[AbbyyTextRun, ...]
    left: int
    top: int
    right: int
    bottom: int


@dataclass(frozen=True)
class AbbyyParagraph:
    page: int
    text: str
    lines: tuple[AbbyyLine, ...]
    start_indent: int
    has_overflowed_head: bool
    block_left: int
    block_top: int
    block_right: int
    block_bottom: int


def _tag(name: str) -> str:
    return f"{NS}{name}"


def _int_attr(element: etree._Element, name: str, default: int = 0) -> int:
    raw = element.attrib.get(name)
    if raw is None:
        return default
    try:
        return int(float(raw))
    except ValueError:
        return default


def _text_from_chars(element: etree._Element) -> str:
    return "".join(char.text or "" for char in element.findall(f".//{_tag('charParams')}"))


def _line_from_element(line: etree._Element) -> AbbyyLine:
    runs: list[AbbyyTextRun] = []
    for formatting in line.findall(_tag("formatting")):
        text = _text_from_chars(formatting)
        if not text:
            continue
        runs.append(
            AbbyyTextRun(
                text=text,
                bold=formatting.attrib.get("bold") == "1",
                italic=formatting.attrib.get("italic") == "1",
            )
        )

    if not runs:
        text = _text_from_chars(line)
        if text:
            runs.append(AbbyyTextRun(text=text, bold=False, italic=False))

    return AbbyyLine(
        text="".join(run.text for run in runs),
        runs=tuple(runs),
        left=_int_attr(line, "l"),
        top=_int_attr(line, "t"),
        right=_int_attr(line, "r"),
        bottom=_int_attr(line, "b"),
    )


def _join_lines(lines: Iterable[AbbyyLine]) -> str:
    parts: list[str] = []
    for line in lines:
        text = SPACE_RE.sub(" ", line.text).strip()
        if not text:
            continue
        if not parts:
            parts.append(text)
            continue
        previous = parts[-1]
        if WORD_SPLIT_RE.search(previous) or SPACED_WORD_SPLIT_RE.search(previous):
            parts[-1] = SPACED_WORD_SPLIT_RE.sub("", WORD_SPLIT_RE.sub("", previous)) + text
        else:
            parts.append(text)
    return SPACE_RE.sub(" ", " ".join(parts)).strip()


def _paragraph_from_element(
    par: etree._Element,
    block: etree._Element,
    page: int,
) -> AbbyyParagraph | None:
    lines = tuple(_line_from_element(line) for line in par.findall(_tag("line")))
    text = _join_lines(lines)
    if not text:
        return None
    return AbbyyParagraph(
        page=page,
        text=text,
        lines=lines,
        start_indent=_int_attr(par, "startIndent"),
        has_overflowed_head=par.attrib.get("hasOverflowedHead") == "1",
        block_left=_int_attr(block, "l"),
        block_top=_int_attr(block, "t"),
        block_right=_int_attr(block, "r"),
        block_bottom=_int_attr(block, "b"),
    )


@contextmanager
def _open_xml(path: Path) -> Iterator[BinaryIO]:
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as fh:
            yield fh
    else:
        with path.open("rb") as fh:
            yield fh


def iter_abbyy_paragraphs(path: Path) -> Iterator[AbbyyParagraph]:
    """Yield text paragraphs from ABBYY XML without loading the full file."""
    with _open_xml(path) as fh:
        context = etree.iterparse(
            fh,
            events=("end",),
            tag=_tag("page"),
            huge_tree=True,
            recover=True,
        )
        for page, (_, page_element) in enumerate(context, start=1):
            for block in page_element.findall(_tag("block")):
                if block.attrib.get("blockType") != "Text":
                    continue
                for par in block.findall(f".//{_tag('par')}"):
                    paragraph = _paragraph_from_element(par, block, page)
                    if paragraph is not None:
                        yield paragraph
            page_element.clear()
            while page_element.getprevious() is not None:
                del page_element.getparent()[0]


def _canonical_abbyy_lemma(head: str) -> str:
    first = head.split(",", 1)[0].strip()
    words = first.split()
    if words:
        first = words[0]
    first = first.strip("[](){}•*| ")
    first = HOMONYM_DIGIT_RE.sub("", first)
    first = first.strip("[](){}•*| ")
    return SPACE_RE.sub(" ", first).strip().lower()


def _head_end_match(paragraph: str) -> re.Match[str] | None:
    stripped = paragraph.lstrip()
    offset = len(paragraph) - len(stripped)
    start = offset + 1 if stripped.startswith(("(", "{")) else offset
    return HEAD_END_RE.search(paragraph, start)


def _extract_abbyy_headword(paragraph: str) -> str | None:
    match = _head_end_match(paragraph)
    if not match:
        return None
    head = paragraph[: match.start()].strip()
    if not 1 <= len(head) <= 100:
        return None
    lemma = _canonical_abbyy_lemma(head)
    if not lemma:
        return None
    if "«" in head or "»" in head:
        return None
    if any(lemma.startswith(prefix) for prefix in LEADING_LANGUAGE_ABBREVIATIONS):
        return None
    if len(lemma.split()) > 4:
        return None
    if not re.match(rf"^[\[\(]?[{CYRILLIC_RE}]", lemma):
        return None
    if _looks_like_ocr_garbage(lemma):
        return None
    return lemma


def _is_header_or_footer(paragraph: AbbyyParagraph) -> bool:
    text = paragraph.text
    if PAGE_RE.match(text):
        page = int(text)
        return 1 <= page <= 700
    height = paragraph.block_bottom - paragraph.block_top
    near_top = paragraph.block_bottom < HEADER_FOOTER_EDGE_BAND
    near_bottom = paragraph.block_top > 6000
    if height <= HEADER_FOOTER_MAX_HEIGHT and (near_top or near_bottom):
        return not ENTRY_PUNCT_RE.search(text)
    return False


def _leading_headword_is_styled(paragraph: AbbyyParagraph) -> bool:
    if not paragraph.lines:
        return False
    for run in paragraph.lines[0].runs:
        if not run.text.strip():
            continue
        return run.bold or run.italic
    return False


def _visual_start_indent(paragraph: AbbyyParagraph) -> int:
    if not paragraph.lines:
        return 0
    return max(0, paragraph.lines[0].left - paragraph.block_left)


def _is_entry_start_paragraph(paragraph: AbbyyParagraph) -> bool:
    if paragraph.has_overflowed_head:
        return False
    if _is_header_or_footer(paragraph):
        return False
    has_entry_indent = (
        paragraph.start_indent >= MIN_ENTRY_START_INDENT
        or _visual_start_indent(paragraph) >= MIN_VISUAL_ENTRY_INDENT
        or _leading_headword_is_styled(paragraph)
    )
    if not has_entry_indent:
        return False
    return _extract_abbyy_headword(paragraph.text) is not None


def _looks_like_complete_abbyy_entry(text: str) -> bool:
    if ENTRY_PUNCT_RE.search(text) is None:
        return False
    if _extract_abbyy_headword(text) is None:
        return False
    return len(text) >= 20 or "див." in text


def _is_body_start(paragraph: AbbyyParagraph, vol: int) -> bool:
    pattern = BODY_START_RE_BY_VOL.get(vol)
    return pattern is not None and pattern.match(paragraph.text) is not None


def _is_body_end(paragraph: AbbyyParagraph) -> bool:
    text = paragraph.text.strip().upper()
    return any(text.startswith(prefix) for prefix in BODY_END_PREFIXES)


def parse_abbyy_xml(path: Path, vol: int) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    current_page = 0
    current_parts: list[str] = []
    body_started = vol not in BODY_START_RE_BY_VOL

    def flush_current() -> None:
        nonlocal current_parts, current_page
        if not current_parts:
            return
        text = SPACE_RE.sub(" ", " ".join(current_parts)).strip()
        current_parts = []
        if not _looks_like_complete_abbyy_entry(text):
            return
        lemma = _extract_abbyy_headword(text)
        if lemma is None:
            return
        entries.append(
            {
                "lemma": lemma,
                "vol": vol,
                "page": current_page,
                "etymology_text": text,
                "cognates": _extract_cognate_markers(text),
            }
        )

    for paragraph in iter_abbyy_paragraphs(path):
        if not body_started:
            if _is_header_or_footer(paragraph):
                continue
            if not _is_body_start(paragraph, vol):
                continue
            body_started = True
        if _is_body_end(paragraph):
            flush_current()
            break
        if _is_header_or_footer(paragraph):
            continue
        if _is_entry_start_paragraph(paragraph):
            flush_current()
            current_page = paragraph.page
            current_parts = [paragraph.text]
        elif current_parts:
            current_parts.append(paragraph.text)

    flush_current()
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
            "Parse ЕСУМ ABBYY FineReader XML into one JSONL record per etymology entry. "
            "Use this for IA ABBYY XML volumes 1, 2, 3, and 6."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/ingest/esum_abbyy_parser.py --input data/raw/esum/ia-abbyy-xml/vol1-abbyy.xml --output /tmp/esum_vol1_abbyy.jsonl --vol 1
  .venv/bin/python scripts/ingest/esum_abbyy_parser.py --input data/raw/esum/ia-abbyy-xml/vol1-abbyy.gz --output /tmp/esum_vol1_abbyy.jsonl --vol 1

Outputs:
  Writes JSONL with lemma, volume, page, etymology_text, and cognate marker fields.

Exit codes:
  0 on successful parse with at least one entry; >=1 on missing input, parse failure, or write failure.

Related:
  GitHub issue #2175; load output with scripts/ingest/esum_load.py after parser validation.
""",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Path to ЕСУМ ABBYY XML or .gz input. Default: {DEFAULT_INPUT}",
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
    entries = parse_abbyy_xml(args.input, args.vol)
    if not entries:
        print("No ЕСУМ entries parsed; inspect ABBYY XML and segmentation rules.", file=sys.stderr)
        return 1
    count = write_jsonl(entries, args.output)
    print(f"Parsed {count:,} ЕСУМ vol {args.vol} entries -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
