# Prompt Engineering Review: prohibitions-and-signs

**Track:** a1 | **Sequence:** 55
**Pipeline:** v4
**Validate attempts:** 3
**Friction reports:** 2 (content: 1, activities: 1)
**Review outcome:** FAIL (Overall 5.3/10 -- severe linguistic hallucination)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Contradictory constraint: imperative forbidden vs module teaches imperative contrast | HIGH | phase-2-prompt.md, placeholders.yaml | PEDAGOGICAL_CONSTRAINTS says "Imperative forms NOT taught until M47" but M55 explicitly contrasts infinitive signs vs imperative spoken commands ("Не торкатися!" vs "Не чіпай!"). The research output even flags this: "contrast impersonal sign language vs personal commands conceptually". The constraint is stale for M47+ modules. |
| Textbook reference examples completely irrelevant | MEDIUM | phase-2-prompt.md | Lines 38-208 inject Grade 1 bukvar exercises (syllable drills for letters з, в, ф, дз) as "inspiration" for M55 teaching prohibition signs and street navigation. Zero pedagogical relevance. |
| Word target ambiguity leading to massive overproduction | MEDIUM | phase-2-prompt.md | Target says "approximately 1200 words" but the module produced 4039 words (337% of target). The "approximately" qualifier combined with the "Output capacity: 65,000+ tokens" note and the EXPANSION_METHOD rules ("write deeper") apparently encouraged massive overproduction. The 1200 target was a minimum, not a ceiling, but 3x overshoot wastes tokens and creates more surface area for errors. |
| Meta outline includes IPA instruction despite IPA ban | LOW | phase-A-output.md | Research outline point 4 says "Provide IPA for the first occurrence of each word" but the content prompt explicitly bans IPA. Contradictory instruction across phases. |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| No specific відкрито/відчинено distinction in prompt constraints | HIGH | The research correctly identifies "відкрито vs відчинено" as a key learner error, but the content prompt's Russianisms checklist does not include this pair. Gemini hallucinated "роботу" instead of "відкрито" -- a catastrophic error that would have been caught if the specific Surzhyk pair was listed. |
| Discovery results entirely irrelevant | LOW | RAG chunks returned grade 3-9 grammar pages about antonyms, compound sentences, and announcements -- nothing about prohibition signs, street vocabulary, or the відчинено/зачинено distinction. The discovery phase added zero value to this build. |
| No collocation examples in vocabulary hints | MEDIUM | Plan vocabulary_hints presumably listed lemmas but not usage contexts. The Richness score gap shows "collocations: 0/20" -- the template does not prompt for collocations in vocabulary output. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|----------------|---------|--------------|
| Catastrophic hallucination: "роботу" instead of "відкрито" | model_limitation + context_gap | Gemini confused "робота" (work) with "відкрито" (opened) in 3+ locations, teaching beginners a completely fabricated Surzhyk error. The research correctly identified the відкрито/відчинено pair, but the content prompt did not surface this specific contrast as a critical vocabulary item. The model hallucinated under insufficient context about this specific lexical distinction. | Add відкрито/відчинено to the Russianisms/Surzhyk checklist. Add a "CRITICAL VOCABULARY CONTRASTS" section to the content prompt that surfaces plan-specific lexical distinctions requiring precision. |
| English calques throughout text | model_limitation | "зберегти гроші" (save money = keep safe), "говорить до людини" (speaks to a person), "мати увагу" (have attention). These are direct English-to-Ukrainian translations that are grammatically wrong. | Expand the Russianisms/calques checklist to include common English calques: зберегти гроші -> заощадити гроші, мати увагу -> привернути увагу. |
| Dative "вам" used despite A1 ban (fix 3) | conflicting_guidance | Same pattern as M54: LEVEL_CONSTRAINTS bans Dative but module naturally needs it. Fix prompt told Gemini to restructure sentences, adding fix loop cost. | Same fix as M54: flexible exception mechanism. |
| Massive word count overproduction (4039 vs 1200) | template_gap | The content prompt gives a soft target ("approximately 1200") but structural rules demand depth per concept, engagement boxes, and the EXPANSION_METHOD encourages writing more. No upper bound is specified. The model produced 3.4x the target, creating more surface area for errors. | Add explicit upper bound: "Target: 1200 words. Acceptable range: 1200-1800. Do NOT exceed 1800 words -- additional depth should come from precision, not volume." |
| Section title mismatch (fix 1) | schema_mismatch | Same pattern as M54. Audit expected bilingual titles but content used different format. | Same fix: standardize bilingual title format in meta outline. |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|-----------|--------------|
| Validate | 3 | Fix 1: unclear audit failure (generic error). Fix 2: section-level fix for "На вулиці" (unclear trigger). Fix 3: Dative "вам" flagged in 2 locations. | Fix 3 preventable with exception mechanism. Fix 1-2 had vague prompts with no specific error details. |
| Review | 2 fix attempts | Hallucinated "роботу" error (3 locations), English calques, Dative construction, robotic LLM phrasing. | The hallucination is model_limitation but partially preventable by surfacing the research-identified відкрито/відчинено contrast as a CRITICAL item in the content prompt. |

