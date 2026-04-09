<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/a1-finale.yaml` file for module **55: A1 Finale** (a1).

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

- `<!-- INJECT_ACTIVITY: order-day-events -->`
- `<!-- INJECT_ACTIVITY: match-survival-phrases -->`
- `<!-- INJECT_ACTIVITY: fill-in-tenses -->`
- `<!-- INJECT_ACTIVITY: a1-grammar-quiz -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Put the events of the day in chronological order.
  items:
  - Зранку я прокинувся в готелі.
  - Потім я снідав у кафе.
  - Після сніданку я їхав на метро в центр.
  - Я гуляв по місту і купив сувеніри.
  - Вдень я обідав з новою подругою Оленою.
  - Ввечері ми ходили в кіно.
  - Потім ми вечеряли в ресторані.
  - Вночі я повернувся в готель і відпочивав.
  type: order
- focus: Complete the sentences narrating the day using past, present, and future
    tenses.
  items:
  - '{Зранку|Завтра|Ввечері} я снідав у кафе.'
  - Зараз я {гуляю|гуляв|буду гуляти} по Хрещатику, тут дуже гарно!
  - Учора я {купив|купую|буду купувати} квиток на поїзд.
  - Завтра я {буду подорожувати|подорожував|подорожую} по Україні.
  - Ввечері ми {ходили|ходимо|будемо ходити} в кіно.
  - Зараз Олена {замовляє|замовляла|замовить} борщ і салат.
  - Учора була гарна погода, і ми {гуляли|гуляємо|будемо гуляти} в парку.
  - Я вже {готовий|початок|сувенір} до рівня А2! Вітаю!
  type: fill-in
- focus: Match the situation to the correct A1 survival phrase.
  items:
  - Ordering coffee == Будь ласка, каву з молоком.
  - Asking for directions == Вибачте, як дістатися до метро?
  - Buying a souvenir == Скільки коштує ця вишиванка?
  - Meeting someone new == Привіт! Звідки ти?
  - Emergency == Допоможіть! Викличте швидку!
  - At the pharmacy == Дайте, будь ласка, таблетки від головного болю.
  - Saying goodbye == Дякую! До побачення!
  type: match-up
- focus: Review of key A1 grammar and survival vocabulary.
  items:
  - options:
    - Скільки коштує квиток?
    - Де тут квиток?
    - Дайте один квиток.
    question: How do you ask about the price of a ticket?
  - options:
    - Ходімо в кафе!
    - Я був у кафе.
    - Де кафе?
    question: You are inviting a friend to a cafe. What do you say?
  - options:
    - У мене болить голова.
    - У мене температура.
    - Я хворий.
    question: How do you say 'My head hurts'?
  - options:
    - Я на вулиці Хрещатик.
    - Мене звати Адам.
    - Я з Канади.
    question: Someone asks 'Де ви?'. How do you answer?
  - options:
    - Future
    - Past
    - Present
    question: What tense is 'Завтра я буду читати книгу'?
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- круасан (croissant, m)
- карта (map, f)
- лінія (line, f)
- фільм (film, m)
- познайомитися (to get acquainted)
- подорожувати (to travel)
- Лавра (Lavra — Kyiv monastery)
- готель (hotel, m)
required:
- готовий (ready, adj m)
- вітаю (congratulations — chunk)
- початок (beginning, m)
- сувенір (souvenir, m)
- квиток (ticket, m)
- зустріти (to meet)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Ранок: Початок дня у Києві

You love to **подорожувати** (travel). This is the culmination of all your hard work. You are living a day in a Ukrainian city. The past tense forms immediately root us in the reality of completed actions. 

**Ти прокинувся в готелі.** (You woke up in a hotel, masculine).
Or for feminine: **Ти прокинулася в готелі.** (You woke up in a hotel).

You look out the window of your **готель** (hotel) and check the weather to start planning your day.
- **Доброго ранку!** (Good morning!)
- **Яка сьогодні погода?** (What is the weather today?)
- **Сьогодні тепло і сонячно.** (Today it is warm and sunny.)

Down in the cafe, you use your survival skills. **Ти снідаєш у кафе.** (You eat breakfast in a cafe).

