#!/usr/bin/env python3
"""V4 A6 safe arena: a label-blind, author-blind, hash-keyed packet plus a
no-self-vote / leave-one-out disagreement receipt, bound to the merged A5
evidence receipt and the frozen V4 pilot slot manifest.

A6 owns the *safe arena* role (``role_ownership.A6 == "safe_arena"`` in the
frozen slot manifest): a packet a model-agreement round could run against
without ever seeing which candidate proposed which label, and a strict,
text-free receipt of what happened. It never admits silver, never creates
gold, and never emits a dataset row -- ``dataset_rows_emitted`` stays 0.

This module never loads source text, never re-fetches corpus, and never
opens A4's private extraction ledger or A3's held-out membership file: its
only inputs are four already-public artifacts --

* A2's source operation admission receipt (rights/coverage residuals),
* A4's deterministic extraction receipt (only ``builder_packet_consumption
  .unit_commitments`` -- hash IDs, never a span),
* A5's evidence enrichment receipt (structural, expression-free evidence,
  itself already carrying A2's and A4's residuals forward), and
* the frozen 100-slot V4 pilot slot manifest (``slot_series`` -- public slot
  IDs only, never a real ``source_unit_id``).

Two independent parts:

1. ``check_arena_gate`` -- independently re-derives, from those four public
   artifacts alone, whether a real label-blind arena slice can run at all.
   Right now it cannot: every one of the manifest's eight strata still has
   ``assignment_state: "UNASSIGNED_PENDING_A2_A3"`` (no slot has a real
   source unit behind it yet) and A2 still carries eight unresolved
   rights/coverage residuals -- so no candidate model could receive a slot's
   text without transmitting a still-unresolved-rights source. Per the
   binding contract this module must *never* claim ``ARENA_SLICE_READY``
   while that is true; it reports ``arena_slice_ready: false`` and a typed
   ``blocked_reason_code`` instead.
2. ``build_receipt`` -- assembles the public receipt: the frozen 100-slot
   denominator (derived only from the manifest's own ``slot_series``, the
   same formula ``tests/test_open_model_dataset_v4_pilot_slots.py`` already
   locks), the label-blind packet's reproduction metadata (reusing, never
   duplicating, ``v4_arena_receipt``'s own frozen markers/schema/quarantine
   constant), the gate, every A2/A4/A5 residual carried forward unresolved,
   and one typed ``independence_unavailable`` A6 residual per frozen slot --
   never a duplicate or synthesized vote standing in for the missing
   independent view.

Run with no arguments to verify the checked-in A6 receipt reproduces from
the four public artifacts on disk -- no ``batch_state/`` required, so this
passes in a fresh checkout. Pass ``--write-receipt`` to (re)assemble and
persist it after a genuine change to one of those four artifacts or to the
arena engine itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

_SELF_ROOT = Path(__file__).resolve().parents[3]
if str(_SELF_ROOT) not in sys.path:
    sys.path.insert(0, str(_SELF_ROOT))

from scripts.projects.open_model_data import v4_a5_evidence_enrichment as evidence
from scripts.projects.open_model_data import v4_arena_receipt as arena

ROOT = _SELF_ROOT
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"

A6_RECEIPT_PATH = ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json"
A6_SCHEMA_PATH = CONTRACTS / "dataset_v4_a6_blind_arena_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_PATH = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
SLOT_MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"
ARENA_ENGINE_PATH = ROOT / "scripts/projects/open_model_data/v4_arena_receipt.py"
SELF_PATH = ROOT / "scripts/projects/open_model_data/v4_a6_blind_arena.py"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

# Mirrors v4_a5_evidence_enrichment.FORBIDDEN_KEYS/FORBIDDEN_SUBSTRINGS -- reused,
# never redefined, so the two builder-facing modules can never silently drift
# apart on what counts as a leak. The one deliberate exception: "gold" is not
# a leak here -- it is the *name* of this receipt's own always-false
# eligibility flag (matching v4_arena_receipt.build_receipts' own
# {"gold": False, ...} shape), never a real gold label or gold admission.
FORBIDDEN_KEYS = evidence.FORBIDDEN_KEYS - {"gold"}
FORBIDDEN_SUBSTRINGS = evidence.FORBIDDEN_SUBSTRINGS

ARENA_ELIGIBILITY = {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}


class ArenaWiringError(ValueError):
    """The A6 arena binding or its deterministic receipt is unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ArenaWiringError(message)


