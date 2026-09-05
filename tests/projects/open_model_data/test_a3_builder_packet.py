"""V4 A3 builder packet: private complement disclosure, public commitment-only receipt.

Exercises scripts/projects/open_model_data/v4_a3_builder_packet.py directly
(import + call), never by inspecting the private packet's own committed
salt/ids -- those stay opaque here, as they must in production. Every test
family_id/source_unit_id below is synthetic, never a real V4 family.
"""

from __future__ import annotations

import copy
import json
import os
import secrets
import stat
from pathlib import Path

import pytest

from scripts.projects.open_model_data import v4_a3_builder_packet as packet
from scripts.projects.open_model_data import v4_a3_heldout_family_assignment as heldout

ROOT = Path(__file__).resolve().parents[3]
REAL_SEAL_RECEIPT_PATH = (
    ROOT / "data/projects/open_model_data/admission/dataset_v4_a3_heldout_source_family_seal_receipt_v1.json"
)
REAL_SEAL_RECEIPT = json.loads(REAL_SEAL_RECEIPT_PATH.read_text(encoding="utf-8"))

FAMILY_IDS = [f"fam-synthetic-{index:02d}" for index in range(9)]
assert len(FAMILY_IDS) == len(REAL_SEAL_RECEIPT["source_family_registry"]["families"])


def _seal_receipt_shape(family_ids: list[str]) -> dict:
    """A full, schema-conformant stand-in seal receipt built from the real
    checked-in one -- same bindings/access_firewall/everything else -- with
    only the family registry swapped for synthetic ids and the commitments
    cleared (unsealed)."""
    receipt = copy.deepcopy(REAL_SEAL_RECEIPT)
    receipt["source_family_registry"]["families"] = [
        {
            "family_id": fid,
            "member_source_unit_ids": [f"synthetic.{fid}"],
            "source_class": "existing_corpus_collection",
            "grouping_rationale": (
                "distinct_existing_local_corpus_collection_identity_no_cross_collection_merge_evidence"
            ),
        }
        for fid in family_ids
    ]
    algorithm = receipt["heldout_partition_seal"]["assignment_algorithm"]
    algorithm["salt_commitment_sha256"] = ""
    algorithm["assignment_commitment_sha256"] = ""
    return receipt


def _sealed_receipt(salt: bytes, family_ids: list[str]) -> tuple[dict, dict]:
    result = heldout.assign(salt, family_ids)
    summary = heldout.public_commitment_summary(salt, result)
    receipt = _seal_receipt_shape(family_ids)
    algorithm = receipt["heldout_partition_seal"]["assignment_algorithm"]
    algorithm["salt_commitment_sha256"] = summary["salt_commitment_sha256"]
    algorithm["assignment_commitment_sha256"] = summary["assignment_commitment_sha256"]
    return receipt, result


@pytest.fixture(autouse=True)
def _fixed_synthetic_provenance_resources():
    from _v4_provenance_resource_fixture import synthetic_resources
    with synthetic_resources():
        yield


def _write_seal_receipt(tmp_path: Path, receipt: dict, name: str = "seal_receipt.json") -> Path:
    from _v4_provenance_resource_fixture import ACTIVE
    ACTIVE.get().install_seal(receipt, tmp_path)
    path = tmp_path / name
    path.write_text(json.dumps(receipt))
    return path


def _seed_membership(tmp_path: Path, salt: bytes, result: dict, receipt: dict, name: str = "private") -> Path:
    membership_dir = tmp_path / name
    membership_path = membership_dir / heldout.MEMBERSHIP_FILENAME
    binding = heldout.receipt_binding_sha256(receipt)
    heldout.write_private_artifact(membership_path, salt, result, binding)
    return membership_dir


def _tamper_packet(packet_path: Path, mutate) -> None:
    payload = json.loads(packet_path.read_text(encoding="utf-8"))
    mutate(payload)
    os.chmod(packet_path, 0o600)
    packet_path.write_text(json.dumps(payload))
    os.chmod(packet_path, heldout.PRIVATE_FILE_MODE)


# --- source_unit_id mapping -------------------------------------------------


