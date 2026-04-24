"""Validated-patchability predicate for convergence-loop routing.

Introduced 2026-04-24 (GH #1525 P0) to replace fragile location-string heuristics
in ``finding_topology.py`` as the ONLY signal that decides whether a reviewer
finding can be patched deterministically.

## Scope: this is a BATCH-LEVEL predicate (GH #1526 item 1)

**Read this before adding a new caller.** The predicate operates at
**observation level** — it validates a `<fixes>` block as a whole, not each
finding against its "own" fix. Reviewer output does not link findings to
specific fixes (no `fix_for_finding id=...` contract today); every fix is
anonymous within the block. Consequence:

- ``batch_patch_ok`` means "every fix in the reviewer's `<fixes>` block has
  an anchor present in current content", NOT "this finding has a
  corresponding fix that applies cleanly".
- If the reviewer emits 2 fixes for 3 findings, all 3 non-plan findings
  share the ``batch_patch_ok`` status. The apply step
  (``_apply_review_fixes``) applies only the 2 matching fixes; the third
  finding's content defect persists and gets re-flagged next round, where
  the stall detector (``convergence_loop._stall_signals``) catches it
  (``top3_overlap`` or ``hard_floor_persisted``) and escalates to
  ``plan_revision_request``. So the asymmetry costs at most one extra
  round; it never silently ships a defect.

A per-finding upgrade — reviewer prompts emitting
``<fix_for_finding id="...">`` blocks so the predicate can map 1:1 — is
tracked in GH #1526 item 1 (Path A). Deferred until empirical evidence of
false-positive patchability classification shows up in production; until
then the batch-level semantic is the conservative right call.

## Why this exists

``convergence_loop.select_strategy`` gates the ``patch`` tier on
``topologies == {"local_to_prose"}``. The topology classifier decides that by
string-matching the finding's ``location`` field against a small token list
(``sentence``, ``paragraph``, backticks, ``##`` headings). When the reviewer
phrases the location without those magic tokens — common for Plan-Adherence
findings that point at ``INJECT_ACTIVITY`` markers — the classifier defaults to
``cross_section`` and the WHOLE fix-application path escalates to
``plan_revision_request``, even when the reviewer emitted clean
``<fixes>`` pairs.

## The predicate (3-part, deterministic)

A finding is "batch-patchable" iff ALL three hold:

1. ``parsed_fixes`` is non-empty (reviewer actually emitted ``<fixes>``)
2. **Every** fix's anchor (``find`` or ``insert_after``) string is present in
   the current module content. Not a subset — every one. A partial-anchor set
   means the reviewer saw a stale version of the text, so the fixes are not
   trustworthy as a batch.
3. The finding itself is NOT ``plan_level`` (``finding_normalizer`` already
   labels plan-contradiction / vocab-density / pedagogical-sequence /
   scenario-grammar-misalignment at the source). Plan-level findings keep the
   hard stop regardless of whether a fix was emitted.

When the predicate validates, ``_normalize_observation`` overrides the
topology classifier's output to ``local_to_prose`` for that finding, which
lets ``select_strategy`` route the whole set to the deterministic patch tier.

## What this is NOT

This is not a revival of any killed LLM-regeneration tier (M1 / M2 / M4 in
ADR-007). ADR-007 holds unchanged — we do not regenerate content with an
LLM during review. We only fix the ROUTING around the existing deterministic
``<fixes>`` find/replace loop so that reviewer-emitted patches actually get
applied instead of being black-holed because the location wording failed a
fragile heuristic.

This is also NOT a per-finding patchability check — see "Scope" above.

Cross-agent consensus: architecture thread ``8aaa5760a2814e1192dac1b61b1b4098``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal

PatchabilityStatus = Literal[
    # NOTE: ``batch_patch_ok`` (not ``patch_ok``) because this status is
    # derived from OBSERVATION-level validation of the whole ``<fixes>``
    # block, not from per-finding matching. See module docstring "Scope"
    # section. GH #1526 item 1 renamed from ``patch_ok`` on 2026-04-24.
    "batch_patch_ok",      # all 3 predicate parts hold — override to local_to_prose
    "no_fixes",            # reviewer emitted no <fixes> block at all
    "anchor_missing",      # at least one fix has find-string NOT present in content
    "plan_level_hardstop", # finding.plan_level is True — ADR-007 plan-revision path
    "not_evaluated",       # caller did not supply content/fixes — legacy code path
]


@dataclass(frozen=True)
class AnchorValidation:
    """Observation-level result of validating every fix's anchor against content.

    This dataclass, and the ``batch_patch_ok`` status derived from it, are
    OBSERVATION-SCOPED — they describe the reviewer's ``<fixes>`` block as a
    whole, not individual findings. Every non-plan finding in the same
    observation shares the same ``AnchorValidation`` result. See the module
    docstring "Scope" section (GH #1526 item 1) for why.

    Computed once per review round, then passed to ``classify_patchability``
    for each finding. Avoids the O(findings × fixes) substring scans that
    would happen if each finding re-validated the full fixes list.

    ``evaluated=False`` when the caller did not supply fixes/content — the
    legacy code path that falls back to the fuzzy topology classifier.

    Note on anchor-matching parity: this uses plain ``str in content``. The
    actual apply step (``_apply_review_fixes`` in v6_build.py) has four
    matching strategies including stress-mark-aware and whitespace-normalized
    matching. This predicate is INTENTIONALLY stricter — false negatives here
    escalate to plan_revision_request (human review), which is the safe
    failure direction. A future refactor may extract the apply step's match
    strategies into a shared helper (EPIC #1525 follow-up); for P0 we
    accept the asymmetry.
    """

    evaluated: bool
    total: int
    valid: int
    invalid: int


def _has_valid_anchor(fix: dict[str, Any], content: str) -> bool:
    """Return True iff the fix's anchor string is present in ``content``.

    Supports both ``find`` / ``replace`` and ``insert_after`` / ``text`` shapes
    (see ``_parse_review_fixes`` in ``v6_build.py``).

    Dispatch order MUST mirror ``_apply_review_fixes`` at v6_build.py:8180 —
    apply checks ``insert_after`` FIRST and continues past ``find`` when both
    keys are present. A validator that checks ``find`` first would mark a
    mixed-shape fix ``batch_patch_ok`` on a valid ``find`` anchor while the
    apply step uses a missing ``insert_after`` anchor and silently skips the
    fix (false positive in the batch-patchability contract).
    """
    if "insert_after" in fix and "text" in fix:
        anchor = fix.get("insert_after")
        return bool(anchor) and isinstance(anchor, str) and anchor in content
    if "find" in fix and "replace" in fix:
        anchor = fix.get("find")
        return bool(anchor) and isinstance(anchor, str) and anchor in content
    return False


def validate_fix_anchors(
    fixes: Sequence[dict[str, Any]],
    content: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split a fixes sequence into (valid, invalid) by anchor presence in content.

    A fix is valid iff its ``find`` or ``insert_after`` string appears verbatim
    in the module content. Returned lists preserve input order so callers can
    log which fixes failed anchor validation in telemetry.
    """
    valid: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    for fix in fixes:
        if _has_valid_anchor(fix, content):
            valid.append(fix)
        else:
            invalid.append(fix)
    return valid, invalid


def compute_anchor_validation(
    fixes: Sequence[dict[str, Any]] | None,
    content: str | None,
) -> AnchorValidation:
    """Compute observation-level anchor validation ONCE per review round.

    Called from ``_normalize_observation`` before the per-finding loop, the
    result is then passed to every ``classify_patchability`` call for that
    round. Replaces the O(findings × fixes) substring scanning that a naive
    per-finding implementation would do.

    ``evaluated=False`` when fixes or content is None — callers should treat
    this as the legacy "not evaluated" path that falls back to the fuzzy
    topology classifier.
    """
    if fixes is None or content is None:
        return AnchorValidation(evaluated=False, total=0, valid=0, invalid=0)
    valid, invalid = validate_fix_anchors(fixes, content)
    return AnchorValidation(
        evaluated=True,
        total=len(fixes),
        valid=len(valid),
        invalid=len(invalid),
    )


def classify_patchability(
    finding: dict[str, Any],
    *,
    anchor_validation: AnchorValidation,
) -> tuple[PatchabilityStatus, str]:
    """Apply the 3-part patchability predicate to a single normalized finding.

    Returns ``(status, reason)``. The caller in ``_normalize_observation`` uses
    the status to decide whether to override the topology classifier's output
    for this finding:

    - ``batch_patch_ok`` → override topology to ``local_to_prose``
    - everything else → leave topology as-is (classifier-determined)

    The only per-finding signal consumed here is ``plan_level`` — plan-level
    findings hardstop regardless of batch-level anchor validity. All other
    findings share the status derived from the observation-level
    ``AnchorValidation``; see the module docstring "Scope" section for why
    this is batch-level and not per-finding.

    ``reason`` is a human-readable one-liner suitable for telemetry / JSONL
    event emission.

    Args:
        finding: A normalized finding dict (output of ``normalize_finding``).
            Must have ``plan_level`` key set by the normalizer.
        anchor_validation: Result of ``compute_anchor_validation(fixes, content)``
            for this review round. Shared across all findings — do not compute
            per-finding.
    """
    # Plan-level hardstop: ADR-007 says these route to plan_revision_request
    # regardless of whether a fix was emitted. The fix itself may be cosmetic
    # while the underlying plan defect persists.
    if finding.get("plan_level"):
        return (
            "plan_level_hardstop",
            f"finding error_class={finding.get('error_class')!r} is plan-level; human plan edit required",
        )
    if not anchor_validation.evaluated:
        return (
            "not_evaluated",
            "patchability predicate skipped — caller did not supply fixes/content",
        )
    if anchor_validation.total == 0:
        return (
            "no_fixes",
            "reviewer emitted no <fixes> block — nothing to patch",
        )
    if anchor_validation.invalid > 0:
        return (
            "anchor_missing",
            f"{anchor_validation.invalid} of {anchor_validation.total} fix anchors not present in content (could be stale review, normalization asymmetry, or reviewer-side anchor bug)",
        )
    return (
        "batch_patch_ok",
        f"all {anchor_validation.valid} fix anchors validated against current content "
        f"(batch-level: does NOT prove 1:1 mapping to this finding; see GH #1526)",
    )
