#!/usr/bin/env python3
"""Freeze the metadata-only Phase 3 V3-C held-out and solo-custody contract.

This module defines the custody boundary; it does not construct, expose, label,
evaluate, or train on a held-out example.  Source/document/work/edition/
duplicate identities are represented only by a future private commitment.  The
tracked artifact contains the exact V3-A denominator and per-stratum residuals,
but never held-out membership, source bodies, locators, labels, fingerprints,
derivatives, or private identities.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCHEMA_PATH = DATA / "contracts/phase3_v3c_heldout_extension_solo_custody_v1.schema.json"
ARTIFACT_PATH = DATA / "contracts/phase3_v3c_heldout_extension_solo_custody_v1.json"
SCRIPT_PATH = Path(__file__).resolve()

V3A_ARTIFACT_PATH = DATA / "contracts/phase3_v3a_taxonomy_denominator_compatibility_v1.json"
V3A_MATRIX_PATH = DATA / "contracts/phase3_v3a_compatibility_matrix_v1.json"

PARENT_OUTCOME_SHA256 = "890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47"
V3_CONSENSUS_SHA256 = "d3444c126deb91d05129d51c5344aa204b1db9ca0927c246698e0389466d0b1a"
V3A_ARTIFACT_SHA256 = "131d4b7286de0a6c079548b9eba21e5eec6804bbdd1dd41817e3ce58444d9a28"
V3A_MATRIX_SHA256 = "580a3785aa4af22a910a61c55d789c5d930f6fafaf317054ce070074ecf3ddbd"

SCHEMA_VERSION = "phase3-v3c-heldout-extension-solo-custody-v1"
RECEIPT_SCHEMA_VERSION = "phase3-v3c-custody-receipt-v1"
SOLO_OPERATOR_ROLE = "SOLO_OPERATOR_V1"
HASH_PATTERN = "^[0-9a-f]{64}$"

ACTIVE_BLOCKER = "SOURCE_OPERATION_RIGHTS_UNRESOLVED"
NOT_APPLICABLE_BLOCKER = "V3A_NOT_APPLICABLE_WITH_EVIDENCE"
LINEAGE_BLOCKER = "LINEAGE_ONLY_PARENT_NO_DIRECT_COVERAGE"

IDENTITY_DIMENSIONS = (
    "source_identity",
    "document_identity",
    "work_identity",
    "edition_identity",
    "duplicate_group_identity",
)
FIREWALL_FIELDS = (
    "construction_prompts_sha256",
    "construction_code_sha256",
    "construction_rules_sha256",
    "candidate_snapshot_sha256",
    "development_adjudications_sha256",
)
VISIBILITY_FORBIDDEN_FIELDS = (
    "heldout_identity",
    "heldout_content",
    "heldout_labels",
    "heldout_locators",
    "heldout_fingerprints",
    "heldout_derivatives",
    "heldout_near_neighbours",
)
STOP_CODES = (
    "SPLIT_LEAKAGE",
    "CYCLE007_CONTAMINATION",
    "POST_EXPOSURE_CONSTRUCTION_MUTATION",
    "SOURCE_IDENTITY_COLLISION",
    "DENOMINATOR_DRIFT",
)

CONSTRUCTION_ROLE_IDS = (
    "SOURCE_ADMISSION",
    "CONSTRUCTION_MODEL",
    "DEVELOPMENT_ADJUDICATOR",
    "CANDIDATE_BUILDER",
)

STATE_TRANSITIONS = (
    ("UNSEALED_NO_EXPOSURE", "SEALED_PRE_EXPOSURE", "all_construction_freeze_fields_committed"),
    ("SEALED_PRE_EXPOSURE", "EXPOSED", "sealed_cycle_exposed_by_solo_operator"),
    ("EXPOSED", "INVALIDATED_RESEAL_REQUIRED", "post_exposure_construction_mutation"),
    ("INVALIDATED_RESEAL_REQUIRED", "SEALED_PRE_EXPOSURE", "new_cycle_sealed_with_new_version"),
)

FORBIDDEN_FIELDS = frozenset(
    {
        "content",
        "text",
        "source_body",
        "source_content",
        "source_text",
        "heldout_content",
        "heldout_membership",
        "heldout_member",
        "heldout_identity",
        "heldout_ids",
        "heldout_locators",
        "heldout_fingerprints",
        "heldout_labels",
        "labels",
        "locators",
        "fingerprint",
        "fingerprints",
        "derivative",
        "derivatives",
        "near_neighbour",
        "near_neighbours",
        "private_identity",
        "provider_output",
    }
)


class V3CError(ValueError):
    """The V3-C contract or custody receipt stream is stale or unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise V3CError(message)


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except OSError as exc:
        raise V3CError(f"cannot hash artifact: {path}") from exc


def sha256_value(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def logical(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def binding(path: Path) -> dict[str, str]:
    require(path.is_file(), f"missing binding artifact: {logical(path)}")
    return {"path": logical(path), "sha256": sha256_file(path)}


def read_json(path: Path) -> dict[str, Any]:
    try:
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode) and not path.is_symlink(), f"artifact must be regular: {path}")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise V3CError(f"cannot read JSON artifact: {path}") from exc
    require(isinstance(value, dict), f"JSON artifact must be an object: {path}")
    return value


def receipt_sha(value: Mapping[str, Any], field: str = "receipt_sha256") -> str:
    body = dict(value)
    body.pop(field, None)
    return sha256_value(body)


def _with_hash(value: dict[str, Any], field: str) -> dict[str, Any]:
    value.pop(field, None)
    value[field] = receipt_sha(value, field)
    return value


