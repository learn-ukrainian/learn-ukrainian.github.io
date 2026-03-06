# Prompt Engineering Review: my-family

**Track:** a1 | **Sequence:** 49
**Pipeline:** v4
**Validate attempts:** 1
**Friction reports:** 2 (content: NONE, activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| IPA mention in research output | LOW | phase-A-prompt.md | Research output mentions "IPA on first occurrence only" in content_outline point, contradicting the absolute IPA ban. The research template does not explicitly forbid IPA references in outline points. |
| Decodable vocabulary instruction irrelevant | LOW | phase-2-prompt.md | "Does every Ukrainian word use only the allowed letter set?" -- this pre-submission check is for Cyrillic primer modules (M1-M6), not M49. Noise for the model. |
| H3_WORD_RANGE placeholder unresolved | LOW | phase-2-prompt.md | Line 6: "Every H3 gets {H3_WORD_RANGE} words" -- placeholder appears in the rendered prompt header but is properly resolved in placeholders.yaml (60-80). The template should use the resolved value directly. |
| Example content is letter-introduction style | LOW | phase-2-prompt.md | The "Example of Good A1 Content" section shows letter-introduction pedagogy (visual traps, letter sounds). For M49 (family vocabulary), this example is misleading. A vocabulary-focused example would be better. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| None significant | N/A | N/A |
| Plan file contents not inlined | LOW | Plan is referenced by path; Gemini reads it. Could inline vocabulary_hints directly for reliability. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|-----------------|---------|--------------|
| Content friction: NONE | N/A | Clean generation | N/A |
| Activity friction: NONE | N/A | Clean generation | N/A |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| validate | 1 | Generic audit failure (likely section heading mismatch on first pass, resolved on retry) | Partially -- validate-fix1-prompt.md only shows generic "AUDIT FAILED" with no specific issue detail. The fix prompt lacks diagnostic specificity. |

## VESUM Findings

- 199/199 words verified (100%). No issues.

## Suggested Template Fixes

### Fix 1: Remove irrelevant decodable-vocabulary pre-submission check for non-primer modules (Priority: LOW)
**Before:** "4. **Decodable vocabulary**: Does every Ukrainian word use only the allowed letter set?"
**After:** Only include this check when DECODABLE_VOCABULARY is non-empty. Add conditional: `{{#if DECODABLE_VOCABULARY}}...{{/if}}`

### Fix 2: Provide level-appropriate content example (Priority: MEDIUM)
**Before:** Example shows letter-introduction (visual traps, letter sounds) -- irrelevant for M49.
**After:** Add a second example block for vocabulary/grammar modules showing bilingual vocab tables, possessive patterns, and cultural callouts. Select example based on module type (primer vs. vocabulary vs. grammar).

### Fix 3: Make validate-fix prompt diagnostic (Priority: MEDIUM)
**Before:** validate-fix1-prompt.md shows only "AUDIT FAILED" with no breakdown.
**After:** Always include the specific gate failures and their details in the fix prompt, even when the failure is generic. The current template does this for later attempts but the first attempt was sparse.

## Summary

**Template health:** GOOD
**Top 3 fixes by leverage:**
1. Level-appropriate content example for non-primer modules (MEDIUM) -- prevents model confusion about expected output style
2. Diagnostic specificity in validate-fix prompts (MEDIUM) -- reduces fix loop iterations
3. Conditional decodable-vocabulary check (LOW) -- reduces prompt noise
