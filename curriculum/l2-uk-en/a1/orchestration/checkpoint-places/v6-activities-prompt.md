<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-places.yaml` file for module **35: Checkpoint: Places** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-question-choice -->`
- `<!-- INJECT_ACTIVITY: group-sort-case-function -->`
- `<!-- INJECT_ACTIVITY: quiz-euphony-rules -->`
- `<!-- INJECT_ACTIVITY: fill-in-dialogue-forms -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Choose the correct question: Де? Куди? Звідки?'
  items: 8
  questions:
  - '... ти живеш? — У Києві. (Де / Куди / Звідки)'
  - '... ти йдеш? — У магазин. (Куди / Де / Звідки)'
  - '... ви? — Ми з Канади. (Звідки / Де / Куди)'
  - '... музей? — У центрі. (Де / Куди / Звідки)'
  - '... їде автобус? — На вокзал. (Куди / Де / Звідки)'
  - '... ти їдеш? — З роботи. (Звідки / Куди / Де)'
  - '... аптека? — Направо. (Де / Куди / Звідки)'
  - '... вони? — Зі США. (Звідки / Де / Куди)'
  type: quiz
- blanks:
  - Вибачте, я {з Канади}. Де тут музей?
  - Музей {у центрі}. Ідіть на метро.
  - А як дістатися {від метро}?
  - Вийдіть і йдіть {направо}. Музей на площі.
  - Я хочу їхати {у Львів}. Де вокзал?
  - Вокзал далеко, їдьте {на метро}.
  focus: Complete the connected dialogue with correct forms
  items: 6
  type: fill-in
- focus: Sort phrases by case/function (Locative, Accusative, Genitive chunks)
  groups:
  - items:
    - у школі
    - на площі
    - в центрі
    name: Локація (Де?)
  - items:
    - на роботу
    - у Львів
    - в Канаду
    name: Напрямок (Куди?)
  - items:
    - з України
    - зі США
    - з роботи
    name: Походження (Звідки?)
  items: 9
  type: group-sort
- focus: 'Euphony rules check: у/в, і/й, з/із/зі'
  items: 8
  questions:
  - Брат ... сестра (і / й)
  - Вона живе ... Львові (у / в)
  - Я йду ... школи (зі / з)
  - Він ... Києві (у / в)
  - Мама ... тато (і / й)
  - Ми ... України (з / із)
  - Я ... кімнаті (в / у)
  - Вона ... США (зі / з)
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

You have reached the final stage of the Places phase. Navigating a Ukrainian city requires you to combine several different skills into one smooth conversation. You must know how to state your current location, your destination, your point of origin, and your mode of transport. This checkpoint brings all those pieces together.

The Ukrainian spatial system relies on a solid triad of questions. Understanding these three questions unlocks basic urban mobility. The static location answers the question **Де?** (Where?). The dynamic destination answers the question **Куди?** (To where?). Finally, the point of origin answers the question **Звідки?** (From where?). Ukrainians naturally categorize every movement into one of these three buckets.

Review this checklist to see what you already know. Can you apply the rules of euphony for a smooth pronunciation?
* **Вона живе у Львові.** (She lives in Lviv.)
* **Він живе в Києві.** (He lives in Kyiv.)

Can you say where things are currently located?
* **Я зараз у парку.** (I am in the park now.)
* **Ми в центрі.** (We are in the center.)

Can you say where you are going right now?
* **Я йду в магазин.** (I am going to the store.)
* **Вона йде на роботу.** (She is going to work.)

Can you accurately state your origin?
* **Я родом з України.** (I am originally from Ukraine.)
* **Він іде зі школи.** (He is walking from school.)

Can you use transport vocabulary and give basic directions?
* **Ми їдемо автобусом.** (We are going by bus.)
* **Ідіть прямо і направо.** (Go straight and to the right.)

To prove you are ready, read this short introduction out loud:
> **Мене звати Анна.**
> *(My name is Anna.)*
>
> **Я живу в Києві.**
> *(I live in Kyiv.)*
>
> **Я щодня їду на роботу.**
> *(I travel to work every day.)*
>
> **Я їду на метро.**
> *(I travel by metro.)*

<!-- INJECT_ACTIVITY: quiz-question-choice -->

## Читання (Reading Practice)

Real navigation happens in continuous conversation, not in isolated textbook sentences. Imagine a tourist navigating the bustling, vibrant streets of Kyiv. They need to ask locals for accurate directions, understand the public transit system, locate a specific cultural site, and clearly explain their travel plans. This requires combining all your spatial skills.

Read the following narrative about a tourist in the city. It combines all the spatial patterns you have learned so far.

> **Привіт! Я турист з Канади.**
> *(Hi! I am a tourist from Canada.)*
>
> **Я зараз у центрі Києва.**
> *(I am currently in the center of Kyiv.)*
>
> **Я дуже хочу їхати в музей.**
> *(I really want to go to the museum.)*
>
> **Але музей стоїть далеко.**
> *(But the museum stands far away.)*
>
> **Тому я йду на метро.**
> *(Therefore I am walking to the metro.)*
>
> **Я їду на станцію Хрещатик.**
> *(I travel to the Khreshchatyk station.)*
>
> **Там я йду прямо і направо.**
> *(There I go straight and to the right.)*
>
> **І ось музей на великій площі!**
> *(And here is the museum on the large square!)*

Notice how this narrative effortlessly switches between different spatial concepts to tell a complete story. The tourist starts by answering the question of origin with **з Канади** (from Canada). Then, they state their current static location using **у центрі Києва** (in the center of Kyiv). Next, they switch to a dynamic destination with **в музей** (to the museum). They describe their route using transport vocabulary and basic directions like **прямо** (straight) and **направо** (to the right). Finally, they confirm the static location of their destination with **на великій площі** (on the large square). You already possess all the grammatical tools needed to understand and construct a detailed story exactly like this one.

## Граматика (Grammar Summary)

The core spatial patterns form the absolute foundation of your navigation skills. The question **Де?** (Where?) requires the prepositions **в** or **на** followed by the Locative case. You use this exclusively for static locations, telling people exactly where an object or person currently rests.
* **Студент зараз у школі.** (The student is in school now.)
* **Вона весь день на роботі.** (She is at work all day.)
* **Ми сидимо в парку.** (We are sitting in the park.)
* **Зошит лежить на столі.** (The notebook is lying on the table.)

The question **Куди?** (To where?) requires the prepositions **в** or **на** followed by the Accusative case. You use this strictly for movement toward a destination, indicating the endpoint of a physical journey.
* **Студент іде у школу.** (The student is going to school.)
* **Вона швидко їде на роботу.** (She is traveling quickly to work.)
* **Ми йдемо в парк.** (We are walking to the park.)
* **Він іде в театр.** (He is going to the theater.)

The question **Звідки?** (From where?) requires the prepositions **з**, **із**, or **зі** followed by the Genitive case. You use this to express the starting point of a movement or a person's geographic origin.
* **Студент іде зі школи.** (The student is walking from school.)
* **Вона йде з роботи.** (She is walking from work.)
* **Турист іде з готелю.** (The tourist is walking from the hotel.)
* **Я йду з парку.** (I am walking from the park.)

Ukrainian speech requires a smooth flow of sounds. The euphony rules ensure that words connect naturally without awkward consonant clusters. You alternate between vowels and consonants using specific sets of prepositions and conjunctions.
* **Брат і сестра йдуть.** (Brother and sister are walking.)
* **Мама й тато вдома.** (Mom and dad are at home.)
* **Вона зараз у Львові.** (She is in Lviv now.)
* **Він живе в Одесі.** (He lives in Odesa.)

When discussing your daily commute and transport, you use specific grammatical forms. You use the Instrumental case for the vehicle itself, or you use the preposition **на** with the Locative case for public transit systems.
* **Ми їдемо великим автобусом.** (We are going by a large bus.)
* **Вони їдуть на метро.** (They are going by metro.)

You also use fixed, unchanging adverbs for simple directions on the street.
* **Ідіть прямо по вулиці.** (Go straight along the street.)
* **Аптека стоїть направо.** (The pharmacy stands to the right.)
* **Гарний парк наліво.** (The beautiful park is to the left.)

All these individual elements combine to form complete, natural, and highly functional thoughts.
* **Я їду з роботи.** (I am traveling from work.)
* **Я їду автобусом у центр.** (I am traveling by bus to the center.)

<!-- INJECT_ACTIVITY: group-sort-case-function -->
<!-- INJECT_ACTIVITY: quiz-euphony-rules -->

## Діалог (Connected Dialogue)

Imagine you are visiting Kyiv and you urgently need some assistance. You stop a local resident on the street to ask for clear directions to a famous museum. After you find out about the museum, you also need to figure out how to reach the main train station for your onward journey to the city of Lviv.

> **Турист:** Вибачте, я з Канади. Де тут музей?
> *(Tourist: Excuse me, I am from Canada. Where is the museum here?)*
>
> **Місцевий:** Музей у центрі. Ідіть на метро до станції Хрещатик.
> *(Local: The museum is in the center. Go by metro to the Khreshchatyk station.)*
>
> **Турист:** А як дістатися від метро?
> *(Tourist: And how do I get there from the metro?)*
>
> **Місцевий:** Вийдіть і йдіть направо. Музей на площі.
> *(Local: Exit and go right. The museum is on the square.)*
>
> **Турист:** Дякую! А потім я хочу їхати у Львів. Де вокзал?
> *(Tourist: Thank you! And then I want to travel to Lviv. Where is the train station?)*
>
> **Місцевий:** Вокзал далеко, їдьте на метро до станції Вокзальна.
> *(Local: The train station is far, go by metro to Vokzalna station.)*

The first half of the dialogue handles the immediate navigation problem. The tourist successfully states their geographical origin using the phrase **з Канади** (from Canada). They then ask a simple, direct question about their target location using **Де тут музей?** (Where is the museum here?). The local resident responds with a static location, **у центрі** (in the center), and provides a clear route using transport vocabulary. 

The tourist then asks how to navigate on foot from the station using the phrase **від метро** (from the metro). They use the verb **дістатися** (to reach / to get to). This is a highly practical verb when you need to know how to navigate between two specific points.

The second half of the dialogue shifts the focus to a future destination. The tourist uses the Accusative case to explain their next city target, saying **у Львів** (to Lviv). They immediately ask for the location of the main train station. The local resident gives them practical advice, explaining that the station is far away. They use the command form **їдьте** (drive/travel) and combine it with the transport phrase to give a clear, actionable route across the city.

:::note
You might hear people say **на метро** (by metro) very often in casual speech. While this is widely understood, standard Ukrainian style guides often recommend simply using the word **метро** on its own (as an instrumental form) or **в метро** to sound more authentic. However, **на метро** remains extremely common in everyday city navigation.
:::

<!-- INJECT_ACTIVITY: fill-in-dialogue-forms -->

## Підсумок — Summary

You can now successfully navigate the bustling streets of a Ukrainian city. You have built a solid grammatical foundation for basic urban survival. You know exactly how to ask locals for directions, understand the specific routes people give you, and explain your own daily movements. You can confidently state where you are originally from and where you currently intend to go. This means you can handle the most crucial interactions required of any traveler or new resident.

You have acquired several powerful technical tools during this phase. You know the euphony rules that make your pronunciation sound natural, fluid, and connected. You know how to use the Locative case to answer the question **Де?** (Where?) for static locations. You know how to use the Accusative case to answer the question **Куди?** (To where?) for dynamic movement toward a target. You also know how to use Genitive chunks to answer the question **Звідки?** (From where?). These tools allow you to form precise, accurate sentences without second-guessing your preposition choices.

The next phase of your learning journey will build directly on these exact skills. In the upcoming Food and Shopping modules, you will take the Accusative case, which you currently use only for physical destinations, and dramatically expand its function. You will learn to use the Accusative case for direct objects, allowing you to successfully order a coffee, buy a train ticket, or purchase fresh groceries at the market. Understanding how to direct your movement was the first step; soon, you will direct your actions toward objects. You have the momentum, and you are ready for the next step.
```
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-places
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

**Level: A1.4+ (Module 35/55) — BEGINNER**

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
