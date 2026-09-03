#!/usr/bin/env python3
"""V4 A7 independent original-row factory: source-derived candidate rows/cases
with independent construction and lineage, wired to (never replacing) the
shared ``v4_original_row_admission`` engine and bound to the merged A6 blind
arena receipt.

A7 owns the *original row factory* role (``role_ownership.A7 ==
"original_row_factory"`` in the frozen slot manifest): the one place a real,
independently authored or independently constructed source-derived row would
be built and submitted to the shared admission engine. It must never see
held-out membership, never create gold, and never let a model-agreement /
arena-vote basis stand in for independent construction -- the shared engine
(``v4_original_row_admission.evaluate_row``) already refuses that
(``MODEL_ONLY_BASES``); this module wires that refusal into the V4 pilot
without loosening it.

This module never loads source text, never re-fetches corpus, and never opens
A3's held-out membership file or A4's private extraction ledger: its only
inputs are five already-public artifacts --

* A2's source operation admission receipt (``stratum_coverage_map`` and
  ``residuals`` -- rights/coverage state, never source text),
* A4's deterministic extraction receipt (only its own already-carried
  residuals, never A4's private ledger),
* A5's evidence enrichment receipt (already-carried residuals only),
* A6's blind arena receipt (already-carried residuals, and its own gate
  state as the direct upstream signal this module's gate builds on), and
* the frozen 100-slot V4 pilot slot manifest (``slot_series`` -- public slot
  IDs only, never a real ``source_unit_id``).

Two independent parts:

1. ``check_factory_gate`` -- independently re-derives, from those five public
   artifacts alone, whether a real independently-constructed row may be
   produced at all. Right now it cannot: every frozen slot is still
   ``UNASSIGNED_PENDING_A2_A3`` and A2 still carries eight unresolved
   rights/coverage residuals -- so no source-derived row could be built
   without either transmitting a still-unresolved-rights source or
   inventing one. Per the binding contract this module must *never* claim
   the row-ready status while that is true; it reports
   ``factory_slice_ready: false`` and a typed ``blocked_reason_code``
   instead.
2. ``build_receipt`` -- assembles the public receipt: the frozen 100-slot
   denominator (reusing, never duplicating,
   ``v4_a6_blind_arena.frozen_slot_strata``/``all_frozen_slot_ids``), the
   gate, a real (zero-row) call into the shared
   ``v4_original_row_admission.admit_rows`` engine proving the wiring is
   live rather than declarative, every A2/A4/A5/A6 residual carried forward
   unresolved, and one typed per-slot A7 residual -- ``rights_unknown``,
   ``source_incomplete``, or ``independence_unavailable`` -- derived
   deterministically from A2's own public ``stratum_coverage_map``, never a
   silently dropped slot and never a synthesized row standing in for the
   missing independent construction.

Run with no arguments to verify the checked-in A7 receipt reproduces from the
five public artifacts on disk -- no ``batch_state/`` required, so this passes
in a fresh checkout. Pass ``--write-receipt`` to (re)assemble and persist it
after a genuine change to one of those five artifacts or to this module or
the shared admission engine.
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

from scripts.projects.open_model_data import v4_a6_blind_arena as a6
from scripts.projects.open_model_data import v4_original_row_admission as admission

ROOT = _SELF_ROOT
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"

A7_RECEIPT_PATH = ADMISSION / "dataset_v4_a7_original_row_factory_receipt_v1.json"
A7_SCHEMA_PATH = CONTRACTS / "dataset_v4_a7_original_row_factory_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_PATH = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
A6_RECEIPT_PATH = ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json"
SLOT_MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"
ADMISSION_ENGINE_PATH = ROOT / "scripts/projects/open_model_data/v4_original_row_admission.py"
SELF_PATH = ROOT / "scripts/projects/open_model_data/v4_a7_original_row_factory.py"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

# Mirrors v4_a6_blind_arena.FORBIDDEN_KEYS exactly -- "gold" is deliberately
# excluded because it is the name of this receipt's own always-false
# eligibility flag, never a real gold label.
FORBIDDEN_KEYS = a6.FORBIDDEN_KEYS
FORBIDDEN_SUBSTRINGS = a6.FORBIDDEN_SUBSTRINGS

# Completion-vocabulary claims that belong to other roles or are unreachable
# today -- never emitted here (see the manifest's own completion_vocabulary
# and A0's non_goals). Checked defensively against the serialized receipt in
# addition to the status enum, so a future edit cannot slip one in through a
# free-text field.
FORBIDDEN_COMPLETION_CLAIMS = ("TRAINING_READY_SILVER", "ARENA_SLICE_READY", "TRAINING_READY_GOLD_SUBSET", "GOLD_UPGRADE_READY")

FACTORY_ELIGIBILITY = {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}

canonical_json = a6.canonical_json
sha256_text = a6.sha256_text
sha256_file = a6.sha256_file


class OriginalRowFactoryError(ValueError):
    """The A7 wiring or its deterministic receipt is unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise OriginalRowFactoryError(message)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# --- A2 stratum reason -> A7 per-slot residual reason ------------------------
