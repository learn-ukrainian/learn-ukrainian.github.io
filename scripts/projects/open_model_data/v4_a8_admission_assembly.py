#!/usr/bin/env python3
"""V4 A8 admission/assembly: the admitted-slice assembly, schema checks, and
residual-attachment layer bound to the merged A7 original-row factory
receipt, the frozen V4 pilot slot manifest, and the V4 SHA.

A8 owns the *admission_assembly* role (``role_ownership.A8 ==
"admission_assembly"`` in the frozen slot manifest): the one place an
already-admitted, rights-cleared silver/gold row -- built by A7's factory and
run through the shared ``v4_original_row_admission`` engine -- would be
assembled into the pilot's append-only, per-slot admitted view. It must
never waive the shared engine's contract/privacy gates, never admit silver
from a model-agreement / arena-vote / model-vote basis (the engine's own
``MODEL_ONLY_BASES`` refusal, wired here unmodified), and never invent
coverage for a frozen slot that has no admitted row -- a gap is a typed
residual, never a silently-renamed ``not_applicable``.

This module never loads source text, never re-fetches corpus, never opens
A3's held-out membership file, and never opens A4's private extraction
ledger: its only inputs are six already-public artifacts --

* A2's source operation admission receipt (``stratum_coverage_map`` and
  ``residuals`` -- rights/coverage state, never source text),
* A4's deterministic extraction receipt (only its own already-carried
  residuals, never A4's private ledger),
* A5's evidence enrichment receipt (already-carried residuals only),
* A6's blind arena receipt (already-carried residuals only),
* A7's original-row factory receipt (already-carried residuals, its own
  zero-row engine admission receipt, and its own gate state as the direct
  upstream signal this module's gate builds on), and
* the frozen 100-slot V4 pilot slot manifest (``slot_series`` -- public slot
  IDs only, never a real ``source_unit_id``).

Two independent parts:

1. ``check_assembly_gate`` -- independently re-derives, from those six public
   artifacts alone, whether a real admitted slice may be assembled at all.
   Right now it cannot: A7 itself reports ``factory_slice_ready: false``
   (every frozen slot is still ``UNASSIGNED_PENDING_A2_A3`` and A2 still
   carries eight unresolved rights/coverage residuals), so A7's own engine
   call admitted zero rows -- there is nothing rights-cleared to assemble.
   Per the binding contract this module must *never* claim
   ``ADMITTED_SLICE_READY`` while that is true; it reports
   ``assembly_slice_ready: false`` and a typed ``blocked_reason_code``
   instead.
2. ``build_receipt`` -- assembles the public receipt: the frozen 100-slot
   denominator (reusing, never duplicating,
   ``v4_a6_blind_arena.frozen_slot_strata``/``all_frozen_slot_ids``), the
   gate, a real (zero-row) call into the shared, unmodified
   ``v4_original_row_admission.admit_rows`` engine proving A8's own wiring is
   live rather than declarative, every A2/A4/A5/A6/A7 residual carried
   forward unresolved, an append-only per-slot ``admitted_slice_view`` (empty
   of rows today, one typed residual reference per slot -- never a row and
   never a dropped slot), and one typed per-slot A8 residual reusing A7's own
   already-public per-stratum reason codes -- never a fourth, independently
   invented reason.

Run with no arguments to verify the checked-in A8 receipt reproduces from the
six public artifacts on disk -- no ``batch_state/`` required, so this passes
in a fresh checkout. Pass ``--write-receipt`` to (re)assemble and persist it
after a genuine change to one of those six artifacts or to this module or the
shared admission engine.
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

from scripts.projects.open_model_data import v4_a7_original_row_factory as a7
from scripts.projects.open_model_data import v4_original_row_admission as admission

ROOT = _SELF_ROOT
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"

A8_RECEIPT_PATH = ADMISSION / "dataset_v4_a8_admission_assembly_receipt_v1.json"
A8_SCHEMA_PATH = CONTRACTS / "dataset_v4_a8_admission_assembly_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_PATH = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
A6_RECEIPT_PATH = ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json"
A7_RECEIPT_PATH = ADMISSION / "dataset_v4_a7_original_row_factory_receipt_v1.json"
SLOT_MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"
ADMISSION_ENGINE_PATH = ROOT / "scripts/projects/open_model_data/v4_original_row_admission.py"
SELF_PATH = ROOT / "scripts/projects/open_model_data/v4_a8_admission_assembly.py"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

# Mirrors v4_a7_original_row_factory.FORBIDDEN_KEYS exactly -- "gold" is
# deliberately excluded because it is the name of this receipt's own
# always-false eligibility flag, never a real gold label.
FORBIDDEN_KEYS = a7.FORBIDDEN_KEYS
FORBIDDEN_SUBSTRINGS = a7.FORBIDDEN_SUBSTRINGS

# Completion-vocabulary claims that belong to other roles or are unreachable
# today (see the manifest's own completion_vocabulary and A0's non_goals) --
# never emitted here, and never a "stronger release state than evidence".
FORBIDDEN_COMPLETION_CLAIMS = (
    "TRAINING_READY_SILVER",
    "ARENA_SLICE_READY",
    "EVAL_ARTIFACT_READY",
    "TRAINING_READY_GOLD_SUBSET",
    "GOLD_UPGRADE_READY",
)

ASSEMBLY_ELIGIBILITY = {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}

canonical_json = a7.canonical_json
sha256_text = a7.sha256_text
sha256_file = a7.sha256_file


class AdmissionAssemblyError(ValueError):
    """The A8 wiring or its deterministic receipt is unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AdmissionAssemblyError(message)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# --- A7 reason -> A8 per-slot residual reason --------------------------------
