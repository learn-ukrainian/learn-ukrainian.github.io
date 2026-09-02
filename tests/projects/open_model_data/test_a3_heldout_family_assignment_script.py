"""V4 A3 held-out family assignment script: salted commitment, fail-closed
rerun, and private-artifact filesystem protections.

Exercises scripts/projects/open_model_data/v4_a3_heldout_family_assignment.py
directly (import + call), never by inspecting the sealed receipt's own
committed hashes -- those stay opaque here, as they must in production.
"""

from __future__ import annotations

import json
import os
import secrets
import stat
from pathlib import Path

import pytest

from scripts.projects.open_model_data import v4_a3_heldout_family_assignment as assignment

FAMILY_IDS = [f"fam-synthetic-{index:02d}" for index in range(9)]


def _fresh_receipt(salt: bytes, family_ids: list[str]) -> dict:
    """Build a minimal stand-in receipt carrying real commitments for the
    given (salt, family_ids), shaped like the sealed production receipt."""
    result = assignment.assign(salt, family_ids)
    summary = assignment.public_commitment_summary(salt, result)
    return {
        "heldout_partition_seal": {
            "assignment_algorithm": {
                "salt_commitment_sha256": summary["salt_commitment_sha256"],
                "assignment_commitment_sha256": summary["assignment_commitment_sha256"],
            }
        }
    }


# --- commitment is not enumerable from public fields ----------------------


def test_a3_heldout_assignment_commitment_resists_public_enumeration() -> None:
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    real_commitment = assignment.assignment_commitment_sha256(salt, result["membership"])

    # Public knowledge: the family_id registry and heldout_count == 1. An
    # attacker enumerates every single-family-heldout candidate membership.
    for candidate_heldout in FAMILY_IDS:
        candidate_membership = {
            fid: ("heldout" if fid == candidate_heldout else "builder_eligible") for fid in FAMILY_IDS
        }
        # The old, unsalted commitment (plain sha256 over the membership
        # JSON) is exactly this enumeration attack -- it must not match.
        unsalted_guess = assignment.sha256_text(assignment.canonical_json(candidate_membership))
        assert unsalted_guess != real_commitment
        # Guessing without the real salt also fails, even for the correct
        # candidate membership.
        wrong_key_guess = assignment.assignment_commitment_sha256(b"0" * 32, candidate_membership)
        assert wrong_key_guess != real_commitment

    # Only the true (salt, membership) pair reproduces the commitment.
    assert assignment.assignment_commitment_sha256(salt, result["membership"]) == real_commitment


def test_a3_heldout_assignment_commitment_is_domain_separated_from_salt_commitment() -> None:
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    assert assignment.assignment_commitment_sha256(salt, result["membership"]) != assignment.salt_commitment_sha256(
        salt
    )


# --- persistence roundtrip -------------------------------------------------


