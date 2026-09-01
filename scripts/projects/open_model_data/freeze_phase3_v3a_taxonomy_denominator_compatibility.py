#!/usr/bin/env python3
"""Freeze and verify the metadata-only Phase 3 V3-A taxonomy denominator.

The generator reads committed predecessor metadata and, when explicitly asked,
verifies the locally retained dialectology source without emitting source text.
It cannot create examples, labels, gold, split membership, or training rows.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sqlite3
import stat
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCHEMA_PATH = DATA / "contracts/phase3_v3a_taxonomy_denominator_compatibility_v1.schema.json"
ARTIFACT_PATH = DATA / "contracts/phase3_v3a_taxonomy_denominator_compatibility_v1.json"
MATRIX_PATH = DATA / "contracts/phase3_v3a_compatibility_matrix_v1.json"
SCRIPT_PATH = Path(__file__).resolve()

P1_PATH = DATA / "evidence/phase3_p1_universe_freeze_v1.json"
P1_DIALECT_PATH = DATA / "evidence/phase3_p1_dialect_regional_protection_amendment_v1.json"
P2_PATH = DATA / "evidence/phase3_p2_canonical_contracts_v1.json"
V3_SCHEMA_PATH = DATA / "contracts/phase3_v3_cooperative_control_plane_v1.schema.json"
V3_ARTIFACT_PATH = DATA / "evidence/phase3_v3_cooperative_control_plane_v1.json"
V2_MATRIX_PATH = DATA / "evidence/phase3_v2_compatibility_matrix_v1.json"
SOURCE_POLICY_PATH = DATA / "admission/phase3_complete_source_policy_v4.json"

V2_OUTCOME_SHA256 = "890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47"
V3_CONSENSUS_SHA256 = "d3444c126deb91d05129d51c5344aa204b1db9ca0927c246698e0389466d0b1a"
EXPECTED_HASHES = {
    P1_PATH: "0b1cd81448b96b4e818aa1dedd7df7633ff88eb500bb4d6ac3668be02962a35b",
    P1_DIALECT_PATH: "5a4b259f764a3d41499f0a989c02fed921c18b62c9831d361d18d19dcc948afa",
    P2_PATH: "dc8dfdf207728ef386cea14ddb328289b2beee5159afb98bf076e5f117602ea3",
    V3_SCHEMA_PATH: "d7897f3f4a5899e24f504916d9a63bcb82d3e20968d0be26ba8166f27ba5a852",
    V3_ARTIFACT_PATH: "f7d5da9ede20967f05c4eee22b3bda14ca3b6bc30cd0e4b32f659bd572a7078d",
    V2_MATRIX_PATH: "9f3113776f899759dc9d4bdde9cde8e3fd5c85f5b3e6e748bf0ac79fac28a29c",
    SOURCE_POLICY_PATH: "98e7a80f8fdc1274a190cda793699aceaa79741ebf2145669d73e4c8a2236559",
}

PARENT_CELL_ID = (
    "protection.source_attested_ukrainian_dialect_or_regional_form."
    "dialect_or_regional_form.protected_dialect_or_regional"
)
SOURCE_ID = "uni-ukrmova-dialectology-torchynska-2017"
JSONL_SHA256 = "b8d349c725f0964817111c05bdb6c8dcdba6ac35139b91ea65ccdafe042fc89c"
FRONT_MATTER_ROWS_SHA256 = "2f24ce001b5ecb222bfa84e5065607403de26edcc3c9b5ec87b4a368329ed7fa"
LOCAL_SOURCE_ROW_COUNT = 281
LOCAL_SOURCE_ROWS_SHA256 = "29938730938d3a5c17a4dc320bf5dfbad6f4a8b96f0b0aad1e658f186d8f83dd"

OPERATIONS = (
    "retain",
    "deterministic_local_analysis",
    "external_provider_transmission",
    "derive",
    "model_training",
    "publish_text_or_metadata",
    "redistribute",
)
FORBIDDEN_FIELDS = frozenset(
    {
        "content",
        "gold",
        "heldout_content",
        "heldout_derivatives",
        "heldout_fingerprints",
        "heldout_labels",
        "heldout_locators",
        "heldout_membership",
        "label",
        "prompt",
        "provider_output",
        "source_body",
        "source_content",
        "source_text",
        "text",
    }
)

CHILDREN = (
    {
        "region_id": "northern_polissian",
        "chunk_evidence": (
            (
                "uni-ukrmova-dialectology-torchynska-2017_s0019",
                12,
                "f7e068c2a28a4feb9bbf2013d3fd482e56b184817428d902f4ba09b1e61021e8",
            ),
            (
                "uni-ukrmova-dialectology-torchynska-2017_s0020",
                13,
                "956423d25eb12a89a01d11f94bf6529533f583b825c0b286c747564c39040844",
            ),
        ),
    },
    {
        "region_id": "southeastern",
        "chunk_evidence": (
            (
                "uni-ukrmova-dialectology-torchynska-2017_s0020",
                13,
                "956423d25eb12a89a01d11f94bf6529533f583b825c0b286c747564c39040844",
            ),
        ),
    },
    {
        "region_id": "southwestern",
        "chunk_evidence": (
            (
                "uni-ukrmova-dialectology-torchynska-2017_s0020",
                13,
                "956423d25eb12a89a01d11f94bf6529533f583b825c0b286c747564c39040844",
            ),
        ),
    },
)


class V3AError(ValueError):
    """The V3-A contract is stale, incomplete, or unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise V3AError(message)


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise V3AError(f"cannot hash artifact: {path}") from exc