#
# A2's own stratum_coverage_map already types each stratum's blocker as one of
# three reason codes. This module never invents a fourth: "coverage_blocked"
# (a stratum with an identified supporting source unit whose coverage/rights
# review is not yet complete) maps to "independence_unavailable" -- a real
# source exists but no independently constructed row can be safely derived
# from it yet -- while "rights_unknown" and "source_incomplete" pass through
# unchanged.
A2_REASON_TO_A7_REASON = {
    "rights_unknown": "rights_unknown",
    "source_incomplete": "source_incomplete",
    "coverage_blocked": "independence_unavailable",
}

A7_NEXT_ACTION_BY_REASON = {
    "rights_unknown": (
        "no independently authored or independently constructed row may be produced for this frozen slot "
        "until A2 resolves unit-specific training/derivation rights for its stratum's supporting source unit "
        "-- never derive a row while rights remain unknown"
    ),
    "source_incomplete": (
        "no source unit is yet identified for this frozen slot's stratum -- never invent or substitute a "
        "placeholder source; wait for A2/A3 to identify or lawfully acquire a real source"
    ),
    "independence_unavailable": (
        "a supporting source unit is identified for this frozen slot's stratum but its coverage/rights review "
        "is not yet complete, so no independently constructed row can be safely derived from it yet"
    ),
}


def stratum_reason_codes(a2_receipt: dict[str, Any]) -> dict[str, str]:
    """Pure function of A2's own public ``residuals`` and
    ``stratum_coverage_map`` -- never opens any private state. Fails closed
    if a stratum's coverage entry does not resolve to exactly one already-
    known A2 reason code (drift this module must not silently paper over)."""
    reason_by_residual_id = {entry["residual_id"]: entry["reason_code"] for entry in a2_receipt["residuals"]}
    resolved: dict[str, str] = {}
    for coverage in a2_receipt["stratum_coverage_map"]:
        stratum = coverage["stratum"]
        reasons = {reason_by_residual_id[rid] for rid in coverage["residual_ids"] if rid in reason_by_residual_id}
        require(len(reasons) == 1, f"A2 stratum_coverage_map entry {stratum!r} does not resolve to exactly one reason code -- refusing")
        (reason,) = reasons
        require(reason in A2_REASON_TO_A7_REASON, f"A2 stratum_coverage_map entry {stratum!r} carries an unmapped reason code {reason!r} -- refusing")
        resolved[stratum] = A2_REASON_TO_A7_REASON[reason]
    return resolved


# --- factory gate (public-only) ----------------------------------------------


