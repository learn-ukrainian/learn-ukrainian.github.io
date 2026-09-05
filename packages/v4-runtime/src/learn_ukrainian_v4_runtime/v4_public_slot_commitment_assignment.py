#!/usr/bin/env python3
"""V4 public-slot -> A4-commitment assignment: binds every frozen, public
``v4p-*`` slot to a builder-eligible A4 HMAC commitment (or a typed
residual), bound to the merged A4 deterministic-extraction receipt and the
frozen V4 pilot slot manifest.

This is *not* a new A-stage number. A0-A13 already exist on main with zero
admitted rows because every frozen slot stays ``UNASSIGNED_PENDING_A2_A3``
(see the frozen manifest's own ``slot_series``). This module answers one
narrow question honestly, for every one of the 100 frozen slots, without
ever dropping a slot from the denominator: *is a builder-eligible A4
commitment bound to this slot yet, and if not, why not?*

The answer is structural, not merely "not yet done": A4's own unit-commitment
algorithm is deliberately ``content_blind`` (see
``dataset_v4_a4_deterministic_extraction_receipt_v1.json``'s
``builder_packet_consumption.unit_commitment_algorithm``) -- a published
commitment HMAC carries no stratum label. Binding a specific commitment to a
specific stratum's public slot would require this module to open the
private ``source_unit_id`` -> stratum mapping (the private builder packet or
A2's own internal ledger), which it must never do: doing so, and then
publishing the result, would itself be exactly the stratum-to-commitment
leak the V4 rights/firewall contract forbids (it would let a reader narrow
down which real source units are candidates for a given stratum, risking
identification of singleton candidate families or the sealed held-out
complement by elimination). So every ``assignment_status`` this module can
ever honestly publish is ``"residual"`` -- see ``COMMITMENT_BINDING_POLICY``
below, which documents this as a fixed policy, not a live computation.

This module never loads source text, never re-fetches corpus, and never
opens A3's held-out membership file, A4's private extraction ledger, or the
private builder packet: its only inputs are three already-public artifacts
--

* A2's source operation admission receipt (``stratum_coverage_map`` and
  ``residuals`` -- rights/coverage state, never source text),
* A4's deterministic extraction receipt (only its own already-published,
  content-blind ``builder_packet_consumption.unit_commitments`` and its own
  already-carried residuals, never A4's private ledger), and
* the frozen 100-slot V4 pilot slot manifest (``slot_series`` -- public slot
  IDs only, never a real ``source_unit_id``).

Two independent parts:

1. ``check_assignment_gate`` -- independently re-derives, from those three
   public artifacts alone, the assignment state: whether A2's rights are
   resolved (informational only -- it does not unlock assignment, since the
   real blocker is structural, not rights) and how many builder-eligible
   commitments A4 has published. ``assignment_ready`` and
   ``stratum_commitment_binding_available`` are frozen ``False`` -- this
   module has no path to ever flip them without violating the firewall.
2. ``build_receipt`` -- assembles the public receipt: the frozen 100-slot
   denominator (reusing, never duplicating,
   ``v4_a7_original_row_factory.a6.frozen_slot_strata``/
   ``all_frozen_slot_ids``), the republished (never re-derived) content-blind
   commitment pool A4 already made public, one typed ``assignment_record``
   per frozen slot (``commitment_sha256`` always ``null``,
   ``assignment_status`` always ``"residual"``, reusing A2's own already-
   public per-stratum reason code -- ``rights_unknown``,
   ``source_incomplete``, or ``independence_unavailable`` -- never a fourth
   invented reason), every A2/A4 residual carried forward unresolved, and a
   real (zero-row) call into the shared
   ``v4_original_row_admission.admit_rows`` engine proving this module's own
   wiring is live rather than declarative.

Run with no arguments to verify the checked-in receipt reproduces from the
three public artifacts on disk -- no ``batch_state/`` required, so this
passes in a fresh checkout. Pass ``--write-receipt`` to (re)assemble and
persist it after a genuine change to one of those three artifacts or to this
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

from learn_ukrainian_v4_runtime import v4_a4_deterministic_extraction as a4
from learn_ukrainian_v4_runtime import v4_a7_original_row_factory as a7

ROOT = _SELF_ROOT
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"

ASSIGNMENT_RECEIPT_PATH = ADMISSION / "dataset_v4_public_slot_commitment_assignment_receipt_v1.json"
ASSIGNMENT_SCHEMA_PATH = CONTRACTS / "dataset_v4_public_slot_commitment_assignment_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
SLOT_MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"
ADMISSION_ENGINE_PATH = ROOT / "scripts/projects/open_model_data/v4_original_row_admission.py"
SELF_PATH = ROOT / "scripts/projects/open_model_data/v4_public_slot_commitment_assignment.py"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

# Mirrors v4_a7_original_row_factory.FORBIDDEN_KEYS/FORBIDDEN_SUBSTRINGS exactly
# -- reused, never redefined, so every builder-facing V4 module stays aligned
# on what counts as a leak. "gold" stays excluded because it is the name of
# this receipt's own always-false eligibility flag, never a real gold label.
FORBIDDEN_KEYS = a7.FORBIDDEN_KEYS
FORBIDDEN_SUBSTRINGS = a7.FORBIDDEN_SUBSTRINGS

# Completion-vocabulary claims that belong to other roles or are unreachable
# by this module -- never emitted here. Mirrors v4_a7_original_row_factory's
# own list.
FORBIDDEN_COMPLETION_CLAIMS = a7.FORBIDDEN_COMPLETION_CLAIMS

ASSIGNMENT_ELIGIBILITY = {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}

# The fixed, data-independent binding policy. Never varies with A2/A4 state
# -- the block is structural (A4's commitments are content-blind by design),
# not a temporary "not yet done." Republished verbatim in every receipt this
# module ever produces so a reader never mistakes today's zero-assigned
# count for a bug rather than the intended, permanent, privacy-preserving
# outcome.
COMMITMENT_BINDING_POLICY = {
    "policy_id": "v4-public-slot-commitment-binding-policy-v1",
    "stratum_commitment_binding_ever_public": False,
    "reason": (
        "A4's published unit commitments are content-blind by design "
        "(builder_packet_consumption.unit_commitment_algorithm.content_blind == true): a commitment HMAC "
        "carries no stratum label. Binding a specific commitment to a specific stratum's public slot would "
        "require opening the private source_unit_id-to-stratum mapping, which this module must never do -- "
        "publishing the result would itself be a stratum-to-commitment leak forbidden by the V4 rights/"
        'firewall contract. Every assignment_status this module can ever publish is therefore "residual".'
    ),
    "owner_role": "A2_A3_PRIVATE_ARTIFACT",
}

canonical_json = a7.canonical_json
sha256_text = a7.sha256_text
sha256_file = a7.sha256_file


class SlotAssignmentError(ValueError):
    """The public-slot commitment-assignment wiring or its receipt is unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SlotAssignmentError(message)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# --- A2 stratum reason -> per-slot residual reason ---------------------------
