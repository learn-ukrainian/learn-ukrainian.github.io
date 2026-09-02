#!/usr/bin/env python3
"""V4 A3 held-out source-family assignment: frozen, salt-keyed, content-blind.

Deterministic given ``(private_salt, family_ids)``: produces a private-only
membership mapping (``family_id -> pool``) plus a small set of public-safe
commitments (counts and one-way commitments, never the salt or the
membership itself).

The formula and its fixed parameters are frozen in ``ALGORITHM_DESCRIPTOR``
below; its SHA-256 (``ALGORITHM_DESCRIPTOR_SHA256``) is pinned as a schema
``const`` in ``dataset_v4_a3_heldout_source_family_seal_receipt_v1.schema.json``,
and this file's own SHA-256 is pinned as an ``artifact_binding`` entry in the
receipt. A private implementation that computes membership any other way
cannot reproduce ``ALGORITHM_DESCRIPTOR_SHA256`` or this file's hash, so it
cannot silently swap in a different membership while still validating
against the sealed schema.

Family count is fixed by the formula (not by the salt), so the held-out
group is always non-empty for the current 9-family registry -- but *which*
family lands in it is salt-dependent and therefore not guessable, not
prestige-ordered, and not provider-arrival-ordered.

``assignment_commitment_sha256`` is an HMAC-SHA256 keyed by the private salt
(domain-separated from any other salt usage), not a plain hash of the public
membership JSON. With a small, fully public family_id registry and a public
``heldout_count``, a plain ``sha256(membership)`` commitment is enumerable:
an attacker just hashes every candidate single-family-heldout membership and
matches it against the published commitment. Keying the commitment on the
salt removes that attack -- reproducing the commitment also requires the
32-byte salt, which never leaves the private artifact.

This script is also fail-closed on rerun: it never silently generates a new
salt or overwrites an existing private artifact. Generating a fresh
assignment requires the explicit ``--generate`` flag *and* no private
artifact already present; if one is present, the script only ever verifies
it reproduces the frozen algorithm and matches the sealed public receipt's
commitments -- it refuses on any drift.

It is also fail-closed against an already-sealed public receipt: if the
receipt loaded via ``--receipt`` already carries real commitments (the
normal state once a receipt is checked in), ``--generate`` refuses to write
a private artifact unless the freshly generated (salt, membership) actually
reproduces those exact commitments. A random salt essentially never does,
so in practice ``--generate`` only succeeds once, before the receipt is
sealed; afterward this script is verify-only for that receipt.

Verification does not stop at the two commitment hashes: it binds the
private artifact to the full receipt context it was sealed against --
``controlling_outcome_sha256``, every artifact ``bindings`` entry, the
complete ``source_family_registry``, and ``reseal_required_on`` -- via a
``receipt_binding_sha256`` fingerprint stored in the private artifact at
generation time and recomputed from the live receipt on every verify. Any
drift in any of those fields (not just the commitments) is refused.

Outputs never leave ``batch_state/`` (git-ignored, mode 0700/0600) or the
private operational board (learn-ukrainian-infra-private#622); only counts
and commitments are safe to publish in the tracked public receipt.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import hmac
import json
import os
import secrets
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
PRIVATE_ROOT = ROOT / "batch_state"
DEFAULT_PRIVATE_DIR = PRIVATE_ROOT / "open-model-data/v4-a3-heldout"
DEFAULT_RECEIPT = (
    ROOT / "data/projects/open_model_data/admission/dataset_v4_a3_heldout_source_family_seal_receipt_v1.json"
)

# Test-only salt override, read from the environment rather than a CLI flag
# so the private salt is never visible in argv / process listings (`ps`,
# `/proc/<pid>/cmdline`). Never set this in production.
TEST_SALT_ENV_VAR = "V4_A3_HELDOUT_TEST_SALT_HEX_ONLY"

ALGORITHM_ID = "v4-a3-hmac-sha256-family-rank-split-v1"
ALGORITHM_VERSION = "v1"

# Domain-separation label for the assignment commitment HMAC. Kept distinct
# from any other use of the private salt (e.g. salt_commitment_sha256, which
# hashes the salt alone) so this commitment can never be confused with or
# reduced to a different keyed digest over the same secret.
ASSIGNMENT_COMMITMENT_DOMAIN = b"v4-a3-heldout-assignment-commitment-v1"

MEMBERSHIP_FILENAME = "v4_a3_heldout_membership_v1.json"
PRIVATE_FILE_MODE = 0o600
PRIVATE_DIR_MODE = 0o700

# Frozen: any edit here changes ALGORITHM_DESCRIPTOR_SHA256, which breaks the
# schema `const` binding and forces an explicit reseal. Do not tune in place.
ALGORITHM_DESCRIPTOR: dict[str, Any] = {
    "algorithm_id": ALGORITHM_ID,
    "algorithm_version": ALGORITHM_VERSION,
    "identity_dimensions": ["family_id"],
    "content_blind": True,
    "formula": (
        "rank_key(family_id) = int(hmac.new(key=private_salt, "
        "msg=family_id.encode('utf-8'), digestmod=hashlib.sha256).hexdigest(), 16); "
        "order family_ids ascending by (rank_key(family_id), family_id); "
        "heldout_target_count = max(1, round(family_count * heldout_fraction)); "
        "the first heldout_target_count family_ids in that order are assigned to the "
        "heldout pool; every remaining family_id is assigned to the builder_eligible pool"
    ),
    "heldout_fraction": 0.1,
    "rounding_rule": "python_round_half_to_even",
    "minimum_heldout_count": 1,
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


ALGORITHM_DESCRIPTOR_SHA256 = sha256_text(canonical_json(ALGORITHM_DESCRIPTOR))


class AssignmentError(ValueError):
    """Assignment cannot proceed safely."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssignmentError(message)


