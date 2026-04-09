<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/weather.yaml` file for module **24: Weather** (a1).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 2-3 quick checks after key teaching points. Workbook = 4-8 deeper practice exercises covering the full topic.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: fill-in-weather-season -->`
- `<!-- INJECT_ACTIVITY: fill-in-weather-for-season -->`
- `<!-- INJECT_ACTIVITY: match-weather-context -->`
- `<!-- INJECT_ACTIVITY: fill-in-dialogue-weather -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match the weather phrase to its logical context or season
  pairs:
  - іде дощ ↔ холодно і мокро
  - іде сніг ↔ зима
  - світить сонце ↔ сонячно
  - дме вітер ↔ прохолодно
  - мінус десять ↔ холодно
  - плюс тридцять ↔ спекотно
  - плюс двадцять ↔ тепло
  - хмарно ↔ сонце не світить
  type: match-up
- focus: Choose the logical weather for the season
  items:
  - Взимку часто {іде сніг|іде дощ|світить сонце}.
  - Влітку дуже {спекотно|холодно|хмарно}.
  - Восени часто {іде дощ|іде сніг|сонячно}.
  - Навесні {тепло|холодно|спекотно} і красиво.
  - Сьогодні мінус п'ять, дуже {холодно|тепло|спекотно}.
  - Сьогодні плюс двадцять п'ять, {тепло|прохолодно|холодно}.
  type: fill-in
- focus: Complete the dialogue about the weather
  items:
  - — Яка сьогодні {погода|сонце|дощ}? — Сьогодні тепло.
  - — Завтра {буде|є|був} сонячно. — Добре, гуляємо!
  - — Яка пора року тобі {подобається|любить|робить}? — Літо.
  - — Чому ти любиш літо? — Тому що влітку {сонячно|холодно|хмарно}.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- спекотно (hot)
- прохолодно (cool)
- вітер (wind, m)
- хмарно (cloudy)
- ясно (clear)
- сонячно (sunny)
- градус (degree, m)
- вчора (yesterday)
required:
- погода (weather, f)
- холодно (cold — adverb)
- тепло (warm — adverb)
- дощ (rain, m)
- сніг (snow, m)
- сонце (sun, n)
- сьогодні (today)
- завтра (tomorrow)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Іванко and Галя stand at a window on a grey morning. They want to go hiking — but the sky looks terrible. Should they go today, or wait until tomorrow?

> **Іванко:** Яка сьогодні погода? *(What's the weather like today?)*
> **Галя:** Сьогодні холодно і йде дощ. *(It's cold today and it's raining.)*
> **Іванко:** Ой... А завтра? *(Oh... And tomorrow?)*
> **Галя:** Завтра буде тепло і сонячно. *(Tomorrow it will be warm and sunny.)*
> **Іванко:** Добре! Тоді завтра гуляємо! *(Great! Then tomorrow we walk!)*
> **Галя:** Так! Завтра буде гарний день. *(Yes! Tomorrow will be a nice day.)*

Three phrases to notice here. **Яка погода** (what weather) — this is how you ask about the weather. **Холодно** (cold) — no subject, no "it is," just the state. And **буде тепло** (will be warm) — **буде** works as a simple future marker. Treat it as a chunk for now, not a full grammar lesson.

There's something interesting about Ukrainian weather sentences: the weather just IS. There is no dummy subject like English "it." **Сьогодні холодно** means exactly "today cold." The language skips the filler word English needs. This makes weather talk shorter and more direct.

Now Іванко and Галя talk about their favourite seasons:

> **Іванко:** Яка пора року тобі подобається? *(What season do you like?)*
> **Галя:** Мені подобається літо. *(I like summer.)*
> **Іванко:** Чому? *(Why?)*
> **Галя:** Тому що влітку тепло і сонячно. А тобі? *(Because in summer it's warm and sunny. And you?)*
> **Іванко:** Мені подобається осінь. *(I like autumn.)*
> **Галя:** Восени красиво? *(Is it beautiful in autumn?)*
> **Іванко:** Так! А взимку? *(Yes! And in winter?)*
> **Галя:** Взимку холодно, але красиво. Йде сніг! *(In winter it's cold, but beautiful. It snows!)*

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

> **Іванко:** Яка твоя ідеальна погода? *(What's your ideal weather?)*
> **Галя:** Плюс двадцять, сонячно і без вітру. *(Plus twenty, sunny, and no wind.)*
> **Іванко:** А взимку ти любиш сніг? *(And in winter, do you like snow?)*
> **Галя:** Так, але не дуже холодно! *(Yes, but not too cold!)*
> **Іванко:** У Києві зараз мінус п'ять. *(In Kyiv right now it's minus five.)*
> **Галя:** О, це дуже холодно! А у тебе? *(Oh, that's very cold! And where you are?)*
> **Іванко:** У мене сьогодні тепло. Плюс п'ятнадцять і хмарно. *(Here today it's warm. Plus fifteen and cloudy.)*
> **Галя:** Добре! Не холодно — і добре! *(Good! Not cold — and that's fine!)*

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

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: weather
level: a1

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:
      - question: "_____ стіл"
        options: ["мій", "моя", "моє"]
        correct: 0             # 0-based index

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]

workbook:
  - type: match-up
    instruction: "З'єднайте пари"
    pairs:
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"

  - type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Category A"
        items: ["word1", "word2"]
      - label: "Category B"
        items: ["word3", "word4"]

  - type: true-false
    instruction: "Правда чи ні?"
    items:
      - statement: "Statement here"
        correct: true
        explanation: "Why it's true"

  - type: error-correction
    instruction: "Виправте помилку"
    items:
      - sentence: "Sentence with error"
        error: "wrong word"
        correction: "correct word"
        error_type: "word"
        options: ["option1", "option2", "option3"]
        explanation: "Why it's wrong"

  - type: observe
    examples:
      - "example sentence 1"
      - "example sentence 2"
    prompt: "What pattern do you notice?"

  - type: translate
    instruction: "Оберіть правильний переклад"
    items:
      - source: "English phrase"
        options:
          - text: "correct Ukrainian"
            correct: true
          - text: "wrong Ukrainian"
            correct: false

  - type: anagram
    instruction: "Складіть слово з літер"
    items:
      - letters: ["к", "н", "и", "г", "а"]
        answer: "книга"
        hint: "book"
```

