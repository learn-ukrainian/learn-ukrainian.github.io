<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/questions.yaml` file for module **19: Questions** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-question-word-choice -->`
- `<!-- INJECT_ACTIVITY: match-question-answer -->`
- `<!-- INJECT_ACTIVITY: fill-in-negation-transform -->`
- `<!-- INJECT_ACTIVITY: quiz-double-negation -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Choose the right question word: ___ ти живеш? (Де/Що/Хто)'
  items: 8
  type: quiz
- focus: 'Make it negative: Я знаю → Я не знаю, Хтось знає → Ніхто не знає'
  items: 8
  type: fill-in
- focus: 'Match question to answer: Де ти живеш? ↔ У Києві.'
  items: 6
  type: match-up
- focus: 'Double negation: choose the correct Ukrainian sentence.'
  items: 6
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- ніхто (nobody)
- нічого (nothing)
- ніколи (never)
- жити (to live)
- розуміти (to understand)
- тому що (because)
required:
- хто (who)
- що (what)
- де (where)
- куди (where to)
- коли (when)
- чому (why)
- як (how)
- не (not)
- ні (no)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Asking for information is the foundation of any conversation. When you travel, meet new people, or simply try to find a missing object, you need to know how to ask about locations, identities, and reasons. The dialogues below demonstrate how Ukrainians ask and answer questions in everyday situations.

> **Турист:** Вибачте, де центр? *(Excuse me, where is the center?)*
> **Перехожий:** Центр там. *(The center is there.)*
> **Турист:** Дякую! Куди іде цей автобус? *(Thanks! Where does this bus go?)*
> **Перехожий:** Цей автобус іде в парк. *(This bus goes to the park.)*
> **Турист:** Добре. Як пройти до парку? *(Good. How to get to the park?)*
> **Перехожий:** Прямо і направо. *(Straight and to the right.)*

When arriving in a new city, finding your way relies heavily on your ability to use question words. The tourist uses **де** (where) to locate a static place, **куди** (where to) to ask about the direction of the bus, and **як** (how) to request instructions for reaching a destination.

> **Марко:** Хто ти? *(Who are you?)*
> **Анна:** Я студент. *(I am a student.)*
> **Марко:** Що ти вивчаєш? *(What do you study?)*
> **Анна:** Я вивчаю українську. *(I study Ukrainian.)*
> **Марко:** Де ти живеш? *(Where do you live?)*
> **Анна:** Я живу в Києві. *(I live in Kyiv.)*
> **Марко:** Коли ти працюєш? *(When do you work?)*
> **Анна:** Вранці. *(In the morning.)*

When you meet someone new, you naturally want to expand the conversation beyond basic greetings. Notice how each question targets a specific detail. The word **хто** (who) asks about a person's identity, **що** (what) targets an action or object, and **коли** (when) establishes a timeframe.

> **Олег:** Де моя книга? *(Where is my book?)*
> **Ірина:** Я не знаю. *(I don't know.)*
> **Олег:** А хто знає? *(And who knows?)*
> **Ірина:** Мама знає. *(Mom knows.)*
> **Олег:** Чому мама? *(Why mom?)*
> **Ірина:** Тому що вона все знає! *(Because she knows everything!)*
> **Олег:** Чому ти не бачиш її? *(Why don't you see it?)*
> **Ірина:** Тому що я нічого не бачу без окулярів. *(Because I see nothing without glasses.)*

A typical domestic scene often involves missing items and a lack of information. This conversation introduces the word **чому** (why) alongside its natural response **тому що** (because). It also demonstrates how to express negation using **не** (not) and how to indicate the total absence of something using **нічого** (nothing).

## Питальні слова (Question Words)

To gather information effectively, you need a core set of linguistic tools. Ukrainian relies on seven essential question words: **хто** (who), **що** (what), **де** (where), **куди** (where to), **коли** (when), **чому** (why), and **як** (how). In a typical sentence, these question words take the very first position.

*   **Хто це?** (Who is this?)
*   **Хто говорить?** (Who speaks?)
*   **Що це?** (What is this?)
*   **Що ти робиш?** (What are you doing?)

The distinction between **хто** (who) and **що** (what) is strictly tied to animacy. You must use **хто** when asking about people or animals, and **що** when asking about inanimate objects or abstract concepts. English speakers frequently use "what" to ask for a description or specification, such as "What color is it?" or "What kind of car is it?". You cannot do this in Ukrainian. The word **що** only asks for identification. If you point to a vehicle and ask **Що це?** (What is this?), the answer is simply "A car." To ask for a description, you must use the word **який** (what kind / which). This clear separation prevents confusion and guarantees that you receive the specific information you want.

Understanding location and movement requires mastering a spatial and temporal triplet: **де** (where), **куди** (where to), and **коли** (when). English often uses "where" for both a static location and a destination. Ukrainian separates these two concepts entirely. You use **де** when a person or object is resting in one place. You use **куди** strictly when there is physical motion directed toward a destination.

*   **Де ти живеш?** (Where do you live?)
*   **Де ти?** (Where are you?)
*   **Куди ти йдеш?** (Where are you going?)
*   **Коли ти працюєш?** (When do you work?)

Manner and reason use the question words **як** (how) and **чому** (why). You already know **як** from basic greetings, but it also asks for instructions or methods. The word **чому** almost always prompts an answer that starts with the conjunction **тому що** (because).

*   **Як справи?** (How are things?)
*   **Чому ти не працюєш?** (Why don't you work?)
*   **Тому що я хочу спати.** (Because I want to sleep.)

:::tip
The phrase **тому що** consists of two separate words. When answering a **чому** question, always use both words together to provide a natural, complete reason.
:::

Not every inquiry requires a specific question word. Many questions simply ask for a "yes" or "no" confirmation. In spoken Ukrainian, you create a yes/no question without changing the word order or adding any helper verbs. You simply raise your intonation at the end of the sentence.

*   **Ти знаєш.** (You know. — flat statement intonation)
*   **Ти знаєш? ↑** (Do you know? — rising pitch on the last word)
*   **Ти говориш українською? ↑** (Do you speak Ukrainian?)

You can also use the particle **чи** (whether / if) at the beginning of the sentence to act as a formal marker for a yes/no question. Even with this addition, the word order remains exactly the same as a regular statement.

*   **Чи ти знаєш?** (Do you know?)
*   **Чи ти говориш?** (Do you speak?)

Using **чи** is optional in casual everyday conversation, but it makes your question instantly recognizable in writing or more formal speech. Because Ukrainian grammar defines the roles of words clearly, the overall word order in questions remains quite flexible.

*   **Де ти живеш?** (Where do you live?)
*   **Ти де живеш?** (You where live?)

Both variations mean exactly the same thing. The first option, with the question word at the front, is the most neutral and common pattern.

<!-- INJECT_ACTIVITY: quiz-question-word-choice -->

<!-- INJECT_ACTIVITY: match-question-answer -->

## Заперечення (Negation)

Stating what is not happening or what you do not know is just as crucial as asking questions. The primary tool for negation in Ukrainian is the particle **не** (not). In English, you often need helper verbs like "do" or "does" to make a sentence negative. Ukrainian makes this process much simpler. You just place **не** directly before the main verb.

*   **Я не знаю.** (I do not know.)
*   **Ми не розуміємо.** (We do not understand.)
*   **Він не хоче.** (He does not want.)
*   **Він не працює.** (He does not work.)

The particle **не** forms a very tight unit with the verb that immediately follows it. You must never separate them with other words. 

When you need to answer a question negatively without providing a full sentence, you use the standalone word **ні** (no).

*   **Ти студент? — Ні.** (Are you a student? — No.)
*   **Ні, дякую.** (No, thank you.)
*   **Ні, я не знаю.** (No, I don't know.)

The word **ні** also serves as a prefix for creating negative pronouns and adverbs. By attaching **ні-** to question words, you generate vocabulary that represents the absolute absence of something.

*   **ніхто** (nobody)
*   **нічого** (nothing)
*   **ніколи** (never)
*   **ніде** (nowhere)

When you use these absolute negative words in a sentence, Ukrainian grammar requires a structure known as double negation. In English, grammar rules dictate that you can only have one negative element per clause — you say "I know nothing" or "I do not know anything." Ukrainian operates on a different, but highly consistent, logic. If a sentence contains a negative pronoun or adverb, the verb must also be negated with **не**. Both parts are strictly required to form a grammatically correct sentence.

*   **Я нічого не знаю.** (I know nothing. / Literally: I nothing do not know.)
*   **Ніхто не говорить.** (Nobody speaks. / Literally: Nobody does not speak.)
*   **Ніхто не прийшов.** (Nobody came.)
*   **Ми ніколи не відпочиваємо.** (We never rest.)

:::caution
Applying English logic to Ukrainian negation leads directly to grammatical errors. A sentence like "Я бачу нічого" (I see nothing) sounds broken to a native speaker. The presence of **нічого** absolutely demands the presence of **не** before the verb. You must say: **Я нічого не бачу**.
:::

<!-- INJECT_ACTIVITY: fill-in-negation-transform -->

<!-- INJECT_ACTIVITY: quiz-double-negation -->

## Підсумок — Summary

This module provided the essential tools for extracting information and expressing negative statements. You now possess a complete set of question words to navigate daily situations, gather facts, and build relationships.

*   **Хто?** (Who?)
*   **Що?** (What?)
*   **Де?** (Where?)
*   **Куди?** (Where to?)
*   **Коли?** (When?)
*   **Чому?** (Why?)
*   **Як?** (How?)

You learned that yes/no questions rely almost entirely on raising your intonation at the end of the sentence, such as **Ти знаєш?** (Do you know?). You also saw how the particle **чи** can optionally mark these questions in a more formal register, without ever altering the fundamental word order.

Negation in Ukrainian follows strict but simple patterns. The particle **не** always stands directly before the verb. When expressing absolute absence, Ukrainian demands double negation. 

| Структура (Structure) | Приклад (Example) | Переклад (Translation) |
| :--- | :--- | :--- |
| **Не + Verb** | **Я не знаю.** | I do not know. |
| **Ні- word + Не + Verb** | **Я нічого не знаю.** | I know nothing. |
| **Ні- word + Не + Verb** | **Ніхто не знає.** | Nobody knows. |

To verify your progress, respond to the following prompts. These practical tasks test your ability to apply the patterns you just read to real situations.

1.  Ask three questions about a friend's life using **де** (where), **що** (what), and **коли** (when). For example: **Де живе твій друг?** (Where does your friend live?)
2.  Change the positive statement "Я бачу все" (I see everything) into a negative statement meaning "I see nothing" using the double negation rule.
3.  Form a question from the statement **Ти говориш українською** (You speak Ukrainian) using only your intonation.
4.  Explain the grammatical difference between asking **Де ти?** (Where are you?) and **Куди ти йдеш?** (Where are you going?).

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: questions
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

**Level: A1.2-A1.3 (Module 19/55) — EARLY BEGINNER**

The learner knows the alphabet and ~200 words. They:
- Can read Ukrainian slowly
- Know basic nouns, adjectives, simple verb forms
- Cannot handle complex sentences or grammar terminology in Ukrainian

**Instructions in simple English with Ukrainian key terms in bold.**
Example: 'Choose the correct form of **мій/моя/моє**'

**Good activity types:** quiz, fill-in (simple sentences), match-up, group-sort, true-false, observe, anagram, translate (English→Ukrainian), error-correction (simple), divide-words, count-syllables, odd-one-out, order.


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