def logical(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def binding(path: Path) -> dict[str, str]:
    return {"path": logical(path), "sha256": sha256_file(path)}


def read_json(path: Path) -> dict[str, Any]:
    try:
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode) and not path.is_symlink(), f"artifact must be a regular file: {path}")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise V3AError(f"cannot read JSON artifact: {path}") from exc
    require(isinstance(value, dict), f"JSON artifact must be an object: {path}")
    return value


def receipt_sha(value: Mapping[str, Any]) -> str:
    body = dict(value)
    body.pop("receipt_sha256", None)
    return sha256_bytes(canonical_bytes(body))


def with_receipt(value: dict[str, Any]) -> dict[str, Any]:
    value["receipt_sha256"] = receipt_sha(value)
    return value


def verify_predecessors() -> None:
    for path, expected in EXPECTED_HASHES.items():
        require(sha256_file(path) == expected, f"predecessor byte drift: {logical(path)}")


def _walk_forbidden(value: Any, path: str = "artifact") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            require(key not in FORBIDDEN_FIELDS, f"forbidden field at {path}/{key}")
            _walk_forbidden(child, f"{path}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden(child, f"{path}/{index}")


def verify_source_db(path: Path) -> None:
    require(path.is_file(), f"source DB missing: {path}")
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT chunk_id,title,text,parent_section_id FROM textbooks WHERE source_file=? ORDER BY chunk_id",
            (SOURCE_ID,),
        ).fetchall()
    finally:
        connection.close()
    digest = hashlib.sha256()
    chunk_hashes: dict[str, str] = {}
    for chunk_id, title, body, parent_section_id in rows:
        record = {
            "chunk_id": chunk_id,
            "parent_section_id": parent_section_id,
            "text": body,
            "title": title,
        }
        digest.update(canonical_bytes(record))
        chunk_hashes[str(chunk_id)] = sha256_bytes(str(body).encode())
    require(len(rows) == LOCAL_SOURCE_ROW_COUNT, "dialectology source row count drift")
    require(digest.hexdigest() == LOCAL_SOURCE_ROWS_SHA256, "dialectology source row digest drift")
    for child in CHILDREN:
        for chunk_id, _page, expected_sha in child["chunk_evidence"]:
            require(chunk_hashes.get(chunk_id) == expected_sha, f"dialect evidence chunk drift: {chunk_id}")


def _children() -> list[dict[str, Any]]:
    result = []
    for spec in CHILDREN:
        region = spec["region_id"]
        result.append(
            {
                "stratum_id": f"{PARENT_CELL_ID}.{region}.contemporary_ukrainian.territorial_spoken_dialect",
                "parent_cell_id": PARENT_CELL_ID,
                "source_id": SOURCE_ID,
                "region_id": region,
                "period_id": "contemporary_ukrainian",
                "register_id": "territorial_spoken_dialect",
                "lineage_status": "child_of_parent",
                "coverage_status": "coverage_blocked",
                "coverage_target": True,
                "coverage_credit": False,
                "source_membership_frozen": True,
                "evidence_role": "taxonomy_partition_only_not_example_coverage",
                "evidence_locators": [
                    {"chunk_id": chunk, "source_page": page, "chunk_text_sha256": digest}
                    for chunk, page, digest in spec["chunk_evidence"]
                ],
            }
        )
    return result


