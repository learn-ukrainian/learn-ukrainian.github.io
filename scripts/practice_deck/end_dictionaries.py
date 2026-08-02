"""Textbook end-dictionary / mini-glossary extractor for Atlas practice coverage.

School українська мова textbooks often end with mini-dictionaries (наголоси,
колоритна лексика, фразеологізми, тлумачний додаток). Those sections live in
``textbook_sections`` inside ``data/sources.db``.

This module:

1. Classifies end-glossary sections with deterministic title patterns plus
   optional structural heuristics on ``full_text``.
2. Parses the dominant layouts into structured rows (lemmaPlain, optional
   stress/gloss, multiword flag, rights-safe locator).
3. Emits a compact inventory suitable for the practice coverage path.

Honesty contract
----------------
Lemma+gloss / lemma-only / stress-list rows are **not** blankable cloze
sentences. They feed a clearly named inventory sidecar and optional stress
enrichment when a combining acute is present. Do not invent cloze from
definitions alone.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import unicodedata
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = PROJECT_ROOT / "data" / "lexicon" / "textbook-end-dictionaries"
SCHEMA = "atlas-end-dictionary-inventory"
SCHEMA_VERSION = 1

# Soft hyphens and other OCR joiners that appear mid-word in textbook OCR.
_SOFT_HYPHEN_RE = re.compile(r"[\u00ad\u200b-\u200d\ufeff]")
_WHITESPACE_RE = re.compile(r"\s+")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# Private-use / mojibake stress placeholders seen in some OCR dumps (e.g. U+E02D).
_PUA_RE = re.compile(r"[\ue000-\uf8ff]")
_APOSTROPHE_MAP = str.maketrans({"’": "'", "ʼ": "'", "ʻ": "'", "＇": "'", "`": "'"})
_DASH_CHARS = "\u2010\u2011\u2012\u2013\u2014\u2015\u2212—"
_EMDASH_SPLIT_RE = re.compile(rf"\s*[{_DASH_CHARS}-]{{1,2}}\s*")
_LETTER_HEADER_RE = re.compile(
    r"^\s*(?:[А-ЩЬЮЯЄІЇҐ]|[A-Z]|Є|І|Ї|Ґ)\s*$",
)
_PAGE_ONLY_RE = re.compile(r"^\s*\d{1,4}\s*$")
_TITLE_NOISE_RE = re.compile(
    r"(?i)^\s*(?:короткий\s+словник|словничок|словники|тлумачний\s+словник|"
    r"з\s+тлумачного\s+словника|додаток\s+\d+|зміст|"
    r"орфографічний\s+словничок|словник\s+термінів).*$"
)
_BULLET_RE = re.compile(r"^[\s•·▪◦●○\t]+")
_UK_LEMMA_RE = re.compile(
    r"^[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+(?:[ʼ'’-][А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+)*$"
)
_UK_TOKEN_RE = re.compile(
    r"[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+(?:[ʼ'’-][А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+)*"
)
_ACADEMIC_HEAD_RE = re.compile(
    r"^(?P<head>[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ][А-ЩЬЮЯЄІЇҐа-щьюяєіїґʼ'’-]*)"
    r"(?:,\s*[^\.]{0,80})?"
    r"(?:\.\s+|\s+)(?P<gloss>.+)$",
    re.DOTALL,
)
# Packed academic mini-dict: ``lemma, -morph, POS. Gloss. nextlemma, …``
# Headwords are lowercase; capitalized tokens after ``.`` are gloss prose.
_ACADEMIC_MORPH_RE = re.compile(
    r"(?:(?<=[.!?…;])\s+|^)"
    r"(?P<head>[а-яєіїґ][а-яєіїґʼ'’-]{2,40})"
    r"(?:,\s*(?:-[а-яєіїґʼ'0-9-]+|[а-яєіїґʼ'\-\s,]{1,40})){0,6}"
    r"\.\s+(?P<gloss>[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ][^.]{2,}(?:\.\s+\d+\.[^.]*)*)"
)
# Cleaner ``Абрис. Обриси предмета…`` rows (capitalized head + period).
_ACADEMIC_SIMPLE_RE = re.compile(
    r"(?:(?<=[.!?…])\s+|^)"
    r"(?P<head>[А-ЩЬЮЯЄІЇҐ][а-щьюяєіїґʼ'’-]{2,40})"
    r"\.\s+(?P<gloss>[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ][^.]{2,})"
)
# Latin/OCR stress lookalikes that corrupt synonym heads (åîóàѕÞÈ etc.).
_OCR_LATIN_JUNK_RE = re.compile(r"[A-Za-zÀ-ÿÞþÈèÅåÎîÓóÔô]")
_MIN_LEMMA_LEN = 3
_ABBREV_HEADS = frozenset(
    {
        "ч",
        "ж",
        "с",
        "мн",
        "присл",
        "прикм",
        "док",
        "недок",
        "муз",
        "перен",
        "нар",
        "поет",
        "заст",
        "розм",
        "діал",
        "книжн",
        "ірон",
        "жарт",
        "знев",
        "лайл",
        "фам",
        "спец",
        "вульг",
    }
)
_COMBINING_ACUTE = "\u0301"
_UKRMOVA_SOURCE_RE = re.compile(
    r"(?i)(?:ukrmova|ukrajinska[-_]?mova|ukrajinska_mova)"
)

# Title → layout kind. First match wins.
_TITLE_KIND_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("stress", re.compile(r"(?i)(?:словник|словничок).{0,20}наголос")),
    ("color_lexicon", re.compile(r"(?i)словник.{0,40}колорит")),
    ("phraseology", re.compile(r"(?i)словник.{0,40}фразеолог")),
    ("paronym", re.compile(r"(?i)словничок.{0,20}паронім")),
    ("synonym", re.compile(r"(?i)словничок.{0,20}синонім")),
    ("orthography", re.compile(r"(?i)орфографічн\w+\s+словничок")),
    ("gloss", re.compile(r"(?i)(?:тлумачн\w+\s+словник|з\s+тлумачного\s+словника)")),
    ("terms", re.compile(r"(?i)^словник\s+термінів")),
    ("stress", re.compile(r"(?i)короткий\s+словник\s+наголос")),
)

# Exclude lesson prose about dictionaries / TOC noise.
_TITLE_EXCLUDE_RE = re.compile(
    r"(?i)(?:§\s*\d|орфоепічн\w+\s+помилка|порядок\s+слів|"
    r"логічний\s+наголос|не\s+користуючись\s+словником|"
    r"за\s+допомогою\s+словник|витлумачте\s+вислів|"
    r"словник\s+—\s+це|сторінка\s+\d)"
)


@dataclass(frozen=True)
class EndDictionarySection:
    """One classified textbook end-glossary section (no full_text)."""

    section_id: int
    grade: int | None
    section_title: str
    source_file: str
    page_start: int | None
    page_end: int | None
    char_count: int
    kind: str
    layout: str
    match_reason: str

    @property
    def locator(self) -> str:
        return f"textbook_sections:{self.section_id}"


@dataclass(frozen=True)
class EndDictionaryEntry:
    """One parsed end-dictionary row."""

    lemma_plain: str
    section_id: int
    grade: int | None
    source_file: str
    kind: str
    layout: str
    locator: str
    stress: str | None = None
    gloss: str | None = None
    multiword: bool = False

    def to_json(self) -> dict[str, Any]:
        row: dict[str, Any] = {
            "lemmaPlain": self.lemma_plain,
            "sectionId": self.section_id,
            "grade": self.grade,
            "sourceFile": self.source_file,
            "kind": self.kind,
            "layout": self.layout,
            "locator": self.locator,
            "multiword": self.multiword,
        }
        if self.stress:
            row["stress"] = self.stress
        if self.gloss:
            row["gloss"] = self.gloss
        return row


def resolve_sources_db(explicit: Path | None = None) -> Path:
    """Resolve sources.db from the worktree or a parent checkout."""
    if explicit is not None:
        return explicit
    for parent in (PROJECT_ROOT, *PROJECT_ROOT.parents):
        candidate = parent / "data" / "sources.db"
        if candidate.is_file():
            return candidate
    return PROJECT_ROOT / "data" / "sources.db"


def normalize_surface(text: str) -> str:
    """Normalize OCR noise while preserving combining acute stress marks."""
    value = unicodedata.normalize("NFC", text or "")
    value = _SOFT_HYPHEN_RE.sub("", value)
    value = _PUA_RE.sub("-", value)
    value = _CONTROL_RE.sub("", value)
    value = value.translate(_APOSTROPHE_MAP)
    value = _WHITESPACE_RE.sub(" ", value).strip()
    return value


def strip_stress(text: str) -> str:
    return text.replace(_COMBINING_ACUTE, "")


def _is_ukrmova_source(source_file: str) -> bool:
    return bool(_UKRMOVA_SOURCE_RE.search(source_file or ""))


def classify_section_title(title: str) -> tuple[str, str] | None:
    """Return (kind, match_reason) for an end-glossary title, else None."""
    cleaned = normalize_surface(title)
    if not cleaned or _TITLE_EXCLUDE_RE.search(cleaned):
        return None
    for kind, pattern in _TITLE_KIND_PATTERNS:
        if pattern.search(cleaned):
            return kind, f"title:{pattern.pattern}"
    return None


def infer_layout(kind: str, full_text: str, *, section_title: str = "") -> str:
    """Pick a parser layout from kind + cheap structural heuristics."""
    text = normalize_surface(full_text)
    title = normalize_surface(section_title)
    lines = [line.strip() for line in (full_text or "").splitlines() if line.strip()]
    short_lines = sum(1 for line in lines if len(normalize_surface(line)) <= 40)
    short_ratio = (short_lines / len(lines)) if lines else 0.0
    emdash_hits = sum(1 for ch in text if ch in _DASH_CHARS or ch == "—")
    if kind == "stress":
        return "stress_list"
    if kind == "color_lexicon":
        return "word_list"
    if kind == "phraseology":
        return "phrase_emdash"
    if kind == "paronym":
        return "paronym_block"
    if kind == "gloss" and re.search(r"(?i)^з\s+тлумачного\s+словника", title):
        # Packed academic morphology rows; em-dashes are rare prose dashes.
        return "academic_morph"
    if kind in {"gloss", "terms"}:
        if emdash_hits >= 5 and kind == "terms":
            return "gloss_emdash"
        if emdash_hits >= 8 and "—" in (full_text or ""):
            return "gloss_emdash"
        # Avramenko mini glosses use ``Lemma — gloss``; Voron uses ``Lemma. Gloss``.
        if emdash_hits >= 5:
            return "gloss_emdash"
        simple_hits = len(_ACADEMIC_SIMPLE_RE.findall(text))
        if simple_hits >= 5:
            return "academic_simple"
        return "academic_morph"
    if kind == "synonym":
        return "synonym_list"
    if kind == "orthography":
        return "word_list" if short_ratio >= 0.5 else "stress_list"
    return "word_list" if short_ratio >= 0.55 else "gloss_emdash"


def classify_section_row(row: Mapping[str, Any]) -> EndDictionarySection | None:
    """Classify one textbook_sections row as an end-glossary section."""
    source_file = str(row.get("source_file") or "")
    if not _is_ukrmova_source(source_file):
        return None
    title = str(row.get("section_title") or "")
    matched = classify_section_title(title)
    if matched is None:
        return None
    kind, reason = matched
    full_text = str(row.get("full_text") or "")
    layout = infer_layout(kind, full_text, section_title=title)
    grade_raw = row.get("grade")
    grade = int(grade_raw) if isinstance(grade_raw, int) or str(grade_raw).isdigit() else None
    page_start = row.get("page_start")
    page_end = row.get("page_end")
    return EndDictionarySection(
        section_id=int(row["section_id"]),
        grade=grade,
        section_title=title,
        source_file=source_file,
        page_start=int(page_start) if page_start is not None else None,
        page_end=int(page_end) if page_end is not None else None,
        char_count=len(full_text),
        kind=kind,
        layout=layout,
        match_reason=reason,
    )


def enumerate_end_dictionary_sections(
    conn: sqlite3.Connection,
) -> list[EndDictionarySection]:
    """Deterministic SQL + title classifier over textbook_sections."""
    rows = conn.execute(
        """
        SELECT section_id, grade, section_title, source_file,
               page_start, page_end, full_text
        FROM textbook_sections
        WHERE source_file LIKE '%ukrmova%'
           OR source_file LIKE '%ukrajinska-mova%'
           OR source_file LIKE '%ukrajinska_mova%'
        ORDER BY grade, section_id
        """
    ).fetchall()
    columns = [
        "section_id",
        "grade",
        "section_title",
        "source_file",
        "page_start",
        "page_end",
        "full_text",
    ]
    sections: list[EndDictionarySection] = []
    seen_ids: set[int] = set()
    for raw in rows:
        payload = dict(zip(columns, raw, strict=True))
        section = classify_section_row(payload)
        if section is None or section.section_id in seen_ids:
            continue
        seen_ids.add(section.section_id)
        sections.append(section)
    return sections


def _skip_noise_line(line: str) -> bool:
    cleaned = normalize_surface(line)
    if not cleaned:
        return True
    if _PAGE_ONLY_RE.match(cleaned):
        return True
    if _LETTER_HEADER_RE.match(cleaned):
        return True
    if _TITLE_NOISE_RE.match(cleaned):
        return True
    if cleaned.startswith("•") and "тлумачним словником" in cleaned.casefold():
        return True
    return cleaned.casefold().startswith("за тлумачним")


def _lemma_from_token(token: str) -> tuple[str, str | None] | None:
    cleaned = normalize_surface(token)
    cleaned = _BULLET_RE.sub("", cleaned)
    # Drop parenthetical sense notes: "вигода (користь)"
    if "(" in cleaned:
        cleaned = cleaned.split("(", 1)[0].strip()
    # Keep first alternative of "гальмо, гальма"
    if "," in cleaned:
        cleaned = cleaned.split(",", 1)[0].strip()
    if not cleaned:
        return None
    stressed = cleaned if _COMBINING_ACUTE in cleaned else None
    plain = strip_stress(cleaned).casefold()
    if not _UK_LEMMA_RE.match(plain):
        return None
    if len(plain) < _MIN_LEMMA_LEN and plain not in {"я", "ти", "ми", "ви"}:
        return None
    if plain in _ABBREV_HEADS:
        return None
    return plain, stressed


def _repair_ocr_letters(token: str) -> str | None:
    """Return token only when free of Latin OCR junk; else skip as residual."""
    if _OCR_LATIN_JUNK_RE.search(token):
        return None
    return token


def parse_word_list(text: str) -> list[tuple[str, str | None]]:
    """Parse one-lemma-per-line mini-dictionaries (stress / color / ortho)."""
    out: list[tuple[str, str | None]] = []
    seen: set[str] = set()
    for raw_line in (text or "").splitlines():
        if _skip_noise_line(raw_line):
            continue
        line = normalize_surface(_BULLET_RE.sub("", raw_line))
        # Instruction lines / TOC bleed
        if len(line) > 60 and " " in line and _COMBINING_ACUTE not in line:
            continue
        if line.casefold().startswith("зміст"):
            break
        parsed = _lemma_from_token(line)
        if parsed is None:
            continue
        plain, stressed = parsed
        if plain in seen:
            continue
        seen.add(plain)
        out.append((plain, stressed))
    return out


def parse_gloss_emdash(text: str) -> list[tuple[str, str | None, str, bool]]:
    """Parse ``Lemma — gloss`` / ``Phrase — gloss`` blocks."""
    out: list[tuple[str, str | None, str, bool]] = []
    seen: set[str] = set()
    buffer = ""
    for raw_line in (text or "").splitlines():
        if _skip_noise_line(raw_line):
            buffer = ""
            continue
        line = normalize_surface(_BULLET_RE.sub("", raw_line))
        if line.casefold().startswith("зміст"):
            break
        if _LETTER_HEADER_RE.match(line):
            buffer = ""
            continue
        if buffer:
            line = f"{buffer} {line}"
            buffer = ""
        if not _EMDASH_SPLIT_RE.search(line):
            # Soft-wrap continuation of previous unfinished entry is rare at
            # line start; keep short leftovers only when previous needed glue.
            buffer = (
                line
                if len(line) <= 40 and not line.endswith(".") and "словник" not in line.casefold()
                else ""
            )
            continue
        parts = _EMDASH_SPLIT_RE.split(line, maxsplit=1)
        if len(parts) != 2:
            continue
        left, gloss = parts[0].strip(), parts[1].strip()
        if not left or not gloss:
            continue
        if "словник" in left.casefold():
            # Title bleed: keep the final headword after the mini-dict heading.
            left = left.split()[-1] if left.split() else left
        tokens = _UK_TOKEN_RE.findall(left)
        if not tokens:
            continue
        # Cap runaway title/prose left-hand sides.
        if len(tokens) > 8:
            continue
        plain = strip_stress(normalize_surface(" ".join(tokens))).casefold()
        stressed = left if _COMBINING_ACUTE in left else None
        multiword = len(tokens) > 1
        if not multiword:
            single = _lemma_from_token(tokens[0])
            if single is None:
                continue
            plain, stressed = single
        if plain in _ABBREV_HEADS or plain in seen:
            continue
        seen.add(plain)
        out.append((plain, stressed, gloss[:400], multiword))
    return out


def parse_academic_gloss(text: str, *, style: str = "morph") -> list[tuple[str, str | None, str, bool]]:
    """Parse academic mini-dict rows (morph-packed or simple ``Lemma. Gloss``)."""
    out: list[tuple[str, str | None, str, bool]] = []
    seen: set[str] = set()
    lines: list[str] = []
    for raw_line in (text or "").splitlines():
        if _skip_noise_line(raw_line):
            continue
        line = normalize_surface(_BULLET_RE.sub("", raw_line))
        if line.casefold().startswith("зміст"):
            break
        if _LETTER_HEADER_RE.match(line) and len(line) <= 2:
            continue
        lines.append(line)
    compacted = " ".join(lines)
    pattern = _ACADEMIC_SIMPLE_RE if style == "simple" else _ACADEMIC_MORPH_RE
    for match in pattern.finditer(compacted):
        head = match.group("head")
        gloss = normalize_surface(match.group("gloss"))
        # Reject POS abbreviations mistaken for heads.
        if head.casefold() in _ABBREV_HEADS:
            continue
        parsed = _lemma_from_token(head)
        if parsed is None or not gloss or len(gloss) < 3:
            continue
        plain, stressed = parsed
        if plain in seen:
            continue
        seen.add(plain)
        out.append((plain, stressed, gloss[:400], False))
    if out:
        return out
    for line in lines:
        match = _ACADEMIC_HEAD_RE.match(line)
        if not match:
            continue
        parsed = _lemma_from_token(match.group("head"))
        gloss = normalize_surface(match.group("gloss"))
        if parsed is None or not gloss:
            continue
        plain, stressed = parsed
        if plain in seen:
            continue
        seen.add(plain)
        out.append((plain, stressed, gloss[:400], False))
    return out


def parse_paronym_block(text: str) -> list[tuple[str, str | None, str | None, bool]]:
    """Parse ``А // Б`` paronym pairs with following gloss lines."""
    out: list[tuple[str, str | None, str | None, bool]] = []
    seen: set[str] = set()
    for raw_line in (text or "").splitlines():
        if _skip_noise_line(raw_line):
            continue
        line = normalize_surface(raw_line)
        if "//" in line and len(line) < 80:
            left, _, right = line.partition("//")
            for side in (left, right):
                parsed = _lemma_from_token(side.strip())
                if parsed is None:
                    continue
                plain, stressed = parsed
                if plain in seen:
                    continue
                seen.add(plain)
                out.append((plain, stressed, None, False))
            continue
        # ``Lemma – gloss`` sense lines
        if _EMDASH_SPLIT_RE.search(line) or " – " in line or " - " in line:
            for plain, stressed, gloss, multiword in parse_gloss_emdash(line):
                if plain in seen:
                    continue
                seen.add(plain)
                out.append((plain, stressed, gloss, multiword))
    return out


