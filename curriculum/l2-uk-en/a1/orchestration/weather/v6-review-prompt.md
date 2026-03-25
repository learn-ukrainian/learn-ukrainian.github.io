# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 24: Weather (A1, A1.4 [Time and Nature])
**Writer:** Gemini Pro
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-024
level: A1
sequence: 24
slug: weather
version: '1.2'
title: Weather
subtitle: Сьогодні холодно — talking about the weather
focus: vocabulary
pedagogy: PPP
phase: A1.4 [Time and Nature]
word_target: 1200
objectives:
- Describe weather using impersonal constructions (cold, warm, hot)
- Use "іде дощ / іде сніг" pattern for precipitation
- Combine weather with seasons and months
- Ask and answer "What's the weather like?"
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Looking out the window (ULP Ep16 pattern): — Яка сьогодні погода?
    — Сьогодні холодно і йде дощ. — А завтра? — Завтра буде тепло і сонячно. — Добре!
    Тоді завтра гуляємо! Weather + future plans (буде as chunk).'
  - 'Dialogue 2 — Seasons conversation: — Яка пора року тобі подобається? — Мені подобається
    літо. — Чому? — Тому що влітку тепло і сонячно. А тобі? — Мені подобається осінь.
    Восени красиво. Weather + seasons + opinion verbs from M15.'
- section: Яка погода? (What's the Weather?)
  words: 300
  points:
  - 'Impersonal weather expressions (no subject — the weather just IS): Сьогодні холодно.
    (It''s cold today.) Сьогодні тепло. (It''s warm.) Сьогодні спекотно. (It''s hot.)
    Сьогодні прохолодно. (It''s cool.) Заболотний Grade 8 p.126: безособові речення
    передають явища природи. These are adverbs — no subject needed, just the state.'
  - 'Precipitation patterns: Іде дощ. (It''s raining — literally ''rain goes''.) Іде
    сніг. (It''s snowing — ''snow goes''.) Дме вітер. (The wind is blowing.) Світить
    сонце. (The sun is shining.) Хмарно / ясно. (Cloudy / clear.) Note: іде дощ (not
    ''дощить'') is the natural conversational form.'
- section: Погода і пори року (Weather and Seasons)
  words: 300
  points:
  - 'Connecting weather to seasons (M23): Взимку холодно. Іде сніг. (In winter it''s
    cold. It snows.) Навесні тепло. Все зелене. (In spring it''s warm. Everything''s
    green.) Влітку спекотно. Світить сонце. (In summer it''s hot. The sun shines.)
    Восени прохолодно. Іде дощ. (In autumn it''s cool. It rains.)'
  - 'Temperature vocabulary: градуси (degrees) — Сьогодні двадцять градусів. (20 degrees.)
    плюс / мінус — Мінус десять. (Minus 10.) тепло / холодно as nouns: На вулиці тепло.
    (It''s warm outside.) Time words: сьогодні (today), завтра (tomorrow), вчора (yesterday).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Weather toolkit: Question: Яка сьогодні погода? Temperature: холодно, тепло,
    спекотно, прохолодно. Precipitation: іде дощ, іде сніг, дме вітер, світить сонце.
    Sky: хмарно, ясно, сонячно. Seasons: взимку холодно, влітку спекотно. Self-check:
    Describe today''s weather. What''s winter like where you live?'
vocabulary_hints:
  required:
  - погода (weather, f)
  - холодно (cold — adverb)
  - тепло (warm — adverb)
  - дощ (rain, m)
  - сніг (snow, m)
  - сонце (sun, n)
  - сьогодні (today)
  - завтра (tomorrow)
  recommended:
  - спекотно (hot)
  - прохолодно (cool)
  - вітер (wind, m)
  - хмарно (cloudy)
  - ясно (clear)
  - сонячно (sunny)
  - градус (degree, m)
  - вчора (yesterday)
