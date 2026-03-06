        # Fix 5 issue(s) in `food-vocabulary`

        ### Fix 1: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'поділіть' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 357):** `Подивіться на ці слова і швидко поділіть їх. Перша група — це їжа. Друга група — це напої.`

### Fix 2: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'подумайте' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 367):** `Тепер подумайте про закінчення слів. Знайдіть слова чоловічого роду. Потім знайдіть слова жіночого роду.`

### Fix 3: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Знайдіть' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 367):** `Тепер подумайте про закінчення слів. Знайдіть слова чоловічого роду. Потім знайдіть слова жіночого роду.`

### Fix 4: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'знайдіть' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 367):** `Тепер подумайте про закінчення слів. Знайдіть слова чоловічого роду. Потім знайдіть слова жіночого роду.`

### Fix 5: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Зробімо' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 353):** `Зробімо дуже швидку і надзвичайно корисну вправу. Вона чудово тренує ваш мозок і пам'ять.`

### Other Audit Failures

```
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/food-vocabulary-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/food-vocabulary.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/food-vocabulary.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/food-vocabulary.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

## Large Module — Section-Level Output

This module is 4560 words. Fix ONLY sections: "Мені подобається / Я не їм (Preferences)", "Напої (Drinks)"

**Output format:**
```
===SECTION_FIX_START===
## {section title}
{fixed section content}
===SECTION_FIX_END===
```