def parse_synonym_list(text: str) -> list[tuple[str, str | None, str, bool]]:
    """Parse uppercase-head synonym rows: ``LEMMA, syn1, syn2…``.

    OCR-corrupted heads (Latin lookalike vowels) are repaired when possible;
    irreparable fragments are skipped and counted as layout residual.
    """
    out: list[tuple[str, str | None, str, bool]] = []
    seen: set[str] = set()
    for raw_line in (text or "").splitlines():
        if _skip_noise_line(raw_line):
            continue
        line = normalize_surface(raw_line)
        if "," not in line:
            continue
        head, _, rest = line.partition(",")
        head_raw = head.strip()
        repaired = _repair_ocr_letters(head_raw)
        if repaired is None:
            continue
        head = repaired
        tokens = _UK_TOKEN_RE.findall(head)
        if not tokens:
            continue
        candidate = tokens[0]
        letters = [ch for ch in candidate if ch.isalpha()]
        if not letters:
            continue
        upper_ratio = sum(1 for ch in letters if ch.isupper()) / len(letters)
        if upper_ratio < 0.6:
            continue
        plain = strip_stress(candidate).casefold()
        if len(plain) < _MIN_LEMMA_LEN or not _UK_LEMMA_RE.match(plain) or plain in seen:
            continue
        seen.add(plain)
        gloss = normalize_surface(rest)[:400]
        out.append((plain, None, gloss, False))
    return out


