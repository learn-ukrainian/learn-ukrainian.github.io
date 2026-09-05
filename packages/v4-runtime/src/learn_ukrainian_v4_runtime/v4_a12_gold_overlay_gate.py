#!/usr/bin/env python3
"""V4 A12 later gold-overlay path: the typed gold-overlay eligibility receipt
bound to the merged A11 silver release gate receipt, the frozen V4 pilot slot
manifest, and the V4 SHA.

A12 owns the *later_gold_overlay* role (``role_ownership.A12 ==
"later_gold_overlay"`` in the frozen slot manifest): the one place a
source-qualified human adjudication overlay would ever be applied on top of
an already-released, stable silver row ID. Gold is never inferred from model
agreement, an arena vote, a model vote, or a bare hypothesis, and it is never
self-adjudicated. Per the manifest's own ``release_train``
(``initial: "silver"``, ``later_overlay: "gold"``, ``model_agreement_creates_
gold: false``) and ``required_gate_ids`` (``MODEL_AGREEMENT_NOT_SILVER_OR_
GOLD``, ``SILVER_FIRST_STABLE_IDS``), this module must never claim
``TRAINING_READY_GOLD_SUBSET`` -- A11 released zero silver rows, so there is
nothing to overlay -- and may only ever describe ``GOLD_UPGRADE_READY`` as a
bounded overlay *plan*, never as proof that a gold row already exists. It
must never open A3's held-out membership file or A4's private extraction
ledger, and it must never load source text.

This module never loads source text, never re-fetches corpus, and never
overlays a gold label onto a missing, unreleased, or model-agreement-only
row: its only inputs are nine already-public artifacts --

* A2's source operation admission receipt (``stratum_coverage_map`` and
  ``residuals`` -- rights/coverage state, never source text),
* A4's deterministic extraction receipt (only its own already-carried
  residuals, never A4's private ledger),
* A5's evidence enrichment receipt (already-carried residuals only),
* A6's blind arena receipt (already-carried residuals only),
* A7's original-row factory receipt (its own ``a7_residuals`` only),
* A8's admission/assembly receipt (its own ``a8_residuals`` only),
* A9's evaluation package receipt (its own ``a9_residuals`` only),
* A10's pilot review gate receipt (its own ``a10_residuals`` only),
* A11's silver release gate receipt (its own ``a11_residuals``,
  ``silver_release_view``, and ``release_gate.silver_release_slice_ready`` --
  the direct upstream signal this module's gate and gold-overlay view build
  on; a gold overlay can never apply before a silver row exists), and
* the frozen 100-slot V4 pilot slot manifest (``slot_series`` and
  ``required_gate_ids`` -- public slot IDs and the two gate IDs this module
  owns, never a real ``source_unit_id``).

Three independent parts:

1. ``check_gold_overlay_gate`` -- independently re-derives, from those nine
   public artifacts alone, whether a gold overlay may ever be claimed ready.
   Right now it cannot: A11 itself reports
   ``release_gate.silver_release_slice_ready: false`` (A8 admitted zero rows,
   so A11 has released nothing as silver, so there is no stable silver row ID
   to overlay), and independent of that, no overlay-execution mechanism
   exists yet at all -- ``gold_overlay_executed`` is a hardcoded ``False``,
   never derived from a file that does not exist, so the gate cannot open by
   accident even if every upstream flag flips true. Per the binding contract
   this module must *never* claim ``TRAINING_READY_GOLD_SUBSET``; it reports
   ``gold_overlay_slice_ready: false`` and a typed ``blocked_reason_code``
   instead.
2. ``build_overlay_packet`` -- the fixed, data-independent contract every
   real future gold overlay must satisfy: an already-released silver row, a
   source-qualified human adjudicator, an overlay bound to the row's already-
   stable silver ID (never a renumbered ID), and an explicit refusal of
   model agreement, arena votes, model votes, self-adjudication, or a bare
   hypothesis as a basis for gold. The packet never varies with gate state --
   it is the same requirement whether the gate is open or closed -- and it is
   never itself evidence that an overlay happened.
3. ``build_receipt`` -- assembles the public receipt: the frozen 100-slot
   denominator (reusing, never duplicating,
   ``v4_a6_blind_arena.frozen_slot_strata``/``all_frozen_slot_ids``), the
   gate, the overlay packet, the always-quarantined model-agreement status, a
   real (zero-row) call into the shared, unmodified
   ``v4_original_row_admission.admit_rows`` engine proving A12's own wiring
   is live rather than declarative, every
   A2/A4/A5/A6/A7/A8/A9/A10/A11 residual carried forward unresolved, a
   per-slot gold-overlay view built by cross-checking A11's own
   ``silver_release_view`` and never marking a slot overlaid, and one typed
   per-slot A12 residual reusing A11's own already-public per-stratum reason
   codes -- never a fourth, independently invented reason.

Run with no arguments to verify the checked-in A12 receipt reproduces from
the nine public artifacts on disk -- no ``batch_state/`` required, so this
passes in a fresh checkout. Pass ``--write-receipt`` to (re)assemble and
persist it after a genuine change to one of those nine artifacts or to this
module.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from learn_ukrainian_v4_runtime.resources import resource_root

_SELF_ROOT = resource_root()

from learn_ukrainian_v4_runtime import v4_a11_silver_release_gate as a11

ROOT = _SELF_ROOT
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"

A12_RECEIPT_PATH = ADMISSION / "dataset_v4_a12_gold_overlay_gate_receipt_v1.json"
A12_SCHEMA_PATH = CONTRACTS / "dataset_v4_a12_gold_overlay_gate_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_PATH = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
A6_RECEIPT_PATH = ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json"
A7_RECEIPT_PATH = ADMISSION / "dataset_v4_a7_original_row_factory_receipt_v1.json"
A8_RECEIPT_PATH = ADMISSION / "dataset_v4_a8_admission_assembly_receipt_v1.json"
A9_RECEIPT_PATH = ADMISSION / "dataset_v4_a9_evaluation_package_receipt_v1.json"
A10_RECEIPT_PATH = ADMISSION / "dataset_v4_a10_pilot_review_gate_receipt_v1.json"
A11_RECEIPT_PATH = ADMISSION / "dataset_v4_a11_silver_release_gate_receipt_v1.json"
SLOT_MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"
SELF_PATH = ROOT / "scripts/projects/open_model_data/v4_a12_gold_overlay_gate.py"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

# The manifest's own required gate IDs for this stage -- never invented, and
# checked at gate-derivation time to still be present in the live manifest.
# A12 re-wires both: MODEL_AGREEMENT_NOT_SILVER_OR_GOLD (this module's
# shared-engine wiring refuses a model-only basis for gold too) and
# SILVER_FIRST_STABLE_IDS (a gold overlay is applied on top of the same
# frozen v4p-* slot IDs used since A6 -- never renumbered for the overlay).
REQUIRED_GATE_IDS = ("MODEL_AGREEMENT_NOT_SILVER_OR_GOLD", "SILVER_FIRST_STABLE_IDS")

# This module's own frozen expectation of what the shared admission engine
# must refuse as a gold basis -- checked against the live
# ``v4_original_row_admission.MODEL_ONLY_BASES`` on every gate derivation,
# never re-derived from a receipt (a receipt only proves a *past* run
# matched, not that the live engine still does).
EXPECTED_MODEL_ONLY_BASES = frozenset({"arena_vote", "model_agreement", "model_vote"})

# Mirrors v4_a11_silver_release_gate.FORBIDDEN_KEYS exactly -- "gold" stays
# excluded because it names this receipt's own always-false eligibility flag
# and this module's own field names, never a real gold label.
FORBIDDEN_KEYS = a11.FORBIDDEN_KEYS
FORBIDDEN_SUBSTRINGS = a11.FORBIDDEN_SUBSTRINGS

# Completion-vocabulary claims that belong to other roles or are unreachable
# today (see the manifest's own completion_vocabulary and A0's non_goals) --
# never emitted here. Unlike A11's own list, "TRAINING_READY_SILVER" (A11's
# own ready state, now a foreign claim from A12's point of view) is added
# back, and "GOLD_UPGRADE_READY" (A12's own legitimate -- if currently
# unreachable -- ready state, and the manifest's own completion_vocabulary
# entry for this role) is removed, mirroring how each stage excludes only
# its own name from the borrowed forbidden-claims list.
# "TRAINING_READY_GOLD_SUBSET" is never removed -- it is not this stage's own
# name (a bounded overlay *plan* is not a claim that gold rows already
# exist), and the binding contract requires it stay forbidden permanently.
FORBIDDEN_COMPLETION_CLAIMS = tuple(
    sorted({*a11.FORBIDDEN_COMPLETION_CLAIMS, "TRAINING_READY_SILVER"} - {"GOLD_UPGRADE_READY"})
)

GOLD_OVERLAY_ELIGIBILITY = {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}

# The fixed overlay-packet contract. Never varies with gate state, and is
# never itself evidence that an overlay happened -- it is the requirement a
# real future gold overlay must satisfy, not a record that one occurred.
OVERLAY_PACKET_REQUIREMENTS = {
    "gate_ids": list(REQUIRED_GATE_IDS),
    "requires_upstream_silver_release_executed": True,
    "requires_source_qualified_human_adjudicator": True,
    "requires_overlay_bound_to_stable_silver_row_id": True,
    "self_adjudication_admits_gold": False,
    "model_agreement_admits_gold": False,
    "arena_vote_admits_gold": False,
    "model_vote_admits_gold": False,
    "hypothesis_admits_gold": False,
    "gold_ids_never_renumber_the_frozen_silver_slot_ids": True,
    "overlay_fields_are_additive_only": True,
    "overlay_may_execute_against_missing_or_empty_silver_rows": False,
    "overlay_execution_state": "NOT_EXECUTED_NO_RELEASED_SILVER_ROWS",
}

# The always-quarantined model-agreement status this module carries -- never
# a live computation, and never anything but this one frozen shape. Model
# agreement is quarantined, not silently discarded: it stays visible as a
# permanently non-gold-admitting signal, never inferred into gold.
MODEL_AGREEMENT_QUARANTINE = {
    "status": "MODEL_AGREEMENT_QUARANTINED_NOT_GOLD",
    "model_only_bases_excluded": sorted(EXPECTED_MODEL_ONLY_BASES),
    "self_adjudication_admits_gold": False,
}

canonical_json = a11.canonical_json
sha256_text = a11.sha256_text
sha256_file = a11.sha256_file


class GoldOverlayGateError(ValueError):
    """The A12 wiring or its deterministic receipt is unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GoldOverlayGateError(message)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# --- A11 reason -> A12 per-slot residual reason ------------------------------