def _walk_forbidden(value: Any, path: str = "artifact") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            require(key not in FORBIDDEN_FIELDS, f"forbidden field at {path}/{key}")
            _walk_forbidden(child, f"{path}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden(child, f"{path}/{index}")


def verify_predecessors() -> None:
    expected = {
        V3A_ARTIFACT_PATH: V3A_ARTIFACT_SHA256,
        V3A_MATRIX_PATH: V3A_MATRIX_SHA256,
    }
    for path, digest in expected.items():
        require(sha256_file(path) == digest, f"predecessor byte drift: {logical(path)}")


def _load_predecessors() -> tuple[dict[str, Any], dict[str, Any]]:
    verify_predecessors()
    return read_json(V3A_ARTIFACT_PATH), read_json(V3A_MATRIX_PATH)


def _visible_strata() -> list[dict[str, Any]]:
    """Expand the V3-A matrix into the exact 15+parent+3 visible rows."""
    v3a, matrix = _load_predecessors()
    denominator = v3a["denominator"]
    require(denominator["source_units"] == 57, "V3-A source-unit denominator drift")
    require(denominator["visible_cells"] == 19, "V3-A visible denominator drift")
    require(denominator["active_coverage_target_cells"] == 16, "V3-A active denominator drift")
    require(denominator["active_coverage_blocked_cells"] == 16, "V3-A blocked denominator drift")
    require(denominator["not_applicable_cells"] == 2, "V3-A N/A denominator drift")
    require(denominator["lineage_only_parent_cells"] == 1, "V3-A lineage denominator drift")
    rows = matrix.get("rows")
    require(isinstance(rows, list) and len(rows) == 16, "V3-A compatibility rows drift")
    children = v3a.get("dialect_partition", {}).get("child_strata")
    require(isinstance(children, list) and len(children) == 3, "V3-A child partition drift")
    result: list[dict[str, Any]] = []
    ordinal = 1
    for row in rows:
        stratum_id = row.get("v3_cell_id")
        require(isinstance(stratum_id, str) and stratum_id, "V3-A stratum identity missing")
        v2_status = row.get("v2_status")
        if row.get("disposition") == "superseded_by_partition":
            require(v2_status == "coverage_blocked", "V3-A parent status drift")
            result.append(_stratum_record(stratum_id, ordinal, "lineage_only", v2_status, LINEAGE_BLOCKER))
            ordinal += 1
            for child in children:
                child_id = child.get("stratum_id")
                require(isinstance(child_id, str) and child_id, "V3-A child stratum identity missing")
                result.append(_stratum_record(child_id, ordinal, "active_blocked", "coverage_blocked", ACTIVE_BLOCKER))
                ordinal += 1
            continue
        if v2_status == "not_applicable_with_evidence":
            result.append(_stratum_record(stratum_id, ordinal, "not_applicable", v2_status, NOT_APPLICABLE_BLOCKER))
        else:
            require(v2_status == "coverage_blocked", f"unexpected V3-A status: {v2_status!r}")
            result.append(_stratum_record(stratum_id, ordinal, "active_blocked", v2_status, ACTIVE_BLOCKER))
        ordinal += 1
    require(len(result) == 19, "V3-C visible stratum expansion drift")
    require(len({row["stratum_id"] for row in result}) == 19, "V3-C visible stratum collision")
    require(sum(row["denominator_class"] == "active_blocked" for row in result) == 16, "V3-C active rows drift")
    require(sum(row["denominator_class"] == "not_applicable" for row in result) == 2, "V3-C N/A rows drift")
    require(sum(row["denominator_class"] == "lineage_only" for row in result) == 1, "V3-C lineage row drift")
    return result


def _stratum_record(
    stratum_id: str,
    ordinal: int,
    denominator_class: str,
    predecessor_status: str,
    blocker_code: str,
) -> dict[str, Any]:
    active = denominator_class == "active_blocked"
    return {
        "stratum_id": stratum_id,
        "denominator_ordinal": ordinal,
        "denominator_visible": True,
        "denominator_class": denominator_class,
        "predecessor_status": predecessor_status,
        "heldout_requirement": {
            "exact": True,
            "required_item_count": 1 if active else None,
            "requirement_state": "blocked" if active else denominator_class,
            "blocker_code": blocker_code,
            "blocker_is_denominator_visible": True,
        },
        "evaluation_threshold": {
            "minimum_eligible_item_count": 1 if active else None,
            "minimum_direct_human_review_fraction": 1.0,
            "abstention_is_not_gold": True,
            "applies_only_when_requirement_admitted": True,
        },
    }


def _denominator() -> dict[str, int]:
    v3a, _matrix = _load_predecessors()
    source = v3a["denominator"]
    return {
        "source_units": int(source["source_units"]),
        "visible_cells": int(source["visible_cells"]),
        "active_coverage_target_cells": int(source["active_coverage_target_cells"]),
        "active_coverage_blocked_cells": int(source["active_coverage_blocked_cells"]),
        "not_applicable_cells": int(source["not_applicable_cells"]),
        "lineage_only_parent_cells": int(source["lineage_only_parent_cells"]),
        "rights_operation_cells": 399,
        "rule_slots_R": 0,
    }


def _build_requirement_ledger(strata: Sequence[Mapping[str, Any]], denominator: Mapping[str, Any]) -> dict[str, Any]:
    ledger = {
        "ledger_id": "v3c_per_stratum_requirement_ledger_v1",
        "denominator_sha256": sha256_value(denominator),
        "visible_stratum_count": 19,
        "active_target_count": 16,
        "blocked_target_count": 16,
        "not_applicable_count": 2,
        "lineage_only_count": 1,
        "rows": [dict(row) for row in strata],
        "exact_row_count": 19,
        "no_silent_zero": True,
        "zero_requirement_rows_must_have_blocker": True,
    }
    return _with_hash(ledger, "ledger_sha256")


def _identity_group_freeze() -> dict[str, Any]:
    dimensions = [
        {
            "dimension_id": dimension,
            "frozen": True,
            "private_input_required": True,
            "public_membership_present": False,
            "actual_membership_present": False,
            "commitment_present": False,
            "grouping_role": "same_group_never_split",
        }
        for dimension in IDENTITY_DIMENSIONS
    ]
    body = {
        "freeze_id": "v3c_identity_group_freeze_v1",
        "status": "FROZEN_ALGORITHM_ONLY_NO_MEMBERSHIP",
        "dimensions": dimensions,
        "dimension_order_is_frozen": True,
        "all_identity_dimensions_frozen": True,
        "source_admission_assigns_hidden_membership": False,
        "construction_receives_hidden_membership": False,
        "identity_collision_policy": "GLOBAL_STOP_SOURCE_IDENTITY_COLLISION",
        "duplicate_group_policy": "duplicate_group_is_atomic_split_unit",
        "private_materialization": "deferred_until_rights_and_sealed_private_cycle",
    }
    body["freeze_descriptor_sha256"] = sha256_value(body)
    return body


def _split_assignment(identity_freeze: Mapping[str, Any]) -> dict[str, Any]:
    body = {
        "algorithm_id": "v3c_sha256_grouped_stratified_split_v1",
        "algorithm_version": 1,
        "assignment_unit": "duplicate_group_identity",
        "identity_dimensions": list(IDENTITY_DIMENSIONS),
        "grouping_before_split": True,
        "same_group_never_split": True,
        "bucket_count": 10000,
        "heldout_bucket_range": [0, 999],
        "construction_bucket_range": [1000, 9999],
        "heldout_target_rate_basis_points": 1000,
        "minimum_nonzero_requirement_per_admitted_active_stratum": 1,
        "assignment_formula": "bucket=SHA256(domain|canonical_group_identity|salt_commitment) modulo 10000",
        "salt_commitment_sha256": sha256_value("phase3-v3c-heldout-split-salt-v1"),
        "identity_freeze_descriptor_sha256": identity_freeze["freeze_descriptor_sha256"],
        "source_admission_assigns_hidden_membership": False,
        "membership_present": False,
        "membership_commitment_present": False,
        "construction_can_infer_membership": False,
        "construction_access": "forbidden",
        "preconstruction_freeze_required": True,
        "assignment_is_deterministic": True,
        "assignment_is_content_blind": True,
    }
    body["algorithm_descriptor_sha256"] = sha256_value(body)
    return body


def _construction_visibility() -> dict[str, Any]:
    roles = []
    for role_id in CONSTRUCTION_ROLE_IDS:
        roles.append(
            {
                "role_id": role_id,
                "heldout_identity_visible": False,
                "heldout_content_visible": False,
                "heldout_labels_visible": False,
                "heldout_locators_visible": False,
                "heldout_fingerprints_visible": False,
                "heldout_derivatives_visible": False,
                "heldout_near_neighbours_visible": False,
                "forbidden_fields": list(VISIBILITY_FORBIDDEN_FIELDS),
            }
        )
    return {
        "contract_id": "v3c_construction_visibility_v1",
        "construction_roles": roles,
        "all_construction_roles_blind": True,
        "heldout_access_is_deny_by_default": True,
        "source_admission_may_read_rights_only": True,
        "development_adjudication_is_construction_input": True,
        "heldout_membership_never_enters_construction_prompt": True,
    }


def _temporal_firewall(identity_freeze: Mapping[str, Any], split: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "firewall_id": "v3c_solo_operator_temporal_firewall_v1",
        "operator_role_id": SOLO_OPERATOR_ROLE,
        "pre_exposure_construction_freeze_required": True,
        "freeze_fields": list(FIREWALL_FIELDS),
        "freeze_field_commitments": {field: None for field in FIREWALL_FIELDS},
        "identity_freeze_descriptor_sha256": identity_freeze["freeze_descriptor_sha256"],
        "split_algorithm_descriptor_sha256": split["algorithm_descriptor_sha256"],
        "construction_mutation_after_exposure": False,
        "exposure_requires_all_freeze_fields": True,
        "exposure_before_freeze_forbidden": True,
        "post_exposure_mutation_action": "invalidate_evaluation_version_and_require_new_sealed_cycle",
        "current_cycle_state": "UNSEALED_NO_EXPOSURE",
        "exposure_allowed": False,
        "evaluation_version_present": False,
        "new_cycle_required_after_invalidation": True,
    }


def _custody_receipt_contract(ledger: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_ref": "#/$defs/custodyReceipt",
        "append_only": True,
        "update_or_delete_permitted": False,
        "contiguous_sequence_required": True,
        "previous_hash_chain_required": True,
        "byte_identical_replay_only": True,
        "divergent_replay_rejected": True,
        "duplicates_in_canonical_stream_forbidden": True,
        "exposure_requires_pre_exposure_seal": True,
        "invalidation_requires_prior_exposure": True,
        "invalidation_requires_new_cycle": True,
        "sealed_commitment_pair_reuse_forbidden": True,
        "construction_mutation_after_exposure_is_global_stop": True,
        "ledger_sha256": ledger["ledger_sha256"],
        "rows": [],
        "row_count": 0,
        "head_receipt_sha256": None,
    }


def _solo_custody() -> dict[str, Any]:
    body = {
        "operator_role_id": SOLO_OPERATOR_ROLE,
        "operator_count": 1,
        "credential_claimed": False,
        "institutional_independence_claimed": False,
        "independent_adjudicator_claimed": False,
        "disclosure": "One pseudonymous operator controls custody; this is not institutional or independent adjudication.",
        "ambiguity_action": "abstain_non_gold",
        "direct_inspection_required_for_gold": True,
        "registry_materialized": False,
        "private_identity_present": False,
    }
    body["custody_disclosure_sha256"] = sha256_value(body)
    return body


def _evaluation_policy(strata: Sequence[Mapping[str, Any]], ledger: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "evaluation_version_status": "NOT_CREATED_NO_EXPOSURE",
        "heldout_exposure_authorized": False,
        "per_stratum_thresholds": [
            {
                "stratum_id": row["stratum_id"],
                "minimum_eligible_item_count": row["evaluation_threshold"]["minimum_eligible_item_count"],
                "minimum_direct_human_review_fraction": 1.0,
                "abstention_is_not_gold": True,
                "requirement_state": row["heldout_requirement"]["requirement_state"],
                "blocker_code": row["heldout_requirement"]["blocker_code"],
            }
            for row in strata
        ],
        "threshold_row_count": 19,
        "requirement_ledger_sha256": ledger["ledger_sha256"],
        "gold_requires_direct_human_inspection": True,
        "gold_requires_evidence_bound_decision": True,
        "abstention_is_never_gold": True,
        "model_agreement_is_never_gold": True,
        "training_labels_created": 0,
    }


def _residual_query(strata: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = []
    for row in strata:
        requirement = row["heldout_requirement"]
        rows.append(
            {
                "stratum_id": row["stratum_id"],
                "denominator_ordinal": row["denominator_ordinal"],
                "residual_code": requirement["blocker_code"],
                "blocking": True,
                "owner_role_id": SOLO_OPERATOR_ROLE,
                "safe_next_action": "resolve_rights_or_source_evidence_without_receiving_hidden_membership",
            }
        )
    return {
        "row_contract": {
            "required_fields": [
                "stratum_id",
                "denominator_ordinal",
                "residual_code",
                "blocking",
                "owner_role_id",
                "safe_next_action",
            ],
            "all_denominator_rows_visible": True,
        },
        "rows": rows,
        "row_count": len(rows),
        "query_is_machine_readable": True,
    }


def _state_machine() -> dict[str, Any]:
    return {
        "states": [
            "UNSEALED_NO_EXPOSURE",
            "SEALED_PRE_EXPOSURE",
            "EXPOSED",
            "INVALIDATED_RESEAL_REQUIRED",
        ],
        "transitions": [
            {"from_state": source, "to_state": target, "condition_code": condition}
            for source, target, condition in STATE_TRANSITIONS
        ],
        "initial_state": "UNSEALED_NO_EXPOSURE",
        "terminal_state": "EXPOSED",
        "global_stop_codes": list(STOP_CODES),
        "post_exposure_mutation_has_no_continue_edge": True,
        "invalidated_cycle_cannot_be_reused": True,
    }


def build_schema() -> dict[str, Any]:
    hash_schema = {"type": "string", "pattern": HASH_PATTERN}
    nullable_hash = {"anyOf": [hash_schema, {"type": "null"}]}

    def strict(properties: Mapping[str, Any], required: Sequence[str]) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": list(required),
            "properties": dict(properties),
        }

    definitions: dict[str, Any] = {
        "hash": hash_schema,
        "binding": strict({"path": {"type": "string", "minLength": 1}, "sha256": hash_schema}, ("path", "sha256")),
        "requirement": strict(
            {
                "exact": {"const": True},
                "required_item_count": {"anyOf": [{"type": "integer", "minimum": 1}, {"type": "null"}]},
                "requirement_state": {"enum": ["blocked", "not_applicable", "lineage_only"]},
                "blocker_code": {"type": "string", "minLength": 1},
                "blocker_is_denominator_visible": {"const": True},
            },
            ("exact", "required_item_count", "requirement_state", "blocker_code", "blocker_is_denominator_visible"),
        ),
        "threshold": strict(
            {
                "minimum_eligible_item_count": {
                    "anyOf": [{"type": "integer", "minimum": 1}, {"type": "null"}]
                },
                "minimum_direct_human_review_fraction": {"const": 1.0},
                "abstention_is_not_gold": {"const": True},
                "applies_only_when_requirement_admitted": {"const": True},
            },
            (
                "minimum_eligible_item_count",
                "minimum_direct_human_review_fraction",
                "abstention_is_not_gold",
                "applies_only_when_requirement_admitted",
            ),
        ),
        "stratum": strict(
            {
                "stratum_id": {"type": "string", "minLength": 1},
                "denominator_ordinal": {"type": "integer", "minimum": 1, "maximum": 19},
                "denominator_visible": {"const": True},
                "denominator_class": {"enum": ["active_blocked", "not_applicable", "lineage_only"]},
                "predecessor_status": {"type": "string", "minLength": 1},
                "heldout_requirement": {"$ref": "#/$defs/requirement"},
                "evaluation_threshold": {"$ref": "#/$defs/threshold"},
            },
            (
                "stratum_id",
                "denominator_ordinal",
                "denominator_visible",
                "denominator_class",
                "predecessor_status",
                "heldout_requirement",
                "evaluation_threshold",
            ),
        ),
        "ledger": strict(
            {
                "ledger_id": {"const": "v3c_per_stratum_requirement_ledger_v1"},
                "denominator_sha256": hash_schema,
                "visible_stratum_count": {"const": 19},
                "active_target_count": {"const": 16},
                "blocked_target_count": {"const": 16},
                "not_applicable_count": {"const": 2},
                "lineage_only_count": {"const": 1},
                "rows": {"type": "array", "minItems": 19, "maxItems": 19, "items": {"$ref": "#/$defs/stratum"}},
                "exact_row_count": {"const": 19},
                "no_silent_zero": {"const": True},
                "zero_requirement_rows_must_have_blocker": {"const": True},
                "ledger_sha256": hash_schema,
            },
            (
                "ledger_id",
                "denominator_sha256",
                "visible_stratum_count",
                "active_target_count",
                "blocked_target_count",
                "not_applicable_count",
                "lineage_only_count",
                "rows",
                "exact_row_count",
                "no_silent_zero",
                "zero_requirement_rows_must_have_blocker",
                "ledger_sha256",
            ),
        ),
        "identityDimension": strict(
            {
                "dimension_id": {"enum": list(IDENTITY_DIMENSIONS)},
                "frozen": {"const": True},
                "private_input_required": {"const": True},
                "public_membership_present": {"const": False},
                "actual_membership_present": {"const": False},
                "commitment_present": {"const": False},
                "grouping_role": {"const": "same_group_never_split"},
            },
            (
                "dimension_id",
                "frozen",
                "private_input_required",
                "public_membership_present",
                "actual_membership_present",
                "commitment_present",
                "grouping_role",
            ),
        ),
        "identityFreeze": strict(
            {
                "freeze_id": {"const": "v3c_identity_group_freeze_v1"},
                "status": {"const": "FROZEN_ALGORITHM_ONLY_NO_MEMBERSHIP"},
                "dimensions": {"type": "array", "minItems": 5, "maxItems": 5, "items": {"$ref": "#/$defs/identityDimension"}},
                "dimension_order_is_frozen": {"const": True},
                "all_identity_dimensions_frozen": {"const": True},
                "source_admission_assigns_hidden_membership": {"const": False},
                "construction_receives_hidden_membership": {"const": False},
                "identity_collision_policy": {"const": "GLOBAL_STOP_SOURCE_IDENTITY_COLLISION"},
                "duplicate_group_policy": {"const": "duplicate_group_is_atomic_split_unit"},
                "private_materialization": {"const": "deferred_until_rights_and_sealed_private_cycle"},
                "freeze_descriptor_sha256": hash_schema,
            },
            (
                "freeze_id",
                "status",
                "dimensions",
                "dimension_order_is_frozen",
                "all_identity_dimensions_frozen",
                "source_admission_assigns_hidden_membership",
                "construction_receives_hidden_membership",
                "identity_collision_policy",
                "duplicate_group_policy",
                "private_materialization",
                "freeze_descriptor_sha256",
            ),
        ),
        "splitAssignment": strict(
            {
                "algorithm_id": {"const": "v3c_sha256_grouped_stratified_split_v1"},
                "algorithm_version": {"const": 1},
                "assignment_unit": {"const": "duplicate_group_identity"},
                "identity_dimensions": {"const": list(IDENTITY_DIMENSIONS)},
                "grouping_before_split": {"const": True},
                "same_group_never_split": {"const": True},
                "bucket_count": {"const": 10000},
                "heldout_bucket_range": {"const": [0, 999]},
                "construction_bucket_range": {"const": [1000, 9999]},
                "heldout_target_rate_basis_points": {"const": 1000},
                "minimum_nonzero_requirement_per_admitted_active_stratum": {"const": 1},
                "assignment_formula": {"type": "string", "minLength": 1},
                "salt_commitment_sha256": hash_schema,
                "identity_freeze_descriptor_sha256": hash_schema,
                "source_admission_assigns_hidden_membership": {"const": False},
                "membership_present": {"const": False},
                "membership_commitment_present": {"const": False},
                "construction_can_infer_membership": {"const": False},
                "construction_access": {"const": "forbidden"},
                "preconstruction_freeze_required": {"const": True},
                "assignment_is_deterministic": {"const": True},
                "assignment_is_content_blind": {"const": True},
                "algorithm_descriptor_sha256": hash_schema,
            },
            (
                "algorithm_id",
                "algorithm_version",
                "assignment_unit",
                "identity_dimensions",
                "grouping_before_split",
                "same_group_never_split",
                "bucket_count",
                "heldout_bucket_range",
                "construction_bucket_range",
                "heldout_target_rate_basis_points",
                "minimum_nonzero_requirement_per_admitted_active_stratum",
                "assignment_formula",
                "salt_commitment_sha256",
                "identity_freeze_descriptor_sha256",
                "source_admission_assigns_hidden_membership",
                "membership_present",
                "membership_commitment_present",
                "construction_can_infer_membership",
                "construction_access",
                "preconstruction_freeze_required",
                "assignment_is_deterministic",
                "assignment_is_content_blind",
                "algorithm_descriptor_sha256",
            ),
        ),
        "visibilityRole": strict(
            {
                "role_id": {"type": "string", "minLength": 1},
                "heldout_identity_visible": {"const": False},
                "heldout_content_visible": {"const": False},
                "heldout_labels_visible": {"const": False},
                "heldout_locators_visible": {"const": False},
                "heldout_fingerprints_visible": {"const": False},
                "heldout_derivatives_visible": {"const": False},
                "heldout_near_neighbours_visible": {"const": False},
                "forbidden_fields": {"type": "array", "items": {"type": "string", "minLength": 1}, "uniqueItems": True},
            },
            (
                "role_id",
                "heldout_identity_visible",
                "heldout_content_visible",
                "heldout_labels_visible",
                "heldout_locators_visible",
                "heldout_fingerprints_visible",
                "heldout_derivatives_visible",
                "heldout_near_neighbours_visible",
                "forbidden_fields",
            ),
        ),
        "visibility": strict(
            {
                "contract_id": {"const": "v3c_construction_visibility_v1"},
                "construction_roles": {"type": "array", "minItems": 4, "items": {"$ref": "#/$defs/visibilityRole"}},
                "all_construction_roles_blind": {"const": True},
                "heldout_access_is_deny_by_default": {"const": True},
                "source_admission_may_read_rights_only": {"const": True},
                "development_adjudication_is_construction_input": {"const": True},
                "heldout_membership_never_enters_construction_prompt": {"const": True},
            },
            (
                "contract_id",
                "construction_roles",
                "all_construction_roles_blind",
                "heldout_access_is_deny_by_default",
                "source_admission_may_read_rights_only",
                "development_adjudication_is_construction_input",
                "heldout_membership_never_enters_construction_prompt",
            ),
        ),
        "firewall": strict(
            {
                "firewall_id": {"const": "v3c_solo_operator_temporal_firewall_v1"},
                "operator_role_id": {"const": SOLO_OPERATOR_ROLE},
                "pre_exposure_construction_freeze_required": {"const": True},
                "freeze_fields": {"const": list(FIREWALL_FIELDS)},
                "freeze_field_commitments": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": list(FIREWALL_FIELDS),
                    "properties": {field: nullable_hash for field in FIREWALL_FIELDS},
                },
                "identity_freeze_descriptor_sha256": hash_schema,
                "split_algorithm_descriptor_sha256": hash_schema,
                "construction_mutation_after_exposure": {"const": False},
                "exposure_requires_all_freeze_fields": {"const": True},
                "exposure_before_freeze_forbidden": {"const": True},
                "post_exposure_mutation_action": {"const": "invalidate_evaluation_version_and_require_new_sealed_cycle"},
                "current_cycle_state": {"const": "UNSEALED_NO_EXPOSURE"},
                "exposure_allowed": {"const": False},
                "evaluation_version_present": {"const": False},
                "new_cycle_required_after_invalidation": {"const": True},
            },
            (
                "firewall_id",
                "operator_role_id",
                "pre_exposure_construction_freeze_required",
                "freeze_fields",
                "freeze_field_commitments",
                "identity_freeze_descriptor_sha256",
                "split_algorithm_descriptor_sha256",
                "construction_mutation_after_exposure",
                "exposure_requires_all_freeze_fields",
                "exposure_before_freeze_forbidden",
                "post_exposure_mutation_action",
                "current_cycle_state",
                "exposure_allowed",
                "evaluation_version_present",
                "new_cycle_required_after_invalidation",
            ),
        ),
        "custodyReceipt": strict(
            {
                "schema_version": {"const": RECEIPT_SCHEMA_VERSION},
                "receipt_id": hash_schema,
                "sequence": {"type": "integer", "minimum": 0},
                "cycle_id": {"type": "string", "minLength": 1},
                "event_type": {"enum": ["cycle_sealed", "exposure", "invalidation"]},
                "cycle_status": {"enum": ["SEALED_PRE_EXPOSURE", "EXPOSED", "INVALIDATED_RESEAL_REQUIRED"]},
                "operator_role_id": {"const": SOLO_OPERATOR_ROLE},
                "construction_mutation_after_exposure": {"type": "boolean"},
                "new_cycle_required": {"type": "boolean"},
                "freeze_field_count": {"const": len(FIREWALL_FIELDS)},
                "freeze_commitment_sha256": hash_schema,
                "evaluation_version_sha256": hash_schema,
                "requirement_ledger_sha256": hash_schema,
                "reason_code": {"type": "string", "minLength": 1},
                "previous_receipt_sha256": nullable_hash,
                "receipt_sha256": hash_schema,
            },
            (
                "schema_version",
                "receipt_id",
                "sequence",
                "cycle_id",
                "event_type",
                "cycle_status",
                "operator_role_id",
                "construction_mutation_after_exposure",
                "new_cycle_required",
                "freeze_field_count",
                "freeze_commitment_sha256",
                "evaluation_version_sha256",
                "requirement_ledger_sha256",
                "reason_code",
                "previous_receipt_sha256",
                "receipt_sha256",
            ),
        ),
        "receiptContract": strict(
            {
                "schema_ref": {"const": "#/$defs/custodyReceipt"},
                "append_only": {"const": True},
                "update_or_delete_permitted": {"const": False},
                "contiguous_sequence_required": {"const": True},
                "previous_hash_chain_required": {"const": True},
                "byte_identical_replay_only": {"const": True},
                "divergent_replay_rejected": {"const": True},
                "duplicates_in_canonical_stream_forbidden": {"const": True},
                "exposure_requires_pre_exposure_seal": {"const": True},
                "invalidation_requires_prior_exposure": {"const": True},
                "invalidation_requires_new_cycle": {"const": True},
                "sealed_commitment_pair_reuse_forbidden": {"const": True},
                "construction_mutation_after_exposure_is_global_stop": {"const": True},
                "ledger_sha256": hash_schema,
                "rows": {"type": "array", "maxItems": 0, "items": {"$ref": "#/$defs/custodyReceipt"}},
                "row_count": {"const": 0},
                "head_receipt_sha256": {"type": "null"},
            },
            (
                "schema_ref",
                "append_only",
                "update_or_delete_permitted",
                "contiguous_sequence_required",
                "previous_hash_chain_required",
                "byte_identical_replay_only",
                "divergent_replay_rejected",
                "duplicates_in_canonical_stream_forbidden",
                "exposure_requires_pre_exposure_seal",
                "invalidation_requires_prior_exposure",
                "invalidation_requires_new_cycle",
                "sealed_commitment_pair_reuse_forbidden",
                "construction_mutation_after_exposure_is_global_stop",
                "ledger_sha256",
                "rows",
                "row_count",
                "head_receipt_sha256",
            ),
        ),
        "soloCustody": strict(
            {
                "operator_role_id": {"const": SOLO_OPERATOR_ROLE},
                "operator_count": {"const": 1},
                "credential_claimed": {"const": False},
                "institutional_independence_claimed": {"const": False},
                "independent_adjudicator_claimed": {"const": False},
                "disclosure": {"type": "string", "minLength": 1},
                "ambiguity_action": {"const": "abstain_non_gold"},
                "direct_inspection_required_for_gold": {"const": True},
                "registry_materialized": {"const": False},
                "private_identity_present": {"const": False},
                "custody_disclosure_sha256": hash_schema,
            },
            (
                "operator_role_id",
                "operator_count",
                "credential_claimed",
                "institutional_independence_claimed",
                "independent_adjudicator_claimed",
                "disclosure",
                "ambiguity_action",
                "direct_inspection_required_for_gold",
                "registry_materialized",
                "private_identity_present",
                "custody_disclosure_sha256",
            ),
        ),
        "evaluation": strict(
            {
                "evaluation_version_status": {"const": "NOT_CREATED_NO_EXPOSURE"},
                "heldout_exposure_authorized": {"const": False},
                "per_stratum_thresholds": {
                    "type": "array",
                    "minItems": 19,
                    "maxItems": 19,
                    "items": strict(
                        {
                            "stratum_id": {"type": "string", "minLength": 1},
                            "minimum_eligible_item_count": {"anyOf": [{"type": "integer", "minimum": 1}, {"type": "null"}]},
                            "minimum_direct_human_review_fraction": {"const": 1.0},
                            "abstention_is_not_gold": {"const": True},
                            "requirement_state": {"enum": ["blocked", "not_applicable", "lineage_only"]},
                            "blocker_code": {"type": "string", "minLength": 1},
                        },
                        (
                            "stratum_id",
                            "minimum_eligible_item_count",
                            "minimum_direct_human_review_fraction",
                            "abstention_is_not_gold",
                            "requirement_state",
                            "blocker_code",
                        ),
                    ),
                },
                "threshold_row_count": {"const": 19},
                "requirement_ledger_sha256": hash_schema,
                "gold_requires_direct_human_inspection": {"const": True},
                "gold_requires_evidence_bound_decision": {"const": True},
                "abstention_is_never_gold": {"const": True},
                "model_agreement_is_never_gold": {"const": True},
                "training_labels_created": {"const": 0},
            },
            (
                "evaluation_version_status",
                "heldout_exposure_authorized",
                "per_stratum_thresholds",
                "threshold_row_count",
                "requirement_ledger_sha256",
                "gold_requires_direct_human_inspection",
                "gold_requires_evidence_bound_decision",
                "abstention_is_never_gold",
                "model_agreement_is_never_gold",
                "training_labels_created",
            ),
        ),
        "residualRow": strict(
            {
                "stratum_id": {"type": "string", "minLength": 1},
                "denominator_ordinal": {"type": "integer", "minimum": 1, "maximum": 19},
                "residual_code": {"type": "string", "minLength": 1},
                "blocking": {"const": True},
                "owner_role_id": {"const": SOLO_OPERATOR_ROLE},
                "safe_next_action": {"type": "string", "minLength": 1},
            },
            (
                "stratum_id",
                "denominator_ordinal",
                "residual_code",
                "blocking",
                "owner_role_id",
                "safe_next_action",
            ),
        ),
        "residualQuery": strict(
            {
                "row_contract": strict(
                    {
                        "required_fields": {"const": ["stratum_id", "denominator_ordinal", "residual_code", "blocking", "owner_role_id", "safe_next_action"]},
                        "all_denominator_rows_visible": {"const": True},
                    },
                    ("required_fields", "all_denominator_rows_visible"),
                ),
                "rows": {"type": "array", "minItems": 19, "maxItems": 19, "items": {"$ref": "#/$defs/residualRow"}},
                "row_count": {"const": 19},
                "query_is_machine_readable": {"const": True},
            },
            ("row_contract", "rows", "row_count", "query_is_machine_readable"),
        ),
        "stateMachine": strict(
            {
                "states": {"const": ["UNSEALED_NO_EXPOSURE", "SEALED_PRE_EXPOSURE", "EXPOSED", "INVALIDATED_RESEAL_REQUIRED"]},
                "transitions": {
                    "const": [
                        {"from_state": source, "to_state": target, "condition_code": condition}
                        for source, target, condition in STATE_TRANSITIONS
                    ]
                },
                "initial_state": {"const": "UNSEALED_NO_EXPOSURE"},
                "terminal_state": {"const": "EXPOSED"},
                "global_stop_codes": {"const": list(STOP_CODES)},
                "post_exposure_mutation_has_no_continue_edge": {"const": True},
                "invalidated_cycle_cannot_be_reused": {"const": True},
            },
            (
                "states",
                "transitions",
                "initial_state",
                "terminal_state",
                "global_stop_codes",
                "post_exposure_mutation_has_no_continue_edge",
                "invalidated_cycle_cannot_be_reused",
            ),
        ),
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://learn-ukrainian.github.io/contracts/phase3_v3c_heldout_extension_solo_custody_v1.schema.json",
        "title": "Phase 3 V3-C held-out extension and solo custody",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "artifact_type",
            "status",
            "text_free",
            "metadata_only",
            "outcome_boundary",
            "bindings",
            "denominator",
            "strata",
            "requirement_ledger",
            "identity_group_freeze",
            "split_assignment",
            "construction_visibility",
            "solo_operator_custody",
            "temporal_firewall",
            "evaluation_policy",
            "custody_receipts",
            "residual_query",
            "state_machine",
            "execution_gates",
            "stop_policy",
            "receipt_sha256",
        ],
        "properties": {
            "schema_version": {"const": SCHEMA_VERSION},
            "artifact_type": {"const": "v3c_heldout_extension_solo_custody_receipt"},
            "status": {"const": "FROZEN_METADATA_ONLY_NO_EXPOSURE"},
            "text_free": {"const": True},
            "metadata_only": {"const": True},
            "outcome_boundary": {"$ref": "#/$defs/outcomeBoundary"},
            "bindings": {"type": "object", "additionalProperties": {"$ref": "#/$defs/binding"}, "minProperties": 4},
            "denominator": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "source_units",
                    "visible_cells",
                    "active_coverage_target_cells",
                    "active_coverage_blocked_cells",
                    "not_applicable_cells",
                    "lineage_only_parent_cells",
                    "rights_operation_cells",
                    "rule_slots_R",
                ],
                "properties": {
                    "source_units": {"const": 57},
                    "visible_cells": {"const": 19},
                    "active_coverage_target_cells": {"const": 16},
                    "active_coverage_blocked_cells": {"const": 16},
                    "not_applicable_cells": {"const": 2},
                    "lineage_only_parent_cells": {"const": 1},
                    "rights_operation_cells": {"const": 399},
                    "rule_slots_R": {"const": 0},
                },
            },
            "strata": {"type": "array", "minItems": 19, "maxItems": 19, "items": {"$ref": "#/$defs/stratum"}},
            "requirement_ledger": {"$ref": "#/$defs/ledger"},
            "identity_group_freeze": {"$ref": "#/$defs/identityFreeze"},
            "split_assignment": {"$ref": "#/$defs/splitAssignment"},
            "construction_visibility": {"$ref": "#/$defs/visibility"},
            "solo_operator_custody": {"$ref": "#/$defs/soloCustody"},
            "temporal_firewall": {"$ref": "#/$defs/firewall"},
            "evaluation_policy": {"$ref": "#/$defs/evaluation"},
            "custody_receipts": {"$ref": "#/$defs/receiptContract"},
            "residual_query": {"$ref": "#/$defs/residualQuery"},
            "state_machine": {"$ref": "#/$defs/stateMachine"},
            "execution_gates": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "provider_calls_authorized",
                    "provider_call_count",
                    "labeling_authorized",
                    "labeling_count",
                    "evaluation_authorized",
                    "evaluation_runs",
                    "training_authorized",
                    "training_runs",
                    "heldout_rows_created",
                ],
                "properties": {
                    "provider_calls_authorized": {"const": False},
                    "provider_call_count": {"const": 0},
                    "labeling_authorized": {"const": False},
                    "labeling_count": {"const": 0},
                    "evaluation_authorized": {"const": False},
                    "evaluation_runs": {"const": 0},
                    "training_authorized": {"const": False},
                    "training_runs": {"const": 0},
                    "heldout_rows_created": {"const": 0},
                },
            },
            "stop_policy": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "global_stop_codes",
                    "fail_closed",
                    "safe_disjoint_work_may_continue",
                    "new_cycle_required_on_invalidation",
                ],
                "properties": {
                    "global_stop_codes": {"const": list(STOP_CODES)},
                    "fail_closed": {"const": True},
                    "safe_disjoint_work_may_continue": {"const": True},
                    "new_cycle_required_on_invalidation": {"const": True},
                },
            },
            "receipt_sha256": hash_schema,
        },
        "$defs": {
            **definitions,
            "outcomeBoundary": strict(
                {
                    "parent_outcome_sha256": {"const": PARENT_OUTCOME_SHA256},
                    "reviewed_v3_consensus_sha256": {"const": V3_CONSENSUS_SHA256},
                    "v3a_artifact_sha256": {"const": V3A_ARTIFACT_SHA256},
                    "heldout_membership_present": {"const": False},
                    "heldout_content_present": {"const": False},
                    "provider_calls": {"const": 0},
                    "labeling_count": {"const": 0},
                    "evaluation_runs": {"const": 0},
                    "training_runs": {"const": 0},
                },
                (
                    "parent_outcome_sha256",
                    "reviewed_v3_consensus_sha256",
                    "v3a_artifact_sha256",
                    "heldout_membership_present",
                    "heldout_content_present",
                    "provider_calls",
                    "labeling_count",
                    "evaluation_runs",
                    "training_runs",
                ),
            ),
        },
    }


