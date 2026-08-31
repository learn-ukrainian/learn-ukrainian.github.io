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
OUTPUT = DATA / "evidence/phase3_p2_canonical_contracts_v1.json"

OUTCOME_SHA256 = "890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47"
SCHEMA_VERSION = "phase3_p2_canonical_contracts_v1"
PINNED_P1_MANIFEST_SHA256 = "0b1cd81448b96b4e818aa1dedd7df7633ff88eb500bb4d6ac3668be02962a35b"
RULE_SLOT_ALGORITHM_VERSION = "phase3_p2_rule_admission_and_identity_v1"
CASE_RECORD_KINDS = frozenset(
    {
        "correct_modern_production",
        "source_backed_correction",
        "minimal_contrast",
        "protected_historical_context",
        "abstention",
        "not_applicable_with_evidence",
        "coverage_blocked",
    }
)


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


def build_contract() -> dict[str, Any]:
    p1 = read_p1()
    source_units = p1.get("source_manifest", {}).get("source_units")
    cells = p1.get("required_cell_manifest", {}).get("cells")
    if not isinstance(source_units, list) or not isinstance(cells, list):
        raise ValueError("p1_shape_drift")
    unknown_rights = sum(
        1
        for unit in source_units
        if isinstance(unit, dict)
        and isinstance(unit.get("rights"), dict)
        and unit["rights"].get("required_state") == "unknown"
    )
    if len(source_units) != 57 or unknown_rights != 39 or len(cells) != 15:
        raise ValueError("p1_denominator_drift")
    algorithm = {
        "algorithm_version": RULE_SLOT_ALGORITHM_VERSION,
        "derivation": "future_rule_slots_require_source_qualified_claim_typed_evidence_and_human_adjudication; p1_cells_are_coverage_strata_not_rules",
        "input_p1_manifest_sha256": PINNED_P1_MANIFEST_SHA256,
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
            "source_unit_count": len(source_units),
            "unknown_rights_blocker_count": unknown_rights,
            "required_cell_count": len(cells),
            "required_cell_statuses": [
                {"cell_id": cell["cell_id"], "status": cell["status"]}
                for cell in sorted(cells, key=lambda item: item["cell_id"])
            ],
        },
        "rule_slot_universe": {
            "symbol": "R",
            "algorithm": algorithm,
            "slot_count": len(slots),
            "slots": slots,
            "rule_manifest_sha256": sha256_bytes(canonical_json(slots)),
            "coverage_strata_are_rules": False,
            "merge_criteria": {"permitted": True, "requires": ["source_qualified_claim_typed_evidence", "human_adjudication", "all_parent_slot_ids"], "preserves": ["p1_cell_id", "case_denominator"], "version_effect": "new_rule_manifest_version"},
            "split_criteria": {"permitted": True, "requires": ["source_qualified_claim_typed_evidence", "human_adjudication", "parent_slot_id"], "preserves": ["p1_cell_id", "case_denominator"], "version_effect": "new_rule_manifest_version_with_parent_child_lineage"},
            "denominator_change_policy": "new_p1_manifest_sha256_and_new_dataset_version_required",
            "substantive_rule_claims": "not_frozen",
        },
        "evidence_contract": {
            "claim_typed_roles": [
                "applicability_scope",
                "correction_authority",
                "minimal_contrast_authority",
                "protected_historical_identity",
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
            "validator_functions": ["validate_contract_integrity", "validate_case_record", "validate_promotion"],
        },
        "case_state_contract": {
            "structurally_distinct_states": [
                "correct_modern_production",
                "source_backed_correction",
                "minimal_contrast",
                "protected_historical_context",
                "abstention",
                "not_applicable_with_evidence",
                "coverage_blocked",
            ],
            "exactly_one_primary_state_per_case": True,
            "coverage_blocked_emits_case": False,
            "coverage_blocked_record_kind": "coverage_blocked",
            "protected_historical_is_not_modern_correction": True,
        },
        "proposal_contract": {
            "model_or_tool_proposals_permitted": True,
            "proposal_provenance_required": True,
            "proposal_may_promote_to_gold": False,
            "proposal_may_replace_human_adjudication": False,
            "gold_authorship_by_models": False,
            "proposal_fingerprint": "sha256_canonical_metadata_without_proposal_sha256",
            "current_rule_manifest_allows_promotion": False,
        },
        "fail_closed_invariants": {
            "rights_or_provenance_unknown_blocks_admission": True,
            "historical_non_erasure": "protected_historical_context_requires_source_period_region_recension_and_no_modern_normalization",
            "historical_auto_normalization_forbidden": "historical_or_rusyn_identity_may_not_be_mapped_to_modern_national_successor",
            "historical_protection_invariants": p1["historical_protection"],
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


def _proposal_sha256(proposal: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json({key: value for key, value in proposal.items() if key != "proposal_sha256"}))


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
    cells = {
        cell["cell_id"]: cell
        for cell in p1["required_cell_manifest"]["cells"]
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
    if kind == "protected_historical_context" and cell["protection_required"] is not True:
        return False
    allowed_roles = set(contract_value["evidence_contract"]["claim_typed_roles"])
    seen_ids: set[str] = set()
    roles: set[str] = set()
    for ref in refs:
        if not isinstance(ref, dict) or set(ref) != {"evidence_ref_id", "claim_role", "source_unit_id", "source_unit_identity_sha256", "source_artifact_sha256", "provenance_sha256"}:
            return False
        identifier = ref["evidence_ref_id"]
        if not _metadata_identifier(identifier) or identifier in seen_ids or not _metadata_identifier(ref["source_unit_id"]):
            return False
        unit = units.get(ref["source_unit_id"])
        if unit is None or ref["claim_role"] not in allowed_roles:
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
        "abstention": {"abstention_or_not_applicable_authority", "rights_provenance"},
        "not_applicable_with_evidence": {"abstention_or_not_applicable_authority", "rights_provenance"},
    }
    if not required_roles[kind] <= roles:
        return False
    if kind == "protected_historical_context":
        return set(record) == base | {"historical_identity", "period_id", "region_id", "recension_editorial_layer", "modern_normalization"} and all(
            _metadata_identifier(record[key])
            for key in ("historical_identity", "period_id", "region_id", "recension_editorial_layer")
        ) and record["modern_normalization"] is False
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
    if set(proposal) != {"record_kind", "proposal_id", "producer_kind", "producer_provenance", "input_identity_sha256", "proposal_metadata_sha256", "proposal_sha256"}:
        return False
    if proposal.get("record_kind") != "proposal" or proposal.get("producer_kind") not in {"model", "tool"}:
        return False
    if not _metadata_identifier(proposal.get("proposal_id")) or not all(
        isinstance(proposal.get(key), str) and len(proposal[key]) == 64
        for key in ("input_identity_sha256", "proposal_metadata_sha256", "proposal_sha256")
    ) or proposal.get("proposal_sha256") != _proposal_sha256(proposal):
        return False
    provenance = proposal.get("producer_provenance")
    if not isinstance(provenance, dict) or set(provenance) != {"producer_kind", "run_identity_sha256", "input_identity_sha256", "proposal_process_version"}:
        return False
    if provenance.get("producer_kind") != proposal.get("producer_kind") or provenance.get("input_identity_sha256") != proposal.get("input_identity_sha256") or not _metadata_identifier(provenance.get("proposal_process_version")):
        return False
    if not isinstance(provenance.get("run_identity_sha256"), str) or len(provenance["run_identity_sha256"]) != 64:
        return False
    if set(promotion) != {"record_kind", "proposal_id", "proposal_sha256", "decision", "authority"}:
        return False
    if promotion.get("record_kind") != "promotion_decision" or promotion.get("decision") not in {"pending", "rejected"}:
        return False
    if promotion.get("proposal_id") != proposal.get("proposal_id") or promotion.get("proposal_sha256") != proposal.get("proposal_sha256"):
        return False
    if promotion.get("authority") != {"authority_kind": "source_qualified_human_adjudication", "actor_kind": "human"}:
        return False
    value = build_contract()
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
