#!/usr/bin/env python3
"""Freeze P2's metadata-only canonical rule and adjudication contracts (#7426).

The generator reads only the committed P1 metadata manifest.  It never opens
source/evidence bodies, produces a linguistic claim, calls a provider, labels,
or trains a model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
P1 = DATA / "evidence/phase3_p1_universe_freeze_v1.json"
P1_DIALECT_REGIONAL_AMENDMENT = (
    DATA / "evidence/phase3_p1_dialect_regional_protection_amendment_v1.json"
)
OUTPUT = DATA / "evidence/phase3_p2_canonical_contracts_v1.json"

OUTCOME_SHA256 = "890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47"
SCHEMA_VERSION = "phase3_p2_canonical_contracts_v1"
PINNED_P1_MANIFEST_SHA256 = "0b1cd81448b96b4e818aa1dedd7df7633ff88eb500bb4d6ac3668be02962a35b"
PINNED_P1_DIALECT_REGIONAL_AMENDMENT_SHA256 = "5a4b259f764a3d41499f0a989c02fed921c18b62c9831d361d18d19dcc948afa"
RULE_SLOT_ALGORITHM_VERSION = "phase3_p2_rule_admission_and_identity_v1"
CASE_RECORD_KINDS = frozenset(
    {
        "correct_modern_production",
        "source_backed_correction",
        "minimal_contrast",
        "protected_historical_context",
        "protected_dialect_or_regional_context",
        "abstention",
        "not_applicable_with_evidence",
        "coverage_blocked",
    }
)
RULE_SLOT_IDENTITY_FIELDS = (
    "coverage_stratum_id",
    "claim_type",
    "source_class",
    "identity_candidate",
    "applicability_predicate_id",
    "evidence_set_sha256",
    "adjudication_record_sha256",
)
HISTORICAL_PROTECTED_CLASSES = (
    "old_east_slavic_kyivan_rus",
    "middle_ukrainian",
    "church_slavonic_recension",
    "source_attested_rusyn",
)
HISTORICAL_PROTECTION_INVARIANTS = {
    "historical_forms_protected": True,
    "modern_correction_eligible": False,
    "old_east_slavic_is_modern_russian": False,
    "historical_ruskyi_auto_mapped_to_modern_russian": False,
    "automatic_mapping_to_modern_national_successor": False,
    "recension_and_editorial_layer_required": True,
}


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def artifact(path: Path) -> dict[str, str]:
    return {"path": relative(path), "sha256": sha256_file(path)}


def read_p1() -> dict[str, Any]:
    if sha256_file(P1) != PINNED_P1_MANIFEST_SHA256:
        raise ValueError("p1_artifact_sha_drift")
    value = json.loads(P1.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("p1_manifest_not_object")
    if value.get("schema_version") != "phase3_p1_universe_freeze_v1":
        raise ValueError("p1_schema_drift")
    if value.get("controlling_outcome_sha256") != OUTCOME_SHA256:
        raise ValueError("p1_outcome_drift")
    if value.get("text_free") is not True:
        raise ValueError("p1_not_text_free")
    return value


def read_dialect_regional_amendment() -> dict[str, Any]:
    if sha256_file(P1_DIALECT_REGIONAL_AMENDMENT) != PINNED_P1_DIALECT_REGIONAL_AMENDMENT_SHA256:
        raise ValueError("p1_dialect_regional_amendment_sha_drift")
    value = json.loads(P1_DIALECT_REGIONAL_AMENDMENT.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("p1_dialect_regional_amendment_not_object")
    if value.get("schema_version") != "phase3_p1_dialect_regional_protection_amendment_v1":
        raise ValueError("p1_dialect_regional_amendment_schema_drift")
    if value.get("controlling_outcome_sha256") != OUTCOME_SHA256 or value.get("text_free") is not True:
        raise ValueError("p1_dialect_regional_amendment_outcome_drift")
    if value.get("base_p1_manifest") != artifact(P1):
        raise ValueError("p1_dialect_regional_amendment_base_drift")
    return value


def _composite_cells(p1: dict[str, Any], amendment: dict[str, Any]) -> list[dict[str, Any]]:
    base_cells = p1.get("required_cell_manifest", {}).get("cells")
    additive_cells = amendment.get("amendment", {}).get("additive_cells")
    if not isinstance(base_cells, list) or not isinstance(additive_cells, list):
        raise ValueError("p1_composite_shape_drift")
    cells = [*base_cells, *additive_cells]
    identifiers = [cell.get("cell_id") for cell in cells if isinstance(cell, dict)]
    if len(cells) != 16 or len(identifiers) != 16 or len(set(identifiers)) != 16:
        raise ValueError("p1_composite_denominator_drift")
    if amendment.get("amendment", {}).get("composite_required_cell_count") != len(cells):
        raise ValueError("p1_amendment_count_drift")
    return cells


def build_contract() -> dict[str, Any]:
    p1 = read_p1()
    dialect_amendment = read_dialect_regional_amendment()
    source_units = p1.get("source_manifest", {}).get("source_units")
    base_cells = p1.get("required_cell_manifest", {}).get("cells")
    cells = _composite_cells(p1, dialect_amendment)
    if not isinstance(source_units, list) or not isinstance(base_cells, list):
        raise ValueError("p1_shape_drift")
    unknown_rights = sum(
        1
        for unit in source_units
        if isinstance(unit, dict)
        and isinstance(unit.get("rights"), dict)
        and unit["rights"].get("required_state") == "unknown"
    )
    if len(source_units) != 57 or unknown_rights != 39 or len(base_cells) != 15:
        raise ValueError("p1_denominator_drift")
    composite_input = {
        "base_p1_manifest_sha256": PINNED_P1_MANIFEST_SHA256,
        "dialect_regional_amendment_sha256": PINNED_P1_DIALECT_REGIONAL_AMENDMENT_SHA256,
        "composite_required_cell_statuses": [
            {"cell_id": cell["cell_id"], "status": cell["status"]}
            for cell in sorted(cells, key=lambda item: item["cell_id"])
        ],
    }
    composite_input_sha256 = sha256_bytes(canonical_json(composite_input))
    algorithm = {
        "algorithm_version": RULE_SLOT_ALGORITHM_VERSION,
        "derivation": "future_rule_slots_are_atomic_metadata_identities; p1_cells_are_coverage_strata_not_rules",
        "input_composite_manifest_sha256": composite_input_sha256,
        "atomic_identity_fields": list(RULE_SLOT_IDENTITY_FIELDS),
        "admission_requirements": [
            "source_qualified_claim_typed_evidence",
            "registered_qualified_human_adjudication",
            "immutable_adjudication_record_sha256",
            "unique_canonical_rule_slot_id",
        ],
        "slot_id_rule": "p2_rule_slot:sha256_canonical_atomic_identity",
    }
    algorithm["algorithm_sha256"] = sha256_bytes(canonical_json(algorithm))
    slots: list[dict[str, Any]] = []
    return {
        "schema_version": SCHEMA_VERSION,
        "text_free": True,
        "status": "FROZEN_METADATA_ONLY",
        "controlling_outcome_sha256": OUTCOME_SHA256,
        "p1_binding": {
            "p1_manifest": artifact(P1),
            "dialect_regional_protection_amendment": artifact(P1_DIALECT_REGIONAL_AMENDMENT),
            "source_unit_count": len(source_units),
            "unknown_rights_blocker_count": unknown_rights,
            "required_cell_count": len(base_cells),
            "required_cell_statuses": [
                {"cell_id": cell["cell_id"], "status": cell["status"]} for cell in sorted(base_cells, key=lambda item: item["cell_id"])
            ],
            "composite_required_cell_count": len(cells),
            "composite_required_cell_statuses": composite_input["composite_required_cell_statuses"],
            "composite_input_sha256": composite_input_sha256,
        },
        "rule_slot_universe": {
            "symbol": "R",
            "algorithm": algorithm,
            "slot_count": len(slots),
            "slots": slots,
            "rule_manifest_sha256": sha256_bytes(canonical_json(slots)),
            "rule_manifest_version": "phase3_p2_rule_manifest_v1",
            "coverage_strata_are_rules": False,
            "merge_criteria": {"permitted": True, "requires": ["source_qualified_claim_typed_evidence", "registered_qualified_human_adjudication", "all_parent_slot_ids"], "preserves": ["coverage_stratum_id", "case_denominator", "atomic_identity_lineage"], "version_effect": "new_rule_manifest_version_with_all_parent_lineage"},
            "split_criteria": {"permitted": True, "requires": ["source_qualified_claim_typed_evidence", "registered_qualified_human_adjudication", "parent_slot_id"], "preserves": ["coverage_stratum_id", "case_denominator", "atomic_identity_lineage"], "version_effect": "new_rule_manifest_version_with_parent_child_lineage"},
            "denominator_change_policy": "new_p1_manifest_sha256_and_new_dataset_version_required",
            "substantive_rule_claims": "not_frozen",
        },
        "evidence_contract": {
            "claim_typed_roles": [
                "applicability_scope",
                "correction_authority",
                "minimal_contrast_authority",
                "protected_historical_identity",
                "protected_dialect_or_regional_identity",
                "rights_provenance",
                "source_qualified_human_adjudication",
                "abstention_or_not_applicable_authority",
            ],
            "role_assignment": "immutable_one_or_more_claim_typed_roles_per_future_case",
            "evidence_body_in_contract": False,
            "source_qualified_human_adjudication_required": True,
            "adjudication_may_not_be_replaced_by_model_output": True,
            "record_schema_ids": [
                "phase3_p2_case_record_v1",
                "phase3_p2_proposal_record_v1",
                "phase3_p2_promotion_decision_v1",
            ],
            "validator_functions": ["validate_contract_integrity", "validate_case_record", "validate_promotion", "validate_rule_slot_identity", "validate_rule_manifest_evolution"],
        },
        "adjudication_contract": {
            "registry_status": "FROZEN_NONADMITTING",
            "semantic_case_admission_permitted": False,
            "required_adjudicator_qualification": {
                "authority_kind": "source_qualified_human_adjudication",
                "actor_kind": "human",
                "qualification_status": "registered_source_qualified_human",
            },
            "required_adjudication_record": {
                "record_identity_rule": "sha256_canonical_adjudication_metadata",
                "record_sha256_required": True,
                "evidence_ref_ids_bound": True,
                "source_qualified_identity_bound": True,
            },
            "adjudication_registry_sha256": None,
        },
        "case_state_contract": {
            "structurally_distinct_states": [
                "correct_modern_production",
                "source_backed_correction",
                "minimal_contrast",
                "protected_historical_context",
                "protected_dialect_or_regional_context",
                "abstention",
                "not_applicable_with_evidence",
                "coverage_blocked",
            ],
            "exactly_one_primary_state_per_case": True,
            "coverage_blocked_emits_case": False,
            "coverage_blocked_record_kind": "coverage_blocked",
            "protected_historical_is_not_modern_correction": True,
            "protected_dialect_or_regional_is_not_modern_correction": True,
        },
        "proposal_contract": {
            "model_or_tool_proposals_permitted": True,
            "proposal_provenance_required": True,
            "proposal_may_promote_to_gold": False,
            "proposal_may_replace_human_adjudication": False,
            "gold_authorship_by_models": False,
            "proposal_fingerprint": "sha256_canonical_metadata_without_proposal_sha256",
            "proposal_metadata_fingerprint": "sha256_canonical_proposal_metadata",
            "proposal_input_binding": "p1_base_plus_dialect_regional_amendment_composite_input_sha256",
            "current_rule_manifest_allows_promotion": False,
        },
        "fail_closed_invariants": {
            "rights_or_provenance_unknown_blocks_admission": True,
            "historical_non_erasure": "protected_historical_context_requires_source_period_region_recension_and_no_modern_normalization",
            "historical_auto_normalization_forbidden": "historical_or_rusyn_identity_may_not_be_mapped_to_modern_national_successor",
            "historical_protection_invariants": p1["historical_protection"],
            "dialect_regional_protection_invariants": dialect_amendment["dialect_regional_protection"],
            "unregistered_adjudication_blocks_semantic_case_admission": True,
            "unresolved_identity_routes_to_abstention_or_protection": True,
            "missing_claim_typed_evidence_blocks_promotion": True,
            "provider_calls": False,
            "labels_created": False,
            "gold_created": False,
            "training_performed": False,
        },
        "generator": artifact(Path(__file__)),
    }


def _metadata_identifier(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and len(value) <= 256


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _is_rule_slot_id(value: Any) -> bool:
    prefix = "p2_rule_slot:"
    return isinstance(value, str) and value.startswith(prefix) and _is_sha256(value.removeprefix(prefix))


def _proposal_sha256(proposal: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json({key: value for key, value in proposal.items() if key != "proposal_sha256"}))


def _historical_protection_is_exact(p1: dict[str, Any]) -> bool:
    """Keep protected records bound to P1's non-erasure contract, not assertions."""
    return (
        p1.get("language_universe", {}).get("historical_protected_classes")
        == list(HISTORICAL_PROTECTED_CLASSES)
        and p1.get("historical_protection") == HISTORICAL_PROTECTION_INVARIANTS
    )