def _rights_rows(p1: Mapping[str, Any]) -> list[dict[str, Any]]:
    units = sorted(p1["source_manifest"]["source_units"], key=lambda row: row["source_unit_id"])
    rows = []
    for unit in units:
        rights = unit["rights"]
        operations = []
        for operation in OPERATIONS:
            item: dict[str, Any] = {
                "operation": operation,
                "state": "unknown",
                "reason_code": "no_operation_specific_rights_evidence",
                "evidence_binding": binding(P1_PATH),
            }
            if operation == "publish_text_or_metadata":
                item["scope_qualifier"] = {
                    "body_scope": "unknown",
                    "metadata_scope": "unknown",
                    "combined_grant_forbidden": True,
                }
            operations.append(item)
        rows.append(
            {
                "source_unit_id": unit["source_unit_id"],
                "legacy_capability_state": rights["capability_state"],
                "legacy_required_state": rights["required_state"],
                "legacy_blocked_lanes": rights.get("blocked_lanes", []),
                "operations": operations,
            }
        )
    return rows


def _derive_denominator(
    p1: Mapping[str, Any],
    v3: Mapping[str, Any],
    children: list[dict[str, Any]],
) -> dict[str, Any]:
    """Reconcile the V3-A denominator from hash-bound predecessor metadata."""
    source_units = p1["source_manifest"]["source_units"]
    v2_cells = v3["compatibility"]["cells"]
    predecessor_denominator = v3["compatibility"]["v2_composite_denominator"]

    source_unit_count = len(source_units)
    unknown_rights_count = sum(unit["rights"]["required_state"] == "unknown" for unit in source_units)
    not_applicable_count = sum(cell["v2_status"] == "not_applicable_with_evidence" for cell in v2_cells)
    lineage_parent_count = sum(cell["v2_cell_id"] == PARENT_CELL_ID for cell in v2_cells)
    legacy_active_targets = len(v2_cells) - not_applicable_count - lineage_parent_count
    child_count = len(children)
    active_targets = legacy_active_targets + child_count
    blocked_children = sum(child["coverage_status"] == "coverage_blocked" for child in children)
    active_blocked = int(predecessor_denominator["coverage_blocked_cells"]) - lineage_parent_count + blocked_children
    return {
        "source_units": source_unit_count,
        "legacy_unknown_rights_units": unknown_rights_count,
        "rule_slots_R": int(predecessor_denominator["rule_slots_R"]),
        "v2_visible_cells": len(v2_cells),
        "v3_child_cells": child_count,
        "visible_cells": len(v2_cells) + child_count,
        "active_coverage_target_cells": active_targets,
        "active_coverage_blocked_cells": active_blocked,
        "not_applicable_cells": not_applicable_count,
        "lineage_only_parent_cells": lineage_parent_count,
        "legacy_blocked_snapshot_records": (int(predecessor_denominator["coverage_blocked_cells"]) + blocked_children),
        "satisfied_cells": active_targets - active_blocked,
        "no_double_count_proof": (
            f"{legacy_active_targets}_v2_targets_excluding_parent_plus_{child_count}_children_equals_{active_targets}"
        ),
    }


