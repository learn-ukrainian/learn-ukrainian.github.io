<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/what-is-it-like.yaml` file for module **9: What Is It Like?** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-question-word -->`
- `<!-- INJECT_ACTIVITY: fill-in-adjective-endings -->`
- `<!-- INJECT_ACTIVITY: match-up-opposites -->`
- `<!-- INJECT_ACTIVITY: fill-in-room-description -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Add correct adjective ending: нов__ книга, велик__ стіл, чист__ вікно'
  items: 10
  type: fill-in
- focus: 'Match adjective opposites: великий ↔ маленький'
  items: 6
  type: match-up
- focus: Який/яка/яке? Choose correct question word.
  items: 6
  type: quiz
- focus: Describe the room using given nouns and adjectives
  items: 6
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- поганий (bad)
- брудний (dirty)
- світлий (light, bright)
- темний (dark)
- а (and/but — contrast)
- але (but)
required:
- який, яка, яке (what kind? — m/f/n)
- великий (big)
- маленький (small)
- новий (new)
- старий (old)
- гарний (nice, beautiful)
- чистий (clean)
- дорогий (expensive)
- дешевий (cheap)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

It is the weekend, and the city center is bustling with activity. We visit a local weekend book fair, a popular gathering place where vendors display an interesting assortment of printed materials, vintage goods, and cultural artifacts. People browse through the stalls, carefully looking at items like maps, books, and posters, often picking them up to appreciate the quality of the paper or the vibrancy of the ink. We join **Тарас** and **Софія** as they walk from table to table. They are examining the items on display and sharing their immediate impressions of what they see.

The book fair is an excellent place to practice our new descriptive skills because the objects are constantly changing. One table might have historical artifacts, while another has modern textbooks. As our friends walk, they point out specific details that catch their eye. Examine their conversation below.

As they stop at a large wooden stall, **Тарас** unrolls a massive poster while **Софія** picks up a thick, freshly printed volume and an antique photograph from a nearby stack.

> **Тарас:** Який великий плакат! *(What a big poster!)*
> **Софія:** А яка цікава книга! *(And what an interesting book!)*
> **Тарас:** Це новий атлас? *(Is this a new atlas?)*
> **Софія:** Так, новий атлас. А там — старе фото. *(Yes, a new atlas. And there — an old photo.)*
> **Тарас:** І маленька листівка. *(And a small postcard.)*

They are doing more than just naming objects; they are actively describing them, assigning qualities to the things they see. Notice how the ending of the describing word changes depending on whether the object is masculine, feminine, or neuter. Describing objects at a market is useful, but the most common place we describe things is in our own homes. When you invite a guest over, or when you are simply talking about your living space with a new friend, you naturally want to communicate what your environment looks like. Listen to another conversation. This time, **Софія** is describing her personal space to **Тарас**, focusing on the everyday furniture items we learned about previously. This is a classic situation found in the Вашуленко Grade 3 textbook under the topic "Моя кімната" (My room).

Listen to how **Софія** provides details about the size, age, and brightness of her room and the items inside it.

> **Тарас:** Яка твоя кімната? *(What is your room like?)*
> **Софія:** Моя кімната велика і світла. *(My room is big and bright.)*
> **Тарас:** А стіл? *(And the table?)*
> **Софія:** Стіл новий. А ліжко — старе. *(The table is new. And the bed is old.)*

Here, the description feels very natural. The questions and the answers both rely on matching the describing word to the object being discussed.

## Який? Яка? Яке? (What kind?)

To ask "What kind?" or "Which?" in English, you rely on fixed words that never change shape. In Ukrainian grammar, the reality is much more dynamic. A describing word is called a **прикметник** (adjective), a term that literally suggests it is a feature attached to an object. Its primary job is to tell you the qualities of a noun—its size, color, age, or value. However, you cannot simply memorize one single, unchanging word for "What kind?". Just as you learned that the word for "my" changes based on gender, strictly following the **мій**, **моя**, **моє** pattern, the question word for descriptions must also adapt to precisely match the noun it asks about. The question "What kind?" changes by gender exactly like the possessive pronouns do, acting as a mirror to the noun.

When you want to describe a masculine noun, you use the specific question word **який?** (what kind?). The answer to this question will typically be an adjective ending in the letters **-ий**. For example, if you are looking at a table, you ask **Який стіл?** (What kind of table?), and the accurate answer is **Великий стіл** (A big table) or **Новий атлас** (A new atlas). For feminine nouns, the entire system shifts to accommodate the feminine gender. The question word changes to **яка?**. Consequently, the describing word will end in the letter **-а**, giving you descriptive phrases like **Нова книга** (A new book) or **Велика листівка** (A big postcard).

Neuter nouns require their own specific grammatical form to maintain this harmony. To ask about a neuter object, you must use the question word **яке?**. Following the established logic, the adjective that directly answers this neuter question will end in the letter **-е**. If you point to a window, you ask **Яке вікно?** (What kind of window?), and the appropriate response is **Чисте вікно** (A clean window) or **Старе фото** (An old photo). Note that while some adjectives have soft-stem endings like **-ій**, **-я**, or **-є** (such as **синій**, which means dark blue), we will cover those exceptions in the next module about colors. For now, you must focus entirely on mastering the standard **-ий**, **-а**, **-е** pattern.

Practicing this skill requires active listening. When you hear a native speaker describe an object, pay close attention to the ending of the adjective. You will notice that the ending always matches the gender of the noun it is attached to. This consistency is what makes Ukrainian grammar so logical once you grasp the foundational rules. It might seem like a lot of variations at first, but with practice, this matching process will become second nature.

:::tip
According to the Пономарова Grade 3 textbook (p.98), the fundamental rule is that an adjective has the same gender as the noun. Think of the noun as the boss, and the adjective as the loyal assistant that must put on the matching uniform!
:::

This means the noun dictates the gender, and the adjective obediently copies it without exception. For masculine words, you will always use **-ий** (**великий**, **новий**, **чистий**). For feminine words, you will use **-а** (**велика**, **нова**, **чиста**). For neuter words, you will use **-е** (**велике**, **нове**, **чисте**). This pattern of agreement will reappear in every single grammatical case as you continue learning the language, so you must learn it well right now to build a strong foundation for future fluency.

<!-- INJECT_ACTIVITY: quiz-question-word -->

<!-- INJECT_ACTIVITY: fill-in-adjective-endings -->

## Прикметники (Common Adjectives)

One of the most effective strategies for expanding your descriptive vocabulary quickly is to learn adjectives in opposite pairs. Human memory thrives on contrast, making it much easier to remember two interconnected words together than trying to memorize them in isolation. Start with the primary size and age pairs. For physical size, we have the word **великий** (big) and its direct opposite **маленький** (small). For the age of objects, we pair **новий** (new) with **старий** (old). You can immediately apply these new adjectives to the vocabulary objects you already know, creating useful combinations like **великий стіл** (a big table), **маленька ручка** (a small pen), **новий телефон** (a new phone), and **старе фото** (an old photo).

Next, we expand the vocabulary set with quality and light pairs. To express whether something is visually pleasing, attractive, or generally good, use the adjective **гарний** (nice, beautiful). Its direct opposite is **поганий** (bad). For measuring physical cleanliness, pair **чистий** (clean) with **брудний** (dirty). When talking about the amount of natural or artificial light in a space, use **світлий** (light, bright) and **темний** (dark). These descriptive words are incredibly useful for everyday conversations. You might say to a friend that you have a **гарний день** (nice day), express a desire to drink **чиста вода** (clean water), or mention that you prefer to read a book in a **світла кімната** (bright room).

Consider how often you make judgments about the things around you. Every time you decide whether a shirt is clean or dirty, or whether a room is too dark to read in, you are using qualitative adjectives. Applying these new words to your immediate surroundings is the fastest way to memorize them. Look at your desk right now. Is your pen new or old? Is your coffee cup big or small? By constantly labeling your environment with these opposite pairs, you actively reinforce the vocabulary in your mind.

When you are out shopping or discussing the financial value of everyday items, you need a completely different set of descriptors. The word for an item that costs a significant amount of money is **дорогий** (expensive). The opposite descriptor, used for an item that is highly affordable, is **дешевий** (cheap). Imagine you are window shopping in the city center and looking closely at a storefront display filled with various goods.

> **Софія:** Яка гарна сумка! *(What a beautiful bag!)*
> **Тарас:** Так, але вона дорога. *(Yes, but it is expensive.)*
> **Софія:** А телефон? Який він? *(And the phone? What is it like?)*
> **Тарас:** Він великий і дешевий. *(It is big and cheap.)*

:::note
Notice the small connecting words used to build longer sentences. We use **і** (and) when two qualities exist in parallel harmony. We use **а** (and/but) to show a contrast between two different things.
:::

When building rich descriptions with the everyday objects you learned in the previous module, these tiny structural words are absolutely essential for fluency. By combining your known vocabulary, you can proudly say **У мене є великий стіл** (I have a big table). When explicitly linking parallel ideas, use **і**: **Вікно велике і чисте** (The window is big and clean). When highlighting a clear contrast, use **а**: **Стілець старий, а ліжко — нове** (The chair is old, and/but the bed is new). Finally, you can use **але** (but) for slightly unexpected or surprising combinations: **Моя кімната маленька, але гарна** (My room is small, but nice).

<!-- INJECT_ACTIVITY: match-up-opposites -->

<!-- INJECT_ACTIVITY: fill-in-room-description -->

## Підсумок — Summary

Describing your physical environment in Ukrainian requires paying close and constant attention to the nouns you are talking about. Every single describing word must perfectly match the grammatical gender of the noun it modifies. When you want to ask about the qualities of an object, your question word changes accordingly. For a masculine noun, you must ask **який?**, and the responding adjective will end in **-ий**, as seen in **великий**. For a feminine noun, the question logically shifts to **яка?**, leading to an adjective ending in **-а**, such as **велика**. For a neuter noun, you use **яке?**, and the adjective predictably takes the **-е** ending, exactly like **велике**. Remember that learning adjectives in direct contrasting pairs, such as pairing **новий** and **старий** or grouping **чистий** and **брудний**, makes vocabulary acquisition much more efficient and natural. Finally, when constructing your full sentences, use **і** to seamlessly connect matching parallel qualities, and use the contrastive conjunction **а** to boldly highlight the differences between two distinct items in your description.

The ability to accurately describe the world around you is a major milestone in your language journey. It moves you beyond simply pointing at objects and allows you to share your unique perspective and opinions. A table is no longer just a table; it is a big, new, clean table. A room is no longer just a room; it is a small but beautiful space. This descriptive power breathes life into your conversations and helps you connect with native speakers on a deeper level.

Verify your understanding of these core descriptive patterns before you proceed to the next lesson. Mastery of these concepts is essential for your progression. Can you confidently answer these practical self-check questions without hesitation?

*   Як буде "What kind of book?"
    *   **Яка книга?** (Because the word for book is feminine).
*   What ending does a masculine adjective have?
    *   Masculine adjectives typically end in **-ий** (or sometimes **-ій**).
*   What ending does a feminine adjective have?
    *   Feminine adjectives typically end in **-а** (or **-я**).
*   What ending does a neuter adjective have?
    *   Neuter adjectives typically end in **-е** (or **-є**).
*   Як сказати "The table is big, but the chair is small"?
    *   **Стіл великий, а стілець маленький.**

**Завдання** (Task): Describe your room in 3 sentences using adjectives. Look around your space and practice out loud right now. Make sure you correctly match the gender of the furniture items to the adjectives you choose.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: what-is-it-like
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

**Level: A1.2-A1.3 (Module 9/55) — EARLY BEGINNER**

The learner knows the alphabet and ~200 words. They:
- Can read Ukrainian slowly
- Know basic nouns, adjectives, simple verb forms
- Cannot handle complex sentences or grammar terminology in Ukrainian

**Instructions in simple English with Ukrainian key terms in bold.**
Example: 'Choose the correct form of **мій/моя/моє**'

**Good activity types:** quiz, fill-in (simple sentences), match-up, group-sort, true-false, observe, anagram, translate (English→Ukrainian), error-correction (simple), divide-words, count-syllables, odd-one-out, order.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

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

### Pattern: grammar-pluralization [§4.2.1.1]
**Множина іменників** (Noun plurals)
- **fill-in** — Утвори множину: Утворити множину іменника — закінчення -и vs -і залежно від приголосного / Form noun plural — -и vs -і endings depending on consonant
  - Instruction: *Напишіть множину*
- **group-sort** — Закінчення -и чи -і?: Розподілити іменники за типом закінчення множини / Sort nouns by plural ending type
  - Instruction: *Розподіліть*
- **match-up** — Однина → множина: Зіставити форму однини з формою множини / Match singular form to plural form
  - Instruction: *З'єднайте*
- **error-correction** — Виправ множину: Знайти неправильну форму множини та виправити / Find incorrect plural form and fix it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Множина — це словотворення. Учні мають продукувати форми, а не тільки вибирати
- ❌ fill-in-no-options: На A1 завжди давати варіанти — учень ще не знає всіх закінчень

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
