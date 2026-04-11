<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-verbs.yaml` file for module **46: Контрольна точка: Вид, час і рух** (a2).

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

- `<!-- INJECT_ACTIVITY: group-sort -->`
- `<!-- INJECT_ACTIVITY: fill-in -->`
- `<!-- INJECT_ACTIVITY: quiz -->`
- `<!-- INJECT_ACTIVITY: error-correction -->`

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

У цій **контрольній точці** (checkpoint) ми об'єднаємо три ключові теми граматики: **вид дієслова** (verb aspect), часи та **дієслова руху** (motion verbs). Ми повторимо, як один префікс може змінити значення всього речення з процесу на результат. Ви вже знаєте, що українські дієслова працюють у парах. The **недоконаний вид** (imperfective aspect) describes the action itself, while the **доконаний вид** (perfective aspect) describes the finish line. Let's see how this works in practice.

In the past tense, aspect is a choice between a process (or habit) and a result. Use the **недоконаний вид** when you want to emphasize *that* you did something, or *how long* it took. Use the **доконаний вид** when you want to emphasize the final product.

*   **Вчора я довго писав статтю.** (Yesterday I wrote the article for a long time.) — This is a process. We focus on the time spent: **довго** (for a long time). The verb is **писати** (to write — impf).
*   **Вчора я нарешті написав статтю.** (Yesterday I finally wrote/finished the article.) — This is a result. The article is done. We use the prefix **на-** to form **написати** (to write — pf).
*   **Вона щовечора читала книгу.** (She read a book every evening.) — This is a habit (**щовечора** — every evening). We must use the imperfective **читати** (to read).
*   **Вона прочитала книгу за ніч.** (She read the book in one night.) — This is a single, completed event. We use the perfective **прочитати** (to read — pf).

The future tense also forces you to choose between process and result. Ukrainian has two ways to talk about the future, depending on the aspect. The analytical future (складена форма) uses **бути** + infinitive, and it always requires the **недоконаний вид**. The simple future (проста форма) uses the **доконаний вид** with personal endings.

*   **Завтра о п'ятій я буду працювати.** (Tomorrow at five I will be working.) — This describes a process in the future. You are in the middle of doing it.
*   **Я зроблю цю роботу до вечора.** (I will do this work by evening.) — This guarantees a result. By evening, the work will be finished. We use the perfective **зробити**.
*   **Ми будемо готувати обід разом.** (We will be preparing lunch together.) — The focus is on the activity of cooking.
*   **Ми приготуємо обід дуже швидко.** (We will prepare lunch very quickly.) — The focus is on the finished lunch.

Ukrainian has a unique, rhythmic alternative to the "буду + infinitive" future tense: the synthetic future (**складна форма**). This form is used only for the **недоконаний вид** (process/intent). It adds the endings **-му, -меш, -ме, -мемо, -мете, -муть** directly to the infinitive (without the final -ти). Historically, this comes from the infinitive plus an old form of the verb **мати** (to have). It sounds very authentic and is widely used in modern Ukrainian.

*   **Завтра я працюватиму вдома.** (Tomorrow I will be working at home.) — This is exactly the same meaning as "я буду працювати".
*   **Ти знатимеш усі правила.** (You will know all the rules.) — Same as "ти будеш знати".
*   **Ми читатимемо цю статтю на уроці.** (We will be reading this article in class.)
*   **Вони житимуть у Києві.** (They will live in Kyiv.)

<!-- INJECT_ACTIVITY: group-sort -->

## Частина 2: Дієслова руху та наказовий спосіб (Part 2: Motion Verbs and Imperatives)

**Дієслова руху** (motion verbs) in Ukrainian require you to think about *how* and *where* you are going. English uses "to go" for everything. Ukrainian splits "to go" into two pairs: **іти/ходити** (by foot) and **їхати/їздити** (by transport). Inside each pair, we contrast unidirectional motion (a specific trip right now) with multidirectional motion (a regular habit or general movement).

*   **Я зараз іду додому.** (I am going home right now.) — Unidirectional, by foot. A specific trip happening at this moment.
*   **Я щодня ходжу до парку.** (I go to the park every day.) — Multidirectional/habitual, by foot. A regular action (**щодня** — every day).
*   **Сьогодні ми їдемо на роботу машиною.** (Today we are going to work by car.) — Unidirectional, by transport. One specific trip.
*   **Ми часто їздимо в Карпати.** (We often go to the Carpathians.) — Multidirectional/habitual, by transport. A repeating event.

When you use **дієслова руху**, you must use the correct prepositions to show directionality. The preposition changes the case of the noun.

*   **До + Родовий відмінок** (Genitive) shows destination: **Ми їдемо до Львова.** (We are going to Lviv.) **Він іде до школи.** (He is going to school.)
*   **З/Зі + Родовий відмінок** (Genitive) shows origin/movement from: **Ми їдемо зі Львова.** (We are going from Lviv.) **Він іде зі школи.** (He is coming from school.)
*   **На + Знахідний відмінок** (Accusative) shows movement to an event, an open space, or a specific activity: **Я йду на роботу.** (I am going to work.) **Вона їде на концерт.** (She is going to a concert.)
*   **В/У + Знахідний відмінок** (Accusative) shows movement *into* an enclosed space: **Я йду в магазин.** (I am going into the store.)

The **наказовий спосіб** (imperative mood) is how we give commands, advice, or suggestions. For the 2nd person singular ("you" informal), the ending is usually **-и** or zero ending. For the plural/formal, add **-те** or **-іть**. For the 1st person plural ("let's"), add **-мо** or **-імо**. Stress is very important here: it changes the grammatical meaning.

*   **Читай цей текст!** (Read this text!) — 2nd person singular.
*   **Читайте цей текст!** (Read this text!) — 2nd person plural/formal.
*   **Читаймо цей текст!** (Let's read this text!) — 1st person plural.
*   **Пиши!** (Write!) / **Пишіть!** (Write!) / **Пишімо!** (Let's write!)
*   **Ти рОбиш** (You do/are doing — present tense) vs. **ЗробИ!** (Do it! — imperative).

Sometimes we need to give a command or express a wish indirectly to a 3rd person ("let him/her/them"). For this, we use the particles **хай** or **нехай** plus the present/future tense verb. We also have a special construction for personal wishes: **Vocative case + будь/будьте + Instrumental case**.

*   **Хай він читає цей текст.** (Let him read this text.)
*   **Нехай вони знають правду.** (Let them know the truth.)
*   **Маріє, будь щасливою!** (Maria, be happy!) — The name is in the Vocative, the adjective is in the Instrumental.
*   **Друже, будь обережним!** (Friend, be careful!)

<!-- INJECT_ACTIVITY: fill-in -->

## Частина 3: Комплексні завдання (Part 3: Integrated Tasks)

Let's look at how all these elements work together in a real situation. Here is an oral review where a teacher asks a student to retell his weekend.

> **Пані Олена:** Марку, розкажи, що ти робив у вихідні? *(Marko, tell me, what did you do on the weekend?)*
> **Марко:** У суботу я довго спав. Потім я ходив у магазин. *(On Saturday I slept for a long time. Then I went to the store.)*
> **Пані Олена:** Добре. А що ти купив? *(Good. And what did you buy?)*
> **Марко:** Я купив хліб і молоко. У неділю я поїхав до брата. Я нарешті написав есе для університету. *(I bought bread and milk. On Sunday I went to my brother's. I finally wrote the essay for the university.)*
> **Пані Олена:** Чудово! *(Excellent!)*
> **Марко:** Пані Олено, давай підемо на перерву? *(Ms. Olena, let's go on break?)*
> **Пані Олена:** Марку, правильно казати: "Ходімо на перерву". *(Marko, it is correct to say: "Let's go on break".)*

Marko correctly used the imperfective **спав** for a long process, the multidirectional **ходив** for a round trip to the store, and the perfective **поїхав** and **написав** for completed results. However, his teacher corrected a very common error at the end.

:::caution
English speakers often struggle with Ukrainian verbs because English relies on the single verb "to go" and has a completely different tense structure. Another major issue is the influence of Russian calques.

1.  **"Я іду на роботу на автобусі."** — ❌ Error. You cannot use **іти** (by foot) with transport. Correct: **Я їду на роботу автобусом.**
2.  **"Завтра я буду прочитати книгу."** — ❌ Error. You cannot use **буду** with a perfective verb (**прочитати**). Correct: **Завтра я прочитаю книгу.** (I will read/finish the book tomorrow) OR **Завтра я буду читати книгу.** (I will be reading the book tomorrow).
3.  **"Давай підемо!"** — ❌ Error. The construction "давай + verb" is a Russian calque. Authentic Ukrainian uses the 1st person plural imperative ending **-мо / -імо**. Correct: **Ходімо!** (Let's go!) or **Зробімо!** (Let's do it!).
:::

Now let's listen to two friends planning a hike in the Carpathian mountains. Notice how they use motion verbs for giving directions and imperatives for making suggestions.

> **Андрій:** Ірино, ми поїдемо в Карпати у п'ятницю. *(Iryna, we will go to the Carpathians on Friday.)*
> **Ірина:** Супер! Як ми будемо їхати? *(Super! How will we be traveling?)*
> **Андрій:** Ми поїдемо потягом до Франківська. Потім треба їхати автобусом. *(We will go by train to Frankivsk. Then we need to go by bus.)*
> **Ірина:** Добре. Що мені взяти? *(Good. What should I take?)*
> **Андрій:** Обов'язково візьми карту і теплий одяг. Купи воду. *(Definitely take a map and warm clothes. Buy water.)*
> **Ірина:** Зрозуміла. Ідіть до лісу обережно. Друзі, будьмо готові! *(Understood. Go to the forest carefully. Friends, let's be ready!)*

Andriy uses the perfective future **поїдемо** for the planned trip, while Iryna uses the analytical imperfective future **будемо їхати** to ask about the process of travel. Andriy gives direct commands: **візьми** (take — pf) and **купи** (buy — pf). Iryna finishes with a beautiful wish: **будьмо готові** (let's be ready).

Let's integrate all these skills into a short narrative. Imagine a traveler visiting Kyiv for the first time.

**Влітку мій друг приїхав до Києва. Він ніколи раніше не був в Україні. У перший день він просто йшов вулицями і дивився на архітектуру. Він часто заходив у кав'ярні, пив каву і слухав людей. Увечері він сказав мені: "Завтра я піду в музеї. Я оглядатиму місто цілий день. Ходімо разом!" Я відповів: "Звичайно, я покажу тобі найкращі місця". Ми чудово провели час.** (In the summer my friend arrived in Kyiv. He had never been to Ukraine before. On the first day he just walked the streets and looked at the architecture. He often went into cafes, drank coffee and listened to people. In the evening he told me: "Tomorrow I will go to the museums. I will be viewing the city all day. Let's go together!" I answered: "Of course, I will show you the best places." We had a wonderful time.)

Notice how the prefixes **по-** and **при-** interact with aspect and motion. The imperfective verb **ішов** (was walking) describes the process of movement through the streets. But when we add **при-** to form **приїхав** (arrived by transport), it becomes a perfective result — the arrival is complete. When the traveler plans his next day, he says **піду** (I will go/set off). The prefix **по-** adds the meaning of starting a journey, creating a perfective future verb. He then contrasts this with **оглядатиму** (I will be viewing) — the synthetic future describing the continuous process of exploring the city.

<!-- INJECT_ACTIVITY: quiz -->

<!-- INJECT_ACTIVITY: error-correction -->

## Підсумок

Ця **перевірка** (review, check) охоплює основні механізми українських дієслів. Час для **самоперевірки** (self-check). Ask yourself the following questions. If you can answer "так" (yes) to all of them, 

*   Чи можу я обрати правильний вид дієслова у минулому часі? (Do I know when to use the imperfective for a process or habit, and the perfective for a result?)
*   Чи розрізняю я "буду читати" та "прочитаю"? (Can I form both the analytical future for process and the simple future for result?)
*   Чи знаю я, коли використовувати "іти", а коли "ходити"? (Can I correctly choose between unidirectional and multidirectional motion verbs by foot and by transport?)
*   Чи вмію я утворювати наказовий спосіб для всіх осіб? (Can I form commands for "you", "let's", and use "хай" for 3rd person without using Russian calques?)
*   Чи можу я побажати комусь чогось (Vocative + будь + Instrumental)?

Якщо ви **впевнено** (confidently) відповіли «так» на ці питання, ви добре засвоїли матеріал. Якщо є якась **помилка** (error), ви завжди можете повернутися до попередніх уроків і **виправити** (to correct) свої знання.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-verbs
level: a2

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
2. Run `query_cefr_level` on any word you're unsure about — it must be a2-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
