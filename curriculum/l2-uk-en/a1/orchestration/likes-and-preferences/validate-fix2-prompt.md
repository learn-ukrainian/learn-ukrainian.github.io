        # Fix 4 issue(s) in `likes-and-preferences`

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'цю' (VESUM: adj:f:v_zna:pron:dem) in M19. Accusative not taught until M25.
**How to fix:** Replace 'цю' (accusative) with nominative form or use English equivalent.
**Where:** ~line 100

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'книгу' (VESUM: noun:inanim:f:v_zna) in M19. Accusative not taught until M25.
**How to fix:** Replace 'книгу' (accusative) with nominative form or use English equivalent.
**Where:** ~line 100

### Fix 3: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'українську' (VESUM: noun:inanim:f:v_zna) in M19. Accusative not taught until M25.
**How to fix:** Replace 'українську' (accusative) with nominative form or use English equivalent.
**Where:** ~line 172

### Fix 4: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'мову' (VESUM: noun:inanim:f:v_zna) in M19. Accusative not taught until M25.
**How to fix:** Replace 'мову' (accusative) with nominative form or use English equivalent.
**Where:** ~line 172


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

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/likes-and-preferences.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/likes-and-preferences.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/likes-and-preferences.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

