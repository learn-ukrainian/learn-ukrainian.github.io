<!-- version: 1.1.0 | updated: 2026-03-31 -->
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

- `<!-- INJECT_ACTIVITY: match-place-activity -->`
- `<!-- INJECT_ACTIVITY: quiz-preposition-v-na -->`
- `<!-- INJECT_ACTIVITY: fill-in-describe-city -->`
- `<!-- INJECT_ACTIVITY: quiz-situational-place -->`

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

Imagine you are sitting with a Ukrainian friend. Alina is drawing a map of her neighborhood in the Ukrainian capital, Kyiv. She calls this local space **мій район у Києві** (my neighborhood in Kyiv). Being able to define your physical space and understand where things are located is a vital survival skill in any city. 

Read how Ukrainians talk about places and ask for simple directions.

> **Ігор:** Вибачте, будь ласка. Де тут аптека? *(Excuse me, please. Where is the pharmacy here?)*
> **Аліна:** Аптека на вулиці Шевченка. *(The pharmacy is on Shevchenko street.)*
> **Ігор:** Дякую. А де бібліотека? *(Thank you. And where is the library?)*
> **Аліна:** Бібліотека у центрі. *(The library is in the center.)*
> **Ігор:** Це далеко? *(Is this far?)*
> **Аліна:** Ні, вона біля парку. *(No, it is near the park.)*
> **Ігор:** Дуже дякую! *(Thank you very much!)*

Notice the polite phrase **Вибачте, будь ласка** (Excuse me, please). This is exactly how you get a stranger's attention on the street politely. The question **Де тут...** (Where here is...) is the most efficient way to ask for directions without needing complex grammar.

Alina describes her immediate neighborhood to Igor using the existence word **є** (there is/are) and the preposition **біля** (near/next to).

> **Ігор:** Що є біля твого дому? *(What is near your house?)*
> **Аліна:** Біля дому є магазин і кафе. *(Near the house there is a shop and a cafe.)*
> **Ігор:** А школа? Школа близько? *(And the school? Is the school near?)*
> **Аліна:** Ні, школа далеко, у центрі міста. *(No, the school is far, in the city center.)*

The word **є** acts like the English "there is" or "there are". Ukrainians use it to state that a place exists in a certain location. You will use this small word frequently when describing your own city.

## Місця в місті (City Places)

To navigate a Ukrainian city, you need foundational vocabulary. We group these city places by grammatical gender to help you remember their forms. Grouping vocabulary by gender makes it easier to predict case endings later.

Masculine places end in a consonant:
*   **магазин** (shop)
*   **супермаркет** (supermarket)
*   **банк** (bank)
*   **готель** (hotel)
*   **вокзал** (train station)
*   **музей** (museum)
*   **театр** (theater)

Feminine places end in -а or -я:
*   **аптека** (pharmacy)
*   **бібліотека** (library)
*   **лікарня** (hospital)
*   **пошта** (post office)
*   **церква** (church)
*   **школа** (school)

Neuter places end in -о, -е, or -я:
*   **кафе** (cafe)
*   **кінотеатр** / **кіно** (cinema)
*   **озеро** (lake)

When you answer the question **Де?** (Where?), you use the Locative case. For city buildings, you must choose between the prepositions **в/у** (in) and **на** (on). Use **в/у** for standard enclosed spaces. 

*   **Я в аптеці.** (I am in the pharmacy.)
*   **Ми у банку.** (We are in the bank.)
*   **Брат в готелі.** (Brother is in the hotel.)
*   **Сестра у музеї.** (Sister is in the museum.)
*   **Студенти у бібліотеці.** (Students are in the library.)

Use the preposition **на** for open concepts, public platforms, or wide spaces. 

*   **Я на пошті.** (I am at the post office.)
*   **Він на вокзалі.** (He is at the train station.)
*   **Ми на стадіоні.** (We are at the stadium.)
*   **Люди на площі.** (People are on the square.)

