<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-verbs.yaml` file for module **46: Контрольна точка: Вид, час і рух** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 10 | 10+ | inline + workbook combined |
| Inline (lesson tab) | 3 | 5 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 7 | 10 | extended practice |
| Items per activity | 10 | — | each activity must have at least 10 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 3 inline activities AND at least 7 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** quiz, true-false, fill-in, match-up, group-sort, classify, mark-the-words
- **Inline priority (preferred):** fill-in, match-up, true-false
- **Workbook types:** cloze, error-correction, fill-in, unjumble, translate, match-up, group-sort, odd-one-out, quiz, true-false, mark-the-words, observe, phrase-table
- **Workbook priority (preferred):** error-correction, cloze, unjumble, translate, fill-in
- **FORBIDDEN at this level:** anagram, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, highlight-morphemes, grammar-identify

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 3–5 quick checks after key teaching points. Workbook = 7–10 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: group-sort-verb-forms -->`
- `<!-- INJECT_ACTIVITY: fill-in-mixed-drill -->`
- `<!-- INJECT_ACTIVITY: quiz-error-correction -->`
- `<!-- INJECT_ACTIVITY: error-correction-verb-forms -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Mixed drill — complete sentences requiring aspect choice, motion verb selection,
    and imperative formation across all M35-40 topics
  items: 8
  type: fill-in
- focus: Error correction — identify and fix verb errors (wrong aspect, motion type,
    imperative form, or future formation)
  items: 8
  type: quiz
- focus: Sort verb forms into categories — imperfective past, perfective past, synthetic
    future, analytical future, imperative
  items: 8
  type: group-sort
- focus: Find and fix verb form errors — wrong aspect, wrong motion verb type, wrong
    imperative form, wrong future tense construction
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- впевнено (confidently)
- самоперевірка (self-check)
- обрати (to choose — pf.)
required:
- контрольна точка (checkpoint)
- перевірка (review, check)
- завдання (task, exercise)
- помилка (error, mistake)
- виправити (to correct)
- вид дієслова (verb aspect)
- дієслова руху (motion verbs)
- наказовий спосіб (imperative mood)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Частина 1: Вид дієслова — минулий і майбутній час (Part 1: Aspect in Past and Future)

Ми вже вивчили багато важливих тем. Тепер настала **контрольна точка** (checkpoint). Наша головна мета сьогодні — це комплексна **перевірка** (review, check) ваших знань про українські дієслова. Ми детально згадаємо **вид дієслова** (verb aspect), щоб ви могли правильно описувати минулий та майбутній час. Також ми обов'язково повторимо **дієслова руху** (motion verbs) та **наказовий спосіб** (imperative mood). Ці теми дуже важливі для вільного, природного спілкування. Коли ви говорите про свої плани, подорожі або даєте поради друзям, ви завжди використовуєте ці граматичні конструкції. Уявіть таку життєву ситуацію: вчитель та студент розмовляють на уроці. Це типове усне **завдання** (task, exercise) для перевірки знань. Вчитель запитує студента про його минулі вихідні та розпитує про плани на майбутнє. Зверніть увагу на те, які дієслова вони обирають.

> **Вчитель:** Добрий день, Максиме! Розкажи, будь ласка, що ти робив на вихідних? *(Tell me, please, what did you do on the weekend?)*
> **Студент:** Добрий день! У суботу я був удома. Я дуже довго готував обід для родини. *(I cooked lunch for my family for a very long time.)*
> **Вчитель:** Це дуже цікаво. І що саме ти приготував? *(And what exactly did you cook [finish cooking]?)*
> **Студент:** Я приготував велику каструлю смачного борщу. *(I cooked a large pot of delicious borscht.)*
> **Вчитель:** Чудово! А що ти будеш робити завтра ввечері, після університету? *(And what will you be doing tomorrow evening?)*
> **Студент:** Завтра я буду читати нову книгу про історію України. *(Tomorrow I will be reading a new book.)*
> **Вчитель:** Як ти думаєш, ти прочитаєш її до кінця тижня? *(Will you read it [finish it] by the end of the week?)*
> **Студент:** Так, я прочитаю її дуже швидко, бо вона цікава. *(Yes, I will read it very quickly.)*

In Ukrainian, understanding the past tense relies heavily on the **вид дієслова**. This is the foundation of Ukrainian storytelling. We use the imperfective aspect (**недоконаний вид**) when we want to focus on a continuous process, a regular habit, or a background action in the past. For example, `Він довго писав листа` *(He was writing a letter for a long time)* describes a continuous process. We do not know if the letter is finished; we only see the action happening over time.

Conversely, we use the perfective aspect (**доконаний вид**) when we focus on the final result, a specific sequence of events, or a single, completed action. For example, `Він швидко написав листа` *(He wrote / finished writing a letter quickly)* tells us the action is completely finished and the result (the letter) exists now.

Look at these common aspectual pairs (**видова пара**):
*   `робити` (to do/make - process) — `зробити` (to do/make - result)
*   `читати` (to read - process) — `прочитати` (to read - result)
*   `готувати` (to cook - process) — `приготувати` (to cook - result)

When you speak, always ask yourself: is this a process (`що робив?`) or a result (`що зробив?`). If you say `Я читав книгу`, your friend might naturally ask: `Ти прочитав її?` *(Did you finish it?)*.

The future tense also strictly depends on the **вид дієслова**. If you want to describe a planned process, a continuous action, or a regular habit in the future, you must use the imperfective aspect. We form this analytical future using the auxiliary verb `бути` (to be) and the infinitive of the main verb: `я буду читати` *(I will be reading)*, `ти будеш працювати` *(you will be working)*. This form focuses entirely on the activity itself.

If you want to express a planned result or a single, completed action in the future, you use the perfective aspect. This is the simple synthetic future form. It is created by adding present-tense endings to a perfective verb base, often with a prefix: `я прочитаю` *(I will read completely)*, `я напишу` *(I will write completely)*.

:::caution
A very common **помилка** (error, mistake) among learners is mixing these two forms. You can NEVER use the auxiliary verb `буду` with a perfective infinitive. For example, saying `буду прочитати` or `буду написати` is strictly incorrect in Ukrainian grammar. You must choose either the continuous process (`я буду читати`) or the completed result (`я прочитаю`).
:::

## Частина 2: Дієслова руху та наказовий спосіб (Part 2: Motion Verbs and Imperatives)

Now we will move forward and review another essential topic: **дієслова руху** (motion verbs) and how to give commands or suggestions. Giving correct directions, discussing your daily commute, and making active plans with friends is a key part of everyday life. In Ukrainian, verbs of motion have special rules that differ significantly from English. Let's look at a new real-life situation. Two friends, Oksana and Taras, are planning a hiking trip to the Carpathian Mountains. They need to discuss their logistics, choose the right transport, and give each other instructions. Pay attention to how they talk about their movement and how they make suggestions using the **наказовий спосіб**.

> **Оксана:** Тарасе, ми їдемо в Карпати у п'ятницю? *(Taras, are we going to the Carpathians on Friday?)*
> **Тарас:** Так! Ми поїдемо на поїзді ввечері після роботи. *(We will go by train in the evening after work.)*
> **Оксана:** Дуже добре. Що мені взяти з собою? *(What should I take with me?)*
> **Тарас:** Візьми теплий одяг і зручні черевики для гір. *(Take warm clothes and comfortable boots for the mountains.)*
> **Оксана:** Зрозуміла. А коли ми підемо в гори? *(Understood. And when will we go to the mountains?)*
> **Тарас:** У суботу вранці. Ходімо купувати квитки просто зараз! *(Let's go buy tickets right now!)*
> **Оксана:** Погоджуюсь, ходімо! *(I agree, let's go!)*

In Ukrainian, **дієслова руху** require you to make a clear distinction between moving on foot and moving by transport. This is fundamentally different from the English verb "to go".

*   **On foot:** `іти` (unidirectional) / `ходити` (multidirectional)
*   **By transport:** `їхати` (unidirectional) / `їздити` (multidirectional)

Unidirectional verbs describe a specific, single trip in one direction at a given moment (for example, `Я йду до школи` — *I am walking to school right now*). Multidirectional verbs describe your habits, regular round trips, or moving around without a specific direction (for example, `Я ходжу до школи щодня` — *I walk to school every day*).

To talk about future plans or completed trips, we add prefixes to these verbs. The prefix `по-` indicates the start of a trip or a future plan (`Я поїду до Львова` — *I will go to Lviv by transport*). The prefix `при-` indicates arrival at the destination (`Він приїде завтра` — *He will arrive tomorrow*).

Remember to use the correct prepositions with motion verbs: use `з` + Genitive case for moving "from" a place (`з Києва`), `до` + Genitive case for moving "to" a place (`до Львова`), and `на` + Accusative case for moving "to" an event or an open surface (`на концерт`, `на роботу`).

The **наказовий спосіб** is the grammatical tool we use to give commands, advice, or suggestions to other people. We form it differently depending on who we are addressing:

*   **2nd person singular/plural:** We use the endings `-и` / `-іть` or `-й` / `-йте`. For example: `роби` / `робіть` *(do!)*, `читай` / `читайте` *(read!)*. You must also choose the correct aspect. `Пиши` means "write!" (process), while `Напиши` means "finish writing!".
*   **3rd person:** We use the particle `хай` or `нехай` plus the standard present or future tense form of the verb. For example: `хай читає` *(let him/her read)*, `хай знає` *(let him/her know)*.
*   **1st person plural (suggestions):** When you want to say "let's do something", we use the ending `-імо` or `-ймо`. For example: `робімо` *(let's do)*, `читаймо` *(let's read)*, `ходімо` *(let's go)*.

:::tip
A very common Russian calque is using the word "давай" plus a verb to make suggestions (for example, saying `давай поговоримо`). In natural, correct Ukrainian, you should avoid this. Always use the proper 1st person plural imperative form. Say `поговорімо` замість цього (instead of this).
:::

<!-- INJECT_ACTIVITY: group-sort-verb-forms -->

## Частина 3: Комплексні завдання (Part 3: Integrated Tasks)

In real-life conversations, you never use grammar rules in complete isolation. You must combine them dynamically. Choosing the correct aspect, selecting the right motion verb, and using the proper mood simultaneously is absolutely essential for natural, fluent Ukrainian storytelling. When you tell a story about your life or a recent trip, you build a complex narrative sequence. You will use imperfective verbs to set the background scene or describe your regular habits. Then, you will use perfective verbs to show the main events, actions, and concrete results. You will also use verbs of motion to explain exactly how you traveled there, and you might quote a conversation using the imperative mood to give advice. Let's see how these different grammatical elements interact in practice.

<!-- INJECT_ACTIVITY: fill-in-mixed-drill -->

Read this short narrative text carefully. It models the upcoming exercise. It clearly contrasts multidirectional habits with a unidirectional future plan, and it mixes different verb aspects to build a complete story.

> Моя сім'я дуже любить гори. Кожного літа ми **їздимо** (multidirectional habit - by transport) в Карпати на два тижні. Там ми багато гуляємо лісом і **робимо** (imperfective process) красиві фотографії. Але цього року ми **поїдемо** (unidirectional future perfective) до моря. Ми вже купили квитки на поїзд. Завтра ми **зробимо** (perfective result) всі важливі покупки для відпочинку. Мама суворо каже мені: "**Візьми** (imperative perfective) теплий светр!"

Notice how `їздимо` shows a repeated action every summer, while `поїдемо` shows a specific, planned trip. Similarly, `робимо` is a continuous process of taking photos, but `зробимо покупки` is a finished task. In the exercises below, you will need to fill in similar blanks and choose the correct forms for many different situations.

<!-- INJECT_ACTIVITY: quiz-error-correction -->

Before you take the final test, let's systematically review some typical mistakes so you can successfully and швидко **виправити** (to correct) them. Look at these examples and understand why they are wrong:

1.  *`Він щодня зробив вправи.`* This is a critical **помилка**. The time marker `щодня` (every day) clearly indicates a regular habit. A habit always requires the imperfective aspect. The correct form is: `Він щодня робив вправи.`
2.  *`Я буду поїхати до Києва у вівторок.`* As we learned, you absolutely cannot combine the auxiliary verb `буду` with a perfective verb like `поїхати`. For a planned result or a complete trip, you must use the simple future tense: `Я поїду до Києва у вівторок.`
3.  *`Ми ідемо туди кожного літа відпочивати.`* The phrase `кожного літа` (every summer) means this is a recurring, round-trip journey. The unidirectional verb `ідемо` (which also means on foot!) is incorrect here. We need the multidirectional verb for transport: `Ми їздимо туди кожного літа відпочивати.`

<!-- INJECT_ACTIVITY: error-correction-verb-forms -->

Now it is time for your final **завдання** (task, exercise) in this checkpoint module. You will write a short, cohesive text. Write 8-10 complete sentences narrating a weekend trip. You must follow these specific grammatical requirements:

1.  Include past tense aspect pairs: use at least one imperfective verb to describe a background process or habit, and one perfective verb to show a completed result.
2.  Use at least two different motion verbs with their corresponding prepositions (for example, `поїхав до`, `ходив по`). Make sure you distinguish between foot and transport!
3.  Include one direct speech sentence giving a clear suggestion to a friend using the imperative mood (for example, `ходімо в кіно` or `візьми квитки`).
4.  Include one friendly wish using the Vocative case, the verb `бути` in the imperative, and the Instrumental case (for example, `Олено, будь щасливою!` or `Тарасе, будь здоровим!`).

Complete this task **впевнено** (confidently) and завжди робіть **самоперевірка** (self-check) to verify your forms before submitting!

## Підсумок

Це була дуже важлива **контрольна точка**. Давайте зробимо підсумок ваших знань. Дайте відповідь на ці запитання, щоб **обрати** (to choose) свій наступний крок:

*   Can I confidently choose between the imperfective and perfective aspect in the past and future tenses? Do I clearly understand the difference between `читав` (process) and `прочитав` (result), or `буду читати` and `прочитаю`?
*   Do I know exactly when to use unidirectional motion verbs (like `іти`, `їхати`) versus multidirectional ones (like `ходити`, `їздити`)? Can I correctly use the prefixes `по-` and `при-`?
*   Can I form imperatives for all persons, especially avoiding the `давай` calque? Can I correctly say `ходімо` and `хай знає`?
*   Can I make warm wishes using the Vocative case and the Instrumental case (for example, `будь здоровим`)?

If you answered "yes" to these questions, you have successfully mastered the core verb system of this level. You are fully ready to advance to module A2.7!
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-verbs
level: a2

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (10 total / 3–5 inline / 7–10 workbook,
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

**Level: A2 (Module 46/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

### Pattern: grammar-verbs-present [§4.2.4.1]
**Дієвідмінювання в теперішньому часі** (Present tense conjugation)
- **fill-in** — Відмінюй дієслово: Вставити правильну форму дієслова за особою та числом / Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Розподілити дієслова за типом дієвідміни / Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Зіставити особові займенники з формами дієслова / Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Знайти неправильно відмінене дієслово та виправити / Find incorrectly conjugated verb and fix it
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує відмінювання. Англійські дієслова не змінюються за особами

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

### Pattern: grammar-verb-aspect [A2 §4.2.3.1, B1 §4.2.3.1]
**Вид дієслова** (Verb aspect)
- **group-sort** — Доконаний чи недоконаний?: Розподілити дієслова за видом — розпізнати видові пари / Sort verbs by aspect — recognize aspect pairs
  - Instruction: *Розподіліть дієслова за видами*
- **match-up** — Утвори видові пари: Зіставити недоконане з доконаним дієсловом / Match imperfective ↔ perfective aspect pairs
  - Instruction: *З'єднайте видові пари*
- **fill-in** — Який вид доречний?: Обрати правильний вид для контексту (тривалість vs завершеність) / Choose correct aspect for context (duration vs completion)
  - Instruction: *Оберіть правильну форму*
- **quiz** — Визнач вид дієслова: Визначити вид поданого дієслова / Identify aspect of a given verb
**Anti-patterns (DO NOT generate):**
- ❌ translate: Англійський минулий час НЕ відповідає 1:1 українському виду. «I read» = і «читав», і «прочитав»
- ❌ quiz-only: Вид — це вибір мовця. Учні мають практикувати вибір виду в контексті, а не тільки розпізнавати

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
- **Total: 10 activities.** Inline: 3–5. Workbook: 7–10. The audit gate FAILS the module if you ship fewer.
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
2. Run `query_cefr_level` on any word you're unsure about — it must be a2-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **at least 3** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 7** workbook activities.
- [ ] **Total ≥ 10.**
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
