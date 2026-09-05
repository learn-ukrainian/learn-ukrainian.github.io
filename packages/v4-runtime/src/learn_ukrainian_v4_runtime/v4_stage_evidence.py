#!/usr/bin/env python3
"""Shared per-stage prerequisite-eligibility / positive-completion / residual
model for V4 A6-A9 and the per-slot private factory companion.

PR #7654 repair cycle 2 (``batch_state/tasks/design-7654-partial-stage-
evidence.result``, RECOMMENDATION: A). Cycle 1's per-slot fix (commits
``a6d8d99b98``..``a5e053454d``) removed the cross-stratum global-AND gate but
left a second, deeper bug: a slot's readiness was derived from A2 rights and
manifest assignment *metadata* plus the *absence* of that slot from an
upstream stage's own residual list. Absence is never completion evidence --
A6's own residual builder unconditionally lists every one of the 100 frozen
slots as unresolved regardless of gate state, so nothing in production could
ever have produced a false positive through that specific path, but the
mechanism itself was unsound: it could never represent a stage that had
genuinely done real per-slot work, only a stage that had not yet been asked
to. Cross-family review (2026-09-04) confirmed this with two P1s: (1) the
only way to observe a "ready" slot was to delete upstream residuals and
monkeypatch the upstream validator in a test, never through any real
production path; (2) the schemas hard-required exactly 100 residual items,
so a genuinely resolved stratum could not even be represented without
raising or failing schema validation.

This module is the single owner of the fix: **per-slot prerequisite
eligibility is not stage completion.**

* **Eligibility** answers "can this stratum's slots be worked on at all?" --
  a pure function of A2's own ``stratum_coverage_map``/``residuals`` and the
  frozen manifest's own per-stratum ``assignment_state``. It has nothing to
  do with any A6-A9 stage's own work and is reported per stratum (eight
  entries), because A2 and the manifest never publish anything finer.
* **Completion** answers "did *this stage* -- and, for A7-A9, every upstream
  stage -- do its own real, positively-evidenced work for this slot?". It is
  never inferred from a slot's absence from a residual list. It is read only
  from a stage's own typed, validator-owned completion records
  (``aN_completions``), which every builder in this repo leaves empty today,
  because no stage has an execution mechanism yet (design packet follow-up
  F2: three decisions -- an A7-requires-A6 policy, a disclosure-timing
  policy, and a real per-slot execution/private-ledger design -- none of
  which this PR makes or needs to make).
* **Residual** at a stage is the complement of completion over the full
  100-slot frozen denominator -- never over just the eligible slots, so a
  forgotten slot can never silently vanish from either list. Today,
  completion is always empty, so residual is always all 100, exactly
  matching every checked-in production receipt before and after this
  module -- this is a mechanism fix, not a behavior change.

Every stage-facing function here is a pure function of public artifacts
(never opens ``batch_state/`` or A3's held-out membership) and takes an
explicit ``error_cls`` so each caller keeps raising its own module's
existing exception type.
"""

from __future__ import annotations

from typing import Any

# --- gate-level reason codes (blocked_reason_code) ---------------------------
#
# A small, ordered enum -- never a per-stage variant of the same idea. A
# caller checks these in order; the first applicable one wins.
REASON_UPSTREAM_RECEIPT_INVALID = "upstream_receipt_invalid"
REASON_NO_SLOT_ELIGIBLE = "no_slot_prerequisite_eligible"
REASON_ELIGIBLE_AWAITING_UPSTREAM_COMPLETION = "eligible_slots_awaiting_upstream_stage_completion"
REASON_ELIGIBLE_AWAITING_STAGE_EXECUTION = "eligible_slots_awaiting_this_stage_execution"
REASON_PARTIAL_COMPLETION_RESIDUAL = "partial_completion_blocked_with_residuals"