> **Ти:** Будь ласка, каву з молоком і круасан. *(Please, coffee with milk and a croissant.)*
> **Бариста:** Смачного! *(Enjoy your meal!)*
> **Ти:** Скільки коштує? *(How much does it cost?)*
> **Бариста:** Сто двадцять гривень. *(One hundred twenty hryvnias.)*
> **Ти:** Дякую! До побачення! *(Thank you! Goodbye!)*

:::tip
The question **Скільки коштує?** (How much does it cost?) is arguably your most important A1 survival tool. Memorize it well—you will use it every single day for everything from ordering a quick snack to purchasing train tickets.
:::

You step outside and need to find the city center.

> **Ти:** Вибачте, як дістатися до Хрещатика? *(Excuse me, how to get to Khreshchatyk?)*
> **Перехожий:** Їдьте на метро, станція Хрещатик. *(Go by metro, Khreshchatyk station.)*

You listen for the imperative **їдьте** (go/drive) to follow instructions. At the station, you handle the purchase. **Ти купуєш квиток.** (You buy a ticket).
**Один квиток, будь ласка.** (One ticket, please). 
Knowing how to use polite imperatives and direct requests makes navigating transit systems surprisingly manageable.

Underground, you navigate visually. **В метро ти дивишся на карту.** (In the metro you look at a map). You use an impersonal chunk to state a need:
**Тобі потрібна зелена лінія.** (You need the green line).
You are connecting different moments in time using your grammar skills.
**Зранку я снідав.** (In the morning I ate breakfast).
**Зараз я їду в метро.** (Now I am riding the metro).
This shift from the past to the present shows you are narrating your own life. You are ready to reach the heart of the city.

<!-- INJECT_ACTIVITY: order-day-events -->

## День: Прогулянка та нові друзі

You emerge from the underground into the bright sunlight. **Ти гуляєш по Хрещатику.** (You are walking along Khreshchatyk). 
**Яка гарна вулиця!** (What a beautiful street!). 
You see the sweeping architecture and point out landmarks.
- **Ця будівля — мерія.** (This building is the city hall.)
- **Цей майдан — Незалежності.** (This square is of Independence.)

Using demonstratives like **цей** (this, masculine) and **ця** (this, feminine) instantly makes your speech more precise. You can evaluate the entire scene around you. 

You spot a vibrant shop. **Ти бачиш великий магазин.** (You see a large store). **Ти заходиш і купуєш сувеніри.** (You enter and buy souvenirs).

