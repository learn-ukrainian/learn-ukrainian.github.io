#!/usr/bin/env python3
"""Validate the public, text-free Phase 3 v2 compatibility matrix.

This module makes no linguistic decision.  It verifies exact tracked artifact
coverage, hashes, dispositions, and the operator-pinned v2 contract boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_functional_roles as functional_roles

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCHEMA_PATH = DATA / "contracts/phase3_v2_compatibility_matrix_v1.schema.json"
MATRIX_PATH = DATA / "evidence/phase3_v2_compatibility_matrix_v1.json"
SCRIPT_PATH = ROOT / "scripts/projects/open_model_data/phase3_v2_compatibility.py"
V2_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
V2_1_AMENDMENT_SHA256 = "ae36a961318b2a0a494837314929efd9849b4e6a6fa299b3d8dde17261777f5b"
V2_1_COMBINED_SHA256 = "2f3ef840325d917b9f2763188627ad69d1b4e45b804860499a134586b112a907"
MATRIX_LOGICAL_PATH = "data/projects/open_model_data/evidence/phase3_v2_compatibility_matrix_v1.json"
FUNCTIONAL_ROLE_LOGICAL_PATH = "data/projects/open_model_data/evidence/correction_protection_functional_role_contract_v2_1.json"
CURRENT_EVALUATION_LOGICAL_PATH = (
    "data/projects/open_model_data/evidence/correction_protection_evaluation_contract_v1.json"
)
REQUIRED_CLAIMS = {
    "public_canary_9_of_9": "public_canary_not_v2_evaluation",
    "nine_case_seed": "seed_not_v2_evaluation",
    "phase2_rows": "phase2_rows_not_phase3_evidence",
    "breadth_floor_100_total": "legacy_floor_not_v2_completion",
    "breadth_floor_25_automatic": "legacy_floor_not_v2_completion",
}
SEMANTIC_CLASSES = {
    "linguistic_status",
    "source_status",
    "consumer_status",
    "completion_status",
    "role_contract_status",
    "phase2_artifact",
}
LEGACY_PROVENANCE = {
    "authority": "legacy_provenance_only_not_current_authority",
    "original_prompt_v1_sha256": "6a563a7526c4ec7a89732f3de5651b0ab2e176ec089abf80f9eb733337db7662",
    "scope_amendment_v3_sha256": "da0f814f2f12e4974073de1a7b547fc3f27c07f6d903c95fde8f704d4e664132",
    "combined_v1_v3_sha256": "bf387adaeb180d11ade272819d77e1eb3d3fdecc43982fff9c775039c9e0bed7",
}
INVALIDATION_REASONS = {
    "linguistic_status": "pre_v2_linguistic_status_invalidated",
    "source_status": "pre_v2_source_status_invalidated",
    "consumer_status": "pre_v2_consumer_status_invalidated",
    "completion_status": "pre_v2_completion_status_invalidated",
    "role_contract_status": "pre_v2_role_contract_invalidated",
    "phase2_artifact": "phase2_rows_not_phase3_evidence",
}
ENGINE_PATHS = frozenset({
    # v2.1 packet compilation and execution.
    "scripts/projects/open_model_data/phase3_rule_author_packets.py",
    "scripts/projects/open_model_data/phase3_rule_author_runner.py",
    # v2.1 source population, release, and audit mechanics.
    "scripts/projects/open_model_data/phase3_heldout_partition.py",
    "scripts/projects/open_model_data/phase3_rule_author_source_rows.py",
    "scripts/projects/open_model_data/phase3_source_dispositions.py",
    "scripts/projects/open_model_data/phase3_disposition_audit.py",
    "scripts/projects/open_model_data/phase3_audit_entropy.py",
    "scripts/projects/open_model_data/phase3_lexical_coverage.py",
    "scripts/projects/open_model_data/phase3_textbook_nonhit.py",
    "scripts/projects/open_model_data/phase3_pravopys_delta.py",
    "scripts/projects/open_model_data/phase3_evaluation_reproduction.py",
    # Direct, load-bearing deterministic validators imported by the live paths.
    "scripts/projects/open_model_data/phase3_near_duplicate.py",
    "scripts/projects/open_model_data/phase3_source_universe.py",
    "scripts/projects/open_model_data/verify_phase3_source_universe_freeze.py",
    "scripts/projects/open_model_data/phase3_recovery_contracts.py",
    "scripts/projects/open_model_data/phase3_source_unit_materialization.py",
    "scripts/projects/open_model_data/phase3_prior_exposure_manifest.py",
    "scripts/projects/open_model_data/phase3_evaluation_freeze.py",
    "scripts/projects/open_model_data/phase3_heldout_label_transport.py",
    # Every closed Phase 3 schema consumed by the current runtime closure.
    "data/projects/open_model_data/contracts/phase3_rule_author_packet_bundle_v1.schema.json",
    "data/projects/open_model_data/contracts/phase3_rule_author_run_manifest_v1.schema.json",
    "data/projects/open_model_data/contracts/phase3_heldout_partition_bundle_v1.schema.json",
    "data/projects/open_model_data/contracts/phase3_rule_author_source_rows_v1.schema.json",
    "data/projects/open_model_data/contracts/phase3_source_disposition_input_v1.schema.json",
    "data/projects/open_model_data/contracts/phase3_disposition_audit_bundle_v1.schema.json",
    "data/projects/open_model_data/contracts/phase3_audit_entropy_receipt_v1.schema.json",
    "data/projects/open_model_data/contracts/phase3_textbook_nonhit_bundle_v1.schema.json",
    "data/projects/open_model_data/contracts/correction_protection_coverage_contract_v1.schema.json",
    "data/projects/open_model_data/contracts/phase3_pravopys_delta_bundle_v1.schema.json",
    "data/projects/open_model_data/contracts/phase3_evaluation_reproduction_bundle_v1.schema.json",
    "data/projects/open_model_data/contracts/phase3_source_universe_freeze_v1.schema.json",
    "data/projects/open_model_data/contracts/correction_protection_evaluation_contract_v1.schema.json",
    "data/projects/open_model_data/contracts/phase3_source_unit_materialization_receipt_v1.schema.json",
    "data/projects/open_model_data/contracts/phase3_evaluation_freeze_bundle_v1.schema.json",
    "data/projects/open_model_data/contracts/phase3_heldout_label_transport_bundle_v1.schema.json",
    "data/projects/open_model_data/contracts/phase3_heldout_clean_modern_label_prompt_v1.md",
})


class CompatibilityError(ValueError):
    """The compatibility matrix is incomplete, stale, or unsafe."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CompatibilityError(message)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompatibilityError(f"cannot read JSON artifact: {path}") from exc
    require(isinstance(value, dict), "JSON artifact must be an object")
    return value


