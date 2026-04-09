<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/yesterday.yaml` file for module **49: Yesterday** (a1).

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

- `<!-- INJECT_ACTIVITY: ordering-daily-routine -->`
- `<!-- INJECT_ACTIVITY: fill-in-narrative-flow -->`
- `<!-- INJECT_ACTIVITY: gender-consistency-drill -->`

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

Being able to say what you did in the past is useful, but the real power of language comes from telling a story. Up until now, we have looked at isolated past tense sentences. Moving from a single statement to a connected narrative changes how you communicate. Compare a present tense fact like **Сьогодні я працюю** (Today I am working) with a past narrative like **Учора я працював** (Yesterday I worked). Knowing how to chain these actions together allows you to describe exactly what happened, step by step.

Sequencing actions is crucial when facts matter. In the situation below, a witness speaks to a police officer about a stolen bicycle. The witness uses past tense verbs to build a precise timeline of events.

> **Свідок:** Я припаркував велосипед біля магазину. *(I parked the bicycle near the store.)*
> **Поліцейський:** А потім? *(And then?)*
> **Свідок:** Потім зайшов у кав'ярню. *(Then I went into the cafe.)*
> **Поліцейський:** Ви довго там були? *(Were you there long?)*
> **Свідок:** Ні. Коли вийшов, велосипед зник. *(No. When I came out, the bicycle disappeared.)*
> **Поліцейський:** Ви бачили когось? *(Did you see anyone?)*
> **Свідок:** Бачив чоловіка в куртці та кепці. *(I saw a man in a jacket and a cap.)*

The words **велосипед** (bicycle) and **магазин** (store) are masculine, while **кав'ярня** (cafe) and **куртка** (jacket) are feminine. The sequence of verbs — **припаркував** (parked), **зайшов** (went in), **вийшов** (came out) — creates a clear, undeniable timeline of the incident.

:::note
When the order of events matters, using clear past tense verbs in sequence is essential. In official situations, a well-structured narrative establishes the facts without confusion.
:::

Narrating a day is just as common in casual conversation. Friends frequently catch up on a typical work day and discuss their routines.

> **Олег:** Як пройшов твій день? *(How was your day?)*
> **Тарас:** Добре! Зранку я прокинувся о сьомій. *(Good! In the morning I woke up at seven.)*
> **Олег:** Що ти робив зранку? *(What did you do in the morning?)*
> **Тарас:** Я поснідав і пішов на роботу. *(I had breakfast and went to work.)*
> **Олег:** А вдень? *(And in the afternoon?)*
> **Тарас:** Вдень я працював і обідав з колегою. *(In the afternoon I worked and had lunch with a colleague.)*
> **Олег:** А ввечері? *(And in the evening?)*
> **Тарас:** Ввечері я дивився фільм і рано ліг спати. *(In the evening I watched a film and went to sleep early.)*

And here is how someone might describe a fun weekend:

> **Максим:** Що ти робила у суботу? *(What did you do on Saturday?)*
> **Ірина:** О, я мала чудовий день! *(Oh, I had a wonderful day!)*
> **Максим:** Розкажи! *(Tell me!)*
> **Ірина:** Зранку я ходила на ринок і купила фрукти. *(In the morning I went to the market and bought fruit.)*
> **Максим:** А потім? *(And then?)*
> **Ірина:** Потім я готувала обід. А вдень гуляла в парку. *(Then I cooked lunch. And in the afternoon I walked in the park.)*
> **Максим:** А ввечері? *(And in the evening?)*
> **Ірина:** Ввечері ми з подругою ходили в ресторан. *(In the evening my friend and I went to a restaurant.)*
> **Максим:** Як файно! *(How nice!)*

Notice how the words **потім** (then) and the phrase **а потім** (and then) act as the glue between different verbs. They keep the story moving forward efficiently. Furthermore, in a connected story, we do not need to repeat the subject **я** (I) in every single sentence. Once the context is established, the verbs themselves carry the narrative perfectly.

## Розповідь про день (Narrating a Day)

To structure any story, you need clear time anchors. The daily routine is typically divided into four main parts. We use **зранку** (in the morning) for the start of the day. As the day progresses, we use **вдень** (in the afternoon). Later, we transition to **ввечері** (in the evening), and finally **вночі** (at night). 

:::caution
Pay attention to the spelling of **вдень**. Written as one word, it means "in the daytime" or "in the afternoon". Do not confuse it with the two-word phrase **в день** (on the day), which is used differently, such as in **в день народження** (on the birthday).
:::

Using the correct time markers gives the listener a clear map of when events occurred. Beyond basic time markers, sequencing words create a chronological chain. Without them, a story is just a list of disconnected facts. Start the sequence with **спочатку** (first). To transition to the next action, use **потім** (then). For further actions, use **після цього** (after that). To conclude the narrative, use **нарешті** (finally). These connectors turn separate thoughts into a fluid story.

*   **Спочатку я поснідав.** *(First I had breakfast.)*
*   **Потім я пішов на роботу.** *(Then I went to work.)*
*   **Після цього я обідав.** *(After that I had lunch.)*

This logical flow makes your Ukrainian sound much more natural and cohesive.

The daily routine relies on a core set of action verbs. Because the Ukrainian past tense must agree with the grammatical gender of the speaker, males use the **-в** or **-вся** ending, while females use the **-ла** or **-лася** ending. The most frequent verbs for narrating a day follow this pattern:

| Дієслово (Infinitive) | Чоловічий рід (Masculine) | Жіночий рід (Feminine) |
| :--- | :--- | :--- |
| **прокинутися** *(to wake up)* | **прокинувся** | **прокинулася** |
| **поснідати** *(to have breakfast)* | **поснідав** | **поснідала** |
| **піти** *(to go)* | **пішов** | **пішла** |
| **обідати** *(to have lunch)* | **обідав** | **обідала** |
| **повернутися** *(to return)* | **повернувся** | **повернулася** |
| **лягти спати** *(to lie down to sleep)* | **ліг спати** | **лягла спати** |

Notice that for the verb meaning to lie down (**лягти**), the masculine form **ліг** drops the **-в** suffix entirely, while the feminine form **лягла** keeps the standard **-ла** ending. This is a common pattern for verbs with stems ending in a consonant.

<!-- INJECT_ACTIVITY: ordering-daily-routine -->

## Мій учорашній день (My Yesterday)

A complete narrative relies on these structural elements. Anna describes her yesterday below. Since Anna is female, every past tense verb she uses ends in **-ла** or **-лася**. Her story chains actions logically using time markers.

*   **Учора був звичайний день.** *(Yesterday was an ordinary day.)*
*   **Зранку я прокинулася о пів на сьому.** *(In the morning I woke up at half past six.)*
*   **Я поснідала — їла кашу і пила каву.** *(I had breakfast — I ate porridge and drank coffee.)*
*   **Потім я пішла на роботу.** *(Then I went to work.)*
*   **Вдень я обідала в кафе біля офісу.** *(In the afternoon I had lunch in a cafe near the office.)*
*   **Я замовила салат і сік.** *(I ordered a salad and juice.)*
*   **Після роботи я ходила в магазин і купила продукти.** *(After work I went to the store and bought groceries.)*
*   **Ввечері я готувала вечерю і дивилася серіал.** *(In the evening I cooked dinner and watched a TV series.)*
*   **О одинадцятій я лягла спати.** *(At eleven I went to sleep.)*

This narrative is highly structured. Starting with **звичайний день** (ordinary day) sets the context immediately. Notice the strict gender agreement between the speaker and her actions. Because Anna is speaking, every verb aligns with her feminine gender: **прокинулася** (woke up), **поснідала** (had breakfast), **пішла** (went), **обідала** (had lunch), **купила** (bought), **готувала** (cooked), and **лягла** (lay down). If a man were telling this exact same story, all of those endings would shift to the masculine forms. 

:::tip
The pronoun **я** (I) remains the same, so the verb ending is the only indicator of the speaker's gender. Memorize the ending that matches your own gender and use it consistently.
:::

It is your turn to build a narrative. Use the following template to structure your thoughts:

*   **Учора...** *(Yesterday...)*
*   **Зранку я...** *(In the morning I...)*
*   **Потім...** *(Then...)*
*   **Вдень я...** *(In the afternoon I...)*
*   **Ввечері я...** *(In the evening I...)*

Combine these past-tense verbs with places you already know, such as a **кафе** (cafe), a **парк** (park), or a **магазин** (store). Add food items like **каша** (porridge), **кава** (coffee), or a **салат** (salad). You can also include the people you interacted with, whether it was a **друг** (friend), a **колега** (colleague), or a **подруга** (female friend). Everything you learned in A1 comes together here to help you share your personal story clearly and accurately.

<!-- INJECT_ACTIVITY: fill-in-narrative-flow -->
<!-- INJECT_ACTIVITY: gender-consistency-drill -->

## Summary

The narration toolkit contains the elements needed to describe past experiences. Telling a coherent story requires organizing verbs with time anchors and maintaining strict grammatical consistency.

*   **Time structure:** **зранку** → **вдень** → **ввечері** → **вночі**.
*   **Sequencing:** **спочатку**, **потім**, **після цього**, **нарешті**.
*   **Daily routine past forms:** **прокинувся/-лася**, **поснідав/-ла**, **пішов/пішла**, **обідав/-ла**, **повернувся/-лася**, **ліг/лягла спати**.
*   **Gender consistency:** male speakers use **-в/-вся** forms throughout, female speakers use **-ла/-лася** throughout.

Before you finish, perform a final self-check on your storytelling skills. Ask yourself these questions when building a narrative:

*   **Чи використав я принаймні 5 дієслів у минулому часі?** *(Did I use at least 5 verbs?)*
*   **Чи всі дієслова мають однаковий рід (чоловічий або жіночий)?** *(Are all verbs the same gender?)*
*   **Чи є в моїй розповіді «спочатку» і «потім»?** *(Are there "first" and "then"?)*

Tell the story of your yesterday using at least 5 verbs aloud, either to a partner or to yourself. Make absolutely sure to include what you ate for breakfast, using **поснідав** or **поснідала**, and mention when you went to sleep, using **ліг спати** or **лягла спати**. Practice this daily until the sequence feels natural and your verb endings match your gender automatically.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: yesterday
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