#
# Reused unchanged from v4_a7_original_row_factory.stratum_reason_codes so
# this module's per-slot reason codes can never silently drift from A7's own
# already-public mapping.
ASSIGNMENT_NEXT_ACTION_BY_REASON = {
    "rights_unknown": (
        "no builder-eligible commitment may be bound to this frozen slot until A2 resolves unit-specific "
        "training/derivation rights for its stratum's supporting source unit -- this module never binds a "
        "commitment while rights remain unknown"
    ),
    "source_incomplete": (
        "no source unit is yet identified for this frozen slot's stratum -- this module never invents or "
        "substitutes a placeholder commitment binding"
    ),
    "independence_unavailable": (
        "a supporting source unit is identified for this frozen slot's stratum but its coverage/rights review "
        "is not yet complete, and A4's published commitments are content-blind -- no commitment may be safely "
        "bound to this slot without opening the private stratum-to-source-unit mapping this module must never "
        "open"
    ),
}


# --- assignment gate (public-only) --------------------------------------------


def check_assignment_gate(root: Path = ROOT) -> dict[str, Any]:
    """Independently re-derive the assignment state from the three public
    artifacts alone -- never trusting the receipt's own declared fields,
    never opening ``batch_state/``. ``assignment_ready`` and
    ``stratum_commitment_binding_available`` are always ``False``: this is a
    structural property of A4's content-blind commitment algorithm, not a
    condition that resolves once A2's rights residuals do (that only
    changes ``a2_rights_resolved``, reported here purely for visibility).

    Fails closed -- a *closed gate*, not an exception -- if any of the three
    required public artifacts (slot manifest, A2 receipt, A4 receipt) is
    missing, mirroring the other V4 modules' own missing-artifact
    handling."""
    manifest_path = (root / "data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json").resolve()
    a2_path = (
        root / "data/projects/open_model_data/admission/dataset_v4_a2_source_operation_admission_receipt_v1.json"
    ).resolve()
    a4_path = (
        root / "data/projects/open_model_data/admission/dataset_v4_a4_deterministic_extraction_receipt_v1.json"
    ).resolve()
    required_paths = {"slot_manifest": manifest_path, "a2_receipt": a2_path, "a4_receipt": a4_path}
    for label, path in required_paths.items():
        require(root.resolve() in path.parents, f"{label} path escapes the repository root -- refusing")

    missing = sorted(label for label, path in required_paths.items() if not path.is_file())
    if missing:
        return {
            "gate_id": "v4-public-slot-commitment-assignment-gate-v1",
            "a4_receipt_valid": False,
            "a2_rights_resolved": False,
            "builder_eligible_commitments_available": 0,
            "stratum_commitment_binding_available": False,
            "assignment_ready": False,
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
    rights_resolved = len(a2_receipt.get("residuals", [])) == 0

    a4_receipt = _load(a4_path)
    try:
        a4.validate_receipt_independently(a4_receipt, root)
        a4_valid = True
    except a4.ExtractionError:
        a4_valid = False

    commitments_available = (
        len(a4_receipt.get("builder_packet_consumption", {}).get("unit_commitments", [])) if a4_valid else 0
    )

    blocked_reason_code = "required_public_artifact_missing:none" if a4_valid else "a4_receipt_invalid"
    if a4_valid:
        # The real reason is always structural (content-blind commitments),
        # never merely "A2 rights are unresolved" -- reported even once
        # rights resolve, so a reader never mistakes a future rights
        # resolution for a path to a real per-slot binding.
        blocked_reason_code = "stratum_commitment_binding_unavailable_content_blind"

    return {
        "gate_id": "v4-public-slot-commitment-assignment-gate-v1",
        "a4_receipt_valid": a4_valid,
        "a2_rights_resolved": rights_resolved,
        "builder_eligible_commitments_available": commitments_available,
        "stratum_commitment_binding_available": False,
        "assignment_ready": False,
        "owner_role": manifest["sealed_heldout_commitment"]["assignment_owner"],
        "blocked_reason_code": blocked_reason_code,
    }


# --- commitment pool (public, republished from A4 verbatim) ------------------


def build_commitment_pool(a4_receipt: dict[str, Any]) -> dict[str, Any]:
    """Republishes (never re-derives, never expands) A4's own already-public
    content-blind commitment pool -- the same ``unit_commitments`` A4's own
    receipt already carries in ``builder_packet_consumption``. No stratum
    label is ever attached here."""
    consumption = a4_receipt["builder_packet_consumption"]
    algorithm = consumption["unit_commitment_algorithm"]
    require(
        algorithm["content_blind"] is True,
        "A4's unit_commitment_algorithm is not content_blind -- refusing to republish it as a safe pool",
    )
    commitments = sorted(consumption["unit_commitments"])
    return {
        "pool_id": "v4-public-slot-commitment-pool-v1",
        "commitment_algorithm_id": algorithm["algorithm_id"],
        "commitment_algorithm_descriptor_sha256": algorithm["algorithm_descriptor_sha256"],
        "content_blind": algorithm["content_blind"],
        "total_builder_eligible_commitments": len(commitments),
        "commitments": commitments,
    }


# --- per-slot assignment records (public, source-free) -----------------------


def derive_assignment_records(
    manifest: dict[str, Any], a2_receipt: dict[str, Any], gate: dict[str, Any]
) -> list[dict[str, Any]]:
    """One typed assignment record per frozen public slot ID -- never a
    silently dropped slot and never a fabricated commitment binding. A pure
    function of the manifest's own ``slot_series``, A2's own public reason
    codes, and the gate this module itself re-derives; never opens any
    private state. ``commitment_sha256`` is always ``null`` and
    ``assignment_status`` is always ``"residual"`` -- see
    ``COMMITMENT_BINDING_POLICY``. The residual reason code is identical in
    shape and uniformly present across every stratum (each stratum's slots
    all carry the *same* reason, and every stratum has one), so no stratum's
    absence of an assigned slot is distinguishable from any other's --
    a reader cannot use this table to single out the sealed held-out
    complement."""
    owner_role = gate["owner_role"]
    reasons_by_stratum = a7.stratum_reason_codes(a2_receipt)
    records = []
    for stratum_entry in a7.a6.frozen_slot_strata(manifest):
        stratum = stratum_entry["stratum"]
        reason_code = reasons_by_stratum[stratum]
        for slot_id in stratum_entry["slot_ids"]:
            records.append(
                {
                    "slot_id": slot_id,
                    "stratum": stratum,
                    "assignment_status": "residual",
                    "commitment_sha256": None,
                    "reason_code": reason_code,
                    "owner_role": owner_role,
                    "next_action": ASSIGNMENT_NEXT_ACTION_BY_REASON[reason_code],
                }
            )
    records.sort(key=lambda record: record["slot_id"])
    return records


def validate_residual_status_uniform_across_strata(records: list[dict[str, Any]], strata: list[dict[str, Any]]) -> None:
    """Every stratum must show the identical assignment pattern -- zero
    assigned, every slot residual -- so no single stratum's shape (e.g. "the
    only stratum with zero assigned slots") can be used to single out the
    sealed held-out complement by elimination."""
    by_stratum: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_stratum.setdefault(record["stratum"], []).append(record)
    require(
        set(by_stratum) == {s["stratum"] for s in strata},
        "assignment records do not cover exactly the manifest's own strata -- refusing",
    )
    for stratum, stratum_records in by_stratum.items():
        assigned = sum(1 for r in stratum_records if r["assignment_status"] == "assigned")
        require(
            assigned == 0,
            f"stratum {stratum!r} has a nonzero assigned count -- refusing (no stratum may ever show a different assignment shape today)",
        )
        require(
            all(r["assignment_status"] == "residual" and r["commitment_sha256"] is None for r in stratum_records),
            f"stratum {stratum!r} carries a non-residual or commitment-bound record -- refusing",
        )


# --- shared engine wiring (real call, zero rows today) ------------------------


def run_engine_admission_check(rows: list[dict[str, Any]] = ()) -> dict[str, Any]:  # type: ignore[assignment]
    """A real (never stubbed) call into the shared, already-on-main
    ``v4_original_row_admission.admit_rows`` engine, bound to the V4
    controlling outcome. This module never admits a row -- ``rows`` stays
    empty and the engine's own counters both come back 0 -- proving this
    module's own wiring into the unmodified, fail-closed admission engine is
    live at the assignment layer too, never fabricating a row to exercise
    it."""
    return a7.admission.admit_rows(outcome_sha256=V4_SHA256, rows=list(rows))


# --- receipt assembly ---------------------------------------------------------


def build_receipt(root: Path = ROOT) -> dict[str, Any]:
    manifest = _load(SLOT_MANIFEST_PATH)
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)
    gate = check_assignment_gate(root)

    strata = a7.a6.frozen_slot_strata(manifest)
    frozen_slot_ids = a7.a6.all_frozen_slot_ids(manifest)

    assignment_records = derive_assignment_records(manifest, a2_receipt, gate)
    commitment_pool = build_commitment_pool(a4_receipt)

    a2_residuals_carried = [
        {
            "residual_id": entry["residual_id"],
            "origin_stage": "A2",
            "status": "unresolved_carried_to_public_slot_commitment_assignment",
        }
        for entry in a2_receipt["residuals"]
    ]
    a4_residuals_carried = [
        {
            "residual_id": entry["residual_id"],
            "origin_stage": "A4",
            "status": "unresolved_carried_to_public_slot_commitment_assignment",
        }
        for entry in a4_receipt["a4_residuals"]
    ]

    engine_admission_receipt = run_engine_admission_check([])
    assigned_count = sum(1 for r in assignment_records if r["assignment_status"] == "assigned")
    residual_count = len(assignment_records) - assigned_count

    return {
        "schema_version": "dataset_v4_public_slot_commitment_assignment_receipt_v1",
        "receipt_id": "dataset-v4-public-slot-commitment-assignment-v1",
        "status": "V4_PUBLIC_SLOT_COMMITMENT_ASSIGNMENT_ALL_SLOTS_RESIDUAL_TEXT_FREE_NO_STRATUM_COMMITMENT_LINK",
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
                "schema_version": "v4_public_slot_commitment_assignment_script_v1",
            },
        },
        "role_map": manifest["role_ownership"],
        "frozen_slot_denominator": {"total_slots": len(frozen_slot_ids), "strata": strata},
        "assignment_gate": gate,
        "commitment_binding_policy": dict(COMMITMENT_BINDING_POLICY),
        "commitment_pool": commitment_pool,
        "assignment_records": assignment_records,
        "a2_residuals_carried_forward": a2_residuals_carried,
        "a4_residuals_carried_forward": a4_residuals_carried,
        "engine_wiring": {
            "engine_schema_version": a7.admission.SCHEMA_VERSION,
            "engine_input_schema_version": a7.admission.INPUT_SCHEMA_VERSION,
            "model_only_bases_blocked": sorted(a7.admission.MODEL_ONLY_BASES),
            "admission_receipt": engine_admission_receipt,
        },
        "execution_counters": {
            "dataset_rows_emitted": engine_admission_receipt["counts"]["admitted_rows"],
            "frozen_slot_count": len(frozen_slot_ids),
            "assigned_slot_count": assigned_count,
            "residual_slot_count": residual_count,
            "builder_eligible_commitments_available": commitment_pool["total_builder_eligible_commitments"],
        },
        "eligibility": dict(ASSIGNMENT_ELIGIBILITY),
        "safety_assertions": {
            "rows_not_admitted": True,
            "text_emitted": False,
            "source_text_loaded_into_model": False,
            "corpus_refetched": False,
            "held_out_membership_referenced": False,
            "held_out_membership_opened": False,
            "private_builder_packet_opened": False,
            "a4_private_ledger_opened": False,
            "stratum_to_commitment_binding_published": False,
            "commitment_bound_to_a_slot": False,
            "gold_created": False,
            "training_ready_silver_claimed": False,
            "arena_slice_ready_claimed": False,
            "eval_artifact_ready_claimed": False,
            "mac_corpus_copy_created": False,
            "epic_done_claimed": False,
            "heldout_family_identity_leaked": False,
            "denominator_reduced_below_100": False,
            "residual_silently_dropped": False,
        },
    }


