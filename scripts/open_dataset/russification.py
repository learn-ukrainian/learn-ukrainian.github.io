"""Opt-in contrast projection and the default-split quarantine gate (#8989).

Inputs are source-cited projections of admitted word-card contrasts, never raw
СУМ-11 entries. This module does not adjudicate or certify those inputs.
"""

from __future__ import annotations

import copy
import json
import re
import unicodedata
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import ahocorasick

from scripts.projects.open_model_data.review_build.output import OutputGuard

SCHEMA = "russification-contrast.v1"
CARD = Path(__file__).with_name("RUSSIFICATION_DATASET_CARD.md")
MODERN_SOURCES = frozenset({"sum20", "ulif", "vts_busel_slovnyk_me"})
QUARANTINE_FIELDS = frozenset({
    "russification_exposed", "soviet_colonization_context", "sovietization_risk", "sovietization_keywords",
})
SUM11 = re.compile(r"(?:sum|сум)[\s_\-–—]*11(?!\d)|sum\.in\.ua|slovnyk\.me/dict/sum/", re.IGNORECASE)


class QuarantineError(ValueError):
    """Unsafe or incomplete data; diagnostics never include source quotations."""


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _fold(text: str) -> str:
    """Fold apostrophes, acute stress, NFC, case and whitespace for matching."""
    text = text.translate(str.maketrans("’ʼ`", "'''")).replace("\u0301", "")
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key)
            yield from _strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item)


class QuarantineGate:
    """Compile the frozen quotation inventory once for all files in a package."""

    def __init__(self, sum11_texts: Iterable[str] = ()) -> None:
        automaton = ahocorasick.Automaton()
        for text in sum11_texts:
            if not _text(text):
                raise QuarantineError("invalid_sum11_inventory")
            automaton.add_word(_fold(text), True)
        self.quotations = automaton if len(automaton) else None
        if self.quotations is not None:
            self.quotations.make_automaton()

    def validate(self, records: Iterable[Any]) -> int:
        """Reject a whole default split on the first contaminated record."""
        count = 0
        for record in records:
            for text in _strings(record):
                folded = _fold(text)
                if (
                    SUM11.search(folded)
                    or folded in QUARANTINE_FIELDS
                    or folded == SCHEMA
                    or (self.quotations is not None and next(self.quotations.iter(folded), None) is not None)
                ):
                    raise QuarantineError("sum11_in_default_split")
            count += 1
        return count


def validate_default_split(records: Iterable[Any], *, sum11_texts: Iterable[str] = ()) -> int:
    """Reject quarantined provenance and known quotations, including nested text.

    Pass the independently frozen СУМ-11 quotation inventory for a content audit.
    Without that inventory this checks provenance only; unlabelled text cannot
    be attributed to a dictionary from its characters alone.
    """
    return QuarantineGate(sum11_texts).validate(records)


def build_contrastive_subset(records: Iterable[dict[str, Any]], *, opt_in: bool = False) -> list[dict[str, Any]]:
    """Validate and project complete pairs only after explicit opt-in.

    Each side carries a verbatim quotation and a citation with a source id,
    snapshot, locator and attribution. The norm also names its card assertion.
    Unknown fields are refused rather than exported as standalone Soviet text.
    """
    if opt_in is not True:
        raise QuarantineError("explicit_opt_in_required")
    result = []
    seen = set()
    for record in records:
        if not isinstance(record, dict) or set(record) != {
            "pair_id", "sense_id", "imposed", "norm", "distortion_type",
        }:
            raise QuarantineError("contrast_pair_required")
        if not all(_text(record[key]) for key in ("pair_id", "sense_id", "distortion_type")):
            raise QuarantineError("contrast_identity_required")
        if record["pair_id"] in seen:
            raise QuarantineError("duplicate_contrast_pair")
        seen.add(record["pair_id"])
        for side in ("imposed", "norm"):
            value = record[side]
            fields = {"text", "citation", "assertion_id"} if side == "norm" else {
                "text", "citation", "sovietization_risk", "sovietization_keywords",
            }
            if not isinstance(value, dict) or set(value) != fields or not _text(value.get("text")):
                raise QuarantineError("both_quoted_sides_required")
            citation = value["citation"]
            if not isinstance(citation, dict) or set(citation) != {
                "source_id", "snapshot_id", "locator", "attribution",
            } or not all(_text(item) for item in citation.values()):
                raise QuarantineError("both_citations_required")
            source = citation["source_id"]
            if (side == "imposed" and source != "sum11") or (side == "norm" and source not in MODERN_SOURCES):
                raise QuarantineError("contrast_source_role_mismatch")
        imposed, norm = record["imposed"], record["norm"]
        if (
            type(imposed["sovietization_risk"]) is not int
            or imposed["sovietization_risk"] not in {0, 1, 2}
            or not isinstance(imposed["sovietization_keywords"], list)
            or not all(_text(item) for item in imposed["sovietization_keywords"])
            or not _text(norm["assertion_id"])
        ):
            raise QuarantineError("contrast_evidence_required")
        if _fold(imposed["text"]) == _fold(norm["text"]):
            raise QuarantineError("distinct_correction_required")
        validate_default_split([norm])
        result.append({
            "schema": SCHEMA,
            "opt_in": True,
            "for_pretraining": False,
            "soviet_colonization_context": copy.deepcopy(record),
        })
    return sorted(result, key=lambda row: row["soviet_colonization_context"]["pair_id"])


def write_contrastive_subset(
    records: Iterable[dict[str, Any]], output: Path, *, opt_in: bool = False,
) -> int:
    """Write a separate host-only JSONL and card under the existing output guard.

    No publication or certification is performed. Invalid inputs write no data.
    """
    if opt_in is not True:
        raise QuarantineError("explicit_opt_in_required")
    with OutputGuard(output) as guard:
        pairs = build_contrastive_subset(records, opt_in=opt_in)
        content = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in pairs)
        guard.write("russification-contrast.jsonl", content.encode("utf-8"))
        guard.write("README.md", CARD.read_bytes())
    return len(pairs)
