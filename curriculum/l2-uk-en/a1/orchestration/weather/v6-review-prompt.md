<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 24: Weather (A1, A1.4 [Time and Nature])
**Writer:** Gemini
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

Morning routines often begin with a glance outside the window to check the conditions. Deciding what to wear for the day or planning an outdoor trip with a friend requires basic vocabulary to describe the environment. Ivan and Halya are looking out their window, trying to figure out if today is a good day for a hike in the mountains. 

Ivan asks the most common question about the daily conditions, and Halya responds by describing both the temperature and the rain. Notice how Halya uses the word **буде** (will be) as a fixed chunk to predict the conditions for the next day.

> **Іванко:** Яка сьогодні погода? *(What is the weather like today?)*
> **Галя:** Сьогодні холодно і йде дощ. *(Today it is cold and it is raining.)*
> **Іванко:** А завтра? *(And tomorrow?)*
> **Галя:** Завтра буде тепло і сонячно. *(Tomorrow it will be warm and sunny.)*
> **Іванко:** Добре! Тоді завтра гуляємо! *(Good! Then we walk tomorrow!)*

The word **погода** (weather) is a feminine noun. When asking about it, use the feminine question word **яка** (what kind of). The adverb **сьогодні** (today) sets the context for the current day, and **завтра** (tomorrow) looks ahead. These time adverbs help ground your conversation in the present or the future.

People also have strong opinions about different times of the year. When discussing your favorite time of year, you can connect the seasons to the typical conditions you experience during those months. The phrase **пора року** translates to "season" (literally "time of the year").

> **Іванко:** Яка пора року тобі подобається? *(Which season do you like?)*
> **Галя:** Мені подобається літо. *(I like summer.)*
> **Іванко:** Чому? *(Why?)*
> **Галя:** Тому що влітку тепло і сонячно. А тобі? *(Because in summer it is warm and sunny. And you?)*
> **Іванко:** Мені подобається осінь. Восени красиво. *(I like autumn. In autumn it is beautiful.)*

This conversation uses the verb construction **мені подобається** (I like / it is pleasing to me) alongside the adverbs **тепло** (warm), **сонячно** (sunny), and **красиво** (beautiful). Ukrainian relies heavily on these descriptive adverbs to convey states and environments accurately.

## Яка погода? (What's the Weather?)

English requires a subject and a verb to build a sentence, even when neither makes logical sense. You say "It is cold", using the empty pronoun "it". Ukrainian grammar takes a different, much more direct approach. According to the textbook *Заболотний Grade 8* (page 126), Ukrainian uses **безособові речення** (impersonal sentences) to convey natural phenomena. You simply state the adverb without any subject or the verb "to be" to establish the fact. You say **холодно** (cold) to mean "It is cold", and **тепло** (warm) to mean "It is warm". A common mistake for English speakers is trying to translate word-for-word, resulting in incorrect phrases like **Це є тепло** (This is warm) or **Воно є сонячно** (It is sunny). These literal translations sound highly unnatural to native speakers. Drop the subject and verb entirely.

:::caution
Never use **це є** or **воно є** to describe the weather. Ukrainian drops the subject entirely. Use the bare adverb: **Сьогодні тепло** (Today it is warm).
:::

The core vocabulary for discussing temperature consists of four essential adverbs. Use **холодно** (cold) for winter days, **прохолодно** (cool) for crisp autumn mornings, **тепло** (warm) for pleasant spring afternoons, and **спекотно** (hot) for the peak of summer. You can modify these states by adding the adverb **дуже** (very) before the weather word.

*   **Сьогодні дуже спекотно.** — Today it is very hot.
*   **Вчора було прохолодно.** — Yesterday it was cool.
*   **Сьогодні дуже тепло.** — Today it is very warm.
*   **Вчора було холодно.** — Yesterday it was cold.

The word **вчора** means "yesterday". When talking about the past, you must add the neuter past-tense verb **було** (it was) before the adverb.

Ukrainian personifies precipitation, treating it as an active participant. Instead of saying "it is raining", you say that the rain or snow "goes" or "walks". The verb **іти** (to go on foot) describes this action. This creates fixed, highly idiomatic paradigms.

*   **Іде дощ.** — It is raining (literally "rain goes").
*   **Іде сніг.** — It is snowing (literally "snow goes").

While the single verb **дощить** (it rains) exists in the dictionary, the phrase **іде дощ** is the natural conversational form you will hear on the street. Other weather events use different verbs: **світить сонце** (the sun is shining) and **дме вітер** (the wind is blowing).

<!-- INJECT_ACTIVITY: fill-in-weather-dialogue -->

## Погода і пори року (Weather and Seasons)

Linking weather states to the seasons you learned earlier provides excellent conversational practice. Use the seasonal adverbs **взимку** (in winter), **навесні** (in spring), **влітку** (in summer), and **восени** (in autumn) to establish the time context, and then add the typical environmental conditions.

