<!-- version: 1.0.0 | updated: 2026-03-27 -->
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
dialogue_situations:
- setting: Two friends deciding whether to go hiking — checking weather together
  speakers:
  - Іванко
  - Галя
  motivation: 'Impersonal: Сьогодні холодно, Завтра буде тепло, Іде дощ'
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
  - іде дощ ↔ холодно і мокро
  - іде сніг ↔ зима
  - світить сонце ↔ сонячно
  - дме вітер ↔ прохолодно
  - мінус десять ↔ холодно
  - плюс тридцять ↔ спекотно
  - плюс двадцять ↔ тепло
  - хмарно ↔ сонце не світить
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

Іванко and Галя stand at a window on a grey morning. They want to go hiking — but the sky looks terrible. Should they go today, or wait until tomorrow?

<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Іванко:</span> Яка сьогодні погода? *(What's the weather like today?)*</div>

<div class="dialogue-line"><span class="speaker">Галя:</span> Сьогодні холодно і йде дощ. *(It's cold today and it's raining.)*</div>

<div class="dialogue-line"><span class="speaker">Іванко:</span> Ой... А завтра? *(Oh... And tomorrow?)*</div>

<div class="dialogue-line"><span class="speaker">Галя:</span> Завтра буде тепло і сонячно. *(Tomorrow it will be warm and sunny.)*</div>

<div class="dialogue-line"><span class="speaker">Іванко:</span> Добре! Тоді завтра гуляємо! *(Great! Then tomorrow we walk!)*</div>

<div class="dialogue-line"><span class="speaker">Галя:</span> Так! Завтра буде гарний день. *(Yes! Tomorrow will be a nice day.)*</div>

</div>

Three phrases to notice here. **Яка погода** (what weather) — this is how you ask about the weather. **Холодно** (cold) — no subject, no "it is," just the state. And **буде тепло** (will be warm) — **буде** works as a simple future marker. Treat it as a chunk for now, not a full grammar lesson.

There's something interesting about Ukrainian weather sentences: the weather just IS. There is no dummy subject like English "it." **Сьогодні холодно** means exactly "today cold." The language skips the filler word English needs. This makes weather talk shorter and more direct.

Now Іванко and Галя talk about their favourite seasons:

<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Іванко:</span> Яка пора року тобі подобається? *(What season do you like?)*</div>

<div class="dialogue-line"><span class="speaker">Галя:</span> Мені подобається літо. *(I like summer.)*</div>

<div class="dialogue-line"><span class="speaker">Іванко:</span> Чому? *(Why?)*</div>

<div class="dialogue-line"><span class="speaker">Галя:</span> Тому що влітку тепло і сонячно. А тобі? *(Because in summer it's warm and sunny. And you?)*</div>

<div class="dialogue-line"><span class="speaker">Іванко:</span> Мені подобається осінь. *(I like autumn.)*</div>

<div class="dialogue-line"><span class="speaker">Галя:</span> Восени красиво? *(Is it beautiful in autumn?)*</div>

<div class="dialogue-line"><span class="speaker">Іванко:</span> Так! А взимку? *(Yes! And in winter?)*</div>

<div class="dialogue-line"><span class="speaker">Галя:</span> Взимку холодно, але красиво. Йде сніг! *(In winter it's cold, but beautiful. It snows!)*</div>

</div>

Notice the season adverbs: **взимку** (in winter), **навесні** (in spring), **влітку** (in summer), **восени** (in autumn). These are frozen adverbs you already know from M23. They don't change form. Now pair each with the weather you just heard: **взимку** — **холодно**, **влітку** — **тепло**, **восени** — **дощ**.

## Яка погода? (What's the Weather?)

Ukrainian weather sentences have no subject — just a state adverb sitting alone as the whole sentence. **Сьогодні холодно** — "today it's cold." Compare the four temperature adverbs side by side: **холодно** (cold), **прохолодно** (cool), **тепло** (warm), **спекотно** (hot). Each word is an adverb that doubles as a full predicate — nothing else needed. No subject, no verb "to be." As Заболотний teaches in Grade 8: безособові речення (impersonal sentences) express natural phenomena. The weather simply exists.

Beyond temperature, you need sky conditions: **хмарно** (cloudy), **ясно** (clear), **сонячно** (sunny). These work exactly the same way — standalone adverbs as full sentences. Compare: **Сьогодні ясно і сонячно** versus **Сьогодні хмарно**. You can toggle between today and tomorrow using time adverbs: **Сьогодні хмарно. Завтра буде сонячно.** Notice **буде** appears again — it's a simple future marker used as a chunk here, not a full verb lesson yet. **Сьогодні** (today) states the present; **завтра** (tomorrow) plus **буде** signals the future.

<!-- INJECT_ACTIVITY: fill-in-weather-season -->

Now the really fun part — precipitation and movement. Each weather phenomenon in Ukrainian has its own verb:

- **Іде дощ.** — It's raining (literally "rain goes").
- **Іде сніг.** — It's snowing ("snow goes").
- **Дме вітер.** — The wind is blowing.
- **Світить сонце.** — The sun is shining.

There's a lovely moment in a Grade 5 textbook (Avramenko, p.27) where a little sister hears her brother say **піде дощ** and asks: *«А хіба дощ може ходити?»* — "Can rain really walk?" This confusion shows that **іде дощ** is an idiom, not literal walking. Rain "goes" the same way English rain "falls" — nobody pictures it tripping. Learn all four verbs as fixed chunks: **іде** (goes — for rain and snow), **дме** (blows — for wind), **світить** (shines — for the sun).

Temperature in numbers uses **градуси** (degrees). **Сьогодні двадцять градусів** — "Today it's twenty degrees." For positive and negative temperatures, use **плюс** and **мінус**: **Плюс тридцять** (plus thirty — hot), **Мінус десять** (minus ten — very cold). In everyday speech, Ukrainians often drop **градусів**: simply **Сьогодні мінус десять.** Ukrainian weather forecasts always use Celsius — **плюс двадцять** (20°C) is **тепло**, **плюс тридцять** (30°C) is **спекотно**, **мінус десять** (−10°C) is **дуже холодно**.

## Погода і пори року (Weather and Seasons)

Connect weather to all four seasons using the adverbs from M23. Here are four mini-portraits — each season in two weather facts and one image from nature:

- **Взимку холодно. Іде сніг. Все біле.** — In winter it's cold. It snows. Everything is white.
- **Навесні тепло. Іде дощ. Все зелене.** — In spring it's warm. It rains. Everything is green.
- **Влітку спекотно. Світить сонце. Все квітне.** — In summer it's hot. The sun shines. Everything blooms.
- **Восени прохолодно. Дме вітер. Листя жовте.** — In autumn it's cool. The wind blows. The leaves are yellow.

Each portrait follows the same pattern: season adverb + temperature + precipitation or sky + nature image. This is the Grade 4 textbook pattern: *«Сади цвітуть навесні, улітку трав поля шовкові, а восени врожай збирають, узимку снігу всі чекають.»*

<!-- INJECT_ACTIVITY: fill-in-weather-for-season -->

Weather descriptions naturally combine with opinions. You already know **подобається** (like) from M15. Now pair it with seasons and weather:

- **Мені подобається зима. Іде сніг і все біле.** — I like winter. It snows and everything is white.
- **Я люблю літо. Спекотно і сонячно.** — I love summer. It's hot and sunny.
- **Мені подобається весна. Тепло і все зелене.** — I like spring. It's warm and everything is green.

The pattern is simple: **Мені подобається** + season, then a separate sentence with the weather reason. This recycles **подобається** and **люблю** from M15 while adding your new weather vocabulary.

<!-- INJECT_ACTIVITY: match-weather-context -->

Now put everything together in one more conversation. Іванко asks Галя about her dream weather:

<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Іванко:</span> Яка твоя ідеальна погода? *(What's your ideal weather?)*</div>

<div class="dialogue-line"><span class="speaker">Галя:</span> Плюс двадцять, сонячно і без вітру. *(Plus twenty, sunny, and no wind.)*</div>

<div class="dialogue-line"><span class="speaker">Іванко:</span> А взимку ти любиш сніг? *(And in winter, do you like snow?)*</div>

<div class="dialogue-line"><span class="speaker">Галя:</span> Так, але не дуже холодно! *(Yes, but not too cold!)*</div>

<div class="dialogue-line"><span class="speaker">Іванко:</span> У Києві зараз мінус п'ять. *(In Kyiv right now it's minus five.)*</div>

<div class="dialogue-line"><span class="speaker">Галя:</span> О, це дуже холодно! А у тебе? *(Oh, that's very cold! And where you are?)*</div>

<div class="dialogue-line"><span class="speaker">Іванко:</span> У мене сьогодні тепло. Плюс п'ятнадцять і хмарно. *(Here today it's warm. Plus fifteen and cloudy.)*</div>

<div class="dialogue-line"><span class="speaker">Галя:</span> Добре! Не холодно — і добре! *(Good! Not cold — and that's fine!)*</div>

</div>

Notice **ідеальна** (ideal), **без вітру** (without wind — **без** means "without"), and how Галя and Іванко compare weather in different cities using **у Києві** (in Kyiv) and **у мене** (where I am).

## Підсумок — Summary

You now have three weather tools. First, state adverbs for temperature: **холодно** (cold), **прохолодно** (cool), **тепло** (warm), **спекотно** (hot), plus sky conditions **хмарно** (cloudy), **ясно** (clear), **сонячно** (sunny). Second, movement verbs for precipitation: **іде дощ**, **іде сніг**, **дме вітер**, **світить сонце**. Third, season-weather combinations: **взимку холодно**, **влітку спекотно**. Together these cover everything a real weather conversation needs.

:::tip Інструменти погоди — Weather Toolkit
- **Питання:** Яка сьогодні погода?
- **Температура:** холодно · прохолодно · тепло · спекотно
- **Опади:** іде дощ · іде сніг
- **Небо:** хмарно · ясно · сонячно
- **Вітер/сонце:** дме вітер · світить сонце
- **Градуси:** плюс двадцять · мінус десять
- **Час:** сьогодні · завтра · вчора
- **Пори року:** взимку · навесні · влітку · восени
:::

<!-- INJECT_ACTIVITY: fill-in-dialogue-weather -->

### Перевір себе — Self-check

Try these on your own. Say each answer out loud in Ukrainian before checking:

- Опиши сьогоднішню погоду трьома реченнями. *(Describe today's weather in three sentences.)*
- Яка погода взимку там, де ти живеш? *(What's the weather like in winter where you live?)*
- Яка твоя улюблена пора року? Чому? *(What's your favourite season? Why?)*
- Say in Ukrainian: "Tomorrow it will be warm and sunny."
- Say in Ukrainian: "I like autumn because it's cool."
- How do you say "it's raining" in Ukrainian? And "it's snowing"?

Next up: **My Day** (M25) builds a full daily schedule. You'll need today's weather to decide what to wear and where to go — all the vocabulary from this module feeds directly into M25 morning routines and outdoor plans. **Сьогодні тепло? Тоді гуляємо!**

**Deterministic word count: 1357 words** (calculated by pipeline, do NOT estimate manually)

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

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | DEDUCT for: motivational openers ("Numbers unlock the real Ukraine!"), meta-commentary ("Let us look at...", "Let us now explore..."), generic enthusiasm ("incredibly melodic", "hugely important"), telling instead of showing ("You now possess...", "You have unlocked..."), gamified language ("unlocked the ability"), corporate-speak ("precision and accuracy"), "The magic of...", any sentence that could apply to any language course unchanged. REWARD for: specific cultural details, natural dialogues, humor, concrete examples, teacher demonstrating rather than lecturing about how great the content is. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count outside target range, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count in range. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

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

Verified: 130 words | Not found: 2 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Іванко — NOT IN VESUM
  ✗ Галя — NOT IN VESUM

All 130 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