def build_artifact() -> dict[str, Any]:
    denominator = _denominator()
    strata = _visible_strata()
    ledger = _build_requirement_ledger(strata, denominator)
    identity_freeze = _identity_group_freeze()
    split = _split_assignment(identity_freeze)
    artifact = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "v3c_heldout_extension_solo_custody_receipt",
        "status": "FROZEN_METADATA_ONLY_NO_EXPOSURE",
        "text_free": True,
        "metadata_only": True,
        "outcome_boundary": {
            "parent_outcome_sha256": PARENT_OUTCOME_SHA256,
            "reviewed_v3_consensus_sha256": V3_CONSENSUS_SHA256,
            "v3a_artifact_sha256": V3A_ARTIFACT_SHA256,
            "heldout_membership_present": False,
            "heldout_content_present": False,
            "provider_calls": 0,
            "labeling_count": 0,
            "evaluation_runs": 0,
            "training_runs": 0,
        },
        "bindings": {
            "schema": binding(SCHEMA_PATH),
            "validator": binding(SCRIPT_PATH),
            "v3a_artifact": binding(V3A_ARTIFACT_PATH),
            "v3a_compatibility_matrix": binding(V3A_MATRIX_PATH),
        },
        "denominator": denominator,
        "strata": strata,
        "requirement_ledger": ledger,
        "identity_group_freeze": identity_freeze,
        "split_assignment": split,
        "construction_visibility": _construction_visibility(),
        "solo_operator_custody": _solo_custody(),
        "temporal_firewall": _temporal_firewall(identity_freeze, split),
        "evaluation_policy": _evaluation_policy(strata, ledger),
        "custody_receipts": _custody_receipt_contract(ledger),
        "residual_query": _residual_query(strata),
        "state_machine": _state_machine(),
        "execution_gates": {
            "provider_calls_authorized": False,
            "provider_call_count": 0,
            "labeling_authorized": False,
            "labeling_count": 0,
            "evaluation_authorized": False,
            "evaluation_runs": 0,
            "training_authorized": False,
            "training_runs": 0,
            "heldout_rows_created": 0,
        },
        "stop_policy": {
            "global_stop_codes": list(STOP_CODES),
            "fail_closed": True,
            "safe_disjoint_work_may_continue": True,
            "new_cycle_required_on_invalidation": True,
        },
    }
    return _with_hash(artifact, "receipt_sha256")


