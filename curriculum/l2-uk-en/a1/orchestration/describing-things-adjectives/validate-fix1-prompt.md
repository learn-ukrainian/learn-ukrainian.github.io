        # Fix 13 issue(s) in `describing-things-adjectives`

        ### Fix 1: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Уявіть' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 11):** `> Уявіть, що ви в кафе і хочете велику каву, а не маленьку. Або шукаєте новий телефон, а не старий. Прикметники допомагають нам точно описувати світ.`

### Fix 2: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Уявімо' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 163):** `Уявімо іншу ситуацію. Ми в агенції нерухомості.`

### Fix 3: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'використовуємо' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 159):** `> В українській міфології Ма́вка — це дух лісу (a forest spirit). Її су́кня завжди зеле́на. Оскільки сло́во «су́кня» (dress) — це жіночий рід, ми використовуємо закінчення **-а**: зеле́н**а** су́кня.`

### Fix 4: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'Уявімо' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 163):** `Уявімо іншу ситуацію. Ми в агенції нерухомості.`

### Fix 5: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'допомагають' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 11):** `> Уявіть, що ви в кафе і хочете велику каву, а не маленьку. Або шукаєте новий телефон, а не старий. Прикметники допомагають нам точно описувати світ.`

### Fix 6: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'роблять' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 68):** `> Студенти часто роблять помилку. Вони кажуть «нови́й маши́на». Це помилка! Маши́на — це жіночий рід.`

### Fix 7: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'має' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 128):** `> У Київському метро є **си́ня лі́нія** (blue line) та **зеле́на лі́нія** (green line). «Зеле́на» має тверду основу (hard stem), тому закінчується на **-а**, а «си́ня» має м'яку основу (soft stem), тому закінчується на **-я**!`

### Fix: Gate `Pedagogy` FAIL — 3 violations

### Fix: Gate `Immersion` FAIL — 22.8% LOW (target 25-40% (M11))
**Action:** Add more Ukrainian-language content blocks. Convert some English explanations to Ukrainian with English glosses.

### Fix 10: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'ь, що в'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 11: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Київському метро си ня лі...'

### Fix 12: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 16 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Зеле на має тверду основу...'

### Fix 13: PEDAGOGICAL_VIOLATION
**What:** [METALANGUAGE] Metalanguage terms used but not in vocabulary: множина
**How to fix:** Add these grammar terms to vocabulary with translations, or use English equivalents.

### Other Audit Failures

```
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/describing-things-adjectives-audit.log for details)
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

