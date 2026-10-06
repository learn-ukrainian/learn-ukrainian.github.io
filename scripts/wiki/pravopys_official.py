"""Official «Український правопис» (2019): PDF parsing, storage and offline lookup.

The source is the authorized edition (Наукова думка, 2019, ISBN 978-966-00-1728-3)
that the Ukrainian National Commission on Orthography designated on 12 July 2019,
as distributed by the Ministry of Education and Science (mon.gov.ua) and by the
Ukrainian Language-Information Fund (ulif.org.ua).  The choice and its evidence are
recorded in ``docs/sources/pravopys-2019-official-source.md``.

The PDF text layer mixes Unicode fonts with legacy fonts:

* fonts named ``1251…`` carry Windows-1251 bytes under a WinAnsi encoding, so the
  extracted characters are Latin-1 lookalikes («ÁÓÊÂÅÍ²» for «БУКВЕНІ»);
* fonts named ``1251TimesNew…`` hold the stressed vowels (и́, у́, я́, ю́, є́, ї́, …)
  at the Windows-1251 position of the plain vowel;
* the Unicode Times fonts write stressed а, е, і, о, у, и as the Latin letters
  á, é, í, ó, ý, ú inside Cyrillic words (also in endings set off by a hyphen);
* a few words encode a letter with its lookalike from the other script
  («Cкладені» with a Latin C, «Мicrosóft» with a Cyrillic М).

``decode_span_text`` undoes the first two encodings per span; ``restore_scripts``
undoes the other two word by word, reading hyphenated words across line breaks.
Every rule was checked against rendered glyphs of the official PDF.  Nothing here
edits the rules text: stored ``text`` is the printed text line by line, and
``text_normalized`` only joins lines and resolves line-end hyphenation.

Collection access is offline: ``scripts/ingest/pravopys_2019_ingest.py`` writes
the tables once, and readers query them read-only.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from typing import Any

from scripts.lib.readonly_sqlite import SQLiteConnection
from scripts.lib.readonly_sqlite import open_readonly as _open_readonly

PRAVOPYS_SOURCE_ID = "pravopys_2019_official"
PARSER_VERSION = "pravopys_2019_pdf_v3"
PRAVOPYS_TITLE = "Український правопис"
PRAVOPYS_EDITION = "Авторизоване видання 2019 р. — Київ: Наукова думка, 2019. 392 с. ISBN 978-966-00-1728-3"
PRAVOPYS_APPROVALS = (
    "Схвалив Кабінет Міністрів України (Постанова № 437 від 22 травня 2019 р.)",
    "Схвалили спільною постановою Президія НАН України (протокол № 22/10 від 24 жовтня 2018 р.) "
    "та рішенням Колегія МОН України (протокол № 10/4-13 від 24 жовтня 2018 р.)",
    "Затвердила Українська національна комісія з питань правопису (протокол № 5 від 22 жовтня 2018 р.)",
    "Українська національна комісія з питань правопису рішенням від 12 липня 2019 р. визначила "
    "Видавництво «Наукова думка» НАН України установою, уповноваженою випустити авторизоване видання",
)
PRAVOPYS_CITATION = "Український правопис. Київ: Наукова думка, 2019"
PRAVOPYS_CABINET_RESOLUTION_URL = "https://zakon.rada.gov.ua/laws/show/437-2019-%D0%BF"

# Number of § entries in the official table of contents (pp. 383–391).
TOC_PARAGRAPH_COUNT = 168

# Printed page numbers of the parts of the book that are parsed.
FRONT_MATTER_FIRST_PAGE = 5  # ПЕРЕДМОВА
BODY_LAST_PAGE = 256  # § 168 ends here; ПОКАЖЧИК starts on p. 257
TOC_FIRST_PAGE = 383
TOC_LAST_PAGE = 391


@dataclass(frozen=True)
class OfficialFile:
    """One byte-exact official distribution of the authorized edition."""

    sha256: str
    url: str
    distributor: str
    pdf_pages: int
    # PDF page index of printed page 1 (the MON copy has one leading blank page).
    printed_page_one_index: int


ULIF_PDF_URL = "https://www.ulif.org.ua/system/files/pravopus-new.pdf"
MON_PDF_URL = "https://mon.gov.ua/static-objects/mon/sites/1/zagalna%20serednya/Pravopys.2019/ukr.pravopys-2019.pdf"

OFFICIAL_FILES: dict[str, OfficialFile] = {
    "0d2fd75a2e9b2a412d4c8e072f6a8cac06d075a297a770fd037312054b0e501a": OfficialFile(
        sha256="0d2fd75a2e9b2a412d4c8e072f6a8cac06d075a297a770fd037312054b0e501a",
        url=ULIF_PDF_URL,
        distributor="Український мовно-інформаційний фонд НАН України (ulif.org.ua)",
        pdf_pages=392,
        printed_page_one_index=0,
    ),
    "ff7548cacc63e96420d652e068ea6e6fb5d35f983117668f2e8c94571cc1beae": OfficialFile(
        sha256="ff7548cacc63e96420d652e068ea6e6fb5d35f983117668f2e8c94571cc1beae",
        url=MON_PDF_URL,
        distributor="Міністерство освіти і науки України (mon.gov.ua)",
        pdf_pages=393,
        printed_page_one_index=1,
    ),
}


class PravopysParseError(ValueError):
    """Raised when the PDF does not yield the structure of the official edition."""


# ── Decoding ─────────────────────────────────────────────────────

ACUTE = chr(0x0301)  # combining acute (stress mark)
GRAVE = chr(0x0300)
_CYRILLIC_VOWELS = frozenset("аеєиіїоуюяАЕЄИІЇОУЮЯ")
# Latin precomposed letters that the Unicode Times fonts use for stressed Cyrillic vowels.
_LATIN_STRESSED = {
    "á": "а" + ACUTE,
    "é": "е" + ACUTE,
    "í": "і" + ACUTE,
    "ó": "о" + ACUTE,
    "ý": "у" + ACUTE,
    "ú": "и" + ACUTE,
    "Á": "А" + ACUTE,
    "É": "Е" + ACUTE,
    "Í": "І" + ACUTE,
    "Ó": "О" + ACUTE,
    "Ý": "У" + ACUTE,
    "Ú": "И" + ACUTE,
}
_WORD_CHARS = rf"\w{ACUTE}’'"
# A hyphenated word, also when the printed line breaks after one of its hyphens («пліч-\nó-пліч»).
_COMPOUND_RE = re.compile(f"[{_WORD_CHARS}]+(?:-\n?[{_WORD_CHARS}]+)*")
_COMPOUND_JOINER_RE = re.compile("(-\n?)")
# Letters whose Latin and Cyrillic glyphs are identical in the edition's fonts.
_LATIN_TO_CYRILLIC_HOMOGLYPH = dict(zip("ABCEHIKMOPTXaceiopxyÏï", "АВСЕНІКМОРТХасеіорхуЇї", strict=True))
_CYRILLIC_TO_LATIN_HOMOGLYPH = {cyr: lat for lat, cyr in _LATIN_TO_CYRILLIC_HOMOGLYPH.items()}
_ROMAN_NUMERAL_RE = re.compile(r"M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})")
CYRILLIC, LATIN, MIXED = "cyrillic", "latin", "mixed"


def font_base_name(font: str) -> str:
    """Drop the six-letter subset prefix (``BDFOCI+TimesNewRoman`` → ``TimesNewRoman``)."""
    return font.split("+", 1)[1] if "+" in font else font


def _cp1251(char: str) -> str:
    try:
        return char.encode("cp1252").decode("cp1251")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return char


def decode_span_text(font: str, text: str) -> str:
    """Decode one PDF span according to its font family.

    ``1251…`` fonts are re-read as Windows-1251; in ``1251TimesNew…`` fonts every
    vowel glyph is the stressed form, so the acute accent is restored after it.
    Unicode fonts are returned unchanged (see ``restore_scripts``).
    """
    base = font_base_name(font)
    if not base.startswith("1251"):
        return text
    stressed_font = base.startswith("1251TimesNew")
    out: list[str] = []
    for char in text:
        decoded = _cp1251(char) if ord(char) >= 0x80 else char
        out.append(decoded)
        if stressed_font and decoded in _CYRILLIC_VOWELS and ord(char) >= 0x80:
            out.append(ACUTE)
    return "".join(out)


def _is_cyrillic_letter(char: str) -> bool:
    return "Ѐ" <= char <= "ӿ" and char.isalpha()


def _is_latin_letter(char: str) -> bool:
    return char.isalpha() and unicodedata.name(char, "").startswith("LATIN")


def _part_script(part: str) -> str | None:
    """Script of one hyphen-free word part, judged by the letters that differ between the scripts.

    The stressed Latin vowels of the Unicode fonts are neutral.  A part spelled
    only with letters whose glyphs both scripts share takes the script it is
    encoded in; when it mixes the two, only a Roman numeral is decidable (Latin).
    Returns ``CYRILLIC``, ``LATIN``, ``MIXED`` or None (no letter decides).
    """
    distinct: set[str] = set()
    shared: set[str] = set()
    for char in part:
        if _is_cyrillic_letter(char):
            (shared if char in _CYRILLIC_TO_LATIN_HOMOGLYPH else distinct).add(CYRILLIC)
        elif _is_latin_letter(char) and char not in _LATIN_STRESSED:
            (shared if char in _LATIN_TO_CYRILLIC_HOMOGLYPH else distinct).add(LATIN)
    letters = distinct or shared
    if len(letters) == 1:
        return letters.pop()
    if not letters:
        return None
    if not distinct and _ROMAN_NUMERAL_RE.fullmatch(_in_script(part, LATIN, own=True)):
        return LATIN
    return MIXED


def _in_script(part: str, script: str, *, own: bool) -> str:
    """Rewrite ``part`` in ``script``.

    A part whose own letters decide its script also has its lookalike letters
    re-read («Cкладені» with a Latin C); a part that only inherits a script from
    its word or line changes nothing but the stressed vowels.
    """
    if script == CYRILLIC:
        table = {**_LATIN_TO_CYRILLIC_HOMOGLYPH, **_LATIN_STRESSED} if own else _LATIN_STRESSED
    elif script == LATIN and own:
        table = _CYRILLIC_TO_LATIN_HOMOGLYPH
    else:
        return part
    return "".join(table.get(char, char) for char in part)


def restore_scripts(text: str) -> str:
    """Write every word of ``text`` in one script, as printed.

    The Unicode fonts encode stressed Cyrillic vowels as the Latin letters
    á é í ó ý ú, and the text layer sometimes encodes a Cyrillic letter with its
    Latin lookalike or the reverse («Cкладені», «Мicrosóft»).  Each part of a
    hyphenated word (also across a line break: «пліч-\\nó-пліч») takes the
    script its own letters decide; a part made only of stressed vowels
    («душ-á») takes the script of its word, and a lone ending («(-о́ві, -í)»)
    that of the preceding word on its line.  Parts that mix distinct letters of
    both scripts, and a lone letter cited without a hyphen («Польське ó»), are
    left as printed.
    """
    out: list[str] = []
    last = 0
    line_script: str | None = None
    for match in _COMPOUND_RE.finditer(text):
        gap = text[last : match.start()]
        if "\n" in gap:
            line_script = None
        out.append(gap)
        pieces = _COMPOUND_JOINER_RE.split(match.group(0))
        scripts = [_part_script(part) for part in pieces[::2]]
        decided = {script for script in scripts if script in (CYRILLIC, LATIN)}
        word_script = next(iter(decided)) if len(decided) == 1 else None
        is_ending = text[match.start() - 1 : match.start()] == "-"
        inherited = word_script or (line_script if is_ending else None)
        for index, script in enumerate(scripts):
            if script in (CYRILLIC, LATIN):
                pieces[2 * index] = _in_script(pieces[2 * index], script, own=True)
            elif script is None and inherited:
                pieces[2 * index] = _in_script(pieces[2 * index], inherited, own=False)
        out.append("".join(pieces))
        line_script = next((s for s in reversed(scripts) if s in (CYRILLIC, LATIN)), line_script)
        last = match.end()
    out.append(text[last:])
    return unicodedata.normalize("NFC", "".join(out))


def script_anomalies(text: str) -> list[str]:
    """Hyphenated words of ``text`` that mix Latin and Cyrillic letters, or that carry a
    stressed Latin vowel (á é í ó ý ú) without any other Latin letter that only Latin has.

    After ``restore_scripts`` these are the printed Latin examples inside Ukrainian
    words («PIN-код») and the cases it leaves as printed; any other hit is a decoding defect.
    """
    found: list[str] = []
    for match in _COMPOUND_RE.finditer(text):
        word = match.group(0)
        has_cyrillic = any(_is_cyrillic_letter(char) for char in word)
        latin = [char for char in word if _is_latin_letter(char)]
        bare_stress = any(char in _LATIN_STRESSED for char in latin) and all(
            char in _LATIN_STRESSED or char in _LATIN_TO_CYRILLIC_HOMOGLYPH for char in latin
        )
        if (has_cyrillic and latin) or bare_stress:
            found.append(word)
    return found


def restore_page_scripts(pages: Sequence[PageLayout]) -> list[PageLayout]:
    """Apply ``restore_scripts`` to the rows of ``pages`` read as one text, so words split across lines stay whole."""
    rows = [row for page in pages for row in page.rows]
    if any("\n" in row.text for row in rows):
        raise PravopysParseError("a PDF row contains a line break")
    restored = iter(restore_scripts("\n".join(row.text for row in rows)).split("\n"))
    result: list[PageLayout] = []
    for page in pages:
        result.append(
            PageLayout(
                page=page.page,
                rows=[replace(row, text=next(restored)) for row in page.rows],
                margin_labels=[replace(label, text=restore_scripts(label.text)) for label in page.margin_labels],
                printed_number=page.printed_number,
            )
        )
    return result


# ── Layout ───────────────────────────────────────────────────────

RUNNING_HEAD_MAX_Y = 45.0
PAGE_NUMBER_MIN_Y = 515.0
MARGIN_LABEL_MAX_SIZE = 9.0
# Body text is 10.5–11 pt; the first lines of a § start right of the margin labels.
BODY_MIN_SIZE = 10.0
HANGING_BLOCK_X = 236.0
MARGIN_NEIGHBOUR_DY = 8.0
PART_HEADING_MIN_SIZE = 14.5
GROUP_HEADING_MIN_SIZE = 12.3
SUBHEADING_MIN_SIZE = 11.9
INDENT_MIN_X_OFFSET = 10.0
TAB_GAP = 8.0
SPACE_GAP = 1.0


@dataclass(frozen=True)
class PdfLine:
    """One text line from the PDF, already decoded, on a printed page."""

    page: int
    x0: float
    y0: float
    x1: float
    size: float
    text: str


@dataclass(frozen=True)
class Row:
    """A printed row of body text (table cells on one baseline are tab-joined)."""

    page: int
    x0: float
    y0: float
    size: float
    text: str

    @property
    def heading_level(self) -> int:
        if self.size >= PART_HEADING_MIN_SIZE:
            return 1
        if self.size >= GROUP_HEADING_MIN_SIZE:
            return 2
        if self.size >= SUBHEADING_MIN_SIZE:
            return 3
        return 0


@dataclass(frozen=True)
class MarginLabel:
    page: int
    y0: float
    text: str


@dataclass
class PageLayout:
    page: int
    rows: list[Row] = field(default_factory=list)
    margin_labels: list[MarginLabel] = field(default_factory=list)
    printed_number: str | None = None


def lines_from_pdf(pdf_path: Path, official: OfficialFile, first_page: int, last_page: int) -> list[PdfLine]:
    """Read font-decoded lines for printed pages ``first_page``..``last_page`` (PyMuPDF).

    Script restoration needs the neighbouring lines and runs on the laid-out
    pages (``restore_page_scripts``).
    """
    import pymupdf

    lines: list[PdfLine] = []
    with pymupdf.open(str(pdf_path)) as doc:
        if doc.page_count != official.pdf_pages:
            raise PravopysParseError(
                f"{pdf_path}: {doc.page_count} pages, expected {official.pdf_pages} for {official.url}"
            )
        for printed in range(first_page, last_page + 1):
            page = doc[official.printed_page_one_index + printed - 1]
            # PyMuPDF reports coordinates relative to the crop box; the MON copy crops every
            # page at x = 116.4, so translate back to page space to keep one set of thresholds.
            dx, dy = page.cropbox.x0, page.cropbox.y0
            for block in page.get_text("dict", sort=True)["blocks"]:
                for line in block.get("lines", []):
                    spans = line.get("spans", [])
                    if not spans:
                        continue
                    text = "".join(decode_span_text(span["font"], span["text"]) for span in spans)
                    if not text.strip():
                        continue
                    x0, y0, x1, _y1 = line["bbox"]
                    lines.append(
                        PdfLine(
                            page=printed,
                            x0=float(x0 + dx),
                            y0=float(y0 + dy),
                            x1=float(x1 + dx),
                            size=float(max(span["size"] for span in spans)),
                            text=text,
                        )
                    )
    return lines


def _join_row(parts: Sequence[PdfLine]) -> str:
    ordered = sorted(parts, key=lambda line: line.x0)
    text = ordered[0].text.strip()
    for previous, current in pairwise(ordered):
        gap = current.x0 - previous.x1
        sep = "\t" if gap > TAB_GAP else (" " if gap > SPACE_GAP else "")
        text += sep + current.text.strip()
    return text


def layout_pages(lines: Iterable[PdfLine]) -> list[PageLayout]:
    """Group lines into rows per page; drop running heads and page numbers; keep margin labels apart."""
    by_page: dict[int, list[PdfLine]] = {}
    for line in lines:
        by_page.setdefault(line.page, []).append(line)
    pages: list[PageLayout] = []
    for page_number in sorted(by_page):
        layout = PageLayout(page=page_number)
        content: list[PdfLine] = []
        page_lines = by_page[page_number]
        for line in page_lines:
            stripped = line.text.strip()
            if line.y0 < RUNNING_HEAD_MAX_Y and line.size < MARGIN_LABEL_MAX_SIZE + 1:
                continue  # running head (part/chapter title in small caps)
            if line.y0 > PAGE_NUMBER_MIN_Y and stripped.isdigit():
                layout.printed_number = stripped
                continue
            if line.size < MARGIN_LABEL_MAX_SIZE or _is_small_margin_label(line, page_lines):
                layout.margin_labels.append(MarginLabel(page_number, line.y0, stripped))
                continue
            content.append(line)
        content.sort(key=lambda line: (line.y0, line.x0))
        current: list[PdfLine] = []
        for line in content:
            if current and abs(line.y0 - current[0].y0) > 2.0:
                layout.rows.append(_row(current))
                current = []
            current.append(line)
        if current:
            layout.rows.append(_row(current))
        layout.margin_labels.sort(key=lambda label: label.y0)
        pages.append(layout)
    return pages


def _is_small_margin_label(line: PdfLine, page_lines: Sequence[PdfLine]) -> bool:
    """A note-size line in the margin column beside a body line of the indented first-line block.

    Parts III–IV print margin labels («Ą, Ę») at the 9.5 pt size of notes; a note's
    last line also ends left of the block, but no body line sits beside it.
    """
    if line.size >= BODY_MIN_SIZE or line.x1 >= HANGING_BLOCK_X:
        return False
    return any(
        other.x0 >= HANGING_BLOCK_X and other.size >= BODY_MIN_SIZE and abs(other.y0 - line.y0) <= MARGIN_NEIGHBOUR_DY
        for other in page_lines
    )


def _row(parts: Sequence[PdfLine]) -> Row:
    first = min(parts, key=lambda line: line.x0)
    return Row(
        page=first.page,
        x0=first.x0,
        y0=min(line.y0 for line in parts),
        size=max(line.size for line in parts),
        text=_join_row(parts),
    )


# ── Table of contents ────────────────────────────────────────────

_TOC_PAGE_RE = re.compile(r"\s*(?:\.{2,}|…+)?\s*(\d{1,3})\s*$")
_TOC_LEADER_RE = re.compile(r"\.{2,}|…{2,}")
_PARAGRAPH_HEAD_RE = re.compile(r"^§\s*(\d{1,3})\.(?=\s|$)")
# The contents print «§ 140» without a title or full stop.
_TOC_PARAGRAPH_RE = re.compile(r"^§\s*(\d{1,3})\.?(?=\s|$)")
_PART_HEAD_RE = re.compile(r"^[IVІХ]{1,4}\.\s+[^a-zа-яіїєґ]+$")


@dataclass(frozen=True)
class TocEntry:
    kind: str  # "paragraph" | "heading" | "part"
    number: int | None
    title: str
    page: int | None


def parse_toc(rows: Iterable[Row]) -> list[TocEntry]:
    """Parse the printed contents into § entries, headings and part titles."""
    entries: list[TocEntry] = []
    buffer: list[str] = []

    def flush(page: int | None) -> None:
        if not buffer:
            return
        text = " ".join(part.strip() for part in buffer if part.strip())
        text = re.sub(r"(\w)- (\w)", r"\1\2", text) if page is not None else text
        text = re.sub(r"\s+", " ", text).strip()
        head = _TOC_PARAGRAPH_RE.match(text)
        if head:
            title = text[head.end() :].strip()
            entries.append(TocEntry("paragraph", int(head.group(1)), title, page))
        elif _PART_HEAD_RE.match(text) and page is None:
            entries.append(TocEntry("part", None, text, None))
        else:
            entries.append(TocEntry("heading", None, text, page))
        buffer.clear()

    for row in rows:
        text = row.text.replace("\t", " ").strip()
        if not text or text.casefold() == "зміст":
            continue
        if _TOC_PARAGRAPH_RE.match(text) and buffer:
            flush(None)
        if _PART_HEAD_RE.match(text) and not _TOC_LEADER_RE.search(text) and not _TOC_PAGE_RE.search(text):
            flush(None)
            buffer.append(text)
            flush(None)
            continue
        page_match = _TOC_PAGE_RE.search(text) if _TOC_LEADER_RE.search(text) or buffer else None
        if page_match and (_TOC_LEADER_RE.search(text) or text[: page_match.start()].strip() == ""):
            buffer.append(_TOC_LEADER_RE.sub(" ", text[: page_match.start()]))
            flush(int(page_match.group(1)))
        else:
            buffer.append(text)
    flush(None)
    return entries


# ── Segmentation ─────────────────────────────────────────────────


@dataclass
class Section:
    ordinal: int
    level: int
    title: str
    page: int
    parent_ordinal: int | None
    rows: list[Row] = field(default_factory=list)


@dataclass
class Paragraph:
    number: int
    page_start: int
    section_ordinal: int | None
    rows: list[Row] = field(default_factory=list)
    margin_labels: list[MarginLabel] = field(default_factory=list)

    @property
    def page_end(self) -> int:
        return max(row.page for row in self.rows)


@dataclass
class ParsedEdition:
    sections: list[Section]
    paragraphs: list[Paragraph]
    toc: list[TocEntry]
    printed_page_mismatches: list[tuple[int, str | None]]


def _paragraph_start(row: Row, expected: int) -> bool:
    match = _PARAGRAPH_HEAD_RE.match(row.text)
    return bool(match) and int(match.group(1)) == expected


# Level given to a contents-listed heading printed at body size («А. Однина»).
BODY_SIZE_HEADING_LEVEL = 4
_MAX_HEADING_ROWS = 3


def heading_key(text: str) -> str:
    """Comparison key for headings: folded, Latin I read as Cyrillic І, letters only."""
    folded = fold_for_lookup(text).replace("i", "і")
    return re.sub(r"[\W\d_]", "", folded)


@dataclass
class _HeadingGroup:
    level: int
    rows: list[Row]

    @property
    def title(self) -> str:
        return " ".join(row.text.replace("\t", " ").strip() for row in self.rows)


def _match_listed_heading(stream: Sequence[Row | MarginLabel], start: int, toc_keys: frozenset[str]) -> int:
    """Number of body-size rows from ``start`` that spell a heading listed in the contents (0 if none).

    The longest match wins: «ЧЕРГУВАННЯ ГОЛОСНИХ / У ДІЄСЛІВНИХ КОРЕНЯХ» is one
    heading even though its first row alone is another listed heading.
    """
    key = ""
    best = 0
    for taken, item in enumerate(stream[start : start + _MAX_HEADING_ROWS], start=1):
        if isinstance(item, MarginLabel) or item.heading_level:
            break
        key += heading_key(item.text)
        if key in toc_keys:
            best = taken
        if not key or not any(listed.startswith(key) for listed in toc_keys):
            break
    return best


def _heading_run(
    stream: Sequence[Row | MarginLabel], start: int, expected: int, toc_keys: frozenset[str]
) -> tuple[list[_HeadingGroup], list[MarginLabel], int]:
    """Collect consecutive heading rows from ``start``; returns (groups, skipped labels, next index)."""
    groups: list[_HeadingGroup] = []
    labels: list[MarginLabel] = []
    index = start
    while index < len(stream):
        item = stream[index]
        if isinstance(item, MarginLabel):
            labels.append(item)
            index += 1
            continue
        if _paragraph_start(item, expected):
            break
        if item.heading_level:
            if groups and groups[-1].level == item.heading_level:
                groups[-1].rows.append(item)
            else:
                groups.append(_HeadingGroup(item.heading_level, [item]))
            index += 1
            continue
        taken = _match_listed_heading(stream, index, toc_keys)
        if not taken:
            break
        groups.append(
            _HeadingGroup(BODY_SIZE_HEADING_LEVEL, [r for r in stream[index : index + taken] if isinstance(r, Row)])
        )
        index += taken
    return groups, labels, index


def segment_body(
    pages: Sequence[PageLayout],
    toc: Sequence[TocEntry] = (),
    expected_count: int = TOC_PARAGRAPH_COUNT,
) -> tuple[list[Section], list[Paragraph]]:
    """Split body rows into structural sections and numbered § paragraphs.

    A § starts at a row beginning «§ N.» where N is the next expected number, so
    cross-references («див. § 126») never start one.  Heading rows are rows of
    heading size, or body-size rows that spell a heading listed in the printed
    contents.  A run of heading rows directly followed by a § start opens
    sections (one per heading level); so does a part or group heading followed
    by text, whose text up to the next § is the section's introduction.  A
    lower-level heading inside an open § stays in the § text.
    """
    toc_keys = frozenset(heading_key(entry.title) for entry in toc if entry.kind != "paragraph" and entry.title)
    stream: list[Row | MarginLabel] = []
    for page in pages:
        items: list[tuple[float, int, Row | MarginLabel]] = [(row.y0, 0, row) for row in page.rows]
        items += [(label.y0, 1, label) for label in page.margin_labels]
        stream.extend(item for _y, _k, item in sorted(items, key=lambda entry: (entry[0], entry[1])))

    sections: list[Section] = []
    paragraphs: list[Paragraph] = []
    stack: dict[int, Section] = {}
    current_paragraph: Paragraph | None = None
    current_section: Section | None = None
    pending_labels: list[MarginLabel] = []
    expected = 1
    index = 0

    def open_section(group: _HeadingGroup) -> Section:
        parent = next((stack[lvl] for lvl in range(group.level - 1, 0, -1) if lvl in stack), None)
        section = Section(
            ordinal=len(sections) + 1,
            level=group.level,
            title=group.title,
            page=group.rows[0].page,
            parent_ordinal=parent.ordinal if parent else None,
        )
        sections.append(section)
        stack[group.level] = section
        for deeper in [lvl for lvl in stack if lvl > group.level]:
            del stack[deeper]
        return section

    while index < len(stream):
        item = stream[index]
        if isinstance(item, MarginLabel):
            (current_paragraph.margin_labels if current_paragraph else pending_labels).append(item)
            index += 1
            continue
        if _paragraph_start(item, expected):
            current_paragraph = Paragraph(
                number=expected,
                page_start=item.page,
                section_ordinal=current_section.ordinal if current_section else None,
                rows=[item],
                margin_labels=pending_labels,
            )
            pending_labels = []
            paragraphs.append(current_paragraph)
            expected += 1
            index += 1
            # A § printed as a heading («§ 166. КОМБІНОВАНЕ ВЖИВАННЯ / РОЗДІЛОВИХ ЗНАКІВ»)
            # continues on the following rows of the same size.
            while (
                item.heading_level
                and index < len(stream)
                and isinstance(stream[index], Row)
                and stream[index].heading_level == item.heading_level
                and not _paragraph_start(stream[index], expected)
            ):
                current_paragraph.rows.append(stream[index])
                index += 1
            continue
        groups, labels, after = _heading_run(stream, index, expected, toc_keys)
        if groups:
            following = next((row for row in stream[after:] if isinstance(row, Row)), None)
            starts_paragraph = following is not None and _paragraph_start(following, expected)
            for group in groups:
                if starts_paragraph or group.level <= 2 or current_paragraph is None:
                    current_section = open_section(group)
                    current_paragraph = None
                else:
                    current_paragraph.rows.extend(group.rows)
            (current_paragraph.margin_labels if current_paragraph else pending_labels).extend(labels)
            index = after
            continue
        if current_paragraph is not None:
            current_paragraph.rows.append(item)
        elif current_section is not None:
            current_section.rows.append(item)
        else:
            raise PravopysParseError(f"text before the first heading on p. {item.page}: {item.text[:60]!r}")
        index += 1

    if expected - 1 != expected_count:
        raise PravopysParseError(f"found §§ 1–{expected - 1}, expected {expected_count}")
    return sections, paragraphs


# ── Text forms ───────────────────────────────────────────────────

_HYPHEN_END_RE = re.compile(f"([{_WORD_CHARS}]+)-$")
_WORD_START_RE = re.compile(f"^([{_WORD_CHARS}]+)")
# A morpheme written with hyphens on both sides («-шк-»): the opening hyphen follows a non-letter.
_MORPHEME_OPEN_RE = re.compile(f"(?:^|[^{_WORD_CHARS}])-$")
# Rows that begin a note or a numbered point even without a deeper indent.
_ITEM_START_RE = re.compile(r"^(?:Примітка\b|\d{1,2}\.\s|\d{1,2}\)\s|[а-яґєії]\)\s)")
LexiconPredicate = Callable[[str], bool]


def layout_text(rows: Iterable[Row]) -> str:
    """The printed text, one printed row per line (table cells tab-separated)."""
    return "\n".join(row.text for row in rows)


def fold_for_lookup(value: str) -> str:
    """Lowercase, drop stress marks, unify apostrophes (for lexicon and search keys)."""
    folded = unicodedata.normalize("NFD", value)
    folded = folded.replace(ACUTE, "").replace(GRAVE, "")
    folded = unicodedata.normalize("NFC", folded)
    return folded.replace("'", "’").replace("ʼ", "’").casefold()


def normalized_text(rows: Sequence[Row], is_word: LexiconPredicate | None = None) -> tuple[str, list[str]]:
    """Join printed rows into running text and resolve line-end hyphens.

    Line-end hyphens are decided by ``_line_end_hyphen``.  A row indented beyond
    the previous one, a note or numbered point, a table row and a heading start a
    new line.  This is a derived reading aid; the printed text is ``layout_text``.
    Returns ``(text, alternatives)``: for every hyphen the lexicon does not
    decide, the reading the rules did not choose (``Бе́рклі-сквер`` when
    «Бе́рклі-/сквер» was joined, ``НьюЙорк`` when «Нью-/Йорк» kept its hyphen), so
    that search finds the word either way.  Their number is the unresolved count.
    """
    if not rows:
        return "", []
    alternatives: list[str] = []
    out = rows[0].text
    for previous, row in pairwise(rows):
        new_line = (
            row.x0 - previous.x0 >= INDENT_MIN_X_OFFSET
            or _ITEM_START_RE.match(row.text) is not None
            or "\t" in row.text
            or "\t" in previous.text
            or row.heading_level > 0
            or previous.heading_level > 0
        )
        hyphen = _HYPHEN_END_RE.search(out)
        start = _WORD_START_RE.match(row.text)
        if hyphen and start and not new_line:
            left, right = hyphen.group(1), start.group(1)
            decision, attested = _line_end_hyphen(out[: hyphen.start()], left, right, is_word)
            if not attested:
                alternatives.append(f"{left}-{right}" if decision == "join" else f"{left}{right}")
            out = (out[:-1] if decision == "join" else out + (" " if decision == "space" else "")) + row.text
            continue
        out += ("\n" if new_line else " ") + row.text
    return out, alternatives


def _line_end_hyphen(before: str, left: str, right: str, is_word: LexiconPredicate | None) -> tuple[str, bool]:
    """Decide a line-end hyphen: ``("join" | "keep" | "space", attested_by_lexicon)``.

    VESUM decides when it knows the joined or the hyphenated form.  Otherwise the
    hyphen is kept for morpheme notation («-шк-» at the line end, then a space),
    before a capital («Нью-Йо́рк», «псе́вдо-Фа́уст»: a split inside one word never
    puts a capital mid-word), and, in lowercase words, when both parts are words
    («годи́на-дві») or a linking о/е precedes a word («свердли́льно-шліфува́льний»).
    Any other split is joined («Ха́р-ків»).  Only the lexicon-backed decisions are
    attested; the caller counts the rest as unresolved.
    """
    left_key = fold_for_lookup(left).rstrip("’")
    right_key = fold_for_lookup(right).rstrip("’")

    def known(form: str) -> bool:
        return bool(is_word and form and is_word(form))

    if known(left_key + right_key):
        return "join", True
    if known(f"{left_key}-{right_key}"):
        return "keep", True
    if _MORPHEME_OPEN_RE.search(before):
        return "space", False
    if right[:1].isupper() and not left.isupper():
        return "keep", False
    if left[:1].islower():
        if known(left_key) and known(right_key):
            return "keep", False
        if left_key[-1:] in {"о", "е"} and len(left_key) > 4 and known(right_key):
            return "keep", False
    return "join", False


def vesum_word_predicate(vesum_db: Path) -> LexiconPredicate:
    """Exact word-form membership in VESUM (read-only, cached)."""
    conn = _open_readonly(vesum_db.resolve())
    cache: dict[str, bool] = {}

    def is_word(form: str) -> bool:
        if form not in cache:
            variants = {form, form.replace("’", "'")}
            placeholders = ",".join("?" for _ in variants)
            row = conn.execute(
                f"SELECT 1 FROM forms_all WHERE word_form IN ({placeholders}) LIMIT 1",
                tuple(variants),
            ).fetchone()
            cache[form] = row is not None
        return cache[form]

    return is_word


# ── Context readings ─────────────────────────────────────────────


@dataclass(frozen=True)
class ContextReading:
    """A printed token spelled only with letters both scripts share, re-read in the script its § decides.

    ``restore_scripts`` cannot decide such a token from its glyphs; the
    surrounding text of the § can.  ``count`` is the number of occurrences the
    pinned PDF prints, so a parse that drifts fails instead of missing one.
    """

    paragraph: int
    where: str  # "rows" or "margin_labels"
    printed: str
    reading: str
    count: int
    context: str


CONTEXT_READINGS: tuple[ContextReading, ...] = (
    ContextReading(
        129, "rows", "-іa", "-ia", 1, "p. 159: the rule cites the foreign (Latin) ending -ia, rendered as -ія"
    ),
    ContextReading(
        34, "margin_labels", "-IР-", "-ІР-", 1, "pp. 45–46: the label names the Cyrillic suffix -ір- of the body"
    ),
    # pp. 96–97 number the four declensions I, II, III, IV; III and IV are encoded in Latin.
    ContextReading(66, "rows", "І відміна", "I відміна", 1, "pp. 96–97: Roman numeral of the I declension"),
    ContextReading(66, "rows", "ІІ відміна", "II відміна", 1, "pp. 96–97: Roman numeral of the II declension"),
)


def apply_context_readings(
    paragraphs: Sequence[Paragraph], readings: Sequence[ContextReading] = CONTEXT_READINGS
) -> list[Paragraph]:
    """Return ``paragraphs`` with every reading applied to the whole-word occurrences of its printed token."""
    by_number = {paragraph.number: paragraph for paragraph in paragraphs}
    for reading in readings:
        paragraph = by_number.get(reading.paragraph)
        if paragraph is None:
            raise PravopysParseError(f"context reading for missing § {reading.paragraph}")
        pattern = re.compile(rf"(?<!\w){re.escape(reading.printed)}(?!\w)")
        items = getattr(paragraph, reading.where)
        found = sum(len(pattern.findall(item.text)) for item in items)
        if found != reading.count:
            raise PravopysParseError(
                f"§ {reading.paragraph}: {reading.printed!r} printed {found} times, expected {reading.count}"
            )
        updated = [
            replace(item, text=pattern.sub(lambda _match, new=reading.reading: new, item.text)) for item in items
        ]
        by_number[reading.paragraph] = replace(paragraph, **{reading.where: updated})
    return [by_number[paragraph.number] for paragraph in paragraphs]


# ── Parse driver ─────────────────────────────────────────────────


def parse_edition(pdf_path: Path, official: OfficialFile) -> ParsedEdition:
    """Parse body (front matter to § 168) and contents of the official PDF."""
    body_pages = restore_page_scripts(
        layout_pages(lines_from_pdf(pdf_path, official, FRONT_MATTER_FIRST_PAGE, BODY_LAST_PAGE))
    )
    toc_pages = restore_page_scripts(layout_pages(lines_from_pdf(pdf_path, official, TOC_FIRST_PAGE, TOC_LAST_PAGE)))
    mismatches = [(page.page, page.printed_number) for page in body_pages if page.printed_number != str(page.page)]
    toc = parse_toc(row for page in toc_pages for row in page.rows)
    sections, paragraphs = segment_body(body_pages, toc)
    return ParsedEdition(sections, apply_context_readings(paragraphs), toc, mismatches)


def toc_paragraphs(toc: Iterable[TocEntry]) -> dict[int, TocEntry]:
    found: dict[int, TocEntry] = {}
    for entry in toc:
        if entry.kind == "paragraph" and entry.number is not None:
            if entry.number in found:
                raise PravopysParseError(f"§ {entry.number} appears twice in the contents")
            found[entry.number] = entry
    return found


def validate_against_toc(parsed: ParsedEdition) -> list[str]:
    """Return every disagreement between the parsed body and the printed contents."""
    problems: list[str] = []
    toc = toc_paragraphs(parsed.toc)
    if sorted(toc) != list(range(1, TOC_PARAGRAPH_COUNT + 1)):
        problems.append(f"contents lists {len(toc)} §§, expected 1–{TOC_PARAGRAPH_COUNT}")
    body = {paragraph.number: paragraph for paragraph in parsed.paragraphs}
    if sorted(body) != sorted(toc):
        problems.append("body § numbers differ from the contents")
    for number, entry in toc.items():
        paragraph = body.get(number)
        if paragraph is not None and entry.page != paragraph.page_start:
            problems.append(f"§ {number}: contents p. {entry.page}, body starts p. {paragraph.page_start}")
    for page, printed in parsed.printed_page_mismatches:
        problems.append(f"p. {page}: printed page number {printed!r}")
    return problems


# ── Storage ──────────────────────────────────────────────────────

PRAVOPYS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS pravopys_sources (
    source_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    edition TEXT NOT NULL,
    approvals TEXT NOT NULL,
    citation TEXT NOT NULL,
    file_sha256 TEXT NOT NULL,
    file_url TEXT NOT NULL,
    distributor TEXT NOT NULL,
    official_urls TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    pdf_pages INTEGER NOT NULL,
    toc_paragraph_count INTEGER NOT NULL,
    paragraph_count INTEGER NOT NULL,
    section_count INTEGER NOT NULL,
    parser_version TEXT NOT NULL,
    ingested_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pravopys_sections (
    source_id TEXT NOT NULL REFERENCES pravopys_sources(source_id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    level INTEGER NOT NULL,
    title TEXT NOT NULL,
    page INTEGER NOT NULL,
    parent_ordinal INTEGER,
    intro_text TEXT NOT NULL,
    intro_text_normalized TEXT NOT NULL,
    intro_sha256 TEXT NOT NULL,
    PRIMARY KEY (source_id, ordinal)
);
CREATE TABLE IF NOT EXISTS pravopys_paragraphs (
    source_id TEXT NOT NULL REFERENCES pravopys_sources(source_id) ON DELETE CASCADE,
    number INTEGER NOT NULL,
    title TEXT NOT NULL,
    toc_page INTEGER NOT NULL,
    page_start INTEGER NOT NULL,
    page_end INTEGER NOT NULL,
    section_ordinal INTEGER,
    section_path TEXT NOT NULL,
    margin_labels TEXT NOT NULL,
    text TEXT NOT NULL,
    text_normalized TEXT NOT NULL,
    hyphen_alternatives TEXT NOT NULL DEFAULT '[]',
    text_sha256 TEXT NOT NULL,
    unresolved_hyphenations INTEGER NOT NULL,
    locator TEXT NOT NULL,
    PRIMARY KEY (source_id, number)
);
"""


