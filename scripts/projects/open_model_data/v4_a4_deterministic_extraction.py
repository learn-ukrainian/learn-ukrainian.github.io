#!/usr/bin/env python3
"""V4 A4 deterministic extraction: frozen algorithm, builder-packet-gated.

A4 is the builder-facing role that turns builder-eligible source units into
immutable, byte-stable, text-free extraction records (span identity +
input/output hashes, never the span text itself). It must never see which
source-family the A3 held-out firewall assigned to the held-out pool -- see
``dataset_v4_a3_heldout_source_family_seal_receipt_v1.json``'s
``access_firewall``, where ``A4_deterministic_extraction`` is locked to
``heldout_family_pool_visible: false`` and forbidden from every held-out
field. This module never opens ``batch_state/open-model-data/v4-a3-heldout/``
(the private membership artifact A3_heldout owns) -- doing so from a
builder-facing role would itself be the leak this firewall exists to
prevent, independent of whether the file happens to be readable.

The only channel by which A4 may learn *which* source units are
builder-eligible is a **builder packet**: a distinct, A3_heldout-authored,
schema-bound public artifact that names the builder-eligible complement and
never the held-out id. A3's own sealed receipt records
``temporal_firewall.builder_packet_issued`` and
``execution_counters.builder_packets_issued`` for exactly this reason. As of
this script, both are ``false``/``0`` -- no builder packet has been issued.

This module therefore has two independent halves:

1. ``EXTRACTION_ALGORITHM_DESCRIPTOR`` -- the frozen, hashed, reproducible
   span-extraction formula A4 will run once a builder packet exists. Frozen
   the same way A3 froze its assignment formula: any edit changes
   ``EXTRACTION_ALGORITHM_DESCRIPTOR_SHA256``, which is pinned as a schema
   ``const`` in the receipt schema, so a different implementation cannot
   silently swap the formula while still validating.
2. ``check_builder_packet_gate`` -- independently re-derives the current
   block state from the bound A3 receipt on disk (never trusting the A4
   receipt's own declared fields) and refuses to proceed with extraction
   while the gate is closed.

Run with no arguments to verify the checked-in A4 receipt reproduces both
halves and is consistent with the bound A2/A3 receipts on disk.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"

A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A4_SCHEMA_PATH = CONTRACTS / "dataset_v4_a4_deterministic_extraction_receipt_v1.schema.json"
A3_RECEIPT_PATH = ADMISSION / "dataset_v4_a3_heldout_source_family_seal_receipt_v1.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

# Fields no builder-facing artifact -- including this one -- may ever carry.
# Mirrors the A3 seal's own forbidden-field set plus the generic text/label
# leak surface every A-stage receipt in this project screens for.
FORBIDDEN_KEYS = frozenset(
    {
        "content",
        "text",
        "source_body",
        "source_text",
        "prompt",
        "label",
        "gold",
        "heldout_membership",
        "heldout_locator",
        "heldout_fingerprint",
        "heldout_neighbour",
        "heldout_near_neighbour",
        "held_out_membership",
        "heldout_family_pool",
        "heldout_membership_locator",
    }
)


class ExtractionError(ValueError):
    """Extraction cannot proceed safely, or a receipt/binding failed to verify."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ExtractionError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- frozen extraction algorithm -------------------------------------------
#
# Not yet executed against any source unit (the builder-packet gate below is
# closed), but frozen and hashed now so that the moment a builder packet is
# issued, extraction runs against a formula that was fixed *before* any
# builder-eligible unit was known -- not tuned post hoc to whichever unit
# turns out to be in the complement.

