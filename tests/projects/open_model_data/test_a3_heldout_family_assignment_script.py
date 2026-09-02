"""V4 A3 held-out family assignment script: salted commitment, fail-closed
rerun, full receipt-binding verification, and private-artifact filesystem
protections.

Exercises scripts/projects/open_model_data/v4_a3_heldout_family_assignment.py
directly (import + call), never by inspecting the sealed receipt's own
committed hashes -- those stay opaque here, as they must in production.
"""

from __future__ import annotations

import copy
import json
import os
import secrets
import stat
from pathlib import Path

import pytest

from scripts.projects.open_model_data import v4_a3_heldout_family_assignment as assignment

FAMILY_IDS = [f"fam-synthetic-{index:02d}" for index in range(9)]


@pytest.fixture(autouse=True)
def _private_root_under_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect the module's intended private root under pytest's tmp_path
    for every test, so ordinary tests don't need to know about the
    containment check -- only the dedicated traversal tests below override
    this again to exercise it directly."""
    monkeypatch.setattr(assignment, "PRIVATE_ROOT", tmp_path)


def _receipt_shape(family_ids: list[str]) -> dict:
    """A full, production-shaped stand-in receipt (minus the fields that
    only ``_fresh_receipt``/``_sealed_receipt`` fill in), so binding tests
    exercise the same fields the real receipt carries: controlling SHA,
    bindings, the full family registry, and reseal triggers."""
    return {
        "controlling_outcome_sha256": "1" * 64,
        "bindings": {
            "assignment_algorithm_implementation": {
                "path": "scripts/projects/open_model_data/v4_a3_heldout_family_assignment.py",
                "sha256": "2" * 64,
                "schema_version": "v4_a3_heldout_family_assignment_script_v1",
            }
        },
        "source_family_registry": {
            "grouping_basis": "source_identity_not_prestige_or_provider_arrival_order",
            "family_count": len(family_ids),
            "families": [{"family_id": fid} for fid in family_ids],
        },
        "heldout_partition_seal": {
            "reseal_required_on": ["source_family_registry_change"],
        },
    }


def _fresh_receipt(salt: bytes, family_ids: list[str]) -> dict:
    """Build a full stand-in receipt carrying real commitments for the
    given (salt, family_ids), shaped like the sealed production receipt."""
    result = assignment.assign(salt, family_ids)
    summary = assignment.public_commitment_summary(salt, result)
    receipt = _receipt_shape(family_ids)
    receipt["heldout_partition_seal"]["assignment_algorithm"] = {
        "salt_commitment_sha256": summary["salt_commitment_sha256"],
        "assignment_commitment_sha256": summary["assignment_commitment_sha256"],
    }
    return receipt


def _write_receipt(tmp_path: Path, receipt: dict) -> Path:
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt))
    return receipt_path


def _generate(monkeypatch: pytest.MonkeyPatch, argv: list[str], salt_hex: str | None = None) -> None:
    """Invoke ``main`` with ``--generate``, supplying a deterministic test
    salt (if given) via the env-var override -- never via a CLI flag, so the
    salt is never in argv, matching the production entrypoint's contract."""
    if salt_hex is not None:
        monkeypatch.setenv(assignment.TEST_SALT_ENV_VAR, salt_hex)
    else:
        monkeypatch.delenv(assignment.TEST_SALT_ENV_VAR, raising=False)
    assignment.main(argv)


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


def test_a3_heldout_assignment_requires_exact_32_byte_salt() -> None:
    with pytest.raises(assignment.AssignmentError, match="32 bytes"):
        assignment.assign(b"0" * 16, FAMILY_IDS)
    with pytest.raises(assignment.AssignmentError, match="32 bytes"):
        assignment.assign(b"0" * 33, FAMILY_IDS)


# --- persistence roundtrip -------------------------------------------------