> **Ти:** Скільки коштує ця вишиванка? *(How much does this vyshyvanka cost?)*
> **Продавець:** Тисяча двісті гривень. *(One thousand two hundred hryvnias.)*
> **Ти:** Дорого! А ця? *(Expensive! And this one?)*
> **Продавець:** Ця — вісімсот. *(This one is eight hundred.)*
> **Ти:** Добре, я беру! *(Good, I'll take it!)*

:::note
In Ukrainian, we simply say **сувенір** (souvenir). Do not say "пам'ятний сувенір" (memorable souvenir) as you might in English, because the word itself already implies that it is a memory of a place.
:::

In a quiet place, you strike up a conversation. **В кафе ти зустрічаєш Олену.** (In a cafe you meet Olena).

> **Олена:** Привіт! Ти звідки? *(Hi! Where are you from?)*
> **Ти:** Я з Канади. *(I am from Canada.)*
> **Олена:** Що ти робиш тут? *(What are you doing here?)*
> **Ти:** Я вивчаю українську! *(I am studying Ukrainian!)*

You seamlessly use present tense verbs to explain your current state. You have moved past basic drills and are forming genuine connections with locals. Olena smiles at your impressive progress.

> **Олена:** Як цікаво! Ходімо обідати! *(How interesting! Let's go have lunch!)*

You use the imperative **Ходімо** (Let's go) to accept the invitation. You settle at a table and order a warm meal. **Ти замовляєш борщ і вареники.** (You order borscht and varenyky). **Олена замовляє салат.** (Olena orders a salad).

> **Ти:** Смачно! *(Tasty!)*
> **Олена:** Ти добре говориш українською! *(You speak Ukrainian well!)*
> **Ти:** Дякую! *(Thank you!)*

<!-- INJECT_ACTIVITY: match-survival-phrases -->

## Вечір: Кіно та рефлексія

The day is winding down, but the city is still alive. You switch to the compound future tense to make plans.

> **Ти:** Що будемо робити ввечері? *(What will we do in the evening?)*
> **Олена:** Ходімо в кіно! *(Let's go to the cinema!)*
> **Ти:** Добре! О котрій? *(Good! At what time?)*
> **Олена:** О сьомій. *(At seven.)*

You use the critical structure of **о** plus the locative case to pinpoint the exact hour for your evening entertainment.

You are sitting in the dark theater, listening to the actors. **Ви дивитеся український фільм.** (You watch a Ukrainian film). At this stage, integrated communication and getting the gist are much more important than grammatical perfection.
- **Ти не все розумієш.** (You do not understand everything.)
- **Але багато!** (But a lot!)

You use linking words to describe the sequence of events to yourself later. **Спочатку ми купили квитки.** (First we bought tickets). **Потім ми дивилися фільм.** (Then we watched a film).

The movie ends, and you step back onto the street. **Після кіно ви йдете в ресторан.** (After the cinema you go to a restaurant). You reflect on the hours you have spent together. You express your feelings clearly using past and present forms. **Я дуже задоволений.** (I am very satisfied, masculine). **Я дуже задоволена.** (I am very satisfied, feminine). It feels incredible to navigate an entire evening exclusively in Ukrainian.

Back in your room, you summarize your day. **Ввечері в готелі ти думаєш про свій день.** (In the evening in the hotel you think about your day).
- **Сьогодні був чудовий день!** (Today was a wonderful day!)
- **Зранку я снідав у кафе.** (In the morning I ate breakfast in a cafe. — or **снідала** for feminine)
- **Потім я гуляв по місту.** (Then I walked around the city. — or **гуляла**)
- **Я познайомився з Оленою.** (I got acquainted with Olena. — or **познайомилася**)
- **Ввечері ми ходили в кіно і ресторан.** (In the evening we went to the cinema and a restaurant.)

Looking ahead, you make a plan:
- **Завтра я буду їздити по Києву.** (Tomorrow I will ride around Kyiv.)
- **Я хочу побачити Лавру!** (I want to see the Lavra!)

<!-- INJECT_ACTIVITY: fill-in-tenses -->

## Підсумок: Ти готовий до А2!

Take a moment to realize how far you have come. You can now greet people, introduce yourself, and proudly say where you are from (A1.1). You can describe your friends, your family, and everyday objects (A1.2). You talk easily about your daily habits, your likes, and your actions (A1.3). You know how to tell the time, discuss the weather, and name the days and months (A1.4). You can successfully navigate a major city, give directions, and use public transport (A1.5). You can order food in a restaurant, shop in a market, and handle money (A1.6). You know how to address people politely, give basic instructions, and connect ideas (A1.7). And finally, you can confidently talk about what happened in the past, handle emergencies, and make plans for the future (A1.8).

**Вітаю! Ти вивчив рівень А1.** (Congratulations! You learned the A1 level). Or for feminine: **Ти вивчила рівень А1.** (You learned the A1 level). You should be incredibly proud. But the journey continues! In A2, you will unlock the true engine of the language: **відмінки** (cases), which change word endings to show their role in a sentence. You will explore **доконаний і недоконаний вид** (perfective and imperfective aspect) to distinguish between ongoing and completed actions. You will learn the elegant synthetic future tense, like saying **прочитаю** (I will read) instead of just using **буду читати**. You will master subordinate clauses to build complex thoughts. **Це тільки початок!** (This is only the **початок** — beginning!). You can now truly live in a Ukrainian city.

Before you turn the page, test yourself with these real-world questions:
- Can you describe YOUR day in a Ukrainian city in 10 or more sentences?
- Can you walk into a cafe and order a full meal without using any English?
- Can you ask a stranger for directions to the metro and understand their answer?

If you can do these things, you are **готовий** (ready). You have built a solid, unbreakable foundation. Celebrate this incredible milestone. 

:::tip
Celebrate your progress! The phrase **Ти вже можеш жити в українському місті** (You can already live in a Ukrainian city) is not an exaggeration. The A1 level gives you all the fundamental building blocks to survive, connect, and thrive.
:::

**До зустрічі на рівні А2!** (See you at the A2 level!)

<!-- INJECT_ACTIVITY: a1-grammar-quiz -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: a1-finale
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

**Level: A1.4+ (Module 55/55) — BEGINNER**

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

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options


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
