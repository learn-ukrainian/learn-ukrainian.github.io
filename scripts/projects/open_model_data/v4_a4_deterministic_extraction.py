#!/usr/bin/env python3
"""V4 A4 deterministic extraction: frozen byte-level algorithm (still unexecuted),
real builder-packet consumption, packet-receipt-gated.

A4 is the builder-facing role that turns builder-eligible source units into
immutable, byte-stable, text-free extraction records (span identity +
input/output hashes, never the span text itself). It must never see which
source-family the A3 held-out firewall assigned to the held-out pool -- see
``dataset_v4_a3_heldout_source_family_seal_receipt_v1.json``'s
``access_firewall``, where ``A4_deterministic_extraction`` is locked to
``heldout_family_pool_visible: false`` and forbidden from every held-out
field. This module never opens ``batch_state/open-model-data/v4-a3-heldout/
v4_a3_heldout_membership_v1.json`` (the private membership artifact
A3_heldout owns) -- doing so from a builder-facing role would itself be the
leak this firewall exists to prevent, independent of whether the file
happens to be readable.

The only channel by which A4 may learn *which* source units are
builder-eligible is a **builder packet**: a distinct, A3_heldout-authored,
schema-bound private artifact (``v4_a3_builder_packet_v1.json``, in the same
directory as -- but never the same file as -- the private membership) whose
public commitment receipt (``dataset_v4_a3_builder_packet_receipt_v1.json``)
names the builder-eligible complement's *counts and commitments* and never
the held-out id. A3's own sealed receipt records
``temporal_firewall.builder_packet_issued`` as a permanent, past-tense fact
about the seal event itself (``false`` -- the seal really was completed
before any packet existed, and that never changes); this module therefore
never reads that field to decide whether *a* packet has since been issued
(see ``check_builder_packet_gate``, which reads only the packet's own public
receipt).

This module has three independent parts:

1. ``EXTRACTION_ALGORITHM_DESCRIPTOR`` -- the frozen, hashed, real-corpus
   span-extraction formula A4 will eventually run once byte-addressable
   source content is available for the builder-eligible complement. Not yet
   executed: this receipt's ``extraction_ledger`` stays empty and
   ``source_units_extracted``/``spans_extracted`` stay ``0`` regardless of
   the builder-packet gate's state -- see the ``a4-residual-byte-level-
   extraction-pending-source-ingestion`` residual. Frozen the same way A3
   froze its assignment formula: any edit changes
   ``EXTRACTION_ALGORITHM_DESCRIPTOR_SHA256``, pinned as a schema ``const``.
2. ``UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR`` -- a second, distinct, also
   frozen and hashed algorithm that *does* run today: a content-blind,
   HMAC-keyed commitment over the real (private) builder-eligible
   ``source_unit_id`` set A4 learns from the packet. This is genuine,
   reproducible, immutable extraction-adjacent work over real private data
   -- but it is never described as satisfying
   ``EXTRACTION_ALGORITHM_DESCRIPTOR``'s ``sha256(raw_span_bytes_utf8)``
   formula, because it does not touch span bytes at all. Keeping the two
   algorithms distinct (separate ids, separate frozen hashes, separate
   receipt sections) means neither can be silently substituted for the
   other while still validating.
3. ``check_builder_packet_gate`` -- independently re-derives the current
   gate state from the bound A3 seal receipt *and* the bound A3 builder
   packet receipt on disk (both public, never trusting the A4 receipt's own
   declared fields, never opening any private artifact).

Run with no arguments to verify the checked-in A4 receipt reproduces all
three parts and is consistent with the bound A2/A3 receipts on disk -- using
only public artifacts, so this passes in a fresh checkout with no
``batch_state/``. Pass ``--consume`` (only meaningful where the private
builder packet actually exists) to open it for real, independently verify
it against the public seal receipt's family registry, and (re)compute the
real unit commitments; add ``--write-receipt`` to persist a freshly
assembled receipt. Pass ``--verify-private`` to additionally re-derive the
checked-in receipt's ``builder_packet_consumption`` commitments
cryptographically from the private packet and the private A4 salt artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import secrets
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

_SELF_ROOT = Path(__file__).resolve().parents[3]
if str(_SELF_ROOT) not in sys.path:
    sys.path.insert(0, str(_SELF_ROOT))

from scripts.projects.open_model_data import v4_a3_builder_packet as packet
from scripts.projects.open_model_data import v4_a3_heldout_family_assignment as heldout

ROOT = heldout.ROOT
PRIMARY_ROOT = heldout.PRIMARY_ROOT
PRIVATE_ROOT = heldout.PRIVATE_ROOT

ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"

A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A4_SCHEMA_PATH = CONTRACTS / "dataset_v4_a4_deterministic_extraction_receipt_v1.schema.json"
A3_SEAL_RECEIPT_PATH = ADMISSION / "dataset_v4_a3_heldout_source_family_seal_receipt_v1.json"
A3_PACKET_RECEIPT_PATH = ADMISSION / "dataset_v4_a3_builder_packet_receipt_v1.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"

# The packet A3 issued *to A4* -- distinct from, and stored alongside, the
# private membership file A4 must never open. Same directory (both owned by
# A3_heldout, both under the primary checkout's batch_state/), different
# filename.
DEFAULT_PRIVATE_PACKET_DIR = heldout.DEFAULT_PRIVATE_DIR
# A4's own private artifact directory: the salt behind the unit-commitment
# HMAC. Never shared with, and cryptographically independent of, A3's salt
# (which A4 cannot read: it lives only in the membership file).
DEFAULT_A4_PRIVATE_DIR = PRIVATE_ROOT / "open-model-data/v4-a4-extraction"
A4_SALT_FILENAME = "v4_a4_unit_commitment_salt_v1.json"
A4_SALT_REQUIRED_FIELDS = frozenset({"algorithm_id", "algorithm_version", "salt_hex", "receipt_binding_sha256"})

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
        "salt",
        "salt_hex",
        "private_salt",
    }
)


class ExtractionError(ValueError):
    """Extraction cannot proceed safely, or a receipt/binding failed to verify."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ExtractionError(message)


