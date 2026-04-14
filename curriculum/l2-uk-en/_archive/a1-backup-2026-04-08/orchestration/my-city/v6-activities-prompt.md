<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/my-city.yaml` file for module **30: My City** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-prepositions -->`
- `<!-- INJECT_ACTIVITY: match-places-activities -->`
- `<!-- INJECT_ACTIVITY: quiz-where-would-you-go -->`
- `<!-- INJECT_ACTIVITY: fill-in-your-city -->`
- `<!-- INJECT_ACTIVITY: quiz-mixed-review -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Match place to activity: аптека ↔ купувати ліки'
  items: 8
  type: match-up
- focus: В or на? Choose preposition for city places.
  items: 8
  type: quiz
- focus: 'Describe your city: У моєму місті є ___.'
  items: 6
  type: fill-in
- focus: Where would you go? Choose the right place for each situation.
  items: 6
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- лікарня (hospital, f)
- супермаркет (supermarket, m)
- пошта (post office, f)
- музей (museum, m)
- церква (church, f)
- далеко (far)
- близько (near)
- біля (near — + genitive chunk)
required:
- аптека (pharmacy, f)
- бібліотека (library, f)
- магазин (shop, m)
- ресторан (restaurant, m)
- готель (hotel, m)
- вокзал (train station, m)
- тут (here)
- там (there)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

**Аліна** has just moved to a new part of Kyiv. She stops a stranger on the street.

> **Аліна:** Вибачте, де тут аптека? *(Excuse me, where is the pharmacy here?)*
> **Перехожий:** Аптека на вулиці Шевченка, біля парку. *(The pharmacy is on Shevchenko Street, near the park.)*
> **Аліна:** А бібліотека? *(And the library?)*
> **Перехожий:** Бібліотека в центрі міста. *(The library is in the city center.)*
> **Аліна:** Це далеко? *(Is it far?)*
> **Перехожий:** Ні, близько. *(No, it's close.)*
> **Аліна:** Дякую! *(Thank you!)*
> **Перехожий:** Будь ласка! *(You're welcome!)*

Notice the polite register here. **Вибачте** (excuse me) is how you address a stranger on the street — this matches the textbook pattern from Заболотний Grade 6: *Вибачте, ви не скажете, де...* The stranger answers with specific locations: **на вулиці Шевченка** (on Shevchenko Street) uses **на** + locative for streets, and **біля парку** (near the park) pins the pharmacy to a landmark. The reply **в центрі міста** (in the city center) uses **в** + locative. Two location adverbs close the exchange: **далеко** (far) and **близько** (near/close).

Now Аліна is chatting with her friend **Ігор** about their neighborhoods.

> **Ігор:** Що є біля твого дому? *(What's near your house?)*
> **Аліна:** Біля дому є магазин і кафе. *(Near the house there's a shop and a café.)*
> **Ігор:** А лікарня? *(And a hospital?)*
> **Аліна:** Лікарня там, далеко від центру. *(The hospital is over there, far from the center.)*
> **Ігор:** У тебе є стадіон? *(Do you have a stadium nearby?)*
> **Аліна:** Так, стадіон на вулиці Лесі Українки. *(Yes, the stadium is on Lesya Ukrainka Street.)*

This dialogue recycles **є** (there is/are) from earlier modules — now it works with city places. **Біля дому** (near the house) is a fixed chunk with **біля** + genitive. Notice **магазин** (shop) and **кафе** (café) — two essential neighborhood words. The phrase **далеко від центру** (far from the center) pairs the adverb **далеко** with a genitive chunk.

These two dialogues show city vocabulary in action — asking for directions with a stranger, then describing your neighborhood with a friend. Now let's meet all the city vocabulary in full.

Every Ukrainian **місто** (city) has its landmarks: a **ринок** (market), a **площа** (square), a **вокзал** (train station), a **пошта** (post office). Kyiv's most famous street is **Хрещатик** — the main **вулиця** (street) that runs through the heart of the capital. Close by sits **Майдан Незалежності** (Independence Square), the центральна площа that every Ukrainian knows. Lviv has its own iconic **площа Ринок** (Market Square). When Ukrainians give directions, they orient by these landmarks — not by abstract addresses.

## Місця в місті (City Places)

Here are 17 essential city places. Gender matters because locative endings differ — feminine, masculine, and neuter nouns each have their own pattern from M29.

**Feminine (f):**
- **аптека** (pharmacy) · **бібліотека** (library) · **лікарня** (hospital) · **пошта** (post office) · **церква** (church) · **зупинка** (bus stop)

**Masculine (m):**
- **магазин** (shop) · **супермаркет** (supermarket) · **ресторан** (restaurant) · **банк** (bank) · **вокзал** (train station) · **готель** (hotel) · **музей** (museum) · **театр** (theatre) · **кінотеатр** (cinema) · **стадіон** (stadium) · **університет** (university)

**Neuter (n):**
- **кафе** (café)

Two prepositions control where you are. Most places take **в/у** + locative. A small group — transit and service infrastructure — takes **на** + locative. Here are the locative forms:

**В/у + locative:**
- аптека → **в аптеці** · бібліотека → **у бібліотеці** · магазин → **в магазині** · банк → **у банку** · готель → **у готелі** · ресторан → **у ресторані** · музей → **в музеї** · університет → **в університеті** · лікарня → **у лікарні** · кінотеатр → **у кінотеатрі**

**На + locative:**
- пошта → **на пошті** · вокзал → **на вокзалі** · стадіон → **на стадіоні** · зупинка → **на зупинці**

The pattern: **на** is used for transit and service points — **пошта**, **вокзал**, **стадіон**, **зупинка**. Everything else takes **в/у**. This is confirmed by Ukrainian grammar textbooks (Avramenko Grade 11): *прийменник «на» вживають з назвами установ типу пошта, вокзал.*

<!-- INJECT_ACTIVITY: quiz-prepositions -->

Now combine these places with verbs you already know from A1.3. What do you do at each place?

- **Я купую ліки в аптеці.** — I buy medicine at the pharmacy.
- **Я читаю книги у бібліотеці.** — I read books at the library.
- **Я їм піцу в ресторані.** — I eat pizza at the restaurant.
- **Я п'ю каву в кафе.** — I drink coffee at the café.
- **Я надсилаю листи на пошті.** — I send letters at the post office.
- **Я дивлюся фільм у кінотеатрі.** — I watch a film at the cinema.
- **Я відпочиваю в парку.** — I relax in the park.
- **Я чекаю на потяг на вокзалі.** — I wait for a train at the station.

Notice how familiar verbs — **купую**, **читаю**, **їм**, **п'ю** — now appear in locative context. The place tells you *where* the action happens. And **кафе** never changes form: **в кафе**, **біля кафе** — it stays the same in every case, because it is an indeclinable noun.

<!-- INJECT_ACTIVITY: match-places-activities -->

## Де це? (Where Is It?)

Four core adverbs let you describe where anything is. They come in natural pairs:

**Тут** (here) vs **там** (there):
- **Аптека тут.** — The pharmacy is here.
- **Вокзал там.** — The train station is there.

**Далеко** (far) vs **близько** (near):
- **Університет далеко від дому.** — The university is far from home.
- **Магазин близько.** — The shop is nearby.
- **Стадіон далеко.** — The stadium is far.
- **Бібліотека близько від парку.** — The library is near the park.

A useful synonym: **недалеко** means the same as **близько** (confirmed by Заболотний Grade 5 synonyms appendix: *близько, недалеко, поблизу*).

The preposition **біля** always takes the genitive case — but at A1, learn these as memorized chunks, not grammar rules. Just remember: **біля** + a fixed word form.

- **біля парку** — near the park
- **біля дому** — near the house
- **біля університету** — near the university
- **біля вокзалу** — near the station
- **біля кафе** — near the café (кафе never changes!)

Six example sentences:
- **Аптека біля парку.** — The pharmacy is near the park.
- **Музей біля університету.** — The museum is near the university.
- **Зупинка біля вокзалу.** — The bus stop is near the station.
- **Магазин біля мого дому.** — The shop is near my house.
- **Церква біля площі.** — The church is near the square.
- **Готель біля кафе.** — The hotel is near the café.

:::tip
**Кафе** never changes — **біля кафе**, **у кафе**, **це кафе**. It looks the same in every case. This is true for all borrowed words ending in **-е** or **-о**: **метро**, **кіно**, **кафе**.
:::

Three more location phrases for describing your neighborhood:

- **у центрі міста** (in the city center) — **Театр у центрі міста.** The theatre is in the city center.
- **на розі вулиці** (on the corner of the street) — **Аптека на розі вулиці Шевченка.** The pharmacy is on the corner of Shevchenko Street.
- **у нашому районі** (in our neighborhood) — **Бібліотека у нашому районі.** The library is in our neighborhood.

Now describe your whole city using **є** (there is/are). The construction is simple: **У** + place + **є** + what's there.

- **У Києві є метро.** — Kyiv has a metro.
- **У нашому місті є великий парк.** — Our city has a big park.
- **У цьому районі є стадіон і кінотеатр.** — This neighborhood has a stadium and a cinema.

For the negative, use **немає** + genitive: **Біля мого дому немає вокзалу.** (There is no train station near my house.)

<!-- INJECT_ACTIVITY: quiz-where-would-you-go -->

## Підсумок — Summary

Here is your city vocabulary organized by preposition — the most important pattern from this module:

**В/у + locative:**
- аптека → **в аптеці** · бібліотека → **у бібліотеці** · лікарня → **у лікарні** · магазин → **в магазині** · банк → **у банку** · готель → **у готелі** · ресторан → **у ресторані** · музей → **в музеї** · університет → **в університеті** · кінотеатр → **у кінотеатрі**

**На + locative:**
- пошта → **на пошті** · вокзал → **на вокзалі** · стадіон → **на стадіоні** · зупинка → **на зупинці**

**Rule: на** = transit and service infrastructure. Everything else = **в/у**.

Location words at a glance:
- **тут** — here: **Магазин тут.**
- **там** — there: **Вокзал там.**
- **далеко** — far: **Університет далеко.**
- **близько** / **недалеко** — near: **Парк близько.**
- **біля** + gen — next to: **Аптека біля дому.**
- **у центрі** — in the center: **Театр у центрі.**
- **на розі** — on the corner: **Банк на розі.**
- **у районі** — in the neighborhood: **Школа у районі.**

Self-check — answer these questions about your own city:

- **Де ти купуєш ліки?** → В аптеці.
- **Де ти їси?** → У ресторані / у кафе.
- **Де ти читаєш книги?** → У бібліотеці.
- **Де ти чекаєш на потяг?** → На вокзалі.
- **Що є біля твого дому?** → Біля мого дому є … (your answer).
- **Твій університет далеко чи близько?** → (open answer).

<!-- INJECT_ACTIVITY: fill-in-your-city -->

You now know where things are in a city and how to describe your neighborhood. The next module (M31 — Where To?) introduces **куди** — movement *toward* places using the accusative case: **Я іду до бібліотеки. Я їду на вокзал.** The same places, a new question: not **де** (where — location) but **куди** (where to — destination).

<!-- INJECT_ACTIVITY: quiz-mixed-review -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: my-city
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

**Level: A1.4+ (Module 30/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
