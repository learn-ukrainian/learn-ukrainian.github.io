        # Fix 18 issue(s) in `imperative-and-requests`

        ### Fix 1: AGREEMENT_ERROR
**What:** Agreement mismatch: 'неформальна' (f) + 'форми' (f/p)
**How to fix:** Change 'неформальна' to match the gender/case of 'форми', or vice versa.
**Where:** ~line 17

### Fix 2: AGREEMENT_ERROR
**What:** Agreement mismatch: 'формальна' (f) + 'ви' (p)
**How to fix:** Change 'формальна' to match the gender/case of 'ви', or vice versa.
**Where:** ~line 17

### Fix 3: AGREEMENT_ERROR
**What:** Agreement mismatch: 'корисних' (p) + 'кілька' (f)
**How to fix:** Change 'корисних' to match the gender/case of 'кілька', or vice versa.
**Where:** ~line 110

### Fix 4: AGREEMENT_ERROR
**What:** Agreement mismatch: 'ввічливим' (m/n/p) + 'прохання' (n/p)
**How to fix:** Change 'ввічливим' to match the gender/case of 'прохання', or vice versa.
**Where:** ~line 127

### Fix 5: AGREEMENT_ERROR
**What:** Agreement mismatch: 'можна' (f) + 'слово' (n)
**How to fix:** Change 'можна' to match the gender/case of 'слово', or vice versa.
**Where:** ~line 127

### Fix 6: PLAN_SECTION_MISSING
**What:** Missing 2 plan section(s): Вісім обов'язкових дієслів (Eight required verbs), Ввічливе прохання (Polite requests)
**How to fix:** Add content for the missing plan sections or update section headings to match plan.
**Where:** (plan vs content)

### Fix: Gate `Structure` FAIL — Missing '## Summary'

### Fix: Gate `Pedagogy` FAIL — 10 violations

### Fix 9: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'мові'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 10: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Instrumental case used at A1: 'перед дієсловом'
**How to fix:** Instrumental case not allowed until A2 (M36+). Restructure sentence.

### Fix 11: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: ', які в'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 12: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'б
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 13: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'Щоб у'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 14: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'щоб п'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 15: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'Щоб з'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 16: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Коли ми даємо інструкції або...'

### Fix 17: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Для форми ви просто додайте...'

### Fix 18: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Ось вісім дуже важливих дієслів...'

### Other Audit Failures

```
Практика та підсумок (Practice and Summary)          79 /  175  ❌ (-96)
TOTAL                                              1123 / 1200  ❌ (-77)
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