canonical_json = heldout.canonical_json


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- frozen byte-level extraction algorithm (real corpus, not yet run) -----
#
# Not yet executed against any source unit -- see the module docstring and
# the a4-residual carried in a4_residuals. Frozen and hashed now so that the
# moment byte-addressable, rights-clear source content exists for the
# builder-eligible complement, extraction runs against a formula that was
# fixed before any builder-eligible unit was known -- not tuned post hoc.

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


# --- frozen unit-commitment algorithm (real, content-blind, runs today) ----
#
# Distinct from EXTRACTION_ALGORITHM_DESCRIPTOR above: this never touches
# span bytes, only the real (private) builder-eligible source_unit_id
# strings A4 learns from the packet. HMAC-keyed (never a plain hash) for the
# same reason A3's own commitments are keyed: with a small, fully public
# family_id/source_unit_id registry, an unsalted sha256(id) is enumerable --
# hash every one of the (currently 9) known ids and match. Keying on a
# private salt A4 generates and keeps for itself (never A3's salt, which A4
# cannot read) closes that off.

UNIT_COMMITMENT_DOMAIN = b"v4-a4-builder-eligible-unit-commitment-v1"
UNIT_COMMITMENT_ROOT_DOMAIN = b"v4-a4-builder-eligible-unit-commitment-root-v1"

UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR: dict[str, Any] = {
    "algorithm_id": "v4-a4-unit-commitment-hmac-sha256-v1",
    "algorithm_version": "v1",
    "identity_dimensions": ["source_unit_id"],
    "content_blind": True,
    "formula": (
        "unit_commitment_sha256(id) = hmac_sha256(key=private_a4_salt, "
        "msg=UNIT_COMMITMENT_DOMAIN + 0x00 + canonical_json({source_unit_id: id})); "
        "consumed_units_commitment_sha256(ids) = hmac_sha256(key=private_a4_salt, "
        "msg=UNIT_COMMITMENT_ROOT_DOMAIN + 0x00 + canonical_json({source_unit_ids: sorted(ids), "
        "count: len(ids)}))"
    ),
    "text_emitted": False,
    "reproducibility": "byte_stable_given_the_same_private_a4_salt_and_the_same_builder_eligible_source_unit_id_set",
}

UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR_SHA256 = sha256_text(canonical_json(UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR))


def unit_commitment_sha256(salt: bytes, source_unit_id: str) -> str:
    message = UNIT_COMMITMENT_DOMAIN + b"\x00" + canonical_json({"source_unit_id": source_unit_id}).encode("utf-8")
    return hmac.new(salt, message, hashlib.sha256).hexdigest()


def root_commitment_sha256(salt: bytes, source_unit_ids: list[str]) -> str:
    ordered = sorted(source_unit_ids)
    message = (
        UNIT_COMMITMENT_ROOT_DOMAIN
        + b"\x00"
        + canonical_json({"source_unit_ids": ordered, "count": len(ordered)}).encode("utf-8")
    )
    return hmac.new(salt, message, hashlib.sha256).hexdigest()


def builder_eligible_unit_commitments(salt: bytes, source_unit_ids: list[str]) -> list[str]:
    """Sorted by *commitment value*, not by source_unit_id -- so publishing
    this array never leaks the original ids' sort order either."""
    return sorted(unit_commitment_sha256(salt, unit_id) for unit_id in source_unit_ids)


# --- builder-packet gate (public-only) --------------------------------------


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def check_builder_packet_gate(root: Path = ROOT) -> dict[str, Any]:
    """Independently re-derive the current gate state from the bound A3 seal
    receipt *and* the bound A3 builder packet receipt on disk -- both
    public, git-tracked artifacts. Never trusts anything the A4 receipt
    itself declares, and never opens ``batch_state/`` (the private packet or
    the private membership file A3_heldout owns).

    Deliberately does not consult the sealed A3 receipt's own
    ``temporal_firewall.builder_packet_issued`` -- that field is a
    permanent, past-tense fact about the *seal event itself* (the seal
    really was completed before any packet existed, and stays ``false``
    forever). Whether a packet has since been issued is answered by the
    packet's own, later, distinct public receipt.
    """
    a3_seal_path = (
        root / "data/projects/open_model_data/admission/dataset_v4_a3_heldout_source_family_seal_receipt_v1.json"
    ).resolve()
    require(root.resolve() in a3_seal_path.parents, "A3 seal receipt path escapes the repository root -- refusing")
    require(
        a3_seal_path.is_file(), f"A3 held-out seal receipt is missing, cannot evaluate the builder-packet gate: {a3_seal_path}"
    )

    a3_seal = _load(a3_seal_path)
    require(
        a3_seal.get("controlling_outcome_sha256") == V4_SHA256,
        "A3 seal receipt is not bound to the expected V4 controlling outcome -- refusing",
    )
    seal = a3_seal.get("heldout_partition_seal", {})
    a3_seal_complete = bool(seal.get("heldout_membership_assigned_privately")) and not bool(
        seal.get("heldout_membership_included")
    )

    a3_packet_receipt_path = (
        root / "data/projects/open_model_data/admission/dataset_v4_a3_builder_packet_receipt_v1.json"
    ).resolve()
    require(
        root.resolve() in a3_packet_receipt_path.parents,
        "A3 builder packet receipt path escapes the repository root -- refusing",
    )

    if not a3_packet_receipt_path.is_file():
        return {
            "gate_id": "v4-a4-builder-packet-gate-v1",
            "a3_seal_complete": a3_seal_complete,
            "builder_packet_issued": False,
            "builder_eligible_source_unit_ids_known_to_a4": False,
            "packet_receipt_binding_verified": False,
            "gate_open": False,
            "owner_role": "A3_heldout",
            "blocked_reason_code": "builder_packet_not_issued",
        }

    packet_receipt = _load(a3_packet_receipt_path)
    packet.validate_receipt_schema(packet_receipt)
    require(
        packet_receipt.get("controlling_outcome_sha256") == V4_SHA256,
        "A3 builder packet receipt is not bound to the expected V4 controlling outcome -- refusing",
    )
    actual_seal_sha256 = sha256_file(a3_seal_path)
    require(
        packet_receipt["seal_receipt_binding"]["sha256"] == actual_seal_sha256,
        "A3 builder packet receipt's seal_receipt_binding.sha256 does not match the live on-disk A3 seal "
        "receipt -- refusing (packet was issued against a different seal, or the seal has since drifted)",
    )

    temporal = packet_receipt["temporal_firewall_packet"]
    counters = packet_receipt["execution_counters"]
    builder_packet_issued = bool(temporal["builder_packet_issued"]) and counters["builder_packets_issued"] > 0
    gate_open = a3_seal_complete and builder_packet_issued

    return {
        "gate_id": "v4-a4-builder-packet-gate-v1",
        "a3_seal_complete": a3_seal_complete,
        "builder_packet_issued": builder_packet_issued,
        "builder_eligible_source_unit_ids_known_to_a4": gate_open,
        "packet_receipt_binding_verified": True,
        "gate_open": gate_open,
        "owner_role": "A3_heldout",
        "blocked_reason_code": None if gate_open else "builder_packet_not_issued",
    }