:::note
**Чергування** (Alternation)
Notice how words ending in **-ка** change in the Locative case: **аптека** becomes **в аптеці**, and **бібліотека** becomes **у бібліотеці**. The consonant **к** changes to **ц** before the **-і** ending. This makes the word easier to pronounce.
:::

Combine these places with action verbs to describe what people do there. This provides practical context for your new vocabulary.

*   **Я купую ліки в аптеці.** (I buy medicine in the pharmacy.)
*   **Ми читаємо книги у бібліотеці.** (We read books in the library.)
*   **Вони дивляться фільм у кінотеатрі.** (They watch a film in the cinema.)
*   **Мама купує продукти у магазині.** (Mom buys groceries in the shop.)
*   **Тато обідає у ресторані.** (Dad has lunch in the restaurant.)
*   **Брат працює в офісі.** (Brother works in the office.)
*   **Сестра відпочиває у парку.** (Sister rests in the park.)

<!-- INJECT_ACTIVITY: match-place-activity -->

<!-- INJECT_ACTIVITY: quiz-preposition-v-na -->

Transportation hubs are critical city infrastructure. You need specific vocabulary for different types of travel. 

*   **вокзал** (train station)
*   **автовокзал** (bus station)
*   **аеропорт** (airport)
*   **зупинка** (bus stop)

In Ukraine, the word **вокзал** by default implies the main railway station. If you need a bus, you must specifically ask for the **автовокзал**. You wait for local city transport at a **зупинка**.

*   **Автобус на зупинці.** (The bus is at the stop.)
*   **Поїзд на вокзалі.** (The train is at the station.)

## Де це? (Where Is It?)

To explain where something is, you need relative distance adverbs. The most basic are **тут** (here) and **там** (there). For distance, use **близько** (near/close) and **далеко** (far). 

Notice how Ukrainians use these words in contrastive examples.

*   **Магазин тут, а школа далеко.** (The shop is here, but the school is far.)
*   **Центр близько, а вокзал далеко.** (The center is near, but the station is far.)
*   **Аптека там.** (The pharmacy is there.)
*   **Готель тут.** (The hotel is here.)

When you want to say that something is *near something else*, use the preposition **біля** (near/next to). This preposition requires the Genitive case. For now, learn these common locations as functional chunks.

*   **біля дому** (near the house)
*   **біля парку** (near the park)
*   **біля університету** (near the university)
*   **біля метро** (near the metro)

You use **біля** to describe physical proximity between two objects. It acts as a bridge between the object and its location.

*   **Кафе біля парку.** (The cafe is near the park.)
*   **Лікарня біля метро.** (The hospital is near the metro.)
*   **Аптека біля банку.** (The pharmacy is near the bank.)

To describe an entire neighborhood or city, combine the existence word **є** (there is/are) with your vocabulary and numbers. 

*   **У моєму місті є великий парк і два музеї.** (In my city there is a big park and two museums.)
*   **Тут є один стадіон.** (There is one stadium here.)
*   **Бібліотека біля університету.** (The library is near the university.)
*   **Магазин тут, біля дому.** (The shop is here, near the house.)

This structure allows you to build complex descriptions using simple grammar. You state the location, use **є**, and then name the place.

<!-- INJECT_ACTIVITY: fill-in-describe-city -->

<!-- INJECT_ACTIVITY: quiz-situational-place -->

Finally, here are some specific location markers for precise navigation. 

*   **на розі** (on the corner)
*   **у центрі** (in the center)
*   **поруч** (nearby)

The word **поруч** acts similarly to **близько**, but it often emphasizes immediate side-by-side proximity. You can pair it with the preposition **з** to say "next to something".

*   **Аптека на розі вулиці.** (The pharmacy is on the corner of the street.)
*   **Ресторан у центрі міста.** (The restaurant is in the center of the city.)
*   **Музей поруч з готелем.** (The museum is next to the hotel.)

