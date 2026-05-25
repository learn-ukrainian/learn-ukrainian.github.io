"""Structured textbook citation matching for Python QG."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

_CYRILLIC_TO_LATIN = str.maketrans(
    {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "h",
        "ґ": "g",
        "д": "d",
        "е": "e",
        "є": "ie",
        "ж": "zh",
        "з": "z",
        "и": "y",
        "і": "i",
        "ї": "i",
        "й": "i",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "kh",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "shch",
        "ь": "",
        "ю": "iu",
        "я": "ia",
        "ы": "y",
        "э": "e",
        "ъ": "",
    }
)

_PAGE_RE = re.compile(
    r"(?i)(?:\bp\.?\s*|\bpage\s+|[сc]\.?\s*|\bстор\.?\s*|"
    r"\bсторінка\s+)(?P<page>\d+)(?:\s*[-–—]\s*(?P<page_end>\d+))?\b"
)


@dataclass(frozen=True)
class CitationKey:
    author: str
    grade: int
    page: int
    page_end: int | None = None


def normalize_citation_ref(value: Any) -> str:
    normalized = re.sub(r"\s+", " ", str(value or "")).strip()
    return re.sub(r"\bp\.\s+(\d+)\b", r"p.\1", normalized)


def extract_plan_reference_titles(plan: Mapping[str, Any]) -> list[Any]:
    references = plan.get("references")
    if references is None:
        references = plan.get("plan_references", [])
    if not isinstance(references, list):
        return []
    return [
        ref["title"] for ref in references if isinstance(ref, Mapping) and ref.get("title")
    ]


def extract_chunk_id_from_notes(notes: str) -> str | None:
    match = re.search(r"chunk_id:\s*([A-Za-z0-9_\-]+)", str(notes or ""))
    return match.group(1) if match else None


def extract_citation_key(value: Any) -> CitationKey | None:
    text = str(value or "")
    # The first capitalized token is intentionally a narrow author heuristic:
    # title-first citations fail closed instead of laundering unknown sources.
    author_match = re.search(r"\b[А-ЯҐЄІЇA-Z][А-ЯҐЄІЇа-яґєіїA-Za-z'’-]*\b", text)
    if author_match is None:
        return None

    grade_match = re.search(
        r"(?i)(?:\b(?:grade|clas|class|klas)\s*(1[01]|[1-9])\b|"
        r"\b(1[01]|[1-9])\s*(?:клас|grade|clas|class|klas)\b)",
        text,
    )
    if grade_match is None:
        return None

    page_matches = list(_PAGE_RE.finditer(text))
    if len(page_matches) != 1:
        return None
    page_match = page_matches[0]
    page = int(page_match.group("page"))
    page_end_text = page_match.group("page_end")
    page_end = int(page_end_text) if page_end_text is not None else None
    if page_end is not None and page_end < page:
        return None

    author = fold_citation_author(author_match.group(0))
    if not author:
        return None
    grade = int(next(group for group in grade_match.groups() if group is not None))
    return CitationKey(author=author, grade=grade, page=page, page_end=page_end)


def fold_citation_author(author: str) -> str:
    """Canonicalize an author token so the BGN-style transliteration used by
    plan references ("Захарійчук" → "zakhariichuk") matches the
    Wikipedia/chunk-id transliteration used by textbook source records
    ("Zaharijchuk" → "zaharijchuk").

    Two real-world transliteration schemes appear in the pipeline:

    - **Plan references** are written in Cyrillic and translated by
      ``_CYRILLIC_TO_LATIN`` (BGN/PCGN-style: х → "kh", й → "i").
    - **Textbook chunk-ids** (and the ``source`` field synthesized from
      them in ``_parse_mcp_search_text_markdown``) use Wikipedia-style
      Latin: х → "h", й → "j", и/і → either "y" or "i".

    Without canonicalization, "zakhariichuk" and "zaharijchuk" compare
    unequal even though both refer to *Захарійчук*, which silently broke
    ``textbook_grounding`` on a1/m20 (build 2026-05-16 23:01).

    The fold pipeline:
      1. casefold + ``_CYRILLIC_TO_LATIN`` (existing behaviour)
      2. strip non-letters
      3. ``kh`` → ``h`` (collapse to the Wikipedia variant)
      4. ``j`` → ``i``, ``y`` → ``i`` (й/и/і all collapse to ``i``)
      5. squeeze any consecutive duplicates introduced by the collapses
         (e.g. "zahariichuk" → "zaharichuk")
    """
    folded = re.sub(r"[^a-z]", "", author.casefold().translate(_CYRILLIC_TO_LATIN))
    folded = folded.replace("kh", "h").replace("j", "i").replace("y", "i")
    return re.sub(r"(.)\1+", r"\1", folded)


def citation_keys_match(
    citation: CitationKey,
    plan_reference: CitationKey,
    *,
    page_tolerance: int = 5,
) -> bool:
    citation_start, citation_end = _page_bounds(citation)
    plan_start, plan_end = _page_bounds(plan_reference)
    return (
        citation.author == plan_reference.author
        and citation.grade == plan_reference.grade
        and citation_start <= plan_end + page_tolerance
        and plan_start <= citation_end + page_tolerance
    )


def _page_bounds(citation: CitationKey) -> tuple[int, int]:
    return citation.page, citation.page_end if citation.page_end is not None else citation.page
