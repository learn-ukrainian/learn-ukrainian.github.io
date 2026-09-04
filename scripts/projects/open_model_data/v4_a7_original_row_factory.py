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
* A6's blind arena receipt (already-carried residuals, and its own typed,
  positive ``a6_completions`` -- the direct upstream signal this module's
  gate builds on), and
* the frozen 100-slot V4 pilot slot manifest (``slot_series`` -- public slot
  IDs only, never a real ``source_unit_id``).

**Prerequisite eligibility is not stage completion** (PR #7654 repair cycle
2, Option A -- ``batch_state/tasks/design-7654-partial-stage-evidence.
result``). Cycle 1 derived a slot's readiness from A2 rights + manifest
assignment metadata plus a slot's *absence* from A6's own residual list --
absence is never completion evidence (cross-family P1, 2026-09-04). This
module now reads A6's own typed, positive ``a6_completions`` records
directly; a slot is only ever counted A7-complete once a real ``a7_completions``
record exists for it *and* that record's slot is also present in A6's own
``a6_completions`` (the upstream-subset invariant). Two independent parts:

1. ``check_factory_gate`` -- independently re-derives, from those five public
   artifacts alone, whether a real independently-constructed row may be
   produced at all. Right now it cannot: every frozen slot is still
   ``UNASSIGNED_PENDING_A2_A3``, A2 still carries eight unresolved
   rights/coverage residuals, and A6's own ``a6_completions`` is empty --
   so ``slots_prerequisite_eligible`` is 0 and ``factory_slice_ready`` is
   false. Per the binding contract this module must *never* claim the
   row-ready status while that is true; it reports ``factory_slice_ready:
   false`` and a typed ``blocked_reason_code`` instead.
2. ``build_receipt`` -- assembles the public receipt: the frozen 100-slot
   denominator (reusing, never duplicating, ``v4_stage_evidence
   .frozen_slot_strata``/``all_frozen_slot_ids``), the per-stratum
   eligibility table, the gate, a real (zero-row) call into the shared
   ``v4_original_row_admission.admit_rows`` engine proving the wiring is
   live rather than declarative, every A2/A4/A5/A6 residual carried forward
   unresolved, the always-empty ``a7_completions``, and one typed per-slot
   A7 residual for every slot not yet complete -- never a silently dropped
   slot and never a synthesized row standing in for the missing independent
   construction.

Run with no arguments to verify the checked-in A7 receipt reproduces from the
five public artifacts on disk -- no ``batch_state/`` required, so this passes
in a fresh checkout. Pass ``--write-receipt`` to (re)assemble and persist it
after a genuine change to one of those five artifacts or to this module or
the shared admission engine. Every path this module reads or writes is
derived from its ``root`` argument, never a module-level production-path
constant, so it is directly testable against a synthetic root.
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
from scripts.projects.open_model_data import v4_stage_evidence as ev

ROOT = _SELF_ROOT
ADMISSION_RELATIVE = "data/projects/open_model_data/admission"
CONTRACTS_RELATIVE = "data/projects/open_model_data/contracts"

A7_RECEIPT_RELATIVE = f"{ADMISSION_RELATIVE}/dataset_v4_a7_original_row_factory_receipt_v1.json"
A7_SCHEMA_RELATIVE = f"{CONTRACTS_RELATIVE}/dataset_v4_a7_original_row_factory_receipt_v1.schema.json"
A2_RECEIPT_RELATIVE = f"{ADMISSION_RELATIVE}/dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_RELATIVE = f"{ADMISSION_RELATIVE}/dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_RELATIVE = f"{ADMISSION_RELATIVE}/dataset_v4_a5_evidence_enrichment_receipt_v1.json"
A6_RECEIPT_RELATIVE = f"{ADMISSION_RELATIVE}/dataset_v4_a6_blind_arena_receipt_v1.json"
SLOT_MANIFEST_RELATIVE = f"{ADMISSION_RELATIVE}/dataset_v4_pilot_slot_manifest_v1.json"
ADMISSION_ENGINE_RELATIVE = "scripts/projects/open_model_data/v4_original_row_admission.py"
SELF_RELATIVE = "scripts/projects/open_model_data/v4_a7_original_row_factory.py"

