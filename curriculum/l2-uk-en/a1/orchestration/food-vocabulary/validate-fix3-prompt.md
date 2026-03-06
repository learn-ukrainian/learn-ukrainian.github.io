        # Fix 4 issue(s) in `food-vocabulary`

        ### Fix 1: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'ятайте' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 23):** `Слова чоловічого роду зазвичай закінчуються на твердий приголосний звук. Це дуже велика і популярна категорія слів. Ми часто використовуємо ці слова щодня. Коли ви вчите нове слово, запам'ятайте його рід.`

### Fix 2: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Уявіть' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 194):** `Подивімося уважно, як ці граматичні правила працюють у реальному житті. Уявіть затишне сучасне кафе. Ви хочете зробити замовлення.`

### Fix 3: PEDAGOGICAL
**What:** [NO_IMPERATIVES_EARLY_A1] 'Використовуйте' — Imperative verb forms should not appear in early A1 modules (M1-46). Students haven't learned verb conjugation yet.
**How to fix:** Replace imperative verbs with English instructions or simple noun phrases. E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'
**Context (line 257):** `Коли ви кажете цю фразу, ви повинні змінити слово. Використовуйте знахідний відмінок для їжі та напоїв. Правило працює абсолютно однаково.`

### Fix 4: PLAN_SECTION_MISSING
**What:** Missing 5 plan section(s): Їжа (Food), Напої (Drinks), Паляниця (The Shibboleth Bread), Мені подобається / Я не їм (Preferences), Практика (Practice)
**How to fix:** Add content for the missing plan sections or update section headings to match plan.
**Where:** (plan vs content)

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

This module is 4544 words. Fix ONLY sections: "Напої", "Я люблю / Я не їм"

**Output format:**
```
===SECTION_FIX_START===
## {section title}
{fixed section content}
===SECTION_FIX_END===
```

