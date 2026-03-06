        # Fix 7 issue(s) in `describing-things-adjectives`

        ### Fix 1: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Давайте' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 103):** `Давайте практикувати! — Let's practice! Ми починаємо з української культури. — We start with Ukrainian culture.`

### Fix 2: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Повторімо' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 137):** `Повторімо. — Let's review. Прикметники завжди відповідають роду та числу іменника. — Adjectives always match the gender and number of the noun. Ми питаємо. — We ask: «Яки́й? Яка́? Яке́? Які́?».`

### Fix 3: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'знаємо' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 18):** `Ми вже знаємо слова. Тепер ми описуємо світ! — We already know the words. Now we describe the world!`

### Fix 4: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'описуємо' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 18):** `Ми вже знаємо слова. Тепер ми описуємо світ! — We already know the words. Now we describe the world!`

### Fix 5: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'починаємо' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 103):** `Давайте практикувати! — Let's practice! Ми починаємо з української культури. — We start with Ukrainian culture.`

### Fix 6: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'Повторімо' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 137):** `Повторімо. — Let's review. Прикметники завжди відповідають роду та числу іменника. — Adjectives always match the gender and number of the noun. Ми питаємо. — We ask: «Яки́й? Яка́? Яке́? Які́?».`

### Fix 7: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'питаємо' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 137):** `Повторімо. — Let's review. Прикметники завжди відповідають роду та числу іменника. — Adjectives always match the gender and number of the noun. Ми питаємо. — We ask: «Яки́й? Яка́? Яке́? Які́?».`


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M11-14 — Adjectives & Plurals):
Student knows: alphabet, gender, greetings, Це/Я/Мене звати, basic nouns.
Learning: adjective agreement (M11), colors (M12), plurals (M13), checkpoint (M14).

GRAMMAR STATUS:
- AVAILABLE: nouns (nom. sg & pl from M13), adjective+noun agreement (from M11), Це/Я sentences, memorized phrases
- FORBIDDEN: verb conjugation (starts M15), imperatives (M47), cases beyond nominative (accusative starts M25)
- Use English for classroom instructions

METALANGUAGE: English-first, Ukrainian in parentheses



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/describing-things-adjectives.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/describing-things-adjectives.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/describing-things-adjectives.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

