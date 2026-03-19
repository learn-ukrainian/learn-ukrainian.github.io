# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> The review already applied some fixes. You handle what's still failing.
> You have **Edit** and **Grep** tools — fix files directly.

---

## Ukrainian Alphabet Reference (use when editing letter/sound content)

When fixing content about the Ukrainian alphabet, vowels, or consonants, use these EXACT classifications:
- **10 vowel letters (голосні)**: А, О, У, Е, И, І, Я, Ю, Є, Ї (6 base + 4 iotated)
- **22 consonant letters (приголосні)**: Б, В, Г, Ґ, Д, Ж, З, Й, К, Л, М, Н, П, Р, С, Т, Ф, Х, Ц, Ч, Ш, Щ
- **1 modifier**: Ь (soft sign)
- Common confusions: В is a CONSONANT, І is a VOWEL, Й is a CONSONANT

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original, not less.
- **PRESERVE the author's intent.** If a paragraph explains something poorly, rewrite it to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your rewrite should read like the original author wrote it on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information that cannot be salvaged). This should be rare.

---

## Fix Plan (from Phase D.1 review)



**NOTE: 10 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥30 items
  - Actual: Activity has 15 items
  - Fix: Add 15 more items to 'match-up' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥30 items
  - Actual: Activity has 10 items
  - Fix: Add 20 more items to 'match-up' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 15 items
  - Fix: Add 5 more items to 'match-up' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 10 items
  - Fix: Add 10 more items to 'match-up' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 8 items
  - Fix: Add 7 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 6 items
  - Fix: Add 9 more items to 'fill-in' activity


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Activities YAML line 122, Line 72 / Section "Пори року та природа (Seasons & Nature)", Line 93, Line 93 / Section "Пори року та природа (Seasons & Nature)", Lines 11, 49, 93, 124 across multiple sections, Lines 124, 130, Section "Складні речення та прогноз (Complex Sentences & Forecast)" (lines 95-127), Vocabulary YAML

### Finding 1: Factually wrong stress explanation (CRITICAL)
**Location**: Line 72 / Section "Пори року та природа (Seasons & Nature)"
**Problem**: This is factually incorrect. восени́ has stress on the final syllable (і), NOT on the first о. The stress mark in the bold text correctly shows восени́ but the English explanation contradicts it. Teaching wrong stress placement will create persistent learner errors.
**Required Fix**: Change to "Similarly, with **восени́**, the stress falls on the very last syllable — the і."
**Severity**: HIGH

### Finding 2: Missing бо-sentences — plan violation (HIGH)
**Location**: Section "Складні речення та прогноз (Complex Sentences & Forecast)" (lines 95-127)
**Problem**: Plan §4 point 1 explicitly requires "побудова конструкцій зі сполучником «бо»" with example "Ми не гуляємо, бо холодно." Content completely omits бо, teaching consecutive sentences instead. The activities YAML (line 122) then tests бо in a fill-in item, testing untaught material.
**Required Fix**: Add бо-sentence examples: "Ми не гуля́ємо, бо хо́лодно." "Я не ї́ду в го́ри, бо йде си́льний дощ." "Вони́ йдуть у ліс, бо тепло́."
**Severity**: HIGH

### Finding 3: 10 stress mismatches (HIGH)
**Location**: Lines 11, 49, 93, 124 across multiple sections
**Severity**: HIGH

### Finding 4: Invalid word form — лістя (HIGH)
**Location**: Line 93 / Section "Пори року та природа (Seasons & Nature)"
**Problem**: "лістя" is NOT found in VESUM. The correct Ukrainian word is "листя" (leaves). "лістя" with і is a non-standard/dialectal form.
**Required Fix**: Change лі́стя → ли́стя
**Severity**: HIGH

### Finding 5: Invalid word form — порів (HIGH)
**Location**: Line 93 / Section "Пори року та природа (Seasons & Nature)"
**Problem**: "порів" is NOT found in VESUM. The genitive plural of "пора" is "пір" (VESUM confirmed: `noun:inanim:p:v_rod:xp2`).
**Required Fix**: Change по́рів → пір
**Severity**: HIGH

### Finding 6: Imperatives out of grammar scope (HIGH)
**Location**: Lines 124, 130
**Problem**: Imperatives (verb:perf:impr:p:2) are not taught until M47. Using them in A1.4 M43 is a scope violation.
**Required Fix**: Line 124: Replace "Візьмі́ть пара́сольку!" with "Не забу́дьте парасо́льку!" — wait, that's also imperative. Better: rephrase to "Парасо́лька — це ва́жливо!" or remove imperative entirely and use English: "Remember to bring an umbrella!"
**Severity**: HIGH

### Finding 7: Activities test untaught material (MEDIUM)
**Location**: Activities YAML line 122
**Problem**: (a) бо is not taught in the prose, (b) Візьміть is an imperative not in A1.4 scope
**Required Fix**: Replace with a sentence using taught structures, e.g.: "Можливий дощ. Потрібна ___." with answer "парасолька"
**Severity**: HIGH

### Finding 8: Missing vocabulary items (MEDIUM)
**Location**: Vocabulary YAML
**Problem**: парасолька and температура appear in activities (match-up items 31-35) but are absent from the vocabulary YAML. Learners need these in their word list.
**Required Fix**: Add both to vocabulary YAML
**Severity**: HIGH

