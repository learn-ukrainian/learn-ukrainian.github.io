        # Fix 6 issue(s) in `demonstratives-this-that`

        ### Fix: Gate `Pedagogy` FAIL — 1 violations

### Fix: Gate `Immersion` FAIL — 25.1% LOW (target 35-55% (M21))
**Action:** Add more Ukrainian-language content blocks. Convert some English explanations to Ukrainian with English glosses.

### Fix 3: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'мові'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 4: PEDAGOGICAL_VIOLATION
**What:** [METALANGUAGE] Metalanguage terms used but not in vocabulary: однина
**How to fix:** Add these grammar terms to vocabulary with translations, or use English equivalents.

### Fix 5: PEDAGOGICAL_VIOLATION
**What:** [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'which word...'.
**How to fix:** Vary sentence structure.

### Fix 6: PEDAGOGICAL_VIOLATION
**What:** [VOCAB_NOT_IN_CONTENT] Only 12/20 (60%) vocabulary words appear in content+activities. Missing: кожний, сам, той, це, цей, ця, ці, інший
**How to fix:** Integrate missing vocabulary words into the prose or activities. Each vocab word should appear at least once in context.

### Other Audit Failures

```
❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'which word...'.
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/demonstratives-this-that-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/demonstratives-this-that.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/demonstratives-this-that.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/demonstratives-this-that.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