def rank_key(salt: bytes, family_id: str) -> int:
    digest = hmac.new(salt, family_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return int(digest, 16)


def assign(salt: bytes, family_ids: list[str]) -> dict[str, Any]:
    """Apply the frozen ALGORITHM_DESCRIPTOR formula. Pure function of (salt, family_ids)."""
    require(len(salt) == 32, "salt must be exactly 32 bytes")
    require(len(family_ids) == len(set(family_ids)), "family_ids must be unique")
    family_count = len(family_ids)
    require(family_count >= 2, "need at least 2 families to hold one out and keep one builder-eligible")

    ordered = sorted(family_ids, key=lambda fid: (rank_key(salt, fid), fid))
    heldout_target_count = max(1, round(family_count * ALGORITHM_DESCRIPTOR["heldout_fraction"]))
    heldout_target_count = min(heldout_target_count, family_count - 1)
    heldout = set(ordered[:heldout_target_count])
    membership = {fid: ("heldout" if fid in heldout else "builder_eligible") for fid in family_ids}
    heldout_ids = sorted(fid for fid, pool in membership.items() if pool == "heldout")
    builder_ids = sorted(fid for fid, pool in membership.items() if pool == "builder_eligible")
    return {
        "family_count": family_count,
        "membership": membership,
        "heldout_family_ids": heldout_ids,
        "builder_eligible_family_ids": builder_ids,
        "heldout_count": len(heldout_ids),
        "builder_eligible_count": len(builder_ids),
    }


def salt_commitment_sha256(salt: bytes) -> str:
    return hashlib.sha256(salt).hexdigest()


def assignment_commitment_sha256(salt: bytes, membership: dict[str, str]) -> str:
    """HMAC-SHA256 over the membership, keyed by the private salt.

    Unsalted ``sha256(membership)`` is enumerable: with a small, fully
    public ``family_id`` registry and a public ``heldout_count``, hashing
    every candidate single-family-heldout membership and matching against
    the published commitment recovers the held-out family_id without ever
    seeing the salt. Keying on the salt (which never leaves the private
    artifact) makes that enumeration attack require the 32-byte salt too.
    """
    message = ASSIGNMENT_COMMITMENT_DOMAIN + b"\x00" + canonical_json(membership).encode("utf-8")
    return hmac.new(salt, message, hashlib.sha256).hexdigest()


def public_commitment_summary(salt: bytes, result: dict[str, Any]) -> dict[str, Any]:
    """Counts and one-way commitments only. Never the salt or membership."""
    return {
        "algorithm_id": ALGORITHM_ID,
        "algorithm_version": ALGORITHM_VERSION,
        "algorithm_descriptor_sha256": ALGORITHM_DESCRIPTOR_SHA256,
        "family_count": result["family_count"],
        "heldout_count": result["heldout_count"],
        "builder_eligible_count": result["builder_eligible_count"],
        "salt_commitment_sha256": salt_commitment_sha256(salt),
        "assignment_commitment_sha256": assignment_commitment_sha256(salt, result["membership"]),
    }


def receipt_binding_context(receipt: dict[str, Any]) -> dict[str, Any]:
    """The full set of receipt facts a sealed private assignment is bound to.

    Not just the two commitment hashes: the controlling outcome SHA, every
    artifact binding, the complete family registry, and the reseal triggers.
    A receipt that still carries the same two commitment hashes but has
    drifted in any of these -- a family added/removed, a bound artifact
    swapped, the controlling epic changed -- must fail verification.
    """
    seal = receipt["heldout_partition_seal"]
    return {
        "controlling_outcome_sha256": receipt["controlling_outcome_sha256"],
        "bindings": receipt["bindings"],
        "source_family_registry": receipt["source_family_registry"],
        "reseal_required_on": seal["reseal_required_on"],
    }


def receipt_binding_sha256(receipt: dict[str, Any]) -> str:
    return sha256_text(canonical_json(receipt_binding_context(receipt)))


# --- filesystem hardening -----------------------------------------------
#
# Mirrors the symlink/no-clobber/fsync discipline used by the other private
# artifact writers in this project (see phase3_heldout_partition.py and
# phase3_cycle007_labeling_guardian.py). A private artifact carrying the
# held-out membership salt must never be silently overwritten, written
# through a symlink, or written outside its intended directory.


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _assert_no_symlink_components(path: Path) -> None:
    """Refuse if any component of an absolute path (leaf included) is a symlink."""
    require(path.is_absolute(), f"path must be absolute: {path}")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode), f"refusing symlink path component: {current}")


