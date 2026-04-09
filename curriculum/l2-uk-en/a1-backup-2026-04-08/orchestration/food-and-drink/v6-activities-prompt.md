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

- `<!-- INJECT_ACTIVITY: fill-in-z-chunks -->`
- `<!-- INJECT_ACTIVITY: quiz-meals-dishes -->`
- `<!-- INJECT_ACTIVITY: match-food-drink -->`
- `<!-- INJECT_ACTIVITY: group-sort-food-drinks -->`

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

It's a weekday morning. Oksana and her roommate Daria are in the kitchen, deciding what to eat. In Ukrainian homes, breakfast is a ritual — every person has their go-to combination of food and drink, and they say it as a single phrase: **кава з молоком** (coffee with milk), **хліб з маслом** (bread with butter). Listen to how naturally these pairings flow.

> **Оксана:** Що ти хочеш на сніданок? *(What do you want for breakfast?)*
> **Дарія:** Каву з молоком і хліб з маслом. *(Coffee with milk and bread with butter.)*
> **Оксана:** А я хочу чай з цукром і кашу. *(And I want tea with sugar and porridge.)*
> **Дарія:** Кашу з молоком чи без? *(Porridge with milk or without?)*
> **Оксана:** З молоком, звичайно! *(With milk, of course!)*
> **Дарія:** Добре. Я теж хочу яйце. *(Good. I also want an egg.)*

The key words here: **кава** (coffee, f), **молоко** (milk, n), **хліб** (bread, m), **масло** (butter, n), **чай** (tea, m), **цукор** (sugar, m), **каша** (porridge, f), **яйце** (egg, n). Notice how Daria doesn't say "I want coffee, and then I want milk" — she says **каву з молоком** as one unit, like a single word. That's how Ukrainians order food.

Ukrainians eat three meals a day: **сніданок** (breakfast, m), **обід** (lunch, m), **вечеря** (dinner, f). Each meal has its own character — сніданок is light and quick, обід is the biggest meal, and вечеря is relaxed. The next dialogue shows how Ukrainians talk about обід and вечеря.

> **Марко:** Що ти зазвичай їси на обід? *(What do you usually eat for lunch?)*
> **Соломія:** Суп і салат. Іноді м'ясо з картоплею. *(Soup and salad. Sometimes meat with potatoes.)*
> **Марко:** Яке м'ясо ти любиш? *(What meat do you like?)*
> **Соломія:** Курку або рибу. А ти? *(Chicken or fish. And you?)*
> **Марко:** Я теж люблю рибу з рисом. *(I also like fish with rice.)*
> **Соломія:** А на вечерю? *(And for dinner?)*
> **Марко:** Зазвичай суп або омлет. *(Usually soup or an omelette.)*
> **Соломія:** А ти п'єш каву чи чай? *(Do you drink coffee or tea?)*
> **Марко:** Ввечері — чай з лимоном. *(In the evening — tea with lemon.)*

New vocabulary: **суп** (soup, m), **салат** (salad, m), **м'ясо** (meat, n), **картопля** (potato, f), **курка** (chicken, f), **риба** (fish, f), **рис** (rice, m), **лимон** (lemon, m). The word **зазвичай** means "usually" — it's how you talk about habits.

:::tip Chunk Pattern
Notice **кава з молоком**, **чай з цукром**, **риба з рисом** — all use the same pattern: **[food/drink] з [addition]**. Learn these as whole phrases for now, like single words. You'll learn the grammar reason behind the endings (-ом, -ою) in A2.
:::

<!-- INJECT_ACTIVITY: fill-in-z-chunks -->

## Їжа (Food)

Ukrainian food vocabulary falls into six clear categories. Once you know these groups, you can describe almost any meal. Think of them as your food toolkit — six drawers, each with essential items.

**Хліб і каша** (Bread and porridge): **хліб** (bread, m), **каша** (porridge, f), **рис** (rice, m), **макарони** (pasta, pl)
- «Я їм кашу щоранку.» — *I eat porridge every morning.*

**М'ясо і риба** (Meat and fish): **м'ясо** (meat, n), **курка** (chicken, f), **риба** (fish, f)
- «Вона їсть курку на обід.» — *She eats chicken for lunch.*

