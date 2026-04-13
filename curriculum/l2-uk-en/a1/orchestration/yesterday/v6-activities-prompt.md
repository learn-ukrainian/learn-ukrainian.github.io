<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/yesterday.yaml` file for module **49: Yesterday** (a1).

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

- `<!-- INJECT_ACTIVITY: order-daily-routine -->`
- `<!-- INJECT_ACTIVITY: fill-in-time-markers -->`
- `<!-- INJECT_ACTIVITY: fill-in-gender-consistency -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Put the daily routine in chronological order
  items:
  - Зранку я прокинувся.
  - Спочатку я поснідав.
  - Потім я пішов на роботу.
  - Вдень я обідав з колегою.
  - Ввечері я повернувся і дивився серіал.
  - Нарешті я ліг спати.
  type: ordering
- focus: Complete the narrative with time markers and sequenced verbs
  items:
  - Учора {зранку|вдень|потім} я прокинулася о сьомій.
  - '{Спочатку|Нарешті|Вночі} я поснідала.'
  - '{Потім|Зранку|Ввечері} я пішла на роботу.'
  - Вдень я {обідала|обідав|обідали} в кафе.
  - '{Ввечері|Вдень|Зранку} я готувала вечерю.'
  - О десятій я {лягла|ліг|лягли} спати.
  type: fill-in
- focus: Practice gender consistency in narration (Female speaker 'Anna')
  items:
  - Я мала звичайний день. Я {прокинулася|прокинувся} рано.
  - Потім я {поснідала|поснідав}.
  - Після цього я {пішла|пішов} у магазин.
  - Там я {купила|купив} продукти.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- спочатку (first/at first)
- нарешті (finally)
- повернутися (to return)
- лягти (to lie down)
- звичайний (ordinary, adj)
- продукти (groceries, pl)
- серіал (TV series, m)
- колега (colleague, m/f)
required:
- учора (yesterday)
- зранку (in the morning)
- вдень (in the afternoon)
- ввечері (in the evening)
- потім (then)
- прокинутися (to wake up)
- поснідати (to have breakfast)
- обідати (to have lunch)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Dialogues

Chaining events together in a logical order is a vital skill in any language, and in Ukrainian, it is the key to sharing your life with others. Whether you are telling a friend about your weekend or reporting a missing item to the authorities, you need to know how to sequence actions. Talking about your daily routine — what you did from the moment you opened your eyes until you went to sleep — is one of the most common conversational topics. By the end of this module, you will be able to turn a simple list of actions into a coherent story that flows naturally from morning to night.

In our first dialogue, let us listen to Petro as he describes a typical workday. Notice how he uses specific time markers to signal each phase of his day.

> **Колега:** Як пройшов твій день? *(How was your day?)*
> **Петро:** Добре! Зранку я **прокинувся** (woke up) о сьомій. *(Good! In the morning I woke up at seven.)*
> **Колега:** Що ти робив зранку? *(What did you do in the morning?)*
> **Петро:** Я **поснідав** (had breakfast) і **пішов** (went) на роботу. *(I had breakfast and went to work.)*
> **Колега:** А вдень? *(And in the afternoon?)*
> **Петро:** Вдень я працював і **обідав** (had lunch) з колегою. *(In the afternoon I worked and had lunch with a colleague.)*
> **Колега:** А ввечері? *(And in the evening?)*
> **Петро:** Ввечері я дивився фільм і рано **ліг** спати. *(In the evening I watched a movie and went to bed early.)*

This short conversation demonstrates how the "skeleton" of a day is built using four main blocks: **зранку** (in the morning), **вдень** (in the afternoon), **ввечері** (in the evening), and finally, **лягти** (to lie down/go to) спати. Petro is a man, so his past tense verbs all end in the masculine suffix **-в** or **-вся**. He says **прокинувся** (I woke up), **поснідав** (I had breakfast), **пішов** (I went), and **ліг** (I lay down). These endings are consistent throughout his entire story, reflecting his gender in every action he recounts.

Now, let us listen to a feminine perspective. Anna is telling her friend about her Saturday. Pay attention to how the verb endings change and how she uses "then" to keep the story moving.

> **Подруга:** Що ти робила у суботу? *(What did you do on Saturday?)*
> **Анна:** О, я мала чудовий день! *(Oh, I had a wonderful day!)*
> **Подруга:** Розкажи! *(Tell me!)*
> **Анна:** Зранку я **ходила** (went) на ринок і **купила** (bought) фрукти. *(In the morning I went to the market and bought fruit.)*
> **Подруга:** А **потім** (then)? *(And then?)*
> **Анна:** **Потім** я готувала обід. А вдень гуляла в парку. *(Then I was cooking lunch. And in the afternoon I walked in the park.)*
> **Подруга:** А ввечері? *(And in the evening?)*
> **Анна:** Ввечері ми з подругою **ходили** (went) в ресторан. *(In the evening me and a friend went to a restaurant.)*
> **Подруга:** Як файно! *(How lovely!)*

