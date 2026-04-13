<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/shopping.yaml` file for module **39: Shopping** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-prices -->`
- `<!-- INJECT_ACTIVITY: quiz-currency -->`
- `<!-- INJECT_ACTIVITY: match-up-locations -->`
- `<!-- INJECT_ACTIVITY: fill-in-quantities -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Скільки коштує ___? — ___ гривень. (match items with prices)
  items:
  - Скільки коштує {хліб|хліба}? — Двадцять гривень.
  - Скільки коштує {вода|воду}? — Десять гривень.
  - Скільки коштує {сир|сиру}? — Сто гривень.
  - Скільки коштують {яблука|яблук}? — Сорок гривень.
  - Скільки коштують {помідори|помідорів}? — Тридцять гривень.
  - Скільки коштує {молоко|молока}? — П'ятдесят гривень.
  - Скільки коштує {сік|соку}? — Шістдесят гривень.
  - Скільки коштують {банани|бананів}? — Сімдесят гривень.
  type: fill-in
- focus: 'Choose correct: 23 (гривня / гривні / гривень)'
  items:
  - options:
    - гривня
    - гривні
    - гривень
    question: 21 ___
  - options:
    - гривні
    - гривня
    - гривень
    question: 32 ___
  - options:
    - гривень
    - гривня
    - гривні
    question: 45 ___
  - options:
    - гривень
    - гривня
    - гривні
    question: 100 ___
  - options:
    - гривня
    - гривні
    - гривень
    question: 1 ___
  - options:
    - гривні
    - гривня
    - гривень
    question: 3 ___
  - options:
    - гривень
    - гривня
    - гривні
    question: 10 ___
  - options:
    - гривні
    - гривня
    - гривень
    question: 54 ___
  type: quiz
- focus: 'At the market: Дайте ___ (кілограм/літр/пляшка) ___.'
  items:
  - Дайте {кілограм|літр|пляшку} яблук.
  - Дайте {літр|кілограм|пачку} молока.
  - Дайте {пляшку|кілограм|літр} води.
  - Дайте {пачку|літр|пляшку} чаю.
  - Дайте {буханку|літр|кілограм} хліба.
  - Дайте {кілограм|літр|пляшку} помідорів.
  type: fill-in
- focus: Where do you buy it? Match item to shop type.
  items:
  - помідори: ринок
  - м'ясо: м'ясний відділ
  - сир: молочний відділ
  - хліб: крамниця
  - молоко: супермаркет
  - вода: магазин
  - кава: кафе
  - борщ: ресторан
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- копійка (kopeck, f)
- кілограм (kilogram, m)
- літр (liter, m)
- пляшка (bottle, f)
- пачка (pack, f)
- знижка (discount, f)
- супермаркет (supermarket, m)
- гроші (money, pl.)
- готівка (cash, f)
required:
- коштувати (to cost)
- скільки (how much/many)
- гривня (hryvnia, f)
- ціна (price, f)
- магазин (shop, m)
- ринок (market, m)
- купувати (to buy)
- дорого (expensive — adverb)
- дешево (cheap — adverb)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Shopping in Ukraine blends modern convenience with traditional culture. A large **супермаркет** (supermarket) offers everything under one roof, with clear price tags and self-checkout counters. However, if you want the freshest vegetables, seasonal fruit, or a chance to speak directly with the people who grow your food, you must visit a **ринок** (market). At the market, there are rarely printed price tags on every item; you must ask the seller directly. This makes the local market the perfect place to practice your Ukrainian communication skills. Let's see how a typical interaction unfolds when buying fresh produce.

> **(На ринку / At the market)**
> **Покупець:** Добрий день! Скільки коштує кілограм яблук? *(Good day! How much does a kilogram of apples cost?)*
> **Продавець:** Сорок гривень. *(Forty hryvnias.)*
> **Покупець:** А помідори? *(And the tomatoes?)*
> **Продавець:** Тридцять п'ять гривень за кілограм. *(Thirty-five hryvnias per kilogram.)*
> **Покупець:** Дайте, будь ласка, два кілограми помідорів і кілограм яблук. *(Give me, please, two kilograms of tomatoes and a kilogram of apples.)*
> **Продавець:** Сімдесят п'ять гривень. *(Seventy-five hryvnias.)*
> **Покупець:** Ось, будь ласка. *(Here you go.)*

Let's look at the key phrases used in this conversation. To ask for an item politely, the shopper uses the phrase **Дайте, будь ласка...** (Give me, please...). This is the standard, most natural way to request something from a seller in Ukraine. Notice how the shopper states both the quantity and the item clearly together: **кілограм яблук** (a kilogram of apples) and **два кілограми помідорів** (two kilograms of tomatoes). The prices are spoken directly as numbers followed by the currency. There is no need for complex sentences; short, clear, and direct phrases are exactly how native speakers handle transactions.

> **(У супермаркеті / At the supermarket)**
> **Мама:** Вибачте, де тут хліб? *(Excuse me, where is the bread here?)*
> **Працівник:** Хліб у третьому ряду. *(The bread is in the third aisle.)*
> **Мама:** А молоко? *(And the milk?)*
> **Працівник:** Молоко в холодильнику, там. *(The milk is in the fridge, there.)*
> **Дочка:** Мамо, скільки коштує цей сир? *(Mom, how much does this cheese cost?)*
> **Мама:** Сто двадцять гривень. *(One hundred twenty hryvnias.)*
> **Дочка:** Дорого! А є дешевший? *(Expensive! Is there a cheaper one?)*
> **Мама:** Так, ось цей — вісімдесят. *(Yes, this one — eighty.)*

In a large store, navigating is your first priority. You ask for directions using **де тут...** (where is... here). You can also naturally react to prices using adjectives: if a product costs too much money, you can exclaim **Дорого!** (Expensive!), or you can ask a worker for something **дешевший** (cheaper).

## Скільки коштує? (How Much?)

The most important question in your shopping toolkit is **Скільки коштує...?** (How much does it cost?). You must pay close attention to the item you are asking about, as the verb must agree with the noun. If you are buying a single or uncountable item, use the singular verb form **коштує**. If you are pointing to a plural item, the verb must take the plural form **коштують**.

*   **Скільки коштує хліб?** *(How much does the bread cost?)*
*   **Скільки коштує молоко?** *(How much does the milk cost?)*
*   **Скільки коштують яблука?** *(How much do the apples cost?)*
*   **Скільки коштують помідори?** *(How much do the tomatoes cost?)*

The official currency of Ukraine is the **гривня** (hryvnia). When stating a **ціна** (price), the ending of the word changes depending on the specific number before it. This is a fundamental rule of noun-number agreement in Ukrainian.

*   Ends in 1 (except 11): singular **гривня**.
    *   **Одна гривня.** *(One hryvnia.)*
    *   **Двадцять одна гривня.** *(Twenty-one hryvnias.)*
*   Ends in 2, 3, or 4 (except 12-14): plural **гривні**.
    *   **Дві гривні.** *(Two hryvnias.)*
    *   **Тридцять чотири гривні.** *(Thirty-four hryvnias.)*
*   Ends in 5-9, 0, or any of the teens (11-19): plural **гривень**.
    *   **П'ять гривень.** *(Five hryvnias.)*
    *   **Сорок гривень.** *(Forty hryvnias.)*

The smaller unit of currency is the **копійка** (kopeck), representing one hundredth of a hryvnia. The grammar rules for its endings are identical: **одна копійка**, **дві копійки**, **п'ять копійок**. However, physical kopecks are less common today. Prices are frequently rounded to the nearest ten kopecks or whole hryvnia, so you will hear **гривня** much more often than **копійка**.

Let's apply numbers directly to prices. Notice how the last digit entirely determines the currency's form.

*   **Скільки коштує кава? Двадцять одна гривня.** *(How much is the coffee? Twenty-one hryvnias.)*
*   **Скільки коштує чай? Тридцять дві гривні.** *(How much is the tea? Thirty-two hryvnias.)*
*   **Скільки коштує торт? Сорок п'ять гривень.** *(How much is the cake? Forty-five hryvnias.)*
*   **Скільки коштує сир? Сто гривень.** *(How much is the cheese? One hundred hryvnias.)*

<!-- INJECT_ACTIVITY: fill-in-prices -->

Before handing over your **гроші** (money), you might react to the final total. If you feel it is too high, exclaim **Дорого!** (Expensive!). If it is a fantastic deal, happily say **Дешево!** (Cheap!) or **Нормальна ціна.** (Fair price.). To ask for the final sum, use **Скільки за все?** (How much for everything?). You might also politely ask **Є знижка?** (Is there a discount?).

Here is a short example of calculating a total in an everyday scenario:

> **Це яблуко коштує десять гривень. Вода коштує двадцять гривень. За все я плачу тридцять гривень.**
> *(This apple costs ten hryvnias. The water costs twenty hryvnias. For everything I pay thirty hryvnias.)*

<!-- INJECT_ACTIVITY: quiz-currency -->

## Де купити? (Where to Buy)

Where exactly do you go to **купувати** (to buy) what you need? A standard shop is called a **магазин** (shop), while a very large one is a **супермаркет** (supermarket). A smaller, local shop is often called a **крамниця** (store — an authentic Ukrainian synonym for магазин). For fresh produce or homemade goods, you visit the **ринок** (market). Finally, for medicine or vitamins, you go to an **аптека** (pharmacy).

Inside a large store or covered market, products are grouped into sections. If you want sausage, chicken, or pork, find the **м'ясний відділ** (meat section). For milk, butter, or cottage cheese, look for the **молочний відділ** (dairy section).

*   **Вибачте, де молочний відділ?** *(Excuse me, where is the dairy section?)*
*   **М'ясний відділ там, у другому ряду.** *(The meat section is there, in the second aisle.)*

<!-- INJECT_ACTIVITY: match-up-locations -->

When asking for a product, you rarely ask for just "water" or "apples"; you specify an exact quantity. In Ukrainian grammar, the item following a quantity word changes its ending. It takes a form called the genitive case, which indicates "of something" (like a liter *of* milk). At this introductory level, simply learn these combinations as fixed chunks.

For solid goods and produce, the standard measurement is a **кілограм** (kilogram).

*   **Дайте, будь ласка, кілограм яблук.** *(Give me, please, a kilogram of apples.)*
*   **Я хочу купити два кілограми помідорів.** *(I want to buy two kilograms of tomatoes.)*

For liquids, you use a **літр** (liter).

*   **Дайте, будь ласка, літр молока.** *(Give me, please, a liter of milk.)*
*   **Скільки коштують два літри соку?** *(How much do two liters of juice cost?)*

Here is how you might describe a quick trip to the grocery store:

> **Я йду в супермаркет. Я купую літр молока і два кілограми яблук. Вони дуже свіжі.**
> *(I am going to the supermarket. I am buying a liter of milk and two kilograms of apples. They are very fresh.)*

Packaged goods have specific quantity words. A standard package is a **пачка** (pack). A liquid container is a **пляшка** (bottle). For bread, you ask for a **буханець** (loaf).

*   **Скільки коштує пачка масла?** *(How much does a pack of butter cost?)*
*   **Дайте, будь ласка, пачку чаю.** *(Give me, please, a pack of tea.)*
*   **Де тут пляшка води?** *(Where is a bottle of water here?)*
*   **Я хочу купити буханець хліба.** *(I want to buy a loaf of bread.)*

:::tip
You might sometimes hear the word «буханка» used for a loaf of bread, but this is an incorrect Russian calque. The natural, authentic Ukrainian word is **буханець** or **хлібина**.
:::

<!-- INJECT_ACTIVITY: fill-in-quantities -->

## Підсумок — Summary

Let's recap your essential shopping toolkit. You now know how to navigate a store, ask for items, and handle prices. When you enter a **магазин** or approach a seller at a **ринок**, locate what you need with **Де тут...?** (Where is... here?). Then, ask the price using **Скільки коштує?** for one item or **Скільки коштують?** for many. You politely request your goods by stating **Дайте, будь ласка...** followed by a quantity like a **літр** or a **кілограм**. React to the price by saying **Дорого!** or **Дешево!**, and confirm your purchase with **Добре, беру.** (Good, I'll take it.). Finally, wrap up the transaction by asking **Скільки за все?** (How much for everything?) and checking **Можна карткою?** (Can I pay by card?) if you don't have enough **готівка** (cash).

Here is a short summary of a successful shopping trip:

> **Я на ринку. Я запитую продавця: «Скільки коштують помідори?». Це дуже хороша ціна. Я беру два кілограми.**
> *(I am at the market. I ask the seller: "How much do the tomatoes cost?". This is a very good price. I take two kilograms.)*

Here is a quick question-and-answer review of the most important patterns from this module. Use these as a self-check before your next trip to the market.

*   **Як запитати ціну на помідори?** *(How to ask the price of tomatoes?)*
    *   **Скільки коштують помідори?** *(How much do the tomatoes cost?)*
*   **Як попросити два кілограми яблук?** *(How to ask for two kilos of apples?)*
    *   **Дайте, будь ласка, два кілограми яблук.** *(Give me, please, two kilograms of apples.)*
*   **Як сказати, що ціна зависока?** *(How to say the price is too high?)*
    *   **Це дорого!** *(This is expensive!)*
*   **Як дізнатися загальну суму до сплати?** *(How to ask for the total sum to pay?)*
    *   **Скільки за все?** *(How much for everything?)*
*   **Як запитати про форму оплати?** *(How to ask about the payment method?)*
    *   **Можна карткою чи потрібна готівка?** *(Can I pay by card or is cash needed?)*
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: shopping
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

**Level: A1.4+ (Module 39/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-numbers [§4.2.1.3]
**Числівники** (Numerals)
- **quiz** — Яке число?: Розпізнати числівники, записані словами / Recognize written number words
- **fill-in** — Напиши цифру словом: Записати числівник словом по-українськи / Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Зіставити цифри з їхніми українськими назвами / Match digits to their Ukrainian word forms
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Числівники складні для написання — давати варіанти на A1

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