:::tip
**Далеко чи близько?**
When asking a yes/no question in Ukrainian, you do not need auxiliary words like "is it" or "do you". Just raise your intonation at the end of the sentence: **Це далеко?** (Is this far?).
:::

## Підсумок — Summary

Review the city vocabulary with their required Locative prepositions. Mastery of these patterns is essential for urban navigation.

Use **В/У** for these enclosed spaces:
*   **в аптеці** (in the pharmacy)
*   **у бібліотеці** (in the library)
*   **у банку** (in the bank)
*   **в готелі** (in the hotel)
*   **у магазині** (in the shop)
*   **у музеї** (in the museum)
*   **у ресторані** (in the restaurant)
*   **у лікарні** (in the hospital)
*   **у школі** (in the school)
*   **в університеті** (in the university)
*   **у кафе** (in the cafe)

Use **НА** for these open areas and transport hubs:
*   **на пошті** (at the post office)
*   **на вокзалі** (at the train station)
*   **на стадіоні** (at the stadium)
*   **на зупинці** (at the bus stop)
*   **на площі** (on the square)

To orient yourself, use the distance words **тут** (here), **там** (there), **далеко** (far), and **близько** (near). 

Remember the critical difference between **близько** and **біля**. You use the adverb **близько** to state a general fact: **Магазин близько.** (The shop is near). You use the preposition **біля** to connect two nouns and show physical proximity: **Магазин біля парку.** (The shop is near the park). Always pair **біля** with a noun in the Genitive case.

Practice your new skills by answering these self-check questions aloud.

*   **Де ви живете?** (Where do you live?)
*   **Що є біля вашого дому?** (What is near your house?)
*   **Де ви купуєте ліки?** (Where do you buy medicine?)
*   **Центр міста далеко чи близько?** (Is the city center far or near?)
*   **Які музеї є у вашому місті?** (What museums are in your city?)

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

  - type: order
    instruction: "Розставте речення в правильному порядку"
    items:                         # Lines displayed SHUFFLED to the learner
      - "— Служба порятунку, слухаю вас."
      - "— Допоможіть! Тут пожежа!"
      - "— Де ви?"
    correct_order: [0, 1, 2]       # TOP-LEVEL field, zero-based indices into items[]

  - type: unjumble
    instruction: "Складіть правильне речення зі слів"
    items:
      - words: ["швидку!", "Викличте"]            # Jumbled words
        correct_order: ["Викличте", "швидку!"]    # Words as STRINGS in correct order (NOT integers!)
      - words: ["потрібен", "Мені", "лікар."]
        correct_order: ["Мені", "потрібен", "лікар."]
        hint: "Dative + потрібен + noun"

  - type: error-correction
    instruction: "Знайдіть і виправте помилку"
    items:
      - sentence: "Мені потрібна лікар."
        error: "потрібна"
        correction: "потрібен"
        error_type: "word"           # MUST be one of: "word", "phrase", "register", "construction"
        options: ["потрібен", "потрібне", "потрібно"]
        explanation: "Лікар is masculine, so потрібен."