# --- real builder-packet consumption ----------------------------------------


def consume_builder_packet(
    seal_receipt_path: Path = A3_SEAL_RECEIPT_PATH,
    packet_dir: Path = DEFAULT_PRIVATE_PACKET_DIR,
    a4_private_dir: Path = DEFAULT_A4_PRIVATE_DIR,
) -> dict[str, Any]:
    """Open the real private builder packet (never the membership file),
    independently verify its ``builder_eligible_source_unit_ids`` reproduce
    from its own ``builder_eligible_family_ids`` against the *public* seal
    receipt's family registry, resolve A4's own private unit-commitment salt
    (verify-only if one already exists; generate-once, create-only
    otherwise), and compute the real, keyed, id-free commitments.

    Fails closed (raises ``ExtractionError``/``heldout.AssignmentError``) if
    the private packet is missing, unreadable, or does not reproduce --
    never guesses at the builder-eligible set."""
    seal_receipt = _load(seal_receipt_path)
    heldout.validate_receipt_independently(seal_receipt)

    packet_path = packet_dir / packet.PACKET_FILENAME
    stored_packet = heldout.load_private_artifact(packet_path, required_fields=packet.PRIVATE_PACKET_REQUIRED_FIELDS)
    require(
        stored_packet["seal_receipt_binding_sha256"] == heldout.receipt_binding_sha256(seal_receipt),
        "private builder packet seal_receipt_binding_sha256 drift against the live A3 seal receipt -- refusing",
    )
    source_unit_ids = packet.builder_eligible_source_unit_ids(seal_receipt, stored_packet["builder_eligible_family_ids"])
    require(
        source_unit_ids == stored_packet["builder_eligible_source_unit_ids"],
        "private builder packet builder_eligible_source_unit_ids does not reproduce from the live seal "
        "receipt's source_family_registry -- refusing (tampered artifact or registry drift)",
    )

    binding = sha256_text(
        canonical_json(
            {
                "controlling_outcome_sha256": V4_SHA256,
                "seal_receipt_binding_sha256": heldout.receipt_binding_sha256(seal_receipt),
                "packet_seal_receipt_binding_sha256": stored_packet["seal_receipt_binding_sha256"],
            }
        )
    )
    salt_path = a4_private_dir / A4_SALT_FILENAME
    if salt_path.exists() or salt_path.is_symlink():
        stored_salt = heldout.load_private_artifact(salt_path, required_fields=A4_SALT_REQUIRED_FIELDS)
        require(
            stored_salt["algorithm_id"] == UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR["algorithm_id"],
            "private A4 salt artifact algorithm_id does not match the frozen unit-commitment algorithm -- refusing",
        )
        require(
            stored_salt["receipt_binding_sha256"] == binding,
            "private A4 salt artifact receipt_binding_sha256 drift against the live A3 seal/packet -- "
            "refusing (reseal/regenerate required)",
        )
        salt = bytes.fromhex(stored_salt["salt_hex"])
    else:
        salt = secrets.token_bytes(32)
        heldout.write_new_private_json_artifact(
            salt_path,
            {
                "algorithm_id": UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR["algorithm_id"],
                "algorithm_version": UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR["algorithm_version"],
                "salt_hex": salt.hex(),
                "receipt_binding_sha256": binding,
            },
        )

    unit_commitments = builder_eligible_unit_commitments(salt, source_unit_ids)
    root_commitment = root_commitment_sha256(salt, source_unit_ids)

    return {
        "packet_consumed": True,
        "consumed_source_unit_count": len(source_unit_ids),
        "unit_commitments": unit_commitments,
        "consumed_units_commitment_sha256": root_commitment,
    }


