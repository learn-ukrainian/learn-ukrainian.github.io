        # Fix 14 issue(s) in `at-the-cafe`

        ### Fix 1: AGREEMENT_ERROR
**What:** Agreement mismatch: 'української' (f) + 'частина' (f)
**How to fix:** Change 'української' to match the gender/case of 'частина', or vice versa.
**Where:** ~line 11

### Fix 2: AGREEMENT_ERROR
**What:** Agreement mismatch: 'щирої' (f) + 'символ' (m)
**How to fix:** Change 'щирої' to match the gender/case of 'символ', or vice versa.
**Where:** ~line 19

### Fix 3: AGREEMENT_ERROR
**What:** Agreement mismatch: 'мо́жна' (f) + 'слово' (n)
**How to fix:** Change 'мо́жна' to match the gender/case of 'слово', or vice versa.
**Where:** ~line 119

### Fix 4: AGREEMENT_ERROR
**What:** Agreement mismatch: 'Мо́жна' (f) + 'меню́' (n/p)
**How to fix:** Change 'Мо́жна' to match the gender/case of 'меню́', or vice versa.
**Where:** ~line 122

### Fix 5: AGREEMENT_ERROR
**What:** Agreement mismatch: 'Мо́жна' (f) + 'во́ду' (f)
**How to fix:** Change 'Мо́жна' to match the gender/case of 'во́ду', or vice versa.
**Where:** ~line 123

### Fix 6: AGREEMENT_ERROR
**What:** Agreement mismatch: 'Мо́жна' (f) + 'раху́нок' (m)
**How to fix:** Change 'Мо́жна' to match the gender/case of 'раху́нок', or vice versa.
**Where:** ~line 139

### Fix 7: AGREEMENT_ERROR
**What:** Agreement mismatch: 'Яку́' (f) + 'Бариста' (f/m)
**How to fix:** Change 'Яку́' to match the gender/case of 'Бариста', or vice versa.
**Where:** ~line 165

### Fix 8: AGREEMENT_ERROR
**What:** Agreement mismatch: 'Мо́жна' (f) + 'Клієнт' (m)
**How to fix:** Change 'Мо́жна' to match the gender/case of 'Клієнт', or vice versa.
**Where:** ~line 169

### Fix 9: AGREEMENT_ERROR
**What:** Agreement mismatch: 'українською' (f) + 'напій' (m)
**How to fix:** Change 'українською' to match the gender/case of 'напій', or vice versa.
**Where:** ~line 202

### Fix 10: AGREEMENT_ERROR
**What:** Agreement mismatch: 'правильна' (f) + 'правило' (n)
**How to fix:** Change 'правильна' to match the gender/case of 'правило', or vice versa.
**Where:** ~line 202

### Fix 11: AGREEMENT_ERROR
**What:** Agreement mismatch: 'жіночого' (m/n) + 'слів' (p)
**How to fix:** Change 'жіночого' to match the gender/case of 'слів', or vice versa.
**Where:** ~line 202

### Fix 12: ACTIVITY_VESUM_FAIL
**What:** Activity answers contain VESUM-failed words: Марія
**How to fix:** Fix spelling or replace these words — students will practice non-existent forms.
**Where:** at-the-cafe.yaml

### Fix: Gate `Pedagogy` FAIL — 1 violations

### Fix 14: PEDAGOGICAL_VIOLATION
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

