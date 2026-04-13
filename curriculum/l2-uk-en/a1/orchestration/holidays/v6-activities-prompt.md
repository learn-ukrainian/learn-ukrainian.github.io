<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/holidays.yaml` file for module **46: Holidays** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-which-holiday -->`
- `<!-- INJECT_ACTIVITY: quiz-match-date -->`
- `<!-- INJECT_ACTIVITY: group-sort-traditions -->`
- `<!-- INJECT_ACTIVITY: fill-in-greetings -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Match holiday to date: Різдво → 25 грудня, День Незалежності → 24 серпня'
  items: 8
  type: quiz
- focus: 'Greetings: З ___! (Різдвом, Великоднем, Новим роком)'
  items: 8
  type: fill-in
- focus: Which holiday? Кутя, колядки, Свята вечеря → (Різдво / Великдень / Новий
    рік)
  items: 8
  type: quiz
- focus: 'Sort traditions by holiday: Різдво vs Великдень vs День Незалежності'
  items: 10
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- кутя (kutia, f)
- колядка (carol, f)
- писанка (decorated Easter egg, f)
- паска (Easter bread, f)
- парад (parade, m)
- прапор (flag, m)
- вишиванка (embroidered shirt, f)
- незалежність (independence, f)
- салют (fireworks, m)
required:
- свято (holiday, n)
- святкувати (to celebrate)
- Різдво (Christmas, n)
- Великдень (Easter, m)
- Новий рік (New Year)
- вітати (to congratulate/greet)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Ukrainian holidays are a central part of family life and national identity. Knowing how to talk about celebrations is a natural way to connect with people. You will often hear questions about dates and specific traditions. 

В Україні є багато свят. Ми часто збираємо родину разом. Люди готують смачну їжу. Ми також любимо співати пісні.
> *In Ukraine there are many holidays. We often gather the family together. People prepare tasty food. We also love to sing songs.*

The most important winter celebration is **Різдво** (Christmas). During the festive season, families gather to share special meals and sing traditional songs. Notice how the speakers discuss the recent date change for this holiday.

> **Джон:** Коли в тебе Різдво? *(When do you have Christmas?)*
> **Оксана:** Двадцять п'ятого грудня. А в тебе? *(On the twenty-fifth of December. And you?)*
> **Джон:** У нас — теж! *(We do too!)*
> **Оксана:** Раніше святкували сьомого січня, але тепер — двадцять п'ятого. *(Earlier we celebrated on January seventh, but now on the twenty-fifth.)*
> **Джон:** Що ви робите на Різдво? *(What do you do on Christmas?)*
> **Оксана:** Ми співаємо колядки і їмо кутю. *(We sing carols and eat kutia.)*
> **Джон:** Як гарно! З Різдвом! *(How beautiful! Merry Christmas!)*
> **Оксана:** З Різдвом Христовим! *(Merry Christmas!)*

Let's break down the vocabulary. **Різдво** is the noun for Christmas, and the verb **святкувати** means to celebrate. A **колядка** is a traditional carol that children and adults sing. The word **кутя** refers to a special ritual dish eaten only during the winter holidays. When saying goodbye or raising a toast, Ukrainians use the phrase **З Різдвом!** (Merry Christmas!).

* Я люблю святкувати Різдво. *(I love to celebrate Christmas.)*
* Вони святкують удома. *(They celebrate at home.)*
* Де ви святкуєте? *(Where do you celebrate?)*

The most important civic date is **День Незалежності** (Independence Day). This summer holiday brings people to the streets for public events, concerts, and patriotic displays.

> **Марко:** Двадцять четверте серпня — День Незалежності! *(The twenty-fourth of August is Independence Day!)*
> **Сара:** Так, це головне державне свято України. *(Yes, this is the main state holiday of Ukraine.)*
> **Марко:** Що ви робите? *(What do you do?)*
> **Сара:** Ми дивимося парад і ходимо на концерт. *(We watch the parade and go to a concert.)*
> **Марко:** А ввечері? *(And in the evening?)*
> **Сара:** Ввечері — салют і святковий вечір з друзями. *(In the evening — fireworks and a festive evening with friends.)*
> **Марко:** З Днем Незалежності! *(Happy Independence Day!)*
> **Сара:** Слава Україні! *(Glory to Ukraine!)*

This conversation introduces the core noun **свято** (holiday). The phrase **державне свято** means state holiday. During these events, a **парад** (parade) takes place, a **концерт** (concert) provides music, and a **салют** (fireworks) lights up the sky. The greeting **З Днем Незалежності!** is standard for August 24. It is frequently paired with the national salute **Слава Україні!** (Glory to Ukraine!).

* Це велике свято. *(This is a big holiday.)*
* Яке сьогодні свято? *(What holiday is today?)*
* Завтра державне свято. *(Tomorrow is a state holiday.)*

## Українські свята (Ukrainian Holidays)

A **свято** is a time for rest, family, and tradition. When you want to **вітати** (to greet) someone for a festive occasion but you do not know the exact phrase, you can always say **Зі святом!** (Happy Holiday!). It is a universal, polite phrase that works for almost any situation.

The winter cycle centers around **Різдво**. Historically, under Russian and Soviet influence, many Ukrainians celebrated on January 7. However, in 2023, Ukraine officially moved the date to December 25. This decision aligns the country with Europe and the majority of the Christian world, marking a major cultural shift away from the Russian Orthodox calendar.

> **Олена:** Що ми готуємо на Святвечір? *(What are we preparing for Christmas Eve?)*
> **Мама:** Ми готуємо дванадцять страв. *(We are preparing twelve dishes.)*
> **Олена:** А кутя є? *(And is there kutia?)*
> **Мама:** Звичайно, кутя — перша страва. *(Of course, kutia is the first dish.)*

The most important meal happens on the evening of December 24, known as **Свята вечеря** (Holy Supper). By tradition, families wait for the first star to appear in the sky before sitting down to eat.

На столі стоять дванадцять страв. Вони дуже смачні і традиційні. Головна страва — це кутя. Ми дуже любимо це свято.
> *There are twelve dishes on the table. They are very tasty and traditional. The main dish is kutia. We really love this holiday.*

There must be exactly twelve meatless dishes, representing the twelve apostles. **Кутя** is always the first thing people eat. It is a sweet wheat porridge mixed with honey, poppy seeds, and nuts. Afterward, groups of **колядники** (carolers) go from house to house. They sing a **колядка** to wish their neighbors health, peace, and prosperity.

In the spring, the biggest religious event is **Великдень** (Easter). The exact date changes every year depending on the lunar calendar, but the rich traditions remain exactly the same.

Великдень — це велике весняне свято. Ми йдемо в церкву святити кошик. Там є паска і красиві писанки. Люди кажуть: «Христос воскрес!». Ми відповідаємо: «Воістину воскрес!».
> *Easter is a big spring holiday. We go to church to bless the basket. There is Easter bread and beautiful decorated eggs there. People say: "Christ is risen!". We answer: "Indeed He is risen!".*

A common mistake for language learners is confusing the name of the holiday with the food. **Великдень** is the name of the holiday itself, while a **паска** (Easter bread) is the sweet, tall bread baked specifically for the occasion. You eat a **паска** on **Великдень**. In the morning, families go to church to **святити кошик** (bless the basket) full of food.

:::note
Another famous Easter tradition is making a **писанка** (decorated Easter egg). These are not just painted with a brush; they are carefully drawn using hot beeswax and natural dyes, featuring ancient geometric symbols.
:::

* Моя бабуся готує паску. *(My grandmother prepares Easter bread.)*
* Вони малюють писанки удома. *(They draw decorated eggs at home.)*
* Це красива українська традиція. *(This is a beautiful Ukrainian tradition.)*

<!-- INJECT_ACTIVITY: quiz-which-holiday -->

## Державні свята (National Holidays)

On August 24, 1991, Ukraine officially declared its **незалежність** (independence) from the Soviet Union. Today, **День Незалежності** is the most important **державне свято**. People gather in city centers to celebrate their freedom, culture, and national identity.

> **Тарас:** Ти йдеш на парад? *(Are you going to the parade?)*
> **Іван:** Так, я маю великий прапор. *(Yes, I have a big flag.)*
> **Тарас:** Тоді ми зустрічаємося там. *(Then we meet there.)*
> **Іван:** Добре! Слава Україні! *(Good! Glory to Ukraine!)*

У серпні ми святкуємо День Незалежності. На вулиці проходить великий парад. Ми бачимо сині і жовті прапори. Увечері люди дивляться яскравий салют. Усі гордо кажуть: «Слава Україні!».
> *In August we celebrate Independence Day. A big parade takes place on the street. We see blue and yellow flags. In the evening people watch bright fireworks. Everyone proudly says: "Glory to Ukraine!".*

A **прапор** is a flag, and the Ukrainian **прапор** features a blue band over a yellow band, representing the sky above wheat fields. During the celebrations, you will constantly hear people shouting **Слава Україні!**, to which the crowd enthusiastically replies **Героям слава!** (Glory to the heroes!).

Another massive celebration is **Новий рік** (New Year) on January 1. It is the biggest secular event of the year, bringing families and friends together for midnight toasts.

Першого січня — Новий рік. Удома стоїть висока зелена ялинка. Ми готуємо велику святкову вечерю. Діти дуже люблять нові подарунки.
> *On the first of January is New Year. A tall green New Year tree stands at home. We prepare a big festive dinner. Children really love new gifts.*

Notice the word **подарунок** (gift). It is a very important word for any celebration. The standard greeting as the clock strikes midnight is **З Новим роком!**.

* Я хочу новий телефон. *(I want a new phone.)*
* Це мій новий подарунок. *(This is my new gift.)*
* Ми не спимо вночі. *(We do not sleep at night.)*

There are several other important cultural dates to know. On the third Thursday of May, people observe **Вишиванковий день** (Vyshyvanka Day). Everyone wears a **вишиванка** (traditional embroidered shirt) to work, to school, or just walking in the park. It is a powerful symbol of Ukrainian identity and resistance.

:::tip
You will also hear about **День Конституції** (Constitution Day) on June 28, and **День захисників і захисниць** (Defenders' Day) on October 1. The October holiday honors all the men and women fighting for the country's freedom.
:::

<!-- INJECT_ACTIVITY: quiz-match-date -->
<!-- INJECT_ACTIVITY: group-sort-traditions -->

## Підсумок — Summary

Whenever you want to **вітати** (to greet or congratulate) someone for a specific holiday, Ukrainian uses a very consistent, logical grammar pattern. You simply combine the preposition **з** (with) and the name of the holiday in the instrumental case.

You already know the instrumental case from describing things that go together, like **кава з молоком** (coffee with milk) or **борщ з м'ясом** (borscht with meat). When greeting someone, you are literally saying that you congratulate them *with* the holiday.

* **З Різдвом!** — Merry Christmas!
* **З Великоднем!** — Happy Easter!
* **З Новим роком!** — Happy New Year!
* **З Днем Незалежності!** — Happy Independence Day!
* **З днем народження!** — Happy birthday!

Here is a short paragraph showing how to use these greetings in context:

Сьогодні дуже гарне світле свято. Я тепло вітаю маму з Різдвом. Ми п'ємо чорний чай з тортом. Це справді такий чудовий день.
> *Today is a very beautiful bright holiday. I warmly greet mom with Christmas. We drink black tea with cake. This is truly such a wonderful day.*

* Ми вітаємо друга. *(We greet a friend.)*
* Ми купуємо гарні подарунки. *(We buy beautiful gifts.)*

<!-- INJECT_ACTIVITY: fill-in-greetings -->

Let's review the calendar of major dates so you know exactly when to use these greetings throughout the year:

* **січень 1** (January 1) — Новий рік (New Year)
* **весна** (Spring) — Великдень (Easter)
* **травень** (May) — Вишиванковий день (Vyshyvanka Day)
* **червень 28** (June 28) — День Конституції (Constitution Day)
* **серпень 24** (August 24) — День Незалежності (Independence Day)
* **жовтень 1** (October 1) — День захисників і захисниць (Defenders' Day)
* **грудень 25** (December 25) — Різдво (Christmas)

:::caution
Remember that Ukrainian capitalizes the first word of holidays. For example, **День Незалежності** has both words capitalized because it is a major state holiday, but **Новий рік** only has the first word capitalized. Religious holidays like **Різдво** and **Великдень** are always capitalized.
:::

Self-check questions to test your memory before moving on:
* How do you say "Merry Christmas" and "Happy New Year"? (З Різдвом! З Новим роком!)
* How do you reply to "Слава Україні!"? (Героям слава!)
* What is the difference between "Великдень" and "паска"? (Великдень is the holiday itself, while паска is the traditional sweet bread).
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: holidays
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

**Level: A1.4+ (Module 46/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
