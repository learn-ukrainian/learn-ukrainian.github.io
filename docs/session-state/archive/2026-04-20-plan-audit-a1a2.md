# Plan Audit — A1 + A2 readiness as immutable contract
Date: 2026-04-20

## Summary
- A1: 55 plans total, 55 ready, 0 with issues
- A2: 69 plans total, 66 ready, 3 with issues
- Overall verdict: NEEDS-FIXES

## A1 — plans with issues (grouped by severity)

### BLOCKER (cannot build without fix)
None. All 55 plans have the required structure, non-empty fields, and valid references.

### NEEDS-FIX (buildable but quality risk)
None.

### NITPICK (minor polish)
- Almost all A1 plans (e.g., `my-day`, `things-have-gender`, `this-and-that`, `where-to`) have items within the `content_outline` that are very short or vague (under 4 words). Examples include bare topic headers instead of descriptive guidance like "Introduce past tense for perfective verbs...". Consider expanding these for better generation guidance.

## A2 — plans with issues

### BLOCKER (cannot build without fix)
None. All 69 plans have the required structure, non-empty fields, and valid references.

### NEEDS-FIX (buildable but quality risk)
- `metalanguage-syntax-cases`: Unexpected `word_target` 4000 (expected one of [2000, 1500])
- `metalanguage-phonetics`: Unexpected `word_target` 4000 (expected one of [2000, 1500])
- `metalanguage-morphology`: Unexpected `word_target` 4000 (expected one of [2000, 1500])

### NITPICK (minor polish)
- Similar to A1, the majority of A2 plans (e.g., `relative-clauses`, `dative-verbs`, `because-and-although`, `aspect-mastery`) have items in the `content_outline` that are very short or vague. While buildable, expanding the prompt detail will improve the quality of the LLM generation.

## Cross-plan issues
- **Forward-references**: No broken or unresolved forward-references detected. The plans primarily refer to concepts organically without hardcoded `A1/M01` style syntax errors.
- **Inconsistent vocabulary scoping**: None detected programmatically.
- **Gaps in topic progression**: None explicitly found.

## Recommendation
- **NEEDS-FIXES**: The 3 `metalanguage-*` A2 plans have an anomalous `word_target: 4000`. These should be corrected to the standard `2000` (or `1500` if they are checkpoint modules).
- This is a minor metadata fix that should take less than 5 minutes to apply across the 3 files. Once corrected, the batch build is **READY** to green light.
