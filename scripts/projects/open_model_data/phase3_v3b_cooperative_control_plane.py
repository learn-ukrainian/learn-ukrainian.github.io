#!/usr/bin/env python3
"""Freeze and verify the metadata-only Phase 3 V3-B control plane."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCHEMA_PATH = DATA / "contracts/phase3_v3b_cooperative_control_plane_v1.schema.json"
ARTIFACT_PATH = DATA / "contracts/phase3_v3b_cooperative_control_plane_v1.json"
SCRIPT_PATH = Path(__file__).resolve()

V3_SCHEMA_PATH = DATA / "contracts/phase3_v3_cooperative_control_plane_v1.schema.json"
V3_ARTIFACT_PATH = DATA / "evidence/phase3_v3_cooperative_control_plane_v1.json"
V3_VALIDATOR_PATH = DATA.parent.parent.parent / "scripts/projects/open_model_data/phase3_v3_cooperative_control_plane.py"
P2_PATH = DATA / "evidence/phase3_p2_canonical_contracts_v1.json"
V3A_SCHEMA_PATH = DATA / "contracts/phase3_v3a_taxonomy_denominator_compatibility_v1.schema.json"
V3A_ARTIFACT_PATH = DATA / "contracts/phase3_v3a_taxonomy_denominator_compatibility_v1.json"
V3A_MATRIX_PATH = DATA / "contracts/phase3_v3a_compatibility_matrix_v1.json"
V3A_VALIDATOR_PATH = DATA.parent.parent.parent / "scripts/projects/open_model_data/freeze_phase3_v3a_taxonomy_denominator_compatibility.py"

V2_OUTCOME_SHA256 = "890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47"
V3_CONSENSUS_SHA256 = "d3444c126deb91d05129d51c5344aa204b1db9ca0927c246698e0389466d0b1a"
EXPECTED_HASHES = {
    V3_SCHEMA_PATH: "d7897f3f4a5899e24f504916d9a63bcb82d3e20968d0be26ba8166f27ba5a852",
    V3_ARTIFACT_PATH: "f7d5da9ede20967f05c4eee22b3bda14ca3b6bc30cd0e4b32f659bd572a7078d",
    V3_VALIDATOR_PATH: "50a6ef3de21ee999325a07478e9c3570f9b7d353a622fc28ab50a3f75e9055b3",
    P2_PATH: "dc8dfdf207728ef386cea14ddb328289b2beee5159afb98bf076e5f117602ea3",
    V3A_SCHEMA_PATH: "b26ece53abafe4a8a2b3dfbf2003824fa48b1649bd8b2c58a3fdab4ab08cb735",
    V3A_ARTIFACT_PATH: "131d4b7286de0a6c079548b9eba21e5eec6804bbdd1dd41817e3ce58444d9a28",
    V3A_MATRIX_PATH: "580a3785aa4af22a910a61c55d789c5d930f6fafaf317054ce070074ecf3ddbd",
    V3A_VALIDATOR_PATH: "9526e76ddc65c4b4876f7fa74b39b185eba855acee8b8b0cd77282a51038853a",
}

HASH_PATTERN = "^[0-9a-f]{64}$"
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

MODEL_ROLES = (
    ("IDENTITY_LEAD", "anthropic", "claude-fable-5", "v3b.identity.opinion"),
    ("INDEPENDENT_DISSENT", "google", "gemini-3.7-flash-high", "v3b.identity.opinion"),
    ("DISPUTE_CRITIC", "xai", "grok-4.6", "v3b.dispute.critique"),
    ("CANDIDATE_BUILDER", "openai", "gpt-5.6-sol", "v3b.case.candidate"),
)

GOLD_GUARD_FIELDS = (
    "identity_resolved_or_explicit_protected_abstention",
    "case_state_permitted",
    "operation_rights_allowed",
    "claim_appropriate_evidence_bound",
    "active_registry_entry_bound",
    "qualification_snapshot_bound",
    "direct_human_inspection_recorded",
    "atomic_decision_key_complete",
    "adjudication_record_self_hash_valid",
)

STATES = (
    "SOURCE_RIGHTS_BLOCKED",
    "SOURCE_RIGHTS_REVIEW_PENDING",
    "SOURCE_ADMITTED",
    "IDENTITY_PENDING",
    "IDENTITY_RETRY_PENDING",
    "IDENTITY_SUBSTITUTE_PENDING",
    "IDENTITY_HUMAN_QUEUE",
    "IDENTITY_RESOLVED",
    "IDENTITY_ABSTAINED_NON_GOLD",
    "MODEL_AGREEMENT_QUARANTINED_NOT_GOLD",
    "DISPUTE_CRITIC_PENDING",
    "CRITIC_RETRY_PENDING",
    "CRITIC_SUBSTITUTE_PENDING",
    "CASE_CANDIDATE_PENDING",
    "CANDIDATE_RETRY_PENDING",
    "CANDIDATE_SUBSTITUTE_PENDING",
    "CASE_HUMAN_QUEUE",
    "HUMAN_QUEUE_OVERFLOW",
    "CASE_EVIDENCE_INSUFFICIENT",
    "CASE_HUMAN_ABSTAINED",
    "CASE_HUMAN_ADJUDICATED",
    "GOLD_ELIGIBLE_METADATA_ONLY",
)

TRANSITIONS = (
    ("SOURCE_RIGHTS_BLOCKED", "SOURCE_RIGHTS_REVIEW_PENDING", "rights_evidence_supplied"),
    ("SOURCE_RIGHTS_REVIEW_PENDING", "SOURCE_RIGHTS_BLOCKED", "rights_still_unresolved"),
    ("SOURCE_RIGHTS_REVIEW_PENDING", "SOURCE_ADMITTED", "operation_rights_verified"),
    ("SOURCE_ADMITTED", "IDENTITY_PENDING", "identity_packet_frozen"),
    ("IDENTITY_PENDING", "MODEL_AGREEMENT_QUARANTINED_NOT_GOLD", "exact_model_agreement"),
    ("IDENTITY_PENDING", "DISPUTE_CRITIC_PENDING", "identity_disagreement"),
    ("IDENTITY_PENDING", "IDENTITY_RETRY_PENDING", "format_failure_retry_available"),
    ("IDENTITY_PENDING", "IDENTITY_SUBSTITUTE_PENDING", "provider_failure_substitute_available"),
    ("IDENTITY_PENDING", "IDENTITY_HUMAN_QUEUE", "model_budget_exhausted"),
    ("IDENTITY_RETRY_PENDING", "IDENTITY_PENDING", "format_retry_dispatched"),
    ("IDENTITY_RETRY_PENDING", "IDENTITY_HUMAN_QUEUE", "format_retry_exhausted"),
    ("IDENTITY_SUBSTITUTE_PENDING", "IDENTITY_PENDING", "family_safe_substitute_dispatched"),
    ("IDENTITY_SUBSTITUTE_PENDING", "IDENTITY_HUMAN_QUEUE", "substitute_exhausted"),
    ("MODEL_AGREEMENT_QUARANTINED_NOT_GOLD", "CASE_HUMAN_QUEUE", "complete_human_review_selected"),
    ("MODEL_AGREEMENT_QUARANTINED_NOT_GOLD", "IDENTITY_HUMAN_QUEUE", "identity_requires_human_review"),
    ("DISPUTE_CRITIC_PENDING", "CASE_HUMAN_QUEUE", "critic_routes_human_review"),
    ("DISPUTE_CRITIC_PENDING", "CRITIC_RETRY_PENDING", "critic_format_retry_available"),
    ("DISPUTE_CRITIC_PENDING", "CRITIC_SUBSTITUTE_PENDING", "critic_substitute_available"),
    ("CRITIC_RETRY_PENDING", "DISPUTE_CRITIC_PENDING", "critic_format_retry_dispatched"),
    ("CRITIC_RETRY_PENDING", "CASE_HUMAN_QUEUE", "critic_retry_exhausted"),
    ("CRITIC_SUBSTITUTE_PENDING", "DISPUTE_CRITIC_PENDING", "critic_substitute_dispatched"),
    ("CRITIC_SUBSTITUTE_PENDING", "CASE_HUMAN_QUEUE", "critic_substitute_exhausted"),
    ("IDENTITY_HUMAN_QUEUE", "IDENTITY_RESOLVED", "human_identity_resolved"),
    ("IDENTITY_HUMAN_QUEUE", "IDENTITY_ABSTAINED_NON_GOLD", "human_identity_abstained"),
    ("IDENTITY_HUMAN_QUEUE", "CASE_EVIDENCE_INSUFFICIENT", "identity_evidence_insufficient"),
    ("IDENTITY_HUMAN_QUEUE", "HUMAN_QUEUE_OVERFLOW", "human_capacity_exhausted"),
    ("IDENTITY_RESOLVED", "CASE_CANDIDATE_PENDING", "resolved_identity_bound"),
    ("IDENTITY_ABSTAINED_NON_GOLD", "CASE_HUMAN_ABSTAINED", "abstention_case_preserved"),
    ("CASE_CANDIDATE_PENDING", "CASE_HUMAN_QUEUE", "candidate_requires_complete_human_review"),
    ("CASE_CANDIDATE_PENDING", "CANDIDATE_RETRY_PENDING", "candidate_format_retry_available"),
    ("CASE_CANDIDATE_PENDING", "CANDIDATE_SUBSTITUTE_PENDING", "candidate_substitute_available"),
    ("CANDIDATE_RETRY_PENDING", "CASE_CANDIDATE_PENDING", "candidate_format_retry_dispatched"),
    ("CANDIDATE_RETRY_PENDING", "CASE_HUMAN_QUEUE", "candidate_retry_exhausted"),
    ("CANDIDATE_SUBSTITUTE_PENDING", "CASE_CANDIDATE_PENDING", "candidate_substitute_dispatched"),
    ("CANDIDATE_SUBSTITUTE_PENDING", "CASE_HUMAN_QUEUE", "candidate_substitute_exhausted"),
    ("CASE_HUMAN_QUEUE", "CASE_HUMAN_ADJUDICATED", "qualified_human_adjudicated"),
    ("CASE_HUMAN_QUEUE", "CASE_HUMAN_ABSTAINED", "qualified_human_abstained"),
    ("CASE_HUMAN_QUEUE", "CASE_EVIDENCE_INSUFFICIENT", "case_evidence_insufficient"),
    ("CASE_HUMAN_QUEUE", "HUMAN_QUEUE_OVERFLOW", "human_capacity_exhausted"),
    ("CASE_HUMAN_ADJUDICATED", "GOLD_ELIGIBLE_METADATA_ONLY", "all_gold_guards_satisfied"),
    ("HUMAN_QUEUE_OVERFLOW", "CASE_HUMAN_QUEUE", "capacity_added_resume"),
    ("CASE_EVIDENCE_INSUFFICIENT", "CASE_HUMAN_QUEUE", "new_evidence_resume"),
    ("CASE_HUMAN_ABSTAINED", "CASE_HUMAN_QUEUE", "reopened_with_new_evidence"),
)


class V3BError(ValueError):
    """The V3-B contract or receipt stream is stale, incomplete, or unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise V3BError(message)


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except OSError as exc:
        raise V3BError(f"cannot hash artifact: {path}") from exc


