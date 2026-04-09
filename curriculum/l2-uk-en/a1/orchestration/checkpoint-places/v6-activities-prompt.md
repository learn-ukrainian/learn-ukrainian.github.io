<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-places.yaml` file for module **35: Checkpoint: Places** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-question-choice -->`
- `<!-- INJECT_ACTIVITY: group-sort-cases -->`
- `<!-- INJECT_ACTIVITY: quiz-euphony-check -->`
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

Navigating a new city is often your very first real test of survival in a completely new language environment. Before reaching this point in your studies, you could name a few isolated objects, describe who you are, or exchange basic daily greetings. Now, you have acquired the tools to confidently step out into the street, find what you need, and interact with the world around you. This module serves as a comprehensive checkpoint to review the essential skills you acquired throughout the "Places" section. 

The leap from speaking in isolated words to building connected urban navigation phrases is a huge milestone. You are no longer just pointing and saying **центр** (center) or **метро** (subway); instead, you are constructing full ideas by saying **у центрі** (in the center) and **на метро** (by subway). This review highlights the critical differences between simply being somewhere, actively going somewhere, and returning from somewhere. 

Evaluate exactly what you know so far. Ask yourself the following questions to see if you are truly ready to navigate the busy streets of Ukraine:

*   **Чи можу я вибрати між «у» та «в»?** (Can I choose between «у» and «в»?) — This tests your grasp of euphony rules for smooth pronunciation.
*   **Чи знаю я, як сказати, де я?** (Do I know how to say where I am?) — This checks if you can use the locative case to state your location.
*   **Чи можу я назвати місця в місті?** (Can I name places in the city?) — This ensures you recognize essential city vocabulary.
*   **Чи можу я сказати, куди я йду?** (Can I say where I am going?) — This confirms you understand the accusative case for direction.
*   **Чи можу я користуватися транспортом?** (Can I use transport?) — This checks your ability to say how you are traveling.
*   **Чи можу я запитати дорогу?** (Can I ask for directions?) — This ensures you can communicate with locals and follow a route.
*   **Чи можу я сказати, звідки я приїхав?** (Can I say where I came from?) — This confirms you can use genitive chunks for origin.

If you can answer these questions affirmatively, you have a solid foundation for the rest of the A1 level.

<!-- INJECT_ACTIVITY: quiz-question-choice -->

## Читання (Reading Practice)

Reading short, contextual narratives in Ukrainian helps solidify grammar patterns naturally without feeling like you are memorizing rules. The following reading practice follows a traveler named Марк who arrives in the capital city. He begins his journey at the main train station, known as **вокзал** (train station), and needs to locate his accommodation, a **готель** (hotel), which is situated right in the heart of the city. Finally, he navigates his way to one of the most famous historical landmarks in the capital, **Золоті ворота** (Golden Gate). 

Read the text below carefully. Pay close attention to how Mark uses prepositions like **у**, **в**, **на**, and **з** depending on whether he is describing his static location, his destination, or his origin.

*   **Я зараз у Києві.** (I am currently in Kyiv.)
*   **Я з Польщі.** (I am from Poland.)
*   **Мій готель у центрі.** (My hotel is in the center.)
*   **Я йду пішки.** (I am walking on foot.)
*   **Вокзал далеко.** (The train station is far.)
*   **Я їду на метро.** (I am going by subway.)
*   **Скажіть, будь ласка, де музей?** (Tell me, please, where is the museum?)
*   **Я йду направо.** (I am walking to the right.)
*   **Тут площа.** (Here is a square.)
*   **Золоті ворота близько.** (Golden Gate is near.)
*   **Я вже біля музею.** (I am already near the museum.)

Notice how Mark integrates all the fundamental A1.5 vocabulary and grammar in just a few straightforward sentences. He seamlessly uses **на метро** (by subway) for his mode of transport, **направо** (to the right) for simple directions, and **біля музею** (near the museum) to establish his exact location relative to another landmark. 

:::tip
As you read Ukrainian texts, try your best not to translate word for word in your head. Instead, visualize the scene unfolding. Picture Mark exiting the train station, looking at a map, and walking towards the center. This visualization technique helps you link the Ukrainian words directly to real-world concepts.
:::

## Граматика (Grammar Summary)

The grammatical patterns from this phase rely on a few core principles. First, the Ukrainian language places a very high value on a smooth, flowing sound, a concept known as euphony. The rules of euphony determine whether we should use **у** or **в**, **і** or **й**, and **з**, **із**, or **зі**. The basic guiding principle is to avoid awkward clusters of consonants or vowels. 

Compare the following pairs:
*   **Він у Львові** (He is in Lviv) versus **Вона в Одесі** (She is in Odesa). We use **у** between consonants, and **в** between vowels.
*   **Брат і сестра** (Brother and sister) versus **Тато й мама** (Dad and mom). We use **і** between consonants, and **й** between vowels.
*   **Зі школи** (From school) versus **З роботи** (From work). We use **зі** before difficult consonant clusters, but **з** before a single consonant.

The most crucial grammatical concept in urban navigation is understanding the three main directional questions. The specific noun case you use depends entirely on the question you are answering:

