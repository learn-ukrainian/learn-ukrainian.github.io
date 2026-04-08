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

- `<!-- INJECT_ACTIVITY: quiz -->`
- `<!-- INJECT_ACTIVITY: fill-in -->`
- `<!-- INJECT_ACTIVITY: fill-in-2 -->`
- `<!-- INJECT_ACTIVITY: error-correction -->`

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


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

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

A **контрольна точка** (checkpoint) is an essential pedagogical tool for consolidating knowledge and confirming linguistic reflexes. According to the standard curriculum guidelines, such as those found in the classic *Заболотний Grade 5-6* textbook, a dedicated **повторення вивченого** (review of what has been learned) is necessary before advancing to complex sentence structures. This systematic **перевірка** (check, test) anchors the core concepts of verb aspect and the Genitive case into your active memory.

> **Олена:** Привіт, Марку! Ти готовий до перевірки? *(Hi, Marko! Are you ready for the test?)*
> **Марко:** Привіт! Не дуже. Ця **контрольна точка** здається складною. *(Hi! Not really. This checkpoint seems difficult.)*
> **Олена:** Давай повторимо разом. Скажи, скільки у тебе братів? *(Let's review together. Tell me, how many brothers do you have?)*
> **Марко:** У мене... двох братів... ні, два брати! Ох, я завжди плутаю. *(I have... two brothers... no, two brothers! Oh, I always confuse them.)*
> **Олена:** Дивись, після числа два ми використовуємо називний відмінок: два брати. А після п'яти — родовий множини: п'ять братів. *(Look, after the number two we use the nominative: two brothers. And after five — genitive plural: five brothers.)*
> **Марко:** А як щодо дієслів? Ти вчора читала **текст** чи прочитала його? *(And what about verbs? Did you read the text yesterday or read it completely?)*
> **Олена:** Я **читала** його довго, але нарешті **прочитала**. *(I was reading it for a long time, but finally I read it completely.)*
> **Марко:** Зрозумів. Процес і результат. Дякую! *(Understood. Process and result. Thanks!)*

The foundation of recognizing verb aspect lies in distinguishing the duration of an action from its completion. Imperfective verbs describe a process, habit, or general fact, answering the question «що робити?» (what to be doing). Perfective verbs describe a finished result, a single occurrence, or a limit reached, answering the question «що зробити?» (what to get done). 

In Exercise 1, a short text is provided. The learner must highlight all perfective verbs in one color and all imperfective verbs in another. This visual sorting helps map out the flow of the narrative, separating background actions from advancing plot points. 

**Читаємо українською** (Reading in Ukrainian)
* Кожного дня я **робив** свої **вправи**. (Every day I was doing my exercises.)
* Учора я швидко **зробив** нове **завдання**. (Yesterday I quickly completed the new task.)
* Студенти довго **писали** складне есе. (The students were writing the complex essay for a long time.)
* Нарешті він **написав** ідеальне **речення**. (Finally he wrote a perfect sentence.)
* Ми часто **зустрічали** друзів у парку. (We often met friends in the park.)
* Сьогодні я **зустрів** брата біля школи. (Today I met my brother near the school.)

For Exercise 2, you will see a list of sentences with a noun in parentheses. The learner must rewrite the sentence, putting the noun in the correct Genitive form. For example, changing «У мене немає (брат)» to «У мене немає брата». The Genitive case is fundamentally triggered by the concept of absence, mathematically represented by the word **немає** (there is no).

**Форми родового відмінка** (Genitive case forms)
* У мене немає **часу** на розмови. (I have no time for conversations.)
* Сьогодні в магазині не було свіжого **хліба**. (There was no fresh bread in the store today.)
* Без **тебе** тут дуже сумно. (It's very sad here without you.)
* Я чекаю свого старого **друга**. (I am waiting for my old friend.)
* Ми йдемо до великого **парку**. (We are going to the large park.)

Exercise 3 asks you to match the imperfective verbs with their perfective partners. Creating mental links between verb pairs is crucial for choosing the right aspect later. Many pairs are formed simply by adding a prefix, while others change a suffix or adopt a completely different root.

**Видові пари дієслів** (Verb aspect pairs)
* робити — з**робити** (to do — to get done)
* читати — **про**читати (to read — to finish reading)
* писати — **на**писати (to write — to finish writing)
* купувати — куп**ити** (to be buying — to buy)
* говорити — сказ**ати** (to be speaking — to say)

<!-- INJECT_ACTIVITY: quiz -->

## Частина 2: Вправи на вибір (Part 2: Choice Exercises)

Moving forward, Exercise 4 features multiple-choice sentences where the learner must choose between the perfective and imperfective form of a verb. A classic example is deciding between «Вчора я (читав / прочитав) цю книгу три години». The phrase «три години» (three hours) explicitly emphasizes the duration and continuous nature of the action. Because the focus is on the ongoing process rather than the final achievement, the imperfective form «читав» is the only **правильний** (correct) choice.

> **Мама:** Доню, ти вже зробила всі свої **вправи**? *(Daughter, have you already done all your exercises?)*
> **Донька:** Ще ні. Мені треба закінчити одне **завдання**. *(Not yet. I need to finish one task.)*
> **Мама:** Що саме ти повинна **зробити** сьогодні? *(What exactly must you get done today?)*
> **Донька:** Я маю **написати** довгу **відповідь**. *(I have to write a long answer.)*
> **Мама:** Добре, я не буду тобі заважати. Немає **часу** на розмови. *(Good, I will not bother you. There is no time for conversations.)*
> **Донька:** Дякую! Я знайду найкращий **варіант** дуже швидко. *(Thanks! I will find the best option very quickly.)*

Context clues dictate the aspect. Words like «завжди» (always), «часто» (often), and «довго» (for a long time) trigger the imperfective. Words like «раптом» (suddenly), «нарешті» (finally), and «за хвилину» (in a minute) demand the perfective.

**Вибір дієслова** (Choosing the verb)
* Я **робив** це складне **завдання** весь вечір. (I was doing this complex task all evening.)
* Я **зробив** це **завдання** за п'ять хвилин. (I got this task done in five minutes.)
* Щовечора вона **дивилася** цікавий серіал. (Every evening she watched an interesting series.)
* Вона **подивилася** фільм і пішла спати. (She watched the film completely and went to sleep.)
* Ми **купували** продукти на ринку. (We were buying groceries at the market.)
* Я **купив** свіжі яблука для пирога. (I bought fresh apples for the pie.)

Exercise 5 involves fill-in-the-blanks with the correct quantity word or numeral, ensuring noun agreement. You will complete sentences like «У класі ___ (5) студентів» by applying the numerical rules. Historians of the Ukrainian language note that numbers like **п'ять** (five) and **десять** (ten) were originally nouns in Old East Slavic (давньоруська мова). Because they functioned as nouns, they required the word following them to take the Genitive plural case, literally translating to a phrase like "a five of tables." This historical logic is perfectly preserved in modern Ukrainian.

When counting, the number «один» (one) acts like an adjective, agreeing fully with the noun. The numbers «два, три, чотири» (two, three, four) pair with the Nominative plural form of the noun. Numbers from «п'ять» (five) upward strictly govern the Genitive plural. 

**Кількість і відмінок** (Quantity and case)
* Один великий **стіл** стоїть у кімнаті. (One large table stands in the room.)
* Два нові **столи** стоять у кімнаті. (Two new tables stand in the room.)
* П'ять старих **столів** стоять у кімнаті. (Five old tables stand in the room.)
* Одна цікава **книга** лежить на полиці. (One interesting book lies on the shelf.)
* Три нові **книги** лежать на полиці. (Three new books lie on the shelf.)
* Шість розумних **студентів** сидять у класі. (Six smart students sit in the classroom.)

:::tip
**Правильний варіант** (Correct option)
When reviewing your work, you must look for the **правильний** (correct) answer, not "вірний". The adjective "вірний" means "loyal" or "faithful" (like a loyal dog). A correct answer on a test is always a **правильна відповідь**. Recognizing this distinction elevates your speech and avoids common calques.
:::

<!-- INJECT_ACTIVITY: fill-in -->

## Частина 3: Практичне застосування (Part 3: Production Exercises)

In Exercise 6, you will answer open-ended questions that require the Genitive case or a specific aspect. You will see questions like «Скільки у вас братів і сестер?», «Що ви зробили вчора?», and «Коли у вас день народження?». Formulating original responses forces the brain to retrieve the correct grammatical endings without a prompt, testing true mastery over the language patterns.

When answering «Скільки у вас братів і сестер?», you must navigate the rules of possession and quantity simultaneously. If you lack siblings, you employ the absolute negation trigger **немає**, which immediately demands the Genitive case. If you have siblings, the number you use dictates whether you follow with the Nominative or Genitive plural.

**Приклади відповідей** (Example answers)
* У мене немає **братів** і **сестер**. (I have no brothers and sisters.)
* У мене є один **брат** і дві **сестри**. (I have one brother and two sisters.)
* У мене є три **брати** і чотири **сестри**. (I have three brothers and four sisters.)
* Моя бабуся має п'ять **братів**. (My grandmother has five brothers.)
* Я не маю вільного **часу** сьогодні. (I do not have free time today.)

When answering «Що ви зробили вчора?», you must consciously choose your verb aspect based on your intent. If you want to communicate that an action was successfully completed, you must deploy the perfective form. If you merely want to state that an action occupied your time, the imperfective is required.

**Минулий час** (Past tense)
* Вчора я **написав** лист і **прочитав** довгу статтю. (Yesterday I wrote a letter and read a long article.)
* Вчора я весь день **працював** і **відпочивав**. (Yesterday I worked all day and rested.)
* Ми **купили** новий телефон для нашої мами. (We bought a new phone for our mom.)
* Студенти уважно **слухали** новий **текст**. (The students were listening carefully to the new text.)

Finally, Exercise 7 provides a short writing prompt of 5-7 sentences. The prompt is «Напишіть про свої плани на вихідні. Що ви будете робити? Що ви хочете зробити?». This encourages you to synthesize your knowledge into a cohesive paragraph. Discussing plans inherently involves the future tense, requiring another layer of aspectual choice. The phrase «Що ви будете робити?» invites process-oriented imperfective verbs constructed with the auxiliary verb **бути**. The phrase «Що ви хочете зробити?» targets concrete goals, requiring perfective infinitives.

> **Вчитель:** Доброго ранку! Хто хоче розповісти про свої плани на вихідні? *(Good morning! Who wants to tell about their plans for the weekend?)*
> **Анна:** Я можу розповісти. У суботу я **буду допомагати** батькам. *(I can tell. On Saturday I will be helping my parents.)*
> **Вчитель:** Дуже добре. А що ти **хочеш зробити** ввечері? *(Very good. And what do you want to get done in the evening?)*
> **Анна:** Я **хочу приготувати** смачну вечерю для всієї родини. *(I want to prepare a delicious dinner for the whole family.)*
> **Вчитель:** Чудовий план. Скільки страв ти приготуєш? *(A wonderful plan. How many dishes will you prepare?)*
> **Анна:** Я думаю, що я приготую три **страви** і спечу один пиріг. *(I think that I will prepare three dishes and bake one pie.)*

To succeed in this final writing prompt, observe how native speakers combine these elements into a single narrative flow. You can use this example as a structural template.

**Приклад тексту про плани** (Example text about plans)
На ці вихідні я маю багато планів. У суботу вранці я **буду прибирати** свою кімнату. Це забере багато **часу**. Потім я **хочу зустрітися** з друзями в центрі міста. Ми підемо до нового кафе і **будемо пити** гарячу каву. У неділю я **буду відпочивати** вдома. Я планую **прочитати** цікаву статтю і **написати** невелике есе. Сподіваюся, мої вихідні будуть чудовими!

:::caution
**Уникаємо русизмів** (Avoiding Russianisms)
As you write your sentences, remember that Ukrainian has its own unique idioms. The construction **брати участь** (to take part) is genuinely Ukrainian. You must never use the direct translation «приймати участь», which is a common calque. Additionally, when discussing school tasks, we say **складати іспит** (to take an exam), not «здавати іспит». Using authentic phrasing demonstrates true language proficiency.
:::

<!-- INJECT_ACTIVITY: fill-in-2 -->
<!-- INJECT_ACTIVITY: error-correction -->

## Підсумок — Summary

This checkpoint solidifies the essential grammatical pillars required for confident communication in Ukrainian. We reviewed the critical distinction between imperfective and perfective verb aspects, learning to accurately **обрати** (choose) between describing a continuous process and a completed result. We reinforced the mechanics of the Genitive case, confirming its role in expressing absence with **немає**, denoting possession, and modifying nouns following numbers like **п'ять** and above.

By completing these recognition exercises, multiple-choice tasks, and open-ended writing prompts, you have tested your ability to apply rules dynamically. You constructed sentences about your personal plans, manipulated verb pairs, and corrected common numerical agreement errors. This rigorous review guarantees that your foundational knowledge is secure, providing a stable platform for mastering more complex vocabulary and syntax in the upcoming modules.

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

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: id, prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Required: id, passage, questions[]
- **source-evaluation**: Required: id, source_text, criteria[], guiding_questions[]

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
