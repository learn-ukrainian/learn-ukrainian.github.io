#!/usr/bin/env python3
"""Parse and sanitise single-word relation terms mined from MiyKlas.

MiyKlas dictionary entries can place abbreviated register, style, and domain
labels directly before a term (for example ``зневаж. віршомаз``).  Those labels
are metadata, not headwords.  They must only be removed when they are complete
dot-terminated tokens: stripping arbitrary substrings corrupts words such as
``заступник``.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

# Abbreviations used as MiyKlas qualifiers, including observed spelling errors
# (``спрт.``) and label stems which previously leaked into the artifact.  This
# is intentionally a denylist: a relation candidate cannot be a qualifier.
QUALIFIER_LABELS = frozenset(
    {
        "анат",
        "арх",
        "астр",
        "безос",
        "біол",
        "бот",
        "букв",
        "вет",
        "військ",
        "вульг",
        "геогр",
        "грам",
        "діал",
        "дипл",
        "дит",
        "екон",
        "ел",
        "етн",
        "жарг",
        "зоол",
        "заст",
        "зневаж",
        "ірон",
        "іст",
        "книжн",
        "лайл",
        "лінгв",
        "літ",
        "мат",
        "мед",
        "метал",
        "мист",
        "мор",
        "муз",
        "нар",
        "неол",
        "обр",
        "озд",
        "перен",
        "пестл",
        "поб",
        "поліграф",
        "політ",
        "поет",
        "псих",
        "реліг",
        "ритор",
        "роз",
        "розм",
        "сільськ",
        "сил",
        "сленг",
        "соц",
        "спец",
        "спорт",
        "спрт",
        "стил",
        "суч",
        "театр",
        "текст",
        "тех",
        "торг",
        "уроч",
        "фарм",
        "фам",
        "фіз",
        "філос",
        "фін",
        "хім",
        "церк",
        "юр",
        "юрид",
    }
)

# The prior miner emitted these fragments after deleting qualifier substrings
# inside real terms.  They cannot be reconstructed from the artifact because
# its raw source item was not retained, so reject them during its one-time
# cleanup as well as at every future candidate boundary.
REJECTED_MALFORMED_TERMS = frozenset({"адка", "инно", "упник", "учка", "ьний"})

_EDGE_PUNCTUATION = " \t\r\n,;:!?()[]{}«»\"“”"
_WORD_RE = re.compile(r"^[А-Яа-яЄєІіЇїҐґ]+(?:['’ʼ-][А-Яа-яЄєІіЇїҐґ]+)*$", re.IGNORECASE)
_QUALIFIER_RE = re.compile(
    rf"^(?:{'|'.join(re.escape(label) for label in sorted(QUALIFIER_LABELS, key=len, reverse=True))})\."
    rf"(?=\s|$)",
    re.IGNORECASE,
)


def parse_relation_term(raw: object) -> str | None:
    """Return one valid headword, excluding leading MiyKlas qualifiers.

    A qualifier is recognised only as an entire dotted token at the beginning
    of an item.  Thus ``заст. заступник`` becomes ``заступник``, while a bare
    ``заступник`` remains untouched.  The miner retains only single-word
    candidates; phrases belong to their source data but not this artifact.
    """
    term = re.sub(r"\s+", " ", str(raw or "")).strip(_EDGE_PUNCTUATION).casefold()
    while match := _QUALIFIER_RE.match(term):
        term = term[match.end() :].lstrip()
    if (
        not term
        or term in QUALIFIER_LABELS
        or term in REJECTED_MALFORMED_TERMS
        or not _WORD_RE.fullmatch(term)
    ):
        return None
    return term


def clean_candidate_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return records whose existing relation headwords are valid candidates."""
    cleaned: list[dict[str, Any]] = []
    for record in records:
        word_a = parse_relation_term(record.get("word_a"))
        word_b = parse_relation_term(record.get("word_b"))
        if word_a is None or word_b is None:
            continue
        cleaned.append({**record, "word_a": word_a, "word_b": word_b})
    return cleaned


def clean_candidate_file(input_path: Path, output_path: Path) -> tuple[int, int]:
    """Clean a JSON candidate list and return its before/after record counts."""
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not all(isinstance(record, dict) for record in payload):
        raise ValueError(f"Expected a JSON list of candidate records: {input_path}")
    cleaned = clean_candidate_records(payload)
    output_path.write_text(
        json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(payload), len(cleaned)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sanitise MiyKlas lexical-relation candidates.")
    parser.add_argument("input", type=Path, help="MiyKlas candidate JSON to clean.")
    parser.add_argument("output", type=Path, help="Destination JSON path.")
    args = parser.parse_args()
    before, after = clean_candidate_file(args.input, args.output)
    print(f"MiyKlas candidates: before={before} after={after} removed={before - after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
