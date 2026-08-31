#!/usr/bin/env python3
"""Validate the additive Phase 3 V3 cooperative control-plane contract.

The V3 artifact is intentionally a *contract*, not a dataset receipt.  This
validator checks the exact predecessor bindings, strict metadata schema,
role/visibility boundary, state-machine reachability, rights capabilities,
held-out firewall, and V2 cell dispositions.  It never reads source bodies,
held-out membership, labels, or provider output, and it cannot create a
candidate, gold row, or training view.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCHEMA_PATH = DATA / "contracts/phase3_v3_cooperative_control_plane_v1.schema.json"
ARTIFACT_PATH = DATA / "evidence/phase3_v3_cooperative_control_plane_v1.json"
SCRIPT_PATH = Path(__file__).resolve()
SCHEMA_LOGICAL_PATH = "data/projects/open_model_data/contracts/phase3_v3_cooperative_control_plane_v1.schema.json"
SCRIPT_LOGICAL_PATH = "scripts/projects/open_model_data/phase3_v3_cooperative_control_plane.py"
ARTIFACT_LOGICAL_PATH = "data/projects/open_model_data/evidence/phase3_v3_cooperative_control_plane_v1.json"

V2_PARENT_OUTCOME_SHA256 = "890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47"
REVIEWED_V3_CONSENSUS_SHA256 = "d3444c126deb91d05129d51c5344aa204b1db9ca0927c246698e0389466d0b1a"
V2_COMPATIBILITY_SHA256 = "9f3113776f899759dc9d4bdde9cde8e3fd5c85f5b3e6e748bf0ac79fac28a29c"
P2_CANONICAL_CONTRACTS_SHA256 = "dc8dfdf207728ef386cea14ddb328289b2beee5159afb98bf076e5f117602ea3"
P1_DIALECT_AMENDMENT_SHA256 = "5a4b259f764a3d41499f0a989c02fed921c18b62c9831d361d18d19dcc948afa"
P4_SCHEMA_SHA256 = "0af9e421a0a734718ff884a2b08286533c8f6f6af24c1be4b9023044719f1e8f"
P4_ADMISSION_FILE_SHA256 = "d12ed8d0827263cf5c31f049c518cf90befb4fdf4ca5cb5b413d51b17a1ec4dd"
P4_ADMISSION_RECEIPT_SHA256 = "9d070d83ab9978d71c0f09249adca4738beb3395215fc603c33e8aeae61e8881"

P4_SCHEMA_LOGICAL_PATH = "data/projects/open_model_data/contracts/phase3_p4_pilot_construction_v1.schema.json"
P4_ADMISSION_LOGICAL_PATH = "data/projects/open_model_data/admission/phase3_p4_pilot_construction_v1.json"
V2_COMPATIBILITY_LOGICAL_PATH = "data/projects/open_model_data/evidence/phase3_v2_compatibility_matrix_v1.json"
P2_LOGICAL_PATH = "data/projects/open_model_data/evidence/phase3_p2_canonical_contracts_v1.json"
P1_DIALECT_LOGICAL_PATH = "data/projects/open_model_data/evidence/phase3_p1_dialect_regional_protection_amendment_v1.json"

V2_CELL_IDS = (
    "boundary.latin_script_slavic.ambiguous_noisy.scope_boundary.not_applicable",
    "boundary.mixed_identity.ambiguous_noisy.scope_boundary.abstention",
    "boundary.non_slavic_cyrillic.ambiguous_noisy.scope_boundary.not_applicable",
    "boundary.other_or_unresolved_slavic_cyrillic.ambiguous_noisy.scope_boundary.abstention",
    "boundary.unknown.ambiguous_noisy.scope_boundary.abstention",
    "historical.church_slavonic_recension.historical_text.historical_identity.protected_historical",
    "historical.middle_ukrainian.historical_text.historical_identity.protected_historical",
    "historical.old_east_slavic_kyivan_rus.historical_text.historical_identity.protected_historical",
    "historical.source_attested_rusyn.historical_text.historical_identity.protected_historical",
    "modern.belarusian.unmarked.contact_interference.source_backed_correction",
    "modern.bulgarian.unmarked.contact_interference.source_backed_correction",
    "modern.macedonian.unmarked.contact_interference.source_backed_correction",
    "modern.montenegrin_cyrillic.unmarked.contact_interference.source_backed_correction",
    "modern.russian.unmarked.contact_interference.source_backed_correction",
    "modern.serbian_cyrillic.unmarked.contact_interference.source_backed_correction",
    "protection.source_attested_ukrainian_dialect_or_regional_form.dialect_or_regional_form.protected_dialect_or_regional",
)
V2_CELL_STATUS = {
    V2_CELL_IDS[0]: "not_applicable_with_evidence",
    V2_CELL_IDS[1]: "coverage_blocked",
    V2_CELL_IDS[2]: "not_applicable_with_evidence",
    V2_CELL_IDS[3]: "coverage_blocked",
    V2_CELL_IDS[4]: "coverage_blocked",
    V2_CELL_IDS[5]: "coverage_blocked",
    V2_CELL_IDS[6]: "coverage_blocked",
    V2_CELL_IDS[7]: "coverage_blocked",
    V2_CELL_IDS[8]: "coverage_blocked",
    V2_CELL_IDS[9]: "coverage_blocked",
    V2_CELL_IDS[10]: "coverage_blocked",
    V2_CELL_IDS[11]: "coverage_blocked",
    V2_CELL_IDS[12]: "coverage_blocked",
    V2_CELL_IDS[13]: "coverage_blocked",
    V2_CELL_IDS[14]: "coverage_blocked",
    V2_CELL_IDS[15]: "coverage_blocked",
}
DIALECT_PARENT_CELL_ID = V2_CELL_IDS[-1]
DIALECT_CHILD_STRATA: tuple[str, ...] = ()

ROLE_IDS = (
    "SOURCE_ADMISSION",
    "SPLIT_CUSTODY",
    "IDENTITY_LEAD",
    "INDEPENDENT_DISSENT",
    "DISPUTE_CRITIC",
    "CANDIDATE_BUILDER",
    "HUMAN_STEWARD",
    "EVALUATION_STEWARD",
    "ORCHESTRATOR",
)
STATE_IDS = (
    "SOURCE_INVENTORIED",
    "SOURCE_ADMITTED",
    "SOURCE_BLOCKED",
    "SPLIT_SEALED",
    "IDENTITY_REVIEWS_PENDING",
    "IDENTITY_AGREEMENT_QC",
    "IDENTITY_DISPUTED",
    "IDENTITY_PROVIDER_FAILURE",
    "IDENTITY_HUMAN_QUEUE",
    "DISPUTE_CRITIC_PENDING",
    "DISPUTE_CRITIQUED",
    "IDENTITY_HUMAN_ADJUDICATED",
    "IDENTITY_HUMAN_ABSTAINED",
    "IDENTITY_EVIDENCE_INSUFFICIENT",
    "MODEL_AGREEMENT_QUARANTINED_NOT_GOLD",
    "CASE_CANDIDATE_PENDING",
    "CASE_CANDIDATE_PROPOSED",
    "CANDIDATE_PROVIDER_FAILURE",
    "CASE_HUMAN_QUEUE",
    "CASE_HUMAN_ADJUDICATED",
    "CASE_HUMAN_ABSTAINED",
    "CASE_EVIDENCE_INSUFFICIENT",
    "GOLD_ELIGIBLE",
    "TRAINING_ELIGIBLE",
)
EXPECTED_NEXT_STATES = {
    "SOURCE_INVENTORIED": {"SOURCE_ADMITTED", "SOURCE_BLOCKED"},
    "SOURCE_ADMITTED": {"SPLIT_SEALED"},
    "SOURCE_BLOCKED": {"SOURCE_INVENTORIED"},
    "SPLIT_SEALED": {"IDENTITY_REVIEWS_PENDING"},
    "IDENTITY_REVIEWS_PENDING": {"IDENTITY_AGREEMENT_QC", "IDENTITY_DISPUTED", "IDENTITY_PROVIDER_FAILURE"},
    "IDENTITY_AGREEMENT_QC": {"IDENTITY_HUMAN_QUEUE", "MODEL_AGREEMENT_QUARANTINED_NOT_GOLD"},
    "IDENTITY_DISPUTED": {"DISPUTE_CRITIC_PENDING"},
    "IDENTITY_PROVIDER_FAILURE": {"IDENTITY_REVIEWS_PENDING", "IDENTITY_HUMAN_QUEUE"},
    "IDENTITY_HUMAN_QUEUE": {"IDENTITY_HUMAN_ADJUDICATED", "IDENTITY_HUMAN_ABSTAINED", "IDENTITY_EVIDENCE_INSUFFICIENT"},
    "DISPUTE_CRITIC_PENDING": {"DISPUTE_CRITIQUED", "IDENTITY_HUMAN_QUEUE"},
    "DISPUTE_CRITIQUED": {"IDENTITY_HUMAN_QUEUE"},
    "IDENTITY_HUMAN_ADJUDICATED": {"CASE_CANDIDATE_PENDING"},
    "IDENTITY_HUMAN_ABSTAINED": {"CASE_CANDIDATE_PENDING"},
    "IDENTITY_EVIDENCE_INSUFFICIENT": set(),
    "MODEL_AGREEMENT_QUARANTINED_NOT_GOLD": set(),
    "CASE_CANDIDATE_PENDING": {"CASE_CANDIDATE_PROPOSED", "CANDIDATE_PROVIDER_FAILURE"},
    "CASE_CANDIDATE_PROPOSED": {"CASE_HUMAN_QUEUE"},
    "CANDIDATE_PROVIDER_FAILURE": {"CASE_CANDIDATE_PENDING", "CASE_HUMAN_QUEUE"},
    "CASE_HUMAN_QUEUE": {"CASE_HUMAN_ADJUDICATED", "CASE_HUMAN_ABSTAINED", "CASE_EVIDENCE_INSUFFICIENT"},
    "CASE_HUMAN_ADJUDICATED": {"GOLD_ELIGIBLE"},
    "CASE_HUMAN_ABSTAINED": {"CASE_EVIDENCE_INSUFFICIENT"},
    "CASE_EVIDENCE_INSUFFICIENT": set(),
    "GOLD_ELIGIBLE": {"TRAINING_ELIGIBLE"},
    "TRAINING_ELIGIBLE": set(),
}

FORBIDDEN_FIELD_NAMES = frozenset(
    {
        "content",
        "gold",
        "heldout_membership",
        "heldout_content",
        "heldout_label",
        "label",
        "prompt",
        "provider_output",
        "provider_outputs",
        "source_body",
        "source_content",
        "source_text",
        "text",
    }
)


class ControlPlaneError(ValueError):
    """The V3 control-plane artifact is stale, incomplete, or unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ControlPlaneError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def canonical_bytes(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ControlPlaneError(f"cannot hash artifact: {path}") from exc


def _regular_file(path: Path, label: str) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise ControlPlaneError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(info.st_mode) and not path.is_symlink(), f"{label} must be a regular file")


