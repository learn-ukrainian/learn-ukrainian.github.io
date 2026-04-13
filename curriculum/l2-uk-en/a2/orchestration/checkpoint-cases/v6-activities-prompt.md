<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-cases.yaml` file for module **39: Контрольна точка: Відмінки та множина** (a2).

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

- `<!-- INJECT_ACTIVITY: group-sort-cases -->`
- `<!-- INJECT_ACTIVITY: fill-in-mixed-cases -->`
- `<!-- INJECT_ACTIVITY: quiz-error-correction -->`
- `<!-- INJECT_ACTIVITY: error-correction-mixed -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Mixed case drill — complete sentences requiring all 7 cases, singular and
    plural
  items: 8
  type: fill-in
- focus: Error correction — identify and fix case errors in sentences
  items: 8
  type: quiz
- focus: Sort noun forms by case (Nom., Gen., Dat., Acc., Instr., Loc., Voc.)
  items: 8
  type: group-sort
- focus: Find and fix mixed case errors in sentences — wrong endings after prepositions,
    animate/inanimate confusion, Gen.Pl. mistakes
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- самоперевірка (self-check)
- впевнено (confidently)
- вихідний день (day off)
required:
- перевірка (check, review)
- контрольна точка (checkpoint)
- завдання (task, exercise)
- помилка (error, mistake)
- виправити (to correct)
- відмінок (grammatical case)
- множина (plural)
- однина (singular)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Частина 1: Форми множини (Part 1: Plural Forms)

Welcome to this **контрольна точка** (checkpoint). Today, our goal is a comprehensive **перевірка** (check, review) of your skills. We will look at how the Ukrainian language changes words in the **множина** (plural). The plural in Ukrainian affects every **відмінок** (grammatical case), not just the Nominative. When you move from **однина** (singular) to plural, the endings change entirely. This is essential for talking about groups of people, daily routines, and quantities.

> **Наталя:** Де мої речі? *(Where are my things?)*
> **Олег:** Твої речі лежать там. *(Your things are lying there.)*
> **Наталя:** А де мої книги і зошити? *(And where are my books and notebooks?)*
> **Олег:** Вони на столі. *(They are on the table.)*

First, let's review the Nominative plural endings. Most nouns take «-и», «-і/ї», or «-а/я». 

> Ось мій **стіл**. Там стоять великі **столи**. *(Here is my table. Big tables stand there.)*
> Це наша **земля**. Ми любимо наші **землі**. *(This is our land. We love our lands.)*
> Це старе **місто**. Я люблю красиві **міста**. *(This is an old city. I love beautiful cities.)*

However, the most frequently used words often have irregular forms. You must memorize these completely because you will use them every single day:
- **друг** (friend) changes to **друзі** (friends).
- **людина** (person) changes to **люди** (people).
- **дитина** (child) changes to **діти** (children).
- **око** (eye) changes to **очі** (eyes).

> Мої **друзі** хочуть знімати квартиру разом. *(My friends want to rent an apartment together.)*
> На вулиці стоять невідомі **люди**. *(Unknown people are standing on the street.)*
> Маленькі **діти** граються у парку. *(Little children are playing in the park.)*
> У неї красиві блакитні **очі**. *(She has beautiful blue eyes.)*

Your **завдання** (task, exercise) is to form the Nominative plural for a mixed-gender list of ten singular nouns. Think about how words like «книга», «зошит», and «вікно» change.

Next, we review the complex Genitive plural forms. These are often considered the hardest. Many feminine and neuter nouns take a "zero ending" (they lose their final vowel). For example, «книга» becomes «книг», and «місто» becomes «міст». Sometimes, a fleeting vowel appears to make pronunciation easier: «земля» becomes «земель». 

> У бібліотеці дуже багато **книг**. *(There are very many books in the library.)*
> В Україні багато великих **міст**. *(There are many large cities in Ukraine.)*
> Ми купили багато солодких **яблук**. *(We bought many sweet apples.)*

Most masculine nouns take the «-ів» ending.
> В університеті тисячі **студентів**. *(There are thousands of students at the university.)*
> На столі лежить п'ять **олівців**. *(Five pencils lie on the table.)*
> У нас немає нових **комп'ютерів**. *(We do not have new computers.)*
> Ми знаємо назви п'яти **морів**. *(We know the names of five seas.)*

Finally, some nouns take the «-ей» ending.
> Вони працювали п'ять довгих **ночей**. *(They worked for five long nights.)*
> У магазині є багато гарних **речей**. *(There are many nice things in the store.)*
> Ми чекаємо важливих **гостей**. *(We are waiting for important guests.)*

To master this, your next task is to form the Genitive plural for ten challenging nouns. Can you form the Genitive plural for **теля** (calf)? It becomes **телят**!

