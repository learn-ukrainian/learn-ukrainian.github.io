        # Fix 6 issue(s) in `the-gender-code`

        ### Fix 1: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Дивіться' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 36):** `Як знати? Не треба вгадувати! Дивіться на останню літеру. (How to know? No need to guess! Look at the last letter.)`

### Fix 2: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Спробуйте' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 138):** `**Спробуйте зараз!** Before we continue — can you guess the gender of these words?`

### Fix 3: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Слухайте' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 263):** `Here is gender agreement in action. Слухайте! Notice how **мій** and **моя** change depending on who we are talking about.`

### Fix 4: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Зверніть' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 234):** `**Подивіться!** (Look!) **Зверніть увагу!** (Pay attention!) Here are words you will use every day.`

### Fix 5: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'використовуємо' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 54):** `**Розглянемо правила!** (Let's look at the rules!) Ми використовуємо кольори: **Blue** (Masculine), **Red** (Feminine), and **Yellow** (Neuter).`

### Fix 6: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'мають' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 296):** `Українські міста також мають код: **Київ** — Masculine, **Одеса** — Feminine, **Запоріжжя** — Neuter.`


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M5-10 — Phonology & First Grammar):
Full alphabet known. Modules teach: syllables (M5), stress (M6), gender (M7), greetings (M8), Це/Я/Мене звати (M9), Що це? (M10).

GRAMMAR STATUS:
- AVAILABLE: bare nouns, gender classification, Це + noun, Я + noun, memorized politeness phrases (Дякую, Будь ласка, Вибачте from M8)
- FORBIDDEN: verb conjugation, imperatives, adjective agreement, plurals, all cases except nominative
  Exception (M6 stress): Conjugated verb forms allowed ONLY as stress pattern examples (e.g., писа́ти → пишу́ → пи́шеш to show stress mobility). Do not teach conjugation rules.
  Exception (M7 gender): Adjective agreement examples allowed to demonstrate what gender does (e.g., великий стіл, нова книга, чисте вікно). Do not teach agreement rules.
- BANNED Ukrainian phrases: Подивімось, Поговорімо, Повторімо, Давайте розглянемо, Розглянемо — always use English equivalents (Let us look at, Let's talk about, Let's review)
- Use English for all classroom instructions

METALANGUAGE: English-first, Ukrainian term in parentheses on first use



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-gender-code.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-gender-code.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