def read_json(path: Path) -> dict[str, Any]:
    _regular_file(path, "JSON artifact")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ControlPlaneError(f"cannot read JSON artifact: {path}") from exc
    require(isinstance(value, dict), "JSON artifact must be an object")
    return value


def _walk_forbidden_fields(value: Any, path: str = "artifact") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            require(key not in FORBIDDEN_FIELD_NAMES, f"forbidden body field at {path}/{key}")
            _walk_forbidden_fields(child, f"{path}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden_fields(child, f"{path}/{index}")


def _validate_schema(value: Mapping[str, Any]) -> None:
    schema = read_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.absolute_path))
    if errors:
        location = "/".join(str(x) for x in errors[0].absolute_path) or "artifact"
        raise ControlPlaneError(f"artifact schema violation at {location}: {errors[0].message}")


def _binding(value: Mapping[str, Any], name: str, path: str, digest: str) -> None:
    actual = value[name]
    require(actual == {"path": path, "sha256": digest}, f"binding drift: {name}")
    resolved = ROOT / path
    require(sha256_file(resolved) == digest, f"bound artifact bytes drift: {path}")


def _verify_bindings(value: Mapping[str, Any]) -> None:
    bindings = value["bindings"]
    _binding(bindings, "v2_compatibility_matrix", V2_COMPATIBILITY_LOGICAL_PATH, V2_COMPATIBILITY_SHA256)
    _binding(bindings, "p2_canonical_contracts", P2_LOGICAL_PATH, P2_CANONICAL_CONTRACTS_SHA256)
    _binding(bindings, "p1_dialect_amendment", P1_DIALECT_LOGICAL_PATH, P1_DIALECT_AMENDMENT_SHA256)
    require(
        bindings["schema"] == {"path": SCHEMA_LOGICAL_PATH, "sha256": sha256_file(SCHEMA_PATH)},
        "control-plane schema binding drift",
    )
    require(
        bindings["validator"] == {"path": SCRIPT_LOGICAL_PATH, "sha256": sha256_file(SCRIPT_PATH)},
        "control-plane validator binding drift",
    )
    p4 = bindings["p4_v1"]
    require(p4["schema"] == {"path": P4_SCHEMA_LOGICAL_PATH, "sha256": P4_SCHEMA_SHA256}, "P4 v1 schema binding drift")
    require(
        sha256_file(ROOT / P4_SCHEMA_LOGICAL_PATH) == P4_SCHEMA_SHA256,
        "bound P4 v1 schema bytes drift",
    )
    require(
        p4["admission_file"] == {"path": P4_ADMISSION_LOGICAL_PATH, "sha256": P4_ADMISSION_FILE_SHA256},
        "P4 v1 admission binding drift",
    )
    require(
        sha256_file(ROOT / P4_ADMISSION_LOGICAL_PATH) == P4_ADMISSION_FILE_SHA256,
        "bound P4 v1 admission bytes drift",
    )
    p4_actual = read_json(ROOT / P4_ADMISSION_LOGICAL_PATH)
    p4_actual_body = {key: item for key, item in p4_actual.items() if key != "receipt_sha256"}
    require(
        p4_actual.get("receipt_sha256") == P4_ADMISSION_RECEIPT_SHA256
        and p4_actual["receipt_sha256"] == sha256_bytes(canonical_bytes(p4_actual_body)),
        "P4 v1 admission receipt drift",
    )
    require(p4["admission_receipt_sha256"] == P4_ADMISSION_RECEIPT_SHA256, "P4 v1 receipt digest drift")
    require(
        p4["status"] == "BLOCKED_PENDING_SOURCE_QUALIFIED_ADJUDICATION"
        and p4["denominator"]
        == {
            "source_units": 57,
            "unknown_rights_blockers": 39,
            "base_required_cells": 15,
            "composite_required_cells": 16,
            "coverage_blocked_cells": 14,
            "not_applicable_cells": 2,
            "rule_slots_R": 0,
        },
        "P4 v1 status or denominator drift",
    )
    require(
        p4_actual.get("status") == p4["status"] and p4_actual.get("denominator") == p4["denominator"],
        "P4 v1 artifact status or denominator drift",
    )
    require(
        p4_actual.get("current_construction")
        == {
            "candidate_admission_implemented": True,
            "construction_state": "no_admitted_cases",
            "dataset_case_row_count": 0,
            "dataset_case_rows": [],
        },
        "P4 v1 zero-row construction drift",
    )
    require(
        p4_actual.get("claims")
        == {
            "dataset_ready_claimed": False,
            "historical_or_dialect_modernized": False,
            "nonempty_pilot_constructed": False,
            "pilot_validated_claimed": False,
            "training_validated_claimed": False,
        },
        "P4 v1 semantic claim drift",
    )
    require(bindings["v2_parent_outcome_sha256"] == V2_PARENT_OUTCOME_SHA256, "V2 parent outcome binding drift")
    require(
        value["outcome_boundary"]["reviewed_v3_consensus_sha256"] == REVIEWED_V3_CONSENSUS_SHA256,
        "reviewed V3 consensus binding drift",
    )