#
# A7 already types each frozen slot's blocker as one of three reason codes
# (see ``v4_a7_original_row_factory.stratum_reason_codes``, itself derived
# from A2's own public ``stratum_coverage_map``). A8 never invents a fourth
# reason -- it reuses A7's own mapping unchanged, because "why has A7 not
# admitted a row for this slot" is exactly "why can A8 not assemble one".
A8_NEXT_ACTION_BY_REASON = {
    "rights_unknown": (
        "no rights-cleared row exists to assemble for this frozen slot until A2 resolves unit-specific "
        "training/derivation rights for its stratum's supporting source unit -- never assemble a row while "
        "rights remain unknown"
    ),
    "source_incomplete": (
        "no source unit is yet identified for this frozen slot's stratum, so A7's factory has nothing to admit "
        "and A8 has nothing to assemble -- never invent or substitute a placeholder row"
    ),
    "independence_unavailable": (
        "a supporting source unit is identified for this frozen slot's stratum but its coverage/rights review "
        "is not yet complete, so A7 admitted no row for it and A8 has nothing to assemble yet"
    ),
}


# --- assembly gate (public-only) ---------------------------------------------


def check_assembly_gate(root: Path = ROOT) -> dict[str, Any]:
    """Independently re-derive whether a real admitted slice may be
    assembled at all, from the frozen slot manifest's own
    ``assignment_state`` per stratum, A2's own residuals, and A7's
    independent validity -- never trusting the A8 receipt's own declared
    fields, never opening ``batch_state/``. ``assembly_slice_ready`` is only
    ever true once every frozen slot is assigned to a real source unit *and*
    A2 has zero unresolved residuals *and* A7 itself still independently
    validates.

    Fails closed -- a *closed gate*, not an exception -- if any of the three
    required public artifacts (slot manifest, A2 receipt, A7 receipt) is
    missing, mirroring ``v4_a7_original_row_factory.check_factory_gate``'s
    own missing-artifact handling."""
    manifest_path = (root / "data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json").resolve()
    a2_path = (root / "data/projects/open_model_data/admission/dataset_v4_a2_source_operation_admission_receipt_v1.json").resolve()
    a7_path = (root / "data/projects/open_model_data/admission/dataset_v4_a7_original_row_factory_receipt_v1.json").resolve()
    required_paths = {"slot_manifest": manifest_path, "a2_receipt": a2_path, "a7_receipt": a7_path}
    for label, path in required_paths.items():
        require(root.resolve() in path.parents, f"{label} path escapes the repository root -- refusing")

    missing = sorted(label for label, path in required_paths.items() if not path.is_file())
    if missing:
        return {
            "gate_id": "v4-a8-assembly-gate-v1",
            "a7_receipt_valid": False,
            "a2_rights_resolved": False,
            "all_slots_assigned": False,
            "assembly_slice_ready": False,
            "owner_role": "A2_A3_PRIVATE_ARTIFACT",
            "blocked_reason_code": f"required_public_artifact_missing:{missing[0]}",
        }

    manifest = _load(manifest_path)
    require(manifest.get("controlling_outcome_sha256") == V4_SHA256, "slot manifest is not bound to the expected V4 controlling outcome -- refusing")

    a2_receipt = _load(a2_path)
    require(a2_receipt.get("controlling_outcome_sha256") == V4_SHA256, "A2 receipt is not bound to the expected V4 controlling outcome -- refusing")
    rights_resolved = len(a2_receipt.get("residuals", [])) == 0

    all_assigned = all(series["assignment_state"] == "ASSIGNED" for series in manifest["slot_series"])

    a7_receipt = _load(a7_path)
    try:
        a7.validate_receipt_independently(a7_receipt, root)
        a7_valid = True
    except a7.OriginalRowFactoryError:
        a7_valid = False

    assembly_slice_ready = rights_resolved and all_assigned and a7_valid
    blocked_reason_code = None
    if not assembly_slice_ready:
        if not a7_valid:
            blocked_reason_code = "a7_receipt_invalid"
        elif not rights_resolved and not all_assigned:
            blocked_reason_code = "rights_unresolved_and_slots_unassigned"
        elif not rights_resolved:
            blocked_reason_code = "rights_unresolved"
        else:
            blocked_reason_code = "slot_assignment_pending_a2_a3"

    return {
        "gate_id": "v4-a8-assembly-gate-v1",
        "a7_receipt_valid": a7_valid,
        "a2_rights_resolved": rights_resolved,
        "all_slots_assigned": all_assigned,
        "assembly_slice_ready": assembly_slice_ready,
        "owner_role": manifest["sealed_heldout_commitment"]["assignment_owner"],
        "blocked_reason_code": blocked_reason_code,
    }


