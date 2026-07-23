# Decision: fleet-comms v1 Gate D residual (formal CF eligibility)

**Date:** 2026-07-23  
**Stream:** #4707 · **Product:** #5512  
**Status:** accepted for v1 closeout

## Context

Isolation design spikes (#5614 / #5617 / #5620) closed **Option C fail-closed residual**.
Wire issues #5615–#5616 (AGY), #5618–#5619 (Kimi), #5621–#5622 (Grok) cannot flip
`formal_review_eligible` without Option A (native seal flags) or proven Option B
(proxy/wrapper) — both need new engineering + advisor review for architecture.

## Decision

For **fleet-comms v1 completion**:

1. **Keep** `formal_review_eligible: false` for agy / kimi / grok.
2. **Keep** fail-closed isolation raises + substitute formal CF path
   (`review-pr --reviewer claude|codex|glm`).
3. **Close** wire/enablement issues as **v1 residual** (not silent partial seal).
4. **Leave** parents #5555–#5557 open only as *future isolation engineering* trackers
   (or close with residual note if product prefers a single open epic line).

## Non-decisions

- Not a permanent wontfix for isolation engineering.
- Not a flip of stream authority (Gate B) or retention apply (Gate C).
- Not dual_write plane default (Gate A is shadow only in this decision).

## Evidence

- Runbooks: `docs/runbooks/{agy,kimi,grok}-formal-cf-isolation.md`
- Tests: `tests/test_review_isolation.py` (`agy_isolated`, grok OAuth/isolation)
- Config: `scripts/config/fleet_communications.yaml` eligibility flags

## Operator finish-mode

Operator directed 2026-07-23: fully finish fleet-comms without optional stop-asks.
Gate D residual closeout is required so v1 is not blocked on unproven seals.
