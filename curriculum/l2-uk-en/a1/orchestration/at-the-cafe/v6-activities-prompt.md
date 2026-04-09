<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/at-the-cafe.yaml` file for module **38: At the Cafe** (a1).

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

- `<!-- INJECT_ACTIVITY: match-up-functions -->`
- `<!-- INJECT_ACTIVITY: fill-in-ordering-accusative -->`
- `<!-- INJECT_ACTIVITY: quiz-situation-choice -->`
- `<!-- INJECT_ACTIVITY: dialogue-completion-cafe -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Order at a cafe: Мені ___, будь ласка. (choose correct accusative)'
  items:
  - Мені {каву|кава|каві}, будь ласка.
  - Мені {воду|вода|водою}, будь ласка.
  - Мені {борщ|борщу|борщем}, будь ласка.
  - Мені {салат|салату|салатом}, будь ласка.
  - Мені {суп|супу|супом}, будь ласка.
  - Дайте, будь ласка, {чай|чаю|чаєм}.
  - Я буду {піцу|піца|піці}.
  - Можна {хліб|хліба|хлібом}?
  type: fill-in
- focus: What do you say? Match situation to phrase (order/pay/ask/compliment)
  items:
  - options:
    - Мені каву, будь ласка.
    - Рахунок, будь ласка.
    - Що ви рекомендуєте?
    question: You want to order coffee. What do you say?
  - options:
    - Рахунок, будь ласка.
    - Можна меню?
    - Це гостре?
    question: You want to pay. What do you say?
  - options:
    - Скільки коштує?
    - Це з м'ясом?
    - Тут вільно?
    question: You want to know the price. What do you say?
  - options:
    - Що ви рекомендуєте?
    - Є вегетаріанське меню?
    - Все було дуже смачно!
    question: You want to ask for a recommendation. What do you say?
  - options:
    - Все було дуже смачно!
    - Можна карткою?
    - Без цукру.
    question: You want to praise the food. What do you say?
  - options:
    - Тут вільно?
    - Ще одну каву, будь ласка.
    - Рахунок, будь ласка.
    question: You want to know if a seat is free. What do you say?
  - options:
    - Це гостре?
    - Це з м'ясом?
    - Скільки коштує?
    question: You want to ask if the dish is spicy. What do you say?
  - options:
    - Можна карткою?
    - Є вегетаріанське меню?
    - Що ви рекомендуєте?
    question: You want to pay by card. What do you say?
  type: quiz
- focus: Complete the cafe dialogue with correct phrases
  items:
  - — Добрий день! Ось {меню|рахунок|картка}.
  - — Дякую. Що ви {рекомендуєте|коштуєте|платите}?
  - — Борщ дуже {смачний|гострий|вільний}.
  - — Добре, {мені|я|мене} борщ і хліб, будь ласка.
  - — А що будете {пити|їсти|читати}?
  - — Каву з молоком. — Добре, одну {хвилинку|годину|каву}.
  type: fill-in
- focus: Match Ukrainian cafe phrases with their functions
  items:
  - Рахунок, будь ласка.: Asking for the bill
  - Що ви рекомендуєте?: Asking for advice
  - Мені борщ, будь ласка.: Ordering food
  - Скільки коштує?: Asking the price
  - Можна карткою?: Asking about payment method
  - Дуже смачно!: Complimenting the food
  - Тут вільно?: Asking for a seat
  - Можна меню?: Asking to see the options
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- ресторан (restaurant, m)
- рекомендувати (to recommend)
- чайові (tip/gratuity, pl.)
- готівка (cash, f)
- картка (card, f)
- гостре (spicy — neuter adj.)
- вегетаріанський (vegetarian — adj.)
required:
- кафе (cafe, n, indecl.)
- меню (menu, n, indecl.)
- рахунок (bill, m)
- замовляти (to order)
- офіціант (waiter, m)
- смачно (delicious — adverb)
- будь ласка (please)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги — Dialogues

