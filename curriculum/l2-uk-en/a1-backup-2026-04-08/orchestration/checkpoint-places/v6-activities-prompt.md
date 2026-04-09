<!-- version: 1.0.0 | updated: 2026-03-27 -->
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

- `<!-- INJECT_ACTIVITY: quiz-de-kudy-zvidky -->`
- `<!-- INJECT_ACTIVITY: quiz-euphony -->`
- `<!-- INJECT_ACTIVITY: group-sort-cases -->`
- `<!-- INJECT_ACTIVITY: fill-in-dialogue -->`

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

Seven modules of A1.5 are behind you — euphony, locative case, city vocabulary, accusative for direction, transport, giving directions, and saying where you're from. Before moving to the next phase, test yourself. Can you apply euphony rules (**у/в**, **і/й**, **з/із/зі**)? Can you say where something is? Where you're going? Where you're from? Can you name city places and use transport words?

Try answering these questions out loud:

- **Де ти живеш?** (Where do you live?) — **У Києві.** (In Kyiv.)
- **Куди ти йдеш?** (Where are you going?) — **У магазин.** (To the store.)
- **Звідки ти?** (Where are you from?) — **Я з Канади.** (I'm from Canada.)
- **Як ти їдеш?** (How do you travel?) — **Автобусом.** (By bus.)
- **Де музей?** (Where is the museum?) — **Музей у центрі.** (The museum is in the centre.)
- Choose **і** or **й**: **Брат ___ сестра.**
- Choose **у** or **в**: **Я живу ___ Львові.**

If those answers came quickly, you're ready for this checkpoint. If some felt tricky, that's exactly what this module is for. We'll bring all seven patterns together — euphony (M28), location (M29), city vocabulary (M30), direction (M31), transport (M32), directions (M33), and origin (M34) — into one connected practice. By the end, you'll see how these pieces form a complete toolkit for navigating a Ukrainian city.

## Читання (Reading Practice)

Read this short text about a tourist in Kyiv. Every sentence uses patterns from M28–M34. See how many you can spot — euphony choices, locative for location, accusative for direction, genitive for origin, transport, and directions.

> **Мене звати Томас.** *(My name is Tomas.)* **Я з Канади.** *(I'm from Canada.)* **Зараз я у Києві.** *(Right now I'm in Kyiv.)*
>
> **Сьогодні я гуляю по місту.** *(Today I'm walking around the city.)* **Вранці я їду на метро до станції Хрещатик.** *(In the morning I take the metro to Khreshchatyk station.)* **Метро у Києві дуже зручне.** *(The metro in Kyiv is very convenient.)*
>
> **Я виходжу зі станції.** *(I exit the station.)* **Іду направо.** *(I go right.)* **Попереду — Хрещатик, головна вулиця міста.** *(Ahead is Khreshchatyk, the main street of the city.)* **Я йду прямо.** *(I walk straight.)* **Бачу красивий парк.** *(I see a beautiful park.)* **У парку є фонтани й лавки.** *(In the park there are fountains and benches.)*
>
> **Потім я питаю перехожого:** *(Then I ask a passerby:)* **«Вибачте, де Національний музей?»** *(«Excuse me, where is the National Museum?»)* **Він відповідає:** *(He answers:)* **«Музей на площі. Ідіть прямо, потім наліво.»** *(«The museum is on the square. Go straight, then left.»)*
>
> **Я іду до музею.** *(I go to the museum.)* **Потім хочу їхати до Лаври.** *(Then I want to go to the Lavra.)* **Сідаю в автобус.** *(I get on a bus.)* **Їду до зупинки Арсенальна.** *(I ride to Arsenalna stop.)* **Від зупинки до Лаври пішки — п'ять хвилин.** *(From the stop to the Lavra on foot — five minutes.)*
>
> **Увечері я у готелі.** *(In the evening I'm at the hotel.)* **Телефоную в Канаду:** *(I call Canada:)* **«Я зараз у Києві! Хочу їхати у Львів!»** *(«I'm in Kyiv now! I want to go to Lviv!»)*

Now check your understanding:

1. **Звідки Томас?** (Where is Tomas from?) — **З Канади.** (From Canada.)
2. **Куди він їде вранці?** (Where does he go in the morning?) — **На метро до станції Хрещатик.** (By metro to Khreshchatyk station.)
3. **Де музей?** (Where is the museum?) — **На площі.** (On the square.)

Notice the patterns at work: **з Канади** (genitive — where from), **у Києві** (locative — where), **на метро** (transport), **зі станції** (euphony — **зі** before **ст-**), **направо** and **прямо** (directions), **до Лаври** (direction — where to), **в автобус** (onto transport). Томас uses every A1.5 skill in one short story — combining patterns naturally rather than thinking about grammar rules one at a time.

<!-- INJECT_ACTIVITY: quiz-de-kudy-zvidky -->

## Граматика (Grammar Summary)

Here are the seven key patterns from A1.5 — your personal grammar card for navigating Ukrainian cities. Each pattern answers a different question.

**Pattern 1: Euphony (M28)** — Ukrainian alternates certain sounds for smooth speech.

- **у/в**: **Я у школі.** (I'm at school.) / **Він в офісі.** (He's in the office.)
- **і/й**: **Брат і сестра.** (Brother and sister.) / **Ольга й Андрій.** (Olha and Andriy.)
- **з/із/зі**: **Я з України.** (I'm from Ukraine.) / **Зі США.** (From the USA.)

<!-- INJECT_ACTIVITY: quiz-euphony -->

**Pattern 2: Де? → в/на + locative (M29)** — where something IS.

- **У школі.** (At school.) **На роботі.** (At work.) **В центрі.** (In the centre.) **На площі.** (On the square.)

**Pattern 3: Куди? → в/на + accusative (M31)** — where you're GOING.

- **У школу.** (To school.) **На роботу.** (To work.) **У Львів.** (To Lviv.) **На площу.** (To the square.)

Compare: **у школі** (at school — you're there) vs. **у школу** (to school — you're heading there). Same preposition, different case ending.

**Pattern 4: Звідки? → з/із/зі + genitive (M34)** — where you're FROM.

- **З України.** (From Ukraine.) **Зі США.** (From the USA.) **З роботи.** (From work.) **З Канади.** (From Canada.)

**Pattern 5: Transport (M32)** — how you travel.

- **Їхати автобусом.** (To go by bus.) **На метро до станції Хрещатик.** (By metro to Khreshchatyk station.)

:::tip
Transport hubs (**станція**, **вокзал**, **зупинка**) always take **на**: **на станції**, **на вокзалі**, **на зупинці** — never **в станції**.
:::

**Pattern 6: Directions (M33)** — imperative forms for giving directions.

- **Ідіть прямо.** (Go straight.) **Направо.** (To the right.) **Наліво.** (To the left.) **Вийдіть тут.** (Exit here.)

**Pattern 7: City places with prepositions (M30)** — each noun pairs with its own preposition.

- **У музеї.** (In the museum.) **На вокзалі.** (At the train station.) **В парку.** (In the park.) **На площі.** (On the square.) **У готелі.** (In the hotel.) **У бібліотеці.** (In the library.)

<!-- INJECT_ACTIVITY: group-sort-cases -->

## Діалог (Connected Dialogue)

Марко is visiting Kyiv for the first time. He stops a local, Оксана, near a metro entrance to ask for help. Watch how all seven A1.5 patterns appear in one real conversation.

> **Марко:** Вибачте! Ви місцева? *(Excuse me! Are you local?)*
> **Оксана:** Так, я з Києва. Що шукаєте? *(Yes, I'm from Kyiv. What are you looking for?)*
> **Марко:** Я з Канади. Я тут уперше. Де Національний музей? *(I'm from Canada. This is my first time here. Where is the National Museum?)*
> **Оксана:** Музей у центрі, на вулиці Грушевського. Їдьте на метро до станції Арсенальна. Потім пішки. *(The museum is in the centre, on Hrushevskyi Street. Take the metro to Arsenalna station. Then walk.)*
> **Марко:** А де станція метро? *(And where is the metro station?)*
> **Оксана:** Ось тут, за рогом. Ідіть прямо, потім направо. Там — вхід. *(Right here, around the corner. Go straight, then right. The entrance is there.)*
> **Марко:** Добре! А після музею я хочу їхати у Львів. Де вокзал? *(OK! After the museum I want to go to Lviv. Where is the train station?)*
> **Оксана:** Центральний вокзал далеко. Їдьте на метро до станції Вокзальна. *(The central station is far. Take the metro to Vokzalna station.)*
> **Марко:** Скільки їхати? *(How long is the ride?)*
> **Оксана:** Хвилин двадцять. Вокзал біля станції. *(About twenty minutes. The station is right by the stop.)*
> **Марко:** А де тут кафе? *(Where is a café around here?)*
> **Оксана:** Кафе на площі Незалежності. Це одна зупинка на метро. *(There's a café at Independence Square. It's one metro stop.)*
> **Марко:** Дякую! *(Thanks!)*
> **Оксана:** Будь ласка! Гарної подорожі! *(You're welcome! Have a good trip!)*

Every A1.5 pattern appeared naturally. **Де музей?** — locative: **у центрі**. Where to? — **у Львів** (accusative). Where from? — **з Канади**, **з Києва** (genitive). Transport — **на метро до станції**. Directions — **прямо**, **направо**. City places — **на площі**, **біля станції**, **за рогом**. Seven patterns, one conversation.

Now try it yourself. Imagine you're video-calling a friend while walking through **Одеса** (Odesa). Describe what you see:

- **Я зараз на Дерибасівській вулиці.** (I'm on Derybasivska Street now.)
- **Іду до порту.** (I'm heading to the port.)
- **Потім хочу на пляж.** (Then I want to go to the beach.)
- **Я з [your city].** (I'm from [your city].)

Use at least five of the seven patterns from this module.

<!-- INJECT_ACTIVITY: fill-in-dialogue -->

## Підсумок — Summary

You've completed A1.5 — Places. Here's what you can now do in Ukrainian:

- ✅ **Euphony (M28)** — You choose **у/в**, **і/й**, **з/із/зі** automatically based on surrounding sounds
- ✅ **Location (M29)** — **Де?** → в/на + locative: **у школі**, **на роботі**, **в центрі**
- ✅ **City vocabulary (M30)** — **вулиця**, **площа**, **парк**, **музей**, **вокзал**, **аптека**, **бібліотека**
- ✅ **Direction (M31)** — **Куди?** → в/на + accusative: **у школу**, **у Львів**, **на площу**
- ✅ **Transport (M32)** — **їхати автобусом**; **на метро до станції Хрещатик**
- ✅ **Giving directions (M33)** — **ідіть прямо**, **направо**, **наліво**, **вийдіть**
- ✅ **Origin (M34)** — **Звідки?** → з/із/зі + genitive: **з України**, **зі США**, **з Канади**

In A1.6 — Food and Shopping, you'll learn how to order food, buy things at a market, and use the accusative case for objects — not just directions. You'll say things like **Я хочу каву** (I want coffee), **Дайте хліб** (Give me bread), and **Скільки коштує?** (How much does it cost?). The accusative you practiced for direction (**у школу**) now works for objects too — a natural extension of what you already know.

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

**Level: A1.4+ (Module 35/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-cases
- **fill-in** — Який відмінок?: Fill in the correct case ending for a noun in context
  - Instruction: *Вставте іменник у правильній формі*
- **quiz** — Визнач відмінок: Identify which case a highlighted noun is in
- **group-sort** — Розподіли за відмінками: Sort noun forms by their case
- **error-correction** — Знайди помилку у відмінку: Find wrong case ending and correct it

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