**Овочі** (Vegetables): **картопля** (potato, f), **морква** (carrot, f), **цибуля** (onion, f), **помідор** (tomato, m), **огірок** (cucumber, m)
- «Картопля — популярний овоч в Україні.» — *Potato is a popular vegetable in Ukraine.*

**Фрукти** (Fruit): **яблуко** (apple, n), **банан** (banana, m), **апельсин** (orange, m)
- «Він їсть яблуко щодня.» — *He eats an apple every day.*

**Молочне** (Dairy): **молоко** (milk, n), **сир** (cheese, m), **масло** (butter, n), **сметана** (sour cream, f), **йогурт** (yogurt, m)
- «Сметана — важливий продукт.» — *Sour cream is an important product.*

**Інше** (Other): **яйце** (egg, n), **цукор** (sugar, m), **сіль** (salt, f), **олія** (oil, f)
- «Без солі їжа несмачна.» — *Without salt, food is tasteless.*

### Ukrainian iconic dishes

These four dishes are not just vocabulary — they are cultural identity. When a Ukrainian hears a foreigner name these dishes correctly, it signals respect.

**Борщ** (m) — Ukraine's national soup, made with **буряк** (beetroot), **картопля**, **капуста** (cabbage), **м'ясо**, **морква**, **цибуля**, and always served with a spoonful of **сметана**. Ukrainian Grade 1 textbooks already teach children to name its ingredients: «Вибери продукти для борщу.» Борщ is a symbol of home.

:::note Cultural Identity
Борщ is Ukrainian — not "Eastern European" and not Russian. In 2022, UNESCO recognized Ukrainian borshch culture as intangible cultural heritage. When you say **борщ**, you say something deeply Ukrainian.
:::

**Вареники** (pl, **вареник** m) — filled dumplings made from **тісто** (dough), stuffed with **картопля і сир** or cherries. Always eaten with **сметана**. As the textbook says: «Вареники в українській культурі — символ заможного, щасливого життя.» They are a symbol of a prosperous, happy life.

**Сало** (n) — cured pork fat, eaten with **хліб**. Iconic, deeply embedded in Ukrainian cultural humor and everyday life. If you want to make a Ukrainian smile, mention **сало з хлібом**.

**Деруни** (pl) — potato pancakes made from grated **картопля**, often served with **сметана**.

Now imagine a real kitchen moment — **Бабуся** (grandma) teaching her **онучка** (granddaughter) to make борщ:

