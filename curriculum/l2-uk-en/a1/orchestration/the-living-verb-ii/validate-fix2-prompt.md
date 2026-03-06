        # Fix 2 issue(s) in `the-living-verb-ii`

        ### Fix: Gate `Immersion` FAIL — 13.3% LOW (target 25-40% (M16))
**Action:** Add more Ukrainian-language content blocks. Convert some English explanations to Ukrainian with English glosses.

### Fix 2: PEDAGOGICAL_VIOLATION
**What:** [CONTENT_REDUNDANCY] Redundant information detected in lesson (88% overlap): "Now, we are ready to explore the second major family of Ukrainian action words.". Shares significant keywords with sentence at index 2.
**How to fix:** Remove redundant paragraphs. Ensure each section adds new unique value.

### Other Audit Failures

```
❌ [CONTENT_REDUNDANCY] Redundant information detected in lesson (88% overlap): "Now, we are ready to explore the second major family of Ukrainian action words.". Shares significant keywords with sentence at index 2.
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-living-verb-ii-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-living-verb-ii.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-living-verb-ii.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-living-verb-ii.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

