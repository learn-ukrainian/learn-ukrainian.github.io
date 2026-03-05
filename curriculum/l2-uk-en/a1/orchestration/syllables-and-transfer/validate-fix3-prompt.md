        # Fix 6 issue(s) in `syllables-and-transfer`

        ### Fix 1: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Подивімось' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 23):** `Подивімось на коротке слово. Let us look at a short word:`

### Fix 2: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'поговорімо' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 45):** `Тепер поговорімо про два типи складів: відкриті та закриті. Now let's talk about two types of syllables: open and closed. Це дуже важливо. This is very important.`

### Fix 3: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Повторімо' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 117):** `Повторімо. Let us review the fundamental concepts you have learned about syllables and dividing words. You now have the tools to tackle long, intimidating words with confidence.`

### Fix 4: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'поговорімо' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 45):** `Тепер поговорімо про два типи складів: відкриті та закриті. Now let's talk about two types of syllables: open and closed. Це дуже важливо. This is very important.`

### Fix 5: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'Повторімо' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 117):** `Повторімо. Let us review the fundamental concepts you have learned about syllables and dividing words. You now have the tools to tackle long, intimidating words with confidence.`

### Fix 6: ACTIVITY_VESUM_FAIL
**What:** Activity answers contain VESUM-failed words: ка, ло, стра
**How to fix:** Fix spelling or replace these words — students will practice non-existent forms.
**Where:** syllables-and-transfer.yaml


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M5-10 — Phonology & First Grammar):
Full alphabet known. Modules teach: syllables (M5), stress (M6), gender (M7), greetings (M8), Це/Я/Мене звати (M9), Що це? (M10).

GRAMMAR STATUS:
- AVAILABLE: bare nouns, gender classification, Це + noun, Я + noun, memorized politeness phrases (Дякую, Будь ласка, Вибачте from M8)
- FORBIDDEN: verb conjugation, imperatives, adjective agreement, plurals, all cases except nominative
- Use English for all classroom instructions

METALANGUAGE: English-first, Ukrainian term in parentheses on first use



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/syllables-and-transfer.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/syllables-and-transfer.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/syllables-and-transfer.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

