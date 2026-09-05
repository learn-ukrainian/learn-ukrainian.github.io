#!/usr/bin/env python3
"""V4 A11 silver release gate: the typed silver-release receipt bound to the
merged A10 pilot review gate receipt, the frozen V4 pilot slot manifest, and
the V4 SHA.

A11 owns the *training_ready_release* role (``role_ownership.A11 ==
"training_ready_release"`` in the frozen slot manifest): the one place a
reviewed, rights-cleared, deterministically-admitted row would be released
into the pilot's silver slice. Per the manifest's own ``release_train``
(``model_agreement_admits_silver: false``, ``model_agreement_creates_gold:
false``) and ``required_gate_ids`` (``MODEL_AGREEMENT_NOT_SILVER_OR_GOLD``,
``SILVER_FIRST_STABLE_IDS``), this module must never treat a model
hypothesis, an arena vote, or model agreement as a basis for silver -- it
wires the shared, unmodified ``v4_original_row_admission`` engine's own
``MODEL_ONLY_BASES`` refusal unchanged, at the release layer too, rather than
re-deriving or weakening it. It must never claim ``TRAINING_READY_SILVER``
while A8 has admitted and A10 has reviewed zero rows, never invent coverage
for a frozen slot with no released row (a gap is a typed residual, never a
silently-renamed ``not_applicable``), and never open A3's held-out
membership file or A4's private extraction ledger.

This module never loads source text, never re-fetches corpus, and never
releases a row without both an upstream admission and an upstream passed
pilot review: its only inputs are eight already-public artifacts --

* A2's source operation admission receipt (``stratum_coverage_map`` and
  ``residuals`` -- rights/coverage state, never source text),
* A4's deterministic extraction receipt (only its own already-carried
  residuals, never A4's private ledger),
* A5's evidence enrichment receipt (already-carried residuals only),
* A6's blind arena receipt (already-carried residuals only),
* A7's original-row factory receipt (its own ``a7_residuals`` only),
* A8's admission/assembly receipt (its own ``a8_residuals`` and
  ``engine_wiring.model_only_bases_blocked`` -- the already-public proof that
  the shared admission engine still refuses a model-only basis),
* A9's evaluation package receipt (its own ``a9_residuals`` only), and
* A10's pilot review gate receipt (its own ``a10_residuals`` and
  ``review_readiness_view`` -- the direct upstream signal this module's gate
  and silver-release view build on), and
* the frozen 100-slot V4 pilot slot manifest (``slot_series`` and
  ``required_gate_ids`` -- public slot IDs and the two gate IDs this module
  owns, never a real ``source_unit_id``).

Three independent parts:

1. ``check_silver_release_gate`` -- independently re-derives, from those
   eight public artifacts alone, whether a silver release may ever be
   claimed. Right now it cannot: A10 itself reports
   ``review_gate.pilot_review_slice_ready: false`` (A8 admitted zero rows,
   so A10 has nothing reviewed), and independent of that, no release-
   execution mechanism exists yet at all -- ``silver_release_executed`` is a
   hardcoded ``False``, never derived from a file that does not exist, so
   the gate cannot open by accident even if every upstream flag flips true.
   Per the binding contract this module must *never* claim
   ``TRAINING_READY_SILVER`` while that is true; it reports
   ``silver_release_slice_ready: false`` and a typed ``blocked_reason_code``
   instead.
2. ``build_release_packet`` -- the fixed, data-independent contract every
   real future release must satisfy: deterministic admission checks passed,
   an upstream passed pilot review, and an explicit refusal of model
   agreement, arena votes, model votes, or a bare hypothesis as a basis for
   silver. The packet never varies with gate state -- it is the same
   requirement whether the gate is open or closed -- and it is never itself
   evidence that a release happened.
3. ``build_receipt`` -- assembles the public receipt: the frozen 100-slot
   denominator (reusing, never duplicating,
   ``v4_a6_blind_arena.frozen_slot_strata``/``all_frozen_slot_ids``), the
   gate, the release packet, a real (zero-row) call into the shared,
   unmodified ``v4_original_row_admission.admit_rows`` engine proving A11's
   own wiring is live rather than declarative, every
   A2/A4/A5/A6/A7/A8/A9/A10 residual carried forward unresolved, a per-slot
   silver-release view built by cross-checking A10's own
   ``review_readiness_view`` and never marking a slot released, and one
   typed per-slot A11 residual reusing A10's own already-public per-stratum
   reason codes -- never a fourth, independently invented reason.

Run with no arguments to verify the checked-in A11 receipt reproduces from
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
from learn_ukrainian_v4_runtime.stage_policy import bind_constructed_stage, current_stage_schema

_SELF_ROOT = resource_root()

from learn_ukrainian_v4_runtime import v4_a10_pilot_review_gate as a10

ROOT = _SELF_ROOT
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"

A11_RECEIPT_PATH = ADMISSION / "dataset_v4_a11_silver_release_gate_receipt_v1.json"
A11_SCHEMA_PATH = CONTRACTS / "dataset_v4_a11_silver_release_gate_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_PATH = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
A6_RECEIPT_PATH = ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json"
A7_RECEIPT_PATH = ADMISSION / "dataset_v4_a7_original_row_factory_receipt_v1.json"
A8_RECEIPT_PATH = ADMISSION / "dataset_v4_a8_admission_assembly_receipt_v1.json"
A9_RECEIPT_PATH = ADMISSION / "dataset_v4_a9_evaluation_package_receipt_v1.json"
A10_RECEIPT_PATH = ADMISSION / "dataset_v4_a10_pilot_review_gate_receipt_v1.json"
SLOT_MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"
SELF_PATH = ROOT / "scripts/projects/open_model_data/v4_a11_silver_release_gate.py"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

# The manifest's own required gate IDs for this stage -- never invented, and
# checked at gate-derivation time to still be present in the live manifest.
# A11 is the one place both are wired: MODEL_AGREEMENT_NOT_SILVER_OR_GOLD
# (this module's shared-engine wiring refuses a model-only basis) and
# SILVER_FIRST_STABLE_IDS (silver is released, if ever, under the same
# frozen v4p-* slot IDs used since A6 -- never renumbered for a later gold
# overlay).
REQUIRED_GATE_IDS = ("MODEL_AGREEMENT_NOT_SILVER_OR_GOLD", "SILVER_FIRST_STABLE_IDS")

# This module's own frozen expectation of what the shared admission engine
# must refuse as a silver basis -- checked against the live
# ``v4_original_row_admission.MODEL_ONLY_BASES`` on every gate derivation,
# never re-derived from a receipt (a receipt only proves a *past* run
# matched, not that the live engine still does).
EXPECTED_MODEL_ONLY_BASES = frozenset({"arena_vote", "model_agreement", "model_vote"})

# Mirrors v4_a10_pilot_review_gate.FORBIDDEN_KEYS exactly -- "gold" is
# deliberately excluded because it is the name of this receipt's own
# always-false eligibility flag, never a real gold label.
FORBIDDEN_KEYS = a10.FORBIDDEN_KEYS
FORBIDDEN_SUBSTRINGS = a10.FORBIDDEN_SUBSTRINGS

# Completion-vocabulary claims that belong to other roles or are unreachable
# today (see the manifest's own completion_vocabulary and A0's non_goals) --
# never emitted here. Unlike A10's own list, "PILOT_REVIEW_PASSED" (A10's
# own ready state, now a foreign claim from A11's point of view) is added
# back, and "TRAINING_READY_SILVER" (A11's own legitimate -- if currently
# unreachable -- ready state, and the manifest's own completion_vocabulary
# entry for this role) is removed, mirroring how each stage excludes only
# its own name from the borrowed forbidden-claims list.
FORBIDDEN_COMPLETION_CLAIMS = tuple(
    sorted({*a10.FORBIDDEN_COMPLETION_CLAIMS, "PILOT_REVIEW_PASSED"} - {"TRAINING_READY_SILVER"})
)

SILVER_RELEASE_ELIGIBILITY = {
    "gold": False,
    "training": False,
    "evaluation": False,
    "teaching": False,
    "coverage": False,
}

# The fixed release-packet contract. Never varies with gate state, and is
# never itself evidence that a release happened -- it is the requirement a
# real future release must satisfy, not a record that one occurred.
RELEASE_PACKET_REQUIREMENTS = {
    "gate_ids": list(REQUIRED_GATE_IDS),
    "requires_deterministic_admission_checks_passed": True,
    "requires_upstream_pilot_review_passed": True,
    "model_agreement_admits_silver": False,
    "arena_vote_admits_silver": False,
    "model_vote_admits_silver": False,
    "hypothesis_admits_silver": False,
    "silver_ids_stable_across_gold_upgrade": True,
    "gold_overlay_is_separate_later_stage": True,
    "release_may_execute_against_missing_or_empty_rows": False,
    "release_execution_state": "NOT_EXECUTED_NO_ADMITTED_ROWS",
}

canonical_json = a10.canonical_json
sha256_text = a10.sha256_text
sha256_file = a10.sha256_file


class SilverReleaseGateError(ValueError):
    """The A11 wiring or its deterministic receipt is unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SilverReleaseGateError(message)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# --- A10 reason -> A11 per-slot residual reason ------------------------------