def check_factory_gate(root: Path = ROOT) -> dict[str, Any]:
    """Independently re-derive whether a real, source-derived, independently
    constructed row may be produced at all, from the frozen slot manifest's
    own ``assignment_state`` per stratum, A2's own residuals, and A6's
    independent validity -- never trusting the A7 receipt's own declared
    fields, never opening ``batch_state/``. ``factory_slice_ready`` is only
    ever true once every frozen slot is assigned to a real source unit *and*
    A2 has zero unresolved residuals *and* A6 itself still independently
    validates.

    Fails closed -- a *closed gate*, not an exception -- if any of the three
    required public artifacts (slot manifest, A2 receipt, A6 receipt) is
    missing, mirroring ``v4_a6_blind_arena.check_arena_gate``'s own missing-
    artifact handling."""
    manifest_path = (root / "data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json").resolve()
    a2_path = (root / "data/projects/open_model_data/admission/dataset_v4_a2_source_operation_admission_receipt_v1.json").resolve()
    a6_path = (root / "data/projects/open_model_data/admission/dataset_v4_a6_blind_arena_receipt_v1.json").resolve()
    required_paths = {"slot_manifest": manifest_path, "a2_receipt": a2_path, "a6_receipt": a6_path}
    for label, path in required_paths.items():
        require(root.resolve() in path.parents, f"{label} path escapes the repository root -- refusing")

    missing = sorted(label for label, path in required_paths.items() if not path.is_file())
    if missing:
        return {
            "gate_id": "v4-a7-factory-gate-v1",
            "a6_receipt_valid": False,
            "a2_rights_resolved": False,
            "all_slots_assigned": False,
            "factory_slice_ready": False,
            "owner_role": "A2_A3_PRIVATE_ARTIFACT",
            "blocked_reason_code": f"required_public_artifact_missing:{missing[0]}",
        }

    manifest = _load(manifest_path)
    require(manifest.get("controlling_outcome_sha256") == V4_SHA256, "slot manifest is not bound to the expected V4 controlling outcome -- refusing")

    a2_receipt = _load(a2_path)
    require(a2_receipt.get("controlling_outcome_sha256") == V4_SHA256, "A2 receipt is not bound to the expected V4 controlling outcome -- refusing")
    rights_resolved = len(a2_receipt.get("residuals", [])) == 0

    all_assigned = all(series["assignment_state"] == "ASSIGNED" for series in manifest["slot_series"])

    a6_receipt = _load(a6_path)
    try:
        a6.validate_receipt_independently(a6_receipt, root)
        a6_valid = True
    except a6.ArenaWiringError:
        a6_valid = False

    factory_slice_ready = rights_resolved and all_assigned and a6_valid
    blocked_reason_code = None
    if not factory_slice_ready:
        if not a6_valid:
            blocked_reason_code = "a6_receipt_invalid"
        elif not rights_resolved and not all_assigned:
            blocked_reason_code = "rights_unresolved_and_slots_unassigned"
        elif not rights_resolved:
            blocked_reason_code = "rights_unresolved"
        else:
            blocked_reason_code = "slot_assignment_pending_a2_a3"

    return {
        "gate_id": "v4-a7-factory-gate-v1",
        "a6_receipt_valid": a6_valid,
        "a2_rights_resolved": rights_resolved,
        "all_slots_assigned": all_assigned,
        "factory_slice_ready": factory_slice_ready,
        "owner_role": manifest["sealed_heldout_commitment"]["assignment_owner"],
        "blocked_reason_code": blocked_reason_code,
    }


# --- A7's own per-slot residuals (public, source-free) -----------------------


def derive_a7_slot_residuals(manifest: dict[str, Any], a2_receipt: dict[str, Any], gate: dict[str, Any]) -> list[dict[str, Any]]:
    """One typed residual per frozen public slot ID -- never a silently
    dropped slot and never a synthesized row standing in for the missing
    independent construction. A pure function of the manifest's own
    ``slot_series``, A2's own public reason codes, and the gate this module
    itself re-derives; never opens any private state."""
    owner_role = gate["owner_role"]
    reasons_by_stratum = stratum_reason_codes(a2_receipt)
    residuals = []
    for stratum_entry in a6.frozen_slot_strata(manifest):
        stratum = stratum_entry["stratum"]
        reason_code = reasons_by_stratum[stratum]
        for slot_id in stratum_entry["slot_ids"]:
            residuals.append(
                {
                    "residual_id": f"a7-residual-{reason_code.replace('_', '-')}-{slot_id}",
                    "subject_kind": "pilot_slot",
                    "subject_id": slot_id,
                    "stage": "A7",
                    "reason_code": reason_code,
                    "owner_role": owner_role,
                    "next_action": A7_NEXT_ACTION_BY_REASON[reason_code],
                    "retryability": "retryable",
                    "evidence_refs": [
                        "admission.dataset_v4_pilot_slot_manifest_v1.slot_series",
                        "admission.dataset_v4_a2_source_operation_admission_receipt_v1.stratum_coverage_map",
                        "admission.dataset_v4_a6_blind_arena_receipt_v1.a6_residuals",
                    ],
                }
            )
    residuals.sort(key=lambda residual: residual["subject_id"])
    return residuals