def test_builder_eligible_source_unit_ids_maps_families_sorted() -> None:
    receipt = _seal_receipt_shape(FAMILY_IDS)
    subset = sorted(FAMILY_IDS[:3])
    ids = packet.builder_eligible_source_unit_ids(receipt, subset)
    assert ids == sorted(f"synthetic.{fid}" for fid in subset)


def test_builder_eligible_source_unit_ids_refuses_unknown_family_id() -> None:
    receipt = _seal_receipt_shape(FAMILY_IDS)
    with pytest.raises(packet.BuilderPacketError, match="not present in seal receipt registry"):
        packet.builder_eligible_source_unit_ids(receipt, ["fam-does-not-exist"])


# --- commitment: unforgeable, unenumerable, domain-separated ---------------


def test_packet_commitment_resists_public_enumeration_and_is_domain_separated() -> None:
    salt = secrets.token_bytes(32)
    receipt, result = _sealed_receipt(salt, FAMILY_IDS)
    source_unit_ids = packet.builder_eligible_source_unit_ids(receipt, result["builder_eligible_family_ids"])
    payload = packet._private_packet_payload(receipt, result["builder_eligible_family_ids"], source_unit_ids)
    real_commitment = packet.packet_commitment_sha256(salt, payload)

    # Public knowledge: the 9-member family_id registry and heldout_count ==
    # 1. An attacker enumerates every candidate 8-of-9 builder-eligible
    # complement (equivalently, every candidate single held-out family).
    for held_out_candidate in FAMILY_IDS:
        candidate_family_ids = sorted(fid for fid in FAMILY_IDS if fid != held_out_candidate)
        candidate_units = packet.builder_eligible_source_unit_ids(receipt, candidate_family_ids)
        candidate_payload = packet._private_packet_payload(receipt, candidate_family_ids, candidate_units)
        wrong_key_guess = packet.packet_commitment_sha256(b"0" * 32, candidate_payload)
        assert wrong_key_guess != real_commitment

    assert packet.packet_commitment_sha256(salt, payload) == real_commitment
    # Domain-separated from the sibling module's assignment commitment over
    # the exact same secret -- never confusable/reducible to it.
    assignment_commitment = heldout.assignment_commitment_sha256(salt, result["membership"])
    assert real_commitment != assignment_commitment


# --- issuance ----------------------------------------------------------


def test_issue_packet_writes_private_artifact_and_returns_id_free_summary(tmp_path: Path) -> None:
    salt = secrets.token_bytes(32)
    receipt, result = _sealed_receipt(salt, FAMILY_IDS)
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)
    membership_dir = _seed_membership(tmp_path, salt, result, receipt)
    packet_dir = tmp_path / "packet"

    summary = packet.issue_packet(seal_receipt_path, membership_dir, packet_dir)

    assert summary["family_count"] == 9
    assert summary["heldout_count"] == 1
    assert summary["builder_eligible_count"] == 8
    assert summary["builder_eligible_source_unit_count"] == 8
    serialized_summary = json.dumps(summary)
    assert not any(fid in serialized_summary for fid in FAMILY_IDS)

    packet_path = packet_dir / packet.PACKET_FILENAME
    assert stat.S_IMODE(packet_dir.stat().st_mode) == heldout.PRIVATE_DIR_MODE
    assert stat.S_IMODE(packet_path.stat().st_mode) == heldout.PRIVATE_FILE_MODE

    stored = heldout.load_private_artifact(packet_path, required_fields=packet.PRIVATE_PACKET_REQUIRED_FIELDS)
    assert stored["builder_eligible_family_ids"] == result["builder_eligible_family_ids"]
    assert stored["builder_eligible_source_unit_ids"] == sorted(
        f"synthetic.{fid}" for fid in result["builder_eligible_family_ids"]
    )
    # Disjointness: nothing from the held-out pool ever enters the packet.
    assert set(stored["builder_eligible_family_ids"]).isdisjoint(result["heldout_family_ids"])


def test_issue_packet_refuses_when_seal_receipt_not_yet_sealed(tmp_path: Path) -> None:
    receipt = _seal_receipt_shape(FAMILY_IDS)  # unsealed: empty commitment strings
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)

    with pytest.raises(packet.BuilderPacketError, match="not yet sealed"):
        packet.issue_packet(seal_receipt_path, tmp_path / "private", tmp_path / "packet")