def parse_section_entries(
    section: EndDictionarySection,
    full_text: str,
) -> list[EndDictionaryEntry]:
    """Parse one section into structured inventory rows."""
    layout = section.layout
    rows: list[EndDictionaryEntry] = []
    if layout in {"stress_list", "word_list"}:
        for plain, stressed in parse_word_list(full_text):
            rows.append(
                EndDictionaryEntry(
                    lemma_plain=plain,
                    stress=stressed,
                    section_id=section.section_id,
                    grade=section.grade,
                    source_file=section.source_file,
                    kind=section.kind,
                    layout=layout,
                    locator=section.locator,
                    multiword=False,
                )
            )
        return rows
    if layout == "phrase_emdash":
        parsed = parse_gloss_emdash(full_text)
        for plain, stressed, gloss, multiword in parsed:
            rows.append(
                EndDictionaryEntry(
                    lemma_plain=plain,
                    stress=stressed,
                    gloss=gloss,
                    multiword=True if multiword else (" " in plain),
                    section_id=section.section_id,
                    grade=section.grade,
                    source_file=section.source_file,
                    kind=section.kind,
                    layout=layout,
                    locator=section.locator,
                )
            )
        return rows
    if layout == "gloss_emdash":
        for plain, stressed, gloss, multiword in parse_gloss_emdash(full_text):
            rows.append(
                EndDictionaryEntry(
                    lemma_plain=plain,
                    stress=stressed,
                    gloss=gloss,
                    multiword=multiword,
                    section_id=section.section_id,
                    grade=section.grade,
                    source_file=section.source_file,
                    kind=section.kind,
                    layout=layout,
                    locator=section.locator,
                )
            )
        return rows
    if layout == "academic_gloss":
        parsed_rows = parse_academic_gloss(full_text, style="morph")
        for plain, stressed, gloss, multiword in parsed_rows:
            rows.append(
                EndDictionaryEntry(
                    lemma_plain=plain,
                    stress=stressed,
                    gloss=gloss,
                    multiword=multiword,
                    section_id=section.section_id,
                    grade=section.grade,
                    source_file=section.source_file,
                    kind=section.kind,
                    layout=layout,
                    locator=section.locator,
                )
            )
        return rows
    if layout == "academic_morph":
        for plain, stressed, gloss, multiword in parse_academic_gloss(full_text, style="morph"):
            rows.append(
                EndDictionaryEntry(
                    lemma_plain=plain,
                    stress=stressed,
                    gloss=gloss,
                    multiword=multiword,
                    section_id=section.section_id,
                    grade=section.grade,
                    source_file=section.source_file,
                    kind=section.kind,
                    layout=layout,
                    locator=section.locator,
                )
            )
        return rows
    if layout == "academic_simple":
        for plain, stressed, gloss, multiword in parse_academic_gloss(full_text, style="simple"):
            rows.append(
                EndDictionaryEntry(
                    lemma_plain=plain,
                    stress=stressed,
                    gloss=gloss,
                    multiword=multiword,
                    section_id=section.section_id,
                    grade=section.grade,
                    source_file=section.source_file,
                    kind=section.kind,
                    layout=layout,
                    locator=section.locator,
                )
            )
        return rows
    if layout == "paronym_block":
        for plain, stressed, gloss, multiword in parse_paronym_block(full_text):
            rows.append(
                EndDictionaryEntry(
                    lemma_plain=plain,
                    stress=stressed,
                    gloss=gloss or None,
                    multiword=multiword,
                    section_id=section.section_id,
                    grade=section.grade,
                    source_file=section.source_file,
                    kind=section.kind,
                    layout=layout,
                    locator=section.locator,
                )
            )
        return rows
    if layout == "synonym_list":
        for plain, stressed, gloss, multiword in parse_synonym_list(full_text):
            rows.append(
                EndDictionaryEntry(
                    lemma_plain=plain,
                    stress=stressed,
                    gloss=gloss,
                    multiword=multiword,
                    section_id=section.section_id,
                    grade=section.grade,
                    source_file=section.source_file,
                    kind=section.kind,
                    layout=layout,
                    locator=section.locator,
                )
            )
        return rows
    # Unknown layout residual: still try word-list salvage.
    for plain, stressed in parse_word_list(full_text):
        rows.append(
            EndDictionaryEntry(
                lemma_plain=plain,
                stress=stressed,
                section_id=section.section_id,
                grade=section.grade,
                source_file=section.source_file,
                kind=section.kind,
                layout="word_list_fallback",
                locator=section.locator,
            )
        )
    return rows


