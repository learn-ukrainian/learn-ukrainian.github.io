# Prompt Engineering Review: travel-and-transport

**Track:** a1 | **Sequence:** 52
**Pipeline:** v4
**Validate attempts:** 2
**Friction reports:** 2 (content: NONE, activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Activity item minimums not enforced in first pass | HIGH | phase-C-prompt.md | First fix attempt (validate-fix1) found 7 activities with too few items: match-ups had 6 pairs (min 8), quiz had 6 items (min 8), true-false had 6 (min 8), fill-in had 6 (min 8), unjumble had 4 (min 6). The prompt clearly states minimums but Gemini systematically under-produced. |
| Immersion dropped to 11% after fix | HIGH | validate-fix2-prompt.md | Fix attempt 1 destroyed immersion (11% vs 35% target). The fix prompt focused on section headings but the model likely rewrote sections in English. The fix prompt says "do not rewrite working content" but this conflicts with needing to fix section headings. |
| Dative false positive | MEDIUM | validate-fix2-prompt.md | "пові" flagged as dative -- likely a substring match false positive on a word like "повідомити". The audit tool's dative detector is too aggressive. |
| PLAN_SECTION_MISSING again | MEDIUM | validate-fix1-prompt.md | Same false positive as M51 -- 5 sections flagged as "missing" that exist. |
| ACTIVITY_VESUM_FAIL: "Антон", "Іван" | LOW | validate-fix prompts | Proper nouns used in activities fail VESUM. Expected -- these are names, not vocabulary errors. But the fix prompt asks to "Fix spelling or replace" which is misleading. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| No guidance on maintaining immersion during fixes | HIGH | Add to validate-fix template: "CRITICAL: When fixing issues, do NOT reduce Ukrainian content. If you rewrite a Ukrainian sentence, replace it with another Ukrainian sentence of equal or greater length." |
| Activity minimums need stronger emphasis | HIGH | Bold the minimums table in phase-C-prompt.md and add: "HARD FAIL: Any activity with fewer items than the minimum will trigger a fix loop." |
| Proper noun VESUM failures need exemption guidance | LOW | Add to fix prompt: "Proper nouns (names like Антон, Іван, Микола) are expected VESUM misses -- do not replace them." |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|-----------------|---------|--------------|
| validate-fix1: section mismatch + VESUM name | schema_mismatch | Same heading matcher false positive as M51. Proper noun VESUM miss. | Fix heading matcher; add proper noun exemption |
| validate-fix2: 15 issues (11 pedagogy) | template_gap + model_limitation | Dative (2x false positive), activity item counts (7 under minimum), immersion crash (11%), sentence length. | Stronger activity minimums enforcement; immersion preservation in fix prompts |
| Immersion crash during fix | conflicting_guidance | Fix prompt says "Fix ONLY the issues listed" + "do not rewrite working content" but fixing section headings caused model to rewrite content in English. | Add explicit immersion preservation instruction |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| validate | 2 | Fix1: section heading mismatch + VESUM name (mostly false positives). Fix2: activity item counts too low, dative false positives, immersion crash from fix1. | PARTIALLY -- item count issues preventable with stronger prompt emphasis. Immersion crash caused by fix1 was a cascade. False positives are tooling issues. |

## VESUM Findings

- 227/229 (99.1%) verified
- Not found: "Одесу" (accusative of Одеса -- should be in VESUM; possible VESUM gap), "Укрзалізниця" (brand name -- expected miss)

## Suggested Template Fixes

### Fix 1: Enforce activity item minimums more aggressively (Priority: HIGH)
**Before:** Minimums table exists in phase-C-prompt.md but is not prominently placed.
**After:** Move minimums to a CRITICAL box at the top of the activity section. Add: "MANDATORY PRE-SUBMISSION CHECK: Count items in EVERY activity. Any activity below the minimum = automatic fix loop. quiz/true-false/fill-in/match-up: 8+. unjumble: 6+. group-sort: 8+ total items across groups."
**Cross-module:** All modules.

### Fix 2: Add immersion preservation to fix prompts (Priority: HIGH)
**Before:** Fix prompt says "Fix ONLY the issues listed -- do not rewrite working content"
**After:** Add: "IMMERSION RULE: When fixing content, maintain Ukrainian immersion percentage. Do NOT convert Ukrainian sentences to English. If a Ukrainian sentence must be removed, add an equivalent Ukrainian sentence elsewhere in the same section."
**Cross-module:** All modules.

### Fix 3: Reduce dative false positives in audit tool (Priority: MEDIUM)
**Issue:** Substring matching catches "пові" as dative when it is part of "повідомити" or similar words.
**Fix:** Tooling fix -- the dative detector should check whole word forms, not substrings.

### Fix 4: Add proper noun exemption to VESUM fix prompts (Priority: LOW)
**Before:** "Activity answers contain VESUM-failed words: Антон. Fix spelling or replace."
**After:** "Activity answers contain VESUM-failed words: Антон. NOTE: Proper nouns (personal names, brand names) are expected VESUM misses. Only fix if the word is misspelled -- do not replace valid names."

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Enforce activity item minimums more aggressively in phase-C-prompt (HIGH) -- 7 activities under minimum is systematic
2. Add immersion preservation rule to validate-fix template (HIGH) -- prevents cascading quality loss during fixes
3. Reduce dative false positives in audit tooling (MEDIUM) -- eliminates unnecessary fix iterations