canonical_json = arena.canonical_json


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# --- frozen 100-slot denominator (public, manifest-only) --------------------


def slot_ids_for_series(series: dict[str, Any]) -> list[str]:
    return [f"{series['id_prefix']}-{number:03d}" for number in range(series["start"], series["start"] + series["count"])]


def frozen_slot_strata(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """One entry per manifest ``slot_series`` item, in manifest order --
    matches ``tests/test_open_model_dataset_v4_pilot_slots.py``'s own
    ``_slot_ids`` formula exactly, so the two can never silently diverge."""
    return [
        {
            "stratum": series["stratum"],
            "id_prefix": series["id_prefix"],
            "count": series["count"],
            "assignment_state": series["assignment_state"],
            "slot_ids": slot_ids_for_series(series),
        }
        for series in manifest["slot_series"]
    ]


def all_frozen_slot_ids(manifest: dict[str, Any]) -> list[str]:
    return [slot_id for stratum in frozen_slot_strata(manifest) for slot_id in stratum["slot_ids"]]


# --- arena gate (public-only) ------------------------------------------------


def check_arena_gate(root: Path = ROOT) -> dict[str, Any]:
    """Independently re-derive whether a real label-blind arena slice may run
    at all, from A2's residuals, the frozen slot manifest's own
    ``assignment_state`` per stratum, and A5's independent validity -- never
    trusting the A6 receipt's own declared fields, never opening
    ``batch_state/``. ``arena_slice_ready`` is only ever true once every
    frozen slot is assigned to a real source unit *and* A2 has zero
    unresolved residuals *and* A5 itself still independently validates.

    Fails closed -- a *closed gate*, not an exception -- if any of the three
    required public artifacts (slot manifest, A2 receipt, A5 receipt) is
    missing, mirroring ``v4_a5_evidence_enrichment.check_enrichment_gate``'s
    own missing-A4-receipt handling.
    """
    manifest_path = (root / "data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json").resolve()
    a2_path = (root / "data/projects/open_model_data/admission/dataset_v4_a2_source_operation_admission_receipt_v1.json").resolve()
    a5_path = (root / "data/projects/open_model_data/admission/dataset_v4_a5_evidence_enrichment_receipt_v1.json").resolve()
    required_paths = {"slot_manifest": manifest_path, "a2_receipt": a2_path, "a5_receipt": a5_path}
    for label, path in required_paths.items():
        require(root.resolve() in path.parents, f"{label} path escapes the repository root -- refusing")

    missing = sorted(label for label, path in required_paths.items() if not path.is_file())
    if missing:
        return {
            "gate_id": "v4-a6-arena-gate-v1",
            "a5_receipt_valid": False,
            "a2_rights_resolved": False,
            "all_slots_assigned": False,
            "arena_slice_ready": False,
            # The manifest itself may be one of the missing artifacts, so this
            # cannot be read dynamically here; it is the manifest's own frozen,
            # already-known ``sealed_heldout_commitment.assignment_owner``.
            "owner_role": "A2_A3_PRIVATE_ARTIFACT",
            "blocked_reason_code": f"required_public_artifact_missing:{missing[0]}",
        }

    manifest = _load(manifest_path)
    require(manifest.get("controlling_outcome_sha256") == V4_SHA256, "slot manifest is not bound to the expected V4 controlling outcome -- refusing")

    a2_receipt = _load(a2_path)
    require(a2_receipt.get("controlling_outcome_sha256") == V4_SHA256, "A2 receipt is not bound to the expected V4 controlling outcome -- refusing")
    rights_resolved = len(a2_receipt.get("residuals", [])) == 0

    all_assigned = all(series["assignment_state"] == "ASSIGNED" for series in manifest["slot_series"])

    a5_receipt = _load(a5_path)
    try:
        evidence.validate_receipt_independently(a5_receipt, root)
        a5_valid = True
    except evidence.EnrichmentError:
        a5_valid = False

    arena_slice_ready = rights_resolved and all_assigned and a5_valid
    blocked_reason_code = None
    if not arena_slice_ready:
        if not a5_valid:
            blocked_reason_code = "a5_receipt_invalid"
        elif not rights_resolved and not all_assigned:
            blocked_reason_code = "rights_unresolved_and_slots_unassigned"
        elif not rights_resolved:
            blocked_reason_code = "rights_unresolved"
        else:
            blocked_reason_code = "slot_assignment_pending_a2_a3"

    return {
        "gate_id": "v4-a6-arena-gate-v1",
        "a5_receipt_valid": a5_valid,
        "a2_rights_resolved": rights_resolved,
        "all_slots_assigned": all_assigned,
        "arena_slice_ready": arena_slice_ready,
        "owner_role": manifest["sealed_heldout_commitment"]["assignment_owner"],
        "blocked_reason_code": blocked_reason_code,
    }


# --- A6's own per-slot residuals (public, source-free) -----------------------

A6_RESIDUAL_REASON_INDEPENDENCE_UNAVAILABLE = "independence_unavailable"


def derive_a6_slot_residuals(manifest: dict[str, Any], gate: dict[str, Any]) -> list[dict[str, Any]]:
    """One typed residual per frozen public slot ID -- never a filled-in or
    duplicated vote standing in for the missing independent view. A pure
    function of the manifest's own ``slot_series`` plus the gate this module
    itself re-derives; never opens any private state."""
    owner_role = gate["owner_role"]
    residuals = []
    for slot_id in all_frozen_slot_ids(manifest):
        residuals.append(
            {
                "residual_id": f"a6-residual-independence-unavailable-{slot_id}",
                "subject_kind": "pilot_slot",
                "subject_id": slot_id,
                "stage": "A6",
                "reason_code": A6_RESIDUAL_REASON_INDEPENDENCE_UNAVAILABLE,
                "owner_role": owner_role,
                "next_action": (
                    "no independent peer view can run for this frozen slot without transmitting source text to "
                    "a model, which stays blocked until A2/A3 assign a real source unit to this slot and resolve "
                    "its stratum's rights/coverage residual -- never synthesize a vote in place of this gap"
                ),
                "retryability": "retryable",
                "evidence_refs": [
                    "admission.dataset_v4_pilot_slot_manifest_v1.slot_series",
                    "admission.dataset_v4_a2_source_operation_admission_receipt_v1.residuals",
                ],
            }
        )
    residuals.sort(key=lambda residual: residual["subject_id"])
    return residuals


# --- receipt assembly --------------------------------------------------------


def build_receipt(root: Path = ROOT) -> dict[str, Any]:
    manifest = _load(SLOT_MANIFEST_PATH)
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)
    a5_receipt = _load(A5_RECEIPT_PATH)
    gate = check_arena_gate(root)

    strata = frozen_slot_strata(manifest)
    frozen_slot_ids = all_frozen_slot_ids(manifest)

    a2_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A2", "status": "unresolved_carried_to_a6"}
        for entry in a2_receipt["residuals"]
    ]
    a4_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A4", "status": "unresolved_carried_to_a6"}
        for entry in a4_receipt["a4_residuals"]
    ]
    a5_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A5", "status": "unresolved_carried_to_a6"}
        for entry in a5_receipt["a5_residuals"]
    ]

    return {
        "schema_version": "dataset_v4_a6_blind_arena_receipt_v1",
        "receipt_id": "dataset-v4-a6-blind-arena-v1",
        "status": (
            "A6_BLIND_ARENA_PACKET_AND_PARSER_READY_SLICE_NOT_READY_TEXT_FREE_NO_SELF_VOTE"
            if not gate["arena_slice_ready"]
            else "ARENA_SLICE_READY"
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
            "pilot_slot_manifest": {
                "path": str(SLOT_MANIFEST_PATH.relative_to(root)),
                "sha256": sha256_file(SLOT_MANIFEST_PATH),
                "schema_version": "dataset_v4_pilot_slot_manifest_v1",
            },
            "arena_engine_implementation": {
                "path": str(ARENA_ENGINE_PATH.relative_to(root)),
                "sha256": sha256_file(ARENA_ENGINE_PATH),
                "schema_version": "v4_arena_receipt_script_v1",
            },
            "wiring_implementation": {
                "path": str(SELF_PATH.relative_to(root)),
                "sha256": sha256_file(SELF_PATH),
                "schema_version": "v4_a6_blind_arena_script_v1",
            },
        },
        "role_map": manifest["role_ownership"],
        "frozen_slot_denominator": {"total_slots": len(frozen_slot_ids), "strata": strata},
        "packet": {
            "label_blind": True,
            "author_blind": True,
            "proposal_schema_version": arena.PROPOSAL_SCHEMA_VERSION,
            "begin_marker": arena.BEGIN_MARKER,
            "end_marker": arena.END_MARKER,
            "canonical_json": "utf8-sort-keys-compact-newline-sha256",
            "self_vote_forbidden": True,
            "format_retry_policy": "one_format_only_retry_then_recorded_failure",
            "aggregation": "leave_one_out_ballots_only_never_self_report",
            "quarantine_disposition": arena.QUARANTINE,
        },
        "arena_gate": {
            "gate_id": gate["gate_id"],
            "requires": ["a5_receipt_independently_valid", "a2_rights_fully_resolved", "all_frozen_slots_assigned"],
            "a5_receipt_valid": gate["a5_receipt_valid"],
            "a2_rights_resolved": gate["a2_rights_resolved"],
            "all_slots_assigned": gate["all_slots_assigned"],
            "arena_slice_ready": gate["arena_slice_ready"],
            "owner_role": gate["owner_role"],
            "blocked_reason_code": gate["blocked_reason_code"],
        },
        "a2_residuals_carried_forward": a2_residuals_carried,
        "a4_residuals_carried_forward": a4_residuals_carried,
        "a5_residuals_carried_forward": a5_residuals_carried,
        "a6_residuals": derive_a6_slot_residuals(manifest, gate),
        "execution_counters": {
            "dataset_rows_emitted": 0,
            "live_proposals_run": 0,
            "candidates_voted": 0,
            "frozen_slot_count": len(frozen_slot_ids),
            "slots_arena_ready": len(frozen_slot_ids) if gate["arena_slice_ready"] else 0,
            "slots_independence_unavailable": 0 if gate["arena_slice_ready"] else len(frozen_slot_ids),
        },
        "eligibility": dict(ARENA_ELIGIBILITY),
        "safety_assertions": {
            "rows_not_admitted": True,
            "text_emitted": False,
            "source_text_transmitted_to_model": False,
            "live_model_inference_over_corpus": False,
            "held_out_membership_referenced": False,
            "self_vote_permitted": False,
            "silver_admitted_by_arena": False,
            "gold_created_by_arena": False,
            "mac_corpus_copy_created": False,
            "epic_done_claimed": False,
            "heldout_family_identity_leaked": False,
        },
    }


