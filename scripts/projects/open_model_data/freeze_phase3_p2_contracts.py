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
RULE_SLOT_ALGORITHM_VERSION = "phase3_p2_atomic_rule_slot_derivation_v1"


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


def rule_slot(cell: dict[str, Any]) -> dict[str, Any]:
    identity = {
        "algorithm_version": RULE_SLOT_ALGORITHM_VERSION,
        "cell_id": cell["cell_id"],
        "context_role": cell["context_role"],
        "language_identity": cell["language_identity"],
        "phenomenon": cell["phenomenon"],
        "role": cell["role"],
    }
    return {
        "rule_slot_id": "p2_rule_slot:" + sha256_bytes(canonical_json(identity)),
        "p1_cell_id": cell["cell_id"],
        "p1_cell_identity_sha256": sha256_bytes(canonical_json(cell)),
        "required_case_state": {
            "source_backed_correction": "correction",
            "protected_historical": "protected_historical_context",
            "abstention": "abstention",
            "not_applicable_with_evidence": "not_applicable_with_evidence",
        }.get(cell["role"], "coverage_blocked"),
        "p1_status": cell["status"],
        "protection_required": cell["protection_required"],
        "substantive_rule_claim_frozen": False,
        "metadata_only": True,
    }


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
    slots = sorted((rule_slot(cell) for cell in cells), key=lambda item: item["p1_cell_id"])
    algorithm = {
        "algorithm_version": RULE_SLOT_ALGORITHM_VERSION,
        "derivation": "one_atomic_slot_per_p1_required_cell; canonical_cell_metadata_sha256; lexicographic_p1_cell_id_order",
        "input_p1_manifest_sha256": sha256_file(P1),
    }
    algorithm["algorithm_sha256"] = sha256_bytes(canonical_json(algorithm))
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
            "merge_criteria": "forbidden; one_p1_required_cell_maps_to_exactly_one_atomic_slot",
            "split_criteria": "forbidden_without_new_versioned_p1_cell_and_new_dataset_version",
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
            "protected_historical_is_not_modern_correction": True,
        },
        "proposal_contract": {
            "model_or_tool_proposals_permitted": True,
            "proposal_provenance_required": True,
            "proposal_may_promote_to_gold": False,
            "proposal_may_replace_human_adjudication": False,
            "gold_authorship_by_models": False,
        },
        "fail_closed_invariants": {
            "rights_or_provenance_unknown_blocks_admission": True,
            "historical_non_erasure": True,
            "historical_auto_normalization_forbidden": True,
            "unresolved_identity_routes_to_abstention_or_protection": True,
            "missing_claim_typed_evidence_blocks_promotion": True,
            "provider_calls": False,
            "labels_created": False,
            "gold_created": False,
            "training_performed": False,
        },
        "generator": artifact(Path(__file__)),
    }


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