*   **Взимку холодно. Іде сніг.** — In winter it is cold. It snows.
*   **Навесні тепло. Все зелене.** — In spring it is warm. Everything is green.
*   **Влітку спекотно. Світить сонце.** — In summer it is hot. The sun shines.
*   **Восени прохолодно. Іде дощ.** — In autumn it is cool. It rains.

These short, descriptive sentences form the foundation of natural storytelling in Ukrainian.

Beyond temperature and precipitation, you often need to describe the appearance of the sky. The three main adverbs for the sky are **хмарно** (cloudy), **ясно** (clear), and **сонячно** (sunny). There is a logical link between the state of the sky and the type of weather you can expect.

*   **Сьогодні ясно і сонячно.** — Today it is clear and sunny.
*   **Зараз дуже хмарно.** — Right now it is very cloudy.
*   **Сонце не світить. Хмарно.** — The sun is not shining. It is cloudy.

If the sky is covered in heavy clouds, you might soon say **іде дощ**. 

:::tip
The word **ясно** (clear) is also frequently used in conversation to mean "I understand" or "It is clear to me."
:::

When exact details matter, you can discuss the temperature using numbers. Ukraine uses the Celsius scale, so any numbers you hear will reflect that system. The noun **градус** (degree) is masculine. Combine it with the words **плюс** (plus) or **мінус** (minus) to specify the exact conditions outside. If someone asks **Яка температура?** (What is the temperature?), you reply with the number.

*   **Сьогодні плюс двадцять градусів.** — Today it is plus twenty degrees.
*   **Сьогодні двадцять градусів.** — Today is twenty degrees.
*   **Зараз мінус десять.** — Right now it is minus ten.

You can also use the adverbs **тепло** and **холодно** as nouns in certain contexts to refer to the abstract concept of warmth or cold. For example, **На вулиці тепло** means "It is warm outside" (literally "on the street"). Using the phrase **на вулиці** (outside) is a very common way to describe outdoor conditions in daily conversation.

<!-- INJECT_ACTIVITY: match-up-weather-season -->
<!-- INJECT_ACTIVITY: fill-in-season-weather -->

## Підсумок — Summary

You now have a complete toolkit for describing the environment around you. The fundamental question is **Яка сьогодні погода?** (What is the weather like today?). To answer, you rely on impersonal adverbs without subjects or verbs: **холодно** (cold), **тепло** (warm), **спекотно** (hot), and **прохолодно** (cool). Precipitation is personified as a moving object, giving us the natural conversational phrases **іде дощ** (it is raining) and **іде сніг** (it is snowing). We also use active verbs for other phenomena, such as **дме вітер** (the wind is blowing) and **світить сонце** (the sun is shining). When you look at the sky, you can describe it as **хмарно** (cloudy), **ясно** (clear), or **сонячно** (sunny). Connecting these conditions to the time of year allows you to build rich sentences like **взимку холодно** (in winter it is cold) or **влітку спекотно** (in summer it is hot).

Use this self-check to practice your new vocabulary. Read the questions below and try to answer them aloud in complete Ukrainian sentences. Think about the current conditions outside your window, the temperature, and your personal preferences.

*   Яка сьогодні погода у твоєму місті?
*   Яка температура сьогодні: плюс чи мінус?
*   Яка твоя улюблена пора року? Чому?
*   Що йде взимку: дощ чи сніг?

If you can answer these questions confidently using adverbs like **тепло** or phrases like **іде дощ**,  This vocabulary will allow you to plan your days, discuss your favorite seasons, and easily start conversations with native speakers.
</generated_module_content>

**PIPELINE NOTE — Word count: 1332 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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
| 6 | **Engagement & tone** | 10% | The writer's persona is an encouraging teacher — natural teacher phrasing like "Let us look at..." or "Have you noticed..." is FINE and should NOT be penalized. DEDUCT ONLY for: self-congratulatory openers ("Welcome to A2! Congratulations on completing..."), gamified/corporate language ("You have unlocked...", "You now possess...", "Your journey begins..."), empty filler that adds words but zero information ("This is a very important concept that you will use frequently in your daily life"), generic enthusiasm not specific to Ukrainian ("incredibly beautiful language", "wonderfully consistent system"). REWARD for: teacher warmth with substance, specific cultural details, humor, concrete Ukrainian examples, natural classroom energy. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 1200 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
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
- The `find` string MUST be an EXACT copy-paste from the module content. DO NOT change quotes (« » to " "), dashes (— to -), or spacing. If you change a single character in the `find` string, the automated replacement will fail.
- Keep fixes minimal — change only what's wrong, preserve surrounding text. Provide enough context (e.g. 5-7 words) to make the match unique.
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

Verified: 79 words | Not found: 2 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Іванко — NOT IN VESUM
  ✗ Галя — NOT IN VESUM

All 79 other words are confirmed to exist in VESUM.

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
