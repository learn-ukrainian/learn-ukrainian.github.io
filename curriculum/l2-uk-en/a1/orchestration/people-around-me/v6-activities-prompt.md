<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/people-around-me.yaml` file for module **40: People Around Me** (a1).

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

- `<!-- INJECT_ACTIVITY: group-sort-animate-inanimate -->`
- `<!-- INJECT_ACTIVITY: fill-in-accusative-forms -->`
- `<!-- INJECT_ACTIVITY: quiz-choose-correct-accusative -->`
- `<!-- INJECT_ACTIVITY: fill-in-dialogue-completion -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Я бачу ___ (nominative → accusative: мама → маму, брат → брата)'
  items:
  - Я бачу {маму|мама|мами}.
  - Я бачу {брата|брат|брату}.
  - Я знаю {Олену|Олена|Олени}.
  - Я знаю {друга|друг|другу}.
  - Я люблю {тата|тато|таті}.
  - Я чекаю {вчителя|вчитель|вчителю}.
  - Я шукаю {подругу|подруга|подруги}.
  - Я бачу {сусіда|сусід|сусіду}.
  - Я чекаю {лікаря|лікар|лікарю}.
  - Я знаю {сестру|сестра|сестри}.
  type: fill-in
- focus: 'Sort: animate (кого?) vs inanimate (що?) — changes vs stays same for masculine'
  groups:
  - items:
    - брата
    - маму
    - друга
    - лікаря
    - Олену
    name: Animate (кого?)
  - items:
    - хліб
    - каву
    - воду
    - чай
    - борщ
    name: Inanimate (що?)
  type: group-sort
- focus: 'Choose correct: Я знаю (Олена / Олену / Олени)'
  items:
  - options:
    - Олену
    - Олена
    - Олени
    question: Я знаю ___.
  - options:
    - брата
    - брат
    - братом
    question: Я бачу ___.
  - options:
    - подругу
    - подруга
    - подруги
    question: Я люблю ___.
  - options:
    - сусіда
    - сусід
    - сусідом
    question: Я чекаю ___.
  - options:
    - вчителя
    - вчитель
    - вчителю
    question: Я шукаю ___.
  - options:
    - лікаря
    - лікар
    - лікарем
    question: Я знаю ___.
  - options:
    - колегу
    - колега
    - колеги
    question: Я бачу ___.
  - options:
    - тата
    - тато
    - татом
    question: Я люблю ___.
  type: quiz
- focus: 'Complete: Я люблю ___, знаю ___, чекаю ___. (family/friends)'
  items:
  - — Кого ти {бачиш|бачити|бачить}?
  - — Я бачу {брата|брат|братом} і маму.
  - — Ти знаєш мого {друга|друг|другу} Тараса?
  - — Ні, я не {знаю|знає|знати} твого друга.
  - — А кого ти {чекаєш|чекати|чекає}?
  - — Я чекаю {лікаря|лікар|лікарем}.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- сусід (neighbor, m)
- колега (colleague, m/f)
- викладач (lecturer, m)
- вчитель (teacher, m)
- лікар (doctor, m)
- продавець (seller, m)
- покупець (buyer, m)
required:
- бачити (to see)
- знати (to know)
- любити (to love)
- чекати (to wait for)
- шукати (to look for)
- друг (friend, m)
- подруга (friend, f)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

We interact with people every day in our lives. When we talk about the people around us—identifying family members, mentioning a **друг** (friend, m) or **подруга** (friend, f), or interacting with professionals—we often use them as the direct object of our sentences. In Ukrainian, this means applying the accusative case for people. This module explores how to correctly refer to people when you see, know, or look for them.

«Це моя сім'я. Я дуже люблю маму і тата. У мене є брат. Ви знаєте мого брата? Він лікар. Я часто бачу брата вдома.»
> *This is my family. I love mom and dad very much. I have a brother. Do you know my brother? He is a doctor. I often see my brother at home.*

Let us look at a natural conversation. Two friends are looking at wedding photos and identifying people in them.

