<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-time-nature.yaml` file for module **27: Checkpoint: Time and Nature** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-mixed-review -->`
- `<!-- INJECT_ACTIVITY: match-up-logical-logic -->`
- `<!-- INJECT_ACTIVITY: fill-in-routine-sequence -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Mixed review of time, days, and weather chunks
  items:
  - Зустріч {о п'ятій|в п'ятій|у п'ята} годині.
  - Ми йдемо в кіно {у суботу|в суботі|на суботу}.
  - Мій день народження {у січні|в січень|січень}.
  - Сьогодні {іде дощ|іде дощова|дощить} і холодно.
  - Взимку дуже {холодно|спекотно|тепло}.
  - Я прокидаюся о сьомій {ранку|рано|вранці}.
  type: fill-in
- focus: Match the questions to logical answers
  pairs:
  - Котра година? ↔ Десята тридцять.
  - О котрій зустріч? ↔ О першій.
  - Яка сьогодні погода? ↔ Тепло і сонячно.
  - Коли твій день народження? ↔ У жовтні.
  - Що ти робиш у суботу? ↔ Граю у футбол.
  - Як часто ти читаєш? ↔ Кожен день ввечері.
  - Ходімо в парк! ↔ Добре, о котрій?
  - Що ти будеш робити завтра? ↔ Буду працювати.
  type: match-up
- focus: Complete the paragraph describing a day
  items:
  - '{Спочатку|Потім|Нарешті} я прокидаюся і снідаю.'
  - '{Потім|Вранці|Вночі} я йду на роботу.'
  - Я працюю з дев'ятої {до|і|по} п'ятої.
  - '{Після обіду|Вранці|Вночі} я гуляю в парку.'
  - Я гуляю, тому що сьогодні {тепло|холодно|дощ} і сонячно.
  - '{Ввечері|Вдень|Вранці} я вечеряю і слухаю музику.'
  - '{Нарешті|Спочатку|Потім} я лягаю спати о дванадцятій.'
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended: []
required: []


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Що ми знаємо? (What Do We Know?)

You have reached a significant milestone in your Ukrainian journey. The last five modules introduced the foundational vocabulary of daily communication: time, the calendar, weather, and your daily routine. You started by learning to read the clock, moving from numbers to formal time expressions. Then, you expanded your vocabulary to include the days of the week and the months of the year, allowing you to discuss schedules in broader strokes. You discovered how to describe the world outside your window with precise weather expressions and seasonal vocabulary. Finally, you brought all these elements together to narrate your own daily schedule and discuss your hobbies. A checkpoint is an opportunity to pause, reflect, and consolidate these foundational skills before moving forward.

Take a moment to ask yourself a few essential questions about your progress. Can you confidently ask a stranger **Котра година?** (What time is it?) on the street? When scheduling a meeting, can you specify **о п'ятій годині** (at five o'clock)? Do you remember all seven days of the week, starting sequentially from **понеділок** (Monday)? Look outside right now—can you describe the current weather using impersonal constructions like **сонячно** (sunny) or **іде дощ** (it is raining)? Can you talk about what you usually do in the morning, afternoon, and evening? Can you talk about your hobbies, like what you do on the weekend? If you can answer yes to these questions, you have built a solid grammatical and lexical foundation.

:::note
You do not need to memorize every single word perfectly right now. A checkpoint is about recognizing your progress. If you can understand the main ideas and patterns in this review, you are exactly where you need to be!
:::

These tools are absolutely essential for a vibrant social life in any Ukrainian-speaking environment. You need this specific vocabulary to make concrete plans with friends, understand local transport schedules, and simply talk about the world around you. Time and nature are universal topics of conversation. Mastering them allows you to move beyond basic greetings and start participating in real, practical exchanges. Whether you are arranging a coffee date, checking when a museum opens, or deciding if you need an umbrella today, these vocabulary sets work together constantly.

## Читання (Reading Practice)

The following short narrative describes a typical week for a person living and working in Ukraine. It combines time expressions, days of the week, weather vocabulary, and daily routine actions. Reading it aloud helps practice pronunciation, while highlighting how the sentences transition smoothly from one idea to the next.

**Мій робочий тиждень** (My work week)

*   **Сьогодні понеділок.** (Today is Monday.)
*   **Вранці я прокидаюся о сьомій годині.** (In the morning I wake up at seven o'clock.)
*   **Спочатку я снідаю.** (First I eat breakfast.)
*   **Потім я йду на роботу.** (Then I go to work.)
*   **Я завжди працюю з дев'ятої до п'ятої.** (I always work from nine to five.)
*   **У середу ввечері я часто гуляю в парку.** (On Wednesday evening I often walk in the park.)
*   **Зараз весна.** (It is spring now.)
*   **На вулиці дуже тепло і сонячно.** (Outside it is very warm and sunny.)
*   **У суботу я ніколи не працюю.** (On Saturday I never work.)
*   **Взимку я люблю дивитися кіно.** (In winter I like to watch movies.)
*   **Влітку я часто ходжу на річку.** (In summer I often go to the river.)
*   **Нарешті я відпочиваю вдома.** (Finally I rest at home.)

The linguistic structure of this text relies on specific grammatical patterns. Notice the choice of prepositions when talking about time. For days of the week, speakers use the preposition **у** or **в** followed by the accusative case, as seen in **у середу** (on Wednesday) and **у суботу** (on Saturday). However, when we talk about seasons, we do not use a preposition with a noun. Instead, we use a single seasonal adverb like **взимку** (in winter) or **влітку** (in summer). You can also see the sequence words **спочатку** (first), **потім** (then), and **нарешті** (finally) used to create a chronological order of the day's events. These small connective words are what transform a disjointed list of sentences into a natural, flowing narrative. By adding frequency adverbs like **завжди** (always) or **часто** (often), the speaker provides a clear picture of their consistent habits.

## Граматика (Grammar Summary)

Telling time requires understanding the difference between two key questions. When you want to know the current time, you ask **Котра година?** (What time is it?). When you want to know the timing of a specific event, you ask **О котрій годині?** (At what time?). In both cases, Ukrainian uses ordinal numbers in the feminine form to match the feminine noun **година** (hour). 

*   **Котра година?** — What time is it?
*   **Зараз перша година.** — It is now one o'clock.
*   **О котрій зустріч?** — At what time is the meeting?
*   **Зустріч о п'ятій годині.** — The meeting is at five o'clock.

Your calendar vocabulary relies heavily on specific prepositions and case endings. To say that an event happens on a specific day, use **у** or **в** with the accusative case. To say an event happens in a specific month, use the locative case ending. The four seasons operate differently; they function as standalone adverbs without adding any extra prepositions. 

*   **Я працюю у п'ятницю.** — I work on Friday.
*   **Мій день народження у січні.** — My birthday is in January.
*   **Взимку дуже холодно.** — In winter it is very cold.
*   **Навесні гарна погода.** — In spring the weather is beautiful.

:::tip
Remember the Ukrainian euphony rules for **у** and **в**. You should use **у** before words starting with consonants like **в** or **ф**, and before consonant clusters (like **у вівторок** or **у п'ятницю**). You use **в** when it sits between two vowels. This alternation makes your Ukrainian sound smooth and natural.
:::

Describing the weather often involves impersonal constructions. You do not need a subject like "it" in Ukrainian. You simply state the condition using an adverb. For precipitation, use the verb **іде** (goes) combined with the noun. Finally, you can describe how often these weather patterns or your own habits occur using frequency adverbs.

*   **Сьогодні дуже тепло і сонячно.** — Today it is very warm and sunny.
*   **Восени часто іде дощ.** — In autumn it often rains.
*   **Я завжди читаю ввечері.** — I always read in the evening.
*   **Вона ніколи не п'є каву.** — She never drinks coffee.

<!-- INJECT_ACTIVITY: fill-in-mixed-review -->

## Діалог (Connected Dialogue)

These rules apply directly to real-world situations. Two friends, Олена (Olena) and Марко (Marko), are planning a weekend trip to a nearby city. They need to check the weather forecast, agree on a departure time, and decide what activities they will do. They use the present tense and direct invitations to discuss their scheduled plans, which is a very common and natural way to speak in Ukrainian.

> **Марко:** Привіт! Яка завтра погода? *(Hi! What is the weather tomorrow?)*
> **Олена:** Привіт! У суботу тепло і сонячно. *(Hi! On Saturday it is warm and sunny.)*
> **Марко:** Чудово! Ходімо в музей! О котрій? *(Great! Let's go to the museum! At what time?)*
> **Олена:** О дев'ятій ранку. *(At nine in the morning.)*
> **Марко:** Добре. А що ми робимо в неділю? *(Good. And what do we do on Sunday?)*
> **Олена:** У неділю іноді йде дощ. Ходімо в кіно. *(On Sunday it sometimes rains. Let's go to the movies.)*

This dialogue is packed with highly useful communicative chunks. The phrase **Ходімо!** (Let's go!) is a standard invitation. Notice how Olena specifies the exact part of the day by adding **ранку** (of the morning) after the time: **о дев'ятій ранку** (at nine in the morning). You can do the same with **вечора** (of the evening) to clarify your schedule, for example saying **о п'ятій вечора** (at five in the evening). The friends confirm their actions using the present tense, making their planning sound immediate and certain.

:::caution
A common false friend! The word **неділя** (Sunday) refers specifically to the seventh day of the week. Do not confuse it with the word **тиждень** (week), which represents the entire seven-day period. 
:::

There is an important cultural and linguistic distinction to reinforce here. Remember that a work week is **робочий тиждень**, while the day of rest is **неділя**. When Marko and Olena discuss their plans, they clearly separate their Saturday activities from their Sunday expectations based on the weather forecast. 

<!-- INJECT_ACTIVITY: match-up-logical-logic -->
<!-- INJECT_ACTIVITY: fill-in-routine-sequence -->

## Підсумок — Summary

You have reached the end of the Time and Nature phase! This is a major accomplishment that significantly expands your ability to communicate in everyday situations. Here is what you can now do confidently in Ukrainian:

*   Tell time using hours (**Котра година? Перша, друга...**).
*   Use time expressions for appointments (**О котрій? О п'ятій...**).
*   Navigate the calendar: name all 7 days and 12 months with correct prepositions (**у вівторок**, **у березні**).
*   Use seasonal adverbs (**взимку**, **навесні**, **влітку**, **восени**).
*   Describe the weather and state of the environment using impersonal adverbs (**тепло**, **сонячно**, **іде дощ**).
*   Sequence your actions using chronological adverbs like **спочатку**, **потім**, and **нарешті**.
*   Describe your lifestyle with frequency words (**завжди**, **часто**, **іноді**).

Review these points and practice building your own sentences that combine weather, time, and routine. The next phase, A1.5, introduces navigation around the city, giving directions, and using transport. Your knowledge of time and days will be essential to read bus schedules and plan your visits!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-time-nature
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

**Level: A1.4+ (Module 27/55) — BEGINNER**

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
