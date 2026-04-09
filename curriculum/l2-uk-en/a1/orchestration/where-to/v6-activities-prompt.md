<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/where-to.yaml` file for module **31: Where To?** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-accusative-places -->`
- `<!-- INJECT_ACTIVITY: quiz-de-vs-kudy -->`
- `<!-- INJECT_ACTIVITY: group-sort-locative-accusative -->`
- `<!-- INJECT_ACTIVITY: quiz-vs -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Де or Куди? Choose the right question for each sentence.
  items: 8
  type: quiz
- focus: 'Complete: Я йду ___ (школа). Він у ___ (банк).'
  items: 10
  type: fill-in
- focus: 'Sort phrases: Де? (locative) vs Куди? (accusative)'
  items: 10
  type: group-sort
- focus: Йти or їхати? Choose based on distance/transport.
  items: 6
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- магазин → у/в магазин (to the shop)
- бібліотека → у бібліотеку (to the library)
- ресторан → у ресторан (to the restaurant)
- Одеса → в Одесу (to Odesa)
- повертатися → додому (to return home)
required:
- куди (where to)
- йти (to go on foot)
- їхати (to go by transport)
- школа → у школу (to school)
- робота → на роботу (to work)
- банк → у банк (to the bank)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

It is a busy Saturday morning in the bustling city center. Oksana and Stepan are standing on the street corner, holding their lists of weekend errands. They need to visit several different places before finally meeting up later in the afternoon. In Ukrainian, when you are talking about going to a specific destination, you must answer the essential question **куди** (where to).

Listen to their conversation as they figure out their immediate plans and split up to run their respective errands. Pay close attention to how they use the specific question word **куди** (where to) and the prepositions **в** (in/to) and **на** (on/to) to indicate their direction of travel.

> **Степан:** Привіт! **Куди ти йдеш?** *(Hi! Where are you going?)*
> **Оксана:** Привіт! **Я йду в банк.** А ти? *(Hi! I am going to the bank. And you?)*
> **Степан:** **Я йду на роботу.** *(I am going to work.)*
> **Оксана:** А потім? *(And then?)*
> **Степан:** **Потім іду в магазин.** *(Then I am going to the store.)*
> **Оксана:** **А потім ходімо в кафе!** *(And then let's go to a cafe!)*
> **Степан:** Добре! **Я йду в аптеку.** *(Good! I am going to the pharmacy.)*
> **Оксана:** **А я йду на пошту.** *(And I am going to the post office.)*
> **Степан:** **Тоді до зустрічі!** *(Then see you later!)*
> **Оксана:** **Бувай!** *(Bye!)*

Later that afternoon, they meet up at the local cafe and start discussing their upcoming travel plans for the next weekend. Notice how the verb changes when they talk about taking a train or bus to a different city rather than just walking around town.

> **Оксана:** **Куди ти їдеш у суботу?** *(Where are you traveling on Saturday?)*
> **Степан:** **Я їду у Львів.** *(I am traveling to Lviv.)*
> **Оксана:** Клас! А Олена? *(Cool! And Olena?)*
> **Степан:** **Вона їде в Одесу.** *(She is traveling to Odesa.)*
> **Оксана:** А я нікуди не їду. *(And I am not traveling anywhere.)*
> **Степан:** Чому? *(Why?)*
> **Оксана:** **Я йду в бібліотеку.** *(I am going to the library.)*
> **Степан:** **А в неділю?** *(And on Sunday?)*
> **Оксана:** **У неділю я йду в парк.** *(On Sunday I am going to the park.)*

:::note
**Two "Wheres"**
Did you notice how the nouns at the end of their sentences looked slightly different than usual? When Oksana says «**Я йду на пошту**» (I am going to the post office) or «**Я йду в банк**» (I am going to the bank), she is using a specific grammatical form. In English, the word "where" covers both your current location and your future destination. Ukrainian strictly separates these concepts. Asking **куди** (where to) triggers a specific grammatical change that shows movement toward a target.
:::

## Куди? Знахідний відмінок (Where To? Accusative)

In Ukrainian primary schools, Grade 4 students learn to identify cases using "helper words" to ask the right question. For the Accusative case, known as **знахідний відмінок** (accusative case), the helper method is **бачу — кого? що?** (I see — whom? what?). When we talk about inanimate places and destinations, we use the question **що?** (what?). When combined with motion verbs and prepositions like **в/у** or **на**, the Accusative case indicates **куди** (where to) or motion toward a place.

:::tip
**The "No-Change" Rule**
For inanimate masculine nouns and all neuter nouns, the Accusative form is identical to the basic Nominative dictionary form. You simply add the preposition **в/у** (in/into) or **на** (on/onto) before the noun. The noun itself does not change its ending at all.
:::

*   банк → у банк (to the bank)
*   магазин → у магазин (to the store)
*   парк → у парк (to the park)
*   кафе → у кафе (to the cafe)
*   місто → у місто (to the city)

Feminine nouns, however, undergo a highly visible and consistent change. If a feminine noun ends in **-а** or **-я** in its dictionary form, that ending must shift to **-у** or **-ю** in the Accusative case. This small vowel shift is the most frequent signal that you are talking about a destination rather than a static location.

*   школа → у школу (to school)
*   робота → на роботу (to work)
*   бібліотека → у бібліотеку (to the library)
*   вулиця → на вулицю (onto the street)
*   аптека → в аптеку (to the pharmacy)
*   пошта → на пошту (to the post office)
*   країна → в країну (to the country)
*   площа → на площу (onto the square)

This rule for direction applies perfectly to countries and cities as well. Inanimate masculine cities like Kyiv or Lviv will not change their form, while feminine cities will change their final vowel. You will say **в Одесу** (to Odesa). Most importantly, the sovereign nation of Ukraine is a feminine noun ending in **-а**. When expressing travel to Ukraine, you must always use the preposition **в** with the Accusative case ending: **в Україну** (to Ukraine). Never use the preposition **на** for the country of Ukraine.

<!-- INJECT_ACTIVITY: fill-in-accusative-places -->

## Де чи куди? (Where or Where To?)

The most critical habit to build is separating static location from dynamic direction. English conflates these by using "where" and "in" or "at" for both situations. Ukrainian demands a strict choice depending on the intent of the verb. If your verb shows static existence, you must ask **де?** (where?) and use the Locative case. If your verb shows movement toward a goal, you must ask **куди?** (where to?) and use the Accusative case, even though the prepositions **в/у** and **на** remain exactly the same.

Compare these two states directly. Notice how the same preposition requires a completely different noun ending based on whether you are simply existing in a place or traveling toward it.

| Place | **Де?** (Static - Locative) | **Куди?** (Motion - Accusative) |
| :--- | :--- | :--- |
| **школа** (school) | **Я в школі.** (I am at school.) | **Я йду у школу.** (I am going to school.) |
| **робота** (work) | **Він на роботі.** (He is at work.) | **Він іде на роботу.** (He is going to work.) |
| **банк** (bank) | **Ми у банку.** (We are in the bank.) | **Ми йдемо у банк.** (We are going to the bank.) |
| **парк** (park) | **Вона у парку.** (She is in the park.) | **Вона йде у парк.** (She is going to the park.) |
| **кафе** (cafe) | **Степан у кафе.** (Stepan is in the cafe.) | **Степан іде у кафе.** (Stepan is going to the cafe.) |
| **аптека** (pharmacy) | **Оксана в аптеці.** (Oksana is in the pharmacy.) | **Оксана йде в аптеку.** (Oksana is going to the pharmacy.) |

To answer the question **куди?** (where to?), you need verbs of motion. Ukrainian distinguishes between moving under your own physical power and moving by using a vehicle. The verb **йти** means "to go on foot" or "to walk". The verb **їхати** means "to go by transport" or "to drive/ride". Both of these verbs trigger the Accusative case for the destination.

*   **Я йду в магазин.** (I am walking to the store.)
*   **Студент іде в університет.** (The student is walking to the university.)
*   **Ми йдемо в ресторан.** (We are walking to the restaurant.)
*   **Вони йдуть у кіно.** (They are walking to the cinema.)
*   **Я їду на вокзал.** (I am driving to the station.)
*   **Ми їдемо в центр.** (We are driving to the center.)
*   **Тарас їде у Київ.** (Taras is traveling to Kyiv.)
*   **Вона їде в аеропорт.** (She is traveling to the airport.)

:::caution
**The Exception: Going Home**
There is one very common destination that breaks the preposition rules entirely: your own home. When expressing movement homeward, Ukrainian uses a special directional adverb: **додому** (homeward / to home). This word has the direction built directly into it, so it never takes a preposition. You must contrast this with the static adverb **вдома** (at home).
:::

*   **Де Іван? Іван вдома.** (Where is Ivan? Ivan is at home.)
*   **Куди йде Іван? Іван іде додому.** (Where is Ivan going? Ivan is going home.)

<!-- INJECT_ACTIVITY: quiz-de-vs-kudy -->
<!-- INJECT_ACTIVITY: group-sort-locative-accusative -->
<!-- INJECT_ACTIVITY: quiz-vs -->

## Підсумок — Summary

The absolute cornerstone of Ukrainian spatial grammar is the strict two-question system. The question **де?** (where?) asks about a static location and requires the Locative case. The question **куди?** (where to?) asks about dynamic direction and requires the Accusative case. When answering **куди?** (where to?), remember the simplest rule: inanimate masculine and neuter nouns look exactly identical to their original dictionary forms. The only time you need to actively change the noun is when it is a feminine noun ending in **-а** or **-я**, which must always shift to **-у** or **-ю**.

**How do I say "I am going to the bank" and "He is going to the park"?**
You say **Я йду у банк** and **Він іде у парк**. Because these are inanimate masculine nouns, they follow the "no-change" rule for the Accusative case. They look completely identical to the Nominative case.

**How do I say "We are going to the library" and "She is going to work"?**
You say **Ми йдемо у бібліотеку** and **Вона іде на роботу**. These are feminine nouns ending in **-а**. To show direction, the **-а** must change to **-у**.

**What is the difference between "Я вдома" and "Я йду додому"?**
The phrase **Я вдома** (I am at home) is static; it means you are already located there. The phrase **Я йду додому** (I am going home) is dynamic; it means you are currently moving in the direction of your home.

**Which case follows verbs of motion like "їхати" and "йти"?**
Verbs of motion show direction toward a target, so they answer the question **куди?** (where to?) and must be followed by the Accusative case.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: where-to
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

**Level: A1.4+ (Module 31/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-cases [§4.2.3.1, §4.2.3.2, §4.2.3.3]
**Відмінки іменників** (Noun cases)
- **fill-in** — Який відмінок?: Вставити іменник у правильній відмінковій формі / Fill in the correct case ending for a noun in context
  - Instruction: *Вставте іменник у правильній формі*
- **quiz** — Визнач відмінок: Визначити, у якому відмінку стоїть виділений іменник / Identify which case a highlighted noun is in
- **group-sort** — Розподіли за відмінками: Розподілити форми іменників за відмінками / Sort noun forms by their case
- **error-correction** — Знайди помилку у відмінку: Знайти неправильне відмінкове закінчення та виправити / Find wrong case ending and correct it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Учні мають ПРОДУКУВАТИ форми, а не тільки розпізнавати. Обов'язково fill-in
- ❌ translate: Англійська не має відмінків — переклад не тестує відмінювання

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
