#!/usr/bin/env python3
"""Anna Ohoiko quality textbook enrichment for Word Atlas (#7452).

Extracts learner English glosses and cited bilingual example sentences from
in-scope Ohoiko textbooks in ``data/sources.db`` (``anna-ohoiko-1000-words-2nd-ed``
and ``anna-ohoiko-500-verbs``), and merges them onto Atlas entries:
- Sets ``enrichment.translation`` to ``{en: [gloss, ...], source: "learner_english_gloss"}``
  with Anna's learner gloss first, preserving existing dictionary EN terms only when they
  represent a distinct sense.
- Sets ``enrichment.examples`` to ``[{uk, en, source: "Anna Ohoiko", locator}]`` (<=2).
- Re-enriches empty #7397 heads of Ohoiko provenance (e.g. ``так само``, ``забоятися``, etc.).
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lexicon.lemma_normalization import strip_acute_stress

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "sources.db"
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.json"

SOURCE_1000_WORDS = "anna-ohoiko-1000-words-2nd-ed"
SOURCE_500_VERBS = "anna-ohoiko-500-verbs"
SOURCE_LABEL_GLOSS = "learner_english_gloss"
SOURCE_LABEL_AUTHOR = "Anna Ohoiko"

CYRILLIC_CHAR_RE = re.compile(r"[\u0400-\u04ff\u0301]")
LATIN_CHAR_RE = re.compile(r"[a-zA-Z]")
TWO_COL_BOUNDARY_RE = re.compile(
    r"(?<=[\u0400-\u04ff\u0301.?!»\)\x27\x22”’])\s*(?=[A-Z\x22“«\x270-9])"
)

HEADS_7397 = frozenset(
    {
        "виходити заміж",
        "день тижня",
        "картопля фрі",
        "перед тим як",
        "сільське господарство",
        "так само",
        "такий самий",
        "час від часу",
        "забоятися",
    }
)

# Sentence-final punctuation (including a bare colon, which closes a
# handful of genuinely complete 500-verbs examples that introduce a short
# list, e.g. "Voiced and unvoiced consonants form pairs:"). Used to decide
# whether a candidate 500-verbs example needs a wrapped-continuation merge.
TERMINAL_PUNCT_500_VERBS = (".", "?", "!", "…", ":", "”", "»", '"')

FORBIDDEN_EXAMPLE_KEYWORDS = frozenset(
    {
        "stems:",
        "недоконаний",
        "доконаний",
        "особа",
        "теперішній",
        "минулий",
        "майбутній",
        "наказовий",
        "present tense",
        "past tense",
        "future tense",
        "imperative",
        "imperfective",
        "perfective",
        "conjugation:",
    }
)


@dataclass(frozen=True)
class ParsedOhoikoEntry:
    """Parsed representation of a single Ohoiko textbook chunk."""

    source_file: str
    entry_number: int
    locator: str
    lemmas: list[str]
    gloss: str
    example: dict[str, str] | None  # {"uk": ..., "en": ..., "source": ..., "locator": ...}


def is_plausible_example(uk: str, en: str) -> bool:
    """Validate that a candidate UK/EN pair is a genuine, plausible example sentence."""
    if not uk or not en:
        return False
    uk = uk.strip()
    en = en.strip()
    if len(uk) < 2 or len(en) < 2:
        return False
    if not CYRILLIC_CHAR_RE.search(uk) or not LATIN_CHAR_RE.search(en):
        return False

    uk_lower = uk.lower()
    en_lower = en.lower()
    for kw in FORBIDDEN_EXAMPLE_KEYWORDS:
        if kw in uk_lower or kw in en_lower:
            return False

    # Unbalanced parentheses/brackets
    if (")" in uk and "(" not in uk) or (")" in en and "(" not in en):
        return False
    if ("]" in uk and "[" not in uk) or ("]" in en and "[" not in en):
        return False
    if uk.startswith(")") or en.startswith(")") or uk.startswith("]") or en.startswith("]"):
        return False

    # Numbered gloss prefix like "1) to ring" or "2) to call"
    if re.match(r"^\d+\)", uk) or re.match(r"^\d+\)", en):
        return False

    # Reject if Ukrainian side ends with headword equality sign
    if uk.endswith("="):
        return False

    # Must be a plausible multi-word sentence/clause (or dialogue with dash/punctuation)
    if len(uk.split()) < 2 and not any(c in uk for c in "!?.—–"):
        return False
    return not (len(en.split()) < 2 and not any(c in en for c in "!?.—–"))


def is_grammar_note(line: str) -> bool:
    """Check if line is a standalone parenthetical grammar note (e.g. aspect tag)."""
    s = line.strip()
    return s.startswith("(") and any(
        kw in s.lower()
        for kw in [
            "imperfective",
            "perfective",
            "contrast",
            "noun",
            "verb",
            "adjective",
            "adverb",
            "list of choices",
            "ukrainian saying",
        ]
    )


def normalize_chunk_lines(text: str) -> list[str]:
    """Merge wrapped lines and combining accent OCR split lines."""
    raw_lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    merged: list[str] = []
    for line in raw_lines:
        ls = line.strip()
        if merged and ls.startswith("\u0301"):
            # Combining acute accent wrapped to start of next line
            content = re.sub(r"^\u0301\s*", "\u0301", ls)
            merged[-1] = merged[-1] + content
        else:
            merged.append(line)
    return merged


def split_uk_en_line(line: str) -> tuple[str, str] | None:
    """Split a bilingual line into Ukrainian and English columns."""
    line = line.strip()
    if not line:
        return None
    # 1. Two or more spaces
    m = re.search(r"\s{2,}", line)
    if m:
        left = line[: m.start()].strip()
        right = line[m.end() :].strip()
        if CYRILLIC_CHAR_RE.search(left) and LATIN_CHAR_RE.search(right):
            return left, right
    # 2. Single-space boundary where Cyrillic/punctuation meets Latin capital/quote
    m_split = TWO_COL_BOUNDARY_RE.search(line)
    if m_split:
        left = line[: m_split.start()].strip()
        right = line[m_split.end() :].strip()
        if CYRILLIC_CHAR_RE.search(left) and LATIN_CHAR_RE.search(right):
            return left, right
    return None


def extract_1000_words_example(
    lines: list[str],
    *,
    start_i: int = 1,
    locator: str = "",
) -> dict[str, str] | None:
    """Extract at most one bilingual UK/EN example pair from a 1000-words chunk."""
    i = start_i
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        # Skip parenthetical explanatory notes at top of body (e.g. "(contrast between sentences)")
        if is_grammar_note(line):
            i += 1
            continue
        pair = split_uk_en_line(lines[i])
        if pair:
            uk, en = pair
            # Skip grammar aspect tags e.g. "(imperfective, perfective)" on the English side
            if is_grammar_note(en):
                i += 1
                continue

            j = i + 1
            while j < len(lines):
                next_raw = lines[j]
                next_str = next_raw.strip()
                if not next_str:
                    break
                if next_str.startswith("(") and next_str.endswith(")"):
                    # Continuation of right column like "(for work)?"
                    if (
                        LATIN_CHAR_RE.search(next_str)
                        and not CYRILLIC_CHAR_RE.search(next_str)
                        and not next_str.startswith("(Ukrainian")
                    ):
                        en += " " + next_str
                        j += 1
                        continue
                    break

                # Stop if both columns already ended in terminal punctuation
                if uk.endswith((".", "?", "!", "…”", ".”", "!”", "?”", "»", '"')) and en.endswith(
                    (".", "?", "!", "…”", ".”", "!”", "?”", "»", '"')
                ):
                    break

                m2 = re.search(r"\s{2,}", next_raw)
                if m2:
                    nl = next_raw[: m2.start()].strip()
                    nr = next_raw[m2.end() :].strip()
                    if nl and (
                        nl[0].islower()
                        or nl[0].isdigit()
                        or nl.startswith(("%", "—", "-"))
                        or not CYRILLIC_CHAR_RE.search(nl)
                    ):
                        uk += " " + nl
                        en += " " + nr
                        j += 1
                        continue
                    if not nr and CYRILLIC_CHAR_RE.search(nl):
                        uk += " " + nl
                        j += 1
                        continue
                    if not nl and LATIN_CHAR_RE.search(nr):
                        en += " " + nr
                        j += 1
                        continue
                    break

                if CYRILLIC_CHAR_RE.search(next_str) and not LATIN_CHAR_RE.search(next_str):
                    if not next_str.startswith(("«", '"')):
                        uk += " " + next_str
                        j += 1
                        continue
                    break
                if LATIN_CHAR_RE.search(next_str) and not CYRILLIC_CHAR_RE.search(next_str):
                    en += " " + next_str
                    j += 1
                    continue
                break

            uk = re.sub(r"\s+", " ", uk).strip()
            en = re.sub(r"\s+", " ", en).strip()
            if is_plausible_example(uk, en):
                return {
                    "uk": uk,
                    "en": en,
                    "source": SOURCE_LABEL_AUTHOR,
                    "locator": locator,
                }
        i += 1
    return None


def parse_1000_words_head_and_gloss(lines: list[str]) -> tuple[str, str, int]:
    """Parse raw Ukrainian headword and English gloss from 1000-words lines."""
    if not lines:
        return "", "", 0
    l0 = lines[0].strip()
    l0_no_num = re.sub(r"^\d+\.\s*", "", l0)

    pair0 = split_uk_en_line(l0_no_num)
    if pair0:
        head, gloss = pair0
    else:
        lat_m = LATIN_CHAR_RE.search(l0_no_num)
        if lat_m:
            head = l0_no_num[: lat_m.start()].strip()
            gloss = l0_no_num[lat_m.start() :].strip()
        else:
            head = l0_no_num
            gloss = ""

    body_start_idx = 1
    if len(lines) > 1:
        l1 = lines[1].strip()
        if is_grammar_note(l1):
            body_start_idx = 2
        else:
            pair1 = split_uk_en_line(l1)
            uk1, en1 = pair1 if pair1 else (l1, "")
            is_uk_cont = (
                head.endswith(("=", ","))
                or "(1)" in head
                or (not LATIN_CHAR_RE.search(l1) and head.endswith(("=", ",")))
            )
            is_en_cont = (
                gloss.endswith((",", ";", "/", "("))
                or (gloss.count("(") > gloss.count(")"))
                or bool(re.match(r"^\d+\)", en1.strip()))
                or en1.strip().startswith(")")
                or (en1.count(")") > en1.count("("))
                or ("1)" in gloss and "2)" in en1)
                or (
                    not CYRILLIC_CHAR_RE.search(l1)
                    and (
                        gloss.endswith((",", ";", "/"))
                        or gloss.count("(") > gloss.count(")")
                        or not gloss
                    )
                )
            )

            if is_uk_cont or is_en_cont:
                if pair1:
                    if CYRILLIC_CHAR_RE.search(uk1) and not any(c in uk1 for c in ".?!…”»\""):
                        head = (head + " " + uk1).strip()
                    if is_en_cont or not gloss:
                        gloss = (gloss + " " + en1).strip() if gloss else en1.strip()
                else:
                    if not LATIN_CHAR_RE.search(l1):
                        head = (head + " " + l1).strip()
                    elif not CYRILLIC_CHAR_RE.search(l1):
                        gloss = (gloss + " " + l1).strip() if gloss else l1.strip()
                body_start_idx = 2
                if len(lines) > 2 and is_grammar_note(lines[2]):
                    body_start_idx = 3

    return head, gloss, body_start_idx


def split_headword_into_lemmas(head_raw: str) -> list[str]:
    """Split headword text into constituent normalized Ukrainian lemmas."""
    h = head_raw
    # Fix known OCR space artifacts
    h = re.sub(r"(\w[\u0301]?)\s+тися\b", r"\1тися", h)
    segments = re.split(r"[,=|/]", h)
    lemmas: list[str] = []
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        # Expand reflexives
        if "[ся]" in seg or "[сь]" in seg:
            b1 = re.sub(r"\s*\[ся\]", "", seg)
            b1 = re.sub(r"\s*\[сь\]", "", b1).strip()
            b2 = re.sub(r"\s*\[ся\]", "ся", seg)
            b2 = re.sub(r"\s*\[сь\]", "сь", b2).strip()
            candidates = [b1, b2]
        else:
            candidates = [seg]

        for cand in candidates:
            cand = re.sub(r"^\d+\)\s*", "", cand).strip()
            cand = re.sub(r"\s*\([^)]*\)\s*$", "", cand).strip()
            cand_clean = strip_acute_stress(cand).strip()
            cand_clean = re.sub(r"\s+", " ", cand_clean)
            if cand_clean and cand_clean not in lemmas:
                lemmas.append(cand_clean)
    return lemmas


def parse_1000_words_chunk(chunk_id: str, title: str, text: str) -> ParsedOhoikoEntry:
    """Parse a single 1000-words textbook row into structured entry data."""
    num_m = re.search(r"_e(\d+)", chunk_id)
    entry_num = int(num_m.group(1)) if num_m else 0
    locator = f"ohoiko-1000-words entry {entry_num}"

    lines = normalize_chunk_lines(text)
    head_raw, gloss, start_i = parse_1000_words_head_and_gloss(lines)
    lemmas = split_headword_into_lemmas(head_raw)
    example = extract_1000_words_example(lines, start_i=start_i, locator=locator)

    return ParsedOhoikoEntry(
        source_file=SOURCE_1000_WORDS,
        entry_number=entry_num,
        locator=locator,
        lemmas=lemmas,
        gloss=gloss,
        example=example,
    )


def extract_500_verbs_example(lines: list[str], *, start_i: int = 2, locator: str = "") -> dict[str, str] | None:
    """Extract one bilingual UK/EN example sentence from a 500-verbs page.

    Real verb pages run: headword/gloss/stems, full present/past/future/
    conditional/imperative/participle tables, then one or more
    case-government labels (``+ accusative:``, ``-ся + з (із, зі) +
    instrumental:``, ...) each followed by 1-4 two-column example
    sentences. Longer sentences wrap across 2-3 physical lines, and the
    two columns don't always wrap in lockstep -- one side can finish
    (reach terminal punctuation) a line before the other, so a wrapped
    continuation may be a matching two-column row (both sides wrap) or a
    lone Cyrillic-only / Latin-only row (only one side wraps).
    """
    i = start_i
    while i < len(lines):
        pair = split_uk_en_line(lines[i].strip())
        if not pair:
            i += 1
            continue
        uk, en = pair
        j = i + 1
        hops = 0
        while hops < 5 and not (
            uk.rstrip().endswith(TERMINAL_PUNCT_500_VERBS)
            and en.rstrip().endswith(TERMINAL_PUNCT_500_VERBS)
        ):
            if j >= len(lines):
                break
            next_str = lines[j].strip()
            next_pair = split_uk_en_line(next_str)
            has_cyr = bool(CYRILLIC_CHAR_RE.search(next_str))
            has_lat = bool(LATIN_CHAR_RE.search(next_str))
            if next_pair:
                nuk, nen = next_pair
                uk = f"{uk} {nuk}".strip()
                en = f"{en} {nen}".strip()
            elif has_cyr and not has_lat:
                uk = f"{uk} {next_str}".strip()
            elif has_lat and not has_cyr:
                en = f"{en} {next_str}".strip()
            else:
                break
            j += 1
            hops += 1

        uk = re.sub(r"\s+", " ", uk).strip()
        en = re.sub(r"\s+", " ", en).strip()
        if is_plausible_example(uk, en):
            return {"uk": uk, "en": en, "source": SOURCE_LABEL_AUTHOR, "locator": locator}
        i += 1
    return None


def parse_500_verbs_chunk(chunk_id: str, title: str, text: str) -> ParsedOhoikoEntry:
    """Parse a single 500-verbs textbook row into structured entry data."""
    num_m = re.search(r"_e(\d+)", chunk_id)
    entry_num = int(num_m.group(1)) if num_m else 0
    locator = f"ohoiko-500-verbs entry {entry_num}"

    raw_lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    lines: list[str] = []
    for line in raw_lines:
        ls = line.strip()
        if lines and ls.startswith("\u0301"):
            if (
                len(lines) >= 2
                and LATIN_CHAR_RE.search(lines[-1])
                and not CYRILLIC_CHAR_RE.search(lines[-1])
            ):
                content = re.sub(r"^\u0301\s*", "\u0301", ls)
                lines[-2] = lines[-2] + content
                continue
            content = re.sub(r"^\u0301\s*", "\u0301", ls)
            lines[-1] = lines[-1] + content
        else:
            lines.append(line)

    head_raw = ""
    gloss = ""

    for line in lines[:4]:
        ls = line.strip()
        if "Present / Future" in ls:
            if ls.startswith("Present / Future"):
                rem = ls[len("Present / Future") :].strip()
                m_gap = re.search(r"\s{2,}", rem)
                if m_gap:
                    s1 = rem[: m_gap.start()].strip()
                    s2 = rem[m_gap.end() :].strip()
                    head_cand = s2 if (s1.startswith("Stems:") or "Stems:" in s1) else s1
                else:
                    head_cand = rem
            else:
                head_cand = ls.split("Present / Future")[0].strip()
            if head_cand and CYRILLIC_CHAR_RE.search(head_cand):
                head_raw = head_cand
        elif (
            not head_raw
            and CYRILLIC_CHAR_RE.search(ls)
            and ("|" in ls or ls.endswith(("ти", "ти [ся]", "тись", "тися")))
        ):
            head_raw = ls

        if "to " in ls.lower():
            if "to " in ls:
                gloss_idx = ls.find("to ")
                gloss_cand = ls[gloss_idx:].strip()
            else:
                gloss_cand = ls
            if not gloss:
                gloss = gloss_cand

    lemmas = split_headword_into_lemmas(head_raw)

    # The example sentence(s) live after the conjugation tables, past a
    # case-government label like "+ accusative:" (see
    # extract_500_verbs_example). Table rows themselves never match: body
    # rows are Cyrillic-only (both aspect columns), and the "PERSON /
    # IMPERFECTIVE ASPECT / PERFECTIVE ASPECT" header row is Latin-only on
    # its Cyrillic-less left side, so split_uk_en_line rejects both.
    example = extract_500_verbs_example(lines, start_i=2, locator=locator)

    return ParsedOhoikoEntry(
        source_file=SOURCE_500_VERBS,
        entry_number=entry_num,
        locator=locator,
        lemmas=lemmas,
        gloss=gloss,
        example=example,
    )


def normalize_for_comparison(term: str) -> str:
    """Normalize an English translation term for duplicate-sense comparison."""
    t = re.sub(r"\([^)]*\)", "", term)
    t = re.sub(r"^\s*to\s+", "", t, flags=re.IGNORECASE)
    t = re.sub(r"[^\w\s]", "", t).lower().strip()
    return t


def is_duplicate_sense(prior_term: str, anna_gloss: str) -> bool:
    """Return True if prior_term represents the same sense as anna_gloss."""
    p_norm = normalize_for_comparison(prior_term)
    a_norm = normalize_for_comparison(anna_gloss)
    if not p_norm or not a_norm:
        return False
    if p_norm == a_norm:
        return True
    a_subterms = [normalize_for_comparison(s) for s in re.split(r"[,;/]", anna_gloss)]
    p_subterms = [normalize_for_comparison(s) for s in re.split(r"[,;/]", prior_term)]
    return any(s and s in a_subterms for s in p_subterms) or any(
        s and s in p_subterms for s in a_subterms
    )


def merge_translation(
    prior_translation: dict[str, Any] | None,
    anna_gloss: str,
) -> dict[str, Any]:
    """Merge Anna's learner gloss as primary, keeping only distinct prior EN senses."""
    new_en = [anna_gloss]
    if prior_translation and isinstance(prior_translation.get("en"), list):
        for term in prior_translation["en"]:
            term_str = str(term).strip()
            if not term_str:
                continue
            if is_duplicate_sense(term_str, anna_gloss):
                continue
            if term_str not in new_en:
                new_en.append(term_str)

    result: dict[str, Any] = {
        "en": new_en,
        "source": SOURCE_LABEL_GLOSS,
    }
    if prior_translation and prior_translation.get("pos"):
        result["pos"] = prior_translation["pos"]
    return result


