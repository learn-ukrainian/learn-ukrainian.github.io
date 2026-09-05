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
* A6's blind arena receipt (already-carried residuals only -- A8 never
  reads or depends on ``a6_completions``),
* A7's original-row factory receipt (already-carried residuals, its own
  typed, positive ``a7_completions``, its own zero-row engine admission
  receipt, and its own gate state as the direct upstream signal this
  module's gate builds on), and
* the frozen 100-slot V4 pilot slot manifest (``slot_series`` -- public slot
  IDs only, never a real ``source_unit_id``).

**Prerequisite eligibility is not stage completion** (PR #7654 repair cycle
2, Option A). A slot is only ever A8-complete once a real ``a8_completions``
record exists for it *and* that slot is also present in A7's own
``a7_completions`` (the upstream-subset invariant). A7 completion does not
itself require A6 completion -- whether A7 should require A6 completion per
slot is an explicitly deferred policy decision (design packet F2), not one
this repair makes -- so this A8-vs-A7 subset check is the full extent of
A8's own upstream-completion dependency; it never transitively implies an
A7-vs-A6 relationship. Two independent parts:

1. ``check_assembly_gate`` -- independently re-derives, from those six public
   artifacts alone, whether a real admitted slice may be assembled at all.
   Right now it cannot: A7 itself reports zero ``slots_stage_complete``, so
   there is nothing rights-cleared to assemble. Per the binding contract
   this module must *never* claim ``ADMITTED_SLICE_READY`` while that is
   true; it reports ``assembly_slice_ready: false`` and a typed
   ``blocked_reason_code`` instead.
2. ``build_receipt`` -- assembles the public receipt: the frozen 100-slot
   denominator (reusing, never duplicating, ``v4_stage_evidence
   .frozen_slot_strata``/``all_frozen_slot_ids``), the gate, a real call
   into the shared, unmodified ``v4_original_row_admission`` engine proving
   A8's own wiring is live rather than declarative, every A2/A4/A5/A6/A7
   residual carried forward unresolved, ``a8_completions`` (empty in every
   production receipt today), an append-only per-slot
   ``admitted_slice_view`` (``row_admitted: true`` only for a slot with a
   real completion, a typed residual reference otherwise -- never a row and
   never a dropped slot), and one typed per-slot A8 residual for every slot
   not yet complete.

**Real-slot mechanism (mechanism-only in this PR; zero real rows).**
``a8_completions`` and ``check_assembly_gate``/``build_receipt`` now take a
completions list as an explicit parameter rather than hardcoding it empty.
Every A8 completion must name the *exact same* row A7 already admitted for
that slot (``validate_a8_completions_match_a7``) -- A8 never constructs a
new row, it only assembles the one A7's factory produced. As with A7, this
module's own fresh-checkout validation only proves a completion claim is
well-formed and internally consistent; genuineness is proven separately by
``v4_a7_private_ledger.verify_private_replay`` against the private ledger.

Run with no arguments to verify the checked-in A8 receipt reproduces from the
six public artifacts on disk -- no ``batch_state/`` required, so this passes
in a fresh checkout. Pass ``--write-receipt`` to (re)assemble and persist it
after a genuine change to one of those six artifacts or to the shared
admission engine. Every path this module reads or writes is derived from its
``root`` argument, never a module-level production-path constant.
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

from learn_ukrainian_v4_runtime import v4_a7_original_row_factory as a7
from learn_ukrainian_v4_runtime import v4_original_row_admission as admission
from learn_ukrainian_v4_runtime import v4_stage_evidence as ev

ROOT = _SELF_ROOT
ADMISSION_RELATIVE = "data/projects/open_model_data/admission"
CONTRACTS_RELATIVE = "data/projects/open_model_data/contracts"