# --- receipt verification ---------------------------------------------------


def _load_schema() -> dict[str, Any]:
    schema = _load(A6_SCHEMA_PATH)
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
    gate = check_arena_gate(root)
    declared = receipt["arena_gate"]
    require(
        declared["a5_receipt_valid"] == gate["a5_receipt_valid"]
        and declared["a2_rights_resolved"] == gate["a2_rights_resolved"]
        and declared["all_slots_assigned"] == gate["all_slots_assigned"]
        and declared["arena_slice_ready"] == gate["arena_slice_ready"]
        and declared["blocked_reason_code"] == gate["blocked_reason_code"],
        "receipt arena_gate does not match the state independently re-derived from the live public artifacts "
        "-- refusing (re-verify/regenerate required)",
    )
    require(
        gate["arena_slice_ready"] or receipt["status"] != "ARENA_SLICE_READY",
        "receipt claims ARENA_SLICE_READY while the independently re-derived gate is closed -- refusing",
    )


def validate_frozen_slot_denominator(receipt: dict[str, Any], root: Path) -> None:
    manifest = _load(SLOT_MANIFEST_PATH)
    expected_strata = frozen_slot_strata(manifest)
    declared = receipt["frozen_slot_denominator"]
    require(declared["strata"] == expected_strata, "frozen_slot_denominator.strata does not reproduce from the live slot manifest -- refusing")
    all_ids = [slot_id for stratum in expected_strata for slot_id in stratum["slot_ids"]]
    require(len(all_ids) == 100 and len(set(all_ids)) == 100, "frozen slot denominator did not expand to exactly 100 unique slot IDs -- refusing")
    require(declared["total_slots"] == 100, "frozen_slot_denominator.total_slots is not 100 -- refusing")