### Finding 9: D.0 agreement error — DISMISSED
**Location**: Line 93
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Factually wrong stress explanation (CRITICAL)
- **Location**: Line 72 / Section "Пори року та природа (Seasons & Nature)"
- **Original**: 「Similarly, with **восени́**, the stress is firmly on the first «о».」
- **Problem**: This is factually incorrect. восени́ has stress on the final syllable (і), NOT on the first о. The stress mark in the bold text correctly shows восени́ but the English explanation contradicts it. Teaching wrong stress placement will create persistent learner errors.
- **Fix**: Change to "Similarly, with **восени́**, the stress falls on the very last syllable — the і."

### Issue 2: Missing бо-sentences — plan violation (HIGH)
- **Location**: Section "Складні речення та прогноз (Complex Sentences & Forecast)" (lines 95-127)
- **Original**: 「Сього́дні хо́лодно. Ми не гуля́ємо.」 — consecutive sentences used instead of бо
- **Problem**: Plan §4 point 1 explicitly requires "побудова конструкцій зі сполучником «бо»" with example "Ми не гуляємо, бо холодно." Content completely omits бо, teaching consecutive sentences instead. The activities YAML (line 122) then tests бо in a fill-in item, testing untaught material.
- **Fix**: Add бо-sentence examples: "Ми не гуля́ємо, бо хо́лодно." "Я не ї́ду в го́ри, бо йде си́льний дощ." "Вони́ йдуть у ліс, бо тепло́."

### Issue 3: 10 stress mismatches (HIGH)
- **Location**: Lines 11, 49, 93, 124 across multiple sections
- **Errors confirmed by D.0**:
  - Line 11: 「зби́рають」 → збира́ють
  - Line 49: 「га́рячий」 → гаря́чий
  - Line 93: 「чоти́рьох」 → чотирьо́х
  - Line 93: 「де́рева」 → дере́ва
  - Line 93: 「пта́хи」 → птахи́
  - Line 124: 「ви́хідні」 → вихідні́
  - Line 124: 「Темпера́тура」 → температу́ра
  - Line 124: 「Мо́жливий」 → можли́вий
  - Line 124: 「пара́сольку」 → парасо́льку

### Issue 4: Invalid word form — лістя (HIGH)
- **Location**: Line 93 / Section "Пори року та природа (Seasons & Nature)"
- **Original**: 「Восени́ лі́стя жо́вте і черво́не」
- **Problem**: "лістя" is NOT found in VESUM. The correct Ukrainian word is "листя" (leaves). "лістя" with і is a non-standard/dialectal form.
- **Fix**: Change лі́стя → ли́стя

### Issue 5: Invalid word form — порів (HIGH)
- **Location**: Line 93 / Section "Пори року та природа (Seasons & Nature)"
- **Original**: 「Украї́на — це краї́на чоти́рьох по́рів ро́ку.」
- **Problem**: "порів" is NOT found in VESUM. The genitive plural of "пора" is "пір" (VESUM confirmed: `noun:inanim:p:v_rod:xp2`).
- **Fix**: Change по́рів → пір

### Issue 6: Imperatives out of grammar scope (HIGH)
- **Location**: Lines 124, 130
- **Original**: 「Візьмі́ть пара́сольку!」 and 「Запам'ята́йте: в украї́нській мо́ві пого́да не «ро́бить»」
- **Problem**: Imperatives (verb:perf:impr:p:2) are not taught until M47. Using them in A1.4 M43 is a scope violation.
- **Fix**: Line 124: Replace "Візьмі́ть пара́сольку!" with "Не забу́дьте парасо́льку!" — wait, that's also imperative. Better: rephrase to "Парасо́лька — це ва́жливо!" or remove imperative entirely and use English: "Remember to bring an umbrella!"
  Line 130: Replace Ukrainian imperative with English instruction: "Remember: in Ukrainian, weather doesn't «ро́бить» — дощ **іде́**, со́нце **сві́тить**, а ві́тер **ду́є**!"

### Issue 7: Activities test untaught material (MEDIUM)
- **Location**: Activities YAML line 122
- **Original**: `"Візьміть ___, бо можливий дощ."` in fill-in activity
- **Problem**: (a) бо is not taught in the prose, (b) Візьміть is an imperative not in A1.4 scope
- **Fix**: Replace with a sentence using taught structures, e.g.: "Можливий дощ. Потрібна ___." with answer "парасолька"

### Issue 8: Missing vocabulary items (MEDIUM)
- **Location**: Vocabulary YAML
- **Problem**: парасолька and температура appear in activities (match-up items 31-35) but are absent from the vocabulary YAML. Learners need these in their word list.
- **Fix**: Add both to vocabulary YAML

### Issue 9: D.0 agreement error — DISMISSED
- **Location**: Line 93
- **D.0 flagged**: Agreement mismatch 'га́рна' (f) + 'ро́ку' (m)
- **Verdict**: FALSE POSITIVE. Full text: 「Ко́жна пора́ ро́ку га́рна!」 — "га́рна" is predicate agreeing with "пора́" (f), not with "ро́ку". Grammar is correct.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 11 | 「зби́рають」 | збира́ють | Stress |
| 49 | 「га́рячий」 | гаря́чий | Stress |
| 93 | 「чоти́рьох」 | чотирьо́х | Stress |
| 93 | 「по́рів」 | пір | Invalid form |
| 93 | 「де́рева」 | дере́ва | Stress |
| 93 | 「пта́хи」 | птахи́ | Stress |
| 93 | 「лі́стя」 | ли́стя | Invalid form |
| 124 | 「ви́хідні」 | вихідні́ | Stress |
| 124 | 「Темпера́тура」 | температу́ра | Stress |
| 124 | 「Мо́жливий」 | можли́вий | Stress |
| 124 | 「пара́сольку」 | парасо́льку | Stress |
| 72 | "stress on first о" | stress on final і | Factual error |

