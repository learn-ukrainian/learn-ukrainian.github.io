        # Fix 4 issue(s) in `imperative-and-requests`

        ### Fix 1: AGREEMENT_ERROR
**What:** Agreement mismatch: 'цього' (m/n) + 'ми' (p)
**How to fix:** Change 'цього' to match the gender/case of 'ми', or vice versa.
**Where:** ~line 17

### Fix 2: PLAN_SECTION_MISSING
**What:** Missing 5 plan section(s): Наказовий спосіб (Imperative mood), Вісім обов'язкових дієслів (Eight required verbs), Ввічливе прохання (Polite requests), Заборони (Prohibitions), Практика (Practice)
**How to fix:** Add content for the missing plan sections or update section headings to match plan.
**Where:** (plan vs content)

### Fix: Gate `Pedagogy` FAIL — 1 violations

### Fix 4: PEDAGOGICAL_VIOLATION
**What:** [HEADING_LEVEL] Main section 'Summary' uses H2 (##) but spec requires H1 (#)
**How to fix:** Change '## Summary' to '# Summary' for top-level TOC compliance

### Other Audit Failures

```
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/imperative-and-requests-audit.log for details)
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

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/imperative-and-requests.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/imperative-and-requests.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/imperative-and-requests.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

