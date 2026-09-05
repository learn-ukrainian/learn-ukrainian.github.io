#!/usr/bin/env python3
"""V4 A10 pilot review gate: the independent Ukrainian-language review plus
exact-head cross-family (CF) review packet and gate, bound to the merged A9
evaluation package receipt, the frozen V4 pilot slot manifest, and the V4
SHA.

A10 owns the *pilot_review* role (``role_ownership.A10 == "pilot_review"`` in
the frozen slot manifest): the one place the manifest's own
``INDEPENDENT_CROSS_FAMILY_EXACT_HEAD_REVIEW`` required gate is wired. It
must never claim a passed pilot review, never run a live Ukrainian-language
review of corpus or held-out material, never open A3's held-out membership
file, and never open A4's private extraction ledger.

This module never loads source text, never re-fetches corpus, and never
executes a review against an empty or missing row: its only inputs are eight
already-public artifacts --

* A2's source operation admission receipt (``stratum_coverage_map`` and
  ``residuals`` -- rights/coverage state, never source text),
* A4's deterministic extraction receipt (only its own already-carried
  residuals, never A4's private ledger),
* A5's evidence enrichment receipt (already-carried residuals only),
* A6's blind arena receipt (already-carried residuals only),
* A7's original-row factory receipt (its own ``a7_residuals`` only),
* A8's admission/assembly receipt (its own ``a8_residuals`` only),
* A9's evaluation package receipt (its own ``a9_residuals`` and
  ``consumer_reproduction_view`` -- the direct upstream signal this module's
  gate and review-readiness view build on, and ``evaluation_gate
  .evaluation_slice_ready`` -- the one flag that must be true before any real
  review could ever have something to look at), and
* the frozen 100-slot V4 pilot slot manifest (``slot_series`` and
  ``required_gate_ids`` -- public slot IDs and the gate ID this module owns,
  never a real ``source_unit_id``).

Three independent parts:

1. ``check_pilot_review_gate`` -- independently re-derives, from those eight
   public artifacts alone, whether a pilot review may ever be claimed
   passed. Right now it cannot: A9 itself reports
   ``evaluation_gate.evaluation_slice_ready: false`` (A8 admitted zero rows,
   so A9 has nothing scored, so there is nothing for a reviewer to look at),
   and independent of that, no review-execution mechanism exists yet at all
   -- ``independent_review_recorded`` is a hardcoded ``False``, never derived
   from a file that does not exist, so the gate cannot open by accident even
   if every upstream flag flips true. Per the binding contract this module
   must *never* claim ``PILOT_REVIEW_PASSED`` while that is true; it reports
   ``pilot_review_slice_ready: false`` and a typed ``blocked_reason_code``
   instead.
2. ``build_review_packet`` -- the fixed, data-independent contract every real
   future review must satisfy: an independent Ukrainian-language reviewer
   whose model family differs from the row's author family, an exact-head
   cross-family review of record (never mere discussion, never an internal
   helper swarm), and no self-review. The packet never varies with gate
   state -- it is the same requirement whether the gate is open or closed --
   and it is never itself evidence that a review happened.
3. ``build_receipt`` -- assembles the public receipt: the frozen 100-slot
   denominator (reusing, never duplicating,
   ``v4_a6_blind_arena.frozen_slot_strata``/``all_frozen_slot_ids``), the
   gate, the review packet, every A2/A4/A5/A6/A7/A8/A9 residual carried
   forward unresolved, a per-slot review-readiness view built by
   cross-checking A9's own ``consumer_reproduction_view`` and never marking a
   slot reviewed, and one typed per-slot A10 residual reusing A9's own
   already-public per-stratum reason codes -- never a fourth, independently
   invented reason.

Run with no arguments to verify the checked-in A10 receipt reproduces from
the eight public artifacts on disk -- no ``batch_state/`` required, so this
passes in a fresh checkout. Pass ``--write-receipt`` to (re)assemble and
persist it after a genuine change to one of those eight artifacts or to this
module.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from learn_ukrainian_v4_runtime.provenance import validation_session
from learn_ukrainian_v4_runtime.resources import resource_root

_SELF_ROOT = resource_root()

from learn_ukrainian_v4_runtime import v4_a9_evaluation_package as a9

ROOT = _SELF_ROOT
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"

A10_RECEIPT_PATH = ADMISSION / "dataset_v4_a10_pilot_review_gate_receipt_v1.json"
A10_SCHEMA_PATH = CONTRACTS / "dataset_v4_a10_pilot_review_gate_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_PATH = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
A6_RECEIPT_PATH = ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json"
A7_RECEIPT_PATH = ADMISSION / "dataset_v4_a7_original_row_factory_receipt_v1.json"
A8_RECEIPT_PATH = ADMISSION / "dataset_v4_a8_admission_assembly_receipt_v1.json"
A9_RECEIPT_PATH = ADMISSION / "dataset_v4_a9_evaluation_package_receipt_v1.json"
SLOT_MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"
SELF_PATH = ROOT / "scripts/projects/open_model_data/v4_a10_pilot_review_gate.py"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

# The manifest's own required gate ID for this stage -- never invented, and
# checked at gate-derivation time to still be present in the live manifest.
REQUIRED_GATE_ID = "INDEPENDENT_CROSS_FAMILY_EXACT_HEAD_REVIEW"

# Mirrors v4_a9_evaluation_package.FORBIDDEN_KEYS exactly -- "gold" is
# deliberately excluded because it is the name of this receipt's own
# always-false eligibility flag, never a real gold label.
FORBIDDEN_KEYS = a9.FORBIDDEN_KEYS
FORBIDDEN_SUBSTRINGS = a9.FORBIDDEN_SUBSTRINGS

# Completion-vocabulary claims that belong to other roles or are unreachable
# today (see the manifest's own completion_vocabulary and A0's non_goals) --
# never emitted here. Unlike A9's own list, "EVAL_ARTIFACT_READY" (A9's own
# ready state, now a foreign claim from A10's point of view) is added back,
# and "PILOT_REVIEW_PASSED" (A10's own legitimate -- if currently unreachable
# -- ready state) is removed, mirroring how each stage excludes only its own
# name from the borrowed forbidden-claims list.
FORBIDDEN_COMPLETION_CLAIMS = tuple(
    sorted({*a9.FORBIDDEN_COMPLETION_CLAIMS, "EVAL_ARTIFACT_READY"} - {"PILOT_REVIEW_PASSED"})
)

PILOT_REVIEW_ELIGIBILITY = {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}

# The fixed review-packet contract. Never varies with gate state, and is
# never itself evidence that a review happened -- it is the requirement a
# real future review must satisfy, not a record that one occurred.
REVIEW_PACKET_REQUIREMENTS = {
    "gate_id": REQUIRED_GATE_ID,
    "requires_independent_ukrainian_language_reviewer": True,
    "reviewer_family_must_differ_from_author_family": True,
    "requires_exact_head_cross_family_review_of_record": True,
    "self_review_satisfies_gate": False,
    "discussion_only_satisfies_gate": False,
    "internal_helper_swarm_satisfies_gate": False,
    "review_may_execute_against_missing_or_empty_rows": False,
    "review_execution_state": "NOT_EXECUTED_NO_ADMITTED_ROWS",
}

canonical_json = a9.canonical_json
sha256_text = a9.sha256_text
sha256_file = a9.sha256_file


class PilotReviewGateError(ValueError):
    """The A10 wiring or its deterministic receipt is unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PilotReviewGateError(message)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# --- A9 reason -> A10 per-slot residual reason -------------------------------
