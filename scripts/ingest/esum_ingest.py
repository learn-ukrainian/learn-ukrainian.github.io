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
import sqlite3
import sys
from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO / "data" / "raw" / "esum" / "vol1.txt"
DEFAULT_OUTPUT = REPO / "data" / "processed" / "esum_vol1.jsonl"
_VESUM_CONN: sqlite3.Connection | None = None
_VESUM_CONN_UNAVAILABLE = False
_VESUM_LEMMAS: frozenset[str] | None = None
CYRILLIC_WORD = r"[а-яґіїєА-ЯҐІЇЄ'’]"
TEXTPDF_STRONG_HEADWORD = rf"(?:{CYRILLIC_WORD}{{2,20}}[1-9!?-]?|{CYRILLIC_WORD}-)"

# Body-start anchor: a homonym-marked single-letter opener that begins
# the dictionary body for each volume. Vol 1 opens with ``а 1 (``; vol 2
# with ``да 1 «``; vol 4 with ``о 1 (``; vol 6 with ``у 1 (``. Vols 3
# and 5 don't have a homonym-1 marker on the first body entry, so the
# match falls through and the parser starts from line 0; downstream
# entry validation filters out front-matter prose.
BODY_START_RE = re.compile(
    r"^[а-яґіїє]{1,3}\s*[1!]\s+[«\(]",
    re.IGNORECASE,
)

# Body-end anchor: Russian-language colophon header that immediately
# follows the dictionary body in vols 1-3. Vol 3 OCR has a typo
# ``СЄР`` instead of ``ССР``. Vols 4-6 print the colophon broken across
# multiple lines (``АКАДЕМІЯ НАУК\nУКРАЇНИ``); the regex misses and the
# parser falls back to processing to EOF, with entry validation rejecting
# back-matter prose.
BODY_END_RE = re.compile(
    r"^АКАДЕМИЯ\s+НАУК\s+УКРАИНСКОЙ\s+(?:ССР|СЄР)\s*$",
)

# Specific Russian headwords that appear in the tail of vol 6 or as noise.
# While Russian words appear in etymology bodies, they should not be entries.
RUSSIAN_HEADWORDS = {"последний", "который", "этот", "тот"}

# Known OCR noise lemmas collected from spot-checks (Issue #2183).
GARBAGE_HEADWORDS = {
    "видавництво",
    "виготовлено",
    "укладачі",
    "нвп",
    "тов",
    "і£і",
    "ргазкас",
    "з8оіуь",
    "к88",
    "пп:",
    "кзсря",
    "егаепке!",
    "угаьіе",
    "іїейїма",
    "кайап",
    "никсблод",
}

# Text-pdf column transitions can promote tiny fragments or source
# abbreviations to apparent headwords. These exact forms are high-volume
# false positives in vols 4-6 and should not be recovered through VESUM.
TEXT_PDF_FRAGMENT_HEADWORDS = {"ка", "рай", "тин", "від", "ем", "мов", "не", "мак"}

# Real short ESUM headwords that are not reliably covered by VESUM because
# many are particles, interjections, or prefix-like dictionary entries.
SHORT_HEADWORD_ALLOWLIST = {
    "а-",
    "ага",
    "аж",
    "ай",
    "ан",
    "ах",
    "ба",
    "бо",
    "ге",
    "гей",
    "дім",
    "ей",
    "ех",
    "же",
    "ім'я",
    "імя",  # _lemma_lookup_key strips apostrophe
    "ніч",
    "ну",
    "о",
    "око",
    "ого",
    "ой",
    "он",
    "от",
    "ото",
    "ох",
    "рік",
    "сік",
    "син",
    "сир",
    "сіль",
    "соль",  # _lemma_lookup_key collapses ь
    "та",
    "ти",
    "тьху",
    "у-",
    "ух",
    "фу",
    "чи",
    "ще",
    "що",
    "як",
}

TEXT_PDF_MASHED_HEADWORDS = {
    "дорізькийізйре",
    "гневразнийодраза",
    "дорізнийчіткий",
}

TEXT_PDF_LEMMA_CORRECTIONS = {
    "сбнце": "сонце",
    "сднце": "сонце",
}

