<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/food-and-drink.yaml` file for module **36: Food and Drink** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-meals-dishes -->`
- `<!-- INJECT_ACTIVITY: match-up-food-vocab -->`
- `<!-- INJECT_ACTIVITY: group-sort-food-drinks -->`
- `<!-- INJECT_ACTIVITY: fill-in-chunks -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match Ukrainian food and drink words to English
  items: 10
  pairs:
  - хліб: bread
  - м'ясо: meat
  - риба: fish
  - молоко: milk
  - вода: water
  - сік: juice
  - сніданок: breakfast
  - обід: lunch
  - вечеря: dinner
  - суп: soup
  type: match-up
- focus: Categorize into Їжа (Food) and Напої (Drinks)
  groups:
  - items:
    - хліб
    - м'ясо
    - риба
    - суп
    - каша
    name: Їжа
  - items:
    - кава
    - чай
    - вода
    - сік
    - молоко
    name: Напої
  items: 10
  type: group-sort
- blanks:
  - Я хочу каву {з молоком}.
  - Вона п'є чай {з цукром}.
  - Він їсть хліб {з маслом}.
  - Я люблю чай {з лимоном}.
  - Дайте, будь ласка, воду {з газом}.
  - Ми їмо м'ясо {з картоплею}.
  focus: Use 'з + noun' as memorized chunks for additions
  items: 6
  type: fill-in
- focus: Identify meals and iconic Ukrainian dishes
  items: 6
  questions:
  - Що ми їмо вранці? (сніданок / обід / вечерю)
  - Що ми їмо ввечері? (вечерю / сніданок / обід)
  - Традиційний український суп — це... (борщ / каша / вода)
  - 'Українська страва з тіста і картоплі або сиру: (вареники / сало / хліб)'
  - 'Популярний холодний напій з фруктів: (компот / борщ / кава)'
  - Що ми їмо вдень? (обід / сніданок / вечерю)
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- борщ (beet soup, m)
- вареник (dumpling, m)
- каша (porridge, f)
- сир (cheese, m)
- масло (butter, n)
- яйце (egg, n)
- картопля (potato, f)
- цукор (sugar, m)
- сіль (salt, f)
- сметана (sour cream, f)
- компот (compote, m)
- курка (chicken, f)
- салат (salad, m)
- піца (pizza, f)
- помідор (tomato, m)
- огірок (cucumber, m)
- яблуко (apple, n)
- банан (banana, m)
- лимон (lemon, m)
required:
- їжа (food, f)
- напій (drink, m)
- хліб (bread, m)
- кава (coffee, f)
- чай (tea, m)
- вода (water, f)
- молоко (milk, n)
- сік (juice, m)
- м'ясо (meat, n)
- риба (fish, f)
- суп (soup, m)
- сніданок (breakfast, m)
- обід (lunch, m)
- вечеря (dinner, f)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

A typical Saturday morning in a Ukrainian home is a lively and sensory experience. The kitchen smells of fresh herbs, earthy vegetables, and warm bread. An older woman, a **бабуся** (grandma), is standing by the stove, preparing to cook. Her granddaughter, an **онучка** (granddaughter), comes in for a morning meal. They are about to cook the national dish, but first, they need to eat.

They begin their day with a conversation about food. Notice how they use the preposition **з** (with) to describe food pairings as they decide what to eat. 

> **Бабуся:** Що ти хочеш на сніданок? *(What do you want for breakfast?)*
> **Онучка:** Каву з молоком і хліб з маслом. *(Coffee with milk and bread with butter.)*
> **Бабуся:** А я хочу чай з цукром і кашу. *(And I want tea with sugar and porridge.)*

Then, they prepare the fresh ingredients for their soup. Grandma uses this moment to explain that every single ingredient has a grammatical gender, reinforcing a core rule of the language while they cook. 

> **Бабуся:** Для борщу потрібен буряк. Це він. *(For borshch, beetroot is needed. It is a "he".)*
> **Онучка:** А картопля і капуста? *(And potato and cabbage?)*
> **Бабуся:** Це вона. Морква і цибуля — теж вона. *(That is a "she". Carrot and onion are also "she".)*
> **Онучка:** А м'ясо? *(And meat?)*
> **Бабуся:** М'ясо — воно. А в кінці буде сметана! *(Meat is an "it". And at the end there will be sour cream!)*

Food structures our entire day. Ukrainians divide their daily eating habits into three main meals:
* **сніданок** — breakfast
* **обід** — lunch
* **вечеря** — dinner

In the morning, you eat a **сніданок**. In the middle of the day, usually early afternoon, you eat an **обід**, which is traditionally the largest meal. In the evening, you gather with family for a **вечеря**. The verb meaning "to eat" is **їсти**. Learning to talk about these meals helps you describe your daily routine.

:::note Culture
Ukrainian hospitality is deeply connected to food. Being invited to share a meal, whether it is a simple **сніданок** or a festive **вечеря**, is a true sign of friendship and respect.
:::

People frequently talk about their food preferences and ask what others eat. When ordering or asking for food, you use the accusative case for the direct object. Combinations like meat with potatoes form memorized phrases that you can use immediately. 

> **Онучка:** Що ти зазвичай їш на обід? *(What do you usually eat for lunch?)*
> **Бабуся:** Суп і салат. *(Soup and salad.)*
> **Онучка:** А на вечерю? *(And for dinner?)*
> **Бабуся:** М'ясо з картоплею або рибу з рисом. *(Meat with potatoes or fish with rice.)*

<!-- INJECT_ACTIVITY: quiz-meals-dishes -->

## Їжа (Food)

The general word for food is **їжа** (food). Grains and bakery products are fundamental to the Ukrainian diet. The most sacred and respected food on the table is **хліб** (bread). It accompanies almost every meal, and offering bread is a traditional sign of hospitality. You will also frequently eat **каша** (porridge or cereal), which is a common dish for breakfast or served as a warm side dish. Other staple carbohydrates that you will find in any pantry include **рис** (rice) and **макарони** (pasta). 

For proteins and dairy, the Ukrainian kitchen offers many rich options. The general word for meat is **м'ясо** (meat), and a very common, affordable type is **курка** (chicken). If you prefer seafood, you can eat **риба** (fish). A basic ingredient used for a quick breakfast or for baking is an **яйце** (egg). Dairy products are also essential to everyday meals. You will often drink **молоко** (milk) or eat **йогурт** (yogurt). You spread **масло** (butter) on your bread, and you add a spoonful of **сметана** (sour cream) to your soup. 

:::caution Russianisms
Never use the Russian word «творог» for cottage cheese or quark. The authentic Ukrainian word for all types of cheese, both yellow hard cheese and soft farmer's cheese, is **сир** (cheese). Context will always tell you which one a person means.
:::

A Ukrainian garden provides abundant and fresh produce. Common **овочі** (vegetables) form the base for many salads and hearty soups. You will frequently cook with **картопля** (potato), **морква** (carrot), **цибуля** (onion), **помідор** (tomato), and **огірок** (cucumber). For a sweet snack or dessert, you eat **фрукти** (fruits). Popular choices include a **яблуко** (apple), a **банан** (banana), or an **апельсин** (orange). For basic cooking, your pantry needs **цукор** (sugar) for sweetness, **сіль** (salt) for flavor, and liquid **олія** (oil) for frying.

Cultural spotlight: iconic Ukrainian dishes. The absolute national symbol of Ukrainian cuisine is **борщ** (beet soup). It is recognized as a UNESCO intangible cultural heritage and serves as a point of immense national pride. Borshch is definitively Ukrainian, not a generic Eastern European soup. Another beloved favorite is **вареники** (filled dumplings), which cooks stuff with potato, cabbage, meat, or sweet cherries. A highly traditional and culturally significant ingredient is **сало** (cured pork fat), often eaten thin-sliced with dark bread and garlic. Finally, **деруни** (potato pancakes) are a crispy, savory dish always served with a generous spoonful of sour cream. For a modern, quick meal, many people simply order a hot **піца** (pizza), or they prepare a light **суп** (soup) and a fresh **салат** (salad).

<!-- INJECT_ACTIVITY: match-up-food-vocab -->

## Напої (Drinks)

Daily hydration involves both hot and cold choices. The general word for a drink is a **напій** (drink). For a hot drink, many people start the day with a strong **кава** (coffee). Alternatively, you can drink a warm **чай** (tea). For cold drinks, the most basic necessity is **вода** (water) or a sweet fruit **сік** (juice). If you order water in a cafe, a waiter might ask if you want **вода з газом** (sparkling water, literally "water with gas") or **вода без газу** (still water).

:::caution Russianisms
Do not use the Russian word «кофе». The correct Ukrainian word for coffee is always **кава**.
:::

Traditional beverages and milk-based drinks hold a special place on the table. A very popular homemade sweet drink is **компот** (fruit water), made by boiling fresh berries or fruits. In a modern restaurant, you might order a cold **лимонад** (lemonade). During winter holidays, families prepare **узвар** (dried fruit drink), which has a rich, slightly smoky flavor and deep cultural roots. For dairy drinks, the most common choice is **молоко** (milk), but many people also drink **кефір** (a fermented milk drink) for its health benefits. Adults might also recognize alcoholic options like **пиво** (beer) and **вино** (wine).

The 'з + Noun' formula is your key to describing what goes into your drink or meal. In Ukrainian, you often describe drinks and dishes with additions using the preposition **з** (with). At this early stage of learning, you should treat these combinations as single, memorized chunks rather than complex grammar rules. You simply memorize the ending **-ом** for masculine or neuter additions, and **-ою** for feminine additions. By treating the preposition and the noun as a single unit representing the flavor profile, you can speak fluently now without worrying about the full instrumental case table. 

Learn these common combinations as fixed phrases:
* **кава з молоком** — coffee with milk
* **чай з цукром** — tea with sugar
* **вода з газом** — sparkling water
* **чай з лимоном** — tea with lemon (using the word **лимон**, lemon)
* **м'ясо з картоплею** — meat with potatoes

<!-- INJECT_ACTIVITY: group-sort-food-drinks -->
<!-- INJECT_ACTIVITY: fill-in-chunks -->

## Підсумок — Summary

You now possess the fundamental vocabulary to name what you eat and drink in a Ukrainian kitchen. You know that the day revolves around three main meals: **сніданок** (breakfast), **обід** (lunch), and **вечеря** (dinner). When someone asks **Що ти хочеш?** (What do you want?), you can confidently reply with your preferences. You can use the preposition **з** to describe additions as memorized chunks, saying **кава з молоком** or **чай з цукром**. Beyond just words, you recognize the deep cultural weight of Ukrainian cuisine, understanding that dishes like borshch and varenyky are an essential part of national identity and heritage. Food brings people together, and knowing these terms helps you connect with Ukrainians on a personal level.

To test your reading comprehension, read these short texts about daily routines:

> **Я снідаю вдома. Я їм хліб з сиром. Я п'ю каву з молоком. На обід я їм суп і салат. На вечерю я готую рибу. Це дуже смачно!**
> *(I have breakfast at home. I eat bread with cheese. I drink coffee with milk. For lunch I eat soup and salad. For dinner I cook fish. It is very tasty!)*

> **Я люблю холодний компот. Мій друг любить гарячий чай з лимоном. У кафе ми замовляємо воду з газом.**
> *(I love cold fruit water. My friend loves hot tea with lemon. In a cafe we order sparkling water.)*

Before moving forward, verify that you can confidently answer the following questions:
* Name 5 foods you have in your kitchen right now (for example: **хліб**, **яйце**, **сир**, **морква**, **яблуко**).
* Name 3 drinks you like (for example: **кава**, **чай**, **сік**).
* Translate the phrase: "What do you want?" — "I want coffee with milk and bread with butter" (**Що ти хочеш? — Каву з молоком і хліб з маслом**).
* Translate the question: "What do you eat for breakfast, lunch, and dinner?" (**Що ти їш на сніданок, обід і вечерю?**)
* Explain the difference between **сніданок** and **вечеря**, and name a typical food you might eat for each meal.
* Why is **борщ** important to Ukrainians? (It is a powerful symbol of identity and cultural heritage).
* Name one traditional Ukrainian cold drink (**компот** or **узвар**).

If you can answer these questions and name your favorite foods, you are ready to continue your culinary journey and start ordering in Ukrainian cafes.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: food-and-drink
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

**Level: A1.4+ (Module 36/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options

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