def validate_contract_integrity(contract: dict[str, Any]) -> bool:
    """Accept only the exact deterministic P2 contract for the pinned P1 input."""
    if not isinstance(contract, dict):
        return False
    try:
        expected = build_contract()
    except (OSError, ValueError, KeyError, TypeError):
        return False
    # Canonical equality recomputes the pinned P1 binding, the algorithm hash,
    # empty rule-manifest hash, cardinality, and every contract invariant.
    return canonical_json(contract) == canonical_json(expected)


def validate_case_record(record: dict[str, Any], contract: dict[str, Any] | None = None) -> bool:
    """Validate one metadata-only case/coverage record without promotion.

    This is intentionally executable rather than a prose convention. It
    rejects text-bearing fields, model authority, missing claim-typed evidence,
    and state-shape confusion. With P2's empty ``R``, no proposed semantic case
    can become an admitted rule-backed record.
    """
    if not isinstance(record, dict) or record.get("record_kind") not in CASE_RECORD_KINDS:
        return False
    if any(key in record for key in ("source_text", "evidence_text", "gold_text", "content")):
        return False
    if contract is not None and not validate_contract_integrity(contract):
        return False
    contract_value = build_contract()
    p1 = read_p1()
    dialect_amendment = read_dialect_regional_amendment()
    cells = {
        cell["cell_id"]: cell
        for cell in _composite_cells(p1, dialect_amendment)
        if isinstance(cell, dict)
    }
    units = {
        unit["source_unit_id"]: unit
        for unit in p1["source_manifest"]["source_units"]
        if isinstance(unit, dict)
    }
    kind = record["record_kind"]
    if kind == "coverage_blocked":
        return (
            set(record) == {"record_kind", "coverage_stratum_id", "blocker_code"}
            and record["coverage_stratum_id"] in cells
            and cells[record["coverage_stratum_id"]]["status"] == "coverage_blocked"
            and _metadata_identifier(record["blocker_code"])
        )
    # No registry of qualified adjudicators or immutable adjudication records is
    # frozen in P2.  An authority object supplied by a caller is therefore not
    # admissible evidence.  Keep every semantic state blocked until that future
    # registry is independently frozen and hash-bound in a new contract version.
    if contract_value["adjudication_contract"]["semantic_case_admission_permitted"] is not True:
        return False
    base = {"record_kind", "record_id", "coverage_stratum_id", "evidence_refs", "authority"}
    if not base <= set(record) or not _metadata_identifier(record["record_id"]):
        return False
    refs = record["evidence_refs"]
    authority = record["authority"]
    cell = cells.get(record["coverage_stratum_id"])
    if cell is None or not isinstance(refs, list) or not refs:
        return False
    if kind == "not_applicable_with_evidence":
        if cell["status"] != "not_applicable_with_evidence":
            return False
    elif cell["status"] != "satisfied":
        return False
    if kind in {"protected_historical_context", "protected_dialect_or_regional_context"} and cell["protection_required"] is not True:
        return False
    allowed_roles = set(contract_value["evidence_contract"]["claim_typed_roles"])
    seen_ids: set[str] = set()
    roles: set[str] = set()
    for ref in refs:
        if not isinstance(ref, dict) or set(ref) != {"evidence_ref_id", "claim_role", "source_unit_id", "source_class", "identity_candidate", "coverage_stratum_id", "source_unit_identity_sha256", "source_artifact_sha256", "provenance_sha256"}:
            return False
        identifier = ref["evidence_ref_id"]
        if not _metadata_identifier(identifier) or identifier in seen_ids or not _metadata_identifier(ref["source_unit_id"]):
            return False
        unit = units.get(ref["source_unit_id"])
        if unit is None or ref["claim_role"] not in allowed_roles or ref["coverage_stratum_id"] != record["coverage_stratum_id"]:
            return False
        if ref["source_class"] != unit.get("source_class") or not _metadata_identifier(ref["identity_candidate"]):
            return False
        candidates = unit.get("identity_candidates")
        if isinstance(candidates, list) and ref["identity_candidate"] not in candidates:
            return False
        if unit.get("rights", {}).get("required_state") != "scoped_capability" or unit.get("source_unit_disposition") not in {"supporting_only", "protected"}:
            return False
        if ref["source_unit_identity_sha256"] != unit.get("identity_sha256") or ref["source_artifact_sha256"] != unit.get("source_artifact", {}).get("sha256"):
            return False
        if ref["provenance_sha256"] != sha256_bytes(canonical_json(unit.get("provenance"))):
            return False
        seen_ids.add(identifier)
        roles.add(ref["claim_role"])
    if not isinstance(authority, dict) or set(authority) != {"authority_kind", "actor_kind", "adjudication_id", "evidence_ref_ids"}:
        return False
    if authority.get("authority_kind") != "source_qualified_human_adjudication" or authority.get("actor_kind") != "human" or not _metadata_identifier(authority.get("adjudication_id")):
        return False
    if authority.get("evidence_ref_ids") != sorted(seen_ids):
        return False
    required_roles = {
        "correct_modern_production": {"applicability_scope", "rights_provenance"},
        "source_backed_correction": {"applicability_scope", "correction_authority", "rights_provenance"},
        "minimal_contrast": {"minimal_contrast_authority", "rights_provenance"},
        "protected_historical_context": {"protected_historical_identity", "rights_provenance"},
        "protected_dialect_or_regional_context": {"protected_dialect_or_regional_identity", "rights_provenance"},
        "abstention": {"abstention_or_not_applicable_authority", "rights_provenance"},
        "not_applicable_with_evidence": {"abstention_or_not_applicable_authority", "rights_provenance"},
    }
    if not required_roles[kind] <= roles:
        return False
    if kind == "protected_historical_context":
        return (
            _historical_protection_is_exact(p1)
            and set(record)
            == base
            | {
                "historical_identity",
                "period_id",
                "region_id",
                "recension_editorial_layer",
                "modern_normalization",
            }
            and record["historical_identity"] in HISTORICAL_PROTECTED_CLASSES
            and all(
                _metadata_identifier(record[key])
                for key in ("historical_identity", "period_id", "region_id", "recension_editorial_layer")
            )
            and record["modern_normalization"] is False
        )
    if kind == "protected_dialect_or_regional_context":
        protection = dialect_amendment.get("dialect_regional_protection")
        return (
            protection
            == {
                "source_qualified_identity_required": True,
                "region_required": True,
                "register_required": True,
                "dialect_or_regional_forms_protected": True,
                "modern_correction_eligible": False,
                "automatic_normalization_to_modern_standard_ukrainian": False,
                "automatic_mapping_to_modern_national_successor": False,
                "identity_or_region_unknown_route": "coverage_blocked_or_abstention",
            }
            and set(record)
            == base
            | {"dialect_or_regional_identity", "region_id", "register_id", "source_qualified_identity", "modern_normalization"}
            and record["dialect_or_regional_identity"] == "source_attested_ukrainian_dialect_or_regional_form"
            and all(_metadata_identifier(record[key]) for key in ("region_id", "register_id"))
            and record["source_qualified_identity"] is True
            and record["modern_normalization"] is False
        )
    if kind == "abstention":
        return set(record) == base | {"abstention_reason_code"} and _metadata_identifier(record["abstention_reason_code"])
    if kind == "not_applicable_with_evidence":
        return set(record) == base | {"not_applicable_evidence_id"} and _metadata_identifier(record["not_applicable_evidence_id"])
    if kind == "minimal_contrast":
        return set(record) == base | {"contrast_pair_id", "rule_slot_id"} and _metadata_identifier(record["contrast_pair_id"]) and _rule_slot_admitted(record["rule_slot_id"], contract)
    if kind in {"correct_modern_production", "source_backed_correction"}:
        return set(record) == base | {"rule_slot_id"} and _rule_slot_admitted(record["rule_slot_id"], contract)
    return False


