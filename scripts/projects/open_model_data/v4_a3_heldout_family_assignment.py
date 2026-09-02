#!/usr/bin/env python3
"""V4 A3 held-out source-family assignment: frozen, salt-keyed, content-blind.

Deterministic given ``(private_salt, family_ids)``: produces a private-only
membership mapping (``family_id -> pool``) plus a small set of public-safe
commitments (counts and one-way SHA-256 commitments, never the salt or the
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

Outputs never leave ``batch_state/`` (git-ignored, mode 0700/0600) or the
private operational board (learn-ukrainian-infra-private#622); only counts
and commitments are safe to publish in the tracked public receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PRIVATE_DIR = ROOT / "batch_state/open-model-data/v4-a3-heldout"
DEFAULT_RECEIPT = (
    ROOT / "data/projects/open_model_data/admission/dataset_v4_a3_heldout_source_family_seal_receipt_v1.json"
)

ALGORITHM_ID = "v4-a3-hmac-sha256-family-rank-split-v1"
ALGORITHM_VERSION = "v1"

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
    require(len(salt) >= 16, "salt must be at least 16 bytes")
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


def assignment_commitment_sha256(membership: dict[str, str]) -> str:
    return sha256_text(canonical_json(membership))


def write_private_artifact(path: Path, salt: bytes, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    payload = {
        "algorithm_id": ALGORITHM_ID,
        "algorithm_descriptor_sha256": ALGORITHM_DESCRIPTOR_SHA256,
        "salt_hex": salt.hex(),
        "membership": result["membership"],
        "heldout_family_ids": result["heldout_family_ids"],
        "builder_eligible_family_ids": result["builder_eligible_family_ids"],
    }
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


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
        "assignment_commitment_sha256": assignment_commitment_sha256(result["membership"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--private-dir", type=Path, default=DEFAULT_PRIVATE_DIR)
    parser.add_argument(
        "--salt-hex",
        help="use this hex-encoded salt instead of generating a fresh one (deterministic re-runs / tests only)",
    )
    args = parser.parse_args()

    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    family_ids = sorted(family["family_id"] for family in receipt["source_family_registry"]["families"])

    salt = bytes.fromhex(args.salt_hex) if args.salt_hex else secrets.token_bytes(32)
    result = assign(salt, family_ids)

    write_private_artifact(args.private_dir / "v4_a3_heldout_membership_v1.json", salt, result)
    print(canonical_json(public_commitment_summary(salt, result)))


if __name__ == "__main__":
    main()