# --- shared engine wiring (real call, zero rows today) ------------------------


def run_engine_admission(rows: list[dict[str, Any]] = ()) -> dict[str, Any]:  # type: ignore[assignment]
    """A real (never stubbed) call into the shared, already-on-main
    ``v4_original_row_admission.admit_rows`` engine, bound to the V4
    controlling outcome. Today there is no independently constructed,
    rights-cleared row to submit, so ``rows`` stays empty and the engine's
    own ``dataset_rows_emitted``-equivalent counters (``admitted_rows``,
    ``rejected_rows``) both come back 0 -- proving the wiring is live, never
    fabricating a row to exercise it."""
    return admission.admit_rows(outcome_sha256=V4_SHA256, rows=list(rows))


# --- receipt assembly --------------------------------------------------------


def build_receipt(root: Path = ROOT) -> dict[str, Any]:
    manifest = _load(SLOT_MANIFEST_PATH)
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)
    a5_receipt = _load(A5_RECEIPT_PATH)
    a6_receipt = _load(A6_RECEIPT_PATH)
    gate = check_factory_gate(root)

    strata = a6.frozen_slot_strata(manifest)
    frozen_slot_ids = a6.all_frozen_slot_ids(manifest)

    a2_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A2", "status": "unresolved_carried_to_a7"}
        for entry in a2_receipt["residuals"]
    ]
    a4_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A4", "status": "unresolved_carried_to_a7"}
        for entry in a4_receipt["a4_residuals"]
    ]
    a5_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A5", "status": "unresolved_carried_to_a7"}
        for entry in a5_receipt["a5_residuals"]
    ]
    a6_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A6", "status": "unresolved_carried_to_a7"}
        for entry in a6_receipt["a6_residuals"]
    ]

    engine_admission_receipt = run_engine_admission([])

    return {
        "schema_version": "dataset_v4_a7_original_row_factory_receipt_v1",
        "receipt_id": "dataset-v4-a7-original-row-factory-v1",
        "status": (
            "A7_ORIGINAL_ROW_FACTORY_AND_PARSER_READY_ROWS_NOT_READY_TEXT_FREE_NO_MODEL_SILVER"
            if not gate["factory_slice_ready"]
            else "ORIGINAL_ROWS_READY"
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
            "pilot_slot_manifest": {
                "path": str(SLOT_MANIFEST_PATH.relative_to(root)),
                "sha256": sha256_file(SLOT_MANIFEST_PATH),
                "schema_version": "dataset_v4_pilot_slot_manifest_v1",
            },
            "admission_engine_implementation": {
                "path": str(ADMISSION_ENGINE_PATH.relative_to(root)),
                "sha256": sha256_file(ADMISSION_ENGINE_PATH),
                "schema_version": "v4_original_row_admission_script_v1",
            },
            "wiring_implementation": {
                "path": str(SELF_PATH.relative_to(root)),
                "sha256": sha256_file(SELF_PATH),
                "schema_version": "v4_a7_original_row_factory_script_v1",
            },
        },
        "role_map": manifest["role_ownership"],
        "frozen_slot_denominator": {"total_slots": len(frozen_slot_ids), "strata": strata},
        "factory_gate": {
            "gate_id": gate["gate_id"],
            "requires": ["a6_receipt_independently_valid", "a2_rights_fully_resolved", "all_frozen_slots_assigned"],
            "a6_receipt_valid": gate["a6_receipt_valid"],
            "a2_rights_resolved": gate["a2_rights_resolved"],
            "all_slots_assigned": gate["all_slots_assigned"],
            "factory_slice_ready": gate["factory_slice_ready"],
            "owner_role": gate["owner_role"],
            "blocked_reason_code": gate["blocked_reason_code"],
        },
        "engine_wiring": {
            "engine_schema_version": admission.SCHEMA_VERSION,
            "engine_input_schema_version": admission.INPUT_SCHEMA_VERSION,
            "model_only_bases_blocked": sorted(admission.MODEL_ONLY_BASES),
            "admission_receipt": engine_admission_receipt,
        },
        "a2_residuals_carried_forward": a2_residuals_carried,
        "a4_residuals_carried_forward": a4_residuals_carried,
        "a5_residuals_carried_forward": a5_residuals_carried,
        "a6_residuals_carried_forward": a6_residuals_carried,
        "a7_residuals": derive_a7_slot_residuals(manifest, a2_receipt, gate),
        "execution_counters": {
            "dataset_rows_emitted": engine_admission_receipt["counts"]["admitted_rows"],
            "candidate_rows_constructed": engine_admission_receipt["counts"]["input_rows"],
            "frozen_slot_count": len(frozen_slot_ids),
            "slots_factory_ready": len(frozen_slot_ids) if gate["factory_slice_ready"] else 0,
            "slots_blocked": 0 if gate["factory_slice_ready"] else len(frozen_slot_ids),
        },
        "eligibility": dict(FACTORY_ELIGIBILITY),
        "safety_assertions": {
            "rows_not_admitted": True,
            "text_emitted": False,
            "source_text_loaded_into_model": False,
            "corpus_refetched": False,
            "held_out_membership_referenced": False,
            "gold_created": False,
            "silver_admitted_from_model_votes": False,
            "training_ready_silver_claimed": False,
            "arena_slice_ready_claimed": False,
            "mac_corpus_copy_created": False,
            "epic_done_claimed": False,
            "heldout_family_identity_leaked": False,
        },
    }


