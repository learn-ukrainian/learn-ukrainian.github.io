<!-- version: 1.1.0 | updated: 2026-03-31 -->
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

- `<!-- INJECT_ACTIVITY: match-up-shops -->`
- `<!-- INJECT_ACTIVITY: quiz-currency-choice -->`
- `<!-- INJECT_ACTIVITY: fill-in-prices -->`
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
## Діалоги — Dialogues

When you visit Ukraine, you will notice a distinct difference between traditional shopping and modern retail. A traditional market, known as a **ринок** (market) or **базар** (bazaar), is a lively, bustling place where you can find fresh, local produce directly from farmers. It is a highly communicative environment where talking to the seller is part of the experience. On the other hand, a modern **супермаркет** (supermarket) offers convenience and fixed prices. The conversations below show a mother, **Мама**, and her daughter, **Дочка**, shopping for dinner in both of these authentic Ukrainian settings.

> **(На ринку / At the market)**
> **Мама:** Добрий день! Скільки коштує кілограм яблук? *(Good day! How much does a kilogram of apples cost?)*
> **Продавець:** Сорок гривень. *(Forty hryvnias.)*
> **Мама:** А помідори? *(And tomatoes?)*
> **Продавець:** Тридцять п'ять гривень за кілограм. *(Thirty-five hryvnias per kilogram.)*
> **Мама:** Дайте, будь ласка, два кілограми помідорів і кілограм яблук. *(Give me, please, two kilograms of tomatoes and a kilogram of apples.)*
> **Продавець:** Сімдесят п'ять гривень. *(Seventy-five hryvnias.)*
> **Мама:** Ось, будь ласка. *(Here you go, please.)*
> **Продавець:** Дякую! *(Thank you!)*

:::note
**The Ukrainian Market Culture**
A traditional Ukrainian **ринок** (market) is not just a place to buy food; it is a vital social hub. You will often see people chatting with their favorite sellers, asking about their families, and selecting the freshest produce straight from the garden. It is a much more personal experience than visiting a supermarket!
:::

> **(У супермаркеті / At the supermarket)**
> **Мама:** Вибачте, де тут хліб? *(Excuse me, where is the bread here?)*
> **Працівник:** Хліб у третьому ряді. *(The bread is in the third aisle.)*
> **Дочка:** А молоко? *(And milk?)*
> **Працівник:** Молоко в холодильнику, там. *(The milk is in the fridge, over there.)*
> **Мама:** Скільки коштує цей сир? *(How much does this cheese cost?)*
> **Дочка:** Сто двадцять гривень. *(One hundred twenty hryvnias.)*
> **Мама:** Дорого! А є дешевший? *(Expensive! And is there a cheaper one?)*
> **Дочка:** Так, ось цей — вісімдесят. *(Yes, this one here — eighty.)*

The core food items that appeared in these conversations are essential vocabulary. You will hear these words every time you visit a grocery store or market: **хліб** (bread), **молоко** (milk), **сир** (cheese), **ковбаса** (sausage), and **масло** (butter). Memorize these everyday essentials before we explore how to handle numbers and money.

<!-- INJECT_ACTIVITY: match-up-shops -->

## Скільки коштує? — How Much?

To navigate any shop successfully, you must learn how to ask for prices. The most important verb for this situation is **коштувати** (to cost). Because Ukrainian grammar requires the verb to agree with the noun, we use two different forms depending on whether the item is singular or plural. If you are asking about one single item, such as a loaf of bread, use the singular form: **Скільки коштує...?** (How much does ... cost?). If you are asking about multiple items, like apples, use the plural form: **Скільки коштують...?** (How much do ... cost?). These examples show the pattern in action:

- **Скільки коштує хліб?** (How much does the bread cost?)
- **Скільки коштує масло?** (How much does the butter cost?)
- **Скільки коштує вода?** (How much does the water cost?)
- **Скільки коштують яблука?** (How much do the apples cost?)
- **Скільки коштують яйця?** (How much do the eggs cost?)
- **Скільки коштують помідори?** (How much do the tomatoes cost?)

:::caution
**Agreement Matters**
Remember that **коштувати** (to cost) must match the noun it describes. A common mistake is to use the singular **коштує** for plural items like **яблука** (apples). Always check if you are buying one thing or many things before you ask the price!
:::

Once you ask the price, you need to understand the answer. The national currency of Ukraine is the **гривня** (hryvnia). The word for the currency itself changes its ending depending on the exact number that comes right before it. For the number one, and any number ending in one, we use the basic dictionary form: **21 гривня** (twenty-one hryvnias). For numbers ending in two, three, or four, the word takes a plural ending: **32 гривні** (thirty-two hryvnias). For the number five and any number above it, including all the tens, we use the "many" form: **45 гривень** (forty-five hryvnias), **100 гривень** (one hundred hryvnias). You will also see prices that include smaller coins. Traditionally, the hundredth part of a hryvnia is called a **копійка** (kopeck). However, it is important to know that **копійка** is a term imposed during the Russian imperial era. The true, historical Ukrainian term for a small coin is **шаг** (shah), which Ukraine is currently working to restore to everyday use.

When you hear the price, you might want to express your reaction to it. You can use simple adverbs to state your opinion clearly. If a price seems too high, you can use the word **дорого** (expensive). If you find a great deal, you can happily use the word **дешево** (cheap). If the price is exactly what you expected, you can confirm it with the phrase **нормальна ціна** (fair price). When shopping at a traditional market, or if you are buying many items at once, you might want to politely ask for a lower price: **Є знижка?** (Is there a discount?). Finally, when you have selected everything you need and are ready to finish the transaction, you can ask for the total amount by saying **За все** (Total) or ask the seller directly **Скільки з мене?** (How much do I owe?). Here are these reactions and questions in action:

