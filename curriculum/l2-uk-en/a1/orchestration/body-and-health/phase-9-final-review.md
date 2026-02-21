Good. Confirmed: zero instances of "бо" or "тому що" in the entire content file. No Russianisms, no Russian characters. Now let me compile the full review.

---

## Phase 9: Final QA Review — body-and-health (a1 #31)

### Issues Found

**Issue 1: IPA Error — Спина stress placement (CRITICAL)**
- **File:** body-and-health.md, line 32
- **Text:** `**Спина** [ˈspɪna]`
- **Problem:** Stress is on the first syllable [ˈspɪna], but Ukrainian спина́ has stress on the second syllable. Correct IPA: [spɪˈna]. This teaches the wrong pronunciation.

**Issue 2: Missing "бо" and "тому що" conjunctions (IMPORTANT — plan + meta compliance)**
- **File:** body-and-health.md
- **Problem:** The plan (section 4) explicitly requires "Constructing complex sentences with 'бо' and 'тому що' (State Standard §4.3.2)". The meta (section 6) says "Scenario 2: At the doctor's office (Formal, using «тому що/бо»)". Neither conjunction appears ANYWHERE in the content. The Причини section (lines 319-325) only uses "тому" (therefore/consequence), never "бо" or "тому що" (because/cause). These are fundamentally different constructions — "тому" marks consequence, while "бо"/"тому що" mark cause.

**Issue 3: Missing "мед" (honey) in phytotherapy note (MINOR — plan compliance)**
- **File:** body-and-health.md, line 252
- **Problem:** Plan section 2 specifically says "drinking tea with 'малина' (raspberry), 'калина' (viburnum), or 'мед' (honey)". The cultural note mentions малина and калина but omits мед.

**Issue 4: Fabricated activity distractor "вусі" (MODERATE)**
- **File:** activities/body-and-health.yaml, line 83
- **Text:** `options: ['вухо', 'вуха', 'вухом', 'вусі']`
- **Problem:** "Вусі" is not a standard Ukrainian word form. It's not a declension of "вухо" (ear) nor of "вуса" (mustache). This is a fabricated distractor that could confuse learners. Should be a real form like "вух" (Gen. pl. of вухо).

**Issue 5: Dialogues lack causal conjunctions per meta requirement (MODERATE — meta compliance)**
- **File:** body-and-health.md, Scenarios 1-2
- **Problem:** Meta section 6 point 2 says "Scenario 2: At the doctor's office (Formal, using «тому що/бо»)". Neither scenario uses these conjunctions. They should appear in the practice dialogues to reinforce the grammar.

### Items Verified — No Issues

- **IPA:** All other transcriptions correct (ɦ for Г, ʋ for В, tie bars on t͡s/t͡ʃ affricates)
- **Russianisms:** CLEAN — no кушати, получати, приймати участь, слідуючий
- **Russian characters:** CLEAN — no ы, э, ё, ъ
- **Gender agreement:** All correct (хворий/хвора/хворі, червоне горло, сильний кашель, висока температура)
- **Case agreement:** Correct (від кашлю Gen, від головного болю Gen, до лікаря Gen, в аптеку Acc, в лікарні Loc)
- **Unjumble activities:** All word arrays contain exactly the words needed for the answer ✓
- **Fill-in activities:** All answers produce grammatical sentences when inserted ✓
- **Required vocabulary:** All 8 required terms used in prose (голова, рука, нога, живіт, горло, болить, лікар, аптека) ✓
- **Objectives → self-check mapping:** All 4 objectives covered by the 6 self-check questions ✓
- **Activity YAML format:** Bare list at root, correct ✓
- **Word count:** ~2400 words, well above 2000 target ✓
- **No LLM artifacts:** No purple prose, no "Це не просто X, а Y", no fake statistics ✓
- **Factual accuracy:** Proverb correct, phytotherapy claims accurate, pharmacy/doctor cultural info valid ✓

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/body-and-health.md
---OLD---
**Спина** [ˈspɪna] (back) — feminine. Back pain is familiar to everyone.
---NEW---
**Спина** [spɪˈna] (back) — feminine. Back pain is familiar to everyone.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/body-and-health.md
---OLD---
> Ukrainians love natural remedies. Many people drink **малиновий чай** (raspberry tea) or **калиновий чай** (viburnum tea). **Малина** [maˈlɪna] reduces fever, and **калина** [kaˈlɪna] boosts immunity. If a Ukrainian friend offers you tea when you are sick, accept it. It is their way of caring for you.
---NEW---
> Ukrainians love natural remedies. Many people drink **малиновий чай** (raspberry tea) or **калиновий чай** (viburnum tea) with **мед** [mɛd] (honey). **Малина** [maˈlɪna] reduces fever, **калина** [kaˈlɪna] boosts immunity, and **мед** soothes a sore throat. If a Ukrainian friend offers you tea when you are sick, accept it. It is their way of caring for you.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/body-and-health.md
---OLD---
### Причини (Reasons)
Explaining why you are here.

*   **Я хворий, тому я вдома.** (I am sick, so I am at home.)
*   **У мене температура. Тому я тут.** (I have a fever. Therefore I am here.)
*   **Треба лікарняний.** (A sick leave note is needed.)
*   **Я почуваю себе дуже погано.** (I feel very bad.)
---NEW---
### Причини (Reasons)
Explaining why you are here. In Ukrainian, there are two common words for "because": **бо** (informal) and **тому що** (neutral/formal).

*   **Я хворий, тому я вдома.** (I am sick, so I am at home.)
*   **Я не прийшов на роботу, бо я хворий.** (I didn't come to work because I am sick.)
*   **Я тут, тому що у мене температура.** (I am here because I have a fever.)
*   **Треба лікарняний.** (A sick leave note is needed.)
*   **Я почуваю себе дуже погано.** (I feel very bad.)

_Usage Note:_ **Бо** is casual and short — use it with friends. **Тому що** is neutral — use it in any situation. Both mean "because".
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/body-and-health.md
---OLD---
**Ірина:** У мене болить голова й є температура. (I have a headache and a fever.)
**Олег:** Треба відпочивати. Пий малиновий чай. (You need to rest. Drink raspberry tea.)
---NEW---
**Ірина:** У мене болить голова й є температура. Я не пішла на роботу, бо мені погано. (I have a headache and a fever. I didn't go to work because I feel bad.)
**Олег:** Треба відпочивати. Пий малиновий чай. (You need to rest. Drink raspberry tea.)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/body-and-health.md
---OLD---
**Пацієнт:** Доброго дня, лікарю. У мене сильний кашель і болить горло. (Good day, doctor. I have a strong cough and a sore throat.)
**Лікар:** У вас є температура? (Do you have a fever?)
---NEW---
**Пацієнт:** Доброго дня, лікарю. Я тут, тому що у мене сильний кашель і болить горло. (Good day, doctor. I am here because I have a strong cough and a sore throat.)
**Лікар:** У вас є температура? (Do you have a fever?)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/body-and-health.yaml
---OLD---
      options: ['вухо', 'вуха', 'вухом', 'вусі']
---NEW---
      options: ['вухо', 'вуха', 'вухом', 'вух']
===FIX_END===

---

===VERDICT===
APPROVE
===END_VERDICT===