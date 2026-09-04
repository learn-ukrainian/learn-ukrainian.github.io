#!/usr/bin/env python3
"""V4 per-slot private factory: the private-side companion to A7's factory
gate, bound to the merged A7 original-row factory receipt and the frozen V4
pilot slot manifest.

This is **not** a new A-stage number and **not** a new public identity
scheme (see the frozen manifest's own ``role_ownership`` -- A7 already owns
``original_row_factory``). It exists because #7423/#7430's binding contract
draws a hard line this repo's other V4 public modules (A7-A12, and the
public-slot -> A4-commitment assignment module in PR #7646) all respect on
purpose: a *public*, git-committed artifact must never carry a slot ->
source-unit or slot -> commitment binding, because publishing one would let
a reader narrow the sealed held-out complement by elimination. That
restriction is about *publication*, not about whether private, never-
committed operational state may exist at all -- and V4's own rights model
(``rights_policy.operation_specific`` in the frozen manifest) says an
unknown/denied *operation* (transmission, training, publication) blocks only
that operation, never the ability to track per-slot readiness safely.

This module is the one place that per-slot readiness bookkeeping is
persisted -- privately, under ``batch_state/open-model-data/`` (0700
directory, 0600 files, `.gitignore`d, never committed) -- while the public
receipt this module also writes to ``data/projects/open_model_data/
admission/`` stays text-free and carries counts and reason-code totals only,
never a slot-keyed table of any kind.

This module never loads source text, never re-fetches corpus, and never
opens A3's held-out membership file or A4's private extraction ledger: its
only inputs are three already-public artifacts --

* A2's source operation admission receipt (``stratum_coverage_map`` and
  ``residuals`` -- rights/coverage state, never source text),
* A7's original-row factory receipt (its own already-public ``a7_residuals``
  reason codes, its own typed, positive ``a7_completions``, and its own
  independent validity), and
* the frozen 100-slot V4 pilot slot manifest (``slot_series`` -- public slot
  IDs only, never a real ``source_unit_id``).

**Prerequisite eligibility is not stage completion** (PR #7654 repair cycle
2, Option A -- ``batch_state/tasks/design-7654-partial-stage-evidence.
result``): this module's own counters keep those two names visibly distinct,
matching every other V4 stage module. Three independent parts:

1. ``check_per_slot_gate`` -- reuses (never duplicates) the shared
   ``v4_stage_evidence`` eligibility/completion model to independently
   re-derive, per frozen slot, whether that slot's own stratum is
   prerequisite-eligible (A2 rights resolved and manifest-assigned) *and*
   whether A7's own typed ``a7_completions`` names it -- never trusting A7's
   own declared fields, never opening ``batch_state/``. Right now zero slots
   satisfy either: every one of the manifest's eight strata is still
   ``UNASSIGNED_PENDING_A2_A3`` and A7's own ``a7_completions`` is empty
   (A7 has no execution mechanism yet), so ``slots_prerequisite_eligible``
   is 0 and ``slots_stage_complete`` is 0 -- matching the public slot-
   commitment assignment receipt's own "0 assigned / 100 residual" count.
2. ``build_private_ledger`` -- the private, per-slot working ledger this
   pass would populate with real candidate rows once slots go complete.
   Today it carries the same per-stratum eligibility signal already public
   via this module's own receipt (nothing secret) and an empty
   ``candidate_rows`` list -- *never* a fabricated row standing in for the
   independent authorship this module cannot perform automatically, and
   never a slot -> source-unit or slot -> commitment binding (this module
   never opens A4's private ledger, so it never *has* one to publish or to
   leak).
3. ``build_receipt`` -- assembles the public, text-free receipt: the frozen
   100-slot denominator, the per-stratum eligibility table, the gate's
   aggregate counts (never a per-slot table), a reason-code total reused
   unchanged from A7's own public ``a7_residuals`` (never a fourth,
   independently invented reason), and ``private_rows_constructed`` --
   always 0 today, because independent authorship has no automated source
   and no stage has an execution mechanism yet regardless.

Run with no arguments to verify the checked-in receipt reproduces from the
three public artifacts on disk -- no ``batch_state/`` required, so this
passes in a fresh checkout. Pass ``--write-receipt`` to (re)assemble and
persist the public receipt *and* refresh the private ledger under
``batch_state/open-model-data/`` (0700/0600, never committed).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

_SELF_ROOT = Path(__file__).resolve().parents[3]
if str(_SELF_ROOT) not in sys.path:
    sys.path.insert(0, str(_SELF_ROOT))

from scripts.projects.open_model_data import v4_a7_original_row_factory as a7
from scripts.projects.open_model_data import v4_stage_evidence as ev

ROOT = _SELF_ROOT
ADMISSION_RELATIVE = "data/projects/open_model_data/admission"
CONTRACTS_RELATIVE = "data/projects/open_model_data/contracts"
BATCH_STATE_DIR = ROOT / "batch_state/open-model-data"
PRIVATE_LEDGER_PATH = BATCH_STATE_DIR / "v4_private_per_slot_factory_ledger_v1.json"

RECEIPT_RELATIVE = f"{ADMISSION_RELATIVE}/dataset_v4_per_slot_private_factory_receipt_v1.json"
SCHEMA_RELATIVE = f"{CONTRACTS_RELATIVE}/dataset_v4_per_slot_private_factory_receipt_v1.schema.json"
A2_RECEIPT_RELATIVE = f"{ADMISSION_RELATIVE}/dataset_v4_a2_source_operation_admission_receipt_v1.json"
A7_RECEIPT_RELATIVE = f"{ADMISSION_RELATIVE}/dataset_v4_a7_original_row_factory_receipt_v1.json"
SLOT_MANIFEST_RELATIVE = f"{ADMISSION_RELATIVE}/dataset_v4_pilot_slot_manifest_v1.json"
SELF_RELATIVE = "scripts/projects/open_model_data/v4_per_slot_private_factory.py"

RECEIPT_PATH = ROOT / RECEIPT_RELATIVE
SCHEMA_PATH = ROOT / SCHEMA_RELATIVE

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

# Mirrors v4_a7_original_row_factory.FORBIDDEN_KEYS/FORBIDDEN_SUBSTRINGS exactly
# -- reused, never redefined, so every builder-facing V4 module stays aligned
# on what counts as a leak. "gold" stays excluded because it is the name of
# this receipt's own always-false eligibility flag, never a real gold label.
FORBIDDEN_KEYS = a7.FORBIDDEN_KEYS
FORBIDDEN_SUBSTRINGS = a7.FORBIDDEN_SUBSTRINGS
FORBIDDEN_COMPLETION_CLAIMS = a7.FORBIDDEN_COMPLETION_CLAIMS

# A slot-keyed HMAC/commitment column is never public -- see PR #7646's own
# COMMITMENT_BINDING_POLICY. This module never computes one at all (it never
# opens A4's private ledger), but this substring check catches drift if a
# future edit ever tries to add one.
FORBIDDEN_PUBLIC_HMAC_KEYS = {"commitment_sha256", "commitment_hmac", "slot_commitment", "source_unit_id"}

ELIGIBILITY = {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}

canonical_json = a7.canonical_json
sha256_file = a7.sha256_file
frozen_slot_strata = a7.frozen_slot_strata
all_frozen_slot_ids = a7.all_frozen_slot_ids


class PrivateFactoryError(ValueError):
    """The private per-slot factory wiring or its public receipt is unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PrivateFactoryError(message)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# --- per-slot gate (public-only, reuses the shared eligibility model) -------


