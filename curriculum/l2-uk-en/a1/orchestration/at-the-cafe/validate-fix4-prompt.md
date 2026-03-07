        # Fix 5 issue(s) in `at-the-cafe`

        ### Fix 1: AGREEMENT_ERROR
**What:** Agreement mismatch: 'можна' (f) + 'меню́' (n/p)
**How to fix:** Change 'можна' to match the gender/case of 'меню́', or vice versa.
**Where:** ~line 122

### Fix 2: AGREEMENT_ERROR
**What:** Agreement mismatch: 'можна' (f) + 'во́ду' (f)
**How to fix:** Change 'можна' to match the gender/case of 'во́ду', or vice versa.
**Where:** ~line 123

### Fix 3: AGREEMENT_ERROR
**What:** Agreement mismatch: 'можна' (f) + 'раху́нок' (m)
**How to fix:** Change 'можна' to match the gender/case of 'раху́нок', or vice versa.
**Where:** ~line 139

### Fix: Gate `Pedagogy` FAIL — 1 violations

### Fix 5: PEDAGOGICAL_VIOLATION
**What:** [HEADING_LEVEL] Main section 'Summary' uses H2 (##) but spec requires H1 (#)
**How to fix:** Change '## Summary' to '# Summary' for top-level TOC compliance

### Other Audit Failures

```
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/at-the-cafe-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

BANNED IMPERATIVE FORMS (non-exhaustive): Запам'ятайте, Уявіть, Порівняйте, Зверніть увагу, Спробуйте, Подивіться, Послухайте, Прочитайте, Повторіть, Напишіть, Скажіть, Виберіть, Подивімось, Поговорімо, Повторімо, Давайте розглянемо, Розглянемо.

INSTEAD OF → USE:
- Запам'ятайте → "Remember that..." (English)
- Порівняйте → "Compare..." (English)
- Зверніть увагу → "Notice that..." (English)
- Подивіться → "Look at..." (English)
- Спробуйте → "Try to..." (English)
- Прочитайте → "Read..." (English)
- Повторіть → "Repeat..." (English)

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-cafe.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/at-the-cafe.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/at-the-cafe.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

