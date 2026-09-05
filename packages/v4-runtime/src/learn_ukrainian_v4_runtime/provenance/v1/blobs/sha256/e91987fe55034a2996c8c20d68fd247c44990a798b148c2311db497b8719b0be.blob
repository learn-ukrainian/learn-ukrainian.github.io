#!/usr/bin/env python3
"""V4 A13 cleanup/recovery receipt: the typed cleanup-policy and closeout
receipt bound to the merged A12 gold-overlay gate receipt, the frozen V4
pilot slot manifest, and the V4 SHA.

A13 owns the *cleanup_recovery* role (``role_ownership.A13 ==
"cleanup_recovery"`` in the frozen slot manifest): approved temporary-output
cleanup and receipt-backed closeout, and nothing else. It must never hide a
stopped denominator -- the frozen 100-slot count stays 100 and every
unresolved A2/A4/A5/A6/A7/A8/A9/A10/A11/A12 residual is carried forward
unresolved, never quietly dropped because "the epic is being closed out." It
must never claim a stronger release state than the evidence on disk
supports: no ``TRAINING_READY_SILVER``, no ``EVAL_ARTIFACT_READY``, no gold
claim, no passed-pilot claim, and no epic-done claim of any kind. It must
never open A3's held-out membership file or A4's private extraction ledger,
and it must never load source text.

This module never loads source text, never re-fetches corpus, and never
deletes anything itself -- it only *declares* a fixed, auditable cleanup
policy and independently re-verifies that nothing upstream has been
silently resolved or silently dropped. Its only inputs are ten already-public
artifacts --

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
* A11's silver release gate receipt (its own ``a11_residuals`` only),
* A12's gold overlay gate receipt (its own ``a12_residuals`` -- the direct
  upstream signal this module's recovery state builds on), and
* the frozen 100-slot V4 pilot slot manifest (``slot_series`` -- public slot
  IDs, never a real ``source_unit_id``).

Three independent parts:

1. ``check_cleanup_recovery_state`` -- independently re-derives, from those
   ten public artifacts alone, whether A2's rights are fully resolved and
   every frozen slot is assigned. Right now neither holds, so the module
   reports a single named residual -- ``rights_unresolved_and_slots_
   unassigned`` -- whose only legitimate resolution path is A2 (rights) and
   A3 (slot assignment), never A13 deleting or reassigning a slot to make
   the residual disappear.
2. ``build_cleanup_policy`` -- the fixed, data-independent cleanup contract:
   the only two temporary-output classes ever approved for reaping (a merged
   dispatch worktree, an ephemeral pytest cache), and an explicit,
   permanent forbid list covering ``data/sources.db``, A3's private
   held-out-membership batch state, and A4's private extraction-ledger batch
   state. The policy never varies with recovery-state, and it is never
   itself evidence that a cleanup action was executed -- no path in it is
   ever touched by this module.
3. ``build_receipt`` -- assembles the public receipt: the frozen 100-slot
   denominator (reusing, never duplicating,
   ``v4_a12_gold_overlay_gate.a11.a10.a9.a8.a7.a6.frozen_slot_strata``/
   ``all_frozen_slot_ids``), the recovery state, the cleanup policy, a real
   (zero-row) call into the shared, unmodified
   ``v4_original_row_admission.admit_rows`` engine proving A13's own wiring
   is live rather than declarative, every
   A2/A4/A5/A6/A7/A8/A9/A10/A11/A12 residual carried forward unresolved, one
   typed per-slot A13 residual reusing A12's own already-public per-stratum
   reason codes, and the single named top-level residual required by the
   binding contract.

Run with no arguments to verify the checked-in A13 receipt reproduces from
the ten public artifacts on disk -- no ``batch_state/`` required, so this
passes in a fresh checkout. Pass ``--write-receipt`` to (re)assemble and
persist it after a genuine change to one of those ten artifacts or to this
module.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

_SELF_ROOT = Path(__file__).resolve().parents[3]
if str(_SELF_ROOT) not in sys.path:
    sys.path.insert(0, str(_SELF_ROOT))

from scripts.projects.open_model_data import v4_a12_gold_overlay_gate as a12

ROOT = _SELF_ROOT
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"

A13_RECEIPT_PATH = ADMISSION / "dataset_v4_a13_cleanup_recovery_receipt_v1.json"
A13_SCHEMA_PATH = CONTRACTS / "dataset_v4_a13_cleanup_recovery_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_PATH = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
A6_RECEIPT_PATH = ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json"
A7_RECEIPT_PATH = ADMISSION / "dataset_v4_a7_original_row_factory_receipt_v1.json"
A8_RECEIPT_PATH = ADMISSION / "dataset_v4_a8_admission_assembly_receipt_v1.json"
A9_RECEIPT_PATH = ADMISSION / "dataset_v4_a9_evaluation_package_receipt_v1.json"
A10_RECEIPT_PATH = ADMISSION / "dataset_v4_a10_pilot_review_gate_receipt_v1.json"
A11_RECEIPT_PATH = ADMISSION / "dataset_v4_a11_silver_release_gate_receipt_v1.json"
A12_RECEIPT_PATH = ADMISSION / "dataset_v4_a12_gold_overlay_gate_receipt_v1.json"
SLOT_MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"
SELF_PATH = ROOT / "scripts/projects/open_model_data/v4_a13_cleanup_recovery.py"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

# The merged A12 receipt's public sha256, frozen at dispatch time (PR #7643;
# updated by v4-per-slot-private-factory repair cycle 3 once A7's dropped,
# undecided A7-vs-A6 upstream-completion subset rippled A8's/A9's/A10's/
# A11's/A12's own upstream-binding hashes forward; updated again by the
# v4-real-slot-mechanism PR-A once A7's/A8's own completion mechanism and
# the shared admission engine's new helper rippled the same chain forward;
# updated again by PR #7662 repair 4 once A7's new `a3_heldout_source_
# family_seal` binding (Invariant D1 signed trust boundary) rippled the
# same chain forward -- still 0 real completions, only the source hashes
# moved). This module's bindings must reproduce this value on every run --
# proving A13 is bound to the *merged* A12 receipt, never a local unmerged
# draft.
A12_RECEIPT_SHA256_AT_MERGE = "150b7532d814c35bf27176943206fa8caaf4650f220ce498f60b015a62f9e538"

# This module's own frozen expectation of what the shared admission engine
# must refuse as a silver/gold basis -- checked against the live
# ``v4_original_row_admission.MODEL_ONLY_BASES`` on every state derivation,
# never re-derived from a receipt (a receipt only proves a *past* run
# matched, not that the live engine still does).
EXPECTED_MODEL_ONLY_BASES = a12.EXPECTED_MODEL_ONLY_BASES

# Mirrors v4_a12_gold_overlay_gate.FORBIDDEN_KEYS exactly.
FORBIDDEN_KEYS = a12.FORBIDDEN_KEYS
FORBIDDEN_SUBSTRINGS = a12.FORBIDDEN_SUBSTRINGS

# Completion-vocabulary claims that belong to other roles, are unreachable
# today, or are simply never A13's to make -- never emitted here. Builds on
# A12's own forbidden list, adding "GOLD_UPGRADE_READY" (A12's own ready
# state, now a foreign claim from A13's point of view) and "EPIC_DONE" (not
# a manifest completion-vocabulary term at all, but the binding contract
# names it explicitly as a claim A13 must never make). A13 owns no
# completion-vocabulary term of its own, so nothing is ever removed from the
# inherited forbidden list.
FORBIDDEN_COMPLETION_CLAIMS = tuple(sorted({*a12.FORBIDDEN_COMPLETION_CLAIMS, "GOLD_UPGRADE_READY", "EPIC_DONE"}))

CLEANUP_RECOVERY_ELIGIBILITY = {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}

# The fixed, data-independent cleanup contract. Never varies with recovery
# state, and is never itself evidence that a cleanup action happened -- no
# path named here is ever touched by this module. Only two temporary-output
# classes are ever approved for reaping; everything else, and in particular
# the three named forbidden paths, must never be deleted "to save disk."
CLEANUP_POLICY = {
    "policy_id": "v4-a13-cleanup-policy-v1",
    "approved_temp_output_classes": [
        {
            "class_id": "dispatch_worktree_after_merged",
            "description": (
                "A per-dispatch git worktree under .worktrees/dispatch/ may be reaped only after its PR has "
                "merged -- never a worktree still holding unmerged, unreviewed, or in-flight work."
            ),
            "condition": "pr_status_is_merged",
        },
        {
            "class_id": "pytest_cache",
            "description": (
                "Ephemeral pytest cache directories (.pytest_cache/, __pycache__/) carry no dataset content "
                "and may be reaped at any time."
            ),
            "condition": "always",
        },
    ],
    "forbidden_paths": [
        "data/sources.db",
        "batch_state/open-model-data/v4-a3-heldout/",
        "batch_state/open-model-data/v4-a4-extraction/",
    ],
    "forbidden_actions": [
        "delete_source_evidence",
        "delete_private_a4_jsonl",
        "open_a3_heldout_membership",
        "delete_heldout_membership_to_save_disk",
        "reassign_or_delete_a_frozen_slot_to_close_a_residual",
    ],
    "next_owner_for_named_residual": "A2_A3_PRIVATE_ARTIFACT",
}

canonical_json = a12.canonical_json
sha256_text = a12.sha256_text
sha256_file = a12.sha256_file


class CleanupRecoveryError(ValueError):
    """The A13 wiring or its deterministic receipt is unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CleanupRecoveryError(message)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# --- A12 reason -> A13 per-slot residual reason ------------------------------