#
# A10 already types each frozen slot's blocker as one of three reason codes
# (reused unchanged from A9's own mapping, itself from A8's, itself from
# A7's). A11 never invents a fourth -- "why has A10 nothing reviewed for
# this frozen slot" is exactly "why has A11 nothing to release as silver".
A11_NEXT_ACTION_BY_REASON = {
    "rights_unknown": (
        "no reviewed, admitted row exists to release as silver for this frozen slot until A2 resolves "
        "unit-specific training/derivation rights for its stratum's supporting source unit -- never release a "
        "placeholder row while rights remain unknown"
    ),
    "source_incomplete": (
        "no source unit is yet identified for this frozen slot's stratum, so nothing has been reviewed or "
        "admitted for A11 to release as silver -- never invent or substitute a placeholder release"
    ),
    "independence_unavailable": (
        "a supporting source unit is identified for this frozen slot's stratum but its coverage/rights review is "
        "not yet complete, so A10 has nothing reviewed and A11 has no row ready for silver release yet"
    ),
}


# --- silver release gate (public-only) ---------------------------------------


def check_silver_release_gate(root: Path = ROOT) -> dict[str, Any]:
    """Independently re-derive whether a silver release may ever be claimed,
    from the frozen slot manifest's own ``assignment_state`` per stratum,
    A2's own residuals, A8's own already-public engine wiring, and A10's
    independent validity -- never trusting the A11 receipt's own declared
    fields, never opening ``batch_state/``. ``silver_release_slice_ready`` is
    only ever true once every frozen slot is assigned to a real source unit
    *and* A2 has zero unresolved residuals *and* A10 itself still
    independently validates *and* A10's own pilot review gate is open *and*
    the shared admission engine's own ``MODEL_ONLY_BASES`` still matches this
    module's own frozen expectation of what a silver release must refuse
    *and* a silver release has actually been executed -- and that last
    condition has no execution mechanism yet, so it is a hardcoded
    ``False``, never derived from a file that does not exist.

    Fails closed -- a *closed gate*, not an exception -- if any of the three
    required public artifacts (slot manifest, A2 receipt, A10 receipt) is
    missing, mirroring
    ``v4_a10_pilot_review_gate.check_pilot_review_gate``'s own
    missing-artifact handling."""
    manifest_path = (root / "data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json").resolve()
    a2_path = (
        root / "data/projects/open_model_data/admission/dataset_v4_a2_source_operation_admission_receipt_v1.json"
    ).resolve()
    a10_path = (
        root / "data/projects/open_model_data/admission/dataset_v4_a10_pilot_review_gate_receipt_v1.json"
    ).resolve()
    required_paths = {"slot_manifest": manifest_path, "a2_receipt": a2_path, "a10_receipt": a10_path}
    for label, path in required_paths.items():
        require(root.resolve() in path.parents, f"{label} path escapes the repository root -- refusing")

    missing = sorted(label for label, path in required_paths.items() if not path.is_file())
    if missing:
        return {
            "gate_id": "v4-a11-silver-release-gate-v1",
            "a10_receipt_valid": False,
            "model_agreement_exclusion_confirmed": False,
            "a2_rights_resolved": False,
            "all_slots_assigned": False,
            "upstream_pilot_review_passed": False,
            "silver_release_executed": False,
            "silver_release_slice_ready": False,
            "owner_role": "A2_A3_PRIVATE_ARTIFACT",
            "blocked_reason_code": f"required_public_artifact_missing:{missing[0]}",
        }

    manifest = _load(manifest_path)
    require(
        manifest.get("controlling_outcome_sha256") == V4_SHA256,
        "slot manifest is not bound to the expected V4 controlling outcome -- refusing",
    )
    for gate_id in REQUIRED_GATE_IDS:
        require(
            gate_id in manifest.get("required_gate_ids", []),
            f"slot manifest no longer lists this stage's required gate ID {gate_id!r} -- refusing",
        )

    a2_receipt = _load(a2_path)
    require(
        a2_receipt.get("controlling_outcome_sha256") == V4_SHA256,
        "A2 receipt is not bound to the expected V4 controlling outcome -- refusing",
    )
    rights_resolved = len(a2_receipt.get("residuals", [])) == 0

    all_assigned = all(series["assignment_state"] == "ASSIGNED" for series in manifest["slot_series"])

    # A pure, receipt-independent structural check: the shared engine's own
    # MODEL_ONLY_BASES must still equal this module's frozen expectation of
    # what a silver release must refuse. Never derived from a receipt file
    # (which would only prove some *past* run matched, not the live engine),
    # and never a superset/subset substitute -- exact equality only.
    model_agreement_exclusion_confirmed = a10.a9.a8.admission.MODEL_ONLY_BASES == EXPECTED_MODEL_ONLY_BASES

    a10_receipt = _load(a10_path)
    try:
        a10.validate_receipt_independently(a10_receipt, root)
        a10_valid = True
    except a10.PilotReviewGateError:
        a10_valid = False

    upstream_pilot_review_passed = a10_valid and a10_receipt["review_gate"]["pilot_review_slice_ready"] is True

    # No release-execution mechanism exists yet -- this can never be derived
    # true from any file on disk today, so it stays a hardcoded False rather
    # than an independently-computed flag that could accidentally flip.
    silver_release_executed = False

    silver_release_slice_ready = (
        rights_resolved
        and all_assigned
        and a10_valid
        and model_agreement_exclusion_confirmed
        and upstream_pilot_review_passed
        and silver_release_executed
    )
    blocked_reason_code = None
    if not silver_release_slice_ready:
        # Checked before a10_valid: a live engine drift makes A8's/A9's/
        # A10's own nested engine-wiring checks fail too (same shared module
        # object), so the more specific, more upstream cause is reported
        # first rather than the derived "a10_receipt_invalid" symptom.
        if not model_agreement_exclusion_confirmed:
            blocked_reason_code = "model_agreement_exclusion_engine_drifted"
        elif not a10_valid:
            blocked_reason_code = "a10_receipt_invalid"
        elif not rights_resolved and not all_assigned:
            blocked_reason_code = "rights_unresolved_and_slots_unassigned"
        elif not rights_resolved:
            blocked_reason_code = "rights_unresolved"
        elif not all_assigned:
            blocked_reason_code = "slot_assignment_pending_a2_a3"
        elif not upstream_pilot_review_passed:
            blocked_reason_code = f"upstream_a10_blocked:{a10_receipt['review_gate']['blocked_reason_code']}"
        else:
            blocked_reason_code = "silver_release_not_yet_executed_no_admitted_rows"

    return {
        "gate_id": "v4-a11-silver-release-gate-v1",
        "a10_receipt_valid": a10_valid,
        "model_agreement_exclusion_confirmed": model_agreement_exclusion_confirmed,
        "a2_rights_resolved": rights_resolved,
        "all_slots_assigned": all_assigned,
        "upstream_pilot_review_passed": upstream_pilot_review_passed,
        "silver_release_executed": silver_release_executed,
        "silver_release_slice_ready": silver_release_slice_ready,
        "owner_role": manifest["sealed_heldout_commitment"]["assignment_owner"],
        "blocked_reason_code": blocked_reason_code,
    }


