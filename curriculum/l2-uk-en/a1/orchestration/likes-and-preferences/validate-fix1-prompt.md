        # Fix 24 issue(s) in `likes-and-preferences`

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'каву' (VESUM: noun:inanim:f:v_zna) in M19. Accusative not taught until M25.
**How to fix:** Replace 'каву' (accusative) with nominative form or use English equivalent.
**Where:** ~line 129

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'смачну' (VESUM: adj:f:v_zna:compb) in M19. Accusative not taught until M25.
**How to fix:** Replace 'смачну' (accusative) with nominative form or use English equivalent.
**Where:** ~line 173

### Fix 3: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'каву' (VESUM: noun:inanim:f:v_zna) in M19. Accusative not taught until M25.
**How to fix:** Replace 'каву' (accusative) with nominative form or use English equivalent.
**Where:** ~line 173

### Fix 4: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'каву' (VESUM: noun:inanim:f:v_zna) in M19. Accusative not taught until M25.
**How to fix:** Replace 'каву' (accusative) with nominative form or use English equivalent.
**Where:** ~line 179

### Fix: Gate `Words` FAIL — 1046/1200 (raw: 1569)
**Action:** Expand content in the shortest sections. Add examples, explanations, or practice scenarios.

### Fix: Gate `Pedagogy` FAIL — 16 violations

### Fix: Gate `Immersion` FAIL — 14.9% LOW (target 25-40% (M19))
**Action:** Add more Ukrainian-language content blocks. Convert some English explanations to Ukrainian with English glosses.

### Fix 8: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'е, що н'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 9: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 13 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'кафе на роботі чи друзями...'

### Fix 10: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Choose the Right Word' Q2 prompt length 3 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 11: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Choose the Right Word' Q3 prompt length 3 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 12: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Choose the Right Word' Q4 prompt length 3 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 13: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Choose the Right Word' Q6 prompt length 3 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 14: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Choose the Right Word' Q7 prompt length 3 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 15: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Choose the Right Word' Q9 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 16: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Vocabulary Check' Q1 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 17: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Vocabulary Check' Q2 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 18: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Vocabulary Check' Q3 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 19: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Vocabulary Check' Q4 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 20: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Vocabulary Check' Q5 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 21: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Vocabulary Check' Q6 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 22: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Vocabulary Check' Q7 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 23: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Vocabulary Check' Q8 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 24: PEDAGOGICAL_VIOLATION
**What:** [METALANGUAGE] Metalanguage terms used but not in vocabulary: дієслово
**How to fix:** Add these grammar terms to vocabulary with translations, or use English equivalents.

### Other Audit Failures

```
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/likes-and-preferences-audit.log for details)
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

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/likes-and-preferences.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/likes-and-preferences.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/likes-and-preferences.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