def test_issue_packet_refuses_when_membership_artifact_missing(tmp_path: Path) -> None:
    salt = secrets.token_bytes(32)
    receipt, _ = _sealed_receipt(salt, FAMILY_IDS)
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)

    with pytest.raises(heldout.AssignmentError, match="missing"):
        packet.issue_packet(seal_receipt_path, tmp_path / "private", tmp_path / "packet")


def test_issue_packet_refuses_to_overwrite_existing_packet(tmp_path: Path) -> None:
    salt = secrets.token_bytes(32)
    receipt, result = _sealed_receipt(salt, FAMILY_IDS)
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)
    membership_dir = _seed_membership(tmp_path, salt, result, receipt)
    packet_dir = tmp_path / "packet"

    packet.issue_packet(seal_receipt_path, membership_dir, packet_dir)
    with pytest.raises(heldout.AssignmentError, match="already exists"):
        packet.issue_packet(seal_receipt_path, membership_dir, packet_dir)


# --- verify / fail-closed rerun --------------------------------------------


def test_verify_packet_reproduces_issued_commitment(tmp_path: Path) -> None:
    salt = secrets.token_bytes(32)
    receipt, result = _sealed_receipt(salt, FAMILY_IDS)
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)
    membership_dir = _seed_membership(tmp_path, salt, result, receipt)
    packet_dir = tmp_path / "packet"

    issued = packet.issue_packet(seal_receipt_path, membership_dir, packet_dir)
    verified = packet.verify_packet(seal_receipt_path, packet_dir, membership_dir)
    assert verified == issued


def test_verify_packet_detects_tampered_source_unit_ids(tmp_path: Path) -> None:
    salt = secrets.token_bytes(32)
    receipt, result = _sealed_receipt(salt, FAMILY_IDS)
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)
    membership_dir = _seed_membership(tmp_path, salt, result, receipt)
    packet_dir = tmp_path / "packet"
    packet.issue_packet(seal_receipt_path, membership_dir, packet_dir)

    packet_path = packet_dir / packet.PACKET_FILENAME
    _tamper_packet(packet_path, lambda payload: payload.__setitem__("builder_eligible_source_unit_ids", ["synthetic.tampered"]))

    with pytest.raises(packet.BuilderPacketError, match="does not reproduce"):
        packet.verify_packet(seal_receipt_path, packet_dir, membership_dir)


def test_verify_packet_detects_family_id_drift_against_membership_artifact(tmp_path: Path) -> None:
    salt = secrets.token_bytes(32)
    receipt, result = _sealed_receipt(salt, FAMILY_IDS)
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)
    membership_dir = _seed_membership(tmp_path, salt, result, receipt)
    packet_dir = tmp_path / "packet"
    packet.issue_packet(seal_receipt_path, membership_dir, packet_dir)

    packet_path = packet_dir / packet.PACKET_FILENAME
    other_family_ids = sorted(set(FAMILY_IDS) - {result["builder_eligible_family_ids"][0]})
    _tamper_packet(packet_path, lambda payload: payload.__setitem__("builder_eligible_family_ids", other_family_ids))

    with pytest.raises(packet.BuilderPacketError, match="no longer matches the membership artifact"):
        packet.verify_packet(seal_receipt_path, packet_dir, membership_dir)


def test_verify_packet_detects_packet_seal_binding_field_tampered(tmp_path: Path) -> None:
    """Tamper only the packet's own recorded seal_receipt_binding_sha256
    (leaving family/unit ids consistent) -- this is the one drift
    verify_against_receipt's own membership-level check cannot see, because
    it never opens the packet at all."""
    salt = secrets.token_bytes(32)
    receipt, result = _sealed_receipt(salt, FAMILY_IDS)
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)
    membership_dir = _seed_membership(tmp_path, salt, result, receipt)
    packet_dir = tmp_path / "packet"
    packet.issue_packet(seal_receipt_path, membership_dir, packet_dir)

    packet_path = packet_dir / packet.PACKET_FILENAME
    _tamper_packet(packet_path, lambda payload: payload.__setitem__("seal_receipt_binding_sha256", "0" * 64))

    with pytest.raises(packet.BuilderPacketError, match="seal_receipt_binding_sha256 drift"):
        packet.verify_packet(seal_receipt_path, packet_dir, membership_dir)