A7_RECEIPT_PATH = ROOT / A7_RECEIPT_RELATIVE
A7_SCHEMA_PATH = ROOT / A7_SCHEMA_RELATIVE
# Absolute-path aliases kept for backward compatibility with downstream
# modules (A8-A13) that still import these directly rather than deriving
# from a ``root`` argument -- this module's own build/check functions never
# use these, only the *_RELATIVE strings above plus an explicit root.
A2_RECEIPT_PATH = ROOT / A2_RECEIPT_RELATIVE
A4_RECEIPT_PATH = ROOT / A4_RECEIPT_RELATIVE
A5_RECEIPT_PATH = ROOT / A5_RECEIPT_RELATIVE
A6_RECEIPT_PATH = ROOT / A6_RECEIPT_RELATIVE
SLOT_MANIFEST_PATH = ROOT / SLOT_MANIFEST_RELATIVE
ADMISSION_ENGINE_PATH = ROOT / ADMISSION_ENGINE_RELATIVE
SELF_PATH = ROOT / SELF_RELATIVE

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

# Reused, never duplicated -- see v4_a6_blind_arena's own re-export of the
# shared v4_stage_evidence frozen-slot-denominator math.
frozen_slot_strata = a6.frozen_slot_strata
all_frozen_slot_ids = a6.all_frozen_slot_ids


