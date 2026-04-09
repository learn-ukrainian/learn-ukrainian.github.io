<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/holidays.yaml` file for module **46: Holidays** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-holiday-match -->`
- `<!-- INJECT_ACTIVITY: quiz-holiday-clues -->`
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
## Вступ: Що таке свято?

To truly understand a culture, you must understand how its people celebrate. The rhythm of the year is marked by special days that bring people together. In Ukrainian, a holiday is a **свято** (holiday). The plural form is **свята** (holidays). Ukrainians love to gather with family and friends around large tables, share traditional food, and sing songs that have been passed down for generations. 

We group our celebrations into three main categories. First, we have **релігійні свята** (religious holidays) like Christmas and Easter, which are deeply spiritual and rich in ancient traditions. Second, we have **традиційні свята** (traditional holidays) which often connect to the changing seasons and nature. Finally, we have **державні свята** (state holidays) which mark important historical days for the nation.

When a special day arrives, people want to express their joy. The verb for this action is **святкувати** (to celebrate), and to express good wishes we use **вітати** (to congratulate/greet). You will hear these words often. If you are not sure of the exact name of the occasion, you can always use the universal greeting. You simply say **Зі святом!** (Happy Holiday!). This short, polite phrase works for almost any festive occasion and instantly connects you to the Ukrainian soul.

## Діалоги: Говоримо про свята

Let us look at how people talk about these special days in real life. Our first conversation takes place during the winter season. Two friends are discussing their plans for Christmas. In 2023, Ukraine made a major historical shift in its calendar. The country officially moved the date of Christmas to December 25th. This change aligns Ukraine with the majority of Europe and the rest of the Christian world. It was a conscious decision to break away from the Russian Orthodox calendar, which celebrates on January 7th. Now, Ukrainians celebrate in the month of **грудень** (December).

> **Українська родина:** Коли в тебе Різдво? *(When is your Christmas?)*
> **Іноземний гість:** Двадцять п'ятого грудня. А в тебе? *(On the twenty-fifth of December. And yours?)*
> **Українська родина:** У нас теж! *(We also have it then!)*
> **Українська родина:** Раніше святкували сьомого січня. *(Earlier we celebrated on the seventh of January.)*
> **Українська родина:** Але тепер двадцять п'ятого. *(But now on the twenty-fifth.)*
> **Іноземний гість:** Що ви робите на Різдво? *(What do you do for Christmas?)*
> **Українська родина:** Ми співаємо колядки і їмо кутю. *(We sing carols and eat kutia.)*
> **Іноземний гість:** Як гарно! З Різдвом! *(How beautiful! Merry Christmas!)*
> **Українська родина:** З Різдвом Христовим! *(Merry Christmas!)*

Our second conversation happens in the city center during the summer. The date is August 24th, and the streets are full of people. They are celebrating the most important political day of the year. Notice the atmosphere of national pride in their exchange.

> **Оксана:** Двадцять четверте серпня! *(The twenty-fourth of August!)*
> **Марко:** День Незалежності! *(Independence Day!)*
> **Оксана:** Так, це головне державне свято України. *(Yes, it is the main state holiday of Ukraine.)*
> **Марко:** Що ви робите? *(What do you do?)*
> **Оксана:** Ми дивимося парад і ходимо на концерт. *(We watch the parade and go to the concert.)*
> **Марко:** А ввечері? *(And in the evening?)*
> **Оксана:** Ввечері салют. *(In the evening there are fireworks.)*
> **Оксана:** І святковий вечір з друзями. *(And a festive evening with friends.)*
> **Марко:** З Днем Незалежності! *(Happy Independence Day!)*
> **Оксана:** Слава Україні! *(Glory to Ukraine!)*

<!-- INJECT_ACTIVITY: quiz-holiday-match -->

## Українські свята: Традиції та символи

The winter cycle revolves around **Різдво** (Christmas). As we saw in the dialogue, this takes place on December 25th. The celebration actually begins the evening before. December 24th is known as **Свята вечеря** (Holy Supper). When the first star appears in the night sky, families sit down at the dining table. Tradition requires exactly **дванадцять страв** (twelve dishes). This number represents the twelve apostles. All the food on the table must be vegan, meaning no meat or dairy. 

The absolute most important and sacred dish is **кутя** (kutia). This is a sweet, ritual porridge made from whole wheat berries, poppy seeds, honey, and walnuts. It is always the very first food eaten at the meal, and everyone must have at least one spoonful. People also eat traditional **борщ** (borscht), **вареники** (dumplings), **риба** (fish), and drink **узвар** (dried fruit compote). 

:::note Calendar Alignment
In 2023, Ukraine moved its official celebration of Christmas from January 7th to December 25th. This historical change aligns the country with Europe and the broader Christian world, moving away from the Russian Orthodox calendar.
:::

After dinner, the singing begins. People sing **колядки** (carols). Groups of singers called **колядники** (carolers) walk from house to house in their neighborhoods. They carry a large, illuminated star and sing songs to wish the hosts wealth, health, and a good harvest. Inside the home, instead of a plastic tree, you might see a **дідух** (sheaf of wheat). This ancient symbol represents the ancestors and the agricultural harvest, and it predates the modern Christmas tree tradition.