#
# A9 already types each frozen slot's blocker as one of three reason codes
# (reused unchanged from A8's own mapping, itself from A7's). A10 never
# invents a fourth -- "why has A9 not scored a row for this slot" is exactly
# "why has A10 nothing to submit for independent review".
A10_NEXT_ACTION_BY_REASON = {
    "rights_unknown": (
        "no admitted and scored row exists to review for this frozen slot until A2 resolves unit-specific "
        "training/derivation rights for its stratum's supporting source unit -- never review a placeholder row "
        "while rights remain unknown"
    ),
    "source_incomplete": (
        "no source unit is yet identified for this frozen slot's stratum, so A9 has nothing scored and A10 has "
        "nothing to submit for independent Ukrainian-language or exact-head cross-family review -- never invent "
        "or substitute a placeholder review"
    ),
    "independence_unavailable": (
        "a supporting source unit is identified for this frozen slot's stratum but its coverage/rights review is "
        "not yet complete, so A9 scored nothing for it and A10 has no row ready for independent review yet"
    ),
}


# --- pilot review gate (public-only) -----------------------------------------


def check_pilot_review_gate(root: Path = ROOT) -> dict[str, Any]:
    """Independently re-derive whether a pilot review may ever be claimed
    passed, from the frozen slot manifest's own ``assignment_state`` per
    stratum, A2's own residuals, and A9's independent validity -- never
    trusting the A10 receipt's own declared fields, never opening
    ``batch_state/``. ``pilot_review_slice_ready`` is only ever true once
    every frozen slot is assigned to a real source unit *and* A2 has zero
    unresolved residuals *and* A9 itself still independently validates *and*
    A9's own evaluation gate is open *and* an independent review has actually
    been recorded -- and that last condition has no execution mechanism yet,
    so it is a hardcoded ``False``, never derived from a file that does not
    exist.

    Fails closed -- a *closed gate*, not an exception -- if any of the three
    required public artifacts (slot manifest, A2 receipt, A9 receipt) is
    missing, mirroring ``v4_a9_evaluation_package.check_evaluation_gate``'s
    own missing-artifact handling."""
    manifest_path = (root / "data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json").resolve()
    a2_path = (
        root / "data/projects/open_model_data/admission/dataset_v4_a2_source_operation_admission_receipt_v1.json"
    ).resolve()
    a9_path = (
        root / "data/projects/open_model_data/admission/dataset_v4_a9_evaluation_package_receipt_v1.json"
    ).resolve()
    required_paths = {"slot_manifest": manifest_path, "a2_receipt": a2_path, "a9_receipt": a9_path}
    for label, path in required_paths.items():
        require(root.resolve() in path.parents, f"{label} path escapes the repository root -- refusing")

    missing = sorted(label for label, path in required_paths.items() if not path.is_file())
    if missing:
        return {
            "gate_id": "v4-a10-pilot-review-gate-v1",
            "a9_receipt_valid": False,
            "a2_rights_resolved": False,
            "all_slots_assigned": False,
            "upstream_evaluation_slice_ready": False,
            "independent_review_recorded": False,
            "pilot_review_slice_ready": False,
            "owner_role": "A2_A3_PRIVATE_ARTIFACT",
            "blocked_reason_code": f"required_public_artifact_missing:{missing[0]}",
        }

    manifest = _load(manifest_path)
    require(
        manifest.get("controlling_outcome_sha256") == V4_SHA256,
        "slot manifest is not bound to the expected V4 controlling outcome -- refusing",
    )
    require(
        REQUIRED_GATE_ID in manifest.get("required_gate_ids", []),
        "slot manifest no longer lists this stage's required gate ID -- refusing",
    )

    a2_receipt = _load(a2_path)
    require(
        a2_receipt.get("controlling_outcome_sha256") == V4_SHA256,
        "A2 receipt is not bound to the expected V4 controlling outcome -- refusing",
    )
    rights_resolved = len(a2_receipt.get("residuals", [])) == 0

    all_assigned = all(series["assignment_state"] == "ASSIGNED" for series in manifest["slot_series"])

    a9_receipt = _load(a9_path)
    try:
        a9.validate_receipt_independently(a9_receipt, root)
        a9_valid = True
    except a9.EvaluationPackageError:
        a9_valid = False

    upstream_evaluation_slice_ready = a9_valid and a9_receipt["evaluation_gate"]["evaluation_slice_ready"] is True

    # No review-execution mechanism exists yet -- this can never be derived
    # true from any file on disk today, so it stays a hardcoded False rather
    # than an independently-computed flag that could accidentally flip.
    independent_review_recorded = False

    pilot_review_slice_ready = (
        rights_resolved
        and all_assigned
        and a9_valid
        and upstream_evaluation_slice_ready
        and independent_review_recorded
    )
    blocked_reason_code = None
    if not pilot_review_slice_ready:
        if not a9_valid:
            blocked_reason_code = "a9_receipt_invalid"
        elif not rights_resolved and not all_assigned:
            blocked_reason_code = "rights_unresolved_and_slots_unassigned"
        elif not rights_resolved:
            blocked_reason_code = "rights_unresolved"
        elif not all_assigned:
            blocked_reason_code = "slot_assignment_pending_a2_a3"
        elif not upstream_evaluation_slice_ready:
            blocked_reason_code = f"upstream_a9_blocked:{a9_receipt['evaluation_gate']['blocked_reason_code']}"
        else:
            blocked_reason_code = "independent_review_not_yet_executed_no_admitted_rows"

    return {
        "gate_id": "v4-a10-pilot-review-gate-v1",
        "a9_receipt_valid": a9_valid,
        "a2_rights_resolved": rights_resolved,
        "all_slots_assigned": all_assigned,
        "upstream_evaluation_slice_ready": upstream_evaluation_slice_ready,
        "independent_review_recorded": independent_review_recorded,
        "pilot_review_slice_ready": pilot_review_slice_ready,
        "owner_role": manifest["sealed_heldout_commitment"]["assignment_owner"],
        "blocked_reason_code": blocked_reason_code,
    }


