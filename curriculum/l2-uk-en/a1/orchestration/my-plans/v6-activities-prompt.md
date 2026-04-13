<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/my-plans.yaml` file for module **51: My Plans** (a1).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 10 | 10+ | inline + workbook combined |
| Inline (lesson tab) | 4 | 6 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 6 | 9 | extended practice |
| Items per activity | 6 | — | each activity must have at least 6 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 4 inline activities AND at least 6 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** image-to-letter, letter-grid, match-up, watch-and-repeat, quiz, true-false, fill-in, classify
- **Inline priority (preferred):** image-to-letter, match-up, fill-in, quiz, watch-and-repeat
- **Workbook types:** fill-in, match-up, group-sort, anagram, unjumble, quiz, true-false, classify, divide-words, count-syllables, pick-syllables, observe, phrase-table, odd-one-out
- **Workbook priority (preferred):** fill-in, match-up, group-sort, anagram, unjumble
- **FORBIDDEN at this level:** cloze, error-correction, mark-the-words, translate, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, highlight-morphemes, grammar-identify, select

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 4–6 quick checks after key teaching points. Workbook = 6–9 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: fill-in-schedule-time -->`
- `<!-- INJECT_ACTIVITY: match-invitations -->`
- `<!-- INJECT_ACTIVITY: fill-in-weekly-plan -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Combine days of the week, time, and future tense
  items:
  - У {понеділок|вівторок|середу} я буду працювати.
  - У суботу {зранку|ввечері|вдень} я буду прибирати квартиру.
  - '{О|В|На} шостій ми будемо дивитися кіно.'
  - У {неділю|суботу|п'ятницю} він буде відпочивати.
  - У п'ятницю {ввечері|зранку|вдень} буде вечірка.
  type: fill-in
- focus: Match invitations to natural responses
  pairs:
  - Ходімо в кіно!: З задоволенням!
  - Може, підемо в кафе?: Добре! О котрій?
  - Ти будеш вільний у суботу?: На жаль, не можу.
  - Давай зустрінемося о п'ятій!: Чудово! До зустрічі!
  type: matching
- focus: Complete a scheduled plan for the week
  items:
  - У вівторок я {буду вчити|вчив|вчу} українську.
  - У середу ми {будемо готувати|готували|готуємо} вечерю.
  - У четвер вона {буде працювати|працювала|працює} допізна.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- зустрінемося (let's meet — chunk)
- з задоволенням (with pleasure)
- на жаль (unfortunately)
- допізна (until late)
- звичайно (of course)
- квартира (apartment, f)
- кіно (cinema, n)
- вчити (to study/learn)
required:
- план (plan, m)
- тиждень (week, m)
- вільний (free, adj)
- зустріч (meeting, f)
- відпочивати (to rest)
- прибирати (to clean)
- вечірка (party, f)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Dialogues

Arranging a weekend get-together with friends is a perfect way to practice discussing the future. In Ukrainian, expressing a **план** (plan) is a practical skill you use every single day. When organizing your time, you will often need to state what you are doing, when you are doing it, and ask others if they are **вільний** (free). Read this group chat where three friends are trying to align their weekend schedules and find time to relax together.

> **Оксана:** Що ти будеш робити у суботу? *(What will you be doing on Saturday?)*
> **Максим:** Зранку я буду прибирати квартиру. *(In the morning, I will be cleaning the apartment.)*
> **Оксана:** А вдень? *(And in the afternoon?)*
> **Максим:** Вдень я буду ходити в магазин. А ти? *(In the afternoon, I will go to the store. And you?)*
> **Дарина:** Я буду відпочивати! Може, підемо в кафе ввечері? *(I will be resting! Maybe we will go to a cafe in the evening?)*
> **Оксана:** Добре! О котрій? *(Good! At what time?)*
> **Дарина:** О шостій. Добре? *(At six. Good?)*
> **Максим:** Чудово! До зустрічі у суботу! *(Great! See you on Saturday!)*

This short conversation is rich with real-world communication patterns. Notice how Максим combines a time of day with a future action to structure his day. He uses the words **зранку** (in the morning) and **вдень** (in the afternoon) to divide his Saturday into clear segments. Дарина shifts the conversation from personal routines to a shared invitation. Then, Оксана quickly confirms the specific time using the question phrase **о котрій?** (at what time?). This flow moves logically from individual tasks to a shared group activity, representing exactly how friends communicate.

Here is how someone might describe their simple plans for a single day:

Сьогодні я буду відпочивати. Вдень я буду гуляти в парку. Ввечері я буду читати книгу.
> *(Today I will rest. In the afternoon I will walk in the park. In the evening I will read a book.)*

:::caution
When discussing plans, avoid translating directly from English phrases like "I have plans." Instead, use the structure **У мене є плани** (I have plans), which relies on the possession pattern you already know.
:::

Now, read a different conversation about organizing a busy **тиждень** (week) filled with work, studies, and social events. Scheduling involves mapping out commitments day by day.

> **Антон:** У тебе є плани на тиждень? *(Do you have plans for the week?)*
> **Віктор:** Так, багато! *(Yes, many!)*
> **Антон:** У понеділок я буду працювати допізна. *(On Monday, I will work until late.)*
> **Віктор:** У вівторок буду вчитися. У середу — зустріч з друзями. *(On Tuesday, I will study. On Wednesday — a meeting with friends.)*
> **Антон:** А у четвер? *(And on Thursday?)*
> **Віктор:** У четвер я буду готувати на вечірку. *(On Thursday, I will prepare for a party.)*
> **Антон:** А в п'ятницю? *(And on Friday?)*
> **Віктор:** В п'ятницю — вечірка! Ти будеш? *(On Friday — a party! Will you be there?)*
> **Антон:** Звичайно буду! *(Of course I will!)*

This second dialogue shifts focus from a single day to the entire week. The speakers map out their obligations chronologically, from Monday to Friday. They use the days of the week alongside the future tense to create a clear timeline of events like a **зустріч** (meeting) or a **вечірка** (party). Notice the question **Ти будеш?** (Will you be there?) — this is a highly natural, conversational way to confirm attendance at an event. You do not always need a full verb like "attend"; the verb "to be" in the future tense is perfectly sufficient for asking if someone plans to show up.

## Планування (Planning)

Scheduling requires combining the day of the week with the correct preposition. To say "on a certain day," use the temporal pattern **У/В** + Accusative case form of the day.

- **у понеділок** (on Monday)
- **у вівторок** (on Tuesday)
- **у середу** (on Wednesday)
- **у четвер** (on Thursday)
- **у п'ятницю** (on Friday)
- **у суботу** (on Saturday)
- **в неділю** (on Sunday)

:::note
Notice the vowel ending change for feminine days. The days **середа**, **п'ятниця**, and **субота** change their final **-а** or **-я** to **-у** or **-ю**. Masculine days like **понеділок** remain unchanged.
:::

To specify the exact time of an event, use the preposition **о** (or **об** before a vowel) followed by the ordinal number in the Locative case. You can combine the hour with the parts of the day to be precise.

- **о третій** (at three)
- **о шостій** (at six)
- **о дев'ятій** (at nine)
- **об одинадцятій** (at eleven)

You can easily pair the day, the time, and the part of the day.

- У понеділок вранці я працюю. *(On Monday morning I work.)*
- У суботу ввечері ми читаємо. *(On Saturday evening we read.)*
- В неділю вдень вона гуляє. *(On Sunday afternoon she walks.)*

To express what you plan to do at these times, use the compound future tense. This structure is very straightforward: use the future form of the verb "to be" (**бути**), which must match the subject (like **я буду**, **ти будеш**, **ми будемо**), and add an imperfective infinitive verb. The imperfective aspect emphasizes the process or the duration of the action, which is perfect for laying out a continuous schedule. The full structural formula is **У [day] о [time] я буду [verb]**.

- У суботу о третій я буду готувати. *(On Saturday at three I will cook.)*
- У вівторок ввечері ти будеш читати. *(On Tuesday evening you will read.)*
- В неділю зранку ми будемо спати. *(On Sunday morning we will sleep.)*

When you want to include others in your plans, you need functional chunks for making and responding to invitations.

- **Ходімо в кафе!** *(Let's go to a cafe!)*
- **Може, підемо в кіно?** *(Maybe we will go to the cinema?)*
- **Ти будеш вільний у суботу?** *(Will you be free on Saturday? - masculine)*
- **Ти будеш вільна у суботу?** *(Will you be free on Saturday? - feminine)*
- **Давай зустрінемося о п'ятій!** *(Let's meet at five!)*

Responding naturally keeps the conversation moving.

- **Добре!** *(Good!)*
- **Чудово!** *(Great!)*
- **З задоволенням!** *(With pleasure!)*
- **На жаль, не можу.** *(Unfortunately, I cannot.)*

Here is how these scheduling elements look in a continuous thought:

У п'ятницю я працюю допізна. У суботу ввечері ми будемо дивитися кіно. Давай зустрінемося о шостій біля кафе!
> *(On Friday I work until late. On Saturday evening we will watch a movie. Let's meet at six near the cafe!)*

<!-- INJECT_ACTIVITY: fill-in-schedule-time -->

<!-- INJECT_ACTIVITY: match-invitations -->

## Мій тиждень (My Week)

When you connect your daily routines into a larger timeline, you form a cohesive narrative about your life. Look at this model monologue detailing Taras's entire week. Notice how he strings sentences together chronologically.

У понеділок я буду працювати. Після роботи буду вчити українську. У вівторок я буду обідати в кафе. У середу ввечері я буду дивитися футбол. У четвер я буду готувати вечерю для родини. У п'ятницю я буду відпочивати. Я піду в кіно. У суботу зранку я буду прибирати. Вдень я буду гуляти в парку. В неділю я буду спати довго!
> *(On Monday I will work. After work I will study Ukrainian. On Tuesday I will have lunch in a cafe. On Wednesday evening I will watch football. On Thursday I will prepare dinner for the family. On Friday I will rest. I will go to the cinema. On Saturday morning I will clean. In the afternoon I will walk in the park. On Sunday I will sleep long!)*

Taras uses the same foundational structure for every single day, creating a steady rhythm. The action moves smoothly from the start of the week toward the weekend. By keeping his sentences short and focused, he communicates his entire weekly availability without using complicated grammar.

Now, you can create your own weekly plan. Use the core template **У [day] я буду [activity]**. This template is your safest tool for building confidence. To make your sentences more descriptive, expand the basic template by adding specific details. Answer the question **о котрій?** (at what time?) to set a schedule. Answer **де?** (where?) to provide a location. Answer **з ким?** (with whom?) to include the people in your life.

For example, instead of just saying "I will walk," you can build a detailed sentence that paints a much clearer picture of your afternoon:

- У суботу я буду гуляти в парку з другом. *(On Saturday I will walk in the park with a friend.)*
- У середу ввечері ми будемо читати вдома. *(On Wednesday evening we will read at home.)*
- В неділю вдень вона буде обідати в кафе. *(On Sunday afternoon she will have lunch in a cafe.)*

Take a moment to map out your own upcoming days. Use the vocabulary you already know for places like your apartment, a restaurant, or the cinema. Include your daily activities like studying, working, cleaning, and resting.

<!-- INJECT_ACTIVITY: fill-in-weekly-plan -->

## Summary

The ability to structure your time and share your schedule is a major milestone in communication. The core grammatical formula for scheduling in this module is extremely reliable: Day + time + буду + infinitive. This pattern is the primary way you will express future plans in the early stages of your learning journey.

У суботу о третій я буду готувати обід. Ввечері я буду відпочивати. У неділю я буду читати.
> *(On Saturday at three I will prepare lunch. In the evening I will rest. On Sunday I will read.)*

When you want to turn your personal schedule into a social event, you rely on a few key invitation chunks. You can propose an outing with **Ходімо!** (Let's go!), suggest an idea with **Може, підемо?** (Maybe we will go?), or specify a time with **Давай зустрінемося!** (Let's meet!). You can then respond enthusiastically with **Добре!** (Good!) or **З задоволенням!** (With pleasure!), or politely decline using **На жаль, не можу** (Unfortunately, I cannot).

To successfully navigate a calendar, you must retain the days of the week. Review the sequence to ensure they come to mind effortlessly: **понеділок**, **вівторок**, **середа**, **четвер**, **п'ятниця**, **субота**, **неділя**.

:::tip
Mental practice is one of the most effective ways to solidify new vocabulary. While riding the bus or waiting in line, try to list the days of the week silently to yourself.
:::

Now it is time for a self-check task. Mentally plan your ideal weekend using these new structures. Ask yourself: **Що ти будеш робити у суботу?** (What will you do on Saturday?). Think about Sunday: **А в неділю?** (And on Sunday?). Finally, consider the people you want to see: **З ким ти будеш зустрічатися?** (Who will you be meeting?). Formulate your answers in complete Ukrainian sentences to prove you can manage your own schedule.
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: my-plans
level: a1

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (10 total / 4–6 inline / 6–9 workbook,
# 6+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 6 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 6 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 6 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 6 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 6 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 6 pairs total

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
    items:                     # ← real output: ≥ 6 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 6 items total

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

**Level: A1.4+ (Module 51/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


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

### Pattern: grammar-possession [§4.2.1.4, §4.2.2]
**Присвійність** (Possession)
- **fill-in** — У мене є...: Структура «У мене/тебе/нього є...» — як українська виражає володіння / Structure «У мене/тебе/нього є...» — how Ukrainian expresses possession
  - Instruction: *Вставте правильне слово*
- **fill-in** — Мій, твій, наш...: Обрати присвійний займенник, що узгоджується з родом та числом іменника / Choose possessive pronoun matching noun gender and number
  - Instruction: *Вставте правильну форму*
- **match-up** — Чий? Чия? Чиє?: Зіставити присвійний займенник з іменником за родом / Match possessive pronoun to noun by gender
  - Instruction: *З'єднайте*
- **quiz** — У кого є?: Визначити, хто має щось, за контекстом речення / Determine who has something based on sentence context
**Anti-patterns (DO NOT generate):**
- ❌ translate: «У мене є» — унікальна українська структура. Переклад з англ. «I have» маскує різницю

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

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 10 activities.** Inline: 4–6. Workbook: 6–9. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 6 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 6.
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
2. Run `query_cefr_level` on any word you're unsure about — it must be a1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **at least 4** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 6** workbook activities.
- [ ] **Total ≥ 10.**
- [ ] **Every** activity has **at least 6** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 4 and 6. I did NOT create more injection markers than 6.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
