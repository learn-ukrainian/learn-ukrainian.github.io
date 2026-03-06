# Prompt Engineering Review: prohibitions-and-signs

**Track:** a1 | **Sequence:** 55
**Pipeline:** v4
**Validate attempts:** 3
**Friction reports:** 2 (content: 1, activities: 1)
**Review outcome:** FAIL (Overall 5.3/10 -- severe linguistic hallucination)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Contradictory constraint: imperative forbidden vs module teaches imperative contrast | HIGH | phase-2-prompt.md, placeholders.yaml | PEDAGOGICAL_CONSTRAINTS says "Imperative forms NOT taught until M47" but M55 explicitly contrasts infinitive signs vs imperative spoken commands. The constraint is stale for M47+ modules. |
| Textbook reference examples completely irrelevant | MEDIUM | phase-2-prompt.md | Grade 1 bukvar exercises (syllable drills for letters) injected as "inspiration" for M55 teaching prohibition signs and street navigation. Zero pedagogical relevance. |
| Word target ambiguity leading to massive overproduction | MEDIUM | phase-2-prompt.md | Target says "approximately 1200 words" but the module produced 4039 words (337% of target). No upper bound specified. Combined with EXPANSION_METHOD rules encouraging depth, the model dramatically overproduced. |
| Meta outline includes IPA instruction despite IPA ban | LOW | phase-A-output.md | Research outline says "Provide IPA for the first occurrence" but the content prompt bans IPA. |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| No specific відкрито/відчинено distinction in prompt constraints | HIGH | Research correctly identifies this as a key learner error, but the Russianisms checklist omits it. Gemini hallucinated "роботу" instead -- a catastrophic error preventable by explicit constraint. |
| Discovery results entirely irrelevant | LOW | RAG returned grade 3-9 grammar pages with nothing about prohibition signs or the відчинено/зачинено distinction. |
| No collocation examples in vocabulary hints | MEDIUM | Richness gap: "collocations: 0/20". Template does not prompt for collocations. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|----------------|---------|--------------|
| Catastrophic hallucination: "роботу" instead of "відкрито" | model_limitation + context_gap | Gemini confused "робота" (work) with "відкрито" (opened) in 3+ locations, teaching a fabricated Surzhyk error. Research identified the correct pair but it was not surfaced as a hard constraint. | Auto-inject research error pairs into content prompt. Add відкрито/відчинено to Surzhyk checklist. |
| English calques throughout text | model_limitation | "зберегти гроші", "говорить до людини", "мати увагу" -- direct English-to-Ukrainian translations. | Add English calque checklist to content template. |
| Dative "вам" flagged (fix 3) | conflicting_guidance | Same pattern as M54: LEVEL_CONSTRAINTS bans Dative but module naturally needs it. | Flexible exception mechanism. |
| Massive overproduction (4039 vs 1200) | template_gap | No upper bound + expansion encouragement = 337% overshoot. More text = more error surface. | Add explicit upper bound (1200-1800 range). |
| Section title mismatch (fix 1) | schema_mismatch | Same as M54. Audit expected bilingual titles. | Standardize format. |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|-----------|--------------|
| Validate | 3 | Fix 1-2: vague error messages with no specifics. Fix 3: Dative "вам" in 2 locations. | Fix 3 preventable with exception mechanism. Fix 1-2 had uninformative prompts. |
| Review | 2 fix attempts | Hallucinated "роботу", English calques, Dative construction, robotic phrasing. | Hallucination partially preventable by surfacing research findings as hard constraints. |

## Suggested Template Fixes

### Fix 1: Auto-Surface Research Error Pairs into Content Prompt (Priority: HIGH)
Parse research "Common Learner Errors" and inject as hard constraints. Would have prevented the "роботу" catastrophe.

### Fix 2: Add English Calque Checklist (Priority: HIGH)
Gemini systematically produces English calques uncaught by the current Russianisms-only checklist.

### Fix 3: Add Word Count Upper Bound (Priority: MEDIUM)
"Target: 1200 words. Acceptable range: 1200-1800. Do NOT exceed 1800."

### Fix 4: Add Surzhyk Pairs to Checklist (Priority: HIGH)
відкрито/відчинено, закрито/зачинено must be explicit.

### Fix 5: Conditionally Include Textbook Examples (Priority: MEDIUM)
Grade 1 bukvar irrelevant for M15+.

### Fix 6: Validate Fix Prompts Need Specificity (Priority: LOW)
Fix 1-2 had only "AUDIT FAILED" with no details.

## Summary

**Template health:** BROKEN
**Top 3 fixes by leverage:**
1. Auto-surface research error pairs into content prompt constraints -- prevents catastrophic hallucinations
2. Add English calque checklist -- systematic Gemini weakness currently unchecked
3. Add word count upper bound -- 337% overproduction wastes tokens and increases error surface
