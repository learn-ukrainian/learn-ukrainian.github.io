#!/usr/bin/env python3
"""V4 A3 split/near-duplicate safety checker: the one place a candidate
independently-authored row is compared against *every* candidate-family's
private reference text -- never just the one private-ledger-bound unit --
before it may be recorded as split-duplicate-safe.

Owned by A3 (the held-out/family-boundary role), reusing (never
reimplementing) the already-sealed, pinned
``correction_protection_near_duplicate_policy_v1.json`` policy and its
deterministic implementation (``phase3_near_duplicate.py``). This module
adds no new similarity algorithm -- it only decides the *scope* of the
comparison (every candidate unit's text, not one locator) and produces a
receipt that carries no source locator at all: ``receipt_id`` is a
deterministic hash of the candidate's own fingerprint, the policy
fingerprint, and the reference-set size, never a unit id, family id, or
excerpt.

This module never opens real corpus text and is never wired to production
in this PR (no real row exists to check) -- it is exercised only against
synthetic reference texts supplied directly by a caller (tests, or later a
private extraction ledger neither owned nor opened here). Running it for
real would happen privately, on the VPS, against all nine units' private
text (design packet FIRST_PR note) -- that wiring is explicitly out of
scope for this PR.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from learn_ukrainian_v4_runtime import phase3_near_duplicate as near_duplicate

RECEIPT_ID_DOMAIN = "v4-a3-split-duplicate-safety-v1"


class SplitDuplicateCheckError(ValueError):
    """The split-duplicate safety check cannot proceed safely."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SplitDuplicateCheckError(message)


def _receipt_id(candidate_fingerprint: str, policy_fingerprint: str, reference_count: int) -> str:
    """Deterministic, source-locator-free receipt id: a hash of the
    candidate's own fingerprint, the policy fingerprint, and how many
    reference texts were checked against -- never a unit id, family id, or
    any per-reference identifier."""
    payload = f"{RECEIPT_ID_DOMAIN}\x00{candidate_fingerprint}\x00{policy_fingerprint}\x00{reference_count}"
    return f"split-duplicate:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def check_split_duplicate_safety(
    candidate_text: str,
    reference_texts: dict[str, str],
    *,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare ``candidate_text`` against *every* text in ``reference_texts``
    (keyed by an opaque, caller-chosen label this function never echoes
    back) at the pinned near-duplicate policy's "span" scope. ``passed`` is
    true only if none of them classify as exact or near. Fails closed: an
    empty ``reference_texts`` mapping is refused outright -- a split-
    duplicate check that compared against nothing would be a false
    positive-pass, never a legitimate all-clear."""
    require(isinstance(candidate_text, str) and candidate_text, "candidate_text must be a nonempty string")
    require(
        isinstance(reference_texts, dict) and reference_texts,
        "reference_texts must be a nonempty mapping -- refusing a check against zero references",
    )
    active_policy = policy if policy is not None else near_duplicate.load_policy()
    require(
        active_policy.get("policy_fingerprint_sha256") == near_duplicate.policy_fingerprint(active_policy),
        "near-duplicate policy fingerprint drift -- refusing",
    )
    policy_fingerprint = active_policy["policy_fingerprint_sha256"]

    duplicate_against: list[str] = []
    for label, reference_text in reference_texts.items():
        require(isinstance(label, str) and label, "reference_texts keys must be nonempty strings")
        require(
            isinstance(reference_text, str) and reference_text,
            f"reference text for {label!r} must be a nonempty string",
        )
        result = near_duplicate.classify_texts(candidate_text, reference_text, scope="span", policy=active_policy)
        if result.duplicate:
            duplicate_against.append(label)

    candidate_fingerprint = near_duplicate.fingerprint(candidate_text).exact_fingerprint
    passed = not duplicate_against
    return {
        "passed": passed,
        "receipt_id": _receipt_id(candidate_fingerprint, policy_fingerprint, len(reference_texts)),
        "policy_sha256": policy_fingerprint,
        "references_checked": len(reference_texts),
        "duplicate_reference_count": len(duplicate_against),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--payload",
        required=True,
        type=Path,
        help='JSON file: {"candidate_text": str, "reference_texts": {label: text, ...}} -- synthetic test data only, never real corpus text.',
    )
    args = parser.parse_args(argv)
    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    try:
        result = check_split_duplicate_safety(payload["candidate_text"], payload["reference_texts"])
    except SplitDuplicateCheckError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps({k: result[k] for k in ("passed", "receipt_id", "policy_sha256")}))


if __name__ == "__main__":
    main()