def logical(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def binding(path: Path) -> dict[str, str]:
    return {"path": logical(path), "sha256": sha256_file(path)}


def read_json(path: Path) -> dict[str, Any]:
    try:
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode) and not path.is_symlink(), f"artifact must be regular: {path}")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise V3BError(f"cannot read JSON artifact: {path}") from exc
    require(isinstance(value, dict), f"JSON artifact must be an object: {path}")
    return value


def receipt_sha(value: Mapping[str, Any], field: str = "receipt_sha256") -> str:
    body = dict(value)
    body.pop(field, None)
    return sha256_bytes(canonical_bytes(body))


def _walk_forbidden(value: Any, path: str = "artifact") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            require(key not in FORBIDDEN_FIELDS, f"forbidden field at {path}/{key}")
            _walk_forbidden(child, f"{path}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden(child, f"{path}/{index}")


def verify_predecessors() -> None:
    for path, expected in EXPECTED_HASHES.items():
        require(sha256_file(path) == expected, f"predecessor byte drift: {logical(path)}")


def _hash_schema() -> dict[str, Any]:
    return {"type": "string", "pattern": HASH_PATTERN}


def _base_output_properties(contract_id: str) -> dict[str, Any]:
    return {
        "schema_version": {"const": "phase3-v3b-role-output-v1"},
        "contract_id": {"const": contract_id},
        "row_id": _hash_schema(),
        "packet_sha256": _hash_schema(),
        "input_sha256": _hash_schema(),
        "parser_state": {"enum": ["valid", "abstained"]},
        "evidence_ref_ids": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 1,
            "uniqueItems": True,
        },
        "abstain": {"type": "boolean"},
    }


