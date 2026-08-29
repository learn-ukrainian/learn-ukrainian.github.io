#!/usr/bin/env python3
"""Build the metadata-only P1 source and applicability freeze.

This command reads already committed, text-free receipts.  It does not read
source rows, call a provider, create labels, or emit dataset records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
ADMISSION = DATA / "admission"
EVIDENCE = DATA / "evidence"
OUTPUT = EVIDENCE / "phase3_p1_universe_freeze_v1.json"

OUTCOME_SHA256 = "890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47"
FREEZE_COMMIT = "59de8c451df4904b859d8ba4714da223a9ecbd21"
ADMISSION_CUTOFF = "2026-08-29"

MODERN_CONTACT_CLASSES = [
    "russian",
    "belarusian",
    "bulgarian",
    "macedonian",
    "serbian_cyrillic",
    "montenegrin_cyrillic",
]
HISTORICAL_PROTECTED_CLASSES = [
    "old_east_slavic_kyivan_rus",
    "middle_ukrainian",
    "church_slavonic_recension",
    "source_attested_rusyn",
]
FAIL_CLOSED_CLASSES = [
    "other_or_unresolved_slavic_cyrillic",
    "mixed_identity",
    "non_slavic_cyrillic",
    "latin_script_slavic",
    "unknown",
]
CONTEXT_ROLES = [
    "unmarked_modern_ukrainian",
    "quotation",
    "code_switch",
    "transliteration",
    "metalinguistic_example",
    "name_title",
    "dialect_or_regional_form",
    "historical_text",
    "ambiguous_noisy",
]

LEGACY_LEDGER_FAMILIES = {
    "antonenko_style_guide": "normative",
    "antonenko_textbook_representation": "school",
    "calque_inventory": "normative",
    "ua_gec": "correction",
    "school_textbooks": "school",
    "pravopys_2019_complete": "normative",
    "pravopys_2026_complete": "normative",
    "other_normative_style_inventory": "normative",
    "lexical_balla_en_uk": "normative_lexical",
    "lexical_dmklinger_uk_en": "normative_lexical",
    "lexical_esum_cognate_forms": "normative_lexical",
    "lexical_esum_etymology": "normative_lexical",
    "lexical_frazeolohichnyi": "normative_lexical",
    "lexical_grinchenko": "normative_lexical",
    "lexical_puls_cefr": "normative_lexical",
    "lexical_sum11": "normative_lexical",
    "lexical_ukrajinet": "normative_lexical",
    "lexical_wiktionary": "normative_lexical",
    "lexical_ulif": "normative_lexical",
    "lexical_vesum": "normative_lexical",
    "lexical_r2u": "normative_lexical",
}


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": relative(path), "sha256": sha256_file(path)}


def rights_state(capability: str) -> str:
    if capability in {
        "mit",
        "cc_by_nc_4_0_noncommercial_only",
        "private_inspection_and_locator_evidence_only",
        "private_research_only",
        "public_training_with_share_alike_and_attribution",
        "public_training_with_attribution",
    }:
        return "scoped_capability"
    return "unknown"


def blocked_lanes(state: str, disposition: str) -> list[str]:
    lanes = ["local_model_learning", "dataset_publication"] if state == "unknown" else []
    if disposition in {"blocked_with_reason", "unresolved"}:
        lanes.append("source_admission")
    return lanes


def source_unit(
    *,
    source_unit_id: str,
    source_class: str,
    unit_grain: str,
    unit_count: int,
    identity_sha256: str,
    source_artifact: dict[str, Any],
    provenance: dict[str, Any],
    capability: str,
    disposition: str,
    block_reason: str | None = None,
    identity_candidates: list[str] | None = None,
) -> dict[str, Any]:
    rights = {
        "capability_state": capability,
        "required_state": rights_state(capability),
        "blocked_lanes": blocked_lanes(rights_state(capability), disposition),
    }
    value: dict[str, Any] = {
        "source_unit_id": source_unit_id,
        "source_class": source_class,
        "unit_grain": unit_grain,
        "unit_count": unit_count,
        "identity_sha256": identity_sha256,
        "source_artifact": source_artifact,
        "provenance": provenance,
        "rights": rights,
        "source_unit_disposition": disposition,
        "metadata_only": True,
    }
    if block_reason is not None:
        value["block_reason"] = block_reason
    if identity_candidates is not None:
        value["identity_candidates"] = identity_candidates
    return value


def policy_units(path: Path, additive_path: Path) -> list[dict[str, Any]]:
    policy = read_json(path)
    additive = read_json(additive_path)
    sources = [(source, path) for source in policy["sources"]]
    for source in additive["sources"]:
        source_id = source.get("source_id") or source["source_file"]
        if source_id not in {(item.get("source_id") or item["source_file"]) for item, _ in sources}:
            sources.append((source, additive_path))
    units = []
    for source, source_path in sorted(sources, key=lambda item: item[0].get("source_id") or item[0]["source_file"]):
        source_id = source.get("source_id") or source["source_file"]
        final_disposition = source.get("final_disposition", source.get("content_disposition"))
        disposition = {
            "admit_scoped": "supporting_only",
            "contextual_only": "supporting_only",
            "quarantine": "blocked_with_reason",
        }.get(final_disposition, "unresolved")
        capability = source.get("rights_capability", "unknown")
        units.append(
            source_unit(
                source_unit_id=f"policy.{source_id}",
                source_class="operator_supplied_university" if source.get("source_kind", "university_jsonl") == "university_jsonl" else "qualified_reference",
                unit_grain="admission_policy_source_record",
                unit_count=1,
                identity_sha256=sha256_bytes(canonical_json(source)),
                source_artifact=artifact(source_path),
                provenance={"source_id": source_id, "evidence_hashes": source.get("evidence_hashes", []) or [source.get("evidence", {}).get("jsonl_sha256", "unknown")]},
                capability=capability,
                disposition=disposition,
                block_reason=("admission_policy_quarantine" if disposition == "blocked_with_reason" else "rights_capability_not_declared" if capability == "unknown" else None),
            )
        )
    return units


def historical_units(path: Path) -> list[dict[str, Any]]:
    receipt = read_json(path)
    source_artifact = artifact(path)
    units = []
    for collection in sorted(receipt["collections"], key=lambda item: item["collection_id"]):
        rights = collection["rights"]
        disposition = "protected"
        capability = rights.get("reuse_scope", "unknown")
        units.append(
            source_unit(
                source_unit_id=f"historical.{collection['collection_id']}",
                source_class="historical",
                unit_grain="historical_collection_receipt",
                unit_count=1,
                identity_sha256=sha256_bytes(canonical_json(collection)),
                source_artifact=source_artifact,
                provenance={
                    "collection_id": collection["collection_id"],
                    "source_kind": collection["source_kind"],
                    "counts": collection["counts"],
                    "residual_gap_ids": collection["residual_gap_ids"],
                },
                capability=capability,
                disposition=disposition,
                block_reason="historical_semantic_review_pending",
                identity_candidates=(
                    ["old_east_slavic_kyivan_rus", "church_slavonic_recension"]
                    if collection["collection_id"] != "ud-old-east-slavic-ruthenian-05a029e00ccf"
                    else ["old_east_slavic_kyivan_rus", "source_attested_rusyn"]
                ),
            )
        )
    return units


def legacy_units(receipt_path: Path, evidence_dir: Path) -> list[dict[str, Any]]:
    receipt = read_json(receipt_path)
    receipt_artifact = artifact(receipt_path)
    units = []
    for family in sorted(receipt["families"], key=lambda item: item["family_id"]):
        family_id = family["family_id"]
        if family_id in LEGACY_LEDGER_FAMILIES and "ledger_file" in family:
            path = evidence_dir / family["ledger_file"]
            source_artifact = artifact(path)
            identity_sha = sha256_bytes(canonical_json({"family_id": family_id, "ledger_sha256": family["ledger_sha256"], "unit_count": family["unit_count"]}))
            provenance = {"freeze_receipt": receipt_artifact, "family_id": family_id, "ledger_sha256": family["ledger_sha256"]}
        elif family_id in LEGACY_LEDGER_FAMILIES:
            path = evidence_dir / "lexical_structural_freeze_v1.json"
            source_artifact = artifact(path)
            identity_sha = family["structural_universe_sha256"]
            provenance = {"freeze_receipt": receipt_artifact, "family_id": family_id, "structural_universe_sha256": identity_sha}
        else:
            continue
        units.append(
            source_unit(
                source_unit_id=f"ledger.{family_id}",
                source_class=LEGACY_LEDGER_FAMILIES[family_id],
                unit_grain="frozen_source_ledger" if "ledger_file" in family else "frozen_structural_index",
                unit_count=family["unit_count"],
                identity_sha256=identity_sha,
                source_artifact=source_artifact,
                provenance=provenance,
                capability="locator_only_and_source_text_not_committed",
                disposition="rights_limited_locator_only",
                block_reason="source_text_rights_not_committed",
            )
        )
    return units


def cell(cell_id: str, language: str, context: str, phenomenon: str, role: str, status: str, protection_required: bool) -> dict[str, Any]:
    return {
        "cell_id": cell_id,
        "language_identity": language,
        "context_role": context,
        "phenomenon": phenomenon,
        "role": role,
        "status": status,
        "protection_required": protection_required,
    }


def required_cells() -> list[dict[str, Any]]:
    cells = [
        cell(f"modern.{language}.unmarked.contact_interference.source_backed_correction", language, "unmarked_modern_ukrainian", "contact_interference", "source_backed_correction", "coverage_blocked", False)
        for language in MODERN_CONTACT_CLASSES
    ]
    cells.extend(
        cell(f"historical.{language}.historical_text.historical_identity.protected_historical", language, "historical_text", "historical_identity", "protected_historical", "coverage_blocked", True)
        for language in HISTORICAL_PROTECTED_CLASSES
    )
    cells.extend(
        [
            cell("boundary.other_or_unresolved_slavic_cyrillic.ambiguous_noisy.scope_boundary.abstention", "other_or_unresolved_slavic_cyrillic", "ambiguous_noisy", "scope_boundary", "abstention", "coverage_blocked", True),
            cell("boundary.mixed_identity.ambiguous_noisy.scope_boundary.abstention", "mixed_identity", "ambiguous_noisy", "scope_boundary", "abstention", "coverage_blocked", True),
            cell("boundary.unknown.ambiguous_noisy.scope_boundary.abstention", "unknown", "ambiguous_noisy", "scope_boundary", "abstention", "coverage_blocked", True),
            cell("boundary.latin_script_slavic.ambiguous_noisy.scope_boundary.not_applicable", "latin_script_slavic", "ambiguous_noisy", "scope_boundary", "not_applicable_with_evidence", "not_applicable_with_evidence", False),
            cell("boundary.non_slavic_cyrillic.ambiguous_noisy.scope_boundary.not_applicable", "non_slavic_cyrillic", "ambiguous_noisy", "scope_boundary", "not_applicable_with_evidence", "not_applicable_with_evidence", False),
        ]
    )
    return cells


def build_manifest() -> dict[str, Any]:
    policy_path = ADMISSION / "phase3_complete_source_policy_v4.json"
    additive_path = ADMISSION / "phase3_vspu_additive_university_source_policy_v3.json"
    historical_path = ADMISSION / "phase3_historical_evidence_spine_v2.json"
    legacy_receipt = EVIDENCE / "source_universe_v1/source-universe-freeze-receipt.json"
    legacy_dir = EVIDENCE / "source_universe_v1"
    source_units = policy_units(policy_path, additive_path) + historical_units(historical_path) + legacy_units(legacy_receipt, legacy_dir)
    source_units.sort(key=lambda item: item["source_unit_id"])
    source_refs = [policy_path, additive_path, historical_path, legacy_receipt, legacy_dir / "lexical_structural_freeze_v1.json"]
    return {
        "schema_version": "phase3_p1_universe_freeze_v1",
        "text_free": True,
        "status": "INVENTORIED",
        "controlling_outcome_sha256": OUTCOME_SHA256,
        "freeze": {
            "admission_cutoff": ADMISSION_CUTOFF,
            "freeze_commit": FREEZE_COMMIT,
            "later_source_policy": "later_source_requires_new_dataset_version",
            "generator": {"path": relative(Path(__file__)), "sha256": sha256_file(Path(__file__))},
        },
        "source_manifest": {
            "source_unit_count": len(source_units),
            "source_units": source_units,
            "source_unit_identity_rule": "one_entry_per_frozen_source_artifact_or_collection; identity_sha256 is canonical metadata identity; unit_count remains denominator-visible",
            "disposition_rule": "exactly_one_source_unit_disposition_per_entry",
            "input_artifacts": [artifact(path) for path in sorted(source_refs, key=relative)],
        },
        "language_universe": {
            "target_language_identity": "modern_standard_ukrainian",
            "modern_contact_classes": MODERN_CONTACT_CLASSES,
            "modern_contact_classes_exhaustive": True,
            "historical_protected_classes": HISTORICAL_PROTECTED_CLASSES,
            "fail_closed_classes": FAIL_CLOSED_CLASSES,
            "span_fields_required": ["language_identity", "script_profile", "context_role", "scope_status", "period", "region", "register", "recension_editorial_layer", "identity_candidates"],
            "context_roles": CONTEXT_ROLES,
            "script_is_language_identity": False,
            "unknown_mixed_and_unresolved_route": "out_of_scope_protected_or_abstain",
        },
        "historical_protection": {
            "historical_forms_protected": True,
            "modern_correction_eligible": False,
            "old_east_slavic_is_modern_russian": False,
            "historical_ruskyi_auto_mapped_to_modern_russian": False,
            "automatic_mapping_to_modern_national_successor": False,
            "recension_and_editorial_layer_required": True,
        },
        "applicability": {
            "predicate_id": "phase3_p1_correction_applicability_v1",
            "result_when_true": "correction_eligible",
            "all_of": [
                {"field": "language_identity", "operator": "equals", "value": "modern_standard_ukrainian"},
                {"field": "script_profile", "operator": "equals", "value": "cyrillic"},
                {"field": "context_role", "operator": "equals", "value": "unmarked_modern_ukrainian"},
                {"field": "contrasted_contact_class", "operator": "in", "values": MODERN_CONTACT_CLASSES},
                {"field": "scope_status", "operator": "equals", "value": "in_scope"},
                {"field": "human_adjudication", "operator": "equals", "value": "source_qualified"},
            ],
            "else_route": "abstain",
            "script_alone_is_insufficient": True,
            "historical_span_relabel_forbidden": True,
        },
        "required_cell_manifest": {
            "dimension_order": ["language_identity", "context_role", "phenomenon", "role"],
            "implicit_cartesian_product": False,
            "cells": required_cells(),
            "status_semantics": {
                "satisfied": "required coverage is source-backed and complete",
                "not_applicable_with_evidence": "evidence shows the cell does not apply; it never satisfies a protected_historical cell",
                "coverage_blocked": "required cell remains blocked by a named P1 residual",
                "unresolved": "required cell lacks enough evidence for a safe disposition",
            },
        },
        "safety": {
            "provider_calls": False,
            "labels_created": False,
            "dataset_rows_emitted": False,
            "gold_created": False,
            "training_performed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    value = build_manifest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json(value))
    print(f"wrote {relative(args.output) if args.output.is_relative_to(ROOT) else args.output}")
    print(f"source_units={value['source_manifest']['source_unit_count']} cells={len(value['required_cell_manifest']['cells'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