def test_verify_packet_refuses_when_membership_reseal_required(tmp_path: Path) -> None:
    """A public seal receipt that drifted since the packet was issued (e.g.
    reseal_required_on edited) must be caught by the membership-binding check
    before packet-specific logic ever runs."""
    salt = secrets.token_bytes(32)
    receipt, result = _sealed_receipt(salt, FAMILY_IDS)
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)
    membership_dir = _seed_membership(tmp_path, salt, result, receipt)
    packet_dir = tmp_path / "packet"
    packet.issue_packet(seal_receipt_path, membership_dir, packet_dir)

    drifted = copy.deepcopy(receipt)
    drifted["heldout_partition_seal"]["reseal_required_on"] = ["some_other_trigger"]
    drifted_path = _write_seal_receipt(tmp_path, drifted, name="drifted.json")

    with pytest.raises(heldout.AssignmentError, match="binding drift"):
        packet.verify_packet(drifted_path, packet_dir, membership_dir)


# --- public receipt assembly and independent verification ------------------


def test_build_public_receipt_matches_schema_and_carries_no_ids(tmp_path: Path) -> None:
    salt = secrets.token_bytes(32)
    receipt, result = _sealed_receipt(salt, FAMILY_IDS)
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)
    membership_dir = _seed_membership(tmp_path, salt, result, receipt)
    packet_dir = tmp_path / "packet"
    summary = packet.issue_packet(seal_receipt_path, membership_dir, packet_dir)

    public_receipt = packet.build_public_receipt(summary, seal_receipt_path)
    packet.validate_receipt_schema(public_receipt)

    serialized = json.dumps(public_receipt)
    assert not any(fid in serialized for fid in FAMILY_IDS)
    assert not any(f"synthetic.{fid}" in serialized for fid in FAMILY_IDS)
    assert public_receipt["packet"]["builder_eligible_count"] == 8
    assert public_receipt["packet"]["heldout_count"] == 1
    assert public_receipt["temporal_firewall_packet"]["builder_packet_issued"] is True
    assert public_receipt["temporal_firewall_packet"]["seal_was_sealed_before_any_builder_packet"] is True
    assert public_receipt["execution_counters"]["dataset_rows_emitted"] == 0
    assert public_receipt["safety_assertions"]["heldout_membership_exposed_to_builder"] is False
    assert public_receipt["safety_assertions"]["builder_eligible_ids_present_in_public_diff"] is False


def test_validate_public_receipt_independently_accepts_freshly_issued_packet(tmp_path: Path) -> None:
    salt = secrets.token_bytes(32)
    receipt, result = _sealed_receipt(salt, FAMILY_IDS)
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)
    membership_dir = _seed_membership(tmp_path, salt, result, receipt)
    packet_dir = tmp_path / "packet"
    summary = packet.issue_packet(seal_receipt_path, membership_dir, packet_dir)
    public_receipt = packet.build_public_receipt(summary, seal_receipt_path)

    verified = packet.validate_public_receipt_independently(public_receipt, seal_receipt_path, membership_dir, packet_dir)
    assert verified == summary


def test_validate_public_receipt_independently_detects_commitment_tamper(tmp_path: Path) -> None:
    salt = secrets.token_bytes(32)
    receipt, result = _sealed_receipt(salt, FAMILY_IDS)
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)
    membership_dir = _seed_membership(tmp_path, salt, result, receipt)
    packet_dir = tmp_path / "packet"
    summary = packet.issue_packet(seal_receipt_path, membership_dir, packet_dir)
    public_receipt = packet.build_public_receipt(summary, seal_receipt_path)
    public_receipt["packet"]["packet_commitment_sha256"] = "0" * 64

    with pytest.raises(packet.BuilderPacketError, match="packet_commitment_sha256 drift"):
        packet.validate_public_receipt_independently(public_receipt, seal_receipt_path, membership_dir, packet_dir)


