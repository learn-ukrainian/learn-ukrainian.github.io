#!/usr/bin/env python3
"""V4 A3 candidate-family floor (Invariant D1): the fix for the disclosure
leak a per-slot positive completion would otherwise create.

With a small, fully public ``source_family_registry`` and a public
``heldout_count``, a public manifest transition to ``ASSIGNED`` for a
stratum whose ``supporting_existing_source_unit_ids`` names members of only
one family already tells a reader, by elimination, that this family is
builder-eligible -- a later per-slot completion for that stratum would add
no further information, but the *transition itself* already leaked it. The
fix is structural, not a disclosure-timing rule: a stratum may transition
its manifest ``assignment_state`` to ``ASSIGNED`` only if the number of
*distinct* families among its supporting units is at least
``heldout_count + 1`` -- so a reader can never narrow the held-out pool to
a single family from a stratum's supporting-unit list alone.

This module owns exactly that one check. It is deliberately independent of
``v4_stage_evidence.stratum_eligibility`` (which stays a pure function of
A2 + the manifest, with no family-registry input) -- D1 is enforced once,
at the point a stratum is allowed to transition to ``ASSIGNED`` (inside the
A3 reissue/reseal path that would drive such a transition), not re-derived
downstream at every consuming stage. Once a stratum is prerequisite-
eligible (manifest-assigned), D1 has therefore already been proven for it;
A7-A9 never need to re-open the A3 family registry to trust that.

Pure, offline, deterministic -- no salt, no held-out membership, no source
text. Every input here is already public (the A2 coverage map and the A3
seal receipt's own ``source_family_registry``/``heldout_count``).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class CandidateFamilyFloorError(ValueError):
    """A stratum's supporting-unit family composition does not meet D1."""


def require(condition: bool, message: str, error_cls: type[Exception] = CandidateFamilyFloorError) -> None:
    if not condition:
        raise error_cls(message)


def unit_to_family_map(family_registry: dict[str, Any]) -> dict[str, str]:
    """``source_unit_id -> family_id`` from an A3 seal receipt's own
    ``source_family_registry.families`` -- refuses if any unit is claimed
    by more than one family (a same-family-never-split violation)."""
    mapping: dict[str, str] = {}
    for family in family_registry["families"]:
        for unit_id in family["member_source_unit_ids"]:
            require(unit_id not in mapping, f"source_unit_id {unit_id!r} claimed by more than one family -- refusing")
            mapping[unit_id] = family["family_id"]
    return mapping


def distinct_supporting_family_ids(supporting_source_unit_ids: list[str], family_registry: dict[str, Any]) -> set[str]:
    """The distinct family_ids among a stratum's own
    ``supporting_existing_source_unit_ids`` -- refuses if any supporting
    unit is not a member of any registered family (an unregistered unit
    can never legitimately support a stratum's ASSIGNED transition)."""
    mapping = unit_to_family_map(family_registry)
    families: set[str] = set()
    for unit_id in supporting_source_unit_ids:
        require(unit_id in mapping, f"supporting_existing_source_unit_id {unit_id!r} is not a member of any registered family -- refusing")
        families.add(mapping[unit_id])
    return families


def candidate_family_floor_met(supporting_source_unit_ids: list[str], family_registry: dict[str, Any], heldout_count: int) -> bool:
    """True only if the distinct-family count among ``supporting_source_unit_ids``
    is at least ``heldout_count + 1`` -- Invariant D1."""
    require(heldout_count >= 1, "heldout_count must be at least 1")
    families = distinct_supporting_family_ids(supporting_source_unit_ids, family_registry)
    return len(families) >= heldout_count + 1


def validate_candidate_family_floor(stratum: str, coverage_entry: dict[str, Any], family_registry: dict[str, Any], heldout_count: int) -> None:
    """Refuse (fail closed) unless ``coverage_entry`` (an A2
    ``stratum_coverage_map`` entry) meets Invariant D1. This is the one
    place a stratum's manifest ``assignment_state`` may legitimately be
    driven to ``ASSIGNED`` -- callers (the A3 reissue path) must run this
    before ever writing that transition, never after."""
    require(coverage_entry["stratum"] == stratum, f"coverage_entry stratum {coverage_entry.get('stratum')!r} does not match {stratum!r} -- refusing")
    supporting = coverage_entry["supporting_existing_source_unit_ids"]
    require(
        candidate_family_floor_met(supporting, family_registry, heldout_count),
        f"stratum {stratum!r} candidate-family floor not met: needs at least {heldout_count + 1} distinct "
        f"supporting families (heldout_count={heldout_count}) but supporting_existing_source_unit_ids "
        f"resolves to fewer -- refusing the ASSIGNED transition (Invariant D1)",
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--stratum", required=True, help="stratum name being checked, e.g. standard_correct")
    parser.add_argument("--coverage-entry", required=True, type=Path, help="JSON file: one A2 stratum_coverage_map entry")
    parser.add_argument("--family-registry", required=True, type=Path, help="JSON file: an A3 seal receipt's source_family_registry")
    parser.add_argument("--heldout-count", required=True, type=int)
    args = parser.parse_args(argv)

    coverage_entry = json.loads(args.coverage_entry.read_text(encoding="utf-8"))
    family_registry = json.loads(args.family_registry.read_text(encoding="utf-8"))
    try:
        validate_candidate_family_floor(args.stratum, coverage_entry, family_registry, args.heldout_count)
    except CandidateFamilyFloorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps({"stratum": args.stratum, "candidate_family_floor_met": True}))


if __name__ == "__main__":
    main()