activity_hints:
- type: match-up
  focus: Match the weather phrase to its logical context or season
  pairs:
  - іде дощ ↔ потрібна парасолька (umbrella)
  - іде сніг ↔ зима
  - світить сонце ↔ сонячно
  - дме вітер ↔ дерева шумлять (trees rustle)
  - мінус десять ↔ холодно
  - плюс тридцять ↔ спекотно
  - плюс двадцять ↔ тепло
  - сіре небо ↔ хмарно
- type: fill-in
  focus: Choose the logical weather for the season
  items:
  - Взимку часто {іде сніг|іде дощ|світить сонце}.
  - Влітку дуже {спекотно|холодно|хмарно}.
  - Восени часто {іде дощ|іде сніг|сонячно}.
  - Навесні {тепло|холодно|спекотно} і красиво.
  - Сьогодні мінус п'ять, дуже {холодно|тепло|спекотно}.
  - Сьогодні плюс двадцять п'ять, {тепло|прохолодно|холодно}.
- type: fill-in
  focus: Complete the dialogue about the weather
  items:
  - — Яка сьогодні {погода|сонце|дощ}? — Сьогодні тепло.
  - — Завтра {буде|є|був} сонячно. — Добре, гуляємо!
  - — Яка пора року тобі {подобається|любить|робить}? — Літо.
  - — Чому ти любиш літо? — Тому що влітку {сонячно|холодно|хмарно}.
connects_to:
- a1-025 (My Day)
prerequisites:
- a1-023 (Days and Months)
grammar:
- 'Impersonal constructions: cold/warm/hot (no subject)'
- Іде дощ / іде сніг pattern (literally 'goes rain/snow')
- 'Time adverbs: сьогодні, завтра, вчора'
register: розмовний
references:
- title: Заболотний Grade 8, p.126
  notes: 'Безособові речення: явища природи, стан людини.'
- title: ULP Season 1, Episode 16
  url: https://www.ukrainianlessons.com/episode16/
  notes: Weather vocabulary and expressions.

</plan_content>

## Generated Content

<generated_module_content>
## Діалоги (Dialogues)

Talking about the weather is a daily ritual in Ukraine — from deciding whether to grab a парасолька before heading out into the streets of Kyiv, to chatting with a neighbor on the stairwell landing. Knowing how to ask about conditions outside is one of the most practical skills you can learn early. 

Let's look at a common morning situation. You are looking out the window, trying to figure out the plans for the day and the coming weekend.

<div class="dialogue">


**Олена:** Яка сьогодні погода? *(What is the weather like today?)*


**Максим:** Сьогодні холодно і йде дощ. *(Today it is cold and raining.)*


**Олена:** А завтра? *(And tomorrow?)*


**Максим:** Завтра буде тепло і сонячно. *(Tomorrow it will be warm and sunny.)*


**Олена:** Добре! Тоді завтра гуляємо! *(Good! Then tomorrow we walk!)*


</div>


Let's break down the mechanics of this exchange:

- **Яка сьогодні погода?** means "What is the weather like today?" The word **погода** (weather) is a feminine noun, so it requires the feminine question word **яка** (what kind of).
- **Сьогодні** (today) acts as your time anchor. Ukrainian sentences often place time words right at the beginning or near the verb to establish context immediately.
- The phrase **йде дощ** literally translates to "rain goes." We will explore this fascinating pattern in the next section.
- When Olena asks about **завтра** (tomorrow), the timeline shifts. To express the future, we use the word **буде** (will be). For now, treat **буде** as a fixed chunk of vocabulary. You can pair it with any weather condition to make a prediction: **завтра буде тепло** (tomorrow it will be warm), **завтра буде сонячно** (tomorrow it will be sunny).

Our second dialogue connects the weather to personal preferences and seasons. This is how you explain why you love a particular time of year.

<div class="dialogue">


**Антон:** Яка пора року тобі подобається? *(What season do you like?)*


**Ірина:** Мені подобається літо. *(I like summer.)*


**Антон:** Чому? *(Why?)*


