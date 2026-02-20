Good — the `items:` wrapper is used by several vocab files (4 out of the set), so it's an established pattern, not a format error. Now I have all the information needed for the review.

---

# Phase 9: Adversarial QA Review — what-time-is-it (a1-23)

## Issues Found

### Issue 1 — CRITICAL: Vowel Harmony Callout Is Factually Wrong
**File:** `what-time-is-it.md:157-158`
**Text:** "If the next word starts with a consonant, use **у**. If it starts with a vowel, use **в**."
**Problem:** This rule is backwards AND contradicts the examples. The example **в понеділок** has понеділок starting with a consonant, but the rule says to use **у** before consonants. Furthermore, NO day of the week starts with a vowel, making the **в** rule irrelevant here. The actual alternation depends on the *preceding* word's ending (vowel → в, consonant → у), not the following word's beginning. A1 learners will be confused and form wrong habits.

### Issue 2 — CRITICAL: Dialogue 3 Uses Unnatural Static Verbs
**File:** `what-time-is-it.md:339-342`
**Text:** "Коли буде поїзд до Львова?" / "Поїзд буде о п'ятій тридцять."
**Problem:** Using **бути** (to be) for train schedules is unnatural when **відправлятися/прибувати** were already introduced in the same module (lines 101, 238, 305-306). At a ticket window, Ukrainians say "Коли відправляється поїзд?" not "Коли буде поїзд?". This teaches the wrong register.

### Issue 3 — SIGNIFICANT: IPA Stress Error on п'ятнадцять
**File:** `what-time-is-it.md:83`
**Text:** `[ˈʋɔsʲ.mɑ pˈjɑt.nɑ.t͡sʲɑtʲ]`
**Problem:** Stress is on the wrong syllable. п'ятнадцять has stress on the second syllable (п'ят**на́**дцять), not the first. Correct: `[pjɑtˈnɑ.t͡sʲɑtʲ]`.

### Issue 4 — MINOR: Typo "цифферблаті" in Activities
**File:** `what-time-is-it.yaml:140`
**Text:** "цифферблаті" (double ф)
**Problem:** Correct Ukrainian spelling is **циферблат** (one ф). "Цифферблаті" is a misspelling.

### Issue 5 — SIGNIFICANT: Plan Compliance Gap — "Пів на / Чверть" Forms Missing
**File:** `what-time-is-it.md` (Presentation section)
**Problem:** The plan's `content_outline` explicitly includes the point: "Половина та чверть (Пів на другу, чверть на третю) — learner error: confusing 'пів на' (half TO the next hour)". The module completely omits these forms. Even though telegraphic style is prioritized for A1, the plan calls for at least mentioning their existence. A preview note satisfies plan compliance without overloading learners.

### Issue 6 — MINOR: LLM Purple Prose Opener
**File:** `what-time-is-it.md:13`
**Text:** "Time is the heartbeat of daily life in Ukraine."
**Problem:** Classic LLM cliché ("the heartbeat of X"). Should be more direct.

### Issue 7 — MINOR: IPA Inconsistency in Укрзалізниця
**File:** `what-time-is-it.md:20`
**Text:** `[ukr.za.lʲizˈnɪ.t͡sʲa]`
**Problem:** Uses `[a]` for Ukrainian а, while every other IPA transcription in the module correctly uses `[ɑ]`. Should be `[ukr.zɑ.lʲizˈnɪ.t͡sʲɑ]` for consistency.

### Issue 8 — MINOR: Unverifiable Statistic
**File:** `what-time-is-it.md:20`
**Text:** "over 90% of trains arrive exactly on schedule"
**Problem:** Specific percentage without source. While Ukrzaliznytsia has maintained remarkable reliability, "exactly on schedule" with a precise figure is potentially inflated. Softening to a qualitative claim avoids presenting an unverifiable number as fact.

### Issue 9 — MINOR: Awkward Ukrainian in Activity Explanation
**File:** `what-time-is-it.yaml:6`
**Text:** "використовується для дізнання поточного часу"
**Problem:** "для дізнання" is not natural Ukrainian. The verbal noun дізнання is not commonly used this way. Natural form: "щоб дізнатися поточний час".

