## Adversarial QA — The Dative I: Pronouns (a2-01)

I read both files in full before issuing any verdict. Here is what I found.

---

## Issues Found

### Issue 1: Invalid callout type `[!observe]`
**File:** `the-dative-i-pronouns.md`, Practice section "Квіти для живих"
`> [!observe]` is not a valid callout type. The content describes a cultural rule, not an observation prompt.
**Fix:** → `[!culture]`

---

### Issue 2: `дослівно` bug — Age expression section
**File:** `the-dative-i-pronouns.md`, Introduction section
Exact text: `Ми кажемо: **«Мені 20 років»** (дослівно: «Мені 20 років»).`
The parenthetical literally repeats the Ukrainian phrase unchanged. The point is to show the English-literal contrast ("To me is 20 years"), not to duplicate the Ukrainian. This is a copy-paste LLM artifact that teaches nothing.

---

### Issue 3: `дослівно` bug — Physical states section
**File:** `the-dative-i-pronouns.md`, Фізичні відчуття section
Exact text: `**Холодно** (cold) → **Мені холодно** (I am cold / дослівно: «Мені холодно»).`
Same artifact: the `дослівно` annotation repeats the target Ukrainian instead of providing the English literal translation that would aid comprehension.

---

### Issue 4: Dialogue uses Genitive — contradicts taught rule
**File:** `the-dative-i-pronouns.md`, "В гостях" dialogue
`— Мені треба лише води, дякую.`
"Води" is Genitive of "вода". The module explicitly teaches `треба + Nominative noun`. This is a direct contradiction that will confuse A2 learners. The Green Team's fix is correct.

---

### Issue 5: Missing comma in fill-in sentence
**File:** `activities/the-dative-i-pronouns.yaml`, "Змішана практика" section
`'Я думаю, ні, мені навіть ___ що це помилка.'`
When the blank is filled: `мені навіть здається що це помилка` — the subordinate clause introduced by `що` requires a comma. The sentence should pre-position the comma so the completed sentence is grammatical: `мені навіть ___, що це помилка.`

---

### Issue 6: Missing comma — unjumble "На жаль" item
**File:** `activities/the-dative-i-pronouns.yaml`, unjumble "Складіть речення: Подобатися"
`answer: 'На жаль йому зовсім не подобається ця гучна музика'`
Introductory phrase "На жаль" requires a comma. Neither the words array token nor the answer includes it.

---

### Issue 7: Missing comma — unjumble "Скажіть" item
**File:** `activities/the-dative-i-pronouns.yaml`, unjumble "Складіть речення: Подобатися"
`answer: 'Скажіть чи вам подобається наше старе історичне місто'`
Imperative + indirect question requires comma: "Скажіть, чи..."

---

### Issue 8: Missing comma — unjumble vocative "колего"
**File:** `activities/the-dative-i-pronouns.yaml`, unjumble "Складіть речення: Діалоги"
`answer: 'Мені дуже приємно познайомитися з вами сьогодні колего'`
"Колего" is a vocative — Ukrainian grammar mandates a comma before it.

---

### Issue 9: Missing comma — unjumble "Вибачте" item
**File:** `activities/the-dative-i-pronouns.yaml`, unjumble "Складіть речення: Діалоги"
`answer: 'Вибачте чи можу я вам допомогти знайти дорогу'`
"Вибачте" as a polite interjection requires a separating comma: "Вибачте, чи..."

---

### Issue 10: Missing comma — unjumble "здається що"
**File:** `activities/the-dative-i-pronouns.yaml`, unjumble "Складіть речення: Діалоги"
`answer: 'Мені чомусь здається що це все абсолютна правда'`
Subordinate "що"-clause requires comma after "здається": "Мені чомусь здається, що..."

---

### Note (plan compliance, no fix possible in module): Required vocabulary "необхідно" from `vocabulary_hints.required` does not appear in prose or activities. The vocabulary YAML file is also missing. The audit recorded this as "1 info" gate. Since the vocabulary file does not exist, the word cannot be introduced without creating that file — flagged for follow-up.

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a2/the-dative-i-pronouns.md
---OLD---
> [!observe]
> **Квіти для живих**
---NEW---
> [!culture]
> **Квіти для живих**
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/the-dative-i-pronouns.md
---OLD---
Ми кажемо: **«Мені 20 років»** (дослівно: «Мені 20 років»).
---NEW---
Ми кажемо: **«Мені 20 років»** (literally: *To me is 20 years* — not "I am 20 years old").
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/the-dative-i-pronouns.md
---OLD---
*   **Холодно** (cold) → **Мені холодно** (I am cold / дослівно: «Мені холодно»).
---NEW---
*   **Холодно** (cold) → **Мені холодно** (I am cold / literally: *To me is cold*).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/the-dative-i-pronouns.md
---OLD---
— Мені треба лише води, дякую. Я дуже хочу пити.
---NEW---
— Мені потрібна лише вода, дякую. Я дуже хочу пити.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-dative-i-pronouns.yaml
---OLD---
    - sentence: 'Я думаю, ні, мені навіть ___ що це помилка.'
---NEW---
    - sentence: 'Я думаю, ні, мені навіть ___, що це помилка.'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-dative-i-pronouns.yaml
---OLD---
    - words: ['На', 'жаль', 'йому', 'зовсім', 'не', 'подобається', 'ця', 'гучна', 'музика']
      answer: 'На жаль йому зовсім не подобається ця гучна музика'
---NEW---
    - words: ['На', 'жаль,', 'йому', 'зовсім', 'не', 'подобається', 'ця', 'гучна', 'музика']
      answer: 'На жаль, йому зовсім не подобається ця гучна музика'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-dative-i-pronouns.yaml
---OLD---
    - words: ['Скажіть', 'чи', 'вам', 'подобається', 'наше', 'старе', 'історичне', 'місто']
      answer: 'Скажіть чи вам подобається наше старе історичне місто'
---NEW---
    - words: ['Скажіть,', 'чи', 'вам', 'подобається', 'наше', 'старе', 'історичне', 'місто']
      answer: 'Скажіть, чи вам подобається наше старе історичне місто'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-dative-i-pronouns.yaml
---OLD---
    - words: ['Мені', 'дуже', 'приємно', 'познайомитися', 'з', 'вами', 'сьогодні', 'колего']
      answer: 'Мені дуже приємно познайомитися з вами сьогодні колего'
---NEW---
    - words: ['Мені', 'дуже', 'приємно', 'познайомитися', 'з', 'вами', 'сьогодні,', 'колего']
      answer: 'Мені дуже приємно познайомитися з вами сьогодні, колего'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-dative-i-pronouns.yaml
---OLD---
    - words: ['Вибачте', 'чи', 'можу', 'я', 'вам', 'допомогти', 'знайти', 'дорогу']
      answer: 'Вибачте чи можу я вам допомогти знайти дорогу'
---NEW---
    - words: ['Вибачте,', 'чи', 'можу', 'я', 'вам', 'допомогти', 'знайти', 'дорогу']
      answer: 'Вибачте, чи можу я вам допомогти знайти дорогу'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-dative-i-pronouns.yaml
---OLD---
    - words: ['Мені', 'чомусь', 'здається', 'що', 'це', 'все', 'абсолютна', 'правда']
      answer: 'Мені чомусь здається що це все абсолютна правда'
---NEW---
    - words: ['Мені', 'чомусь', 'здається,', 'що', 'це', 'все', 'абсолютна', 'правда']
      answer: 'Мені чомусь здається, що це все абсолютна правда'
===FIX_END===

===VERDICT===
APPROVE
===END_VERDICT===