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

ROOT = Path(__file__).resolve().parents[3]
REAL_RECEIPT_PATH = (
    ROOT / "data/projects/open_model_data/admission/dataset_v4_a3_heldout_source_family_seal_receipt_v1.json"
)
REAL_RECEIPT = json.loads(REAL_RECEIPT_PATH.read_text(encoding="utf-8"))

FAMILY_IDS = [f"fam-synthetic-{index:02d}" for index in range(9)]
assert len(FAMILY_IDS) == len(REAL_RECEIPT["source_family_registry"]["families"])


@pytest.fixture(autouse=True)
def _private_root_under_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect the module's intended private root under pytest's tmp_path
    for every test, so ordinary tests don't need to know about the
    containment check -- only the dedicated traversal tests below override
    this again to exercise it directly."""
    monkeypatch.setattr(assignment, "PRIVATE_ROOT", tmp_path)


def _receipt_shape(family_ids: list[str]) -> dict:
    """A full, schema-conformant stand-in receipt: a deep copy of the real
    sealed production receipt -- same bindings (real paths, real on-disk
    sha256), same access_firewall, same everything else -- with only
    ``source_family_registry.families`` swapped for synthetic ``family_ids``
    (same count as the real registry, so every schema const tied to
    family_count, including ``heldout_count``/``builder_eligible_count``,
    still holds) and the two salt-derived commitment hashes cleared to
    represent a not-yet-sealed state (``_receipt_is_sealed`` treats an empty
    string as absent).

    Building this from the real receipt -- rather than hand-rolling an
    approximation -- means every test that runs through ``main()`` exercises
    the exact schema/algorithm-metadata/binding-hash independent-validation
    path production runs, not a stand-in of it.
    """
    assert len(family_ids) == len(REAL_RECEIPT["source_family_registry"]["families"])
    receipt = copy.deepcopy(REAL_RECEIPT)
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


def _fresh_receipt(salt: bytes, family_ids: list[str]) -> dict:
    """Build a full stand-in receipt carrying real commitments for the
    given (salt, family_ids), shaped like the sealed production receipt."""
    result = assignment.assign(salt, family_ids)
    summary = assignment.public_commitment_summary(salt, result)
    receipt = _receipt_shape(family_ids)
    algorithm = receipt["heldout_partition_seal"]["assignment_algorithm"]
    algorithm["salt_commitment_sha256"] = summary["salt_commitment_sha256"]
    algorithm["assignment_commitment_sha256"] = summary["assignment_commitment_sha256"]
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


# --- independent receipt validation ----------------------------------------
#
# Reproduces the reviewer's probe directly: a receipt whose declared
# algorithm_descriptor_sha256 / heldout_count / binding sha256 was altered
# must be refused by main() itself -- not merely by a separate pytest run
# against the schema -- before any private-artifact filesystem operation.
# Uses the real, on-disk production receipt (mutated in a temp copy) so
# these are genuine end-to-end regressions, not stand-ins of the real shape.


def test_a3_heldout_main_refuses_receipt_with_altered_algorithm_descriptor_sha256(tmp_path: Path) -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["heldout_partition_seal"]["assignment_algorithm"]["algorithm_descriptor_sha256"] = "0" * 64
    receipt_path = _write_receipt(tmp_path, receipt)
    private_dir = tmp_path / "private"

    with pytest.raises(assignment.AssignmentError, match="algorithm_descriptor_sha256"):
        assignment.main(["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--generate"])
    assert not (private_dir / assignment.MEMBERSHIP_FILENAME).exists()


def test_a3_heldout_main_refuses_receipt_with_altered_algorithm_metadata_field(tmp_path: Path) -> None:
    """A mismatched individual metadata field (heldout_fraction) must be
    caught independently of the descriptor hash comparison -- not just
    trusted because some other field still matches."""
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["heldout_partition_seal"]["assignment_algorithm"]["heldout_fraction"] = 0.5
    receipt_path = _write_receipt(tmp_path, receipt)
    private_dir = tmp_path / "private"

    with pytest.raises(assignment.AssignmentError, match="assignment_algorithm metadata"):
        assignment.main(["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--generate"])
    assert not (private_dir / assignment.MEMBERSHIP_FILENAME).exists()


def test_a3_heldout_main_refuses_receipt_with_altered_heldout_count(tmp_path: Path) -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["heldout_partition_seal"]["heldout_count"] = 2
    receipt["heldout_partition_seal"]["builder_eligible_count"] = 7
    receipt_path = _write_receipt(tmp_path, receipt)
    private_dir = tmp_path / "private"

    with pytest.raises(assignment.AssignmentError, match="heldout_count"):
        assignment.main(["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--generate"])
    assert not (private_dir / assignment.MEMBERSHIP_FILENAME).exists()


def test_a3_heldout_main_refuses_receipt_with_altered_binding_hash(tmp_path: Path) -> None:
    """A binding's declared sha256 is never trusted -- the actual file named
    by ``path`` is hashed and must match."""
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["bindings"]["slot_manifest"]["sha256"] = "0" * 64
    receipt_path = _write_receipt(tmp_path, receipt)
    private_dir = tmp_path / "private"

    with pytest.raises(assignment.AssignmentError, match="on-disk sha256"):
        assignment.main(["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--generate"])
    assert not (private_dir / assignment.MEMBERSHIP_FILENAME).exists()


def test_a3_heldout_main_refuses_sealed_receipt_that_fails_schema(tmp_path: Path) -> None:
    """A sealed receipt (real commitments present) must also be fully
    schema-conformant -- a schema-forbidden field (e.g. a smuggled salt_hex
    on a binding) is refused even though every other independent check
    (algorithm metadata, counts, on-disk binding hash) still passes."""
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["bindings"]["slot_manifest"]["salt_hex"] = "00" * 32
    receipt_path = _write_receipt(tmp_path, receipt)
    private_dir = tmp_path / "private"

    with pytest.raises(assignment.AssignmentError, match="schema"):
        assignment.main(["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--generate"])
    assert not (private_dir / assignment.MEMBERSHIP_FILENAME).exists()


def test_a3_heldout_main_accepts_the_real_sealed_receipt_unmutated() -> None:
    """Sanity check: the actual checked-in production receipt passes every
    independent check unmutated (schema, algorithm metadata, pool counts,
    on-disk binding hashes) -- proving the checks above fail *because* of
    the specific mutation, not because the real receipt itself is somehow
    unable to pass its own validation. Does not exercise --generate here:
    a fresh random salt can never reproduce the real receipt's already-
    sealed commitments, which is a separate (and already-tested) refusal."""
    assignment.validate_receipt_independently(copy.deepcopy(REAL_RECEIPT))


# --- legacy artifact migration (pre receipt_binding_sha256) ----------------


def _write_legacy_artifact(private_dir: Path, salt: bytes, result: dict) -> Path:
    """Write a private artifact in the exact shape parent 0587a233 wrote:
    every current field except receipt_binding_sha256, which did not exist
    yet. Bypasses write_private_artifact deliberately -- that function
    always writes the current (post-migration) shape."""
    private_dir.mkdir(mode=assignment.PRIVATE_DIR_MODE, parents=True, exist_ok=True)
    os.chmod(private_dir, assignment.PRIVATE_DIR_MODE)
    payload = {
        "algorithm_id": assignment.ALGORITHM_ID,
        "algorithm_descriptor_sha256": assignment.ALGORITHM_DESCRIPTOR_SHA256,
        "salt_hex": salt.hex(),
        "membership": result["membership"],
        "heldout_family_ids": result["heldout_family_ids"],
        "builder_eligible_family_ids": result["builder_eligible_family_ids"],
    }
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME
    membership_path.write_text(assignment.canonical_json(payload) + "\n")
    os.chmod(membership_path, assignment.PRIVATE_FILE_MODE)
    return membership_path


def test_a3_heldout_assignment_is_legacy_artifact_detects_pre_binding_shape(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    membership_path = _write_legacy_artifact(private_dir, salt, result)

    assert assignment.is_legacy_artifact(membership_path)


def test_a3_heldout_assignment_plain_verify_against_legacy_artifact_points_at_migrate(tmp_path: Path) -> None:
    """A plain rerun (no --generate, no --migrate) against a legacy artifact
    must not be stuck on a generic 'missing required fields' error -- it
    must fail closed with clear guidance to pass --migrate."""
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    receipt = _fresh_receipt(salt, FAMILY_IDS)
    receipt_path = _write_receipt(tmp_path, receipt)
    _write_legacy_artifact(private_dir, salt, result)

    with pytest.raises(assignment.AssignmentError, match="--migrate"):
        assignment.main(["--receipt", str(receipt_path), "--private-dir", str(private_dir)])


def test_a3_heldout_assignment_generate_against_legacy_artifact_still_refuses(tmp_path: Path) -> None:
    """--generate against an existing (even legacy) artifact is still
    refused -- --migrate, not --generate, is the only sanctioned upgrade."""
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    receipt = _fresh_receipt(salt, FAMILY_IDS)
    receipt_path = _write_receipt(tmp_path, receipt)
    membership_path = _write_legacy_artifact(private_dir, salt, result)

    with pytest.raises(assignment.AssignmentError, match="already exists"):
        assignment.main(["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--generate"])
    # Untouched: still legacy-shaped, no receipt_binding_sha256 was added.
    assert assignment.is_legacy_artifact(membership_path)


def test_a3_heldout_assignment_migrate_upgrades_legacy_artifact_in_place(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    receipt = _fresh_receipt(salt, FAMILY_IDS)
    receipt_path = _write_receipt(tmp_path, receipt)
    membership_path = _write_legacy_artifact(private_dir, salt, result)

    assignment.main(["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--migrate"])
    printed = json.loads(capsys.readouterr().out)
    assert printed["salt_commitment_sha256"] == receipt["heldout_partition_seal"]["assignment_algorithm"][
        "salt_commitment_sha256"
    ]

    assert not assignment.is_legacy_artifact(membership_path)
    upgraded = assignment.load_private_artifact(membership_path)
    assert upgraded["membership"] == result["membership"]
    assert upgraded["heldout_family_ids"] == result["heldout_family_ids"]
    assert upgraded["builder_eligible_family_ids"] == result["builder_eligible_family_ids"]
    assert upgraded["salt_hex"] == salt.hex()
    assert upgraded["receipt_binding_sha256"] == assignment.receipt_binding_sha256(receipt)

    # A plain verify now succeeds -- the artifact is no longer stuck.
    assignment.main(["--receipt", str(receipt_path), "--private-dir", str(private_dir)])


def test_a3_heldout_assignment_migrate_is_idempotent_refuses_already_migrated_artifact(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    receipt = _fresh_receipt(salt, FAMILY_IDS)
    receipt_path = _write_receipt(tmp_path, receipt)
    membership_path = private_dir / assignment.MEMBERSHIP_FILENAME
    assignment.write_private_artifact(membership_path, salt, result, assignment.receipt_binding_sha256(receipt))

    with pytest.raises(assignment.AssignmentError, match="nothing to migrate"):
        assignment.main(["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--migrate"])


def test_a3_heldout_assignment_migrate_refuses_when_no_artifact_exists(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    receipt_path = _write_receipt(tmp_path, _fresh_receipt(secrets.token_bytes(32), FAMILY_IDS))

    with pytest.raises(assignment.AssignmentError, match="no private artifact found to migrate"):
        assignment.main(["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--migrate"])


def test_a3_heldout_assignment_migrate_refuses_generate_combined(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    receipt_path = _write_receipt(tmp_path, _fresh_receipt(secrets.token_bytes(32), FAMILY_IDS))

    with pytest.raises(assignment.AssignmentError, match="mutually exclusive"):
        assignment.main(
            ["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--migrate", "--generate"]
        )


def test_a3_heldout_assignment_migrate_refuses_tampered_legacy_membership(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    receipt = _fresh_receipt(salt, FAMILY_IDS)
    receipt_path = _write_receipt(tmp_path, receipt)
    membership_path = _write_legacy_artifact(private_dir, salt, result)

    payload = json.loads(membership_path.read_text(encoding="utf-8"))
    first_family = FAMILY_IDS[0]
    payload["membership"][first_family] = (
        "builder_eligible" if payload["membership"][first_family] == "heldout" else "heldout"
    )
    os.chmod(membership_path, 0o600)
    membership_path.write_text(json.dumps(payload))
    os.chmod(membership_path, assignment.PRIVATE_FILE_MODE)

    with pytest.raises(assignment.AssignmentError, match="does not reproduce"):
        assignment.main(["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--migrate"])
    assert assignment.is_legacy_artifact(membership_path)


def test_a3_heldout_assignment_migrate_refuses_commitment_drift(tmp_path: Path) -> None:
    """A legacy artifact whose recomputed commitments don't match the sealed
    receipt (e.g. the receipt was resealed against a different salt since
    the legacy artifact was written) must be refused, not silently adopted."""
    private_dir = tmp_path / "private"
    salt = secrets.token_bytes(32)
    result = assignment.assign(salt, FAMILY_IDS)
    membership_path = _write_legacy_artifact(private_dir, salt, result)

    other_receipt = _fresh_receipt(secrets.token_bytes(32), FAMILY_IDS)
    receipt_path = _write_receipt(tmp_path, other_receipt)

    with pytest.raises(assignment.AssignmentError, match="drift"):
        assignment.main(["--receipt", str(receipt_path), "--private-dir", str(private_dir), "--migrate"])
    assert assignment.is_legacy_artifact(membership_path)