```

---

## Activity Type Reference

**CRITICAL RULE: EVERY single activity object MUST include an `id` field (a unique string like "quiz-grammar", "match-up-vocab"). Do NOT generate an activity without an `id`.**

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: id, instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: id, instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: id, instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: id, instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: id, instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: id, instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: id, instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: id, instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: id, examples[], prompt
- **classify**: Multi-category sort. Required: id, instruction, categories[{label, items[]}]

### Ukrainian pedagogy types (A1 phonetics/syllables):
- **divide-words**: Interactive syllable division. Required: id, instruction, items[{word, answer}]. Optional: hint. Example: word: "молоко", answer: "мо-ло-ко"
- **count-syllables**: Count syllables in a word. Required: id, items[{word, correct}]. Optional: instruction, maxCount, translation. Example: word: "яблуко", correct: 3
- **pick-syllables**: Select syllables matching criteria. Required: id, syllables[], correctIndices[], category. Example: syllables: ["ка", "май", "ре"], correctIndices: [1], category: "закриті"
- **odd-one-out**: Find the word that doesn't belong. Required: id, items[{words[], correct, explanation}]. `correct` is 0-based index. Example: words: ["кіт", "пес", "молоко"], correct: 2, explanation: "молоко — 3 syllables, rest have 1"
- **image-to-letter**: See image/emoji, identify letter. Required: id, instruction, items[{image, letter}]. Optional: options[]
- **letter-grid**: Letter reference grid. Required: id, letters[{upper, lower}]. Optional: name, emoji, key_word, sound_type
- **watch-and-repeat**: Watch video, repeat pronunciation. Required: id, items[{video}]. Optional: letter, word, note
- **phrase-table**: Grouped phrases for communication patterns. Required: id, groups[{label, phrases[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: id, prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Required: id, passage, questions[]
- **source-evaluation**: Required: id, source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A1.4+ (Module 30/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-pronouns [§4.2.1.4, §4.2.2]
**Особові займенники** (Personal pronouns)
- **match-up** — Займенник → дієслово: Зіставити особовий займенник із правильною формою дієслова — зв'язок займенника з дієвідмінюванням / Match personal pronoun with correct verb form — linking pronouns to conjugation
  - Instruction: *З'єднайте займенник із дієсловом*
- **fill-in** — Вставте займенник: Обрати правильний займенник за контекстом речення / Choose the correct pronoun based on sentence context
  - Instruction: *Вставте правильний займенник*
- **group-sort** — Однина чи множина?: Розподілити займенники на однину та множину / Sort pronouns into singular and plural
  - Instruction: *Розподіліть*
- **quiz** — Ти чи Ви?: Обрати правильну форму звертання — неформальне (ти) чи ввічливе (Ви) / Choose correct address form — informal (ти) vs polite (Ви)
**Anti-patterns (DO NOT generate):**
- ❌ translate: Займенники — про зв'язок з дієсловом, а не переклад

### Pattern: general-reading [§1 (Speech activities — reading)]
**Розуміння тексту** (Reading comprehension)
- **true-false** — Правда чи ні?: Перевірити розуміння тексту або діалогу / Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Відповісти на запитання за текстом / Answer questions about a text passage


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Default minimum: 6 items per activity.** Quiz = 6+, fill-in = 6+, match-up = 6+ pairs, true-false = 6+, anagram = 6+, error-correction = 6+, translate = 6+, divide-words = 6+, count-syllables = 6+, odd-one-out = 6+.
- **Lower minimums for specific types:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items.
- If you can't think of enough items, add more examples from the module's vocabulary and content.
- **Exactly 4 options per quiz question at A2+** — enough to prevent guessing, not so many to overwhelm. A1 allows 3-4.
- **BINARY CONCEPTS (e.g., НВ/ДВ, masculine/feminine, true/false):** Do NOT use `quiz` with only 2 options — use `true-false` (for statement evaluation) or `group-sort` (for categorization) instead. Quiz type requires 4 options at A2+.

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
- `mcp_rag_verify_words` / `mcp_rag_verify_word` / `mcp_rag_verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp_rag_search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp_rag_search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp_rag_query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp_rag_query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp_rag_search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp_rag_query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp_rag_search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp_rag_search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp_rag_search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp_rag_search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp_rag_translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp_rag_query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp_rag_query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp_rag_search_style_guide` first (it knows calques). Then `mcp_rag_query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp_rag_verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp_rag_query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp_rag_verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp_rag_search_idioms` for Ukrainian expressions, `mcp_rag_search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp_rag_query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp_rag_query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp_rag_verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp_rag_verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp_rag_verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp_rag_query_pravopys` or `mcp_rag_search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp_rag_verify_words` with 5-15 words at once.
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