# --- A10's own per-slot residuals (public, source-free) ----------------------


def derive_a10_slot_residuals(
    manifest: dict[str, Any], a2_receipt: dict[str, Any], gate: dict[str, Any]
) -> list[dict[str, Any]]:
    """One typed residual per frozen public slot ID -- never a silently
    dropped slot and never a review verdict invented in place of the missing
    scored row. A pure function of the manifest's own ``slot_series``, A9's
    own already-public per-stratum reason codes, and the gate this module
    itself re-derives; never opens any private state."""
    owner_role = gate["owner_role"]
    reasons_by_stratum = a9.a8.a7.stratum_reason_codes(a2_receipt)
    residuals = []
    for stratum_entry in a9.a8.a7.a6.frozen_slot_strata(manifest):
        stratum = stratum_entry["stratum"]
        reason_code = reasons_by_stratum[stratum]
        for slot_id in stratum_entry["slot_ids"]:
            residuals.append(
                {
                    "residual_id": f"a10-residual-{reason_code.replace('_', '-')}-{slot_id}",
                    "subject_kind": "pilot_slot",
                    "subject_id": slot_id,
                    "stage": "A10",
                    "reason_code": reason_code,
                    "owner_role": owner_role,
                    "next_action": A10_NEXT_ACTION_BY_REASON[reason_code],
                    "retryability": "retryable",
                    "evidence_refs": [
                        "admission.dataset_v4_pilot_slot_manifest_v1.slot_series",
                        "admission.dataset_v4_a2_source_operation_admission_receipt_v1.stratum_coverage_map",
                        "admission.dataset_v4_a9_evaluation_package_receipt_v1.a9_residuals",
                    ],
                }
            )
    residuals.sort(key=lambda residual: residual["subject_id"])
    return residuals


