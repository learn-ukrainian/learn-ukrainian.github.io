        # Fix 23 issue(s) in `body-and-health`

        ### Fix: Gate `Density` FAIL — 6 < 6

### Fix: Gate `Pedagogy` FAIL — 19 violations

### Fix 3: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'голові'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 4: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'вам'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 5: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'вам'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 6: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'вам'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 7: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'є, що ф'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 8: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'и, що в'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 9: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'є, що ч'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 10: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'і, коли в'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 11: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'о, коли м'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 12: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'Якщо б'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 13: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'тому що в'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 14: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'бо я'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 15: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'бо в'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 16: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] fill-in 'Expressing Pain' has 6 items (minimum: 8)
**How to fix:** Add more items. A1 fill-in requires at least 8 items.

### Fix 17: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] fill-in 'Describing Symptoms' has 6 items (minimum: 8)
**How to fix:** Add more items. A1 fill-in requires at least 8 items.

### Fix 18: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] true-false 'True or False?' has 6 items (minimum: 8)
**How to fix:** Add more items. A1 true-false requires at least 8 items.

### Fix 19: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] unjumble 'Build the Sentences' has 5 items (minimum: 6)
**How to fix:** Add more items. A1 unjumble requires at least 6 items.

### Fix 20: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] quiz 'Health & Pharmacy Quiz' has 6 items (minimum: 8)
**How to fix:** Add more items. A1 quiz requires at least 8 items.

### Fix 21: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] fill-in 'Why? (Causes)' has 6 items (minimum: 8)
**How to fix:** Add more items. A1 fill-in requires at least 8 items.

### Fix 22: PEDAGOGICAL_VIOLATION
**What:** [METALANGUAGE] Metalanguage terms used but not in vocabulary: однина, множина
**How to fix:** Add these grammar terms to vocabulary with translations, or use English equivalents.

### Fix 23: PEDAGOGICAL_VIOLATION
**What:** [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'у ме́не...'.
**How to fix:** Vary sentence structure.

### Other Audit Failures

```
❌ Expressing Pain
❌ Describing Symptoms
❌ True or False?
❌ Build the Sentences
❌ Health & Pharmacy Quiz
❌ Why? (Causes)
❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'у ме́не...'.
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/body-and-health-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/body-and-health.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/body-and-health.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/body-and-health.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