def verify_builder_packet_consumption_privately(
    receipt: dict[str, Any],
    seal_receipt_path: Path = A3_SEAL_RECEIPT_PATH,
    packet_dir: Path = DEFAULT_PRIVATE_PACKET_DIR,
    a4_private_dir: Path = DEFAULT_A4_PRIVATE_DIR,
) -> None:
    """Full cryptographic re-derivation of ``builder_packet_consumption``:
    opens the real private builder packet and the private A4 salt artifact
    and requires every declared commitment to reproduce exactly. Not called
    by ``validate_receipt_independently`` (and therefore never required by
    the pytest suite, which must pass in a fresh checkout with no
    ``batch_state/``) -- call this explicitly (``--verify-private``)
    whenever the private artifacts are actually present."""
    consumption = receipt["builder_packet_consumption"]
    require(consumption["packet_consumed"] is True, "receipt does not claim the packet was consumed -- nothing to verify")

    seal_receipt = _load(seal_receipt_path)
    heldout.validate_receipt_independently(seal_receipt)

    packet_path = packet_dir / packet.PACKET_FILENAME
    stored_packet = heldout.load_private_artifact(packet_path, required_fields=packet.PRIVATE_PACKET_REQUIRED_FIELDS)
    require(
        stored_packet["seal_receipt_binding_sha256"] == heldout.receipt_binding_sha256(seal_receipt),
        "private builder packet seal_receipt_binding_sha256 drift against the live A3 seal receipt -- refusing",
    )
    recomputed_ids = packet.builder_eligible_source_unit_ids(seal_receipt, stored_packet["builder_eligible_family_ids"])
    require(
        recomputed_ids == stored_packet["builder_eligible_source_unit_ids"],
        "private builder packet builder_eligible_source_unit_ids does not reproduce from the live seal "
        "receipt's source_family_registry -- refusing",
    )

    salt_path = a4_private_dir / A4_SALT_FILENAME
    stored_salt = heldout.load_private_artifact(salt_path, required_fields=A4_SALT_REQUIRED_FIELDS)
    require(
        stored_salt["algorithm_id"] == UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR["algorithm_id"],
        "private A4 salt artifact algorithm_id does not match the frozen unit-commitment algorithm -- refusing",
    )
    salt = bytes.fromhex(stored_salt["salt_hex"])

    expected_commitments = builder_eligible_unit_commitments(salt, recomputed_ids)
    require(
        expected_commitments == consumption["unit_commitments"],
        "receipt builder_packet_consumption.unit_commitments does not reproduce from the private packet's "
        "real ids and the private A4 salt -- refusing",
    )
    require(
        root_commitment_sha256(salt, recomputed_ids) == consumption["consumed_units_commitment_sha256"],
        "receipt builder_packet_consumption.consumed_units_commitment_sha256 does not reproduce -- refusing",
    )
    require(
        consumption["consumed_source_unit_count"] == len(recomputed_ids),
        "receipt builder_packet_consumption.consumed_source_unit_count does not match the recomputed real "
        "count -- refusing",
    )


# --- receipt assembly --------------------------------------------------------