def test_validate_public_receipt_independently_detects_bound_seal_hash_tamper(tmp_path: Path) -> None:
    salt = secrets.token_bytes(32)
    receipt, result = _sealed_receipt(salt, FAMILY_IDS)
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)
    membership_dir = _seed_membership(tmp_path, salt, result, receipt)
    packet_dir = tmp_path / "packet"
    summary = packet.issue_packet(seal_receipt_path, membership_dir, packet_dir)
    public_receipt = packet.build_public_receipt(summary, seal_receipt_path)
    public_receipt["seal_receipt_binding"]["sha256"] = "0" * 64

    with pytest.raises(packet.BuilderPacketError, match="on-disk sha256"):
        packet.validate_public_receipt_independently(public_receipt, seal_receipt_path, membership_dir, packet_dir)


def test_validate_public_receipt_independently_detects_count_tamper(tmp_path: Path) -> None:
    salt = secrets.token_bytes(32)
    receipt, result = _sealed_receipt(salt, FAMILY_IDS)
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)
    membership_dir = _seed_membership(tmp_path, salt, result, receipt)
    packet_dir = tmp_path / "packet"
    summary = packet.issue_packet(seal_receipt_path, membership_dir, packet_dir)
    public_receipt = packet.build_public_receipt(summary, seal_receipt_path)
    # Still schema-valid (schema only bounds this field with a minimum) --
    # must be caught by the recomputation cross-check, not schema alone.
    public_receipt["packet"]["builder_eligible_source_unit_count"] = 999

    with pytest.raises(packet.BuilderPacketError, match="counts drift"):
        packet.validate_public_receipt_independently(public_receipt, seal_receipt_path, membership_dir, packet_dir)


# --- real production receipt: schema/registry sanity (no private access) ---


def test_real_seal_receipt_family_registry_supports_the_packet_module() -> None:
    """The real, checked-in production seal receipt has the shape this
    module expects -- exercised without ever touching a private artifact."""
    families = REAL_SEAL_RECEIPT["source_family_registry"]["families"]
    real_family_ids = sorted(family["family_id"] for family in families)
    ids = packet.builder_eligible_source_unit_ids(REAL_SEAL_RECEIPT, real_family_ids[:1])
    assert ids  # at least one source_unit_id resolves for a real family_id


# --- CLI -----------------------------------------------------------------


def test_cli_issue_write_receipt_then_default_verify_roundtrip(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    salt = secrets.token_bytes(32)
    receipt, result = _sealed_receipt(salt, FAMILY_IDS)
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)
    membership_dir = _seed_membership(tmp_path, salt, result, receipt)
    packet_dir = tmp_path / "packet"
    packet_receipt_path = tmp_path / "packet_receipt.json"

    packet.main(
        [
            "--seal-receipt", str(seal_receipt_path),
            "--membership-dir", str(membership_dir),
            "--packet-dir", str(packet_dir),
            "--packet-receipt", str(packet_receipt_path),
            "--issue",
            "--write-receipt",
        ]
    )
    capsys.readouterr()
    assert packet_receipt_path.exists()
    written = json.loads(packet_receipt_path.read_text(encoding="utf-8"))
    serialized = json.dumps(written)
    assert not any(fid in serialized for fid in FAMILY_IDS)

    packet.main(
        [
            "--seal-receipt", str(seal_receipt_path),
            "--membership-dir", str(membership_dir),
            "--packet-dir", str(packet_dir),
            "--packet-receipt", str(packet_receipt_path),
        ]
    )
    printed = json.loads(capsys.readouterr().out)
    assert printed["builder_eligible_count"] == 8
    assert not any(fid in json.dumps(printed) for fid in FAMILY_IDS)


def test_cli_issue_refuses_to_overwrite_existing_packet(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    salt = secrets.token_bytes(32)
    receipt, result = _sealed_receipt(salt, FAMILY_IDS)
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)
    membership_dir = _seed_membership(tmp_path, salt, result, receipt)
    packet_dir = tmp_path / "packet"
    argv = [
        "--seal-receipt", str(seal_receipt_path),
        "--membership-dir", str(membership_dir),
        "--packet-dir", str(packet_dir),
        "--issue",
    ]

    packet.main(argv)
    capsys.readouterr()
    with pytest.raises(heldout.AssignmentError, match="already exists"):
        packet.main(argv)