def extract_all(
    conn: sqlite3.Connection,
) -> tuple[list[EndDictionarySection], list[EndDictionaryEntry]]:
    """Enumerate sections and parse every classified end-dictionary."""
    sections = enumerate_end_dictionary_sections(conn)
    by_id = {section.section_id: section for section in sections}
    if not by_id:
        return sections, []
    placeholders = ",".join("?" for _ in by_id)
    text_rows = conn.execute(
        f"""
        SELECT section_id, full_text
        FROM textbook_sections
        WHERE section_id IN ({placeholders})
        """,
        tuple(by_id),
    ).fetchall()
    entries: list[EndDictionaryEntry] = []
    for section_id, full_text in text_rows:
        section = by_id[int(section_id)]
        entries.extend(parse_section_entries(section, full_text or ""))
    return sections, entries


def stress_overlay_from_entries(
    entries: Sequence[EndDictionaryEntry],
) -> dict[str, dict[str, str]]:
    """Map lemmaPlain → stressed form for entries that carry combining acute.

    OCR stress mini-dicts usually lack real acutes; those lemmas are inventory-
    only and intentionally absent from this overlay.
    """
    overlay: dict[str, dict[str, str]] = {}
    for entry in entries:
        if not entry.stress or _COMBINING_ACUTE not in entry.stress:
            continue
        plain = entry.lemma_plain
        if plain in overlay:
            continue
        overlay[plain] = {
            "form": entry.stress,
            "source": f"textbook-end-dictionary:{entry.locator}",
        }
    return overlay