def _verify_taxonomy(value: Mapping[str, Any]) -> None:
    taxonomy = value["taxonomy"]
    require(
        taxonomy["tuple_fields"]
        == [
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
            "original_surface",
            "editorial_surface",
            "normalized_surface",
        ],
        "orthogonal taxonomy tuple drift",
    )
    axis_ids = [entry["axis_id"] for entry in taxonomy["axes"]]
    require(
        axis_ids
        == [
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
        ],
        "taxonomy axis set or order drift",
    )
    require(
        {entry["layer_id"] for entry in taxonomy["surface_layers"]}
        == {"original_surface", "editorial_surface", "normalized_surface"},
        "surface layer set drift",
    )
    invariants = taxonomy["protected_invariants"]
    require(invariants["original_surface_preserved"], "original surface is not protected")
    require(invariants["modern_correction_eligible_when_protected"] is False, "protected form became correction eligible")
    require(invariants["automatic_standard_normalization"] is False, "automatic standard normalization enabled")
    require(invariants["automatic_national_successor_mapping"] is False, "automatic successor mapping enabled")
    boundaries = taxonomy["identity_boundaries"]
    require(all(boundaries.values()), "identity boundary invariant disabled")
    partition = taxonomy["dialect_parent_partition"]
    require(partition["parent_cell_id"] == DIALECT_PARENT_CELL_ID, "dialect parent cell drift")
    require(partition["partition_complete"] is False, "dialect partition was claimed materialized")
    require(partition["membership_frozen"] is False, "dialect membership was claimed frozen")
    require(partition["parent_denominator_visible"] is True, "dialect parent left denominator")
    require(partition["parent_direct_coverage_credit"] is False, "dialect parent receives direct child credit")
    require(partition["partition_dimensions"] == ["source", "region", "period", "register"], "dialect partition dimensions drift")
    child_ids = tuple(entry["stratum_id"] for entry in partition["child_strata"])
    require(child_ids == DIALECT_CHILD_STRATA, "dialect child stratum set drift")
    require(all(entry["parent_cell_id"] == DIALECT_PARENT_CELL_ID for entry in partition["child_strata"]), "dialect lineage drift")
    require(all(entry["source_membership_frozen"] is False for entry in partition["child_strata"]), "source membership leaked")


