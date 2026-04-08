<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-instrumental.yaml` file for module **31: Контрольна точка: Орудний відмінок** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-instrumental-mixed -->`
- `<!-- INJECT_ACTIVITY: fill-in-instrumental-transform -->`
- `<!-- INJECT_ACTIVITY: group-sort-functions -->`
- `<!-- INJECT_ACTIVITY: error-correction-instrumental -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Mixed Instrumental case quiz covering all functions from M21-M26
  items: 8
  type: quiz
- focus: Sentence transformation — put noun phrases into Instrumental with correct
    agreement
  items: 8
  type: fill-in
- focus: Sort Instrumental sentences by function (tool, companion, profession, spatial,
    temporal)
  items: 8
  type: group-sort
- focus: Find and correct grammar errors in sentences covering module topics
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- правильний (correct)
- словосполучення (phrase, word combination)
- описати (to describe)
- визначити (to identify, to determine)
required:
- орудний відмінок (instrumental case)
- вправа (exercise)
- контрольна точка (checkpoint)
- завдання (task)
- речення (sentence)
- відповідь (answer)
- текст (text)
- перевірка (check, test)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Частина 1: Розпізнавання та форми (Part 1: Recognition and Forms)

> **Студент:** Що ми робимо сьогодні? *(What are we doing today?)*
> **Вчитель:** Сьогодні у нас **контрольна точка** *(checkpoint)*. Ми повторюємо **орудний відмінок** *(instrumental case)*.

The **орудний відмінок** (instrumental case) is essential. It answers the questions **ким?** (by whom?) and **чим?** (by/with what?). In this module, we review five primary functions: tool or means (**інструмент або засіб**), accompaniment (**супровід**), profession (**професія**), spatial location (**місце**), and temporal expressions (**час**). Let us test your knowledge.

Let's review the basic noun endings. Words in the first and second declensions change depending on their stem (hard, soft, or mixed).

For hard stems, we use the endings **-ою** (feminine) and **-ом** (masculine/neuter).
* **Вона розмовляє з рідною сестрою.** (She is talking with her own sister.)
* **Родина сидить за великим столом.** (The family sits behind the large table.)

For soft and mixed stems, we use **-ею** and **-ем**.
* **Фермер працює із сирою землею.** (The farmer works with the damp earth.)
* **Чайки літають над синім морем.** (The seagulls fly above the blue sea.)

For words ending in a vowel sound, we use **-єю** and **-єм**.
* **Ми живемо однією великою мрією.** (We live by one great dream.)
* **Стежка йде самим краєм лісу.** (The path goes by the very edge of the forest.)

Nouns in the third and fourth declensions have special phonetic changes. When a third declension feminine noun ends in a single consonant, that consonant doubles.
* **Вона любить гуляти темною ніччю.** (She likes to walk during the dark night.)
* **Ми купуємо хліб із морською сіллю.** (We buy bread with sea salt.)

If the word ends in two consonants or an `р` or a labial consonant (б, п, в, м, ф), we do not double it. Instead, we use an apostrophe.
* **Вона пише картину з великою любов'ю.** (She paints the picture with great love.)
* **Він часто говорить з матір'ю.** (He often speaks with his mother.)

Neuter nouns of the fourth declension can have parallel forms.
* **Ми називаємо його своїм справжнім ім'ям.** (We call him by his real name.)
* **Також можна сказати: своїм іменем.** (Also one can say: by his name.)

Adjectives must agree with their nouns. For masculine and neuter words, the ending is **-им**. For feminine words, the ending is **-ою**. Personal pronouns also have specific forms. You must memorize these forms: **мною** (me), **тобою** (you), **ним** (him/it), **нею** (her), **нами** (us), **вами** (you, plural), and **ними** (them).

A crucial rule applies to third-person pronouns. When they follow a preposition, they require a mandatory **н-** at the beginning.

* **Він іде в кіно зі мною.** (He goes to the cinema with me.)
* **Я хочу танцювати тільки з тобою.** (I want to dance only with you.)
* **Сьогодні я обідаю з ним.** (Today I am having lunch with him.)
* **Ми довго розмовляли з нею вчора.** (We talked with her for a long time yesterday.)
* **Друзі хочуть поїхати з нами на море.** (Friends want to go to the sea with us.)
* **Кіт любить спати між ними.** (The cat likes to sleep between them.)

<!-- INJECT_ACTIVITY: quiz-instrumental-mixed -->

## Частина 2: Вибір та застосування (Part 2: Choice and Application)

Spatial prepositions describe where things are located. When we describe a static location — answering the question **де?** (where?) — we must use the **орудний відмінок** (instrumental case). The most common spatial prepositions are **над** (above), **під** (under), and **між** (between).

* **Кругле дзеркало висить над умивальником.** (The round mirror hangs above the washbasin.)
* **Велика картина висить над моїм ліжком.** (The large painting hangs above my bed.)
* **Чорна кішка спить під столом.** (The black cat sleeps under the table.)
* **Старі кросівки лежать під шафою.** (The old sneakers lie under the wardrobe.)
* **Кіт любить сидіти між вікнами.** (The cat likes to sit between the windows.)
* **Є вузький прохід між шафою і ліжком.** (There is a narrow passage between the wardrobe and the bed.)

Notice that **між** (between) always requires at least two nouns, and both must be in the instrumental case.
* **Вона стоїть між братом і сестрою.** (She stands between the brother and the sister.)

:::tip
Always ask yourself if the object is moving to a new location. If the object is stationary (**де?**), use the instrumental case with these prepositions.
:::

The most common mistake learners make is mixing up the tool function and the accompaniment function. Both use the instrumental case, but only accompaniment uses the preposition **з** (with). A tool NEVER takes a preposition.

* **Я пишу синьою ручкою.** (I am writing with a blue pen.) — *Tool*
* **Кухар ріже овочі гострим ножем.** (The cook cuts vegetables with a sharp knife.) — *Tool*

If you add **з** to a tool, it creates an absurd situation where you and the object are companions.
* ❌ **Я гуляю з ручкою.** (I am walking with a pen.) — *Incorrect for a tool!*
* ✅ **Я гуляю з братом.** (I am walking with my brother.) — *Accompaniment*

Only use **з** when two living beings or separate entities do something together.

We use the **орудний відмінок** (instrumental case) to describe professions or temporary states when using verbs like **бути** (to be) in the past or future tense, **стати** (to become), and **працювати** (to work).

* **Він хоче стати відомим архітектором.** (He wants to become a famous architect.)
* **Коли вона виросте, вона буде лікаркою.** (When she grows up, she will be a doctor.)
* **Моя старша сестра стала менеджеркою.** (My older sister became a manager.)
* **Він багато років працює перекладачем.** (He has worked as a translator for many years.)
* **У дитинстві я був тихим хлопчиком.** (In childhood, I was a quiet boy.)

This structure shows that the profession or state is not permanent. It is something you do or become.

Certain Ukrainian verbs require the **орудний відмінок** (instrumental case) directly, without any prepositions. The most common verbs in this category are **цікавитися** (to be interested in), **займатися** (to be occupied with / to do), and **пишатися** (to be proud of).

* **Я дуже цікавлюся українською історією.** (I am very interested in Ukrainian history.)
* **Мій брат цікавиться сучасною літературою.** (My brother is interested in modern literature.)
* **Щоранку я займаюся активним спортом.** (Every morning I do active sports.)
* **Діти займаються музикою та малюванням.** (The children study music and drawing.)
* **Батьки завжди пишаються своїм сином.** (Parents are always proud of their son.)
* **Ми щиро пишаємося вашим успіхом.** (We are sincerely proud of your success.)

Whenever you use these verbs, immediately put the following noun into the instrumental case. Do not use any prepositions like "в" or "про".

<!-- INJECT_ACTIVITY: fill-in-instrumental-transform -->
<!-- INJECT_ACTIVITY: group-sort-functions -->

## Частина 3: Вільне вживання (Part 3: Free Production)

Let us look at a natural dialogue. In this scene, friends recall a perfect day out. Notice how many times they use the **орудний відмінок** (instrumental case).

> **Оксана:** Пам'ятаєш наш чудовий день у парку? *(Do you remember our wonderful day in the park?)*
> **Тарас:** Звичайно! Ми **їхали автобусом**, і там було порожньо. *(Of course! We traveled by bus, and it was empty.)*
> **Оксана:** Так, а потім ми довго **гуляли з дітьми** біля озера. *(Yes, and then we walked for a long time with the children near the lake.)*
> **Тарас:** А на обід ми **їли канапки з сиром**. *(And for lunch, we ate sandwiches with cheese.)*
> **Оксана:** Було так тепло! Ми **сиділи під старою липою** і відпочивали. *(It was so warm! We sat under the old linden tree and rested.)*
> **Тарас:** Цей день був **найкращим**! *(This day was the best!)*

Every highlighted phrase uses the instrumental case for a different reason: means of transport, accompaniment, ingredient, and location.

When speaking Ukrainian, you must avoid translating directly from other languages. We call this linguistic hygiene. Avoid common Russianisms and calques by learning the correct Ukrainian verbs and their required cases.

1. **Language of communication:** Always use the pure instrumental case when saying what language you speak.
   ✅ **Ми розмовляємо українською мовою.** (We speak the Ukrainian language.)
   ❌ *Ми розмовляємо на мові.* (Incorrect calque).
2. **Missing someone:** The verb **сумувати** (to miss/be sad) requires the preposition **за** with the instrumental case.
   ✅ **Я дуже сумую за тобою.** (I miss you very much.)
   ❌ *Я сумую по тобі.* (Incorrect Russianism).
3. **Laughing at something:** The verb **сміятися** (to laugh) requires the preposition **з** and the *genitive* case. Do not use **над** with the instrumental case.
   ✅ **Ми голосно сміялися з нього.** (We laughed loudly at him.)
   ❌ *Ми сміялися над ним.* (Incorrect Russian error).

Let us analyze a visual scene to prepare for your next **завдання** (task). Imagine a busy kitchen. You must **описати** (to describe) the scene using the instrumental case.

> **На кухні багато людей. Батько ріже свіжий хліб гострим ножем.** *(There are many people in the kitchen. The father is cutting fresh bread with a sharp knife.)*
> **Мати готує смачний суп із м'ясом.** *(The mother is cooking a delicious soup with meat.)*
> **Велика миска з фруктами стоїть між вікнами.** *(A large bowl with fruit stands between the windows.)*
> **Білий рушник висить під раковиною.** *(A white towel hangs under the sink.)*
> **Маленький собака лежить під обіднім столом.** *(A small dog lies under the dining table.)*

This short **текст** (text) uses the instrumental case to show the tool (**гострим ножем**), the ingredients (**із м'ясом**), and the spatial relations (**між вікнами**, **під раковиною**, **під обіднім столом**).

Now it is time to write your own paragraph. A great way to practice the **орудний відмінок** (instrumental case) is to describe your daily routine. You can build complex **речення** (sentences) by combining different functions.

Use these sentence starters:
* **Я працюю...** (I work as...) — Add your profession.
* **Я добираюся на роботу...** (I commute to work by...) — Add a vehicle as a tool.
* **На роботі я часто розмовляю з...** (At work I often talk with...) — Add a colleague or client.
* **Ввечері я займаюся...** (In the evening I am occupied with...) — Add a hobby.

By linking these **словосполучення** (phrases), you create a rich narrative. Ensure that every noun phrase has the **правильний** (correct) ending.

Here is a sample narrative. Read this text about "My Tuesday" (**Мій вівторок**). It demonstrates the goal of your final writing task. It contains more than six different instrumental functions.

> **Зазвичай мій вівторок дуже активний. Я працюю головним архітектором у великій компанії. Вранці я п'ю чорну каву з молоком. Потім я їду на роботу швидким поїздом. Вдень я маю зустріч із новим клієнтом. Ми довго сидимо за круглим столом у конференц-залі. Після роботи я цікавлюся фотографією, тому йду в парк. Там я гуляю зі своїм собакою. Ввечері я готую вечерю і ріжу овочі великим ножем. Я завжди пишаюся своїм продуктивним днем!**

*(Usually my Tuesday is very active. I work as a chief architect in a large company. In the morning I drink black coffee with milk. Then I go to work by a fast train. During the day I have a meeting with a new client. We sit for a long time at a round table in the conference room. After work I am interested in photography, so I go to the park. There I walk with my dog. In the evening I cook dinner and cut vegetables with a large knife. I am always proud of my productive day!)*

<!-- INJECT_ACTIVITY: error-correction-instrumental -->

## Підсумок

You have completed the checkpoint! Let us do a quick **перевірка** (check). Can you answer these questions with a **правильна відповідь** (correct answer)?

*   **Can you form feminine endings with -ою/-ею?**
    *   Yes, I know that hard stems take **-ою** (**мамою**) and soft stems take **-ею** (**землею**).
*   **Do you remember to use 'н-' with 'з ним/нею'?**
    *   Yes, after prepositions, third-person pronouns must start with "н", like **з ними** (with them).
*   **Can you describe your profession?**
    *   Yes, I use the verb **працювати** and the instrumental case: **Я працюю лікарем** (I work as a doctor).
*   **Do you use 'з' only for company, not for tools?**
    *   Yes, I write **ручкою** (with a pen, no "з"), but I walk **з братом** (with a brother).

Review these points often. You are now ready for the next level of Ukrainian grammar!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-instrumental
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

**Level: A2 (Module 31/60) — ELEMENTARY**

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

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

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