def load_inventory(path: Path) -> dict[str, Any]:
    """Load a committed atlas-end-dictionary-inventory payload."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise ValueError(f"{path} must use {SCHEMA} schema")
    return payload


def read_end_dictionary_stress_overlay(path: Path | None) -> dict[str, dict[str, str]]:
    """Load stress overlay from a committed inventory file."""
    if path is None or not path.exists():
        return {}
    payload = load_inventory(path)
    entries_raw = payload.get("entries")
    if not isinstance(entries_raw, list):
        return {}
    overlay: dict[str, dict[str, str]] = {}
    for row in entries_raw:
        if not isinstance(row, dict):
            continue
        plain = str(row.get("lemmaPlain") or "").casefold()
        stress = row.get("stress")
        locator = str(row.get("locator") or "")
        if not plain or not isinstance(stress, str) or _COMBINING_ACUTE not in stress:
            continue
        if plain in overlay:
            continue
        overlay[plain] = {
            "form": stress,
            "source": f"textbook-end-dictionary:{locator}" if locator else "textbook-end-dictionary",
        }
    return overlay


def coverage_intersection_report(
    practice_lemmas_by_level: Mapping[str, set[str]],
    cloze_eligible_by_level: Mapping[str, set[str]],
    entries: Sequence[EndDictionaryEntry] | Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Intersect practice residual with end-dictionary lemmas (tool proof)."""
    end_lemmas: set[str] = set()
    for entry in entries:
        if isinstance(entry, EndDictionaryEntry):
            end_lemmas.add(entry.lemma_plain)
        else:
            plain = str(entry.get("lemmaPlain") or "").casefold()
            if plain:
                end_lemmas.add(plain)
    levels: dict[str, Any] = {}
    for level, practice in sorted(practice_lemmas_by_level.items()):
        eligible = cloze_eligible_by_level.get(level, set())
        residual = practice - eligible
        hit = residual & end_lemmas
        levels[level] = {
            "practiceLexemes": len(practice),
            "clozeEligible": len(eligible),
            "residual": len(residual),
            "residualInEndDictionary": len(hit),
            "coverage": round(len(eligible) / len(practice), 4) if practice else 0.0,
        }
    return {
        "endDictionaryUniqueLemmas": len(end_lemmas),
        "levels": levels,
        "note": (
            "residualInEndDictionary counts lemma-only / gloss / stress-list hits; "
            "these do not unlock cloze without a blankable public sentence."
        ),
    }