def test_a3_heldout_assignment_persistence_roundtrip(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    receipt = _fresh_receipt(salt, FAMILY_IDS)
    binding = assignment.receipt_binding_sha256(receipt)
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME

    assignment.write_private_artifact(membership_path, salt, result, binding)

    assert stat.S_IMODE(private_dir.stat().st_mode) == assignment.PRIVATE_DIR_MODE
    assert stat.S_IMODE(membership_path.stat().st_mode) == assignment.PRIVATE_FILE_MODE

    loaded = assignment.load_private_artifact(membership_path)
    assert loaded["salt_hex"] == salt.hex()
    assert loaded["membership"] == result["membership"]
    assert loaded["heldout_family_ids"] == result["heldout_family_ids"]
    assert loaded["builder_eligible_family_ids"] == result["builder_eligible_family_ids"]
    assert loaded["algorithm_descriptor_sha256"] == assignment.ALGORITHM_DESCRIPTOR_SHA256
    assert loaded["receipt_binding_sha256"] == binding


# --- fail-closed rerun -------------------------------------------------


def test_a3_heldout_assignment_default_refuses_to_generate_without_flag(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    receipt_path = _write_receipt(tmp_path, _receipt_shape(FAMILY_IDS))

    with pytest.raises(assignment.AssignmentError, match="--generate"):
        assignment.main(["--receipt", str(receipt_path), "--private-dir", str(private_dir)])

    assert not (private_dir / assignment.MEMBERSHIP_FILENAME).exists()


def test_a3_heldout_assignment_rerun_verifies_and_never_regenerates(
    tmp_path: Path, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    private_dir = tmp_path / "private"
    salt_hex = secrets.token_bytes(32).hex()

    salt = bytes.fromhex(salt_hex)
    receipt = _fresh_receipt(salt, FAMILY_IDS)
    receipt_path = _write_receipt(tmp_path, receipt)

    _generate(
        monkeypatch,
        ["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--generate"],
        salt_hex=salt_hex,
    )
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME
    first_write_mtime = membership_path.stat().st_mtime_ns
    capsys.readouterr()

    # A second run (no --generate) with the artifact already present must
    # verify, not regenerate: the file is untouched, no new salt is drawn.
    monkeypatch.delenv(assignment.TEST_SALT_ENV_VAR, raising=False)
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


def test_a3_heldout_assignment_generate_refuses_when_receipt_already_sealed_with_other_commitments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A receipt that already carries real (sealed) commitments -- the
    normal state of a checked-in receipt -- must never accept a freshly
    generated (random-salt) assignment that contradicts those commitments.
    No private artifact may be written in that case."""
    private_dir = tmp_path / "private"
    sealed_receipt = _fresh_receipt(secrets.token_bytes(32), FAMILY_IDS)
    receipt_path = _write_receipt(tmp_path, sealed_receipt)

    with pytest.raises(assignment.AssignmentError, match="already sealed"):
        _generate(
            monkeypatch,
            ["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--generate"],
            salt_hex=secrets.token_bytes(32).hex(),
        )
    assert not (private_dir / assignment.MEMBERSHIP_FILENAME).exists()


def test_a3_heldout_assignment_generate_succeeds_when_it_reproduces_sealed_commitments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The one case --generate may succeed against an already-sealed
    receipt: the supplied salt reproduces the exact sealed commitments."""
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    sealed_receipt = _fresh_receipt(salt, FAMILY_IDS)
    receipt_path = _write_receipt(tmp_path, sealed_receipt)

    _generate(
        monkeypatch,
        ["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--generate"],
        salt_hex=salt.hex(),
    )
    assert (private_dir / assignment.MEMBERSHIP_FILENAME).exists()


def test_a3_heldout_assignment_generate_unsealed_receipt_always_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A receipt with no commitments yet recorded (pre-seal) accepts any
    freshly generated assignment -- there is nothing yet to contradict."""
    private_dir = tmp_path / "private"
    receipt_path = _write_receipt(tmp_path, _receipt_shape(FAMILY_IDS))

    _generate(
        monkeypatch,
        ["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--generate"],
        salt_hex=secrets.token_bytes(32).hex(),
    )
    assert (private_dir / assignment.MEMBERSHIP_FILENAME).exists()


def test_a3_heldout_assignment_rerun_detects_commitment_drift_against_receipt(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    receipt = _fresh_receipt(salt, FAMILY_IDS)
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME
    assignment.write_private_artifact(membership_path, salt, result, assignment.receipt_binding_sha256(receipt))

    # A receipt sealed against a *different* salt's commitments -- e.g. the
    # public receipt drifted (edited) after the private artifact was made.
    other_receipt = _fresh_receipt(secrets.token_bytes(32), FAMILY_IDS)

    with pytest.raises(assignment.AssignmentError, match="drift"):
        assignment.verify_against_receipt(membership_path, other_receipt, FAMILY_IDS)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda receipt: receipt.__setitem__("controlling_outcome_sha256", "9" * 64),
        lambda receipt: receipt["bindings"]["assignment_algorithm_implementation"].__setitem__(
            "sha256", "9" * 64
        ),
        lambda receipt: receipt["source_family_registry"]["families"].append({"family_id": "fam-extra"}),
        lambda receipt: receipt["heldout_partition_seal"].__setitem__(
            "reseal_required_on", ["some_other_trigger"]
        ),
    ],
    ids=["controlling_sha", "bindings", "family_registry", "reseal_triggers"],
)
def test_a3_heldout_assignment_rerun_detects_binding_context_drift(tmp_path: Path, mutate) -> None:
    """Verification is bound to more than the two commitment hashes: a
    change to the controlling SHA, bindings, family registry, or reseal
    triggers -- even with the commitment hashes unchanged -- must refuse."""
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    receipt = _fresh_receipt(salt, FAMILY_IDS)
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME
    assignment.write_private_artifact(membership_path, salt, result, assignment.receipt_binding_sha256(receipt))

    drifted = copy.deepcopy(receipt)
    mutate(drifted)
    # The commitment hashes are untouched by the mutation -- only the
    # binding context changed.
    assert drifted["heldout_partition_seal"]["assignment_algorithm"]["salt_commitment_sha256"] == receipt[
        "heldout_partition_seal"
    ]["assignment_algorithm"]["salt_commitment_sha256"]

    with pytest.raises(assignment.AssignmentError, match="binding drift"):
        assignment.verify_against_receipt(membership_path, drifted, FAMILY_IDS)


def test_a3_heldout_assignment_rerun_detects_tampered_membership(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    receipt = _fresh_receipt(salt, FAMILY_IDS)
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME
    assignment.write_private_artifact(membership_path, salt, result, assignment.receipt_binding_sha256(receipt))

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


def test_a3_heldout_assignment_rerun_detects_tampered_heldout_family_ids_list(tmp_path: Path) -> None:
    """The persisted ``heldout_family_ids`` list is validated against
    recomputation independently of ``membership`` -- a tamper that only
    touches the derived list (leaving ``membership`` itself untouched) must
    still be caught."""
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    receipt = _fresh_receipt(salt, FAMILY_IDS)
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME
    assignment.write_private_artifact(membership_path, salt, result, assignment.receipt_binding_sha256(receipt))

    payload = json.loads(membership_path.read_text(encoding="utf-8"))
    payload["heldout_family_ids"] = ["fam-not-really-heldout"]
    os.chmod(membership_path, 0o600)
    membership_path.write_text(json.dumps(payload))
    os.chmod(membership_path, assignment.PRIVATE_FILE_MODE)

    with pytest.raises(assignment.AssignmentError, match="heldout_family_ids"):
        assignment.verify_against_receipt(membership_path, receipt, FAMILY_IDS)


# --- filesystem protections -------------------------------------------------


def test_a3_heldout_assignment_write_refuses_to_clobber_existing_artifact(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    receipt = _fresh_receipt(salt, FAMILY_IDS)
    binding = assignment.receipt_binding_sha256(receipt)
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME
    assignment.write_private_artifact(membership_path, salt, result, binding)

    with pytest.raises(assignment.AssignmentError, match="already exists"):
        assignment.write_private_artifact(membership_path, secrets.token_bytes(32), result, binding)


def test_a3_heldout_assignment_write_refuses_symlinked_private_dir(tmp_path: Path) -> None:
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    private_dir = tmp_path / "private-symlink"
    private_dir.symlink_to(real_dir, target_is_directory=True)

    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME

    with pytest.raises(assignment.AssignmentError, match="symlink"):
        assignment.write_private_artifact(membership_path, salt, result, "x" * 64)


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
        assignment.write_private_artifact(membership_path, salt, result, "x" * 64)
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
        assignment.write_private_artifact(membership_path, salt, result, "x" * 64)
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


# --- CLI symlink / traversal protection on --private-dir --------------------


def test_a3_heldout_assignment_cli_refuses_private_dir_outside_intended_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``--private-dir`` pointing outside the intended private root (no
    symlink involved -- a plain absolute path escape) must be refused
    before any filesystem write is attempted."""
    fake_root = tmp_path / "fake-batch-state"
    monkeypatch.setattr(assignment, "PRIVATE_ROOT", fake_root)
    outside_dir = tmp_path / "not-batch-state"
    receipt_path = _write_receipt(tmp_path, _receipt_shape(FAMILY_IDS))

    with pytest.raises(assignment.AssignmentError, match="private root"):
        _generate(
            monkeypatch,
            ["--receipt", str(receipt_path), "--private-dir", str(outside_dir), "--generate"],
            salt_hex=secrets.token_bytes(32).hex(),
        )
    assert not outside_dir.exists()


def test_a3_heldout_assignment_cli_refuses_symlinked_private_dir_component(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A symlinked ancestor component of ``--private-dir`` (e.g. pointing
    ``--private-dir`` at a path that resolves, via a symlink, to somewhere
    like ``/usr/bin``) must be caught by the pre-resolve symlink check, not
    silently followed by ``Path.resolve()`` first."""
    fake_root = tmp_path / "fake-batch-state"
    fake_root.mkdir()
    monkeypatch.setattr(assignment, "PRIVATE_ROOT", fake_root)
    decoy_link = fake_root / "decoy-symlink"
    outside_target = tmp_path / "outside-target"
    outside_target.mkdir()
    decoy_link.symlink_to(outside_target, target_is_directory=True)
    receipt_path = _write_receipt(tmp_path, _receipt_shape(FAMILY_IDS))

    with pytest.raises(assignment.AssignmentError, match="symlink"):
        _generate(
            monkeypatch,
            [
                "--receipt",
                str(receipt_path),
                "--private-dir",
                str(decoy_link / "v4-a3-heldout"),
                "--generate",
            ],
            salt_hex=secrets.token_bytes(32).hex(),
        )
    assert not any(outside_target.iterdir())


# --- test-only salt override never rides in argv -----------------------------


def test_a3_heldout_assignment_salt_hex_is_not_a_cli_flag(tmp_path: Path) -> None:
    """The private salt must never be accepted via argv (visible to any
    same-host user via `ps` / `/proc/<pid>/cmdline`) on the shipped
    entrypoint -- only via the test-only environment-variable override."""
    private_dir = tmp_path / "private"
    receipt_path = _write_receipt(tmp_path, _receipt_shape(FAMILY_IDS))

    with pytest.raises(SystemExit):
        assignment.main(
            [
                "--receipt",
                str(receipt_path),
                "--private-dir",
                str(private_dir),
                "--generate",
                "--salt-hex",
                secrets.token_bytes(32).hex(),
            ]
        )
    assert not (private_dir / assignment.MEMBERSHIP_FILENAME).exists()


def test_a3_heldout_assignment_test_salt_override_requires_32_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    private_dir = tmp_path / "private"
    receipt_path = _write_receipt(tmp_path, _receipt_shape(FAMILY_IDS))

    with pytest.raises(assignment.AssignmentError, match="32 bytes"):
        _generate(
            monkeypatch,
            ["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--generate"],
            salt_hex="00" * 16,
        )