def _verify_roles_and_visibility(value: Mapping[str, Any]) -> None:
    roles = value["roles"]
    role_ids = tuple(role["role_id"] for role in roles)
    require(role_ids == ROLE_IDS, "role set or order drift")
    expected_routes = {
        "SOURCE_ADMISSION": ("deterministic", "deterministic_tooling", "deterministic", "none"),
        "SPLIT_CUSTODY": ("deterministic", "deterministic_tooling", "deterministic", "none"),
        "IDENTITY_LEAD": ("model", "anthropic", "claude-fable-5", "high"),
        "INDEPENDENT_DISSENT": ("model", "google", "gemini-3.7-flash-high", "high"),
        "DISPUTE_CRITIC": ("model", "xai", "grok-4.6", "high"),
        "CANDIDATE_BUILDER": ("model", "openai", "gpt-5.6-sol", "xhigh"),
        "HUMAN_STEWARD": ("human", "operator", "human_operator", "manual"),
        "EVALUATION_STEWARD": ("human", "operator", "human_operator_and_deterministic_custody", "manual"),
        "ORCHESTRATOR": ("deterministic", "control_plane", "deterministic_control_plane", "none"),
    }
    for role in roles:
        route = role["preferred_route"]
        require(
            (route["route_kind"], route["provider_family"], route["model"], route["effort_or_exposure"])
            == expected_routes[role["role_id"]],
            f"preferred route drift: {role['role_id']}",
        )
        require(
            role["may_author_gold"] is (role["role_id"] == "HUMAN_STEWARD"),
            f"gold authority drift: {role['role_id']}",
        )
        require(role["may_count_toward_coverage"] is False, f"direct role coverage credit drift: {role['role_id']}")
    matrix = value["visibility_matrix"]
    require(tuple(entry["role_id"] for entry in matrix) == ROLE_IDS, "visibility role set or order drift")
    entries = {entry["role_id"]: entry for entry in matrix}
    identity_allowed = entries["IDENTITY_LEAD"]["allowed_input_classes"]
    identity_forbidden = entries["IDENTITY_LEAD"]["forbidden_input_classes"]
    dissent = entries["INDEPENDENT_DISSENT"]
    require(dissent["allowed_input_classes"] == identity_allowed, "identity packets differ")
    require(dissent["forbidden_input_classes"] == identity_forbidden, "identity blind boundary differs")
    for role_id, entry in entries.items():
        expected_heldout = role_id == "EVALUATION_STEWARD"
        require(entry["heldout_access"] == ("evaluation_runtime_only" if expected_heldout else "forbidden"), f"held-out access drift: {role_id}")
        require(
            next(role for role in roles if role["role_id"] == role_id)["may_access_heldout"] is expected_heldout,
            f"role/visibility held-out access disagreement: {role_id}",
        )
        require(entry["coverage_credit"] is False and entry["gold_credit"] is False and entry["training_credit"] is False, f"credit leaked to {role_id}")
    for role_id in ("IDENTITY_LEAD", "INDEPENDENT_DISSENT", "DISPUTE_CRITIC", "CANDIDATE_BUILDER"):
        forbidden = set(entries[role_id]["forbidden_input_classes"])
        require(
            {
                "heldout_membership",
                "heldout_content",
                "heldout_labels",
                "heldout_locators",
                "heldout_fingerprints",
                "heldout_derivatives",
                "provider_output",
            }.issubset(forbidden),
            f"blind boundary drift: {role_id}",
        )
    require(value["conflict_contract"]["same_packet_for_identity_roles"] is True, "identity packet sharing disabled")
    require(value["conflict_contract"]["identity_outputs_hidden_from_each_other"] is True, "identity output isolation disabled")
    require(value["conflict_contract"]["builder_receives_identity_opinions"] is False, "builder receives identity opinions")
    require(value["conflict_contract"]["critic_receives_model_prestige_or_order"] is False, "critic receives model prestige")
    require(value["conflict_contract"]["model_may_vote_on_own_output"] is False, "self-vote is enabled")
    require(value["conflict_contract"]["independent_family_required"] is True, "cross-family independence disabled")