PAGE_RE = re.compile(r"^\d{1,3}$")
WORD_SPLIT_RE = re.compile(r"(?<=[А-Яа-яІіЇїЄєҐґA-Za-z])[-¬]\s*$")
SPACED_WORD_SPLIT_RE = re.compile(r"(?<=[А-Яа-яІіЇїЄєҐґA-Za-z])\s+[-¬]\s*$")
WORD_SPLIT_TEXTPDF_RE = re.compile(r"(?<=[А-Яа-яІіЇїЄєҐґA-Za-z])[-¬|\[]\s*$")
SPACED_WORD_SPLIT_TEXTPDF_RE = re.compile(r"(?<=[А-Яа-яІіЇїЄєҐґA-Za-z])\s+[-¬|\[]\s*$")
SPACE_RE = re.compile(r"[ \t]+")
ENTRY_PUNCT_RE = re.compile(r"[;—]")
ENTRY_PUNCT_TEXTPDF_RE = re.compile(r"[;—«]")
HEAD_END_RE = re.compile(r"[,;(—«]")
CLEAN_LEMMA_MARKER_RE = re.compile(r"[1-9!?-]+$")
COMBINING_ACUTE_RE = re.compile("\u0301")
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


def _looks_like_strong_entry_start_textpdf(line: str) -> bool:
    """Strong text-pdf entry start: punctuated Cyrillic headword or bracketed form."""
    plain = re.match(
        rf"^(?P<head>{TEXTPDF_STRONG_HEADWORD})\s*[,;]\s*(?P<body>[а-яґіїєА-ЯҐІЇЄ\[«].*)",
        line,
    )
    if plain:
        body = plain.group("body").lower()
        return not any(body.startswith(marker) for marker in LEADING_LANGUAGE_ABBREVIATIONS)
    return bool(re.match(r"^\[[а-яґіїєА-ЯҐІЇЄ'’]{2,20}\]?\s*[«,]", line))


def _lemma_lookup_key(lemma: str) -> str:
    key = COMBINING_ACUTE_RE.sub("", lemma.lower())
    key = CLEAN_LEMMA_MARKER_RE.sub("", key)
    return key.strip("[]() ")


def _vesum_db_path() -> Path:
    return REPO / "data" / "vesum.db"


def _vesum_conn() -> sqlite3.Connection | None:
    global _VESUM_CONN, _VESUM_CONN_UNAVAILABLE
    if _VESUM_CONN_UNAVAILABLE:
        return None
    if _VESUM_CONN is not None:
        return _VESUM_CONN
    db_path = _vesum_db_path()
    if not db_path.exists():
        _VESUM_CONN_UNAVAILABLE = True
        return None
    try:
        _VESUM_CONN = sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True)
    except sqlite3.Error:
        _VESUM_CONN_UNAVAILABLE = True
        return None
    return _VESUM_CONN


def _vesum_lemmas() -> frozenset[str]:
    global _VESUM_LEMMAS
    if _VESUM_LEMMAS is not None:
        return _VESUM_LEMMAS
    conn = _vesum_conn()
    if conn is None:
        _VESUM_LEMMAS = frozenset()
        return _VESUM_LEMMAS
    try:
        _VESUM_LEMMAS = frozenset(
            _lemma_lookup_key(row[0])
            for row in conn.execute("SELECT DISTINCT lemma FROM forms")
            if row[0]
        )
    except sqlite3.Error:
        _VESUM_LEMMAS = frozenset()
    return _VESUM_LEMMAS


@lru_cache(maxsize=8192)
def _vesum_has_lemma(lemma: str) -> bool:
    key = _lemma_lookup_key(lemma)
    if not key:
        return False
    lemmas = _vesum_lemmas()
    return key in lemmas


def _is_short_textpdf_headword_allowed(lemma: str) -> bool:
    key = _lemma_lookup_key(lemma)
    if key in TEXT_PDF_FRAGMENT_HEADWORDS:
        return False
    if lemma.lower() in SHORT_HEADWORD_ALLOWLIST or key in SHORT_HEADWORD_ALLOWLIST:
        return True
    # Common prefix-like ESUM headwords such as "а-" are allowlisted above;
    # other 2-3 character non-VESUM starts are overwhelmingly column debris.
    return _vesum_has_lemma(key)