A8_RECEIPT_RELATIVE = f"{ADMISSION_RELATIVE}/dataset_v4_a8_admission_assembly_receipt_v1.json"
A8_SCHEMA_RELATIVE = f"{CONTRACTS_RELATIVE}/dataset_v4_a8_admission_assembly_receipt_v1.schema.json"
A2_RECEIPT_RELATIVE = f"{ADMISSION_RELATIVE}/dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_RELATIVE = f"{ADMISSION_RELATIVE}/dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_RELATIVE = f"{ADMISSION_RELATIVE}/dataset_v4_a5_evidence_enrichment_receipt_v1.json"
A6_RECEIPT_RELATIVE = f"{ADMISSION_RELATIVE}/dataset_v4_a6_blind_arena_receipt_v1.json"
A7_RECEIPT_RELATIVE = f"{ADMISSION_RELATIVE}/dataset_v4_a7_original_row_factory_receipt_v1.json"
SLOT_MANIFEST_RELATIVE = f"{ADMISSION_RELATIVE}/dataset_v4_pilot_slot_manifest_v1.json"
ADMISSION_ENGINE_RELATIVE = "scripts/projects/open_model_data/v4_original_row_admission.py"
SELF_RELATIVE = "scripts/projects/open_model_data/v4_a8_admission_assembly.py"

A8_RECEIPT_PATH = ROOT / A8_RECEIPT_RELATIVE
A8_SCHEMA_PATH = ROOT / A8_SCHEMA_RELATIVE
# Absolute-path aliases kept for backward compatibility with downstream
# modules (A9-A13) that still import these directly rather than deriving
# from a ``root`` argument -- this module's own build/check functions never
# use these, only the *_RELATIVE strings above plus an explicit root.
A2_RECEIPT_PATH = ROOT / A2_RECEIPT_RELATIVE
A4_RECEIPT_PATH = ROOT / A4_RECEIPT_RELATIVE
A5_RECEIPT_PATH = ROOT / A5_RECEIPT_RELATIVE
A6_RECEIPT_PATH = ROOT / A6_RECEIPT_RELATIVE
A7_RECEIPT_PATH = ROOT / A7_RECEIPT_RELATIVE
SLOT_MANIFEST_PATH = ROOT / SLOT_MANIFEST_RELATIVE
ADMISSION_ENGINE_PATH = ROOT / ADMISSION_ENGINE_RELATIVE
SELF_PATH = ROOT / SELF_RELATIVE

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
frozen_slot_strata = a7.frozen_slot_strata
all_frozen_slot_ids = a7.all_frozen_slot_ids