def _strict_object(properties: dict[str, Any], required: Sequence[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(required),
        "properties": properties,
    }


def _output_definitions() -> dict[str, Any]:
    common_required = (
        "schema_version",
        "contract_id",
        "row_id",
        "packet_sha256",
        "input_sha256",
        "parser_state",
        "evidence_ref_ids",
        "abstain",
    )
    identity = _base_output_properties("v3b.identity.opinion")
    identity["decision"] = _strict_object(
        {
            "span_offsets": {
                "type": "array",
                "prefixItems": [{"type": "integer", "minimum": 0}, {"type": "integer", "minimum": 0}],
                "minItems": 2,
                "maxItems": 2,
            },
            "language_identity": {
                "enum": [
                    "ukrainian",
                    "russian",
                    "belarusian",
                    "bulgarian",
                    "macedonian",
                    "serbian",
                    "montenegrin_cyrillic",
                    "rusyn",
                    "church_slavonic",
                    "old_east_slavic",
                    "mixed_or_unresolved",
                    "non_slavic",
                    "unknown",
                ]
            },
            "identity_candidates": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
                "minItems": 1,
                "uniqueItems": True,
            },
            "diachronic_status": {"enum": ["modern", "archaic_bookish_modern", "historical_stage", "undetermined"]},
            "variety_status": {"enum": ["standard", "dialectal", "regional", "source_attested_identity", "literary_eye_dialect", "unspecified"]},
            "variety_id": {"type": "string", "minLength": 1},
            "period_id": {"type": "string", "minLength": 1},
            "region_id": {"type": "string", "minLength": 1},
            "register_id": {"type": "string", "minLength": 1},
            "contact_composition": {"enum": ["none", "surzhyk_contact_mixing", "quotation", "transliteration", "unresolved_contact"]},
            "context_role": {"enum": ["production", "correction", "protected_context", "quotation", "metalinguistic", "named_entity", "unresolved"]},
            "recension_editorial_layer_id": {"type": "string", "minLength": 1},
            "primary_case_state": {"type": "string", "minLength": 1},
            "modern_correction_eligible": {"type": "boolean"},
            "protection_flags": {"type": "array", "items": {"type": "string"}, "uniqueItems": True},
            "confidence_or_abstention_state": {"enum": ["high", "medium", "low", "abstain"]},
        },
        (
            "span_offsets",
            "language_identity",
            "identity_candidates",
            "diachronic_status",
            "variety_status",
            "variety_id",
            "period_id",
            "region_id",
            "register_id",
            "contact_composition",
            "context_role",
            "recension_editorial_layer_id",
            "primary_case_state",
            "modern_correction_eligible",
            "protection_flags",
            "confidence_or_abstention_state",
        ),
    )
    critic = _base_output_properties("v3b.dispute.critique")
    critic.update(
        {
            "disagreement_sha256": _hash_schema(),
            "recommendation": {"enum": ["human_review", "evidence_insufficient", "abstain"]},
        }
    )
    candidate = _base_output_properties("v3b.case.candidate")
    candidate.update(
        {
            "identity_join_sha256": _hash_schema(),
            "proposed_case_state": {
                "enum": [
                    "correct_modern_production",
                    "source_backed_correction",
                    "minimal_contrast",
                    "protected_historical_context",
                    "protected_dialect_or_regional_context",
                    "abstention",
                ]
            },
            "proposal_sha256": _hash_schema(),
        }
    )
    return {
        "identity_output": _strict_object(identity, (*common_required, "decision")),
        "critic_output": _strict_object(
            critic, (*common_required, "disagreement_sha256", "recommendation")
        ),
        "candidate_output": _strict_object(
            candidate, (*common_required, "identity_join_sha256", "proposed_case_state", "proposal_sha256")
        ),
    }


