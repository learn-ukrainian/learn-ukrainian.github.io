<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/aspect-concept.yaml` file for module **2: Зроблено чи в процесі? Вступ до виду дієслів** (a2).

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

- `<!-- INJECT_ACTIVITY: aspect-sorting-process-result -->`
- `<!-- INJECT_ACTIVITY: identify-aspect-in-sentences -->`
- `<!-- INJECT_ACTIVITY: match-up-context-aspect -->`
- `<!-- INJECT_ACTIVITY: error-correction-aspect -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Aspect Sorting: Process vs. Result'
  items: 8
  type: quiz
- focus: Identify the Aspect in Sentences
  items: 8
  type: fill-in
- focus: Choose the Correct Aspect (Context-based)
  items: 8
  type: match-up
- focus: Find and fix wrong aspect choice in sentences (e.g., *Він щодня зробив вправи
    → робив, *Вона довго написала листа → писала)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- завершений (completed, finished)
- тривалий (ongoing, lasting)
- одноразовий (single, one-time)
- концепція (concept)
required:
- вид дієслова (verb aspect)
- недоконаний вид (imperfective aspect)
- доконаний вид (perfective aspect)
- процес (process)
- результат (result)
- дія (action)
- повторення (repetition)
- робити / зробити (to do)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Що таке вид дієслова?

Welcome to one of the most important concepts in Ukrainian grammar. Until now, you have focused on verb tenses. Tense tells us exactly when an action happens. However, Ukrainian verbs have a hidden dimension called **вид дієслова** (verb aspect). While tense answers the question of time, aspect tells us how the action unfolds. In English, you use complex tense structures to express whether an action is ongoing or completed. In Ukrainian, this information is built directly into the vocabulary. The concept of aspect is not about time at all. Instead, it is about the internal completion of the action. It describes whether we view an event as a continuous, flowing process or as a single, finished point in time. Understanding this difference is the key to speaking naturally.

To master this dimension, you need to meet the two main categories of Ukrainian verbs. The first category is called **недоконаний вид** (imperfective aspect). We will often abbreviate this as НВ. This aspect represents the unfinished nature of an action. We use it to describe an ongoing **процес** (process), a repeated habit, or a general fact. The second category is **доконаний вид** (perfective aspect). We will abbreviate this as ДВ. This represents the finished nature of an action. We use it when we want to highlight total completion and a successful **результат** (result). Every time you choose a verb, you must decide what matters more: the journey or the destination.

When Ukrainian children learn grammar in school, they do not memorize long lists of rules to figure out the aspect of a verb. Instead, they use a simple question hack. Every verb form answers a specific question that reveals its true nature. Verbs of the imperfective aspect always answer the question «Що робити?» (What to be doing?). Verbs of the perfective aspect always answer the question «Що зробити?» (What to have done?). Notice the tiny difference at the beginning of the second question! This simple test helps you group vocabulary into pairs. For example, you have **робити** (to do) and **зробити** (to have done). You also have **писати** (to write) and **написати** (to have written), as well as **читати** (to read) and **прочитати** (to have read).

If the grammar terms feel too abstract, imagine that every action is a visual medium. Using the imperfective aspect is exactly like watching the middle of a movie. The action is actively happening, the characters are moving, and you are immersed in the scene without knowing how it ends. Using the perfective aspect is like seeing the «Кінець» (The End) screen or looking at a still photograph of the finished scene. The action is over, and the result is locked in place. For instance, in the past tense, saying «Я писав» (I was writing) means you were inside the movie. Saying «Я написав» (I wrote) means the credits are already rolling.

Let us look at how this plays out in real life. Imagine two friends watching a football match on television. The first friend describes the ongoing flow of the game, focusing on the process. The second friend reacts excitedly to the sudden, completed actions that change the score.

> — **Марко:** Дивись, він біжить дуже швидко! *(Look, he is running very fast!)*
> — **Андрій:** Так, він забив гол! *(Yes, he scored a goal!)*
> — **Марко:** Вони грають сьогодні дуже добре. *(They are playing very well today.)*
> — **Андрій:** Вона чудово передала м'яч. *(She passed the ball wonderfully.)*

In this scenario, **бігти** (to run) and **грати** (to play) describe the ongoing process. Meanwhile, **забити** (to score) and **передати** (to pass) report a final result.


## Недоконаний вид: Процес і повторення

