#!/usr/bin/env python3
"""V4 A3 Invariant-D1 transition validator: the one deterministic check that
must run at every point a manifest stratum's ``ASSIGNED`` state -- or a
completion claiming a row inside that stratum -- is trusted, not only inside
the A3 reissue path (PR #7662 repair 4, blocking repair C -- designated-
advisor ``GO_REPAIR``).

Before this module existed, the candidate-family floor (Invariant D1, see
``v4_a3_candidate_family_floor.py``) ran only inside
``v4_a3_reissue.reissue_private_artifact``. A manifest could be edited
directly to ``ASSIGNED`` without ever calling reissue, and A7 never
re-checked D1 at all -- ``v4_a7_original_row_factory.check_factory_gate``,
``v4_a7_private_ledger.construct_completion``, and
``v4_a7_private_ledger.verify_private_replay`` all trusted the manifest's
own ``assignment_state`` at face value.

This module owns the one shared, deterministic implementation --
``validate_manifest_meets_d1`` -- over the tracked manifest, A2's own
coverage receipt, and the *public* A3 seal receipt (never a caller-supplied
family registry). ``v4_a3_reissue.py`` and every A7 load-bearing entrypoint
(``check_factory_gate``, ``construct_completion``, ``verify_private_replay``)
call this same function, unconditionally, rather than each re-deriving its
own copy. No private membership, salt, or source text is required -- the
seal receipt's own ``source_family_registry``/``heldout_count`` are already
public.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts.projects.open_model_data import v4_a3_candidate_family_floor as floor
from scripts.projects.open_model_data import v4_a3_heldout_family_assignment as heldout
from scripts.projects.open_model_data import v4_stage_evidence as ev

SEAL_RECEIPT_RELATIVE = "data/projects/open_model_data/admission/dataset_v4_a3_heldout_source_family_seal_receipt_v1.json"
SEAL_RECEIPT_SCHEMA_VERSION = "dataset_v4_a3_heldout_source_family_seal_receipt_v1"


class D1TransitionError(ValueError):
    """A manifest/A2/A3 state does not meet Invariant D1 (candidate-family floor)."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise D1TransitionError(message)


def _coverage_entry_for_stratum(a2_receipt: dict[str, Any], stratum: str) -> dict[str, Any] | None:
    for entry in a2_receipt["stratum_coverage_map"]:
        if entry["stratum"] == stratum:
            return entry
    return None


def validate_manifest_meets_d1(manifest: dict[str, Any], a2_receipt: dict[str, Any], seal_receipt: dict[str, Any]) -> None:
    """Fail-closed D1 check over every manifest stratum currently
    ``ASSIGNED``, against ``seal_receipt``'s own public
    ``source_family_registry``/``heldout_count`` -- never a caller-supplied
    registry. Requires ``seal_receipt`` to independently validate and be
    sealed first (an unsealed, tampered, or malformed receipt can never
    satisfy D1). Refuses on a missing/mismatched A2 coverage entry, an
    unregistered supporting unit, or fewer than ``heldout_count + 1``
    distinct supporting families for any ``ASSIGNED`` stratum. An unassigned
    stratum is never checked and never blocks."""
    require(isinstance(manifest, dict) and isinstance(manifest.get("slot_series"), list), "manifest is malformed -- refusing")
    require(isinstance(a2_receipt, dict) and isinstance(a2_receipt.get("stratum_coverage_map"), list), "A2 receipt is malformed -- refusing")
    require(isinstance(seal_receipt, dict), "A3 seal receipt is malformed -- refusing")
    try:
        heldout.validate_receipt_independently(seal_receipt)
    except heldout.AssignmentError as exc:
        raise D1TransitionError(f"A3 seal receipt failed independent validation -- refusing: {exc}") from exc
    require(heldout.receipt_is_sealed(seal_receipt), "A3 seal receipt is not sealed -- refusing")

    family_registry = seal_receipt["source_family_registry"]
    heldout_count = seal_receipt["heldout_partition_seal"]["heldout_count"]
    for series in manifest["slot_series"]:
        require(isinstance(series.get("stratum"), str) and series["stratum"], "manifest slot_series entry is missing a stratum -- refusing (malformed slot mapping)")
        if series.get("assignment_state") != "ASSIGNED":
            continue
        stratum = series["stratum"]
        coverage_entry = _coverage_entry_for_stratum(a2_receipt, stratum)
        require(coverage_entry is not None, f"manifest stratum {stratum!r} is ASSIGNED but has no matching A2 stratum_coverage_map entry -- refusing")
        try:
            floor.validate_candidate_family_floor(stratum, coverage_entry, family_registry, heldout_count)
        except floor.CandidateFamilyFloorError as exc:
            raise D1TransitionError(str(exc)) from exc


def stratum_for_slot_id(manifest: dict[str, Any], slot_id: str) -> str:
    """The one sanctioned way to derive a slot's stratum -- from the frozen
    manifest's own ``slot_series``, never a caller assertion. Fails closed
    if ``slot_id`` is not a member of any manifest stratum."""
    for stratum_entry in ev.frozen_slot_strata(manifest):
        if slot_id in stratum_entry["slot_ids"]:
            return stratum_entry["stratum"]
    raise D1TransitionError(f"slot_id {slot_id!r} is not a member of any manifest stratum -- refusing")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", required=True, type=Path, help="the frozen 100-slot pilot manifest JSON")
    parser.add_argument("--a2-receipt", required=True, type=Path, help="A2's public stratum_coverage_map receipt JSON")
    parser.add_argument("--seal-receipt", required=True, type=Path, help="the public A3 heldout-source-family seal receipt JSON")
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    a2_receipt = json.loads(args.a2_receipt.read_text(encoding="utf-8"))
    seal_receipt = json.loads(args.seal_receipt.read_text(encoding="utf-8"))
    try:
        validate_manifest_meets_d1(manifest, a2_receipt, seal_receipt)
    except D1TransitionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps({"d1_validated": True}))


if __name__ == "__main__":
    main()