---

## Activity Type Reference

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: instruction, items[{sentence, error, correction}]
- **anagram**: Letter rearrangement. Required: instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: instruction, items[{words[], correct_order[]}]
- **observe**: Pattern discovery. Required: examples[], prompt
- **classify**: Multi-category sort. Required: instruction, categories[{label, items[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: prompt. Optional: min_words, model_answer, evaluation_criteria[]
- **reading**: Required: passage, questions[]
- **source-evaluation**: Required: source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A1.4+ (Module 24/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-adjectives
- **fill-in** — Який? Яка? Яке?: Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Match nouns to correct adjective forms

### Pattern: general-reading
- **true-false** — Правда чи ні?: Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Answer questions about a text passage


**Use these patterns.** If the pattern library recommends `divide-words` for a syllable module, generate a `divide-words` exercise. If it recommends `group-sort` for gender, generate a `group-sort`. The patterns encode how Ukrainian teachers actually test these concepts.

---

## Quality Rules

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Every activity MUST have at least 6 items.** Quiz = 6+ questions. Fill-in = 6+ sentences. Match-up = 6+ pairs. True-false = 6+ statements. Group-sort = 6+ items per group minimum. Anagram = 6+ words.
- If you can't think of 6 items, add more examples from the module's vocabulary and content. NEVER submit an activity with fewer than 6 items.
- **3-5 options per quiz/fill-in question** — enough to prevent guessing, not so many to overwhelm.

**Instructions match learner level:**
1. **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
2. **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
3. **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
4. **A2+:** Instructions in Ukrainian.
5. **B1+:** Full Ukrainian, no English.

**Other rules:**
6. **No duplicate options** — each option in a quiz item must be unique
7. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
8. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
9. **Min 6 pairs for match-up** — to prevent trivial elimination
10. **Explanations for true-false and error-correction** — help the learner understand WHY
11. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

---

## Verification Tools (MCP)

Use these tools to verify your exercise content:



---

## Live Verification Tools (MCP)

You have access to RAG-powered MCP tools to verify Ukrainian language constructs **live as you write**. The research phase is already complete; use these tools strictly for targeted verification to ensure zero Russianisms, accurate grammar, and authentic usage.

**Core Tools:**
- `mcp__rag__verify_words` / `mcp__rag__verify_word` / `mcp__rag__verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp__rag__search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp__rag__search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp__rag__query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp__rag__query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp__rag__search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp__rag__query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp__rag__search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp__rag__search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp__rag__search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp__rag__search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp__rag__translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp__rag__query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp__rag__query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp__rag__query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp__rag__search_style_guide` first (it knows calques). Then `mcp__rag__query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp__rag__verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp__rag__query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp__rag__verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp__rag__search_idioms` for Ukrainian expressions, `mcp__rag__search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp__rag__query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp__rag__query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp__rag__verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp__rag__verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp__rag__verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp__rag__query_pravopys` or `mcp__rag__search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp__rag__verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 10-20 tool calls per module** (was 8-15; mandatory checks added).

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