def _absolute_unresolved(path: Path) -> Path:
    """Absolute, lexically-normalized path that never follows a symlink to
    get there.

    Unlike ``Path.resolve()``, which silently follows every symlink
    component *before* any check can run -- so a supplied ``--private-dir``
    of e.g. ``/bin`` (a symlink to ``/usr/bin`` on many systems) resolves
    away to a path that then contains no symlink components to catch --
    this only does lexical ``..``/``.`` normalization via
    ``os.path.normpath``, which touches no filesystem state and follows no
    symlinks. Symlink components are then checked explicitly, on this
    unresolved path, by ``_assert_no_symlink_components``.
    """
    base = path if path.is_absolute() else Path.cwd() / path
    return Path(os.path.normpath(base))


def _assert_within_private_root(path: Path, root: Path) -> None:
    """Refuse a ``--private-dir`` outside the one intended private root.

    Runs on the lexically-normalized, not-yet-resolved path (see
    ``_absolute_unresolved``), so this is a real containment check and not
    one a symlink or a resolved ``..`` can route around.
    """
    require(
        path == root or root in path.parents,
        f"--private-dir must be inside the intended private root {root}, refusing traversal: {path}",
    )


def _assert_contained(candidate: Path, base: Path) -> None:
    """Refuse a resolved path that escapes the intended base directory (traversal)."""
    resolved_candidate = candidate.resolve()
    resolved_base = base.resolve()
    require(
        resolved_candidate == resolved_base or resolved_base in resolved_candidate.parents,
        f"refusing path escaping private directory {resolved_base}: {candidate}",
    )


def write_private_artifact(
    path: Path, salt: bytes, result: dict[str, Any], receipt_binding: str
) -> None:
    """Atomically *create* the private membership artifact. Never overwrites.

    Uses write-temp -> fsync -> hardlink-into-place -> unlink-temp: the
    final path either does not exist or holds fully-written content (atomic),
    and ``os.link`` raises ``FileExistsError`` if the destination is already
    occupied by any filesystem object -- a regular file, a stale hardlink, or
    a symlink -- so reruns can never clobber a prior salt (no-clobber).
    Callers must route reruns through ``verify_against_receipt`` instead of
    calling this again.
    """
    private_dir = path.parent
    _assert_no_symlink_components(private_dir)
    private_dir.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
    os.chmod(private_dir, PRIVATE_DIR_MODE)
    _assert_no_symlink_components(path)
    _assert_contained(path, private_dir)
    require(not path.exists() and not path.is_symlink(), f"private artifact already exists, refusing to overwrite: {path}")

    payload = {
        "algorithm_id": ALGORITHM_ID,
        "algorithm_descriptor_sha256": ALGORITHM_DESCRIPTOR_SHA256,
        "salt_hex": salt.hex(),
        "membership": result["membership"],
        "heldout_family_ids": result["heldout_family_ids"],
        "builder_eligible_family_ids": result["builder_eligible_family_ids"],
        "receipt_binding_sha256": receipt_binding,
    }
    encoded = (canonical_json(payload) + "\n").encode("utf-8")

    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=private_dir)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), PRIVATE_FILE_MODE)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            raise AssignmentError(f"private artifact already exists, refusing to overwrite: {path}") from None
        _fsync_directory(private_dir)
    finally:
        with contextlib.suppress(OSError):
            temporary.unlink()