def validate_packet_matches_engine(receipt: dict[str, Any]) -> None:
    packet = receipt["packet"]
    require(
        packet["proposal_schema_version"] == arena.PROPOSAL_SCHEMA_VERSION
        and packet["begin_marker"] == arena.BEGIN_MARKER
        and packet["end_marker"] == arena.END_MARKER
        and packet["quarantine_disposition"] == arena.QUARANTINE,
        "receipt packet does not match the live arena engine's own frozen markers/schema/quarantine constant "
        "-- refusing (engine changed without regenerating this receipt)",
    )


def validate_residuals_carried_from_a2_a4_a5(receipt: dict[str, Any], root: Path) -> None:
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)
    a5_receipt = _load(A5_RECEIPT_PATH)
    manifest = _load(SLOT_MANIFEST_PATH)
    gate = check_arena_gate(root)

    for stage, source_ids, carried in (
        ("A2", {e["residual_id"] for e in a2_receipt["residuals"]}, receipt["a2_residuals_carried_forward"]),
        ("A4", {e["residual_id"] for e in a4_receipt["a4_residuals"]}, receipt["a4_residuals_carried_forward"]),
        ("A5", {e["residual_id"] for e in a5_receipt["a5_residuals"]}, receipt["a5_residuals_carried_forward"]),
    ):
        carried_ids = {entry["residual_id"] for entry in carried}
        require(carried_ids == source_ids, f"{stage.lower()}_residuals_carried_forward does not reproduce from {stage} -- refusing")
        for entry in carried:
            require(
                entry["origin_stage"] == stage and entry["status"] == "unresolved_carried_to_a6",
                f"{stage.lower()}_residuals_carried_forward entry has an unexpected origin_stage/status -- refusing",
            )

    expected_a6_residuals = derive_a6_slot_residuals(manifest, gate)
    require(receipt["a6_residuals"] == expected_a6_residuals, "a6_residuals does not reproduce from the live slot manifest and gate -- refusing")


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