# --- A8's own per-slot residuals (public, source-free) -----------------------


def derive_a8_slot_residuals(manifest: dict[str, Any], a2_receipt: dict[str, Any], gate: dict[str, Any]) -> list[dict[str, Any]]:
    """One typed residual per frozen public slot ID -- never a silently
    dropped slot and never coverage invented by renaming a gap
    ``not_applicable``. A pure function of the manifest's own
    ``slot_series``, A7's own already-public per-stratum reason codes, and
    the gate this module itself re-derives; never opens any private state."""
    owner_role = gate["owner_role"]
    reasons_by_stratum = a7.stratum_reason_codes(a2_receipt)
    residuals = []
    for stratum_entry in a7.a6.frozen_slot_strata(manifest):
        stratum = stratum_entry["stratum"]
        reason_code = reasons_by_stratum[stratum]
        for slot_id in stratum_entry["slot_ids"]:
            residuals.append(
                {
                    "residual_id": f"a8-residual-{reason_code.replace('_', '-')}-{slot_id}",
                    "subject_kind": "pilot_slot",
                    "subject_id": slot_id,
                    "stage": "A8",
                    "reason_code": reason_code,
                    "owner_role": owner_role,
                    "next_action": A8_NEXT_ACTION_BY_REASON[reason_code],
                    "retryability": "retryable",
                    "evidence_refs": [
                        "admission.dataset_v4_pilot_slot_manifest_v1.slot_series",
                        "admission.dataset_v4_a2_source_operation_admission_receipt_v1.stratum_coverage_map",
                        "admission.dataset_v4_a7_original_row_factory_receipt_v1.a7_residuals",
                    ],
                }
            )
    residuals.sort(key=lambda residual: residual["subject_id"])
    return residuals


# --- append-only per-slot admitted view (public, source-free) ----------------


