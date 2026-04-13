<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/i-eat-i-drink.yaml` file for module **37: I Eat, I Drink** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-conjugation -->`
- `<!-- INJECT_ACTIVITY: fill-in-accusative-endings -->`
- `<!-- INJECT_ACTIVITY: group-sort-accusative -->`
- `<!-- INJECT_ACTIVITY: quiz-accusative-selection -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- blanks:
  - Я їм (риба) {рибу}.
  - Вона п'є (вода) {воду}.
  - Він їсть (хліб) {хліб}.
  - Ми п'ємо (молоко) {молоко}.
  - Вони їдять (каша) {кашу}.
  - Ти п'єш (кава) {каву}.
  - Я їм (суп) {суп}.
  - Вона їсть (картопля) {картоплю}.
  focus: Form the accusative case for feminine (-а/-я → -у/-ю) and masculine/neuter
    (no change)
  items: 8
  type: fill-in
- focus: Select the correct accusative form to complete the sentence
  items: 6
  questions:
  - Я п'ю... (каву / кава / кави)
  - Він їсть... (рибу / риба / рибі)
  - Ми п'ємо... (сік / соку / соком)
  - Вона їсть... (м'ясо / м'ясу / м'яса)
  - Вони п'ють... (воду / вода / воді)
  - Ти їш... (кашу / каша / каші)
  type: quiz
- blanks:
  - Я {їм} суп.
  - Ми {п'ємо} чай.
  - Вона {їсть} хліб.
  - Вони {п'ють} воду.
  - Ти {їси} рибу?
  - Ви {п'єте} каву?
  - Він {п'є} сік.
  - Вони {їдять} кашу.
  focus: Conjugate the verbs їсти (irregular) and пити (Group I)
  items: 8
  type: fill-in
- focus: Sort nouns based on how they change in the accusative case (inanimate)
  groups:
  - items:
    - кава
    - вода
    - риба
    - каша
    name: Змінюється (-у/-ю)
  - items:
    - хліб
    - сік
    - молоко
    - м'ясо
    name: Не змінюється (як у називному)
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- кашу (porridge — accusative)
- картоплю (potato — accusative)
- сметану (sour cream — accusative)
- їсть (he/she eats)
- п'є (he/she drinks)
- їдять (they eat)
- п'ють (they drink)
required:
- їсти (to eat — irregular)
- пити (to drink)
- їм (I eat)
- п'ю (I drink)
- каву (coffee — accusative)
- воду (water — accusative)
- рибу (fish — accusative)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Food and daily routines are universal topics that connect us all. When learning Ukrainian, organizing your vocabulary around daily meals is the most practical and immediate way to start speaking. In Ukraine, daily life revolves around three main meals. In the morning, people have a **сніданок** (breakfast). In the middle of the day, it is time for an **обід** (lunch), which is traditionally the largest meal and often includes soup. Finally, the day ends with a **вечеря** (dinner). To talk about these meals, we need the core verbs that describe our eating and drinking habits. The following realistic conversation shows how Ukrainians actually talk about their food in everyday situations.

> **Оксана і Тарас працюють разом. Зараз ранок.**
> *Oksana and Taras work together. It is morning now.*
> **Оксана:** Тарасе, що ти зазвичай їш на сніданок?
> *Oksana: Taras, what do you usually eat for breakfast?*
> **Тарас:** Я їм кашу і п'ю каву. А ти?
> *Taras: I eat porridge and drink coffee. And you?*
> **Оксана:** Я теж! А Олена?
> *Oksana: Me too! And Olena?*
> **Тарас:** Вона їсть хліб з маслом і п'є чай.
> *Taras: She eats bread with butter and drinks tea.*
> **Оксана:** Зрозуміло. А діти?
> *Oksana: Understood. And the children?*
> **Тарас:** Вони їдять яйця і п'ють молоко.
> *Taras: They eat eggs and drink milk.*

Notice how the forms of the verbs change depending on who is performing the action. When Taras talks about himself, he says **я їм** (I eat) and **я п'ю** (I drink). When he mentions his colleague Olena, he switches to **вона їсть** (she eats) and **вона п'є** (she drinks). Finally, for the plural "children", he uses **вони їдять** (they eat) and **вони п'ють** (they drink). This demonstrates the full conjugation spectrum in a natural context.

Later in the day, the same colleagues might gather for their lunch break. The next dialogue illustrates how they talk about their midday meal and how they order food.

> **Обідня перерва в офісі.**
> *Lunch break at the office.*
> **Оксана:** Що ви їсте на обід сьогодні?
> *Oksana: What are you eating for lunch today?*
> **Тарас і Олена:** Ми їмо суп і салат.
> *Taras and Olena: We are eating soup and salad.*
> **Оксана:** Смачно! А що п'єте?
> *Oksana: Tasty! And what are you drinking?*
> **Тарас:** Ми п'ємо воду або сік.
> *Taras: We are drinking water or juice.*
> **Оксана:** Я теж хочу суп.
> *Oksana: I also want soup.*
> **Олена:** Добре, замовляй!
> *Olena: Good, order it!*

This second dialogue reviews the verbs with plural subjects like **ми** (we) and introduces a very useful transactional verb: **хотіти** (to want). Oksana says **я хочу** (I want) to express her desire for soup. You will use these phrases constantly whether you are unpacking lunch boxes with colleagues or ordering at a cafe.

## Їсти і пити (To Eat and To Drink)

To actively participate in conversations about food, you must master two essential, high-frequency daily verbs: **їсти** (to eat) and **пити** (to drink). Because these actions are so fundamental to human life, the verbs describing them are very old, and they can be slightly unusual. The verb **їсти** is completely irregular. It does not follow the standard Group I or Group II conjugation patterns used for most other verbs. On the other hand, **пити** is a Group I verb, but it features a shifting stem that requires careful attention to spelling and pronunciation.

The irregular verb **їсти** requires memorizing its forms individually, as they appear constantly in daily conversation.

| Займенник (Pronoun) | Дієслово (Verb) | Переклад (Translation) |
| :--- | :--- | :--- |
| я | **їм** | I eat |
| ти | **їси** | you eat (informal) |
| він / вона / воно | **їсть** | he / she / it eats |
| ми | **їмо** | we eat |
| ви | **їсте** | you eat (formal/plural) |
| вони | **їдять** | they eat |

:::caution
A very common mistake for learners is confusing the first-person and third-person forms. Remember that **я їм** means "I eat," while **він їсть** means "he eats." Do not mix them up!
:::

These sentences demonstrate the forms in simple contexts:
*   **Я їм смачний суп.** (I am eating a tasty soup.)
*   **Ти їси хліб.** (You are eating bread.)
*   **Вона їсть м'ясо.** (She is eating meat.)
*   **Ми їмо салат.** (We are eating a salad.)
*   **Ви їсте борщ.** (You are eating borscht.)
*   **Вони їдять кашу.** (They are eating porridge.)

The verb **пити** (to drink) is a Group I verb, but its stem changes dramatically from the infinitive form to the present tense forms.

| Займенник (Pronoun) | Дієслово (Verb) | Переклад (Translation) |
| :--- | :--- | :--- |
| я | **п'ю** | I drink |
| ти | **п'єш** | you drink (informal) |
| він / вона / воно | **п'є** | he / she / it drinks |
| ми | **п'ємо** | we drink |
| ви | **п'єте** | you drink (formal/plural) |
| вони | **п'ють** | they drink |

Notice the apostrophe in words like **п'ю** and **п'є**. In Ukrainian orthography, the apostrophe indicates a slight pause and signals that the following letter (ю, є, я, ї) should be pronounced as two distinct sounds (for example, й + у). Therefore, **п'ю** is pronounced as [п й у], keeping the consonant "п" hard.

*   **Я п'ю гарячий чай.** (I am drinking hot tea.)
*   **Ти п'єш каву.** (You are drinking coffee.)
*   **Він п'є молоко.** (He is drinking milk.)
*   **Ми п'ємо воду.** (We are drinking water.)
*   **Ви п'єте холодний сік.** (You are drinking cold juice.)
*   **Вони п'ють воду.** (They are drinking water.)

> **Ми часто їмо разом. Я їм рибу, а мій друг їсть м'ясо. Ми п'ємо воду.**
> *We often eat together. I eat fish, and my friend eats meat. We drink water.*

<!-- INJECT_ACTIVITY: fill-in-conjugation -->

## Знахідний відмінок — неживе (Accusative Inanimate)

Connecting actions to the objects being consumed requires a specific grammatical structure. In Ukrainian grammar, the direct object of a sentence — the thing that is being acted upon — takes the Accusative case, known as **Знахідний відмінок** (Accusative case).

In Ukrainian schools, children learn to identify this case by asking a specific pair of diagnostic questions: **Бачу що? кого?** (What/who do I see?). The verb "to see" naturally takes a direct object. Since food and drinks are inanimate objects, the relevant question is simply **що?** (what?). When stating **Я їм** (I eat) or **Я п'ю** (I drink), the immediate logical question is "what?". The noun that answers this question must be in the Accusative case.

For Masculine and Neuter inanimate nouns, the rule is remarkably simple: they do not change at all. Their Accusative form is exactly the same as their Nominative (dictionary) form.

These examples show the stability of masculine and neuter nouns:
*   **хліб** (bread, masculine) → **Я їм хліб.** (I eat bread.)
*   **сік** (juice, masculine) → **Я п'ю сік.** (I drink juice.)
*   **суп** (soup, masculine) → **Він їсть суп.** (He eats soup.)
*   **молоко** (milk, neuter) → **Ми п'ємо молоко.** (We drink milk.)
*   **яйце** (egg, neuter) → **Вони їдять яйце.** (They are eating an egg.)
*   **м'ясо** (meat, neuter) → **Вона їсть м'ясо.** (She is eating meat.)

You simply take the dictionary form of a masculine or neuter food item and place it right after your verb.

The critical rule at the A1 level concerns Feminine nouns. When a feminine noun serves as the direct object of a verb, its ending changes. The pattern is highly consistent: the ending **-а** changes to **-у**, and the ending **-я** changes to **-ю**.

This is the most important accusative change to master. Observe how this transforms common feminine food vocabulary:
*   **кава** (coffee) → **каву**: **Я п'ю каву.** (I drink coffee.)
*   **вода** (water) → **воду**: **Він п'є воду.** (He drinks water.)
*   **риба** (fish) → **рибу**: **Ми їмо рибу.** (We eat fish.)
*   **каша** (porridge) → **кашу**: **Ти їси кашу.** (You are eating porridge.)
*   **картопля** (potato) → **картоплю**: **Я їм картоплю.** (I am eating potatoes.)
*   **сметана** (sour cream) → **сметану**: **Вона любить сметану.** (She loves sour cream.)

:::tip
This ending shift applies to any verb that takes a direct object. Whether the sentence is **Я їм картоплю** (I eat potatoes), **Я п'ю воду** (I drink water), or **Я хочу каву** (I want coffee), the feminine ending must become **-у** or **-ю**.
:::

> **Сьогодні я готую обід. Я маю картоплю і рибу. Я їм картоплю, але я не п'ю каву. Я п'ю воду.**
> *Today I am cooking lunch. I have potatoes and fish. I am eating potatoes, but I do not drink coffee. I drink water.*

<!-- INJECT_ACTIVITY: fill-in-accusative-endings -->
<!-- INJECT_ACTIVITY: group-sort-accusative -->
<!-- INJECT_ACTIVITY: quiz-accusative-selection -->

## Підсумок — Summary

This module establishes the foundation for building practical, everyday sentences. Discussing daily meals and expressing basic needs requires an understanding of how actions affect objects, which involves applying the rules of the Accusative inanimate case.

The Accusative inanimate rules depend entirely on the gender of the noun. When an inanimate object, such as a piece of food or a beverage, is the direct target of an action — for instance, following verbs like **їсти** (to eat), **пити** (to drink), or **хотіти** (to want) — it must take the Accusative form.

*   **Masculine and Neuter nouns do not change form.** Words like **хліб** (bread), **сік** (juice), and **молоко** (milk) stay exactly the same as they appear in the dictionary. A speaker can simply say **Я їм хліб** or **Я п'ю молоко** without any modifications to the noun.
*   **Feminine nouns undergo a specific ending shift.** If a feminine noun ends in **-а**, that ending changes to **-у**. If it ends in **-я**, it changes to **-ю**. This is why **кава** becomes **каву**, and **картопля** becomes **картоплю**. This change is mandatory and highly frequent in spoken Ukrainian.

> **Кожного дня я снідаю. Я їм кашу і п'ю чай. На обід я їм суп. Це дуже смачно!**
> *Every day I have breakfast. I eat porridge and drink tea. For lunch I eat soup. It is very tasty!*

The following short self-check test ensures these vital patterns are internalized. Fill in the blanks using the correct Accusative form of the word in parentheses:

*   Test: Я їм ___ (**риба** → **рибу**).
*   Test: Я п'ю ___ (**вода** → **воду**).
*   Test: Вона їсть ___ (**хліб** → **хліб**).
*   Test: Ми хочемо ___ (**кава** → **каву**).
*   Test: Ти п'єш ___ (**сік** → **сік**).

As an active self-check, say three things you eat and three things you drink today out loud. Pay close attention to the gender of each word, and use the correct accusative form for each item. If the word is feminine, ensure the crucial shift to the "-у" ending is made.
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: i-eat-i-drink
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

**Level: A1.4+ (Module 37/55) — BEGINNER**

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
