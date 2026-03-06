        # Fix 4 issue(s) in `demonstratives-this-that`

        ### Fix 1: IPA_BANNED
**What:** Banned IPA transcription: [pointing to the counter]
**How to fix:** Remove phonetic brackets. Use only stress marks (´) for pronunciation.
**Where:** ~line 142

### Fix 2: IPA_BANNED
**What:** Banned IPA transcription: [pointing behind the vendor]
**How to fix:** Remove phonetic brackets. Use only stress marks (´) for pronunciation.
**Where:** ~line 143

### Fix 3: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Виберіть' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 165):** `А тепер невелика самоперевірка. Виберіть правильне українське слово.`

### Fix 4: PLAN_SECTION_MISSING
**What:** Missing 2 plan section(s): Цей vs Той у контексті (This vs That in context), Практика (Practice)
**How to fix:** Add content for the missing plan sections or update section headings to match plan.
**Where:** (plan vs content)

### Other Audit Failures

```
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