def _verify_state_machine(value: Mapping[str, Any]) -> None:
    machine = value["state_machine"]
    states = {state["state_id"]: state for state in machine["states"]}
    require(tuple(states) == STATE_IDS, "state set or order drift")
    require(machine["initial_state"] == "SOURCE_INVENTORIED", "initial state drift")
    for state_id in STATE_IDS:
        state = states[state_id]
        next_states = set(state["legal_next_states"])
        require(next_states == EXPECTED_NEXT_STATES[state_id], f"legal transition drift: {state_id}")
        expected_coverage = state_id in {"GOLD_ELIGIBLE", "TRAINING_ELIGIBLE"}
        require(state["counts_toward_coverage"] is expected_coverage, f"coverage semantics drift: {state_id}")
        expected_gold = state_id in {"GOLD_ELIGIBLE", "TRAINING_ELIGIBLE"}
        expected_training = state_id == "TRAINING_ELIGIBLE"
        require(state["gold_eligible"] is expected_gold, f"gold semantics drift: {state_id}")
        require(state["training_eligible"] is expected_training, f"training semantics drift: {state_id}")
        if next_states:
            require(state["terminal"] is False, f"nonterminal state marked terminal: {state_id}")
        else:
            require(state["terminal"] is True, f"dead-end state not explicit terminal: {state_id}")
        if state_id in {
            "SOURCE_BLOCKED",
            "IDENTITY_EVIDENCE_INSUFFICIENT",
            "MODEL_AGREEMENT_QUARANTINED_NOT_GOLD",
            "CASE_EVIDENCE_INSUFFICIENT",
        }:
            require(state["resumable"] is True and state["resume_to_state"] is not None, f"resumable failure missing: {state_id}")
        elif state_id == "TRAINING_ELIGIBLE":
            require(state["resumable"] is False and state["resume_to_state"] is None, "training terminal drift")
        else:
            require(state["resume_to_state"] is None, f"unexpected resume target: {state_id}")
    transitions = {(item["from_state"], item["to_state"]) for item in machine["transitions"]}
    expected_transitions = {
        (from_state, target)
        for from_state, targets in EXPECTED_NEXT_STATES.items()
        for target in targets
    }
    require(transitions == expected_transitions, "transition table exact-set drift")
    require(machine["format_retry_limit"] == 1, "format retry limit drift")
    require(machine["no_dead_end_invariant"] is True, "no-dead-end invariant disabled")