- **Це дуже дорого!** (This is very expensive!)
- **Тут дешево.** (It is cheap here.)
- **Це нормальна ціна.** (This is a fair price.)
- **Є знижка на яблука?** (Is there a discount on apples?)
- **Скільки за все?** (How much for everything?)
- **Скільки з мене?** (How much do I owe?)

<!-- INJECT_ACTIVITY: quiz-currency-choice -->
<!-- INJECT_ACTIVITY: fill-in-prices -->

## Де купити? — Where to Buy

When you step out into a Ukrainian city or town, you will encounter several different types of places to buy your daily goods. A general, everyday shop is simply called a **магазин** (shop). If you are visiting a large, modern self-service store with shopping carts and long aisles, you will call it a **супермаркет** (supermarket). You will also frequently see the beautiful, traditional Ukrainian word **крамниця** (store), which is an excellent native synonym for a shop. Inside a massive supermarket, you need to know how to navigate between different product zones. For example, if you are looking for chicken or sausage, you will head to the **м'ясний відділ** (meat section). If you need to buy yogurt, butter, or cheese, you will look for the **молочний відділ** (dairy section). For medicines, you will visit an **аптека** (pharmacy). You will use these location words frequently:

- **Ми йдемо в магазин.** (We are going to the shop.)
- **Цей супермаркет дуже великий.** (This supermarket is very big.)
- **Наш ринок старий.** (Our market is old.)
- **М'ясний відділ там.** (The meat section is there.)
- **Молочний відділ тут.** (The dairy section is here.)

When you ask for food, you rarely just ask for the item itself; you usually need a specific amount. In Ukrainian, quantity words act as a fixed grammatical chunk. The word that comes after the quantity always takes a special ending (the genitive case), which naturally includes the English meaning of the word "of". Memorize these useful combinations as complete phrases:

- **кілограм яблук** (a kilogram of apples)
- **два кілограми помідорів** (two kilograms of tomatoes)
- **літр молока** (a liter of milk)
- **два літри соку** (two liters of juice)
- **пачка масла** (a pack of butter)
- **пачка чаю** (a pack of tea)
- **пляшка води** (a bottle of water)
- **пляшка соку** (a bottle of juice)
- **буханка хліба** (a loaf of bread)

:::tip
**The Hidden "Of"**
When you use quantity words like **кілограм** (kilogram) or **літр** (liter), you do not need to add a separate Ukrainian word for "of". The relationship is built directly into the grammar when the second word changes its ending. **Літр молока** literally means "a liter of milk" all by itself!
:::

When it is your turn to speak to the seller, you will use a standard, polite formula to make your request. You should always start with the imperative phrase **Дайте, будь ласка...** (Give me, please...). This is the most natural and respectful way to ask for items in Ukraine. Once the seller has gathered your items, it is time to pay. You have two main payment options: **готівка** (cash) or **картка** (card). If you prefer to pay electronically, you can politely ask the cashier **Можна карткою?** (Is it possible by card?). If you pay with physical money, the seller will hand back your change and say **Ось решта** (Here is the change). Regardless of how you pay, the transaction usually ends when the cashier hands you a small piece of paper and says **Ось ваш чек** (Here is your receipt). These are the most common phrases you will hear and use at the checkout:

- **Дайте, будь ласка, літр молока.** (Give me, please, a liter of milk.)
- **Дайте, будь ласка, кілограм сиру.** (Give me, please, a kilogram of cheese.)
- **Я хочу купити хліб.** (I want to buy bread.)
- **Можна карткою?** (Is it possible by card?)
- **Можна готівкою?** (Is it possible with cash?)
- **Ось ваша решта.** (Here is your change.)
- **Ось ваш чек.** (Here is your receipt.)

<!-- INJECT_ACTIVITY: fill-in-quantities -->

## Підсумок — Summary

You now have a complete and practical toolkit for navigating any shopping scenario in Ukraine. A successful purchase always follows a predictable rhythm of four steps. First, you ask for information to locate items and check prices: **Скільки коштує?** (How much does it cost?) and **Де тут хліб?** (Where is the bread here?). Second, you confidently choose your items and state the quantities you need: **Дайте, будь ласка, кілограм яблук** (Give me, please, a kilogram of apples). Third, you react to the price to ensure it is fair: **Дорого!** (Expensive!), **Дешево!** (Cheap!), or accept it with **Добре, беру** (Good, I'll take it). Finally, you complete the transaction by asking for the total and choosing your payment method: **Скільки за все?** (How much for everything?) and **Можна карткою?** (Is it possible by card?). By practicing these exact phrases, you will be prepared for daily life.

When you shop at a traditional Ukrainian market, you will quickly notice a charming cultural habit. Sellers frequently use special diminutive forms of words when speaking to customers. Instead of simply offering a standard potato, they might offer you a **картопелька** (little potato). Instead of regular apples, they will proudly show you their **яблучка** (little apples). They do not use these words because the food is physically small. In Ukrainian culture, adding these gentle, softening endings to words is a way to express warmth, hospitality, and a welcoming attitude toward the buyer. It makes the market feel like a friendly community rather than a cold business transaction. Despite this friendly atmosphere, you must always remember to maintain your own politeness by using the formal pronoun **Ви** (You) when speaking to any seller you do not know personally.

Before you finish this module, take a moment to test your new skills mentally. Imagine yourself in these three common situations and try to form the correct Ukrainian sentences in your head:

- You are standing at a vibrant outdoor market. How do you ask the seller for the exact price of five kilograms of fresh potatoes?
- The seller tells you the price, but it seems much too high for your budget. How do you clearly express to the seller that two hundred hryvnias is too expensive?
- Imagine you need to buy 3 items at a market. How do you successfully ask the price, choose a quantity for each, and pay?
```

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