### Issue 10 — NOTED: Vocabulary File Missing Recommended Items
**File:** `what-time-is-it.yaml` (vocabulary)
**Problem:** Plan recommends **січень** and **рано** but neither is in the vocabulary file. No month names at all despite the module teaching 12 months. Recommend enrichment in a separate pass.

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/what-time-is-it.md
---OLD---
> Time is the heartbeat of daily life in Ukraine. Whether you are catching a train that leaves exactly on the minute or arranging a coffee meeting with a friend, precision matters. This lesson gives you the power to navigate schedules, appointments, and deadlines with confidence.
---NEW---
> Knowing the time is essential for daily life in Ukraine. Whether you are catching a train or arranging a coffee meeting with a friend, precision matters. After this lesson, you will be able to read the clock, schedule appointments, and understand train tickets in Ukrainian.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/what-time-is-it.md
---OLD---
> The Ukrainian railway system, **Укрзалізниця** [ukr.za.lʲizˈnɪ.t͡sʲa], is legendary for its resilience and punctuality. Even during the most difficult times of war, over 90% of trains arrive exactly on schedule. In Ukraine, time is respected. Being "on time" (**вчасно** [ˈu̯t͡ʃɑs.nɔ]) is a sign of reliability.
---NEW---
> The Ukrainian railway system, **Укрзалізниця** [ukr.zɑ.lʲizˈnɪ.t͡sʲɑ], is legendary for its resilience and punctuality. Even during the most difficult times of war, the vast majority of trains continue to run on schedule. In Ukraine, time is respected. Being "on time" (**вчасно** [ˈu̯t͡ʃɑs.nɔ]) is a sign of reliability.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/what-time-is-it.md
---OLD---
*   08:15 — **Восьма п'ятнадцять** [ˈʋɔsʲ.mɑ pˈjɑt.nɑ.t͡sʲɑtʲ]
---NEW---
*   08:15 — **Восьма п'ятнадцять** [ˈʋɔsʲ.mɑ pjɑtˈnɑ.t͡sʲɑtʲ]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/what-time-is-it.md
---OLD---
Цей метод — простий. Ви говорите годину і хвилини. Це ввічливо і правильно.
---NEW---
Цей метод — простий. Ви говорите годину і хвилини. Це ввічливо і правильно.

> [!note] **Preview: Half and Quarter**
> In everyday speech, you may also hear **пів на другу** (half past one, literally "half to the second hour") and **чверть на третю** (quarter past two). These forms are common but more complex — we will learn them at a later stage. For now, the telegraphic style covers all your needs.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/what-time-is-it.md
---OLD---
> [!observe] **Vowel Harmony**
> Notice we switch between **у** and **в** (e.g., **у вівторок**, **в понеділок**) to make speech flow smoothly. The rule is simple: avoid stacking consonants. If the next word starts with a consonant, use **у**. If it starts with a vowel, use **в**.
---NEW---
> [!observe] **У or В?**
> You will see both **у** and **в** before days of the week. The choice depends on the sound *before* the preposition: use **у** after a consonant or at the start of a sentence (**У понеділок я працюю**), and **в** after a vowel (**Я працюю в понеділок**). This keeps speech flowing smoothly. At A1, using **у** is always a safe choice.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/what-time-is-it.md
---OLD---
— **Добрий день. Коли буде поїзд до Львова?** (Good afternoon. When will be the train to Lviv?)
— **Поїзд буде о п'ятій тридцять.** (The train will be at 5:30.)
— **О котрій він буде у Львові?** (At what time will it be in Lviv?)
— **Він буде об одинадцятій сорок п'ять.** (It will be at 11:45.)
---NEW---
— **Добрий день. Коли відправляється поїзд до Львова?** (Good afternoon. When does the train to Lviv depart?)
— **Поїзд відправляється о п'ятій тридцять.** (The train departs at 5:30.)
— **О котрій він прибуває до Львова?** (At what time does it arrive in Lviv?)
— **Він прибуває об одинадцятій сорок п'ять.** (It arrives at 11:45.)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/what-time-is-it.yaml
---OLD---
      explanation: "Питання «Котра година?» використовується для дізнання поточного часу."
---NEW---
      explanation: "Питання «Котра година?» використовується, щоб дізнатися поточний час."
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/what-time-is-it.yaml
---OLD---
  instruction: "З'єднайте час на цифферблаті з правильним українським варіантом."
---NEW---
  instruction: "З'єднайте час на циферблаті з правильним українським варіантом."
===FIX_END===

---

## Review Summary

| Category | Assessment |
|----------|-----------|
| Ukrainian Language Quality | Good. No Russianisms, no Russian characters. One IPA stress error and one IPA inconsistency fixed. |
| Pedagogical Correctness | Strong. Telegraphic style is excellent for A1. Vowel harmony rule was dangerously wrong — fixed. Plan compliance gap for пів на/чверть — addressed with preview note. |
| Factual Accuracy | Month etymologies correct. Day etymologies correct. Train punctuality statistic softened to qualitative claim. |
| LLM Artifacts | Minimal. One purple prose opener fixed. No "Це не просто X, а Y" patterns. Content reads naturally overall. |
| Plan Compliance | All sections present. Vocabulary hints covered in prose. Objectives map to self-check questions. Missing пів на/чверть now addressed. |
| Activity Integrity | All unjumble word arrays match answers. All fill-in answers produce grammatical sentences. Quiz distractors are plausible but clearly wrong. Excellent variety and volume. |

**Strengths:**
- Telegraphic style for A1 is a pedagogically excellent choice
- Cultural hook (Ukrzaliznytsia) is engaging and relevant
- Activity volume and variety are strong (12 quiz + 12 match-up + 12 fill-in + 12 unjumble + group-sort + 12 quiz + 12 fill-in + 12 unjumble + 12 match-up = ~96 items)
- Dialogues cover real-world scenarios naturally (after fix)

**Remaining minor items (not blocking):**
- Vocabulary file missing recommended items (січень, рано) and month names — recommend enrichment pass
- Vocabulary file missing IPA fields unlike some other vocab files — recommend enrichment pass

===VERDICT===
APPROVE
===END_VERDICT===