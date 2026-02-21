Now I have all the information I need for a thorough review. Let me compile the findings.

---

# Phase 9: Final Adversarial QA — being-and-becoming (a2-06)

## Issues Found

### ISSUE 1: Cloze passage — logical error ("вступила до університету і стала економісткою")
**File:** `activities/being-and-becoming.yaml`, line 423
**Text:** `Вона вступила до університету і стала {{5}}.`
**Problem:** "Вступити до" means "to enroll in." You don't become an economist by enrolling — you become one by graduating. The prose content correctly says "Вона **закінчила** економічний університет і стала економісткою" (line 253 of .md). The cloze should match.
**Fix:** "вступила до університету" → "закінчила університет"

### ISSUE 2: Cloze blank 7 — story inconsistency (менеджером vs аналітиком)
**File:** `activities/being-and-becoming.yaml`, lines 443-445
**Text:** Blank 7 answer is `менеджером`
**Problem:** The cloze says she worked as "аналітиком" (blank 6), then "Вона не хотіла бути менеджером все життя." If she worked as an analyst, she wouldn't want to be an analyst forever — not a manager. The prose story has no manager role for Iryna. The answer should be "аналітиком" for story coherence.

### ISSUE 3: Pedagogical contradiction — "Вона є успішною директоркою" uses є + Instrumental in present tense
**File:** `being-and-becoming.md`, line 232
**Text:** `*   Вона є успішною **директоркою**.`
**Problem:** The module explicitly teaches (line 116): "In the present tense, it is invisible (Zero Copula)." and "But when we travel to the past or future, it appears, and it demands the Instrumental case." Two paragraphs after the feminitives section, we see "є" + Instrumental in a present-tense example. This directly contradicts the taught rule. A2 learners will be confused. Should use present-tense Nominative construction instead.
**Fix:** → `*   Вона — успішна **директорка**.`

### ISSUE 4: Group-sort spelling inconsistency — "учитель" vs "вчителька"
**File:** `activities/being-and-becoming.yaml`, line 128
**Text:** Masculine group has `'учитель'` but feminine group has `'вчителька'`
**Problem:** The module content uses "вчитель" consistently (line 73: "Вчитель → вчителем"). The group-sort masculine uses "учитель" while the feminine uses "вчителька" (derived from "вчитель"). Both spellings are valid per the 2019 orthography, but within one module, consistency matters. A learner seeing "учитель" here but "вчитель" everywhere else will be confused.

### ISSUE 5: Feminitive fill-in spelling inconsistency — "учитель/учителька"
**File:** `activities/being-and-becoming.yaml`, lines 470-472
**Text:** `'Він — учитель, вона — (учитель) ________.'` with answer `'учителька'`
**Problem:** Same inconsistency as Issue 4. The rest of the module uses "вчитель/вчителька".

### ISSUE 6: Вправа 2 pedagogical tension — "Вона стала директором" marked correct without feminitive note
**File:** `being-and-becoming.md`, line 332
**Text:** `3. **Так.**` (answering whether "Вона стала директором" is correct grammar)
**Problem:** The module actively teaches feminitives and the 2019 reform. Marking "Вона стала директором" as simply correct without noting the modern preference creates tension. The prose itself shows both forms: "стала лікаркою (або лікарем)" at line 245. A brief parenthetical note preserves the answer while reinforcing the feminitive teaching.

### ISSUE 7: Duplicate vocabulary entries
**File:** `vocabulary/being-and-becoming.yaml`, lines 81-92
**Text:** Three entries duplicated with different capitalization:
- "Називний відмінок" duplicates "називний відмінок" (lines 1-4)
- "Орудний відмінок" duplicates "орудний відмінок" (lines 9-12)
- "Множина" duplicates "множина" (lines 17-20)

### ISSUE 8 (FLAG ONLY): Missing "ставати" — plan-required vocabulary
The plan explicitly lists `ставати (to be becoming)` as REQUIRED vocabulary. The imperfective counterpart to "стати" is never introduced or used anywhere in the content or activities. This is a notable plan compliance gap that would require prose additions.

### ISSUE 9 (FLAG ONLY): Missing "юристка" — plan-required vocabulary pair
The plan requires `юрист / юристка`. Only the masculine "юрист/юристом" appears (dialogue 3). The feminitive is absent from both prose and activities.

### ISSUE 10 (FLAG ONLY): Missing "програмувальник" — plan-specified formal variant
Plan says: "mention formal програмувальник vs. universally used програміст." Research notes confirm this. Not in the content.

### ISSUE 11 (FLAG ONLY): Missing "громадянин/громадянка" — plan-recommended State Standard example
Plan recommends: "громадянин / громадянка (citizen) — мріє стати громадянкою України (State Standard example)." Neither the word nor the example appears anywhere.

---

## Verification Summary

