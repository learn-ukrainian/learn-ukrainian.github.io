#!/usr/bin/env python3
"""V4 A9 evaluation package: held-out scoring, manifest/hash checks, and
consumer-view reproduction, wired to (never replacing) the shared
``v4_evaluation_scorer`` engine and bound to the merged A8 admission/assembly
receipt, the frozen V4 pilot slot manifest, and the V4 SHA.

A9 owns the *evaluation_package* role (``role_ownership.A9 ==
"evaluation_package"`` in the frozen slot manifest): the one place a
consumer's independent reproduction of the (currently empty) admitted slice
would be scored and re-verified. It must never alter construction after
exposure -- it only ever reads A8's own already-public receipt, never A8's
private inputs, and it never calls back into A2--A8's construction logic --
and it must never open A3's held-out membership file or A4's private
extraction ledger.

This module never loads source text, never re-fetches corpus, and never runs
live model inference over the corpus: its only inputs are seven already-
public artifacts --

* A2's source operation admission receipt (``stratum_coverage_map`` and
  ``residuals`` -- rights/coverage state, never source text),
* A4's deterministic extraction receipt (only its own already-carried
  residuals, never A4's private ledger),
* A5's evidence enrichment receipt (already-carried residuals only),
* A6's blind arena receipt (already-carried residuals only),
* A7's original-row factory receipt (its own ``a7_residuals`` only),
* A8's admission/assembly receipt (its own ``a8_residuals``,
  ``admitted_slice_view``, and ``engine_wiring.admission_receipt`` -- the
  direct upstream signal this module's gate and consumer reproduction build
  on), and
* the frozen 100-slot V4 pilot slot manifest (``slot_series`` -- public slot
  IDs only, never a real ``source_unit_id``).

Three independent parts:

1. ``check_evaluation_gate`` -- independently re-derives, from those seven
   public artifacts alone, whether a real evaluation artifact may be
   produced at all. Right now it cannot: A8 itself reports
   ``assembly_slice_ready: false`` (A8 admitted zero rows, so there is
   nothing admitted to evaluate), so per the binding contract this module
   must *never* claim ``EVAL_ARTIFACT_READY`` while that is true; it reports
   ``evaluation_slice_ready: false`` and a typed ``blocked_reason_code``
   instead.
2. ``build_consumer_reproduction_view`` -- reproduces, per frozen slot,
   exactly what a consumer rebuilding A8's public admitted slice would see.
   It cross-checks every ``row_admitted`` claim in A8's own
   ``admitted_slice_view`` against A8's own ``engine_wiring
   .admission_receipt.rows`` (the shared admission engine's own admitted
   rows) and fails closed -- refuses, never silently drops -- if a row ever
   appears in the view without a matching real A8 admission. Today every
   entry is unadmitted, so this passes trivially; the check exists precisely
   so it cannot be bypassed once a real row appears.
3. ``build_receipt`` -- assembles the public receipt: the frozen 100-slot
   denominator (reusing, never duplicating,
   ``v4_a6_blind_arena.frozen_slot_strata``/``all_frozen_slot_ids``), the
   gate, a real (zero-row) call into the shared, unmodified
   ``v4_evaluation_scorer.score_rows`` engine proving A9's own wiring is
   live rather than declarative, every A2/A4/A5/A6/A7/A8 residual carried
   forward unresolved, the consumer reproduction view, and one typed
   per-slot A9 residual reusing A8's own already-public per-stratum reason
   codes -- never a fourth, independently invented reason.

Run with no arguments to verify the checked-in A9 receipt reproduces from the
seven public artifacts on disk -- no ``batch_state/`` required, so this
passes in a fresh checkout. Pass ``--write-receipt`` to (re)assemble and
persist it after a genuine change to one of those seven artifacts or to this
module or the shared evaluation scorer.
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

from scripts.projects.open_model_data import v4_a8_admission_assembly as a8
from scripts.projects.open_model_data import v4_evaluation_scorer as scorer

ROOT = _SELF_ROOT
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"

A9_RECEIPT_PATH = ADMISSION / "dataset_v4_a9_evaluation_package_receipt_v1.json"
A9_SCHEMA_PATH = CONTRACTS / "dataset_v4_a9_evaluation_package_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_PATH = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
A6_RECEIPT_PATH = ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json"
A7_RECEIPT_PATH = ADMISSION / "dataset_v4_a7_original_row_factory_receipt_v1.json"
A8_RECEIPT_PATH = ADMISSION / "dataset_v4_a8_admission_assembly_receipt_v1.json"
SLOT_MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"
SCORER_ENGINE_PATH = ROOT / "scripts/projects/open_model_data/v4_evaluation_scorer.py"
SELF_PATH = ROOT / "scripts/projects/open_model_data/v4_a9_evaluation_package.py"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

# Mirrors v4_a8_admission_assembly.FORBIDDEN_KEYS exactly -- "gold" is
# deliberately excluded because it is the name of this receipt's own
# always-false eligibility flag, never a real gold label.
FORBIDDEN_KEYS = a8.FORBIDDEN_KEYS
FORBIDDEN_SUBSTRINGS = a8.FORBIDDEN_SUBSTRINGS

# Completion-vocabulary claims that belong to other roles or are unreachable
# today (see the manifest's own completion_vocabulary and A0's non_goals) --
# never emitted here. Unlike A8's own list, "ADMITTED_SLICE_READY" (A8's own
# ready state, now a foreign claim from A9's point of view) is added, and
# "EVAL_ARTIFACT_READY" (A9's own legitimate -- if currently unreachable --
# ready state) is removed, mirroring how each stage excludes only its own
# name from the borrowed forbidden-claims list.
FORBIDDEN_COMPLETION_CLAIMS = tuple(
    sorted({*a8.FORBIDDEN_COMPLETION_CLAIMS, "ADMITTED_SLICE_READY"} - {"EVAL_ARTIFACT_READY"})
)

EVALUATION_ELIGIBILITY = {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}

canonical_json = a8.canonical_json
sha256_text = a8.sha256_text
sha256_file = a8.sha256_file


class EvaluationPackageError(ValueError):
    """The A9 wiring or its deterministic receipt is unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvaluationPackageError(message)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# --- A8 reason -> A9 per-slot residual reason --------------------------------
