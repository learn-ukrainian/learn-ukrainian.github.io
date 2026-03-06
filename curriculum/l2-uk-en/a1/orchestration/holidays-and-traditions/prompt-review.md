# Prompt Engineering Review: holidays-and-traditions

**Track:** a1 | **Sequence:** 50
**Pipeline:** v4
**Validate attempts:** 1
**Friction reports:** 2 (content: NONE, activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| IPA in research outline | MEDIUM | phase-A-output.md | Research output includes IPA: `/schtschastja/` and `/zdorovja/` in the content_outline points for the Wishes section. This directly contradicts the absolute IPA ban in SHARED_CONTENT_RULES. The content writer may reproduce these. |
| Constraint contradiction: Instrumental case | HIGH | phase-2-prompt.md + placeholders.yaml | LEVEL_CONSTRAINTS say "Instrumental case FORBIDDEN" but the module requires teaching "З Новим роком" (Instrumental). Research notes correctly say "present as fixed formulas", but the constraint text flatly bans instrumental endings (-ом/-ою). The prompt should explicitly note the exception for lexicalized greetings. |
| Constraint contradiction: past tense verb | MEDIUM | phase-2-output-1.md | Content uses "написав" (perfective past) in "Микола Леонтович написав цю музику" -- this violates both "Only imperfective aspect verbs" AND "Past tense at M36" (module is M50 > M36, so past is OK, but perfective is not). The prompt constraints were clear but the model violated them. |
| Example content irrelevant | LOW | phase-2-prompt.md | Same letter-introduction example as M49. Not useful for a cultural vocabulary module. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| No explicit Instrumental exception for fixed formulas | HIGH | Add to LEVEL_CONSTRAINTS or PEDAGOGICAL_CONSTRAINTS: "Exception: Fixed greeting formulas (З Новим роком, З Різдвом) are taught as memorized chunks, not productive grammar." |
| Research IPA leaking to content | MEDIUM | Add to phase-A-prompt: "Do NOT include IPA in content_outline points." |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|-----------------|---------|--------------|
| Content friction: NONE | N/A | No friction reported, but constraint violation occurred silently | Template needs explicit exception for Instrumental in fixed formulas |
| Activities friction: NONE | N/A | Clean | N/A |
| VESUM: "успіха", "успіхі" not found | schema_mismatch | These are incorrect Ukrainian forms used as distractors in fill-in activities. "Успіха" is not a valid Ukrainian form (correct Gen. is "успіху"). | Add to activity template: "Distractor options must be real Ukrainian word forms, not invented non-forms." |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| validate | 1 | Generic audit failure, fix resolved it | Same sparse fix prompt issue as M49 |

## VESUM Findings

- 278/282 (98.6%) verified
- Not found: Леонтович, Микола (proper nouns -- expected), успіха, успіхі (invalid Ukrainian forms in activity distractors)
- **Issue:** "успіха" is a Russian genitive form, not Ukrainian. Ukrainian genitive is "успіху". Using fake forms as distractors teaches wrong patterns.

## Suggested Template Fixes

### Fix 1: Add Instrumental exception for fixed greeting formulas (Priority: HIGH)
### Fix 2: Ban invented distractor forms in activities (Priority: HIGH)
### Fix 3: Forbid IPA in research outline points (Priority: MEDIUM)
### Fix 4: Forbid perfective aspect in content with examples (Priority: MEDIUM)

(See audit copy for full details on each fix.)

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Add Instrumental exception for fixed greeting formulas (HIGH)
2. Ban invented distractor forms in fill-in activities (HIGH)
3. Forbid perfective aspect with concrete examples (MEDIUM)
