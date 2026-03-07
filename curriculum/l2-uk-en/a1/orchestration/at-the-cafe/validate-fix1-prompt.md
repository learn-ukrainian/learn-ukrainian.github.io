        # Fix 27 issue(s) in `at-the-cafe`

        ### Fix 1: IPA_BANNED
**What:** Banned IPA transcription: [have]
**How to fix:** Remove phonetic brackets. Use only stress marks (´) for pronunciation.
**Where:** ~line 57

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'будь' (VESUM: verb:imperf:impr:s:2) — imperatives not taught until M47.
**How to fix:** Replace 'будь' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 11

### Fix 3: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'кажіть' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'кажіть' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 61

### Fix 4: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Використовуйте' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Використовуйте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 61

### Fix 5: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Зверніть' (VESUM: verb:perf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Зверніть' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 125

### Fix 6: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'просіть' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'просіть' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 142

### Fix 7: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Пам'ятайте' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Пам'ятайте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 204

### Fix 8: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'використовуйте' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'використовуйте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 204

### Fix 9: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'забувайте' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'забувайте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 204

### Fix 10: AGREEMENT_ERROR
**What:** Agreement mismatch: 'українського' (m/n) + 'частина' (f)
**How to fix:** Change 'українського' to match the gender/case of 'частина', or vice versa.
**Where:** ~line 11

### Fix 11: AGREEMENT_ERROR
**What:** Agreement mismatch: 'справжньої' (f) + 'знак' (m)
**How to fix:** Change 'справжньої' to match the gender/case of 'знак', or vice versa.
**Where:** ~line 19

### Fix 12: AGREEMENT_ERROR
**What:** Agreement mismatch: 'відома' (f) + 'своєю' (f)
**How to fix:** Change 'відома' to match the gender/case of 'своєю', or vice versa.
**Where:** ~line 39

### Fix 13: AGREEMENT_ERROR
**What:** Agreement mismatch: 'Англійською' (f) + 'ми' (p)
**How to fix:** Change 'Англійською' to match the gender/case of 'ми', or vice versa.
**Where:** ~line 51

### Fix 14: AGREEMENT_ERROR
**What:** Agreement mismatch: 'жіночого' (m/n) + 'слів' (p)
**How to fix:** Change 'жіночого' to match the gender/case of 'слів', or vice versa.
**Where:** ~line 69

### Fix 15: AGREEMENT_ERROR
**What:** Agreement mismatch: 'найкращий' (m) + 'меню' (n/p)
**How to fix:** Change 'найкращий' to match the gender/case of 'меню', or vice versa.
**Where:** ~line 119

### Fix 16: AGREEMENT_ERROR
**What:** Agreement mismatch: 'мо́жна' (f) + 'слово' (n)
**How to fix:** Change 'мо́жна' to match the gender/case of 'слово', or vice versa.
**Where:** ~line 119

### Fix 17: ACTIVITY_VESUM_FAIL
**What:** Activity answers contain VESUM-failed words: Оля
**How to fix:** Fix spelling or replace these words — students will practice non-existent forms.
**Where:** at-the-cafe.yaml

### Fix: Gate `Structure` FAIL — Missing '## Summary'

### Fix: Gate `Pedagogy` FAIL — 8 violations

### Fix 20: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'вам'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 21: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Participle used before B1: 'улюблений'
**How to fix:** Participles not allowed until B1. Use relative clauses or simple sentences.

### Fix 22: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'Якщо у'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 23: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 15 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Якщо український друг запрошує вас...'

### Fix 24: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Він допоміг врятувати Відень потім...'

### Fix 25: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 13 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'інших регіонах чай часто популярнішим...'

### Fix 26: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'слово мо жна також вимагає...'

### Fix 27: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Ordering Rules in a Cafe' Q7 prompt length 3 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Other Audit Failures

```
Продукція та Підсумок (Production and Summary)   144 /  200  ❌ (-56)
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

