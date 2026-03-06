        # Fix 5 issue(s) in `describing-things-adjectives`

        ### Fix 1: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'описують' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 62):** `Додамо ще кілька слів. — Let's add a few more words. Ці слова описують розмір і якість. — These words describe size and quality.`

### Fix 2: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'виглядають' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 75):** `Ось як виглядають м'які закінчення. Вони дуже схожі на тверді закінчення, але мають м'який звук. — Here is how the soft endings look. They are very similar to hard endings, but have a soft sound.`

### Fix 3: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'мають' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 75):** `Ось як виглядають м'які закінчення. Вони дуже схожі на тверді закінчення, але мають м'який звук. — Here is how the soft endings look. They are very similar to hard endings, but have a soft sound.`

### Fix 4: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'відповідають' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 137):** `Повторення. — Review. Прикметники завжди відповідають роду та числу іменника. — Adjectives always match the gender and number of the noun. Питання. — The question: «Яки́й? Яка́? Яке́? Які́?».`

### Fix 5: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'має' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 32):** `Most adjectives in Ukrainian belong to the "тверда група" — hard group. Their base ends in a hard sound, and they take standard, predictable endings. У словнику прикметник завжди має чоловічий рід. — In the dictionary, an adjective always has a masculine gender.`


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