Because Anna is female, her verbs end in **-ла**: **ходила** (went), **купила** (bought), **готувала** (cooked). She also uses the word **потім** (then) several times. In Ukrainian, **потім** is a very useful "glue" word that allows you to link one event to another without repeating the time of day. You can also use **а потім** (and then) to add a bit of variety to your storytelling.

## Розповідь про день (Narrating a Day)

To tell a story effectively, you need a timeline. Ukrainian uses four primary adverbs to divide the day into manageable chunks. These words usually appear at the start of a sentence to establish the context immediately.

*   **зранку** (in the morning) — used for everything from waking up to starting work.
*   **вдень** (in the afternoon / during the day) — used for the middle of the day, typically lunchtime and work hours.
*   **ввечері** (in the evening) — used for the time after work, dinner, and relaxation.
*   **вночі** (at night) — used for the late hours when the world is asleep.

When you put these together, you create a natural progression. For example, a student might say:

**Зранку** я читав книгу. **Вдень** я був в університеті. **Ввечері** я відпочивав.
> *In the morning I read a book. In the afternoon I was at the university. In the evening I was resting.*

Once you have your time blocks, you need sequencing words to connect the dots. Without these, your story sounds like a grocery list of isolated facts. Ukrainian provides a specific set of adverbs to help you navigate through time:

*   **спочатку** (first / at first) — sets the very first scene.
*   **потім** (then) — the most common way to move to the next event.
*   **після цього** (after that) — a slightly more formal way to say "after that."
*   **нарешті** (finally) — used to signal the last action in a sequence.

Observe how these words transform separate sentences into a cohesive narrative paragraph:

**Спочатку** я **поснідав**. **Потім** я **пішов** на роботу. **Після цього** я **обідав**. **Нарешті** я **повернувся** додому.
> *First I had breakfast. Then I went to work. After that I had lunch. Finally I returned home.*

The "engine" of your narrative consists of daily routine verbs. In the past tense, these verbs must match your gender. Here is a table showing the most common routine verbs in their masculine and feminine forms.

| Verb (Infinitive) | Male Speaker (Він) | Female Speaker (Вона) | Meaning |
| :--- | :--- | :--- | :--- |
| **прокинутися** | **прокинувся** | **прокинулася** | to wake up |
| **поснідати** | **поснідав** | **поснідала** | to have breakfast |
| **піти** | **пішов** | **пішла** | to go / set out |
| **працювати** | **працював** | **працювала** | to work |
| **бути** | **був** | **була** | to be |

:::tip
Notice the verb **пішов** (masculine) and **пішла** (feminine). This is an irregular shift from the infinitive **піти**. It is one of the most common verbs in the past tense, so it is worth memorizing these two forms early!
:::

As the day continues, you will need verbs for the afternoon and evening activities. These follow the same gender-agreement patterns.

*   **обідати** (to have lunch) → **обідав** / **обідала**
*   **повернутися** (to return) → **повернувся** / **повернулася**
*   **вечеряти** (to have dinner) → **вечеряв** / **вечеряла**
*   **лягти** спати (to go to bed) → **ліг** спати / **лягла** спати

The verb **лягти** (to lie down) is particularly unique. A man says **я ліг**, while a woman says **я лягла**. This change from **і** to **я** is a common feature in some old Ukrainian verbs, but for now, just treat them as a pair of set forms for "going to bed."

<!-- INJECT_ACTIVITY: order-daily-routine -->

## Мій учорашній день (My Yesterday)

A truly natural story is more than just a list of verbs; it is a tapestry that combines your actions with the places you visited, the food you ate, and the people you met. To make your narrative "come alive," you should integrate the vocabulary you have learned in previous modules. Instead of just saying "I ate," you can say "I ate porridge and drank coffee." This adds texture and personality to your speech.

Let us look at a model narrative from Anna. She is describing an **звичайний** (ordinary) day. Pay close attention to how she weaves together her routine, her meals, and her evening relaxation.

