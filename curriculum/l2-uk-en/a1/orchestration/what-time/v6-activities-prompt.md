<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/what-time.yaml` file for module **22: What Time?** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-clock-matching -->`
- `<!-- INJECT_ACTIVITY: match-up-digits -->`
- `<!-- INJECT_ACTIVITY: fill-in-o-kotrii -->`
- `<!-- INJECT_ACTIVITY: quiz-time-of-day -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Котра година? Match clock faces to spoken time.
  items: 8
  type: quiz
- focus: 'О котрій? Complete: Я снідаю о ___. (восьмій)'
  items: 8
  type: fill-in
- focus: 'Match times: 7:00 ↔ сьома, 9:00 ↔ дев''ята'
  items: 6
  type: match-up
- focus: Ранку, дня, or вечора? Choose the right time of day.
  items: 6
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- четверта, п'ята, шоста (4th, 5th, 6th)
- сьома, восьма, дев'ята (7th, 8th, 9th)
- десята, одинадцята, дванадцята (10th, 11th, 12th)
- пів (half)
- чверть (quarter)
- опівдні (at noon)
required:
- година (hour, f)
- котра (which — feminine, for time)
- перша, друга, третя (1st, 2nd, 3rd — feminine ordinals)
- ранок (morning, m)
- вечір (evening, m)
- день (day, m)
- ніч (night, f)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги

In Ukrainian, we talk about time using two main questions. We use one to ask for the current time, and another to schedule an event. A typical telephone conversation between colleagues illustrates how these questions function when people coordinate their schedules and find a time to meet.

> **Марина:** Привіт, Олексію! **Котра година**? *(Hi, Oleksiy! What time is it?)*
> **Олексій:** Привіт! **Десята**. *(Hi! Ten o'clock.)*
> **Марина:** **О котрій** ти **працюєш**? *(At what time do you work?)*
> **Олексій:** **О дев'ятій**. А ти? *(At nine. And you?)*
> **Марина:** Я працюю **о десятій**. *(I work at ten.)*
> **Олексій:** **Добре**, **тоді** **о першій**? *(Good, then at one?)*
> **Марина:** Так! *(Yes!)*

The specific communicative functions of these questions show a clear division. The phrase **котра година** identifies the current time on the clock, much like asking for a name in an ordered sequence. Marina wants to know the exact hour right now. On the other hand, the question **о котрій** asks for a specific point on a timeline. Speakers use this when scheduling an event or an action. You should contrast the English phrases "At what time?" versus "What time is it?". While English uses the noun "time" for both concepts, Ukrainian relies on two distinct structures to differentiate between identifying the current moment and setting an appointment.

A discussion about daily schedules between two university students shows how time phrases work with familiar verbs. This scenario integrates verbs from your previous vocabulary, such as **снідати** (to eat breakfast), **обідати** (to eat lunch), **вечеряти** (to eat dinner), and **відпочивати** (to rest), directly with these new time chunks.

> **Студент А:** **Коли** ти снідаєш? *(When do you eat breakfast?)*
> **Студент Б:** **О восьмій ранку**. *(At eight in the morning.)*
> **Студент А:** А обідаєш? *(And eat lunch?)*
> **Студент Б:** **О першій**. Вечеряю **о сьомій**. *(At one. I eat dinner at seven.)*

Here, the students use the question word **коли** (when) interchangeably with scheduling questions. The answers form neat, fixed chunks that specify exactly when each routine action takes place during the day.

## Котра година?

When you want to know the current time, the standard and natural question to ask a Ukrainian speaker is **Котра година?**. The word **котра** means "which" specifically for an ordered sequence, and it is a feminine word. We use this instead of **яка** (what kind of) or **скільки** (how much). You are literally asking "Which hour is it?" in a sequence of twenty-four hours. You must avoid the common errors **який зараз час** (what kind of time is it now) or **скільки годин** (how many hours), as these do not sound natural to a native speaker.

To answer this question for the full hours from one to twelve, we use feminine ordinal numbers. Following the native pedagogical approach shown in the Zakhariichuk Grade 4 textbook, because the word **година** (hour) is feminine, the numbers must agree with it. You simply list the hour as the "first," "second," or "third" hour. Here are the core forms: **перша** (1:00), **друга** (2:00), **третя** (3:00), **четверта** (4:00), **п'ята** (5:00), **шоста** (6:00), **сьома** (7:00), **восьма** (8:00), **дев'ята** (9:00), **десята** (10:00), **одинадцята** (11:00), and **дванадцята** (12:00). You must contrast these sequence words with regular cardinal numbers like **один** (one) or **два** (two), which are never used to state the hour.

Telling half-hours in Ukrainian relies on a specific structural pattern using the word **пів** (half). We use the phrase **пів на** (half towards) followed by the ordinal number for the next hour. The ordinal number takes the accusative case, ending in a "у" or "ю" sound. You must focus on the mental concept of moving "half towards the next hour". For example, 1:30 is **пів на другу** (literally "half to the second"), 6:30 is **пів на сьому** (half to the seventh), and 11:30 is **пів на дванадцяту** (half to the twelfth). You should remember that saying something like "пів восьмої" is a direct mistake.

For now, you only need to recognize quarters, using the word **чверть** (quarter). You will hear **чверть на** (a quarter past) and **за чверть** (a quarter to). For example, 2:15 is **чверть на третю** (a quarter onto the third) and 2:45 is **за чверть третя** (in a quarter, the third). You must warn against using the word "без" (without) for time, which is a common Russianism and incorrect in standard Ukrainian.

<!-- INJECT_ACTIVITY: quiz-clock-matching -->
<!-- INJECT_ACTIVITY: match-up-digits -->

## О котрій?

When you need to talk about scheduling an event, you ask **О котрій годині?**. This introduces the preposition **о** or **об** (at). The rule for choosing between them is simple: use **об** before vowels to make the pronunciation smooth, like in the phrase **об одинадцятій**, and use **о** before consonants. You must explicitly forbid using the prepositions "в" or "у" for time expressions, as this is a very common Russianism that Ukrainian speakers avoid.

The answers to this scheduling question are locative time chunks. You should learn to treat these as fixed vocabulary units right now. They combine the preposition with the locative case ending for the hour. The complete list of chunks is: **о першій**, **о другій**, **о третій**, **о четвертій**, **о п'ятій**, **о шостій**, **о сьомій**, **о восьмій**, **о дев'ятій**, **о десятій**, **об одинадцятій**, and **о дванадцятій**. Memorizing these phrases as whole pieces will make speaking about your daily plans much easier and much more natural in conversation without needing to think about complex grammar rules.

To be more precise, you can refine your time expressions with time of day words. The base words are **ранок** (morning, m), **день** (day, m), **вечір** (evening, m), and **ніч** (night, f). Ukrainian uses their genitive forms as markers to specify the part of the day: **ранку** (of the morning), **дня** (of the day or afternoon), **вечора** (of the evening), and **ночі** (of the night). You add these directly after the hour chunk. For examples, you can say **о сьомій ранку** (at 7 AM), **о третій дня** (at 3 PM), or **о десятій вечора** (at 10 PM). This is how speakers distinguish morning and afternoon clearly.

There are also special time markers for noon and midnight. You can learn **опівдні** (at noon) and **опівночі** (at midnight) as single-word vocabulary chunks. When talking about the middle of the day, you have a choice: you can use the full phrase **о дванадцятій дня** (at twelve of the day), or you can simply use the single word **опівдні** to mean exactly the same thing. You will also frequently hear the words **зараз** (now) and **скоро** (soon) when people discuss their immediate plans or describe events that are happening very shortly.

<!-- INJECT_ACTIVITY: fill-in-o-kotrii -->
<!-- INJECT_ACTIVITY: quiz-time-of-day -->

## Підсумок — Summary

This summary table helps you contrast the question structures and the correct answer structures for telling time.

| Question | Ukrainian Answer | English Meaning |
| :--- | :--- | :--- |
| **Котра година?** | **Десята.** | What time? — Ten o'clock. |
| **О котрій годині?** | **О десятій.** | At what time? — At ten. |
| **Котра година?** | **Пів на другу.** | What time? — 1:30. |
| **О котрій годині?** | **О пів на другу.** | At what time? — At 1:30. |

Remember the common pitfalls: there is no "без" for minutes, there is no "в" for scheduling hours, and you must never use basic cardinal numbers to identify the hour.

Use this self-check checklist to verify your understanding of the material before you move on to the next module. Read each point carefully and try to answer out loud.

*   Can you say what time it is right now? Answer the question: **Котра зараз година?**
*   Can you state exactly what time you wake up in the morning? Try to answer: **О котрій ти прокидаєшся?**
*   Can you say the phrase "half past four" in Ukrainian? Ensure you use the correct pattern: **Пів на п'яту.**
*   Do you know when you must use the preposition **об** instead of the standard **о**? You use it before vowels for smoother pronunciation.

For your final writing task, you should create a simple three-sentence schedule describing your own typical day. This will help you practice combining verbs with the time chunks you have just learned. Review the use of ordinal forms and prepositions as you write.

Here is a model example to guide you:
*   **Я прокидаюся о сьомій ранку.** (I wake up at seven in the morning.)
*   **Я обідаю о першій дня.** (I eat lunch at one in the afternoon.)
*   **Я вечеряю о восьмій вечора.** (I eat dinner at eight in the evening.)

Try writing three similar sentences using your own daily routine and time expressions!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: what-time
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

**Level: A1.4+ (Module 22/55) — BEGINNER**

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

### Pattern: grammar-possession [§4.2.1.4, §4.2.2]
**Присвійність** (Possession)
- **fill-in** — У мене є...: Структура «У мене/тебе/нього є...» — як українська виражає володіння / Structure «У мене/тебе/нього є...» — how Ukrainian expresses possession
  - Instruction: *Вставте правильне слово*
- **fill-in** — Мій, твій, наш...: Обрати присвійний займенник, що узгоджується з родом та числом іменника / Choose possessive pronoun matching noun gender and number
  - Instruction: *Вставте правильну форму*
- **match-up** — Чий? Чия? Чиє?: Зіставити присвійний займенник з іменником за родом / Match possessive pronoun to noun by gender
  - Instruction: *З'єднайте*
- **quiz** — У кого є?: Визначити, хто має щось, за контекстом речення / Determine who has something based on sentence context
**Anti-patterns (DO NOT generate):**
- ❌ translate: «У мене є» — унікальна українська структура. Переклад з англ. «I have» маскує різницю

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
