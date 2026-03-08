        # Fix 8 issue(s) in `the-living-verb-i`

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'мо́ву' (VESUM: noun:inanim:f:v_zna) in M15. Accusative not taught until M25.
**How to fix:** Replace 'мо́ву' (accusative) with nominative form or use English equivalent.
**Where:** ~line 149

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Non-present verb 'ви́вчили' (past tense, VESUM: verb:perf:past:p) in M15. Only present tense available before M36.
**How to fix:** Replace 'ви́вчили' with present tense form or English.
**Where:** ~line 163

### Fix 3: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'Пти́цю' (VESUM: noun:anim:f:v_zna) in M15. Accusative not taught until M25.
**How to fix:** Replace 'Пти́цю' (accusative) with nominative form or use English equivalent.
**Where:** ~line 170

### Fix 4: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'люди́ну' (VESUM: noun:anim:f:v_zna) in M15. Accusative not taught until M25.
**How to fix:** Replace 'люди́ну' (accusative) with nominative form or use English equivalent.
**Where:** ~line 170

### Fix 5: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'осно́ву' (VESUM: noun:inanim:f:v_zna) in M15. Accusative not taught until M25.
**How to fix:** Replace 'осно́ву' (accusative) with nominative form or use English equivalent.
**Where:** ~line 184

### Fix 6: AGREEMENT_ERROR
**What:** Agreement mismatch: 'украї́нських' (p) + 'Більшість' (f)
**How to fix:** Change 'украї́нських' to match the gender/case of 'Більшість', or vice versa.
**Where:** ~line 45

### Fix 7: AGREEMENT_ERROR
**What:** Agreement mismatch: 'мо́жна' (f) + 'ми' (p)
**How to fix:** Change 'мо́жна' to match the gender/case of 'ми', or vice versa.
**Where:** ~line 84

### Fix 8: AGREEMENT_ERROR
**What:** Agreement mismatch: 'пе́ршої' (f) + 'Дієсло́ва' (n/p)
**How to fix:** Change 'пе́ршої' to match the gender/case of 'Дієсло́ва', or vice versa.
**Where:** ~line 164


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

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-living-verb-i.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-living-verb-i.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-living-verb-i.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