*   **Де?** (Where?) indicates a static location. It uses the Locative case. 
    *   **В аптеці** (In the pharmacy)
    *   **В школі** (In school)
    *   **На роботі** (At work)
*   **Куди?** (To where?) indicates the direction of movement. It uses the Accusative case.
    *   **В аптеку** (To the pharmacy)
    *   **У школу** (To school)
    *   **На роботу** (To work)
*   **Звідки?** (From where?) indicates an origin or starting point. It uses the Genitive case with the preposition **з** (or **із**/**зі**).
    *   **З аптеки** (From the pharmacy)
    *   **З України** (From Ukraine)
    *   **З роботи** (From work)

Notice the distinct contrast between **на роботі** (location) and **на роботу** (direction). Furthermore, the preposition **на** is generally used for open spaces, events, and abstract concepts, while **в** / **у** is strictly used for enclosed physical structures. This directional system also applies when matching city places with correct prepositions, taking transport like **автобусом** (by bus) or **на метро** (by subway), and following adverbs for directions such as **прямо** (straight), **направо** (to the right), and **наліво** (to the left).

<!-- INJECT_ACTIVITY: group-sort-cases -->
<!-- INJECT_ACTIVITY: quiz-euphony-check -->

## Діалог (Connected Dialogue)

Imagine a very common, real-world scenario: a tourist from Canada arrives at a busy, crowded metro station in Kyiv. They need to find a specific museum first, and then head over to the main train station, the **вокзал**. When approaching a stranger on the street for help, it is absolutely vital to emphasize the polite register. Starting your request with **Вибачте** (Excuse me) and **Скажіть, будь ласка** (Tell me, please) shows cultural respect and instantly makes people much more willing to assist you. 

Read the multi-turn connected dialogue below. Pay close attention to how the tourist combines phrases indicating origin, location, and direction into a single, cohesive conversation.

> **Турист:** Вибачте, я з Канади. Де тут музей? *(Excuse me, I am from Canada. Where is the museum here?)*
> **Місцевий:** Музей у центрі. Ідіть на метро до станції Хрещатик. *(The museum is in the center. Go by subway to Khreshchatyk station.)*
> **Турист:** А як дістатися від метро? *(And how to get there from the subway?)*
> **Місцевий:** Вийдіть і йдіть направо. Музей на площі. *(Exit and walk to the right. The museum is on the square.)*
> **Турист:** Дякую! А потім я хочу їхати у Львів. Де вокзал? *(Thank you! And then I want to go to Lviv. Where is the train station?)*
> **Місцевий:** Вокзал далеко. Їдьте на метро до станції Вокзальна. *(The train station is far. Go by subway to Vokzalna station.)*

This exchange perfectly demonstrates practical functional language in action. Notice the specific use of the word **дістатися** (to get to). While **йти** (to go on foot) and **їхати** (to go by vehicle) specify the exact method of transport, **дістатися** focuses purely on the goal of reaching the destination, making it the perfect word for asking directions. 

You also see how prepositions shift based on the point of reference. The local uses **від метро** (from the subway), showing the starting point of the walking route, and **до вокзалу** (to the station) to show the end point. 

:::note
To fully consolidate your urban vocabulary, try describing your own city or a city you love. Imagine video-calling a friend while walking through a coastal city like **Одеса** (Odesa). You might show them the sights: **Дерибасівська вулиця** (Derybasivska street), the famous **Потьомкінські сходи** (Potemkin Stairs), a large **порт** (port), and a sunny **пляж** (beach). Practice describing exactly where you are and where you are going using these nouns!
:::

<!-- INJECT_ACTIVITY: fill-in-dialogue-forms -->

## Підсумок — Summary

Congratulations on reaching the end of the A1.5 phase! You have successfully built a solid, reliable foundation for urban survival in Ukraine. The following points summarize your new achievements. 

**Я тепер можу...** (I can now...):
*   Apply basic euphony rules. You know how to instinctively alternate between **у** and **в**, or **і** and **й**, to ensure your spoken Ukrainian maintains a natural, flowing rhythm.
*   State your exact location. You can confidently answer the question **Де?** (Where?) using the locative case, such as saying **в готелі** (in the hotel) or **на площі** (on the square).
*   Indicate your direction of travel. You can accurately answer the question **Куди?** (To where?) using the accusative case, such as stating you are going **у парк** (to the park).
*   Use city transport options. You can explain how you are traveling from point A to point B, using forms like **на автобусі** (by bus) or **на метро** (by subway).
*   Give and follow street directions. You understand vital navigation commands like **направо** (to the right), **наліво** (to the left), and **прямо** (straight).
*   State your country of origin. You can seamlessly answer the question **Звідки?** (From where?), telling people you are **з України** (from Ukraine) or from another specific country.

You can now find your way to a shop, a museum, or a restaurant, but what happens when you finally walk inside the building? In the upcoming A1.6 module, "Food and Shopping," we will transition directly from navigating the outdoor streets to interacting within these indoor establishments. You will learn the specific language required for ordering food, buying groceries, and using the Accusative case to talk about direct objects. Get ready to proudly say **Я хочу каву** (I want coffee) and master the art of the daily transaction!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-places
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