def check_per_slot_gate(root: Path = ROOT) -> dict[str, Any]:
    """Independently re-derive per-stratum eligibility from A2's and the
    manifest's own public state, and A7's own already-public
    ``a7_completions``, reusing (never duplicating)
    ``v4_stage_evidence.stratum_eligibility`` -- never trusting A7's own
    declared fields, never opening ``batch_state/``. Also independently
    re-validates the A7 receipt itself (structural validity only); a slot
    can never be counted complete if the upstream A7 receipt does not
    independently validate.

    Fails closed -- a *closed gate*, not an exception -- if any of the three
    required public artifacts (slot manifest, A2 receipt, A7 receipt) is
    missing. Every path is derived from ``root``."""
    manifest_path = (root / SLOT_MANIFEST_RELATIVE).resolve()
    a2_path = (root / A2_RECEIPT_RELATIVE).resolve()
    a7_path = (root / A7_RECEIPT_RELATIVE).resolve()
    required_paths = {"slot_manifest": manifest_path, "a2_receipt": a2_path, "a7_receipt": a7_path}
    for label, path in required_paths.items():
        require(root.resolve() in path.parents, f"{label} path escapes the repository root -- refusing")

    missing = sorted(label for label, path in required_paths.items() if not path.is_file())
    if missing:
        return {
            "gate_id": "v4-per-slot-private-factory-gate-v1",
            "a7_receipt_valid": False,
            "slots_prerequisite_eligible": 0,
            "slots_stage_complete": 0,
            "slots_residual": 100,
            "owner_role": "A2_A3_PRIVATE_ARTIFACT",
            "blocked_reason_code": f"required_public_artifact_missing:{missing[0]}",
        }

    manifest = _load(manifest_path)
    require(manifest.get("controlling_outcome_sha256") == V4_SHA256, "slot manifest is not bound to the expected V4 controlling outcome -- refusing")

    a2_receipt = _load(a2_path)
    require(a2_receipt.get("controlling_outcome_sha256") == V4_SHA256, "A2 receipt is not bound to the expected V4 controlling outcome -- refusing")

    a7_receipt = _load(a7_path)
    try:
        a7.validate_receipt_independently(a7_receipt, root)
        a7_valid = True
    except a7.OriginalRowFactoryError:
        a7_valid = False

    eligibility = ev.stratum_eligibility(manifest, a2_receipt, error_cls=PrivateFactoryError)
    eligible_ids = ev.eligible_slot_ids(eligibility)
    total_ids = set(all_frozen_slot_ids(manifest))
    a7_completion_ids = (
        ev.completion_slot_ids(a7_receipt.get("a7_completions", []), stage="A7", total_slot_ids=total_ids, error_cls=PrivateFactoryError) if a7_valid else set()
    )
    ev.validate_subset(a7_completion_ids, eligible_ids, label="A7 completions vs prerequisite-eligible slots", error_cls=PrivateFactoryError)

    slots_prerequisite_eligible = len(eligible_ids)
    slots_stage_complete = len(a7_completion_ids)
    slots_residual = 100 - slots_stage_complete

    blocked_reason_code = ev.gate_blocked_reason_code(
        upstream_valid=a7_valid,
        slots_prerequisite_eligible=slots_prerequisite_eligible,
        has_upstream_stage=True,
        slots_upstream_complete=slots_stage_complete,  # this module mirrors A7's own completion, never a stage of its own
        slots_stage_complete=slots_stage_complete,
        total=100,
    )

    return {
        "gate_id": "v4-per-slot-private-factory-gate-v1",
        "a7_receipt_valid": a7_valid,
        "slots_prerequisite_eligible": slots_prerequisite_eligible,
        "slots_stage_complete": slots_stage_complete,
        "slots_residual": slots_residual,
        "owner_role": manifest["sealed_heldout_commitment"]["assignment_owner"],
        "blocked_reason_code": blocked_reason_code,
    }