We use the Genitive plural extensively with quantities and special nouns. After numbers five and higher, or words like **багато** (many) and **мало** (few), you must use the Genitive plural.
> У мене є п'ять **років** досвіду. *(I have five years of experience.)*
> На площі було багато **людей**. *(There were many people on the square.)*
> У класі мало **учнів**. *(There are few students in the class.)*

Some nouns only exist in the plural. These are called pluralia tantum. Examples include **гроші** (money), **окуляри** (glasses), and **штани** (pants). Since they are always plural, their Genitive forms are also plural: «грошей», «окулярів», «штанів». 
> У мене немає **грошей**. *(I have no money.)*
> Я не бачу без **окулярів**. *(I cannot see without glasses.)*
> У магазині немає чорних **штанів**. *(There are no black pants in the store.)*

Complete quantity expressions with the correct Genitive plural forms: `п'ять...`, `багато...`, `скільки...`?

## Частина 2: Який відмінок? (Part 2: Which Case?)

Choosing the correct case depends heavily on the verb. Different verbs govern different cases. For instance, the verb **допомагати** (to help) requires the Dative case. You are giving help "to" someone.
> Я завжди допомагаю своїй **сестрі**. *(I always help my sister.)*
> Син допомагає **батькові**. *(The son helps the father.)*
> Ми радісно допомагаємо новим **друзям**. *(We gladly help new friends.)*

The verb **бачити** (to see) requires the Accusative case for direct objects.
> Ми бачимо красивих **людей** на вулиці. *(We see beautiful people on the street.)*
> Я бачу великий **будинок**. *(I see a big house.)*

Meanwhile, the verb **користуватися** (to use) requires the Instrumental case.
> Вона користується новим **словником**. *(She uses a new dictionary.)*
> Вони щодня користуються **комп'ютерами**. *(They use computers every day.)*

Prepositions also dictate case selection. The preposition «у» or «в» takes the Locative case when describing a location (answering the question "where?").
> Вони живуть у **Чернівцях**. *(They live in Chernivtsi.)*
> Мої старі книги лежать у **сумці**. *(My old books lie in the bag.)*

However, it takes the Accusative case when describing direction or destination (answering the question "where to?").
> Діти швидко йдуть в **школу**. *(The children are walking quickly to school.)*
> Ми завтра їдемо у **Київ**. *(We are traveling to Kyiv tomorrow.)*

Similarly, the preposition «з» takes the Genitive case when showing origin (from where?).
> Він приїхав з великого **міста**. *(He arrived from a big city.)*
> Вона взяла книгу з дерев'яної **полиці**. *(She took the book from the wooden shelf.)*

But it takes the Instrumental case when it means "with" (accompaniment).
> Я гуляю з найкращими **друзями**. *(I am walking with my best friends.)*
> Ми п'ємо чорний чай з **молоком**. *(We drink black tea with milk.)*

<!-- INJECT_ACTIVITY: group-sort-cases -->

Ukrainian uses special case constructions for specific meanings. For time expressions with days of the week or years, we use specific cases.
> Ми зустрінемося у **четвер**. *(We will meet on Thursday.)* — Accusative case.
> Це сталося у дві тисячі чотирнадцятому **році**. *(This happened in 2014.)* — Locative case.

To describe a characteristic, like clothing, we use «у/в» with the Locative.
> Хто той хлопець у жовтому **светрі**? *(Who is that guy in the yellow sweater?)*
> Жінка у червоній **сукні** — моя мама. *(The woman in the red dress is my mom.)*

