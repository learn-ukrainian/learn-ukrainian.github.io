Now I have everything I need. Let me conduct the full adversarial review.

---

## Phase 9 Final QA Review: weather-and-nature (a1-29)

### Issues Found

#### CRITICAL

**Issue 1: Typo — non-existent word «Прогулянця»**
- **Location:** content L216 — `### Читання: Прогулянця під дощем`
- **Problem:** «Прогулянця» does not exist in Ukrainian. Correct word: «Прогулянка» (прогулянка = walk/stroll).

**Issue 2: Calque — «Україна має чотири пори року»**
- **Location:** content L32-33
- **Problem:** Direct English calque "Ukraine has four seasons." Natural Ukrainian uses existential construction: «В Україні чотири пори року.»

**Issue 3: Pedagogical gap — «бо» tested but never taught**
- **Location:** Activity unjumble L193 requires building «Я беру парасолю бо йде дощ» using the conjunction «бо» (because). Content Презентація 5 "Причина та Наслідок" (L399-405) only shows separate sentences, never introducing «бо». The plan (source of truth) explicitly requires: "побудова конструкцій зі сполучником «бо»" and the meta says: "Syntax: 'Ми не гуляємо, бо холодно' (Causal link §4.3.2)."

**Issue 4: Activity — unjumble answer missing comma before «бо»**
- **Location:** activities L194 — `answer: 'Я беру парасолю бо йде дощ'`
- **Problem:** Ukrainian requires a comma before the conjunction «бо»: «Я беру парасолю, бо йде дощ.»

#### IMPORTANT — IPA Accuracy

**Issue 5: Wrong stress on «Тепло»**
- **Location:** content L82, L104 — ``
- **Problem:** As an impersonal adverb ("it is warm"), тепло has stress on the last syllable: теплó. The transcription gives the stress of the noun (тéпло = warmth). Since this module teaches the adverb, the stress is wrong.

**Issue 6: Systematic В transcribed as [v] instead of [ʋ]**
- **Locations:** L190 (Вітер), L193 (Світить), L199 (Вітряно), L262 (чудова), L264 (жахлива), L272 (градусів), L321 (Взимку), L327 (Навесні), L333 (Влітку), L339 (Восени)
- **Problem:** Ukrainian В is a labiodental approximant [ʋ], not a labiodental fricative [v]. The prompt explicitly requires "ʋ not w for В."

**Issue 7: Missing tie bars on affricates**
- **Locations:** L162 (Дощ [dɔʃt͡ʃ]), L188 (Сонце), L197 (Сонячно), L262 (чудова)
- **Problem:** Affricates require tie bars: ц = [t͡s], ч = [t͡ʃ], щ = [ʃt͡ʃ].

**Issue 8: Inconsistent г transcription — [h] vs [ɦ]**
- **Locations:** L272 градусів, L395 Градус — use [h], but L394 Прогноз correctly uses [ɦ].
- **Problem:** Ukrainian г is voiced glottal fricative [ɦ], not voiceless [h].

#### MINOR

**Issue 9: «Всі» instead of «Усі»**
- **Location:** content L324 — `Всі дерева білі.`
- **Problem:** At sentence start (after pause), standard Ukrainian orthography prefers «усі». «Всі» is a colloquial/dialectal variant inappropriate for a teaching module.

**Issue 10: Inaccurate literal translation of «Бабине літо»**
- **Location:** content L62 — `(literally "women's summer")`
- **Problem:** «Бабине» derives from «баба» = grandmother/old woman, not "women." Correct literal translation: "grandmother's summer" or "old woman's summer." "Women's summer" would be «жіноче літо».

**Issue 11: Vocabulary file uses `items:` wrapper instead of bare list**
- **Location:** vocabulary file L1
- **Problem:** Other vocab files in the project (e.g., the-living-verb-i.yaml, around-the-city.yaml) use bare list format at root. This file wraps entries in `items:` — inconsistent with project convention.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
### Читання: Прогулянця під дощем (Reading: Walk in the Rain)
---NEW---
### Читання: Прогулянка під дощем (Reading: Walk in the Rain)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
Україна має чотири пори року.
Ukraine has four seasons.
---NEW---
В Україні чотири пори року.
In Ukraine, there are four seasons.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
### Причина та Наслідок (Cause and Effect)

We use short sentences to explain our actions.

*   **На вулиці холодно. Ми не гуляємо.** — It is cold outside. We are not walking.
*   **Йде дощ. Я беру парасолю.** — It is raining. I am taking an umbrella. (**Парасоля** = umbrella).
*   **Світить сонце. Ми йдемо в парк.** — The sun shines. We are going to the park.
---NEW---
### Причина та Наслідок (Cause and Effect)

We can connect a result with a reason using **бо** [bɔ] — *because*. Always put a comma before **бо**.