Welcome to a cozy **кафе** (cafe) in the heart of Lviv. The city is famous for its rich **кава** (coffee) culture, where locals spend hours talking over a warm cup. Before you can enjoy the atmosphere, you need to know how to navigate the interaction. Every cafe visit begins with a polite greeting, such as **Добрий день** (Good day), and a direct request to see what they offer. To start, you simply ask the waiter: **Можна меню?** (Can I have the menu?). Politeness is your strongest tool, so always keep **будь ласка** (please) and **дякую** (thank you) ready.

> **Ростик:** Добрий день! Можна меню? *(Good day! Can I have the menu?)*
> **Офіціант:** Ось, будь ласка. *(Here, please.)*
> **Ростик:** Що ви рекомендуєте? *(What do you recommend?)*
> **Офіціант:** Борщ дуже смачний. *(The borscht is very delicious.)*
> **Ростик:** Добре, мені борщ і хліб. А тобі, Іванко? *(Good, I will have borscht and bread. And for you, Ivanka?)*
> **Іванка:** Мені каву з молоком і тістечко. *(I will have a coffee with milk and a pastry.)*

This dialogue shows the core structure of ordering. When the waiter approaches, Rostyk asks for advice using the verb **рекомендувати** (to recommend). Once they decide, they use the pattern **Мені + [Accusative case]** to state their choices. You already know the accusative case from the previous module. Notice the noun genders: the feminine **кава** (coffee) changes to **каву**, while the masculine **чай** (tea) and neuter **тістечко** (pastry) stay exactly the same. Even when you are ordering a complex combination like **кава з молоком** (coffee with milk), only the main noun changes its ending.

> **Ростик:** Вибачте, можна рахунок? *(Excuse me, can I have the bill?)*
> **Офіціант:** Так, одну хвилинку. З вас сто двадцять гривень. Карткою чи готівкою? *(Yes, one minute. From you, one hundred twenty hryvnias. By card or by cash?)*
> **Ростик:** Карткою, будь ласка. *(By card, please.)*
> **Офіціант:** Ось термінал. Дякую. *(Here is the terminal. Thank you.)*
> **Іванка:** Дуже смачно було! Дякуємо! *(It was very delicious! We thank you!)*
> **Офіціант:** Приходьте ще! *(Come again!)*

<!-- INJECT_ACTIVITY: match-up-functions -->

## Як замовити — How to Order

The most versatile request phrase you can learn at this level is **Можна мені...?**. Literally, it means "Is it possible for me...?" and it is the standard, polite way to ask for anything you need. Always follow this phrase with the item in the accusative case. Let us look at a few examples:

*   **Можна мені каву?** — Can I have a coffee?
*   **Можна мені воду?** — Can I have some water?
*   **Можна мені сік?** — Can I have juice?
*   **Можна мені меню?** — Can I have the menu?

Another polite option is **Дайте, будь ласка** (Give me, please), which is slightly more direct but perfectly acceptable. When you are finally ready to tell the waiter your decision, you will often use the phrase **Я буду** (I will have). This is the standard way to state a final choice from the menu. 

*   **Я буду піцу і чай.** — I will have pizza and tea.
*   **Я буду салат і суп.** — I will have a salad and soup.

You might also hear people say **Я хочу** (I want). While **Я хочу** is grammatically correct and widely used, it sounds slightly more demanding than **Я буду**. Both require the accusative case.

Before you make a final decision, you may need to ask questions about the food. You can easily check for specific dietary preferences or tastes using simple questions. If you do not like spicy food, you ask: **Це гостре?** (Is it spicy?). If you want to know the ingredients, you can ask: **Це з м'ясом?** (Is it with meat?) or **Є вегетаріанське меню?** (Is there a vegetarian menu?). Often, you will see a delicious pastry in the display case but you do not know the name. In that situation, you simply point and ask: **А що це?** (And what is this?). 

Sometimes you just need a bit more. You can handle extra quantities easily by saying: **Ще одну каву, будь ласка** (One more coffee, please). You can also add simple modifiers to your drink order. You might ask for a drink **без цукру** (without sugar) or **з лимоном** (with lemon). Finally, listen carefully for the most common question at any modern coffee counter: **Вам тут чи з собою?** (For here or to go?). You just reply **Тут** (Here) or **З собою** (To go).

