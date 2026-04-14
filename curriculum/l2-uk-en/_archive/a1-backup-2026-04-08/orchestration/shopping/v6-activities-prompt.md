<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/shopping.yaml` file for module **39: Shopping** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-currency-forms -->`
- `<!-- INJECT_ACTIVITY: fill-in-prices -->`
- `<!-- INJECT_ACTIVITY: fill-in-quantities -->`
- `<!-- INJECT_ACTIVITY: match-shop-types -->`

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

Taras is at a busy outdoor **ринок** (market) in Kyiv. He needs **яблука** (apples) and **помідори** (tomatoes). Listen to how he asks the price, hears the total, and places his order.

> **Тарас:** Добрий день! *(Good day!)*
> **Продавець:** Добрий день! *(Good day!)*
> **Тарас:** Скільки коштує кілограм яблук? *(How much does a kilogram of apples cost?)*
> **Продавець:** Сорок гривень. *(Forty hryvnias.)*
> **Тарас:** А помідори? *(And tomatoes?)*
> **Продавець:** Тридцять п'ять гривень за кілограм. *(Thirty-five hryvnias per kilogram.)*
> **Тарас:** Дайте, будь ласка, два кілограми помідорів і кілограм яблук. *(Please give me two kilograms of tomatoes and a kilogram of apples.)*
> **Продавець:** Сімдесят п'ять гривень, будь ласка. *(Seventy-five hryvnias, please.)*
> **Тарас:** Ось, будь ласка. *(Here you go.)*
> **Продавець:** Дякую! До побачення! *(Thank you! Goodbye!)*

Two key phrases to notice here. First, **за кілограм** means "per kilogram" — the vendor states the unit price. Second, **Дайте, будь ласка** followed by a quantity and an item is the standard buying request at any Ukrainian market or shop.

Now a different setting. **Мама** (Mom) and **Дочка** (Daughter) are in a **супермаркет** (supermarket). They need to find bread, compare cheese prices, and pay.