def build_schema() -> dict[str, Any]:
    definitions = _output_definitions()
    definitions["transition_receipt"] = _strict_object(
        {
            "schema_version": {"const": "phase3-v3b-transition-receipt-v1"},
            "receipt_id": _hash_schema(),
            "row_id": _hash_schema(),
            "denominator_sha256": _hash_schema(),
            "contract_sha256": _hash_schema(),
            "sequence": {"type": "integer", "minimum": 0},
            "from_state": {"enum": list(STATES)},
            "to_state": {"enum": list(STATES)},
            "condition_code": {"type": "string", "minLength": 1},
            "role_id": {
                "enum": [
                    "SOURCE_ADMISSION",
                    "IDENTITY_LEAD",
                    "INDEPENDENT_DISSENT",
                    "DISPUTE_CRITIC",
                    "CANDIDATE_BUILDER",
                    "HUMAN_STEWARD",
                ]
            },
            "attempt_count": {"type": "integer", "minimum": 0, "maximum": 3},
            "format_retry_used": {"type": "boolean"},
            "substitute_used": {"type": "boolean"},
            "resolved_route": _strict_object(
                {
                    "provider_family": {"type": "string", "minLength": 1},
                    "model": {"type": "string", "minLength": 1},
                    "harness": {"type": "string", "minLength": 1},
                    "effort": {"type": "string", "minLength": 1},
                },
                ("provider_family", "model", "harness", "effort"),
            ),
            "input_sha256": _hash_schema(),
            "prompt_sha256": _hash_schema(),
            "output_sha256": _hash_schema(),
            "parser_result": {"enum": ["valid", "format_failure", "provider_failure", "not_applicable"]},
            "failure_code": {"type": ["string", "null"]},
            "guard_bundle_sha256": _hash_schema(),
            "guard_result": {"enum": ["pass", "not_applicable"]},
            "gold_guard_results": _strict_object(
                {field: {"type": "boolean"} for field in GOLD_GUARD_FIELDS},
                GOLD_GUARD_FIELDS,
            ),
            "previous_receipt_sha256": {"anyOf": [_hash_schema(), {"type": "null"}]},
            "receipt_sha256": _hash_schema(),
        },
        (
            "schema_version",
            "receipt_id",
            "row_id",
            "denominator_sha256",
            "contract_sha256",
            "sequence",
            "from_state",
            "to_state",
            "condition_code",
            "role_id",
            "attempt_count",
            "format_retry_used",
            "substitute_used",
            "resolved_route",
            "input_sha256",
            "prompt_sha256",
            "output_sha256",
            "parser_result",
            "failure_code",
            "guard_bundle_sha256",
            "guard_result",
            "gold_guard_results",
            "previous_receipt_sha256",
            "receipt_sha256",
        ),
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://learn-ukrainian.github.io/contracts/phase3_v3b_cooperative_control_plane_v1.schema.json",
        "title": "Phase 3 V3-B cooperative control plane",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "status",
            "text_free",
            "metadata_only",
            "bindings",
            "outcome_boundary",
            "denominator",
            "incidence_manifest",
            "role_contracts",
            "blindness_and_conflicts",
            "output_contracts",
            "retry_and_substitution",
            "single_human_registry",
            "human_work_manifest",
            "state_machine",
            "gold_guard",
            "transition_receipt_contract",
            "residual_policy",
            "execution_gates",
            "receipt_sha256",
        ],
        "properties": {
            "schema_version": {"const": "phase3-v3b-cooperative-control-plane-v1"},
            "status": {"const": "FROZEN_METADATA_ONLY_NO_EXECUTION"},
            "text_free": {"const": True},
            "metadata_only": {"const": True},
            "bindings": {"type": "object", "additionalProperties": {"type": "object"}},
            "outcome_boundary": {"type": "object"},
            "denominator": {"type": "object"},
            "incidence_manifest": {"type": "object"},
            "role_contracts": {"type": "array", "minItems": 5, "uniqueItems": True},
            "blindness_and_conflicts": {"type": "object"},
            "output_contracts": {"type": "object"},
            "retry_and_substitution": {"type": "object"},
            "single_human_registry": {"type": "object"},
            "human_work_manifest": {"type": "object"},
            "state_machine": {"type": "object"},
            "gold_guard": {"type": "object"},
            "transition_receipt_contract": {"type": "object"},
            "residual_policy": {"type": "object"},
            "execution_gates": {"type": "object"},
            "receipt_sha256": _hash_schema(),
        },
        "$defs": definitions,
    }


def _denominator(v3a: Mapping[str, Any]) -> dict[str, Any]:
    expected = {
        "source_units": 57,
        "visible_cells": 19,
        "active_coverage_target_cells": 16,
        "active_coverage_blocked_cells": 16,
        "not_applicable_cells": 2,
        "lineage_only_parent_cells": 1,
        "rights_operation_cells": 399,
        "rule_slots_R": 0,
    }
    source = v3a["denominator"]
    actual = {key: source[key] for key in expected if key != "rights_operation_cells"}
    actual["rights_operation_cells"] = v3a["rights_capabilities"]["operation_cell_count"]
    require(actual == expected, "V3-A denominator drift")
    return expected


def _incidence_manifest() -> dict[str, Any]:
    body = {
        "implicit_cartesian_product": False,
        "row_contract": {
            "required_fields": [
                "row_id",
                "source_unit_id",
                "coverage_stratum_id",
                "current_state",
                "residual_owner",
            ],
            "row_id_rule": "sha256_canonical_row_metadata_without_row_id",
            "all_rows_visible_in_state_query": True,
            "all_rows_visible_in_residual_query": True,
        },
        "source_cell_row_count": 0,
        "rows": [],
        "state_query_row_count": 0,
        "residual_query_row_count": 0,
        "current_state": "EMPTY_NO_OPERATION_RIGHTS_AND_R0",
    }
    body["denominator_sha256"] = sha256_bytes(canonical_bytes(body))
    return body


