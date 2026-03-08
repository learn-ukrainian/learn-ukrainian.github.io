        # Fix 21 issue(s) in `the-living-verb-i`

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Non-present verb 'вчи́ли' (past tense, VESUM: verb:imperf:past:p) in M15. Only present tense available before M36.
**How to fix:** Replace 'вчи́ли' with present tense form or English.
**Where:** ~line 17

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'да́вню' (VESUM: adj:f:v_zna:compb) in M15. Accusative not taught until M25.
**How to fix:** Replace 'да́вню' (accusative) with nominative form or use English equivalent.
**Where:** ~line 29

### Fix 3: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'істо́рію' (VESUM: noun:inanim:f:v_zna) in M15. Accusative not taught until M25.
**How to fix:** Replace 'істо́рію' (accusative) with nominative form or use English equivalent.
**Where:** ~line 29

### Fix 4: MORPHOLOGICAL_VIOLATION
**What:** Non-present verb 'надрукува́в' (past tense, VESUM: verb:perf:past:m) in M15. Only present tense available before M36.
**How to fix:** Replace 'надрукува́в' with present tense form or English.
**Where:** ~line 31

### Fix 5: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'осно́ву' (VESUM: noun:inanim:f:v_zna) in M15. Accusative not taught until M25.
**How to fix:** Replace 'осно́ву' (accusative) with nominative form or use English equivalent.
**Where:** ~line 51

### Fix 6: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'осо́бу' (VESUM: noun:anim:f:v_zna) in M15. Accusative not taught until M25.
**How to fix:** Replace 'осо́бу' (accusative) with nominative form or use English equivalent.
**Where:** ~line 85

### Fix 7: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'пра́вду' (VESUM: noun:inanim:f:v_zna) in M15. Accusative not taught until M25.
**How to fix:** Replace 'пра́вду' (accusative) with nominative form or use English equivalent.
**Where:** ~line 94

### Fix 8: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Дава́йте' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Дава́йте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 99

### Fix 9: MORPHOLOGICAL_VIOLATION
**What:** Non-present verb 'Розгля́немо' (futr tense, VESUM: verb:perf:futr:p:1) in M15. Only present tense available before M36.
**How to fix:** Replace 'Розгля́немо' with present tense form or English.
**Where:** ~line 101

### Fix 10: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Дава́йте' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Дава́йте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 119

### Fix 11: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Зверні́ть' (VESUM: verb:perf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Зверні́ть' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 120

### Fix 12: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'ува́гу' (VESUM: noun:inanim:f:v_zna) in M15. Accusative not taught until M25.
**How to fix:** Replace 'ува́гу' (accusative) with nominative form or use English equivalent.
**Where:** ~line 120

### Fix 13: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Прочита́йте' (VESUM: verb:perf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Прочита́йте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 122

### Fix 14: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'му́зику' (VESUM: noun:anim:m:v_zna) in M15. Accusative not taught until M25.
**How to fix:** Replace 'му́зику' (accusative) with nominative form or use English equivalent.
**Where:** ~line 127

### Fix 15: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'кни́гу' (VESUM: noun:inanim:f:v_zna) in M15. Accusative not taught until M25.
**How to fix:** Replace 'кни́гу' (accusative) with nominative form or use English equivalent.
**Where:** ~line 140

### Fix: Gate `Pedagogy` FAIL — 5 violations

### Fix 17: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Друкова на кни га Украї...'

### Fix 18: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 14 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Якщо сло во закінчується на...'

### Fix 19: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Без сло ва ва ша...'

### Fix 20: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Check Your Knowledge: Meanings' Q5 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 21: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Check Your Knowledge: Meanings' Q6 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Other Audit Failures

```
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/the-living-verb-i-audit.log for details)
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

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-living-verb-i.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-living-verb-i.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-living-verb-i.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