---

## Fix Plan to Reach 9/10 (REQUIRED)

### Linguistic Accuracy: 5/10 → 9/10
**What to fix:**
1. Fix all 10 stress marks (lines 11, 49, 93, 124) — mechanical find/replace
2. Line 93: Change лі́стя → ли́стя, по́рів → пір
3. Line 72: Fix factually wrong stress explanation for восени́
4. Lines 124, 130: Remove imperatives or replace with English instructions
**Expected score after fix:** 9/10

### Language: 6/10 → 9/10
**What to fix:** Same as Linguistic Accuracy — all errors are stress/form issues
**Expected score after fix:** 9/10

### Pedagogy: 6/10 → 9/10
**What to fix:**
1. Section "Складні речення та прогноз (Complex Sentences & Forecast)": Add бо-sentence teaching before the dialogue (3-4 examples with бо)
2. Fix the stress explanation on line 72
3. Activities YAML line 122: Replace imperative+бо item with taught structures
**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(8×1.5 + 9×1.1 + 9×1.2 + 8×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9
= (12.0 + 9.9 + 10.8 + 10.4 + 10.4 + 8.0 + 13.5) / 8.9
= 75.0 / 8.9 = 8.4/10
```

---

## Audit Failures (from automated re-audit)

```
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 8 violations
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 50/100)
→ Revision recommended (severity 50/100)
→ 9 violations (significant)
→ 3 grammar-level violations (fundamental)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/weather-and-nature-audit.log for details)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/weather-and-nature.md`

```markdown
## Summary

In this module, you will learn how to talk about the weather and nature in Ukrainian. You will master impersonal weather expressions (тепло, холодно, спекотно), describe rain, snow, sun, and wind using authentic Ukrainian verb collocations (йде дощ, світить сонце, дує вітер), name the four seasons and use their temporal adverbs (взимку, навесні, влітку, восени), discuss natural landscapes (ліс, озеро, річка, гори, море), and build compound sentences with бо to explain your plans based on the weather forecast.

## Вступ (Introduction)

Приві́т! Welcome to navigating the great outdoors and mastering one of the most essential, universal topics in the Ukrainian language: the weather (**пого́да**). 

Whether you are waiting for a morning bus in **Киї́в**, ordering a fresh coffee in **Львів**, or planning an ambitious hike up into the **го́ри** (mountains), knowing how to talk about the weather is your ultimate key to small talk. In Ukraine, the climate is not just a passive background detail; it is an active part of daily life and conversation. 

We experience four very distinct, beautiful seasons (**весна́**, **лі́то**, **о́сінь**, **зима́**). Each brings its own unique character, its own vocabulary, and its own challenges. Being able to discuss the changing conditions means you can easily connect with anyone, anywhere. It shows that you are paying attention to the world around you.

Before we dive into the grammar, let me share a special cultural hook with you. Have you ever heard of «Ба́бине лі́то»? In English, this is often called Indian Summer. It is a brief, unseasonably warm, and dry period that usually arrives on the border between September and October. Historically, this time was incredibly important for the agricultural cycle. It was the final window of opportunity for farmers to gather the last of the harvest, pick apples, and prepare their homes before the hard winter set in. In Ukrainian folklore, «Ба́бине лі́то» is associated with a magical calm, golden sunlight, and the delicate spiderwebs that float through the autumn air. It is a beautiful moment of pause in nature.

> 💡 **Ба́бине лі́то** — це тепло́ восени́. Со́нце світи́ть, приро́да га́рна. Це час, коли́ лю́ди гуля́ють у па́рку і збира́ють я́блука. Украї́нці ду́же лю́блять цей час ро́ку.

Mastering these concepts allows you to describe these seasonal changes, talk about the rain, the sun, and the wind, and build sentences that explain your plans. Time to discover the natural world!

## Погода та безособові форми (Weather & Impersonal Forms)

When you look out the window, how do you describe what you see? In English, we rely heavily on the dummy subject "it" to talk about the weather. We say, "It is cold," or "It is raining." However, Ukrainian grammar takes a much more direct and elegant approach. We use impersonal forms.

For the state of nature and temperature, we simply use adverbs. There is no need for a subject at all. The weather just *is*. Let's look at the core adverbs you need to know:

- **Тепло́.** (It is warm.)
- **Хо́лодно.** (It is cold.)
- **Спекотно.** (It is hot.)
- **Прохоло́дно.** (It is cool.)

A very common mistake for English speakers is to translate literally and say «Це хо́лодно». You must avoid this! If you say «Це хо́лодно», a Ukrainian will assume you are touching a physical object, like a cold glass of water or a metal pole. When you are talking about the environment, the atmosphere, or the weather outside, you must drop the «це» entirely and simply say: **Хо́лодно.**

