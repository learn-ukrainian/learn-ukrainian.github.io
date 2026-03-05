        # Fix 2 issue(s) in `stress-and-intonation`

        ### Fix 1: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Прочитайте' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 223):** `Прочитайте цей текст. Зверніть увагу на наголос та інтонацію (Read this text. Pay attention to the stress and intonation):`

### Fix 2: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Зверніть' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 223):** `Прочитайте цей текст. Зверніть увагу на наголос та інтонацію (Read this text. Pay attention to the stress and intonation):`


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M5-10 — Phonology & First Grammar):
Full alphabet known. Modules teach: syllables (M5), stress (M6), gender (M7), greetings (M8), Це/Я/Мене звати (M9), Що це? (M10).

GRAMMAR STATUS:
- AVAILABLE: bare nouns, gender classification, Це + noun, Я + noun, memorized politeness phrases (Дякую, Будь ласка, Вибачте from M8)
- FORBIDDEN: verb conjugation, imperatives, adjective agreement, plurals, all cases except nominative
- Use English for all classroom instructions

METALANGUAGE: English-first, Ukrainian term in parentheses on first use



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/stress-and-intonation.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/stress-and-intonation.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/stress-and-intonation.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