def build_inventory_payload(
    sections: Sequence[EndDictionarySection],
    entries: Sequence[EndDictionaryEntry],
) -> dict[str, Any]:
    kind_counts = Counter(section.kind for section in sections)
    layout_counts = Counter(section.layout for section in sections)
    entry_kind_counts = Counter(entry.kind for entry in entries)
    stressed = sum(1 for entry in entries if entry.stress)
    glossed = sum(1 for entry in entries if entry.gloss)
    multiword = sum(1 for entry in entries if entry.multiword)
    return {
        "schema": SCHEMA,
        "schemaVersion": SCHEMA_VERSION,
        "source": "textbook_sections",
        "scope": "ukrmova/ukrajinska-mova end-glossary title classifier",
        "counts": {
            "sections": len(sections),
            "entries": len(entries),
            "uniqueLemmas": len({entry.lemma_plain for entry in entries}),
            "entriesWithStress": stressed,
            "entriesWithGloss": glossed,
            "multiwordEntries": multiword,
            "sectionsByKind": dict(sorted(kind_counts.items())),
            "sectionsByLayout": dict(sorted(layout_counts.items())),
            "entriesByKind": dict(sorted(entry_kind_counts.items())),
        },
        "clozePolicy": {
            "fakeClozeFromDefinitions": False,
            "blankableSentenceRequired": True,
            "wireTarget": "inventory_sidecar_and_optional_stress_overlay",
        },
        "layoutResidual": {
            "academic_morph_packed_ocr": (
                "Grade-9 «З тлумачного словника» is densely packed morphology; "
                "parser recovers high-precision rows only (not full section recall)."
            ),
            "synonym_orthography_ocr": (
                "Some Zabolotnyi appendices use Latin lookalike OCR for stress; "
                "corrupted heads are skipped rather than repaired into wrong lemmas."
            ),
            "stress_lists_without_acute": (
                "Stress mini-dicts list hard-stress lemmas but OCR lacks combining "
                "acute; they enrich inventory priority, not stress forms."
            ),
        },
        "sections": [
            {
                "sectionId": section.section_id,
                "grade": section.grade,
                "sectionTitle": section.section_title,
                "sourceFile": section.source_file,
                "pageStart": section.page_start,
                "pageEnd": section.page_end,
                "charCount": section.char_count,
                "kind": section.kind,
                "layout": section.layout,
                "locator": section.locator,
                "matchReason": section.match_reason,
            }
            for section in sections
        ],
        "entries": [entry.to_json() for entry in entries],
    }