## Suggested Template Fixes

### Fix 1: Add Surzhyk Pairs to Content Prompt Checklist (Priority: HIGH)

The research phase correctly identified the відкрито/відчинено vs закрито/зачинено distinction as a critical learner error, but this knowledge was not surfaced as a hard constraint in the content prompt.

**Before** (phase-2-prompt.md, Russianisms table):
```
| красивий | гарний |
| прекрасне / прекрасний | чудовий / чудове |
```

**After:**
```
| красивий | гарний |
| прекрасне / прекрасний | чудовий / чудове |
| відкрито (for doors/shops) | відчинено |
| закрито (for doors/shops) | зачинено |
```

Additionally, add a pipeline step: **Auto-inject research-identified error pairs into the content prompt's constraint section.** The research phase already discovers these -- they should flow automatically to the content builder.

### Fix 2: Add English Calque Checklist (Priority: HIGH)

The Russianisms checklist catches Russian interference but not English interference, which is the primary error source for Gemini (an English-dominant model).

**New section in content template:**
```
### English Calques (WARNING if found)

| English Calque | Correct Ukrainian |
|---------------|-------------------|
| зберегти гроші (keep safe money) | заощадити / зекономити гроші |
| мати увагу (have attention) | привернути увагу |
| говорити до (speak to) | говорити з / звертатися до |
| давати для вас (give for you) | давати вам |
```

Cross-module applicability: ALL modules. English calques are a systematic Gemini weakness.

### Fix 3: Add Word Count Upper Bound (Priority: MEDIUM)

**Before** (phase-2-prompt.md):
```
- **Target**: approximately 1200 words
```

**After:**
```
- **Target**: 1200 words (acceptable range: 1200-1800). Do NOT exceed 1800 words.
  More words = more surface area for errors. Depth comes from precision, not volume.
```

This module produced 4039 words for a 1200-word target. The overproduction created more text to hallucinate in, more text to review, and more text to fix. For A1, shorter and more precise is always better.

### Fix 4: Conditionally Include Textbook Examples (Priority: MEDIUM)

Same as M54 recommendation. Grade 1 bukvar exercises are irrelevant for M15+ modules. The template should conditionally inject level-appropriate examples or omit them.

### Fix 5: Auto-Surface Research Findings as Hard Constraints (Priority: HIGH)

The research phase discovered "відкрито vs відчинено" as a critical error pair. But this finding was buried in research notes that the content builder may or may not have read carefully. The pipeline should automatically extract error pairs from research output and inject them into the content prompt's hard-constraint section.

**Implementation:** Parse `===RESEARCH_START===` for "Common Learner Errors" section, extract error->correction pairs, inject into content prompt's Russianisms/calques table.

### Fix 6: Validate Fix Prompts Need Specificity (Priority: LOW)

Fix prompts 1 and 2 for this module had no specific error details -- just "AUDIT FAILED" with a log reference. The model cannot fix what it cannot see. Fix prompts must always include the specific violation text.

## Summary

**Template health:** BROKEN
**Top 3 fixes by leverage:**
1. Auto-surface research error pairs into content prompt constraints -- would have prevented the catastrophic "роботу" hallucination, the module's worst error
2. Add English calque checklist -- Gemini systematically produces English calques that are as harmful as Russianisms but currently unchecked
3. Add word count upper bound -- 337% overproduction creates unnecessary error surface and wastes review/fix tokens