def test_a3_heldout_assignment_persistence_roundtrip(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME

    assignment.write_private_artifact(membership_path, salt, result)

    assert stat.S_IMODE(private_dir.stat().st_mode) == assignment.PRIVATE_DIR_MODE
    assert stat.S_IMODE(membership_path.stat().st_mode) == assignment.PRIVATE_FILE_MODE

    loaded = assignment.load_private_artifact(membership_path)
    assert loaded["salt_hex"] == salt.hex()
    assert loaded["membership"] == result["membership"]
    assert loaded["algorithm_descriptor_sha256"] == assignment.ALGORITHM_DESCRIPTOR_SHA256


# --- fail-closed rerun -------------------------------------------------


def test_a3_heldout_assignment_default_refuses_to_generate_without_flag(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(
        json.dumps({"source_family_registry": {"families": [{"family_id": fid} for fid in FAMILY_IDS]}})
    )

    with pytest.raises(assignment.AssignmentError, match="--generate"):
        assignment.main(["--receipt", str(receipt_path), "--private-dir", str(private_dir)])

    assert not (private_dir / assignment.MEMBERSHIP_FILENAME).exists()


def test_a3_heldout_assignment_rerun_verifies_and_never_regenerates(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    private_dir = tmp_path / "private"
    salt_hex = secrets.token_bytes(32).hex()

    salt = bytes.fromhex(salt_hex)
    receipt = _fresh_receipt(salt, FAMILY_IDS)
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(
        json.dumps({**receipt, "source_family_registry": {"families": [{"family_id": fid} for fid in FAMILY_IDS]}})
    )

    assignment.main(
        [
            "--receipt",
            str(receipt_path),
            "--private-dir",
            str(private_dir),
            "--generate",
            "--salt-hex",
            salt_hex,
        ]
    )
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME
    first_write_mtime = membership_path.stat().st_mtime_ns
    capsys.readouterr()

    # A second run (no --generate) with the artifact already present must
    # verify, not regenerate: the file is untouched, no new salt is drawn.
    assignment.main(["--receipt", str(receipt_path), "--private-dir", str(private_dir)])
    assert membership_path.stat().st_mtime_ns == first_write_mtime
    printed = json.loads(capsys.readouterr().out)
    assert printed["salt_commitment_sha256"] == receipt["heldout_partition_seal"]["assignment_algorithm"][
        "salt_commitment_sha256"
    ]

    # --generate against an existing artifact is also refused -- it must not
    # draw a fresh salt and overwrite the sealed one.
    with pytest.raises(assignment.AssignmentError, match="already exists"):
        assignment.main(
            ["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--generate"]
        )
    assert membership_path.stat().st_mtime_ns == first_write_mtime


def test_a3_heldout_assignment_rerun_detects_drift_against_receipt(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME
    assignment.write_private_artifact(membership_path, salt, result)

    # A receipt sealed against a *different* salt's commitments -- e.g. the
    # public receipt drifted (edited) after the private artifact was made.
    other_receipt = _fresh_receipt(secrets.token_bytes(32), FAMILY_IDS)

    with pytest.raises(assignment.AssignmentError, match="drift"):
        assignment.verify_against_receipt(membership_path, other_receipt, FAMILY_IDS)


def test_a3_heldout_assignment_rerun_detects_tampered_membership(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME
    assignment.write_private_artifact(membership_path, salt, result)
    receipt = _fresh_receipt(salt, FAMILY_IDS)

    # Tamper the private artifact directly (simulating a corrupted or
    # maliciously edited private file) by flipping one family's pool.
    payload = json.loads(membership_path.read_text(encoding="utf-8"))
    first_family = FAMILY_IDS[0]
    payload["membership"][first_family] = (
        "builder_eligible" if payload["membership"][first_family] == "heldout" else "heldout"
    )
    os.chmod(membership_path, 0o600)
    membership_path.write_text(json.dumps(payload))
    os.chmod(membership_path, assignment.PRIVATE_FILE_MODE)

    with pytest.raises(assignment.AssignmentError, match="does not reproduce"):
        assignment.verify_against_receipt(membership_path, receipt, FAMILY_IDS)


# --- filesystem protections -------------------------------------------------


def test_a3_heldout_assignment_write_refuses_to_clobber_existing_artifact(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME
    assignment.write_private_artifact(membership_path, salt, result)

    with pytest.raises(assignment.AssignmentError, match="already exists"):
        assignment.write_private_artifact(membership_path, secrets.token_bytes(32), result)


def test_a3_heldout_assignment_write_refuses_symlinked_private_dir(tmp_path: Path) -> None:
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    private_dir = tmp_path / "private-symlink"
    private_dir.symlink_to(real_dir, target_is_directory=True)

    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME

    with pytest.raises(assignment.AssignmentError, match="symlink"):
        assignment.write_private_artifact(membership_path, salt, result)


def test_a3_heldout_assignment_write_refuses_symlinked_target_path(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    private_dir.mkdir(mode=0o700)
    decoy = tmp_path / "decoy.json"
    decoy.write_text("{}")
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME
    membership_path.symlink_to(decoy)

    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)

    with pytest.raises(assignment.AssignmentError, match="symlink"):
        assignment.write_private_artifact(membership_path, salt, result)
    # The decoy target must never be written through.
    assert decoy.read_text() == "{}"


def test_a3_heldout_assignment_write_refuses_preexisting_hardlink_at_target(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    private_dir.mkdir(mode=0o700)
    decoy = tmp_path / "decoy.json"
    decoy.write_text("{}")
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME
    os.link(decoy, membership_path)

    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)

    with pytest.raises(assignment.AssignmentError, match="already exists"):
        assignment.write_private_artifact(membership_path, salt, result)
    assert decoy.read_text() == "{}"


def test_a3_heldout_assignment_load_refuses_symlinked_artifact(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    private_dir.mkdir(mode=0o700)
    decoy = tmp_path / "decoy.json"
    decoy.write_text(
        json.dumps({"salt_hex": "00" * 32, "membership": {}, "algorithm_descriptor_sha256": "x"})
    )
    os.chmod(decoy, 0o600)
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME
    membership_path.symlink_to(decoy)

    with pytest.raises(assignment.AssignmentError, match="symlink"):
        assignment.load_private_artifact(membership_path)


def test_a3_heldout_assignment_load_refuses_wrong_mode(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    private_dir.mkdir(mode=0o700)
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME
    membership_path.write_text(
        json.dumps({"salt_hex": "00" * 32, "membership": {}, "algorithm_descriptor_sha256": "x"})
    )
    os.chmod(membership_path, 0o644)

    with pytest.raises(assignment.AssignmentError, match="mode"):
        assignment.load_private_artifact(membership_path)