def _schema_validate(value: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    Draft202012Validator.check_schema(dict(schema))
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.path))
    if errors:
        location = "/".join(str(item) for item in errors[0].path) or "artifact"
        raise V3CError(f"schema violation at {location}: {errors[0].message}")


def _receipt_identity(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "sequence": value["sequence"],
        "cycle_id": value["cycle_id"],
        "event_type": value["event_type"],
        "cycle_status": value["cycle_status"],
        "construction_mutation_after_exposure": value["construction_mutation_after_exposure"],
        "new_cycle_required": value["new_cycle_required"],
        "freeze_field_count": value["freeze_field_count"],
        "freeze_commitment_sha256": value["freeze_commitment_sha256"],
        "evaluation_version_sha256": value["evaluation_version_sha256"],
    }


def validate_custody_receipts(
    receipts: Sequence[Mapping[str, Any]], artifact: Mapping[str, Any] | None = None
) -> None:
    """Validate an append-only custody stream without inspecting held-out data."""
    artifact = artifact or build_artifact()
    schema = read_json(SCHEMA_PATH)
    receipt_schema = schema["$defs"]["custodyReceipt"]
    ledger_sha = artifact["requirement_ledger"]["ledger_sha256"]
    seen_ids: dict[str, bytes] = {}
    previous_hash: str | None = None
    current_cycle: str | None = None
    current_state: str | None = None
    cycle_ids: set[str] = set()
    sealed_commitment_pairs: set[tuple[str, str]] = set()
    sealed_freeze_commitment: str | None = None
    sealed_evaluation_version: str | None = None
    exposed_version: str | None = None
    for expected_sequence, receipt in enumerate(receipts):
        errors = sorted(Draft202012Validator(receipt_schema).iter_errors(receipt), key=lambda error: list(error.path))
        require(not errors, f"custody receipt schema violation: {errors[0].message}" if errors else "receipt invalid")
        _walk_forbidden(receipt, "custody_receipt")
        encoded = canonical_bytes(receipt)
        receipt_id = str(receipt["receipt_id"])
        if receipt_id in seen_ids:
            require(seen_ids[receipt_id] == encoded, "divergent custody receipt replay")
            raise V3CError("duplicate custody receipt in canonical stream")
        seen_ids[receipt_id] = encoded
        require(receipt["sequence"] == expected_sequence, "custody receipt sequence gap")
        require(receipt["previous_receipt_sha256"] == previous_hash, "custody receipt previous hash mismatch")
        require(receipt["receipt_id"] == sha256_value(_receipt_identity(receipt)), "custody receipt identity drift")
        require(receipt["receipt_sha256"] == receipt_sha(receipt), "custody receipt self-hash mismatch")
        require(receipt["requirement_ledger_sha256"] == ledger_sha, "custody receipt denominator drift")
        event = receipt["event_type"]
        status = receipt["cycle_status"]
        cycle = receipt["cycle_id"]
        mutated = receipt["construction_mutation_after_exposure"]
        if current_cycle is None:
            require(event == "cycle_sealed", "custody stream must begin with cycle seal")
            require(status == "SEALED_PRE_EXPOSURE", "first custody receipt must seal before exposure")
            require(receipt["previous_receipt_sha256"] is None, "first custody receipt has predecessor")
            require(mutated is False and receipt["new_cycle_required"] is False, "initial cycle seal flags invalid")
            require(receipt["freeze_commitment_sha256"] != "0" * 64, "initial freeze commitment missing")
            require(receipt["evaluation_version_sha256"] != "0" * 64, "initial evaluation version missing")
            current_cycle = cycle
            current_state = status
            cycle_ids.add(cycle)
            sealed_freeze_commitment = receipt["freeze_commitment_sha256"]
            sealed_evaluation_version = receipt["evaluation_version_sha256"]
            sealed_commitment_pairs.add((sealed_freeze_commitment, sealed_evaluation_version))
        elif cycle != current_cycle:
            require(current_state == "INVALIDATED_RESEAL_REQUIRED", "new cycle before invalidation")
            require(event == "cycle_sealed" and status == "SEALED_PRE_EXPOSURE", "new cycle must begin sealed")
            require(cycle not in cycle_ids, "invalidated cycle cannot be reused")
            require(mutated is False and receipt["new_cycle_required"] is False, "new cycle seal flags invalid")
            require(receipt["freeze_commitment_sha256"] != "0" * 64, "new cycle freeze commitment missing")
            require(receipt["evaluation_version_sha256"] != "0" * 64, "new cycle evaluation version missing")
            commitment_pair = (
                receipt["freeze_commitment_sha256"],
                receipt["evaluation_version_sha256"],
            )
            require(commitment_pair not in sealed_commitment_pairs, "sealed commitment pair cannot be reused")
            current_cycle = cycle
            current_state = status
            cycle_ids.add(cycle)
            sealed_freeze_commitment = receipt["freeze_commitment_sha256"]
            sealed_evaluation_version = receipt["evaluation_version_sha256"]
            sealed_commitment_pairs.add(commitment_pair)
            exposed_version = None
        elif event == "cycle_sealed":
            raise V3CError("new cycle id required after invalidation")
        elif event == "exposure":
            require(current_state == "SEALED_PRE_EXPOSURE", "exposure before pre-exposure seal")
            require(status == "EXPOSED", "exposure receipt state invalid")
            require(mutated is False and receipt["new_cycle_required"] is False, "exposure flags invalid")
            require(receipt["freeze_commitment_sha256"] == sealed_freeze_commitment, "exposure freeze commitment drift")
            require(receipt["evaluation_version_sha256"] == sealed_evaluation_version, "exposure evaluation version drift")
            require(receipt["freeze_commitment_sha256"] != "0" * 64, "exposure freeze commitment missing")
            current_state = status
            exposed_version = receipt["evaluation_version_sha256"]
        elif event == "invalidation":
            require(current_state == "EXPOSED", "invalidation without prior exposure")
            require(status == "INVALIDATED_RESEAL_REQUIRED", "invalidation receipt state invalid")
            require(mutated is True and receipt["new_cycle_required"] is True, "post-exposure mutation not invalidated")
            require(exposed_version == receipt["evaluation_version_sha256"], "invalidated evaluation version drift")
            require(receipt["freeze_commitment_sha256"] == sealed_freeze_commitment, "invalidated freeze commitment drift")
            current_state = status
        else:
            raise V3CError(f"unsupported custody event: {event}")
        previous_hash = str(receipt["receipt_sha256"])


