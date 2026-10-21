"""Derive every L1 leaf field from a parser record (design r3 §4, §6.1, §6.2).

Nothing here is copied from a previous generation: keys, ``case_signal``,
``grammar_parsed``, ``norm_flags``, ``proposed_repairs``, ``refusal_code``,
``rights_class`` and ``row_sha256`` are recomputed from the record with the
bound normalizer every time a unit is (re-)parsed.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from scripts.lexdata import rule_tables
from scripts.lexdata.canonical import canonical_json, sha256_canonical
from scripts.lexdata.normalize import Normalized
from scripts.lexdata.records import LexItemRecord, UnitInput

Normalizer = Callable[[str], Normalized]

ROW_SHA256_FIELDS = (
    "raw_span", "surface", "key_stressed", "key_unstressed", "key_fold",
    "case_signal", "grammar_parsed", "homonym_marker", "norm_flags", "proposed_repairs",
    "refusal_code", "rights_class",
)


def item_key(unit: UnitInput, local_id: str) -> str:
    """Parser-stable leaf identity: source, unit locator and the parser's local id."""
    return canonical_json([unit.source_id, unit.l0_locator, local_id])


def row_sha256(fields: dict[str, Any], *, parent_item_key: str | None, member_index: int | None,
               role: str) -> str:
    """§6.2: SHA-256 of the canonical JSON of the leaf's derived content and binding."""
    content = {name: fields[name] for name in ROW_SHA256_FIELDS}
    content["binding"] = {"parent_item_key": parent_item_key, "member_index": member_index, "role": role}
    return sha256_canonical(content)


def derive_leaf(unit: UnitInput, item: LexItemRecord, *, normalizer: Normalizer, rights_class: str,
                importer_version: str) -> dict[str, Any]:
    """Return the L1 column values for one leaf (ids and FKs are set by the writer)."""
    normalized = normalizer(item.raw_span)
    refusal = item.parser_refusal or normalized.refusal_code
    accepted = refusal is None
    repairs = [repair.as_json() for repair in item.proposed_repairs] + list(normalized.proposed_repairs)
    grammar = rule_tables.map_grammar_labels(item.grammar_labels) if item.grammar_labels else None
    fields: dict[str, Any] = {
        "raw_span": item.raw_span,
        "surface": normalized.surface,
        "key_stressed": normalized.key_stressed if accepted else None,
        "key_unstressed": normalized.key_unstressed if accepted else None,
        "key_fold": normalized.key_fold if accepted else None,
        "case_signal": normalized.case_signal if accepted else None,
        "grammar_parsed": None if grammar is None else canonical_json(grammar),
        "homonym_marker": item.homonym_marker,
        "norm_flags": canonical_json(list(normalized.norm_flags)),
        "proposed_repairs": canonical_json(repairs),
        "refusal_code": refusal,
        "rights_class": rights_class,
    }
    parent_key = None if item.parent is None else item_key(unit, item.parent)
    fields["row_sha256"] = row_sha256(fields, parent_item_key=parent_key, member_index=item.member_index,
                                      role=item.role)
    fields.update({
        "item_key": item_key(unit, item.local_id),
        "parent_item_key": parent_key,
        "line_no": item.line_no,
        "span_start": item.span_start,
        "span_end": item.span_end,
        "member_index": item.member_index,
        "role": item.role,
        "grammar_raw": item.grammar_raw,
        "importer_version": importer_version,
    })
    return fields
