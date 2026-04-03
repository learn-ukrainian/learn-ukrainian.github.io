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
- `<!-- INJECT_ACTIVITY: fill-in-z-chunks -->`
- `<!-- INJECT_ACTIVITY: match-food-drink -->`
- `<!-- INJECT_ACTIVITY: group-sort-food-drinks -->`
- `<!-- INJECT_ACTIVITY: quiz-meals-dishes -->`

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
## Діалоги

Food is woven into Ukrainian daily life, from morning **кава** (coffee) to evening **вечеря** (dinner). The two dialogues below put this module's vocabulary into real use — ordering breakfast at home and discussing what you eat at each meal.

> **Марко:** Що ти хочеш на сніданок? *(What do you want for breakfast?)*
> **Оленка:** Каву з молоком і хліб з маслом. *(Coffee with milk and bread with butter.)*
> **Марко:** А я хочу чай з цукром і кашу. *(And I want tea with sugar and porridge.)*
> **Оленка:** Добре. Каша на плиті. *(Good. The porridge is on the stove.)*
> **Марко:** Смачно! Дякую. *(Delicious! Thanks.)*

Notice the phrases **каву з молоком**, **хліб з маслом**, **чай з цукром** — each one is a memorized chunk. Do not try to analyze the endings yet. Think of **кава з молоком** the way you think of "coffee with milk" in English — as one unit.

:::tip Memorized chunks
**Кава з молоком**, **чай з цукром**, **хліб з маслом** — learn each phrase as a single block. The ending on the second word changes (молоко → молоком, цукор → цукром), but you will study WHY in A2. For now, repeat each phrase until it feels automatic.
:::

> **Оленка:** Що ти зазвичай їси на обід? *(What do you usually eat for lunch?)*
> **Марко:** Зазвичай суп і салат. Іноді піцу. *(Usually soup and salad. Sometimes pizza.)*
> **Оленка:** А на вечерю? *(And for dinner?)*
> **Марко:** М'ясо з картоплею або рибу з рисом. А ти? *(Meat with potato or fish with rice. And you?)*
> **Оленка:** Я люблю вареники або кашу. *(I like dumplings or porridge.)*

Three meal names appear naturally here: **сніданок** (breakfast, from Dialogue 1), **обід** (lunch), and **вечеря** (dinner). Each meal anchors to a time of day: **сніданок** happens **вранці** (in the morning), **обід** — **вдень** (in the afternoon), **вечеря** — **ввечері** (in the evening). These time words appear in later activities — note them now.

## Їжа

Ukrainian cuisine is rooted in the land — fields of wheat, gardens full of vegetables, orchards heavy with apples. Core staples fall into clear categories. **Хліб і каша**: **хліб** (bread) is the daily staple — no Ukrainian meal is complete without it. **Каша** (porridge) — **гречана каша** (buckwheat porridge) is the most characteristically Ukrainian. **Рис** (rice) and **макарони** (pasta) round out the group. **М'ясо і риба**: **м'ясо** (meat) is the umbrella word, **курка** (chicken) is the most commonly eaten, and **риба** (fish) is especially popular on fasting days.

**Овочі** (vegetables): **картопля** (potato) is the most eaten vegetable in Ukraine — it appears in **борщ**, **вареники**, and **деруни**. **Морква** (carrot), **цибуля** (onion), **помідор** (tomato), **огірок** (cucumber) complete the basics. Memory hook: **картопля** is everywhere — if you remember one vegetable, remember this one. **Фрукти** (fruit): **яблуко** (apple) — Ukrainian gardens are famous for apple trees. **Банан** (banana) is imported but very popular. **Апельсин** (orange). **Лимон** (lemon) — goes straight into **чай**.

:::note Dairy and pantry basics
**Молочне** (dairy): **молоко** (milk), **сир** (cheese — this word also means cottage cheese; hard cheese is **твердий сир**), **масло** (butter — also used for oil; context tells you which), **сметана** (sour cream — essential on борщ), **йогурт** (yogurt). **Інше** (other): **яйце** (egg), **цукор** (sugar), **сіль** (salt), **олія** (vegetable oil — **соняшникова олія**, sunflower oil, is the Ukrainian kitchen staple).
:::

These next words are not just vocabulary — they are symbols of Ukrainian identity.

**Борщ** — the national dish, a rich beet soup made with **буряк** (beetroot), **картопля**, **капуста** (cabbage), **морква**, **цибуля**, and **м'ясо**, served with a generous spoonful of **сметана**. UNESCO recognized Ukrainian борщ as part of the Intangible Cultural Heritage list in 2022. As Ukrainian textbooks say: *«Україна завжди славилася своєю кухнею. Усім відомі українські борщ, галушки, вареники.»*

**Вареники** — half-moon dumplings filled with **картопля** and **сир** (the most beloved filling), or with **вишня** (cherry) for dessert. Families make вареники together at the kitchen table — it is a ritual passed from grandmother to grandchild. As one textbook puts it: *«Вареники в українській культурі — символ заможного, щасливого життя.»*

**Сало** — cured pork fat, eaten thinly sliced with **хліб** and **часник** (garlic). It appears in folk humor and proverbs as the ultimate Ukrainian food. **Галушки** — soft dumplings from the Poltava region, immortalized in Kotliarevsky's *Енеїда*. **Деруни** — potato pancakes, crisp and golden, served with **сметана**. Knowing these dishes is a first step into Ukrainian culture.

:::caution Борщ is Ukrainian
Борщ is a Ukrainian national dish. Its origins are Ukrainian, and UNESCO listed specifically Ukrainian борщ culture. This is not a matter of opinion — it is documented cultural heritage.
:::

