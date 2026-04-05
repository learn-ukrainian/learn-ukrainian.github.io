<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-foundations.yaml` file for module **8: Контрольна точка: Основи А2** (a2).

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

- `<!-- INJECT_ACTIVITY: exercise-1 -->`
- `<!-- INJECT_ACTIVITY: exercise-2 -->`
- `<!-- INJECT_ACTIVITY: exercise-4 -->`
- `<!-- INJECT_ACTIVITY: exercise-5 -->`
- `<!-- INJECT_ACTIVITY: exercise-3 -->`
- `<!-- INJECT_ACTIVITY: exercise-6 -->`
- `<!-- INJECT_ACTIVITY: exercise-7 -->`
- `<!-- INJECT_ACTIVITY: exercise-8 -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Mixed Grammar Quiz
  items: 8
  type: quiz
- focus: Sentence Transformation Drill
  items: 8
  type: fill-in
- focus: Short written responses using genitive and aspect
  items: 6
  type: fill-in
- focus: Find and fix mixed grammar errors — wrong aspect choice, wrong genitive endings,
    agreement mistakes
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. **Respect the `placement` field:**
- Hints with `placement: inline` go in the `inline:` array. They MUST have an `id` matching one of the injection markers above (e.g., `comprehension-check` or `reading-check`). If the marker id doesn't match exactly, use the closest match.
- Hints with `placement: workbook` go in the `workbook:` array.
- If no `placement` field, use this rule: quiz and reading go inline (2-3 max), everything else goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- правильний (correct)
- варіант (option, variant)
- обрати (to choose)
- написати (to write)
required:
- вправа (exercise)
- перевірка (check, test)
- контрольна точка (checkpoint)
- завдання (task)
- текст (text)
- речення (sentence)
- відповідь (answer)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Частина 1: Вправи на розпізнавання (Part 1: Recognition Exercises)

Welcome to the first major review of the A2 level. A **контрольна точка** (checkpoint) is an essential opportunity for a **перевірка** (check, test) of your knowledge. This module is not a strict exam to stress you out; rather, it is a moment to consolidate what you know and build confidence. You will work with a variety of tasks and questions. Every **вправа** (exercise) and **завдання** (task) in this section is designed to help you recognize grammatical patterns naturally, without constantly looking at translation tables.

Let us start by listening to two friends who are preparing for a Ukrainian language class. Read the dialogue aloud to practice your pronunciation.