# --- receipt verification -----------------------------------------------------


def _load_schema() -> dict[str, Any]:
    schema = _load(ASSIGNMENT_SCHEMA_PATH)
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
    gate = check_assignment_gate(root)
    declared = receipt["assignment_gate"]
    require(
        declared == gate,
        "receipt assignment_gate does not match the state independently re-derived from the live public artifacts -- refusing (re-verify/regenerate required)",
    )
    require(
        declared["assignment_ready"] is False,
        "receipt assignment_gate claims assignment_ready -- refusing (never a valid claim today)",
    )
    require(
        declared["stratum_commitment_binding_available"] is False,
        "receipt assignment_gate claims stratum_commitment_binding_available -- refusing (structural, never true)",
    )


def validate_frozen_slot_denominator(receipt: dict[str, Any], root: Path) -> None:
    manifest = _load(SLOT_MANIFEST_PATH)
    expected_strata = a7.a6.frozen_slot_strata(manifest)
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


def validate_commitment_binding_policy(receipt: dict[str, Any]) -> None:
    require(
        receipt["commitment_binding_policy"] == COMMITMENT_BINDING_POLICY,
        "commitment_binding_policy does not equal the frozen policy contract -- refusing",
    )


def validate_commitment_pool_matches_a4(receipt: dict[str, Any], root: Path) -> None:
    a4_receipt = _load(A4_RECEIPT_PATH)
    expected = build_commitment_pool(a4_receipt)
    require(
        receipt["commitment_pool"] == expected,
        "commitment_pool does not reproduce from the live A4 receipt's own published commitments -- refusing",
    )
    published = set(a4_receipt["builder_packet_consumption"]["unit_commitments"])
    require(
        set(receipt["commitment_pool"]["commitments"]) <= published,
        "commitment_pool republishes a commitment A4 never published -- refusing",
    )


