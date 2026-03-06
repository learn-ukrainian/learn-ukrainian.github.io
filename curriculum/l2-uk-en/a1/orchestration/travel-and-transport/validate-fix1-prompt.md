        # Fix 2 issue(s) in `travel-and-transport`

        ### Fix 1: PLAN_SECTION_MISSING
**What:** Missing 5 plan section(s): Транспорт (Transport types), Вокзал та аеропорт (Station and airport), Напрямки (Directions), Подорожі (Journeys), Практика (Practice)
**How to fix:** Add content for the missing plan sections or update section headings to match plan.
**Where:** (plan vs content)

### Fix 2: ACTIVITY_VESUM_FAIL
**What:** Activity answers contain VESUM-failed words: Антон
**How to fix:** Fix spelling or replace these words — students will practice non-existent forms.
**Where:** travel-and-transport.yaml

### Other Audit Failures

```
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/travel-and-transport-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/travel-and-transport.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/travel-and-transport.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/travel-and-transport.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

