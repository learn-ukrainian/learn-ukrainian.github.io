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
from collections.abc import Iterable
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_cycle_void_receipt as cycle_void
from scripts.projects.open_model_data import phase3_functional_roles as functional_roles
from scripts.projects.open_model_data.paths import REGISTRY_OPEN_MODEL_DATA_DIR
from scripts.storage.paths import artifact_set

ROOT = Path(__file__).resolve().parents[3]

DATA = REGISTRY_OPEN_MODEL_DATA_DIR
DEFAULT_GIT_TIMEOUT_SECONDS: float = 30.0
SCHEMA_PATH = DATA / "contracts/phase3_v2_compatibility_matrix_v1.schema.json"
MATRIX_PATH = DATA / "evidence/phase3_v2_compatibility_matrix_v1.json"
SCRIPT_PATH = ROOT / "scripts/projects/open_model_data/phase3_v2_compatibility.py"
# Original reviewed source identities, independently matched to Git history.
FROZEN_VALIDATOR_SHA256 = "ae1e82ee32e1e1be1d358098abf0646ac74f2e318866c62e9c2635d48a1b09eb"
FROZEN_ROLE_VALIDATOR_SHA256 = "29a95031fc9af1feff3824d9f34120bd2a430af3a45ae3773b5aacbd5ad90840"
CURRENT_ROLE_VALIDATOR_SHA256 = "dea7e919b081903d6d95492f6438fd61f4132f1b411c9d9136320c443096a724"
FROZEN_VOID_PRODUCER_SHA256 = "1213a5b24bcfeb5ff7a6bf0348d608d3b8e3f1ad940fda3b0cad507b428ff02d"
CURRENT_VOID_PRODUCER_SHA256 = "e69c26c64fd70b843b6dd6136223f960a15a185fa48135a44c8f33b0ad61f1d9"
V2_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
V2_1_AMENDMENT_SHA256 = "ae36a961318b2a0a494837314929efd9849b4e6a6fa299b3d8dde17261777f5b"
V2_1_COMBINED_SHA256 = "2f3ef840325d917b9f2763188627ad69d1b4e45b804860499a134586b112a907"
MATRIX_LOGICAL_PATH = "data/projects/open_model_data/evidence/phase3_v2_compatibility_matrix_v1.json"
FUNCTIONAL_ROLE_LOGICAL_PATH = (
    "data/projects/open_model_data/evidence/correction_protection_functional_role_contract_v2_1.json"
)
CURRENT_EVALUATION_LOGICAL_PATH = (
    "data/projects/open_model_data/evidence/correction_protection_evaluation_contract_v1.json"
)
CURRENT_HELDOUT_LABEL_LOGICAL_PATH = (
    "data/projects/open_model_data/evidence/phase3_heldout_label_public_receipt_v1.json"
)
CYCLE002_ROLE_LOGICAL_PATH = (
    "data/projects/open_model_data/evidence/correction_protection_functional_role_contract_v2_2.json"
)
CYCLE002_EVALUATION_LOGICAL_PATH = (
    "data/projects/open_model_data/evidence/correction_protection_evaluation_contract_v2_2.json"
)
CYCLE001_VOID_LOGICAL_PATH = "data/projects/open_model_data/evidence/phase3_cycle001_void_receipt_v1.json"
UNIVERSITY_SOURCE_POLICY_LOGICAL_PATH = "data/projects/open_model_data/evidence/phase3_university_source_policy_v1.json"
# The compatibility matrix predates the current Phase 3 P1/V3 freezes.  Keep
# the post-v2 boundary explicit so a later metadata artifact cannot silently
# change the legacy/pre-v2 denominator or weaken its exact-coverage check.  A
# new post-v2 evidence artifact must be reviewed and added here deliberately.
CURRENT_PHASE_EVIDENCE_PATHS = frozenset(
    {
        "data/projects/open_model_data/evidence/phase3_p1_universe_freeze_v1.json",
        "data/projects/open_model_data/evidence/phase3_p1_dialect_regional_protection_amendment_v1.json",
        "data/projects/open_model_data/evidence/phase3_p2_canonical_contracts_v1.json",
        "data/projects/open_model_data/evidence/phase3_scope_circularity_firewall_v1.json",
        "data/projects/open_model_data/evidence/phase3_v3_cooperative_control_plane_v1.json",
    }
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
ENGINE_PATHS = frozenset(
    {
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
        "scripts/projects/open_model_data/phase3_fixed_release.py",
        # Direct, load-bearing deterministic validators imported by the live paths.
        "scripts/projects/open_model_data/phase3_near_duplicate.py",
        "scripts/projects/open_model_data/phase3_source_universe.py",
        "scripts/projects/open_model_data/verify_phase3_source_universe_freeze.py",
        "scripts/projects/open_model_data/phase3_recovery_contracts.py",
        "scripts/projects/open_model_data/phase3_source_unit_materialization.py",
        "scripts/projects/open_model_data/phase3_prior_exposure_manifest.py",
        "scripts/projects/open_model_data/phase3_evaluation_freeze.py",
        "scripts/projects/open_model_data/phase3_heldout_label_transport.py",
        "scripts/projects/open_model_data/phase3_source_production_transport.py",
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
        "data/projects/open_model_data/contracts/phase3_fixed_release_manifest_v1.schema.json",
        "data/projects/open_model_data/contracts/phase3_source_universe_freeze_v1.schema.json",
        "data/projects/open_model_data/contracts/correction_protection_evaluation_contract_v1.schema.json",
        "data/projects/open_model_data/contracts/phase3_source_unit_materialization_receipt_v1.schema.json",
        "data/projects/open_model_data/contracts/phase3_evaluation_freeze_bundle_v1.schema.json",
        "data/projects/open_model_data/contracts/phase3_heldout_label_transport_bundle_v1.schema.json",
        "data/projects/open_model_data/contracts/phase3_heldout_clean_modern_label_prompt_v1.md",
        "data/projects/open_model_data/contracts/phase3_heldout_semantic_gold_label_prompt_v1.md",
        "data/projects/open_model_data/contracts/phase3_source_production_transport_v1.schema.json",
        "data/projects/open_model_data/contracts/phase3_source_author_prompt_v1.md",
        "data/projects/open_model_data/contracts/phase3_source_review_prompt_v1.md",
    }
)


# Historical hashes below were matched to Git source blobs before migration.
# Current exact hashes retain a runtime integrity check without rewriting the frozen matrix.
MIGRATED_ENGINE_SOURCE_SHA256 = {
    "scripts/projects/open_model_data/phase3_heldout_partition.py": (
        "af0f544405a29055943d538b7e13f69983397ddac5562dea2ce156f06e924e77",
        "af99c2d154e48510dfbc0f80135acd6efcca754cce5147522e7d9988f5bb59e9",
    ),
    "scripts/projects/open_model_data/phase3_rule_author_packets.py": (
        "d07538485af2456a47177df164ca5d266ef52203849188e506595ecb17d8a9b3",
        "98d5898bad7b1564e2030fa7d3bdced3e90f2396fdc06835282a8110c0bf7dda",
    ),
    "scripts/projects/open_model_data/phase3_rule_author_runner.py": (
        "e25c6859176a185ad7fc6ec0b51033400eb25eae6440e526452d567da0404a34",
        "42a709997975d460ccc787a02e6463c00b7c8fff3b060ebe20b5a768409c48fd",
    ),
    "scripts/projects/open_model_data/phase3_rule_author_source_rows.py": (
        "0c01cf20cc39114b7394a6e02701ef35fc8c1d64412c35328e01059db8183d3c",
        "8cba9fd3dc05a8cf951c0d1662f5ddb5505bdfc6fe70ef0dea88fd139e0ddeb6",
    ),
    "scripts/projects/open_model_data/phase3_source_dispositions.py": (
        "f1fe490423bc49fcfbca9902f193be78510c3b2b4a5c7cc1aec04b5c877bf903",
        "56e0095fdb79c94c1a36e88eb16cb3634bcec382170e5f26636bdbc524695903",
    ),
    "scripts/projects/open_model_data/phase3_disposition_audit.py": (
        "5b40dc718387789a6d6a16aadcab5c900a6066aa96e6bae52d79b26a7c8b6177",
        "7d5da1395175e2e4f0b858e100f2fe7c41f060fc694023873e02b40281c30376",
    ),
    "scripts/projects/open_model_data/phase3_audit_entropy.py": (
        "0ae777894dd7b52eb6e91fd2f83eb079ecfd8a9aad9658571f8016ef6e8e7d86",
        "7fda57ffb5d614028d3a4afce505133dba42513edd8719e3509d6c8de63ba8e0",
    ),
    "scripts/projects/open_model_data/phase3_lexical_coverage.py": (
        "b921a82938cc28637168e3cacc1d502322334e0b27e57ef5a9f5a895ff8b67dc",
        "e5a12844941e62519e72f10185724ed72adb622857926376c9ba9f7f96e5d329",
    ),
    "scripts/projects/open_model_data/phase3_textbook_nonhit.py": (
        "2cfe4b75834f0974a61cf8de85e4d46676c2a221ad81928455560443f1c41b5f",
        "d8ac6428e42c55dd51fcab5040a01c7c64f938185a5772a60926e1270337d34b",
    ),
    "scripts/projects/open_model_data/phase3_pravopys_delta.py": (
        "4ffdf9114d8a62625d192dac905b007a4124b1fe4d5e8662c790339f436a177a",
        "afcb74a48896988d0d735a32c69d467aed8db031db2fce4b15205d2b60350318",
    ),
    "scripts/projects/open_model_data/phase3_evaluation_reproduction.py": (
        "bd743e6596448702f924b7c83bb3c95e61836780609d6f76ca9baa45feb42e5e",
        "194dd4b4446629a0403aea59e8f1fbbeb1e60df7dd136e4519e21a6c13f9cbbe",
    ),
    "scripts/projects/open_model_data/phase3_fixed_release.py": (
        "3f9148de609e91a4e37a8065e00d418a79555fc3d9eaeab09e2173005cd325a8",
        "baa5a5ea4b16df59f68baedef0c2a7f4bab4cc561543bfd8fbf31dbf7177ec51",
    ),
    "scripts/projects/open_model_data/phase3_near_duplicate.py": (
        "9b576cf313774e49fe81c9653c28310d0bc1ab25c628a94e1571aa0f41e72015",
        "80fa32a8ed3b5bf41f179a9a5fcb5a3aac12cb82c17fe1d5077f93bec6bfb799",
    ),
    "scripts/projects/open_model_data/phase3_recovery_contracts.py": (
        "ae63b4f5dd9b68ded453e30d91feaf5c35f364743602e8e71bebd845930bee44",
        "094177112a708d144e083d81a1faaa465b6cd7eabd012ed19d72ac3e43cfd9ce",
    ),
    "scripts/projects/open_model_data/phase3_evaluation_freeze.py": (
        "e8070f11384d7fd2362bbef34a084fa8b86e0fbefc7b6f42beac154a13054f2b",
        "7378d9daaa4a5c023db7d2c9c5d56ac43a534eb090222e60b99f264b0cb4c4f4",
    ),
    "scripts/projects/open_model_data/phase3_heldout_label_transport.py": (
        "a1c4fed207f4c79c682dd5ad0efed9e2d1e333f4f9650e48067ae29eaef46e8f",
        "5f8e6bf5a60217fff6dc73ab67ec2e7d7b98e6cbb7696e7421757c82d9c3dbde",
    ),
    "scripts/projects/open_model_data/phase3_source_production_transport.py": (
        "65bbd0ce715084c01a78df4ad047a90837e480928efeb0e0dd7fe9d8cd83debb",
        "b9ec762891d2d9ff3fea4cc16b20b1c88591bfae72f32fc7f0ec0007db97ef05",
    ),
    "scripts/projects/open_model_data/phase3_source_unit_materialization.py": (
        "5e1b9ee4cf86ff1f951270e069274e8664e73df44c8903e65f17ad5653319bbe",
        "998d8db85fa3f34ff0bb2b7be7509d3eed961a499cb6b1c65fa02272ead751ff",
    ),
    "scripts/projects/open_model_data/phase3_source_universe.py": (
        "032088c131f97b28ba0e300f884fc18964854c6e96046288fbda69a595fb969d",
        "f1f2730eeaa9a6f282a55200a3eed54d698e4f0358bd5a396805fc74ce407241",
    ),
    "scripts/projects/open_model_data/verify_phase3_source_universe_freeze.py": (
        "b45d83a24d71aedd36b9fc2cb11541dd5f97124046fa2b2d6ad5a920b62bc04d",
        "11a865bab60f9d49bedb3264cb0844f4f2c8aebe7d181124cedf327f93d8cb3c",
    ),
}


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


def _physical_k_path(logical_path: str) -> Path:
    """Resolve a frozen logical P3 K name to its checked-in registry bytes."""
    prefix = Path("data/projects/open_model_data")
    logical = Path(logical_path)
    if logical.is_relative_to(prefix):
        return REGISTRY_OPEN_MODEL_DATA_DIR / logical.relative_to(prefix)
    return ROOT / logical


def _input_bytes(logical_path: str, evidence_snapshot: Any) -> bytes:
    member = logical_path.removeprefix("data/")
    if member in evidence_snapshot.artifacts:
        return evidence_snapshot.artifacts[member]
    return _physical_k_path(logical_path).read_bytes()


def _input_sha256(logical_path: str, evidence_snapshot: Any) -> str:
    return hashlib.sha256(_input_bytes(logical_path, evidence_snapshot)).hexdigest()


def _pre_v2_evidence_paths(paths: Iterable[str]) -> set[str]:
    """Return the exact tracked evidence set covered by the v2 matrix."""
    excluded = {MATRIX_LOGICAL_PATH, *CURRENT_PHASE_EVIDENCE_PATHS}
    return {path for path in paths if path and path not in excluded}


def _tracked_evidence_paths(evidence_snapshot: Any) -> set[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "registry/projects/open_model_data/evidence/**"],
            check=False,
            capture_output=True,
            text=True,
            timeout=DEFAULT_GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CompatibilityError("cannot enumerate tracked evidence") from exc
    require(result.returncode == 0, "cannot enumerate tracked evidence")
    paths = _pre_v2_evidence_paths(
        [
            path.replace("registry/projects/open_model_data/", "data/projects/open_model_data/", 1)
            for path in result.stdout.splitlines()
        ]
        + [
            f"data/{path}"
            for path in evidence_snapshot.artifacts
            if path.startswith("projects/open_model_data/evidence/")
        ]
    )
    for logical_path in (
        FUNCTIONAL_ROLE_LOGICAL_PATH,
        CURRENT_HELDOUT_LABEL_LOGICAL_PATH,
        CYCLE002_ROLE_LOGICAL_PATH,
        CYCLE002_EVALUATION_LOGICAL_PATH,
        CYCLE001_VOID_LOGICAL_PATH,
    ):
        if _physical_k_path(logical_path).is_file():
            paths.add(logical_path)
    return paths


def _verify_heldout_label_receipt() -> dict[str, Any]:
    path = _physical_k_path(CURRENT_HELDOUT_LABEL_LOGICAL_PATH)
    receipt = read_json(path)
    require(
        receipt.get("schema_version") == "phase3_heldout_label_public_receipt_v1"
        and receipt.get("text_free") is True
        and receipt.get("complete") is True
        and receipt.get("row_count") == 2_000
        and receipt.get("packet_count") == 50,
        "heldout label freeze receipt is incomplete",
    )
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    require(
        receipt.get("receipt_sha256") == hashlib.sha256((canonical_json(body) + "\n").encode("utf-8")).hexdigest(),
        "heldout label freeze receipt body hash drift",
    )
    bindings = receipt.get("bindings", {})
    require(
        bindings.get("base_contract_sha256") == V2_SHA256
        and bindings.get("amendment_sha256") == V2_1_AMENDMENT_SHA256
        and bindings.get("combined_contract_sha256") == V2_1_COMBINED_SHA256
        and bindings.get("functional_role_contract_sha256")
        == sha256_file(_physical_k_path(FUNCTIONAL_ROLE_LOGICAL_PATH))
        and bindings.get("label_prompt_sha256")
        == sha256_file(
            ROOT / "registry/projects/open_model_data/contracts/phase3_heldout_clean_modern_label_prompt_v1.md"
        ),
        "heldout label freeze receipt contract binding drift",
    )
    return receipt


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
    require(matrix["bindings"]["validator_sha256"] == FROZEN_VALIDATOR_SHA256, "matrix validator binding drift")
    require(
        sha256_file(ROOT / "scripts/projects/open_model_data/phase3_functional_roles.py")
        == CURRENT_ROLE_VALIDATOR_SHA256,
        "current functional-role validator drift",
    )
    require(
        sha256_file(ROOT / "scripts/projects/open_model_data/phase3_cycle_void_receipt.py")
        == CURRENT_VOID_PRODUCER_SHA256,
        "current void-receipt producer drift",
    )
    evidence_snapshot = artifact_set("open_model_evidence_indexes", repo=ROOT)
    role_result = functional_roles.verify()
    cycle002_result = functional_roles.verify_cycle002_contracts()
    void_receipt = cycle_void.verify_receipt_value(read_json(_physical_k_path(CYCLE001_VOID_LOGICAL_PATH)))
    heldout_label_receipt = _verify_heldout_label_receipt()
    require(
        matrix["functional_role_binding"]
        == {
            "logical_path": FUNCTIONAL_ROLE_LOGICAL_PATH,
            "artifact_sha256": role_result["functional_role_contract_sha256"],
            "schema_sha256": sha256_file(functional_roles.SCHEMA_PATH),
            "validator_sha256": FROZEN_ROLE_VALIDATOR_SHA256,
            "conflict_graph_sha256": role_result["conflict_graph_sha256"],
            "role_graph_ready": True,
        },
        "functional-role validator binding drift",
    )
    require(
        matrix["cycle002_foundation_binding"]
        == {
            "role_contract_logical_path": CYCLE002_ROLE_LOGICAL_PATH,
            "role_contract_sha256": cycle002_result["role_contract_sha256"],
            "role_schema_sha256": sha256_file(functional_roles.CYCLE002_ROLE_SCHEMA_PATH),
            "evaluation_contract_logical_path": CYCLE002_EVALUATION_LOGICAL_PATH,
            "evaluation_contract_sha256": cycle002_result["evaluation_contract_sha256"],
            "evaluation_schema_sha256": sha256_file(functional_roles.CYCLE002_EVALUATION_SCHEMA_PATH),
            "void_receipt_logical_path": CYCLE001_VOID_LOGICAL_PATH,
            "void_receipt_schema_sha256": sha256_file(cycle_void.SCHEMA_PATH),
            "void_receipt_producer_sha256": FROZEN_VOID_PRODUCER_SHA256,
            "void_receipt_file_sha256": sha256_file(_physical_k_path(CYCLE001_VOID_LOGICAL_PATH)),
            "void_receipt_sha256": void_receipt["receipt_sha256"],
            "validator_sha256": FROZEN_ROLE_VALIDATOR_SHA256,
            "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-002",
            "required_frozen_labels_before_extraction": 9_392,
            "source_authoring_blocked": True,
            "verified": True,
        },
        "cycle002 foundation binding drift",
    )
    engine_entries = matrix["engine_bindings"]
    require({entry["logical_path"] for entry in engine_entries} == ENGINE_PATHS, "v2 engine binding set drift")
    for entry in engine_entries:
        logical_path = entry["logical_path"]
        migrated = MIGRATED_ENGINE_SOURCE_SHA256.get(logical_path)
        if migrated is not None:
            historical, current = migrated
            require(entry["artifact_sha256"] == historical, "v2 engine historical source identity drift")
            require(sha256_file(ROOT / logical_path) == current, "v2 engine current source byte drift")
        else:
            require(
                sha256_file(_physical_k_path(logical_path)) == entry["artifact_sha256"], "v2 engine artifact hash drift"
            )
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
    require(
        set(paths) == _tracked_evidence_paths(evidence_snapshot),
        "matrix does not exactly cover tracked pre-v2 evidence",
    )
    for entry in entries:
        logical_path = entry["logical_path"]
        path = _physical_k_path(logical_path)
        require(
            (
                logical_path.removeprefix("data/") in evidence_snapshot.artifacts
                or (path.is_file() and not path.is_symlink())
            ),
            f"matrix artifact missing or aliased: {logical_path}",
        )
        require(
            _input_sha256(logical_path, evidence_snapshot) == entry["artifact_sha256"],
            f"matrix artifact hash drift: {logical_path}",
        )
        require(entry["phase3_v2_contract_sha256"] == V2_SHA256, "entry v2 pin drift")
        if entry["logical_path"] == CURRENT_EVALUATION_LOGICAL_PATH:
            require(
                entry["artifact_class"] == "completion_status"
                and entry["disposition"] == "rebound"
                and entry["machine_reason"] == "evaluation_contract_rebound_to_v2_1",
                "current v2.1 evaluation contract is not rebound",
            )
        elif entry["logical_path"] == CURRENT_HELDOUT_LABEL_LOGICAL_PATH:
            require(
                entry["artifact_class"] == "source_status"
                and entry["disposition"] == "rebound"
                and entry["machine_reason"] == "heldout_labels_frozen_v2_1",
                "current heldout label freeze receipt is not rebound",
            )
            require(
                entry["artifact_sha256"] == sha256_file(_physical_k_path(CURRENT_HELDOUT_LABEL_LOGICAL_PATH))
                and heldout_label_receipt["receipt_sha256"]
                == "e2d3c170e94fa4762295805c522d1e52adaaaa867e60e8b02a06b19355a9694e",
                "heldout label freeze identity drift",
            )
        elif entry["logical_path"] == CYCLE002_ROLE_LOGICAL_PATH:
            require(
                entry["artifact_class"] == "functional_role_contract"
                and entry["disposition"] == "rebound"
                and entry["machine_reason"] == "cycle002_functional_role_contract_rebound",
                "cycle002 functional-role contract is not rebound",
            )
        elif entry["logical_path"] == CYCLE002_EVALUATION_LOGICAL_PATH:
            require(
                entry["artifact_class"] == "completion_status"
                and entry["disposition"] == "rebound"
                and entry["machine_reason"] == "cycle002_evaluation_contract_rebound",
                "cycle002 evaluation contract is not rebound",
            )
        elif entry["logical_path"] == CYCLE001_VOID_LOGICAL_PATH:
            require(
                entry["artifact_class"] == "source_status"
                and entry["disposition"] == "rebound"
                and entry["machine_reason"] == "cycle001_void_receipt_bound_for_cycle002",
                "cycle001 void receipt is not rebound",
            )
        elif entry["logical_path"] == UNIVERSITY_SOURCE_POLICY_LOGICAL_PATH:
            require(
                entry["artifact_class"] == "source_status"
                and entry["disposition"] == "rebound"
                and entry["machine_reason"] == "university_source_policy_rebound_to_v2_1",
                "current university source policy is not rebound",
            )
        elif entry["artifact_class"] == "functional_role_contract":
            require(
                entry["disposition"] == "rebound"
                and entry["machine_reason"] == "functional_role_contract_rebound_to_v2_1",
                "v2.1 functional-role ledger is not rebound",
            )
        elif entry["artifact_class"] in SEMANTIC_CLASSES:
            require(
                entry["disposition"] == "invalidated",
                "pre-v2 semantic/source/consumer/completion artifact not invalidated",
            )
            require(
                entry["machine_reason"] == INVALIDATION_REASONS[entry["artifact_class"]],
                "invalidated artifact machine reason drift",
            )
        else:
            require(
                entry["disposition"] in {"valid", "rebound"}, "deterministic engine lacks valid/rebound disposition"
            )
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
        matrix["source_authoring"] == {"blocked": True, "reason": "cycle002_closure_not_established"},
        "source-authoring block drift",
    )
    require(
        matrix["phase4"] == {"blocked": True, "reason": "phase3_v2_rebuild_review_and_completion_not_established"},
        "Phase 4 block drift",
    )
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