def write_inventory(payload: Mapping[str, Any], out_dir: Path) -> tuple[Path, Path]:
    """Write full inventory JSON plus a sections-only summary (no entries)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = out_dir / "inventory.json"
    sections_path = out_dir / "sections.json"
    inventory_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    summary = {
        "schema": SCHEMA,
        "schemaVersion": SCHEMA_VERSION,
        "counts": payload.get("counts"),
        "clozePolicy": payload.get("clozePolicy"),
        "layoutResidual": payload.get("layoutResidual"),
        "sections": payload.get("sections"),
    }
    sections_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return inventory_path, sections_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources-db", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)
    sources_db = resolve_sources_db(args.sources_db)
    if not sources_db.is_file():
        raise SystemExit(f"sources.db not found: {sources_db}")
    conn = sqlite3.connect(f"file:{sources_db}?mode=ro", uri=True)
    try:
        sections, entries = extract_all(conn)
    finally:
        conn.close()
    payload = build_inventory_payload(sections, entries)
    inventory_path, sections_path = write_inventory(payload, args.out_dir)
    counts = payload["counts"]
    print(
        "end-dictionaries "
        f"sections={counts['sections']} entries={counts['entries']} "
        f"uniqueLemmas={counts['uniqueLemmas']} "
        f"withStress={counts['entriesWithStress']} "
        f"withGloss={counts['entriesWithGloss']}"
    )
    print(f"wrote {inventory_path}")
    print(f"wrote {sections_path}")
    print("sectionsByKind", json.dumps(counts["sectionsByKind"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
