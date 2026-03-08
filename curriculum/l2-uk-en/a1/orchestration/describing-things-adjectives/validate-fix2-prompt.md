        # Fix 2 issue(s) in `describing-things-adjectives`

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Non-nominative 'нас' (genitive, VESUM: noun:anim:p:v_rod:pron:pers:1) in M11. Only nominative case allowed before M25.
**How to fix:** Replace 'нас' (genitive) with its nominative form or use English equivalent.
**Where:** ~line 269

### Fix 2: PEDAGOGICAL_VIOLATION
**What:** [METALANGUAGE] Metalanguage terms used but not in vocabulary: множина
**How to fix:** Add these grammar terms to vocabulary with translations, or use English equivalents.

### Other Audit Failures

```
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



## Verification Tools (USE THEM)

You have MCP tools for Ukrainian language verification. **Use them before fixing.**

- `verify_words(["word1", "word2"])` — check words exist in VESUM (standard Ukrainian dictionary)
- `verify_lemma("word")` — get all inflected forms of a word

**Before replacing any Ukrainian word:**
1. Call `verify_words` with your replacement to confirm it exists
2. If NOT FOUND, call `verify_lemma` on the base form to find correct inflections
3. Never use a word that returns NOT FOUND — rephrase in English instead


        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/describing-things-adjectives.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/describing-things-adjectives.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/describing-things-adjectives.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