#
# A11 already types each frozen slot's blocker as one of three reason codes
# (reused unchanged from A10's own mapping, itself from A9's, itself from
# A8's, itself from A7's). A12 never invents a fourth -- "why has A11
# released nothing as silver for this frozen slot" is exactly "why has A12
# no stable silver row ID to overlay with gold".
A12_NEXT_ACTION_BY_REASON = {
    "rights_unknown": (
        "no released silver row exists to overlay with gold for this frozen slot until A2 resolves "
        "unit-specific training/derivation rights for its stratum's supporting source unit -- never overlay gold "
        "onto a placeholder row while rights remain unknown"
    ),
    "source_incomplete": (
        "no source unit is yet identified for this frozen slot's stratum, so nothing has been released as silver "
        "for A12 to overlay with gold -- never invent or substitute a placeholder gold overlay"
    ),
    "independence_unavailable": (
        "a supporting source unit is identified for this frozen slot's stratum but its coverage/rights review is "
        "not yet complete, so A11 has released nothing as silver and A12 has no stable silver row ID to overlay "
        "with gold yet"
    ),
}


# --- gold overlay gate (public-only) ------------------------------------------


def check_gold_overlay_gate(root: Path = ROOT) -> dict[str, Any]:
    """Independently re-derive whether a gold overlay may ever be claimed
    ready, from the frozen slot manifest's own ``assignment_state`` per
    stratum, A2's own residuals, A11's own already-public silver-release
    gate, and A11's independent validity -- never trusting the A12 receipt's
    own declared fields, never opening ``batch_state/``.
    ``gold_overlay_slice_ready`` is only ever true once every frozen slot is
    assigned to a real source unit *and* A2 has zero unresolved residuals
    *and* A11 itself still independently validates *and* A11's own silver
    release gate is open *and* the shared admission engine's own
    ``MODEL_ONLY_BASES`` still matches this module's own frozen expectation
    of what a gold overlay must refuse *and* a source-qualified human
    adjudication has actually been recorded *and* a gold overlay has
    actually been executed -- and the last two conditions have no execution
    mechanism yet, so both stay hardcoded ``False``, never derived from a
    file that does not exist.

    Fails closed -- a *closed gate*, not an exception -- if any of the three
    required public artifacts (slot manifest, A2 receipt, A11 receipt) is
    missing, mirroring
    ``v4_a11_silver_release_gate.check_silver_release_gate``'s own
    missing-artifact handling."""
    manifest_path = (root / "data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json").resolve()
    a2_path = (
        root / "data/projects/open_model_data/admission/dataset_v4_a2_source_operation_admission_receipt_v1.json"
    ).resolve()
    a11_path = (
        root / "data/projects/open_model_data/admission/dataset_v4_a11_silver_release_gate_receipt_v1.json"
    ).resolve()
    required_paths = {"slot_manifest": manifest_path, "a2_receipt": a2_path, "a11_receipt": a11_path}
    for label, path in required_paths.items():
        require(root.resolve() in path.parents, f"{label} path escapes the repository root -- refusing")

    missing = sorted(label for label, path in required_paths.items() if not path.is_file())
    if missing:
        return {
            "gate_id": "v4-a12-gold-overlay-gate-v1",
            "a11_receipt_valid": False,
            "model_agreement_exclusion_confirmed": False,
            "a2_rights_resolved": False,
            "all_slots_assigned": False,
            "upstream_silver_release_ready": False,
            "source_qualified_human_adjudication_recorded": False,
            "gold_overlay_executed": False,
            "gold_overlay_slice_ready": False,
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
    # what a gold overlay must refuse. Never derived from a receipt (which
    # would only prove some *past* run matched, not the live engine), and
    # never a superset/subset substitute -- exact equality only.
    model_agreement_exclusion_confirmed = a11.a10.a9.a8.admission.MODEL_ONLY_BASES == EXPECTED_MODEL_ONLY_BASES

    a11_receipt = _load(a11_path)
    try:
        a11.validate_receipt_independently(a11_receipt, root)
        a11_valid = True
    except a11.SilverReleaseGateError:
        a11_valid = False

    upstream_silver_release_ready = a11_valid and a11_receipt["release_gate"]["silver_release_slice_ready"] is True

    # Neither execution mechanism exists yet -- these can never be derived
    # true from any file on disk today, so they stay hardcoded False rather
    # than independently-computed flags that could accidentally flip.
    source_qualified_human_adjudication_recorded = False
    gold_overlay_executed = False

    gold_overlay_slice_ready = (
        rights_resolved
        and all_assigned
        and a11_valid
        and model_agreement_exclusion_confirmed
        and upstream_silver_release_ready
        and source_qualified_human_adjudication_recorded
        and gold_overlay_executed
    )
    blocked_reason_code = None
    if not gold_overlay_slice_ready:
        # Checked before a11_valid: a live engine drift makes A8's/A9's/
        # A10's/A11's own nested engine-wiring checks fail too (same shared
        # module object), so the more specific, more upstream cause is
        # reported first rather than the derived "a11_receipt_invalid"
        # symptom.
        if not model_agreement_exclusion_confirmed:
            blocked_reason_code = "model_agreement_exclusion_engine_drifted"
        elif not a11_valid:
            blocked_reason_code = "a11_receipt_invalid"
        elif not rights_resolved and not all_assigned:
            blocked_reason_code = "rights_unresolved_and_slots_unassigned"
        elif not rights_resolved:
            blocked_reason_code = "rights_unresolved"
        elif not all_assigned:
            blocked_reason_code = "slot_assignment_pending_a2_a3"
        elif not upstream_silver_release_ready:
            blocked_reason_code = f"upstream_a11_blocked:{a11_receipt['release_gate']['blocked_reason_code']}"
        else:
            blocked_reason_code = "gold_overlay_not_yet_executed_no_source_qualified_adjudication"

    return {
        "gate_id": "v4-a12-gold-overlay-gate-v1",
        "a11_receipt_valid": a11_valid,
        "model_agreement_exclusion_confirmed": model_agreement_exclusion_confirmed,
        "a2_rights_resolved": rights_resolved,
        "all_slots_assigned": all_assigned,
        "upstream_silver_release_ready": upstream_silver_release_ready,
        "source_qualified_human_adjudication_recorded": source_qualified_human_adjudication_recorded,
        "gold_overlay_executed": gold_overlay_executed,
        "gold_overlay_slice_ready": gold_overlay_slice_ready,
        "owner_role": manifest["sealed_heldout_commitment"]["assignment_owner"],
        "blocked_reason_code": blocked_reason_code,
    }


# --- A12's own per-slot residuals (public, source-free) ----------------------


def derive_a12_slot_residuals(
    manifest: dict[str, Any], a2_receipt: dict[str, Any], gate: dict[str, Any]
) -> list[dict[str, Any]]:
    """One typed residual per frozen public slot ID -- never a silently
    dropped slot and never a gold overlay invented in place of the missing
    released row. A pure function of the manifest's own ``slot_series``,
    A11's own already-public per-stratum reason codes, and the gate this
    module itself re-derives; never opens any private state."""
    owner_role = gate["owner_role"]
    reasons_by_stratum = a11.a10.a9.a8.a7.stratum_reason_codes(a2_receipt)
    residuals = []
    for stratum_entry in a11.a10.a9.a8.a7.a6.frozen_slot_strata(manifest):
        stratum = stratum_entry["stratum"]
        reason_code = reasons_by_stratum[stratum]
        for slot_id in stratum_entry["slot_ids"]:
            residuals.append(
                {
                    "residual_id": f"a12-residual-{reason_code.replace('_', '-')}-{slot_id}",
                    "subject_kind": "pilot_slot",
                    "subject_id": slot_id,
                    "stage": "A12",
                    "reason_code": reason_code,
                    "owner_role": owner_role,
                    "next_action": A12_NEXT_ACTION_BY_REASON[reason_code],
                    "retryability": "retryable",
                    "evidence_refs": [
                        "admission.dataset_v4_pilot_slot_manifest_v1.slot_series",
                        "admission.dataset_v4_a2_source_operation_admission_receipt_v1.stratum_coverage_map",
                        "admission.dataset_v4_a11_silver_release_gate_receipt_v1.a11_residuals",
                    ],
                }
            )
    residuals.sort(key=lambda residual: residual["subject_id"])
    return residuals


# --- gold overlay view (public, fail-closed, never executes an overlay) -----


def build_gold_overlay_view(
    manifest: dict[str, Any], a11_receipt: dict[str, Any], a12_residuals: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Reproduce, per frozen slot, exactly what a gold overlay would see --
    and fail closed if A11's own ``silver_release_view`` ever claims a gold
    overlay applied without a released silver row. Never marks a slot
    overlaid: ``gold_overlay_applied`` is unconditionally ``False`` because
    this module has no execution mechanism and must never overlay gold onto
    a missing, unreleased, or model-agreement-only row."""
    residual_by_slot = {residual["subject_id"]: residual["residual_id"] for residual in a12_residuals}
    expected_slot_ids = set(a11.a10.a9.a8.a7.a6.all_frozen_slot_ids(manifest))
    seen_slot_ids = {entry["slot_id"] for entry in a11_receipt["silver_release_view"]}
    require(
        seen_slot_ids == expected_slot_ids,
        "A11 silver_release_view does not cover exactly the frozen slot manifest -- refusing gold overlay view",
    )

    view = []
    for entry in a11_receipt["silver_release_view"]:
        slot_id = entry["slot_id"]
        silver_row_released = entry["release_executed"]
        require(
            entry["label_tier"] != "gold",
            f"A11 silver_release_view already carries a gold label_tier for slot {slot_id!r} -- refusing "
            "(gold is never granted upstream of A12)",
        )
        view.append(
            {
                "slot_id": slot_id,
                "silver_row_released": silver_row_released,
                "gold_overlay_required": True,
                "gold_overlay_applied": False,
                "adjudicator_source_qualification": None,
                "gold_label_tier": None,
                "residual_id": residual_by_slot[slot_id],
            }
        )
    view.sort(key=lambda entry: entry["slot_id"])
    return view


# --- overlay packet (fixed, data-independent contract) -----------------------


def build_overlay_packet() -> dict[str, Any]:
    """The fixed overlay-packet contract every real future gold overlay must
    satisfy. Never varies with gate state and never itself claims an overlay
    happened -- returns a fresh copy of the frozen
    ``OVERLAY_PACKET_REQUIREMENTS`` so callers cannot mutate the module-level
    constant."""
    return dict(OVERLAY_PACKET_REQUIREMENTS)


def build_model_agreement_quarantine() -> dict[str, Any]:
    """The fixed, always-quarantined model-agreement status this module
    carries -- returns a fresh copy of the frozen
    ``MODEL_AGREEMENT_QUARANTINE`` so callers cannot mutate the module-level
    constant."""
    return dict(MODEL_AGREEMENT_QUARANTINE)


# --- shared engine wiring (real call, zero rows today) -----------------------


def run_engine_admission_check(rows: list[dict[str, Any]] = ()) -> dict[str, Any]:  # type: ignore[assignment]
    """A real (never stubbed) call into the shared, already-on-main
    ``v4_original_row_admission.admit_rows`` engine, bound to the V4
    controlling outcome. A11 released zero silver rows, so there is nothing
    for A12 to overlay with gold; ``rows`` stays empty and the engine's own
    counters (``admitted_rows``, ``rejected_rows``) both come back 0 --
    proving A12's own wiring into the unmodified, fail-closed admission
    engine (the one place a model-agreement-only row is refused) is live at
    the overlay layer too, never fabricating a row to exercise it."""
    return a11.a10.a9.a8.admission.admit_rows(outcome_sha256=V4_SHA256, rows=list(rows))


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
    a10_receipt = _load(A10_RECEIPT_PATH)
    a11_receipt = _load(A11_RECEIPT_PATH)
    gate = check_gold_overlay_gate(root)

    strata = a11.a10.a9.a8.a7.a6.frozen_slot_strata(manifest)
    frozen_slot_ids = a11.a10.a9.a8.a7.a6.all_frozen_slot_ids(manifest)

    a2_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A2", "status": "unresolved_carried_to_a12"}
        for entry in a2_receipt["residuals"]
    ]
    a4_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A4", "status": "unresolved_carried_to_a12"}
        for entry in a4_receipt["a4_residuals"]
    ]
    a5_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A5", "status": "unresolved_carried_to_a12"}
        for entry in a5_receipt["a5_residuals"]
    ]
    a6_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A6", "status": "unresolved_carried_to_a12"}
        for entry in a6_receipt["a6_residuals"]
    ]
    a7_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A7", "status": "unresolved_carried_to_a12"}
        for entry in a7_receipt["a7_residuals"]
    ]
    a8_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A8", "status": "unresolved_carried_to_a12"}
        for entry in a8_receipt["a8_residuals"]
    ]
    a9_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A9", "status": "unresolved_carried_to_a12"}
        for entry in a9_receipt["a9_residuals"]
    ]
    a10_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A10", "status": "unresolved_carried_to_a12"}
        for entry in a10_receipt["a10_residuals"]
    ]
    a11_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A11", "status": "unresolved_carried_to_a12"}
        for entry in a11_receipt["a11_residuals"]
    ]

    engine_admission_receipt = run_engine_admission_check([])
    a12_residuals = derive_a12_slot_residuals(manifest, a2_receipt, gate)
    gold_overlay_view = build_gold_overlay_view(manifest, a11_receipt, a12_residuals)
    overlay_packet = build_overlay_packet()
    model_agreement_quarantine = build_model_agreement_quarantine()

    rows_overlaid = sum(1 for entry in gold_overlay_view if entry["gold_overlay_applied"])
    rows_released_eligible = sum(1 for entry in gold_overlay_view if entry["silver_row_released"])

    return {
        "schema_version": "dataset_v4_a12_gold_overlay_gate_receipt_v1",
        "receipt_id": "dataset-v4-a12-gold-overlay-gate-v1",
        "status": (
            "A12_GOLD_OVERLAY_GATE_WIRED_OVERLAY_NOT_EXECUTED_TEXT_FREE_NO_GOLD_UPGRADE_CLAIM"
            if not gate["gold_overlay_slice_ready"]
            else "GOLD_UPGRADE_READY"
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
            "a11_silver_release_gate": {
                "path": str(A11_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A11_RECEIPT_PATH),
                "schema_version": "dataset_v4_a11_silver_release_gate_receipt_v1",
            },
            "pilot_slot_manifest": {
                "path": str(SLOT_MANIFEST_PATH.relative_to(root)),
                "sha256": sha256_file(SLOT_MANIFEST_PATH),
                "schema_version": "dataset_v4_pilot_slot_manifest_v1",
            },
            "admission_engine_implementation": {
                "path": str(a11.a10.a9.a8.ADMISSION_ENGINE_PATH.relative_to(root)),
                "sha256": sha256_file(a11.a10.a9.a8.ADMISSION_ENGINE_PATH),
                "schema_version": "v4_original_row_admission_script_v1",
            },
            "wiring_implementation": {
                "path": str(SELF_PATH.relative_to(root)),
                "sha256": sha256_file(SELF_PATH),
                "schema_version": "v4_a12_gold_overlay_gate_script_v1",
            },
        },
        "role_map": manifest["role_ownership"],
        "frozen_slot_denominator": {"total_slots": len(frozen_slot_ids), "strata": strata},
        "overlay_gate": {
            "gate_id": gate["gate_id"],
            "requires": [
                "a11_receipt_independently_valid",
                "model_agreement_exclusion_confirmed",
                "a2_rights_fully_resolved",
                "all_frozen_slots_assigned",
                "upstream_a11_silver_release_executed",
                "source_qualified_human_adjudication_recorded",
                "gold_overlay_executed",
            ],
            "a11_receipt_valid": gate["a11_receipt_valid"],
            "model_agreement_exclusion_confirmed": gate["model_agreement_exclusion_confirmed"],
            "a2_rights_resolved": gate["a2_rights_resolved"],
            "all_slots_assigned": gate["all_slots_assigned"],
            "upstream_silver_release_ready": gate["upstream_silver_release_ready"],
            "source_qualified_human_adjudication_recorded": gate["source_qualified_human_adjudication_recorded"],
            "gold_overlay_executed": gate["gold_overlay_executed"],
            "gold_overlay_slice_ready": gate["gold_overlay_slice_ready"],
            "owner_role": gate["owner_role"],
            "blocked_reason_code": gate["blocked_reason_code"],
        },
        "overlay_packet": overlay_packet,
        "model_agreement_quarantine": model_agreement_quarantine,
        "engine_wiring": {
            "engine_schema_version": a11.a10.a9.a8.admission.SCHEMA_VERSION,
            "engine_input_schema_version": a11.a10.a9.a8.admission.INPUT_SCHEMA_VERSION,
            "model_only_bases_blocked": sorted(a11.a10.a9.a8.admission.MODEL_ONLY_BASES),
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
        "a11_residuals_carried_forward": a11_residuals_carried,
        "a12_residuals": a12_residuals,
        "gold_overlay_view": gold_overlay_view,
        "execution_counters": {
            "dataset_rows_emitted": 0,
            "rows_overlaid_with_gold": rows_overlaid,
            "rows_released_as_silver_and_eligible_for_overlay": rows_released_eligible,
            "frozen_slot_count": len(frozen_slot_ids),
            "slots_overlay_ready": len(frozen_slot_ids) if gate["gold_overlay_slice_ready"] else 0,
            "slots_blocked": 0 if gate["gold_overlay_slice_ready"] else len(frozen_slot_ids),
        },
        "eligibility": dict(GOLD_OVERLAY_ELIGIBILITY),
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
            "training_ready_gold_subset_claimed": False,
            "gold_upgrade_ready_claimed": False,
            "arena_slice_ready_claimed": False,
            "admitted_slice_ready_claimed": False,
            "eval_artifact_ready_claimed": False,
            "pilot_review_passed_claimed": False,
            "self_review_occurred": False,
            "self_adjudication_occurred": False,
            "review_executed_against_missing_or_empty_row": False,
            "overlay_executed_against_missing_or_empty_silver_row": False,
            "contract_gate_waived": False,
            "privacy_gate_waived": False,
            "a4_private_ledger_loaded": False,
            "mac_corpus_copy_created": False,
            "epic_done_claimed": False,
            "heldout_family_identity_leaked": False,
            "model_agreement_admitted_silver": False,
            "model_agreement_admitted_gold": False,
            "arena_vote_admitted_silver": False,
            "arena_vote_admitted_gold": False,
            "hypothesis_admitted_silver": False,
            "hypothesis_admitted_gold": False,
            "silver_released_without_pilot_review_or_admission": False,
            "gold_overlaid_without_silver_release_or_adjudication": False,
        },
    }


# --- receipt verification ---------------------------------------------------


def _load_schema() -> dict[str, Any]:
    schema = _load(A12_SCHEMA_PATH)
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
    gate = check_gold_overlay_gate(root)
    declared = receipt["overlay_gate"]
    require(
        declared["a11_receipt_valid"] == gate["a11_receipt_valid"]
        and declared["model_agreement_exclusion_confirmed"] == gate["model_agreement_exclusion_confirmed"]
        and declared["a2_rights_resolved"] == gate["a2_rights_resolved"]
        and declared["all_slots_assigned"] == gate["all_slots_assigned"]
        and declared["upstream_silver_release_ready"] == gate["upstream_silver_release_ready"]
        and declared["source_qualified_human_adjudication_recorded"]
        == gate["source_qualified_human_adjudication_recorded"]
        and declared["gold_overlay_executed"] == gate["gold_overlay_executed"]
        and declared["gold_overlay_slice_ready"] == gate["gold_overlay_slice_ready"]
        and declared["blocked_reason_code"] == gate["blocked_reason_code"],
        "receipt overlay_gate does not match the state independently re-derived from the live public artifacts "
        "-- refusing (re-verify/regenerate required)",
    )
    require(
        gate["gold_overlay_slice_ready"] or receipt["status"] != "GOLD_UPGRADE_READY",
        "receipt claims GOLD_UPGRADE_READY while the independently re-derived gate is closed -- refusing",
    )
    require(
        receipt["status"] != "TRAINING_READY_GOLD_SUBSET",
        "receipt claims TRAINING_READY_GOLD_SUBSET -- refusing (never a valid A12 claim)",
    )
    require(
        declared["source_qualified_human_adjudication_recorded"] is False,
        "receipt overlay_gate claims a human adjudication was recorded, but no execution mechanism exists -- refusing",
    )
    require(
        declared["gold_overlay_executed"] is False,
        "receipt overlay_gate claims a gold overlay was executed, but no execution mechanism exists -- refusing",
    )


def validate_frozen_slot_denominator(receipt: dict[str, Any], root: Path) -> None:
    manifest = _load(SLOT_MANIFEST_PATH)
    expected_strata = a11.a10.a9.a8.a7.a6.frozen_slot_strata(manifest)
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


def validate_overlay_packet(receipt: dict[str, Any]) -> None:
    """The overlay packet is a fixed contract, never a live computation --
    requires byte-identical equality with the module-level constant, proving
    it was never weakened (or strengthened into a false claim) per receipt."""
    require(
        receipt["overlay_packet"] == OVERLAY_PACKET_REQUIREMENTS,
        "overlay_packet does not equal the frozen overlay-packet contract -- refusing",
    )


def validate_model_agreement_quarantine(receipt: dict[str, Any]) -> None:
    require(
        receipt["model_agreement_quarantine"] == MODEL_AGREEMENT_QUARANTINE,
        "model_agreement_quarantine does not equal the frozen quarantine status -- refusing (model agreement must never admit gold)",
    )


def validate_engine_wiring(receipt: dict[str, Any]) -> None:
    """Re-runs the real shared admission engine call and requires a
    byte-identical result, plus makes the engine independently verify its
    own nested receipt (``v4_original_row_admission.verify_receipt``) --
    proving this is a live wire into the on-main engine at the overlay layer
    too, not a declared/stubbed shape, and that the model-only-basis refusal
    ``MODEL_ONLY_BASES`` still matches what this receipt declares."""
    wiring = receipt["engine_wiring"]
    admission = a11.a10.a9.a8.admission
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
        "engine_wiring.admission_receipt does not report zero rows -- refusing (no released silver row exists yet; "
        "dataset_rows_emitted must stay 0)",
    )


def validate_residuals_and_gold_overlay_view(receipt: dict[str, Any], root: Path) -> None:
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)
    a5_receipt = _load(A5_RECEIPT_PATH)
    a6_receipt = _load(A6_RECEIPT_PATH)
    a7_receipt = _load(A7_RECEIPT_PATH)
    a8_receipt = _load(A8_RECEIPT_PATH)
    a9_receipt = _load(A9_RECEIPT_PATH)
    a10_receipt = _load(A10_RECEIPT_PATH)
    a11_receipt = _load(A11_RECEIPT_PATH)
    manifest = _load(SLOT_MANIFEST_PATH)
    gate = check_gold_overlay_gate(root)

    for stage, source_ids, carried in (
        ("A2", {e["residual_id"] for e in a2_receipt["residuals"]}, receipt["a2_residuals_carried_forward"]),
        ("A4", {e["residual_id"] for e in a4_receipt["a4_residuals"]}, receipt["a4_residuals_carried_forward"]),
        ("A5", {e["residual_id"] for e in a5_receipt["a5_residuals"]}, receipt["a5_residuals_carried_forward"]),
        ("A6", {e["residual_id"] for e in a6_receipt["a6_residuals"]}, receipt["a6_residuals_carried_forward"]),
        ("A7", {e["residual_id"] for e in a7_receipt["a7_residuals"]}, receipt["a7_residuals_carried_forward"]),
        ("A8", {e["residual_id"] for e in a8_receipt["a8_residuals"]}, receipt["a8_residuals_carried_forward"]),
        ("A9", {e["residual_id"] for e in a9_receipt["a9_residuals"]}, receipt["a9_residuals_carried_forward"]),
        ("A10", {e["residual_id"] for e in a10_receipt["a10_residuals"]}, receipt["a10_residuals_carried_forward"]),
        ("A11", {e["residual_id"] for e in a11_receipt["a11_residuals"]}, receipt["a11_residuals_carried_forward"]),
    ):
        carried_ids = {entry["residual_id"] for entry in carried}
        require(
            carried_ids == source_ids,
            f"{stage.lower()}_residuals_carried_forward does not reproduce from {stage} -- refusing",
        )
        for entry in carried:
            require(
                entry["origin_stage"] == stage and entry["status"] == "unresolved_carried_to_a12",
                f"{stage.lower()}_residuals_carried_forward entry has an unexpected origin_stage/status -- refusing",
            )

    expected_a12_residuals = derive_a12_slot_residuals(manifest, a2_receipt, gate)
    require(
        receipt["a12_residuals"] == expected_a12_residuals,
        "a12_residuals does not reproduce from the live slot manifest, A2 receipt, and gate -- refusing",
    )

    expected_view = build_gold_overlay_view(manifest, a11_receipt, expected_a12_residuals)
    require(
        receipt["gold_overlay_view"] == expected_view,
        "gold_overlay_view does not reproduce from the live A11 receipt and a12_residuals -- refusing",
    )
    require(
        all(
            entry["gold_overlay_applied"] is False
            and entry["gold_label_tier"] is None
            and entry["adjudicator_source_qualification"] is None
            and entry["silver_row_released"] is False
            for entry in receipt["gold_overlay_view"]
        ),
        "gold_overlay_view claims a row was overlaid, labeled, or adjudicated while no silver row has been released -- refusing",
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
        receipt["eligibility"] == GOLD_OVERLAY_ELIGIBILITY,
        "receipt eligibility does not equal the frozen all-false gold-overlay eligibility -- refusing",
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
        receipt["execution_counters"]["rows_overlaid_with_gold"] == 0,
        "receipt execution_counters.rows_overlaid_with_gold is not 0 -- refusing (no overlay-execution mechanism exists yet)",
    )


def validate_receipt_independently(receipt: dict[str, Any], root: Path = ROOT) -> None:
    from learn_ukrainian_v4_runtime.stage_policy import validate_stage_policy

    validate_stage_policy(receipt)
    from learn_ukrainian_v4_runtime.provenance import validate_receipt_bindings

    validate_receipt_bindings(receipt, root, validate_bindings_hash_to_disk)
    validate_gate_matches_receipt(receipt, root)
    validate_frozen_slot_denominator(receipt, root)
    validate_overlay_packet(receipt)
    validate_model_agreement_quarantine(receipt)
    validate_engine_wiring(receipt)
    validate_residuals_and_gold_overlay_view(receipt, root)
    validate_no_forbidden_keys(receipt)
    validate_no_forbidden_completion_claims(receipt)
    validate_eligibility_and_safety_all_false(receipt)
    validate_receipt_schema(receipt)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--receipt",
        type=Path,
        default=A12_RECEIPT_PATH,
        help="A12 receipt JSON to verify (default: the tracked V4 A12 gold overlay gate receipt).",
    )
    parser.add_argument(
        "--write-receipt", action="store_true", help="Assemble and persist a freshly computed receipt to --receipt."
    )
    args = parser.parse_args(argv)

    if args.write_receipt:
        receipt = build_receipt()
        validate_receipt_independently(receipt)
        args.receipt.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        print(canonical_json({"status": receipt["status"], "overlay_gate": receipt["overlay_gate"]}))
        return

    receipt = _load(args.receipt)
    validate_receipt_independently(receipt)
    print(canonical_json({"status": receipt["status"], "overlay_gate": receipt["overlay_gate"]}))


if __name__ == "__main__":
    try:
        main()
    except GoldOverlayGateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