def _tracked_evidence_paths() -> set[str]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "data/projects/open_model_data/evidence/**"],
        check=False,
        capture_output=True,
        text=True,
    )
    require(result.returncode == 0, "cannot enumerate tracked evidence")
    paths = {line for line in result.stdout.splitlines() if line and line != MATRIX_LOGICAL_PATH}
    if (ROOT / FUNCTIONAL_ROLE_LOGICAL_PATH).is_file():
        paths.add(FUNCTIONAL_ROLE_LOGICAL_PATH)
    return paths


def verify(matrix_path: Path = MATRIX_PATH) -> dict[str, Any]:
    matrix = read_json(matrix_path)
    schema = read_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(matrix), key=lambda error: list(error.path))
    require(not errors, f"matrix schema violation: {errors[0].message if errors else ''}")
    require(matrix["phase3_v2_contract_sha256"] == V2_SHA256, "Phase 3 v2 pin drift")
    require(matrix["phase3_v2_1_amendment_sha256"] == V2_1_AMENDMENT_SHA256, "Phase 3 v2.1 amendment pin drift")
    require(matrix["phase3_v2_1_combined_contract_sha256"] == V2_1_COMBINED_SHA256, "Phase 3 v2.1 combined pin drift")
    require(matrix["legacy_provenance"] == LEGACY_PROVENANCE, "legacy v1/v3 provenance binding drift")
    require(matrix["bindings"]["schema_sha256"] == sha256_file(SCHEMA_PATH), "matrix schema binding drift")
    require(matrix["bindings"]["validator_sha256"] == sha256_file(SCRIPT_PATH), "matrix validator binding drift")
    role_result = functional_roles.verify()
    require(
        matrix["functional_role_binding"]
        == {
            "logical_path": FUNCTIONAL_ROLE_LOGICAL_PATH,
            "artifact_sha256": role_result["functional_role_contract_sha256"],
            "schema_sha256": sha256_file(functional_roles.SCHEMA_PATH),
            "validator_sha256": sha256_file(ROOT / "scripts/projects/open_model_data/phase3_functional_roles.py"),
            "conflict_graph_sha256": role_result["conflict_graph_sha256"],
            "role_graph_ready": True,
        },
        "functional-role validator binding drift",
    )
    engine_entries = matrix["engine_bindings"]
    require({entry["logical_path"] for entry in engine_entries} == ENGINE_PATHS, "v2 engine binding set drift")
    for entry in engine_entries:
        require(sha256_file(ROOT / entry["logical_path"]) == entry["artifact_sha256"], "v2 engine artifact hash drift")
        require(
            entry["disposition"] == "rebound"
            and entry["machine_reason"] == "deterministic_engine_rebound_to_v2"
            and entry["phase3_v2_contract_sha256"] == V2_SHA256,
            "v2 engine rebound binding drift",
        )

    entries = matrix["inventory"]
    paths = [entry["logical_path"] for entry in entries]
    ids = [entry["artifact_id"] for entry in entries]
    require(len(paths) == len(set(paths)) and len(ids) == len(set(ids)), "duplicate matrix path or artifact ID")
    require(set(paths) == _tracked_evidence_paths(), "matrix does not exactly cover tracked pre-v2 evidence")
    for entry in entries:
        path = ROOT / entry["logical_path"]
        require(path.is_file() and not path.is_symlink(), f"matrix artifact missing or aliased: {entry['logical_path']}")
        require(sha256_file(path) == entry["artifact_sha256"], f"matrix artifact hash drift: {entry['logical_path']}")
        require(entry["phase3_v2_contract_sha256"] == V2_SHA256, "entry v2 pin drift")
        if entry["logical_path"] == CURRENT_EVALUATION_LOGICAL_PATH:
            require(
                entry["artifact_class"] == "completion_status"
                and entry["disposition"] == "rebound"
                and entry["machine_reason"] == "evaluation_contract_rebound_to_v2_1",
                "current v2.1 evaluation contract is not rebound",
            )
        elif entry["artifact_class"] == "functional_role_contract":
            require(
                entry["disposition"] == "rebound"
                and entry["machine_reason"] == "functional_role_contract_rebound_to_v2_1",
                "v2.1 functional-role ledger is not rebound",
            )
        elif entry["artifact_class"] in SEMANTIC_CLASSES:
            require(entry["disposition"] == "invalidated", "pre-v2 semantic/source/consumer/completion artifact not invalidated")
            require(
                entry["machine_reason"] == INVALIDATION_REASONS[entry["artifact_class"]],
                "invalidated artifact machine reason drift",
            )
        else:
            require(entry["disposition"] in {"valid", "rebound"}, "deterministic engine lacks valid/rebound disposition")
            expected_reason = (
                "deterministic_nonsemantic_engine_valid_under_v2"
                if entry["disposition"] == "valid"
                else "deterministic_engine_rebound_to_v2"
            )
            require(entry["machine_reason"] == expected_reason, "deterministic engine machine reason drift")

    claims = {item["claim_id"]: item for item in matrix["legacy_claims"]}
    require(set(claims) == set(REQUIRED_CLAIMS), "legacy claim invalidation set drift")
    for claim_id, reason in REQUIRED_CLAIMS.items():
        require(
            claims[claim_id]["disposition"] == "invalidated" and claims[claim_id]["machine_reason"] == reason,
            f"legacy claim is not correctly invalidated: {claim_id}",
        )
    require(
        matrix["source_authoring"]
        == {"blocked": True, "reason": "heldout_labels_not_frozen"},
        "source-authoring block drift",
    )
    require(matrix["phase4"] == {"blocked": True, "reason": "phase3_v2_rebuild_review_and_completion_not_established"}, "Phase 4 block drift")
    return {
        "ok": True,
        "schema_version": matrix["schema_version"],
        "phase3_v2_contract_sha256": V2_SHA256,
        "phase3_v2_1_amendment_sha256": V2_1_AMENDMENT_SHA256,
        "phase3_v2_1_combined_contract_sha256": V2_1_COMBINED_SHA256,
        "matrix_sha256": sha256_file(matrix_path),
        "inventory_count": len(entries),
        "invalidated_count": sum(entry["disposition"] == "invalidated" for entry in entries),
        "rebound_count": sum(entry["disposition"] == "rebound" for entry in entries),
        "valid_count": sum(entry["disposition"] == "valid" for entry in entries),
        "role_graph_ready": True,
        "source_authoring_blocked": True,
        "phase4_blocked": True,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the deterministic Phase 3 v2 compatibility matrix.")
    parser.add_argument("--matrix", type=Path, default=MATRIX_PATH)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        print(canonical_json(verify(args.matrix)))
    except CompatibilityError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