#
# A8 already types each frozen slot's blocker as one of three reason codes
# (reused unchanged from A7's own mapping). A9 never invents a fourth --
# "why has A8 not assembled a row for this slot" is exactly "why can A9 not
# score one".
A9_NEXT_ACTION_BY_REASON = {
    "rights_unknown": (
        "no admitted row exists to evaluate for this frozen slot until A2 resolves unit-specific "
        "training/derivation rights for its stratum's supporting source unit -- never score a placeholder row "
        "while rights remain unknown"
    ),
    "source_incomplete": (
        "no source unit is yet identified for this frozen slot's stratum, so A8 has nothing assembled and A9 "
        "has nothing to score -- never invent or substitute a placeholder score"
    ),
    "independence_unavailable": (
        "a supporting source unit is identified for this frozen slot's stratum but its coverage/rights review "
        "is not yet complete, so A8 assembled no row for it and A9 has nothing to score yet"
    ),
}


# --- evaluation gate (public-only) -------------------------------------------


def check_evaluation_gate(root: Path = ROOT) -> dict[str, Any]:
    """Independently re-derive whether a real evaluation artifact may be
    produced at all, from the frozen slot manifest's own ``assignment_state``
    per stratum, A2's own residuals, and A8's independent validity -- never
    trusting the A9 receipt's own declared fields, never opening
    ``batch_state/``. ``evaluation_slice_ready`` is only ever true once every
    frozen slot is assigned to a real source unit *and* A2 has zero
    unresolved residuals *and* A8 itself still independently validates.

    Fails closed -- a *closed gate*, not an exception -- if any of the three
    required public artifacts (slot manifest, A2 receipt, A8 receipt) is
    missing, mirroring ``v4_a8_admission_assembly.check_assembly_gate``'s own
    missing-artifact handling."""
    manifest_path = (root / "data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json").resolve()
    a2_path = (root / "data/projects/open_model_data/admission/dataset_v4_a2_source_operation_admission_receipt_v1.json").resolve()
    a8_path = (root / "data/projects/open_model_data/admission/dataset_v4_a8_admission_assembly_receipt_v1.json").resolve()
    required_paths = {"slot_manifest": manifest_path, "a2_receipt": a2_path, "a8_receipt": a8_path}
    for label, path in required_paths.items():
        require(root.resolve() in path.parents, f"{label} path escapes the repository root -- refusing")

    missing = sorted(label for label, path in required_paths.items() if not path.is_file())
    if missing:
        return {
            "gate_id": "v4-a9-evaluation-gate-v1",
            "a8_receipt_valid": False,
            "a2_rights_resolved": False,
            "all_slots_assigned": False,
            "slots_ready": 0,
            "slots_residual": 100,
            "evaluation_slice_ready": False,
            "owner_role": "A2_A3_PRIVATE_ARTIFACT",
            "blocked_reason_code": f"required_public_artifact_missing:{missing[0]}",
        }

    manifest = _load(manifest_path)
    require(manifest.get("controlling_outcome_sha256") == V4_SHA256, "slot manifest is not bound to the expected V4 controlling outcome -- refusing")

    a2_receipt = _load(a2_path)
    require(a2_receipt.get("controlling_outcome_sha256") == V4_SHA256, "A2 receipt is not bound to the expected V4 controlling outcome -- refusing")

    # Per-slot, never a single global AND across all 100 slots: resolving one
    # stratum's residual never depends on, or unblocks, any other stratum.
    readiness = a8.a7.per_slot_readiness(manifest, a2_receipt)
    rights_resolved = all(record["rights_resolved"] for record in readiness)
    all_assigned = all(record["assigned"] for record in readiness)

    a8_receipt = _load(a8_path)
    try:
        a8.validate_receipt_independently(a8_receipt, root)
        a8_valid = True
    except a8.AdmissionAssemblyError:
        a8_valid = False

    slots_ready = sum(1 for record in readiness if record["slot_ready"]) if a8_valid else 0
    slots_residual = len(readiness) - slots_ready
    evaluation_slice_ready = slots_ready == len(readiness)

    blocked_reason_code = None
    if not evaluation_slice_ready:
        if not a8_valid:
            blocked_reason_code = "a8_receipt_invalid"
        elif slots_ready == 0:
            if not rights_resolved and not all_assigned:
                blocked_reason_code = "rights_unresolved_and_slots_unassigned"
            elif not rights_resolved:
                blocked_reason_code = "rights_unresolved"
            else:
                blocked_reason_code = "slot_assignment_pending_a2_a3"
        else:
            # Some, but not all, frozen slots are ready -- the case the old
            # global-AND gate could never represent.
            blocked_reason_code = "partial_slots_pending_a2_a3"

    return {
        "gate_id": "v4-a9-evaluation-gate-v1",
        "a8_receipt_valid": a8_valid,
        "a2_rights_resolved": rights_resolved,
        "all_slots_assigned": all_assigned,
        "slots_ready": slots_ready,
        "slots_residual": slots_residual,
        "evaluation_slice_ready": evaluation_slice_ready,
        "owner_role": manifest["sealed_heldout_commitment"]["assignment_owner"],
        "blocked_reason_code": blocked_reason_code,
    }