#
# A12 already types each frozen slot's blocker as one of three reason codes
# (reused unchanged all the way back through A6). A13 never invents a
# fourth -- "why is there still no released or overlaid row for this frozen
# slot" is exactly "why A13 has nothing to clean up or recover for it."
A13_NEXT_ACTION_BY_REASON = {
    "rights_unknown": (
        "no released or overlaid row exists for this frozen slot until A2 resolves unit-specific "
        "training/derivation rights for its stratum's supporting source unit -- A13 never deletes or reaps "
        "any private evidence supporting this slot while rights remain unknown"
    ),
    "source_incomplete": (
        "no source unit is yet identified for this frozen slot's stratum -- A13 never invents or substitutes "
        "a placeholder row, and never reaps anything for this slot while its source is unidentified"
    ),
    "independence_unavailable": (
        "a supporting source unit is identified for this frozen slot's stratum but its coverage/rights review "
        "is not yet complete -- A13 never treats an in-review slot as eligible for cleanup"
    ),
}


# --- cleanup/recovery state (public-only) -------------------------------------


def check_cleanup_recovery_state(root: Path = ROOT) -> dict[str, Any]:
    """Independently re-derive whether upstream rights/assignment residuals
    are resolved, from the frozen slot manifest's own ``assignment_state``
    per stratum, A2's own residuals, and A12's independent validity --
    never trusting the A13 receipt's own declared fields, never opening
    ``batch_state/``. This never becomes a "ready to close the epic" flag --
    A13 has no completion state to reach; it only reports whether the single
    named residual (rights unresolved and/or slots unassigned) still holds.

    Fails closed -- a *closed state*, not an exception -- if any of the
    three required public artifacts (slot manifest, A2 receipt, A12
    receipt) is missing, mirroring
    ``v4_a12_gold_overlay_gate.check_gold_overlay_gate``'s own
    missing-artifact handling."""
    manifest_path = (root / "data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json").resolve()
    a2_path = (root / "data/projects/open_model_data/admission/dataset_v4_a2_source_operation_admission_receipt_v1.json").resolve()
    a12_path = (root / "data/projects/open_model_data/admission/dataset_v4_a12_gold_overlay_gate_receipt_v1.json").resolve()
    required_paths = {"slot_manifest": manifest_path, "a2_receipt": a2_path, "a12_receipt": a12_path}
    for label, path in required_paths.items():
        require(root.resolve() in path.parents, f"{label} path escapes the repository root -- refusing")

    missing = sorted(label for label, path in required_paths.items() if not path.is_file())
    if missing:
        return {
            "state_id": "v4-a13-cleanup-recovery-v1",
            "a12_receipt_valid": False,
            "model_agreement_exclusion_confirmed": False,
            "a2_rights_resolved": False,
            "all_slots_assigned": False,
            "denominator_stable": False,
            "epic_closed": False,
            "owner_role": "A2_A3_PRIVATE_ARTIFACT",
            "blocked_reason_code": f"required_public_artifact_missing:{missing[0]}",
        }

    manifest = _load(manifest_path)
    require(manifest.get("controlling_outcome_sha256") == V4_SHA256, "slot manifest is not bound to the expected V4 controlling outcome -- refusing")

    a2_receipt = _load(a2_path)
    require(a2_receipt.get("controlling_outcome_sha256") == V4_SHA256, "A2 receipt is not bound to the expected V4 controlling outcome -- refusing")
    rights_resolved = len(a2_receipt.get("residuals", [])) == 0

    all_assigned = all(series["assignment_state"] == "ASSIGNED" for series in manifest["slot_series"])

    # A pure, receipt-independent structural check: the shared engine's own
    # MODEL_ONLY_BASES must still equal this module's frozen expectation.
    # Never derived from a receipt, and never a superset/subset substitute.
    model_agreement_exclusion_confirmed = a12.a11.a10.a9.a8.admission.MODEL_ONLY_BASES == EXPECTED_MODEL_ONLY_BASES

    a12_receipt = _load(a12_path)
    try:
        a12.validate_receipt_independently(a12_receipt, root)
        a12_valid = True
    except a12.GoldOverlayGateError:
        a12_valid = False

    all_ids = [slot_id for stratum in a12.a11.a10.a9.a8.a7.a6.frozen_slot_strata(manifest) for slot_id in stratum["slot_ids"]]
    denominator_stable = len(all_ids) == 100 and len(set(all_ids)) == 100

    blocked_reason_code = None
    if not model_agreement_exclusion_confirmed:
        blocked_reason_code = "model_agreement_exclusion_engine_drifted"
    elif not a12_valid:
        blocked_reason_code = "a12_receipt_invalid"
    elif not denominator_stable:
        blocked_reason_code = "frozen_slot_denominator_unstable"
    elif not rights_resolved and not all_assigned:
        blocked_reason_code = "rights_unresolved_and_slots_unassigned"
    elif not rights_resolved:
        blocked_reason_code = "rights_unresolved"
    elif not all_assigned:
        blocked_reason_code = "slot_assignment_pending_a2_a3"
    # else: every upstream residual this module can independently observe is
    # resolved. Even then, A13 never claims the epic is done -- see
    # build_receipt's fixed status and safety_assertions.

    return {
        "state_id": "v4-a13-cleanup-recovery-v1",
        "a12_receipt_valid": a12_valid,
        "model_agreement_exclusion_confirmed": model_agreement_exclusion_confirmed,
        "a2_rights_resolved": rights_resolved,
        "all_slots_assigned": all_assigned,
        "denominator_stable": denominator_stable,
        "epic_closed": False,
        "owner_role": manifest["sealed_heldout_commitment"]["assignment_owner"],
        "blocked_reason_code": blocked_reason_code,
    }


