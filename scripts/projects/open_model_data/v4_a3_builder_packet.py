#!/usr/bin/env python3
"""V4 A3 builder packet: private complement disclosure, public commitment-only receipt.

Issues the artifact a builder-facing role (A4 first) needs to learn the
*builder-eligible* ``source_unit_id`` complement without ever learning the
held-out ``family_id``, the private salt, or the membership map itself.

Two artifacts, two audiences:

- a **private** packet (``batch_state/open-model-data/v4-a3-heldout/v4_a3_builder_packet_v1.json``,
  mode 0600 under a 0700 dir, resolved against the primary checkout the same
  way as the private membership artifact -- see
  ``v4_a3_heldout_family_assignment.PRIMARY_ROOT``) naming the
  builder-eligible ``source_unit_id`` complement. A3_heldout-authored,
  never the held-out family_id, salt, or membership map.
- a **public**, git-tracked, text-free receipt
  (``dataset_v4_a3_builder_packet_receipt_v1.json``) carrying counts and a
  salt-keyed commitment hash only. The public A3 seal registry already names
  all 9 families; publishing the 8 builder-eligible ids in git would, by
  elimination, name the held-out family -- so the public receipt never lists
  a single id, only counts and one HMAC commitment.

The sealed A3 seal receipt's own schema ``const``s
``temporal_firewall.builder_packet_issued`` to ``false`` and
``execution_counters.builder_packets_issued`` to ``0``. That is a correct,
permanent historical fact -- the seal really was completed before any
builder packet existed -- and this module never edits it. This packet
receipt is a separate, later artifact with its own
``temporal_firewall_packet`` section recording ``builder_packet_issued:
true`` for *this* event, so a consumer (e.g. a future A4 revision) can
detect packet issuance from a public, schema-bound artifact without ever
opening the private membership file.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

_SELF_ROOT = Path(__file__).resolve().parents[3]
if str(_SELF_ROOT) not in sys.path:
    sys.path.insert(0, str(_SELF_ROOT))

from scripts.projects.open_model_data import v4_a3_heldout_family_assignment as heldout

ROOT = heldout.ROOT
PRIMARY_ROOT = heldout.PRIMARY_ROOT
PRIVATE_ROOT = heldout.PRIVATE_ROOT

DEFAULT_SEAL_RECEIPT = heldout.DEFAULT_RECEIPT
DEFAULT_MEMBERSHIP_DIR = heldout.DEFAULT_PRIVATE_DIR
DEFAULT_PACKET_RECEIPT = (
    ROOT / "data/projects/open_model_data/admission/dataset_v4_a3_builder_packet_receipt_v1.json"
)
PACKET_RECEIPT_SCHEMA = (
    ROOT / "data/projects/open_model_data/contracts/dataset_v4_a3_builder_packet_receipt_v1.schema.json"
)

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

PACKET_FILENAME = "v4_a3_builder_packet_v1.json"
PACKET_ID = "v4-a3-builder-packet-v1"
PACKET_ALGORITHM_ID = "v4-a3-builder-packet-hmac-sha256-v1"
ISSUED_TO_ROLE = "A4_deterministic_extraction"
SEAL_RECEIPT_PUBLIC_PATH = "data/projects/open_model_data/admission/dataset_v4_a3_heldout_source_family_seal_receipt_v1.json"
SEAL_RECEIPT_SCHEMA_VERSION = "dataset_v4_a3_heldout_source_family_seal_receipt_v1"

# Domain-separation label for the packet commitment HMAC -- distinct from
# heldout.ASSIGNMENT_COMMITMENT_DOMAIN even though both are keyed by the
# same private salt, so this commitment can never be confused with, or
# reduced to, the assignment commitment over the same secret.
PACKET_COMMITMENT_DOMAIN = b"v4-a3-builder-packet-commitment-v1"

PRIVATE_PACKET_REQUIRED_FIELDS = frozenset(
    {
        "packet_id",
        "algorithm_id",
        "seal_receipt_binding_sha256",
        "family_count",
        "heldout_count",
        "builder_eligible_count",
        "builder_eligible_family_ids",
        "builder_eligible_source_unit_ids",
    }
)


class BuilderPacketError(ValueError):
    """Builder packet issuance/verification cannot proceed safely."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BuilderPacketError(message)


canonical_json = heldout.canonical_json


def packet_commitment_sha256(salt: bytes, packet_payload: dict[str, Any]) -> str:
    """HMAC-SHA256 over the private packet payload, keyed by the private salt.

    Mirrors ``assignment_commitment_sha256`` in the sibling module: an
    unsalted ``sha256(packet)`` would be enumerable against the public,
    9-member family_id registry -- hash every candidate 8-of-9 complement and
    match against the published commitment. Keying on the salt, which never
    leaves the private artifacts, closes that off.
    """
    message = PACKET_COMMITMENT_DOMAIN + b"\x00" + canonical_json(packet_payload).encode("utf-8")
    return hmac.new(salt, message, hashlib.sha256).hexdigest()