**Учора** був **звичайний** день. **Зранку** я **прокинулася** о пів на сьому. Я **поснідала** — їла кашу і пила каву. **Потім** я **пішла** на роботу. **Вдень** я **обідала** в кафе біля офісу. Я замовила салат і сік. Після роботи я **ходила** в магазин і купила **продукти** (groceries). **Ввечері** я готувала вечерю і дивилася **серіал** (TV series). О одинадцятій я **лягла** спати.
> *Yesterday was an ordinary day. In the morning I woke up at half past six. I had breakfast — I ate porridge and drank coffee. Then I went to work. In the afternoon I had lunch in a cafe near the office. I ordered a salad and juice. After work I went to the store and bought groceries. In the evening I was cooking dinner and watching a TV series. At eleven I went to bed.*

If we analyze Anna's story, we can see why it sounds so authentic. First, because Anna is a woman, every single past tense verb ends in **-ла**: **прокинулася**, **поснідала**, **пішла**, **обідала**, **ходила**, **лягла**. This consistency is the hallmark of a fluent speaker. Second, she uses her surroundings to ground the story. She doesn't just "go"; she goes to the **магазин** (store) or the **кафе**. She doesn't just "eat"; she eats **продукти** (groceries) or a **салат**.

:::note
Even in a simple story, Ukrainian style prefers to avoid repetition. Anna uses **потім** (then) and **після роботи** (after work) to transition between scenes. This prevents every sentence from starting with "I did this, I did that."
:::

Now it is your turn to build your own narrative. You can use the template below as a guide. Simply choose the verb forms that match your gender and fill in the details of your own life.

**Учора...** (**Учора був гарний день!**)
**Зранку я...** (Select: **прокинувся** / **прокинулася**)
**Потім я...** (Select: **поснідав** / **поснідала** ... **каву / чай / кашу**)
**Вдень я...** (Select: **працював** / **працювала** ... **в офісі / вдома**)
**Ввечері я...** (Select: **дивився** / **дивилася** ... **серіал / фільм**)
**Нарешті я...** (Select: **ліг** / **лягла** ... **спати**)

Try to include at least one **колега** (colleague) or **друг** (friend) in your story to make it more social. The more you practice connecting these chunks, the faster you will move from "translating" to "thinking" in Ukrainian.

<!-- INJECT_ACTIVITY: fill-in-time-markers -->

<!-- INJECT_ACTIVITY: fill-in-gender-consistency -->

## Summary

Narrating your day in Ukrainian is like building a bridge across time. You start with a solid foundation of time markers that divide your story into logical segments. By using **зранку** (in the morning), **вдень** (in the afternoon), and **ввечері** (in the evening), you provide a clear, natural flow that native speakers expect. These words act as signposts, letting your listener know exactly where they are in your timeline.

To make that bridge smooth, you use sequencing words as the "glue" between your sentences. Without words like **спочатку** (first), **потім** (then), **після цього** (after that), and **нарешті** (finally), your speech would sound like a series of disconnected bumps. These connectors are the secret to moving beyond disjointed phrases into a fluid, connected story that sounds professional and natural.

In this module, we have focused on a core toolkit of routine verbs that cover the vast majority of daily life. Mastering these few forms allows you to describe almost any day:

*   **прокинувся/-лася** (woke up)
*   **поснідав/-ла** (had breakfast)
*   **пішов/пішла** (went)
*   **обідав/-ла** (had lunch)
*   **повернувся/-лася** (returned)
*   **ліг/лягла** спати (went to bed)

The most important rule to remember is gender consistency. In English, "I went" is the same for everyone, but in Ukrainian, your gender is built into the verb itself. A man must strictly use the **-в** or **-вся** forms throughout his story, while a woman must strictly use the **-ла** or **-лася** forms. Switching between them mid-story is a common learner mistake that can confuse your listener.

As a final self-check, try to tell the story of your **учора** (yesterday) aloud right now. Use at least five of the routine verbs and three different time markers. If you can tell your story from morning to night without stopping, you have mastered the art of Ukrainian narration!
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: yesterday
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

**Level: A1.4+ (Module 49/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-gender [§4.2.1.1, §4.2.2]
**Рід іменників** (Noun gender)
- **group-sort** — Він, вона чи воно?: Розподілити іменники за граматичним родом за закінченням / Sort nouns by grammatical gender using ending rules
  - Instruction: *Розподіліть слова за родами*
- **quiz** — Який рід?: Визначити рід за закінченням: приголосний=чол., -а/-я=жін., -о/-е=серед. / Determine gender from ending — consonant=masc, -а/-я=fem, -о/-е=neut
- **fill-in** — Мій, моя чи моє?: Обрати присвійний займенник, що узгоджується з родом іменника / Choose possessive that matches noun gender
  - Instruction: *Вставте правильне слово*
- **match-up** — Іменник + займенник: Зіставити іменники з він/вона/воно / Match nouns to він/вона/воно
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: На рівні A1 завжди давати варіанти для вибору

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