> **Дочка:** Мамо, де тут хліб? *(Mom, where is the bread here?)*
> **Мама:** Хліб у третьому ряді. *(Bread is in the third aisle.)*
> **Дочка:** А молоко? *(And milk?)*
> **Мама:** Молоко в холодильнику, там. *(Milk is in the fridge, over there.)*
> **Дочка:** Скільки коштує цей сир? *(How much does this cheese cost?)*
> **Мама:** Сто двадцять гривень. *(One hundred twenty hryvnias.)*
> **Дочка:** Дорого! А є дешевший? *(Expensive! Is there a cheaper one?)*
> **Мама:** Так, ось цей — вісімдесят. *(Yes, this one — eighty.)*
> **Дочка:** Добре, беру. *(OK, I'll take it.)*
> **Мама:** Скільки за все? *(How much is everything?)*
> **Касир:** Сто сорок сім гривень. *(One hundred forty-seven hryvnias.)*
> **Мама:** Можна карткою? *(Can I pay by card?)*
> **Касир:** Так, звичайно. Дякуємо за покупку! *(Yes, of course. Thanks for the purchase!)*

:::tip
Four phrases from this dialogue to memorize now: **Дорого!** (Expensive!), **Добре, беру.** (OK, I'll take it.), **Скільки за все?** (How much total?), **Можна карткою?** (Can I pay by card?)
:::

## Скільки коштує? (How Much?)

The question **Скільки коштує?** (How much does it cost?) uses the verb **коштувати** (to cost) in third person singular. When the item is plural, the verb changes: **Скільки коштують?** (How much do they cost?). The verb agrees with the item — singular item, singular verb; plural item, plural verb. Compare:

- **Скільки коштує хліб?** — How much does the bread cost?
- **Скільки коштує молоко?** — How much does the milk cost?
- **Скільки коштують яблука?** — How much do the apples cost?
- **Скільки коштують помідори?** — How much do the tomatoes cost?

The word **гривня** (hryvnia — Ukraine's currency) changes form depending on the number before it. Learn this as a pattern rather than a grammar rule. After **1**, use **гривня**. After **2, 3, 4** (and compounds ending in them), use **гривні**. After **5 and above**, use **гривень**. Here are real prices to practice:

- **1 гривня** — one hryvnia
- **2 гривні** — two hryvnias
- **4 гривні** — four hryvnias
- **5 гривень** — five hryvnias
- **20 гривень** — twenty hryvnias
- **21 гривня** — twenty-one hryvnias (ends in 1 → гривня)
- **32 гривні** — thirty-two hryvnias (ends in 2 → гривні)
- **100 гривень** — one hundred hryvnias

The smaller unit, **копійка** (kopeck), follows a similar pattern: 1 **копійка**, 2 **копійки**, 5 **копійок**. In everyday speech, prices are usually rounded to whole **гривні**, so you will hear **копійки** mostly on receipts.

<!-- INJECT_ACTIVITY: quiz-currency-forms -->

Now practice reading prices aloud. Here are the five items from the supermarket dialogue:

- **Хліб — двадцять п'ять гривень.** Bread — 25 hryvnias.
- **Молоко — сорок дві гривні.** Milk — 42 hryvnias.
- **Сир — вісімдесят дев'ять гривень.** Cheese — 89 hryvnias.
- **Ковбаса — сто двадцять гривень.** Sausage — 120 hryvnias.
- **Масло — шістдесят п'ять гривень.** Butter — 65 hryvnias.

Notice **сорок дві гривні** — the number **дві** is feminine here because **гривня** is a feminine noun. With masculine nouns you would say **два**, but with **гривня** it is always **дві**.

After you hear a price, you react. Here are six useful expressions:

- **Дорого!** — Expensive! (when ковбаса is 120 гривень)
- **Дешево!** — Cheap! (a pleasant surprise)
- **Нормальна ціна.** — Fair price.
- **Є знижка?** — Is there a discount?
- **За все — сто п'ятдесят гривень.** — The total is 150 hryvnias.
- **Добре, беру.** — OK, I'll take it.

<!-- INJECT_ACTIVITY: fill-in-prices -->

## Де купити? (Where to Buy)

Ukraine has several types of shopping locations, each with its own character. Here are the five most common:

- **Магазин** (shop) — a general store. **Я йду в магазин.** (I'm going to the shop.)
- **Супермаркет** (supermarket) — a large self-service store. **У супермаркеті є все.** (The supermarket has everything.)
- **Ринок** (market) — an open-air market where prices are often lower. **На ринку часто дешевше.** (At the market it's often cheaper.)
- **Крамниця** (store) — a distinctly Ukrainian word, synonym for **магазин**. Common in western Ukraine and literary language. **У нашій крамниці гарний вибір.** (Our store has a good selection.)
- **Аптека** (pharmacy) — for medicines and cosmetics, not food. **Ліки купують в аптеці.** (Medicine is bought at the pharmacy.)

Inside a **супермаркет**, products are organized into sections called **відділ** (section/department):

- **Де тут молочний відділ?** — Where is the dairy section? — **Там, праворуч.** (Over there, to the right.)
- **Де тут хлібний відділ?** — Where is the bread section? — **Перший ряд, ліворуч.** (First aisle, to the left.)
- **М'ясний відділ** — the meat section.
- **Овочевий відділ** — the vegetable/produce section.

This connects back to Dialogue 2: **Де тут хліб? — Хліб у третьому ряді.**

When you buy food, you need quantity words. Learn these as ready-made chunks — the item form after each quantity is fixed, and you will study why in A2. For now, just copy the pattern:

- **Кілограм** (kilogram): **кілограм яблук**, **два кілограми помідорів** — **Дайте, будь ласка, кілограм яблук.** (Please give me a kilogram of apples.)
- **Літр** (liter): **літр молока**, **два літри соку** — **Дайте, будь ласка, літр молока.** (Please give me a liter of milk.)
- **Пачка** (pack): **пачка масла**, **пачка чаю** — **Дайте, будь ласка, дві пачки кави.** (Please give me two packs of coffee.)
- **Пляшка** (bottle): **пляшка води**, **пляшка соку** — **Дайте, будь ласка, пляшку води.** (Please give me a bottle of water.)
- **Буханка** (loaf — used only for bread): **буханка хліба** — **Дайте, будь ласка, буханку хліба.** (Please give me a loaf of bread.)

You will see these genitive endings again in A2. For now, learn the chunks — they are the same ones native speakers use automatically.

The buying formula is always the same: **Дайте, будь ласка,** + quantity + item. Three more examples:

- **Дайте, будь ласка, два кілограми помідорів.** (Please give me two kilograms of tomatoes.)
- **Дайте, будь ласка, літр молока.** (Please give me a liter of milk.)
- **Дайте, будь ласка, буханку хліба.** (Please give me a loaf of bread.)

The quantity word changes form with the number (**кілограм** → **два кілограми**), and the item stays in the same form after the quantity. For now, just copy these chunks as whole units.

<!-- INJECT_ACTIVITY: fill-in-quantities -->

<!-- INJECT_ACTIVITY: match-shop-types -->

## Підсумок — Summary

Here is your complete shopping toolkit, organized by what you need to do:

**Ask:**
- **Скільки коштує хліб?** — How much does the bread cost? (singular item)
- **Скільки коштують яблука?** — How much do the apples cost? (plural item)
- **Де тут молочний відділ?** — Where is the dairy section here?
- **Є дешевший?** — Is there a cheaper one?
- **Є знижка?** — Is there a discount?

**Buy:**
- **Дайте, будь ласка, кілограм яблук.** — Please give me a kilogram of apples.
- **Можна пляшку води?** — Can I have a bottle of water? (informal, common at markets)

**React:**
- **Дорого!** — Expensive!
- **Дешево!** — Cheap!
- **Нормальна ціна.** — Fair price.
- **Добре, беру.** — OK, I'll take it.

**Pay:**
- **Скільки за все?** — How much is everything?
- **Можна карткою?** — Can I pay by card?
- **Можна готівкою?** — Can I pay cash?

### Self-Check

Test yourself. You are at a Kyiv market and need three things: 2 kg of tomatoes (**помідори**, 50 грн/кг), 1 bottle of juice (**сік**, 30 грн), and 1 loaf of bread (**хліб**, 20 грн). Walk through the full exchange:

> **Ви:** Скільки коштують помідори? *(How much do the tomatoes cost?)*
> **Продавець:** П'ятдесят гривень за кілограм. *(Fifty hryvnias per kilogram.)*
> **Ви:** Скільки коштує сік? *(How much does the juice cost?)*
> **Продавець:** Тридцять гривень. *(Thirty hryvnias.)*
> **Ви:** Скільки коштує хліб? *(How much does the bread cost?)*
> **Продавець:** Двадцять гривень. *(Twenty hryvnias.)*
> **Ви:** Дайте, будь ласка, два кілограми помідорів, пляшку соку і буханку хліба. *(Please give me two kilograms of tomatoes, a bottle of juice, and a loaf of bread.)*
> **Продавець:** Сто п'ятдесят гривень. *(One hundred fifty hryvnias.)*
> **Ви:** Можна карткою? *(Can I pay by card?)*
> **Продавець:** Так, звичайно. *(Yes, of course.)*

Can you do this without looking at the toolkit above? That is your goal.

## Підсумок

You have now completed the shopping module — one of the most practical skills for daily life in Ukraine. The three core verbs — **коштувати** (to cost), **купувати** (to buy), and **платити** (to pay) — plus **гроші** (money) and **ціна** (price) will appear again and again throughout A1. The number pattern for **гривня** (1 гривня / 2–4 гривні / 5+ гривень) applies to many other Ukrainian nouns, so mastering it here saves you work later. Next up: M40 People Around Me, where you will meet the neighbors and family members you might shop with. And a small piece of history — the word **гривня** comes from Kyivan Rus, where it meant a silver ingot used as currency over a thousand years ago. Ukraine's modern money carries that ancient name.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: shopping
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
```

---

## Activity Type Reference

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: instruction, items[{sentence, error, correction}]
- **anagram**: Letter rearrangement. Required: instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: instruction, items[{words[], correct_order[]}]
- **observe**: Pattern discovery. Required: examples[], prompt
- **classify**: Multi-category sort. Required: instruction, categories[{label, items[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: prompt. Optional: min_words, model_answer, evaluation_criteria[]
- **reading**: Required: passage, questions[]
- **source-evaluation**: Required: source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A1.4+ (Module 39/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-numbers
- **quiz** — Яке число?: Recognize written number words
- **fill-in** — Напиши цифру словом: Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Match digits to their Ukrainian word forms

### Pattern: general-reading
- **true-false** — Правда чи ні?: Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Answer questions about a text passage


**Use these patterns.** If the pattern library recommends `divide-words` for a syllable module, generate a `divide-words` exercise. If it recommends `group-sort` for gender, generate a `group-sort`. The patterns encode how Ukrainian teachers actually test these concepts.

---

## Quality Rules

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Every activity MUST have at least 6 items.** Quiz = 6+ questions. Fill-in = 6+ sentences. Match-up = 6+ pairs. True-false = 6+ statements. Group-sort = 6+ items per group minimum. Anagram = 6+ words.
- If you can't think of 6 items, add more examples from the module's vocabulary and content. NEVER submit an activity with fewer than 6 items.
- **3-5 options per quiz/fill-in question** — enough to prevent guessing, not so many to overwhelm.

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
- `mcp__rag__verify_words` / `mcp__rag__verify_word` / `mcp__rag__verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp__rag__search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp__rag__search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp__rag__query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp__rag__query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp__rag__search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp__rag__query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp__rag__search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp__rag__search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp__rag__search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp__rag__search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp__rag__translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp__rag__query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp__rag__query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp__rag__query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp__rag__search_style_guide` first (it knows calques). Then `mcp__rag__query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp__rag__verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp__rag__query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp__rag__verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp__rag__search_idioms` for Ukrainian expressions, `mcp__rag__search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp__rag__query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp__rag__query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp__rag__verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp__rag__verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp__rag__verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp__rag__query_pravopys` or `mcp__rag__search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp__rag__verify_words` with 5-15 words at once.
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