def _verify_agreement_and_quarantine(value: Mapping[str, Any]) -> None:
    predicate = value["agreement_predicate"]
    require(predicate["comparison"] == "canonical_json_exact_equality_over_required_fields", "agreement is not exact")
    require(predicate["primary_language_only_insufficient"] is True, "language-only agreement accepted")
    require(predicate["majority_agreement_insufficient"] is True, "majority agreement accepted")
    require(predicate["abstention_state_compared"] is True, "abstention not compared")
    require(predicate["provider_output_not_gold"] is True, "provider output can become gold")
    quarantine = value["quarantine_policy"]
    for key in ("counts_toward_coverage", "gold_eligible", "training_eligible", "evaluation_eligible", "teaching_view_eligible", "unsampled_promotion_allowed"):
        require(quarantine[key] is False, f"quarantine policy drift: {key}")
    require(quarantine["promotion_state"] == "CASE_HUMAN_ADJUDICATED", "quarantine promotion bypasses human case adjudication")
    require(quarantine["protected_high_risk_always_human"] is True, "protected/high-risk human gate disabled")
    require(quarantine["critic_unresolved_routes_to_human"] is True, "critic failure stranded")


def _verify_human_and_firewall(value: Mapping[str, Any]) -> None:
    manifest = value["human_work_manifest"]
    require(manifest["required_before_provider_pilot"] is True, "human manifest is not pre-provider")
    require(manifest["atomic_decision_key"] == ["span_hash", "claim_type", "proposed_value", "evidence_bundle_hash", "source_revision"], "human decision key drift")
    require(manifest["protected_high_risk_review_fraction"] == 1.0, "protected/high-risk rows are not 100% reviewed")
    require(manifest["provider_calls_authorized"] is False, "provider calls enabled by control-plane contract")
    require(manifest["unsampled_agreement_policy"] == "remain_quarantined_no_coverage_or_consumer_view_credit", "unsampled promotion policy drift")
    require(manifest["audit_failure_policy"] == "freeze_uninspected_cohort_and_route_complete_human_review_or_unresolved", "audit failure policy drift")
    firewall = value["heldout_firewall"]
    require(firewall["required_nonzero_count_per_v3_stratum"] is True, "held-out strata do not require nonzero counts")
    for key in ("membership_sealed_before_construction", "construction_freeze_before_exposure", "post_exposure_mutation_invalidates_version", "new_partition_required_after_invalidation", "solo_operator_limitation_disclosed"):
        require(firewall[key] is True, f"held-out firewall drift: {key}")
    for key in ("construction_access_to_membership", "construction_access_to_content", "construction_access_to_labels", "construction_access_to_locators", "construction_access_to_fingerprints", "construction_access_to_derivatives", "private_evaluation_runtime_during_construction"):
        require(firewall[key] is False, f"held-out construction access leaked: {key}")
    require(firewall["ambiguous_evidence_action"] == "abstain", "ambiguous evidence does not abstain")


