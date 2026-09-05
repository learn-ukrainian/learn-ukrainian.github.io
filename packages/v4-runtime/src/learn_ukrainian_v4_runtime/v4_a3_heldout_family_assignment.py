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
complete ``source_family_registry``, ``reseal_required_on``,
``access_firewall``, ``temporal_firewall``, ``cycle007_denial``, and
``safety_assertions`` -- via a ``receipt_binding_sha256`` fingerprint stored
in the private artifact at generation time and recomputed from the live
receipt on every verify. Any drift in any of those fields (not just the
commitments) is refused. The access-firewall and Cycle007-denial invariants
are additionally enforced unconditionally, independent of any private
artifact or binding hash -- see ``validate_access_firewall_invariants`` and
``validate_cycle007_denial_invariants``.

Outputs never leave ``batch_state/`` (git-ignored, mode 0700/0600) or the
private operational board (learn-ukrainian-infra-private#622); only counts
and commitments are safe to publish in the tracked public receipt.

``batch_state/`` is resolved against the one shared **primary** checkout
(see ``_discover_primary_root``), never against ``__file__`` of whichever
checkout happens to run this script. A dispatch worktree has its own
gitignored ``batch_state/`` that is not shared with (not a symlink to) the
primary checkout -- a private artifact written relative to the running
worktree's own path is lost the moment that worktree is reaped. This is
exactly how the first V4 A3 membership artifact was lost: ``--generate`` ran
in a dispatch worktree, and the worktree reaper deleted the only copy.
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
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from learn_ukrainian_v4_runtime.provenance import validation_session
from learn_ukrainian_v4_runtime.resources import resource_root

ROOT = resource_root()


PRIMARY_ROOT = Path(".")
PRIVATE_ROOT = PRIMARY_ROOT / "batch_state"
DEFAULT_PRIVATE_DIR = PRIVATE_ROOT / "open-model-data/v4-a3-heldout"
DEFAULT_RECEIPT = (
    ROOT / "data/projects/open_model_data/admission/dataset_v4_a3_heldout_source_family_seal_receipt_v1.json"
)
RECEIPT_SCHEMA = (
    ROOT / "data/projects/open_model_data/contracts/dataset_v4_a3_heldout_source_family_seal_receipt_v1.schema.json"
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


def heldout_target_count(family_count: int) -> int:
    """The `heldout_fraction`/`minimum_heldout_count` half of the frozen formula.

    Deliberately salt-independent: which family lands in the held-out pool is
    salt-dependent, but how many do is fixed by the formula alone. Exposed
    separately so the public ``heldout_count``/``builder_eligible_count`` a
    receipt declares can be independently recomputed from the public
    ``family_count`` -- no salt, and therefore no private artifact, required.
    """
    require(family_count >= 2, "need at least 2 families to hold one out and keep one builder-eligible")
    target = max(1, round(family_count * ALGORITHM_DESCRIPTOR["heldout_fraction"]))
    return min(target, family_count - 1)


def assign(salt: bytes, family_ids: list[str]) -> dict[str, Any]:
    """Apply the frozen ALGORITHM_DESCRIPTOR formula. Pure function of (salt, family_ids)."""
    require(len(salt) == 32, "salt must be exactly 32 bytes")
    require(len(family_ids) == len(set(family_ids)), "family_ids must be unique")
    family_count = len(family_ids)

    ordered = sorted(family_ids, key=lambda fid: (rank_key(salt, fid), fid))
    heldout = set(ordered[: heldout_target_count(family_count)])
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
    artifact binding, the complete family registry, the reseal triggers, and
    -- critically -- the access firewall, temporal firewall, Cycle007
    denial, and safety assertions. A receipt that still carries the same two
    commitment hashes but has drifted in any of these -- a family
    added/removed, a bound artifact swapped, the controlling epic changed,
    a builder role's held-out visibility flipped to true, or a denied
    Cycle007 fingerprint dropped from the list -- must fail verification.
    (A CF probe found exactly this gap: flipping A4's held-out visibility or
    dropping a denied fingerprint still verified, because those sections
    were not part of this context. See also
    ``validate_access_firewall_invariants``/``validate_cycle007_denial_invariants``,
    which enforce the same two invariants unconditionally -- independent of
    whether a private artifact even exists yet to bind against.)
    """
    seal = receipt["heldout_partition_seal"]
    return {
        "controlling_outcome_sha256": receipt["controlling_outcome_sha256"],
        "bindings": receipt["bindings"],
        "source_family_registry": receipt["source_family_registry"],
        "reseal_required_on": seal["reseal_required_on"],
        "access_firewall": receipt["access_firewall"],
        "temporal_firewall": receipt["temporal_firewall"],
        "cycle007_denial": receipt["cycle007_denial"],
        "safety_assertions": receipt["safety_assertions"],
    }


def receipt_binding_sha256(receipt: dict[str, Any]) -> str:
    return sha256_text(canonical_json(receipt_binding_context(receipt)))


# --- independent receipt validation ---------------------------------------
#
# Everything below trusts nothing the receipt merely *declares*: it re-derives
# each fact from a source this script controls (the frozen ALGORITHM_DESCRIPTOR,
# the public family_count, the actual bytes on disk of every bound artifact) and
# compares. A receipt that is schema-conformant and carries commitment hashes
# that happen to match is not enough on its own -- see
# ``verify_against_receipt`` for the salt-bound commitment checks; this is the
# salt-independent half, run unconditionally (both --generate and verify) so a
# corrupted or hand-edited receipt is caught before any private-artifact
# filesystem operation is even attempted.


def _load_receipt_schema() -> dict[str, Any]:
    schema = json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def validate_receipt_schema(receipt: dict[str, Any]) -> None:
    errors = sorted(Draft202012Validator(_load_receipt_schema()).iter_errors(receipt), key=lambda e: list(e.path))
    require(not errors, f"receipt fails schema validation: {errors[0].message}" if errors else "")


def validate_algorithm_metadata(receipt: dict[str, Any]) -> None:
    """Recompute the algorithm descriptor hash from the frozen constants in
    this file and require the receipt's declared metadata -- both the
    individual fields and the ``algorithm_descriptor_sha256`` derived from
    them -- to match exactly. A receipt that declares a different
    ``algorithm_descriptor_sha256`` (or individual fields inconsistent with
    it) must fail here, independent of anything else in the receipt."""
    algorithm = receipt["heldout_partition_seal"]["assignment_algorithm"]
    declared_metadata = {
        "algorithm_id": algorithm.get("algorithm_id"),
        "algorithm_version": algorithm.get("algorithm_version"),
        "identity_dimensions": algorithm.get("identity_dimensions"),
        "content_blind": algorithm.get("content_blind"),
        "formula": algorithm.get("formula"),
        "heldout_fraction": algorithm.get("heldout_fraction"),
        "rounding_rule": algorithm.get("rounding_rule"),
        "minimum_heldout_count": algorithm.get("minimum_heldout_count"),
    }
    require(
        declared_metadata == ALGORITHM_DESCRIPTOR,
        "receipt assignment_algorithm metadata does not match the frozen ALGORITHM_DESCRIPTOR -- refusing",
    )
    require(
        algorithm.get("algorithm_descriptor_sha256") == ALGORITHM_DESCRIPTOR_SHA256,
        "receipt algorithm_descriptor_sha256 does not match the locally recomputed frozen descriptor hash -- refusing",
    )


def actual_family_count(receipt: dict[str, Any]) -> int:
    """The one source of truth for family_count: the number of *unique*
    ``family_id`` values actually present in
    ``source_family_registry.families``.

    Never trust the declared ``source_family_registry.family_count`` /
    ``heldout_partition_seal.family_count`` integers on their own -- a
    not-yet-sealed draft receipt skips schema validation (see
    ``validate_receipt_independently``), so a hand-edited draft can declare
    ``family_count: 9`` while the ``families`` array actually holds 8 (or
    contains a duplicate ``family_id``), and every downstream pool-count
    check would silently use the wrong denominator. This is derived from the
    array itself, not from any declared integer.
    """
    family_ids = [family["family_id"] for family in receipt["source_family_registry"]["families"]]
    require(
        len(family_ids) == len(set(family_ids)),
        "receipt source_family_registry.families contains duplicate family_id values -- refusing",
    )
    return len(family_ids)


def validate_pool_counts(receipt: dict[str, Any]) -> None:
    """Recompute the expected heldout/builder-eligible split size from the
    actual unique ``family_id`` count in ``source_family_registry.families``
    (via ``actual_family_count`` -- never the declared integer fields, which
    can disagree with the array itself) and require every declared count --
    ``source_family_registry.family_count``,
    ``heldout_partition_seal.family_count``, ``heldout_count``, and
    ``builder_eligible_count`` -- to match what that recomputation implies.
    Catches a receipt whose counts were hand-edited (e.g. to hide or inflate
    the held-out pool, or to declare a family_count the families array does
    not actually support) even though the commitment hashes still verify."""
    seal = receipt["heldout_partition_seal"]
    family_count = actual_family_count(receipt)
    require(
        receipt["source_family_registry"]["family_count"] == family_count,
        f"receipt source_family_registry.family_count "
        f"({receipt['source_family_registry']['family_count']}) does not match the actual number of unique "
        f"family_id values in source_family_registry.families ({family_count}) -- refusing",
    )
    require(
        seal["family_count"] == family_count,
        f"receipt heldout_partition_seal.family_count ({seal['family_count']}) does not match the actual "
        f"number of unique family_id values in source_family_registry.families ({family_count}) -- refusing",
    )
    expected_heldout = heldout_target_count(family_count)
    expected_builder_eligible = family_count - expected_heldout
    require(
        seal["heldout_count"] == expected_heldout,
        f"receipt heldout_count ({seal['heldout_count']}) does not match the count recomputed from the frozen "
        f"formula and family_count={family_count} ({expected_heldout}) -- refusing",
    )
    require(
        seal["builder_eligible_count"] == expected_builder_eligible,
        f"receipt builder_eligible_count ({seal['builder_eligible_count']}) does not match the count recomputed "
        f"from the frozen formula and family_count={family_count} ({expected_builder_eligible}) -- refusing",
    )


# Held-out fields a builder-facing role must never have visibility into --
# mirrors heldout_partition_seal's own membership_owner_role concept and the
# access_firewall.forbidden_fields entries in the sealed receipt.
BUILDER_FORBIDDEN_HELDOUT_FIELDS = frozenset(
    {"heldout_family_pool", "heldout_membership_locator", "heldout_fingerprint", "heldout_near_neighbour"}
)


def validate_access_firewall_invariants(receipt: dict[str, Any]) -> None:
    """Independently enforce that no role other than the declared held-out
    owner role (``heldout_partition_seal.membership_owner_role``) can see
    any held-out signal, and that every other role's ``forbidden_fields``
    still lists every held-out field.

    This is unconditional -- it does not rely on ``receipt_binding_sha256``
    drift detection, which only fires on a *rerun* against an existing
    private artifact. A CF probe found that setting a builder role's (e.g.
    A4) held-out visibility to true still verified because access_firewall
    was not part of the binding context; this check refuses that receipt
    outright, regardless of whether any private artifact exists yet.
    """
    owner_role = receipt["heldout_partition_seal"]["membership_owner_role"]
    for entry in receipt["access_firewall"]:
        if entry["role_id"] == owner_role:
            continue
        require(
            not entry["heldout_family_pool_visible"]
            and not entry["heldout_membership_locator_visible"]
            and not entry["heldout_fingerprint_visible"]
            and not entry["heldout_near_neighbour_visible"],
            f"access_firewall role {entry['role_id']!r} is not the held-out owner role ({owner_role!r}) but "
            f"declares held-out visibility -- refusing",
        )
        require(
            set(entry.get("forbidden_fields", [])) >= BUILDER_FORBIDDEN_HELDOUT_FIELDS,
            f"access_firewall role {entry['role_id']!r} does not forbid every held-out field -- refusing",
        )


def validate_cycle007_denial_invariants(receipt: dict[str, Any]) -> None:
    """Independently enforce that the Cycle007 denial is intact: the denial
    itself has not been flipped to permit reuse, and every fingerprint it
    lists is still marked denied.

    Unconditional for the same reason as ``validate_access_firewall_invariants``
    -- a CF probe found that dropping a denied fingerprint (or flipping one
    entry's ``denied`` to false) still verified, because ``cycle007_denial``
    was not part of the binding context.
    """
    denial = receipt["cycle007_denial"]
    require(denial["denied"] is True, "cycle007_denial.denied is not true -- refusing")
    require(denial["adoption_forbidden"] is True, "cycle007_denial.adoption_forbidden is not true -- refusing")
    require(denial["reused_in_v4"] is False, "cycle007_denial.reused_in_v4 is not false -- refusing")
    fingerprints = denial["denied_fingerprints"]
    require(len(fingerprints) > 0, "cycle007_denial.denied_fingerprints is empty -- refusing")
    for entry in fingerprints:
        require(
            entry["denied"] is True,
            f"cycle007_denial fingerprint {entry.get('fingerprint_kind')!r} is not denied -- refusing",
        )


def validate_bindings_hash_to_disk(receipt: dict[str, Any], root: Path) -> None:
    """Independently hash every file named in ``bindings`` and require it to
    match the receipt's declared ``sha256`` -- the declared hash is never
    trusted on its own. Also refuses a bound path that escapes ``root``
    (e.g. an absolute path or a ``..`` traversal) before ever reading it."""
    for name, binding in receipt["bindings"].items():
        bound_path = (root / binding["path"]).resolve()
        require(
            root.resolve() in bound_path.parents or bound_path == root.resolve(),
            f"binding {name!r} path escapes the repository root -- refusing: {binding['path']}",
        )
        require(bound_path.is_file(), f"binding {name!r} does not point at a file: {bound_path}")
        actual_sha256 = hashlib.sha256(bound_path.read_bytes()).hexdigest()
        require(
            actual_sha256 == binding["sha256"],
            f"binding {name!r} on-disk sha256 ({actual_sha256}) does not match the receipt's declared "
            f"sha256 ({binding['sha256']}) for {binding['path']} -- refusing",
        )


@validation_session
def validate_receipt_independently(receipt: dict[str, Any], root: Path = ROOT) -> None:
    """Run every salt-independent check that does not trust a declared field
    at face value: algorithm metadata/hash, pool counts, the access-firewall
    and Cycle007-denial invariants, and on-disk binding hashes always; full
    schema conformance whenever the receipt claims to be sealed
    (``_receipt_is_sealed``, which itself fails closed on a partially-sealed
    receipt -- see its docstring).

    Schema conformance is gated on sealing, not unconditional, because the
    pinned production schema (``RECEIPT_SCHEMA``) models only the final,
    committed artifact -- it requires sha256-pattern commitment fields a
    not-yet-sealed draft receipt does not have yet by design (see
    ``_receipt_is_sealed`` and the ``--generate``-against-unsealed-receipt
    path in ``main``). Once a receipt claims real commitments it must also be
    fully schema-conformant; nothing about that claim is trusted otherwise.

    Called unconditionally in ``main`` -- before --generate, --migrate, or a
    plain verify -- so nothing downstream ever operates against a receipt
    whose declared fields were trusted rather than re-derived."""
    validate_algorithm_metadata(receipt)
    validate_pool_counts(receipt)
    validate_access_firewall_invariants(receipt)
    validate_cycle007_denial_invariants(receipt)
    from learn_ukrainian_v4_runtime.provenance import validate_receipt_bindings

    validate_receipt_bindings(receipt, root, validate_bindings_hash_to_disk)
    if _receipt_is_sealed(receipt):
        validate_receipt_schema(receipt)


# --- filesystem hardening -----------------------------------------------
#
# Mirrors the symlink/no-clobber/fsync discipline used by the other private
# artifact writers in this project (see phase3_heldout_partition.py and
# phase3_cycle007_labeling_guardian.py). A private artifact carrying the
# held-out membership salt must never be silently overwritten, written
# through a symlink, or written outside its intended directory.


def _open_directory_no_symlink(path: Path) -> int:
    """Open ``path`` as a directory file descriptor, refusing if the leaf
    component is (or resolves via a trailing symlink to) anything but a
    real directory.

    Every subsequent operation against this directory's contents is then
    anchored to this fd (``dir_fd=``) rather than to the pathname again --
    closing the classic check-then-act window where the pathname could be
    replaced (e.g. the directory itself swapped for a symlink to somewhere
    else) between an earlier ``lstat``-based check and a later
    open/link/replace against the same path string. ``_assert_no_symlink_components``
    is still run by callers first, as defense in depth against a symlinked
    *ancestor* component; this closes the remaining race on the leaf
    directory itself. Caller is responsible for closing the returned fd.
    """
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
    return os.open(path, flags)


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


def write_new_private_json_artifact(path: Path, payload: dict[str, Any]) -> None:
    """Atomically *create* a private JSON artifact at ``path``. Never overwrites.

    The generic, payload-agnostic half of what was originally
    ``write_private_artifact``: every private artifact this project writes
    under ``batch_state/`` (the held-out membership here, the builder packet
    in ``v4_a3_builder_packet.py``) needs the identical symlink-safe,
    no-clobber, fsync'd-to-disk write discipline -- only the JSON payload
    differs. Callers assemble their own ``payload`` dict and pass it here
    rather than re-implementing this filesystem hardening.

    Uses write-temp -> fsync -> hardlink-into-place -> unlink-temp: the
    final path either does not exist or holds fully-written content (atomic),
    and ``os.link`` raises ``FileExistsError`` if the destination is already
    occupied by any filesystem object -- a regular file, a stale hardlink, or
    a symlink -- so reruns can never clobber a prior artifact (no-clobber).
    Callers must route reruns through their own verify path instead of
    calling this again.

    All of the temp-write/link/unlink/fsync steps are performed relative to
    a single directory file descriptor (see ``_open_directory_no_symlink``)
    opened once at the top, rather than by re-resolving ``private_dir`` as a
    pathname for each step -- closing the window where the directory could
    be replaced (e.g. by a symlink) between an earlier check and a later
    step that still trusted the pathname.
    """
    private_dir = path.parent
    _assert_no_symlink_components(private_dir)
    private_dir.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
    os.chmod(private_dir, PRIVATE_DIR_MODE)
    _assert_no_symlink_components(path)
    _assert_contained(path, private_dir)

    dir_fd = _open_directory_no_symlink(private_dir)
    try:
        try:
            os.stat(path.name, dir_fd=dir_fd, follow_symlinks=False)
            already_exists = True
        except FileNotFoundError:
            already_exists = False
        require(not already_exists, f"private artifact already exists, refusing to overwrite: {path}")

        encoded = (canonical_json(payload) + "\n").encode("utf-8")

        temporary_name = f".{path.name}.{secrets.token_hex(8)}.tmp"
        descriptor = os.open(temporary_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, PRIVATE_FILE_MODE, dir_fd=dir_fd)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                os.fchmod(handle.fileno(), PRIVATE_FILE_MODE)
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary_name, path.name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
            except FileExistsError:
                raise AssignmentError(f"private artifact already exists, refusing to overwrite: {path}") from None
            os.fsync(dir_fd)
        finally:
            with contextlib.suppress(OSError):
                os.unlink(temporary_name, dir_fd=dir_fd)
    finally:
        os.close(dir_fd)


def write_private_artifact(path: Path, salt: bytes, result: dict[str, Any], receipt_binding: str) -> None:
    """Assemble the held-out membership payload and create it via
    ``write_new_private_json_artifact`` (create-only, no-clobber). See that
    function's docstring for the filesystem-hardening discipline this uses.
    """
    payload = {
        "algorithm_id": ALGORITHM_ID,
        "algorithm_descriptor_sha256": ALGORITHM_DESCRIPTOR_SHA256,
        "salt_hex": salt.hex(),
        "membership": result["membership"],
        "heldout_family_ids": result["heldout_family_ids"],
        "builder_eligible_family_ids": result["builder_eligible_family_ids"],
        "receipt_binding_sha256": receipt_binding,
    }
    write_new_private_json_artifact(path, payload)


REQUIRED_ARTIFACT_FIELDS = frozenset(
    {
        "salt_hex",
        "membership",
        "heldout_family_ids",
        "builder_eligible_family_ids",
        "receipt_binding_sha256",
    }
)

# Fields a private artifact written before receipt_binding_sha256 existed
# (parent 0587a233) still has -- everything except that one field. Used only
# by the explicit --migrate path; a plain (non-migrate) load always requires
# the full REQUIRED_ARTIFACT_FIELDS set above.
LEGACY_REQUIRED_ARTIFACT_FIELDS = REQUIRED_ARTIFACT_FIELDS - {"receipt_binding_sha256"}


def load_private_artifact(path: Path, required_fields: frozenset[str] = REQUIRED_ARTIFACT_FIELDS) -> dict[str, Any]:
    """Read the private membership artifact, refusing anything but a plain,
    owner-only-mode regular file reached with no symlink in its path.

    The regular-file and mode checks are run via ``os.fstat`` on the file
    descriptor already opened (with ``O_NOFOLLOW``) for reading -- not via a
    separate ``lstat`` on the pathname beforehand -- so the checks always
    describe exactly the bytes about to be read, with no window between a
    pathname-based check and a later pathname-based open where the file
    could be swapped.

    ``required_fields`` defaults to the full current field set; pass
    ``LEGACY_REQUIRED_ARTIFACT_FIELDS`` to read a pre-receipt_binding_sha256
    artifact (only ever done from the explicit ``--migrate`` path)."""
    _assert_no_symlink_components(path)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        raise AssignmentError(f"private artifact missing: {path}") from None
    except OSError as exc:
        raise AssignmentError(f"private artifact is not a regular file: {path}") from exc

    with os.fdopen(descriptor, "rb") as handle:
        info = os.fstat(handle.fileno())
        require(
            stat.S_ISREG(info.st_mode),
            f"private artifact is not a regular file: {path}",
        )
        require(
            stat.S_IMODE(info.st_mode) == PRIVATE_FILE_MODE,
            f"private artifact has unexpected mode (want {oct(PRIVATE_FILE_MODE)}): {path}",
        )
        try:
            raw = handle.read()
        except OSError as exc:
            raise AssignmentError(f"cannot read private artifact: {path}") from exc
    value = json.loads(raw.decode("utf-8"))
    require(isinstance(value, dict), f"private artifact is not a JSON object: {path}")
    require(required_fields <= value.keys(), f"private artifact missing required fields: {path}")
    return value


def _rewrite_private_artifact(path: Path, payload: dict[str, Any]) -> None:
    """Atomically *replace* an existing private artifact's content in place.

    Unlike ``write_private_artifact`` (create-only, no-clobber), this is the
    one sanctioned path allowed to overwrite a private artifact -- used only
    by ``migrate_private_artifact``, and only after every recomputation and
    commitment check there has already passed. Same write-temp -> fsync ->
    atomic-swap -> fsync-directory discipline as ``write_private_artifact``,
    but swaps via ``os.replace`` (atomic on POSIX) instead of a no-clobber
    ``os.link``, since replacing is exactly what a migration must do. Also
    anchored to a single directory file descriptor throughout, for the same
    TOCTOU reason documented on ``_open_directory_no_symlink``.
    """
    private_dir = path.parent
    _assert_no_symlink_components(private_dir)
    _assert_no_symlink_components(path)
    _assert_contained(path, private_dir)

    dir_fd = _open_directory_no_symlink(private_dir)
    try:
        try:
            info = os.stat(path.name, dir_fd=dir_fd, follow_symlinks=False)
        except FileNotFoundError:
            raise AssignmentError(
                f"private artifact missing or not a regular file, nothing to migrate: {path}"
            ) from None
        require(
            stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode),
            f"private artifact missing or not a regular file, nothing to migrate: {path}",
        )

        encoded = (canonical_json(payload) + "\n").encode("utf-8")
        temporary_name = f".{path.name}.{secrets.token_hex(8)}.tmp"
        descriptor = os.open(temporary_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, PRIVATE_FILE_MODE, dir_fd=dir_fd)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                os.fchmod(handle.fileno(), PRIVATE_FILE_MODE)
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, path.name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
            os.fsync(dir_fd)
        finally:
            with contextlib.suppress(OSError):
                os.unlink(temporary_name, dir_fd=dir_fd)
    finally:
        os.close(dir_fd)


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

    Fails closed if exactly one of the two commitment fields is present: a
    receipt cannot legitimately have a ``salt_commitment_sha256`` without an
    ``assignment_commitment_sha256`` (or vice versa) -- both are written
    together by ``public_commitment_summary`` at generation time. A receipt
    in that state is corrupt or hand-edited, not merely "not yet sealed",
    and must never be silently treated as the latter.
    """
    algorithm = receipt.get("heldout_partition_seal", {}).get("assignment_algorithm", {})
    has_salt_commitment = bool(algorithm.get("salt_commitment_sha256"))
    has_assignment_commitment = bool(algorithm.get("assignment_commitment_sha256"))
    require(
        has_salt_commitment == has_assignment_commitment,
        "receipt carries exactly one of salt_commitment_sha256/assignment_commitment_sha256 -- "
        "a partially sealed receipt is invalid, refusing (fail closed)",
    )
    return has_salt_commitment and has_assignment_commitment


def receipt_is_sealed(receipt: dict[str, Any]) -> bool:
    """Public wrapper around ``_receipt_is_sealed`` for other A3-owned
    modules (e.g. ``v4_a3_builder_packet.py``) that need to refuse issuing a
    builder packet against a receipt that has not actually been sealed yet,
    without reaching into this module's private name."""
    return _receipt_is_sealed(receipt)


def verify_against_receipt(membership_path: Path, receipt: dict[str, Any], family_ids: list[str]) -> dict[str, Any]:
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


def is_legacy_artifact(membership_path: Path) -> bool:
    """True if the artifact at ``membership_path`` predates
    ``receipt_binding_sha256`` (written by parent 0587a233 or earlier).

    Reads with the same relaxed (legacy) required-field set a plain load
    would refuse outright, purely to distinguish "legacy, needs --migrate"
    from "corrupt, missing other fields too" -- it never trusts the content
    beyond that one presence check.
    """
    stored = load_private_artifact(membership_path, required_fields=LEGACY_REQUIRED_ARTIFACT_FIELDS)
    return "receipt_binding_sha256" not in stored


def migrate_private_artifact(membership_path: Path, receipt: dict[str, Any], family_ids: list[str]) -> dict[str, Any]:
    """Explicit, fail-closed upgrade path for a private artifact written
    before ``receipt_binding_sha256`` existed (parent ``0587a233``).

    Never invoked by a plain verify run -- only via ``--migrate``. Runs the
    identical recomputation and commitment checks ``verify_against_receipt``
    runs (membership reproduces from the artifact's own stored salt, the
    persisted derived lists match, and the resulting commitments match the
    sealed public receipt's) before ever touching the file. The one check it
    does *not* run is the ``receipt_binding_sha256`` comparison -- the legacy
    artifact does not have one yet; computing and writing it is exactly what
    this migration does. Only if every recomputation/commitment check passes
    does it rewrite the artifact in place (atomic replace, same private
    mode/dir) to add ``receipt_binding_sha256`` computed from the *current*
    receipt. Membership, salt, and every other field are carried over
    byte-for-byte -- a migration never changes the held-out assignment
    itself, only adds the binding fingerprint that was missing.
    """
    stored = load_private_artifact(membership_path, required_fields=LEGACY_REQUIRED_ARTIFACT_FIELDS)
    require(
        "receipt_binding_sha256" not in stored,
        f"private artifact already carries receipt_binding_sha256 -- nothing to migrate, "
        f"omit --migrate to verify instead: {membership_path}",
    )
    require(
        stored.get("algorithm_descriptor_sha256") == ALGORITHM_DESCRIPTOR_SHA256,
        "private artifact algorithm_descriptor_sha256 does not match the frozen descriptor -- refusing to migrate",
    )
    salt = bytes.fromhex(stored["salt_hex"])
    recomputed = assign(salt, family_ids)
    require(
        recomputed["membership"] == stored["membership"],
        "private artifact membership does not reproduce from its own stored salt -- refusing to migrate "
        "(tampered artifact or a family_ids change without a reseal)",
    )
    require(
        recomputed["heldout_family_ids"] == stored["heldout_family_ids"],
        "private artifact heldout_family_ids does not match recomputed membership -- refusing to migrate "
        "(tampered artifact)",
    )
    require(
        recomputed["builder_eligible_family_ids"] == stored["builder_eligible_family_ids"],
        "private artifact builder_eligible_family_ids does not match recomputed membership -- refusing to migrate "
        "(tampered artifact)",
    )

    summary = public_commitment_summary(salt, recomputed)
    receipt_commitments = _receipt_commitments(receipt)
    require(
        summary["salt_commitment_sha256"] == receipt_commitments["salt_commitment_sha256"],
        "salt_commitment_sha256 drift between the private artifact and the sealed public receipt -- "
        "refusing to migrate",
    )
    require(
        summary["assignment_commitment_sha256"] == receipt_commitments["assignment_commitment_sha256"],
        "assignment_commitment_sha256 drift between the private artifact and the sealed public receipt -- "
        "refusing to migrate",
    )

    payload = {**stored, "receipt_binding_sha256": receipt_binding_sha256(receipt)}
    _rewrite_private_artifact(membership_path, payload)
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
    parser.add_argument(
        "--migrate",
        action="store_true",
        help=(
            "Explicit, fail-closed upgrade for a private artifact written before "
            "receipt_binding_sha256 existed (parent 0587a233): verify-and-rewrite in place, "
            "adding the missing field -- never changes the held-out membership itself. "
            "Refused if no artifact exists at --private-dir, if --generate is also passed, "
            "or if the existing artifact already carries receipt_binding_sha256 (nothing to migrate)."
        ),
    )
    args = parser.parse_args(argv)
    require(not (args.generate and args.migrate), "--generate and --migrate are mutually exclusive")

    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    family_ids = sorted(family["family_id"] for family in receipt["source_family_registry"]["families"])
    # Independent validation: re-derive every algorithm-metadata/count/binding
    # fact from a source this script controls rather than trusting the
    # receipt's declared fields -- see validate_receipt_independently. Runs
    # before any private-artifact filesystem operation, for --generate,
    # --migrate, and plain verify alike.
    validate_receipt_independently(receipt)

    private_dir = _absolute_unresolved(args.private_dir)
    _assert_no_symlink_components(private_dir)
    _assert_within_private_root(private_dir, PRIVATE_ROOT)
    membership_path = private_dir / MEMBERSHIP_FILENAME

    if args.migrate:
        require(
            membership_path.exists() or membership_path.is_symlink(),
            f"no private artifact found to migrate: {membership_path}",
        )
        summary = migrate_private_artifact(membership_path, receipt, family_ids)
        print(canonical_json(summary))
        return

    if membership_path.exists() or membership_path.is_symlink():
        require(
            not args.generate,
            f"private artifact already exists, refusing to overwrite: {membership_path} "
            "-- fail closed on rerun; omit --generate to verify it instead",
        )
        require(
            not is_legacy_artifact(membership_path),
            f"private artifact predates receipt_binding_sha256 (written before the reseal-drift fix in "
            f"parent 0587a233) -- pass --migrate to verify and upgrade it in place (fail-closed, the "
            f"held-out membership itself is never changed); a plain verify cannot proceed until it is "
            f"migrated: {membership_path}",
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
