<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-food-shopping.yaml` file for module **41: Checkpoint: Food and Shopping** (a1).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 8 | 8+ | inline + workbook combined |
| Inline (lesson tab) | 3 | 5 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 5 | 8 | extended practice |
| Items per activity | 10 | — | each activity must have at least 10 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 3 inline activities AND at least 5 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** match-up, quiz, fill-in, true-false, classify, group-sort
- **Inline priority (preferred):** match-up, fill-in, quiz
- **Workbook types:** fill-in, match-up, group-sort, unjumble, quiz, true-false, classify, observe, phrase-table, odd-one-out, anagram
- **Workbook priority (preferred):** fill-in, match-up, group-sort, unjumble, anagram
- **FORBIDDEN at this level:** image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, cloze, error-correction, mark-the-words, translate, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, highlight-morphemes, grammar-identify, select

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 3–5 quick checks after key teaching points. Workbook = 5–8 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: group-sort-accusative -->`
- `<!-- INJECT_ACTIVITY: quiz-accusative-forms -->`
- `<!-- INJECT_ACTIVITY: fill-in-dialogue -->`
- `<!-- INJECT_ACTIVITY: quiz-situational-phrases -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Accusative check: choose correct form for inanimate AND animate nouns'
  items:
  - options:
    - салат
    - салата
    - салату
    question: Я їм ___.
  - options:
    - брата
    - брат
    - брату
    question: Я бачу ___.
  - options:
    - воду
    - вода
    - води
    question: Я п'ю ___.
  - options:
    - Олену
    - Олена
    - Олени
    question: Я знаю ___.
  - options:
    - борщ
    - борща
    - борщу
    question: Я люблю ___.
  - options:
    - друга
    - друг
    - другу
    question: Я чекаю ___.
  - options:
    - хліб
    - хліба
    - хлібу
    question: Я купую ___.
  - options:
    - лікаря
    - лікар
    - лікарю
    question: Я бачу ___.
  - options:
    - піцу
    - піца
    - піци
    question: Я їм ___.
  - options:
    - маму
    - мама
    - мами
    question: Я люблю ___.
  type: quiz
- focus: Complete the cafe + market dialogue with correct forms
  items:
  - — Що ти їш на сніданок? — Я їм {кашу|каша|каші} і п'ю каву.
  - — Потім іду на ринок. Скільки {коштують|коштує|коштувати} помідори?
  - — Тридцять {гривень|гривні|гривня}.
  - — Дайте {кілограм|літр|пляшку} яблук, будь ласка.
  - '— Потім у кафе: {Мені|Я|Меня} борщ і воду, будь ласка.'
  - — Рахунок, будь ласка. Можна {карткою|картка|картки}?
  - — О, я бачу {Олену|Олена|Олени}! Олено, привіт!
  - — Ти знаєш мого {брата|брат|братом}?
  type: fill-in
- focus: 'Sort accusative forms: inanimate (що?) vs animate (кого?)'
  groups:
  - items:
    - борщ
    - хліб
    - сік
    - чай
    - сир
    name: Inanimate (що?)
  - items:
    - брата
    - лікаря
    - сусіда
    - друга
    - вчителя
    name: Animate (кого?)
  type: group-sort
- focus: What do you say? Match shopping/cafe situations to correct phrases
  items:
  - options:
    - Мені каву, будь ласка.
    - Скільки коштує?
    - Тут вільно?
    question: 'You want to order coffee:'
  - options:
    - Скільки коштує?
    - Можна карткою?
    - Що ви рекомендуєте?
    question: 'You ask for the price:'
  - options:
    - Можна карткою?
    - Рахунок, будь ласка.
    - Дорого!
    question: 'You want to pay with a card:'
  - options:
    - Рахунок, будь ласка.
    - Мені борщ.
    - Все було дуже смачно!
    question: 'You ask for the bill:'
  - options:
    - Дайте кілограм яблук.
    - Скільки коштує?
    - Можна меню?
    question: 'You ask for 1 kg of apples:'
  - options:
    - Дорого!
    - Дешево!
    - Нормальна ціна.
    question: 'You think the price is high:'
  - options:
    - Тут вільно?
    - Можна меню?
    - Рахунок, будь ласка.
    question: 'You ask if a seat is free:'
  - options:
    - Все було дуже смачно!
    - Можна карткою?
    - Це гостре?
    question: 'You compliment the food:'
  type: quiz


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

Welcome to the A1.6 Checkpoint! You have reached a major milestone in your Ukrainian language journey. In this module, we are bringing together everything you learned in the last five modules. We will combine your food vocabulary, practical shopping phrases, and the accusative case for both things and people in realistic, everyday scenarios.

This is your opportunity to step back and reflect on how much you can already understand and communicate. Look at the self-check questionnaire below. If you can answer "yes" to these questions, you are ready to confidently navigate a Ukrainian cafe or market!

*   **Словник (Vocabulary):** Can you name ten foods (for example, **хліб** (bread), **яблуко** (apple), **сир** (cheese), **м'ясо** (meat)) and five drinks (for example, **вода** (water), **кава** (coffee), **сік** (juice))?
*   **Їжа (Food):** Can you say what you eat using the accusative case (for example, **Я їм кашу.** (I eat porridge.))?
*   **Кафе (Cafe):** Can you order a meal at a cafe (for example, **Мені борщ, будь ласка.** (Borscht for me, please.))?
*   **Ринок (Market):** Can you ask for prices and buy things at the market (for example, **Скільки коштує? Дайте кілограм...** (How much does it cost? Give me a kilogram...))?
*   **Люди (People):** Can you use the accusative case to talk about people (for example, **Я бачу брата.** (I see a brother.), **Я знаю Олену.** (I know Olena.))?

## Читання (Reading Practice)

Let us put these new skills into practice with a short reading text. Anna is having a very busy day running errands around the city. First, she goes to the local market (**ринок**) to buy some fresh groceries for dinner. After finishing her shopping, she relaxes at a nearby cafe (**кафе**). Notice how she uses the accusative case and common shopping chunks throughout her day.

> **Анна йде на ринок. Вона бачить помідори і яблука.**
> *(Anna goes to the market. She sees tomatoes and apples.)*
> **— Скільки коштують помідори?**
> *(— How much do the tomatoes cost?)*
> **— Тридцять гривень.**
> *(— Thirty hryvnias.)*
> **— Добре. Дайте кілограм, будь ласка.**
> *(— Good. Give me a kilogram, please.)*
> **Потім Анна йде у кафе. Вона бачить стіл.**
> *(Then Anna goes to a cafe. She sees a table.)*
> **— Тут вільно?**
> *(— Is it free here?)*
> **— Так, звичайно.**
> *(— Yes, of course.)*
> **— Мені борщ і каву з молоком, будь ласка.**
> *(— Borscht and coffee with milk for me, please.)*
> **Анна їсть борщ і п'є каву. Потім вона просить рахунок.**
> *(Anna eats borscht and drinks coffee. Then she asks for the bill.)*
> **— Рахунок, будь ласка. Можна карткою?**
> *(— The bill, please. Can I pay by card?)*
> **— Так, будь ласка.**
> *(— Yes, please.)*
> **Раптом вона бачить Олену.**
> *(Suddenly she sees Olena.)*
> **— Олено, привіт! Ти знаєш мого брата?**
> *(— Olena, hi! Do you know my brother?)*

This short text seamlessly combines functional shopping chunks (like **Рахунок, будь ласка.**) with the accusative case. Notice the accusative for inanimate objects when Anna orders food (**борщ**, **каву**), and the accusative for animate objects when she sees a friend (**Олену**) or mentions family (**брата**). You already know enough vocabulary and grammar to understand a full day of real-world activities in Ukrainian!

## Граматика (Grammar Summary)

To succeed in everyday interactions, you need a strong grasp of essential food and drink vocabulary (**їжа**, **напої**). Crucial combinations often use the preposition **з** (with), creating useful chunks like **кава з молоком** (coffee with milk) or **чай з лимоном** (tea with lemon). These are the fundamental building blocks of any market or cafe conversation in Ukraine, helping you sound more natural.

When we talk about the objects of our actions, we must use the accusative case. Remember the important difference between inanimate things (**що?** (what?)) and animate people (**кого?** (whom?)).
For inanimate objects, masculine nouns stay the same (**Я їм борщ.**, **Я купую хліб.**), while feminine nouns change their ending from **-а** to **-у** (**Я п'ю воду.**, **Я їм піцу.**).
For animate objects, the feminine rule is exactly the same (**Я бачу Олену.**, **Я люблю маму.**). However, masculine animate nouns take the genitive ending **-а** or **-я** (**Я бачу брата.**, **Я чекаю лікаря.**, **Я знаю друга.**).

Finally, always remember the specific patterns for asking prices. Use **Скільки коштує?** (How much does it cost?) for a single item, and **Скільки коштують?** (How much do they cost?) for plural items. Keep the currency agreement in mind: **одна гривня** (one hryvnia), **дві гривні** (two hryvnias), but **п'ять гривень** (five hryvnias).

<!-- INJECT_ACTIVITY: group-sort-accusative -->

<!-- INJECT_ACTIVITY: quiz-accusative-forms -->

## Діалог (Connected Dialogue)

This dialogue models a complete, realistic day of food and shopping. It combines talking about breakfast at home, buying fresh produce at the market, and ordering lunch at a cafe. Watch how the speakers use fixed phrases to get what they want smoothly and efficiently.

> **Олег:** Що ти їш на сніданок?
> *(What do you eat for breakfast?)*
> **Марія:** Я їм кашу і п'ю каву з молоком.
> *(I eat porridge and drink coffee with milk.)*
> **Олег:** Потім іду на ринок. Скільки коштують помідори?
> *(Then I go to the market. How much do tomatoes cost?)*
> **Марія:** Тридцять гривень.
> *(Thirty hryvnias.)*
> **Олег:** Дайте кілограм, будь ласка.
> *(Give me a kilogram, please.)*
> **Марія:** Мені борщ і воду, будь ласка. Рахунок, будь ласка. Можна карткою?
> *(Borscht and water for me, please. The bill, please. Can I pay by card?)*
> **Олег:** О, я бачу Олену! Олено, привіт! Ти знаєш мого брата?
> *(Oh, I see Olena! Olena, hi! Do you know my brother?)*

Phrases like **Мені...** (For me...), **Дайте...** (Give me...), **Тут вільно?** (Is it free here?), and **Можна карткою?** (Can I pay by card?) are fixed communicative chunks. You do not need to analyze their deep grammar right now. Treat them as reliable tools: memorize them as complete units, and use them to communicate naturally in a Ukrainian market or cafe without hesitation.

<!-- INJECT_ACTIVITY: fill-in-dialogue -->

<!-- INJECT_ACTIVITY: quiz-situational-phrases -->

## Підсумок — Summary

Congratulations on reaching the end of the A1.6 Checkpoint! You have successfully brought together a wide range of practical skills. Here is a summary of what you can now do in Ukrainian:

*   You can talk confidently about everyday food and drinks, describing exactly what you eat for breakfast, lunch, or dinner.
*   You can order a delicious meal at a cafe, check if a seat is free, and politely ask for the bill when you finish.
*   You can shop at a market, accurately ask for prices, understand quantities, and handle amounts in **гривні**.
*   You can correctly use the accusative case to talk about both inanimate things (like eating pizza or drinking water) AND animate people (like seeing a brother or waiting for a friend).

You are building a strong foundation for real-world communication. Next, in A1.7, you will focus on Communication—learning how to make phone calls, write emails, and make exciting plans with friends!
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-food-shopping
level: a1

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (8 total / 3–5 inline / 5–8 workbook,
# 10+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 10 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 10 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 10 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 10 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 10 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 10 pairs total

  - id: group-sort-gender
    type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Чоловічий рід"
        items: ["стіл", "олівець", "будинок"]   # ≥ 3 items per group
      - label: "Жіночий рід"
        items: ["книга", "ручка", "школа"]
      - label: "Середній рід"
        items: ["вікно", "море", "молоко"]

  - id: true-false-grammar
    type: true-false
    instruction: "Правда чи ні?"
    items:                     # ← real output: ≥ 10 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 10 items total

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
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]. **CRITICAL: use `____` (four underscores) for the blank, NOT `{word}` curly-brace syntax. Example: `sentence: "Це ____ кімната."` with `answer: "моя"`. The validator REJECTS `{word}` format.**
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

**Level: A1.4+ (Module 41/55) — BEGINNER**

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

### Pattern: grammar-pluralization [§4.2.1.1]
**Множина іменників** (Noun plurals)
- **fill-in** — Утвори множину: Утворити множину іменника — закінчення -и vs -і залежно від приголосного / Form noun plural — -и vs -і endings depending on consonant
  - Instruction: *Напишіть множину*
- **group-sort** — Закінчення -и чи -і?: Розподілити іменники за типом закінчення множини / Sort nouns by plural ending type
  - Instruction: *Розподіліть*
- **match-up** — Однина → множина: Зіставити форму однини з формою множини / Match singular form to plural form
  - Instruction: *З'єднайте*
- **error-correction** — Виправ множину: Знайти неправильну форму множини та виправити / Find incorrect plural form and fix it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Множина — це словотворення. Учні мають продукувати форми, а не тільки вибирати
- ❌ fill-in-no-options: На A1 завжди давати варіанти — учень ще не знає всіх закінчень

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

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 8 activities.** Inline: 3–5. Workbook: 5–8. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 10 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 10.
- **Lower minimums for specific types only:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items, essay-response/critical-analysis = 1 prompt.
- If you can't think of enough items, add more examples from the module's vocabulary and content. NEVER ship a 1-item or 2-item activity unless its type cap explicitly allows it.
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

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **at least 3** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 5** workbook activities.
- [ ] **Total ≥ 8.**
- [ ] **Every** activity has **at least 10** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 3 and 5. I did NOT create more injection markers than 5.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
