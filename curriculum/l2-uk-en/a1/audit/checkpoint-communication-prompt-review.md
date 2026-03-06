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
| Research output mentions IPA despite IPA being banned | LOW | phase-A-output.md / meta outline | Research outline point says "Provide IPA for the first occurrence" but the content prompt bans IPA. Contradictory instruction across phases. |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| No prior module content injected (M53 at-the-restaurant) | LOW | Checkpoint modules review skills from prior modules but the prompt has no visibility into what M47-M53 actually taught. Builder must guess or read files. |
| Plan's activity_hints not surfaced in content prompt | MEDIUM | The plan required a single 30-item comprehensive quiz, but neither the content nor activities prompt surfaced this requirement explicitly. Activities prompt only shows "Required types: (empty)". Result: quiz was split into smaller activities, flagged as missing by review. |
| Discovery results poor quality / irrelevant | LOW | RAG chunks are grade 4-10 grammar textbook pages about verb conjugation, not about communication checkpoints. Discovery found no videos and only tangentially relevant blogs. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|----------------|---------|--------------|
| PLAN_SECTION_MISSING (fix 1) | schema_mismatch | Section titles in content used Ukrainian-only names while audit expected bilingual format with parenthetical English translations. | Standardize section title format in meta outline template: always require bilingual "Ukrainian (English)" format. |
| Dative case flagged as forbidden (fix 2-4) | conflicting_guidance | LEVEL_CONSTRAINTS says "Dative FORBIDDEN" but the plan explicitly requires "мені треба" as a fixed chunk. The validator cannot distinguish between forbidden grammar and plan-approved fixed chunks. | Add an exception list to LEVEL_CONSTRAINTS for plan-approved fixed expressions. |
| Russian calque "Давай зустрінемось" (review) | model_limitation | Gemini generated the colloquial Russian-influenced "Давай + future" pattern instead of standard Ukrainian synthetic imperatives. The content prompt's Russianisms checklist does not include this pattern. | Add "Давай + 1st person plural future" to the Russianisms checklist. |
| Fabricated word forms as distractors "требом" (review) | model_limitation | Gemini invented morphologically impossible declined forms of the indeclinable word "треба" as activity distractors. | Add explicit rule: "NEVER invent morphological forms that do not exist. All distractors must be real Ukrainian words." |
| Quiz question prompt length violations (fix 2) | template_gap | Audit flagged quiz question prompts as too long (16 words vs 5-10 target) but the activities prompt specifies no prompt length constraint. | Add explicit prompt length guidance to activities template. |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|-----------|--------------|
| Validate | 4 | Fix 1: section title mismatch. Fix 2: Dative flagged despite being plan-approved. Fix 3-4: residual checkpoint format errors with no actionable detail in fix prompts. | YES for fix 1-2. Fix 3-4 prompts lack specificity. |
| Review | 2 fix attempts | "Давай" calque, fabricated distractors, nominative-case distractors in accusative context. | PARTIALLY preventable with expanded checklists. |

## Suggested Template Fixes

### Fix 1: Add "Давай + future" to Russianisms Checklist (Priority: HIGH)
Cross-module applicability: Any module M47+ teaching imperatives.

### Fix 2: Add Fixed-Chunk Exception Mechanism to LEVEL_CONSTRAINTS (Priority: HIGH)
Cross-module applicability: All A1 modules with plan-approved fixed expressions.

### Fix 3: Ban Fabricated Distractor Forms in Activities Template (Priority: HIGH)
Add: "NEVER invent morphological forms that do not exist. All distractors must be real Ukrainian words."

### Fix 4: Remove Irrelevant Bukvar Examples for M15+ Modules (Priority: MEDIUM)
Conditionally include textbook examples only for M1-M14.

### Fix 5: Standardize Section Title Format (Priority: MEDIUM)
Require bilingual "Ukrainian (English)" format in meta outline.

### Fix 6: Improve Fix Prompt Specificity After Attempt 2 (Priority: LOW)
Fix prompts 3-4 had no actionable detail.

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Add "Давай + future" calque to Russianisms checklist
2. Add fixed-chunk exception mechanism to LEVEL_CONSTRAINTS
3. Ban fabricated distractor forms in activities template
