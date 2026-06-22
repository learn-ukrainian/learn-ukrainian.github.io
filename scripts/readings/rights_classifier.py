#!/usr/bin/env python3
"""Classify primary-text hosting rights for the readings pipeline."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal, TypedDict

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RIGHTS_PATH = PROJECT_ROOT / "data" / "authors_rights.yaml"

RightsClass = Literal["public_domain", "in_copyright"]

FOLK_AUTHOR_KEYS = frozenset(
    {
        "народна творчість",
        "традиційний текст",
        "traditional",
        "anonymous",
        "анонім",
    }
)
PREMODERN_TRACK_KEYS = frozenset(
    {
        "oes",
        "old east slavic",
        "old_east_slavic",
        "ruthenian",
        "baroque",
        "middle ukrainian",
        "middle_ukrainian",
        "old ukrainian",
        "old_ukrainian",
    }
)
STRESS_MARKS = {"\u0300", "\u0301"}
WHITESPACE_RE = re.compile(r"\s+")


class RightsVerdict(TypedDict):
    """Serializable rights verdict for one demanded primary text."""

    rights_class: RightsClass
    basis: str
    confidence: float


@dataclass(frozen=True)
class AuthorRights:
    death_year: int | None
    repressed_rehabilitated: bool = False
    rehab_year: int | None = None
    note: str = ""


def classify_rights(
    author: str,
    work: str = "",
    year: int | str | None = None,
    source_file: str = "",
    track: str = "",
    *,
    current_year: int | None = None,
    rights_path: Path = DEFAULT_RIGHTS_PATH,
) -> RightsVerdict:
    """Return the hosting-rights verdict for a demanded work."""
    threshold = _pd_threshold(current_year)
    normalized_author = normalize_author(author)
    normalized_track = normalize_token(track)
    normalized_source = str(source_file or "").casefold()
    work_year = _optional_int(year, "year")

    if _is_folk_or_traditional(normalized_author, normalized_source):
        return _verdict("public_domain", "folk/traditional public-domain source", 1.0)

    if _is_premodern(normalized_track, work_year):
        return _verdict("public_domain", "pre-modern track/work before 1800", 0.95)

    author_table = load_author_rights(rights_path)
    author_rights = author_table.get(normalized_author)
    if author_rights is not None:
        return _classify_known_author(author_rights, threshold)

    if work_year is not None and work_year <= 1928:
        return _verdict("public_domain", f"legacy publication-year fallback ({work_year} <= 1928)", 0.7)

    return _verdict("in_copyright", "conservative default (unknown)", 0.5)


def is_public_domain_verdict(verdict: RightsVerdict) -> bool:
    """Return whether a classifier verdict permits full-text hosting."""
    return verdict["rights_class"] == "public_domain"


def load_author_rights(rights_path: Path = DEFAULT_RIGHTS_PATH) -> dict[str, AuthorRights]:
    """Load the curated author-rights table keyed by normalized author name."""
    raw = yaml.safe_load(rights_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{rights_path} must contain a YAML mapping")

    table: dict[str, AuthorRights] = {}
    for author_key, raw_rights in raw.items():
        if not isinstance(raw_rights, dict):
            raise ValueError(f"{rights_path}: {author_key!r} must map to fields")
        normalized_key = normalize_author(str(author_key))
        if not normalized_key:
            raise ValueError(f"{rights_path}: author key must not be blank")
        rights = AuthorRights(
            death_year=_optional_int(raw_rights.get("death_year"), f"{author_key}.death_year"),
            repressed_rehabilitated=_optional_bool(
                raw_rights.get("repressed_rehabilitated", False),
                f"{author_key}.repressed_rehabilitated",
            ),
            rehab_year=_optional_int(raw_rights.get("rehab_year"), f"{author_key}.rehab_year"),
            note=str(raw_rights.get("note") or ""),
        )
        existing = table.get(normalized_key)
        if existing is not None and existing != rights:
            raise ValueError(f"{rights_path}: conflicting duplicate author key after normalization: {author_key!r}")
        table[normalized_key] = rights
    return table


def normalize_author(author: str) -> str:
    """Normalize an author key for table lookup."""
    return normalize_token(author)


def normalize_token(value: str) -> str:
    """Case-fold, de-stress, and collapse punctuation/spacing for rights keys."""
    decomposed = unicodedata.normalize("NFD", value or "")
    chars: list[str] = []
    for char in decomposed:
        if char in STRESS_MARKS:
            continue
        if unicodedata.category(char).startswith("P"):
            chars.append(" ")
            continue
        chars.append(char)
    normalized = unicodedata.normalize("NFC", "".join(chars))
    return WHITESPACE_RE.sub(" ", normalized).strip().casefold()


def _classify_known_author(author_rights: AuthorRights, threshold: int) -> RightsVerdict:
    if author_rights.repressed_rehabilitated:
        if author_rights.rehab_year is None:
            return _verdict("in_copyright", "rehabilitation+70: rehab year unknown", 0.85)
        if author_rights.rehab_year >= threshold:
            return _verdict(
                "in_copyright",
                f"rehabilitation+70: rehab_year {author_rights.rehab_year} >= {threshold}",
                0.95,
            )
        return _verdict(
            "public_domain",
            f"rehabilitation+70: rehab_year {author_rights.rehab_year} before {threshold}",
            0.95,
        )

    if author_rights.death_year is None:
        return _verdict("in_copyright", "conservative default (unknown death year)", 0.8)

    if author_rights.death_year >= threshold:
        return _verdict(
            "in_copyright",
            f"death_year {author_rights.death_year} >= {threshold} life+70 threshold",
            0.95,
        )

    return _verdict(
        "public_domain",
        f"death_year {author_rights.death_year} before {threshold} life+70 threshold",
        0.95,
    )


def _is_folk_or_traditional(normalized_author: str, normalized_source: str) -> bool:
    return normalized_author in FOLK_AUTHOR_KEYS or normalized_source.startswith("ukrlib-narod")


def _is_premodern(normalized_track: str, work_year: int | None) -> bool:
    return normalized_track in PREMODERN_TRACK_KEYS and (work_year is None or work_year < 1800)


def _pd_threshold(current_year: int | None) -> int:
    year = date.today().year if current_year is None else current_year
    if year < 1:
        raise ValueError("current_year must be positive")
    return year - 70


def _verdict(rights_class: RightsClass, basis: str, confidence: float) -> RightsVerdict:
    return {"rights_class": rights_class, "basis": basis, "confidence": confidence}


def _optional_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer or null")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer or null") from exc


def _optional_bool(value: object, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ValueError(f"{field_name} must be true or false")