def validate_assignment_records(receipt: dict[str, Any], root: Path) -> None:
    manifest = _load(SLOT_MANIFEST_PATH)
    a2_receipt = _load(A2_RECEIPT_PATH)
    gate = check_assignment_gate(root)
    expected = derive_assignment_records(manifest, a2_receipt, gate)
    require(
        receipt["assignment_records"] == expected,
        "assignment_records does not reproduce from the live slot manifest, A2 receipt, and gate -- refusing",
    )
    slot_ids = {record["slot_id"] for record in receipt["assignment_records"]}
    require(
        len(receipt["assignment_records"]) == 100 and len(slot_ids) == 100,
        "assignment_records does not cover exactly the 100 frozen slots -- refusing",
    )
    require(
        slot_ids == set(a7.a6.all_frozen_slot_ids(manifest)),
        "assignment_records slot IDs do not match the frozen manifest's own slot IDs -- refusing",
    )
    validate_residual_status_uniform_across_strata(receipt["assignment_records"], a7.a6.frozen_slot_strata(manifest))


def validate_engine_wiring(receipt: dict[str, Any]) -> None:
    wiring = receipt["engine_wiring"]
    admission = a7.admission
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
        "engine_wiring.admission_receipt does not report zero rows -- refusing (dataset_rows_emitted must stay 0)",
    )