And we always use the Vocative case to address people directly.
> **Мамо**, де мої ключі? *(Mom, where are my keys?)*
> **Друзі**, ходімо швидше додому! *(Friends, let's go home faster!)*
> **Пане**, ви забули свій телефон. *(Sir, you forgot your phone.)*

Read a short text and identify the case and trigger for the underlined nouns.

<!-- INJECT_ACTIVITY: fill-in-mixed-cases -->

Learners often make common mistakes when applying cases. A frequent **помилка** (error, mistake) is confusing animate and inanimate nouns in the Accusative plural. For inanimate objects, the Accusative plural looks exactly like the Nominative. For living things (animate), it looks exactly like the Genitive plural.
> Я бачу нові **столи**. *(I see new tables.)* — Inanimate (Nominative form).
> Я бачу нових **студентів**. *(I see new students.)* — Animate (Genitive form).

Another common issue is using incorrect case endings after prepositions, such as forgetting that «після» (after) and «без» (without) always take the Genitive.

Let's focus on specific errors. Many learners use the Nominative instead of the Genitive plural after numbers like five. They say «п'ять студенти», but you must **виправити** (to correct) this to «п'ять студентів». 

Another issue is ignoring dual remnants in the Instrumental case. For body parts that come in pairs, we use «-има» instead of «-ами». So, «очами» is wrong; the correct form is «очима». Similarly, we say «плечима» (with shoulders) and «дверима» (with doors). 

:::caution
Subject-verb agreement is critical! If the subject is plural, the verb must be plural. "Книги лежить" is incorrect; it must be "книги лежать". Always check the ending of your verb.
:::

<!-- INJECT_ACTIVITY: quiz-error-correction -->

<!-- INJECT_ACTIVITY: error-correction-mixed -->

## Частина 3: Вільне мовлення (Part 3: Free Production)

Now it is time to integrate all cases into your free speech. The ultimate goal is to naturally mix cases in conversation without overthinking the grammar rules. When you speak, you do not have time to run through declension tables in your head. You just need to express your thoughts. Practice is the only way to build this fluency.

Let's look at a dialogue between a **наречена** (bride) and her **подруга** (female friend). They are planning a wedding, and every case appears naturally. Read the dialogue aloud and notice how the cases change based on the role of the noun.

> **Подруга:** **Олено**! Ти вже маєш запрошення для **гостей**? *(Olena! Do you already have the invitations for the guests?)*
> **Наречена:** Так, маю. А ти вже купила подарунок **нареченій**? *(Yes, I do. And have you already bought a gift for the bride?)*
> **Подруга:** Звичайно! Я бачу **наречену**, яка дуже хвилюється. *(Of course! I see a bride who is very nervous.)*
> **Наречена:** Я просто хочу зробити багато фото з **молодятами**. *(I just want to take a lot of photos with the newlyweds.)*
> **Подруга:** Не хвилюйся, усе буде чудово на **весіллі**! *(Do not worry, everything will be wonderful at the wedding!)*

This dialogue contains all seven cases. Let us analyze them:
- «Олено!» is the Vocative case. It is used to address the person directly.
- «запрошення для гостей» uses the Genitive plural after the preposition «для».
- «подарунок нареченій» uses the Dative singular. It answers the question "to whom?"
- «бачу наречену» uses the Accusative singular. It is the direct object of the verb «бачити».
- «з молодятами» uses the Instrumental plural. It indicates accompaniment with the preposition «з».
- «на весіллі» uses the Locative singular. It indicates the location.

:::tip
When you learn new nouns, always try to use them in small phrases or sentences rather than alone. Knowing that a word is feminine is helpful, but knowing how to say «я йду з мамою» (I am walking with my mom) is practical language use.
:::

To test your understanding, complete a dialogue where you fill in the missing noun forms in the correct case, both singular and plural. Read the surrounding words carefully to find the triggers.

Finally, try a guided writing task: "Опишіть свій ідеальний **вихідний день**" (Describe your ideal day off). This is a perfect way to practice cases. 
Think about where you go. You will need the Accusative or Locative case for destinations.
Think about who you meet. You will need the Accusative or Dative case for people.
Think about what you do. You will need the Accusative or Instrumental case for actions.
Think about what you eat. You will need the Genitive for quantities and Accusative for items.

Here is an example of how you can combine these cases into a coherent text:

> Ось мій ідеальний вихідний день. Вранці я прокидаюся пізно. Я п'ю велику чашку гарячої кави з молоком. Потім я дзвоню своїм друзям. Ми домовляємося зустрітися у центрі міста. О першій годині я їду в улюблений ресторан. Я замовляю смачний український борщ зі сметаною і пампушками. Після обіду ми йдемо в парк. Ми довго гуляємо під високими деревами. Ми говоримо про роботу, життя і плани на майбутнє. Увечері я повертаюся додому. Я читаю нову книгу або дивлюся цікавий фільм. Це ідеальний час для відпочинку.

Try to write eight to ten sentences using these patterns.

## Підсумок

We have covered a lot of ground in this module. Take a moment for a **самоперевірка** (self-check). Ask yourself these questions:

- Чи можу я **впевнено** (confidently) утворювати форми множини, особливо складний Родовий відмінок?
- Чи знаю я, який відмінок вимагає кожен прийменник?
- Чи пам'ятаю я винятки, такі як «діти», «люди», «друзі»?
- Чи використовую я Кличний відмінок при звертанні до людей?
- Чи готовий я до рівня A2.6?

If you can answer "yes" to these questions, you have successfully mastered the Ukrainian case system at the A2 level. Keep practicing, read more texts, and do not be afraid to make a **помилка** — every error is a step toward fluency. You can always review and **виправити** (to correct) your mistakes. The more you use the language, the more natural these cases will feel.
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-cases
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

**Level: A2 (Module 39/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-soft-hard [§4.1.2, §4.1.3]
**М'який знак і апостроф** (Soft sign and apostrophe)
- **group-sort** — М'який чи твердий?: Розподілити приголосні/слова за м'якістю чи твердістю вимови / Sort consonants/words by soft vs hard pronunciation
  - Instruction: *Розподіліть*
- **quiz** — Де потрібен ь?: Обрати слово, де потрібен м'який знак / Choose which word needs м'який знак
- **error-correction** — Виправ помилку: Знайти, де м'який знак або апостроф пропущено або вжито неправильно / Find where м'який знак or апостроф is missing/wrong
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Занадто складно для A1 без варіантів

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