validate_receipts = validate_custody_receipts


def validate(artifact: Mapping[str, Any], schema: Mapping[str, Any] | None = None) -> None:
    verify_predecessors()
    schema = schema or read_json(SCHEMA_PATH)
    _schema_validate(artifact, schema)
    _walk_forbidden(artifact)
    require(artifact["receipt_sha256"] == receipt_sha(artifact), "artifact receipt hash drift")
    require(artifact["outcome_boundary"] == build_artifact()["outcome_boundary"], "outcome boundary drift")
    require(artifact["denominator"] == _denominator(), "V3-C denominator drift")
    expected_strata = _visible_strata()
    require(artifact["strata"] == expected_strata, "V3-C visible strata drift")
    expected_ledger = _build_requirement_ledger(expected_strata, artifact["denominator"])
    require(artifact["requirement_ledger"] == expected_ledger, "per-stratum requirement ledger drift")
    require(artifact["requirement_ledger"]["ledger_sha256"] == receipt_sha(artifact["requirement_ledger"], "ledger_sha256"), "ledger hash drift")
    require(artifact["requirement_ledger"]["denominator_sha256"] == sha256_value(artifact["denominator"]), "ledger denominator binding drift")
    require(artifact["identity_group_freeze"] == _identity_group_freeze(), "identity-group freeze drift")
    require(artifact["split_assignment"] == _split_assignment(artifact["identity_group_freeze"]), "split algorithm drift")
    require(artifact["construction_visibility"] == _construction_visibility(), "construction visibility drift")
    require(artifact["solo_operator_custody"] == _solo_custody(), "solo custody disclosure drift")
    require(artifact["temporal_firewall"] == _temporal_firewall(artifact["identity_group_freeze"], artifact["split_assignment"]), "temporal firewall drift")
    require(artifact["evaluation_policy"] == _evaluation_policy(expected_strata, expected_ledger), "evaluation policy drift")
    require(artifact["custody_receipts"] == _custody_receipt_contract(expected_ledger), "custody receipt contract drift")
    require(artifact["residual_query"] == _residual_query(expected_strata), "residual query drift")
    require(artifact["state_machine"] == _state_machine(), "state machine drift")
    require(artifact["execution_gates"] == build_artifact()["execution_gates"], "execution gate drift")
    require(artifact["stop_policy"] == build_artifact()["stop_policy"], "stop policy drift")
    bindings = artifact["bindings"]
    require(bindings["schema"] == binding(SCHEMA_PATH), "schema binding drift")
    require(bindings["validator"] == binding(SCRIPT_PATH), "validator binding drift")
    require(bindings["v3a_artifact"] == binding(V3A_ARTIFACT_PATH), "V3-A artifact binding drift")
    require(bindings["v3a_compatibility_matrix"] == binding(V3A_MATRIX_PATH), "V3-A matrix binding drift")
    validate_custody_receipts(artifact["custody_receipts"]["rows"], artifact)
    require(artifact["custody_receipts"]["rows"] == [], "tracked artifact contains custody receipts")
    require(artifact["custody_receipts"]["row_count"] == 0, "tracked artifact receipt count drift")
    require(not any(artifact["execution_gates"].values()), "execution gate enabled")
    require(artifact == build_artifact(), "artifact deterministic content drift")


def write_outputs() -> None:
    SCHEMA_PATH.write_bytes(canonical_bytes(build_schema()))
    ARTIFACT_PATH.write_bytes(canonical_bytes(build_artifact()))


def check_outputs() -> None:
    schema = read_json(SCHEMA_PATH)
    artifact = read_json(ARTIFACT_PATH)
    validate(artifact, schema)
    require(SCHEMA_PATH.read_bytes() == canonical_bytes(build_schema()), "schema byte drift")
    require(ARTIFACT_PATH.read_bytes() == canonical_bytes(build_artifact()), "artifact byte drift")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.write:
            write_outputs()
        check_outputs()
    except (V3CError, KeyError, TypeError) as exc:
        print(f"V3-C held-out custody: FAIL: {exc}", file=sys.stderr)
        return 1
    print("V3-C held-out extension and solo custody: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