The spring cycle centers entirely on **Великдень** (Easter). This is the absolute biggest religious celebration of the year in Ukraine. The exact date changes every spring according to the lunar calendar. During this time, Ukrainians create **писанки** (decorated eggs). A **писанка** (decorated egg) is a raw egg covered in intricate, symbolic geometric patterns using hot beeswax and vibrant dyes. It is a highly respected, unique Ukrainian art form. 

:::caution Name vs. Food
Do not confuse the holiday with the holiday food! The holiday itself is **Великдень** or **Пасха** (Easter). However, a **паска** (Easter bread) is the sweet bread you eat on that day. You celebrate **Великдень**, but you eat a **паска**.
:::

On Sunday morning, families wake up very early and go to church. They bring a woven basket filled with bread, eggs, salt, and meat to perform the ritual of **святити кошик** (blessing the basket).

When people meet on Easter Sunday, they do not say standard greetings like "hello" or "good morning". Instead, they use a special, joyful ritual greeting:
*   **Христос воскрес!** (Christ is risen!)
*   **Воістину воскрес!** (Indeed risen!)

<!-- INJECT_ACTIVITY: quiz-holiday-clues -->

## Державні свята: Громадянська ідентичність

State holidays reflect the modern history, struggles, and identity of the nation. The most significant of these is **День Незалежності** (Independence Day). On August 24, 1991, Ukraine officially declared its independence from the Soviet Union. Today, this is the ultimate **державне свято** (state holiday) for every Ukrainian citizen. 

Cities completely transform on this day. People gather in the streets and central squares to celebrate freedom and sovereignty. You will often see a large military **парад** (parade) in the capital city of Kyiv. There are massive public **концерти** (concerts) featuring popular musicians. The streets, balconies, and cars are decorated with thousands of blue and yellow **прапори** (flags). In the evening, the sky lights up with a **салют** (fireworks). To greet someone on this day, you simply say **З Днем Незалежності!** (Happy Independence Day!). You will also hear the patriotic exchange echoing everywhere: **Слава Україні!** (Glory to Ukraine!) and the proud response **Героям слава!** (Glory to the heroes!).

Beyond Independence Day, there are several other important dates to know. The absolute biggest secular celebration of the entire year is **Новий рік** (New Year) on January 1st. On New Year's Eve, families decorate a festive **ялинка** (tree) and exchange **подарунки** (gifts) at midnight. 

In the spring, Ukrainians celebrate a unique cultural event called **Вишиванковий день** (Vyshyvanka Day). This occurs annually on the third Thursday of May. It is a modern, living tradition rather than an official day off work. Everyone goes to school, the university, or the office wearing a **вишиванка** (embroidered shirt). This beautiful traditional garment serves as a powerful visual symbol of Ukrainian identity, unity, and cultural resistance.

Two other key dates mark the foundations of the modern state. On June 28th, the country observes **День Конституції** (Constitution Day), honoring the adoption of the nation's fundamental law. Later in the year, on October 1st, the people honor their military defenders on **День захисників і захисниць** (Defenders' Day). This solemn and important day pays respect to all the men and women who protect the nation's borders.

<!-- INJECT_ACTIVITY: group-sort-traditions -->

## Підсумок — Summary

Now that you know the major Ukrainian holidays, you need to know how to form the most common greetings. Ukrainian uses a very specific, consistent grammatical pattern for this. The formula relies on the preposition **з** (with) followed by the name of the holiday in the instrumental case. You literally wish someone well "with" the holiday.

You already know how the instrumental case works from phrases you learned earlier, like **кава з молоком** (coffee with milk). The spelling changes at the end of the words follow the exact same rules you learned for nouns. Here is how the names of the holidays transform in everyday speech:

*   **Новий рік** → **З Новим роком!** (Happy New Year!)
*   **Різдво** → **З Різдвом!** (Merry Christmas!)
*   **Великдень** → **З Великоднем!** (Happy Easter!)
*   **День народження** → **З днем народження!** (Happy birthday!)
*   **День Незалежності** → **З Днем Незалежності!** (Happy Independence Day!)

After the initial short greeting, people often add longer, specific wishes. The pattern for making a wish uses the verb **бажати** (to wish) followed by the genitive case. You can memorize this very common, polite sequence: **Бажаю щастя, здоров'я, миру** (I wish you happiness, health, peace). 

Let us review the quick calendar of major events to help you remember the timeline. In **грудень** (December) on the 25th, we celebrate **Різдво**. In **січень** (January) on the 1st, we celebrate the secular **Новий рік**. In the **весна** (spring), the date changes, but we always celebrate **Великдень**. Finally, in **серпень** (August) on the 24th, we celebrate **День Незалежності**.

:::tip Self-Check
How do you say "Merry Christmas"?
**З Різдвом!**

What is the ritual response to "Христос воскрес!"?
**Воістину воскрес!**

When is Christmas in Ukraine?
**Двадцять п'ятого грудня.**

How do you say "Happy New Year"?
**З Новим роком!**

How do you greet someone on August 24th?
**З Днем Незалежності!**
:::

<!-- INJECT_ACTIVITY: fill-in-greetings -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: holidays
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