def ensure_pravopys_schema(conn: SQLiteConnection) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(PRAVOPYS_SCHEMA_SQL)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(pravopys_paragraphs)")}
    if "hyphen_alternatives" not in columns:  # tables written by parser v1
        conn.execute("ALTER TABLE pravopys_paragraphs ADD COLUMN hyphen_alternatives TEXT NOT NULL DEFAULT '[]'")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def paragraph_locator(number: int, page_start: int, page_end: int) -> str:
    pages = f"с. {page_start}" if page_start == page_end else f"с. {page_start}–{page_end}"
    return f"{PRAVOPYS_CITATION}, § {number}, {pages}"


def _section_path(sections: dict[int, Section], ordinal: int | None) -> list[str]:
    path: list[str] = []
    while ordinal is not None:
        section = sections[ordinal]
        path.append(section.title)
        ordinal = section.parent_ordinal
    return list(reversed(path))


@dataclass(frozen=True)
class IngestCounts:
    paragraphs: int
    sections: int
    toc_paragraphs: int
    unresolved_hyphenations: int


def store_edition(
    conn: SQLiteConnection,
    parsed: ParsedEdition,
    official: OfficialFile,
    *,
    retrieved_at: str,
    is_word: LexiconPredicate | None = None,
    ingested_at: str | None = None,
) -> IngestCounts:
    """Replace the stored edition with ``parsed`` in one transaction."""
    problems = validate_against_toc(parsed)
    if problems:
        raise PravopysParseError("; ".join(problems))
    toc = toc_paragraphs(parsed.toc)
    sections_by_ordinal = {section.ordinal: section for section in parsed.sections}
    ensure_pravopys_schema(conn)
    unresolved_total = 0
    with conn:
        conn.execute("DELETE FROM pravopys_paragraphs WHERE source_id = ?", (PRAVOPYS_SOURCE_ID,))
        conn.execute("DELETE FROM pravopys_sections WHERE source_id = ?", (PRAVOPYS_SOURCE_ID,))
        conn.execute("DELETE FROM pravopys_sources WHERE source_id = ?", (PRAVOPYS_SOURCE_ID,))
        conn.execute(
            """
            INSERT INTO pravopys_sources (
                source_id, title, edition, approvals, citation, file_sha256, file_url, distributor,
                official_urls, retrieved_at, pdf_pages, toc_paragraph_count, paragraph_count,
                section_count, parser_version, ingested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                PRAVOPYS_SOURCE_ID,
                PRAVOPYS_TITLE,
                PRAVOPYS_EDITION,
                json.dumps(list(PRAVOPYS_APPROVALS), ensure_ascii=False),
                PRAVOPYS_CITATION,
                official.sha256,
                official.url,
                official.distributor,
                json.dumps([f.url for f in OFFICIAL_FILES.values()], ensure_ascii=False),
                retrieved_at,
                official.pdf_pages,
                len(toc),
                len(parsed.paragraphs),
                len(parsed.sections),
                PARSER_VERSION,
                ingested_at or utc_now(),
            ),
        )
        for section in parsed.sections:
            intro = layout_text(section.rows)
            intro_normalized, intro_alternatives = normalized_text(section.rows, is_word)
            unresolved_total += len(intro_alternatives)
            conn.execute(
                """
                INSERT INTO pravopys_sections (
                    source_id, ordinal, level, title, page, parent_ordinal,
                    intro_text, intro_text_normalized, intro_sha256
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    PRAVOPYS_SOURCE_ID,
                    section.ordinal,
                    section.level,
                    section.title,
                    section.page,
                    section.parent_ordinal,
                    intro,
                    intro_normalized,
                    sha256_text(intro),
                ),
            )
        for paragraph in parsed.paragraphs:
            text = layout_text(paragraph.rows)
            text_norm, alternatives = normalized_text(paragraph.rows, is_word)
            unresolved_total += len(alternatives)
            title = toc[paragraph.number].title
            conn.execute(
                """
                INSERT INTO pravopys_paragraphs (
                    source_id, number, title, toc_page, page_start, page_end, section_ordinal,
                    section_path, margin_labels, text, text_normalized, hyphen_alternatives, text_sha256,
                    unresolved_hyphenations, locator
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    PRAVOPYS_SOURCE_ID,
                    paragraph.number,
                    title,
                    toc[paragraph.number].page,
                    paragraph.page_start,
                    paragraph.page_end,
                    paragraph.section_ordinal,
                    json.dumps(_section_path(sections_by_ordinal, paragraph.section_ordinal), ensure_ascii=False),
                    json.dumps(
                        [{"page": label.page, "text": label.text} for label in paragraph.margin_labels],
                        ensure_ascii=False,
                    ),
                    text,
                    text_norm,
                    json.dumps(alternatives, ensure_ascii=False),
                    sha256_text(text),
                    len(alternatives),
                    paragraph_locator(paragraph.number, paragraph.page_start, paragraph.page_end),
                ),
            )
    return IngestCounts(len(parsed.paragraphs), len(parsed.sections), len(toc), unresolved_total)


# ── Offline lookup ───────────────────────────────────────────────

_TOKEN_RE = re.compile(r"[\w’]+")


def _dict_rows(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def pravopys_store_status(conn: SQLiteConnection) -> dict[str, Any]:
    """``{"state": "complete", **source_row}`` only when the full edition is stored."""
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    if not {"pravopys_sources", "pravopys_paragraphs"} <= tables:
        return {"state": "missing_table"}
    sources = _dict_rows(conn.execute("SELECT * FROM pravopys_sources WHERE source_id = ?", (PRAVOPYS_SOURCE_ID,)))
    if not sources:
        return {"state": "empty"}
    stored = conn.execute(
        "SELECT COUNT(*) FROM pravopys_paragraphs WHERE source_id = ?", (PRAVOPYS_SOURCE_ID,)
    ).fetchone()[0]
    if stored != TOC_PARAGRAPH_COUNT or sources[0]["toc_paragraph_count"] != TOC_PARAGRAPH_COUNT:
        return {"state": "incomplete", "stored_paragraphs": stored}
    return {"state": "complete", **sources[0]}


def _paragraph_record(record: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "ok",
        "source": "offline",
        "source_id": PRAVOPYS_SOURCE_ID,
        "section": record["number"],
        "title": record["title"],
        "section_path": json.loads(record["section_path"]),
        "locator": record["locator"],
        "page_start": record["page_start"],
        "page_end": record["page_end"],
        # The printed text line by line; ``text_normalized`` is derived (joined lines).
        "text": record["text"],
        "text_normalized": record["text_normalized"],
        "text_sha256": record["text_sha256"],
        "url": source["file_url"],
        "file_sha256": source["file_sha256"],
        "retrieved_at": source["retrieved_at"],
    }


def get_paragraph(conn: SQLiteConnection, number: int) -> dict[str, Any] | None:
    """The stored § ``number``, or None when the store is incomplete or the § does not exist."""
    status = pravopys_store_status(conn)
    if status["state"] != "complete":
        return None
    rows = _dict_rows(
        conn.execute(
            "SELECT * FROM pravopys_paragraphs WHERE source_id = ? AND number = ?",
            (PRAVOPYS_SOURCE_ID, int(number)),
        )
    )
    return _paragraph_record(rows[0], status) if rows else None


def _topic_stems(topic: str) -> list[str]:
    """Search stems: short words match whole words, longer ones by prefix (inflection)."""
    folded = fold_for_lookup(topic)
    # Legacy keys spell the apostrophe as a hyphen: «м-який-знак» → «м’який знак».
    folded = re.sub(r"^(\w)-(?=[яюєї])", r"\1’", folded)
    stems = []
    for token in _TOKEN_RE.findall(folded.replace("-", " ")):
        if len(token) >= 6:
            token = token[:-2]
        elif len(token) >= 5:
            token = token[:-1]
        stems.append(token)
    return stems


def _matches(word: str, stem: str) -> bool:
    return word == stem if len(stem) <= 3 else word.startswith(stem)


def _word_hits(words: list[str], stems: list[str]) -> int:
    return sum(any(_matches(word, stem) for word in words) for stem in stems)


def search_paragraphs(conn: SQLiteConnection, topic: str, limit: int = 5) -> list[dict[str, Any]]:
    """Rank stored §§ for a topic.

    Top tier: every topic word is in the § title or in its heading path (the
    first § under a matching heading comes first).  Below it, partial matches
    rank by title hits, heading-path hits and occurrences in the text.
    """
    status = pravopys_store_status(conn)
    stems = _topic_stems(topic)
    if status["state"] != "complete" or not stems:
        return []
    scored: list[tuple[float, int, dict[str, Any]]] = []
    for record in _dict_rows(
        conn.execute("SELECT * FROM pravopys_paragraphs WHERE source_id = ?", (PRAVOPYS_SOURCE_ID,))
    ):
        title_words = _TOKEN_RE.findall(fold_for_lookup(record["title"]))
        path_words = _TOKEN_RE.findall(fold_for_lookup(" ".join(json.loads(record["section_path"]))))
        # Unresolved line-end hyphens are indexed in both readings (``normalized_text``).
        alternatives = " ".join(json.loads(record.get("hyphen_alternatives") or "[]"))
        text_words = _TOKEN_RE.findall(fold_for_lookup(f"{record['text_normalized']}\n{alternatives}"))
        title_hits = _word_hits(title_words, stems)
        path_hits = _word_hits(path_words, stems)
        text_occurrences = sum(1 for word in text_words for stem in stems if _matches(word, stem))
        if not (title_hits or path_hits or text_occurrences):
            continue
        if title_hits == len(stems) or path_hits == len(stems):
            score = 1000.0
        else:
            score = 10.0 * title_hits + 3.0 * path_hits + min(text_occurrences, 30) / 10
        scored.append((score, record["number"], record))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [_paragraph_record(record, status) for _score, _number, record in scored[:limit]]


def open_read_only(db_path: Path) -> SQLiteConnection:
    conn = _open_readonly(Path(db_path).resolve(), check_same_thread=False)
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def lookup_offline(topic: str, *, db_path: Path) -> dict[str, Any] | None:
    """Answer a ``query_pravopys`` topic from the stored official text.

    A number (optionally «§ 7») is a § number.  Returns the best match with up to
    four further candidates under ``other_matches``; ``{"status":
    "store_unavailable", "reason": ...}`` when no complete edition is stored; or
    None for a real miss.
    """
    path = Path(db_path)
    if not path.is_file() or not path.stat().st_size:
        return {"status": "store_unavailable", "reason": "no sources.db"}
    conn = open_read_only(path)
    try:
        status = pravopys_store_status(conn)
        if status["state"] != "complete":
            return {"status": "store_unavailable", "reason": status["state"]}
        cleaned = topic.strip().lstrip("§").strip()
        if cleaned.isdigit():
            return get_paragraph(conn, int(cleaned))
        matches = search_paragraphs(conn, cleaned)
        if not matches:
            return None
        best = dict(matches[0])
        best["other_matches"] = [
            {"section": match["section"], "title": match["title"], "locator": match["locator"]} for match in matches[1:]
        ]
        return best
    finally:
        conn.close()
