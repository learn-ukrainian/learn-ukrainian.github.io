# Prompt Engineering Review: stress-and-intonation

**Track:** a1 | **Sequence:** 6
**Pipeline:** v4
**Validate attempts:** 3
**Friction reports:** 2 (both NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| No issue | -- | phase-2-prompt.md | Engagement callouts correctly stated as "3+ MANDATORY". |
| No issue | -- | phase-2-prompt.md | Word target, immersion range, section budgets all clear. |
| Word overshoot | LOW | phase-2-prompt.md | 2469 words for 1200 target (206%). M6 covers stress + intonation + mobile stress + reading dialogues — legitimate depth, but Gemini wrote 2x the target. Not a problem per se (audit passes at >= target). |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| Hortative ban not in constraints | MEDIUM | M6 built before our hortative fix. Gemini used "Прочитайте цей текст" and "Зверніть увагу" — caught by fix2 rule engine. Now fixed in pipeline_lib.py for future builds. |
| Constraint says "FORBIDDEN: verb conjugation" but M6 teaches писати/пишу/пишеш | LOW | Content includes verb conjugation examples (писа́ти, пишу́, пи́шеш) under "Mobile Stress" to demonstrate stress shifts. This is pedagogically valid — it's showing stress patterns, not teaching conjugation. But it creates a tension with the FORBIDDEN constraint. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|--------------|
| Fix1: 0 issues in prompt | **tooling bug** | Empty fix prompt — audit failed but no deterministic issues. Wasted iteration. | **FIXED** — ultra-fallback now dumps raw audit tail |
| Fix2: Imperatives (Прочитайте, Зверніть) | **model limitation** | Gemini used Ukrainian imperatives for reading instructions. Rule engine caught them. | **FIXED** — hortative ban added to M5-M10 constraints |
| Fix3: Immersion too low (14.7%) | **cascading fix** | After removing Ukrainian imperatives in fix2, immersion dropped below 15% target. Gemini added more Ukrainian reading practice blocks. | Not a prompt issue — measurement gate working correctly |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| validate | 3 | Empty fix prompt + imperatives + cascading immersion drop | **Partially** — fix1 wasted (empty prompt bug, now fixed). Fix2 would have been caught earlier with our hortative ban. Fix3 is a natural cascade. |

**Detailed fix loop:**
1. Fix1: 0 issues — empty fix prompt bug. Wasted iteration.
2. Fix2: 2 issues — Прочитайте, Зверніть (imperatives). Gemini replaced with English.
3. Fix3: 1 issue — immersion at 14.7% (target 15-35%). Gemini added reading practice blocks.

## Content Quality Notes

**Strengths:**
- Excellent pedagogical arc: what is stress → patterns → mobile stress → intonation → practice
- Strong minimal pairs: за́мок/замо́к, му́ка/мука́ — classic examples, culturally resonant
- Good use of reading practice with dialogues at the end — feels like real language use
- 5 engagement boxes (exceeds minimum of 3)
- Mobile stress section shows рука́/ру́ки and писа́ти/пишу́/пи́шеш — pedagogically correct preview
- Intonation section with 4 contour types (statement, wh-question, yes/no, exclamation) is well-structured

**Issues:**
- **Verb conjugation in constraints-forbidden zone** (LOW): Content shows писа́ти/пишу́/пи́шеш as stress examples. This is valid for stress demonstration but technically violates "FORBIDDEN: verb conjugation". The constraint should probably have an exception: "Conjugated forms allowed ONLY as stress pattern examples, not for teaching conjugation."
- **2x word overshoot** (INFO): 2469 vs 1200 target. Not a problem but Gemini was very verbose — the dialogues and reading practice sections are extensive. Good content though.

## Suggested Template Fixes

### Fix 1: Verb conjugation exception for stress examples (Priority: LOW)
**Scope:** A1 M5-M10 constraints
**File:** `scripts/pipeline_lib.py` (a1-m05-10 constraint block)

Add: "Exception: Conjugated verb forms may appear as STRESS PATTERN EXAMPLES only (e.g., писа́ти → пишу́ → пи́шеш to demonstrate stress mobility). Do not teach conjugation rules."

## Summary

**Template health:** GOOD — all fixes from M5 review would have prevented 2/3 fix attempts
**Top fix by leverage:** Verb conjugation exception for stress examples (prevents false constraint violations)