> **Наречена:** Дивись, це мої фотографії. *(Look, these are my photos.)*
> **Друг:** Дуже гарні! **Кого ти бачиш?** *(Very beautiful! Whom do you see?)*
> **Наречена:** **Я бачу маму і тата.** *(I see mom and dad.)*
> **Друг:** **А хто це?** *(And who is this?)*
> **Наречена:** **Це мій брат. Ти знаєш мого брата?** *(This is my brother. Do you know my brother?)*
> **Друг:** **Ні, я не знаю твого брата.** *(No, I do not know your brother.)*
> **Наречена:** **Ходімо, я тебе познайомлю!** *(Let's go, I will introduce you!)*

Notice how the nouns for family members change their endings in this dialogue. In the dictionary, these nouns are **мама**, **тато**, and **брат**. However, when they become the object of the verb **бачити** (to see) or **знати** (to know), their endings must change. The noun **мама** becomes **маму**, **тато** becomes **тата**, and **брат** becomes **брата**. We call this the animate accusative form, and it is specifically used for living beings like people and animals. This is a fundamental pattern you will use when talking about your family and friends in Ukrainian.

:::note
In Ukrainian, it is very common to refer to professionals by their titles rather than their names. Discussing a **лікар** (doctor) or **вчитель** (teacher) in the accusative case is a standard way to talk about the people who help you in your daily life.
:::

Now consider a different setting. Two colleagues at work are discussing people they know or are waiting for.

> **Олена:** Привіт! **Ти знаєш нашу вчительку?** *(Hi! Do you know our teacher?)*
> **Максим:** **Так, я знаю Олену Петрівну.** *(Yes, I know Olena Petrivna.)*
> **Олена:** **А нового лікаря?** *(And the new doctor?)*
> **Максим:** **Ні, я ще не знаю лікаря.** *(No, I do not know the doctor yet.)*
> **Олена:** **Він дуже добрий. Я чекаю його зараз.** *(He is very kind. I am waiting for him now.)*

In this workplace setting, we observe the same grammatical pattern applied to professions and names. The noun for a female teacher is **вчителька** (teacher, f), but here it changes to **вчительку**. The name **Олена** becomes **Олену**. The noun for a male doctor is **лікар** (doctor, m), but it transforms into **лікаря**. When the first colleague says she is waiting for him, she uses the verb **чекати** (to wait for). Just like seeing or knowing someone, waiting for a person requires this specific object form. You will use these animate accusative forms constantly when interacting with people around you, whether speaking to a **колега** (colleague, m/f), a **викладач** (lecturer, m), or a **продавець** (seller, m) in a shop.

## Кого? (Whom?)

In the Ukrainian language, the accusative case draws a very strict boundary between inanimate objects and animate objects. Inanimate objects are lifeless things, such as food, furniture, or places. Animate objects are living beings, such as people and animals. This distinction is absolutely critical for masculine nouns. When a masculine inanimate noun is the direct object of a sentence, its ending does not change at all. For example, if you say «Я їм хліб» (I am eating bread), the masculine noun stays exactly the same as in the dictionary. However, when a masculine animate noun is the object, its ending must change. If you say «Я бачу брата» (I see a brother), the noun changes.

«Я йду в магазин. Я купую хліб і воду. Там я бачу сусіда. Я добре знаю сусіда. Ми часто говоримо.»
> *I am going to the store. I am buying bread and water. There I see a neighbor. I know the neighbor well. We often talk.*

To understand when to change the ending of a masculine noun, you must look at the question words that drive the sentence. In Ukrainian, the accusative case uses two different question words. For inanimate objects, the question word is **що?** (what?). When you ask **що?**, the inanimate masculine noun remains unchanged. For animate objects, the question word is **кого?** (whom?). This question word is the key trigger. When a verb answers the question **кого?**, it activates the animate rule. This explicitly dictates that masculine nouns will change their endings. This is why inanimate masculine nouns remain identical to their dictionary forms, while animate masculine nouns require a new grammatical suffix to show they are receiving the action.

:::tip
A helpful mnemonic for remembering the animate question word: **Кого?** (whom?) is used for a **колега** (colleague) or a **кіт** (cat), both of which are animate. The word **Що?** (what?) is used for inanimate things.
:::

In Ukrainian schools, children learn this grammar by memorizing the double question «Бачу кого? що?» (I see whom? what?). These two questions establish two separate patterns. The question **кого?** triggers the animate rule, which introduces a fascinating shortcut in Ukrainian grammar: for masculine animate nouns, the accusative form simply borrows the genitive case ending. You take the genitive form you already know and use it as the direct object.

*   **друг** → **друга**: «Я знаю друга.» (I know a friend.)
*   **тато** → **тата**: «Я люблю тата.» (I love dad.)
*   **лікар** → **лікаря**: «Я чекаю лікаря.» (I am waiting for the doctor.)
*   **сусід** (neighbor, m) → **сусіда**: «Я бачу сусіда.» (I see the neighbor.)

This borrowed ending is exactly why the animate versus inanimate distinction matters so much. It forces masculine nouns representing people to change their shape, ensuring that the listener clearly understands who is receiving the action.

<!-- INJECT_ACTIVITY: group-sort-animate-inanimate -->

## Знахідний відмінок — живе (Accusative Animate)

Let us first examine the rules for feminine animate nouns. There is excellent news for learners: feminine nouns follow the exact same accusative pattern regardless of whether they are animate or inanimate. Just like the inanimate word **кава** (coffee) becomes **каву**, the endings for feminine people change from **-а** to **-у** and from **-я** to **-ю**. There are no surprises or special rules here.

*   **мама** → **маму**: «Я бачу маму.» (I see mom.)
*   **сестра** (sister) → **сестру**: «Я знаю сестру.» (I know the sister.)
*   **Олена** → **Олену**: «Я чекаю Олену.» (I am waiting for Olena.)
*   **подруга** → **подругу**: «Я люблю подругу.» (I love the friend.)

«Я чекаю друга на вулиці. Мій друг — вчитель. Я бачу друга здалеку. Він теж чекає колегу. Ми бачимо колегу разом.»
> *I am waiting for a friend on the street. My friend is a teacher. I see the friend from afar. He is also waiting for a colleague. We see the colleague together.*

Now we must address the critical new rule for masculine animate nouns. As established earlier, the accusative form for masculine living beings is absolutely identical to the genitive form. Instead of remaining unchanged like inanimate objects, these masculine nouns take the **-а** or **-я** ending. Here are clear, everyday examples of this pattern in action:

*   **брат** → **брата**: «Я бачу брата.» (I see a brother.)
*   **друг** → **друга**: «Я шукаю друга.» (I am looking for a friend.)
*   **тато** → **тата**: «Я люблю тата.» (I love dad.)
*   **лікар** → **лікаря**: «Я чекаю лікаря.» (I am waiting for the doctor.)
*   **вчитель** (teacher, m) → **вчителя**: «Я знаю вчителя.» (I know the teacher.)
*   **сусід** → **сусіда**: «Я бачу сусіда.» (I see the neighbor.)

:::caution
English speakers often forget to change the endings of masculine names and professions because English does not do this. Always pause and ask yourself: "Is this a living person?" If the answer is yes, you must use the animate accusative form (the **-а** or **-я** ending) when they are the object of the sentence.
:::

To solidify this concept, let us summarize the masculine paradigm by contrasting the animate and inanimate forms side-by-side. Seeing them together makes the grammatical difference perfectly clear.

*   Inanimate (stays the same): «Я бачу стіл.» (I see a table.)
*   Animate (gets the **-а** ending): «Я бачу брата.» (I see a brother.)
*   Inanimate (stays the same): «Я бачу хліб.» (I see bread.)
*   Animate (gets the **-а** ending): «Я бачу сусіда.» (I see a neighbor.)

This structural difference is absolutely essential for natural Ukrainian speech. Whenever you interact with people or talk about the individuals in your daily life, you must apply this animate accusative pattern to ensure your sentences are correct.

<!-- INJECT_ACTIVITY: fill-in-accusative-forms -->
<!-- INJECT_ACTIVITY: quiz-choose-correct-accusative -->

## Підсумок — Summary

We can now construct a comprehensive summary of the accusative case for both animate and inanimate nouns. This chart presents the full picture of how word endings change depending on what you are talking about.

| Рід (Gender) | Inanimate (**що?**) | Animate (**кого?**) |
| :--- | :--- | :--- |
| Чоловічий (Masculine) | = nominative (**хліб**) | = genitive (**брата**) |
| Жіночий (Feminine) | **-а** → **-у** (**каву**) | **-а** → **-у** (**маму**) |
| Середній (Neuter) | = nominative (**молоко**) | (rare at A1) |

As the chart illustrates, the masculine inanimate noun answers the question **що?** and equals the nominative form. The masculine animate noun answers the question **кого?** and equals the genitive form. The feminine noun always changes its ending from **-а** to **-у**, regardless of animacy. Neuter animate nouns exist but are quite rare at the A1 level.

«Це моя велика родина. Я дуже люблю дідуся і бабусю. Я часто бачу сестру. Сьогодні я чекаю брата і тата. Ми дуже любимо гостей.»
> *This is my large family. I love grandfather and grandmother very much. I often see my sister. Today I am waiting for my brother and dad. We love guests very much.*

There are several high-frequency verbs at the A1 level that frequently trigger this animate accusative case. When you use these verbs with people, you must apply the animate endings.

*   **бачити** (to see): «Я бачу викладача.» (I see the lecturer.)
*   **знати** (to know): «Я знаю студента.» (I know the student.)
*   **любити** (to love): «Я люблю тата.» (I love dad.)
*   **чекати** (to wait for): «Я чекаю лікаря.» (I am waiting for the doctor.)
*   **шукати** (to look for): «Я шукаю подругу.» (I am looking for a friend.)

Mastering these verbs will allow you to describe your interactions with the people around you accurately. Before moving to the exercises, perform a quick self-check to ensure you understand the core concepts.

*   **Q: How do you say "I see mom"?**
*   A: «Я бачу маму» (**мама** → **маму**).
*   **Q: How do you say "I see brother"?**
*   A: «Я бачу брата» (**брат** → **брата**).
*   **Q: What is the question word for people in the accusative?**
*   A: **Кого?**

These simple checks confirm that you are ready to apply the animate accusative rules in practice.

<!-- INJECT_ACTIVITY: fill-in-dialogue-completion -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: people-around-me
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

**Level: A1.4+ (Module 40/55) — BEGINNER**

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
