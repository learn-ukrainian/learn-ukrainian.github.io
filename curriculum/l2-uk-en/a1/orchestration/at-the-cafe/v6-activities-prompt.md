<!-- version: 1.0.0 | updated: 2026-03-27 -->
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

- `<!-- INJECT_ACTIVITY: fill-in-order -->`
- `<!-- INJECT_ACTIVITY: quiz-cafe-phrases -->`
- `<!-- INJECT_ACTIVITY: fill-in-dialogue -->`
- `<!-- INJECT_ACTIVITY: match-cafe-phrases -->`

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
## Діалоги (Dialogues)

Ростик and Іванка walk into a cozy **кафе** (café) on a quiet Lviv street. A waiter approaches their table with two leather-bound menus.

> **Офіціант:** Добрий день! Ось **меню**. *(Good day! Here's the menu.)*
> **Ростик:** Дякую. Що ви рекомендуєте? *(Thank you. What do you recommend?)*
> **Офіціант:** **Борщ** дуже **смачний**. *(The borshch is very tasty.)*
> **Ростик:** Добре, **мені борщ і хліб, будь ласка**. *(Good, borshch and bread for me, please.)*
> **Офіціант:** А що будете пити? *(And what will you drink?)*
> **Ростик:** **Каву з молоком**. *(Coffee with milk.)*
> **Іванка:** **Мені чай і тістечко, будь ласка**. *(Tea and a pastry for me, please.)*
> **Офіціант:** Добре, одну **хвилинку**. *(Good, one moment.)*

Notice the pattern: every order uses **мені** + the accusative form of the food or drink word. You practised accusative endings in M37 — now they're doing real work in a real café.

After the meal, Ростик signals the waiter.

> **Ростик:** **Рахунок, будь ласка**. *(The bill, please.)*
> **Офіціант:** Ось, **будь ласка**. Сто двадцять гривень. *(Here you go. One hundred twenty hryvnias.)*
> **Іванка:** **Можна карткою?** *(Can we pay by card?)*
> **Офіціант:** Так, звичайно. *(Yes, of course.)*
> **Ростик:** Все було дуже **смачно**! *(Everything was very delicious!)*
> **Ростик & Іванка:** **Дякуємо!** *(Thank you!)*
> **Офіціант:** Дякуємо, **приходьте** ще! *(Thank you, come again!)*

A **рахунок** (bill) in Ukraine doesn't come to your table automatically — you always ask for it. And **чайові** (tips)? About 10% is standard, but never obligatory.

Now test yourself — can you answer these questions from the dialogues?

- What did Ростик order? → **Мені борщ і каву з молоком.**
- What did Іванка order? → **Мені чай і тістечко.**
- How did they pay? → **Карткою** (by card).

## Як замовити (How to Order)

There are four polite ways to order at a Ukrainian **кафе**. Each one uses the accusative case — the same endings you learned in M37.

**Pattern 1: Мені [accusative], будь ласка.**
- **Мені каву, будь ласка.** — Coffee for me, please.
- **Мені борщ, будь ласка.** — Borshch for me, please.

**Pattern 2: Можна [accusative]?**
- **Можна воду?** — May I have water?
- **Можна хліб?** — May I have bread?

**Pattern 3: Дайте, будь ласка, [accusative].**
- **Дайте, будь ласка, салат.** — Give me a salad, please.
- **Дайте, будь ласка, сік.** — Give me juice, please.

**Pattern 4: Я буду [accusative].**
- **Я буду піцу.** — I'll have pizza.
- **Я буду суп.** — I'll have soup.

All four are polite. **Я буду** is slightly more casual — something you'd say to a friend working behind the counter. **Дайте, будь ласка** is the most formal.

Quick accusative reminder: masculine inanimate and neuter nouns keep their nominative form (**борщ** → **борщ**, **меню** → **меню**). Feminine nouns ending in **-а** change to **-у** (**кава** → **каву**, **вода** → **воду**, **піца** → **піцу**).

<!-- INJECT_ACTIVITY: fill-in-order -->

Once you've ordered, you might want to ask about the **меню**. Here are six essential phrases:

- **Що ви рекомендуєте?** — What do you recommend?
- **Це гостре?** — Is it spicy?
- **Це з м'ясом?** — Is it with meat?
- **А що це?** — What is this?
- **Скільки коштує?** — How much does it cost?
- **Є вегетаріанське меню?** — Is there a vegetarian menu?

Each question gets a real answer. Ask **Скільки коштує борщ?** and the waiter might say: **Борщ коштує вісімдесят гривень** (The borshch costs eighty hryvnias).

Try building questions from this mini-menu: **борщ** 80 грн, **піца** 150 грн, **кава** 45 грн. For example: **Скільки коштує кава?** — **Кава коштує сорок п'ять гривень.** The numbers connect back to what you learned in earlier modules.

<!-- INJECT_ACTIVITY: quiz-cafe-phrases -->

## Культура кафе (Cafe Culture)

Not every place with food is the same. Ukrainian has three distinct words for three distinct experiences:

| | **Кафе** | **Ресторан** | **Кав'ярня** |
|---|---|---|---|
| Style | Casual, drop-in | Formal, reservations | Coffee-focused |
| Menu | On a board or paper | Leather-bound, multi-page | Drinks + pastries |
| Price | Budget-friendly | Higher | Mid-range |

A **кафе** (café) is where you grab a quick **борщ** and **хліб** for lunch. A **ресторан** (restaurant) is where you celebrate a birthday with a white tablecloth. A **кав'ярня** (coffee shop) is where you spend two hours with a **кава** and a laptop. After Euromaidan in 2014, independent **кав'ярні** exploded across Ukrainian cities, becoming community hubs — places to meet, work, and organize.

When it's time to pay, remember: the **рахунок** (bill) does not come automatically in Ukraine. You say **Рахунок, будь ласка** when you're ready. **Чайові** (tips) are around 10% — common but never obligatory. Most people leave tips in cash even when paying by **картка** (card). Here are the key payment phrases:

- **Можна карткою?** — Can I pay by card?
- **Готівкою.** — In cash.
- **Залиште решту.** — Keep the change.
- **Дякуємо, все було смачно!** — Thank you, everything was delicious!

And here are six phrases for everyday café moments — from arriving to leaving:

- **Вільно?** / **Тут вільно?** — Is this seat free?
- **Можна меню?** — May I have the menu?
- **Ще одну каву, будь ласка.** — One more coffee, please.
- **Без цукру.** — Without sugar.
- **З лимоном.** — With lemon.
- **Все було дуже смачно!** — Everything was delicious!

Each phrase fits a micro-situation: you walk in (**Тут вільно?**), you browse (**Можна меню?**), you reorder (**Ще одну каву**), you customize (**Без цукру**), and you leave happy (**Все було дуже смачно!**).

<!-- INJECT_ACTIVITY: fill-in-dialogue -->

<!-- INJECT_ACTIVITY: match-cafe-phrases -->

## Підсумок — Summary

Here's your café communication toolkit — screenshot this for your next visit to a Ukrainian **кафе**:

| Situation | Phrase | Example |
|---|---|---|
| Order food | **Мені [acc], будь ласка** | Мені каву, будь ласка. |
| Ask about menu | **Скільки коштує?** | Скільки коштує борщ? |
| Request the bill | **Рахунок, будь ласка** | — |
| Pay by card | **Можна карткою?** | — |
| Compliment food | **Дуже смачно!** | Все було дуже смачно! |

Now put it all together. Imagine you walk into a Lviv **кав'ярня** with a friend. You need to: order a starter (**борщ**), a main (**салат**), a drink (**каву** або **сік**), ask about the price of one item, then ask for the bill and pay by card. Try it yourself before checking the model answers below:

- **Мені борщ, будь ласка.**
- **Мені салат і каву, будь ласка.**
- **Скільки коштує сік?**
- **Рахунок, будь ласка.**
- **Можна карткою?**

Ukrainian café culture carries a deeper meaning since 2022. Many Kyiv and Lviv **кав'ярні** stayed open through air-raid alerts, operating as volunteer coordination hubs. Ordering a **кава** in Ukraine today is a small act of normalcy in extraordinary times. As one Kyiv barista put it in 2023: **«Ми варимо каву — значить, ми живемо.»** (We brew coffee — that means we're alive.)

In the next module, you'll take your accusative skills from the **кафе** to the **ринок** (market). Same patterns, new vocabulary: **картопля** (potatoes), **яблука** (apples), **молоко** (milk). **Ходімо!** (Let's go!)

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

**Level: A1.4+ (Module 38/55) — BEGINNER**

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
