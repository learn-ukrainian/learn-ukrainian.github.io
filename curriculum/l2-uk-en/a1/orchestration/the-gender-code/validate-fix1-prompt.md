        # Fix 2 issue(s) in `the-gender-code`

        ### Fix 1: PLAN_SECTION_MISSING
**What:** Missing 2 plan section(s): Самостійна робота (Independent Work/Production), Культурний код та підсумок (Cultural Code and Summary)
**How to fix:** Add content for the missing plan sections or update section headings to match plan.
**Where:** (plan vs content)

### Fix: Gate `Immersion` FAIL — 14.9% LOW (target 15-35% (M07))
**Action:** Add more Ukrainian-language content blocks. Convert some English explanations to Ukrainian with English glosses.

### Other Audit Failures

```
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/the-gender-code-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M5-10 — Phonology & First Grammar):
Full alphabet known. Modules teach: syllables (M5), stress (M6), gender (M7), greetings (M8), Це/Я/Мене звати (M9), Що це? (M10).

GRAMMAR STATUS:
- AVAILABLE: bare nouns, gender classification, Це + noun, Я + noun, memorized politeness phrases (Дякую, Будь ласка, Вибачте from M8)
- FORBIDDEN: verb conjugation, imperatives, adjective agreement, plurals, all cases except nominative
  Exception (M6 stress): Conjugated verb forms allowed ONLY as stress pattern examples (e.g., писа́ти → пишу́ → пи́шеш to show stress mobility). Do not teach conjugation rules.
  Exception (M7 gender): Adjective agreement examples allowed to demonstrate what gender does (e.g., великий стіл, нова книга, чисте вікно). Do not teach agreement rules.
  Exception (M8 greetings): Memorized conversational phrases with conjugated verbs allowed as fixed chunks (e.g., 'Як справи?', 'Що ти робиш?'). Present as whole phrases, not conjugation patterns.
- BANNED Ukrainian phrases: Подивімось, Поговорімо, Повторімо, Давайте розглянемо, Розглянемо, Скажіть — always use English equivalents (Let us look at, Let's talk about, Let's review, Please tell me)
- BANNED IMPERATIVE FORMS (non-exhaustive): Запам'ятайте, Уявіть, Порівняйте, Зверніть увагу, Спробуйте, Подивіться, Послухайте, Прочитайте, Повторіть, Напишіть, Скажіть, Виберіть, Подивімось, Поговорімо, Повторімо, Давайте розглянемо, Розглянемо.
  INSTEAD OF → USE:
  - Запам'ятайте → "Remember that..." (English)
  - Порівняйте → "Compare..." (English)
  - Зверніть увагу → "Notice that..." (English)
  - Подивіться → "Look at..." (English)
  - Спробуйте → "Try to..." (English)
  - Прочитайте → "Read..." (English)
  - Повторіть → "Repeat..." (English)
- Use English for all classroom instructions

VERB-FREE UKRAINIAN PATTERN BANK (use these for immersion WITHOUT verbs):
- Це + noun: «Це кіт», «Це стіл»
- Question particles: «Хто це?», «Що це?»
- Noun listings with gender: «стіл (він), книга (вона), вікно (воно)»
- Contextual labels: «Наприклад — For example», «А тепер — And now»
DO NOT use: conjugated verbs, imperatives, infinitives.
Every Ukrainian phrase must be VERB-FREE. Use English for any sentence requiring a verb.

METALANGUAGE: English-first, Ukrainian term in parentheses on first use



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-gender-code.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-gender-code.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