class OriginalRowFactoryError(ValueError):
    """The A7 wiring or its deterministic receipt is unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise OriginalRowFactoryError(message)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def stratum_reason_codes(a2_receipt: dict[str, Any]) -> dict[str, str]:
    """Backward-compatible alias for A10-A13 (not yet migrated to the
    eligibility/completion split -- design packet follow-up F4 -- and still
    calling this name on every 100-item, always-ineligible-in-production
    stratum). Reuses the shared implementation unchanged; never redefines
    it."""
    return ev.stratum_a2_reason_codes(a2_receipt, error_cls=OriginalRowFactoryError)


# --- factory gate (public-only) ----------------------------------------------


def check_factory_gate(root: Path = ROOT) -> dict[str, Any]:
    """Independently re-derive whether a real, source-derived, independently
    constructed row may be produced at all, from the frozen slot manifest's
    own per-stratum ``assignment_state``, A2's own residuals, and A6's
    independent validity -- never trusting the A7 receipt's own declared
    fields, never opening ``batch_state/``. ``factory_slice_ready`` is only
    ever true once this stage's own positive ``a7_completions`` cover all
    100 frozen slots, each one also present in A6's own ``a6_completions``
    (the upstream-subset invariant) -- prerequisite eligibility is necessary
    but never sufficient on its own.

    Fails closed -- a *closed gate*, not an exception -- if any of the three
    required public artifacts (slot manifest, A2 receipt, A6 receipt) is
    missing, mirroring ``v4_a6_blind_arena.check_arena_gate``'s own missing-
    artifact handling. Every path is derived from ``root``."""
    manifest_path = (root / SLOT_MANIFEST_RELATIVE).resolve()
    a2_path = (root / A2_RECEIPT_RELATIVE).resolve()
    a6_path = (root / A6_RECEIPT_RELATIVE).resolve()
    required_paths = {"slot_manifest": manifest_path, "a2_receipt": a2_path, "a6_receipt": a6_path}
    for label, path in required_paths.items():
        require(root.resolve() in path.parents, f"{label} path escapes the repository root -- refusing")

    missing = sorted(label for label, path in required_paths.items() if not path.is_file())
    if missing:
        return {
            "gate_id": "v4-a7-factory-gate-v1",
            "a6_receipt_valid": False,
            "slots_prerequisite_eligible": 0,
            "slots_upstream_complete": 0,
            "slots_stage_complete": 0,
            "slots_residual": 100,
            "factory_slice_ready": False,
            "owner_role": "A2_A3_PRIVATE_ARTIFACT",
            "blocked_reason_code": f"required_public_artifact_missing:{missing[0]}",
        }

    manifest = _load(manifest_path)
    require(manifest.get("controlling_outcome_sha256") == V4_SHA256, "slot manifest is not bound to the expected V4 controlling outcome -- refusing")

    a2_receipt = _load(a2_path)
    require(a2_receipt.get("controlling_outcome_sha256") == V4_SHA256, "A2 receipt is not bound to the expected V4 controlling outcome -- refusing")

    a6_receipt = _load(a6_path)
    try:
        a6.validate_receipt_independently(a6_receipt, root)
        a6_valid = True
    except a6.ArenaWiringError:
        a6_valid = False

    eligibility = ev.stratum_eligibility(manifest, a2_receipt, error_cls=OriginalRowFactoryError)
    eligible_ids = ev.eligible_slot_ids(eligibility)
    total_ids = set(all_frozen_slot_ids(manifest))

    a6_completion_ids = (
        ev.completion_slot_ids(a6_receipt.get("a6_completions", []), stage="A6", total_slot_ids=total_ids, error_cls=OriginalRowFactoryError) if a6_valid else set()
    )

    a7_completions: list[dict[str, Any]] = []  # A7 has no execution mechanism yet -- always empty (design F2).
    a7_completion_ids = ev.completion_slot_ids(a7_completions, stage="A7", total_slot_ids=total_ids, error_cls=OriginalRowFactoryError)
    residual_ids = ev.derive_residual_slot_ids(total_ids, a7_completion_ids)
    ev.validate_partition(total_ids, a7_completion_ids, residual_ids, label="A7", error_cls=OriginalRowFactoryError)
    ev.validate_subset(a7_completion_ids, eligible_ids, label="A7 completions vs prerequisite-eligible slots", error_cls=OriginalRowFactoryError)
    ev.validate_subset(a7_completion_ids, a6_completion_ids, label="A7 completions vs A6 completions (upstream subset)", error_cls=OriginalRowFactoryError)

    slots_prerequisite_eligible = len(eligible_ids)
    slots_upstream_complete = len(a6_completion_ids)
    slots_stage_complete = len(a7_completion_ids)
    slots_residual = len(residual_ids)
    factory_slice_ready = slots_stage_complete == 100

    blocked_reason_code = ev.gate_blocked_reason_code(
        upstream_valid=a6_valid,
        slots_prerequisite_eligible=slots_prerequisite_eligible,
        has_upstream_stage=True,
        slots_upstream_complete=slots_upstream_complete,
        slots_stage_complete=slots_stage_complete,
        total=100,
    )

    return {
        "gate_id": "v4-a7-factory-gate-v1",
        "a6_receipt_valid": a6_valid,
        "slots_prerequisite_eligible": slots_prerequisite_eligible,
        "slots_upstream_complete": slots_upstream_complete,
        "slots_stage_complete": slots_stage_complete,
        "slots_residual": slots_residual,
        "factory_slice_ready": factory_slice_ready,
        "owner_role": manifest["sealed_heldout_commitment"]["assignment_owner"],
        "blocked_reason_code": blocked_reason_code,
    }


# --- A7's own per-slot residuals (public, source-free) -----------------------


def derive_a7_slot_residuals(manifest: dict[str, Any], a2_receipt: dict[str, Any], gate: dict[str, Any], completion_slot_ids: set[str] = frozenset()) -> list[dict[str, Any]]:
    """One typed residual per frozen public slot ID not yet in
    ``completion_slot_ids`` -- never a silently dropped slot and never a
    synthesized row standing in for the missing independent construction. A
    pure function of the manifest's own ``slot_series``, A2's own public
    reason codes, the gate this module itself re-derives, and the stage's
    own completion slot ids; never opens any private state."""
    owner_role = gate["owner_role"]
    eligibility = ev.stratum_eligibility(manifest, a2_receipt, error_cls=OriginalRowFactoryError)
    eligibility_by_stratum = {record["stratum"]: record for record in eligibility}
    a2_reasons = ev.stratum_a2_reason_codes(a2_receipt, error_cls=OriginalRowFactoryError)
    residuals = []
    for stratum_entry in frozen_slot_strata(manifest):
        stratum = stratum_entry["stratum"]
        reason_code = ev.slot_residual_reason_code(stratum, eligibility_by_stratum, a2_reasons)
        for slot_id in stratum_entry["slot_ids"]:
            if slot_id in completion_slot_ids:
                continue
            residuals.append(
                {
                    "residual_id": f"a7-residual-{reason_code.replace('_', '-')}-{slot_id}",
                    "subject_kind": "pilot_slot",
                    "subject_id": slot_id,
                    "stage": "A7",
                    "reason_code": reason_code,
                    "owner_role": owner_role,
                    "next_action": (
                        "no independently authored or independently constructed row may be produced for this "
                        "frozen slot until its stratum is prerequisite-eligible and A6 and A7 each produce real "
                        "positive completion evidence for it -- never derive a row from metadata alone"
                    ),
                    "retryability": "retryable",
                    "evidence_refs": [
                        "admission.dataset_v4_pilot_slot_manifest_v1.slot_series",
                        "admission.dataset_v4_a2_source_operation_admission_receipt_v1.stratum_coverage_map",
                        "admission.dataset_v4_a6_blind_arena_receipt_v1.a6_completions",
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
    own counters (``admitted_rows``, ``rejected_rows``) both come back 0 --
    proving the wiring is live, never fabricating a row to exercise it."""
    return admission.admit_rows(outcome_sha256=V4_SHA256, rows=list(rows))


