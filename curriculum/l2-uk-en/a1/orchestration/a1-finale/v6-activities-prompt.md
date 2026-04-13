<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/a1-finale.yaml` file for module **55: A1 Finale** (a1).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 10 | 10+ | inline + workbook combined |
| Inline (lesson tab) | 4 | 6 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 6 | 9 | extended practice |
| Items per activity | 6 | — | each activity must have at least 6 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 4 inline activities AND at least 6 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** image-to-letter, letter-grid, match-up, watch-and-repeat, quiz, true-false, fill-in, classify
- **Inline priority (preferred):** image-to-letter, match-up, fill-in, quiz, watch-and-repeat
- **Workbook types:** fill-in, match-up, group-sort, anagram, unjumble, quiz, true-false, classify, divide-words, count-syllables, pick-syllables, observe, phrase-table, odd-one-out
- **Workbook priority (preferred):** fill-in, match-up, group-sort, anagram, unjumble
- **FORBIDDEN at this level:** cloze, error-correction, mark-the-words, translate, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, highlight-morphemes, grammar-identify, select

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 4–6 quick checks after key teaching points. Workbook = 6–9 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: match-up-survival-phrases -->`
- `<!-- INJECT_ACTIVITY: fill-in-tenses -->`
- `<!-- INJECT_ACTIVITY: order-chronological -->`
- `<!-- INJECT_ACTIVITY: quiz-a1-review -->`

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
  - Я вже {готовий|готова|впевнений} до рівня А2! Вітаю!
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
## Ранок (Morning)

Welcome to the culmination of your A1 journey. To test your skills, we will simulate a full day in Ukraine. You will use the past, present, and future tenses. You will navigate the city, order food, and meet people. This is where all the separate pieces you learned come together into natural communication. You are ready for this challenge.

Сьогодні чудовий день. Ти в місті Київ. Зранку ти прокинувся в готелі. Або ти прокинулася. Ти дивишся у вікно. Сьогодні дуже тепло і сонячно. Це ідеальна погода.
> *Today is a wonderful day. You are in the city of Kyiv. In the morning you woke up in a hotel. Or you woke up (female). You look into the window. Today it is very warm and sunny. This is perfect weather.*

This short text uses the past tense for a completed action (**прокинувся**, **прокинулася**) and the present tense for descriptions. The word **готель** (hotel) is in the locative case after **в** (in). It is time to start your day.

You are hungry, so you go to a local cafe for breakfast. Ordering food is a critical survival skill.

> **Ти:** Доброго ранку! *(Good morning!)*
> **Бариста:** Добрий день! Що ви будете? *(Good day! What will you have?)*
> **Ти:** Будь ласка, каву з молоком і круасан. *(Please, coffee with milk and a croissant.)*
> **Бариста:** Це все? *(Is that all?)*
> **Ти:** Так. Скільки коштує? *(Yes. How much does it cost?)*
> **Бариста:** Сто двадцять гривень. *(One hundred twenty hryvnias.)*
> **Ти:** Дякую! До побачення! *(Thank you! Goodbye!)*

Notice the use of **Доброго ранку** for morning greetings, while the barista replies with the standard **Добрий день**. You successfully ordered food using the word **круасан** (croissant) and handled money using numbers. The phrase **кава з молоком** uses the instrumental case for "with milk", which is a fixed chunk you learned earlier. When asking for the price, **скільки коштує** is your best friend.

Now you are ready to explore. You need to find the main street, Khreshchatyk. You ask a local on the street.

> **Ти:** Вибачте, як дістатися до Хрещатика? *(Excuse me, how to get to Khreshchatyk?)*
> **Перехожий:** Їдьте на метро. Станція Хрещатик. *(Go by metro. Station Khreshchatyk.)*
> **Ти:** Дякую дуже! *(Thank you very much!)*

Inside the station, you buy a **квиток** (ticket).

> **Ти:** Один квиток, будь ласка. *(One ticket, please.)*
> **Касир:** Вісім гривень. *(Eight hryvnias.)*

You check the **карта** (map) on the wall. The metro system is large, but you know how to read the signs.