# --- A13's own per-slot residuals (public, source-free) ----------------------


def derive_a13_slot_residuals(manifest: dict[str, Any], a2_receipt: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    """One typed residual per frozen public slot ID -- never a silently
    dropped slot and never a cleanup action invented in place of the
    missing released/overlaid row. A pure function of the manifest's own
    ``slot_series``, A12's own already-public per-stratum reason codes, and
    the state this module itself re-derives; never opens any private
    state."""
    owner_role = state["owner_role"]
    reasons_by_stratum = a12.a11.a10.a9.a8.a7.stratum_reason_codes(a2_receipt)
    residuals = []
    for stratum_entry in a12.a11.a10.a9.a8.a7.a6.frozen_slot_strata(manifest):
        stratum = stratum_entry["stratum"]
        reason_code = reasons_by_stratum[stratum]
        for slot_id in stratum_entry["slot_ids"]:
            residuals.append(
                {
                    "residual_id": f"a13-residual-{reason_code.replace('_', '-')}-{slot_id}",
                    "subject_kind": "pilot_slot",
                    "subject_id": slot_id,
                    "stage": "A13",
                    "reason_code": reason_code,
                    "owner_role": owner_role,
                    "next_action": A13_NEXT_ACTION_BY_REASON[reason_code],
                    "retryability": "retryable",
                    "evidence_refs": [
                        "admission.dataset_v4_pilot_slot_manifest_v1.slot_series",
                        "admission.dataset_v4_a2_source_operation_admission_receipt_v1.stratum_coverage_map",
                        "admission.dataset_v4_a12_gold_overlay_gate_receipt_v1.a12_residuals",
                    ],
                }
            )
    residuals.sort(key=lambda residual: residual["subject_id"])
    return residuals


def build_named_residual(state: dict[str, Any]) -> dict[str, Any]:
    """The single top-level named residual the binding contract requires:
    rights unresolved and/or slots unassigned, with A2/A3 as the only
    legitimate next owner. A13 never resolves this residual by deleting or
    reassigning a slot -- only A2 (rights) and A3 (slot assignment) can."""
    reason_code = state["blocked_reason_code"] or "resolved_upstream_epic_not_closed"
    next_action = {
        "rights_unresolved_and_slots_unassigned": (
            "A2 must resolve unit-specific training/derivation rights and A3 must complete frozen-slot "
            "assignment before this residual can close -- A13 never deletes or reassigns a slot to close it"
        ),
        "rights_unresolved": "A2 must resolve unit-specific training/derivation rights before this residual can close",
        "slot_assignment_pending_a2_a3": "A3 must complete frozen-slot assignment before this residual can close",
        "resolved_upstream_epic_not_closed": (
            "rights and slot assignment are resolved upstream, but A13 still never claims the epic is done -- "
            "per-slot A2-A12 residuals may remain and are carried forward unresolved"
        ),
    }.get(reason_code, f"blocked upstream: {reason_code}")
    return {
        "residual_id": "a13-residual-rights-unresolved-and-slots-unassigned",
        "reason_code": reason_code,
        "owner_role": "A2_A3_PRIVATE_ARTIFACT",
        "next_action": next_action,
        "retryability": "retryable",
    }


def build_cleanup_policy() -> dict[str, Any]:
    """The fixed cleanup-policy contract. Never varies with recovery state,
    and never itself claims a cleanup action happened -- returns a fresh
    copy of the frozen ``CLEANUP_POLICY`` so callers cannot mutate the
    module-level constant."""
    return json.loads(json.dumps(CLEANUP_POLICY))


# --- shared engine wiring (real call, zero rows today) -----------------------


def run_engine_admission_check(rows: list[dict[str, Any]] = ()) -> dict[str, Any]:  # type: ignore[assignment]
    """A real (never stubbed) call into the shared, already-on-main
    ``v4_original_row_admission.admit_rows`` engine, bound to the V4
    controlling outcome. A13 never admits, releases, or overlays a row;
    ``rows`` stays empty and the engine's own counters (``admitted_rows``,
    ``rejected_rows``) both come back 0 -- proving A13's own wiring into the
    unmodified, fail-closed admission engine is live at the cleanup layer
    too, never fabricating a row to exercise it."""
    return a12.a11.a10.a9.a8.admission.admit_rows(outcome_sha256=V4_SHA256, rows=list(rows))


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
    a12_receipt = _load(A12_RECEIPT_PATH)
    state = check_cleanup_recovery_state(root)

    strata = a12.a11.a10.a9.a8.a7.a6.frozen_slot_strata(manifest)
    frozen_slot_ids = a12.a11.a10.a9.a8.a7.a6.all_frozen_slot_ids(manifest)

    residual_carry_specs = (
        ("A2", a2_receipt["residuals"]),
        ("A4", a4_receipt["a4_residuals"]),
        ("A5", a5_receipt["a5_residuals"]),
        ("A6", a6_receipt["a6_residuals"]),
        ("A7", a7_receipt["a7_residuals"]),
        ("A8", a8_receipt["a8_residuals"]),
        ("A9", a9_receipt["a9_residuals"]),
        ("A10", a10_receipt["a10_residuals"]),
        ("A11", a11_receipt["a11_residuals"]),
        ("A12", a12_receipt["a12_residuals"]),
    )
    carried_by_stage = {
        stage: [{"residual_id": entry["residual_id"], "origin_stage": stage, "status": "unresolved_carried_to_a13"} for entry in entries]
        for stage, entries in residual_carry_specs
    }

    engine_admission_receipt = run_engine_admission_check([])
    a13_residuals = derive_a13_slot_residuals(manifest, a2_receipt, state)
    named_residual = build_named_residual(state)
    cleanup_policy = build_cleanup_policy()

    return {
        "schema_version": "dataset_v4_a13_cleanup_recovery_receipt_v1",
        "receipt_id": "dataset-v4-a13-cleanup-recovery-v1",
        "status": "A13_CLEANUP_RECOVERY_WIRED_TEXT_FREE_NO_STRONGER_RELEASE_STATE_CLAIM",
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
            "a12_gold_overlay_gate": {
                "path": str(A12_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A12_RECEIPT_PATH),
                "schema_version": "dataset_v4_a12_gold_overlay_gate_receipt_v1",
            },
            "pilot_slot_manifest": {
                "path": str(SLOT_MANIFEST_PATH.relative_to(root)),
                "sha256": sha256_file(SLOT_MANIFEST_PATH),
                "schema_version": "dataset_v4_pilot_slot_manifest_v1",
            },
            "admission_engine_implementation": {
                "path": str(a12.a11.a10.a9.a8.ADMISSION_ENGINE_PATH.relative_to(root)),
                "sha256": sha256_file(a12.a11.a10.a9.a8.ADMISSION_ENGINE_PATH),
                "schema_version": "v4_original_row_admission_script_v1",
            },
            "wiring_implementation": {
                "path": str(SELF_PATH.relative_to(root)),
                "sha256": sha256_file(SELF_PATH),
                "schema_version": "v4_a13_cleanup_recovery_script_v1",
            },
        },
        "role_map": manifest["role_ownership"],
        "frozen_slot_denominator": {"total_slots": len(frozen_slot_ids), "strata": strata},
        "recovery_state": state,
        "named_residual": named_residual,
        "cleanup_policy": cleanup_policy,
        "engine_wiring": {
            "engine_schema_version": a12.a11.a10.a9.a8.admission.SCHEMA_VERSION,
            "engine_input_schema_version": a12.a11.a10.a9.a8.admission.INPUT_SCHEMA_VERSION,
            "model_only_bases_blocked": sorted(a12.a11.a10.a9.a8.admission.MODEL_ONLY_BASES),
            "admission_receipt": engine_admission_receipt,
        },
        "a2_residuals_carried_forward": carried_by_stage["A2"],
        "a4_residuals_carried_forward": carried_by_stage["A4"],
        "a5_residuals_carried_forward": carried_by_stage["A5"],
        "a6_residuals_carried_forward": carried_by_stage["A6"],
        "a7_residuals_carried_forward": carried_by_stage["A7"],
        "a8_residuals_carried_forward": carried_by_stage["A8"],
        "a9_residuals_carried_forward": carried_by_stage["A9"],
        "a10_residuals_carried_forward": carried_by_stage["A10"],
        "a11_residuals_carried_forward": carried_by_stage["A11"],
        "a12_residuals_carried_forward": carried_by_stage["A12"],
        "a13_residuals": a13_residuals,
        "execution_counters": {
            "dataset_rows_emitted": 0,
            "frozen_slot_count": len(frozen_slot_ids),
            "temp_outputs_reaped": 0,
            "forbidden_paths_touched": 0,
        },
        "eligibility": dict(CLEANUP_RECOVERY_ELIGIBILITY),
        "safety_assertions": {
            "rows_not_admitted": True,
            "text_emitted": False,
            "source_text_loaded_into_model": False,
            "corpus_refetched": False,
            "held_out_membership_referenced": False,
            "held_out_membership_opened": False,
            "held_out_membership_deleted": False,
            "a4_private_ledger_loaded": False,
            "a4_private_ledger_deleted": False,
            "source_evidence_deleted": False,
            "sources_db_deleted": False,
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
            "epic_done_claimed": False,
            "denominator_reduced_below_100": False,
            "residual_silently_dropped": False,
            "self_review_occurred": False,
            "self_adjudication_occurred": False,
            "contract_gate_waived": False,
            "privacy_gate_waived": False,
            "mac_corpus_copy_created": False,
            "heldout_family_identity_leaked": False,
            "complement_leak_occurred": False,
            "a3_membership_opened_by_a13": False,
            "model_agreement_admitted_silver": False,
            "model_agreement_admitted_gold": False,
            "arena_vote_admitted_silver": False,
            "arena_vote_admitted_gold": False,
            "hypothesis_admitted_silver": False,
            "hypothesis_admitted_gold": False,
            "slot_reassigned_or_deleted_to_close_residual": False,
        },
    }