# --- per-slot residual reason codes (each aN_residuals[].reason_code) -------
#
# A2's own stratum blocker, reused unchanged -- this module never invents a
# fourth alongside these three (see ``A2_REASON_TO_RESIDUAL_REASON`` below).
REASON_RIGHTS_UNKNOWN = "rights_unknown"
REASON_SOURCE_INCOMPLETE = "source_incomplete"
REASON_INDEPENDENCE_UNAVAILABLE = "independence_unavailable"
# The one new per-slot residual reason this module adds: a stratum *is*
# prerequisite-eligible (A2 rights resolved and manifest-assigned) but this
# stage (or an upstream one) has not yet produced positive completion
# evidence for it. Never reachable against today's real production A2
# receipt (every stratum still carries a residual), but required for a
# truthful synthetic partial-resolution state, and for any future real one.
REASON_STAGE_COMPLETION_NOT_YET_AVAILABLE = "stage_completion_not_yet_available"

A2_REASON_TO_RESIDUAL_REASON = {
    "rights_unknown": REASON_RIGHTS_UNKNOWN,
    "source_incomplete": REASON_SOURCE_INCOMPLETE,
    "coverage_blocked": REASON_INDEPENDENCE_UNAVAILABLE,
}

RESIDUAL_REASON_CODES = frozenset(
    {
        REASON_RIGHTS_UNKNOWN,
        REASON_SOURCE_INCOMPLETE,
        REASON_INDEPENDENCE_UNAVAILABLE,
        REASON_STAGE_COMPLETION_NOT_YET_AVAILABLE,
    }
)

# A2's own marker for "this stratum's coverage entry legitimately carries no
# residual id" -- the one state a coverage entry with an empty
# ``residual_ids`` list may declare. Anything else with an empty
# ``residual_ids`` list is drift, never a silent pass (see
# ``stratum_eligibility`` below).
A2_RESOLVED_COVERAGE_STATE = "resolved"


def require(condition: bool, message: str, error_cls: type[Exception] = ValueError) -> None:
    if not condition:
        raise error_cls(message)


# --- frozen 100-slot denominator (public, manifest-only) --------------------
#
# Moved here (out of v4_a6_blind_arena) so every stage -- including A6 itself
# -- depends on one shared, non-circular home for this math instead of a
# fragile ``a9.a8.a7.a6.frozen_slot_strata`` daisy-chain.


def slot_ids_for_series(series: dict[str, Any]) -> list[str]:
    return [
        f"{series['id_prefix']}-{number:03d}" for number in range(series["start"], series["start"] + series["count"])
    ]


