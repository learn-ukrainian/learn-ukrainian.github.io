# Prompt Engineering Review: checkpoint-communication

**Track:** a1 | **Sequence:** 54
**Pipeline:** v4
**Validate attempts:** 4
**Friction reports:** 2 (content: 1, activities: 1)
**Review outcome:** FAIL (Language 7/10, Linguistic Accuracy 7/10)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Contradictory constraint: imperative forbidden vs plan requires imperatives | HIGH | phase-2-prompt.md, placeholders.yaml | PEDAGOGICAL_CONSTRAINTS says "Imperative forms NOT taught until M47" but this IS M54, a checkpoint that reviews imperatives. The constraint is stale/wrong for this module and confused both the builder and validator. Fix-loop attempt 2 flagged Dative as forbidden even though the plan explicitly requires "мені треба" as a fixed chunk. |
| Textbook reference examples irrelevant to module type | MEDIUM | phase-2-prompt.md | Lines 38-208 inject Grade 1 bukvar exercises (syllable drills, letter introductions) as "inspiration" for an M54 checkpoint module about modal verbs and imperatives. These examples are completely disconnected from the module's actual content level. |
| {H3_WORD_RANGE} placeholder not resolved in persona reminder | LOW | phase-2-prompt.md | Line 6: "Every H3 gets {H3_WORD_RANGE} words" appears literally, though it IS resolved later in placeholders. The duplicate unresolved reference at the top could confuse the model. |
| Research output mentions IPA despite IPA being banned | LOW | phase-A-output.md / meta outline | Research outline point says "Provide IPA for the first occurrence" but the content prompt bans IPA. Research was generated before the content prompt caught this. Not harmful since the content builder ignored it. |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| No prior module content injected (M53 at-the-restaurant) | LOW | Checkpoint modules review skills from prior modules but the prompt has no visibility into what M47-M53 actually taught. Builder must guess or read files. |
| Plan's activity_hints not surfaced in content prompt | MEDIUM | The plan required a single 30-item comprehensive quiz, but neither the content nor activities prompt surfaced this requirement explicitly. Activities prompt only shows "Required types: (empty)". Result: quiz was split into smaller activities, flagged as missing by review. |
| Discovery results poor quality / irrelevant | LOW | RAG chunks are grade 4-10 grammar textbook pages about verb conjugation, not about communication checkpoints. Discovery found no videos and only tangentially relevant blogs. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|----------------|---------|--------------|
| PLAN_SECTION_MISSING (fix 1) | schema_mismatch | Section titles in content used Ukrainian-only names (e.g. "Навичка 1: Модальні дієслова") while audit expected bilingual format with parenthetical English translations. The plan outline had Ukrainian titles, but the audit match logic needed the "(English Translation)" suffix. | Standardize section title format in meta outline template: always require bilingual "Ukrainian (English)" format. |
| Dative case flagged as forbidden (fix 2-4) | conflicting_guidance | LEVEL_CONSTRAINTS says "Dative FORBIDDEN" but the plan explicitly requires "мені треба" as a fixed chunk. Research output even notes this conflict: "MUST teach as fixed lexical chunks." The validator cannot distinguish between forbidden grammar and plan-approved fixed chunks. | Add an exception list to LEVEL_CONSTRAINTS for plan-approved fixed expressions. Current exceptions exist for M1 ("нам") and M19 ("подобається") but not for M54's "мені треба". |
| Russian calque "Давай зустрінемось" (review) | model_limitation | Gemini generated the colloquial Russian-influenced "Давай + future" pattern instead of standard Ukrainian synthetic imperatives ("Зустріньмося"). The content prompt's Russianisms checklist does not include "давай + verb" as a flagged pattern. | Add "Давай + 1st person plural future" to the Russianisms checklist in the content template with the correct alternative: synthetic -мо imperative. |
| Fabricated word forms as distractors "требом" (review) | model_limitation | Gemini invented morphologically impossible declined forms of the indeclinable word "треба" as activity distractors. The activities prompt warns against fabrication only implicitly via "plausible, clear items." | Add explicit rule to activities template: "NEVER invent morphological forms that do not exist. All distractor options must be real Ukrainian words verifiable in VESUM." |
| Quiz question prompt length violations (fix 2) | template_gap | Audit flagged quiz question prompts as too long (16 words vs 5-10 target) but the activities prompt specifies no prompt length constraint. The content prompt and activities prompt are not aligned on A1 complexity targets. | Add explicit prompt length guidance to activities template: "A1 quiz questions: 5-12 words max." |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|-----------|--------------|
| Validate | 4 | Fix 1: section title mismatch (bilingual vs Ukrainian-only). Fix 2: Dative "мені" flagged despite being plan-approved. Fix 3-4: residual checkpoint format errors (unclear from prompt). | YES for fix 1 (standardize title format). YES for fix 2 (add exception). Fix 3-4 prompts are nearly empty ("CHECKPOINT FORMAT ERRORS") with no actionable detail -- the fix prompt template degrades after fix 2. |
| Review | 2 fix attempts | "Давай" calque, fabricated distractors "требом", nominative-case distractors in accusative-context fill-in. | PARTIALLY -- calque could be caught by expanded Russianisms list. Distractor quality needs explicit template rule. |