# --- receipt verification ---------------------------------------------------


def _load_schema() -> dict[str, Any]:
    schema = _load(A13_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return schema


def validate_receipt_schema(receipt: dict[str, Any]) -> None:
    errors = sorted(Draft202012Validator(_load_schema()).iter_errors(receipt), key=lambda e: list(e.path))
    require(not errors, f"receipt fails schema validation: {errors[0].message}" if errors else "")


def validate_bindings_hash_to_disk(receipt: dict[str, Any], root: Path) -> None:
    for name, binding in receipt["bindings"].items():
        bound_path = (root / binding["path"]).resolve()
        require(root.resolve() in bound_path.parents or bound_path == root.resolve(), f"binding {name!r} path escapes the repository root -- refusing: {binding['path']}")
        require(bound_path.is_file(), f"binding {name!r} does not point at a file: {bound_path}")
        actual = sha256_file(bound_path)
        require(
            actual == binding["sha256"],
            f"binding {name!r} on-disk sha256 ({actual}) does not match the receipt's declared sha256 "
            f"({binding['sha256']}) for {binding['path']} -- refusing",
        )


def validate_bound_to_merged_a12_receipt(receipt: dict[str, Any]) -> None:
    """The binding contract requires this receipt be bound to the *merged*
    A12 receipt SHA frozen at dispatch time (PR #7643), not merely to
    whatever A12 receipt happens to be on disk."""
    require(
        receipt["bindings"]["a12_gold_overlay_gate"]["sha256"] == A12_RECEIPT_SHA256_AT_MERGE,
        "receipt is not bound to the merged A12 receipt's known public sha256 -- refusing",
    )


def validate_recovery_state_matches_receipt(receipt: dict[str, Any], root: Path, state: dict[str, Any] | None = None) -> None:
    state = check_cleanup_recovery_state(root) if state is None else state
    declared = receipt["recovery_state"]
    require(
        declared["a12_receipt_valid"] == state["a12_receipt_valid"]
        and declared["model_agreement_exclusion_confirmed"] == state["model_agreement_exclusion_confirmed"]
        and declared["a2_rights_resolved"] == state["a2_rights_resolved"]
        and declared["all_slots_assigned"] == state["all_slots_assigned"]
        and declared["denominator_stable"] == state["denominator_stable"]
        and declared["epic_closed"] == state["epic_closed"]
        and declared["blocked_reason_code"] == state["blocked_reason_code"],
        "receipt recovery_state does not match the state independently re-derived from the live public "
        "artifacts -- refusing (re-verify/regenerate required)",
    )
    require(declared["epic_closed"] is False, "receipt recovery_state claims the epic is closed -- refusing (never a valid A13 claim)")
    require(receipt["status"] != "EPIC_DONE", "receipt claims EPIC_DONE -- refusing (never a valid A13 claim)")


def validate_frozen_slot_denominator(receipt: dict[str, Any], root: Path) -> None:
    manifest = _load(SLOT_MANIFEST_PATH)
    expected_strata = a12.a11.a10.a9.a8.a7.a6.frozen_slot_strata(manifest)
    declared = receipt["frozen_slot_denominator"]
    require(declared["strata"] == expected_strata, "frozen_slot_denominator.strata does not reproduce from the live slot manifest -- refusing")
    all_ids = [slot_id for stratum in expected_strata for slot_id in stratum["slot_ids"]]
    require(len(all_ids) == 100 and len(set(all_ids)) == 100, "frozen slot denominator did not expand to exactly 100 unique slot IDs -- refusing")
    require(declared["total_slots"] == 100, "frozen_slot_denominator.total_slots is not 100 -- refusing")


def validate_cleanup_policy(receipt: dict[str, Any]) -> None:
    """The cleanup policy is a fixed contract, never a live computation --
    requires byte-identical equality with the module-level constant, proving
    it was never weakened (e.g. a forbidden path quietly dropped) per
    receipt."""
    require(receipt["cleanup_policy"] == CLEANUP_POLICY, "cleanup_policy does not equal the frozen cleanup-policy contract -- refusing")
    forbidden = set(CLEANUP_POLICY["forbidden_paths"])
    require(
        {"data/sources.db", "batch_state/open-model-data/v4-a3-heldout/", "batch_state/open-model-data/v4-a4-extraction/"} <= forbidden,
        "cleanup_policy.forbidden_paths is missing a required forbidden path -- refusing",
    )


def validate_named_residual(receipt: dict[str, Any], root: Path, state: dict[str, Any] | None = None) -> None:
    state = check_cleanup_recovery_state(root) if state is None else state
    require(receipt["named_residual"] == build_named_residual(state), "named_residual does not reproduce from the live recovery state -- refusing")
    require(receipt["named_residual"]["owner_role"] == "A2_A3_PRIVATE_ARTIFACT", "named_residual owner_role is not A2_A3_PRIVATE_ARTIFACT -- refusing")


def validate_engine_wiring(receipt: dict[str, Any]) -> None:
    """Re-runs the real shared admission engine call and requires a
    byte-identical result, plus makes the engine independently verify its
    own nested receipt (``v4_original_row_admission.verify_receipt``) --
    proving this is a live wire into the on-main engine at the cleanup layer
    too, not a declared/stubbed shape."""
    wiring = receipt["engine_wiring"]
    admission = a12.a11.a10.a9.a8.admission
    require(
        wiring["engine_schema_version"] == admission.SCHEMA_VERSION and wiring["engine_input_schema_version"] == admission.INPUT_SCHEMA_VERSION,
        "engine_wiring schema versions do not match the live v4_original_row_admission module -- refusing (engine changed without regenerating this receipt)",
    )
    require(
        wiring["model_only_bases_blocked"] == sorted(admission.MODEL_ONLY_BASES),
        "engine_wiring.model_only_bases_blocked does not match the live engine's MODEL_ONLY_BASES -- refusing",
    )
    recomputed = admission.admit_rows(outcome_sha256=V4_SHA256, rows=[])
    require(wiring["admission_receipt"] == recomputed, "engine_wiring.admission_receipt does not reproduce from a live, zero-row v4_original_row_admission.admit_rows call -- refusing")
    admission.verify_receipt(wiring["admission_receipt"])
    require(
        wiring["admission_receipt"]["counts"] == {"input_rows": 0, "admitted_rows": 0, "rejected_rows": 0},
        "engine_wiring.admission_receipt does not report zero rows -- refusing (dataset_rows_emitted must stay 0)",
    )


def validate_residuals_carried_forward(receipt: dict[str, Any], root: Path, state: dict[str, Any] | None = None) -> None:
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)
    a5_receipt = _load(A5_RECEIPT_PATH)
    a6_receipt = _load(A6_RECEIPT_PATH)
    a7_receipt = _load(A7_RECEIPT_PATH)
    a8_receipt = _load(A8_RECEIPT_PATH)
    a9_receipt = _load(A9_RECEIPT_PATH)
    a10_receipt = _load(A10_RECEIPT_PATH)
    a11_receipt = _load(A11_RECEIPT_PATH)
    a12_receipt = _load(A12_RECEIPT_PATH)
    manifest = _load(SLOT_MANIFEST_PATH)
    state = check_cleanup_recovery_state(root) if state is None else state

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
        ("A12", {e["residual_id"] for e in a12_receipt["a12_residuals"]}, receipt["a12_residuals_carried_forward"]),
    ):
        carried_ids = {entry["residual_id"] for entry in carried}
        require(carried_ids == source_ids, f"{stage.lower()}_residuals_carried_forward does not reproduce from {stage} -- refusing")
        for entry in carried:
            require(
                entry["origin_stage"] == stage and entry["status"] == "unresolved_carried_to_a13",
                f"{stage.lower()}_residuals_carried_forward entry has an unexpected origin_stage/status -- refusing",
            )

    expected_a13_residuals = derive_a13_slot_residuals(manifest, a2_receipt, state)
    require(receipt["a13_residuals"] == expected_a13_residuals, "a13_residuals does not reproduce from the live slot manifest, A2 receipt, and recovery state -- refusing")


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
    require(receipt["eligibility"] == CLEANUP_RECOVERY_ELIGIBILITY, "receipt eligibility does not equal the frozen all-false cleanup-recovery eligibility -- refusing")
    safety = receipt["safety_assertions"]
    require(
        safety["rows_not_admitted"] is True and all(value is False for key, value in safety.items() if key != "rows_not_admitted"),
        "receipt safety_assertions does not hold the expected invariants -- refusing",
    )
    require(receipt["execution_counters"]["dataset_rows_emitted"] == 0, "receipt execution_counters.dataset_rows_emitted is not 0 -- refusing")
    require(receipt["execution_counters"]["temp_outputs_reaped"] == 0, "receipt execution_counters.temp_outputs_reaped is not 0 -- refusing (this module declares policy, it never executes cleanup)")
    require(receipt["execution_counters"]["forbidden_paths_touched"] == 0, "receipt execution_counters.forbidden_paths_touched is not 0 -- refusing")
    require(receipt["execution_counters"]["frozen_slot_count"] == 100, "receipt execution_counters.frozen_slot_count is not 100 -- refusing")