Тобі потрібна зелена лінія. Ти чекаєш на поїзд. Ти їдеш у центр.
> *You need the green line. You wait for the train. You ride to the center.*

The word **лінія** (line) helps you navigate. The color adjective **зелена** (green) matches the feminine noun. You used a polite request: **Один квиток, будь ласка**. You are moving around the city like a local.

<!-- INJECT_ACTIVITY: match-up-survival-phrases -->

## День (Daytime)

You arrive at Khreshchatyk. This is the heart of the city. You walk along the street and take in the sights. The architecture is beautiful.

Ти гуляєш по Хрещатику. Яка гарна вулиця! Тут є старі будинки. Тут є нові кафе. Ти бачиш великий магазин. Ти заходиш у магазин. Ти купуєш сувеніри.
> *You walk along Khreshchatyk. What a beautiful street! Here there are old buildings. Here there are new cafes. You see a large store. You enter the store. You buy souvenirs.*

The phrase **по Хрещатику** means "along Khreshchatyk". You are looking for a **сувенір** (souvenir) for your family. Inside the store, you see traditional embroidered shirts. You need to use demonstrative pronouns like **цей** (this - masculine), **ця** (this - feminine), and **це** (this - neuter) to identify what you want.

> **Ти:** Скільки коштує ця вишиванка? *(How much does this vyshyvanka cost?)*
> **Продавець:** Тисяча двісті гривень. *(One thousand two hundred hryvnias.)*
> **Ти:** Дорого! А ця? *(Expensive! And this one?)*
> **Продавець:** Ця — вісімсот. *(This one is eight hundred.)*
> **Ти:** Добре, я беру! *(Good, I will take it!)*

Here, the pronoun **ця** perfectly matches the feminine noun **вишиванка**. The word **дорого** (expensive) is a useful adverb for shopping. You successfully contrasted two items without repeating the noun.

After shopping, you are hungry again. You go to a cafe for lunch. You share a table and **зустрічаєш** (you meet) a local named Olena. The verb **зустріти** (to meet) is an important social word. It is time to introduce yourself and make small talk.

