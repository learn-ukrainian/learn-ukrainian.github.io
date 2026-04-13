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

Ця контрольна точка допоможе вам повторити орудний відмінок. (This checkpoint will help you review the Instrumental case.) Орудний відмінок відповідає на питання **ким?** та **чим?**. (The Instrumental case answers the questions by whom? and with what?.) У попередніх модулях ми вивчали п'ять головних функцій цього відмінка. (In previous modules, we studied the five main functions of this case.) Ось ці функції (Here are these functions):

1. Інструмент (Tool): Я малюю **олівцем**. (I draw with a pencil.)
2. Супровід (Accompaniment): Вона гуляє **з другом**. (She walks with a friend.)
3. Професія (Profession): Він працює **лікарем**. (He works as a doctor.)
4. Місце (Location): Собака спить **під столом**. (The dog sleeps under the table.)
5. Час (Time): Ми зустрілися раннім **ранком**. (We met in the early morning.)

Давайте згадаємо закінчення іменників першої та другої відмін. (Let's recall the endings of nouns of the first and second declensions.) For these nouns, the endings depend strictly on whether the stem is hard, soft, or mixed. This pattern is consistent across the language.

Перша відміна (First declension - mostly feminine and some masculine nouns ending in -а/-я):
- Тверда група (Hard stem) бере закінчення **-ою**: **сестра** → **сестрою** (with a sister), **машина** → **машиною** (by car), **книга** → **книгою** (with a book).
- М'яка та мішана групи (Soft and mixed stems) беруть закінчення **-ею**: **земля** → **землею** (by/with earth), **межа** → **межею** (by the boundary), **груша** → **грушею** (with a pear).
- Голосний + м'який знак (Vowel + soft sign) бере закінчення **-єю**: **мрія** → **мрією** (with a dream), **надія** → **надією** (with hope).

Друга відміна (Second declension - masculine and neuter nouns):
- Тверда група бере закінчення **-ом**: **стіл** → **столом** (under a table), **брат** → **братом** (with a brother), **батько** → **батьком** (with a father).
- М'яка та мішана групи беруть закінчення **-ем**: **море** → **морем** (by the sea), **олівець** → **олівцем** (with a pencil), **хлопець** → **хлопцем** (with a boy).
- Голосний + м'який знак бере закінчення **-єм**: **край** → **краєм** (by the edge), **музей** → **музеєм** (with a museum).

Іменники третьої та четвертої відмін мають свої фонетичні правила. (Nouns of the third and fourth declensions have their own phonetic rules.) For feminine nouns ending in a consonant (III declension), the final consonant doubles if it is soft or hissing.
- Подовження приголосних (Doubling of consonants): **сіль** → **сіллю** (with salt), **ніч** → **ніччю** (at night), **зустріч** → **зустріччю** (with a meeting).

If the stem ends in a labial consonant (б, п, в, м, ф) or «р», we use an apostrophe instead of doubling.
- Апостроф (Apostrophe): **кров** → **кров'ю** (with blood), **мати** → **матір'ю** (with a mother).

Neuter nouns of the IV declension ending in -я often have parallel forms.
- Паралельні форми (Parallel forms): **ім'я** → **ім'ям** або **іменем** (by name). Обидва варіанти правильні. (Both options are correct.)

Прикметники та займенники також змінюють свою форму. (Adjectives and pronouns also change their form.) Adjectives must agree with the noun they describe in gender, number, and case.
- Чоловічий та середній рід (Masculine and neuter): **-им**. Наприклад: **з новим другом** (with a new friend), **під великим столом** (under a big table).
- Жіночий рід (Feminine): **-ою** / **-ею**. Наприклад: **з гарною подругою** (with a beautiful friend), **синьою ручкою** (with a blue pen).

Особові займенники мають спеціальні форми. (Personal pronouns have special forms.) Вони звучать так: **мною** (me), **тобою** (you), **ним** (him/it), **нею** (her), **нами** (us), **вами** (you all), **ними** (them).

:::caution
Remember the mandatory **н-** rule! When a third-person pronoun follows any preposition, it must start with «н-». You must always say **з ним** (with him) and **з нею** (with her), never *з їм* or *з єю*.
:::

У першій вправі ви прочитаєте короткий текст про чийсь день. (In the first exercise, you will read a short text about someone's day.) You will identify all nouns in the Instrumental case and label their function (tool, companion, profession, spatial, temporal). Далі ви будете змінювати слова в дужках. (Next, you will change the words in parentheses.) You will put nouns into the correct Instrumental form, changing (**брат**) into **братом**, (**подруга**) into **подругою**, and (**море**) into **морем**. Нарешті, ви утворите множину з називного відмінка. (Finally, you will form the plural from the Nominative case.) You will change Nominative plurals like (**руки**) to **руками**, (**олівці**) to **олівцями**, and (**діти**) to **дітьми**.

<!-- INJECT_ACTIVITY: quiz-instrumental-mixed -->

## Частина 2: Вибір та застосування (Part 2: Choice and Application)

Просторові прийменники часто вимагають орудного відмінка. (Spatial prepositions often require the Instrumental case.) When describing a static location that answers the question **де?** (where?), the prepositions **над** (above), **під** (under), and **між** (between) must take the Instrumental case.

- **Над** (above, without physical contact): Дзеркало висить **над умивальником**. (The mirror hangs above the sink.) Картина знаходиться **над ліжком**. (The painting is located above the bed.)
- **Під** (under): Кішка сидить **під столом**. (The cat sits under the table.) Моє тепле взуття лежить **під ліжком**. (My warm shoes lie under the bed.)
- **Між** (between - requires two or more objects): Тут є зручний прохід **між шафою і ліжком**. (Here is a convenient passage between the wardrobe and the bed.) Я сиджу **між братом і сестрою**. (I am sitting between my brother and sister.)

У наступних завданнях ви будете вибирати правильний прийменник. (In the following tasks, you will choose the correct preposition.) You will choose among **з, над, під, перед, за, між** to complete spatial and temporal sentences.

Дуже важливо розрізняти інструмент та супровід. (It is very important to distinguish a tool and accompaniment.) A common error for English speakers is using the preposition **з** (with) for tools. In Ukrainian, **з** is strictly for accompaniment (being with someone) or characteristics. For tools or the means of an action, you must use the bare Instrumental case without any preposition.

- Інструмент (Tool - correct): Я швидко пишу **ручкою**. (I write quickly with a pen.) Ми їмо суп **ложкою**. (We eat soup with a spoon.)
- Супровід (Accompaniment - absurd): Я гуляю **з ручкою**. (I walk with a pen — as if the pen is a person.)
- Супровід (Accompaniment - correct): Я гуляю **з другом**. (I walk with a friend.) Вона п'є каву **з молоком**. (She drinks coffee with milk.)

Ви будете вирішувати, коли потрібен прийменник. (You will decide when a preposition is needed.) This will test your tool vs. accompaniment discrimination, like choosing between **писати ручкою** and **ходити з другом**.

Дієслова стану та професії також потребують орудного відмінка. (Verbs of state and profession also require the Instrumental case.) When describing a temporary state, a future profession, or a change in status, verbs like **бути** (to be) in the future or past tense, **стати** (to become), and **працювати** (to work) govern the Instrumental case. The Nominative case is only used for permanent facts in the present tense (e.g., Вона — студентка).

- **Бути** (to be): Він **буде архітектором**. (He will be an architect.) Вона **була хорошою студенткою**. (She was a good student.)
- **Стати** (to become): Моя молодша сестра **стала менеджеркою**. (My younger sister became a manager.)
- **Працювати** (to work): Я **працюю головним перекладачем**. (I work as a chief translator.) Він **працює лікарем**. (He works as a doctor.)

Ви будете трансформувати речення. (You will transform sentences.) You will change Nominative sentences into sentences using **бути** or **стати** + Instrumental for professions. Наприклад: Вона лікарка → Вона **буде лікаркою**. Ви також будете вибирати правильну форму словосполучень у тестах. (You will also choose the correct form of phrases in tests.) For example, you must select the correct form of an adjective + noun phrase, choosing **з гарним другом** over *з гарний/гарною*.

Деякі дієслова керують орудним відмінком без прийменників. (Some verbs govern the Instrumental case without prepositions.) These include verbs expressing deep interest, hobbies, or pride. They are essential for talking about your personality.

- **Цікавитися** (to be interested in): Я дуже **цікавлюся українською історією**. (I am very interested in Ukrainian history.) Вони **цікавляться сучасним мистецтвом**. (They are interested in modern art.)
- **Займатися** (to be engaged in / to practice): Вона професійно **займається спортом**. (She plays sports professionally.) Ми кожного дня **займаємося музикою**. (We study music every day.)
- **Пишатися** (to be proud of): Я **пишаюся своїм старшим братом**. (I am proud of my older brother.) Батьки **пишаються розумними дітьми**. (The parents are proud of the smart children.)

Запам'ятайте ці дієслова, вони дуже корисні. (Remember these verbs, they are very useful.) They make your speech sound much more natural and expressive in daily conversations.

<!-- INJECT_ACTIVITY: fill-in-instrumental-transform -->
<!-- INJECT_ACTIVITY: group-sort-functions -->

## Частина 3: Вільне вживання (Part 3: Free Production)

Давайте подивимося на природну розмову. (Let's look at a natural conversation.) Two friends are reminiscing about a perfect picnic they had recently.

> **Олег:** Пам'ятаєш наш пікнік минулого тижня? Це був чудовий день! *(Do you remember our picnic last week? It was a wonderful day!)*
> **Марія:** Так, звичайно. Ми поїхали туди **автобусом**. *(Yes, of course. We went there by bus.)*
> **Олег:** Ми так добре гуляли **з дітьми** біля озера. *(We had such a good walk with the children near the lake.)*
> **Марія:** А потім ми їли смачні бутерброди **з ковбасою** і пили гарячий чай. *(And then we ate delicious sandwiches with sausage and drank hot tea.)*
> **Олег:** Ми довго сиділи **під старою липою**, і було дуже тепло. *(We sat for a long time under an old linden tree, and it was very warm.)*
> **Марія:** Згодна, цей день був **найкращим**! *(I agree, this day was the best!)*

Notice how densely the Instrumental case is used here. It expresses transport (**автобусом**), accompaniment (**з дітьми**), ingredients (**з ковбасою**), spatial location (**під старою липою**), and state (**найкращим**).

Коли ви говорите українською, важливо уникати русизмів. (When you speak Ukrainian, it is important to avoid Russianisms.) Pay attention to these important distinctions regarding the Instrumental case:

- Говорити про мову (Talking about language): Always use the bare Instrumental case for the language you speak. Say **Я розмовляю українською мовою** (I speak Ukrainian), and never use the preposition «на» (*на українській мові* is a direct calque). You can also just say **Я розмовляю українською** (I speak Ukrainian).
- Відчувати сум (Feeling sadness): The verb **сумувати** (to miss) requires the preposition **за** + Instrumental case. Say **Я сумую за тобою** (I miss you), not *по тобі*. Ми **сумуємо за домом** (We miss home).
- Сміятися (Laughing): The verb **сміятися** (to laugh) requires the preposition **з** + Genitive case. Say **сміятися з когось** (to laugh at someone), not *над кимось* (which incorrectly uses the Instrumental case).

:::tip
Always use **розмовляти українською** (to speak Ukrainian) without any prepositions. This elegant construction highlights the unique character of the Ukrainian language and shows advanced language skills.
:::

Уявіть собі кухню. (Imagine a kitchen.) Describing a picture is a great way to practice these grammar rules in context.

На кухні дуже шумно і весело. (It is very noisy and fun in the kitchen.) Мама готує смачну вечерю для всієї родини. (Mom is cooking a delicious dinner for the whole family.) Вона обережно ріже свіжий хліб **гострим ножем**. (She carefully cuts fresh bread with a sharp knife.) На столі стоїть велика миска **з салатом**. (A large bowl with salad stands on the table.) Ця миска знаходиться прямо **між вікнами**. (This bowl is located right between the windows.) Наш старий собака солодко спить **під столом**. (Our old dog sleeps sweetly under the table.) Чистий рушник висить **під раковиною**. (A clean towel hangs under the sink.)

У наступній вправі ви будете описувати схожу картинку. (In the next exercise, you will describe a similar picture.) You will state who is cooking, what tools they use, what ingredients are on the table, and where objects are located in space. 

Щоб вільно говорити, треба вміти відповідати на різні питання. (To speak fluently, you need to know how to answer various questions.) Practice answering these open-ended questions out loud:
- **Ким ти працюєш?** (What is your profession?)
- **Чим ти захоплюєшся?** (What are you passionate about?)
- **З ким ти живеш?** (Who do you live with?)
- **Що знаходиться перед твоїм будинком?** (What is in front of your house?)

When you write your own paragraph, use these helpful sentence starters to build a complete story:
- **Я працюю...** (I work as...)
- **Я добираюся на роботу...** (I commute to work by...)
- **Ввечері я займаюся...** (In the evening, I am engaged in...)

Ці фрази допоможуть вам структурувати текст логічно. (These phrases will help you structure the text logically.)

Ось приклад тексту «Мій вівторок». (Here is an example text "My Tuesday".) This model paragraph demonstrates the goal of your final writing task. Your task will be an 8-10 sentence writing prompt: «Опишіть свій типовий день. Розкажіть про свою професію, як ви добираєтесь на роботу, з ким ви обідаєте, і що ви готуєте на вечерю.» (Describe your typical day. Tell about your profession, how you get to work, who you have lunch with, and what you cook for dinner.) You must use at least 6 different Instrumental constructions.

> Я працюю **вчителем** у великій школі. Кожного ранку я добираюся на роботу **автобусом**. Я дуже цікавлюся **історією**, тому читаю історичні книги в дорозі. Вдень я обідаю **з колегами** у шкільному кафе. Наш стіл завжди знаходиться **під великим вікном**. Ввечері я повертаюся додому і готую вечерю **з дружиною**. Ми часто їмо гарячий борщ **із сметаною**. Після вечері я займаюся **спортом**, а потім ми гуляємо **з собакою**. Я дуже задоволений своїм **життям**.

This short text successfully uses the Instrumental case for professions, tools, transport, interests, accompaniment, and spatial relations. 

<!-- INJECT_ACTIVITY: error-correction-instrumental -->

## Підсумок

Перевірте свої знання за допомогою цього списку. (Check your knowledge using this list.) Read each question and answer it honestly.

- Can you form feminine endings with **-ою / -ею**? Наприклад: **сестрою**, **землею**, **ручкою**.
- Do you remember to use the letter **н-** with third-person pronouns like **з ним** and **з нею**? (Remember: never say *з їм*).
- Can you describe your profession using **працювати** or **бути** + Instrumental case? Наприклад: Я працюю **лікарем**, вона буде **вчителькою**.
- Do you confidently use **з** only for company, and the bare Instrumental case for tools? Наприклад: Я пишу **олівцем**, but я гуляю **з другом**.

Орудний відмінок робить вашу українську природною та багатою. (The Instrumental case makes your Ukrainian natural and rich.) You can now confidently describe how you do things, what tools you use, who you spend time with, and where things are located in physical space. Use these skills щодня (every day) to think in Ukrainian!
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