def validate_receipt_independently(receipt: dict[str, Any], root: Path = ROOT) -> None:
    # check_cleanup_recovery_state re-validates the entire upstream A2..A12
    # receipt chain (each stage's own validate_receipt_independently in
    # turn re-validates its own upstream chain), so it is computed once here
    # and threaded through every sub-validator that needs it, rather than
    # each sub-validator recomputing it independently.
    state = check_cleanup_recovery_state(root)
    validate_bindings_hash_to_disk(receipt, root)
    validate_bound_to_merged_a12_receipt(receipt)
    validate_recovery_state_matches_receipt(receipt, root, state)
    validate_frozen_slot_denominator(receipt, root)
    validate_cleanup_policy(receipt)
    validate_named_residual(receipt, root, state)
    validate_engine_wiring(receipt)
    validate_residuals_carried_forward(receipt, root, state)
    validate_no_forbidden_keys(receipt)
    validate_no_forbidden_completion_claims(receipt)
    validate_eligibility_and_safety_all_false(receipt)
    validate_receipt_schema(receipt)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--receipt", type=Path, default=A13_RECEIPT_PATH, help="A13 receipt JSON to verify (default: the tracked V4 A13 cleanup/recovery receipt).")
    parser.add_argument("--write-receipt", action="store_true", help="Assemble and persist a freshly computed receipt to --receipt.")
    args = parser.parse_args(argv)

    if args.write_receipt:
        receipt = build_receipt()
        validate_receipt_independently(receipt)
        args.receipt.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        print(canonical_json({"status": receipt["status"], "recovery_state": receipt["recovery_state"]}))
        return

    receipt = _load(args.receipt)
    validate_receipt_independently(receipt)
    print(canonical_json({"status": receipt["status"], "recovery_state": receipt["recovery_state"]}))


if __name__ == "__main__":
    try:
        main()
    except CleanupRecoveryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