def _registry() -> dict[str, Any]:
    entry = {
        "entry_id": "solo_operator_v1",
        "actor_kind": "human",
        "status": "active",
        "authority_kind": "source_qualified_human_adjudication",
        "qualification_basis": "decision_bound_to_claim_appropriate_frozen_source_evidence",
        "qualification_scope": [
            "language_identity",
            "diachronic_status",
            "variety_status",
            "contact_composition",
            "context_role",
            "case_state",
        ],
        "credential_claimed": False,
        "institutional_independence_claimed": False,
        "may_author_gold_only_after_all_guards": True,
        "may_access_heldout_during_construction": False,
        "provider_identity": False,
    }
    entry["qualification_snapshot_sha256"] = sha256_bytes(canonical_bytes(entry))
    registry = {
        "registry_id": "phase3_v3b_single_human_registry_v1",
        "predecessor_registry_status": "FROZEN_NONADMITTING",
        "entry_count": 1,
        "entries": [entry],
        "registration_does_not_authorize_execution": True,
    }
    registry["registry_sha256"] = sha256_bytes(canonical_bytes(registry))
    return registry


def build_artifact() -> dict[str, Any]:
    v3a = read_json(V3A_ARTIFACT_PATH)
    denominator = _denominator(v3a)
    incidence = _incidence_manifest()
    roles = [
        {
            "role_id": role,
            "provider_family": family,
            "model": model,
            "output_contract_id": contract,
            "heldout_access": "forbidden",
            "may_author_gold": False,
        }
        for role, family, model, contract in MODEL_ROLES
    ]
    roles.append(
        {
            "role_id": "HUMAN_STEWARD",
            "provider_family": "operator",
            "model": "human_operator",
            "output_contract_id": "v3b.human.adjudication",
            "heldout_access": "forbidden",
            "may_author_gold": True,
        }
    )
    artifact: dict[str, Any] = {
        "schema_version": "phase3-v3b-cooperative-control-plane-v1",
        "status": "FROZEN_METADATA_ONLY_NO_EXECUTION",
        "text_free": True,
        "metadata_only": True,
        "bindings": {
            "schema": binding(SCHEMA_PATH),
            "validator": binding(SCRIPT_PATH),
            "v3_foundation_schema": binding(V3_SCHEMA_PATH),
            "v3_foundation_artifact": binding(V3_ARTIFACT_PATH),
            "v3_foundation_validator": binding(V3_VALIDATOR_PATH),
            "p2_canonical_contracts": binding(P2_PATH),
            "v3a_schema": binding(V3A_SCHEMA_PATH),
            "v3a_artifact": binding(V3A_ARTIFACT_PATH),
            "v3a_compatibility_matrix": binding(V3A_MATRIX_PATH),
            "v3a_validator": binding(V3A_VALIDATOR_PATH),
        },
        "outcome_boundary": {
            "v2_outcome_sha256": V2_OUTCOME_SHA256,
            "reviewed_v3_consensus_sha256": V3_CONSENSUS_SHA256,
            "p4_v1_immutable": True,
            "dataset_rows_created": 0,
        },
        "denominator": denominator,
        "incidence_manifest": incidence,
        "role_contracts": roles,
        "blindness_and_conflicts": {
            "identity_packet_canonical_hash_identical": True,
            "identity_outputs_isolated_from_each_other": True,
            "builder_receives_identity_opinions": False,
            "packet_forbidden_metadata": ["model", "model_order", "model_prestige", "provider_family", "role_id"],
            "all_model_role_provider_families_distinct": True,
            "model_may_vote_on_own_output": False,
            "substitution_requires_new_provider_family": True,
        },
        "output_contracts": {
            "v3b.identity.opinion": {"schema_ref": "#/$defs/identity_output", "gold_credit": False},
            "v3b.dispute.critique": {"schema_ref": "#/$defs/critic_output", "gold_credit": False},
            "v3b.case.candidate": {"schema_ref": "#/$defs/candidate_output", "gold_credit": False},
            "v3b.human.adjudication": {
                "schema_ref": "procedural_validator:validate_human_adjudication",
                "requires_registry_binding": True,
            },
            "v3b.transition.receipt": {"schema_ref": "#/$defs/transition_receipt", "append_only": True},
        },
        "retry_and_substitution": {
            "original_attempts": 1,
            "format_retry_limit": 1,
            "independent_family_substitute_limit": 1,
            "maximum_attempts_per_role_per_row": 3,
            "after_exhaustion": "route_human_queue_or_explicit_residual",
            "cumulative_attempt_ledger_required": True,
        },
        "single_human_registry": _registry(),
        "human_work_manifest": {
            "population_denominator_sha256": incidence["denominator_sha256"],
            "current_population_count": 0,
            "current_sample_count": 0,
            "sampling_mode": "complete_review",
            "sample_count_rule": "equals_explicit_admitted_population_count",
            "sample_seed_sha256": V3_CONSENSUS_SHA256,
            "minimum_per_nonempty_stratum": 1,
            "protected_high_risk_review_fraction": 1.0,
            "all_admitted_rows_review_fraction": 1.0,
            "maximum_human_decisions": 64,
            "maximum_steward_minutes": 1920,
            "queue_order": "coverage_stratum_id_then_source_unit_id_then_row_id",
            "queue_overflow_state": "HUMAN_QUEUE_OVERFLOW",
            "promotion_requires_direct_inspection": True,
            "unsampled_promotion_allowed": False,
            "audit_error_threshold": 0.0,
            "failed_cohort_action": "freeze_and_complete_human_review_or_unresolved",
        },
        "state_machine": {
            "states": list(STATES),
            "transitions": [
                {"from_state": source, "to_state": target, "condition_code": condition}
                for source, target, condition in TRANSITIONS
            ],
            "terminal_states": ["GOLD_ELIGIBLE_METADATA_ONLY"],
            "resumable_states": [
                "SOURCE_RIGHTS_BLOCKED",
                "IDENTITY_ABSTAINED_NON_GOLD",
                "MODEL_AGREEMENT_QUARANTINED_NOT_GOLD",
                "HUMAN_QUEUE_OVERFLOW",
                "CASE_EVIDENCE_INSUFFICIENT",
                "CASE_HUMAN_ABSTAINED",
            ],
            "no_dead_end_invariant": True,
            "training_state_present": False,
        },
        "gold_guard": {
            "required_true": list(GOLD_GUARD_FIELDS),
            "identity_abstention_is_gold": False,
            "model_agreement_is_gold": False,
            "model_agreement_coverage_credit": False,
            "training_transition_present": False,
        },
        "transition_receipt_contract": {
            "schema_ref": "#/$defs/transition_receipt",
            "receipt_id_rule": "sha256_canonical_row_sequence_transition_identity",
            "append_only": True,
            "contiguous_sequence_required": True,
            "previous_hash_chain_required": True,
            "from_state_must_match_predecessor_to_state": True,
            "gold_transition_requires_guard_bundle_pass": True,
            "substitution_family_change_verified": True,
            "byte_identical_replay_only": True,
            "divergent_replay_rejected": True,
            "update_or_delete_permitted": False,
        },
        "residual_policy": {
            "preserve_full_denominator": True,
            "safe_disjoint_rows_may_continue": True,
            "explicit_residual_owner": "solo_operator_v1",
            "stop_codes": [
                "MISSING_OPERATION_RIGHTS",
                "MALFORMED_OUTPUT_BUDGET_EXHAUSTED",
                "PROVIDER_UNAVAILABLE",
                "UNRESOLVED_EVIDENCE",
                "ROLE_VISIBILITY_COLLISION",
                "HUMAN_QUEUE_OVERFLOW",
            ],
        },
        "execution_gates": {
            "provider_calls_authorized": False,
            "provider_call_count": 0,
            "labeling_authorized": False,
            "labeling_count": 0,
            "provider_derived_training_labels": 0,
            "gold_rows_admitted": 0,
            "training_authorized": False,
            "training_runs": 0,
            "evaluation_authorized": False,
            "teaching_view_authorized": False,
            "p4_v2_authorized": False,
        },
    }
    artifact["receipt_sha256"] = receipt_sha(artifact)
    return artifact