**Ірина:** Тому що влітку тепло і сонячно. А тобі? *(Because in summer it is warm and sunny. And you?)*


**Антон:** Мені подобається осінь. Восени красиво. *(I like autumn. In autumn it is beautiful.)*


</div>


Key takeaways from this conversation:

- **Пора року** means "season" (literally "time of the year").
- We reuse the highly practical chunk **мені подобається** (to me it is pleasing / I like). You do not need to change or conjugate this phrase; simply place the season you enjoy right after it.
- When giving a reason, use the linking phrase **тому що** (because).
- Notice the specific time adverbs used for the seasons: **влітку** (in summer) and **восени** (in autumn). These tell us exactly when the good weather happens.

:::fill-in
title: "Complete the dialogue about the weather"
---
- sentence: "— Яка сьогодні {погода|сонце|дощ}? — Сьогодні тепло."
- sentence: "— Завтра {буде|є|був} сонячно. — Добре, гуляємо!"
- sentence: "— Яка пора року тобі {подобається|любить|робить}? — Літо."
- sentence: "— Чому ти любиш літо? — Тому що влітку {сонячно|холодно|хмарно}."
:::

## Яка погода? (What's the Weather?)

When English speakers talk about the weather, they rely heavily on the dummy subject "it" — for example, "it is cold," "it is sunny," or "it is raining." Ukrainian does something entirely different and structurally much simpler.

Ukrainian uses what school textbooks, such as the standard Grade 8 grammar guide, call «безособові речення» (impersonal sentences). These are sentences that convey a state or condition without any grammatical subject at all. They are frequently used to describe phenomena of nature or the general environment. Instead of saying "it is cold," Ukrainian drops the subject entirely and simply states the condition using an adverb. The weather does not need a subject; the condition simply exists in the space around you.