def builder_eligible_source_unit_ids(
    seal_receipt: dict[str, Any], builder_eligible_family_ids: list[str]
) -> list[str]:
    """Map builder-eligible family_ids to their member source_unit_ids using
    only the public seal receipt's ``source_family_registry`` -- no private
    data needed for this half."""
    families = {family["family_id"]: family for family in seal_receipt["source_family_registry"]["families"]}
    ids: list[str] = []
    for family_id in builder_eligible_family_ids:
        require(
            family_id in families,
            f"builder-eligible family_id {family_id!r} not present in seal receipt registry -- refusing",
        )
        ids.extend(families[family_id]["member_source_unit_ids"])
    require(len(ids) == len(set(ids)), "builder-eligible source_unit_ids collide across families -- refusing")
    return sorted(ids)


def _private_packet_payload(
    seal_receipt: dict[str, Any],
    builder_eligible_family_ids: list[str],
    source_unit_ids: list[str],
) -> dict[str, Any]:
    return {
        "packet_id": PACKET_ID,
        "algorithm_id": PACKET_ALGORITHM_ID,
        "seal_receipt_binding_sha256": heldout.receipt_binding_sha256(seal_receipt),
        "family_count": seal_receipt["source_family_registry"]["family_count"],
        "heldout_count": seal_receipt["heldout_partition_seal"]["heldout_count"],
        "builder_eligible_count": len(builder_eligible_family_ids),
        "builder_eligible_family_ids": builder_eligible_family_ids,
        "builder_eligible_source_unit_ids": source_unit_ids,
    }


def public_commitment_summary(salt: bytes, packet_payload: dict[str, Any]) -> dict[str, Any]:
    """Counts and one-way commitment only. Never a family_id or source_unit_id."""
    return {
        "packet_id": packet_payload["packet_id"],
        "algorithm_id": packet_payload["algorithm_id"],
        "family_count": packet_payload["family_count"],
        "heldout_count": packet_payload["heldout_count"],
        "builder_eligible_count": packet_payload["builder_eligible_count"],
        "builder_eligible_source_unit_count": len(packet_payload["builder_eligible_source_unit_ids"]),
        "packet_commitment_sha256": packet_commitment_sha256(salt, packet_payload),
        "seal_receipt_binding_sha256": packet_payload["seal_receipt_binding_sha256"],
    }


def issue_packet(
    seal_receipt_path: Path = DEFAULT_SEAL_RECEIPT,
    membership_dir: Path = DEFAULT_MEMBERSHIP_DIR,
    packet_dir: Path = DEFAULT_MEMBERSHIP_DIR,
) -> dict[str, Any]:
    """Verify the sealed receipt and the private membership artifact --
    never trusting either at face value, reusing the sibling module's own
    independent validation -- then create-only-write the private packet and
    return the public-safe commitment summary. Refuses to overwrite an
    existing packet; reruns must use ``verify_packet`` instead."""
    seal_receipt = json.loads(seal_receipt_path.read_text(encoding="utf-8"))
    heldout.validate_receipt_independently(seal_receipt)
    require(
        heldout.receipt_is_sealed(seal_receipt),
        "seal receipt is not yet sealed (no real commitments) -- a builder packet can only be issued "
        "against an already-sealed A3 receipt",
    )
    family_ids = sorted(family["family_id"] for family in seal_receipt["source_family_registry"]["families"])

    membership_path = membership_dir / heldout.MEMBERSHIP_FILENAME
    # Re-derives membership from the artifact's own stored salt and refuses
    # on any drift/tamper -- see verify_against_receipt's docstring.
    heldout.verify_against_receipt(membership_path, seal_receipt, family_ids)
    stored = heldout.load_private_artifact(membership_path)
    salt = bytes.fromhex(stored["salt_hex"])

    source_unit_ids = builder_eligible_source_unit_ids(seal_receipt, stored["builder_eligible_family_ids"])
    payload = _private_packet_payload(seal_receipt, stored["builder_eligible_family_ids"], source_unit_ids)
    summary = public_commitment_summary(salt, payload)

    packet_path = packet_dir / PACKET_FILENAME
    heldout.write_new_private_json_artifact(packet_path, payload)
    return summary