class AdmissionAssemblyError(ValueError):
    """The A8 wiring or its deterministic receipt is unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AdmissionAssemblyError(message)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# --- assembly gate (public-only) ---------------------------------------------


def check_assembly_gate(root: Path = ROOT, a8_completions: list[dict[str, Any]] = ()) -> dict[str, Any]:
    """Independently re-derive whether a real admitted slice may be
    assembled at all, from the frozen slot manifest's own per-stratum
    ``assignment_state``, A2's own residuals, and A7's independent validity
    -- never trusting the A8 receipt's own declared fields, never opening
    ``batch_state/``. ``assembly_slice_ready`` is only ever true once this
    stage's own positive ``a8_completions`` cover all 100 frozen slots, each
    one also present in A7's own ``a7_completions``.

    Fails closed -- a *closed gate*, not an exception -- if any of the three
    required public artifacts (slot manifest, A2 receipt, A7 receipt) is
    missing, mirroring ``v4_a7_original_row_factory.check_factory_gate``'s
    own missing-artifact handling. Every path is derived from ``root``."""
    manifest_path = (root / SLOT_MANIFEST_RELATIVE).resolve()
    a2_path = (root / A2_RECEIPT_RELATIVE).resolve()
    a7_path = (root / A7_RECEIPT_RELATIVE).resolve()
    required_paths = {"slot_manifest": manifest_path, "a2_receipt": a2_path, "a7_receipt": a7_path}
    for label, path in required_paths.items():
        require(root.resolve() in path.parents, f"{label} path escapes the repository root -- refusing")

    missing = sorted(label for label, path in required_paths.items() if not path.is_file())
    if missing:
        return {
            "gate_id": "v4-a8-assembly-gate-v1",
            "a7_receipt_valid": False,
            "slots_prerequisite_eligible": 0,
            "slots_upstream_complete": 0,
            "slots_stage_complete": 0,
            "slots_residual": 100,
            "assembly_slice_ready": False,
            "owner_role": "A2_A3_PRIVATE_ARTIFACT",
            "blocked_reason_code": f"required_public_artifact_missing:{missing[0]}",
        }

    manifest = _load(manifest_path)
    require(
        manifest.get("controlling_outcome_sha256") == V4_SHA256,
        "slot manifest is not bound to the expected V4 controlling outcome -- refusing",
    )

    a2_receipt = _load(a2_path)
    require(
        a2_receipt.get("controlling_outcome_sha256") == V4_SHA256,
        "A2 receipt is not bound to the expected V4 controlling outcome -- refusing",
    )

    a7_receipt = _load(a7_path)
    try:
        a7.validate_receipt_independently(a7_receipt, root)
        a7_valid = True
    except a7.OriginalRowFactoryError:
        a7_valid = False

    eligibility = ev.stratum_eligibility(manifest, a2_receipt, error_cls=AdmissionAssemblyError)
    eligible_ids = ev.eligible_slot_ids(eligibility)
    total_ids = set(all_frozen_slot_ids(manifest))

    a7_completion_ids = (
        ev.completion_slot_ids(
            a7_receipt.get("a7_completions", []), stage="A7", total_slot_ids=total_ids, error_cls=AdmissionAssemblyError
        )
        if a7_valid
        else set()
    )

    a8_completions = list(a8_completions)
    a8_completion_ids = ev.completion_slot_ids(
        a8_completions, stage="A8", total_slot_ids=total_ids, error_cls=AdmissionAssemblyError
    )
    residual_ids = ev.derive_residual_slot_ids(total_ids, a8_completion_ids)
    ev.validate_partition(total_ids, a8_completion_ids, residual_ids, label="A8", error_cls=AdmissionAssemblyError)
    ev.validate_subset(
        a8_completion_ids,
        eligible_ids,
        label="A8 completions vs prerequisite-eligible slots",
        error_cls=AdmissionAssemblyError,
    )
    ev.validate_subset(
        a8_completion_ids,
        a7_completion_ids,
        label="A8 completions vs A7 completions (upstream subset)",
        error_cls=AdmissionAssemblyError,
    )
    if a7_valid:
        validate_a8_completions_match_a7(a8_completions, a7_receipt.get("a7_completions", []))

    slots_prerequisite_eligible = len(eligible_ids)
    slots_upstream_complete = len(a7_completion_ids)
    slots_stage_complete = len(a8_completion_ids)
    slots_residual = len(residual_ids)
    assembly_slice_ready = slots_stage_complete == 100

    blocked_reason_code = ev.gate_blocked_reason_code(
        upstream_valid=a7_valid,
        slots_prerequisite_eligible=slots_prerequisite_eligible,
        has_upstream_stage=True,
        slots_upstream_complete=slots_upstream_complete,
        slots_stage_complete=slots_stage_complete,
        total=100,
    )

    return {
        "gate_id": "v4-a8-assembly-gate-v1",
        "a7_receipt_valid": a7_valid,
        "slots_prerequisite_eligible": slots_prerequisite_eligible,
        "slots_upstream_complete": slots_upstream_complete,
        "slots_stage_complete": slots_stage_complete,
        "slots_residual": slots_residual,
        "assembly_slice_ready": assembly_slice_ready,
        "owner_role": manifest["sealed_heldout_commitment"]["assignment_owner"],
        "blocked_reason_code": blocked_reason_code,
    }


def validate_a8_completions_match_a7(
    a8_completions: list[dict[str, Any]], a7_completions: list[dict[str, Any]]
) -> None:
    """Every A8 completion must name the exact same row A7 already admitted
    for that slot -- A8 never constructs a new row, it only assembles the
    one A7's factory already produced. Refuses a slot_id with no matching
    A7 completion, or a row_id/row_content_sha256 that drifts from it."""
    from learn_ukrainian_v4_runtime.stage_policy import validate_completion_policy

    validate_completion_policy([*a8_completions, *a7_completions])
    a7_by_slot = {completion["slot_id"]: completion for completion in a7_completions}
    for completion in a8_completions:
        a7_completion = a7_by_slot.get(completion["slot_id"])
        require(
            a7_completion is not None,
            f"a8 completion for slot {completion['slot_id']!r} has no matching a7 completion -- refusing",
        )
        require(
            completion["row_id"] == a7_completion["row_id"],
            f"a8 completion row_id does not match the corresponding a7 completion for slot {completion['slot_id']!r} -- refusing",
        )
        require(
            completion["row_content_sha256"] == a7_completion["row_content_sha256"],
            f"a8 completion row_content_sha256 does not match the corresponding a7 completion for slot {completion['slot_id']!r} -- refusing",
        )
        if "trust_policy_sha256" in a7_completion or "trust_policy_sha256" in completion:
            require(
                completion.get("trust_policy_sha256") == a7_completion.get("trust_policy_sha256"),
                f"a8 completion trust_policy_sha256 does not match the corresponding a7 completion for slot {completion['slot_id']!r} -- refusing",
            )


# --- A8's own per-slot residuals (public, source-free) -----------------------


def derive_a8_slot_residuals(
    manifest: dict[str, Any],
    a2_receipt: dict[str, Any],
    gate: dict[str, Any],
    completion_slot_ids: set[str] = frozenset(),
) -> list[dict[str, Any]]:
    """One typed residual per frozen public slot ID not yet in
    ``completion_slot_ids`` -- never a silently dropped slot and never
    coverage invented by renaming a gap ``not_applicable``. A pure function
    of the manifest's own ``slot_series``, A2's own public reason codes, the
    gate this module itself re-derives, and the stage's own completion slot
    ids; never opens any private state."""
    owner_role = gate["owner_role"]
    eligibility = ev.stratum_eligibility(manifest, a2_receipt, error_cls=AdmissionAssemblyError)
    eligibility_by_stratum = {record["stratum"]: record for record in eligibility}
    a2_reasons = ev.stratum_a2_reason_codes(a2_receipt, error_cls=AdmissionAssemblyError)
    residuals = []
    for stratum_entry in frozen_slot_strata(manifest):
        stratum = stratum_entry["stratum"]
        reason_code = ev.slot_residual_reason_code(stratum, eligibility_by_stratum, a2_reasons)
        for slot_id in stratum_entry["slot_ids"]:
            if slot_id in completion_slot_ids:
                continue
            residuals.append(
                {
                    "residual_id": f"a8-residual-{reason_code.replace('_', '-')}-{slot_id}",
                    "subject_kind": "pilot_slot",
                    "subject_id": slot_id,
                    "stage": "A8",
                    "reason_code": reason_code,
                    "owner_role": owner_role,
                    "next_action": (
                        "no rights-cleared row exists to assemble for this frozen slot until its stratum is "
                        "prerequisite-eligible and A7 and A8 each produce real positive completion evidence "
                        "for it -- never assemble a row from metadata alone"
                    ),
                    "retryability": "retryable",
                    "evidence_refs": [
                        "admission.dataset_v4_pilot_slot_manifest_v1.slot_series",
                        "admission.dataset_v4_a2_source_operation_admission_receipt_v1.stratum_coverage_map",
                        "admission.dataset_v4_a7_original_row_factory_receipt_v1.a7_completions",
                    ],
                }
            )
    residuals.sort(key=lambda residual: residual["subject_id"])
    return residuals


# --- append-only per-slot admitted view (public, source-free) ----------------


def build_admitted_slice_view(
    manifest: dict[str, Any], a8_residuals: list[dict[str, Any]], a8_completions: list[dict[str, Any]] = ()
) -> list[dict[str, Any]]:
    """One entry per frozen slot ID -- ``row_admitted`` is only ever true for
    a slot that actually has an admitted row from the shared engine (a real
    ``a8_completions`` entry for it); every other slot carries a reference
    to its own typed A8 residual, never a gap silently renamed
    ``not_applicable``."""
    residual_by_slot = {residual["subject_id"]: residual["residual_id"] for residual in a8_residuals}
    completion_by_slot = {completion["slot_id"]: completion for completion in a8_completions}
    view = []
    for slot_id in all_frozen_slot_ids(manifest):
        completion = completion_by_slot.get(slot_id)
        if completion is not None:
            view.append({"slot_id": slot_id, "row_admitted": True, "row_id": completion["row_id"], "residual_id": None})
        else:
            view.append(
                {
                    "slot_id": slot_id,
                    "row_admitted": False,
                    "row_id": None,
                    "residual_id": residual_by_slot.get(slot_id),
                }
            )
    view.sort(key=lambda entry: entry["slot_id"])
    return view


# --- shared engine wiring (real call, zero rows today) ------------------------


def assemble_engine_admission_receipt(
    a8_completions: list[dict[str, Any]], a7_receipt: dict[str, Any]
) -> dict[str, Any]:
    """Assemble ``engine_wiring.admission_receipt`` from the *same*
    already-evaluated ``row_receipt`` A7's own completion for that slot
    already carries -- A8 never re-runs ``evaluate_row``, it only confirms
    the row A7 already admitted is now assembled. Byte-identical to a live,
    zero-row ``admission.admit_rows`` call when there are no completions,
    so today's real, zero-completion production receipt is unaffected."""
    a7_by_slot = {completion["slot_id"]: completion for completion in a7_receipt.get("a7_completions", [])}
    row_receipts = []
    for completion in a8_completions:
        a7_completion = a7_by_slot.get(completion["slot_id"])
        require(
            a7_completion is not None,
            f"a8 completion for slot {completion['slot_id']!r} has no matching a7 completion -- refusing",
        )
        row_receipts.append(a7_completion["row_receipt"])
    return admission.assemble_receipt_from_row_receipts(outcome_sha256=V4_SHA256, row_receipts=row_receipts)


