<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/please-do-this.yaml` file for module **43: Please Do This** (a1).

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

- `<!-- INJECT_ACTIVITY: group-sort-imperative-register -->`
- `<!-- INJECT_ACTIVITY: fill-in-imperative-formation -->`
- `<!-- INJECT_ACTIVITY: quiz-polite-choice -->`
- `<!-- INJECT_ACTIVITY: fill-in-contextual-names -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Form imperative: читати → читай / читайте, писати → пиши / пишіть'
  items: 10
  type: fill-in
- focus: 'Choose correct: ___, будь ласка! (дай / даєш / дати)'
  items: 8
  type: quiz
- focus: 'Sort: ти-forms vs ви-forms (читай vs читайте, дай vs дайте)'
  items: 10
  type: group-sort
- focus: 'Complete: Олено, ___ книжку! Пане Іване, ___ книжку! (дай/дайте)'
  items: 6
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- відкрити (to open)
- сісти (to sit down)
- показати (to show)
- запитати (to ask)
- підручник (textbook, m)
- сторінка (page, f)
- речення (sentence, n)
required:
- читати (to read)
- писати (to write)
- слухати (to listen)
- дивитися (to look/watch)
- говорити (to speak)
- дати (to give)
- сказати (to say/tell)
- іти (to go)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Every day, we ask people to do things. We ask friends for favors, teachers give instructions to students, and parents guide their children. In Ukrainian, the way you ask someone to do something depends entirely on your relationship with that person. The words you choose signal whether you are talking to a close friend or addressing a group in a formal setting.

Imagine a typical morning in a language class. The teacher is standing at the front, addressing the entire group of students and guiding them through the lesson. Notice the specific endings on the action words the teacher uses to give instructions to the class.

> **Вчитель:** Добрий ранок! **Відкрийте підручники, будь ласка. Читайте текст.** *(Good morning! Open the textbooks, please. Read the text.)*
> **Студент:** Вибачте, яку сторінку? *(Excuse me, which page?)*
> **Вчитель:** Сторінку двадцять три. Тепер **пишіть**. **Напишіть три речення.** *(Page twenty-three. Now write. Write three sentences.)*
> **Студент:** Можна запитати? *(May I ask?)*
> **Вчитель:** Так, **запитуйте**, якщо є питання! *(Yes, ask, if there are questions!)*

In this classroom setting, the teacher uses forms like **відкрийте** (open), **читайте** (read), and **пишіть** (write). Because the teacher is speaking to a group of students, they must use the plural form. These forms end in **-те** or **-іть**, which always signals that you are addressing more than one person, or addressing someone formally using the respectful "you" pronoun.

Consider a completely different situation. Two close friends are walking outside on a beautiful day, trying to decide what to do next. The tone is much more relaxed and direct because they know each other well.