# --- A11's own per-slot residuals (public, source-free) ----------------------


def derive_a11_slot_residuals(
    manifest: dict[str, Any], a2_receipt: dict[str, Any], gate: dict[str, Any]
) -> list[dict[str, Any]]:
    """One typed residual per frozen public slot ID -- never a silently
    dropped slot and never a silver release invented in place of the missing
    reviewed row. A pure function of the manifest's own ``slot_series``,
    A10's own already-public per-stratum reason codes, and the gate this
    module itself re-derives; never opens any private state."""
    owner_role = gate["owner_role"]
    reasons_by_stratum = a10.a9.a8.a7.stratum_reason_codes(a2_receipt)
    residuals = []
    for stratum_entry in a10.a9.a8.a7.a6.frozen_slot_strata(manifest):
        stratum = stratum_entry["stratum"]
        reason_code = reasons_by_stratum[stratum]
        for slot_id in stratum_entry["slot_ids"]:
            residuals.append(
                {
                    "residual_id": f"a11-residual-{reason_code.replace('_', '-')}-{slot_id}",
                    "subject_kind": "pilot_slot",
                    "subject_id": slot_id,
                    "stage": "A11",
                    "reason_code": reason_code,
                    "owner_role": owner_role,
                    "next_action": A11_NEXT_ACTION_BY_REASON[reason_code],
                    "retryability": "retryable",
                    "evidence_refs": [
                        "admission.dataset_v4_pilot_slot_manifest_v1.slot_series",
                        "admission.dataset_v4_a2_source_operation_admission_receipt_v1.stratum_coverage_map",
                        "admission.dataset_v4_a10_pilot_review_gate_receipt_v1.a10_residuals",
                    ],
                }
            )
    residuals.sort(key=lambda residual: residual["subject_id"])
    return residuals