def _has_vesum_boundary_split(lemma: str) -> bool:
    key = _lemma_lookup_key(lemma)
    if len(key) <= 12 or "-" in key or "'" in key or "’" in key:
        return False
    if _vesum_has_lemma(key):
        return False
    for split_at in range(5, len(key) - 4):
        prefix = key[:split_at]
        suffix = key[split_at:]
        if _vesum_has_lemma(prefix) and _vesum_has_lemma(suffix):
            return True
    return False


def _extract_pre_if_html(text: str) -> str:
    """Return `<pre>` content when Archive.org serves an HTML wrapper."""
    if "<pre" not in text[:10_000].lower():
        return text
    match = re.search(r"<pre[^>]*>(.*?)</pre>", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return text
    return html.unescape(match.group(1))


def _strip_front_and_back_matter(lines: list[str]) -> list[str]:
    """Trim cover/foreword/bibliography from the head and Russian
    colophon / errata from the tail.

    Body-start: first line matching BODY_START_RE (a homonym-marked
    short headword like ``а 1 (`` or ``да 1 «``). Volume 1 has ~3,000
    lines of front matter; volumes 2-6 have ~100-250 lines. The earlier
    ``index > 3_000`` cutoff was a volume-1 anti-false-positive guard
    that prevented body-start detection on every other volume — removed.
    If no body-start match exists (vols 3 and 5 open with multi-char
    lemmas instead of homonym-1), ``start`` stays at 0 and the
    paragraph-level entry validator handles filtering downstream.

    Body-end: optional. Only vols 1-3 have the ``АКАДЕМИЯ НАУК
    УКРАИНСКОЙ ССР`` (or vol-3-typo ``СЄР``) header on a single line.
    Vols 4-6 print the same colophon broken across lines, the regex
    misses, and we process to EOF; back-matter prose is filtered by
    the entry validator (incl. lemma sanity gate + bibliography detector
    for text-pdf).

    Note: An earlier iteration of this function tried to detect
    text-pdf colophons in-line by scanning forward for a colophon-marker
    regex (``видавництво|тираж|формат|...``) + a 3-of-5 colophon-shaped
    neighbor check. That over-truncated vol1 by 53% and vol6 by 67%
    because generic Ukrainian words in the marker list (e.g. ``формат``,
    ``тираж``) also appear in etymology bodies, and the 3-of-5 context
    check is too permissive against ESUM's many short continuation
    lines. The lemma sanity gate + bibliography detector handle the
    actual noise correctly without truncating real entries.
    """
    start = 0
    for index, line in enumerate(lines):
        if BODY_START_RE.match(line.strip()):
            start = index
            break
    end = len(lines)
    for index in range(start, len(lines)):
        if BODY_END_RE.match(lines[index].strip()):
            end = index
            break
    return lines[start:end]


def _clean_lines(lines: Iterable[str], source_format: str = "djvutxt") -> list[tuple[int | None, str]]:
    cleaned: list[tuple[int | None, str]] = []
    current_page: int | None = 37
    carry = ""
    textpdf_saw_blank = False

    split_re = WORD_SPLIT_TEXTPDF_RE if source_format == "text-pdf" else WORD_SPLIT_RE
    spaced_split_re = SPACED_WORD_SPLIT_TEXTPDF_RE if source_format == "text-pdf" else SPACED_WORD_SPLIT_RE

    for raw_line in lines:
        line = SPACE_RE.sub(" ", raw_line.rstrip()).strip()
        if PAGE_RE.match(line):
            page = int(line)
            if 1 <= page <= 700:
                current_page = page
                continue

        if not line:
            if source_format == "text-pdf":
                textpdf_saw_blank = True
                continue
            if carry:
                cleaned.append((current_page, carry.strip()))
                carry = ""
            cleaned.append((current_page, ""))
            continue

        if (
            source_format == "text-pdf"
            and textpdf_saw_blank
            and not carry
            and _looks_like_strong_entry_start_textpdf(line)
            and _extract_headword(line, source_format=source_format) is not None
        ):
            cleaned.append((current_page, ""))
        textpdf_saw_blank = False

        if carry:
            # In text-pdf, if a line starts with [ (pipe), it's likely a new entry.
            # Don't merge it into the previous carry, unless it's a hyphenated fragment.
            starts_bracket_entry = (
                source_format == "text-pdf"
                and line.startswith("[")
                and not line.split()[0].rstrip("[").endswith("-")
            )
            starts_plain_entry = (
                source_format == "text-pdf"
                and _looks_like_strong_entry_start_textpdf(line)
                and not split_re.search(carry)
                and not spaced_split_re.search(carry)
            )
            if starts_bracket_entry or starts_plain_entry:
                cleaned.append((current_page, carry.strip()))
                carry = line
            elif split_re.search(carry) or spaced_split_re.search(carry):
                carry = spaced_split_re.sub("", split_re.sub("", carry)) + line
            else:
                carry = f"{carry} {line}"
        else:
            carry = line

        if not split_re.search(carry):
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
    """Extract the canonical headword from the merged entry's head.

    Vol 1 OCR puts the headword followed by inline metadata on the same
    line: ``серце, ст. серьдьце; — р. серце, ...`` — the comma split
    captures only ``серце``. Vols 4-6 print bare headwords on their own
    line, which the parser merges with the next body line:
    ``серце ст. серьдьце; — р. серце, ...`` — without a comma to bound
    the head, the previous version captured the multi-word
    ``серце ст. серьдьце``, which then tripped the ``.``-in-lemma filter
    and the entry got dropped.

    Fix: after the optional comma split, also take only the first
    whitespace-delimited word. The first word is the canonical lemma
    in both layouts.
    """
    first = head.split(",", 1)[0].strip()
    words = first.split()
    if words:
        first = words[0]
    first = first.strip("[]() ")
    first = re.sub(r"\s+[0-9]+$", "", first)
    return SPACE_RE.sub(" ", first).strip().lower()


def _looks_like_ocr_garbage(lemma: str) -> bool:
    """Reject lemmas whose character composition signals OCR noise.

    A clean Ukrainian lemma is mostly Cyrillic letters with optional
    hyphens, apostrophes, and (rare) homonym-digit suffixes. OCR artifacts
    in the multi-volume body — author-name fragments like ``вгйскпег``
    (intended: ``Brückner``), citation tags like ``зі. §г. ii``, and
    column-gutter line-fragments — fail this check.

    Heuristics:
    - At least 75% of letter characters must be Ukrainian Cyrillic.
    - Reject lemmas containing ``§``, ``^``, or ASCII letters following
      an opening Cyrillic letter (signals mid-word OCR break or Latin
      bibliography fragment).
    """
    if not lemma:
        return True
    letters = [c for c in lemma if c.isalpha()]
    if not letters:
        return True
    cyrillic = sum(1 for c in letters if "Ѐ" <= c <= "ӿ")
    if cyrillic / len(letters) < 0.75:
        return True
    return bool(any(ch in lemma for ch in ("§", "^", ".")))


def _is_sane_lemma(lemma: str, source_format: str = "text-pdf") -> bool:
    """Validate lemma quality for text-pdf source to filter out OCR noise.

    Rules:
    - No single-character lemmas (e.g., 'і', 'п', 'т', 'и').
    - No mixed-script or Latin-only entries (e.g., 'ргазкас', 'угаьіе', 'і£і').
    - No digits except as trailing homonym markers 1/2/3 (e.g., reject 'к88', 'з8оіуь').
    - No specific Russian-only headwords ('последний', 'который', 'этот', 'тот').
    - No known garbage lemmas from colophons or OCR artifacts.
    """
    if len(lemma) <= 1:
        # Rule 1: Single char (e.g., 'і', 'п', 'т')
        return False

    if lemma in RUSSIAN_HEADWORDS or lemma in GARBAGE_HEADWORDS:
        # Rule 4 & 5: Russian-only or known garbage headwords
        return False

    if source_format == "text-pdf":
        key = _lemma_lookup_key(lemma)
        key_len = len(key.replace("'", "").replace("’", "").replace("-", ""))
        if 2 <= key_len <= 3 and not _is_short_textpdf_headword_allowed(lemma):
            return False
        if key in TEXT_PDF_MASHED_HEADWORDS or _has_vesum_boundary_split(lemma):
            return False

    # Rule 2: Mixed-script — reject lemmas that contain Basic-Latin letters
    # (these appear when OCR confuses Cyrillic glyphs for Latin lookalikes).
    # Cyrillic Ukrainian + apostrophe + hyphen + stress marks (combining acute
    # U+0301) + homonym digits + entry markers (`!`/`?`) + symbols `§`/`^`/`.`
    # (the latter three rejected separately by `_looks_like_ocr_garbage`) are
    # all legitimate. The narrow Basic-Latin check below catches the real
    # noise without rejecting stress-marked or uppercase lemmas.
    if re.search(r"[A-Za-z£]", lemma):
        return False

    # Rule 3: Digits other than trailing homonym markers (1-9).
    # Reject lemmas with multiple digits ('к88', 'з8оіуь') or non-trailing
    # digits. Allow a single trailing 1-9 as homonym marker.
    digits = re.findall(r"\d", lemma)
    if len(digits) > 1:
        return False
    return not (digits and not re.search(r"[1-9]$", lemma))


def _extract_headword(paragraph: str, source_format: str = "djvutxt") -> str | None:
    match = HEAD_END_RE.search(paragraph)
    if not match:
        return None
    head = paragraph[: match.start()].strip()
    if not 1 <= len(head) <= 80:
        return None
    raw_first = head.split(",", 1)[0].split()[0].strip("[]() ") if head.split() else ""
    if source_format == "text-pdf" and raw_first in {"ЕМ", "Мак"}:
        return None
    lemma = _canonical_lemma(head)
    if source_format == "text-pdf":
        lemma = TEXT_PDF_LEMMA_CORRECTIONS.get(lemma, lemma)
    if not lemma:
        return None
    if "«" in head or "»" in head:
        return None
    if any(lemma.startswith(prefix) for prefix in LEADING_LANGUAGE_ABBREVIATIONS):
        return None
    if len(lemma.split()) > 4:
        return None
    if not re.match(r"^[\[\(]?[А-ЯҐІЇЄа-яґіїє]", lemma):
        return None
    if _looks_like_ocr_garbage(lemma):
        return None
    # Layer 2 (Lemma sanity gate)
    if not _is_sane_lemma(lemma, source_format=source_format):
        return None
    return lemma


def _looks_like_entry_start(paragraph: str, source_format: str = "djvutxt") -> bool:
    # Relax length constraint for text-pdf which has more fragmented lines
    min_len = 20 if source_format == "djvutxt" else 5
    if len(paragraph) < min_len:
        return False
    punct_re = ENTRY_PUNCT_TEXTPDF_RE if source_format == "text-pdf" else ENTRY_PUNCT_RE
    if not punct_re.search(paragraph):
        return False
    return _extract_headword(paragraph, source_format=source_format) is not None


def _looks_like_cross_reference_entry(paragraph: str, source_format: str = "djvutxt") -> bool:
    return "див." in paragraph and _extract_headword(paragraph, source_format=source_format) is not None


def _looks_like_head_candidate(line: str) -> bool:
    if _is_page_header_fragment(line):
        return False
    if not line or line[0] in (")", "]", "»", ".", ",", ";"):
        return False
    head = re.split(r"[,;(—]", line, maxsplit=1)[0].strip()
    lemma = _canonical_lemma(head)
    if not lemma or len(lemma.split()) > 4:
        return False
    if any(lemma.startswith(prefix) for prefix in LEADING_LANGUAGE_ABBREVIATIONS):
        return False
    return bool(re.match(r"^[\[\(]?[А-ЯҐІЇЄа-яґіїє]", lemma))


def _looks_like_complete_entry(paragraph: str, source_format: str = "djvutxt") -> bool:
    if len(paragraph) >= 80:
        return _looks_like_entry_start(paragraph, source_format=source_format)
    if _looks_like_cross_reference_entry(paragraph, source_format=source_format):
        return True
    # For text-pdf, accept shorter entries if they look like real starts (punctuation + headword)
    if source_format == "text-pdf":
        return _looks_like_entry_start(paragraph, source_format=source_format)
    return False


def _is_page_header_fragment(paragraph: str) -> bool:
    """Detect column-pair page running headers and short non-entry artifacts.

    Vols 4-6 print bare headwords on their own line (``серце``,
    ``хата``, ``поле``) with the entry body on the next line. The
    earlier heuristic ``short line + no entry punctuation = page header``
    over-rejected those bare-headword lines and the parser glued them
    onto the previous entry's body — losing thousands of common-word
    entries (вуглець, мова, поле, серце, хата, …) from search_esum.

    Page running headers in this corpus are column-pair lines like
    ``да-ба   даві`` (two headwords side by side from the page's two
    columns). Single-word lines are not running headers — they're real
    headwords. The fix is the ``len(words) < 2`` early-return below.
    """
    if len(paragraph) > 40:
        return False
    if ENTRY_PUNCT_RE.search(paragraph):
        return False
    words = paragraph.split()
    if len(words) < 2:
        # Single word on its own line. Could be a bare-headword line
        # (real entry coming on the next line) — don't reject as page
        # header. Promotion to entry happens via _looks_like_head_candidate
        # plus the body-merge in parse_esum's main loop.
        return False
    if paragraph.lower().startswith(("ще ", "див. ", "пор. ")):
        return False
    if "," in paragraph or "." in paragraph:
        return False
    return bool(re.match(r"^[\[А-Яа-яІіЇїЄєҐґ'’0-9., ]+$", paragraph))


def _extract_cognate_markers(text: str) -> list[str]:
    found = [marker for marker in LANG_MARKERS if marker in text]
    return sorted(set(found), key=found.index)


def _is_likely_abbreviation(text: str) -> bool:
    """Check if a word ending in a period is likely an abbreviation, not an entry end.

    Used in text-pdf mode where blank lines are missing and we rely on punctuation.
    """
    # Specific common ESUM abbreviations
    specific_abbrevs = {
        "див.",
        "пор.",
        "стор.",
        "напр.",
        "очевид.",
        "похідн.",
        "прасл.",
        "болг.",
        "тюрк.",
        "дінд.",
        "прус.",
        "лат.",
        "лит.",
        "псл.",
        "гр.",
    }
    clean = text.lower().rstrip("»\"' ")
    # Match specific ones
    if clean.split()[-1] in specific_abbrevs:
        return True
    # Match general patterns: 1-3 lowercase cyrillic letters or 1-2 uppercase
    return bool(re.search(r"\b[а-яґіїє]{1,3}\.?$", clean) or re.search(r"\b[А-ЯҐІЇЄIVXLCDM]{1,2}\.?$", clean))


def _is_pure_bibliography(text: str) -> bool:
    """Detect if the etymology body is just a bibliography list (OCR noise).

    Example to catch: 'СУМ 9, 763; Бупр. Ш 222; Фасмер Ш 776; Преобр. П 397;'
    Real entries always have prose etymology before any citation cluster.
    """
    if not text:
        return False
    # Identify citation-like chunks: TitleCase or Uppercase abbreviation(s) + space + Roman/Arabic numeral
    # Pattern: ([А-Я]+\.?\s+)+ [IVXLCDM\d]+ \d+(--\d+)?
    chunks = re.findall(r"(?:[А-ЯЁІЇЄҐA-Z][а-яёіїєґa-z]*\.?\s+)+[IVXLCDM\d]+\s*[,;]?\s*\d*(?:--\d+)?", text)
    chunk_len = sum(len(c) for c in chunks)
    # If 80%+ of body characters are within citation-shaped substrings, reject.
    return len(text) > 0 and chunk_len / len(text) > 0.8


def parse_esum(text: str, vol: int, source_format: str = "djvutxt") -> list[dict[str, object]]:
    text = _extract_pre_if_html(text)

    if source_format == "text-pdf":
        text = text.replace("|", "[")
        # Fix uppercase I used as opening bracket: "Інабадкати[" -> "[набадкати["
        text = re.sub(r"\bІ([а-яґіїє]+\[)", r"[\1", text)
        text = re.sub(r"^І([а-яґіїє]+\[)", r"[\1", text, flags=re.MULTILINE)

    lines = _strip_front_and_back_matter(text.splitlines())
    cleaned_lines = _clean_lines(lines, source_format=source_format)

    merged: list[tuple[int, str]] = []
    current_page = 37
    current_parts: list[str] = []
    after_blank = True
    after_end_of_entry = True

    def flush_current() -> None:
        nonlocal current_parts
        if current_parts:
            merged.append((current_page, SPACE_RE.sub(" ", " ".join(current_parts)).strip()))
        current_parts = []

    # Materialize for look-ahead
    rows = list(cleaned_lines)

    def _next_nonblank_index(start: int) -> int | None:
        for j in range(start, len(rows)):
            if rows[j][1]:
                return j
        return None

    def _is_bare_head_only(text: str) -> bool:
        """A line that's a head candidate AND a single short word —
        the shape of running-header lines in vols 4-6. Distinct from
        an inline entry-start which already has body content on the
        same line."""
        if not text or len(text) > 30:
            return False
        if len(text.split()) != 1:
            return False
        # Page headers don't contain typical entry punctuation or meanings
        if any(c in text for c in ",;(—«"):
            return False
        return _looks_like_head_candidate(text)

    i = 0
    while i < len(rows):
        page, line = rows[i]
        if not line:
            after_blank = True
            i += 1
            continue

        is_entry_start = (
            _looks_like_entry_start(line, source_format=source_format)
            or _looks_like_cross_reference_entry(line, source_format=source_format)
            or _looks_like_head_candidate(line)
        )

        # In text-pdf, a line starting with [ (from |) is a strong signal for a new entry.
        # We avoid splitting on variations/fragments that end in a hyphen, or where
        # a meaning is glued immediately to the headword (likely joined fragment).
        is_bracket_strong_start = (
            source_format == "text-pdf"
            and not line.split()[0].rstrip("[").endswith("-")
            and not re.match(r"^\[[а-яґіїє]+«", line)
            and line.startswith("[")
            and _looks_like_head_candidate(line)
        )
        is_plain_strong_after_blank = (
            source_format == "text-pdf"
            and after_blank
            and _looks_like_strong_entry_start_textpdf(line)
            and _extract_headword(line, source_format=source_format) is not None
        )

        condition = (
            (after_blank and is_entry_start)
            if source_format == "djvutxt"
            else (is_bracket_strong_start or is_plain_strong_after_blank or (after_end_of_entry and is_entry_start))
        )

        if condition:
            # Page-running-header detection
            if _is_bare_head_only(line):
                j = _next_nonblank_index(i + 1)
                if j is not None and _is_bare_head_only(rows[j][1]):
                    k = _next_nonblank_index(j + 1)
                    if k is not None:
                        third = rows[k][1]
                        if (
                            third.startswith(("[", "|"))
                            or _is_bare_head_only(third)
                            or _looks_like_entry_start(third, source_format=source_format)
                            or _looks_like_head_candidate(third)
                        ):
                            flush_current()
                            i = j + 1  # skip past both bare headers
                            if source_format == "djvutxt":
                                after_blank = True
                            continue

            flush_current()
            current_page = page or current_page
            current_parts = [line]
        elif current_parts and not _is_page_header_fragment(line):
            current_parts.append(line)

        if source_format == "djvutxt":
            after_blank = False
        else:
            after_blank = False
            clean_end = line.rstrip("»\"' ")
            if clean_end.endswith(".") or clean_end.endswith("!") or clean_end.endswith("?"):
                after_end_of_entry = not _is_likely_abbreviation(clean_end)
            else:
                after_end_of_entry = False

        i += 1
    flush_current()

    entries: list[dict[str, object]] = []
    for page, paragraph in merged:
        if not _looks_like_complete_entry(paragraph, source_format=source_format):
            continue
        lemma = _extract_headword(paragraph, source_format=source_format)
        if lemma is None:
            continue
        # Layer 3 (Bibliography detector)
        if _is_pure_bibliography(paragraph):
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
  GitHub issue #1662; load output with scripts/ingest/esum_ingest.py.
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
    parser.add_argument(
        "--source-format",
        choices=["djvutxt", "text-pdf"],
        default="djvutxt",
        help="Input format: djvutxt (default, for vols 1-3, 6) or text-pdf (vols 4, 5).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.input.exists():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 1
    text = args.input.read_text(encoding="utf-8")
    entries = parse_esum(text, args.vol, source_format=args.source_format)
    if not entries:
        print("No ЕСУМ entries parsed; inspect OCR and segmentation rules.", file=sys.stderr)
        return 1
    count = write_jsonl(entries, args.output)
    print(f"Parsed {count:,} ЕСУМ vol {args.vol} entries -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