def _verify_compatibility(value: Mapping[str, Any]) -> None:
    compatibility = value["compatibility"]
    require(
        compatibility["v2_composite_denominator"]
        == {
            "source_units": 57,
            "base_required_cells": 15,
            "composite_required_cells": 16,
            "coverage_blocked_cells": 14,
            "not_applicable_cells": 2,
            "rule_slots_R": 0,
        },
        "V2 denominator drift",
    )
    cells = compatibility["cells"]
    require(tuple(entry["v2_cell_id"] for entry in cells) == V2_CELL_IDS, "V2 semantic cell set or order drift")
    expected_new = {"path": SCHEMA_LOGICAL_PATH, "sha256": sha256_file(SCHEMA_PATH)}
    for entry in cells:
        cell_id = entry["v2_cell_id"]
        require(entry["v2_status"] == V2_CELL_STATUS[cell_id], f"V2 cell status drift: {cell_id}")
        if cell_id == DIALECT_PARENT_CELL_ID:
            require(entry["old_artifact"] == {"path": P1_DIALECT_LOGICAL_PATH, "sha256": P1_DIALECT_AMENDMENT_SHA256}, "dialect parent provenance drift")
            require(entry["disposition"] == "carried_forward_exact", "dialect parent disposition drift")
            require(tuple(entry["child_partition_ids"]) == DIALECT_CHILD_STRATA, "dialect child partition binding drift")
            require(entry["denominator_effect"] == "same_parent_denominator", "dialect denominator effect drift")
        else:
            require(entry["old_artifact"] == {"path": P2_LOGICAL_PATH, "sha256": P2_CANONICAL_CONTRACTS_SHA256}, f"V2 parent provenance drift: {cell_id}")
            require(entry["disposition"] == "carried_forward_exact", f"V2 cell disposition drift: {cell_id}")
            require(entry["child_partition_ids"] == [], f"unexpected child partition: {cell_id}")
            require(entry["denominator_effect"] in {"same_parent_denominator", "boundary_cell_preserved"}, f"V2 denominator effect drift: {cell_id}")
        require(entry["v3_cell_id"] == cell_id, f"stable cell ID drift: {cell_id}")
        require(entry["new_binding"] == expected_new, f"V3 binding drift: {cell_id}")
    require(compatibility["dispositions_complete"] is True, "compatibility table is incomplete")
    require(compatibility["source_unit_ids_stable"] is True, "source IDs are not stable")
    require(compatibility["parent_cells_no_direct_child_credit"] is True, "parent cell receives child credit")
    require(compatibility["v2_denominator_preserved"] is True, "V2 denominator not preserved")