# --- silver release view (public, fail-closed, never executes a release) ----


def build_silver_release_view(
    manifest: dict[str, Any], a10_receipt: dict[str, Any], a11_residuals: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Reproduce, per frozen slot, exactly what a silver release would see --
    and fail closed if A10's own ``review_readiness_view`` ever claims a
    slot's review passed without an admitted row. Never marks a slot
    released: ``release_executed`` is unconditionally ``False`` because this
    module has no execution mechanism and must never release a missing,
    unreviewed, or model-agreement-only row as silver."""
    residual_by_slot = {residual["subject_id"]: residual["residual_id"] for residual in a11_residuals}
    expected_slot_ids = set(a10.a9.a8.a7.a6.all_frozen_slot_ids(manifest))
    seen_slot_ids = {entry["slot_id"] for entry in a10_receipt["review_readiness_view"]}
    require(
        seen_slot_ids == expected_slot_ids,
        "A10 review_readiness_view does not cover exactly the frozen slot manifest -- refusing silver release view",
    )

    view = []
    for entry in a10_receipt["review_readiness_view"]:
        slot_id = entry["slot_id"]
        row_admitted = entry["row_admitted"]
        pilot_review_passed = entry["cf_review_of_record_passed"]
        require(
            pilot_review_passed is False or row_admitted is True,
            f"A10 review_readiness_view claims pilot review passed for slot {slot_id!r} without an admitted row "
            "-- refusing (cannot release a nonexistent row as silver)",
        )
        view.append(
            {
                "slot_id": slot_id,
                "row_admitted": row_admitted,
                "pilot_review_passed": pilot_review_passed,
                "release_required": True,
                "release_executed": False,
                "label_tier": None,
                "residual_id": residual_by_slot[slot_id],
            }
        )
    view.sort(key=lambda entry: entry["slot_id"])
    return view


# --- release packet (fixed, data-independent contract) -----------------------


def build_release_packet() -> dict[str, Any]:
    """The fixed release-packet contract every real future silver release
    must satisfy. Never varies with gate state and never itself claims a
    release happened -- returns a fresh copy of the frozen
    ``RELEASE_PACKET_REQUIREMENTS`` so callers cannot mutate the
    module-level constant."""
    return dict(RELEASE_PACKET_REQUIREMENTS)


# --- shared engine wiring (real call, zero rows today) ------------------------


def run_engine_admission_check(rows: list[dict[str, Any]] = ()) -> dict[str, Any]:  # type: ignore[assignment]
    """A real (never stubbed) call into the shared, already-on-main
    ``v4_original_row_admission.admit_rows`` engine, bound to the V4
    controlling outcome. A8 admitted zero rows, so there is nothing for A11
    to release; ``rows`` stays empty and the engine's own counters
    (``admitted_rows``, ``rejected_rows``) both come back 0 -- proving A11's
    own wiring into the unmodified, fail-closed admission engine (the one
    place a model-agreement-only row is refused) is live at the release
    layer too, never fabricating a row to exercise it."""
    return a10.a9.a8.admission.admit_rows(outcome_sha256=V4_SHA256, rows=list(rows))


# --- receipt assembly --------------------------------------------------------


@bind_constructed_stage
def build_receipt(root: Path = ROOT) -> dict[str, Any]:
    manifest = _load(SLOT_MANIFEST_PATH)
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)
    a5_receipt = _load(A5_RECEIPT_PATH)
    a6_receipt = _load(A6_RECEIPT_PATH)
    a7_receipt = _load(A7_RECEIPT_PATH)
    a8_receipt = _load(A8_RECEIPT_PATH)
    a9_receipt = _load(A9_RECEIPT_PATH)
    a10_receipt = _load(A10_RECEIPT_PATH)
    gate = check_silver_release_gate(root)

    strata = a10.a9.a8.a7.a6.frozen_slot_strata(manifest)
    frozen_slot_ids = a10.a9.a8.a7.a6.all_frozen_slot_ids(manifest)

    a2_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A2", "status": "unresolved_carried_to_a11"}
        for entry in a2_receipt["residuals"]
    ]
    a4_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A4", "status": "unresolved_carried_to_a11"}
        for entry in a4_receipt["a4_residuals"]
    ]
    a5_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A5", "status": "unresolved_carried_to_a11"}
        for entry in a5_receipt["a5_residuals"]
    ]
    a6_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A6", "status": "unresolved_carried_to_a11"}
        for entry in a6_receipt["a6_residuals"]
    ]
    a7_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A7", "status": "unresolved_carried_to_a11"}
        for entry in a7_receipt["a7_residuals"]
    ]
    a8_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A8", "status": "unresolved_carried_to_a11"}
        for entry in a8_receipt["a8_residuals"]
    ]
    a9_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A9", "status": "unresolved_carried_to_a11"}
        for entry in a9_receipt["a9_residuals"]
    ]
    a10_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A10", "status": "unresolved_carried_to_a11"}
        for entry in a10_receipt["a10_residuals"]
    ]

    engine_admission_receipt = run_engine_admission_check([])
    a11_residuals = derive_a11_slot_residuals(manifest, a2_receipt, gate)
    silver_release_view = build_silver_release_view(manifest, a10_receipt, a11_residuals)
    release_packet = build_release_packet()

    rows_released = sum(1 for entry in silver_release_view if entry["release_executed"])
    rows_admitted = sum(1 for entry in silver_release_view if entry["row_admitted"])

    return {
        "schema_version": "dataset_v4_a11_silver_release_gate_receipt_v1",
        "receipt_id": "dataset-v4-a11-silver-release-gate-v1",
        "status": (
            "A11_SILVER_RELEASE_GATE_WIRED_RELEASE_NOT_EXECUTED_TEXT_FREE_NO_SILVER_RELEASE_READY_CLAIM"
            if not gate["silver_release_slice_ready"]
            else "TRAINING_READY_SILVER"
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
            "a10_pilot_review_gate": {
                "path": str(A10_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A10_RECEIPT_PATH),
                "schema_version": "dataset_v4_a10_pilot_review_gate_receipt_v1",
            },
            "pilot_slot_manifest": {
                "path": str(SLOT_MANIFEST_PATH.relative_to(root)),
                "sha256": sha256_file(SLOT_MANIFEST_PATH),
                "schema_version": "dataset_v4_pilot_slot_manifest_v1",
            },
            "admission_engine_implementation": {
                "path": str(a10.a9.a8.ADMISSION_ENGINE_PATH.relative_to(root)),
                "sha256": sha256_file(a10.a9.a8.ADMISSION_ENGINE_PATH),
                "schema_version": "v4_original_row_admission_script_v1",
            },
            "wiring_implementation": {
                "path": str(SELF_PATH.relative_to(root)),
                "sha256": sha256_file(SELF_PATH),
                "schema_version": "v4_a11_silver_release_gate_script_v1",
            },
        },
        "role_map": manifest["role_ownership"],
        "frozen_slot_denominator": {"total_slots": len(frozen_slot_ids), "strata": strata},
        "release_gate": {
            "gate_id": gate["gate_id"],
            "requires": [
                "a10_receipt_independently_valid",
                "model_agreement_exclusion_confirmed",
                "a2_rights_fully_resolved",
                "all_frozen_slots_assigned",
                "upstream_a10_pilot_review_passed",
                "silver_release_executed",
            ],
            "a10_receipt_valid": gate["a10_receipt_valid"],
            "model_agreement_exclusion_confirmed": gate["model_agreement_exclusion_confirmed"],
            "a2_rights_resolved": gate["a2_rights_resolved"],
            "all_slots_assigned": gate["all_slots_assigned"],
            "upstream_pilot_review_passed": gate["upstream_pilot_review_passed"],
            "silver_release_executed": gate["silver_release_executed"],
            "silver_release_slice_ready": gate["silver_release_slice_ready"],
            "owner_role": gate["owner_role"],
            "blocked_reason_code": gate["blocked_reason_code"],
        },
        "release_packet": release_packet,
        "engine_wiring": {
            "engine_schema_version": a10.a9.a8.admission.SCHEMA_VERSION,
            "engine_input_schema_version": a10.a9.a8.admission.INPUT_SCHEMA_VERSION,
            "model_only_bases_blocked": sorted(a10.a9.a8.admission.MODEL_ONLY_BASES),
            "admission_receipt": engine_admission_receipt,
        },
        "a2_residuals_carried_forward": a2_residuals_carried,
        "a4_residuals_carried_forward": a4_residuals_carried,
        "a5_residuals_carried_forward": a5_residuals_carried,
        "a6_residuals_carried_forward": a6_residuals_carried,
        "a7_residuals_carried_forward": a7_residuals_carried,
        "a8_residuals_carried_forward": a8_residuals_carried,
        "a9_residuals_carried_forward": a9_residuals_carried,
        "a10_residuals_carried_forward": a10_residuals_carried,
        "a11_residuals": a11_residuals,
        "silver_release_view": silver_release_view,
        "execution_counters": {
            "dataset_rows_emitted": 0,
            "rows_released_as_silver": rows_released,
            "rows_admitted_and_eligible_for_release": rows_admitted,
            "frozen_slot_count": len(frozen_slot_ids),
            "slots_release_ready": len(frozen_slot_ids) if gate["silver_release_slice_ready"] else 0,
            "slots_blocked": 0 if gate["silver_release_slice_ready"] else len(frozen_slot_ids),
        },
        "eligibility": dict(SILVER_RELEASE_ELIGIBILITY),
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
            "model_agreement_admitted_silver": False,
            "arena_vote_admitted_silver": False,
            "hypothesis_admitted_silver": False,
            "silver_released_without_pilot_review_or_admission": False,
        },
    }


# --- receipt verification ---------------------------------------------------


def _load_schema() -> dict[str, Any]:
    schema = _load(A11_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return schema


def validate_receipt_schema(receipt: dict[str, Any]) -> None:
    errors = sorted(Draft202012Validator(current_stage_schema(_load_schema())).iter_errors(receipt), key=lambda e: list(e.path))
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
    gate = check_silver_release_gate(root)
    declared = receipt["release_gate"]
    require(
        declared["a10_receipt_valid"] == gate["a10_receipt_valid"]
        and declared["model_agreement_exclusion_confirmed"] == gate["model_agreement_exclusion_confirmed"]
        and declared["a2_rights_resolved"] == gate["a2_rights_resolved"]
        and declared["all_slots_assigned"] == gate["all_slots_assigned"]
        and declared["upstream_pilot_review_passed"] == gate["upstream_pilot_review_passed"]
        and declared["silver_release_executed"] == gate["silver_release_executed"]
        and declared["silver_release_slice_ready"] == gate["silver_release_slice_ready"]
        and declared["blocked_reason_code"] == gate["blocked_reason_code"],
        "receipt release_gate does not match the state independently re-derived from the live public artifacts "
        "-- refusing (re-verify/regenerate required)",
    )
    require(
        gate["silver_release_slice_ready"] or receipt["status"] != "TRAINING_READY_SILVER",
        "receipt claims TRAINING_READY_SILVER while the independently re-derived gate is closed -- refusing",
    )
    require(
        declared["silver_release_executed"] is False,
        "receipt release_gate claims a silver release was executed, but no execution mechanism exists -- refusing",
    )


def validate_frozen_slot_denominator(receipt: dict[str, Any], root: Path) -> None:
    manifest = _load(SLOT_MANIFEST_PATH)
    expected_strata = a10.a9.a8.a7.a6.frozen_slot_strata(manifest)
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


def validate_release_packet(receipt: dict[str, Any]) -> None:
    """The release packet is a fixed contract, never a live computation --
    requires byte-identical equality with the module-level constant, proving
    it was never weakened (or strengthened into a false claim) per receipt."""
    require(
        receipt["release_packet"] == RELEASE_PACKET_REQUIREMENTS,
        "release_packet does not equal the frozen release-packet contract -- refusing",
    )


def validate_engine_wiring(receipt: dict[str, Any]) -> None:
    """Re-runs the real shared admission engine call and requires a
    byte-identical result, plus makes the engine independently verify its
    own nested receipt (``v4_original_row_admission.verify_receipt``) --
    proving this is a live wire into the on-main engine at the release layer
    too, not a declared/stubbed shape, and that the model-only-basis refusal
    ``MODEL_ONLY_BASES`` still matches what this receipt declares."""
    wiring = receipt["engine_wiring"]
    admission = a10.a9.a8.admission
    require(
        wiring["engine_schema_version"] == admission.SCHEMA_VERSION
        and wiring["engine_input_schema_version"] == admission.INPUT_SCHEMA_VERSION,
        "engine_wiring schema versions do not match the live v4_original_row_admission module -- refusing (engine changed without regenerating this receipt)",
    )
    require(
        wiring["model_only_bases_blocked"] == sorted(admission.MODEL_ONLY_BASES),
        "engine_wiring.model_only_bases_blocked does not match the live engine's MODEL_ONLY_BASES -- refusing",
    )
    recomputed = admission.admit_rows(outcome_sha256=V4_SHA256, rows=[])
    require(
        wiring["admission_receipt"] == recomputed,
        "engine_wiring.admission_receipt does not reproduce from a live, zero-row v4_original_row_admission.admit_rows call -- refusing",
    )
    admission.verify_receipt(wiring["admission_receipt"])
    require(
        wiring["admission_receipt"]["counts"] == {"input_rows": 0, "admitted_rows": 0, "rejected_rows": 0},
        "engine_wiring.admission_receipt does not report zero rows -- refusing (no rights-cleared row exists yet; "
        "dataset_rows_emitted must stay 0)",
    )


def validate_residuals_and_silver_view(receipt: dict[str, Any], root: Path) -> None:
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)
    a5_receipt = _load(A5_RECEIPT_PATH)
    a6_receipt = _load(A6_RECEIPT_PATH)
    a7_receipt = _load(A7_RECEIPT_PATH)
    a8_receipt = _load(A8_RECEIPT_PATH)
    a9_receipt = _load(A9_RECEIPT_PATH)
    a10_receipt = _load(A10_RECEIPT_PATH)
    manifest = _load(SLOT_MANIFEST_PATH)
    gate = check_silver_release_gate(root)

    for stage, source_ids, carried in (
        ("A2", {e["residual_id"] for e in a2_receipt["residuals"]}, receipt["a2_residuals_carried_forward"]),
        ("A4", {e["residual_id"] for e in a4_receipt["a4_residuals"]}, receipt["a4_residuals_carried_forward"]),
        ("A5", {e["residual_id"] for e in a5_receipt["a5_residuals"]}, receipt["a5_residuals_carried_forward"]),
        ("A6", {e["residual_id"] for e in a6_receipt["a6_residuals"]}, receipt["a6_residuals_carried_forward"]),
        ("A7", {e["residual_id"] for e in a7_receipt["a7_residuals"]}, receipt["a7_residuals_carried_forward"]),
        ("A8", {e["residual_id"] for e in a8_receipt["a8_residuals"]}, receipt["a8_residuals_carried_forward"]),
        ("A9", {e["residual_id"] for e in a9_receipt["a9_residuals"]}, receipt["a9_residuals_carried_forward"]),
        ("A10", {e["residual_id"] for e in a10_receipt["a10_residuals"]}, receipt["a10_residuals_carried_forward"]),
    ):
        carried_ids = {entry["residual_id"] for entry in carried}
        require(
            carried_ids == source_ids,
            f"{stage.lower()}_residuals_carried_forward does not reproduce from {stage} -- refusing",
        )
        for entry in carried:
            require(
                entry["origin_stage"] == stage and entry["status"] == "unresolved_carried_to_a11",
                f"{stage.lower()}_residuals_carried_forward entry has an unexpected origin_stage/status -- refusing",
            )

    expected_a11_residuals = derive_a11_slot_residuals(manifest, a2_receipt, gate)
    require(
        receipt["a11_residuals"] == expected_a11_residuals,
        "a11_residuals does not reproduce from the live slot manifest, A2 receipt, and gate -- refusing",
    )

    expected_view = build_silver_release_view(manifest, a10_receipt, expected_a11_residuals)
    require(
        receipt["silver_release_view"] == expected_view,
        "silver_release_view does not reproduce from the live A10 receipt and a11_residuals -- refusing",
    )
    require(
        all(
            entry["release_executed"] is False
            and entry["label_tier"] is None
            and entry["row_admitted"] is False
            and entry["pilot_review_passed"] is False
            for entry in receipt["silver_release_view"]
        ),
        "silver_release_view claims a row was released, admitted, or reviewed while none exists -- refusing",
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
        receipt["eligibility"] == SILVER_RELEASE_ELIGIBILITY,
        "receipt eligibility does not equal the frozen all-false silver-release eligibility -- refusing",
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
        receipt["execution_counters"]["rows_released_as_silver"] == 0,
        "receipt execution_counters.rows_released_as_silver is not 0 -- refusing (no release-execution mechanism exists yet)",
    )


@validation_session
def validate_receipt_independently(receipt: dict[str, Any], root: Path = ROOT) -> None:
    from learn_ukrainian_v4_runtime.stage_policy import validate_stage_policy

    validate_stage_policy(receipt)
    from learn_ukrainian_v4_runtime.provenance import validate_receipt_bindings

    validate_receipt_bindings(receipt, root, validate_bindings_hash_to_disk, require)
    validate_gate_matches_receipt(receipt, root)
    validate_frozen_slot_denominator(receipt, root)
    validate_release_packet(receipt)
    validate_engine_wiring(receipt)
    validate_residuals_and_silver_view(receipt, root)
    validate_no_forbidden_keys(receipt)
    validate_no_forbidden_completion_claims(receipt)
    validate_eligibility_and_safety_all_false(receipt)
    validate_receipt_schema(receipt)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--receipt",
        type=Path,
        default=A11_RECEIPT_PATH,
        help="A11 receipt JSON to verify (default: the tracked V4 A11 silver release gate receipt).",
    )
    parser.add_argument(
        "--write-receipt", action="store_true", help="Assemble and persist a freshly computed receipt to --receipt."
    )
    args = parser.parse_args(argv)

    if args.write_receipt:
        receipt = build_receipt()
        validate_receipt_independently(receipt)
        args.receipt.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        print(canonical_json({"status": receipt["status"], "release_gate": receipt["release_gate"]}))
        return

    receipt = _load(args.receipt)
    validate_receipt_independently(receipt)
    print(canonical_json({"status": receipt["status"], "release_gate": receipt["release_gate"]}))


if __name__ == "__main__":
    try:
        main()
    except SilverReleaseGateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