`Сього́дні ду́же хо́лодно.` (It is very cold today.)
`На ву́лиці тепло́.` (It is warm outside.)
`За́втра бу́де спекотно.` (Tomorrow it will be hot.)
`Восени́ прохоло́дно.` (In autumn it is cool.)

Now, let us talk about precipitation. How do we say that it is raining or snowing? Ukrainian uses a very poetic and idiomatic construction based on verbs of motion. The rain and the snow literally "walk" or "go".

- **Йде дощ.** (It is raining. Literally: Rain goes.)
- **Йде сніг.** (It is snowing. Literally: Snow goes.)

You must use the verb **іти́** (to go). A common error is to say «дощ ро́бить» (rain makes or rain does). Please remember that the verb **роби́ти** implies conscious work or creation, like building a house or making dinner. The rain does not work a shift at a factory; it moves, it falls, it "goes". Let's practice this:

`Йде си́льний дощ.` (Heavy rain is falling.)
`Взи́мку йде сніг.` (It snows in winter.)
`Світи́ть яскра́ве со́нце.` (The bright sun is shining.)
`Сього́дні си́льний ві́тер.` (There is a strong wind today.)

Also, if the sun is out, we simply say **Світи́ть со́нце**. This makes your language sound incredibly natural and observant. 

📖 **Reading Practice** — read this short passage aloud and try to understand it:

> Сього́дні ра́нок. На ву́лиці хо́лодно. Йде дощ. Ві́тер си́льний. Я не йду гуля́ти. Я сиджу́ вдо́ма і п'ю гаря́чий чай. Мені́ тепло́ і до́бре. А на ву́лиці — хма́ри, дощ і ві́тер. Мо́же, за́втра бу́де со́нце?

