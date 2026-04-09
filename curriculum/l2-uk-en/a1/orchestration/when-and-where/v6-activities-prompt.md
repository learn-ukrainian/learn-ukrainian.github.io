<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/when-and-where.yaml` file for module **45: When and Where** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-conjunction-choice -->`
- `<!-- INJECT_ACTIVITY: quiz-comma-placement -->`
- `<!-- INJECT_ACTIVITY: quiz-function-id -->`
- `<!-- INJECT_ACTIVITY: fill-in-sentence-builder -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Complete: Я знаю, ___ він тут. Я не знаю, ___ вона живе. Скажи, ___ ти прийдеш.'
  items: 8
  type: fill-in
- focus: Question word or conjunction? Де ти живеш? vs Я знаю, де ти живеш.
  items: 8
  type: quiz
- focus: 'Build complex sentences: Я думаю, що ___. Він каже, що ___.'
  items: 6
  type: fill-in
- focus: Where is the comma? Choose correct punctuation in complex sentences
  items: 8
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- сказати (to say — perfective)
- бачити (to see)
- чути (to hear)
- розуміти (to understand)
- речення (sentence, n)
- головне (main — as in main clause)
required:
- що (that — conjunction)
- де (where — conjunction)
- коли (when — conjunction)
- знати (to know)
- думати (to think)
- казати (to say/tell)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

A real-world navigation scenario often requires linking multiple facts together, such as locations and times. In the following phone conversation, a guest is trying to find an apartment and coordinate a meeting time. The bolded words act as structural links between the speaker's actions and the environment.

> **Гість:** Алло! Я зараз на площі. Ти знаєш, **де** нове кафе? *(Hello! I am on the square now. Do you know where the new cafe is?)*
> **Господар:** Так, я знаю, **де** воно. **Коли** побачиш **фонтан** (fountain), поверни ліворуч. *(Yes, I know where it is. When you see the fountain, turn left.)*
> **Гість:** Добре. Я йду. А **де** побачиш **парк** (park), зупинись? *(Okay. I am walking. And where you see the park, stop?)*
> **Господар:** Саме так. Великий **будинок** (building), **що** стоїть біля дерева — це кафе. Скажи, **коли** ти вільний. *(Exactly. The big building that stands near the tree is the cafe. Tell me when you are free.)*
> **Гість:** Я вільний, **коли** закінчу роботу. Це сьогодні ввечері. *(I am free when I finish work. That is tonight.)*
> **Господар:** Добре. Я думаю, **що** о шостій буде добре. *(Good. I think that at six will be good.)*
> **Гість:** Так, я теж думаю, **що** це гарний час. До зустрічі! *(Yes, I also think that this is a good time. See you!)*

:::note
The imperative verbs **поверни** (turn) and **зупинись** (stop) seen in the dialogue are used for giving direct navigation instructions. They form the core action in the main clause, waiting for the subordinate clause to provide the condition (e.g., **коли побачиш...**).
:::

When discussing other people and sharing information, complex sentences allow speakers to embed one fact inside another. The short bolded words connect the act of knowing or saying with the actual information being shared.

> **Максим:** Привіт! Ти знаєш, **що** Олена вже в Києві? *(Hi! Do you know that Olena is already in Kyiv?)*
> **Тарас:** Ні, я не знав! А де вона живе? *(No, I didn't know! And where does she live?)*
> **Максим:** Я не знаю, **де** саме. Але я знаю, **що** біля центру. *(I don't know exactly where. But I know that it is near the center.)*
> **Тарас:** Скажи їй, **коли** побачиш, **що** я хочу зустрітися. *(Tell her, when you see her, that I want to meet.)*
> **Максим:** Добре, скажу, **коли** побачу. *(Okay, I will tell her when I see her.)*

In these dialogues, the bolded words **що**, **де**, and **коли** are not asking questions, but rather acting as bridges. They are "connector" words that glue two separate pieces of information together into a single, flowing thought. Instead of stating two separate facts like "I know" and "Where does she live?", the speaker combines them using **де**: **Я знаю, де вона живе**. This grammatical structure elevates speech from basic phrases to natural, connected communication. A specific punctuation mark appears before every single one of these connector words. The comma is an absolute requirement here, establishing a structural boundary between the two connected actions.

## Складне речення (Complex Sentences)

In Module 44, you learned how to connect two equal ideas using simple words like **і** (and) or **але** (but). A sentence like **Я читаю, і він пише** (I am reading, and he is writing) contains two independent actions carrying equal weight. Now, the focus shifts to connecting a main idea with a dependent idea. In the sentence **Я знаю, що він тут** (I know that he is here), the phrase **Я знаю** operates as the core statement—it is the main clause. The second part, **що він тут**, provides supporting information and depends entirely on the first part to make sense. Ukrainian textbooks for the fifth grade call this hierarchical structure a **складнопідрядне речення** (a complex sentence with a subordinate clause).

Ukrainian punctuation enforces a strict rule for these complex sentences. You must always place a comma before **що**, **де**, and **коли** when they act as conjunctions linking two clauses. This creates a significant contrast with English, where a sentence like "I think that it is correct" requires no punctuation boundary. In Ukrainian, that comma is a mandatory visual pause indicating the start of a dependent clause.

*   **Я думаю, що це правильно.** (I think that this is correct.)
*   **Він не знає, де магазин.** (He does not know where the store is.)
*   **Зателефонуй, коли прийдеш.** (Call when you arrive.)

Every single example requires the comma before the conjunction.

:::caution
English speakers often forget the comma before **що** because "I think that..." has no punctuation in English. In Ukrainian, writing **Я думаю що це так** without a comma is a grammatical error. Always insert the pause.
:::

Certain actions naturally demand a subordinate clause to finish their thought. These "trigger verbs" describe perception, thought, and communication. The most common examples are **знати** (to know), **думати** (to think), **казати** (to say/tell), **сказати** (to say — perfective), **бачити** (to see), **чути** (to hear), and **розуміти** (to understand). When a speaker uses these verbs, they usually need **що**, **де**, or **коли** to complete the logical sequence. If someone says "I see," the listener immediately waits for the rest of the information. A connected clause satisfies that grammatical expectation.

*   **Я бачу, що ти працюєш.** (I see that you are working.)
*   **Ти чуєш, де грає музика?** (Do you hear where the music is playing?)
*   **Він розуміє, коли треба йти.** (He understands when it is necessary to go.)
*   **Ми знаємо, що це важливо.** (We know that this is important.)
*   **Вона каже, що вона вдома.** (She says that she is at home.)

<!-- INJECT_ACTIVITY: fill-in-conjunction-choice -->

<!-- INJECT_ACTIVITY: quiz-comma-placement -->

## Що, де, коли — двоє облич (Two Faces)

The words **що**, **де**, and **коли** serve two entirely different functions depending on their placement in a sentence. As question words, they appear at the beginning of a sentence to request information. You already know this role from Module 20. When positioned at the start, they function as interrogative markers and demand an answer.

*   **Що це на столі?** (What is this on the table?)
*   **Де ти зараз живеш?** (Where do you live now?)
*   **Коли ти прийдеш додому?** (When will you arrive home?)
*   **Що він робить там?** (What is he doing there?)
*   **Де працює твій брат?** (Where does your brother work?)

In this primary role, their function is to open a conversation and extract specific details from the listener.

When these exact same words move to the middle of the sentence—positioned immediately after a comma—they completely drop their interrogative function and become conjunctions. Compare the direct question **Де ти?** (Where are you?) with the complex statement **Я знаю, де ти** (I know where you are). The segment following the comma uses normal statement word order. No inversion or special question intonation applies, because the speaker is no longer asking anything. The sentence simply states a fact about a location, a time, or an event.

*   **Я знаю, що він робить.** (I know what he is doing.)
*   **Я не знаю, що це.** (I do not know what this is.)
*   **Я думаю, що це правильно.** (I think that this is correct.)
*   **Він каже, що кафе зачинене.** (He says that the cafe is closed.)
*   **Я знаю, де він працює.** (I know where he works.)
*   **Я не знаю, де мій телефон.** (I do not know where my phone is.)
*   **Скажи, коли ти будеш готовий.** (Tell me when you will be ready.)
*   **Я не знаю, коли він приїде.** (I do not know when he will arrive.)

:::tip
A simple trick to identify the function of **що**: if you can replace it with "what" in English, it is a question word. If you can replace it with "that," it is a conjunction connecting two ideas.
:::

A subordinate clause stating a condition or time can sometimes appear before the main action. In such cases, the dependent clause starts with **коли** and opens the sentence.

*   **Коли я прийду, ми поговоримо.** (When I arrive, we will talk.)
*   **Коли я вдома, я відпочиваю.** (When I am at home, I rest.)
*   **Коли вона читає, вона не чує.** (When she is reading, she does not hear.)
*   **Коли ми працюємо, ми не говоримо.** (When we work, we do not talk.)

The mandatory comma still separates the two parts, but it now sits in the middle of the sentence to introduce the main clause. While **що** and **де** almost always remain firmly in the middle of the sentence (e.g., **Я думаю, що...**, **Він каже, що...**), the word **коли** offers more flexibility and frequently jumps to the beginning to establish the context for the main action.

### Практика читання (Reading Practice)

Read the following paragraph. Notice how the short conjunctions hold the narrative together. 

**Мій друг Тарас каже, що він живе біля парку. Я не знаю, де саме цей парк. Але я знаю, що він великий. Коли в Тараса є час, він гуляє там. Я думаю, що це гарне місце. Тарас каже, що він теж гуляє, коли я тут.** 
*(My friend Taras says that he lives near the park. I do not know where exactly this park is. But I know that it is big. When Taras has time, he walks there. I think that this is a good place. Taras says that he also walks when I am here.)*

<!-- INJECT_ACTIVITY: quiz-function-id -->

<!-- INJECT_ACTIVITY: fill-in-sentence-builder -->

## Підсумок — Summary

Complex sentences rely on specific connectors to link a main clause to a subordinate clause. Here is a summary of the three subordinating conjunctions from this module:

| Conjunction | Meaning | Example |
| :--- | :--- | :--- |
| **що** | that | **Я знаю, що він тут.** |
| **де** | where | **Я не знаю, де кафе.** |
| **коли** | when | **Скажи, коли прийдеш.** |

The comma before these conjunctions is a strict requirement of Ukrainian punctuation. Furthermore, **що** translates to "that" when operating as a conjunction, but functions as "what" when acting as a question word. The identical spelling performs two completely different grammatical roles depending entirely on the sentence structure.

Combining subordinating conjunctions with the basic connectors from Module 44 allows for highly detailed sentence structures. Multiple clauses can link together to describe complex situations.

*   **Я не йду, бо я не знаю, де це.** (I am not going, because I do not know where it is.)
*   **Він каже, що прийде, коли закінчить.** (He says that he will come when he finishes.)
*   **Ми думаємо, що вона знає, де він.** (We think that she knows where he is.)
*   **Я бачу, що ти не знаєш, що робити.** (I see that you do not know what to do.)

The first example uses **бо** (because) and **де** (where) in a single thought. The second sentence contains two separate subordinate clauses, demonstrating how these small connecting words build sophisticated real-world communication.

Verify your understanding by reviewing these core concepts. Can you name the three subordinating conjunctions covered in this module? Check your memory regarding the mandatory punctuation mark required before them. Finally, practice building three original sentences starting with these specific phrases:

*   **Я думаю, що...**
*   **Я не знаю, де...**
*   **Скажи мені, коли...**

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: when-and-where
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

**Level: A1.4+ (Module 45/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-syllables [§4.1.1, §4.1.4]
**Склад і складоподіл** (Syllables and syllable division)
- **divide-words** — Поділи слова на склади: Інтерактивний поділ на склади — натиснути між літерами для вставки дефіса / Interactive syllable division — tap between letters to insert hyphens
  - Instruction: *Поділіть слово на склади*
- **count-syllables** — Порахуй склади: Порахувати склади — кожен голосний = один склад (складотворчі голосні) / Count syllables — each vowel = one syllable (складотворчі голосні)
  - Instruction: *Скільки складів?*
- **pick-syllables** — Вибери закриті/відкриті склади: Визначити тип складу: відкритий (закінчується голосним) чи закритий (приголосним) / Classify syllables as відкритий (ends vowel) or закритий (ends consonant)
  - Instruction: *Оберіть усі закриті склади*
- **odd-one-out** — Четверте зайве: Обрати слово, що не пасує — за кількістю або типом складів / Pick the word that doesn't belong — by syllable count, type, or pattern
  - Instruction: *Яке слово зайве?*
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує фонетичні навички поділу

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

### Pattern: general-reading [§1 (Speech activities — reading)]
**Розуміння тексту** (Reading comprehension)
- **true-false** — Правда чи ні?: Перевірити розуміння тексту або діалогу / Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Відповісти на запитання за текстом / Answer questions about a text passage


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