In the previous section, we established that the imperfective aspect (**недоконаний вид**) is like watching the middle of a movie. Now, let us dive deeper into its primary function: describing a process, or **процес** (process) in Ukrainian. When you use an imperfective verb, you signal to your listener that the duration or flow of the action matters much more than its end point. You are describing an ongoing action, which we call a **тривала дія** (ongoing action). Imagine you spent hours immersed in a novel. You want to emphasize the time spent, not whether you reached the final page. You would say: «Я читав книгу цілий вечір» *(I was reading the book all evening)*. In this sentence, the focus is entirely on the activity itself. We do not know if the person finished the book, and frankly, we do not care. The imperfective aspect allows you to paint a picture of an action unfolding over time without worrying about its conclusion. 

The second superpower of the imperfective aspect is its ability to express repetition, or **повторення** (repetition). If an action happens more than once, it becomes a habit or a routine, and in Ukrainian, habits almost always require the imperfective aspect. Think about your daily schedule. You might say: «Я щодня роблю вправи» *(I do exercises every day)*. Because the action repeats, it never truly has a single, final result that ends forever. It is an ongoing cycle. In the past tense, the imperfective aspect is particularly useful for describing things you used to do. For example: «Він часто телефонував» *(He used to call often)*. In English, you might rely on phrases like "used to" or "would" to indicate past habits. In Ukrainian, you do not need extra auxiliary verbs for this. The imperfective verb itself already carries the meaning of a customary action. 

Beyond processes and habits, the imperfective aspect serves another fundamental purpose: stating general facts. When you simply want to name an action or state a universal truth where the idea of completion is entirely irrelevant, you will use the imperfective aspect. For instance, consider the sentence: «Діти читають книги» *(Children read books)*. This is a general statement about what children do. There is no specific result being highlighted. Similarly, if you say «Птахи літають» *(Birds fly)*, you are merely stating a fact of nature. For learners at the A2 level, you can consider the imperfective aspect to be your default setting for describing how the world works. Unless you are specifically trying to draw attention to a single, completed achievement, the imperfective aspect is the safest choice for general observations. 

There is a critical grammatical rule regarding the imperfective aspect that makes speaking Ukrainian much easier: the present tense is exclusively imperfective. Think about it logically. You cannot have a completely finished, result-locked action happening right now in the present moment. If it is happening right now, it is inherently a process. Therefore, any verb you use in the present tense, such as «Я пишу» *(I am writing)*, is always imperfective. You do not even have to make an aspect choice when speaking in the present tense. Contrast this with the past tense, where an action could either be an ongoing process («Я писав» - *I was writing*) or a finished result. 

To help you instantly recognize when to use the imperfective aspect, look out for specific signal words. These are frequency adverbs that inherently describe duration or repetition, making the imperfective aspect mandatory. The most common triggers include **завжди** (always), **часто** (often), **зазвичай** (usually), **регулярно** (regularly), and **щодня** (every day). Whenever you spot these words, you know a habit is being described. Another powerful signal word is **довго** (for a long time), which highlights a prolonged process. For example, if you want to emphasize the duration of an activity, you would say: «Вона довго писала листа» *(She was writing the letter for a long time)*. These adverbs act as clear signposts, guiding you safely toward the imperfective aspect.

<!-- INJECT_ACTIVITY: aspect-sorting-process-result -->
<!-- INJECT_ACTIVITY: identify-aspect-in-sentences -->


## Доконаний вид: Результат! (Perfective: The Result!)

Now that we have explored the ongoing nature of the imperfective aspect, it is time to meet its decisive counterpart: the perfective aspect, or **доконаний вид** (perfective aspect). If the imperfective aspect is about watching the movie unfold, the perfective aspect is the moment the "The End" screen appears. It is all about the result. We use the perfective aspect when we want to announce: "Mission accomplished." It describes a **завершена дія** (completed action). Think about the difference between reading and finishing a book. If you say «Я прочитав книгу» *(I have read the book)*, you are focusing entirely on the outcome. The process of reading is over. The book is now sitting on the shelf, and you know how the story ends. You have crossed the finish line. The perfective aspect does not care how long the action took or how difficult it was; its sole purpose is to confirm that the action reached its limit and produced a clear, final result.

Because the perfective aspect is fundamentally tied to the concept of completion, it has a fascinating grammatical quirk: perfective verbs do not have a present tense. Think about it logically. If an action is happening right now, in the present moment, it is still ongoing. It cannot be completely finished. Therefore, when you take a perfective verb and put it into a form that looks like the present tense, it actually jumps into the future. For example, the perfective verb **зробити** (to do) in the first-person singular is **зроблю** (I will do). But «Я зроблю» does not mean "I am doing." It means "I will do" or "I will get it done." This is a major concept for you to master at the A2 level. By simply choosing the perfective aspect, you can talk about the future without needing any extra auxiliary verbs. It is a powerful tool for making promises and stating clear intentions.

