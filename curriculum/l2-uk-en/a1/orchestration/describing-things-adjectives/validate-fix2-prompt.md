        # Fix 13 issue(s) in `describing-things-adjectives`

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Non-nominative 'Київ' (genitive, VESUM: noun:inanim:p:v_rod) in M11. Only nominative case allowed before M25.
**How to fix:** Replace 'Київ' (genitive) with its nominative form or use English equivalent.
**Where:** ~line 49

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Non-nominative 'Київ' (genitive, VESUM: noun:inanim:p:v_rod) in M11. Only nominative case allowed before M25.
**How to fix:** Replace 'Київ' (genitive) with its nominative form or use English equivalent.
**Where:** ~line 180

### Fix 3: MORPHOLOGICAL_VIOLATION
**What:** Verb 'робить' (VESUM: verb:imperf:inf:short) in pre-verb module M11. Verbs are forbidden before M15.
**How to fix:** Replace verb 'робить' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 220

### Fix 4: MORPHOLOGICAL_VIOLATION
**What:** Non-nominative 'простішим' (instrumental, VESUM: adj:m:v_oru:compc) in M11. Only nominative case allowed before M25.
**How to fix:** Replace 'простішим' (instrumental) with its nominative form or use English equivalent.
**Where:** ~line 220

### Fix 5: MORPHOLOGICAL_VIOLATION
**What:** Verb 'маємо' (VESUM: verb:imperf:pres:p:1) in pre-verb module M11. Verbs are forbidden before M15.
**How to fix:** Replace verb 'маємо' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 232

### Fix 6: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Уявіть' (VESUM: verb:perf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Уявіть' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 247

### Fix 7: MORPHOLOGICAL_VIOLATION
**What:** Non-nominative 'ситуацію' (accusative, VESUM: noun:inanim:f:v_zna) in M11. Only nominative case allowed before M25.
**How to fix:** Replace 'ситуацію' (accusative) with its nominative form or use English equivalent.
**Where:** ~line 247

### Fix 8: MORPHOLOGICAL_VIOLATION
**What:** Verb 'показуєте' (VESUM: verb:imperf:pres:p:2) in pre-verb module M11. Verbs are forbidden before M15.
**How to fix:** Replace verb 'показуєте' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 250

### Fix 9: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Зверніть' (VESUM: verb:perf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Зверніть' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 253

### Fix 10: MORPHOLOGICAL_VIOLATION
**What:** Non-nominative 'увагу' (accusative, VESUM: noun:inanim:f:v_zna) in M11. Only nominative case allowed before M25.
**How to fix:** Replace 'увагу' (accusative) with its nominative form or use English equivalent.
**Where:** ~line 253

### Fix 11: MORPHOLOGICAL_VIOLATION
**What:** Verb 'змінюються' (VESUM: verb:rev:imperf:pres:p:3) in pre-verb module M11. Verbs are forbidden before M15.
**How to fix:** Replace verb 'змінюються' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 253

### Fix 12: MORPHOLOGICAL_VIOLATION
**What:** Verb 'знаєте' (VESUM: verb:imperf:pres:p:2) in pre-verb module M11. Verbs are forbidden before M15.
**How to fix:** Replace verb 'знаєте' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 294

### Fix 13: AGREEMENT_ERROR
**What:** Agreement mismatch: 'новий' (m) + 'машина' (f)
**How to fix:** Change 'новий' to match the gender/case of 'машина', or vice versa.
**Where:** ~line 132

### Other Audit Failures

```
TOTAL                                                                        1165 / 1200  ❌ (-35)
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