# --- receipt verification ---------------------------------------------------


def _load_schema() -> dict[str, Any]:
    schema = _load(A7_SCHEMA_PATH)
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


def validate_gate_matches_receipt(receipt: dict[str, Any], root: Path) -> None:
    gate = check_factory_gate(root)
    declared = receipt["factory_gate"]
    require(
        declared["a6_receipt_valid"] == gate["a6_receipt_valid"]
        and declared["a2_rights_resolved"] == gate["a2_rights_resolved"]
        and declared["all_slots_assigned"] == gate["all_slots_assigned"]
        and declared["factory_slice_ready"] == gate["factory_slice_ready"]
        and declared["blocked_reason_code"] == gate["blocked_reason_code"],
        "receipt factory_gate does not match the state independently re-derived from the live public artifacts "
        "-- refusing (re-verify/regenerate required)",
    )
    require(
        gate["factory_slice_ready"] or receipt["status"] != "ORIGINAL_ROWS_READY",
        "receipt claims ORIGINAL_ROWS_READY while the independently re-derived gate is closed -- refusing",
    )


def validate_frozen_slot_denominator(receipt: dict[str, Any], root: Path) -> None:
    manifest = _load(SLOT_MANIFEST_PATH)
    expected_strata = a6.frozen_slot_strata(manifest)
    declared = receipt["frozen_slot_denominator"]
    require(declared["strata"] == expected_strata, "frozen_slot_denominator.strata does not reproduce from the live slot manifest -- refusing")
    all_ids = [slot_id for stratum in expected_strata for slot_id in stratum["slot_ids"]]
    require(len(all_ids) == 100 and len(set(all_ids)) == 100, "frozen slot denominator did not expand to exactly 100 unique slot IDs -- refusing")
    require(declared["total_slots"] == 100, "frozen_slot_denominator.total_slots is not 100 -- refusing")