def _schema_for_ref(schema: Mapping[str, Any], ref: str) -> dict[str, Any]:
    name = ref.rsplit("/", 1)[-1]
    value = schema["$defs"][name]
    require(isinstance(value, dict), f"invalid schema reference: {ref}")
    return value


def validate_output(contract_id: str, payload: Mapping[str, Any], schema: Mapping[str, Any] | None = None) -> None:
    schema = schema or read_json(SCHEMA_PATH)
    artifact = build_artifact()
    require(contract_id in artifact["output_contracts"], "unknown output contract")
    ref = artifact["output_contracts"][contract_id]["schema_ref"]
    require(ref.startswith("#/$defs/"), "output contract requires procedural validator")
    errors = sorted(Draft202012Validator(_schema_for_ref(schema, ref)).iter_errors(payload), key=lambda item: list(item.path))
    require(not errors, f"output schema violation: {errors[0].message}" if errors else "output schema violation")
    _walk_forbidden(payload, "output")
    if contract_id == "v3b.transition.receipt":
        return
    require((payload["parser_state"] == "abstained") is bool(payload["abstain"]), "output abstention mismatch")
    if contract_id == "v3b.identity.opinion":
        confidence = payload["decision"]["confidence_or_abstention_state"]
        require((confidence == "abstain") is bool(payload["abstain"]), "identity abstention mismatch")


def validate_identity_pair(
    lead: Mapping[str, Any], dissent: Mapping[str, Any], lead_family: str, dissent_family: str
) -> None:
    validate_output("v3b.identity.opinion", lead)
    validate_output("v3b.identity.opinion", dissent)
    require(lead["packet_sha256"] == dissent["packet_sha256"], "identity packet hash mismatch")
    require(lead["row_id"] == dissent["row_id"], "identity row mismatch")
    require(lead_family != dissent_family, "identity family conflict")


def _atomic_key_fields() -> tuple[str, ...]:
    return (
        "source_unit_id",
        "source_revision",
        "span_offsets",
        "span_sha256",
        "coverage_stratum_id",
        "decision_layer",
        "claim_type",
        "source_class",
        "identity_candidate",
        "proposed_value_sha256",
        "evidence_set_sha256",
        "registry_sha256",
    )