def _verify_children_and_gates(value: Mapping[str, Any]) -> None:
    slots = value["child_work_slots"]
    require(tuple(slot["slot_id"] for slot in slots) == ("V3-A", "V3-B", "V3-C"), "V3 child slot set or order drift")
    require(
        {slot["slot_id"]: slot["issue_number"] for slot in slots} == {"V3-A": 7560, "V3-B": 7559, "V3-C": 7561},
        "V3 child issue binding drift",
    )
    for slot in slots:
        require(slot["status"] == "NOT_STARTED", f"child slot status overclaim: {slot['slot_id']}")
        require(slot["provider_calls_authorized"] is False and slot["mass_labeling_authorized"] is False, f"child slot execution gate drift: {slot['slot_id']}")
        require(slot["completion_requires_exact_hashes"] is True, f"child slot hash gate disabled: {slot['slot_id']}")
    require(
        {slot["slot_id"]: slot["dependencies"] for slot in slots}
        == {
            "V3-A": ["phase3_v3_cooperative_control_plane_v1"],
            "V3-B": ["phase3_v3_cooperative_control_plane_v1", "issue_7560"],
            "V3-C": ["phase3_v3_cooperative_control_plane_v1", "issue_7560"],
        },
        "V3 child dependency DAG drift",
    )
    gates = value["gates"]
    require(gates["ratification_complete"] is True, "ratification gate is not closed")
    require(gates["outcome_sha_scope_approved"] is True, "reviewed outcome/scope gate is not closed")
    for key in ("provider_calls_authorized", "labeling_authorized", "training_authorized", "p4_v2_authorized", "p4_v1_mutation_allowed"):
        require(gates[key] is False, f"execution gate unexpectedly open: {key}")
    require(gates["required_child_slots"] == ["V3-A", "V3-B", "V3-C"], "required child slots drift")


def verify(path: Path = ARTIFACT_PATH) -> dict[str, Any]:
    """Validate one artifact and return a deterministic, metadata-only summary."""
    value = read_json(Path(path))
    _walk_forbidden_fields(value)
    _validate_schema(value)
    require(value["text_free"] is True and value["metadata_only"] is True, "artifact is not metadata-only")
    require(
        value["provider_calls"] is False and value["status"] == "FROZEN_REVIEWED_METADATA_ONLY",
        "contract boundary drift",
    )
    body = {key: item for key, item in value.items() if key != "receipt_sha256"}
    require(value["receipt_sha256"] == sha256_bytes(canonical_bytes(body)), "control-plane receipt hash drift")
    _verify_bindings(value)
    _verify_taxonomy(value)
    _verify_roles_and_visibility(value)
    _verify_state_machine(value)
    _verify_agreement_and_quarantine(value)
    _verify_human_and_firewall(value)
    _verify_compatibility(value)
    _verify_children_and_gates(value)
    return {
        "ok": True,
        "schema_version": value["schema_version"],
        "status": value["status"],
        "artifact_sha256": sha256_file(Path(path)),
        "receipt_sha256": value["receipt_sha256"],
        "v2_cell_count": len(value["compatibility"]["cells"]),
        "role_count": len(value["roles"]),
        "state_count": len(value["state_machine"]["states"]),
        "child_slot_count": len(value["child_work_slots"]),
        "provider_calls": value["provider_calls"],
        "gold_authority": "HUMAN_STEWARD",
        "p4_v1_mutation_allowed": value["gates"]["p4_v1_mutation_allowed"],
    }


def build_contract() -> dict[str, Any]:
    """Load the tracked contract for callers that need a stable fixture."""
    return read_json(ARTIFACT_PATH)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate the tracked metadata artifact")
    parser.add_argument("--path", type=Path, default=ARTIFACT_PATH, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if not args.check:
        parser.error("--check is required")
    try:
        result = verify(args.path)
    except ControlPlaneError as exc:
        print(f"phase3_v3_cooperative_control_plane: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
