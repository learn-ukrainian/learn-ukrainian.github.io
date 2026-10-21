"""Closed L1 rule tables (design r3 §4, §6.1 "Rule tables").

Each table is content-hashed into every source's ``l1_transform_digest``
(``scripts/lexdata/transforms.py``), so adding a code or a label changes the
digest and forces a re-parse. Slices extend these tables in reviewed changes;
nothing outside this module defines a refusal code or a disposition.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from types import MappingProxyType

RULE_TABLES_VERSION = "1"

ROLES = frozenset({"headword", "equivalent_lexeme", "variant", "aspect_partner", "form", "mwe"})
UNIT_KINDS = frozenset({"file", "chunk", "section", "page", "zone"})
SENSE_APPLIES_TO = frozenset({"self", "all_members"})

# Refusal-code catalog. An accepted leaf has no code; a refused leaf keeps its
# raw span, carries exactly one code from here and holds NULL keys (§4).
REFUSAL_CODES: Mapping[str, str] = MappingProxyType({
    # Normalizer (scripts/lexdata/normalize.py).
    "empty_span": "the raw span is empty or whitespace only",
    "html_entity_residual": "an HTML entity survives one unescape pass (double escaping)",
    "homoglyph_mixed_script": "Cyrillic letters mixed with Latin or Greek letters in one span",
    "foreign_script": "letters from a non-Cyrillic script and no Cyrillic/Latin homoglyph mix",
    "no_letter": "no letter remains after edge punctuation and whitespace are removed",
    "stress_invalid": "a stress mark that does not follow a single Cyrillic vowel",
    # Parsers (named by the design, §10 (a)).
    "truncated_source": "the parser could read only a truncated copy of the source unit",
})

# Line dispositions for line-grain sources (§8): every line gets exactly one.
LINE_DISPOSITIONS = frozenset({
    # Oho! A1 workbook Словничок.
    "entry", "lesson_heading", "abbreviation_key", "continuation", "page_furniture",
    # ULP lesson notes.
    "zone_entry", "margin_entry", "prose_excluded", "heading", "furniture",
})

# Unit dispositions (l1_unit_disposition): one per source unit.
UNIT_DISPOSITIONS = frozenset({"imported"})
PREFIXED_DISPOSITIONS = ("refused:", "out_of_scope:")

# Source label -> grammar_parsed fields. Only the labels the design names
# (§5.3 R3) are listed; parser slices add their labels here. A label mapped
# to None is known and deliberately unmapped (``pos_unmapped``).
GRAMMAR_LABELS: Mapping[str, Mapping[str, str] | None] = MappingProxyType({
    "іменник": MappingProxyType({"pos": "noun"}),
    "дієслово (недок.)": MappingProxyType({"pos": "verb", "aspect": "imperfective"}),
    "ч.": MappingProxyType({"pos": "noun", "gender": "masculine"}),
    "ж.": MappingProxyType({"pos": "noun", "gender": "feminine"}),
    "с.": MappingProxyType({"pos": "noun", "gender": "neuter"}),
    "прикм.": MappingProxyType({"pos": "adjective"}),
    "незмінюване слово": None,
})


def is_refusal_code(code: str) -> bool:
    return code in REFUSAL_CODES


def is_line_disposition(value: str) -> bool:
    return value in LINE_DISPOSITIONS or _is_refused(value)


def is_unit_disposition(value: str) -> bool:
    if value in UNIT_DISPOSITIONS or _is_refused(value):
        return True
    prefix = "out_of_scope:"
    return value.startswith(prefix) and bool(value[len(prefix):].strip())


def _is_refused(value: str) -> bool:
    prefix = "refused:"
    return value.startswith(prefix) and value[len(prefix):] in REFUSAL_CODES


def map_grammar_labels(labels: Iterable[str]) -> dict[str, object]:
    """Map source labels through the closed table; never guess an unknown label.

    Returns ``{"labels": [...], "fields": {...}, "unmapped": [...], "conflicts": [...]}``.
    Several labels may each contribute; a field two labels set differently is a
    conflict and is left out of ``fields``.
    """
    ordered = list(dict.fromkeys(label.strip() for label in labels if label and label.strip()))
    fields: dict[str, str] = {}
    conflicts: set[str] = set()
    unmapped: list[str] = []
    for label in ordered:
        mapped = GRAMMAR_LABELS.get(label)
        if mapped is None:
            unmapped.append(label)
            continue
        for key, value in mapped.items():
            if key in fields and fields[key] != value:
                conflicts.add(key)
            fields.setdefault(key, value)
    for key in conflicts:
        fields.pop(key, None)
    return {"labels": ordered, "fields": dict(sorted(fields.items())), "unmapped": unmapped,
            "conflicts": sorted(conflicts)}


def table_contents() -> dict[str, object]:
    """Canonical JSON-able contents, hashed by the transform registry."""
    return {
        "version": RULE_TABLES_VERSION,
        "roles": sorted(ROLES),
        "unit_kinds": sorted(UNIT_KINDS),
        "sense_applies_to": sorted(SENSE_APPLIES_TO),
        "refusal_codes": dict(sorted(REFUSAL_CODES.items())),
        "line_dispositions": sorted(LINE_DISPOSITIONS),
        "unit_dispositions": sorted(UNIT_DISPOSITIONS),
        "prefixed_dispositions": list(PREFIXED_DISPOSITIONS),
        "grammar_labels": {label: (None if mapped is None else dict(sorted(mapped.items())))
                           for label, mapped in sorted(GRAMMAR_LABELS.items())},
    }
