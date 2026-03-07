        # Fix 13 issue(s) in `the-accusative-i-things`

        ### Fix 1: IPA_BANNED
**What:** Banned IPA transcription: [accusative]
**How to fix:** Remove phonetic brackets. Use only stress marks (´) for pronunciation.
**Where:** ~line 38

### Fix 2: IPA_BANNED
**What:** Banned IPA transcription: [accusative]
**How to fix:** Remove phonetic brackets. Use only stress marks (´) for pronunciation.
**Where:** ~line 43

### Fix 3: IPA_BANNED
**What:** Banned IPA transcription: [in nominative]
**How to fix:** Remove phonetic brackets. Use only stress marks (´) for pronunciation.
**Where:** ~line 49

### Fix 4: IPA_BANNED
**What:** Banned IPA transcription: [accusative]
**How to fix:** Remove phonetic brackets. Use only stress marks (´) for pronunciation.
**Where:** ~line 175

### Fix 5: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'запам'ятовуйте' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'запам'ятовуйте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 135

### Fix 6: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'описуйте' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'описуйте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 180

### Fix 7: AGREEMENT_ERROR
**What:** Agreement mismatch: 'ідеальне' (n) + 'Магазин' (m)
**How to fix:** Change 'ідеальне' to match the gender/case of 'Магазин', or vice versa.
**Where:** ~line 149

### Fix 8: AGREEMENT_ERROR
**What:** Agreement mismatch: 'жіночого' (m/n) + 'гречка' (f)
**How to fix:** Change 'жіночого' to match the gender/case of 'гречка', or vice versa.
**Where:** ~line 175

### Fix 9: AGREEMENT_ERROR
**What:** Agreement mismatch: 'вашою' (f) + 'відмінок' (m)
**How to fix:** Change 'вашою' to match the gender/case of 'відмінок', or vice versa.
**Where:** ~line 180

### Fix 10: PLAN_SECTION_MISSING
**What:** Missing 4 plan section(s): Вступ (Introduction), Презентація: Знахідний відмінок (Presentation: Accusative Case), Практика та запобігання помилкам (Practice and Error Prevention), Виробництво та культура (Production and Culture)
**How to fix:** Add content for the missing plan sections or update section headings to match plan.
**Where:** (plan vs content)

### Fix 11: ACTIVITY_VESUM_FAIL
**What:** Activity answers contain VESUM-failed words: вихода, вихіду, голоса, стілу, часа, їсту
**How to fix:** Fix spelling or replace these words — students will practice non-existent forms.
**Where:** the-accusative-i-things.yaml

### Fix: Gate `Pedagogy` FAIL — 1 violations

### Fix 13: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Grammar Check: Direct Objects' Q4 prompt length 16 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Other Audit Failures

```
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/the-accusative-i-things-audit.log for details)
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

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-accusative-i-things.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-accusative-i-things.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-accusative-i-things.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