> **Олена:** Марку, давай повторимо граматику перед уроком. *(повторимо — let's review)*
> **Марко:** Добре. Яка у нас сьогодні тема?
> **Олена:** Дієслова та родовий відмінок. Почнемо з простого. Скільки у тебе братів? *(почнемо з простого — let's start with the simple stuff)*
> **Марко:** У мене є п’ять брати... Ні, почекай. У мене є п’ять братів!
> **Олена:** Правильно! П’ять братів. Це родовий відмінок множини. *(множина — plural)*
> **Марко:** Це завжди важко для мене. А як щодо дієслів? Як правильно: «я писав лист» чи «я написав лист»? *(щодо — about / regarding)*
> **Олена:** Залежить від ситуації. Якщо дія вже завершена і є результат, це «написав». Це доконаний вид. *(завершена дія — completed action)*
> **Марко:** А «писав» — це процес? *(процес — process)*
> **Олена:** Так! Ти довго писав, але, можливо, не закінчив. *(можливо — maybe)*
> **Марко:** Зрозумів. Добре, давай робити вправи!

Notice how Olena gently corrects Marko. He tries to say he has five brothers, but he initially uses the wrong form. He says **п'ять брати**, treating it like the numbers two, three, or four. He quickly remembers that numbers five and above require a special form, and corrects himself to the Genitive plural: **п'ять братів**. They also discuss verbal aspect, comparing the long process of writing a letter to the final result of having written a letter completely.

Every Ukrainian verb has an aspect. Aspect (**вид**) tells us whether an action is ongoing or completed. The imperfective aspect (**недоконаний вид**) describes an action in progress, a repeated habit, or a general fact. It answers the question **що робити?** (what to do?). The perfective aspect (**доконаний вид**) describes a completed action, a specific result, or a single event that changes a situation. It answers the question **що зробити?** (what to get done?). Recognizing these two forms in a **текст** (text) is your first goal.

Often, you can recognize a perfective verb because it adds a prefix to the imperfective form. For example, the prefix **про-** often shows the completion of an action related to reading or living. The verb **читати** (to be reading) becomes **прочитати** (to read completely). The prefix **на-** often works with writing or drawing: **писати** (to be writing) becomes **написати** (to write completely). The prefix **за-** is frequently used for calling or planning: **телефонувати** (to be calling) becomes **зателефонувати** (to make a call).

Other times, the aspect is marked by a change in the suffix or the root of the verb itself. For instance, the imperfective verb **купувати** (to be buying) has the perfective partner **купити** (to buy). Recognizing these patterns is key to understanding any Ukrainian narrative. When you see a new text, try to identify the aspect of each verb before translating it.

> **Читаємо українською:**
> **Вона довго снідала, а потім вийшла на вулицю.** (She was having breakfast for a long time, and then she went outside.)
> **Я весь вечір писав цей текст і нарешті написав.** (I was writing this text all evening and finally wrote it.)
> **Сьогодні ми пішли в магазин і купили новий стіл у кімнату.** (Today we went to the store and bought a new table for the room.)
> **Щоранку я купую гарячу каву біля метро.** (Every morning I buy hot coffee near the subway.)
> **Мій старший брат зателефонував мені ввечері.** (My older brother called me in the evening.)

:::tip
Think of perfective verbs as taking a quick photograph of a finished result. Think of imperfective verbs as recording a long video of an ongoing process. You cannot record a long video of a sudden result!
:::

<!-- INJECT_ACTIVITY: exercise-1 -->

The Genitive case (**родовий відмінок**) is one of the most frequently used cases in the Ukrainian language. Its primary role is to show possession, absence, origin, and quantity. You will easily recognize the need for the Genitive case when it follows the negative word **немає** (there is no / does not exist). It is also strictly required after many common prepositions, such as **без** (without), **біля** (near), **від** (from), and **до** (to, until). When you see these trigger words in a sentence, you must change the ending of the noun.

For singular masculine nouns ending in a hard consonant, the Genitive ending is usually **-а**. For example, the word **студент** (student) becomes **студента**, and **брат** (brother) becomes **брата**. For masculine nouns ending in a soft consonant, the ending can be **-я**, such as **вчитель** (teacher) becoming **вчителя**. There is also an ending **-у** or **-ю** for abstract concepts, substances, and some places, such as **цукор** (sugar) becoming **цукру**, or **чай** (tea) becoming **чаю**.

For feminine nouns ending in **-а**, the ending changes to **-и**. The word **вода** (water) becomes **води**, and **машина** (car) becomes **машини**. For feminine nouns ending in **-я**, the ending changes to **-і**, meaning **пісня** (song) becomes **пісні**, and **вулиця** (street) becomes **вулиці**.

> **Читаємо українською:**
> **На жаль, у мене сьогодні немає нового олівця.** (Unfortunately, I do not have a new pencil today.)
> **Ми з родиною живемо біля великого парку.** (My family and I live near a large park.)
> **Він прийшов на важливий урок без зошита.** (He came to the important lesson without a notebook.)
> **Завтра ми йдемо до нового історичного музею.** (Tomorrow we are going to a new historical museum.)
> **На великому столі немає свіжого хліба.** (There is no fresh bread on the large table.)

<!-- INJECT_ACTIVITY: exercise-2 -->

## Частина 2: Вправи на вибір (Part 2: Choice Exercises)

Let us continue with another conversation. Two university students are discussing their homework.

> **(В університеті)**
> **Тарас:** Привіт! Ти вже зробив домашнє завдання?
> **Максим:** Ні, я ще роблю. Я довго читав новий текст.
> **Тарас:** А я швидко прочитав текст і написав правильну відповідь. *(швидко — quickly)*
> **Максим:** Молодець! А скільки у нас нових слів?
> **Тарас:** Дуже багато слів! Майже тридцять дієслів. *(майже — almost)*

In the dialogue above, Taras asks if Maksym has finished his homework. He uses the perfective verb **зробив** because he wants to know about the final result. Maksym replies that he is still in the process of doing it, using the imperfective **роблю**. Maksym explains that he spent a lot of time reading the text (**довго читав**). Taras, however, focuses on his fast result: he read the text completely (**прочитав**) and wrote the correct **відповідь** (answer). He also uses the Genitive plural to describe the large number of new words (**багато слів**).

Choosing between the perfective and imperfective aspect often depends on context clues in the **речення** (sentence). If a sentence focuses on the duration of an activity or a continuous process, you must use the imperfective aspect (**недоконаний вид**). Look for trigger words and phrases like **довго** (for a long time), **весь вечір** (all evening), **часто** (often), or **три години** (for three hours). These words signal that the action took time and the result is not the main focus.

On the other hand, if the action is completed, focuses on a final result, or describes a single specific event, you must use the perfective aspect (**доконаний вид**). Important context clues include words like **раптом** (suddenly), **нарешті** (finally), or prepositions denoting a timeframe for completion like **за годину** (in an hour). When you take a test, you need to **вибрати** (to choose) the **правильний варіант** (correct option) that matches the context clue.

Compare these two sentences. First, look at the imperfective version: **Я читав книгу дві години** (I was reading the book for two hours). Here, the focus is entirely on the process and the time spent. Now look at the perfective version: **Я прочитав книгу за дві години** (I read the book in two hours). This sentence emphasizes that the entire book is now finished, and it took a specific amount of time to achieve that final result. 

> **Читаємо українською:**
> **Вони весь день робили складне домашнє завдання.** (They were doing complex homework all day long.)
> **Він зробив цю вправу дуже швидко і правильно.** (He did this exercise very quickly and correctly.)
> **Мама готувала смачну вечерю, коли я зателефонував.** (Mom was preparing a delicious dinner when I called.)
> **Ми нарешті приготували традиційний український борщ.** (We finally prepared traditional Ukrainian borsch.)
> **Я довго вчив нові слова для тесту.** (I was learning new words for the test for a long time.)
> **Сьогодні вранці я вивчив десять нових дієслів.** (This morning I learned ten new verbs.)

:::note
If you see the word **часто** (often) or **завжди** (always), you are dealing with a repeated habit or a regular routine. You must always use the imperfective aspect for habits.
:::

<!-- INJECT_ACTIVITY: exercise-4 -->

When counting objects from five to twenty, the Ukrainian language uses the Genitive plural (**родовий відмінок множини**). This is often informally called the "Rule of 5-20". The exact same rule applies when using words that denote quantity, such as **багато** (many, a lot) and **мало** (few, a little). Unlike the Genitive singular, the Genitive plural endings can look quite different from the base form of the word, and they require practice to memorize.

There are several common endings you will encounter in the Genitive plural. Masculine nouns that end in a hard consonant usually take the ending **-ів**. For example, **п’ять братів** (five brothers) and **десять столів** (ten tables). If the noun ends in a soft consonant or **-й**, the ending changes slightly to **-їв**, such as **сім музеїв** (seven museums) or **багато героїв** (many heroes).

Many feminine and neuter nouns have a "zero ending" (**нульове закінчення**), meaning they drop their final vowel entirely to form the plural. For example, the word **книжка** (book) becomes **сім книжок** (seven books), **сестра** (sister) becomes **багато сестер** (many sisters), and **дівчина** (girl) becomes **десять дівчат** (ten girls). Notice how sometimes a vowel like **-о-** or **-е-** appears inside the word to make it easier to pronounce, such as **книжка** → **книжок**. Finally, some nouns take the ending **-ей**, such as **багато людей** (many people), **п'ять очей** (five eyes), and **вісім ночей** (eight nights).

> **Читаємо українською:**
> **У нашому класі зараз навчається п’ятнадцять студентів.** (Fifteen students are currently studying in our class.)
> **Вона пішла на ринок і купила десять великих яблук.** (She went to the market and bought ten large apples.)
> **На вулиці сьогодні холодно і дуже мало людей.** (It is cold on the street today and there are very few people.)
> **Почекай, у мене є тільки п'ять вільних хвилин.** (Wait, I only have five free minutes.)
> **Ми маємо багато хороших подруг у цьому місті.** (We have many good female friends in this city.)
> **Двадцять нових столів стоять у великій світлій кімнаті.** (Twenty new tables stand in the large bright room.)

<!-- INJECT_ACTIVITY: exercise-5 -->
<!-- INJECT_ACTIVITY: exercise-3 -->

## Частина 3: Практичне застосування (Part 3: Production Exercises)

Now, let us bring these grammar rules together to tell your own story. You can use the Genitive case to describe your environment and the things around you. Talk about what exists (**що є**) and what is missing (**чого немає**) in your room, your city, or your life. The Genitive case is perfect for expressing possession, a lack of resources, or describing the exact quantity of things you own.

You can also use verbal aspect to describe your recent activities and contrast them. Use imperfective verbs for your daily routines or ongoing tasks that you spent time on yesterday. Use perfective verbs to highlight specific achievements or things you successfully finished. This creates a natural, descriptive narrative that sounds much more authentic than simply listing facts.

> **Читаємо українською:**
> **У моєму місті багато гарних парків, але зовсім немає метро.** (In my city there are many beautiful parks, but there is absolutely no subway.)
> **Вчора я довго працював і нарешті написав цей складний звіт.** (Yesterday I worked for a long time and finally wrote this complex report.)
> **Сьогодні вранці я прокинувся дуже рано, о сьомій годині.** (This morning I woke up very early, at seven o'clock.)
> **Я маю багато хороших друзів, але зараз у мене немає вільного часу.** (I have many good friends, but right now I do not have free time.)
> **Кожного дня ми вчили нові слова, а вчора вивчили великий текст.** (Every day we were learning new words, and yesterday we learned a large text.)

:::tip
When you want to say "I don't have time" in Ukrainian, you must use the Genitive case: **У мене немає часу**. This is a very common phrase in daily conversation, and mastering it will make you sound much more natural.
:::

<!-- INJECT_ACTIVITY: exercise-6 -->

Let us look at how you can use these rules to organize and talk about your future plans. Here is a short conversation about the upcoming weekend.

> **(Плани на вихідні)**
> **Ірина:** Що ти будеш робити у суботу?
> **Андрій:** Я буду відпочивати. А в неділю я поїду до батьків. *(поїду — I will go by vehicle)*
> **Ірина:** Ти вже купив квиток на поїзд? *(квиток — ticket)*
> **Андрій:** Ще ні. Я куплю квиток сьогодні ввечері.
> **Ірина:** Бажаю гарних вихідних! *(бажаю — I wish)*

When talking about the weekend (**у вихідні**), it is important to use the future tense correctly to show your exact intentions. You need to decide whether your plan is an ongoing process or a specific goal. 

Use the imperfective future tense (**буду робити** - I will be doing) for ongoing plans, general processes, or activities you intend to spend time on without necessarily focusing on a final result. When you use the word **буду** with an infinitive, you are telling the listener that the action will take time. For example, **я буду читати** means you will spend time reading, perhaps enjoying the process, but not necessarily finishing the book.

Use the perfective future tense (**зроблю** - I will do, **напишу** - I will write) for specific, concrete results you intend to achieve or finish by Sunday night. This tense is formed by using the perfective verb with future endings, without the word **буду**. For example, **я прочитаю** means you will read the text entirely from start to finish. Combining both aspects makes your plans sound realistic, detailed, and completely natural to a native speaker. In the dialogue above, Andriy plans to spend time resting (**буду відпочивати**), but he has a specific goal to go to his parents (**поїду**) and to buy a ticket (**куплю**).

> **Читаємо українською:**
> **У вихідні я буду багато відпочивати та читати цікаву книгу.** (On the weekend I will rest a lot and read an interesting book.)
> **У суботу ввечері я подивлюся новий український фільм.** (On Saturday evening I will watch a new Ukrainian movie.)
> **Я хочу піти в магазин і купити багато свіжих фруктів.** (I want to go to the store and buy a lot of fresh fruits.)
> **Завтра ми будемо гуляти, а потім приготуємо смачну вечерю.** (Tomorrow we will be walking, and then we will prepare a delicious dinner.)
> **Я обов'язково напишу великого листа для свого старого друга.** (I will definitely write a large letter for my old friend.)

When you write a text about your own weekend, try to combine these forms. Tell your reader what you will be doing, and what you will successfully get done!

<!-- INJECT_ACTIVITY: exercise-7 -->
<!-- INJECT_ACTIVITY: exercise-8 -->

## Підсумок — Summary

You have reached the end of this checkpoint module! This was a major review of fundamental Ukrainian grammar, focusing on how we talk about actions and quantities. This is a critical step in building your foundation for the A2 level. Before you move on to the next topic, take a moment to evaluate your own progress.

Check yourself to see what you remember:
1. Can you explain why we say **п’ять машин** (five cars) but **дві машини** (two cars)?
2. When do you use the prefix **про-** with the verb **читати**? Does it change the meaning?
3. What are three common endings for the Genitive plural when counting objects?
4. How do you say "I do not have a pencil" using the correct case ending for a masculine noun?

If any of these questions feel difficult, do not worry. This is completely normal when learning a new language with a complex case system. You can always go back and review the previous modules to strengthen your foundation. Keep practicing these patterns, read the Ukrainian examples aloud every day, and the grammatical rules for cases and verbal aspects will soon become natural to you!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-foundations
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

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH, FOLK):

**Core seminar types (use for ALL seminar tracks):**
- **critical-analysis**: Analyze a claim, argument, or source. Required: id, prompt. Optional: target_text, questions[], model_answers[], evaluation_criteria[]
- **essay-response**: Extended written response. Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Passage with comprehension questions. Required: id, passage, questions[]. Optional: source
- **source-evaluation**: Evaluate a primary/secondary source. Required: id, source_text, criteria[], guiding_questions[]. Optional: source_metadata, model_evaluation
- **comparative-study**: Compare 2+ items/perspectives. Required: id, items_to_compare[], criteria[], prompt. Optional: model_answer
- **authorial-intent**: Analyze author's purpose/perspective. Required: id, excerpt, questions[]. Optional: model_answer
- **debate**: Structured debate exercise. Required: id, debate_question, positions[{label, arguments[]}]. Optional: analysis_tasks[]

**Linguistics types (OES, RUTH, and linguistic analysis in any track):**
- **etymology-trace**: Trace word evolution across periods. Required: id, instruction, stages[{period, form}]
- **translation-critique**: Evaluate translations. Required: id, original, translations[{text}]. Optional: focus_points[]
- **transcription**: Transcribe historical text. Required: id, original, answer. Optional: hints[]
- **paleography-analysis**: Analyze historical script. Required: id, instruction, image_url, hotspots[{x, y, label}]
- **dialect-comparison**: Compare dialect features. Required: id, text_a, text_b, features[{feature, variant_a, variant_b}]

**Also allowed in seminars (for testing language comprehension):**
- **quiz**: Multiple choice comprehension check. Required: id, instruction, items[{question, options[], correct}]. Use for testing understanding of debates, source arguments, not factual recall.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct, explanation}]. Good for testing understanding of historiographic positions.

**FORBIDDEN in seminar tracks** (these test mechanics, not comprehension):
match-up, fill-in, cloze, group-sort, unjumble, anagram, mark-the-words, error-correction, translate, order

### Seminar activity rules

1. **3-9 activities per seminar module.** Not more.
2. **Required types:** Every seminar module MUST have at least one `reading` + one `essay-response` + one `critical-analysis`.
3. **The golden rule:** Can the learner answer without reading the Ukrainian text? If YES → rewrite the activity. Activities test COMPREHENSION and CRITICAL THINKING, never factual recall.
4. **All instructions in Ukrainian.** Seminar learners are B2+.
5. **Follow the plan's activity_hints.** They specify exactly what to generate.

---

## Learner Level Context

**Level: A2 (Module 8/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