EXTRACTION_ALGORITHM_DESCRIPTOR: dict[str, Any] = {
    "algorithm_id": "v4-a4-deterministic-span-extraction-v1",
    "algorithm_version": "v1",
    "unit_of_extraction": "sentence_span",
    "content_blind": False,
    "ordering": "source_unit_id_ascending_then_byte_offset_ascending",
    "input_hash_formula": "sha256(raw_span_bytes_utf8)",
    "output_hash_formula": (
        "sha256(canonical_json({source_unit_id, span_index, span_byte_length, "
        "input_sha256, extraction_algorithm_id, extraction_algorithm_version}))"
    ),
    "text_emitted": False,
    "reproducibility": "byte_stable_given_identical_source_unit_bytes_and_frozen_segmentation_rule",
}

EXTRACTION_ALGORITHM_DESCRIPTOR_SHA256 = sha256_text(canonical_json(EXTRACTION_ALGORITHM_DESCRIPTOR))


def extraction_record_output_hash(
    source_unit_id: str, span_index: int, span_byte_length: int, input_sha256: str
) -> str:
    """Pure function implementing ``output_hash_formula`` above. Never touches
    span text -- only the record's own identity fields and the already-hashed
    ``input_sha256`` are covered."""
    record = {
        "source_unit_id": source_unit_id,
        "span_index": span_index,
        "span_byte_length": span_byte_length,
        "input_sha256": input_sha256,
        "extraction_algorithm_id": EXTRACTION_ALGORITHM_DESCRIPTOR["algorithm_id"],
        "extraction_algorithm_version": EXTRACTION_ALGORITHM_DESCRIPTOR["algorithm_version"],
    }
    return sha256_text(canonical_json(record))


# --- builder-packet gate ----------------------------------------------------


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def check_builder_packet_gate(root: Path = ROOT) -> dict[str, Any]:
    """Independently re-derive the current block state from the bound A3
    receipt on disk. Never trusts anything the A4 receipt itself declares --
    only the live A3 seal.

    Deliberately does not open ``batch_state/open-model-data/v4-a3-heldout/``
    (the private membership artifact) at all: A4 is not the artifact's
    owner role, and the gate only needs A3's own public
    ``temporal_firewall``/``execution_counters`` fields, which already say
    whether a builder packet was issued -- reading the private artifact
    directly would not tell A4 anything more about *its own* eligibility to
    proceed, and would cross the access-firewall boundary for no gain.
    """
    a3_path = (
        root / "data/projects/open_model_data/admission/dataset_v4_a3_heldout_source_family_seal_receipt_v1.json"
    ).resolve()
    require(root.resolve() in a3_path.parents, "A3 receipt path escapes the repository root -- refusing")
    require(
        a3_path.is_file(), f"A3 held-out seal receipt is missing, cannot evaluate the builder-packet gate: {a3_path}"
    )

    a3_receipt = _load(a3_path)
    require(
        a3_receipt.get("controlling_outcome_sha256") == V4_SHA256,
        "A3 receipt is not bound to the expected V4 controlling outcome -- refusing",
    )
    seal = a3_receipt.get("heldout_partition_seal", {})
    temporal = a3_receipt.get("temporal_firewall", {})
    counters = a3_receipt.get("execution_counters", {})

    a3_seal_complete = bool(seal.get("heldout_membership_assigned_privately")) and not bool(
        seal.get("heldout_membership_included")
    )
    builder_packet_issued = bool(temporal.get("builder_packet_issued"))
    builder_packets_issued_count = counters.get("builder_packets_issued", 0)

    gate_open = a3_seal_complete and builder_packet_issued and builder_packets_issued_count > 0

    return {
        "gate_id": "v4-a4-builder-packet-gate-v1",
        "a3_seal_complete": a3_seal_complete,
        "builder_packet_issued": builder_packet_issued,
        "builder_eligible_source_unit_ids_known_to_a4": gate_open,
        "gate_open": gate_open,
        "owner_role": "A3_heldout",
        "blocked_reason_code": None if gate_open else "builder_packet_not_issued",
    }


# --- receipt verification ---------------------------------------------------