> **Олена:** Привіт! Ти звідки? *(Hi! Where are you from?)*
> **Ти:** Я з Канади. А ти? *(I am from Canada. And you?)*
> **Олена:** Я з Києва. Що ти робиш тут? *(I am from Kyiv. What are you doing here?)*
> **Ти:** Я вивчаю українську! *(I study Ukrainian!)*
> **Олена:** Як цікаво! Ходімо обідати! *(How interesting! Let's go have lunch!)*

You use the imperative form **ходімо** (let's go) to enthusiastically suggest an action. Now you order your food.

Ти замовляєш борщ і вареники. Олена замовляє салат. Їжа дуже смачна. Олена сміється.
> *You order borscht and varenyky. Olena orders a salad. The food is very tasty. Olena laughs.*

> **Олена:** Смачно! Ти добре говориш українською! *(Tasty! You speak Ukrainian well!)*
> **Ти:** Дякую! *(Thank you!)*

<!-- INJECT_ACTIVITY: fill-in-tenses -->

## Вечір (Evening)

Lunch was great, and you want to spend more time with your new friend. You need to make plans for the evening using the future tense. This requires coordination.

> **Ти:** Що будемо робити ввечері? *(What will we do in the evening?)*
> **Олена:** Ходімо в кіно! *(Let's go to the cinema!)*
> **Ти:** Добре! О котрій? *(Good! At what time?)*
> **Олена:** О сьомій. *(At seven.)*

The phrase **що будемо робити** uses the future tense. You are asking about plans. Asking **о котрій** (at what time) is essential for scheduling.

You meet Olena at the cinema. You watch a local movie.

Ви дивитеся український фільм. Актори говорять швидко. Ти не все розумієш. Але ти розумієш багато слів! Це дуже приємно. Після кіно ви йдете в ресторан.
> *You watch a Ukrainian film. The actors speak fast. You do not understand everything. But you understand many words! This is very pleasant. After the cinema you go to a restaurant.*

Using linking words like **але** (but) and **після** (after) makes your story flow naturally. The word **фільм** (film) is a common noun you will hear often. The restaurant is located near the cinema, so you walk there together.

Ви йдете прямо. Потім ви йдете направо. Ресторан там. Це близько.
> *You go straight. Then you go to the right. The restaurant is there. It is close.*

The day is over. You are back in your room. You reflect on everything that happened, mixing tenses to tell a complete story.

Ввечері в готелі ти думаєш про свій день. Сьогодні був чудовий день! Зранку я снідав у кафе. Потім я гуляв по місту. Я познайомився з Оленою. Ввечері ми ходили в кіно. Потім ми були в ресторані.
> *In the evening in the hotel you think about your day. Today was a wonderful day! In the morning I had breakfast in a cafe. Then I walked around the city. I got acquainted with Olena. In the evening we went to the cinema. Then we were in a restaurant.*

You can also think about tomorrow. The verb **подорожувати** (to travel) describes your ultimate goal.

Завтра я буду подорожувати. Я буду їздити по Києву. Я хочу побачити Лавру!
> *Tomorrow I will travel. I will ride around Kyiv. I want to see the Lavra!*

The **Лавра** (Lavra) is a famous historical monastery in Kyiv. In this reflection, you naturally transition from the past tense to describe what you did, into the future tense to describe what you will do.

<!-- INJECT_ACTIVITY: order-chronological -->

## Підсумок: ти готовий/готова!

The course is ending. Imagine it is the last day of your A1 class. Two classmates talk about their progress.

> **Студент 1:** Це наш останній урок. *(This is our last lesson.)*
> **Студент 2:** Так. Я вивчив стільки! *(Yes. I learned so much!)*
> **Студент 1:** Я теж. Я вже говорю українською. *(Me too. I already speak Ukrainian.)*
> **Студент 2:** Давай писати повідомлення. Ось мій номер. *(Let's write messages. Here is my number.)*
> **Студент 1:** Звичайно! До зустрічі на А2! *(Of course! See you at A2!)*

Look back at your journey. You started with zero words. Now, you can greet people, introduce yourself, and say where you are from. You can describe people, objects, and your family. You can talk about your daily habits and what you like to do. You can tell the time, discuss the weather, and name the days of the week. You know how to navigate a city, give directions, and use public transport. You can confidently order food in a restaurant, shop for clothes, and handle Ukrainian money. You can make polite requests and connect your ideas. You can even narrate a story about the past and make plans for the future. You have built a massive linguistic foundation.

What is next? The A2 level awaits. In A2, you will learn the grammatical cases (**відмінки**). You will learn verb aspect, specifically the difference between imperfective and perfective verbs (**доконаний/недоконаний вид**), which changes how you talk about completed actions. You will learn the synthetic future tense, like the word **прочитаю** (I will read). These tools will make your sentences richer and more complex. But right now, you must celebrate your hard work.

Ти вивчив рівень А1! Вітаю! Ти вже можеш жити в українському місті. Ти готовий до нових тем. Це тільки початок!
> *You learned level A1! Congratulations! You already can live in a Ukrainian city. You are ready for new topics. This is only the beginning!*

The word **вітаю** is a fixed chunk used for congratulations, and **початок** (beginning) means there is much more to come. You are now **готовий** (ready) or **готова** (ready) to move forward.

Your final self-check task: Can you describe your day in a Ukrainian city in ten or more sentences? Try it now.

<!-- INJECT_ACTIVITY: quiz-a1-review -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: a1-finale
level: a1

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (10 total / 4–6 inline / 6–9 workbook,
# 6+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 6 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 6 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 6 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 6 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 6 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 6 pairs total

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
    items:                     # ← real output: ≥ 6 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 6 items total

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

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 10 activities.** Inline: 4–6. Workbook: 6–9. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 6 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 6.
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

- [ ] My output has **at least 4** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 6** workbook activities.
- [ ] **Total ≥ 10.**
- [ ] **Every** activity has **at least 6** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 4 and 6. I did NOT create more injection markers than 6.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