def _rule_slot_admitted(rule_slot_id: Any, contract: dict[str, Any] | None) -> bool:
    value = contract if contract is not None else build_contract()
    slots = value.get("rule_slot_universe", {}).get("slots", [])
    return isinstance(rule_slot_id, str) and any(
        isinstance(slot, dict) and slot.get("rule_slot_id") == rule_slot_id for slot in slots
    )


def validate_rule_slot_identity(slot: dict[str, Any], contract: dict[str, Any] | None = None) -> bool:
    """Validate a canonical future atomic slot without admitting one in P2."""
    value = contract if contract is not None else build_contract()
    if not validate_contract_integrity(value) or not isinstance(slot, dict):
        return False
    if set(slot) != {"rule_slot_id", "atomic_identity", "lineage_kind", "parent_slot_ids"}:
        return False
    identity = slot.get("atomic_identity")
    if not isinstance(identity, dict) or set(identity) != set(RULE_SLOT_IDENTITY_FIELDS):
        return False
    composite_cell_ids = {
        cell["cell_id"]
        for cell in _composite_cells(read_p1(), read_dialect_regional_amendment())
        if isinstance(cell, dict)
    }
    if identity["coverage_stratum_id"] not in composite_cell_ids or not _metadata_identifier(identity["claim_type"]):
        return False
    if not _metadata_identifier(identity["source_class"]) or not _metadata_identifier(identity["identity_candidate"]):
        return False
    if not _metadata_identifier(identity["applicability_predicate_id"]):
        return False
    if not _is_sha256(identity["evidence_set_sha256"]) or not _is_sha256(identity["adjudication_record_sha256"]):
        return False
    expected_id = "p2_rule_slot:" + sha256_bytes(canonical_json(identity))
    if slot["rule_slot_id"] != expected_id or slot["lineage_kind"] not in {"root", "split_child", "merge"}:
        return False
    parents = slot["parent_slot_ids"]
    if not isinstance(parents, list) or len(parents) != len(set(parents)) or not all(
        _is_rule_slot_id(parent) for parent in parents
    ):
        return False
    if (slot["lineage_kind"] == "root") != (parents == []):
        return False
    if slot["lineage_kind"] == "split_child" and len(parents) != 1:
        return False
    # This establishes deterministic structural identity only.  Admission is
    # separately denied by the current non-admitting adjudication registry.
    return slot["lineage_kind"] != "merge" or len(parents) >= 2