def _load_schema() -> dict[str, Any]:
    schema = _load(A4_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return schema


def validate_receipt_schema(receipt: dict[str, Any]) -> None:
    errors = sorted(Draft202012Validator(_load_schema()).iter_errors(receipt), key=lambda e: list(e.path))
    require(not errors, f"receipt fails schema validation: {errors[0].message}" if errors else "")


def validate_algorithm_metadata(receipt: dict[str, Any]) -> None:
    algorithm = receipt["extraction_algorithm"]
    declared = {k: algorithm.get(k) for k in EXTRACTION_ALGORITHM_DESCRIPTOR}
    require(
        declared == EXTRACTION_ALGORITHM_DESCRIPTOR,
        "receipt extraction_algorithm does not match the frozen EXTRACTION_ALGORITHM_DESCRIPTOR -- refusing",
    )
    require(
        algorithm.get("algorithm_descriptor_sha256") == EXTRACTION_ALGORITHM_DESCRIPTOR_SHA256,
        "receipt algorithm_descriptor_sha256 does not match the locally recomputed frozen descriptor hash -- refusing",
    )


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
            f"binding {name!r} on-disk sha256 ({actual}) does not match the receipt's declared "
            f"sha256 ({binding['sha256']}) for {binding['path']} -- refusing",
        )


def validate_gate_matches_receipt(receipt: dict[str, Any], root: Path) -> None:
    gate = check_builder_packet_gate(root)
    declared = receipt["builder_packet_gate"]
    require(
        declared["a3_seal_complete"] == gate["a3_seal_complete"]
        and declared["builder_packet_issued"] == gate["builder_packet_issued"]
        and declared["builder_eligible_source_unit_ids_known_to_a4"]
        == gate["builder_eligible_source_unit_ids_known_to_a4"],
        "receipt builder_packet_gate does not match the state independently re-derived from the live A3 "
        "receipt -- refusing (reseal or regenerate required)",
    )
    if not gate["gate_open"]:
        require(
            receipt["extraction_ledger"] == [],
            "builder_packet_gate is closed but extraction_ledger is non-empty -- refusing "
            "(extraction must never run ahead of builder-packet issuance)",
        )
        require(
            receipt["execution_counters"]["source_units_extracted"] == 0
            and receipt["execution_counters"]["spans_extracted"] == 0,
            "builder_packet_gate is closed but execution_counters claim extraction occurred -- refusing",
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


def validate_extraction_ledger_hashes(receipt: dict[str, Any]) -> None:
    """Recompute every ledger record's ``output_sha256`` from its own
    identity fields; catches a hand-edited or stale ledger entry even though
    the ledger is currently always empty (the gate stays closed)."""
    for record in receipt["extraction_ledger"]:
        expected = extraction_record_output_hash(
            record["source_unit_id"], record["span_index"], record["span_byte_length"], record["input_sha256"]
        )
        require(
            record["output_sha256"] == expected,
            f"extraction_ledger record for {record['source_unit_id']!r} span {record['span_index']} "
            f"does not reproduce output_sha256 from its own identity fields -- refusing",
        )


def validate_receipt_independently(receipt: dict[str, Any], root: Path = ROOT) -> None:
    validate_algorithm_metadata(receipt)
    validate_bindings_hash_to_disk(receipt, root)
    validate_gate_matches_receipt(receipt, root)
    validate_no_forbidden_keys(receipt)
    validate_extraction_ledger_hashes(receipt)
    validate_receipt_schema(receipt)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--receipt",
        type=Path,
        default=A4_RECEIPT_PATH,
        help="A4 receipt JSON to verify (default: the tracked V4 A4 extraction receipt). Read-only.",
    )
    args = parser.parse_args(argv)

    receipt = _load(args.receipt)
    validate_receipt_independently(receipt)
    gate = check_builder_packet_gate()
    print(canonical_json({"status": receipt["status"], "builder_packet_gate": gate}))


if __name__ == "__main__":
    try:
        main()
    except ExtractionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
