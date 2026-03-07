        # Fix 16 issue(s) in `describing-things-adjectives`

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Verb 'вивчаємо' (VESUM: verb:imperf:pres:p:1) in pre-verb module M11. Verbs are forbidden before M15.
**How to fix:** Replace verb 'вивчаємо' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 16

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Verb 'описують' (VESUM: verb:imperf:pres:p:3) in pre-verb module M11. Verbs are forbidden before M15.
**How to fix:** Replace verb 'описують' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 19

### Fix 3: MORPHOLOGICAL_VIOLATION
**What:** Verb 'має' (VESUM: verb:imperf:pres:s:3) in pre-verb module M11. Verbs are forbidden before M15.
**How to fix:** Replace verb 'має' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 34

### Fix 4: MORPHOLOGICAL_VIOLATION
**What:** Non-nominative 'центрі' (locative, VESUM: noun:inanim:m:v_mis:xp1) in M11. Only nominative case allowed before M25.
**How to fix:** Replace 'центрі' (locative) with its nominative form or use English equivalent.
**Where:** ~line 49

### Fix 5: MORPHOLOGICAL_VIOLATION
**What:** Verb 'закінчується' (VESUM: verb:rev:imperf:pres:s:3) in pre-verb module M11. Verbs are forbidden before M15.
**How to fix:** Replace verb 'закінчується' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 75

### Fix 6: MORPHOLOGICAL_VIOLATION
**What:** Verb 'змінюємо' (VESUM: verb:imperf:pres:p:1) in pre-verb module M11. Verbs are forbidden before M15.
**How to fix:** Replace verb 'змінюємо' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 81

### Fix 7: MORPHOLOGICAL_VIOLATION
**What:** Non-nominative 'інших' (genitive, VESUM: adj:p:v_rod:pron:def) in M11. Only nominative case allowed before M25.
**How to fix:** Replace 'інших' (genitive) with its nominative form or use English equivalent.
**Where:** ~line 81

### Fix 8: MORPHOLOGICAL_VIOLATION
**What:** Non-nominative 'родів' (genitive, VESUM: noun:inanim:p:v_rod) in M11. Only nominative case allowed before M25.
**How to fix:** Replace 'родів' (genitive) with its nominative form or use English equivalent.
**Where:** ~line 81

### Fix 9: MORPHOLOGICAL_VIOLATION
**What:** Verb 'маємо' (VESUM: verb:imperf:pres:p:1) in pre-verb module M11. Verbs are forbidden before M15.
**How to fix:** Replace verb 'маємо' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 93

### Fix 10: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'перевіряйте' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'перевіряйте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 137

### Fix 11: MORPHOLOGICAL_VIOLATION
**What:** Verb 'закінчується' (VESUM: verb:rev:imperf:pres:s:3) in pre-verb module M11. Verbs are forbidden before M15.
**How to fix:** Replace verb 'закінчується' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 162

### Fix 12: MORPHOLOGICAL_VIOLATION
**What:** Non-nominative 'Києві' (dative, VESUM: noun:inanim:m:v_dav) in M11. Only nominative case allowed before M25.
**How to fix:** Replace 'Києві' (dative) with its nominative form or use English equivalent.
**Where:** ~line 179

### Fix 13: MORPHOLOGICAL_VIOLATION
**What:** Verb 'має' (VESUM: verb:imperf:pres:s:3) in pre-verb module M11. Verbs are forbidden before M15.
**How to fix:** Replace verb 'має' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 183

### Fix 14: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Зверніть' (VESUM: verb:perf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Зверніть' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 186

### Fix 15: MORPHOLOGICAL_VIOLATION
**What:** Non-nominative 'увагу' (accusative, VESUM: noun:inanim:f:v_zna) in M11. Only nominative case allowed before M25.
**How to fix:** Replace 'увагу' (accusative) with its nominative form or use English equivalent.
**Where:** ~line 186

### Fix 16: PEDAGOGICAL_VIOLATION
**What:** [METALANGUAGE] Metalanguage terms used but not in vocabulary: множина
**How to fix:** Add these grammar terms to vocabulary with translations, or use English equivalents.

### Other Audit Failures

```
TOTAL                                                                        1169 / 1200  ❌ (-31)
📚 PEDAGOGICAL VIOLATIONS FOUND:
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M11-14 — Adjectives & Plurals):
Student knows: alphabet, gender, greetings, Це/Я/Мене звати, basic nouns.
Learning: adjective agreement (M11), colors (M12), plurals (M13), checkpoint (M14).

GRAMMAR STATUS:
- AVAILABLE: nouns (nom. sg & pl from M13), adjective+noun agreement (from M11), Це/Я sentences, memorized phrases
- FORBIDDEN: verb conjugation (starts M15), imperatives (M47), cases beyond nominative (accusative starts M25)
- BANNED Ukrainian phrases: Подивімось, Поговорімо, Повторімо, Давайте розглянемо, Розглянемо, Скажіть — always use English equivalents
- BANNED IMPERATIVE FORMS (non-exhaustive): Запам'ятайте, Уявіть, Порівняйте, Зверніть увагу, Спробуйте, Подивіться, Послухайте, Прочитайте, Повторіть, Напишіть, Скажіть, Виберіть, Подивімось, Поговорімо, Повторімо, Давайте розглянемо, Розглянемо.
  INSTEAD OF → USE:
  - Запам'ятайте → "Remember that..." (English)
  - Порівняйте → "Compare..." (English)
  - Зверніть увагу → "Notice that..." (English)
  - Подивіться → "Look at..." (English)
  - Спробуйте → "Try to..." (English)
  - Прочитайте → "Read..." (English)
  - Повторіть → "Repeat..." (English)
- Use English for classroom instructions

VERB-FREE UKRAINIAN PATTERN BANK (use these for immersion WITHOUT verbs):
- Це + noun: «Це кіт», «Це нова книга»
- Adj + noun phrases: «великий дім», «червона сукня», «гарне місто»
- Question particles: «Хто це?», «Що це?», «Який?», «Яка?», «Яке?»
- Demonstratives: «Цей стіл», «Ця книга», «Це вікно», «Ці слова»
- Possessives: «мій зошит», «моя мама», «моє місто», «мої друзі»
- Preposition + noun: «у місті», «на столі», «з молоком»
- Noun listings: «кіт, собака, хом'як — це тварини»
- Contextual labels: «Наприклад — For example», «А тепер — And now»
- Comparisons (without verbs): «кіт — маленький, собака — великий»
DO NOT use: conjugated verbs (є, має, робить), imperatives, infinitives.
Every Ukrainian phrase must be VERB-FREE. Use English for any sentence requiring a verb.

METALANGUAGE: English-first, Ukrainian in parentheses



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/describing-things-adjectives.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/describing-things-adjectives.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/describing-things-adjectives.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