def build_main() -> dict[str, Any]:
    verify_predecessors()
    p1 = read_json(P1_PATH)
    v3 = read_json(V3_ARTIFACT_PATH)
    children = _children()
    rights_rows = _rights_rows(p1)
    denominator = _derive_denominator(p1, v3, children)
    taxonomy = copy.deepcopy(v3["taxonomy"])
    taxonomy.pop("dialect_parent_partition")
    return with_receipt(
        {
            "schema_version": "phase3-v3a-taxonomy-denominator-compatibility-v1",
            "artifact_type": "v3a_taxonomy_denominator_receipt",
            "status": "FROZEN_METADATA_ONLY",
            "text_free": True,
            "controlling_outcome_sha256": V2_OUTCOME_SHA256,
            "reviewed_v3_consensus_sha256": V3_CONSENSUS_SHA256,
            "bindings": {
                "schema": binding(SCHEMA_PATH),
                "validator": binding(SCRIPT_PATH),
                "p1_universe": binding(P1_PATH),
                "p1_dialect_amendment": binding(P1_DIALECT_PATH),
                "p2_contracts": binding(P2_PATH),
                "v3_control_plane_schema": binding(V3_SCHEMA_PATH),
                "v3_control_plane_artifact": binding(V3_ARTIFACT_PATH),
                "v2_compatibility_matrix": binding(V2_MATRIX_PATH),
                "source_policy_v4": binding(SOURCE_POLICY_PATH),
            },
            "taxonomy": taxonomy,
            "dialect_partition": {
                "parent_cell_id": PARENT_CELL_ID,
                "partition_dimensions": ["source", "region", "period", "register"],
                "partition_level": "complete_top_level_macro_region_taxonomy",
                "partition_complete": True,
                "membership_frozen": True,
                "parent_denominator_visible": True,
                "parent_legacy_coverage_status": "coverage_blocked",
                "parent_coverage_role": "lineage_only",
                "parent_direct_coverage_credit": False,
                "source_attestation": {
                    "source_id": SOURCE_ID,
                    "jsonl_sha256": JSONL_SHA256,
                    "front_matter_rows_sha256": FRONT_MATTER_ROWS_SHA256,
                    "local_materialization": {
                        "canonicalization": "sorted_chunk_id_jsonl_v1",
                        "row_count": LOCAL_SOURCE_ROW_COUNT,
                        "rows_sha256": LOCAL_SOURCE_ROWS_SHA256,
                    },
                    "source_body_embedded": False,
                    "coverage_depth": "partial",
                },
                "child_strata": children,
                "finer_dialect_depth_complete": False,
                "example_coverage_complete": False,
            },
            "denominator": denominator,
            "rights_capabilities": {
                "operations": list(OPERATIONS),
                "source_unit_rows": rights_rows,
                "source_unit_count": len(rights_rows),
                "operation_cell_count": len(rights_rows) * len(OPERATIONS),
                "unknown_source_units_by_operation": {operation: len(rights_rows) for operation in OPERATIONS},
                "availability_grants_no_capability": True,
                "unknown_blocks_only_affected_operation": True,
                "execution_authorization_is_separate": True,
            },
            "execution_gates": {
                "provider_calls_authorized": False,
                "labeling_authorized": False,
                "training_authorized": False,
                "p4_v1_mutation_allowed": False,
            },
            "heldout_contract": {
                "owner_issue": 7561,
                "abstract_stratum_ids_visible": True,
                "membership_present": False,
                "locators_present": False,
                "fingerprints_present": False,
            },
            "residuals": [
                "dialect_child_example_coverage_and_finer_depth_remain_blocked",
                "operation_specific_rights_evidence_not_yet_frozen",
                "heldout_membership_owned_by_issue_7561",
                "rule_denominator_R_remains_zero",
            ],
        }
    )


def build_matrix(main: Mapping[str, Any]) -> dict[str, Any]:
    v3 = read_json(V3_ARTIFACT_PATH)
    child_ids = [row["stratum_id"] for row in main["dialect_partition"]["child_strata"]]
    rows = copy.deepcopy(v3["compatibility"]["cells"])
    require(len(rows) == 16, "V3 predecessor compatibility row count drift")
    for row in rows:
        if row["v2_cell_id"] == PARENT_CELL_ID:
            row["disposition"] = "superseded_by_partition"
            row["new_binding"] = binding(ARTIFACT_PATH)
            row["child_partition_ids"] = child_ids
            row["denominator_effect"] = "parent_visible_children_no_double_count"
            row["reason_code"] = "v3_a_source_attested_macro_region_partition_frozen"
    return with_receipt(
        {
            "schema_version": "phase3-v3a-taxonomy-denominator-compatibility-v1",
            "artifact_type": "v3a_compatibility_matrix",
            "status": "FROZEN_METADATA_ONLY",
            "text_free": True,
            "v2_parent_outcome_sha256": V2_OUTCOME_SHA256,
            "v3a_artifact_binding": binding(ARTIFACT_PATH),
            "v3_predecessor_binding": binding(V3_ARTIFACT_PATH),
            "rows": rows,
            "row_count": 16,
            "carried_forward_exact_count": 15,
            "superseded_by_partition_count": 1,
            "source_unit_ids_stable": True,
            "parent_denominator_visible": True,
            "parent_direct_coverage_credit": False,
        }
    )


