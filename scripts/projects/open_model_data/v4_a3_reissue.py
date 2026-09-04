#!/usr/bin/env python3
"""V4 A3 membership-preserving reissue for the held-out family-assignment
private artifact.

Deliberately a **separate module**, never an edit to
``v4_a3_heldout_family_assignment.py`` itself: that module's own file
bytes are pinned as an ``artifact_binding`` entry
(``bindings.assignment_algorithm_implementation``) inside the sealed,
checked-in, real-private-salt-bound production seal receipt
(``dataset_v4_a3_heldout_source_family_seal_receipt_v1.json``). Any edit to
that file changes its sha256 and breaks that binding for the one real
sealed receipt this project has -- a break this module (owned by a
dispatch worktree that must never open the real private salt or migrate
the real private artifact) has no way to repair. Reissue logic therefore
lives here instead, calling into ``v4_a3_heldout_family_assignment``'s
existing public API (never editing it) plus its filesystem-hardening
internals it does not yet expose publicly for this exact operation
(``_rewrite_private_artifact`` -- the same atomic, symlink-safe,
fsync'd-to-disk replace primitive ``migrate_private_artifact`` already
uses for its own one-time schema upgrade).

Distinct from **--migrate** (a one-time schema upgrade for a pre-existing
artifact) and from a **reseal** (a real membership/registry change, which
invalidates A4-A9 and bumps the evaluation version -- see the binding
advisor decision's RESEAL table). A reissue proves, via explicit equality
checks, that the three core commitments
(``algorithm_descriptor_sha256``/``salt_commitment_sha256``/
``assignment_commitment_sha256``) and the full ``source_family_registry``
are byte-for-byte unchanged between an old and a new receipt state, and
then only rebinds the private artifact's own ``receipt_binding_sha256`` to
the new receipt's current content. It never touches the salt or the
membership itself.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts.projects.open_model_data import v4_a3_heldout_family_assignment as heldout

canonical_json = heldout.canonical_json


class ReissueError(ValueError):
    """A membership-preserving reissue cannot proceed safely."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReissueError(message)


def reissue_private_artifact(
    membership_path: Path,
    old_receipt: dict[str, Any],
    new_receipt: dict[str, Any],
    family_ids: list[str],
    *,
    expect_salt_commitment: str | None = None,
    expect_assignment_commitment: str | None = None,
) -> dict[str, Any]:
    """Membership-preserving reissue: rebind the private artifact's
    ``receipt_binding_sha256`` to ``new_receipt``'s current content, having
    first proven -- via explicit equality checks, never a PR-body claim --
    that the algorithm descriptor, salt commitment, assignment commitment,
    and the full ``source_family_registry`` are byte-for-byte unchanged
    between ``old_receipt`` and ``new_receipt``. Any drift in any of those
    is a reseal, not a reissue, and this function refuses it (fail closed).
    Never regenerates membership; never touches the salt.
    """
    heldout.validate_receipt_independently(old_receipt)
    heldout.validate_receipt_independently(new_receipt)
    require(heldout.receipt_is_sealed(old_receipt), "reissue requires the old receipt to already be sealed")
    require(heldout.receipt_is_sealed(new_receipt), "reissue requires the new receipt to already be sealed")

    old_algorithm = old_receipt["heldout_partition_seal"]["assignment_algorithm"]
    new_algorithm = new_receipt["heldout_partition_seal"]["assignment_algorithm"]
    for field in ("algorithm_descriptor_sha256", "salt_commitment_sha256", "assignment_commitment_sha256"):
        require(
            old_algorithm[field] == new_algorithm[field],
            f"reissue changed {field} between the old and new receipt -- this is a reseal, not a reissue -- refusing",
        )
    require(
        canonical_json(old_receipt["source_family_registry"]) == canonical_json(new_receipt["source_family_registry"]),
        "reissue changed source_family_registry between the old and new receipt -- this is a reseal, not a reissue -- refusing",
    )
    if expect_salt_commitment is not None:
        require(
            new_algorithm["salt_commitment_sha256"] == expect_salt_commitment,
            "new receipt salt_commitment_sha256 does not match --expect-salt-commitment -- refusing",
        )
    if expect_assignment_commitment is not None:
        require(
            new_algorithm["assignment_commitment_sha256"] == expect_assignment_commitment,
            "new receipt assignment_commitment_sha256 does not match --expect-assignment-commitment -- refusing",
        )

    # Sanity: the existing private artifact must already reproduce against
    # the OLD receipt before this function ever rebinds it to the new one.
    heldout.verify_against_receipt(membership_path, old_receipt, family_ids)

    stored = heldout.load_private_artifact(membership_path)
    new_binding = heldout.receipt_binding_sha256(new_receipt)
    payload = {**stored, "receipt_binding_sha256": new_binding}
    # `_rewrite_private_artifact` is heldout's private atomic-replace
    # primitive -- see module docstring for why this cross-module reuse is
    # sanctioned rather than a public wrapper added to that pinned file.
    heldout._rewrite_private_artifact(membership_path, payload)

    salt = bytes.fromhex(stored["salt_hex"])
    recomputed = heldout.assign(salt, family_ids)
    return heldout.public_commitment_summary(salt, recomputed)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--old-receipt", type=Path, default=heldout.DEFAULT_RECEIPT, help="the currently sealed receipt JSON (read-only)")
    parser.add_argument("--new-receipt", type=Path, required=True, help="the new sealed receipt JSON to reissue the private artifact's binding against")
    parser.add_argument("--private-dir", type=Path, default=heldout.DEFAULT_PRIVATE_DIR, help=f"private artifact directory; must be inside {heldout.PRIVATE_ROOT}")
    parser.add_argument("--expect-salt-commitment", help="assert the new receipt's salt_commitment_sha256 equals this value")
    parser.add_argument("--expect-assignment-commitment", help="assert the new receipt's assignment_commitment_sha256 equals this value")
    args = parser.parse_args(argv)

    old_receipt = json.loads(args.old_receipt.read_text(encoding="utf-8"))
    new_receipt = json.loads(args.new_receipt.read_text(encoding="utf-8"))
    family_ids = sorted(family["family_id"] for family in old_receipt["source_family_registry"]["families"])

    private_dir = heldout._absolute_unresolved(args.private_dir)
    heldout._assert_no_symlink_components(private_dir)
    heldout._assert_within_private_root(private_dir, heldout.PRIVATE_ROOT)
    membership_path = private_dir / heldout.MEMBERSHIP_FILENAME

    try:
        summary = reissue_private_artifact(
            membership_path,
            old_receipt,
            new_receipt,
            family_ids,
            expect_salt_commitment=args.expect_salt_commitment,
            expect_assignment_commitment=args.expect_assignment_commitment,
        )
    except (ReissueError, heldout.AssignmentError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(canonical_json(summary))


if __name__ == "__main__":
    main()