# --- A9's own per-slot residuals (public, source-free) -----------------------


def derive_a9_slot_residuals(manifest: dict[str, Any], a2_receipt: dict[str, Any], gate: dict[str, Any]) -> list[dict[str, Any]]:
    """One typed residual per frozen public slot ID -- never a silently
    dropped slot and never an evaluation score invented in place of the
    missing admitted row. A pure function of the manifest's own
    ``slot_series``, A8's own already-public per-stratum reason codes, and
    the gate this module itself re-derives; never opens any private state."""
    owner_role = gate["owner_role"]
    reasons_by_stratum = a8.a7.stratum_reason_codes(a2_receipt)
    residuals = []
    for stratum_entry in a8.a7.a6.frozen_slot_strata(manifest):
        stratum = stratum_entry["stratum"]
        reason_code = reasons_by_stratum[stratum]
        for slot_id in stratum_entry["slot_ids"]:
            residuals.append(
                {
                    "residual_id": f"a9-residual-{reason_code.replace('_', '-')}-{slot_id}",
                    "subject_kind": "pilot_slot",
                    "subject_id": slot_id,
                    "stage": "A9",
                    "reason_code": reason_code,
                    "owner_role": owner_role,
                    "next_action": A9_NEXT_ACTION_BY_REASON[reason_code],
                    "retryability": "retryable",
                    "evidence_refs": [
                        "admission.dataset_v4_pilot_slot_manifest_v1.slot_series",
                        "admission.dataset_v4_a2_source_operation_admission_receipt_v1.stratum_coverage_map",
                        "admission.dataset_v4_a8_admission_assembly_receipt_v1.a8_residuals",
                    ],
                }
            )
    residuals.sort(key=lambda residual: residual["subject_id"])
    return residuals