def _validate_schema(value: Mapping[str, Any]) -> None:
    schema = read_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.absolute_path))
    if errors:
        location = "/".join(str(item) for item in errors[0].absolute_path) or "artifact"
        raise V3AError(f"schema violation at {location}: {errors[0].message}")


def validate(main: Mapping[str, Any], matrix: Mapping[str, Any]) -> None:
    verify_predecessors()
    _validate_schema(main)
    _validate_schema(matrix)
    _walk_forbidden(main)
    _walk_forbidden(matrix)
    require(main["receipt_sha256"] == receipt_sha(main), "main receipt hash drift")
    require(matrix["receipt_sha256"] == receipt_sha(matrix), "matrix receipt hash drift")
    bindings = main["bindings"]
    for name, expected_path in {
        "schema": SCHEMA_PATH,
        "validator": SCRIPT_PATH,
        "p1_universe": P1_PATH,
        "p1_dialect_amendment": P1_DIALECT_PATH,
        "p2_contracts": P2_PATH,
        "v3_control_plane_schema": V3_SCHEMA_PATH,
        "v3_control_plane_artifact": V3_ARTIFACT_PATH,
        "v2_compatibility_matrix": V2_MATRIX_PATH,
        "source_policy_v4": SOURCE_POLICY_PATH,
    }.items():
        require(bindings[name] == binding(expected_path), f"binding drift: {name}")

    expected_taxonomy = copy.deepcopy(read_json(V3_ARTIFACT_PATH)["taxonomy"])
    expected_taxonomy.pop("dialect_parent_partition")
    require(main["taxonomy"] == expected_taxonomy, "reviewed taxonomy drift")

    partition = main["dialect_partition"]
    children = partition["child_strata"]
    require(partition["partition_complete"] is True, "dialect partition is not complete")
    require(partition["membership_frozen"] is True, "dialect membership is not frozen")
    require(partition["parent_direct_coverage_credit"] is False, "dialect parent received coverage credit")
    require(
        partition["source_attestation"]
        == {
            "source_id": SOURCE_ID,
            "jsonl_sha256": JSONL_SHA256,
            "front_matter_rows_sha256": FRONT_MATTER_ROWS_SHA256,
            "local_materialization": {
                "canonicalization": "sorted_chunk_id_jsonl_v1",
                "row_count": LOCAL_SOURCE_ROW_COUNT,
                "rows_sha256": LOCAL_SOURCE_ROWS_SHA256,
            },
            "source_body_embedded": False,
            "coverage_depth": "partial",
        },
        "dialect source attestation drift",
    )
    require([row["region_id"] for row in children] == [row["region_id"] for row in CHILDREN], "dialect regions drift")
    require(len(children) == 3, "dialect partition must contain exactly three macro-regions")
    require(children == _children(), "dialect source evidence or lineage drift")
    for child in children:
        require(child["parent_cell_id"] == PARENT_CELL_ID, "dialect child parent drift")
        require(child["source_id"] == SOURCE_ID, "dialect child source drift")
        require(child["period_id"] == "contemporary_ukrainian", "dialect child period drift")
        require(child["register_id"] == "territorial_spoken_dialect", "dialect child register drift")
        require(child["coverage_status"] == "coverage_blocked", "dialect child falsely marked satisfied")
        require(child["coverage_credit"] is False, "dialect child received unearned credit")
        require(child["evidence_locators"], "dialect child lacks source evidence")

    denominator = main["denominator"]
    p1 = read_json(P1_PATH)
    v3 = read_json(V3_ARTIFACT_PATH)
    expected_denominator = _derive_denominator(p1, v3, _children())
    require(denominator == expected_denominator, "V3-A denominator drift")
    require(denominator["visible_cells"] == 19, "visible denominator drift")
    require(denominator["active_coverage_target_cells"] == 16, "active coverage denominator drift")
    require(denominator["active_coverage_blocked_cells"] == 16, "blocked target count drift")
    require(denominator["not_applicable_cells"] == 2, "N/A count drift")
    require(denominator["lineage_only_parent_cells"] == 1, "lineage parent count drift")
    require(denominator["visible_cells"] == 16 + 2 + 1, "denominator accounting is not exhaustive")

    rights = main["rights_capabilities"]
    require(tuple(rights["operations"]) == OPERATIONS, "rights operation order drift")
    source_unit_count = len(p1["source_manifest"]["source_units"])
    require(rights["source_unit_count"] == source_unit_count, "rights source-unit denominator drift")
    require(
        rights["operation_cell_count"] == source_unit_count * len(OPERATIONS),
        "rights operation-cell denominator drift",
    )
    require(
        rights["unknown_source_units_by_operation"] == {operation: source_unit_count for operation in OPERATIONS},
        "rights unresolved-operation counts drift",
    )
    p1_ids = sorted(row["source_unit_id"] for row in p1["source_manifest"]["source_units"])
    require([row["source_unit_id"] for row in rights["source_unit_rows"]] == p1_ids, "rights source IDs drift")
    require(rights["source_unit_rows"] == _rights_rows(p1), "rights evidence matrix drift")
    for row in rights["source_unit_rows"]:
        require([item["operation"] for item in row["operations"]] == list(OPERATIONS), "rights operation set drift")
        for item in row["operations"]:
            require(item["state"] == "unknown", "rights permission was inferred without operation evidence")
            if item["operation"] == "publish_text_or_metadata":
                qualifier = item.get("scope_qualifier", {})
                require(qualifier.get("combined_grant_forbidden") is True, "publication scope conflation")

    rows = matrix["rows"]
    require(len(rows) == 16, "compatibility row count drift")
    require(len({row["v2_cell_id"] for row in rows}) == 16, "compatibility IDs are not unique")
    parent = next(row for row in rows if row["v2_cell_id"] == PARENT_CELL_ID)
    require(parent["disposition"] == "superseded_by_partition", "dialect parent disposition drift")
    require(
        parent["denominator_effect"] == "parent_visible_children_no_double_count", "parent denominator effect drift"
    )
    require(parent["child_partition_ids"] == [row["stratum_id"] for row in children], "child compatibility drift")
    require(matrix["v3a_artifact_binding"] == binding(ARTIFACT_PATH), "matrix V3-A binding drift")
    require(sum(row["disposition"] == "carried_forward_exact" for row in rows) == 15, "carried row count drift")
    predecessor_rows = {row["v2_cell_id"]: row for row in read_json(V3_ARTIFACT_PATH)["compatibility"]["cells"]}
    for row in rows:
        if row["v2_cell_id"] != PARENT_CELL_ID:
            require(row == predecessor_rows[row["v2_cell_id"]], f"carried compatibility row drift: {row['v2_cell_id']}")
    require(
        main["execution_gates"]
        == {
            "provider_calls_authorized": False,
            "labeling_authorized": False,
            "training_authorized": False,
            "p4_v1_mutation_allowed": False,
        },
        "execution gates drift",
    )
    require(
        main["heldout_contract"]
        == {
            "owner_issue": 7561,
            "abstract_stratum_ids_visible": True,
            "membership_present": False,
            "locators_present": False,
            "fingerprints_present": False,
        },
        "held-out boundary drift",
    )


def write_outputs() -> None:
    main = build_main()
    ARTIFACT_PATH.write_bytes(canonical_bytes(main))
    matrix = build_matrix(main)
    MATRIX_PATH.write_bytes(canonical_bytes(matrix))
    validate(main, matrix)


def check_outputs() -> None:
    main = read_json(ARTIFACT_PATH)
    matrix = read_json(MATRIX_PATH)
    validate(main, matrix)
    require(ARTIFACT_PATH.read_bytes() == canonical_bytes(main), "main artifact is not canonical")
    require(MATRIX_PATH.read_bytes() == canonical_bytes(matrix), "compatibility matrix is not canonical")
    expected_main = build_main()
    require(main == expected_main, "main artifact is not deterministically reproduced")
    require(matrix == build_matrix(expected_main), "compatibility matrix is not deterministically reproduced")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--verify-source-db", type=Path)
    args = parser.parse_args()
    try:
        if args.verify_source_db:
            verify_source_db(args.verify_source_db)
        if args.write:
            write_outputs()
        else:
            check_outputs()
    except V3AError as exc:
        print(f"V3-A validation failed: {exc}", file=sys.stderr)
        return 1
    print("V3-A taxonomy denominator contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
