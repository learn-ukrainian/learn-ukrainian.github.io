<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-food-shopping.yaml` file for module **41: Checkpoint: Food and Shopping** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-accusative-check -->`
- `<!-- INJECT_ACTIVITY: fill-in-cafe-market -->`
- `<!-- INJECT_ACTIVITY: group-sort-accusative -->`
- `<!-- INJECT_ACTIVITY: quiz-shopping-cafe -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Accusative check: choose correct form for inanimate AND animate nouns'
  items:
  - options:
    - салат
    - салата
    - салату
    question: Я їм ___.
  - options:
    - брата
    - брат
    - брату
    question: Я бачу ___.
  - options:
    - воду
    - вода
    - води
    question: Я п'ю ___.
  - options:
    - Олену
    - Олена
    - Олени
    question: Я знаю ___.
  - options:
    - борщ
    - борща
    - борщу
    question: Я люблю ___.
  - options:
    - друга
    - друг
    - другу
    question: Я чекаю ___.
  - options:
    - хліб
    - хліба
    - хлібу
    question: Я купую ___.
  - options:
    - лікаря
    - лікар
    - лікарю
    question: Я бачу ___.
  - options:
    - піцу
    - піца
    - піци
    question: Я їм ___.
  - options:
    - маму
    - мама
    - мами
    question: Я люблю ___.
  type: quiz
- focus: Complete the cafe + market dialogue with correct forms
  items:
  - — Що ти їш на сніданок? — Я їм {кашу|каша|каші} і п'ю каву.
  - — Потім іду на ринок. Скільки {коштують|коштує|коштувати} помідори?
  - — Тридцять {гривень|гривні|гривня}.
  - — Дайте {кілограм|літр|пляшку} яблук, будь ласка.
  - '— Потім у кафе: {Мені|Я|Меня} борщ і воду, будь ласка.'
  - — Рахунок, будь ласка. Можна {карткою|картка|картки}?
  - — О, я бачу {Олену|Олена|Олени}! Олено, привіт!
  - — Ти знаєш мого {брата|брат|братом}?
  type: fill-in
- focus: 'Sort accusative forms: inanimate (що?) vs animate (кого?)'
  groups:
  - items:
    - борщ
    - хліб
    - сік
    - чай
    - сир
    name: Inanimate (що?)
  - items:
    - брата
    - лікаря
    - сусіда
    - друга
    - вчителя
    name: Animate (кого?)
  type: group-sort
- focus: What do you say? Match shopping/cafe situations to correct phrases
  items:
  - options:
    - Мені каву, будь ласка.
    - Скільки коштує?
    - Тут вільно?
    question: 'You want to order coffee:'
  - options:
    - Скільки коштує?
    - Можна карткою?
    - Що ви рекомендуєте?
    question: 'You ask for the price:'
  - options:
    - Можна карткою?
    - Рахунок, будь ласка.
    - Дорого!
    question: 'You want to pay with a card:'
  - options:
    - Рахунок, будь ласка.
    - Мені борщ.
    - Все було дуже смачно!
    question: 'You ask for the bill:'
  - options:
    - Дайте кілограм яблук.
    - Скільки коштує?
    - Можна меню?
    question: 'You ask for 1 kg of apples:'
  - options:
    - Дорого!
    - Дешево!
    - Нормальна ціна.
    question: 'You think the price is high:'
  - options:
    - Тут вільно?
    - Можна меню?
    - Рахунок, будь ласка.
    question: 'You ask if a seat is free:'
  - options:
    - Все було дуже смачно!
    - Можна карткою?
    - Це гостре?
    question: 'You compliment the food:'
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended: []
required: []


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Що ми знаємо? (What Do We Know?)

Welcome to the checkpoint module for phase A1.6. This is where we pause to review and consolidate your knowledge. A1.6 covered five essential topics. Let's see what you can do! Can you comfortably perform these tasks in Ukrainian?

- [x] Name 10 foods and 5 drinks (М36)
- [x] Say what you eat and drink using the accusative case (М37)
- [x] Order food and drinks at a café (М38)
- [x] Ask for prices and buy things at a market (М39)
- [x] Use the accusative case for people (М40)

Here is a quick vocabulary warm-up. Cover the English words below. Can you recall 10 foods and 5 drinks in Ukrainian without looking? Then you are ready.

**Їжа** (food): **борщ** (borscht), **вареники** (dumplings), **салат** (salad), **хліб** (bread), **сир** (cheese), **піца** (pizza), **каша** (porridge), **яєчня** (fried eggs), **суп** (soup), **котлета** (cutlet).
**Напої** (drinks): **кава** (coffee), **чай** (tea), **вода** (water), **сік** (juice), **молоко** (milk).

Let's do a quick grammar warm-up. Check if these four patterns feel completely natural to you:
1. Я їм ___: **борщ** (borscht) → **борщ**, **салат** (salad) → **салат**, **суп** (soup) → **суп**.
2. Я п'ю ___: **кава** (coffee) → **каву**, **вода** (water) → **воду**, **сік** (juice) → **сік**.
3. Мені ___, будь ласка: **піца** (pizza) → **піцу**, **кава** (coffee) → **каву**.
4. Я бачу ___: **Олена** (Olena) → **Олену**, **брат** (brother) → **брата**, **друг** (friend) → **друга**.

If all four feel natural, you are in a great place. If not, revisit modules M37 and M40. Let's test your knowledge!

<!-- INJECT_ACTIVITY: quiz-accusative-check -->

## Читання (Reading Practice)

Read about Anna's day. Notice how she uses the accusative case for food, drinks, and people. Try to find at least six accusative forms as you read.

**День Анни** (Anna's Day)
Анна прокидається. Вона їсть **кашу** (porridge) і п'є **каву з молоком** (coffee with milk) на сніданок. Потім вона іде на **ринок** (market).
— Скільки коштують помідори?
— Тридцять гривень кілограм.
— Дайте кілограм, будь ласка.
Анна купує **хліб** (bread), **сир** (cheese), **яблука** (apples), і **салат** (salad).

Потім вона іде в **кафе** (café).
— Тут вільно?
— Так, сідайте.
— Мені **борщ** (borscht) і **воду** (water), будь ласка.
Раптом вона бачить подругу:
— О, я бачу **Олену** (Olena)! Олено, привіт!
Олена підходить до неї. Анна каже:
— Ти знаєш мого **брата Михайла** (brother Mykhailo)? Це мій брат.
Вони обідають разом.
— Рахунок, будь ласка. Можна карткою?
— Звичайно.

Check your understanding. Answer these three questions using full Ukrainian sentences. Try to answer them aloud before moving on.
1. Що Анна купує на ринку?
2. Що вона замовляє в кафе?
3. Кого вона бачить у кафе?

<!-- INJECT_ACTIVITY: fill-in-cafe-market -->

## Граматика (Grammar Summary)

**Шість ключових шаблонів A1.6**
You learned all of these patterns in modules M36 through M40. Here is a quick-reference summary so you have everything in one place.

**Pattern 1: Food and drink vocabulary chunks**
You know words for **їжа** (food), **напої** (drinks), and meals: **сніданок** (breakfast), **обід** (lunch), **вечеря** (dinner).
Notice how we group words using the instrumental case to say "with": **кава з молоком** (coffee with milk), **борщ зі сметаною** (borscht with sour cream), **хліб із сиром** (bread with cheese).
- Я їм кашу на сніданок. (I eat porridge for breakfast.)
- Я п'ю каву з молоком. (I drink coffee with milk.)

**Pattern 2: Accusative case for inanimate nouns**
When an object receives an action (like being eaten, bought, or ordered), its ending changes. Masculine inanimate nouns do not change. They look exactly like their dictionary forms: **борщ** → **борщ**, **хліб** → **хліб**, **сік** → **сік**. Feminine nouns ending in -а/-я change to -у/-ю: **кава** → **каву**, **вода** → **воду**, **піца** → **піцу**, **яєчня** → **яєчню**.

| Nominative (Що це?) | Accusative (Що ти їш?) | Example Sentence |
|---|---|---|
| **вода** (water) | **воду** | Я п'ю **воду**. (I am drinking water.) |
| **піца** (pizza) | **піцу** | Я їм **піцу**. (I am eating pizza.) |
| **суп** (soup) | **суп** | Я замовляю **суп**. (I am ordering soup.) |
| **каша** (porridge) | **кашу** | Я їм **кашу**. (I am eating porridge.) |

**Pattern 3: Ordering and prices**
You can navigate a café and a market using these fixed phrases. Note how they build on the vocabulary you already know:
- **Мені ___, будь ласка.** (To me ___, please. / I'll have ___, please.)
- **Скільки коштує?** (How much does it cost?)
- **Скільки коштують помідори?** (How much do the tomatoes cost?)
- **Дайте ___, будь ласка.** (Give [me] ___, please.)
- **Рахунок, будь ласка.** (The bill, please.)
- **Можна карткою?** (Can I pay by card?)

Remember the currency forms depending on the number: **одна гривня** (1), **дві гривні** (2), **п'ять гривень** (5+). Always use the soft declension for money.

**Pattern 4: Accusative case for animate nouns**
When a person is the object of an action (whom you see or know), the rules differ. Feminine animate nouns follow the same rule as inanimate: **Олена** → **Олену**, **мама** → **маму**. Masculine animate nouns take the genitive ending (-а/-я): **брат** → **брата**, **лікар** → **лікаря**, **друг** → **друга**, **вчитель** → **вчителя**.

Compare these two sentences. One uses an inanimate object, and the other uses an animate object:
- Я бачу **борщ**. (I see the borscht. — inanimate, masculine, no change)
- Я бачу **брата**. (I see the brother. — animate, masculine, ends in -а)

<!-- INJECT_ACTIVITY: group-sort-accusative -->

## Діалог (Connected Dialogue)

Наталя та Дмитро починають день. Читайте і стежте за відмінками. (Natalia and Dmytro start their day. Read and watch the cases.)

**(Сніданок / Breakfast)**
> **Наталя:** Що ти їш на сніданок? *(What are you eating for breakfast?)*
> **Дмитро:** Я їм кашу і п'ю каву з молоком. А ти? *(I am eating porridge and drinking coffee with milk. And you?)*
> **Наталя:** Я їм яєчню і хліб із сиром. *(I am eating fried eggs and bread with cheese.)*

**(На ринку / At the market)**
> **Наталя:** Скільки коштують помідори? *(How much do the tomatoes cost?)*
> **Продавець:** П'ятнадцять гривень кілограм. *(Fifteen hryvnias a kilo.)*
> **Наталя:** Дорого! А яблука? *(Expensive! And the apples?)*
> **Продавець:** Двадцять гривень. Дуже смачні! *(Twenty hryvnias. Very tasty!)*
> **Наталя:** Добре, дайте кілограм яблук, будь ласка. *(Okay, give me a kilo of apples, please.)*

**(У кафе / At the café)**
> **Дмитро:** Тут вільно? *(Is it free here?)*
> **Офіціант:** Так, сідайте! *(Yes, sit down!)*
> **Дмитро:** Мені борщ і воду, будь ласка. *(I'll have borscht and water, please.)*
> **Наталя:** О, я бачу Олену! Олено, привіт! Ти знаєш мого брата Дмитра? *(Oh, I see Olena! Olena, hi! Do you know my brother Dmytro?)*
> **Олена:** Ні, не знаю. Дуже приємно, Дмитре! *(No, I don't. Very nice to meet you, Dmytro!)*
> **Дмитро:** Рахунок, будь ласка. Можна карткою? *(The bill, please. Can I pay by card?)*
> **Офіціант:** Звичайно. *(Of course.)*
> **Наталя:** Все було дуже смачно! *(Everything was very tasty!)*

Did you spot all the key grammar patterns in the dialogue? Let's highlight a few:
1. Accusative inanimate nouns: **кашу**, **яєчню**, **воду**, **борщ**.
2. Accusative animate nouns: **Олену**, **брата Дмитра**.
3. Everyday café and market phrases: **Мені борщ**, **Дайте кілограм**, **Рахунок, будь ласка**.

<!-- INJECT_ACTIVITY: quiz-shopping-cafe -->

## Підсумок — Summary

You have successfully completed phase A1.6 — Food and Shopping. You have expanded your vocabulary and grammar significantly. Here is exactly what you can now do in Ukrainian:

- ✓ Talk about **їжа та напої** (food and drinks) and meals (М36).
- ✓ Use the accusative case for inanimate nouns to describe what you eat and drink: **борщ**, **каву**, **воду**, **піцу** (М37).
- ✓ Order at a **кафе** (café) with confidence: «Мені борщ, будь ласка» / «Рахунок, будь ласка» / «Можна карткою?» (М38).
- ✓ Shop at the **ринок** (market): «Скільки коштує?» / «Дайте кілограм» / **гривня**, **гривні**, **гривень** (М39).
- ✓ Use the accusative case for animate nouns to talk about people: «Я бачу Олену» / «Я знаю брата» (М40).

**Наступний крок — A1.7: Спілкування.** (Next step — A1.7: Communication.) You will learn to make plans, write messages, and talk on the phone. Ukrainian is becoming your language, step by step!

## Підсумок

This section serves as your final self-check for the module. Take a moment to review all the material covered in A1.6. Can you confidently form sentences using both animate and inanimate accusative nouns? Can you comfortably ask for the bill, order your favorite dish, and buy groceries? Do you remember the difference between **гривня**, **гривні**, and **гривень**? If you feel confident in these areas, you are ready to move forward. Keep practicing these phrases in your daily life, and you will continue to build fluency!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-food-shopping
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

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: examples[], prompt
- **classify**: Multi-category sort. Required: instruction, categories[{label, items[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: prompt. Optional: min_words, model_answer, evaluation_criteria[]
- **reading**: Required: passage, questions[]
- **source-evaluation**: Required: source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A1.4+ (Module 41/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-cases
- **fill-in** — Який відмінок?: Fill in the correct case ending for a noun in context
  - Instruction: *Вставте іменник у правильній формі*
- **quiz** — Визнач відмінок: Identify which case a highlighted noun is in
- **group-sort** — Розподіли за відмінками: Sort noun forms by their case
- **error-correction** — Знайди помилку у відмінку: Find wrong case ending and correct it

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
