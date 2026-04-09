<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/linking-ideas.yaml` file for module **44: Linking Ideas** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-conjunction-choice -->`
- `<!-- INJECT_ACTIVITY: group-sort-categories -->`
- `<!-- INJECT_ACTIVITY: fill-in-reason-building -->`
- `<!-- INJECT_ACTIVITY: quiz-conjunction-matching -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Choose: і, а, але, бо — Я хочу ___ не можу. Він працює, ___ вона відпочиває.'
  items: 10
  type: fill-in
- focus: Which conjunction? Я не йду, ___ хворий. (і / а / бо)
  items: 8
  type: quiz
- focus: 'Connect with бо/тому що: Я вчу українську, ___.'
  items: 6
  type: fill-in
- focus: 'Sort: і/та (addition) vs а/але (contrast) vs бо/тому що (reason)'
  items: 10
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- чому (why)
- тому (therefore/that's why)
- також (also)
- теж (also — colloquial)
- або (or)
- чи (or — in questions)
required:
- і (and)
- та (and — synonym of і)
- а (and/but — contrast)
- але (but)
- бо (because)
- тому що (because — longer form)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Two friends are deciding what to order in a local cafe after a long walk through the city. They use basic linking words to explain their choices, contrast their preferences, and make plans together. Notice how these short conjunctions connect simple ideas and give clear reasons for their decisions. Instead of just naming items, they are building a logical, connected conversation.

> **Олена:** Ти хочеш каву чи чай? *(Do you want coffee or tea?)*
> **Марко:** Каву, бо я дуже втомлений. *(Coffee, because I am very tired.)*
> **Олена:** А я хочу чай, але без цукру. *(And I want tea, but without sugar.)*
> **Марко:** Добре. Ходімо в кафе, і я візьму ще тістечко. *(Good. Let's go to the cafe, and I will also take a pastry.)*
> **Олена:** Я теж хочу, але я на дієті! *(I also want one, but I am on a diet!)*

Later that evening, two colleagues catch up on their busy day and discuss why they missed each other's messages earlier. They use linking words to organize the sequence of their actions and explain the exact reasons behind missed connections. In everyday Ukrainian communication, stringing together events and providing quick justifications is a fundamental skill.

> **Антон:** Що ти робив сьогодні? *(What were you doing today?)*
> **Іван:** Я працював, а потім ходив у магазин. *(I worked, and then went to the store.)*
> **Антон:** Я хотів зателефонувати, але ти не відповів. *(I wanted to call, but you did not answer.)*
> **Іван:** Вибач, бо телефон був без звуку. *(Sorry, because the phone was on silent.)*
> **Антон:** Нічого! Завтра я вільний, і ми можемо зустрітися. *(That is nothing! Tomorrow I am free, and we can meet.)*

A married couple is debating where to go for their upcoming summer vacation. They use contrasting words to compare two very different destinations: the Carpathian Mountains and the seaside. This dialogue models how to use adjectives with contrasting conjunctions to weigh pros and cons. You can clearly see how adding a simple linking word changes the entire flow of the debate.

> **Віктор:** Гори гарні, але далеко. *(The mountains are beautiful, but far.)*
> **Марія:** Море тепле, бо зараз літо. *(The sea is warm, because it is summer now.)*
> **Віктор:** Я хочу в гори, а ти — на море. *(I want to go to the mountains, and you want to go to the sea.)*
> **Марія:** Добре. Поїдемо в Карпати, бо там дешевше. *(Fine. Let's go to the Carpathians, because it is cheaper there.)*

## Сполучники (Conjunctions)

To build natural sentences, you need a way to link your thoughts together. The Ukrainian term for this grammatical "glue" is **сполучник** (conjunction), which comes directly from the verb **сполучити** (to connect). These words connect individual items, short phrases, or whole sentences. Without them, communication sounds robotic and completely disconnected. For example, stating **Я люблю каву. Я люблю чай.** (I like coffee. I like tea.) feels very choppy. By adding a simple connecting word, you get a fluid, natural thought: **Я люблю каву і чай.** (I like coffee and tea.) Without a conjunction, you say: **Я хочу піти. Я втомлений.** (I want to go. I am tired.) With a connected thought, you say: **Я хочу піти, бо я втомлений.** (I want to go, because I am tired.)

To add information together, Ukrainian grammar uses **сполучники сурядності** (coordinating conjunctions). These are words that connect equal, balanced parts of a sentence. The most foundational word is **і** (and). Another common word for addition is **та** (and). This is a perfect synonym for **і**, frequently used in both everyday speech and formal writing for variety. When you say **мама і тато** (mom and dad) or **хліб та масло** (bread and butter), the meaning remains exactly the same. You will also see the euphony rule applied: Ukrainians often swap **і** for **й** after a vowel to maintain the melodicity of the language, such as in the phrase **вона й він** (she and he).

* Я читаю і пишу. *(I read and write.)*
* Це стіл і стілець. *(This is a table and a chair.)*

When you want to contrast two ideas or simply switch focus, Ukrainian uses the word **а** (and/but). English speakers often default to using "and" for every situation, but in Ukrainian, if you are comparing two different subjects or highlighting a shift in action, you must use **а**. This is a soft contrast, not a direct contradiction. It smoothly marks a shift in attention. The classic example for learners is **Я люблю каву, а ти?** (I like coffee, and you?) or **Я — студент, а ти — вчитель.** (I am a student, and you are a teacher.)

* Він працює, а вона відпочиває. *(He works, and she rests.)*
* Це не стіл, а стілець. *(This is not a table, but a chair.)*

For a strong contrast, a contradiction, or an unexpected result, use the word **але** (but). This conjunction tells the listener that the second part of the sentence directly opposes the first part. While the word **та** can sometimes mean "but" in specific folk-style contexts (like the saying **малий, та вдалий** meaning small but successful), the word **але** is the absolute A1 standard you should use for clear opposition.

* Суп гарячий, але смачний. *(The soup is hot, but tasty.)*
* Він молодий, але розумний. *(He is young, but smart.)*
* Я хочу піти, але не можу. *(I want to go, but I cannot.)*

<!-- INJECT_ACTIVITY: fill-in-conjunction-choice -->

<!-- INJECT_ACTIVITY: group-sort-categories -->

## Бо і тому що (Because)

Giving reasons is a massive step forward in your ability to communicate. You need to explain *why* you are doing something, *why* you are late, or *why* you prefer one thing over another. Ukrainian has two primary ways to say "because": **бо** and **тому що**. The word **бо** is the absolute workhorse of spoken Ukrainian. It is short, punchy, and incredibly natural. Both are correct. Both are Ukrainian. **бо** is NOT informal or wrong; it is simply the most common way people talk. The phrase **тому що** is longer and serves as the neutral or slightly more formal counterpart, frequently seen in writing or careful speech.

* Я не йду, бо я хворий. *(I am not going, because I am sick.)*
* Я не йду, тому що я хворий. *(I am not going, because I am sick.)*

There is a strict, non-negotiable punctuation rule that you must memorize for writing in Ukrainian: you must always put a comma before these connecting words. English often skips the comma before "because", but Ukrainian punctuation rules require a comma before **а**, **але**, **бо**, and **тому що**. Whenever you introduce a contrast or a reason in writing, you must pause and add that comma. It is a visual signal that the sentence is shifting direction or providing an explanation.

* Ми не гуляємо, тому що йде дощ. *(We are not walking, because it is raining.)*
* Я втомлений, бо багато працював. *(I am tired, because I worked a lot.)*

These conjunctions directly answer the question word **Чому?** (Why?). In English, it can sometimes feel slightly awkward to start a sentence with "Because," but in Ukrainian, this is how Ukrainians explain things. The "Why-Because" loop is the foundation of daily explanation. You hear a question starting with **Чому**, and you immediately fire back with an answer starting with **Бо** or **Тому що**.

* — Чому ти вчиш українську? *(Why are you learning Ukrainian?)*
* — Бо я люблю Україну. *(Because I love Ukraine.)*
* — Чому ти не їси? *(Why are you not eating?)*
* — Тому що я не голодний. *(Because I am not hungry.)*
* — Чому ви тут? *(Why are you here?)*
* — Бо ми чекаємо друга. *(Because we are waiting for a friend.)*

When building these explanatory sentences, English speakers often fall into a syntax trap. They might translate "because interesting" directly into Ukrainian as **бо цікаво**. However, Ukrainian grammar requires a complete structural basis in the second half of the clause. You cannot simply drop the subject. You must provide the full idea.

* Я читаю, бо це цікаво. *(I read, because it is interesting.)*

<!-- INJECT_ACTIVITY: fill-in-reason-building -->

<!-- INJECT_ACTIVITY: quiz-conjunction-matching -->

## Підсумок — Summary

Connecting your thoughts transforms how you sound in Ukrainian. You move away from reciting isolated vocabulary words and begin building real, flowing communication. Reviewing the four key types of linking words makes this process clearer.

For addition, use **і** or its synonym **та**. Both mean "and" and connect equal, balanced ideas without any contradiction. Remember the euphony rule: if the previous word ends in a vowel and the next word begins with a consonant, Ukrainians often swap **і** for **й** to keep the language melodious. 

For soft contrast or shifting focus, use **а** (and/but). This is crucial for comparing two different subjects, like stating what you are doing versus what your friend is doing. It shows a change in direction, not a hard stop.

For strong contrast or opposing ideas, use **але** (but). This introduces limitations, unexpected outcomes, or direct contradictions to what was just stated.

For explaining reasons, use **бо** (the short, spoken "because") or **тому що** (the longer, neutral "because"). Both directly answer the question **Чому?** (Why?).

| Conjunction | Meaning | Example |
| :--- | :--- | :--- |
| **і** / **та** | and | Я їм хліб і п'ю воду. *(I am eating bread and drinking water.)* |
| **а** | and (contrast) | Я читаю, а він пише. *(I am reading, and he is writing.)* |
| **але** | but | Я хочу, але не можу. *(I want to, but I cannot.)* |
| **бо** | because | Я не йду, бо хворий. *(I am not going, because I am sick.)* |
| **тому що** | because | Я не йду, тому що хворий. *(I am not going, because I am sick.)* |

Always remember the "Always Comma" rule: in written Ukrainian, always put a comma before **а**, **але**, **бо**, and **тому що**. You only place a comma before **і** when it connects two entirely separate, full sentences.

Here is a quick self-check. Try to mentally connect these short, choppy sentence pairs using the correct conjunction before you continue your practice. 

* Я люблю каву. Я не люблю чай. *(Try connecting this with **а** or **але**.)*
* Він вдома. Він хворий. *(Try explaining the reason with **бо**.)*
* Вона читає. Він пише. *(Try shifting the focus with **а**.)*
* Сьогодні сонце. Сьогодні холодно. *(Try introducing the contrast with **але**.)*

Building longer, logically connected sentences is the first real step from simply "surviving" in a new language to actually "speaking" it with confidence.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: linking-ideas
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

**Level: A1.4+ (Module 44/55) — BEGINNER**

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