> **Бабуся:** Давай варити борщ. Буряк, картопля, капуста... *(Let's make borshch. Beetroot, potato, cabbage...)*
> **Онучка:** А м'ясо? *(And meat?)*
> **Бабуся:** Так! І морква, цибуля, сметана. *(Yes! And carrot, onion, sour cream.)*

<!-- INJECT_ACTIVITY: quiz-meals-dishes -->

## Напої (Drinks)

Ukrainian drinks split into four groups: **гарячі** (hot), **холодні** (cold), **молочні** (dairy), and **алкогольні** (alcoholic — for recognition only). At a Ukrainian table, you will always find **чай**, **кава**, **компот**, or **вода**.

**Гарячі** (Hot): **кава** (coffee, f), **чай** (tea, m)
- «Я п'ю каву вранці, чай ввечері.» — *I drink coffee in the morning, tea in the evening.*

**Холодні** (Cold): **вода** (water, f), **сік** (juice, m), **компот** (compote, m) <!-- A2-word -->, **лимонад** (lemonade, m)
- «Компот — домашній напій з фруктів.» — *Compote is a homemade drink from fruit.*

**Молочні** (Dairy): **молоко** (milk, n), **кефір** (kefir, m)
- «Кефір корисний для здоров'я.» — *Kefir is good for health.*

**Алкогольні** (Alcoholic — recognition only): **пиво** (beer, n), **вино** (wine, n)

:::caution Компот ≠ Western Compote
Ukrainian **компот** is not the thick fruit stew you might know. It's a drink — fruit boiled in water with sugar, then served warm or cold. Every Ukrainian grandmother makes it. You'll find it in school canteens, at home, and at celebrations. It's closer to fruit punch than to jam.
:::

### The з + noun pattern — chunks, not grammar

When you say **кава з молоком**, the word **молоком** ends in **-ом**. When you say **чай з лимоном**, the word **лимоном** ends in **-ом**. When you say **вода з газом**, the word **газом** ends in **-ом**. This ending comes from the instrumental case — a grammar concept you will study properly in A2.

For now, treat these as memorized phrases, like single words. Say **кавазмолоком** as one chunk. You don't need to know WHY **молоко** becomes **молоком** — just remember the whole phrase. Ukrainian Grade 1 textbooks use exactly this approach: «Тато пив чай із пиріжками. Мама пила чай із печивом.» Children memorize the whole phrase first, grammar comes later.

Your chunk list to memorize:

- **кава з молоком** — coffee with milk
- **чай з цукром** — tea with sugar
- **чай з лимоном** — tea with lemon
- **вода з газом** — sparkling water (lit. water with gas)
- **хліб з маслом** — bread with butter
- **м'ясо з картоплею** — meat with potatoes
- **риба з рисом** — fish with rice

### Reading Practice

Read each sentence aloud. What does each person drink?

1. «Я п'ю каву з молоком щоранку.» — *I drink coffee with milk every morning.*
2. «Вона любить чай з лимоном.» — *She likes tea with lemon.*
3. «Діти п'ють компот або воду.» — *Children drink compote or water.*
4. «Він не п'є каву — тільки чай.» — *He doesn't drink coffee — only tea.*
5. «На столі є сік, вода і кефір.» — *On the table there is juice, water, and kefir.*

Now try: what do YOU drink in the morning? And in the evening?

<!-- INJECT_ACTIVITY: match-food-drink -->

<!-- INJECT_ACTIVITY: group-sort-food-drinks -->

## Підсумок — Summary

Two question patterns cover almost any food conversation at A1:

- «Що ти хочеш?» → **Каву з молоком.** / **Хліб з маслом.** / **Суп і салат.**
- «Що ти їси на сніданок / обід / вечерю?» → **На сніданок — кашу і чай.** **На обід — суп.** **На вечерю — рибу з рисом.**

Practice saying these aloud — swap in your own favorite foods from the vocabulary above.

### Three meals — quick reference

| Час | Прийом їжі | Що типово їдять |
|-----|-----------|----------------|
| Вранці | **сніданок** | каша, яйце, хліб, кава/чай |
| Вдень | **обід** | суп, м'ясо, салат, сік/вода |
| Ввечері | **вечеря** | риба, омлет, сир, чай |

The time words **вранці** (in the morning), **вдень** (during the day), **ввечері** (in the evening) appeared throughout both dialogues. Now they are connected to the three meals. When someone asks «Що ти їси вранці?», you know they mean **сніданок**.

:::tip Your Cultural Passport
A learner who knows **борщ**, **вареники**, **сало**, **деруни** is not just vocabulary-trained — they carry a signal of respect. Every Ukrainian who hears a foreigner name these dishes correctly will respond warmly. Quick summary: **борщ** = буряк + картопля + сметана. **Вареники** = тісто + картопля або сир. **Сало** = свинина + хліб. **Деруни** = картопля + сметана.
:::

### Self-check

Before moving on, test yourself:

- Can you name 5 foods? (e.g., **хліб**, **м'ясо**, **риба**, **картопля**, **яйце**)
- Can you name 3 drinks? (e.g., **кава**, **чай**, **вода**)
- Can you say what you eat at each meal? → «На сніданок я їм...» / «На обід я їм...» / «На вечерю я їм...»
- Can you say one **з + noun** chunk from memory? (**кава з молоком** / **чай з цукром**)
- Can you name one Ukrainian dish and one ingredient it contains? (e.g., **борщ** — **буряк**)

If you answered yes to all five — you have a solid food and drink toolkit in Ukrainian. Next up: **M37 — I Eat, I Drink**, where you'll learn the full present tense conjugation of **їсти** (to eat) and **пити** (to drink).

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
