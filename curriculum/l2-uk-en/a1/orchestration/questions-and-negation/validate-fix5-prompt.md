        # Fix 3 issue(s) in `questions-and-negation`

        ### Fix 1: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Уявіть' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 209):** `> Уявіть практичну ситуацію. Imagine a practical situation. Ви заходите в кав'ярню в Києві. You enter a coffee shop in Kyiv. Ви хочете замовити напій. You want to order a drink.`

### Fix 2: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Кажіть' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 254):** `Embrace the double negative structure. It makes your spoken Ukrainian sound very natural and expressive. Кажіть «ніко́ли не»! Say «ніко́ли не»! It is the only grammatically correct way to express this idea!`

### Fix 3: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'використовуйте' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 262):** `З поліцейським використовуйте **чи**. With a police officer use **чи**. Це показує повагу. This shows respect. With friends or family, drop **чи** and just raise your pitch.`


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/questions-and-negation.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/questions-and-negation.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/questions-and-negation.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

