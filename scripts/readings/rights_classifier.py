#!/usr/bin/env python3
"""Classify primary-text hosting rights for the readings pipeline."""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal, TypedDict

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RIGHTS_PATH = PROJECT_ROOT / "data" / "authors_rights.yaml"
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

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

# A host's public accessibility is not a redistribution licence. UkrLib source
# rows therefore continue to the author-level life+70 check; the remaining
# prefixes retain their established source-level treatment.
FREE_EDUCATIONAL_SOURCE_PREFIXES = ("textbook", "wikisource", "litopys", "izbornyk", "chtyvo")


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


class AuthorRightsTable(dict[str, AuthorRights]):
    """Rights table with exact lookup first, then safe canonical aliases."""

    def __init__(
        self,
        exact: dict[str, AuthorRights],
        canonical_index: dict[str, str],
    ) -> None:
        super().__init__(exact)
        self._canonical_index = canonical_index

    def get(self, key: str, default: AuthorRights | None = None) -> AuthorRights | None:
        normalized_key = normalize_author(key)
        exact = super().get(normalized_key)
        if exact is not None:
            return exact

        for canonical_key in _canonical_author_keys(normalized_key):
            exact_key = self._canonical_index.get(canonical_key)
            if exact_key is not None:
                return super().get(exact_key, default)
        return default

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        normalized_key = normalize_author(key)
        if super().__contains__(normalized_key):
            return True
        return any(
            canonical_key in self._canonical_index
            for canonical_key in _canonical_author_keys(normalized_key)
        )


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
    """Return the hosting-rights verdict for a demanded work.

    Unknown authors conservatively remain in copyright because corpus years are
    not reliable publication years. A separate table-expansion follow-up
    restores public-domain recall for not-yet-tabled classics.
    """
    threshold = _pd_threshold(current_year)
    normalized_author = normalize_author(author)
    normalized_track = normalize_token(track)
    normalized_source = str(source_file or "").casefold()
    work_year = _optional_int(year, "year")

    if _is_folk_or_traditional(normalized_author, normalized_source):
        return _verdict("public_domain", "folk/traditional public-domain source", 1.0)

    if _is_free_educational_source(normalized_source):
        # Sources with an established hosting basis retain their source-level
        # treatment. Public availability on a third-party literary site alone is
        # not such a basis; those rows are classified from author rights below.
        return _verdict(
            "public_domain",
            "freely published on an established educational source — hosted with attribution",
            0.9,
        )

    if _is_premodern(normalized_track, work_year):
        return _verdict("public_domain", "pre-modern track/work before 1800", 0.95)

    author_table = load_author_rights(rights_path)
    author_rights = author_table.get(normalized_author)
    if author_rights is not None:
        return _classify_known_author(author_rights, threshold)

    return _verdict(
        "in_copyright",
        "conservative default (author not in rights table)",
        0.5,
    )


def is_public_domain_verdict(verdict: RightsVerdict) -> bool:
    """Return whether a classifier verdict permits full-text hosting."""
    return verdict["rights_class"] == "public_domain"


def load_author_rights(rights_path: Path = DEFAULT_RIGHTS_PATH) -> AuthorRightsTable:
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
    return AuthorRightsTable(table, _build_canonical_index(table, rights_path))


def _build_canonical_index(
    table: dict[str, AuthorRights],
    rights_path: Path,
) -> dict[str, str]:
    candidates: dict[str, tuple[str, tuple[int | None, bool, int | None]]] = {}
    ambiguous: dict[str, set[str]] = {}

    for exact_key, rights in table.items():
        signature = _rights_signature(rights)
        for canonical_key in _canonical_author_keys(exact_key):
            existing = candidates.get(canonical_key)
            if existing is None:
                candidates[canonical_key] = (exact_key, signature)
                continue
            existing_key, existing_signature = existing
            if existing_signature != signature:
                ambiguous.setdefault(canonical_key, {existing_key}).add(exact_key)

    for canonical_key, exact_keys in sorted(ambiguous.items()):
        candidates.pop(canonical_key, None)
        LOGGER.warning(
            "%s: ambiguous canonical author key %r for %s; "
            "canonical fallback disabled",
            rights_path,
            canonical_key,
            ", ".join(sorted(exact_keys)),
        )

    return {
        canonical_key: exact_key
        for canonical_key, (exact_key, _signature) in candidates.items()
    }


def _rights_signature(rights: AuthorRights) -> tuple[int | None, bool, int | None]:
    return (rights.death_year, rights.repressed_rehabilitated, rights.rehab_year)


def _canonical_author_keys(normalized_author: str) -> set[str]:
    tokens = normalized_author.split()
    keys: set[str] = set()
    if not tokens:
        return keys

    surname_indices = _surname_candidate_indices(tokens)
    for surname_index in surname_indices:
        surname = tokens[surname_index]
        keys.add(f"surname:{surname}")
        first_initial = _first_initial_for_surname(tokens, surname_index)
        if first_initial:
            keys.add(f"surname:{surname}|initial:{first_initial}")
    return keys


def _surname_candidate_indices(tokens: list[str]) -> list[int]:
    non_initial_indices = [index for index, token in enumerate(tokens) if len(token) > 1]
    if len(non_initial_indices) <= 1:
        return non_initial_indices

    if any(len(token) == 1 for token in tokens):
        return non_initial_indices

    return [non_initial_indices[-1]]


def _first_initial_for_surname(tokens: list[str], surname_index: int) -> str | None:
    for index, token in enumerate(tokens):
        if index != surname_index and len(token) == 1:
            return token
    for index, token in enumerate(tokens):
        if index != surname_index and token:
            return token[0]
    return None


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
        # Repressed-and-rehabilitated Ukrainian authors — the Executed Renaissance
        # (Розстріляне відродження) and other Soviet-persecuted writers — are hosted in
        # full as freely-accessible heritage. Their works are published openly by
        # Ukrainian educational institutions (ukrlib.com.ua, state school textbooks,
        # Wikisource); this non-commercial educational project exists precisely to
        # preserve and maximise access to this heritage, with full attribution. The
        # "rehabilitation + 70" copyright-extension reading is deliberately NOT used as a
        # hosting gate: applying it would lock down the works of murdered writers *longer*
        # than ordinary authors — perverse for a cultural-preservation project, and
        # contrary to how Ukraine itself treats these texts. Mission: maximise access to
        # Ukrainian literature, never gatekeep it.
        return _verdict(
            "public_domain",
            "repressed & rehabilitated Ukrainian author — heritage hosted (non-commercial educational, attributed)",
            0.9,
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


def _is_free_educational_source(normalized_source: str) -> bool:
    """True when a source has an established full-text hosting basis.

    UkrLib is intentionally excluded: individual works still pass the author
    rights check so in-copyright rows remain retrieval-only.
    """
    return any(normalized_source.startswith(prefix) for prefix in FREE_EDUCATIONAL_SOURCE_PREFIXES)


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