- Content lines read: 482 (full file)
- Activity items checked: ~96 items across 12 activities
- Unjumble word arrays verified: 6/6 (all words match answers)
- Fill-in answers verified: all produce grammatical sentences
- Ukrainian sentences grammar-checked: ~120
- IPA transcriptions verified: 23 entries (tie bars present on affricates, ʋ for В, u̯ for coda В)
- Russianisms scan: CLEAN
- Russian characters scan: CLEAN
- Factual claims verified: Zelenskyy 2019 ✓, Khmelnytsky 5 UAH ✓, Baptism 988 ✓, Skovoroda epitaph ✓, Krushelnytska Butterfly ✓, Hetman 1648 ✓
- LLM artifacts: minor ("magical verbs") but within persona
- Word count: 3278 raw / 3042 effective (target 3000) ✓

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/being-and-becoming.yaml
---OLD---
  passage: 'Коли Ірина була маленькою {{1}}, вона мріяла стати {{2}}. Її батьки були {{3}}, тому вони хотіли, щоб вона теж стала {{4}}. Але життя змінилося. Вона вступила до університету і стала {{5}}. Після навчання вона п'ять років працювала {{6}} у банку. Це було нудно. Вона не хотіла бути {{7}} все життя. Зараз вона змінила професію. Тепер Ірина працює {{8}}. Вона також планує стати {{9}}. Її друзі стали {{10}}, а вона стала {{11}}. Вона дуже щаслива бути {{12}} людиною.'
---NEW---
  passage: 'Коли Ірина була маленькою {{1}}, вона мріяла стати {{2}}. Її батьки були {{3}}, тому вони хотіли, щоб вона теж стала {{4}}. Але життя змінилося. Вона закінчила університет і стала {{5}}. Після навчання вона п'ять років працювала {{6}} у банку. Це було нудно. Вона не хотіла бути {{7}} все життя. Зараз вона змінила професію. Тепер Ірина працює {{8}}. Вона також планує стати {{9}}. Її друзі стали {{10}}, а вона стала {{11}}. Вона дуже щаслива бути {{12}} людиною.'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/being-and-becoming.yaml
---OLD---
    - id: 7
      answer: 'менеджером'
      options: ['менеджером', 'менеджер', 'менеджера', 'менеджеру']
---NEW---
    - id: 7
      answer: 'аналітиком'
      options: ['аналітиком', 'аналітик', 'аналітика', 'аналітику']
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/being-and-becoming.md
---OLD---
*   Вона є успішною **директоркою**.
---NEW---
*   Вона — успішна **директорка**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/being-and-becoming.yaml
---OLD---
        - 'учитель'
        - 'директор'
---NEW---
        - 'вчитель'
        - 'директор'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/being-and-becoming.yaml
---OLD---
    - sentence: 'Він — учитель, вона — (учитель) ________.'
      answer: 'учителька'
      options: ['учителька', 'учителькою', 'учителі', 'учителя']
---NEW---
    - sentence: 'Він — вчитель, вона — (вчитель) ________.'
      answer: 'вчителька'
      options: ['вчителька', 'вчителькою', 'вчителі', 'вчителя']
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/being-and-becoming.md
---OLD---
3. **Так.**
4. **Так.**
</details>
---NEW---
3. **Так.** (Але сучасна форма: **стала директоркою**)
4. **Так.**
</details>
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/being-and-becoming.yaml
---OLD---
- term: Називний відмінок
  ipa: "nɑzɪu̯ˈnɪj vidˈminɔk"
  translation: "Nominative case"
  pos: noun phrase
- term: Орудний відмінок
  ipa: "ɔˈrudnɪj vidˈminɔk"
  translation: "Instrumental case"
  pos: noun phrase
- term: Множина
  ipa: "mnɔʒɪˈnɑ"
  translation: "plural"
  pos: noun
---NEW---
---
===FIX_END===

---

## Assessment

**Strengths:**
- Excellent pedagogy: "Costume Analogy" and "Nominative Trap" are strong A2-appropriate scaffolds
- The Iryna narrative is genuinely engaging and models the full grammar range naturally
- Activities are dense (12 activities, 10 types, ~96 items) with good variety
- Feminitives section is well-integrated and culturally current
- IT/coworking context is authentic and relevant
- IPA in vocabulary is clean (tie bars, ʋ, correct stress)
- No Russianisms, no Russian characters, no broken activities
- Word count exceeds target (3042/3000)

**Weaknesses (flagged, not fixed — require prose expansion):**
- Missing `ставати` (imperfective) — plan-required vocabulary, never introduced
- Missing `юристка` — plan requires both gender forms
- Missing `програмувальник` — plan-specified formal variant
- Missing `громадянин/громадянка` — plan-recommended State Standard example

These gaps are notable for plan compliance but don't rise to REJECT level: the core grammar (бути/стати/працювати + Instrumental) is thoroughly taught and drilled, the content exceeds word target, and the activities are robust. The missing items would strengthen the module if added in a future pass.

===VERDICT===
APPROVE
===END_VERDICT===