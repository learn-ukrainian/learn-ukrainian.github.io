        # Fix 8 issue(s) in `food-vocabulary`

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Продовжуйте' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Продовжуйте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 138

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'пам'ятайте' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'пам'ятайте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 138

### Fix 3: AGREEMENT_ERROR
**What:** Agreement mismatch: 'свіжі' (p) + 'їм' (p)
**How to fix:** Change 'свіжі' to match the gender/case of 'їм', or vice versa.
**Where:** ~line 15

### Fix 4: AGREEMENT_ERROR
**What:** Agreement mismatch: 'кожен' (m) + 'воду' (f)
**How to fix:** Change 'кожен' to match the gender/case of 'воду', or vice versa.
**Where:** ~line 38

### Fix 5: AGREEMENT_ERROR
**What:** Agreement mismatch: 'потрібна' (f) + 'людині' (f)
**How to fix:** Change 'потрібна' to match the gender/case of 'людині', or vice versa.
**Where:** ~line 38

### Fix 6: AGREEMENT_ERROR
**What:** Agreement mismatch: 'усьому' (m/n) + 'голова' (f/m)
**How to fix:** Change 'усьому' to match the gender/case of 'голова', or vice versa.
**Where:** ~line 65

### Fix 7: AGREEMENT_ERROR
**What:** Agreement mismatch: 'жіночого' (m/n) + 'слово' (n)
**How to fix:** Change 'жіночого' to match the gender/case of 'слово', or vice versa.
**Where:** ~line 156

### Fix 8: ACTIVITY_VESUM_FAIL
**What:** Activity answers contain VESUM-failed words: борща
**How to fix:** Fix spelling or replace these words — students will practice non-existent forms.
**Where:** food-vocabulary.yaml


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

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/food-vocabulary.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/food-vocabulary.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/food-vocabulary.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