def build_receipt(consumption: dict[str, Any], gate: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    a2_receipt = _load(A2_RECEIPT_PATH)
    a2_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A2", "status": "unresolved_carried_to_a4"}
        for entry in a2_receipt["residuals"]
    ]

    return {
        "schema_version": "dataset_v4_a4_deterministic_extraction_receipt_v1",
        "receipt_id": "dataset-v4-a4-deterministic-extraction-v1",
        "status": "A4_BUILDER_PACKET_CONSUMED_GATE_OPEN_TEXT_FREE_NO_COMPLEMENT_ENUMERATION",
        "text_free": True,
        "controlling_outcome_sha256": V4_SHA256,
        "control_surfaces": {"public_control_issue": 7423, "pilot_child_issue": 7430, "private_operational_board": 622},
        "bindings": {
            "a2_source_operation_admission": {
                "path": str(A2_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A2_RECEIPT_PATH),
                "schema_version": "dataset_v4_a2_source_operation_admission_receipt_v1",
            },
            "a3_heldout_source_family_seal": {
                "path": str(A3_SEAL_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A3_SEAL_RECEIPT_PATH),
                "schema_version": "dataset_v4_a3_heldout_source_family_seal_receipt_v1",
            },
            "a3_builder_packet_receipt": {
                "path": str(A3_PACKET_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A3_PACKET_RECEIPT_PATH),
                "schema_version": "dataset_v4_a3_builder_packet_receipt_v1",
            },
            "extraction_algorithm_implementation": {
                "path": "scripts/projects/open_model_data/v4_a4_deterministic_extraction.py",
                "sha256": sha256_file(root / "scripts/projects/open_model_data/v4_a4_deterministic_extraction.py"),
                "schema_version": "v4_a4_deterministic_extraction_script_v1",
            },
        },
        "extraction_algorithm": {
            **EXTRACTION_ALGORITHM_DESCRIPTOR,
            "algorithm_descriptor_sha256": EXTRACTION_ALGORITHM_DESCRIPTOR_SHA256,
        },
        "builder_packet_gate": {
            "gate_id": gate["gate_id"],
            "status": "BUILDER_PACKET_ISSUED_GATE_OPEN" if gate["gate_open"] else "AWAITING_A3_HELDOUT_BUILDER_PACKET_ISSUANCE",
            "requires": ["A3_seal_complete", "builder_packet_issued_by_a3_heldout"],
            "a3_seal_complete": gate["a3_seal_complete"],
            "builder_packet_issued": gate["builder_packet_issued"],
            "builder_eligible_source_unit_ids_known_to_a4": gate["builder_eligible_source_unit_ids_known_to_a4"],
            "packet_receipt_binding_verified": gate["packet_receipt_binding_verified"],
            "owner_role": gate["owner_role"],
            "blocked_reason_code": gate["blocked_reason_code"],
        },
        "builder_packet_consumption": {
            "consumption_id": "v4-a4-builder-packet-consumption-v1",
            "packet_opened_by": "A4_deterministic_extraction",
            "packet_consumed": consumption["packet_consumed"],
            "unit_commitment_algorithm": {
                **UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR,
                "algorithm_descriptor_sha256": UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR_SHA256,
            },
            "consumed_source_unit_count": consumption["consumed_source_unit_count"],
            "unit_commitments": consumption["unit_commitments"],
            "consumed_units_commitment_sha256": consumption["consumed_units_commitment_sha256"],
            "membership_disclosed": False,
            "heldout_family_id_disclosed": False,
        },
        "extraction_ledger": [],
        "a2_residuals_carried_forward": a2_residuals_carried,
        "a4_residuals": [
            {
                "residual_id": "a4-residual-byte-level-extraction-pending-source-ingestion",
                "subject_kind": "process",
                "subject_id": "byte_level_span_extraction",
                "stage": "A4",
                "reason_code": "source_byte_content_not_yet_ingested_for_v4",
                "owner_role": "V4_source_byte_ingestion",
                "next_action": (
                    "ingest byte-addressable, rights-clear source content for the builder-eligible complement "
                    "(never resolving which family is held out) so the frozen sha256(raw_span_bytes_utf8) "
                    "formula in extraction_algorithm can execute for real against real spans; until then "
                    "extraction_ledger stays empty by design"
                ),
                "retryability": "retryable",
                "evidence_refs": [
                    "admission.dataset_v4_a4_deterministic_extraction_receipt_v1.extraction_algorithm",
                    "admission.dataset_v4_a4_deterministic_extraction_receipt_v1.builder_packet_consumption",
                ],
            }
        ],
        "execution_counters": {
            "dataset_rows_emitted": 0,
            "new_source_fetches": 0,
            "source_units_extracted": 0,
            "spans_extracted": 0,
            "builder_packets_consumed": 1 if consumption["packet_consumed"] else 0,
            "builder_eligible_units_committed": consumption["consumed_source_unit_count"],
        },
        "safety_assertions": {
            "rows_not_admitted": True,
            "text_emitted": False,
            "held_out_membership_referenced": False,
            "extraction_executed_without_builder_packet": False,
            "mac_corpus_copy_created": False,
            "historical_v3_control_not_used": True,
            "modern_rusyn_not_mapped_to_dialect": True,
            "prebuilder_state_claimed": False,
            "training_ready_silver_claimed": False,
            "later_release_state_claimed": False,
            "epic_done_claimed": False,
            "builder_eligible_ids_present_in_public_diff": False,
        },
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
        and declared["builder_eligible_source_unit_ids_known_to_a4"] == gate["builder_eligible_source_unit_ids_known_to_a4"]
        and declared["packet_receipt_binding_verified"] == gate["packet_receipt_binding_verified"]
        and declared["blocked_reason_code"] == gate["blocked_reason_code"],
        "receipt builder_packet_gate does not match the state independently re-derived from the live A3 "
        "seal and A3 builder packet receipts -- refusing (reseal/re-issue or regenerate required)",
    )

    # The byte-level extraction ledger stays empty regardless of gate state:
    # this receipt never executes the frozen EXTRACTION_ALGORITHM_DESCRIPTOR
    # formula against real bytes (see a4_residuals) -- only the id-free
    # builder_packet_consumption commitment below reflects real work done.
    require(
        receipt["extraction_ledger"] == [],
        "extraction_ledger is non-empty -- the frozen byte-level formula has not been executed in this "
        "receipt; refusing (real span-byte extraction is a separate, explicitly-scoped future change)",
    )
    require(
        receipt["execution_counters"]["source_units_extracted"] == 0
        and receipt["execution_counters"]["spans_extracted"] == 0,
        "execution_counters claim byte-level extraction occurred while extraction_ledger is empty -- refusing",
    )

    consumption = receipt["builder_packet_consumption"]
    if gate["gate_open"]:
        require(
            consumption["packet_consumed"] is True,
            "builder_packet_gate is open but builder_packet_consumption.packet_consumed is not true -- refusing",
        )
    else:
        require(
            consumption["packet_consumed"] is False and consumption["unit_commitments"] == [],
            "builder_packet_gate is closed but builder_packet_consumption claims a packet was consumed -- refusing",
        )


