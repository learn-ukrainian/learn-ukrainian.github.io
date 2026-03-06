# Prompt Engineering Review: leisure-and-hobbies

**Track:** a1 | **Sequence:** 51
**Pipeline:** v4
**Validate attempts:** 2
**Friction reports:** 2 (content: Constraint Enforcement, activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Dative ban not explicit enough | HIGH | placeholders.yaml (LEVEL_CONSTRAINTS) | Constraint says "Dative case FORBIDDEN (no мені, тобі...)" but the model generated "Мені" 3 times and "Відповідь" false-positived. The word list in the ban is not exhaustive -- model found ways to use dative forms not listed. |
| Sentence length limit poorly enforced | HIGH | placeholders.yaml (LEVEL_CONSTRAINTS) | "Max 10 words per Ukrainian sentence (STRICT)" -- model generated 8 sentences exceeding this (11-14 words). The constraint is clear but the model ignores it. Needs stronger enforcement: count examples, penalty emphasis. |
| Subordinate clause ban incomplete | MEDIUM | placeholders.yaml (LEVEL_CONSTRAINTS) | "що-clause" is banned but model used "А що т..." (subordinate). The ban lists specific markers but model found workarounds. |
| PLAN_SECTION_MISSING false positive | MEDIUM | validate-fix1-prompt.md | Fix 1 says "Missing 5 plan sections" but these sections DO exist in the content -- the issue was likely a heading mismatch (different text encoding or whitespace). The fix prompt does not explain what constitutes a match vs. mismatch. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| No explicit dative word-form examples beyond the listed pronouns | HIGH | Expand the dative ban to include: "Any word form ending in -і that is a dative (мові, відповіді, etc.) is also banned. When in doubt, use a different construction." |
| No sentence-counting example | MEDIUM | Add worked example: "WRONG: 'Ми можемо говорити про наше хобі дуже довго.' (11 words) -> RIGHT: 'Ми говоримо про хобі.' (4 words) + 'Це дуже цікаво.' (3 words)" |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|-----------------|---------|--------------|
| Content: Constraint Enforcement | template_gap | Model noted difficulty separating Ukrainian/English but managed. Real issue: constraints not strict enough to prevent dative/long sentences. | Expand dative ban examples; add sentence-counting examples |
| validate-fix1: PLAN_SECTION_MISSING | schema_mismatch | Heading matching algorithm too strict on exact Unicode match. 5 sections flagged as "missing" that clearly exist. | Fix the section-matching algorithm, not the prompt |
| validate-fix2: 21 issues (19 pedagogy) | conflicting_guidance | Dative (3x), subordinate clause (1x), sentence length (9x), robotic structure (1x). All preventable with stronger prompt constraints. | See suggested fixes below |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| validate | 2 | Fix1: section heading mismatch (false positive). Fix2: 19 pedagogical violations -- dative, sentence length, subordinate clauses. | YES -- stronger constraint examples and enforcement in the content prompt would prevent most of these. The section-matching issue is a tooling bug. |

## VESUM Findings

- 238/239 (99.6%) verified
- Not found: "Оксано" (proper noun vocative -- expected, not a real issue)

## Suggested Template Fixes

### Fix 1: Expand dative ban with concrete examples (Priority: HIGH)
**Before:** "Dative case FORBIDDEN (no мені, тобі, йому, їй, вам, їм, -ові/-еві endings)"
**After:** "Dative case FORBIDDEN. Banned forms include but are not limited to: мені, тобі, йому, їй, вам, їм, AND any noun/adjective in dative (-ові/-еві/-і dative endings). Examples of WRONG dative usage: 'Відповідь мені' -> 'Моя відповідь'; 'Мені подобається' -> 'Я люблю'. If a sentence requires dative, rewrite using a different construction."
**Cross-module:** All A1 modules.

### Fix 2: Add sentence-counting enforcement with examples (Priority: HIGH)
**Before:** "Max 10 words per Ukrainian sentence (STRICT -- count every word)"
**After:** Add: "ENFORCEMENT: Before finalizing EACH Ukrainian sentence, count every word including prepositions, pronouns, and particles. Example: 'Ми | можемо | говорити | про | наше | хобі | дуже | довго' = 8 words (OK). 'Деякі | види | спорту | дуже | популярні | в | Україні | серед | молоді' = 9 words (OK but borderline). Split any sentence at 10+ words."
**Cross-module:** All A1 modules.

### Fix 3: Fix section-heading matching algorithm (Priority: MEDIUM)
**Issue:** PLAN_SECTION_MISSING false positive flagging existing sections.
**Fix:** This is a tooling issue in the audit script, not a prompt issue. The section matcher should normalize Unicode and whitespace before comparing.

### Fix 4: Add robotic-structure prevention to content prompt (Priority: LOW)
**Before:** Anti-robotic rules exist in SHARED_CONTENT_RULES but are easy to miss.
**After:** Move the "No 3+ sentences starting with the same phrase" rule into the main Writing Instructions section with a concrete example.

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Expand dative ban with exhaustive examples and alternative constructions (HIGH) -- prevents the most common pedagogical violation
2. Add sentence-counting enforcement with worked examples (HIGH) -- 9 of 19 violations were sentence-length
3. Fix section-heading matching algorithm (MEDIUM) -- eliminates false-positive fix loops