## Suggested Template Fixes

### Fix 1: Add "Давай + future" to Russianisms Checklist (Priority: HIGH)

**Before** (phase-2-prompt.md, Russianisms table):
```
| кушати | їсти |
| приймати участь | брати участь |
```

**After:**
```
| кушати | їсти |
| приймати участь | брати участь |
| Давай + 1st person plural future (Давай поїдемо) | Synthetic -мо imperative (Поїдьмо) |
```

Cross-module applicability: Any module M47+ teaching imperatives.

### Fix 2: Add Fixed-Chunk Exception Mechanism to LEVEL_CONSTRAINTS (Priority: HIGH)

**Before** (placeholders.yaml, LEVEL_CONSTRAINTS):
```
- Dative case FORBIDDEN (no мені, тобі, йому...)
  Exception: нам is taught as decodable vocabulary in M1
```

**After:**
```
- Dative case FORBIDDEN (no мені, тобі, йому...)
  Exception: нам is taught as decodable vocabulary in M1
  Exception (M19): Dative in «Мені подобається» construction
  Exception: Any dative/instrumental forms listed in plan vocabulary_hints as "fixed chunks" are permitted without case explanation.
```

Cross-module applicability: All A1 modules that teach fixed expressions with otherwise-forbidden cases.

### Fix 3: Ban Fabricated Distractor Forms in Activities Template (Priority: HIGH)

**Before** (phase-C-prompt.md, Activity Quality Rules):
```
2. **Plausible, clear items.** Every question must have one unambiguous correct answer.
```

**After:**
```
2. **Plausible, clear items.** Every question must have one unambiguous correct answer.
3. **All distractors must be real Ukrainian words.** NEVER invent declined, conjugated, or otherwise morphed forms that do not exist (e.g., "требом", "требі" for the indeclinable word "треба"). Use semantically plausible but incorrect real words instead.
```

### Fix 4: Remove Irrelevant Bukvar Examples for M15+ Modules (Priority: MEDIUM)

The "Textbook Reference Examples" section injects Grade 1 syllable/letter exercises regardless of module sequence number. For M15+ modules, these examples waste prompt tokens and can mislead the model about the expected content level.

**Fix:** Conditionally include textbook examples only for M1-M14 (Cyrillic primer modules). For M15+, replace with level-appropriate example snippets or omit entirely.

### Fix 5: Standardize Section Title Format (Priority: MEDIUM)

Require all meta outline section titles to use bilingual format: "Ukrainian Title (English Translation)". This prevents the section-mismatch validation failure seen in fix 1.

### Fix 6: Improve Fix Prompt Specificity After Attempt 2 (Priority: LOW)

Fix prompts 3 and 4 contain only "CHECKPOINT FORMAT ERRORS" with no actionable detail. The fix prompt generator should always include the specific error message and location, even for format-only issues.

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Add "Давай + future" calque to Russianisms checklist -- prevents the most common Ukrainian language quality issue found in review
2. Add fixed-chunk exception mechanism to LEVEL_CONSTRAINTS -- prevents contradictory guidance that caused 3 of 4 validation fix attempts
3. Ban fabricated distractor forms in activities template -- prevents hallucinated morphology that harms beginner safety