def validate_residuals_carried_forward(receipt: dict[str, Any]) -> None:
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)

    for stage, source_ids, carried in (
        ("A2", {e["residual_id"] for e in a2_receipt["residuals"]}, receipt["a2_residuals_carried_forward"]),
        ("A4", {e["residual_id"] for e in a4_receipt["a4_residuals"]}, receipt["a4_residuals_carried_forward"]),
    ):
        carried_ids = {entry["residual_id"] for entry in carried}
        require(
            carried_ids == source_ids,
            f"{stage.lower()}_residuals_carried_forward does not reproduce from {stage} -- refusing",
        )
        for entry in carried:
            require(
                entry["origin_stage"] == stage
                and entry["status"] == "unresolved_carried_to_public_slot_commitment_assignment",
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
    require(
        receipt["eligibility"] == ASSIGNMENT_ELIGIBILITY,
        "receipt eligibility does not equal the frozen all-false assignment eligibility -- refusing",
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
        receipt["execution_counters"]["frozen_slot_count"] == 100,
        "receipt execution_counters.frozen_slot_count is not 100 -- refusing",
    )
    require(
        receipt["execution_counters"]["assigned_slot_count"] == 0,
        "receipt execution_counters.assigned_slot_count is not 0 -- refusing",
    )
    require(
        receipt["execution_counters"]["residual_slot_count"] == 100,
        "receipt execution_counters.residual_slot_count is not 100 -- refusing",
    )


@validation_session
def validate_receipt_independently(receipt: dict[str, Any], root: Path = ROOT) -> None:
    from learn_ukrainian_v4_runtime.provenance import validate_receipt_bindings

    validate_receipt_bindings(receipt, root, validate_bindings_hash_to_disk, require)
    validate_gate_matches_receipt(receipt, root)
    validate_frozen_slot_denominator(receipt, root)
    validate_commitment_binding_policy(receipt)
    validate_commitment_pool_matches_a4(receipt, root)
    validate_assignment_records(receipt, root)
    validate_engine_wiring(receipt)
    validate_residuals_carried_forward(receipt)
    validate_no_forbidden_keys(receipt)
    validate_no_forbidden_completion_claims(receipt)
    validate_eligibility_and_safety(receipt)
    validate_receipt_schema(receipt)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--receipt",
        type=Path,
        default=ASSIGNMENT_RECEIPT_PATH,
        help="Assignment receipt JSON to verify (default: the tracked receipt).",
    )
    parser.add_argument(
        "--write-receipt", action="store_true", help="Assemble and persist a freshly computed receipt to --receipt."
    )
    args = parser.parse_args(argv)

    if args.write_receipt:
        receipt = build_receipt()
        validate_receipt_independently(receipt)
        args.receipt.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        print(canonical_json({"status": receipt["status"], "assignment_gate": receipt["assignment_gate"]}))
        return

    receipt = _load(args.receipt)
    validate_receipt_independently(receipt)
    print(canonical_json({"status": receipt["status"], "assignment_gate": receipt["assignment_gate"]}))


if __name__ == "__main__":
    try:
        main()
    except SlotAssignmentError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