# --- reason-code totals (public, reused unchanged from A7) ------------------


def reason_code_totals(a7_receipt: dict[str, Any]) -> dict[str, int]:
    """Aggregate counts only -- never a per-slot table. Reuses A7's own
    already-public per-slot reason codes unchanged; never invents a fourth."""
    totals = dict.fromkeys(ev.RESIDUAL_REASON_CODES, 0)
    for residual in a7_receipt["a7_residuals"]:
        totals[residual["reason_code"]] += 1
    return totals


# --- private ledger (never committed, 0700/0600 under batch_state/) --------


def build_private_ledger(root: Path = ROOT) -> dict[str, Any]:
    """The private, never-committed, per-slot working ledger this pass would
    populate with real candidate rows once a slot's own stratum resolves and
    A7 produces real completion evidence for it. Every field here is already
    independently reproducible from public artifacts alone (A2's residuals,
    the manifest's own assignment state, and A7's own already-public
    ``a7_completions``) -- nothing secret lives here today. It is private
    only because ``batch_state/`` is this repo's private operational-state
    home (never committed), not because today's zero-row content needs
    confidentiality. ``candidate_rows`` stays empty: independent authorship
    has no automated source, and no stage has an execution mechanism yet
    regardless."""
    manifest = _load(root / SLOT_MANIFEST_RELATIVE)
    a2_receipt = _load(root / A2_RECEIPT_RELATIVE)
    eligibility = ev.stratum_eligibility(manifest, a2_receipt, error_cls=PrivateFactoryError)
    return {
        "ledger_id": "v4-private-per-slot-factory-ledger-v1",
        "controlling_outcome_sha256": V4_SHA256,
        "stratum_eligibility": ev.public_eligibility(eligibility),
        "candidate_rows": [],
    }


