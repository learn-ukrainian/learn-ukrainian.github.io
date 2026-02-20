Good, all files match the prompt. Let me now do the deep adversarial review systematically.

---

## Adversarial QA Review: my-family (a1-32)

### Issue 1: IPA Error — дочка stress placement
**File:** my-family.md, line 71
**Current:** `**дочка** [dot͡ʃˈkɑ]`
**Problem:** Stress is on the wrong syllable. Ukrainian "дочка" has stress on the first syllable: [ˈdot͡ʃkɑ], not the second. This is a phonological error that would teach incorrect pronunciation.

### Issue 2: Gender mismatch — "вона друг"
**File:** my-family.md, line 347
**Current:** `**Сестра — це подруга?** (Is sister a friend?) — **Так, вона друг.**`
**Problem:** The question uses the feminine "подруга" but the answer uses the masculine "друг" with the feminine pronoun "вона". This directly contradicts the gender agreement lesson being taught. The opener at line 17 even says "Моя сестра — моя **подруга**", making this self-contradictory.

### Issue 3: Awkward English — "important definition"
**File:** my-family.md, line 197
**Current:** `their age relative to you is important definition.`
**Problem:** "Important definition" is garbled English. Should be "an important distinction".

### Issue 4: Untaught vocabulary in activity — Племінник/Племінниця
**File:** activities/my-family.yaml, lines 34-35, 40-41
**Current:** Match-up includes "Син брата" → "Племінник" and "Донька сестри" → "Племінниця"
**Problem:** Neither "племінник" nor "племінниця" appear anywhere in the content or the plan's vocabulary_hints. The learner has zero exposure to these words. Testing untaught vocabulary violates the "Teach then Test" principle.

### Issue 5: Untaught Vocative forms in match-up activity
**File:** activities/my-family.yaml, lines 172-179
**Current:** Match-up includes Брат→Брате, Сестра→Сестро, Андрій→Андрію, Олена→Олено
**Problem:** The content explicitly states (line 435): "You don't need to learn the whole grammar table yet, but you MUST know these four forms." Those four are Мамо, Тату, Бабусю, Дідусю. The Vocative forms for Брат, Сестра, Андрій, Олена are never taught. Additionally, "сину" IS modeled in the dialogue at line 413 ("Привіт, сину!"), so it's fair game but the others are not.

### Issue 6: Untaught Vocative forms in fill-in activity
**File:** activities/my-family.yaml, lines 201-216
**Current:** Fill-in tests Брате, Сестро, Андрію, Олено
**Problem:** Same as Issue 5 — these forms were never introduced. The explanation even admits it: "generic rule preview" (line 204). A "preview" is not teaching. Testing it is unfair.

### Issue 7: Off-topic pair in first match-up
**File:** activities/my-family.yaml, lines 19-20
**Current:** `"Хлопець" / "Дівчина"` pair in a family members match-up
**Problem:** Хлопець (guy/boyfriend) and Дівчина (girl/girlfriend) are not family terms. They're never formally introduced in the lesson. This pair is noise in a family vocabulary activity.

### Plan Deviations (noted, not blocking):
- **Зовнішність missing:** Plan calls for "Моя мама має темне волосся" (appearance descriptions). Content covers character traits only — no physical descriptions.
- **Age number phrases skipped:** Plan calls for "simple number phrases (25 років)". Content explicitly defers to A2. Defensible for A1 safety but IS a deviation.
- **No family holiday dialogue:** Plan Practice 2 calls for "Діалог про родинне свято". Not present.

These are scope/coverage gaps, not errors. Content is 3648 words (well above 2000 target), so they're not caused by laziness.

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-family.md
---OLD---
A daughter is **донька** [ˈdonʲkɑ] or sometimes **дочка** [dot͡ʃˈkɑ].
---NEW---
A daughter is **донька** [ˈdonʲkɑ] or sometimes **дочка** [ˈdot͡ʃkɑ].
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-family.md
---OLD---
3.  **Сестра — це подруга?** (Is sister a friend?) — **Так, вона друг.**
---NEW---
3.  **Сестра — це подруга?** (Is sister a friend?) — **Так, вона подруга.**
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-family.md
---OLD---
When you have siblings, their age relative to you is important definition.
---NEW---
When you have siblings, their age relative to you is an important distinction.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/my-family.yaml
---OLD---
    - left: "Син брата"
      right: "Племінник"
    - left: "Тато і мама"
      right: "Батьки"
    - left: "Чоловік мами"
      right: "Тато"
    - left: "Донька сестри"
      right: "Племінниця"
