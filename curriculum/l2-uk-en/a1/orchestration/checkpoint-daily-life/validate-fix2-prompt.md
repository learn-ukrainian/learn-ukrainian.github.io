        # Fix 6 issue(s) in `checkpoint-daily-life`

        ### Fix: Gate `Structure` FAIL — Missing '## Summary'

### Fix: Gate `Pedagogy` FAIL — 3 violations

### Fix 3: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'пові'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 4: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Grammar Check: Past and Future' Q2 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 5: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Grammar Check: Past and Future' Q7 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 6: PEDAGOGICAL_VIOLATION
**What:** [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'can you...'.
**How to fix:** Vary sentence structure.

### Other Audit Failures

```
❌ CHECKPOINT FORMAT ERRORS:
❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'can you...'.
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/checkpoint-daily-life-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/checkpoint-daily-life.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/checkpoint-daily-life.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/checkpoint-daily-life.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

