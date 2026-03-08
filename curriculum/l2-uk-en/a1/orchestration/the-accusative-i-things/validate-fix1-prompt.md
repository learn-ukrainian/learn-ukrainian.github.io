        # Fix 15 issue(s) in `the-accusative-i-things`

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Зверні́ть' (VESUM: verb:perf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Зверні́ть' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 54

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Уяві́ть' (VESUM: verb:perf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Уяві́ть' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 83

### Fix 3: AGREEMENT_ERROR
**What:** Agreement mismatch: 'фіксо́ваний' (m) + 'слів' (p)
**How to fix:** Change 'фіксо́ваний' to match the gender/case of 'слів', or vice versa.
**Where:** ~line 15

### Fix 4: AGREEMENT_ERROR
**What:** Agreement mismatch: 'цьо́го' (m/n) + 'ми' (p)
**How to fix:** Change 'цьо́го' to match the gender/case of 'ми', or vice versa.
**Where:** ~line 15

### Fix 5: AGREEMENT_ERROR
**What:** Agreement mismatch: 'Початко́ва' (f) + 'кни́жку' (f)
**How to fix:** Change 'Початко́ва' to match the gender/case of 'кни́жку', or vice versa.
**Where:** ~line 15

### Fix 6: AGREEMENT_ERROR
**What:** Agreement mismatch: 'Суча́сний' (m) + 'мі́сцях' (p)
**How to fix:** Change 'Суча́сний' to match the gender/case of 'мі́сцях', or vice versa.
**Where:** ~line 83

### Fix 7: AGREEMENT_ERROR
**What:** Agreement mismatch: 'потрі́бен' (m) + 'Сло́во' (n)
**How to fix:** Change 'потрі́бен' to match the gender/case of 'Сло́во', or vice versa.
**Where:** ~line 83

### Fix 8: ACTIVITY_VESUM_FAIL
**What:** Activity answers contain VESUM-failed words: молокі
**How to fix:** Fix spelling or replace these words — students will practice non-existent forms.
**Where:** the-accusative-i-things.yaml

### Fix: Gate `Pedagogy` FAIL — 6 violations

### Fix 10: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Participle used before B1: 'ваний'
**How to fix:** Participles not allowed until B1. Use relative clauses or simple sentences.

### Fix 11: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'ь, що в'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 12: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'слова кни га та робо...'

### Fix 13: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 14 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Це ду же важли ве...'

### Fix 14: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Украї ні за звичай ро...'

### Fix 15: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Understanding the Accusative Case' Q4 prompt length 4 (target: 5-10)
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