**Structure:**
> **[Result], бо [Reason].**

*   **Ми не гуляємо, бо холодно.** — We are not walking, because it is cold.
*   **Я беру парасолю, бо йде дощ.** — I am taking an umbrella, because it is raining. (**Парасоля** = umbrella).
*   **Ми йдемо в парк, бо світить сонце.** — We are going to the park, because the sun is shining.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
*   *Description:* Взимку ми святкуємо Різдво. Всі дерева білі. Ми носимо шапки і шарфи.
---NEW---
*   *Description:* Взимку ми святкуємо Різдво. Усі дерева білі. Ми носимо шапки і шарфи.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
(literally "women's summer")
---NEW---
(literally "grandmother's summer")
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
*   **Тепло** — Warm
*   **Спекотно** — Hot
---NEW---
*   **Тепло** — Warm
*   **Спекотно** — Hot
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
2.  **Тепло** — Warm (20°C - 25°C)
---NEW---
2.  **Тепло** — Warm (20°C - 25°C)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
*   **Дощ** [dɔʃt͡ʃ] — Rain
---NEW---
*   **Дощ** [dɔʃt͡ʃ] — Rain
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
*   **Сонце** — Sun
---NEW---
*   **Сонце** — Sun
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
*   **Вітер** — Wind
---NEW---
*   **Вітер** — Wind
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
*   **Світить сонце.** — The sun is shining.
---NEW---
*   **Світить сонце.** — The sun is shining.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
*   **Сонячно** — Sunny
---NEW---
*   **Сонячно** — Sunny
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
*   **Вітряно** — Windy
---NEW---
*   **Вітряно** — Windy
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
*   **Сьогодні чудова погода.** — Today is wonderful weather.
---NEW---
*   **Сьогодні чудова погода.** — Today is wonderful weather.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
*   **Сьогодні жахлива погода.** — Today is terrible weather.
---NEW---
*   **Сьогодні жахлива погода.** — Today is terrible weather.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
*   **Скільки градусів?** — How many degrees?
---NEW---
*   **Скільки градусів?** — How many degrees?
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
*   **Градус** — Degree
---NEW---
*   **Градус** — Degree
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
*   **Коли?** (When?): **Взимку** — In winter
---NEW---
*   **Коли?** (When?): **Взимку** — In winter
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
*   **Коли?** (When?): **Навесні** — In spring
---NEW---
*   **Коли?** (When?): **Навесні** — In spring
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
*   **Коли?** (When?): **Влітку** — In summer
---NEW---
*   **Коли?** (When?): **Влітку** — In summer
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/weather-and-nature.md
---OLD---
*   **Коли?** (When?): **Восени** — In autumn
---NEW---
*   **Коли?** (When?): **Восени** — In autumn
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/weather-and-nature.yaml
---OLD---
    - words: ['Я', 'беру', 'парасолю', 'бо', 'йде', 'дощ']
      answer: 'Я беру парасолю бо йде дощ'
---NEW---
    - words: ['Я', 'беру', 'парасолю,', 'бо', 'йде', 'дощ']
      answer: 'Я беру парасолю, бо йде дощ'
===FIX_END===

---

### Observations (not fixed — flagged for awareness)

1. **Vocabulary file format inconsistency:** `weather-and-nature.yaml` uses `items:` wrapper while peer files (around-the-city, the-living-verb-i) use bare list format. Requires full file restructure — not fixable via string replacement. Should be addressed in a separate pass.

2. **Plan compliance — nature vocabulary thin:** The plan's source of truth calls for teaching nature objects per State Standard §3.11 (ліс, озеро, річка, гори, море) with weather-per-location descriptions. The content mentions these in passing (L29: "гори, море, ліси і поля") but doesn't formally teach them with IPA/examples. The vocabulary file also omits ліс, гори, and море despite being in `vocabulary_hints.recommended`. Not blocking since the meta outline the builder followed didn't include a dedicated nature subsection, and the word target is met.

3. **Quiz item ambiguity:** "Що ми робимо, коли спекотно?" → correct answer "Йдемо на пляж" is culturally presumptive (many stay home). Internally consistent with the lesson though, so not a blocker.

---

### Summary

| Category | Issues | Fixed |
|----------|--------|-------|
| Critical (typo, calque, pedagogical gap) | 4 | 4 |
| IPA accuracy (stress, ʋ, tie bars, ɦ) | 16 instances | 16 |
| Minor (Russicism, translation accuracy) | 2 | 2 |
| Noted only (vocab format, plan gaps) | 3 | 0 |

All fixable issues have FIX blocks above. After applying fixes: typo resolved, calque eliminated, «бо» properly taught before being tested, all IPA corrected to Ukrainian phonological standards with proper tie bars and ʋ.

===VERDICT===
APPROVE
===END_VERDICT===