def verify_packet(
    seal_receipt_path: Path = DEFAULT_SEAL_RECEIPT,
    packet_dir: Path = DEFAULT_MEMBERSHIP_DIR,
    membership_dir: Path = DEFAULT_MEMBERSHIP_DIR,
) -> dict[str, Any]:
    """Fail-closed rerun: reload the existing private packet, recompute its
    commitment from the membership artifact's own stored salt, and require
    every persisted field to reproduce. Never regenerates or overwrites."""
    seal_receipt = json.loads(seal_receipt_path.read_text(encoding="utf-8"))
    heldout.validate_receipt_independently(seal_receipt)

    family_ids = sorted(family["family_id"] for family in seal_receipt["source_family_registry"]["families"])
    membership_path = membership_dir / heldout.MEMBERSHIP_FILENAME
    heldout.verify_against_receipt(membership_path, seal_receipt, family_ids)
    stored_membership = heldout.load_private_artifact(membership_path)
    salt = bytes.fromhex(stored_membership["salt_hex"])

    packet_path = packet_dir / PACKET_FILENAME
    stored_packet = heldout.load_private_artifact(packet_path, required_fields=PRIVATE_PACKET_REQUIRED_FIELDS)
    require(
        stored_packet["builder_eligible_family_ids"] == stored_membership["builder_eligible_family_ids"],
        "private packet builder_eligible_family_ids no longer matches the membership artifact -- "
        "refusing (reseal required)",
    )
    require(
        stored_packet["seal_receipt_binding_sha256"] == heldout.receipt_binding_sha256(seal_receipt),
        "private packet seal_receipt_binding_sha256 drift against the live seal receipt -- refusing (reseal required)",
    )
    recomputed_ids = builder_eligible_source_unit_ids(seal_receipt, stored_packet["builder_eligible_family_ids"])
    require(
        recomputed_ids == stored_packet["builder_eligible_source_unit_ids"],
        "private packet builder_eligible_source_unit_ids does not reproduce from the live seal receipt's "
        "source_family_registry -- refusing (tampered artifact or registry drift)",
    )
    return public_commitment_summary(salt, stored_packet)


# --- public packet receipt --------------------------------------------------


def build_public_receipt(summary: dict[str, Any], seal_receipt_path: Path) -> dict[str, Any]:
    """Assemble the public, text-free, id-free packet receipt from a
    commitment summary (never from raw ids/salt -- the summary itself never
    carries them, see ``public_commitment_summary``)."""
    seal_sha256 = hashlib.sha256(seal_receipt_path.read_bytes()).hexdigest()
    return {
        "schema_version": "dataset_v4_a3_builder_packet_receipt_v1",
        "receipt_id": "dataset-v4-a3-builder-packet-v1",
        "status": "A3_BUILDER_PACKET_ISSUED_TEXT_FREE_NO_COMPLEMENT_ENUMERATION",
        "text_free": True,
        "controlling_outcome_sha256": V4_SHA256,
        "control_surfaces": {
            "public_control_issue": 7423,
            "pilot_child_issue": 7430,
            "private_operational_board": 622,
        },
        "seal_receipt_binding": {
            "path": SEAL_RECEIPT_PUBLIC_PATH,
            "sha256": seal_sha256,
            "schema_version": SEAL_RECEIPT_SCHEMA_VERSION,
            "receipt_binding_sha256": summary["seal_receipt_binding_sha256"],
        },
        "packet": {
            "packet_id": summary["packet_id"],
            "algorithm_id": summary["algorithm_id"],
            "family_count": summary["family_count"],
            "heldout_count": summary["heldout_count"],
            "builder_eligible_count": summary["builder_eligible_count"],
            "builder_eligible_source_unit_count": summary["builder_eligible_source_unit_count"],
            "packet_commitment_sha256": summary["packet_commitment_sha256"],
            "issued_to_role": ISSUED_TO_ROLE,
            "materialization_location": "private_batch_state_and_private_operational_board_622",
            "membership_disclosed": False,
            "heldout_family_id_disclosed": False,
        },
        "temporal_firewall_packet": {
            "firewall_id": "v4-a3-builder-packet-temporal-firewall-v1",
            "builder_packet_issued": True,
            "builder_packet_issued_after_seal": True,
            "seal_receipt_status_at_issuance": (
                "A3_HELDOUT_SOURCE_FAMILY_SEAL_FIREWALL_SEALED_MEMBERSHIP_ASSIGNED_PRIVATE"
            ),
            "seal_was_sealed_before_any_builder_packet": True,
        },
        "execution_counters": {
            "dataset_rows_emitted": 0,
            "builder_packets_issued": 1,
        },
        "safety_assertions": {
            "heldout_membership_exposed_to_builder": False,
            "heldout_family_id_present_in_public_diff": False,
            "builder_eligible_ids_present_in_public_diff": False,
            "prebuilder_state_claimed": False,
            "epic_done_claimed": False,
        },
    }


