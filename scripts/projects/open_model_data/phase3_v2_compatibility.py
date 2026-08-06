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
from collections.abc import Mapping
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCHEMA_PATH = DATA / "contracts/phase3_v2_compatibility_matrix_v1.schema.json"
MATRIX_PATH = DATA / "evidence/phase3_v2_compatibility_matrix_v1.json"
SCRIPT_PATH = ROOT / "scripts/projects/open_model_data/phase3_v2_compatibility.py"
V2_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
MATRIX_LOGICAL_PATH = "data/projects/open_model_data/evidence/phase3_v2_compatibility_matrix_v1.json"
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
ENGINE_PATHS = {
    "scripts/projects/open_model_data/phase3_rule_author_packets.py",
    "scripts/projects/open_model_data/phase3_rule_author_runner.py",
    "data/projects/open_model_data/contracts/phase3_rule_author_packet_bundle_v1.schema.json",
    "data/projects/open_model_data/contracts/phase3_rule_author_run_manifest_v1.schema.json",
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


def _tracked_evidence_paths() -> set[str]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "data/projects/open_model_data/evidence/**"],
        check=False,
        capture_output=True,
        text=True,
    )
    require(result.returncode == 0, "cannot enumerate tracked evidence")
    return {line for line in result.stdout.splitlines() if line and line != MATRIX_LOGICAL_PATH}


def verify(matrix_path: Path = MATRIX_PATH) -> dict[str, Any]:
    matrix = read_json(matrix_path)
    schema = read_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(matrix), key=lambda error: list(error.path))
    require(not errors, f"matrix schema violation: {errors[0].message if errors else ''}")
    require(matrix["phase3_v2_contract_sha256"] == V2_SHA256, "Phase 3 v2 pin drift")
    require(matrix["legacy_provenance"] == LEGACY_PROVENANCE, "legacy v1/v3 provenance binding drift")
    require(matrix["bindings"]["schema_sha256"] == sha256_file(SCHEMA_PATH), "matrix schema binding drift")
    require(matrix["bindings"]["validator_sha256"] == sha256_file(SCRIPT_PATH), "matrix validator binding drift")
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
        if entry["artifact_class"] in SEMANTIC_CLASSES:
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
        == {"blocked": True, "reason": "v2_exclusive_role_independence_not_established"},
        "source-authoring block drift",
    )
    require(matrix["phase4"] == {"blocked": True, "reason": "phase3_v2_rebuild_review_and_completion_not_established"}, "Phase 4 block drift")
    return {
        "ok": True,
        "schema_version": matrix["schema_version"],
        "phase3_v2_contract_sha256": V2_SHA256,
        "matrix_sha256": sha256_file(matrix_path),
        "inventory_count": len(entries),
        "invalidated_count": sum(entry["disposition"] == "invalidated" for entry in entries),
        "rebound_count": sum(entry["disposition"] == "rebound" for entry in entries),
        "valid_count": sum(entry["disposition"] == "valid" for entry in entries),
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
