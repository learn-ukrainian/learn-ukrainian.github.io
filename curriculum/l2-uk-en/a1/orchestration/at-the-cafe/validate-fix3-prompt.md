        # Fix 5 issue(s) in `at-the-cafe`

        ### Fix 1: IPA_BANNED
**What:** Banned IPA transcription: [Accusative]
**How to fix:** Remove phonetic brackets. Use only stress marks (´) for pronunciation.
**Where:** ~line 82

### Fix 2: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Порівняйте' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 85):** `Порівняйте (Compare):`

### Fix: Gate `Pedagogy` FAIL — 1 violations

### Fix: Gate `Immersion` FAIL — 25.2% LOW (target 35-55% (M41))
**Action:** Add more Ukrainian-language content blocks. Convert some English explanations to Ukrainian with English glosses.

### Fix 5: PEDAGOGICAL_VIOLATION
**What:** [HEADING_LEVEL] Main section 'Summary' uses H2 (##) but spec requires H1 (#)
**How to fix:** Change '## Summary' to '# Summary' for top-level TOC compliance

### Other Audit Failures

```
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/at-the-cafe-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-cafe.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/at-the-cafe.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/at-the-cafe.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