def validate_human_adjudication(value: Mapping[str, Any], artifact: Mapping[str, Any] | None = None) -> None:
    artifact = artifact or build_artifact()
    expected_keys = {
        "schema_version",
        "row_id",
        "registry_sha256",
        "entry_id",
        "qualification_snapshot_sha256",
        "atomic_decision_key",
        "decision_state",
        "evidence_ref_ids",
        "directly_inspected",
        "adjudication_record_sha256",
    }
    require(set(value) == expected_keys, "human adjudication field set drift")
    require(value["schema_version"] == "phase3-v3b-human-adjudication-v1", "human adjudication version drift")
    require(isinstance(value["row_id"], str) and len(value["row_id"]) == 64, "human row identity invalid")
    evidence_refs = value["evidence_ref_ids"]
    require(
        isinstance(evidence_refs, list)
        and evidence_refs
        and len(evidence_refs) == len(set(evidence_refs))
        and all(isinstance(ref, str) and ref for ref in evidence_refs),
        "human evidence references invalid",
    )
    registry = artifact["single_human_registry"]
    entry = registry["entries"][0]
    require(value["registry_sha256"] == registry["registry_sha256"], "registry binding mismatch")
    require(value["entry_id"] == entry["entry_id"], "unregistered human adjudicator")
    require(
        value["qualification_snapshot_sha256"] == entry["qualification_snapshot_sha256"],
        "qualification snapshot mismatch",
    )
    key = value["atomic_decision_key"]
    require(isinstance(key, Mapping) and set(key) == set(_atomic_key_fields()), "atomic decision key incomplete")
    require(
        isinstance(key["source_unit_id"], str) and key["source_unit_id"],
        "atomic source-unit identity invalid",
    )
    require(isinstance(key["source_revision"], str) and key["source_revision"], "atomic source revision invalid")
    offsets = key["span_offsets"]
    require(
        isinstance(offsets, list)
        and len(offsets) == 2
        and all(isinstance(offset, int) and offset >= 0 for offset in offsets)
        and offsets[0] <= offsets[1],
        "atomic span offsets invalid",
    )
    require(key["decision_layer"] in {"identity", "case"}, "atomic decision layer invalid")
    require(key["claim_type"] in entry["qualification_scope"], "adjudicator qualification out of scope")
    for field in ("span_sha256", "proposed_value_sha256", "evidence_set_sha256", "registry_sha256"):
        candidate = key[field]
        require(isinstance(candidate, str) and len(candidate) == 64, f"atomic hash invalid: {field}")
    require(key["registry_sha256"] == registry["registry_sha256"], "atomic registry binding mismatch")
    require(value["directly_inspected"] is True, "promotion requires direct human inspection")
    require(value["decision_state"] in {"adjudicated", "abstained", "evidence_insufficient"}, "decision state invalid")
    require(value["adjudication_record_sha256"] == receipt_sha(value, "adjudication_record_sha256"), "adjudication self-hash mismatch")
    _walk_forbidden(value, "human_adjudication")


def validate_transition_receipts(
    receipts: Sequence[Mapping[str, Any]], artifact: Mapping[str, Any] | None = None
) -> None:
    artifact = artifact or build_artifact()
    schema = read_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema["$defs"]["transition_receipt"])
    transitions = {
        (item["from_state"], item["to_state"], item["condition_code"])
        for item in artifact["state_machine"]["transitions"]
    }
    seen_ids: dict[str, bytes] = {}
    previous_hash: str | None = None
    previous_to: str | None = None
    expected_sequence = 0
    budgets: dict[tuple[str, str], dict[str, Any]] = {}
    model_role_ids = {role for role, _family, _model, _contract in MODEL_ROLES}
    retry_dispatch_conditions = {
        "format_retry_dispatched",
        "critic_format_retry_dispatched",
        "candidate_format_retry_dispatched",
    }
    substitute_dispatch_conditions = {
        "family_safe_substitute_dispatched",
        "critic_substitute_dispatched",
        "candidate_substitute_dispatched",
    }
    retry_limits = artifact["retry_and_substitution"]
    for item in receipts:
        errors = sorted(validator.iter_errors(item), key=lambda error: list(error.path))
        require(not errors, f"transition receipt schema violation: {errors[0].message}" if errors else "receipt invalid")
        encoded = canonical_bytes(item)
        receipt_id = str(item["receipt_id"])
        if receipt_id in seen_ids:
            require(seen_ids[receipt_id] == encoded, "divergent transition receipt replay")
            continue
        seen_ids[receipt_id] = encoded
        require(item["sequence"] == expected_sequence, "transition receipt sequence gap")
        expected_sequence += 1
        require(item["previous_receipt_sha256"] == previous_hash, "transition receipt previous hash mismatch")
        if previous_to is not None:
            require(item["from_state"] == previous_to, "transition receipt from-state mismatch")
        edge = (item["from_state"], item["to_state"], item["condition_code"])
        require(edge in transitions, "transition receipt edge not allowed")
        identity = {
            "row_id": item["row_id"],
            "sequence": item["sequence"],
            "from_state": item["from_state"],
            "to_state": item["to_state"],
            "condition_code": item["condition_code"],
        }
        require(item["receipt_id"] == sha256_bytes(canonical_bytes(identity)), "transition receipt identity drift")
        require(item["denominator_sha256"] == artifact["incidence_manifest"]["denominator_sha256"], "receipt denominator drift")
        require(item["contract_sha256"] == artifact["receipt_sha256"], "receipt contract drift")
        role_id = str(item["role_id"])
        family = str(item["resolved_route"]["provider_family"])
        if role_id in model_role_ids:
            key = (str(item["row_id"]), role_id)
            existed = key in budgets
            budget = budgets.setdefault(
                key,
                {
                    "format_retries": 0,
                    "substitutes": 0,
                    "original_family": family,
                },
            )
            condition = str(item["condition_code"])
            if condition in retry_dispatch_conditions:
                require(existed, "format retry lacks original attempt")
                budget["format_retries"] += 1
            if condition in substitute_dispatch_conditions:
                require(existed, "substitute lacks original attempt")
                budget["substitutes"] += 1
                require(item["substitute_used"] is True, "substitute transition missing flag")
                require(budget["original_family"] != family, "same-family substitution")
            require(
                budget["format_retries"] <= retry_limits["format_retry_limit"],
                "format retry budget exhausted",
            )
            require(
                budget["substitutes"] <= retry_limits["independent_family_substitute_limit"],
                "substitution budget exhausted",
            )
            expected_attempts = 1 + budget["format_retries"] + budget["substitutes"]
            require(item["attempt_count"] == expected_attempts, "cumulative attempt count mismatch")
            require(
                expected_attempts <= retry_limits["maximum_attempts_per_role_per_row"],
                "maximum attempt budget exhausted",
            )
        if item["to_state"] == "GOLD_ELIGIBLE_METADATA_ONLY":
            require(item["guard_result"] == "pass", "gold transition guard not satisfied")
            require(all(item["gold_guard_results"].values()), "gold transition guard bundle incomplete")
        require(item["receipt_sha256"] == receipt_sha(item), "transition receipt self-hash mismatch")
        previous_hash = item["receipt_sha256"]
        previous_to = str(item["to_state"])