def write_private_ledger(ledger: dict[str, Any], path: Path = PRIVATE_LEDGER_PATH) -> None:
    """Writes the private ledger with 0700 directory / 0600 file
    permissions, atomically (write-then-rename), and never under a path
    that would be tracked by git (see ``.gitignore``'s ``batch_state/*``)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    tmp_path = path.with_name(path.name + ".tmp")
    tmp_path.write_text(json.dumps(ledger, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.chmod(tmp_path, 0o600)
    tmp_path.replace(path)
    os.chmod(path, 0o600)


# --- receipt assembly --------------------------------------------------------


def build_receipt(root: Path = ROOT) -> dict[str, Any]:
    manifest = _load(root / SLOT_MANIFEST_RELATIVE)
    a2_receipt = _load(root / A2_RECEIPT_RELATIVE)
    a7_receipt = _load(root / A7_RECEIPT_RELATIVE)
    gate = check_per_slot_gate(root)

    strata = frozen_slot_strata(manifest)
    frozen_slot_ids = all_frozen_slot_ids(manifest)
    eligibility = ev.stratum_eligibility(manifest, a2_receipt, error_cls=PrivateFactoryError)

    private_ledger = build_private_ledger(root)
    private_rows_constructed = len(private_ledger["candidate_rows"])

    a2_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A2", "status": "unresolved_carried_to_private_factory"}
        for entry in a2_receipt["residuals"]
    ]
    a7_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A7", "status": "unresolved_carried_to_private_factory"}
        for entry in a7_receipt["a7_residuals"]
    ]

    return {
        "schema_version": "dataset_v4_per_slot_private_factory_receipt_v1",
        "receipt_id": "dataset-v4-per-slot-private-factory-v1",
        "status": "V4_PER_SLOT_PRIVATE_FACTORY_WIRED_TEXT_FREE_ZERO_PRIVATE_ROWS_NO_SLOT_HMAC_TABLE",
        "text_free": True,
        "controlling_outcome_sha256": V4_SHA256,
        "control_surfaces": {"public_control_issue": 7423, "pilot_child_issue": 7430, "private_operational_board": 622},
        "bindings": {
            "a2_source_operation_admission": {
                "path": A2_RECEIPT_RELATIVE,
                "sha256": sha256_file(root / A2_RECEIPT_RELATIVE),
                "schema_version": "dataset_v4_a2_source_operation_admission_receipt_v1",
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
            "wiring_implementation": {
                "path": SELF_RELATIVE,
                "sha256": sha256_file(root / SELF_RELATIVE),
                "schema_version": "v4_per_slot_private_factory_script_v1",
            },
        },
        "role_map": manifest["role_ownership"],
        "frozen_slot_denominator": {"total_slots": len(frozen_slot_ids), "strata": strata},
        "prerequisite_eligibility": ev.public_eligibility(eligibility),
        "per_slot_gate": gate,
        "reason_code_totals": reason_code_totals(a7_receipt),
        "a2_residuals_carried_forward": a2_residuals_carried,
        "a7_residuals_carried_forward": a7_residuals_carried,
        "execution_counters": {
            "dataset_rows_emitted": 0,
            "private_rows_constructed": private_rows_constructed,
            "slots_prerequisite_eligible": gate["slots_prerequisite_eligible"],
            "slots_stage_complete": gate["slots_stage_complete"],
            "slots_residual": gate["slots_residual"],
            "frozen_slot_count": len(frozen_slot_ids),
        },
        "eligibility": dict(ELIGIBILITY),
        "safety_assertions": {
            "rows_not_admitted": True,
            "text_emitted": False,
            "source_text_loaded_into_model": False,
            "corpus_refetched": False,
            "held_out_membership_referenced": False,
            "a4_private_ledger_opened": False,
            "slot_to_source_unit_table_published": False,
            "slot_to_commitment_table_published": False,
            "gold_created": False,
            "training_ready_silver_claimed": False,
            "arena_slice_ready_claimed": False,
            "mac_corpus_copy_created": False,
            "epic_done_claimed": False,
            "heldout_family_identity_leaked": False,
        },
    }


# --- receipt verification ---------------------------------------------------


def _load_schema(root: Path) -> dict[str, Any]:
    schema = _load(root / SCHEMA_RELATIVE)
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
    gate = check_per_slot_gate(root)
    require(receipt["per_slot_gate"] == gate, "receipt per_slot_gate does not match the state independently re-derived from the live public artifacts -- refusing (re-verify/regenerate required)")


def validate_frozen_slot_denominator(receipt: dict[str, Any], root: Path) -> None:
    manifest = _load(root / SLOT_MANIFEST_RELATIVE)
    expected_strata = frozen_slot_strata(manifest)
    declared = receipt["frozen_slot_denominator"]
    require(declared["strata"] == expected_strata, "frozen_slot_denominator.strata does not reproduce from the live slot manifest -- refusing")
    all_ids = [slot_id for stratum in expected_strata for slot_id in stratum["slot_ids"]]
    require(len(all_ids) == 100 and len(set(all_ids)) == 100, "frozen slot denominator did not expand to exactly 100 unique slot IDs -- refusing")
    require(declared["total_slots"] == 100, "frozen_slot_denominator.total_slots is not 100 -- refusing")


def validate_eligibility_field(receipt: dict[str, Any], root: Path) -> None:
    manifest = _load(root / SLOT_MANIFEST_RELATIVE)
    a2_receipt = _load(root / A2_RECEIPT_RELATIVE)
    expected = ev.public_eligibility(ev.stratum_eligibility(manifest, a2_receipt, error_cls=PrivateFactoryError))
    require(receipt["prerequisite_eligibility"] == expected, "prerequisite_eligibility does not reproduce from the live A2 receipt and slot manifest -- refusing")


def validate_reason_code_totals(receipt: dict[str, Any], root: Path) -> None:
    a7_receipt = _load(root / A7_RECEIPT_RELATIVE)
    expected = reason_code_totals(a7_receipt)
    require(receipt["reason_code_totals"] == expected, "reason_code_totals does not reproduce from A7's own public a7_residuals -- refusing")
    require(sum(expected.values()) == 100, "reason_code_totals does not sum to the frozen 100-slot denominator -- refusing")


def validate_private_rows_constructed(receipt: dict[str, Any], root: Path) -> None:
    ledger = build_private_ledger(root)
    require(
        receipt["execution_counters"]["private_rows_constructed"] == len(ledger["candidate_rows"]),
        "execution_counters.private_rows_constructed does not reproduce from the live (in-memory) private ledger -- refusing",
    )
    require(receipt["execution_counters"]["private_rows_constructed"] == 0, "execution_counters.private_rows_constructed is not 0 -- refusing (no independently authored candidate row exists yet)")
    require(receipt["execution_counters"]["dataset_rows_emitted"] == 0, "execution_counters.dataset_rows_emitted is not 0 -- refusing")


def validate_residuals_carried_from_a2_a7(receipt: dict[str, Any], root: Path) -> None:
    a2_receipt = _load(root / A2_RECEIPT_RELATIVE)
    a7_receipt = _load(root / A7_RECEIPT_RELATIVE)
    for stage, source_ids, carried in (
        ("A2", {e["residual_id"] for e in a2_receipt["residuals"]}, receipt["a2_residuals_carried_forward"]),
        ("A7", {e["residual_id"] for e in a7_receipt["a7_residuals"]}, receipt["a7_residuals_carried_forward"]),
    ):
        carried_ids = {entry["residual_id"] for entry in carried}
        require(carried_ids == source_ids, f"{stage.lower()}_residuals_carried_forward does not reproduce from {stage} -- refusing")
        for entry in carried:
            require(
                entry["origin_stage"] == stage and entry["status"] == "unresolved_carried_to_private_factory",
                f"{stage.lower()}_residuals_carried_forward entry has an unexpected origin_stage/status -- refusing",
            )


def validate_no_forbidden_keys(receipt: dict[str, Any]) -> None:
    def _all_keys(value: Any) -> set[str]:
        if isinstance(value, dict):
            return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
        if isinstance(value, list):
            return set().union(*(_all_keys(item) for item in value), set())
        return set()

    keys = _all_keys(receipt)
    leaked = keys & FORBIDDEN_KEYS
    require(not leaked, f"receipt carries forbidden key(s): {sorted(leaked)} -- refusing")
    leaked_hmac_keys = keys & FORBIDDEN_PUBLIC_HMAC_KEYS
    require(not leaked_hmac_keys, f"receipt carries a forbidden slot->HMAC/source-unit key: {sorted(leaked_hmac_keys)} -- refusing")

    serialized = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
    leaked_substrings = [needle for needle in FORBIDDEN_SUBSTRINGS if needle in serialized]
    require(not leaked_substrings, f"receipt carries forbidden substring(s): {leaked_substrings} -- refusing")


def validate_no_forbidden_completion_claims(receipt: dict[str, Any]) -> None:
    serialized = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
    leaked = [claim for claim in FORBIDDEN_COMPLETION_CLAIMS if claim in serialized]
    require(not leaked, f"receipt carries forbidden completion claim(s): {leaked} -- refusing")


def validate_eligibility_and_safety_all_false(receipt: dict[str, Any]) -> None:
    require(receipt["eligibility"] == ELIGIBILITY, "receipt eligibility does not equal the frozen all-false eligibility -- refusing")
    safety = receipt["safety_assertions"]
    require(
        safety["rows_not_admitted"] is True and all(value is False for key, value in safety.items() if key != "rows_not_admitted"),
        "receipt safety_assertions does not hold the expected invariants -- refusing",
    )


def validate_receipt_independently(receipt: dict[str, Any], root: Path = ROOT) -> None:
    validate_bindings_hash_to_disk(receipt, root)
    validate_gate_matches_receipt(receipt, root)
    validate_frozen_slot_denominator(receipt, root)
    validate_eligibility_field(receipt, root)
    validate_reason_code_totals(receipt, root)
    validate_private_rows_constructed(receipt, root)
    validate_residuals_carried_from_a2_a7(receipt, root)
    validate_no_forbidden_keys(receipt)
    validate_no_forbidden_completion_claims(receipt)
    validate_eligibility_and_safety_all_false(receipt)
    validate_receipt_schema(receipt, root)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--receipt", type=Path, default=RECEIPT_PATH, help="Public receipt JSON to verify (default: the tracked V4 per-slot private factory receipt).")
    parser.add_argument("--write-receipt", action="store_true", help="Assemble and persist a freshly computed public receipt, and refresh the private ledger under batch_state/ (0700/0600, never committed).")
    args = parser.parse_args(argv)

    if args.write_receipt:
        receipt = build_receipt()
        validate_receipt_independently(receipt)
        args.receipt.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        write_private_ledger(build_private_ledger())
        print(canonical_json({"status": receipt["status"], "per_slot_gate": receipt["per_slot_gate"], "execution_counters": receipt["execution_counters"]}))
        return

    receipt = _load(args.receipt)
    validate_receipt_independently(receipt)
    print(canonical_json({"status": receipt["status"], "per_slot_gate": receipt["per_slot_gate"], "execution_counters": receipt["execution_counters"]}))


if __name__ == "__main__":
    try:
        main()
    except PrivateFactoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
