Files confirmed. Now running the deep adversarial check.

---

## Issues Found

### CRITICAL — Issue 1: Wrong grammatical rule for numerals 2–4 (content, line 151)

**Quoted text:**
> After the numbers 2, 3, and 4, we use the Genitive singular form. This is unique to Slavic languages.

**Problem:** This is the *Russian* rule, not the Ukrainian rule. Ukrainian uses the **Nominative plural** after 2, 3, 4 — not the Genitive singular. The distinction is crucial:
- Ukrainian: **два студенти** (Nominative plural)
- Russian: **два студента** (Genitive singular)

The examples shown are actually correct Ukrainian forms (студенти, долари, квитки are all Nominative plural), but the metalinguistic label is wrong. Teaching learners that Ukrainian uses "Genitive singular" after 2–4 will cause direct errors: they will produce "два студента" (Russian form) thinking it is correct Ukrainian.

Evidence: студент → Gen.sg. = **студента**; Nom.pl. = **студенти** — the module uses "студенти," which is Nominative plural.

---

### CRITICAL — Issue 2: Three activity explanations propagate the same wrong rule (activities, lines 230, 252, 285)

**Line 230:**
```
explanation: 'Після чисел 2, 3, 4 вживаємо Родовий відмінок однини (студенти).'
```
**Wrong.** Gen.sg. of "студент" = **студента**. "студенти" is Nom.pl.

**Line 252:**
```
explanation: 'Квиток у родовому однини: квитки.'
```
**Wrong.** Gen.sg. of "квиток" = **квитка**. "квитки" is Nom.pl.

**Line 285:**
```
explanation: 'День у родовому однини: дні.'
```
**Wrong.** Gen.sg. of "день" = **дня**. "дні" is Nom.pl. The correct answer ("дні") is fine, but the explanation mislabels it — doubly bad because a learner who checks this with "дня" would think they're wrong.

---

### MODERATE — Issue 3: "Я дома" labeled incorrect when it is valid Ukrainian (content, lines 93–97)

**Quoted text:**
```
> English speakers often say "I'm home." In Ukrainian, this is impossible without a preposition.
> *   ❌ *Incorrect:* Я дома.
> *   ✅ *Correct:* **Я вдома**.
```

**Problem:** "Дома" is a standalone adverb in Ukrainian meaning "at home" — it is grammatically valid. Neither "дома" nor "вдома" uses a preposition in the modern sense; both are adverbs. Calling "Я дома" incorrect is factually wrong and will confuse learners who hear native speakers use it daily. The warning box's stated rationale ("impossible without a preposition") is false for this particular example. A genuinely broken example (where the preposition is actually missing from a case-governed phrase) is needed to make the pedagogical point correctly.

---

### MINOR — Issue 4: Typo "серендій рід" (activities, line 149)

```
explanation: 'Місто — воно (серендій рід), тому "твоє".'
```
Should be **середній рід**.

---

### MINOR — Issue 5: Sentence capitalization (content, line 100)

```
This is the "golden rule" of the Locative case. almost all singular nouns get the ending **-і**.
```
"almost" begins a new sentence and must be capitalized: **Almost**.

---

### IPA Verification — PASS

- ʋ used correctly for В throughout (not w) ✓
- t͡ʃ has tie bar in [t͡ʃɑsu] ✓  
- [ɦrɪu̯n⁽ʲ⁾i] for гривні — valid: В before consonant cluster vocalizes to u̯ in Ukrainian ✓
- All other transcriptions verified ✓

### Russianisms — CLEAN
### Russian characters — CLEAN
### Plan Compliance — PASS (all sections present, required vocabulary covered)
### Unjumble arrays — PASS (all arrays contain all tokens)
### Fill-in answers — PASS (all produce grammatical sentences)

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-navigation.md
---OLD---
### Quantity: 2, 3, 4
After the numbers 2, 3, and 4, we use the Genitive singular form. This is unique to Slavic languages.
*   **Один студент**.
*   **Два студенти** [stuˈdɛntɪ].
*   **Три гривні** [ɦrɪu̯n⁽ʲ⁾i].
*   **Чотири долари**.

Wait, what about 5? From 5 onwards, we switch to the *Genitive Plural* (п'ять студентів), but for now, just focus on 2, 3, and 4.
---NEW---
### Quantity: 2, 3, 4
After the numbers 2, 3, and 4, Ukrainian uses the **Nominative plural** form. This is an important difference from Russian, which uses the Genitive singular in the same position (Russian: "два студента"; Ukrainian: "два студенти").
*   **Один студент**.
*   **Два студенти** [stuˈdɛntɪ].
*   **Три гривні** [ɦrɪu̯n⁽ʲ⁾i].
*   **Чотири долари**.

What about 5? From 5 onwards, we switch to the *Genitive Plural* (п'ять студентів), but for now, just focus on 2, 3, and 4.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-navigation.md
---OLD---
> [!warning]
> **Don't lose your prepositions!**
> English speakers often say "I'm home." In Ukrainian, this is impossible without a preposition.
> *   ❌ *Incorrect:* Я дома.
> *   ✅ *Correct:* **Я вдома**.
---NEW---
> [!warning]
> **Don't drop prepositions!**
> Ukrainian location expressions require a preposition — you cannot skip it the way English sometimes does.
> *   ❌ *Incorrect:* Я школі. (No preposition — the sentence is broken.)
> *   ✅ *Correct:* **Я в школі.** (Preposition included — correct.)
>
> Note: **вдома** (at home) is the standard literary form for "at home."
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-navigation.md
---OLD---
This is the "golden rule" of the Locative case. almost all singular nouns get the ending **-і**.
---NEW---
This is the "golden rule" of the Locative case. Almost all singular nouns get the ending **-і**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/checkpoint-navigation.yaml
---OLD---
    - question: 'Виберіть правильну форму слова після числа 2: Два ____'
      explanation: 'Після чисел 2, 3, 4 вживаємо Родовий відмінок однини (студенти).'
---NEW---
    - question: 'Виберіть правильну форму слова після числа 2: Два ____'
      explanation: 'Після чисел 2, 3, 4 вживаємо Називний відмінок множини: студент → студенти.'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/checkpoint-navigation.yaml
---OLD---
    - question: 'Яка форма правильна після числа 3: Три ____'
      explanation: 'Гривня (жіночий рід) у родовому однини: гривні.'
---NEW---
    - question: 'Яка форма правильна після числа 3: Три ____'
      explanation: 'Гривня (жіночий рід) у Називному відмінку множини: гривня → гривні.'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/checkpoint-navigation.yaml
---OLD---
    - question: 'Оберіть закінчення після числа 4: Чотири ____'
      explanation: 'Квиток у родовому однини: квитки.'
---NEW---
    - question: 'Оберіть закінчення після числа 4: Чотири ____'
      explanation: 'Квиток у Називному відмінку множини: квиток → квитки.'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/checkpoint-navigation.yaml
---OLD---
    - question: 'Правильна форма для слова "день" після числа 2: Два ____'
      explanation: 'День у родовому однини: дні.'
---NEW---
    - question: 'Правильна форма для слова "день" після числа 2: Два ____'
      explanation: 'День у Називному відмінку множини: день → дні.'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/checkpoint-navigation.yaml
---OLD---
      explanation: 'Місто — воно (серендій рід), тому "твоє".'
---NEW---
      explanation: 'Місто — воно (середній рід), тому "твоє".'
===FIX_END===

===VERDICT===
APPROVE
===END_VERDICT===