# --- review-readiness view (public, fail-closed, never executes a review) ---


def build_review_readiness_view(
    manifest: dict[str, Any], a9_receipt: dict[str, Any], a10_residuals: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Reproduce, per frozen slot, exactly what an independent review packet
    would see -- and fail closed if A9's own ``consumer_reproduction_view``
    ever claims a slot scored without an admitted row. Never marks a slot
    reviewed: ``review_executed`` is unconditionally ``False`` because this
    module has no execution mechanism and must never review a missing or
    empty row."""
    residual_by_slot = {residual["subject_id"]: residual["residual_id"] for residual in a10_residuals}
    expected_slot_ids = set(a9.a8.a7.a6.all_frozen_slot_ids(manifest))
    seen_slot_ids = {entry["slot_id"] for entry in a9_receipt["consumer_reproduction_view"]}
    require(
        seen_slot_ids == expected_slot_ids,
        "A9 consumer_reproduction_view does not cover exactly the frozen slot manifest -- refusing pilot review readiness view",
    )

    view = []
    for entry in a9_receipt["consumer_reproduction_view"]:
        slot_id = entry["slot_id"]
        row_admitted = entry["row_admitted"]
        row_scored = entry["scored"]
        require(
            row_scored is False or row_admitted is True,
            f"A9 consumer_reproduction_view claims slot {slot_id!r} scored without an admitted row -- refusing "
            "(cannot review a nonexistent row)",
        )
        view.append(
            {
                "slot_id": slot_id,
                "row_admitted": row_admitted,
                "row_scored": row_scored,
                "review_required": True,
                "review_executed": False,
                "reviewer_family": None,
                "cf_review_of_record_passed": False,
                "residual_id": residual_by_slot[slot_id],
            }
        )
    view.sort(key=lambda entry: entry["slot_id"])
    return view


# --- review packet (fixed, data-independent contract) -----------------------


def build_review_packet() -> dict[str, Any]:
    """The fixed review-packet contract every real future review must
    satisfy. Never varies with gate state and never itself claims a review
    happened -- returns a fresh copy of the frozen
    ``REVIEW_PACKET_REQUIREMENTS`` so callers cannot mutate the module-level
    constant."""
    return dict(REVIEW_PACKET_REQUIREMENTS)


# --- receipt assembly --------------------------------------------------------


def build_receipt(root: Path = ROOT) -> dict[str, Any]:
    manifest = _load(SLOT_MANIFEST_PATH)
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)
    a5_receipt = _load(A5_RECEIPT_PATH)
    a6_receipt = _load(A6_RECEIPT_PATH)
    a7_receipt = _load(A7_RECEIPT_PATH)
    a8_receipt = _load(A8_RECEIPT_PATH)
    a9_receipt = _load(A9_RECEIPT_PATH)
    gate = check_pilot_review_gate(root)

    strata = a9.a8.a7.a6.frozen_slot_strata(manifest)
    frozen_slot_ids = a9.a8.a7.a6.all_frozen_slot_ids(manifest)

    a2_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A2", "status": "unresolved_carried_to_a10"}
        for entry in a2_receipt["residuals"]
    ]
    a4_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A4", "status": "unresolved_carried_to_a10"}
        for entry in a4_receipt["a4_residuals"]
    ]
    a5_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A5", "status": "unresolved_carried_to_a10"}
        for entry in a5_receipt["a5_residuals"]
    ]
    a6_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A6", "status": "unresolved_carried_to_a10"}
        for entry in a6_receipt["a6_residuals"]
    ]
    a7_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A7", "status": "unresolved_carried_to_a10"}
        for entry in a7_receipt["a7_residuals"]
    ]
    a8_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A8", "status": "unresolved_carried_to_a10"}
        for entry in a8_receipt["a8_residuals"]
    ]
    a9_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A9", "status": "unresolved_carried_to_a10"}
        for entry in a9_receipt["a9_residuals"]
    ]

    a10_residuals = derive_a10_slot_residuals(manifest, a2_receipt, gate)
    review_readiness_view = build_review_readiness_view(manifest, a9_receipt, a10_residuals)
    review_packet = build_review_packet()

    rows_reviewed = sum(1 for entry in review_readiness_view if entry["review_executed"])
    rows_admitted = sum(1 for entry in review_readiness_view if entry["row_admitted"])

    return {
        "schema_version": "dataset_v4_a10_pilot_review_gate_receipt_v1",
        "receipt_id": "dataset-v4-a10-pilot-review-gate-v1",
        "status": (
            "A10_PILOT_REVIEW_GATE_WIRED_REVIEW_NOT_EXECUTED_TEXT_FREE_NO_PASSED_PILOT_CLAIM"
            if not gate["pilot_review_slice_ready"]
            else "PILOT_REVIEW_PASSED"
        ),
        "text_free": True,
        "controlling_outcome_sha256": V4_SHA256,
        "control_surfaces": {"public_control_issue": 7423, "pilot_child_issue": 7430, "private_operational_board": 622},
        "bindings": {
            "a2_source_operation_admission": {
                "path": str(A2_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A2_RECEIPT_PATH),
                "schema_version": "dataset_v4_a2_source_operation_admission_receipt_v1",
            },
            "a4_deterministic_extraction": {
                "path": str(A4_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A4_RECEIPT_PATH),
                "schema_version": "dataset_v4_a4_deterministic_extraction_receipt_v1",
            },
            "a5_evidence_enrichment": {
                "path": str(A5_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A5_RECEIPT_PATH),
                "schema_version": "dataset_v4_a5_evidence_enrichment_receipt_v1",
            },
            "a6_blind_arena": {
                "path": str(A6_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A6_RECEIPT_PATH),
                "schema_version": "dataset_v4_a6_blind_arena_receipt_v1",
            },
            "a7_original_row_factory": {
                "path": str(A7_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A7_RECEIPT_PATH),
                "schema_version": "dataset_v4_a7_original_row_factory_receipt_v1",
            },
            "a8_admission_assembly": {
                "path": str(A8_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A8_RECEIPT_PATH),
                "schema_version": "dataset_v4_a8_admission_assembly_receipt_v1",
            },
            "a9_evaluation_package": {
                "path": str(A9_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A9_RECEIPT_PATH),
                "schema_version": "dataset_v4_a9_evaluation_package_receipt_v1",
            },
            "pilot_slot_manifest": {
                "path": str(SLOT_MANIFEST_PATH.relative_to(root)),
                "sha256": sha256_file(SLOT_MANIFEST_PATH),
                "schema_version": "dataset_v4_pilot_slot_manifest_v1",
            },
            "wiring_implementation": {
                "path": str(SELF_PATH.relative_to(root)),
                "sha256": sha256_file(SELF_PATH),
                "schema_version": "v4_a10_pilot_review_gate_script_v1",
            },
        },
        "role_map": manifest["role_ownership"],
        "frozen_slot_denominator": {"total_slots": len(frozen_slot_ids), "strata": strata},
        "review_gate": {
            "gate_id": gate["gate_id"],
            "requires": [
                "a9_receipt_independently_valid",
                "a2_rights_fully_resolved",
                "all_frozen_slots_assigned",
                "upstream_a9_evaluation_slice_ready",
                "independent_review_recorded",
            ],
            "a9_receipt_valid": gate["a9_receipt_valid"],
            "a2_rights_resolved": gate["a2_rights_resolved"],
            "all_slots_assigned": gate["all_slots_assigned"],
            "upstream_evaluation_slice_ready": gate["upstream_evaluation_slice_ready"],
            "independent_review_recorded": gate["independent_review_recorded"],
            "pilot_review_slice_ready": gate["pilot_review_slice_ready"],
            "owner_role": gate["owner_role"],
            "blocked_reason_code": gate["blocked_reason_code"],
        },
        "review_packet": review_packet,
        "a2_residuals_carried_forward": a2_residuals_carried,
        "a4_residuals_carried_forward": a4_residuals_carried,
        "a5_residuals_carried_forward": a5_residuals_carried,
        "a6_residuals_carried_forward": a6_residuals_carried,
        "a7_residuals_carried_forward": a7_residuals_carried,
        "a8_residuals_carried_forward": a8_residuals_carried,
        "a9_residuals_carried_forward": a9_residuals_carried,
        "a10_residuals": a10_residuals,
        "review_readiness_view": review_readiness_view,
        "execution_counters": {
            "dataset_rows_emitted": 0,
            "rows_reviewed": rows_reviewed,
            "rows_admitted_and_eligible_for_review": rows_admitted,
            "frozen_slot_count": len(frozen_slot_ids),
            "slots_review_ready": len(frozen_slot_ids) if gate["pilot_review_slice_ready"] else 0,
            "slots_blocked": 0 if gate["pilot_review_slice_ready"] else len(frozen_slot_ids),
        },
        "eligibility": dict(PILOT_REVIEW_ELIGIBILITY),
        "safety_assertions": {
            "rows_not_admitted": True,
            "text_emitted": False,
            "source_text_loaded_into_model": False,
            "corpus_refetched": False,
            "held_out_membership_referenced": False,
            "held_out_membership_opened": False,
            "gold_created": False,
            "live_model_inference_over_corpus": False,
            "construction_altered_after_exposure": False,
            "training_ready_silver_claimed": False,
            "arena_slice_ready_claimed": False,
            "admitted_slice_ready_claimed": False,
            "eval_artifact_ready_claimed": False,
            "pilot_review_passed_claimed": False,
            "self_review_occurred": False,
            "review_executed_against_missing_or_empty_row": False,
            "contract_gate_waived": False,
            "privacy_gate_waived": False,
            "a4_private_ledger_loaded": False,
            "mac_corpus_copy_created": False,
            "epic_done_claimed": False,
            "heldout_family_identity_leaked": False,
        },
    }


# --- receipt verification ---------------------------------------------------


def _load_schema() -> dict[str, Any]:
    schema = _load(A10_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return schema


def validate_receipt_schema(receipt: dict[str, Any]) -> None:
    errors = sorted(Draft202012Validator(_load_schema()).iter_errors(receipt), key=lambda e: list(e.path))
    require(not errors, f"receipt fails schema validation: {errors[0].message}" if errors else "")


def validate_bindings_hash_to_disk(receipt: dict[str, Any], root: Path) -> None:
    for name, binding in receipt["bindings"].items():
        bound_path = (root / binding["path"]).resolve()
        require(
            root.resolve() in bound_path.parents or bound_path == root.resolve(),
            f"binding {name!r} path escapes the repository root -- refusing: {binding['path']}",
        )
        require(bound_path.is_file(), f"binding {name!r} does not point at a file: {bound_path}")
        actual = sha256_file(bound_path)
        require(
            actual == binding["sha256"],
            f"binding {name!r} on-disk sha256 ({actual}) does not match the receipt's declared sha256 "
            f"({binding['sha256']}) for {binding['path']} -- refusing",
        )


def validate_gate_matches_receipt(receipt: dict[str, Any], root: Path) -> None:
    gate = check_pilot_review_gate(root)
    declared = receipt["review_gate"]
    require(
        declared["a9_receipt_valid"] == gate["a9_receipt_valid"]
        and declared["a2_rights_resolved"] == gate["a2_rights_resolved"]
        and declared["all_slots_assigned"] == gate["all_slots_assigned"]
        and declared["upstream_evaluation_slice_ready"] == gate["upstream_evaluation_slice_ready"]
        and declared["independent_review_recorded"] == gate["independent_review_recorded"]
        and declared["pilot_review_slice_ready"] == gate["pilot_review_slice_ready"]
        and declared["blocked_reason_code"] == gate["blocked_reason_code"],
        "receipt review_gate does not match the state independently re-derived from the live public artifacts "
        "-- refusing (re-verify/regenerate required)",
    )
    require(
        gate["pilot_review_slice_ready"] or receipt["status"] != "PILOT_REVIEW_PASSED",
        "receipt claims PILOT_REVIEW_PASSED while the independently re-derived gate is closed -- refusing",
    )
    require(
        declared["independent_review_recorded"] is False,
        "receipt review_gate claims a review was recorded, but no execution mechanism exists -- refusing",
    )


def validate_frozen_slot_denominator(receipt: dict[str, Any], root: Path) -> None:
    manifest = _load(SLOT_MANIFEST_PATH)
    expected_strata = a9.a8.a7.a6.frozen_slot_strata(manifest)
    declared = receipt["frozen_slot_denominator"]
    require(
        declared["strata"] == expected_strata,
        "frozen_slot_denominator.strata does not reproduce from the live slot manifest -- refusing",
    )
    all_ids = [slot_id for stratum in expected_strata for slot_id in stratum["slot_ids"]]
    require(
        len(all_ids) == 100 and len(set(all_ids)) == 100,
        "frozen slot denominator did not expand to exactly 100 unique slot IDs -- refusing",
    )
    require(declared["total_slots"] == 100, "frozen_slot_denominator.total_slots is not 100 -- refusing")


def validate_review_packet(receipt: dict[str, Any]) -> None:
    """The review packet is a fixed contract, never a live computation --
    requires byte-identical equality with the module-level constant, proving
    it was never weakened (or strengthened into a false claim) per receipt."""
    require(
        receipt["review_packet"] == REVIEW_PACKET_REQUIREMENTS,
        "review_packet does not equal the frozen review-packet contract -- refusing",
    )


def validate_residuals_and_review_view(receipt: dict[str, Any], root: Path) -> None:
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)
    a5_receipt = _load(A5_RECEIPT_PATH)
    a6_receipt = _load(A6_RECEIPT_PATH)
    a7_receipt = _load(A7_RECEIPT_PATH)
    a8_receipt = _load(A8_RECEIPT_PATH)
    a9_receipt = _load(A9_RECEIPT_PATH)
    manifest = _load(SLOT_MANIFEST_PATH)
    gate = check_pilot_review_gate(root)

    for stage, source_ids, carried in (
        ("A2", {e["residual_id"] for e in a2_receipt["residuals"]}, receipt["a2_residuals_carried_forward"]),
        ("A4", {e["residual_id"] for e in a4_receipt["a4_residuals"]}, receipt["a4_residuals_carried_forward"]),
        ("A5", {e["residual_id"] for e in a5_receipt["a5_residuals"]}, receipt["a5_residuals_carried_forward"]),
        ("A6", {e["residual_id"] for e in a6_receipt["a6_residuals"]}, receipt["a6_residuals_carried_forward"]),
        ("A7", {e["residual_id"] for e in a7_receipt["a7_residuals"]}, receipt["a7_residuals_carried_forward"]),
        ("A8", {e["residual_id"] for e in a8_receipt["a8_residuals"]}, receipt["a8_residuals_carried_forward"]),
        ("A9", {e["residual_id"] for e in a9_receipt["a9_residuals"]}, receipt["a9_residuals_carried_forward"]),
    ):
        carried_ids = {entry["residual_id"] for entry in carried}
        require(
            carried_ids == source_ids,
            f"{stage.lower()}_residuals_carried_forward does not reproduce from {stage} -- refusing",
        )
        for entry in carried:
            require(
                entry["origin_stage"] == stage and entry["status"] == "unresolved_carried_to_a10",
                f"{stage.lower()}_residuals_carried_forward entry has an unexpected origin_stage/status -- refusing",
            )

    expected_a10_residuals = derive_a10_slot_residuals(manifest, a2_receipt, gate)
    require(
        receipt["a10_residuals"] == expected_a10_residuals,
        "a10_residuals does not reproduce from the live slot manifest, A2 receipt, and gate -- refusing",
    )

    expected_view = build_review_readiness_view(manifest, a9_receipt, expected_a10_residuals)
    require(
        receipt["review_readiness_view"] == expected_view,
        "review_readiness_view does not reproduce from the live A9 receipt and a10_residuals -- refusing",
    )
    require(
        all(
            entry["review_executed"] is False
            and entry["reviewer_family"] is None
            and entry["cf_review_of_record_passed"] is False
            for entry in receipt["review_readiness_view"]
        ),
        "review_readiness_view claims a review executed while no review-execution mechanism exists -- refusing",
    )


def validate_no_forbidden_keys(receipt: dict[str, Any]) -> None:
    def _all_keys(value: Any) -> set[str]:
        if isinstance(value, dict):
            return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
        if isinstance(value, list):
            return set().union(*(_all_keys(item) for item in value), set())
        return set()

    leaked = _all_keys(receipt) & FORBIDDEN_KEYS
    require(not leaked, f"receipt carries forbidden key(s): {sorted(leaked)} -- refusing")

    serialized = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
    leaked_substrings = [needle for needle in FORBIDDEN_SUBSTRINGS if needle in serialized]
    require(not leaked_substrings, f"receipt carries forbidden substring(s): {leaked_substrings} -- refusing")


def validate_no_forbidden_completion_claims(receipt: dict[str, Any]) -> None:
    serialized = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
    leaked = [claim for claim in FORBIDDEN_COMPLETION_CLAIMS if claim in serialized]
    require(not leaked, f"receipt carries forbidden completion claim(s): {leaked} -- refusing")


def validate_eligibility_and_safety_all_false(receipt: dict[str, Any]) -> None:
    require(
        receipt["eligibility"] == PILOT_REVIEW_ELIGIBILITY,
        "receipt eligibility does not equal the frozen all-false pilot-review eligibility -- refusing",
    )
    safety = receipt["safety_assertions"]
    require(
        safety["rows_not_admitted"] is True
        and all(value is False for key, value in safety.items() if key != "rows_not_admitted"),
        "receipt safety_assertions does not hold the expected invariants -- refusing",
    )
    require(
        receipt["execution_counters"]["dataset_rows_emitted"] == 0,
        "receipt execution_counters.dataset_rows_emitted is not 0 -- refusing",
    )
    require(
        receipt["execution_counters"]["rows_reviewed"] == 0,
        "receipt execution_counters.rows_reviewed is not 0 -- refusing (no review-execution mechanism exists yet)",
    )


@validation_session
def validate_receipt_independently(receipt: dict[str, Any], root: Path = ROOT) -> None:
    from learn_ukrainian_v4_runtime.stage_policy import validate_stage_policy

    validate_stage_policy(receipt)
    from learn_ukrainian_v4_runtime.provenance import validate_receipt_bindings

    validate_receipt_bindings(receipt, root, validate_bindings_hash_to_disk, require)
    validate_gate_matches_receipt(receipt, root)
    validate_frozen_slot_denominator(receipt, root)
    validate_review_packet(receipt)
    validate_residuals_and_review_view(receipt, root)
    validate_no_forbidden_keys(receipt)
    validate_no_forbidden_completion_claims(receipt)
    validate_eligibility_and_safety_all_false(receipt)
    validate_receipt_schema(receipt)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--receipt",
        type=Path,
        default=A10_RECEIPT_PATH,
        help="A10 receipt JSON to verify (default: the tracked V4 A10 pilot review gate receipt).",
    )
    parser.add_argument(
        "--write-receipt", action="store_true", help="Assemble and persist a freshly computed receipt to --receipt."
    )
    args = parser.parse_args(argv)

    if args.write_receipt:
        receipt = build_receipt()
        validate_receipt_independently(receipt)
        args.receipt.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        print(canonical_json({"status": receipt["status"], "review_gate": receipt["review_gate"]}))
        return

    receipt = _load(args.receipt)
    validate_receipt_independently(receipt)
    print(canonical_json({"status": receipt["status"], "review_gate": receipt["review_gate"]}))


if __name__ == "__main__":
    try:
        main()
    except PilotReviewGateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