def frozen_slot_strata(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """One entry per manifest ``slot_series`` item, in manifest order --
    matches ``tests/test_open_model_dataset_v4_pilot_slots.py``'s own
    ``_slot_ids`` formula exactly, so the two can never silently diverge."""
    return [
        {
            "stratum": series["stratum"],
            "id_prefix": series["id_prefix"],
            "count": series["count"],
            "assignment_state": series["assignment_state"],
            "slot_ids": slot_ids_for_series(series),
        }
        for series in manifest["slot_series"]
    ]


def all_frozen_slot_ids(manifest: dict[str, Any]) -> list[str]:
    return [slot_id for stratum in frozen_slot_strata(manifest) for slot_id in stratum["slot_ids"]]


# --- prerequisite eligibility (public, per stratum, never per-slot) --------


def stratum_eligibility(
    manifest: dict[str, Any], a2_receipt: dict[str, Any], error_cls: type[Exception] = ValueError
) -> list[dict[str, Any]]:
    """One record per manifest stratum (eight total, never per slot -- A2 and
    the frozen manifest never publish anything finer). Each record is:
    ``{"stratum", "rights_resolved", "assigned", "prerequisite_eligible",
    "slot_ids"}`` -- ``slot_ids`` is carried for internal set computation
    only; callers building a public receipt must strip it (the manifest's
    own ``frozen_slot_denominator.strata`` already publishes it once).

    Fails closed (never silently drops or ignores) on the two holes the
    stubbed cycle-1 tests exploited:

    * a coverage entry's ``residual_ids`` referencing a residual id absent
      from A2's own ``residuals`` list -- a forgotten residual is a
      refusal, never a silent pass;
    * a coverage entry with an empty ``residual_ids`` list whose
      ``coverage_state`` is not ``"resolved"`` -- a residual can only clear
      through a matching A2 coverage-state transition, never by quietly
      disappearing from the list."""
    residual_ids = {entry["residual_id"] for entry in a2_receipt.get("residuals", [])}
    manifest_by_stratum = {stratum["stratum"]: stratum for stratum in frozen_slot_strata(manifest)}
    coverage_map = a2_receipt["stratum_coverage_map"]
    require(
        len({c["stratum"] for c in coverage_map}) == len(coverage_map),
        "A2 stratum_coverage_map carries a duplicate stratum entry -- refusing",
        error_cls,
    )
    require(
        {c["stratum"] for c in coverage_map} == set(manifest_by_stratum),
        "A2 stratum_coverage_map does not cover exactly the frozen manifest's strata -- refusing",
        error_cls,
    )

    records = []
    for coverage in coverage_map:
        stratum = coverage["stratum"]
        for rid in coverage["residual_ids"]:
            require(
                rid in residual_ids,
                f"A2 stratum_coverage_map entry {stratum!r} references residual id {rid!r} absent from A2's own residuals -- refusing",
                error_cls,
            )
        if not coverage["residual_ids"]:
            require(
                coverage.get("coverage_state") == A2_RESOLVED_COVERAGE_STATE,
                f"A2 stratum_coverage_map entry {stratum!r} carries no residual ids but coverage_state is not "
                f"{A2_RESOLVED_COVERAGE_STATE!r} -- refusing (a residual can only clear through a matching "
                "coverage-state transition, never by disappearing from the list)",
                error_cls,
            )
        rights_resolved = not coverage["residual_ids"]
        stratum_entry = manifest_by_stratum[stratum]
        assigned = stratum_entry["assignment_state"] == "ASSIGNED"
        records.append(
            {
                "stratum": stratum,
                "rights_resolved": rights_resolved,
                "assigned": assigned,
                "prerequisite_eligible": rights_resolved and assigned,
                "slot_ids": stratum_entry["slot_ids"],
            }
        )
    records.sort(key=lambda record: record["stratum"])
    return records


def eligible_slot_ids(eligibility: list[dict[str, Any]]) -> set[str]:
    return {slot_id for record in eligibility if record["prerequisite_eligible"] for slot_id in record["slot_ids"]}


def public_eligibility(eligibility: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Strips the internal-only ``slot_ids`` key for publication -- the
    manifest's own ``frozen_slot_denominator.strata`` already carries
    ``slot_ids`` per stratum once; this field never duplicates it."""
    return [
        {key: record[key] for key in ("stratum", "rights_resolved", "assigned", "prerequisite_eligible")}
        for record in eligibility
    ]


def stratum_a2_reason_codes(a2_receipt: dict[str, Any], error_cls: type[Exception] = ValueError) -> dict[str, str]:
    """Pure function of A2's own public ``residuals``/``stratum_coverage_map``
    -- never opens private state. Only ever contains an entry for a stratum
    that still carries an unresolved A2 residual; a prerequisite-eligible
    stratum (empty ``residual_ids``) has nothing to report here on purpose
    -- callers must consult ``stratum_eligibility`` first, and use
    ``REASON_STAGE_COMPLETION_NOT_YET_AVAILABLE`` for an eligible stratum
    rather than looking (and failing) here."""
    reason_by_residual_id = {entry["residual_id"]: entry["reason_code"] for entry in a2_receipt.get("residuals", [])}
    resolved: dict[str, str] = {}
    for coverage in a2_receipt["stratum_coverage_map"]:
        stratum = coverage["stratum"]
        if not coverage["residual_ids"]:
            continue
        for rid in coverage["residual_ids"]:
            require(
                rid in reason_by_residual_id,
                f"A2 stratum_coverage_map entry {stratum!r} references residual id {rid!r} absent from A2's own residuals -- refusing",
                error_cls,
            )
        reasons = {reason_by_residual_id[rid] for rid in coverage["residual_ids"]}
        require(
            len(reasons) == 1,
            f"A2 stratum_coverage_map entry {stratum!r} does not resolve to exactly one reason code -- refusing",
            error_cls,
        )
        (reason,) = reasons
        require(
            reason in A2_REASON_TO_RESIDUAL_REASON,
            f"A2 stratum_coverage_map entry {stratum!r} carries an unmapped reason code {reason!r} -- refusing",
            error_cls,
        )
        resolved[stratum] = A2_REASON_TO_RESIDUAL_REASON[reason]
    return resolved


def slot_residual_reason_code(
    stratum: str, eligibility_by_stratum: dict[str, dict[str, Any]], a2_reasons: dict[str, str]
) -> str:
    """The typed reason a slot still carries a residual at some stage: the
    stratum's own A2 blocker if it is not yet prerequisite-eligible, or
    ``REASON_STAGE_COMPLETION_NOT_YET_AVAILABLE`` if it is eligible but no
    positive stage-completion evidence exists for it yet -- never a fourth,
    independently invented reason."""
    if eligibility_by_stratum[stratum]["prerequisite_eligible"]:
        return REASON_STAGE_COMPLETION_NOT_YET_AVAILABLE
    return a2_reasons[stratum]


# --- positive completion evidence (public, validator-owned, empty today) ---


def completion_slot_ids(
    completions: list[dict[str, Any]], *, stage: str, total_slot_ids: set[str], error_cls: type[Exception] = ValueError
) -> set[str]:
    """The set of slot ids a stage's own typed, positive completion records
    name -- never derived from any other list's absence. Fails closed on a
    record naming a stage other than its own, a slot outside the frozen
    denominator, or a duplicate slot id. Empty in every builder this repo
    ships today (no stage has an execution mechanism yet); this function
    exists so that changes, whenever they arrive, are proven by real
    partition/subset checks instead of trusted."""
    if stage in {"A7", "A8", "A9", "A10", "A11", "A12", "A13"} and completions:
        from learn_ukrainian_v4_runtime.stage_policy import validate_completion_policy

        try:
            validate_completion_policy(completions)
        except ValueError as exc:
            raise error_cls(str(exc)) from exc
    ids: list[str] = []
    for record in completions:
        require(
            record.get("stage") == stage,
            f"{stage} completion record does not carry stage={stage!r} -- refusing",
            error_cls,
        )
        slot_id = record.get("slot_id")
        require(
            isinstance(slot_id, str) and slot_id in total_slot_ids,
            f"{stage} completion record references a slot id outside the frozen 100-slot denominator -- refusing",
            error_cls,
        )
        ids.append(slot_id)
    require(len(ids) == len(set(ids)), f"{stage} completions carries a duplicate slot id -- refusing", error_cls)
    return set(ids)


def derive_residual_slot_ids(total_slot_ids: set[str], completion_ids: set[str]) -> set[str]:
    """The complement of completion over the *full* 100-slot denominator --
    never over just the eligible slots, so an ineligible slot's residual is
    never silently dropped either."""
    return total_slot_ids - completion_ids


def validate_partition(
    total_slot_ids: set[str],
    completion_ids: set[str],
    residual_ids: set[str],
    *,
    label: str,
    error_cls: type[Exception] = ValueError,
) -> None:
    require(
        completion_ids.isdisjoint(residual_ids),
        f"{label}: completion and residual slot sets overlap -- refusing",
        error_cls,
    )
    require(
        completion_ids | residual_ids == total_slot_ids,
        f"{label}: completion and residual slot sets do not exactly partition the frozen 100-slot denominator -- refusing",
        error_cls,
    )


def validate_subset(
    smaller: set[str], bigger: set[str], *, label: str, error_cls: type[Exception] = ValueError
) -> None:
    require(smaller <= bigger, f"{label}: is not a subset of the required set -- refusing", error_cls)


# --- gate reason code (small ordered enum) -----------------------------------


def gate_blocked_reason_code(
    *,
    upstream_valid: bool,
    slots_prerequisite_eligible: int,
    has_upstream_stage: bool,
    slots_upstream_complete: int,
    slots_stage_complete: int,
    total: int,
) -> str | None:
    """The one place a gate's ``blocked_reason_code`` is decided -- a small,
    ordered enum, never a per-stage variant of the same idea. Checked in
    order; the first applicable reason wins."""
    if slots_stage_complete == total:
        return None
    if not upstream_valid:
        return REASON_UPSTREAM_RECEIPT_INVALID
    if slots_prerequisite_eligible == 0:
        return REASON_NO_SLOT_ELIGIBLE
    if has_upstream_stage and slots_upstream_complete == 0:
        return REASON_ELIGIBLE_AWAITING_UPSTREAM_COMPLETION
    if slots_stage_complete == 0:
        return REASON_ELIGIBLE_AWAITING_STAGE_EXECUTION
    return REASON_PARTIAL_COMPLETION_RESIDUAL