def _manifest_version_number(value: Any) -> int | None:
    prefix = "phase3_p2_rule_manifest_v"
    if not isinstance(value, str) or not value.startswith(prefix):
        return None
    suffix = value.removeprefix(prefix)
    return int(suffix) if suffix.isdecimal() and int(suffix) > 0 else None


def validate_rule_manifest_evolution(
    previous_manifest: dict[str, Any], next_manifest: dict[str, Any], contract: dict[str, Any] | None = None
) -> bool:
    """Validate a future versioned manifest evolution without admitting it in P2."""
    value = contract if contract is not None else build_contract()
    if not validate_contract_integrity(value) or not isinstance(previous_manifest, dict) or not isinstance(next_manifest, dict):
        return False
    previous_version = _manifest_version_number(previous_manifest.get("manifest_version"))
    if previous_version is None:
        return False
    previous_keys = {"manifest_version", "composite_input_sha256", "slots", "rule_manifest_sha256"}
    if previous_version > 1:
        previous_keys.add("parent_rule_manifest_sha256")
    if set(previous_manifest) != previous_keys:
        return False
    if previous_version > 1 and not _is_sha256(previous_manifest.get("parent_rule_manifest_sha256")):
        return False
    if set(next_manifest) != {"manifest_version", "composite_input_sha256", "parent_rule_manifest_sha256", "slots", "rule_manifest_sha256"}:
        return False
    previous_slots = previous_manifest.get("slots")
    next_slots = next_manifest.get("slots")
    if not isinstance(previous_slots, list) or not isinstance(next_slots, list):
        return False
    composite_input_sha256 = value["p1_binding"]["composite_input_sha256"]
    if (
        previous_manifest.get("composite_input_sha256") != composite_input_sha256
        or next_manifest.get("composite_input_sha256") != composite_input_sha256
    ):
        return False
    if not _is_sha256(previous_manifest["rule_manifest_sha256"]) or previous_manifest["rule_manifest_sha256"] != sha256_bytes(canonical_json(previous_slots)):
        return False
    if not _is_sha256(next_manifest.get("parent_rule_manifest_sha256")) or next_manifest["parent_rule_manifest_sha256"] != previous_manifest["rule_manifest_sha256"]:
        return False
    next_version = _manifest_version_number(next_manifest["manifest_version"])
    if previous_version is None or next_version != previous_version + 1:
        return False
    if not _is_sha256(next_manifest["rule_manifest_sha256"]) or next_manifest["rule_manifest_sha256"] != sha256_bytes(canonical_json(next_slots)):
        return False
    identifiers = [slot.get("rule_slot_id") for slot in next_slots if isinstance(slot, dict)]
    if len(identifiers) != len(next_slots) or len(identifiers) != len(set(identifiers)):
        return False
    if any(not validate_rule_slot_identity(slot, value) for slot in next_slots):
        return False
    if any(not validate_rule_slot_identity(slot, value) for slot in previous_slots):
        return False
    if [slot["rule_slot_id"] for slot in previous_slots] != sorted(slot["rule_slot_id"] for slot in previous_slots):
        return False
    if [slot["rule_slot_id"] for slot in next_slots] != sorted(slot["rule_slot_id"] for slot in next_slots):
        return False
    previous_by_id = {slot["rule_slot_id"]: slot for slot in previous_slots}
    next_by_id = {slot["rule_slot_id"]: slot for slot in next_slots}
    if not set(previous_by_id) <= set(next_by_id):
        return False
    if any(next_by_id[slot_id] != slot for slot_id, slot in previous_by_id.items()):
        return False
    for slot in next_slots:
        parent_ids = set(slot["parent_slot_ids"])
        if parent_ids and not parent_ids <= set(previous_by_id):
            return False
        if parent_ids and any(
            previous_by_id[parent_id]["atomic_identity"]["coverage_stratum_id"]
            != slot["atomic_identity"]["coverage_stratum_id"]
            for parent_id in parent_ids
        ):
            return False
    return True


