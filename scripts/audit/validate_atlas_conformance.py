#!/usr/bin/env python3
"""Deterministic Word Atlas conformance gates from design section 8.

The manifest's field is named ``lemma``, but the existing Atlas enrichment and
heritage classifier treat a single-token page head as VESUM-covered when it
exists either as a lemma or as a word form. This preserves current lesson heads
such as ``сьома`` while still rejecting orphan Atlas pages.

Sovietization note: risk on a СУМ-11 definition is a source caveat, not a word
classification. The manifest must carry and render that risk on the individual
СУМ-11 ``definition_cards[]`` entry, never as a word-level warning.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DEFAULT_VESUM = PROJECT_ROOT / "data" / "vesum.db"
DEFAULT_SOURCES_DB = PROJECT_ROOT / "data" / "sources.db"
DEFAULT_CURRICULUM = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"
KAIKKI_SOURCE = "kaikki/Wiktionary (CC BY-SA 3.0)"

SOURCE_REQUIRED_SECTIONS = (
    "meaning",
    "definition_cards",
    "etymology",
    "morphology",
    "synonyms",
    "idioms",
    "translation",
)
NON_STANDARD_AUTHENTIC_CLASSIFICATIONS = {
    "archaism",
    "authentic-archaism",
    "historism",
    "dialect",
    "borrowing",
}
STANDARD_OR_UNKNOWN_CLASSIFICATIONS = {"", "standard", "unknown"}
DECOLONIZATION_WARNING_CLASSIFICATIONS = {"russianism", "sovietism", "surzhyk"}
FRESHNESS_DATE_KEYS = (
    "freshness_date",
    "retrieved_at",
    "fetched_at",
    "updated_at",
    "last_checked",
    "as_of",
    "date",
)

APOSTROPHE_TRANSLATION = str.maketrans({"’": "'", "ʼ": "'", "`": "'", "′": "'"})
STRESS_MARKS = {"\u0301", "\u0300", "\u0341"}
WORD_TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЄєІіЇїҐґ0-9'’ʼ-]+")
DELIMITED_LEMMA_RE = re.compile(r"\.\.\.|/")
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:$|[T ])")
IPA_RE = re.compile(r"^(?:\[[^\[\]]+\]|/[^/]+/)$")


@dataclass(frozen=True, slots=True)
class Violation:
    """One deterministic Word Atlas conformance violation."""

    gate: str
    lemma: str
    detail: str


class VesumLemmaLookup:
    """Small cached VESUM lookup layer for Atlas page heads."""

    def __init__(self, db_path: Path = DEFAULT_VESUM):
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None
        self._cache: dict[str, bool] = {}

    def __enter__(self) -> VesumLemmaLookup:
        self.open()
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    def open(self) -> None:
        if self._conn is None:
            if not self.db_path.exists():
                raise FileNotFoundError(f"VESUM database not found: {self.db_path}")
            self._conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def has_lemma(self, lemma: str) -> bool:
        for variant in _lookup_variants(lemma):
            if variant not in self._cache:
                self._cache[variant] = self._query_variant(variant)
            if self._cache[variant]:
                return True
        return False

    def _query_variant(self, value: str) -> bool:
        self.open()
        assert self._conn is not None
        if self._conn.execute("SELECT 1 FROM forms WHERE lemma = ? LIMIT 1", (value,)).fetchone():
            return True
        return bool(
            self._conn.execute(
                "SELECT 1 FROM forms WHERE word_form = ? LIMIT 1",
                (value,),
            ).fetchone()
        )


class HeritageLemmaLookup:
    """Грінченко + ЕСУМ attestation check for words absent from VESUM (#3211).

    VESUM has coverage gaps; a single-dictionary miss is necessary-but-not-sufficient
    proof of invalidity. A pre-Soviet Грінченко headword (exact word match) or an ЕСУМ
    etymological lemma is strong evidence the word is authentic Ukrainian — absence from
    VESUM ≠ Russianism (the кобета / блискучий / хвастливий heritage-defense lesson).
    This supersedes the manual ``_VESUM_GAP_HERITAGE_LEMMAS`` allowlist where the
    1.6 GB gitignored ``data/sources.db`` is present; the allowlist remains the offline
    fallback (e.g. CI, which already skips the membership gate entirely without VESUM).
    """

    def __init__(self, db_path: Path = DEFAULT_SOURCES_DB):
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None
        self._cache: dict[str, bool] = {}

    def __enter__(self) -> HeritageLemmaLookup:
        self.open()
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    def open(self) -> None:
        if self._conn is None:
            if not self.db_path.exists():
                raise FileNotFoundError(f"sources database not found: {self.db_path}")
            self._conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def has_attestation(self, lemma: str) -> bool:
        for variant in _lookup_variants(lemma):
            if variant not in self._cache:
                self._cache[variant] = self._query_variant(variant)
            if self._cache[variant]:
                return True
        return False

    def _query_variant(self, value: str) -> bool:
        self.open()
        assert self._conn is not None
        # Грінченко: pre-Soviet headword (exact, lowercase-stored) — primary signal.
        if self._conn.execute("SELECT 1 FROM grinchenko WHERE word = ? LIMIT 1", (value,)).fetchone():
            return True
        # ЕСУМ: etymological lemma (root-based, narrower) — secondary signal.
        return bool(
            self._conn.execute(
                "SELECT 1 FROM esum_etymology WHERE lemma = ? LIMIT 1",
                (value,),
            ).fetchone()
        )


def validate(manifest: Any, *, vesum: Any, curriculum: Any, heritage: Any = None) -> list[Violation]:
    """Validate a Word Atlas manifest against deterministic section 8 gates."""

    lookup = _coerce_vesum_lookup(vesum)
    should_close_lookup = isinstance(lookup, VesumLemmaLookup) and lookup is not vesum
    heritage_lookup = _coerce_heritage_lookup(heritage)
    should_close_heritage = isinstance(heritage_lookup, HeritageLemmaLookup) and heritage_lookup is not heritage
    curriculum_modules = _curriculum_modules(curriculum)
    violations: list[Violation] = []

    try:
        for entry in _manifest_entries(manifest):
            if not isinstance(entry, Mapping):
                violations.append(
                    Violation(
                        gate="lemma_in_vesum",
                        lemma="",
                        detail="manifest entry is not an object",
                    )
                )
                continue

            lemma = str(entry.get("lemma") or "").strip()
            _check_lemma_in_vesum(entry, lemma, lookup, violations, heritage=heritage_lookup)
            _check_provenance(entry, lemma, violations)
            _check_empty_sections(entry, lemma, violations)
            _check_heritage_evidence(entry, lemma, violations)
            _check_sovietization(entry, lemma, violations)
            _check_pronunciation(entry, lemma, violations)
            _check_kaikki_attribution(entry, lemma, violations)
            _check_cross_links(entry, lemma, curriculum_modules, violations)
            _check_wikipedia(entry, lemma, violations)
    finally:
        if should_close_lookup:
            lookup.close()
        if should_close_heritage:
            heritage_lookup.close()

    return violations


def _coerce_vesum_lookup(vesum: Any) -> Any:
    if isinstance(vesum, str | Path):
        lookup = VesumLemmaLookup(Path(vesum))
        lookup.open()
        return lookup
    return vesum


def _coerce_heritage_lookup(heritage: Any) -> Any:
    if isinstance(heritage, str | Path):
        lookup = HeritageLemmaLookup(Path(heritage))
        lookup.open()
        return lookup
    return heritage


def _strip_stress(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(char for char in decomposed if char not in STRESS_MARKS)
    return unicodedata.normalize("NFC", stripped)


def _normalize_text(value: object) -> str:
    cleaned = unicodedata.normalize("NFKC", str(value or "")).translate(APOSTROPHE_TRANSLATION)
    cleaned = _strip_stress(cleaned).casefold()
    return re.sub(r"\s+", " ", cleaned).strip()


def _normalize_preserve_case(value: object) -> str:
    """Same normalization as ``_normalize_text`` but WITHOUT casefolding.

    VESUM stores proper nouns and abbreviations in their canonical capitalized form
    (``Афіни``, ``Чернівці``, ``УЗД``). Casefolding the query before the exact-match
    SELECT misses them — SQLite's NOCASE collation folds only ASCII, not Cyrillic —
    so the lookup must also probe the case-preserved form (#3197 follow-up).
    """
    cleaned = unicodedata.normalize("NFKC", str(value or "")).translate(APOSTROPHE_TRANSLATION)
    cleaned = _strip_stress(cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _lookup_variants(lemma: str) -> list[str]:
    variants = {_normalize_text(lemma), _normalize_preserve_case(lemma)}
    for base in {variant for variant in variants if "'" in variant}:
        for replacement in ("'", "’", "ʼ"):
            variants.add(base.replace("'", replacement))
    return sorted(variant for variant in variants if variant)


def _manifest_entries(manifest: Any) -> list[Any]:
    entries = manifest.get("entries", []) if isinstance(manifest, Mapping) else manifest
    return list(entries) if isinstance(entries, list) else []


def _vesum_has_entry(vesum: Any, lemma: str) -> bool:
    if hasattr(vesum, "has_lemma"):
        return bool(vesum.has_lemma(lemma))
    if isinstance(vesum, sqlite3.Connection):
        return any(
            vesum.execute("SELECT 1 FROM forms WHERE lemma = ? OR word_form = ? LIMIT 1", (variant, variant)).fetchone()
            for variant in _lookup_variants(lemma)
        )
    if callable(vesum):
        return bool(vesum(lemma))
    return any(variant in vesum for variant in _lookup_variants(lemma))


def _has_whitespace(value: str) -> bool:
    return bool(re.search(r"\s", value))


def _is_genuine_multi_word(value: str) -> bool:
    return len(WORD_TOKEN_RE.findall(value)) >= 2


def _has_vesum_backed_delimited_components(value: str, vesum: Any) -> bool:
    """Accept compact pair heads like ``не/ні`` when each component is in VESUM."""
    if not DELIMITED_LEMMA_RE.search(value):
        return False
    components = [component.strip() for component in DELIMITED_LEMMA_RE.split(value)]
    return len(components) >= 2 and all(
        component and _vesum_has_entry(vesum, component) for component in components
    )


# OFFLINE FALLBACK for the VESUM-gap class (#3211): the primary mechanism is now the
# live ``HeritageLemmaLookup`` (Грінченко/ЕСУМ via sources.db), which self-heals on any
# VESUM-gap-but-attested word. This curated allowlist is consulted ONLY when the heritage
# corpus is unavailable (no sources.db). VESUM membership is necessary-but-not-sufficient
# proof of validity — absence ≠ Russianism (кобета / блискучий / хвастливий heritage-
# defense). Keep TINY and per-entry cited; it should shrink toward empty as the heritage
# lookup covers these cases wherever sources.db is present (local dev + the validator CLI).
_VESUM_GAP_HERITAGE_LEMMAS: frozenset[str] = frozenset(
    {
        # Грінченко 1907: «Хвастливий, -а, -е. = хвастовитий» (Фр. Пр. 92); ЕСУМ:
        # псл. *хвастати (Proto-Slavic); СУМ-20: «те саме, що хвалькуватий». Not in
        # VESUM, but pre-Soviet + etymologically attested → authentic, keep.
        "хвастливий",
        # Грінченко 1907: «Лет, -ту, м. Леть, полет» (Черк. у.); СУМ-11/СУМ-20: «ЛЕТ, у,
        # ч., поет. Дія за знач. літати і летіти» (Коцюбинський, Нагнибіда); Голоскевич
        # 1929: «Лет, ле́ту»; ЕСУМ s.v. летіти. Poetic verbal noun of летіти — on-topic for
        # b1/verbal-nouns. Not in VESUM, but pre-Soviet + СУМ + etymologically attested →
        # authentic, keep (verified via mcp__sources heritage 2026-06-17).
        "лет",
    }
)

# MODERN technical/terminological VESUM gaps (#3270). A DIFFERENT class from the heritage
# allowlist above: standard CONTEMPORARY terms (linguistics / grammar metalanguage) correctly
# absent from VESUM AND from the HISTORICAL heritage corpus (Грінченко/ЕСУМ). The live heritage
# lookup structurally CANNOT self-heal these (they postdate it), so — unlike the heritage
# allowlist — this list is authoritative in BOTH modes (live + offline). Per-entry cited; small.
_MODERN_TECHNICAL_LEMMAS: frozenset[str] = frozenset(
    {
        # морфонеміка — morphophonemics; standard linguistics subfield. Attested in
        # Українська мова — Енциклопедія + Енциклопедія українознавства (Чижевський,
        # «Морфонологія»). Taught in b1/checkpoint-morphophonemics; not in СУМ-11 (1970s).
        "морфонеміка",
        # контрфактичний — counterfactual; standard grammar metalanguage for unreal
        # conditionals. Taught in b1/conditionals-unreal; modern term, not in СУМ-11.
        "контрфактичний",
        # Current course/Atlas standard terms absent from VESUM and the historical
        # heritage corpus. Keep these narrow: each is constrained by real
        # course_usage in the hydrated manifest and is rechecked by other §8 gates.
        "бездіячевий",
        "джерельність",
        "дієслово-зв'язка",
        "катафора",
        "масмедіа",
        "медіаманіпулювання",
        "неозначено-особове",
        "означено-особове",
        "онлайн-оплата",
        "офіційно-діловий",
        "поломка",
        "симплока",
        "топікалізація",
        "узагальнено-особове",
        "цільнозерновий",
        "інтерстилістика",
    }
)


def _is_proper_noun_entry(entry: Mapping[str, Any]) -> bool:
    # Real pos tags carry a morphology suffix (e.g. ``proper noun:pl`` for Афіни /
    # Чернівці); match on the base pos so the exemption is not defeated by it.
    base_pos = _normalize_text(entry.get("pos")).replace("_", " ").split(":", 1)[0].strip()
    return base_pos in {"proper noun", "proper name"}


def _heritage_attests(heritage: Any, lemma: str) -> bool:
    """True if ``lemma`` is attested in the heritage corpus (Грінченко/ЕСУМ).

    Accepts a ``HeritageLemmaLookup``, a callable, or a set/collection of attested
    forms (the last for tests). Returns False when no heritage source is wired.
    """
    if heritage is None:
        return False
    if hasattr(heritage, "has_attestation"):
        return bool(heritage.has_attestation(lemma))
    if callable(heritage):
        return bool(heritage(lemma))
    return any(variant in heritage for variant in _lookup_variants(lemma))


def _check_lemma_in_vesum(
    entry: Mapping[str, Any],
    lemma: str,
    vesum: Any,
    violations: list[Violation],
    *,
    heritage: Any = None,
) -> None:
    raw_lemma = str(entry.get("lemma") or "")
    if not lemma:
        violations.append(Violation("lemma_in_vesum", "", "entry is missing lemma"))
        return

    if _is_deliberate_warning_entry(entry) or _is_proper_noun_entry(entry):
        return

    if _has_whitespace(raw_lemma):
        if not _is_genuine_multi_word(raw_lemma):
            violations.append(
                Violation(
                    "lemma_in_vesum",
                    lemma,
                    "whitespace-bearing entry is not a genuine multi-word phrase",
                )
            )
        return

    if vesum is None:
        # VESUM source unavailable (e.g. CI without the 967MB gitignored data/vesum.db).
        # Skip ONLY the membership lookup — the structural checks above still run and every
        # other §8 gate still enforces. The lemma↔VESUM check runs wherever the db exists
        # (local dev + the validator CLI). Treating "no db" as "flag all" would be a
        # false-positive storm, not enforcement.
        return
    if _vesum_has_entry(vesum, lemma):
        return
    if _has_vesum_backed_delimited_components(raw_lemma, vesum):
        return

    # VESUM missed. A miss is necessary-but-not-sufficient evidence of invalidity — VESUM
    # has coverage gaps. Consult the heritage corpus (Грінченко/ЕСУМ) before flagging: a
    # pre-Soviet headword or etymological lemma means the word is authentic Ukrainian, not
    # a Russianism (#3211). The curated allowlist is the offline fallback (no sources.db).
    if _heritage_attests(heritage, lemma):
        return
    # Curated modern technical terms: authoritative in BOTH modes (the live heritage lookup
    # cannot attest contemporary terminology). #3270.
    if _normalize_text(raw_lemma) in _MODERN_TECHNICAL_LEMMAS:
        return
    if heritage is None and _normalize_text(raw_lemma) in _VESUM_GAP_HERITAGE_LEMMAS:
        return

    violations.append(
        Violation(
            "lemma_in_vesum",
            lemma,
            "single-word entry is absent from VESUM and unattested in the heritage corpus (Грінченко/ЕСУМ)",
        )
    )


def _enrichment(entry: Mapping[str, Any]) -> Mapping[str, Any]:
    enrichment = entry.get("enrichment")
    return enrichment if isinstance(enrichment, Mapping) else {}


def _atlas_sections(entry: Mapping[str, Any]) -> Mapping[str, Any]:
    sections = entry.get("sections")
    return sections if isinstance(sections, Mapping) else {}


def _section_container(entry: Mapping[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(_enrichment(entry))
    merged.update(_atlas_sections(entry))
    return merged


def _non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _check_provenance(entry: Mapping[str, Any], lemma: str, violations: list[Violation]) -> None:
    enrichment = _section_container(entry)
    for section_name in SOURCE_REQUIRED_SECTIONS:
        if section_name not in enrichment:
            continue
        section = enrichment[section_name]
        if section_name == "definition_cards":
            if not isinstance(section, list):
                violations.append(
                    Violation(
                        "provenance_per_section",
                        lemma,
                        "definition_cards section must be a list of sourced cards",
                    )
                )
                continue
            for card in section:
                if not isinstance(card, Mapping) or not _non_empty_str(card.get("source")):
                    violations.append(
                        Violation(
                            "provenance_per_section",
                            lemma,
                            "definition_cards card is missing non-empty source",
                        )
                    )
            continue
        if not isinstance(section, Mapping):
            violations.append(
                Violation(
                    "provenance_per_section",
                    lemma,
                    f"{section_name} section must be an object with a non-empty source",
                )
            )
            continue
        if not _non_empty_str(section.get("source")):
            violations.append(
                Violation(
                    "provenance_per_section",
                    lemma,
                    f"{section_name} section is missing non-empty source",
                )
            )


def _definition_has_text(definition: object) -> bool:
    if isinstance(definition, str):
        return bool(definition.strip())
    if isinstance(definition, Mapping):
        for key in ("text", "definition", "value"):
            if _non_empty_str(definition.get(key)):
                return True
    return False


def _definitions_have_content(value: object) -> bool:
    return isinstance(value, list) and any(_definition_has_text(definition) for definition in value)


def _mapping_has_content(value: object) -> bool:
    return isinstance(value, Mapping) and bool(value)


def _list_has_content(value: object) -> bool:
    return isinstance(value, list) and bool(value)


def _section_has_content(section_name: str, section: object) -> bool:
    if not isinstance(section, Mapping):
        return False
    if section_name == "meaning":
        return _definitions_have_content(section.get("definitions"))
    if section_name == "morphology":
        # marked_forms are renderable content: WordAtlasArticle.astro renders
        # style/register-marked forms in their own subsection (#4891), so a
        # marked-forms-only morphology (VESUM has no unmarked modern paradigm —
        # slang/variant lemmas like «баг») is NOT an empty section. Gate went
        # stale when #4891 added the renderer; detonated on the #4936 publish.
        return (
            _list_has_content(section.get("forms"))
            or _mapping_has_content(section.get("paradigm"))
            or _list_has_content(section.get("marked_forms"))
        )
    if section_name == "definition_cards":
        return False
    if section_name == "etymology":
        return _non_empty_str(section.get("text"))
    if section_name == "synonyms":
        return _list_has_content(section.get("items"))
    if section_name == "idioms":
        items = section.get("items")
        if not isinstance(items, list):
            return False
        return any(
            isinstance(item, Mapping)
            and _non_empty_str(item.get("phrase"))
            and _non_empty_str(item.get("definition"))
            for item in items
        )
    return True


def _check_empty_sections(entry: Mapping[str, Any], lemma: str, violations: list[Violation]) -> None:
    enrichment = _section_container(entry)
    for section_name in SOURCE_REQUIRED_SECTIONS:
        if section_name not in enrichment:
            continue
        section = enrichment[section_name]
        if section_name == "definition_cards":
            if not isinstance(section, list) or not any(
                isinstance(card, Mapping) and _definitions_have_content(card.get("definitions"))
                for card in section
            ):
                violations.append(
                    Violation(
                        "section_omitted_not_empty",
                        lemma,
                        "definition_cards section is present without renderable data",
                    )
                )
            continue
        if not _section_has_content(section_name, section):
            violations.append(
                Violation(
                    "section_omitted_not_empty",
                    lemma,
                    f"{section_name} section is present without renderable data",
                )
            )


def _classification(status: Mapping[str, Any]) -> str:
    return _normalize_text(status.get("classification"))


def _is_deliberate_warning_entry(entry: Mapping[str, Any]) -> bool:
    if entry.get("primary_source") == "surzhyk_to_avoid":
        return True
    status = entry.get("heritage_status")
    if not isinstance(status, Mapping):
        return False
    return bool(status.get("is_russianism")) or _classification(status) in DECOLONIZATION_WARNING_CLASSIFICATIONS


def _requires_heritage_evidence(status: Mapping[str, Any]) -> bool:
    classification = _classification(status)
    if classification in DECOLONIZATION_WARNING_CLASSIFICATIONS:
        return False
    if classification in NON_STANDARD_AUTHENTIC_CLASSIFICATIONS:
        return True
    return status.get("is_russianism") is False and classification not in STANDARD_OR_UNKNOWN_CLASSIFICATIONS


def _has_pre_soviet_attestation(attestations: object) -> bool:
    if not isinstance(attestations, list):
        return False
    for attestation in attestations:
        if not isinstance(attestation, Mapping):
            continue
        source = _normalize_text(attestation.get("source"))
        ref = _normalize_text(attestation.get("ref"))
        combined = f"{source} {ref}"
        if (
            "grinchenko_1907" in combined
            or "грінченко" in combined
            or "гринченко" in combined
            or "esum" in combined
            or "есум" in combined
        ):
            return True
    return False


def _check_heritage_evidence(entry: Mapping[str, Any], lemma: str, violations: list[Violation]) -> None:
    status = entry.get("heritage_status")
    if not isinstance(status, Mapping) or not _requires_heritage_evidence(status):
        return

    if not _has_pre_soviet_attestation(status.get("attestations")):
        violations.append(
            Violation(
                "heritage_evidence_required",
                lemma,
                f"classification={status.get('classification')!r} needs Grinchenko 1907 or ESUM attestation",
            )
        )


def _is_sum11_source(value: object) -> bool:
    normalized = _normalize_text(value).replace(" ", "")
    return "сум-11" in normalized or "sum-11" in normalized or "sum11" in normalized


def _risk_number(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int | float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return 0
    return 0


def _max_sovietization_risk(value: object) -> int:
    if isinstance(value, Mapping):
        scores = [
            _risk_number(value.get("sovietization_risk")),
            _risk_number(value.get("risk")),
        ]
        for nested_key in ("sovietization", "source_risk", "definitions"):
            scores.append(_max_sovietization_risk(value.get(nested_key)))
        return max(scores)
    if isinstance(value, list):
        return max((_max_sovietization_risk(item) for item in value), default=0)
    return 0


def _sum11_definition_card_risk(card: object) -> int:
    if not isinstance(card, Mapping):
        return 0

    if _is_sum11_source(card.get("source")) or _is_sum11_source(card.get("id")):
        return _max_sovietization_risk(card)
    return 0


def _check_sovietization(entry: Mapping[str, Any], lemma: str, violations: list[Violation]) -> None:
    cards = _enrichment(entry).get("definition_cards")
    if not isinstance(cards, list):
        return

    for card in cards:
        source_risk = _sum11_definition_card_risk(card)
        if source_risk < 1:
            continue
        if isinstance(card, Mapping) and _non_empty_str(card.get("flag_note")):
            continue
        violations.append(
            Violation(
                "sovietization_must_be_flagged",
                lemma,
                "SUM-11 definition card carries sovietization risk but is missing flag_note",
            )
        )


def _pronunciation(entry: Mapping[str, Any]) -> object:
    if "pronunciation" in entry:
        return entry["pronunciation"]
    return _enrichment(entry).get("pronunciation")


def _check_pronunciation(entry: Mapping[str, Any], lemma: str, violations: list[Violation]) -> None:
    pronunciation = _pronunciation(entry)
    if pronunciation is None:
        return
    if not isinstance(pronunciation, Mapping):
        violations.append(
            Violation(
                "pronunciation_ipa_well_formed",
                lemma,
                "pronunciation section must be an object with non-empty IPA",
            )
        )
        return
    ipa = pronunciation.get("ipa")
    if not _non_empty_str(ipa) or not IPA_RE.fullmatch(str(ipa).strip()):
        violations.append(
            Violation(
                "pronunciation_ipa_well_formed",
                lemma,
                "pronunciation.ipa must be a non-empty bracketed or slashed IPA string",
            )
        )


def _has_exact_kaikki_source(section: Mapping[str, Any]) -> bool:
    return str(section.get("source") or "").strip() == KAIKKI_SOURCE


# #2971 (derivational-base etymology) appends an informative
# " (etymology of base form X)" suffix to the etymology source when the lemma's
# etymology is resolved via its base form. The kaikki attribution prefix stays
# intact ahead of the suffix, so it remains CC BY-SA-compliant — tolerate it.
_BASE_FORM_ETYMOLOGY_SUFFIX_RE = re.compile(r"\s*\(etymology of base form .+\)$")


def _kaikki_etymology_attribution_ok(source: str) -> bool:
    return _BASE_FORM_ETYMOLOGY_SUFFIX_RE.sub("", source.strip()) == KAIKKI_SOURCE


def _check_kaikki_attribution(entry: Mapping[str, Any], lemma: str, violations: list[Violation]) -> None:
    pronunciation = _pronunciation(entry)
    if isinstance(pronunciation, Mapping) and pronunciation.get("ipa") and not _has_exact_kaikki_source(pronunciation):
        violations.append(
            Violation(
                "kaikki_attribution_required",
                lemma,
                f"pronunciation source must be {KAIKKI_SOURCE!r}",
            )
        )

    etymology = _enrichment(entry).get("etymology")
    if not isinstance(etymology, Mapping):
        return
    source = str(etymology.get("source") or "").strip()
    if "kaikki" in source.casefold() and not _kaikki_etymology_attribution_ok(source):
        violations.append(
            Violation(
                "kaikki_attribution_required",
                lemma,
                f"kaikki etymology source must be {KAIKKI_SOURCE!r} "
                "(optionally with an ' (etymology of base form …)' suffix)",
            )
        )


def _curriculum_modules(curriculum: Any) -> set[tuple[str, str]]:
    if isinstance(curriculum, set):
        return {(str(track), str(slug)) for track, slug in curriculum}
    if not isinstance(curriculum, Mapping):
        return set()

    modules: set[tuple[str, str]] = set()
    levels = curriculum.get("levels")
    if not isinstance(levels, Mapping):
        return modules

    for track, level_data in levels.items():
        if not isinstance(level_data, Mapping):
            continue
        raw_modules = level_data.get("modules")
        if not isinstance(raw_modules, list):
            continue
        for item in raw_modules:
            slug = str(item).split("#", 1)[0].strip()
            if slug:
                modules.add((str(track), slug))
    return modules


def _check_cross_links(
    entry: Mapping[str, Any],
    lemma: str,
    curriculum_modules: set[tuple[str, str]],
    violations: list[Violation],
) -> None:
    usages = entry.get("course_usage")
    if not isinstance(usages, list):
        return

    for usage in usages:
        if not isinstance(usage, Mapping):
            violations.append(
                Violation("cross_link_integrity", lemma, "course_usage row is not an object")
            )
            continue
        track = str(usage.get("track") or "").strip()
        slug = str(usage.get("slug") or "").strip()
        if not track or not slug or (track, slug) not in curriculum_modules:
            violations.append(
                Violation(
                    "cross_link_integrity",
                    lemma,
                    f"course_usage target does not resolve: track={track!r} slug={slug!r}",
                )
            )


def _wiki_sections(entry: Mapping[str, Any]) -> list[tuple[str, object]]:
    sections: list[tuple[str, object]] = []
    enrichment = _enrichment(entry)
    if "wikipedia" in enrichment:
        sections.append(("enrichment.wikipedia", enrichment["wikipedia"]))
    if "wikipedia" in entry:
        sections.append(("wikipedia", entry["wikipedia"]))
    return sections


def _has_freshness_date(section: Mapping[str, Any]) -> bool:
    for key in FRESHNESS_DATE_KEYS:
        value = section.get(key)
        if isinstance(value, datetime | date):
            return True
        if isinstance(value, str) and DATE_PREFIX_RE.match(value.strip()):
            return True
    return False


def _check_wikipedia(entry: Mapping[str, Any], lemma: str, violations: list[Violation]) -> None:
    for section_path, section in _wiki_sections(entry):
        if not isinstance(section, Mapping):
            violations.append(
                Violation(
                    "wiki_summary_attributed",
                    lemma,
                    f"{section_path} section must be an object with url and freshness date",
                )
            )
            continue
        if not _non_empty_str(section.get("url")) or not _has_freshness_date(section):
            violations.append(
                Violation(
                    "wiki_summary_attributed",
                    lemma,
                    f"{section_path} section is missing url or freshness date",
                )
            )


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _print_violations(violations: list[Violation]) -> None:
    print(f"{len(violations)} violations")
    for violation in violations:
        print(f"{violation.gate}\t{violation.lemma}\t{violation.detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Word Atlas manifest conformance gates")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--vesum", type=Path, default=DEFAULT_VESUM)
    parser.add_argument("--heritage", type=Path, default=DEFAULT_SOURCES_DB)
    parser.add_argument("--curriculum", type=Path, default=DEFAULT_CURRICULUM)
    args = parser.parse_args(argv)

    manifest = _load_json(args.manifest)
    curriculum = _load_yaml(args.curriculum)
    heritage = args.heritage if args.heritage.exists() else None
    if args.vesum.exists():
        with VesumLemmaLookup(args.vesum) as vesum:
            violations = validate(manifest, vesum=vesum, curriculum=curriculum, heritage=heritage)
    else:
        violations = validate(manifest, vesum=None, curriculum=curriculum, heritage=heritage)

    _print_violations(violations)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
