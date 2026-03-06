        # Fix 7 issue(s) in `shopping-and-market`

        ### Fix: Gate `Pedagogy` FAIL — 4 violations

### Fix: Gate `Immersion` FAIL — 24.4% LOW (target 35-55% (M40))
**Action:** Add more Ukrainian-language content blocks. Convert some English explanations to Ukrainian with English glosses.

### Fix 3: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'Мені'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 4: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'Мені'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 5: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'Мені'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 6: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Ми ло мо жна купи...'

### Fix 7: PEDAGOGICAL_VIOLATION
**What:** [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'скі́льки кошту́є...'.
**How to fix:** Vary sentence structure.

### Other Audit Failures

```
❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'скі́льки кошту́є...'.
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/shopping-and-market-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/shopping-and-market.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/shopping-and-market.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/shopping-and-market.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