def validate_builder_packet_consumption(receipt: dict[str, Any]) -> None:
    """Public-only structural verification of ``builder_packet_consumption``:
    the algorithm metadata/hash, internal count/shape consistency, and (when
    the packet receipt is available on disk) a cross-check of the declared
    count against the packet receipt's own public
    ``builder_eligible_source_unit_count``. Never re-derives the commitment
    *values* themselves -- that requires the private packet and the private
    A4 salt artifact; see ``verify_builder_packet_consumption_privately``."""
    consumption = receipt["builder_packet_consumption"]
    algorithm = consumption["unit_commitment_algorithm"]
    declared = {k: algorithm.get(k) for k in UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR}
    require(
        declared == UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR,
        "builder_packet_consumption.unit_commitment_algorithm does not match the frozen "
        "UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR -- refusing",
    )
    require(
        algorithm.get("algorithm_descriptor_sha256") == UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR_SHA256,
        "builder_packet_consumption.unit_commitment_algorithm.algorithm_descriptor_sha256 does not match the "
        "locally recomputed frozen descriptor hash -- refusing",
    )

    if not consumption["packet_consumed"]:
        require(
            consumption["consumed_source_unit_count"] == 0 and consumption["unit_commitments"] == [],
            "builder_packet_consumption.packet_consumed is false but declares consumed units -- refusing",
        )
        return

    require(
        len(consumption["unit_commitments"]) == consumption["consumed_source_unit_count"],
        "builder_packet_consumption.unit_commitments length does not match consumed_source_unit_count -- refusing",
    )
    require(
        len(set(consumption["unit_commitments"])) == len(consumption["unit_commitments"]),
        "builder_packet_consumption.unit_commitments contains duplicate commitments -- refusing",
    )
    require(
        consumption["unit_commitments"] == sorted(consumption["unit_commitments"]),
        "builder_packet_consumption.unit_commitments is not sorted by commitment value -- refusing",
    )

    if A3_PACKET_RECEIPT_PATH.is_file():
        packet_receipt = _load(A3_PACKET_RECEIPT_PATH)
        require(
            consumption["consumed_source_unit_count"] == packet_receipt["packet"]["builder_eligible_source_unit_count"],
            "builder_packet_consumption.consumed_source_unit_count does not match the public A3 builder "
            "packet receipt's builder_eligible_source_unit_count -- refusing",
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
    the ledger is currently always empty (byte-level extraction has not run)."""
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
    validate_builder_packet_consumption(receipt)
    validate_no_forbidden_keys(receipt)
    validate_extraction_ledger_hashes(receipt)
    validate_receipt_schema(receipt)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--receipt",
        type=Path,
        default=A4_RECEIPT_PATH,
        help="A4 receipt JSON to verify (default: the tracked V4 A4 extraction receipt).",
    )
    parser.add_argument(
        "--consume",
        action="store_true",
        help=(
            "Open the real private builder packet, independently verify it, and (re)compute the real unit "
            "commitments. Requires the packet-gate to be open and the private packet to be present -- "
            "fails closed otherwise. Prints the consumption summary (id-free)."
        ),
    )
    parser.add_argument(
        "--seal-receipt", type=Path, default=A3_SEAL_RECEIPT_PATH, help="public A3 seal receipt JSON (read-only)"
    )
    parser.add_argument(
        "--packet-dir",
        type=Path,
        default=DEFAULT_PRIVATE_PACKET_DIR,
        help="directory holding the private builder packet A3 issued to A4 (read-only)",
    )
    parser.add_argument(
        "--a4-private-dir",
        type=Path,
        default=DEFAULT_A4_PRIVATE_DIR,
        help="directory for A4's own private unit-commitment salt artifact",
    )
    parser.add_argument(
        "--write-receipt",
        action="store_true",
        help="With --consume, assemble and write the freshly computed receipt to --receipt.",
    )
    parser.add_argument(
        "--verify-private",
        action="store_true",
        help="Additionally re-derive builder_packet_consumption cryptographically from the private artifacts.",
    )
    args = parser.parse_args(argv)

    if args.consume:
        gate = check_builder_packet_gate()
        require(
            gate["gate_open"],
            f"builder_packet_gate is not open (blocked_reason_code={gate['blocked_reason_code']!r}) -- "
            "refusing to consume",
        )
        consumption = consume_builder_packet(args.seal_receipt, args.packet_dir, args.a4_private_dir)
        if args.write_receipt:
            receipt = build_receipt(consumption, gate)
            validate_receipt_independently(receipt)
            args.receipt.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        print(canonical_json(consumption))
        return

    receipt = _load(args.receipt)
    validate_receipt_independently(receipt)
    if args.verify_private:
        verify_builder_packet_consumption_privately(receipt, args.seal_receipt, args.packet_dir, args.a4_private_dir)
    gate = check_builder_packet_gate()
    print(canonical_json({"status": receipt["status"], "builder_packet_gate": gate}))


if __name__ == "__main__":
    try:
        main()
    except ExtractionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