def validate_engine_wiring(receipt: dict[str, Any]) -> None:
    """Re-runs the real shared engine call and requires a byte-identical
    result, plus makes the engine independently verify its own nested
    receipt (``v4_original_row_admission.verify_receipt``) -- proving this is
    a live wire into the on-main engine, not a declared/stubbed shape."""
    wiring = receipt["engine_wiring"]
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
        "engine_wiring.admission_receipt does not report zero rows -- refusing (no rights-cleared, independently "
        "constructed row exists yet; dataset_rows_emitted must stay 0)",
    )


def validate_residuals_carried_from_a2_a4_a5_a6(receipt: dict[str, Any], root: Path) -> None:
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)
    a5_receipt = _load(A5_RECEIPT_PATH)
    a6_receipt = _load(A6_RECEIPT_PATH)
    manifest = _load(SLOT_MANIFEST_PATH)
    gate = check_factory_gate(root)

    for stage, source_ids, carried in (
        ("A2", {e["residual_id"] for e in a2_receipt["residuals"]}, receipt["a2_residuals_carried_forward"]),
        ("A4", {e["residual_id"] for e in a4_receipt["a4_residuals"]}, receipt["a4_residuals_carried_forward"]),
        ("A5", {e["residual_id"] for e in a5_receipt["a5_residuals"]}, receipt["a5_residuals_carried_forward"]),
        ("A6", {e["residual_id"] for e in a6_receipt["a6_residuals"]}, receipt["a6_residuals_carried_forward"]),
    ):
        carried_ids = {entry["residual_id"] for entry in carried}
        require(carried_ids == source_ids, f"{stage.lower()}_residuals_carried_forward does not reproduce from {stage} -- refusing")
        for entry in carried:
            require(
                entry["origin_stage"] == stage and entry["status"] == "unresolved_carried_to_a7",
                f"{stage.lower()}_residuals_carried_forward entry has an unexpected origin_stage/status -- refusing",
            )

    expected_a7_residuals = derive_a7_slot_residuals(manifest, a2_receipt, gate)
    require(receipt["a7_residuals"] == expected_a7_residuals, "a7_residuals does not reproduce from the live slot manifest, A2 receipt, and gate -- refusing")


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
    require(receipt["eligibility"] == FACTORY_ELIGIBILITY, "receipt eligibility does not equal the frozen all-false factory eligibility -- refusing")
    safety = receipt["safety_assertions"]
    require(
        safety["rows_not_admitted"] is True and all(value is False for key, value in safety.items() if key != "rows_not_admitted"),
        "receipt safety_assertions does not hold the expected invariants -- refusing",
    )
    require(receipt["execution_counters"]["dataset_rows_emitted"] == 0, "receipt execution_counters.dataset_rows_emitted is not 0 -- refusing")


def validate_receipt_independently(receipt: dict[str, Any], root: Path = ROOT) -> None:
    validate_bindings_hash_to_disk(receipt, root)
    validate_gate_matches_receipt(receipt, root)
    validate_frozen_slot_denominator(receipt, root)
    validate_engine_wiring(receipt)
    validate_residuals_carried_from_a2_a4_a5_a6(receipt, root)
    validate_no_forbidden_keys(receipt)
    validate_no_forbidden_completion_claims(receipt)
    validate_eligibility_and_safety_all_false(receipt)
    validate_receipt_schema(receipt)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--receipt", type=Path, default=A7_RECEIPT_PATH, help="A7 receipt JSON to verify (default: the tracked V4 A7 original-row factory receipt).")
    parser.add_argument("--write-receipt", action="store_true", help="Assemble and persist a freshly computed receipt to --receipt.")
    args = parser.parse_args(argv)

    if args.write_receipt:
        receipt = build_receipt()
        validate_receipt_independently(receipt)
        args.receipt.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        print(canonical_json({"status": receipt["status"], "factory_gate": receipt["factory_gate"]}))
        return

    receipt = _load(args.receipt)
    validate_receipt_independently(receipt)
    print(canonical_json({"status": receipt["status"], "factory_gate": receipt["factory_gate"]}))


if __name__ == "__main__":
    try:
        main()
    except OriginalRowFactoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