<!-- INJECT_ACTIVITY: fill-in-ordering-accusative -->

## Культура кафе — Cafe Culture

When it is time to order, there is one linguistic "Golden Rule" you must follow: always use the verb **замовляти** (to order). You might sometimes hear people use the word *заказати*, but this is a direct calque from Russian and is considered incorrect in modern standard Ukrainian. You should always say **Я замовляю піцу** (I am ordering a pizza). 

Additionally, you need to recognize a special group of nouns like **кафе** (cafe) and **меню** (menu). These are indeclinable foreign words. This means they NEVER change their endings, no matter what case they are in. You say **Це кафе** (This is a cafe) and you also say **Я в кафе** (I am in the cafe). The ending stays exactly the same. Other common indeclinable words you will hear include **какао** (cocoa), **метро** (subway), and **ескімо** (popsicle). 

:::caution
Never try to change the ending of **кафе** or **меню**. Forms like *кафі* or *менюю* do not exist in Ukrainian. Keep them exactly as they are in the dictionary.
:::

When you finish eating, there is an important point of etiquette regarding the **рахунок** (bill). In a traditional **ресторан** (restaurant) or a formal cafe, the waiter rarely brings the bill automatically. This is done so you do not feel rushed to leave. You must catch their eye, raise your hand slightly, and ask: **Можна рахунок?** (Can I have the bill?). Once the bill arrives, you must consider the **чайові** (tips). In most cities, leaving a 10% tip is standard for good service. You can usually leave cash in the folder they provide or ask to add it directly to your card payment.

When it comes to payment logistics, the waiter will almost always ask: **Карткою чи готівкою?** (By card or by cash?). Ukraine has one of the highest rates of contactless payment in Europe. Even a small street kiosk usually has a **термінал** (payment terminal). You can confidently reply **Карткою, будь ласка** (By card, please). If you pay with cash, they will take your **оплата** (payment) and bring you the **решта** (change).

Finally, you need a few social phrases to complete the cafe experience. If you enter a crowded place and see an empty chair at a shared table, you should politely ask: **Тут вільно?** (Is this seat free?). When the waiter brings your food, they will always say: **Смачного!** (Bon appétit!), and you should reply with **Дякую!** (Thank you!). As you leave, the best compliment you can give the staff is to smile and say: **Все було дуже смачно!** (Everything was very delicious!). 

<!-- INJECT_ACTIVITY: quiz-situation-choice -->
<!-- INJECT_ACTIVITY: dialogue-completion-cafe -->

## Підсумок — Summary

You now have the complete communication toolkit needed to navigate a Ukrainian cafe with confidence. You understand that politeness is key, and you know how to use the accusative case to make clear, accurate requests. Here is a recap of the essential patterns you should memorize:

*   **To order:** Мені [accusative], будь ласка. *(Мені каву, будь ласка.)*
*   **To ask:** Скільки коштує? Що рекомендуєте? *(How much does it cost? What do you recommend?)*
*   **To pay:** Рахунок, будь ласка. Можна карткою? *(The bill, please. Can I pay by card?)*
*   **To compliment:** Дуже смачно! Дякую! *(Very delicious! Thank you!)*

Remember that the phrase **будь ласка** (please) is your magic key for all interactions. It softens any request and shows respect for the person helping you. 

Before you move to the next module, do a quick self-check. Can you perform all of these tasks?

*   Can you greet the waiter and ask for a menu? (**Добрий день, можна меню?**)
*   Can you order a drink and a main course using the accusative case? (**Мені каву і піцу.**)
*   Can you ask if a dish is spicy or vegetarian? (**Це гостре? Є вегетаріанське меню?**)
*   Can you ask for the bill and specify your payment method? (**Можна рахунок? Карткою, будь ласка.**)
*   Do you remember to use the correct verb **замовляти** (to order) instead of the Russianism *заказати*?

If you can confidently handle these situations, you are ready to order your next meal in Ukrainian!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: at-the-cafe
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

**Level: A1.4+ (Module 38/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