def _load_packet_receipt_schema() -> dict[str, Any]:
    schema = json.loads(PACKET_RECEIPT_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def validate_receipt_schema(receipt: dict[str, Any]) -> None:
    errors = sorted(Draft202012Validator(_load_packet_receipt_schema()).iter_errors(receipt), key=lambda e: list(e.path))
    require(not errors, f"packet receipt fails schema validation: {errors[0].message}" if errors else "")


def validate_public_receipt_independently(
    receipt: dict[str, Any],
    seal_receipt_path: Path = DEFAULT_SEAL_RECEIPT,
    membership_dir: Path = DEFAULT_MEMBERSHIP_DIR,
    packet_dir: Path = DEFAULT_MEMBERSHIP_DIR,
) -> dict[str, Any]:
    """Full independent verification of a checked-in public packet receipt:
    schema conformance, the seal-receipt binding hash against the actual
    bytes of ``seal_receipt_path`` on disk, and every declared
    count/commitment against a fresh ``verify_packet`` recomputation from
    the private artifacts. Nothing in ``receipt`` is trusted merely because
    it is present.

    Hashes ``seal_receipt_path`` itself -- the same file every other
    computation here (``verify_packet``, ``build_public_receipt``) is bound
    to -- rather than re-deriving a path from the receipt's own declared
    ``seal_receipt_binding.path``. That declared path is schema-``const``ed
    to the one real production seal receipt path, so re-deriving from it
    would silently hash a *different* file than the one the rest of this
    call actually verified against whenever a caller (e.g. a test, or a
    future alternate seal receipt) passes a non-default ``seal_receipt_path``
    -- exactly the kind of drift this function exists to catch, not commit.
    """
    validate_receipt_schema(receipt)

    seal_binding = receipt["seal_receipt_binding"]
    require(seal_receipt_path.is_file(), f"seal receipt not found: {seal_receipt_path}")
    actual_seal_sha256 = hashlib.sha256(seal_receipt_path.read_bytes()).hexdigest()
    require(
        actual_seal_sha256 == seal_binding["sha256"],
        "seal_receipt_binding on-disk sha256 does not match the receipt's declared sha256 -- refusing",
    )

    summary = verify_packet(seal_receipt_path, packet_dir, membership_dir)
    packet = receipt["packet"]
    require(
        summary["packet_commitment_sha256"] == packet["packet_commitment_sha256"],
        "packet_commitment_sha256 drift between the recomputed private packet and the public receipt -- refusing",
    )
    require(
        summary["seal_receipt_binding_sha256"] == seal_binding["receipt_binding_sha256"],
        "seal_receipt_binding_sha256 drift between the recomputed packet and the public receipt -- refusing",
    )
    require(
        summary["family_count"] == packet["family_count"]
        and summary["heldout_count"] == packet["heldout_count"]
        and summary["builder_eligible_count"] == packet["builder_eligible_count"]
        and summary["builder_eligible_source_unit_count"] == packet["builder_eligible_source_unit_count"],
        "packet counts drift between recomputation and the public receipt -- refusing",
    )
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seal-receipt", type=Path, default=DEFAULT_SEAL_RECEIPT, help="sealed A3 receipt JSON (read-only)")
    parser.add_argument("--membership-dir", type=Path, default=DEFAULT_MEMBERSHIP_DIR, help="private membership artifact directory")
    parser.add_argument("--packet-dir", type=Path, default=DEFAULT_MEMBERSHIP_DIR, help="private packet artifact directory")
    parser.add_argument(
        "--packet-receipt", type=Path, default=DEFAULT_PACKET_RECEIPT, help="public packet receipt JSON (read, or written with --write-receipt)"
    )
    parser.add_argument(
        "--issue",
        action="store_true",
        help="Issue a fresh private packet. Refused (fail closed) if one already exists at --packet-dir.",
    )
    parser.add_argument(
        "--write-receipt",
        action="store_true",
        help="Write the recomputed public receipt (counts/commitments only) to --packet-receipt.",
    )
    args = parser.parse_args(argv)

    if args.issue:
        summary = issue_packet(args.seal_receipt, args.membership_dir, args.packet_dir)
    elif args.packet_receipt.exists() and not args.write_receipt:
        receipt = json.loads(args.packet_receipt.read_text(encoding="utf-8"))
        summary = validate_public_receipt_independently(
            receipt, args.seal_receipt, args.membership_dir, args.packet_dir
        )
    else:
        summary = verify_packet(args.seal_receipt, args.packet_dir, args.membership_dir)

    if args.write_receipt:
        receipt = build_public_receipt(summary, args.seal_receipt)
        validate_receipt_schema(receipt)
        args.packet_receipt.write_text(canonical_json(receipt) + "\n", encoding="utf-8")

    print(canonical_json(summary))


if __name__ == "__main__":
    try:
        main()
    except BuilderPacketError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