def validate_eligibility_and_safety_all_false(receipt: dict[str, Any]) -> None:
    require(receipt["eligibility"] == ARENA_ELIGIBILITY, "receipt eligibility does not equal the frozen all-false arena eligibility -- refusing")
    safety = receipt["safety_assertions"]
    require(
        safety["rows_not_admitted"] is True and all(value is False for key, value in safety.items() if key != "rows_not_admitted"),
        "receipt safety_assertions does not hold the expected invariants -- refusing",
    )
    require(receipt["execution_counters"]["dataset_rows_emitted"] == 0, "receipt execution_counters.dataset_rows_emitted is not 0 -- refusing (arena is not silver admission)")


def validate_receipt_independently(receipt: dict[str, Any], root: Path = ROOT) -> None:
    validate_bindings_hash_to_disk(receipt, root)
    validate_gate_matches_receipt(receipt, root)
    validate_frozen_slot_denominator(receipt, root)
    validate_packet_matches_engine(receipt)
    validate_residuals_carried_from_a2_a4_a5(receipt, root)
    validate_no_forbidden_keys(receipt)
    validate_eligibility_and_safety_all_false(receipt)
    validate_receipt_schema(receipt)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--receipt", type=Path, default=A6_RECEIPT_PATH, help="A6 receipt JSON to verify (default: the tracked V4 A6 blind arena receipt).")
    parser.add_argument("--write-receipt", action="store_true", help="Assemble and persist a freshly computed receipt to --receipt.")
    args = parser.parse_args(argv)

    if args.write_receipt:
        receipt = build_receipt()
        validate_receipt_independently(receipt)
        args.receipt.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        print(canonical_json({"status": receipt["status"], "arena_gate": receipt["arena_gate"]}))
        return

    receipt = _load(args.receipt)
    validate_receipt_independently(receipt)
    print(canonical_json({"status": receipt["status"], "arena_gate": receipt["arena_gate"]}))


if __name__ == "__main__":
    try:
        main()
    except ArenaWiringError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