---NEW---
    - left: "Син сина"
      right: "Онук"
    - left: "Тато і мама"
      right: "Батьки"
    - left: "Чоловік мами"
      right: "Тато"
    - left: "Донька доньки"
      right: "Онука"
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/my-family.yaml
---OLD---
    - left: "Чоловік"
      right: "Дружина"
    - left: "Хлопець"
      right: "Дівчина"
---NEW---
    - left: "Чоловік"
      right: "Дружина"
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/my-family.yaml
---OLD---
    - left: "Мама"
      right: "Мамо!"
    - left: "Тато"
      right: "Тату!"
    - left: "Бабуся"
      right: "Бабусю!"
    - left: "Дідусь"
      right: "Дідусю!"
    - left: "Брат"
      right: "Брате!"
    - left: "Сестра"
      right: "Сестро!"
    - left: "Андрій"
      right: "Андрію!"
    - left: "Олена"
      right: "Олено!"
---NEW---
    - left: "Мама"
      right: "Мамо!"
    - left: "Тато"
      right: "Тату!"
    - left: "Бабуся"
      right: "Бабусю!"
    - left: "Дідусь"
      right: "Дідусю!"
    - left: "Син"
      right: "Сину!"
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/my-family.yaml
---OLD---
    - sentence: "{{answer}}, ти мій найкращий друг."
      answer: "Брате"
      options: ["Брате", "Брат", "Брата", "Брату"]
      explanation: "Addressing brother -> Vocative «Брате» (generic rule preview)."
    - sentence: "{{answer}}, яка ти гарна!"
      answer: "Сестро"
      options: ["Сестро", "Сестра", "Сестри", "Сестру"]
      explanation: "Addressing sister -> Vocative «Сестро»."
    - sentence: "{{answer}}, де ти?"
      answer: "Андрію"
      options: ["Андрію", "Андрій", "Андрія", "Андрієм"]
      explanation: "Addressing Andrew -> Vocative «Андрію»."
    - sentence: "{{answer}}, привіт!"
      answer: "Олено"
      options: ["Олено", "Олена", "Олени", "Олені"]
      explanation: "Addressing Olena -> Vocative «Олено»."
---NEW---
    - sentence: "Привіт, {{answer}}! Як ти?"
      answer: "сину"
      options: ["сину", "син", "сина", "сином"]
      explanation: "Greeting your son -> Vocative «сину» (modeled in the phone dialogue)."
    - sentence: "{{answer}}, я тебе люблю!"
      answer: "Мамо"
      options: ["Мамо", "Мама", "Мами", "Маму"]
      explanation: "Expressing love to mom -> Vocative «Мамо»."
===FIX_END===

---

## Review Summary

| Check | Result |
|-------|--------|
| IPA accuracy | 1 error fixed (дочка stress) |
| Russianisms | CLEAN |
| Russian characters | CLEAN |
| Gender/case agreement | 1 error fixed (вона друг → подруга) |
| Activities test only taught material | 3 violations fixed (Vocative match-up, Vocative fill-in, Племінник/Племінниця) |
| Unjumble word arrays | All 12 items verified correct |
| Fill-in grammaticality | All items produce grammatical sentences |
| Factual accuracy | CLEAN |
| LLM artifacts | Minimal ("superpower" is mildly cliché, acceptable) |
| Plan compliance | Content covers 5/6 plan sections; Зовнішність and age number phrases missing |
| Word count | 3648 words (183% of 2000 target) — PASS |

**After fixes:** All activities test only taught/modeled forms. IPA is correct. Gender agreement is consistent. The content itself is warm, well-structured, and pedagogically sound. The plan deviations (appearance, exact age) are defensible scope choices at A1 level and don't warrant rejection given the content's overall quality and length.

===VERDICT===
APPROVE
===END_VERDICT===