def validate_promotion(
    proposal: dict[str, Any], promotion: dict[str, Any], contract: dict[str, Any] | None = None
) -> bool:
    """Allow only immutable non-promoting proposal disposition at P2.

    Model/tool proposals remain metadata candidates. They cannot supply human
    authority, mutate after fingerprinting, or become gold while ``R`` is
    empty.
    """
    if not isinstance(proposal, dict) or not isinstance(promotion, dict):
        return False
    if contract is not None and not validate_contract_integrity(contract):
        return False
    if set(proposal) != {"record_kind", "proposal_id", "producer_kind", "producer_provenance", "input_identity_sha256", "proposal_metadata", "proposal_metadata_sha256", "proposal_sha256"}:
        return False
    if proposal.get("record_kind") != "proposal" or proposal.get("producer_kind") not in {"model", "tool"}:
        return False
    if not _metadata_identifier(proposal.get("proposal_id")) or not all(
        _is_sha256(proposal.get(key)) for key in ("input_identity_sha256", "proposal_metadata_sha256", "proposal_sha256")
    ) or proposal.get("proposal_sha256") != _proposal_sha256(proposal):
        return False
    value = build_contract()
    if proposal["input_identity_sha256"] != value["p1_binding"]["composite_input_sha256"]:
        return False
    metadata = proposal.get("proposal_metadata")
    if not isinstance(metadata, dict) or set(metadata) != {"proposal_schema_version", "candidate_kind", "candidate_identity_sha256", "coverage_stratum_id"}:
        return False
    if metadata.get("proposal_schema_version") != "phase3_p2_proposal_metadata_v1" or not _metadata_identifier(metadata.get("candidate_kind")):
        return False
    if not _is_sha256(metadata.get("candidate_identity_sha256")):
        return False
    composite_cells = {
        cell["cell_id"] for cell in _composite_cells(read_p1(), read_dialect_regional_amendment()) if isinstance(cell, dict)
    }
    if metadata.get("coverage_stratum_id") not in composite_cells:
        return False
    if proposal["proposal_metadata_sha256"] != sha256_bytes(canonical_json(metadata)):
        return False
    provenance = proposal.get("producer_provenance")
    if not isinstance(provenance, dict) or set(provenance) != {"producer_kind", "run_identity_sha256", "input_identity_sha256", "proposal_process_version"}:
        return False
    if provenance.get("producer_kind") != proposal.get("producer_kind") or provenance.get("input_identity_sha256") != proposal.get("input_identity_sha256") or not _metadata_identifier(provenance.get("proposal_process_version")):
        return False
    if not _is_sha256(provenance.get("run_identity_sha256")):
        return False
    if set(promotion) != {"record_kind", "proposal_id", "proposal_sha256", "decision", "authority"}:
        return False
    if promotion.get("record_kind") != "promotion_decision" or promotion.get("decision") not in {"pending", "rejected"}:
        return False
    if promotion.get("proposal_id") != proposal.get("proposal_id") or promotion.get("proposal_sha256") != proposal.get("proposal_sha256"):
        return False
    if promotion.get("authority") != {"authority_kind": "source_qualified_human_adjudication", "actor_kind": "human"}:
        return False
    return value.get("proposal_contract", {}).get("current_rule_manifest_allows_promotion") is False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = canonical_json(build_contract())
    if args.check:
        if not args.output.is_file() or args.output.read_bytes() != expected:
            raise SystemExit("p2_contract_drift")
        print("p2_contract_verified")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(expected)
    print(f"wrote {relative(args.output) if args.output.is_relative_to(ROOT) else args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