For this introductory module, however, we will focus primarily on using the perfective aspect in the past tense. This is where the contrast with the imperfective aspect is most obvious. When you use a perfective verb in the past, you are reporting a concrete achievement. For example: «Я купив квиток» *(I bought a ticket)*. The transaction is complete; you have the ticket in your hand. Or «Вона прийшла додому» *(She arrived home)*. The journey is over; she is inside the house. Consider «Ми зробили завдання» *(We finished the task)*. The work is done. The perfective past tense provides that satisfying "click" of a completed action.

Just as the imperfective aspect has its favorite adverbs, the perfective aspect has specific signal words that highlight a result. Look out for words like **нарешті** (finally), **вже** (already), and **раптом** (suddenly). These words naturally point to an outcome or a sudden change of state. However, be careful with the word **вчора** (yesterday). It is completely neutral and depends entirely on the speaker's focus. You can say «Вчора я читав» *(Yesterday I was reading)* if you want to emphasize the process, or «Вчора я прочитав» *(Yesterday I finished reading)* if you want to emphasize the result.

To truly understand the difference between the two aspects, let's look at a classic contrast: the concept of failure. Imagine you were looking for your keys. You can say: «Я шукав, але не знайшов» *(I looked for, but didn't find)*. The verb **шукав** (was looking for) is imperfective because the search was a process that took up your time. The verb **знайшов** (found) is perfective because finding is the ultimate result you were aiming for. By using the perfective aspect with a negative word, you are stating that the goal was never reached. The boundary was not crossed.

<!-- INJECT_ACTIVITY: match-up-context-aspect -->


## Порівняння пар: Бачимо різницю

Let's look at this in practice by comparing some common verb pairs side-by-side. Consider the verbs **писати** (to write, imperfective) and **написати** (to write, perfective). If you say «Він писав лист» *(He was writing a letter)*, you are describing a process. Maybe he was interrupted, or maybe he never finished. However, «Він написав лист» *(He wrote a letter)* means the letter is complete and ready to send. The same logic applies to food. «Ми пили каву» *(We were drinking coffee)* sets a scene, while «Ми випили каву» *(We drank the coffee)* means the cups are empty. «Вона їла борщ» *(She was eating borsch)* focuses on the activity, whereas «Вона поїла» *(She finished eating)* announces a clear result. We even see this with senses: «Я бачив це» *(I saw this, I was looking at it)* versus «Я побачив це» *(I spotted it)*.

To truly grasp this concept, try visualizing these two aspects as lines drawn on a page. Imagine the imperfective aspect as a wavy, continuous line. It flows across the page, representing the passage of time without a clear beginning or end. It fills the space, just as imperfective verbs fill our stories with ongoing background activities. Now, imagine the perfective aspect as a straight, sharp line that suddenly stops with a bold "X". That "X" is the concrete result, the exact moment of completion. Perfective verbs do not flow; they punctuate time. They act as milestones in your narrative, marking the moments when an action definitively ends.

You might have noticed a pattern in our examples. In Ukrainian, most perfective verbs are created by attaching a prefix to their imperfective partner. For instance, **робити** (to do) becomes **зробити** (to finish doing). **Читати** (to read) becomes **прочитати** (to read completely). There are many different prefixes used for this purpose, such as **на-**, **з-**, **про-**, **ви-**, and **по-**. Their primary job is to flip the grammatical switch from a process to a result. At the A2 level, you do not need to memorize every prefix rule. Your main goal is simply to recognize these pairs and understand that the prefix signals a change in the verb's aspect.

<!-- INJECT_ACTIVITY: error-correction-aspect -->


## Підсумок (Summary)

Let's review what we have learned about verb aspect. Ask yourself these self-check questions to make sure the core concepts are clear:

1. **Яке питання ми ставимо до недоконаного виду?** *(What question do we ask for the imperfective aspect?)*
We ask: **Що робити?** *(What to do?)*. This aspect focuses on the action itself.

2. **Який вид ми використовуємо для регулярних дій?** *(Which aspect do we use for regular actions?)*
We use the imperfective aspect (**недоконаний вид**). Words like **щодня** *(every day)* and **часто** *(often)* are strong signals for this.

3. **Чи мають дієслова доконаного виду теперішній час?** *(Do perfective verbs have a present tense?)*
**Ні.** *(No.)* Because a perfective verb describes a completed result, it cannot happen right now in the present moment. If you use a perfective verb in what looks like a present tense form, it actually carries a future meaning.

4. **Який вид позначає результат?** *(Which aspect indicates a result?)*
The perfective aspect (**доконаний вид**). This is the aspect you use when you cross the finish line.

To recap the most important rule: the imperfective aspect is for a process or repetition, while the perfective aspect is for a result or a single, completed action. Keep this in mind, and you will navigate Ukrainian verbs with confidence.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: aspect-concept
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

**Level: A2 (Module 2/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