# --- receipt assembly --------------------------------------------------------


def build_receipt(root: Path = ROOT) -> dict[str, Any]:
    manifest = _load(root / SLOT_MANIFEST_RELATIVE)
    a2_receipt = _load(root / A2_RECEIPT_RELATIVE)
    a4_receipt = _load(root / A4_RECEIPT_RELATIVE)
    a5_receipt = _load(root / A5_RECEIPT_RELATIVE)
    a6_receipt = _load(root / A6_RECEIPT_RELATIVE)
    gate = check_factory_gate(root)

    strata = frozen_slot_strata(manifest)
    frozen_slot_ids = all_frozen_slot_ids(manifest)
    eligibility = ev.stratum_eligibility(manifest, a2_receipt, error_cls=OriginalRowFactoryError)

    a7_completions: list[dict[str, Any]] = []  # Always empty today -- see module docstring.
    completion_slot_ids = {record["slot_id"] for record in a7_completions}

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
                "path": A2_RECEIPT_RELATIVE,
                "sha256": sha256_file(root / A2_RECEIPT_RELATIVE),
                "schema_version": "dataset_v4_a2_source_operation_admission_receipt_v1",
            },
            "a4_deterministic_extraction": {
                "path": A4_RECEIPT_RELATIVE,
                "sha256": sha256_file(root / A4_RECEIPT_RELATIVE),
                "schema_version": "dataset_v4_a4_deterministic_extraction_receipt_v1",
            },
            "a5_evidence_enrichment": {
                "path": A5_RECEIPT_RELATIVE,
                "sha256": sha256_file(root / A5_RECEIPT_RELATIVE),
                "schema_version": "dataset_v4_a5_evidence_enrichment_receipt_v1",
            },
            "a6_blind_arena": {
                "path": A6_RECEIPT_RELATIVE,
                "sha256": sha256_file(root / A6_RECEIPT_RELATIVE),
                "schema_version": "dataset_v4_a6_blind_arena_receipt_v1",
            },
            "pilot_slot_manifest": {
                "path": SLOT_MANIFEST_RELATIVE,
                "sha256": sha256_file(root / SLOT_MANIFEST_RELATIVE),
                "schema_version": "dataset_v4_pilot_slot_manifest_v1",
            },
            "admission_engine_implementation": {
                "path": ADMISSION_ENGINE_RELATIVE,
                "sha256": sha256_file(root / ADMISSION_ENGINE_RELATIVE),
                "schema_version": "v4_original_row_admission_script_v1",
            },
            "wiring_implementation": {
                "path": SELF_RELATIVE,
                "sha256": sha256_file(root / SELF_RELATIVE),
                "schema_version": "v4_a7_original_row_factory_script_v1",
            },
        },
        "role_map": manifest["role_ownership"],
        "frozen_slot_denominator": {"total_slots": len(frozen_slot_ids), "strata": strata},
        "factory_gate": {
            "gate_id": gate["gate_id"],
            "requires": [
                "a6_receipt_independently_valid",
                "per_stratum_a2_rights_resolved",
                "per_stratum_manifest_assignment",
                "per_slot_a6_completion_evidence",
                "per_slot_a7_completion_evidence",
            ],
            "a6_receipt_valid": gate["a6_receipt_valid"],
            "slots_prerequisite_eligible": gate["slots_prerequisite_eligible"],
            "slots_upstream_complete": gate["slots_upstream_complete"],
            "slots_stage_complete": gate["slots_stage_complete"],
            "slots_residual": gate["slots_residual"],
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
        "prerequisite_eligibility": ev.public_eligibility(eligibility),
        "a2_residuals_carried_forward": a2_residuals_carried,
        "a4_residuals_carried_forward": a4_residuals_carried,
        "a5_residuals_carried_forward": a5_residuals_carried,
        "a6_residuals_carried_forward": a6_residuals_carried,
        "a7_completions": a7_completions,
        "a7_residuals": derive_a7_slot_residuals(manifest, a2_receipt, gate, completion_slot_ids),
        "execution_counters": {
            "dataset_rows_emitted": engine_admission_receipt["counts"]["admitted_rows"],
            "candidate_rows_constructed": engine_admission_receipt["counts"]["input_rows"],
            "frozen_slot_count": len(frozen_slot_ids),
            "slots_prerequisite_eligible": gate["slots_prerequisite_eligible"],
            "slots_upstream_complete": gate["slots_upstream_complete"],
            "slots_stage_complete": gate["slots_stage_complete"],
            "slots_residual": gate["slots_residual"],
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


def _load_schema(root: Path) -> dict[str, Any]:
    schema = _load(root / A7_SCHEMA_RELATIVE)
    Draft202012Validator.check_schema(schema)
    return schema


def validate_receipt_schema(receipt: dict[str, Any], root: Path = ROOT) -> None:
    errors = sorted(Draft202012Validator(_load_schema(root)).iter_errors(receipt), key=lambda e: list(e.path))
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
        and declared["slots_prerequisite_eligible"] == gate["slots_prerequisite_eligible"]
        and declared["slots_upstream_complete"] == gate["slots_upstream_complete"]
        and declared["slots_stage_complete"] == gate["slots_stage_complete"]
        and declared["slots_residual"] == gate["slots_residual"]
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
    manifest = _load(root / SLOT_MANIFEST_RELATIVE)
    expected_strata = frozen_slot_strata(manifest)
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


def validate_eligibility_and_completion(receipt: dict[str, Any], root: Path) -> None:
    manifest = _load(root / SLOT_MANIFEST_RELATIVE)
    a2_receipt = _load(root / A2_RECEIPT_RELATIVE)
    a6_receipt = _load(root / A6_RECEIPT_RELATIVE)
    gate = check_factory_gate(root)

    expected_eligibility = ev.public_eligibility(ev.stratum_eligibility(manifest, a2_receipt, error_cls=OriginalRowFactoryError))
    require(receipt["prerequisite_eligibility"] == expected_eligibility, "prerequisite_eligibility does not reproduce from the live A2 receipt and slot manifest -- refusing")

    total_ids = set(all_frozen_slot_ids(manifest))
    eligible_ids = ev.eligible_slot_ids(ev.stratum_eligibility(manifest, a2_receipt, error_cls=OriginalRowFactoryError))
    a6_completion_ids = ev.completion_slot_ids(a6_receipt.get("a6_completions", []), stage="A6", total_slot_ids=total_ids, error_cls=OriginalRowFactoryError)
    completion_ids = ev.completion_slot_ids(receipt["a7_completions"], stage="A7", total_slot_ids=total_ids, error_cls=OriginalRowFactoryError)
    ev.validate_subset(completion_ids, eligible_ids, label="A7 completions vs prerequisite-eligible slots", error_cls=OriginalRowFactoryError)
    ev.validate_subset(completion_ids, a6_completion_ids, label="A7 completions vs A6 completions (upstream subset)", error_cls=OriginalRowFactoryError)
    require(len(completion_ids) == gate["slots_stage_complete"], "a7_completions count does not match the gate's slots_stage_complete -- refusing")

    residual_subject_ids = {entry["subject_id"] for entry in receipt["a7_residuals"]}
    expected_residual_ids = total_ids - completion_ids
    require(residual_subject_ids == expected_residual_ids, "a7_residuals does not exactly cover the complement of a7_completions over the frozen denominator -- refusing")
    ev.validate_partition(total_ids, completion_ids, residual_subject_ids, label="A7", error_cls=OriginalRowFactoryError)

    expected_residuals = derive_a7_slot_residuals(manifest, a2_receipt, gate, completion_ids)
    require(receipt["a7_residuals"] == expected_residuals, "a7_residuals does not reproduce from the live slot manifest, A2 receipt, and gate -- refusing")


def validate_residuals_carried_from_a2_a4_a5_a6(receipt: dict[str, Any], root: Path) -> None:
    a2_receipt = _load(root / A2_RECEIPT_RELATIVE)
    a4_receipt = _load(root / A4_RECEIPT_RELATIVE)
    a5_receipt = _load(root / A5_RECEIPT_RELATIVE)
    a6_receipt = _load(root / A6_RECEIPT_RELATIVE)

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
    validate_eligibility_and_completion(receipt, root)
    validate_residuals_carried_from_a2_a4_a5_a6(receipt, root)
    validate_no_forbidden_keys(receipt)
    validate_no_forbidden_completion_claims(receipt)
    validate_eligibility_and_safety_all_false(receipt)
    validate_receipt_schema(receipt, root)


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