<!-- INJECT_ACTIVITY: quiz-meals-dishes -->

## Напої

**Напій** (drink, masculine) is the general Ukrainian word for any beverage — hot or cold, alcoholic or not. The plural is **напої** (drinks). When someone asks *«Який напій ти хочеш?»* (What drink do you want?), they mean anything from **кава** to **сік**. This section covers the most common **напої** in Ukrainian daily life.

**Гарячі напої** (hot drinks) rule the Ukrainian morning and evening. **Кава** (coffee) is drunk strong — often **еспресо** or **турецька кава** (Turkish-style coffee). **Чай** (tea) is even more common: **чорний чай** (black tea) and **зелений чай** (green tea) are the main varieties. Both are drunk **з цукром** (with sugar), **з лимоном** (with lemon), or **з медом** (with honey — a natural Ukrainian sweetener).

**Холодні напої** (cold drinks): **вода** (water) — note the difference between **вода без газу** (still water) and **вода з газом** (sparkling water). **Сік** (juice) comes in many kinds: **апельсиновий сік** (orange juice), **яблучний сік** (apple juice), **томатний сік** (tomato juice). **Компот** — a traditional Ukrainian напій made from fruit (**вишня**, **яблуко**, **слива**) boiled with water and **цукор**; every Ukrainian grandmother makes it. **Лимонад** (lemonade or soft drink). **Молочні напої** (dairy drinks): **молоко** and **кефір** (fermented milk — popular, healthy, drunk daily). **Алкогольні напої** (for recognition only): **пиво** (beer), **вино** (wine).

### How «з + noun» works at A1

In English you say "coffee with milk." In Ukrainian: **кава з молоком**. The word after **з** changes its ending:

- молоко → **молоком**
- цукор → **цукром**
- лимон → **лимоном**
- газ → **газом**
- масло → **маслом**
- картопля → **картоплею**

This ending change is called the instrumental case (**орудний відмінок**) — you will study it systematically in A2. At A1, learn each phrase as ONE fixed unit:

- **кава з молоком** · **чай з цукром** · **чай з лимоном**
- **вода з газом** · **хліб з маслом** · **м'ясо з картоплею**

Say each phrase as a single breath. Do not try to produce new combinations yet — just recognize and reproduce these six.

:::tip Ordering at a café
A Kyiv café menu reads: кава з молоком — 65 грн, чай з лимоном — 40 грн, вода з газом — 30 грн. When ordering, say:

- **Будь ласка, каву з молоком.** *(Coffee with milk, please.)*
- **Дайте, будь ласка, чай з лимоном.** *(Give me tea with lemon, please.)*
- **Мені воду з газом.** *(Sparkling water for me.)*

Notice **кава** becomes **каву** and **вода** becomes **воду** when you order — that is the accusative case (**знахідний відмінок**), also for A2. For now, memorize the ordering phrases whole. Recognizing the pattern is enough at A1.
:::

<!-- INJECT_ACTIVITY: fill-in-z-chunks -->

<!-- INJECT_ACTIVITY: match-food-drink -->

<!-- INJECT_ACTIVITY: group-sort-food-drinks -->

<!-- INJECT_ACTIVITY: quiz-meals-dishes -->

## Підсумок — Summary

You now have a toolkit for talking about food and drink in Ukrainian. Here are the key patterns in action:

- **Що ти хочеш?** — **Каву з молоком.** *(What do you want? — Coffee with milk.)*
- **Що ти їси на сніданок?** — **Кашу і хліб з маслом.** *(What do you eat for breakfast? — Porridge and bread with butter.)*
- **Що ти їси на обід?** — **Суп і салат.** *(What do you eat for lunch? — Soup and salad.)*
- **Що ти їси на вечерю?** — **М'ясо з картоплею або рибу з рисом.** *(What do you eat for dinner? — Meat with potato or fish with rice.)*

You have learned 25+ food and drink words across six categories: **хліб/каша** (bread/porridge), **м'ясо/риба** (meat/fish), **овочі** (vegetables), **фрукти** (fruit), **молочне** (dairy), and **напої** (drinks). The word **напій** (drink) is the singular form — you will see it on menus, in questions, and in everyday conversation. You have memorized six **з + noun** chunks as fixed expressions. And you know the three meal names with their time anchors: **сніданок** — **вранці**, **обід** — **вдень**, **вечеря** — **ввечері**.

Ukrainian food is more than vocabulary — it is cultural identity. **Борщ** is more than a soup: it is a symbol of home, family, and the Ukrainian land. When a Ukrainian says *«як мамин борщ»* (like mom's борщ), they mean something irreplaceable and deeply personal. **Вареники** made together at the table are a family ritual — hands covered in flour, laughter, stories. **Сало**, often misunderstood by outsiders, is eaten with deep cultural pride — it appears in proverbs, folk songs, and humor. Learning to recognize **борщ**, **вареники**, **сало** on a menu or in conversation is not just vocabulary: it is your first step into Ukrainian cultural identity.

### Self-check

Test yourself — can you answer these without scrolling back?

- Як по-українськи "breakfast"? → **сніданок**
- Як по-українськи "lunch"? → **обід**
- Як по-українськи "dinner"? → **вечеря**
- Назви 5 овочів. → **картопля, морква, цибуля, помідор, огірок**
- Назви 3 напої. → **кава, чай, вода** (або **сік**, **компот**, **кефір**)
- Який традиційний український суп? → **борщ**
- Як сказати "tea with lemon"? → **чай з лимоном**
- Як сказати "sparkling water"? → **вода з газом**
- Яка українська страва з тіста і картоплі? → **вареники**
- Як по-українськи "drink" (noun)? → **напій**

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