def build_admitted_slice_view(manifest: dict[str, Any], a8_residuals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One entry per frozen slot ID -- ``row_admitted`` is only ever true for
    a slot that actually has an admitted row from the shared engine; every
    other slot carries a reference to its own typed A8 residual, never a gap
    silently renamed ``not_applicable``."""
    residual_by_slot = {residual["subject_id"]: residual["residual_id"] for residual in a8_residuals}
    view = [
        {
            "slot_id": slot_id,
            "row_admitted": False,
            "row_id": None,
            "residual_id": residual_by_slot[slot_id],
        }
        for slot_id in a7.a6.all_frozen_slot_ids(manifest)
    ]
    view.sort(key=lambda entry: entry["slot_id"])
    return view


# --- shared engine wiring (real call, zero rows today) ------------------------


def run_engine_admission(rows: list[dict[str, Any]] = ()) -> dict[str, Any]:  # type: ignore[assignment]
    """A real (never stubbed) call into the shared, already-on-main
    ``v4_original_row_admission.admit_rows`` engine, bound to the V4
    controlling outcome. A7's own factory admitted zero rows, so there is
    nothing rights-cleared for A8 to assemble; ``rows`` stays empty and the
    engine's own counters (``admitted_rows``, ``rejected_rows``) both come
    back 0 -- proving A8's own wiring into the unmodified, contract/privacy-
    gate-enforcing engine is live, never fabricating a row to exercise it."""
    return admission.admit_rows(outcome_sha256=V4_SHA256, rows=list(rows))


# --- receipt assembly --------------------------------------------------------


def build_receipt(root: Path = ROOT) -> dict[str, Any]:
    manifest = _load(SLOT_MANIFEST_PATH)
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)
    a5_receipt = _load(A5_RECEIPT_PATH)
    a6_receipt = _load(A6_RECEIPT_PATH)
    a7_receipt = _load(A7_RECEIPT_PATH)
    gate = check_assembly_gate(root)

    strata = a7.a6.frozen_slot_strata(manifest)
    frozen_slot_ids = a7.a6.all_frozen_slot_ids(manifest)

    a2_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A2", "status": "unresolved_carried_to_a8"}
        for entry in a2_receipt["residuals"]
    ]
    a4_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A4", "status": "unresolved_carried_to_a8"}
        for entry in a4_receipt["a4_residuals"]
    ]
    a5_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A5", "status": "unresolved_carried_to_a8"}
        for entry in a5_receipt["a5_residuals"]
    ]
    a6_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A6", "status": "unresolved_carried_to_a8"}
        for entry in a6_receipt["a6_residuals"]
    ]
    a7_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A7", "status": "unresolved_carried_to_a8"}
        for entry in a7_receipt["a7_residuals"]
    ]

    engine_admission_receipt = run_engine_admission([])
    a8_residuals = derive_a8_slot_residuals(manifest, a2_receipt, gate)
    admitted_slice_view = build_admitted_slice_view(manifest, a8_residuals)

    return {
        "schema_version": "dataset_v4_a8_admission_assembly_receipt_v1",
        "receipt_id": "dataset-v4-a8-admission-assembly-v1",
        "status": (
            "A8_ADMISSION_ASSEMBLY_AND_PARSER_READY_SLICE_NOT_READY_TEXT_FREE_NO_MODEL_SILVER"
            if not gate["assembly_slice_ready"]
            else "ADMITTED_SLICE_READY"
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
                "schema_version": "v4_a8_admission_assembly_script_v1",
            },
        },
        "role_map": manifest["role_ownership"],
        "frozen_slot_denominator": {"total_slots": len(frozen_slot_ids), "strata": strata},
        "assembly_gate": {
            "gate_id": gate["gate_id"],
            "requires": ["a7_receipt_independently_valid", "a2_rights_fully_resolved", "all_frozen_slots_assigned"],
            "a7_receipt_valid": gate["a7_receipt_valid"],
            "a2_rights_resolved": gate["a2_rights_resolved"],
            "all_slots_assigned": gate["all_slots_assigned"],
            "assembly_slice_ready": gate["assembly_slice_ready"],
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
        "a7_residuals_carried_forward": a7_residuals_carried,
        "a8_residuals": a8_residuals,
        "admitted_slice_view": admitted_slice_view,
        "execution_counters": {
            "dataset_rows_emitted": engine_admission_receipt["counts"]["admitted_rows"],
            "candidate_rows_assembled": engine_admission_receipt["counts"]["input_rows"],
            "frozen_slot_count": len(frozen_slot_ids),
            "slots_admitted_ready": len(frozen_slot_ids) if gate["assembly_slice_ready"] else 0,
            "slots_blocked": 0 if gate["assembly_slice_ready"] else len(frozen_slot_ids),
        },
        "eligibility": dict(ASSEMBLY_ELIGIBILITY),
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
            "eval_artifact_ready_claimed": False,
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
    schema = _load(A8_SCHEMA_PATH)
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
    gate = check_assembly_gate(root)
    declared = receipt["assembly_gate"]
    require(
        declared["a7_receipt_valid"] == gate["a7_receipt_valid"]
        and declared["a2_rights_resolved"] == gate["a2_rights_resolved"]
        and declared["all_slots_assigned"] == gate["all_slots_assigned"]
        and declared["assembly_slice_ready"] == gate["assembly_slice_ready"]
        and declared["blocked_reason_code"] == gate["blocked_reason_code"],
        "receipt assembly_gate does not match the state independently re-derived from the live public artifacts "
        "-- refusing (re-verify/regenerate required)",
    )
    require(
        gate["assembly_slice_ready"] or receipt["status"] != "ADMITTED_SLICE_READY",
        "receipt claims ADMITTED_SLICE_READY while the independently re-derived gate is closed -- refusing",
    )


def validate_frozen_slot_denominator(receipt: dict[str, Any], root: Path) -> None:
    manifest = _load(SLOT_MANIFEST_PATH)
    expected_strata = a7.a6.frozen_slot_strata(manifest)
    declared = receipt["frozen_slot_denominator"]
    require(declared["strata"] == expected_strata, "frozen_slot_denominator.strata does not reproduce from the live slot manifest -- refusing")
    all_ids = [slot_id for stratum in expected_strata for slot_id in stratum["slot_ids"]]
    require(len(all_ids) == 100 and len(set(all_ids)) == 100, "frozen slot denominator did not expand to exactly 100 unique slot IDs -- refusing")
    require(declared["total_slots"] == 100, "frozen_slot_denominator.total_slots is not 100 -- refusing")


def validate_engine_wiring(receipt: dict[str, Any]) -> None:
    """Re-runs the real shared engine call and requires a byte-identical
    result, plus makes the engine independently verify its own nested
    receipt (``v4_original_row_admission.verify_receipt``) -- proving this is
    a live wire into the on-main engine at the assembly layer too, not a
    declared/stubbed shape."""
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
        "engine_wiring.admission_receipt does not report zero rows -- refusing (no rights-cleared row exists yet; "
        "dataset_rows_emitted must stay 0)",
    )


def validate_residuals_carried_from_a2_a4_a5_a6_a7(receipt: dict[str, Any], root: Path) -> None:
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)
    a5_receipt = _load(A5_RECEIPT_PATH)
    a6_receipt = _load(A6_RECEIPT_PATH)
    a7_receipt = _load(A7_RECEIPT_PATH)
    manifest = _load(SLOT_MANIFEST_PATH)
    gate = check_assembly_gate(root)

    for stage, source_ids, carried in (
        ("A2", {e["residual_id"] for e in a2_receipt["residuals"]}, receipt["a2_residuals_carried_forward"]),
        ("A4", {e["residual_id"] for e in a4_receipt["a4_residuals"]}, receipt["a4_residuals_carried_forward"]),
        ("A5", {e["residual_id"] for e in a5_receipt["a5_residuals"]}, receipt["a5_residuals_carried_forward"]),
        ("A6", {e["residual_id"] for e in a6_receipt["a6_residuals"]}, receipt["a6_residuals_carried_forward"]),
        ("A7", {e["residual_id"] for e in a7_receipt["a7_residuals"]}, receipt["a7_residuals_carried_forward"]),
    ):
        carried_ids = {entry["residual_id"] for entry in carried}
        require(carried_ids == source_ids, f"{stage.lower()}_residuals_carried_forward does not reproduce from {stage} -- refusing")
        for entry in carried:
            require(
                entry["origin_stage"] == stage and entry["status"] == "unresolved_carried_to_a8",
                f"{stage.lower()}_residuals_carried_forward entry has an unexpected origin_stage/status -- refusing",
            )

    expected_a8_residuals = derive_a8_slot_residuals(manifest, a2_receipt, gate)
    require(receipt["a8_residuals"] == expected_a8_residuals, "a8_residuals does not reproduce from the live slot manifest, A2 receipt, and gate -- refusing")

    expected_view = build_admitted_slice_view(manifest, expected_a8_residuals)
    require(receipt["admitted_slice_view"] == expected_view, "admitted_slice_view does not reproduce from the live slot manifest and a8_residuals -- refusing")
    require(
        all(entry["row_admitted"] is False and entry["row_id"] is None for entry in receipt["admitted_slice_view"]),
        "admitted_slice_view claims an admitted row while no rights-cleared row exists -- refusing",
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
    require(receipt["eligibility"] == ASSEMBLY_ELIGIBILITY, "receipt eligibility does not equal the frozen all-false assembly eligibility -- refusing")
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
    validate_residuals_carried_from_a2_a4_a5_a6_a7(receipt, root)
    validate_no_forbidden_keys(receipt)
    validate_no_forbidden_completion_claims(receipt)
    validate_eligibility_and_safety_all_false(receipt)
    validate_receipt_schema(receipt)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--receipt", type=Path, default=A8_RECEIPT_PATH, help="A8 receipt JSON to verify (default: the tracked V4 A8 admission/assembly receipt).")
    parser.add_argument("--write-receipt", action="store_true", help="Assemble and persist a freshly computed receipt to --receipt.")
    args = parser.parse_args(argv)

    if args.write_receipt:
        receipt = build_receipt()
        validate_receipt_independently(receipt)
        args.receipt.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        print(canonical_json({"status": receipt["status"], "assembly_gate": receipt["assembly_gate"]}))
        return

    receipt = _load(args.receipt)
    validate_receipt_independently(receipt)
    print(canonical_json({"status": receipt["status"], "assembly_gate": receipt["assembly_gate"]}))


if __name__ == "__main__":
    try:
        main()
    except AdmissionAssemblyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
