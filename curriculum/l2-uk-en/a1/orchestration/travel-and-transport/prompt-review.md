# Prompt Engineering Review: travel-and-transport

**Track:** a1 | **Sequence:** 52
**Pipeline:** v4
**Validate attempts:** 2
**Friction reports:** 2 (content: NONE, activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Activity item minimums not enforced in first pass | HIGH | phase-C-prompt.md | 7 activities produced with too few items despite clear minimums in prompt. |
| Immersion dropped to 11% after fix | HIGH | validate-fix2-prompt.md | Fix destroyed immersion. No preservation rule in fix prompt. |
| Dative false positive | MEDIUM | validate-fix2-prompt.md | "пові" flagged incorrectly as dative. |
| PLAN_SECTION_MISSING false positive | MEDIUM | validate-fix1-prompt.md | Same heading matcher bug as M51. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| No immersion preservation in fix prompts | HIGH | Add explicit rule |
| Activity minimums not prominent enough | HIGH | Move to CRITICAL box |
| No proper noun VESUM exemption | LOW | Add note to fix prompts |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|-----------------|---------|--------------|
| 7 activities under minimum | template_gap | Minimums not emphasized enough | Move to CRITICAL box |
| Immersion crash during fix | conflicting_guidance | Fix rules caused content rewrite | Add preservation rule |
| Section heading false positive | schema_mismatch | Tooling bug | Fix audit tool |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| validate | 2 | Fix1: false positives. Fix2: item counts, immersion crash, dative false positives. | PARTIALLY -- item counts and immersion crash preventable. |

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Enforce activity item minimums aggressively (HIGH)
2. Add immersion preservation to fix prompts (HIGH)
3. Reduce dative false positives in audit tooling (MEDIUM)