def load_private_artifact(path: Path) -> dict[str, Any]:
    """Read the private membership artifact, refusing anything but a plain,
    owner-only-mode regular file reached with no symlink in its path."""
    _assert_no_symlink_components(path)
    try:
        info = path.lstat()
    except FileNotFoundError:
        raise AssignmentError(f"private artifact missing: {path}") from None
    require(
        stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode),
        f"private artifact is not a regular file: {path}",
    )
    require(
        stat.S_IMODE(info.st_mode) == PRIVATE_FILE_MODE,
        f"private artifact has unexpected mode (want {oct(PRIVATE_FILE_MODE)}): {path}",
    )
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        with os.fdopen(descriptor, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        raise AssignmentError(f"cannot read private artifact: {path}") from exc
    value = json.loads(raw.decode("utf-8"))
    require(isinstance(value, dict), f"private artifact is not a JSON object: {path}")
    required_fields = {
        "salt_hex",
        "membership",
        "heldout_family_ids",
        "builder_eligible_family_ids",
        "receipt_binding_sha256",
    }
    require(required_fields <= value.keys(), f"private artifact missing required fields: {path}")
    return value


# --- fail-closed rerun ----------------------------------------------------


def _receipt_commitments(receipt: dict[str, Any]) -> dict[str, str]:
    algorithm = receipt["heldout_partition_seal"]["assignment_algorithm"]
    return {
        "salt_commitment_sha256": algorithm["salt_commitment_sha256"],
        "assignment_commitment_sha256": algorithm["assignment_commitment_sha256"],
    }


def _receipt_is_sealed(receipt: dict[str, Any]) -> bool:
    """True once the receipt already carries real commitments.

    The receipt schema requires ``salt_commitment_sha256`` /
    ``assignment_commitment_sha256`` to be present and sha256-shaped, so any
    schema-conformant checked-in receipt is always "sealed" by this
    definition. Generation against an already-sealed receipt must reproduce
    its exact commitments or refuse -- see the ``--generate`` branch in
    ``main``.
    """
    algorithm = receipt.get("heldout_partition_seal", {}).get("assignment_algorithm", {})
    return bool(algorithm.get("salt_commitment_sha256")) and bool(algorithm.get("assignment_commitment_sha256"))


def verify_against_receipt(
    membership_path: Path, receipt: dict[str, Any], family_ids: list[str]
) -> dict[str, Any]:
    """Fail-closed rerun path: never regenerate. Only confirm the existing
    private artifact reproduces the frozen algorithm from its own stored
    salt, that every persisted field reproduces from that recomputation
    (nothing is trusted merely because it was persisted), that the receipt's
    full binding context (controlling SHA, bindings, family registry, reseal
    triggers) has not drifted since sealing, and that the resulting
    commitments match the sealed public receipt. Raises AssignmentError on
    any drift.
    """
    stored = load_private_artifact(membership_path)
    require(
        stored.get("algorithm_descriptor_sha256") == ALGORITHM_DESCRIPTOR_SHA256,
        "private artifact algorithm_descriptor_sha256 does not match the frozen descriptor -- refusing",
    )
    salt = bytes.fromhex(stored["salt_hex"])
    recomputed = assign(salt, family_ids)
    require(
        recomputed["membership"] == stored["membership"],
        "private artifact membership does not reproduce from its own stored salt -- "
        "refusing (tampered artifact or a family_ids change without a reseal)",
    )
    require(
        recomputed["heldout_family_ids"] == stored["heldout_family_ids"],
        "private artifact heldout_family_ids does not match recomputed membership -- refusing (tampered artifact)",
    )
    require(
        recomputed["builder_eligible_family_ids"] == stored["builder_eligible_family_ids"],
        "private artifact builder_eligible_family_ids does not match recomputed membership -- "
        "refusing (tampered artifact)",
    )

    current_binding = receipt_binding_sha256(receipt)
    require(
        stored["receipt_binding_sha256"] == current_binding,
        "receipt binding drift: controlling_outcome_sha256, bindings, source_family_registry, or "
        "reseal_required_on no longer match what this private assignment was sealed against -- "
        "refusing (reseal required)",
    )

    summary = public_commitment_summary(salt, recomputed)
    receipt_commitments = _receipt_commitments(receipt)
    require(
        summary["salt_commitment_sha256"] == receipt_commitments["salt_commitment_sha256"],
        "salt_commitment_sha256 drift between the private artifact and the sealed public receipt -- refusing",
    )
    require(
        summary["assignment_commitment_sha256"] == receipt_commitments["assignment_commitment_sha256"],
        "assignment_commitment_sha256 drift between the private artifact and the sealed public receipt -- refusing",
    )
    return summary


def _resolve_generation_salt() -> bytes:
    """Fresh 32-byte random salt, unless overridden for a deterministic test.

    The override is read from ``TEST_SALT_ENV_VAR`` -- an environment
    variable, never a CLI flag -- so the salt is never visible in argv or
    process listings (`ps`, `/proc/<pid>/cmdline`) of the shipped
    entrypoint. Never set this variable in production.
    """
    override = os.environ.get(TEST_SALT_ENV_VAR)
    if override is None:
        return secrets.token_bytes(32)
    salt = bytes.fromhex(override)
    require(len(salt) == 32, f"{TEST_SALT_ENV_VAR} must decode to exactly 32 bytes")
    return salt


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "--receipt: the sealed public receipt JSON to verify a private artifact against, "
            "or to bind a fresh --generate to (default: the tracked V4 A3 seal receipt). "
            "Read-only -- never written by this script.\n\n"
            f"--private-dir: directory for the private membership artifact; must resolve "
            f"lexically inside {PRIVATE_ROOT} (git-ignored). Created mode 0700 if missing "
            f"(default: {DEFAULT_PRIVATE_DIR})."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        default=DEFAULT_RECEIPT,
        help="sealed public receipt JSON to verify against / bind a fresh generation to (read-only)",
    )
    parser.add_argument(
        "--private-dir",
        type=Path,
        default=DEFAULT_PRIVATE_DIR,
        help=f"private artifact directory; must be inside {PRIVATE_ROOT}",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help=(
            "Generate a fresh salt and membership. Refused (fail closed) if a private "
            "artifact already exists at --private-dir -- reruns only verify, never overwrite. "
            "Also refused if --receipt is already sealed with commitments this generation "
            "does not reproduce."
        ),
    )
    args = parser.parse_args(argv)

    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    family_ids = sorted(family["family_id"] for family in receipt["source_family_registry"]["families"])

    private_dir = _absolute_unresolved(args.private_dir)
    _assert_no_symlink_components(private_dir)
    _assert_within_private_root(private_dir, PRIVATE_ROOT)
    membership_path = private_dir / MEMBERSHIP_FILENAME

    if membership_path.exists() or membership_path.is_symlink():
        require(
            not args.generate,
            f"private artifact already exists, refusing to overwrite: {membership_path} "
            "-- fail closed on rerun; omit --generate to verify it instead",
        )
        summary = verify_against_receipt(membership_path, receipt, family_ids)
        print(canonical_json(summary))
        return

    require(
        args.generate,
        "no private artifact found and --generate was not passed -- "
        "refusing to silently create a new salt (fail closed); pass --generate explicitly",
    )

    salt = _resolve_generation_salt()
    result = assign(salt, family_ids)
    summary = public_commitment_summary(salt, result)

    if _receipt_is_sealed(receipt):
        receipt_commitments = _receipt_commitments(receipt)
        require(
            summary["salt_commitment_sha256"] == receipt_commitments["salt_commitment_sha256"]
            and summary["assignment_commitment_sha256"] == receipt_commitments["assignment_commitment_sha256"],
            "--receipt is already sealed with commitments this freshly generated assignment does not "
            "reproduce -- refusing to write a private artifact that would contradict the sealed public "
            "receipt (fail closed); omit --generate to verify the existing sealed receipt instead",
        )

    write_private_artifact(membership_path, salt, result, receipt_binding_sha256(receipt))
    print(canonical_json(summary))


if __name__ == "__main__":
    try:
        main()
    except AssignmentError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