def validate(artifact: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(artifact), key=lambda item: list(item.path))
    require(not errors, f"schema violation: {errors[0].message}" if errors else "schema violation")
    _walk_forbidden(artifact)
    require(artifact["receipt_sha256"] == receipt_sha(artifact), "artifact receipt mismatch")
    v3a = read_json(V3A_ARTIFACT_PATH)
    require(artifact["denominator"] == _denominator(v3a), "denominator drift")
    incidence = artifact["incidence_manifest"]
    require(incidence["implicit_cartesian_product"] is False, "implicit Cartesian product forbidden")
    require(incidence["source_cell_row_count"] == len(incidence["rows"]), "incidence row count mismatch")
    require(incidence["state_query_row_count"] == len(incidence["rows"]), "state query lost incidence row")
    require(incidence["residual_query_row_count"] == len(incidence["rows"]), "residual query lost incidence row")
    require(len({row.get("row_id") for row in incidence["rows"]}) == len(incidence["rows"]), "duplicate incidence row")
    required_row_fields = set(incidence["row_contract"]["required_fields"])
    for row in incidence["rows"]:
        require(set(row) == required_row_fields, "incidence row field set drift")
        row_body = dict(row)
        row_id = row_body.pop("row_id")
        require(row_id == sha256_bytes(canonical_bytes(row_body)), "incidence row identity drift")
    incidence_body = dict(incidence)
    denominator_sha = incidence_body.pop("denominator_sha256")
    require(denominator_sha == sha256_bytes(canonical_bytes(incidence_body)), "incidence denominator hash mismatch")
    roles = artifact["role_contracts"]
    families = [role["provider_family"] for role in roles if role["role_id"] != "HUMAN_STEWARD"]
    require(len(families) == len(set(families)) == 4, "model family conflict")
    registry = artifact["single_human_registry"]
    registry_body = dict(registry)
    registry_hash = registry_body.pop("registry_sha256")
    require(registry_hash == sha256_bytes(canonical_bytes(registry_body)), "registry hash mismatch")
    require(registry["entry_count"] == len(registry["entries"]) == 1, "single-human registry drift")
    entry = registry["entries"][0]
    entry_body = dict(entry)
    qualification_hash = entry_body.pop("qualification_snapshot_sha256")
    require(qualification_hash == sha256_bytes(canonical_bytes(entry_body)), "qualification snapshot mismatch")
    require(entry["credential_claimed"] is False, "fabricated credential claim")
    require(entry["institutional_independence_claimed"] is False, "fabricated independence claim")
    work = artifact["human_work_manifest"]
    require(work["current_population_count"] == incidence["source_cell_row_count"], "human population drift")
    require(work["current_sample_count"] == work["current_population_count"], "complete human review count drift")
    require(work["all_admitted_rows_review_fraction"] == 1.0, "incomplete human review")
    require(work["protected_high_risk_review_fraction"] == 1.0, "protected review weakened")
    require(work["unsampled_promotion_allowed"] is False, "unsampled promotion enabled")
    machine = artifact["state_machine"]
    require(set(machine["states"]) == set(STATES), "state set drift")
    edges = {(row["from_state"], row["to_state"], row["condition_code"]) for row in machine["transitions"]}
    require(edges == set(TRANSITIONS), "transition set drift")
    outgoing = Counter(row["from_state"] for row in machine["transitions"])
    for state in machine["states"]:
        require(state in machine["terminal_states"] or outgoing[state] > 0, f"dead-end state: {state}")
    require(
        ("MODEL_AGREEMENT_QUARANTINED_NOT_GOLD", "CASE_HUMAN_QUEUE", "complete_human_review_selected") in edges,
        "quarantine lacks human path",
    )
    require(not any(source == "MODEL_AGREEMENT_QUARANTINED_NOT_GOLD" and target.startswith("GOLD") for source, target, _ in edges), "quarantine direct gold path")
    require(not any(source == "IDENTITY_ABSTAINED_NON_GOLD" and target == "CASE_CANDIDATE_PENDING" for source, target, _ in edges), "identity abstention reaches candidate")
    require(all("TRAINING" not in state for state in machine["states"]), "training state present")
    gates = artifact["execution_gates"]
    require(not any(gates.values()), "execution gate enabled")
    retry = artifact["retry_and_substitution"]
    require(retry["maximum_attempts_per_role_per_row"] == 3, "attempt budget drift")
    require(retry["format_retry_limit"] == retry["independent_family_substitute_limit"] == 1, "retry budget drift")
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
        verify_predecessors()
        if args.write:
            write_outputs()
        check_outputs()
    except (V3BError, KeyError, TypeError) as exc:
        print(f"V3-B control plane: FAIL: {exc}", file=sys.stderr)
        return 1
    print("V3-B cooperative control plane: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