# --- receipt assembly --------------------------------------------------------


@bind_constructed_stage
def build_receipt(root: Path = ROOT, a8_completions: list[dict[str, Any]] = ()) -> dict[str, Any]:
    manifest = _load(root / SLOT_MANIFEST_RELATIVE)
    a2_receipt = _load(root / A2_RECEIPT_RELATIVE)
    a4_receipt = _load(root / A4_RECEIPT_RELATIVE)
    a5_receipt = _load(root / A5_RECEIPT_RELATIVE)
    a6_receipt = _load(root / A6_RECEIPT_RELATIVE)
    a7_receipt = _load(root / A7_RECEIPT_RELATIVE)
    a8_completions = list(a8_completions)  # Empty in every production receipt today -- no real row exists yet.
    gate = check_assembly_gate(root, a8_completions)

    strata = frozen_slot_strata(manifest)
    frozen_slot_ids = all_frozen_slot_ids(manifest)
    eligibility = ev.stratum_eligibility(manifest, a2_receipt, error_cls=AdmissionAssemblyError)

    completion_slot_ids = {record["slot_id"] for record in a8_completions}

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

    engine_admission_receipt = assemble_engine_admission_receipt(a8_completions, a7_receipt)
    a8_residuals = derive_a8_slot_residuals(manifest, a2_receipt, gate, completion_slot_ids)
    admitted_slice_view = build_admitted_slice_view(manifest, a8_residuals, a8_completions)

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
            "a7_original_row_factory": {
                "path": A7_RECEIPT_RELATIVE,
                "sha256": sha256_file(root / A7_RECEIPT_RELATIVE),
                "schema_version": "dataset_v4_a7_original_row_factory_receipt_v1",
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
                "schema_version": "v4_a8_admission_assembly_script_v1",
            },
        },
        "role_map": manifest["role_ownership"],
        "frozen_slot_denominator": {"total_slots": len(frozen_slot_ids), "strata": strata},
        "assembly_gate": {
            "gate_id": gate["gate_id"],
            "requires": [
                "a7_receipt_independently_valid",
                "per_stratum_a2_rights_resolved",
                "per_stratum_manifest_assignment",
                "per_slot_a7_completion_evidence",
                "per_slot_a8_completion_evidence",
            ],
            "a7_receipt_valid": gate["a7_receipt_valid"],
            "slots_prerequisite_eligible": gate["slots_prerequisite_eligible"],
            "slots_upstream_complete": gate["slots_upstream_complete"],
            "slots_stage_complete": gate["slots_stage_complete"],
            "slots_residual": gate["slots_residual"],
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
        "prerequisite_eligibility": ev.public_eligibility(eligibility),
        "a2_residuals_carried_forward": a2_residuals_carried,
        "a4_residuals_carried_forward": a4_residuals_carried,
        "a5_residuals_carried_forward": a5_residuals_carried,
        "a6_residuals_carried_forward": a6_residuals_carried,
        "a7_residuals_carried_forward": a7_residuals_carried,
        "a8_completions": a8_completions,
        "a8_residuals": a8_residuals,
        "admitted_slice_view": admitted_slice_view,
        "execution_counters": {
            # Always 0: a dataset row is only ever emitted at A11 release
            # (out of scope for this stage); never derived from the engine's
            # own admitted_rows count, which now can be genuinely nonzero.
            "dataset_rows_emitted": 0,
            "candidate_rows_assembled": engine_admission_receipt["counts"]["input_rows"],
            "frozen_slot_count": len(frozen_slot_ids),
            "slots_prerequisite_eligible": gate["slots_prerequisite_eligible"],
            "slots_upstream_complete": gate["slots_upstream_complete"],
            "slots_stage_complete": gate["slots_stage_complete"],
            "slots_residual": gate["slots_residual"],
        },
        "eligibility": dict(ASSEMBLY_ELIGIBILITY),
        "safety_assertions": {
            # Truthfully reflects whether any row has actually been
            # engine-admitted via a8_completions -- stays True while
            # a8_completions is empty (every production receipt today).
            "rows_not_admitted": len(a8_completions) == 0,
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


def _load_schema(root: Path) -> dict[str, Any]:
    schema = _load(root / A8_SCHEMA_RELATIVE)
    Draft202012Validator.check_schema(schema)
    return schema


def validate_receipt_schema(receipt: dict[str, Any], root: Path = ROOT) -> None:
    errors = sorted(Draft202012Validator(current_stage_schema(_load_schema(root))).iter_errors(receipt), key=lambda e: list(e.path))
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
    gate = check_assembly_gate(root, receipt["a8_completions"])
    declared = receipt["assembly_gate"]
    require(
        declared["a7_receipt_valid"] == gate["a7_receipt_valid"]
        and declared["slots_prerequisite_eligible"] == gate["slots_prerequisite_eligible"]
        and declared["slots_upstream_complete"] == gate["slots_upstream_complete"]
        and declared["slots_stage_complete"] == gate["slots_stage_complete"]
        and declared["slots_residual"] == gate["slots_residual"]
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
    manifest = _load(root / SLOT_MANIFEST_RELATIVE)
    expected_strata = frozen_slot_strata(manifest)
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


def validate_engine_wiring(receipt: dict[str, Any], root: Path) -> None:
    """Requires ``engine_wiring.admission_receipt`` to reproduce, byte for
    byte, from the *same* row receipts A7's own completions already carry
    for these slots (never re-executes ``evaluate_row``), and makes the
    shared engine independently verify the assembled receipt's own internal
    consistency (``v4_original_row_admission.verify_receipt``) -- proving
    this is a live wire into the on-main engine at the assembly layer too,
    not a declared/stubbed shape. With zero completions this recomputation
    is byte-identical to a live, zero-row ``admission.admit_rows`` call --
    today's real production receipt is unaffected."""
    a7_receipt = _load(root / A7_RECEIPT_RELATIVE)
    wiring = receipt["engine_wiring"]
    require(
        wiring["engine_schema_version"] == admission.SCHEMA_VERSION
        and wiring["engine_input_schema_version"] == admission.INPUT_SCHEMA_VERSION,
        "engine_wiring schema versions do not match the live v4_original_row_admission module -- refusing (engine changed without regenerating this receipt)",
    )
    require(
        wiring["model_only_bases_blocked"] == sorted(admission.MODEL_ONLY_BASES),
        "engine_wiring.model_only_bases_blocked does not match the live engine's MODEL_ONLY_BASES -- refusing",
    )
    recomputed = assemble_engine_admission_receipt(receipt["a8_completions"], a7_receipt)
    require(
        wiring["admission_receipt"] == recomputed,
        "engine_wiring.admission_receipt does not reproduce from the matching a7_completions row receipts -- refusing",
    )
    admission.verify_receipt(wiring["admission_receipt"])
    require(
        wiring["admission_receipt"]["counts"]["admitted_rows"] == len(receipt["a8_completions"]),
        "engine_wiring.admission_receipt.counts.admitted_rows does not match the number of declared a8_completions -- refusing",
    )
    if not receipt["a8_completions"]:
        require(
            wiring["admission_receipt"]["counts"] == {"input_rows": 0, "admitted_rows": 0, "rejected_rows": 0},
            "engine_wiring.admission_receipt does not report zero rows -- refusing (no a8_completions declared)",
        )


def validate_a8_completions_shape(receipt: dict[str, Any]) -> None:
    """Each ``a8_completions`` entry must carry a well-formed
    ``row_content_sha256`` and match its own upstream A7 completion --
    a claim inconsistent with its own upstream evidence refuses here."""
    for completion in receipt["a8_completions"]:
        require(
            isinstance(completion["row_content_sha256"], str)
            and admission.SHA256_RE.fullmatch(completion["row_content_sha256"]) is not None,
            "a8_completions.row_content_sha256 is not a well-formed sha256 -- refusing",
        )


def validate_eligibility_and_completion(receipt: dict[str, Any], root: Path) -> None:
    manifest = _load(root / SLOT_MANIFEST_RELATIVE)
    a2_receipt = _load(root / A2_RECEIPT_RELATIVE)
    a7_receipt = _load(root / A7_RECEIPT_RELATIVE)
    gate = check_assembly_gate(root, receipt["a8_completions"])

    expected_eligibility = ev.public_eligibility(
        ev.stratum_eligibility(manifest, a2_receipt, error_cls=AdmissionAssemblyError)
    )
    require(
        receipt["prerequisite_eligibility"] == expected_eligibility,
        "prerequisite_eligibility does not reproduce from the live A2 receipt and slot manifest -- refusing",
    )

    total_ids = set(all_frozen_slot_ids(manifest))
    eligible_ids = ev.eligible_slot_ids(ev.stratum_eligibility(manifest, a2_receipt, error_cls=AdmissionAssemblyError))
    a7_completion_ids = ev.completion_slot_ids(
        a7_receipt.get("a7_completions", []), stage="A7", total_slot_ids=total_ids, error_cls=AdmissionAssemblyError
    )
    completion_ids = ev.completion_slot_ids(
        receipt["a8_completions"], stage="A8", total_slot_ids=total_ids, error_cls=AdmissionAssemblyError
    )
    ev.validate_subset(
        completion_ids,
        eligible_ids,
        label="A8 completions vs prerequisite-eligible slots",
        error_cls=AdmissionAssemblyError,
    )
    ev.validate_subset(
        completion_ids,
        a7_completion_ids,
        label="A8 completions vs A7 completions (upstream subset)",
        error_cls=AdmissionAssemblyError,
    )
    require(
        len(completion_ids) == gate["slots_stage_complete"],
        "a8_completions count does not match the gate's slots_stage_complete -- refusing",
    )

    residual_subject_ids = {entry["subject_id"] for entry in receipt["a8_residuals"]}
    expected_residual_ids = total_ids - completion_ids
    require(
        residual_subject_ids == expected_residual_ids,
        "a8_residuals does not exactly cover the complement of a8_completions over the frozen denominator -- refusing",
    )
    ev.validate_partition(total_ids, completion_ids, residual_subject_ids, label="A8", error_cls=AdmissionAssemblyError)

    expected_residuals = derive_a8_slot_residuals(manifest, a2_receipt, gate, completion_ids)
    require(
        receipt["a8_residuals"] == expected_residuals,
        "a8_residuals does not reproduce from the live slot manifest, A2 receipt, and gate -- refusing",
    )

    expected_view = build_admitted_slice_view(manifest, expected_residuals, receipt["a8_completions"])
    require(
        receipt["admitted_slice_view"] == expected_view,
        "admitted_slice_view does not reproduce from the live slot manifest, a8_residuals, and a8_completions -- refusing",
    )
    for entry in receipt["admitted_slice_view"]:
        if entry["row_admitted"]:
            require(
                entry["row_id"] is not None and entry["residual_id"] is None,
                "admitted_slice_view entry claims row_admitted but is missing row_id or still carries a residual_id -- refusing",
            )
        else:
            require(
                entry["row_id"] is None,
                "admitted_slice_view entry claims no admitted row but carries a row_id -- refusing",
            )

    validate_a8_completions_match_a7(receipt["a8_completions"], a7_receipt.get("a7_completions", []))


def validate_residuals_carried_from_a2_a4_a5_a6_a7(receipt: dict[str, Any], root: Path) -> None:
    a2_receipt = _load(root / A2_RECEIPT_RELATIVE)
    a4_receipt = _load(root / A4_RECEIPT_RELATIVE)
    a5_receipt = _load(root / A5_RECEIPT_RELATIVE)
    a6_receipt = _load(root / A6_RECEIPT_RELATIVE)
    a7_receipt = _load(root / A7_RECEIPT_RELATIVE)

    for stage, source_ids, carried in (
        ("A2", {e["residual_id"] for e in a2_receipt["residuals"]}, receipt["a2_residuals_carried_forward"]),
        ("A4", {e["residual_id"] for e in a4_receipt["a4_residuals"]}, receipt["a4_residuals_carried_forward"]),
        ("A5", {e["residual_id"] for e in a5_receipt["a5_residuals"]}, receipt["a5_residuals_carried_forward"]),
        ("A6", {e["residual_id"] for e in a6_receipt["a6_residuals"]}, receipt["a6_residuals_carried_forward"]),
        ("A7", {e["residual_id"] for e in a7_receipt["a7_residuals"]}, receipt["a7_residuals_carried_forward"]),
    ):
        carried_ids = {entry["residual_id"] for entry in carried}
        require(
            carried_ids == source_ids,
            f"{stage.lower()}_residuals_carried_forward does not reproduce from {stage} -- refusing",
        )
        for entry in carried:
            require(
                entry["origin_stage"] == stage and entry["status"] == "unresolved_carried_to_a8",
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


def validate_eligibility_and_safety(receipt: dict[str, Any]) -> None:
    """See ``v4_a7_original_row_factory.validate_eligibility_and_safety``
    for the identical rationale: ``rows_not_admitted`` must truthfully
    reflect ``a8_completions``, every other safety flag stays False
    unconditionally, and ``dataset_rows_emitted`` stays 0 unconditionally."""
    require(
        receipt["eligibility"] == ASSEMBLY_ELIGIBILITY,
        "receipt eligibility does not equal the frozen all-false assembly eligibility -- refusing",
    )
    safety = receipt["safety_assertions"]
    expected_rows_not_admitted = len(receipt["a8_completions"]) == 0
    require(
        safety["rows_not_admitted"] == expected_rows_not_admitted,
        "receipt safety_assertions.rows_not_admitted does not truthfully reflect whether any row has been "
        "engine-admitted via a8_completions -- refusing",
    )
    require(
        all(value is False for key, value in safety.items() if key != "rows_not_admitted"),
        "receipt safety_assertions does not hold the expected invariants -- refusing",
    )
    require(
        receipt["execution_counters"]["dataset_rows_emitted"] == 0,
        "receipt execution_counters.dataset_rows_emitted is not 0 -- refusing (dataset rows are only ever "
        "emitted at A11 release, out of scope for this stage)",
    )


@validation_session
def validate_receipt_independently(receipt: dict[str, Any], root: Path = ROOT) -> None:
    from learn_ukrainian_v4_runtime.stage_policy import validate_stage_policy

    validate_stage_policy(receipt)
    from learn_ukrainian_v4_runtime.provenance import validate_receipt_bindings

    validate_receipt_bindings(receipt, root, validate_bindings_hash_to_disk, require)
    validate_gate_matches_receipt(receipt, root)
    validate_frozen_slot_denominator(receipt, root)
    validate_engine_wiring(receipt, root)
    validate_a8_completions_shape(receipt)
    validate_eligibility_and_completion(receipt, root)
    validate_residuals_carried_from_a2_a4_a5_a6_a7(receipt, root)
    validate_no_forbidden_keys(receipt)
    validate_no_forbidden_completion_claims(receipt)
    validate_eligibility_and_safety(receipt)
    validate_receipt_schema(receipt, root)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--receipt",
        type=Path,
        default=A8_RECEIPT_PATH,
        help="A8 receipt JSON to verify (default: the tracked V4 A8 admission/assembly receipt).",
    )
    parser.add_argument(
        "--write-receipt", action="store_true", help="Assemble and persist a freshly computed receipt to --receipt."
    )
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
