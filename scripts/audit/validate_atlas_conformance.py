#!/usr/bin/env python3
"""Deterministic Word Atlas conformance gates from design section 8.

The manifest's field is named ``lemma``, but the existing Atlas enrichment and
heritage classifier treat a single-token page head as VESUM-covered when it
exists either as a lemma or as a word form. This preserves current lesson heads
such as ``сьома`` while still rejecting orphan Atlas pages.

Sovietization note: the current manifest carries sovietization risk only on
``heritage_status.sovietization_risk``. This validator also understands future
per-definition risk fields and requires those source-level risks to be mirrored
onto ``heritage_status`` so the red editorial warning renders.
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
DEFAULT_MANIFEST = PROJECT_ROOT / "starlight" / "src" / "data" / "lexicon-manifest.json"
DEFAULT_VESUM = PROJECT_ROOT / "data" / "vesum.db"
DEFAULT_CURRICULUM = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"

SOURCE_REQUIRED_SECTIONS = ("meaning", "attestation", "etymology", "morphology")
NON_STANDARD_AUTHENTIC_CLASSIFICATIONS = {
    "archaism",
    "authentic-archaism",
    "historism",
    "dialect",
    "borrowing",
}
STANDARD_OR_UNKNOWN_CLASSIFICATIONS = {"", "standard", "unknown"}
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
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:$|[T ])")


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


def validate(manifest: Any, *, vesum: Any, curriculum: Any) -> list[Violation]:
    """Validate a Word Atlas manifest against deterministic section 8 gates."""

    lookup = _coerce_vesum_lookup(vesum)
    should_close_lookup = isinstance(lookup, VesumLemmaLookup) and lookup is not vesum
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
            _check_lemma_in_vesum(entry, lemma, lookup, violations)
            _check_provenance(entry, lemma, violations)
            _check_empty_sections(entry, lemma, violations)
            _check_heritage_evidence(entry, lemma, violations)
            _check_sovietization(entry, lemma, violations)
            _check_cross_links(entry, lemma, curriculum_modules, violations)
            _check_wikipedia(entry, lemma, violations)
    finally:
        if should_close_lookup:
            lookup.close()

    return violations


def _coerce_vesum_lookup(vesum: Any) -> Any:
    if isinstance(vesum, str | Path):
        lookup = VesumLemmaLookup(Path(vesum))
        lookup.open()
        return lookup
    return vesum


def _strip_stress(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(char for char in decomposed if char not in STRESS_MARKS)
    return unicodedata.normalize("NFC", stripped)


def _normalize_text(value: object) -> str:
    cleaned = unicodedata.normalize("NFKC", str(value or "")).translate(APOSTROPHE_TRANSLATION)
    cleaned = _strip_stress(cleaned).casefold()
    return re.sub(r"\s+", " ", cleaned).strip()


def _lookup_variants(lemma: str) -> list[str]:
    normalized = _normalize_text(lemma)
    variants = {normalized}
    if "'" in normalized:
        for replacement in ("'", "’", "ʼ"):
            variants.add(normalized.replace("'", replacement))
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


def _check_lemma_in_vesum(entry: Mapping[str, Any], lemma: str, vesum: Any, violations: list[Violation]) -> None:
    raw_lemma = str(entry.get("lemma") or "")
    if not lemma:
        violations.append(Violation("lemma_in_vesum", "", "entry is missing lemma"))
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
    if not _vesum_has_entry(vesum, lemma):
        violations.append(
            Violation(
                "lemma_in_vesum",
                lemma,
                "single-word entry is absent from VESUM lemma and word-form tables",
            )
        )


def _enrichment(entry: Mapping[str, Any]) -> Mapping[str, Any]:
    enrichment = entry.get("enrichment")
    return enrichment if isinstance(enrichment, Mapping) else {}


def _non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _check_provenance(entry: Mapping[str, Any], lemma: str, violations: list[Violation]) -> None:
    enrichment = _enrichment(entry)
    for section_name in SOURCE_REQUIRED_SECTIONS:
        if section_name not in enrichment:
            continue
        section = enrichment[section_name]
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
        return _list_has_content(section.get("forms")) or _mapping_has_content(section.get("paradigm"))
    if section_name in {"attestation", "etymology"}:
        return _non_empty_str(section.get("text"))
    return True


def _check_empty_sections(entry: Mapping[str, Any], lemma: str, violations: list[Violation]) -> None:
    enrichment = _enrichment(entry)
    for section_name in SOURCE_REQUIRED_SECTIONS:
        if section_name not in enrichment:
            continue
        section = enrichment[section_name]
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


def _requires_heritage_evidence(status: Mapping[str, Any]) -> bool:
    classification = _classification(status)
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


def _sum11_definition_risk(meaning: object) -> int:
    if not isinstance(meaning, Mapping):
        return 0

    section_source_is_sum11 = _is_sum11_source(meaning.get("source"))
    meaning_level_risk = _max_sovietization_risk(meaning)
    risk = meaning_level_risk if section_source_is_sum11 else 0
    definitions = meaning.get("definitions")
    if isinstance(definitions, list):
        for definition in definitions:
            if not isinstance(definition, Mapping):
                continue
            source_is_sum11 = section_source_is_sum11 or _is_sum11_source(definition.get("source"))
            if source_is_sum11:
                risk = max(risk, meaning_level_risk, _max_sovietization_risk(definition))
    return risk


def _check_sovietization(entry: Mapping[str, Any], lemma: str, violations: list[Violation]) -> None:
    meaning = _enrichment(entry).get("meaning")
    source_risk = _sum11_definition_risk(meaning)
    if source_risk < 1:
        return

    status = entry.get("heritage_status")
    rendered_risk = _risk_number(status.get("sovietization_risk")) if isinstance(status, Mapping) else 0
    if rendered_risk < 1:
        violations.append(
            Violation(
                "sovietization_must_be_flagged",
                lemma,
                "SUM-11 definition carries sovietization risk but heritage_status.sovietization_risk is < 1",
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
    parser.add_argument("--curriculum", type=Path, default=DEFAULT_CURRICULUM)
    args = parser.parse_args(argv)

    manifest = _load_json(args.manifest)
    curriculum = _load_yaml(args.curriculum)
    with VesumLemmaLookup(args.vesum) as vesum:
        violations = validate(manifest, vesum=vesum, curriculum=curriculum)

    _print_violations(violations)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