*To hear these phrases and adverbs in action, check out this video lesson:*
🎥 [ULP 1-16 | Talking about weather in Ukrainian](https://www.youtube.com/watch?v=ycCrSrHCezQ)

## Пори року та природа (Seasons & Nature)

Now that we know how to describe the weather, we need to know *when* and *where* it is happening. Ukraine is famous for its rich natural landscapes and its distinct four seasons. 

The foundation of discussing nature is knowing the nouns for the seasons themselves:

- **зима́** (winter)
- **весна́** (spring)
- **лі́то** (summer)
- **о́сінь** (autumn)

When we want to say that something happens *in* or *during* a season, we do not simply use a preposition with these nouns. Instead, Ukrainian grammar provides specific temporal adverbs for this exact purpose. You must learn these by heart, paying very close attention to the phonetics and the stress marks.

- **взи́мку** (in winter)
- **навесні́** (in spring)
- **влі́тку** (in summer)
- **восени́** (in autumn)

Please be extremely careful: avoid literal translations like «у весні́» or «в весні́». This sounds unnatural to a native speaker. Always use the proper adverb **навесні́**, and notice how the stress falls heavily on the very last syllable. Similarly, with **восени́**, the stress falls on the very last syllable — the «і».

Now, here are the key natural features around us. The Ukrainian State Standard highlights several key geographical features that are essential for planning your outdoor adventures:

- **ліс** (forest)
- **о́зеро** (lake)
- **рі́чка** (river)
- **го́ри** (mountains)
- **мо́ре** (sea)

Let's combine our new seasons, natural locations, and weather adverbs to describe typical conditions across the country:

`Влі́тку на мо́рі ду́же спекотно.` (In summer, it is very hot at the sea.)
`Взи́мку в го́рах бага́то сні́гу.` (In winter, there is a lot of snow in the mountains.)
`Навесні́ бі́ля річки́ та на о́зері тепло́.` (In spring, it is warm near the river and at the lake.)
`Восени́ у лі́сі прохоло́дно, там га́рна приро́да.` (In autumn, it is cool in the forest, the nature is beautiful there.)

Notice the prepositions we use: **на мо́рі**, **в го́рах**, and **у лі́сі**. By practicing these combinations, your Ukrainian will become rich, descriptive, and perfectly suited for any conversation about nature.

📖 **Reading Practice** — read this short passage and identify the seasons:

> Украї́на — це краї́на чотирьо́х пір ро́ку. Навесні́ приро́да прокида́ється: дере́ва зеле́ні, птахи́ співа́ють, на ву́лиці тепло́. Влі́тку всі ї́дуть на мо́ре або́ на о́зеро. Там спекотно і со́нячно. Восени́ ли́стя жо́вте і черво́не, у лі́сі прохоло́дно. А взи́мку йде сніг, у го́рах бі́ло і хо́лодно. Ко́жна пора́ ро́ку га́рна!

## Складні речення та прогноз (Complex Sentences & Forecast)

When you are trying to organize a weekend picnic, the weather directly dictates your schedule. To express this in Ukrainian, we need to build clear, consecutive sentences. Connecting simple ideas allows you to logically express your plans.

We will use the conjunction **бо** (because) to explain our plans depending on the weather conditions. The structure is straightforward: state your action, then explain why with бо + weather.

`Ми не гуля́ємо, бо хо́лодно.` (We are not walking, because it is cold.)
`Я не ї́ду в го́ри, бо йде си́льний дощ.` (I am not going to the mountains, because heavy rain is falling.)
`Вони́ йдуть у ліс, бо тепло́.` (They are going to the forest, because it is warm.)

Notice how **бо** connects a simple reason to an action. Keep your бо-sentences short and clear — this is a very powerful tool for everyday conversation.

To know what plans to make, you must first check the weather forecast, or **прогно́з**. Let's look at a realistic dialogue between two friends discussing their plans for the weekend. Notice how they ask questions and use common collocations like «га́рний прогно́з» (good forecast) or «пога́ний прогно́з» (bad forecast).

> — Приві́т! Яка сього́дні пого́да?
> — (Hi! What is the weather like today?)
> — Сього́дні пога́на пого́да. Вели́ка хма́ра і си́льний ві́тер.
> — (Today is bad weather. A big cloud and a strong wind.)
> — А що там за прогно́зом на за́втра? Чи бу́де дощ?
> — (And what is in the forecast for tomorrow? Will there be rain?)
> — Ні, за́втра бу́де со́нце і ду́же тепло́.
> — (No, tomorrow there will be sun and it will be very warm.)
> — Чудо́во! Бу́де га́рний прогно́з. Тоді́ ми ї́демо на о́зеро!
> — (Wonderful! There will be a good forecast. Then we are going to the lake!)

In this dialogue, the phrase **що там за прогно́зом?** (what is in the forecast?) is an incredibly authentic way to ask about future conditions. We also see the word **хма́ра** (cloud) and **ві́тер** (wind) being used to describe the current state. Master these questions, and you will never be caught in the rain without an umbrella!

📖 **Reading Practice** — read this weather forecast aloud:

> Прогно́з пого́ди на вихідні́. У субо́ту бу́де тепло́ і со́нячно. Температу́ра — два́дцять гра́дусів. Дощу́ не бу́де. Га́рний день для прогу́лянки! А в неді́лю бу́де хма́рно і прохоло́дно. Можли́вий дощ. Don't forget your парасо́льку!

*For more listening practice on forecasts, try this short lesson:*
🎥 [FMU 1-28 | How to talk about the weather in Ukrainian](https://www.youtube.com/watch?v=6MRrGpcGEp4)

> [!tip]
> Remember: in Ukrainian, weather doesn't «ро́бить» — дощ **іде́**, со́нце **сві́тить**, а ві́тер **ду́є**!


```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/weather-and-nature.yaml`

```yaml
- type: match-up
  title: "Weather and Nature Words"
  instruction: "Match each Ukrainian word to its English meaning."
  pairs:
    - left: "погода"
      right: "weather"
    - left: "дощ"
      right: "rain"
    - left: "сніг"
      right: "snow"
    - left: "сонце"
      right: "sun"
    - left: "хмара"
      right: "cloud"
    - left: "вітер"
      right: "wind"
    - left: "ліс"
      right: "forest"
    - left: "озеро"
      right: "lake"
    - left: "річка"
      right: "river"
    - left: "гори"
      right: "mountains"
    - left: "море"
      right: "sea"
    - left: "природа"
      right: "nature"
    - left: "прогноз"
      right: "forecast"
    - left: "парасолька"
      right: "umbrella"
    - left: "температура"
      right: "temperature"
    - left: "весна"
      right: "spring"
    - left: "літо"
      right: "summer"
    - left: "осінь"
      right: "autumn"
    - left: "зима"
      right: "winter"
    - left: "тепло"
      right: "warm"
    - left: "холодно"
      right: "cold"
    - left: "спекотно"
      right: "hot"
    - left: "прохолодно"
      right: "cool"
    - left: "взимку"
      right: "in winter"
    - left: "влітку"
      right: "in summer"
    - left: "навесні"
      right: "in spring"
    - left: "восени"
      right: "in autumn"
    - left: "хмарно"
      right: "cloudy"
    - left: "сонячно"
      right: "sunny"

- type: match-up
  title: "Match Weather to Seasons"
  instruction: "Match each weather description to the season it typically belongs to."
  pairs:
    - left: "Йде сніг, дуже холодно"
      right: "зима"
    - left: "Спекотно, світить сонце"
      right: "літо"
    - left: "Прохолодно, листя жовте"
      right: "осінь"
    - left: "Тепло, природа прокидається"
      right: "весна"
    - left: "взимку"
      right: "in winter"
    - left: "влітку"
      right: "in summer"
    - left: "восени"
      right: "in autumn"
    - left: "навесні"
      right: "in spring"
    - left: "хмарно"
      right: "cloudy"
    - left: "сонячно"
      right: "sunny"
    - left: "Дує сильний вітер"
      right: "autumn or winter"
    - left: "Багато снігу в горах"
      right: "зима"
    - left: "На морі спекотно"
      right: "літо"
    - left: "Листя жовте і червоне"
      right: "осінь"
    - left: "дощ"
      right: "rain"
    - left: "сніг"
      right: "snow"
    - left: "сонце"
      right: "sun"
    - left: "вітер"
      right: "wind"
    - left: "ліс"
      right: "forest"
    - left: "озеро"
      right: "lake"
    - left: "річка"
      right: "river"
    - left: "море"
      right: "sea"
    - left: "гори"
      right: "mountains"
    - left: "погода"
      right: "weather"
    - left: "прогноз"
      right: "forecast"
    - left: "природа"
      right: "nature"
    - left: "Природа прокидається, тепло"
      right: "весна"
    - left: "Йде сніг, в горах біло"
      right: "зима"
    - left: "Всі їдуть на море"
      right: "літо"
    - left: "У лісі прохолодно"
      right: "осінь"

- type: fill-in
  title: "Complete Weather Descriptions"
  instruction: "Choose the correct word to complete each sentence about the weather."
  items:
    - sentence: "___ дощ."
      answer: "Йде"
      options: ["Йде", "Робить", "Дує", "Світить"]
      explanation: "In Ukrainian, rain 'goes' — йде дощ. Never use робить with rain."
    - sentence: "___ сонце."
      answer: "Світить"
      options: ["Світить", "Йде", "Дує", "Робить"]
      explanation: "The sun shines — світить сонце."
    - sentence: "Сьогодні сильний ___."
      answer: "вітер"
      options: ["вітер", "сонце", "тепло", "озеро"]
      explanation: "Сильний вітер means strong wind."
    - sentence: "Взимку йде ___."
      answer: "сніг"
      options: ["сніг", "сонце", "вітер", "літо"]
      explanation: "In winter, snow falls — взимку йде сніг."
    - sentence: "На вулиці дуже ___."
      answer: "холодно"
      options: ["холодно", "холодний", "холод", "зима"]
      explanation: "For weather, use the adverb холодно without a subject. Not це холодно!"
    - sentence: "Влітку на морі дуже ___."
      answer: "спекотно"
      options: ["спекотно", "холодно", "хмарно", "взимку"]
      explanation: "In summer it is hot at the sea — спекотно."
    - sentence: "Завтра буде ___ погода."
      answer: "гарна"
      options: ["гарна", "гарний", "гарне", "гарно"]
      explanation: "Погода is feminine, so we use the feminine adjective form гарна."
    - sentence: "Взимку в горах багато ___."
      answer: "снігу"
      options: ["снігу", "сніг", "дощу", "сонця"]
      explanation: "Багато requires genitive case — снігу (genitive of сніг)."
    - sentence: "Восени ___ жовте і червоне."
      answer: "листя"
      options: ["листя", "дерева", "природа", "ліс"]
      explanation: "Листя means leaves — восени листя жовте і червоне."
    - sentence: "Ми не гуляємо, ___ холодно."
      answer: "бо"
      options: ["бо", "і", "а", "що"]
      explanation: "Бо means 'because' — we use it to explain the reason."
    - sentence: "___ сильний вітер."
      answer: "Дує"
      options: ["Дує", "Йде", "Світить", "Робить"]
      explanation: "Wind 'blows' in Ukrainian — дує вітер."
    - sentence: "Навесні ___ прокидається."
      answer: "природа"
      options: ["природа", "погода", "хмара", "зима"]
      explanation: "In spring, nature awakens — природа прокидається."
    - sentence: "Восени у ___ прохолодно."
      answer: "лісі"
      options: ["лісі", "ліс", "лісу", "ліса"]
      explanation: "У лісі uses the locative case of ліс."
    - sentence: "Сьогодні ___ погода."
      answer: "погана"
      options: ["погана", "поганий", "погане", "погано"]
      explanation: "Погода is feminine, so we use the feminine adjective form погана."
    - sentence: "Я не їду в гори, ___ йде сильний дощ."
      answer: "бо"
      options: ["бо", "і", "але", "чи"]
      explanation: "Бо connects a reason — I'm not going because of heavy rain."

- type: fill-in
  title: "Weather Conversations"
  instruction: "Choose the correct word to complete each line of the conversation."
  items:
    - sentence: "Яка сьогодні ___?"
      answer: "погода"
      options: ["погода", "природа", "прогноз", "пора"]
      explanation: "Яка сьогодні погода? is how you ask about today's weather."
    - sentence: "Сьогодні погана погода. Велика ___ і сильний вітер."
      answer: "хмара"
      options: ["хмара", "гора", "річка", "весна"]
      explanation: "Хмара means cloud — it describes bad weather along with wind."
    - sentence: "Що там за ___ на завтра?"
      answer: "прогнозом"
      options: ["прогнозом", "прогноз", "погодою", "погода"]
      explanation: "За прогнозом — according to the forecast — uses the instrumental case."
    - sentence: "Завтра буде сонце і дуже ___."
      answer: "тепло"
      options: ["тепло", "теплий", "тепла", "теплі"]
      explanation: "For weather, use the adverb тепло, not an adjective form."
    - sentence: "Тоді ми їдемо на ___!"
      answer: "озеро"
      options: ["озеро", "озері", "озера", "озером"]
      explanation: "На озеро uses accusative (direction) — we are going TO the lake."
    - sentence: "Можливий дощ. Потрібна ___."
      answer: "парасолька"
      options: ["парасолька", "парасольку", "парасольки", "парасольці"]
      explanation: "Потрібна requires nominative — парасолька. An umbrella is needed!"
    - sentence: "Чудово! Тоді ми їдемо на ___!"
      answer: "море"
      options: ["море", "морі", "моря", "морем"]
      explanation: "На море uses accusative (direction) — we are going TO the sea."
    - sentence: "Буде гарний ___ на вихідні."
      answer: "прогноз"
      options: ["прогноз", "прогнозом", "прогнозу", "погода"]
      explanation: "Прогноз is masculine — гарний прогноз (good forecast)."
    - sentence: "Влітку всі їдуть на ___ або на озеро."
      answer: "море"
      options: ["море", "морі", "моря", "морем"]
      explanation: "На море — accusative for direction. Everyone goes TO the sea."
    - sentence: "Біля ___ навесні тепло."
      answer: "річки"
      options: ["річки", "річка", "річку", "річці"]
      explanation: "Біля requires genitive case — річки (genitive of річка)."
    - sentence: "Ми не їдемо на озеро, ___ йде дощ."
      answer: "бо"
      options: ["бо", "і", "але", "чи"]
      explanation: "Бо explains the reason — we aren't going because it's raining."
    - sentence: "Навесні біля річки та на ___ тепло."
      answer: "озері"
      options: ["озері", "озеро", "озера", "озером"]
      explanation: "На озері uses locative case — at the lake."
    - sentence: "___ — двадцять градусів."
      answer: "Температура"
      options: ["Температура", "Прогноз", "Погода", "Природа"]
      explanation: "Температура — двадцять градусів describes the temperature reading."
    - sentence: "Вони йдуть у ліс, ___ тепло."
      answer: "бо"
      options: ["бо", "і", "але", "чи"]
      explanation: "Бо explains the reason — they go to the forest because it is warm."

- type: quiz
  title: "Check Your Weather Knowledge"
  instruction: "Choose the correct answer for each question."
  items:
    - question: "How do you say 'It is cold' when talking about the weather in Ukrainian?"
      options:
        - text: "Холодно"
          correct: true
        - text: "Це холодно"
          correct: false
        - text: "Холодний"
          correct: false
        - text: "Він холодно"
          correct: false
      explanation: "For weather, use the adverb alone — Холодно. Saying Це холодно implies you are touching a cold object."
    - question: "How do Ukrainians say 'It is raining'?"
      options:
        - text: "Йде дощ"
          correct: true
        - text: "Дощ робить"
          correct: false
        - text: "Це дощ"
          correct: false
        - text: "Дощ працює"
          correct: false
      explanation: "Rain 'goes' in Ukrainian — йде дощ. The verb іти (to go) is used, never робити."
    - question: "What does 'навесні' mean?"
      options:
        - text: "in spring"
          correct: true
        - text: "in summer"
          correct: false
        - text: "in winter"
          correct: false
        - text: "in autumn"
          correct: false
      explanation: "Навесні is the temporal adverb meaning 'in spring', from весна."
    - question: "Which word means 'forecast'?"
      options:
        - text: "прогноз"
          correct: true
        - text: "погода"
          correct: false
        - text: "природа"
          correct: false
        - text: "прогулянка"
          correct: false
      explanation: "Прогноз means forecast. Прогноз погоди = weather forecast."
    - question: "Which verb is used with 'сонце' (sun) in Ukrainian?"
      options:
        - text: "світить"
          correct: true
        - text: "йде"
          correct: false
        - text: "дує"
          correct: false
        - text: "робить"
          correct: false
      explanation: "Світить сонце — the sun shines. Йде is for rain/snow, дує is for wind."
    - question: "What is the correct way to say 'in winter' in Ukrainian?"
      options:
        - text: "взимку"
          correct: true
        - text: "у зимі"
          correct: false
        - text: "в зима"
          correct: false
        - text: "на зиму"
          correct: false
      explanation: "Взимку is the proper temporal adverb. Avoid literal translations like у зимі."

- type: true-false
  title: "True or False? Weather in Ukrainian"
  instruction: "Decide whether each statement is true or false."
  items:
    - statement: "To say 'It is cold outside' in Ukrainian, you say 'Це холодно'."
      correct: false
      explanation: "Wrong! You simply say Холодно or На вулиці холодно. Це холодно means a specific object is cold."
    - statement: "The Ukrainian word for rain is дощ."
      correct: true
      explanation: "Correct! Дощ means rain. Йде дощ = It is raining."
    - statement: "Влітку means 'in winter'."
      correct: false
      explanation: "Влітку means 'in summer' (from літо). 'In winter' is взимку."
    - statement: "In Ukrainian, you say 'Йде сніг' to mean 'It is snowing'."
      correct: true
      explanation: "Correct! Snow 'goes' in Ukrainian — йде сніг."
    - statement: "The word хмара means 'mountain'."
      correct: false
      explanation: "Хмара means cloud. Mountain is гора (plural: гори)."
    - statement: "Навесні means 'in spring'."
      correct: true
      explanation: "Correct! Навесні is the temporal adverb for spring, from весна."
    - statement: "Світить сонце means 'The sun is shining'."
      correct: true
      explanation: "Correct! Світити means to shine, and сонце means sun."
    - statement: "To ask about the weather, you say 'Яка сьогодні погода?'"
      correct: true
      explanation: "Correct! This is the standard way to ask 'What is the weather like today?'"

- type: group-sort
  title: "Sort by Category"
  instruction: "Sort these words into the correct category."
  groups:
    - name: "Seasons (пори року)"
      items:
        - "зима"
        - "весна"
        - "літо"
        - "осінь"
    - name: "Weather words (погода)"
      items:
        - "дощ"
        - "сніг"
        - "вітер"
        - "хмара"
    - name: "Natural places (природа)"
      items:
        - "ліс"
        - "озеро"
        - "море"
        - "гори"

- type: unjumble
  title: "Put the Words in Order"
  instruction: "Arrange the words to form a correct Ukrainian sentence."
  items:
    - words: ["дощ", "Йде", "сильний"]
      answer: "Йде сильний дощ"
    - words: ["холодно", "вулиці", "На"]
      answer: "На вулиці холодно"
    - words: ["сонце", "Світить", "яскраве"]
      answer: "Світить яскраве сонце"
    - words: ["тепло", "Сьогодні", "дуже"]
      answer: "Сьогодні дуже тепло"
    - words: ["в", "Взимку", "горах", "холодно"]
      answer: "Взимку в горах холодно"
    - words: ["на", "Влітку", "спекотно", "морі"]
      answer: "Влітку на морі спекотно"
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/weather-and-nature.yaml`

```yaml
items:
  - lemma: "погода"
    translation: "weather"
    pos: "noun"
    gender: "f"
    usage: "Яка сьогодні погода?"
    notes: "One of the most common conversation starters in Ukrainian"
  - lemma: "дощ"
    translation: "rain"
    pos: "noun"
    gender: "m"
    usage: "Йде дощ"
    notes: "Rain 'goes' (йде) in Ukrainian — never use робити"
  - lemma: "сніг"
    translation: "snow"
    pos: "noun"
    gender: "m"
    usage: "Йде сніг"
    notes: "Same construction as rain — йде сніг"
  - lemma: "сонце"
    translation: "sun"
    pos: "noun"
    gender: "n"
    usage: "Світить сонце"
    notes: "Used with світити (to shine)"
  - lemma: "вітер"
    translation: "wind"
    pos: "noun"
    gender: "m"
    usage: "Сьогодні сильний вітер"
  - lemma: "хмара"
    translation: "cloud"
    pos: "noun"
    gender: "f"
    usage: "Велика хмара"
  - lemma: "тепло"
    translation: "warm (it is warm)"
    pos: "adv"
    usage: "На вулиці тепло"
    notes: "Used without a subject for weather. Not Це тепло!"
  - lemma: "холодно"
    translation: "cold (it is cold)"
    pos: "adv"
    usage: "Сьогодні дуже холодно"
    notes: "Common learner error: Це холодно (wrong — implies touching a cold object)"
  - lemma: "спекотно"
    translation: "hot (it is hot)"
    pos: "adv"
    usage: "Влітку спекотно"
  - lemma: "прохолодно"
    translation: "cool (it is cool)"
    pos: "adv"
    usage: "Восени прохолодно"
  - lemma: "весна"
    translation: "spring"
    pos: "noun"
    gender: "f"
    usage: "Навесні тепло"
  - lemma: "літо"
    translation: "summer"
    pos: "noun"
    gender: "n"
    usage: "Влітку спекотно"
  - lemma: "осінь"
    translation: "autumn"
    pos: "noun"
    gender: "f"
    usage: "Восени прохолодно"
  - lemma: "зима"
    translation: "winter"
    pos: "noun"
    gender: "f"
    usage: "Взимку холодно"
  - lemma: "ліс"
    translation: "forest"
    pos: "noun"
    gender: "m"
    usage: "У лісі гарно"
  - lemma: "озеро"
    translation: "lake"
    pos: "noun"
    gender: "n"
    usage: "Ми їдемо на озеро"
  - lemma: "річка"
    translation: "river"
    pos: "noun"
    gender: "f"
    usage: "Біля річки тепло"
  - lemma: "море"
    translation: "sea"
    pos: "noun"
    gender: "n"
    usage: "На морі спекотно"
  - lemma: "прогноз"
    translation: "forecast"
    pos: "noun"
    gender: "m"
    usage: "Прогноз погоди на завтра"
  - lemma: "природа"
    translation: "nature"
    pos: "noun"
    gender: "f"
    usage: "Восени у лісі гарна природа"
  - lemma: "парасолька"
    translation: "umbrella"
    pos: "noun"
    gender: "f"
    usage: "Потрібна парасолька"
    notes: "Essential for rainy weather conversations"
  - lemma: "температура"
    translation: "temperature"
    pos: "noun"
    gender: "f"
    usage: "Температура — двадцять градусів"
    notes: "Used in weather forecasts"
```

---

## Instructions

1. For each issue in the Fix Plan or audit failures, use **Grep** to verify the exact text exists in the file
2. Use the **Edit** tool to fix each issue directly in the file
3. Only fix issues documented above — no silent extra changes
4. Prioritize: audit gate failures first, then review issues

---

## How to Fix

Use the Edit tool for each fix. The workflow for each issue:

1. **Grep** the file to confirm the text exists and is unique
2. **Edit** the file: provide `old_string` (exact text from file) and `new_string` (corrected text)
3. Move to next issue

File paths:
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/weather-and-nature.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/weather-and-nature.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/weather-and-nature.yaml`

## Fix Rules

- Only fix issues documented in the Fix Plan or audit failures above
- You MAY add new activities or modify existing ones if the Fix Plan explicitly requests it
- Do NOT add new prose sections or vocabulary items unless the Fix Plan explicitly requests it
- Maximum **20 edits** total (prioritize the most impactful fixes)
- If nothing needs fixing, state that clearly

---

## Friction Report (MANDATORY)

After all fixes, output:

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: {what you were doing when friction occurred, or "Full Phase D.2"}
**Friction Type**: NONE | EDIT_FAILED | TEXT_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done in Phase D.1
- Do NOT output ===REVIEW_START=== blocks
- Do NOT output FIND/REPLACE blocks — use the Edit tool instead
- You MAY add/modify activities if the Fix Plan requests it
- Do NOT make cosmetic changes beyond what the review flagged