- **Сьогодні холодно.** (It's cold today.)
- **Сьогодні тепло.** (It's warm today.)
- **Сьогодні спекотно.** (It's hot today.)
- **Сьогодні прохолодно.** (It's cool today.)

You do not need a verb like "is" or a subject like "it." You simply take your time word, like **сьогодні** (today), and pair it directly with the weather adverb. Notice that all of these adverbs end in the letter «о». They describe the general environment, rather than modifying a specific noun.

This grammatical feature is not just a quirky rule; it fundamentally changes how you perceive the environment in Ukrainian. By removing the subject, the focus shifts entirely to the feeling or the condition itself. The coldness or warmth surrounds you. It is an immersive way of speaking. When you step outside in January and feel the freezing air, you do not need to construct a complex sentence. You simply say **сьогодні холодно**, and the environment is perfectly summarized.

You can easily adjust the intensity of these conditions by adding modifiers like **дуже** (very) or **трохи** (a little).

- **Сьогодні дуже холодно.** (It's very cold today.)
- **Сьогодні трохи прохолодно.** (It's a little cool today.)

When it comes to precipitation, Ukrainian grammar takes a very active, personified approach. While English uses verbs ("it rains," "it snows"), Ukrainian pairs a noun with a verb of motion. Rain and snow are viewed as active participants that physically "go" or "walk" using the verb **іде** (goes).

- **Іде дощ.** (It's raining — literally "rain goes".)
- **Іде сніг.** (It's snowing — literally "snow goes".)

While you might occasionally encounter a single-verb form in literature, **іде дощ** is the highly natural, conversational standard you will hear from native speakers every day. It gives the language a grounded, poetic rhythm. 

Other forces of nature use their own specific action verbs to describe what they are doing.

- **Дме вітер.** (The wind is blowing.)
- **Світить сонце.** (The sun is shining.)

Finally, when you want to describe the state of the sky above you, you return to the subjectless impersonal adverbs we learned earlier.

- **Сьогодні хмарно.** (Today it is cloudy.)
- **Сьогодні ясно.** (Today it is clear.)
- **Сьогодні сонячно.** (Today it is sunny.)

:::match-up
title: "Match the weather phrase to its logical context or season"
---
- left: "іде дощ"
  right: "потрібна парасолька"
- left: "іде сніг"
  right: "зима"
- left: "світить сонце"
  right: "сонячно"
- left: "дме вітер"
  right: "дерева шумлять"
- left: "мінус десять"
  right: "холодно"
- left: "плюс тридцять"
  right: "спекотно"
- left: "плюс двадцять"
  right: "тепло"
- left: "сіре небо"
  right: "хмарно"
:::

## Погода і пори року (Weather and Seasons)

Weather is intrinsically tied to the rhythm of the year. Let's combine our new weather adverbs and active nature verbs with the seasons. By placing the season adverb first, you establish the scene, and then you simply state the environmental condition.

- **Взимку холодно. Іде сніг.** (In winter it's cold. It snows.)
- **Навесні тепло. Все зелене.** (In spring it's warm. Everything's green.)
- **Влітку спекотно. Світить сонце.** (In summer it's hot. The sun shines.)
- **Восени прохолодно. Іде дощ.** (In autumn it's cool. It rains.)

Notice how direct these sentences are. There is no complex grammar or nested clauses. You set the time (**влітку**), and you state the fact (**спекотно**).

As the seasons change, you will often need to discuss the exact temperature, especially during the sharp transitions of late autumn and early spring. To do this, you need the word for "degree," which is **градус**.

- **Сьогодні двадцять градусів.** (Today is 20 degrees.)

Understanding the temperature scale is vital when conversing with native speakers. Ukraine, like most of the world, uses the Celsius scale. If a friend tells you the temperature is twenty-five degrees, they mean it is excellent beach weather, and anything near zero means you need a heavy winter coat. 

To indicate whether the temperature is above or below freezing, Ukrainian uses the international terms **плюс** (plus) and **мінус** (minus). The transition between seasons in Eastern Europe can be quite dramatic, which makes checking the thermometer a daily ritual. During the late autumn months, temperatures frequently hover around zero, making the distinction between plus and minus critical in daily life.

- **Сьогодні плюс двадцять п'ять, тепло.** (Today is plus 25, it's warm.)
- **Сьогодні мінус десять, дуже холодно.** (Today is minus 10, it's very cold.)

The phrase **на вулиці** (outside, literally "on the street") is a common way to set the scene. When combined with our impersonal weather adverbs, it specifies the location of the condition — the same subjectless pattern, just anchored to a place instead of a time.

- **На вулиці тепло.** (It's warm outside.)
- **На вулиці холодно.** (It's cold outside.)

To be fully conversational about the weather, you must be able to anchor your statements in time. You already know how to talk about the current moment using **сьогодні** (today) and the future using **завтра** (tomorrow). To talk about the past, we introduce the word **вчора** (yesterday).

- **Вчора** (yesterday)
- **Сьогодні** (today)
- **Завтра** (tomorrow)

For now, focus on describing the present conditions and making simple predictions about tomorrow. You can pair your time words with the conditions you want to describe. As you saw in the first dialogue, to predict tomorrow's weather, use the helper word **буде** (will be) as a fixed vocabulary chunk. 

- **Сьогодні холодно.** (Today it is cold.)
- **Завтра буде тепло.** (Tomorrow it will be warm.)
- **Завтра буде сонячно.** (Tomorrow it will be sunny.)

:::fill-in
title: "Choose the logical weather for the season"
---
- sentence: "Взимку часто {іде сніг|іде дощ|світить сонце}."
- sentence: "Влітку дуже {спекотно|холодно|хмарно}."
- sentence: "Восени часто {іде дощ|іде сніг|сонячно}."
- sentence: "Навесні {тепло|холодно|спекотно} і красиво."
- sentence: "Сьогодні мінус п'ять, дуже {холодно|тепло|спекотно}."
- sentence: "Сьогодні плюс двадцять п'ять, {тепло|прохолодно|холодно}."
:::

## Підсумок — Summary

You now have the complete vocabulary and grammar toolkit to navigate daily weather conversations in Ukrainian. The beauty of this system lies in its directness: you do not need complex grammatical subjects to describe the environment around you.

In Ukrainian, nature is alive. The rain walks, the wind blows, and the sun shines with active verbs. At the same time, the general environment is treated as an undeniable state of being — an impersonal construction with no subject at all. This fundamental shift from English dummy subjects to Ukrainian impersonal sentences will make your speech sound significantly more natural and authentic.

When you pair these expressions with your knowledge of the seasons and days of the week, you unlock the ability to make plans, share preferences, and bond over the universal topic of the weather. Whether you are complaining about the gray skies of November or celebrating the first sunny days of April, you are now participating in a daily cultural ritual.

Let's review the core components of your weather toolkit.

**Asking about the weather:**
- Яка сьогодні погода? (What is the weather like today?)

**Temperature and conditions:**
- холодно (cold), тепло (warm), спекотно (hot), прохолодно (cool)

**Precipitation and sky:**
- Іде дощ. (It's raining.) Іде сніг. (It's snowing.)
- Дме вітер. (The wind is blowing.) Світить сонце. (The sun is shining.)
- хмарно (cloudy), ясно (clear), сонячно (sunny)

**Seasons and weather:**
- Взимку холодно. Влітку спекотно. Навесні тепло. Восени прохолодно.

**Time anchors:**
- вчора (yesterday), сьогодні (today), завтра (tomorrow)
- Завтра буде сонячно. (Tomorrow it will be sunny.)

**Self-check:** Try these on your own. Look outside right now and describe the weather in Ukrainian using the patterns from this module. What season is it? What is the temperature? Then think about your favorite season — яка пора року тобі подобається? Describe the weather in that season. Finally, what is winter like where you live? Use the pattern: Взимку... і...

**Deterministic word count: 1747 words** (calculated by pipeline, do NOT estimate manually)

</generated_module_content>

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

List every exercise block (`:::quiz`, `:::fill-in`, `:::match-up`, `:::group-sort`, `:::true-false`). These are filled exercises — a deterministic tool converted placeholders to real content.

For each exercise, check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?
- Are there enough items per exercise? (check against plan's `activity_hints`)

Also check: Are there enough exercises total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercises are generated by a deterministic tool from the writer's placeholders. If the exercise LOGIC is wrong (e.g., matching unrelated items), flag it — the tool's input data needs fixing. If the exercise FORMAT looks unusual, that is expected (the tool uses a specific DSL syntax).

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | Every content_outline point covered? Section word budgets respected (±10%)? All plan references used? |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | PPP (Present→Practice→Produce) applied? Textbook pedagogy used (Большакова, Захарійчук)? Grammar scope respected (no A2 in A1)? |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | Placeholders specific enough? Test the right skills? Placed after relevant teaching? Match plan's activity_hints? Sufficient items? |
| 6 | **Engagement & tone** | 10% | Interesting for teens/adults? Authoritative but warm (like a skilled teacher)? No LLM filler ("Good news!", "Don't panic!", "Fun fact!")? Cultural hooks? |
| 7 | **Structural integrity** | 5% | All H2 headings from plan present? Word count in range? No duplicate sections? No meta-commentary? Clean markdown? |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | Dialogues natural and culturally appropriate? Real situations, real responses? Speaker roles clear? Not stilted or textbook-robotic? |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Critical = module cannot ship. Major = quality below standard. Minor = polish item.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero critical findings, at most minor issues |
| **REVISE** | Has major findings but no criticals — fixable without rewrite |
| **REJECT** | Has any critical finding — fundamental problems requiring rewrite |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string must be an EXACT substring of the module content — copy-paste it
- Keep fixes minimal — change only what's wrong, preserve surrounding text
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 83 words | Not found: 3 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Ірина — NOT IN VESUM
  ✗ Антон — NOT IN VESUM
  ✗ Олена — NOT IN VESUM

All 83 other words are confirmed to exist in VESUM.

</vesum_verification>