> **Олег:** **Слухай**, ходімо в кафе! *(Listen, let's go to a café!)*
> **Максим:** Добре, **йди**, я зараз. *(Okay, go, I'll be right there.)*
> **Олег:** **Подивись**, яка гарна погода! *(Look, what beautiful weather!)*
> **Максим:** Так! **Сідай** тут. *(Yes! Sit down here.)*
> **Олег:** **Дай** мені меню, будь ласка. *(Give me the menu, please.)*
> **Максим:** Ось, **дивись**. **Скажи**, що ти хочеш? *(Here, look. Tell me, what do you want?)*
> **Олег:** Я хочу каву. *(I want coffee.)*

Between friends, the language is quick and informal. Oleg and Maksym use words like **слухай** (listen), **подивись** (look), **дай** (give), and **скажи** (tell). There are no **-те** endings here because they are speaking to each other one-on-one using the informal "you". The grammatical goal is exactly the same as in the classroom — asking someone to act — but the register changes the shape of the verb completely.

## Наказовий спосіб (The Imperative Mood)

In Ukrainian grammar, this way of speaking is called the **наказовий спосіб** (imperative mood). It is the essential tool for everyday commands, requests, invitations, and warnings. For example, consider a volleyball practice where the coach gives rapid warm-up instructions to the players.

> **Тренер:** **Принеси м'яч! Розстав конуси!** *(Bring the ball! Set up the cones!)*
> **Гравці:** Добре! *(Okay!)*
> **Тренер:** **Натягни сітку! Поклади рушники на лавку! Відкрий двері!** *(Tighten the net! Put the towels on the bench! Open the doors!)*

Whether you are instructing athletes, inviting a guest to sit, or asking a barista for a napkin, you are using this exact grammatical structure.

The most important rule about the **наказовий спосіб** is register awareness. Because Ukrainian distinguishes between the informal singular **ти** (you) and the formal or plural **ви** (you), your commands must match the pronoun you would naturally use for that person. If you are talking to someone you call **ти**, you use the short informal command. If you are addressing a group of people, or someone you address respectfully as **ви**, you must use the formal command form. Mixing these up can sound confusing or inappropriately overly familiar.

:::tip
When you are unsure which form to use, think about the pronoun. If you would call the person **ви**, always use the **-те** or **-іть** ending on the verb. If you would call them **ти**, use the shorter form.
:::

Many English speakers worry that giving a direct command sounds abrupt. In Ukrainian, direct imperatives are completely normal and natural in daily speech. Saying **Читай!** (Read!) is not inherently aggressive; it is simply how teachers, parents, and friends communicate. However, if you want to ensure your request is perfectly polite, simply add the magic phrase **будь ласка** (please). Adding **будь ласка** instantly transforms any direct command into a standard, polite request.

*   **Дай!** (Give!) becomes **Дай, будь ласка.** (Please give.)
*   **Скажіть!** (Say/Tell! — formal) becomes **Скажіть, будь ласка.** (Please tell.)

Another excellent way to soften a request and make it sound friendly or respectful is by using the person's name or title. When you call out to someone, you use the vocative case for their name. Combining this with the imperative mood creates a warm, natural sentence.

*   **Олено, читай, будь ласка.** (Olena, please read.)
*   **Пане Іване, читайте, будь ласка.** (Mr. Ivan, please read.)

<!-- INJECT_ACTIVITY: group-sort-imperative-register -->

## Як утворити? (How to Form It)

To create the informal **ти** form, we look at the verb's infinitive. For many common verbs belonging to Group I that end in **-ати**, the rule is wonderfully simple. You remove the **-ти** ending to find the stem, and then you add the letter **-й**. This creates a crisp, one- or two-syllable command.

*   **читати** (to read) → **читай** (read!)
*   **слухати** (to listen) → **слухай** (listen!)
*   **співати** (to sing) → **співай** (sing!)
*   **писати** (to write) → **пиши** (write!)

For verbs in Group II, which often end in **-ити**, the process is slightly different. Instead of adding a completely new sound, you usually drop the final infinitive ending and are left with a stem ending in **-и**. The stress often plays a key role here, landing clearly on that final vowel to give the command its punchy rhythm.

*   **говорити** (to speak) → **говори** (speak!)
*   **ходити** (to go/walk) → **ходи** (go!)
*   **сидіти** (to sit) → **сиди** (sit!)
*   **дивитися** (to look) → **дивись** (look!)

Because the imperative is used so frequently in real life, some of the most essential verbs have irregular or slightly shortened forms that every A1 learner needs. These are words you will hear constantly, so it is best to simply memorize them as core vocabulary items. Notice how short and direct they are.

*   **дати** (to give) → **дай** (give!)
*   **сказати** (to say/tell) → **скажи** (tell!)
*   **їсти** (to eat) → **їж** (eat!)
*   **іти** (to go) → **іди** (go!)
*   **відкрити** (to open) → **відкрий** (open!)

:::caution
Be careful with the word **сказати** (to say). The informal command is **скажи**, not "сказай". Many high-frequency verbs have these slight irregularities, so it is best to memorize them early.
:::

Once you know the informal **ти** form, creating the formal or plural **ви** form for all verbs is incredibly easy. There is a universal rule: you simply take the **ти** form and add the suffix **-те**. If the informal form ends in the vowel **-и**, the spelling sometimes shifts slightly to **-іть** to accommodate the stress, but the concept remains exactly the same.

*   **читай** + **те** = **читайте** (read! — formal/plural)
*   **говори** + **те** = **говоріть** (speak! — formal/plural)
*   **дай** + **те** = **дайте** (give! — formal/plural)
*   **пиши** + **те** = **пишіть** (write! — formal/plural)

<!-- INJECT_ACTIVITY: fill-in-imperative-formation -->
<!-- INJECT_ACTIVITY: quiz-polite-choice -->

## Підсумок — Summary

Mastering the **наказовий спосіб** unlocks your ability to actively participate in Ukrainian life. You can now ask for help, offer things to friends, and follow directions in a classroom. To help you memorize the most critical patterns, here is a comprehensive table of the essential imperatives for daily life. Review these forms until they become a natural reflex.

| Infinitive | Ти | Ви | Meaning |
| :--- | :--- | :--- | :--- |
| **читати** | **читай** | **читайте** | read |
| **писати** | **пиши** | **пишіть** | write |
| **слухати** | **слухай** | **слухайте** | listen |
| **дивитися** | **дивись** | **дивіться** | look |
| **говорити** | **говори** | **говоріть** | speak |
| **іти** | **іди** | **ідіть** | go |
| **дати** | **дай** | **дайте** | give |
| **сказати** | **скажи** | **скажіть** | say/tell |
| **сісти** | **сядь** | **сядьте** | sit down |
| **відкрити** | **відкрий** | **відкрийте** | open |

This table covers the most frequent actions you will need to request or instruct others to perform. Practice reading both the singular and plural forms out loud to build your confidence.

Before you move on to the next module, take a moment for a practical self-check. Imagine yourself in the following real-world situations and test your ability to apply the rules.

*   How do you ask a close friend to "look" at something interesting? You use the short informal form: **Дивись!**
*   How do you instruct a group of people to "listen" to your announcement? You need the plural form: **Слухайте!**
*   What is the single most important word that makes any direct command perfectly polite? The magic phrase is: **Будь ласка.**
*   How do you say "Please say" or "Please tell" to your boss or a stranger? You combine the formal verb with the polite marker: **Скажіть, будь ласка.**

Remember, the goal is not to memorize grammar rules in isolation, but to communicate effectively. Keep practicing these core verbs, always consider who you are speaking to, and never hesitate to add a polite "please" to your requests. The imperative mood is a powerful tool that will make your Ukrainian sound much more natural and engaging.

<!-- INJECT_ACTIVITY: fill-in-contextual-names -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: please-do-this
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

**Level: A1.4+ (Module 43/55) — BEGINNER**

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
