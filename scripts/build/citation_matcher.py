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
    r"\bсторінка\s+)(\d+)\b"
)


@dataclass(frozen=True)
class CitationKey:
    author: str
    grade: int
    page: int


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
    if text[page_match.end() : page_match.end() + 1] in {"-", "–", "—"}:
        return None

    author = fold_citation_author(author_match.group(0))
    if not author:
        return None
    grade = int(next(group for group in grade_match.groups() if group is not None))
    return CitationKey(author=author, grade=grade, page=int(page_match.group(1)))


def fold_citation_author(author: str) -> str:
    return re.sub(r"[^a-z]", "", author.casefold().translate(_CYRILLIC_TO_LATIN))