# --- consumer reproduction of A8's admitted slice (public, fail-closed) ------


def build_consumer_reproduction_view(manifest: dict[str, Any], a8_receipt: dict[str, Any], a9_residuals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reproduce, per frozen slot, exactly what an independent consumer
    rebuilding A8's public admitted slice would see -- and fail closed if a
    row ever appears in A8's own ``admitted_slice_view`` without a matching
    real admission in A8's own shared-engine call. Never trusts A8's
    ``row_admitted`` flag by itself; always cross-checks it against A8's own
    ``engine_wiring.admission_receipt.rows``, the one place a row is really
    admitted."""
    residual_by_slot = {residual["subject_id"]: residual["residual_id"] for residual in a9_residuals}
    admitted_rows_by_id = {
        row["row_id"]: row for row in a8_receipt["engine_wiring"]["admission_receipt"]["rows"] if row.get("disposition") == "admitted"
    }
    expected_slot_ids = set(a8.a7.a6.all_frozen_slot_ids(manifest))
    seen_slot_ids = {entry["slot_id"] for entry in a8_receipt["admitted_slice_view"]}
    require(seen_slot_ids == expected_slot_ids, "A8 admitted_slice_view does not cover exactly the frozen slot manifest -- refusing consumer reproduction")

    view = []
    for entry in a8_receipt["admitted_slice_view"]:
        slot_id = entry["slot_id"]
        row_admitted = entry["row_admitted"]
        row_id = entry["row_id"]
        if row_admitted:
            require(
                isinstance(row_id, str) and row_id in admitted_rows_by_id,
                f"A8 admitted_slice_view claims an admitted row for slot {slot_id!r} that is not present in A8's own "
                "admitted engine rows -- refusing (a row appeared without real A8 admission)",
            )
            row_content_sha256 = admitted_rows_by_id[row_id]["row_content_sha256"]
            require(
                isinstance(row_content_sha256, str) and len(row_content_sha256) == 64,
                f"A8's own admitted row for slot {slot_id!r} does not carry a valid row_content_sha256 -- refusing",
            )
        else:
            require(row_id is None, f"A8 admitted_slice_view carries a row_id for a non-admitted slot {slot_id!r} -- refusing")
        view.append(
            {
                "slot_id": slot_id,
                "row_admitted": row_admitted,
                "row_id": row_id,
                "scored": False,
                "score": None,
                "residual_id": residual_by_slot[slot_id],
            }
        )
    view.sort(key=lambda entry: entry["slot_id"])
    return view


# --- shared engine wiring (real call, zero rows today) ------------------------


def run_engine_scoring(admitted_rows: list[dict[str, Any]] = ()) -> dict[str, Any]:  # type: ignore[assignment]
    """A real (never stubbed) call into the shared, already-on-main
    ``v4_evaluation_scorer.score_rows`` engine, bound to the V4 controlling
    outcome. A8 admitted zero rows, so there is nothing to score;
    ``admitted_rows`` stays empty and the engine's own counters
    (``scored_rows``, ``unscored_rows``) both come back 0 -- proving A9's own
    wiring into the unmodified, fail-closed scoring engine is live, never
    fabricating a row to exercise it."""
    return scorer.score_rows(outcome_sha256=V4_SHA256, admitted_rows=list(admitted_rows))


# --- receipt assembly --------------------------------------------------------


def build_receipt(root: Path = ROOT) -> dict[str, Any]:
    manifest = _load(SLOT_MANIFEST_PATH)
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)
    a5_receipt = _load(A5_RECEIPT_PATH)
    a6_receipt = _load(A6_RECEIPT_PATH)
    a7_receipt = _load(A7_RECEIPT_PATH)
    a8_receipt = _load(A8_RECEIPT_PATH)
    gate = check_evaluation_gate(root)

    strata = a8.a7.a6.frozen_slot_strata(manifest)
    frozen_slot_ids = a8.a7.a6.all_frozen_slot_ids(manifest)

    a2_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A2", "status": "unresolved_carried_to_a9"}
        for entry in a2_receipt["residuals"]
    ]
    a4_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A4", "status": "unresolved_carried_to_a9"}
        for entry in a4_receipt["a4_residuals"]
    ]
    a5_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A5", "status": "unresolved_carried_to_a9"}
        for entry in a5_receipt["a5_residuals"]
    ]
    a6_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A6", "status": "unresolved_carried_to_a9"}
        for entry in a6_receipt["a6_residuals"]
    ]
    a7_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A7", "status": "unresolved_carried_to_a9"}
        for entry in a7_receipt["a7_residuals"]
    ]
    a8_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A8", "status": "unresolved_carried_to_a9"}
        for entry in a8_receipt["a8_residuals"]
    ]

    scoring_receipt = run_engine_scoring([])
    a9_residuals = derive_a9_slot_residuals(manifest, a2_receipt, gate)
    consumer_view = build_consumer_reproduction_view(manifest, a8_receipt, a9_residuals)

    return {
        "schema_version": "dataset_v4_a9_evaluation_package_receipt_v1",
        "receipt_id": "dataset-v4-a9-evaluation-package-v1",
        "status": (
            "A9_EVALUATION_PACKAGE_AND_PARSER_READY_SLICE_NOT_READY_TEXT_FREE_NO_EVAL_ARTIFACT"
            if not gate["evaluation_slice_ready"]
            else "EVAL_ARTIFACT_READY"
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
            "pilot_slot_manifest": {
                "path": str(SLOT_MANIFEST_PATH.relative_to(root)),
                "sha256": sha256_file(SLOT_MANIFEST_PATH),
                "schema_version": "dataset_v4_pilot_slot_manifest_v1",
            },
            "scorer_engine_implementation": {
                "path": str(SCORER_ENGINE_PATH.relative_to(root)),
                "sha256": sha256_file(SCORER_ENGINE_PATH),
                "schema_version": "v4_evaluation_scorer_script_v1",
            },
            "wiring_implementation": {
                "path": str(SELF_PATH.relative_to(root)),
                "sha256": sha256_file(SELF_PATH),
                "schema_version": "v4_a9_evaluation_package_script_v1",
            },
        },
        "role_map": manifest["role_ownership"],
        "frozen_slot_denominator": {"total_slots": len(frozen_slot_ids), "strata": strata},
        "evaluation_gate": {
            "gate_id": gate["gate_id"],
            "requires": ["a8_receipt_independently_valid", "per_slot_a2_rights_resolved", "per_slot_manifest_assignment"],
            "a8_receipt_valid": gate["a8_receipt_valid"],
            "a2_rights_resolved": gate["a2_rights_resolved"],
            "all_slots_assigned": gate["all_slots_assigned"],
            "slots_ready": gate["slots_ready"],
            "slots_residual": gate["slots_residual"],
            "evaluation_slice_ready": gate["evaluation_slice_ready"],
            "owner_role": gate["owner_role"],
            "blocked_reason_code": gate["blocked_reason_code"],
        },
        "scorer_wiring": {
            "scorer_schema_version": scorer.SCHEMA_VERSION,
            "scorer_input_schema_version": scorer.INPUT_SCHEMA_VERSION,
            "unscorable_residual_code": scorer.UNSCORABLE_RESIDUAL_CODE,
            "scoring_receipt": scoring_receipt,
        },
        "a2_residuals_carried_forward": a2_residuals_carried,
        "a4_residuals_carried_forward": a4_residuals_carried,
        "a5_residuals_carried_forward": a5_residuals_carried,
        "a6_residuals_carried_forward": a6_residuals_carried,
        "a7_residuals_carried_forward": a7_residuals_carried,
        "a8_residuals_carried_forward": a8_residuals_carried,
        "a9_residuals": a9_residuals,
        "consumer_reproduction_view": consumer_view,
        "execution_counters": {
            "dataset_rows_emitted": 0,
            "candidate_rows_scored": scoring_receipt["counts"]["scored_rows"],
            "rows_considered_for_scoring": scoring_receipt["counts"]["input_rows"],
            "frozen_slot_count": len(frozen_slot_ids),
            "slots_eval_ready": gate["slots_ready"],
            "slots_blocked": gate["slots_residual"],
        },
        "eligibility": dict(EVALUATION_ELIGIBILITY),
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
    schema = _load(A9_SCHEMA_PATH)
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
    gate = check_evaluation_gate(root)
    declared = receipt["evaluation_gate"]
    require(
        declared["a8_receipt_valid"] == gate["a8_receipt_valid"]
        and declared["a2_rights_resolved"] == gate["a2_rights_resolved"]
        and declared["all_slots_assigned"] == gate["all_slots_assigned"]
        and declared["slots_ready"] == gate["slots_ready"]
        and declared["slots_residual"] == gate["slots_residual"]
        and declared["evaluation_slice_ready"] == gate["evaluation_slice_ready"]
        and declared["blocked_reason_code"] == gate["blocked_reason_code"],
        "receipt evaluation_gate does not match the state independently re-derived from the live public artifacts "
        "-- refusing (re-verify/regenerate required)",
    )
    require(
        gate["evaluation_slice_ready"] or receipt["status"] != "EVAL_ARTIFACT_READY",
        "receipt claims EVAL_ARTIFACT_READY while the independently re-derived gate is closed -- refusing",
    )


def validate_frozen_slot_denominator(receipt: dict[str, Any], root: Path) -> None:
    manifest = _load(SLOT_MANIFEST_PATH)
    expected_strata = a8.a7.a6.frozen_slot_strata(manifest)
    declared = receipt["frozen_slot_denominator"]
    require(declared["strata"] == expected_strata, "frozen_slot_denominator.strata does not reproduce from the live slot manifest -- refusing")
    all_ids = [slot_id for stratum in expected_strata for slot_id in stratum["slot_ids"]]
    require(len(all_ids) == 100 and len(set(all_ids)) == 100, "frozen slot denominator did not expand to exactly 100 unique slot IDs -- refusing")
    require(declared["total_slots"] == 100, "frozen_slot_denominator.total_slots is not 100 -- refusing")


def validate_scorer_wiring(receipt: dict[str, Any]) -> None:
    """Re-runs the real shared scorer engine call and requires a byte-
    identical result, plus makes the engine independently verify its own
    nested receipt (``v4_evaluation_scorer.verify_receipt``) -- proving this
    is a live wire into the on-main engine at the evaluation-package layer
    too, not a declared/stubbed shape."""
    wiring = receipt["scorer_wiring"]
    require(
        wiring["scorer_schema_version"] == scorer.SCHEMA_VERSION and wiring["scorer_input_schema_version"] == scorer.INPUT_SCHEMA_VERSION,
        "scorer_wiring schema versions do not match the live v4_evaluation_scorer module -- refusing (engine changed without regenerating this receipt)",
    )
    require(
        wiring["unscorable_residual_code"] == scorer.UNSCORABLE_RESIDUAL_CODE,
        "scorer_wiring.unscorable_residual_code does not match the live engine's UNSCORABLE_RESIDUAL_CODE -- refusing",
    )
    recomputed = scorer.score_rows(outcome_sha256=V4_SHA256, admitted_rows=[])
    require(wiring["scoring_receipt"] == recomputed, "scorer_wiring.scoring_receipt does not reproduce from a live, zero-row v4_evaluation_scorer.score_rows call -- refusing")
    scorer.verify_receipt(wiring["scoring_receipt"])
    require(
        wiring["scoring_receipt"]["counts"] == {"input_rows": 0, "scored_rows": 0, "unscored_rows": 0},
        "scorer_wiring.scoring_receipt does not report zero rows -- refusing (no admitted row exists yet; "
        "dataset_rows_emitted must stay 0)",
    )


def validate_residuals_and_consumer_view(receipt: dict[str, Any], root: Path) -> None:
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)
    a5_receipt = _load(A5_RECEIPT_PATH)
    a6_receipt = _load(A6_RECEIPT_PATH)
    a7_receipt = _load(A7_RECEIPT_PATH)
    a8_receipt = _load(A8_RECEIPT_PATH)
    manifest = _load(SLOT_MANIFEST_PATH)
    gate = check_evaluation_gate(root)

    for stage, source_ids, carried in (
        ("A2", {e["residual_id"] for e in a2_receipt["residuals"]}, receipt["a2_residuals_carried_forward"]),
        ("A4", {e["residual_id"] for e in a4_receipt["a4_residuals"]}, receipt["a4_residuals_carried_forward"]),
        ("A5", {e["residual_id"] for e in a5_receipt["a5_residuals"]}, receipt["a5_residuals_carried_forward"]),
        ("A6", {e["residual_id"] for e in a6_receipt["a6_residuals"]}, receipt["a6_residuals_carried_forward"]),
        ("A7", {e["residual_id"] for e in a7_receipt["a7_residuals"]}, receipt["a7_residuals_carried_forward"]),
        ("A8", {e["residual_id"] for e in a8_receipt["a8_residuals"]}, receipt["a8_residuals_carried_forward"]),
    ):
        carried_ids = {entry["residual_id"] for entry in carried}
        require(carried_ids == source_ids, f"{stage.lower()}_residuals_carried_forward does not reproduce from {stage} -- refusing")
        for entry in carried:
            require(
                entry["origin_stage"] == stage and entry["status"] == "unresolved_carried_to_a9",
                f"{stage.lower()}_residuals_carried_forward entry has an unexpected origin_stage/status -- refusing",
            )

    expected_a9_residuals = derive_a9_slot_residuals(manifest, a2_receipt, gate)
    require(receipt["a9_residuals"] == expected_a9_residuals, "a9_residuals does not reproduce from the live slot manifest, A2 receipt, and gate -- refusing")

    expected_view = build_consumer_reproduction_view(manifest, a8_receipt, expected_a9_residuals)
    require(receipt["consumer_reproduction_view"] == expected_view, "consumer_reproduction_view does not reproduce from the live A8 receipt and a9_residuals -- refusing")
    require(
        all(entry["row_admitted"] is False and entry["row_id"] is None and entry["scored"] is False and entry["score"] is None for entry in receipt["consumer_reproduction_view"]),
        "consumer_reproduction_view claims an admitted or scored row while no rights-cleared row exists -- refusing",
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
    require(receipt["eligibility"] == EVALUATION_ELIGIBILITY, "receipt eligibility does not equal the frozen all-false evaluation eligibility -- refusing")
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
    validate_scorer_wiring(receipt)
    validate_residuals_and_consumer_view(receipt, root)
    validate_no_forbidden_keys(receipt)
    validate_no_forbidden_completion_claims(receipt)
    validate_eligibility_and_safety_all_false(receipt)
    validate_receipt_schema(receipt)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--receipt", type=Path, default=A9_RECEIPT_PATH, help="A9 receipt JSON to verify (default: the tracked V4 A9 evaluation package receipt).")
    parser.add_argument("--write-receipt", action="store_true", help="Assemble and persist a freshly computed receipt to --receipt.")
    args = parser.parse_args(argv)

    if args.write_receipt:
        receipt = build_receipt()
        validate_receipt_independently(receipt)
        args.receipt.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        print(canonical_json({"status": receipt["status"], "evaluation_gate": receipt["evaluation_gate"]}))
        return

    receipt = _load(args.receipt)
    validate_receipt_independently(receipt)
    print(canonical_json({"status": receipt["status"], "evaluation_gate": receipt["evaluation_gate"]}))


if __name__ == "__main__":
    try:
        main()
    except EvaluationPackageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