def merge_examples(
    prior_examples: list[dict[str, Any]] | None,
    new_examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge new examples with prior examples, capped at <=2 and deduplicated."""
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for ex in new_examples + (prior_examples or []):
        uk = str(ex.get("uk") or "").strip()
        en = str(ex.get("en") or "").strip()
        if not uk or not en:
            continue
        if not is_plausible_example(uk, en):
            continue
        key = (uk, en)
        if key not in seen:
            seen.add(key)
            merged.append(
                {
                    "uk": uk,
                    "en": en,
                    "source": ex.get("source") or SOURCE_LABEL_AUTHOR,
                    "locator": ex.get("locator") or "",
                }
            )
        if len(merged) >= 2:
            break
    return merged


def enrich_entry_with_ohoiko(
    entry: dict[str, Any],
    *,
    anna_gloss: str | None = None,
    anna_example: dict[str, str] | None = None,
) -> bool:
    """Enrich a single Atlas entry dictionary in-place with Ohoiko gloss/example."""
    changed = False
    enrichment = entry.setdefault("enrichment", {})
    if enrichment is None:
        enrichment = {}
        entry["enrichment"] = enrichment

    sources = set(enrichment.get("sources") or [])

    if anna_gloss:
        enrichment["translation"] = merge_translation(enrichment.get("translation"), anna_gloss)
        sources.add(SOURCE_LABEL_GLOSS)
        changed = True

    if anna_example:
        prior_ex = enrichment.get("examples") or []
        enrichment["examples"] = merge_examples(prior_ex, [anna_example])
        sources.add(SOURCE_LABEL_AUTHOR)
        changed = True

    if changed:
        enrichment["sources"] = sorted(sources)

    return changed


def _load_500_verbs_full_text_by_number(cur: sqlite3.Cursor) -> dict[str, str]:
    """Load full verb-page text keyed by verb number, if the section exists.

    ``textbooks.text`` for ``anna-ohoiko-500-verbs`` chunks is a truncated
    stub (headword + first present-tense rows only) left over from a
    legacy ingest path -- it never reaches the example sentences (#7457).
    The full page (conjugation tables + case-government notes + example
    sentences) was separately ingested into ``textbook_sections.full_text``
    by ``scripts/ingest/ohoiko_verbs_ingest.py``, keyed by
    ``section_number`` (the verb number as plain text, e.g. ``"1"``).
    That ingest writes ``_v####`` chunk ids while the live ``textbooks``
    rows use the legacy ``_e####`` ids, so ``textbooks.parent_section_id``
    was never linked -- this looks up the richer text by number instead.
    Returns ``{}`` when the table/rows don't exist (e.g. a DB that
    predates the section-coverage backfill); callers fall back to the
    stub ``textbooks.text``.
    """
    try:
        rows = cur.execute(
            "SELECT section_number, full_text FROM textbook_sections WHERE source_file = ?",
            (SOURCE_500_VERBS,),
        ).fetchall()
    except sqlite3.OperationalError:
        return {}
    return {num: text for num, text in rows if num}


def build_ohoiko_book_catalog(
    conn: sqlite3.Connection,
) -> tuple[list[ParsedOhoikoEntry], list[ParsedOhoikoEntry]]:
    """Load and parse all 1000-words and 500-verbs chunks from sources.db."""
    cur = conn.cursor()
    rows1000 = cur.execute(
        "SELECT chunk_id, title, text FROM textbooks WHERE source_file = ?",
        (SOURCE_1000_WORDS,),
    ).fetchall()
    parsed_1000 = [parse_1000_words_chunk(cid, title, text) for cid, title, text in rows1000]

    rows500 = cur.execute(
        "SELECT chunk_id, title, text FROM textbooks WHERE source_file = ?",
        (SOURCE_500_VERBS,),
    ).fetchall()
    full_text_by_number = _load_500_verbs_full_text_by_number(cur)
    parsed_500 = []
    for cid, title, text in rows500:
        num_m = re.search(r"_e(\d+)", cid)
        full_text = full_text_by_number.get(str(int(num_m.group(1)))) if num_m else None
        parsed_500.append(parse_500_verbs_chunk(cid, title, full_text or text))

    return parsed_1000, parsed_500


def apply_ohoiko_quality_enrichment(
    manifest: dict[str, Any],
    conn: sqlite3.Connection | None = None,
    *,
    parsed_1000: list[ParsedOhoikoEntry] | None = None,
    parsed_500: list[ParsedOhoikoEntry] | None = None,
) -> dict[str, int]:
    """Apply Anna Ohoiko quality enrichment onto a manifest dictionary.

    Returns a summary dict with update counts.
    """
    if parsed_1000 is None or parsed_500 is None:
        if conn is None:
            raise ValueError("Must provide either a sqlite3 connection or parsed chunk lists")
        parsed_1000, parsed_500 = build_ohoiko_book_catalog(conn)

    entries = manifest.get("entries", [])
    entries_by_lemma = {e["lemma"]: e for e in entries if "lemma" in e}

    gloss_updated_1000 = 0
    ex_updated_1000 = 0
    matched_chunks_1000 = 0
    lemmas_updated_1000: set[str] = set()

    for item in parsed_1000:
        chunk_matched = False
        for lem in item.lemmas:
            entry = entries_by_lemma.get(lem)
            if entry is not None:
                chunk_matched = True
                lemmas_updated_1000.add(lem)
                if item.gloss:
                    enrich_entry_with_ohoiko(entry, anna_gloss=item.gloss)
                    gloss_updated_1000 += 1
                if item.example:
                    enrich_entry_with_ohoiko(entry, anna_example=item.example)
                    ex_updated_1000 += 1
        if chunk_matched:
            matched_chunks_1000 += 1

    gloss_updated_500 = 0
    ex_updated_500 = 0
    matched_chunks_500 = 0
    lemmas_updated_500: set[str] = set()

    for item in parsed_500:
        chunk_matched = False
        for lem in item.lemmas:
            entry = entries_by_lemma.get(lem)
            if entry is not None:
                chunk_matched = True
                lemmas_updated_500.add(lem)
                if item.gloss:
                    enrich_entry_with_ohoiko(entry, anna_gloss=item.gloss)
                    gloss_updated_500 += 1
                if item.example:
                    enrich_entry_with_ohoiko(entry, anna_example=item.example)
                    ex_updated_500 += 1
        if chunk_matched:
            matched_chunks_500 += 1

    # Verify #7397 heads
    heads_7397_enriched = 0
    for h in HEADS_7397:
        e = entries_by_lemma.get(h)
        if e and e.get("enrichment", {}).get("translation"):
            heads_7397_enriched += 1

    return {
        "1000_chunks_total": len(parsed_1000),
        "1000_chunks_matched": matched_chunks_1000,
        "1000_lemmas_updated": len(lemmas_updated_1000),
        "1000_gloss_applied": gloss_updated_1000,
        "1000_examples_applied": ex_updated_1000,
        "500_chunks_total": len(parsed_500),
        "500_chunks_matched": matched_chunks_500,
        "500_lemmas_updated": len(lemmas_updated_500),
        "500_gloss_applied": gloss_updated_500,
        "500_examples_applied": ex_updated_500,
        "heads_7397_enriched": heads_7397_enriched,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for Ohoiko quality enrichment."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to sources.db")
    parser.add_argument(
        "--manifest", type=Path, default=DEFAULT_MANIFEST_PATH, help="Path to manifest JSON"
    )
    parser.add_argument("--write", action="store_true", help="Write changes to manifest file")
    args = parser.parse_args(argv)

    if not args.db.is_file():
        print(f"Error: sources.db not found at {args.db}", file=sys.stderr)
        return 1

    from scripts.lexicon.manifest_io import load_manifest, write_manifest

    manifest = load_manifest(args.manifest)
    conn = sqlite3.connect(args.db)
    try:
        stats = apply_ohoiko_quality_enrichment(manifest, conn)
    finally:
        conn.close()

    print(json.dumps(stats, indent=2, ensure_ascii=False))

    if args.write:
        write_manifest(args.manifest, manifest)
        print(f"Wrote updated manifest to {args.manifest}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
