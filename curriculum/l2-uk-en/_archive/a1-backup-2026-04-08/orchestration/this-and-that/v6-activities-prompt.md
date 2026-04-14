<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/this-and-that.yaml` file for module **12: This and That** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-demonstratives-this -->`
- `<!-- INJECT_ACTIVITY: fill-in-demonstratives-this -->`
- `<!-- INJECT_ACTIVITY: quiz-demonstratives-that -->`
- `<!-- INJECT_ACTIVITY: match-up-gender-paradigm -->`
- `<!-- INJECT_ACTIVITY: fill-in-demonstratives-contrast -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Цей, ця, or це? Choose the right demonstrative for each noun.
  items: 8
  type: quiz
- focus: 'Complete: ___ книга нова, а ___ — стара. (ця/та)'
  items: 8
  type: fill-in
- focus: Match цей/ця/це with мій/моя/моє and який/яка/яке — same gender!
  items: 6
  type: match-up
- focus: Той, та, or те? Point at the far object.
  items: 6
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- ось (here is, look — pointing word)
- там (there)
- тут (here)
- він, вона, воно (review from M08 — used for reference)
required:
- цей, ця, це (this — m/f/n)
- той, та, те (that — m/f/n)
- чи (or — in questions)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Ірина walks into an electronics store. Phones line the counter in front of her, laptops sit on a shelf across the room — and she needs to tell the shop assistant exactly which one she wants. **Цей** (this one) or **той** (that one)?

### Dialogue 1 — Shopping for a bag

> **Ірина:** Скільки коштує ця сумка? *(How much is this bag?)*
> **Консультант:** Яка? Ця червона? *(Which one? This red one?)*
> **Ірина:** Ні, та синя. *(No, that blue one.)*
> **Консультант:** Та коштує двісті гривень. *(That one costs two hundred hryvnias.)*
> **Ірина:** А цей рюкзак? *(And this backpack?)*
> **Консультант:** Цей — сто п'ятдесят. *(This one — one hundred fifty.)*
> **Ірина:** Добре, беру цей рюкзак. *(Okay, I'll take this backpack.)*

Notice how Ірина and the Консультант use **ця** and **та** to avoid confusion. When Ірина says **ця сумка** (this bag), she means the one right in front of her — she could touch it. When she says **та синя** (that blue one), she points to the bag farther away on the display. The shop assistant immediately understands which item she means. **Цей рюкзак** (this backpack) works the same way — it is close to Ірина, within reach.

### Dialogue 2 — Comparing furniture in the showroom

Ірина walks through a display room at the back of the store.

> **Ірина:** Що це? *(What is this?)*
> **Консультант:** Це мій стіл. *(This is my desk.)*
> **Ірина:** А те? *(And that?)*
> **Консультант:** Те — крісло. *(That is an armchair.)*
> **Ірина:** Цей стілець новий, а той — старий. *(This chair is new, and that one is old.)*
> **Консультант:** Так, цей зручний, а той — ні. *(Yes, this one is comfortable, and that one — no.)*

Two patterns emerge here. First, **Це мій стіл** uses **це** to introduce something — "This is my desk." Second, **цей стілець** uses **цей** to point at a specific chair — "this chair." Both are natural, and context always makes the meaning clear. When the Консультант says **Те — крісло**, the dash replaces the verb "is" — standard written Ukrainian for equative sentences like "That is an armchair."

<!-- INJECT_ACTIVITY: quiz-demonstratives-this -->

## Цей, ця, це (This)

Ukrainian has three forms of "this" because every noun has a grammatical gender. You already know this pattern from **мій/моя/моє** (my) in Module 6 and **який/яка/яке** (which) in Module 9. Demonstrative pronouns follow exactly the same logic:

- **Цей стіл** (m) — this table
- **Ця книга** (f) — this book
- **Це вікно** (n) — this window

The endings match what you have already seen: **-ий** for masculine, **-а** for feminine, **-е** for neuter. As Заболотний (Grade 6, p. 210) puts it: вказівні займенники цей, той змінюються за родами — demonstrative pronouns change by gender. At A1, we only use the nominative forms listed above. Other case forms come later.

How do you know which form to use? Match it to the noun's gender — the gender you already learned in Module 8. Here are more examples across all three genders:

- **Цей телефон** (m) — this phone
- **Цей олівець** (m) — this pencil
- **Ця камера** (f) — this camera
- **Ця ручка** (f) — this pen
- **Це радіо** (n) — this radio
- **Це місто** (n) — this city

**Цей/ця/це** always refers to something near the speaker — the thing you can reach, hold, or are standing next to. If it is close enough to touch, use **цей/ця/це**.

Demonstratives combine naturally with adjectives and colors. The word order is the same as English — demonstrative first, then adjective(s), then noun:

- **Цей великий червоний стіл.** — This big red table.
- **Ця нова синя сумка.** — This new blue bag.
- **Це маленьке біле вікно.** — This small white window.

Ukrainian word order is more flexible than English in general, but demonstrative + adjective + noun is the most natural, unmarked order. At A1, stick with this pattern and it will always sound right.

<!-- INJECT_ACTIVITY: fill-in-demonstratives-this -->

## Той, та, те (That)

"That" works exactly like "this" — same three genders, same endings. The only difference is distance: **той/та/те** points at something farther away from the speaker, or something mentioned earlier.

- **Той стіл** (m) — that table
- **Та книга** (f) — that book
- **Те вікно** (n) — that window

Contrast pairs make the near/far distinction vivid:

- **Цей стілець новий, а той — старий.** — This chair is new, and that one is old.
- **Цей рюкзак синій, а той — чорний.** — This backpack is blue, and that one is black.
- **Це крісло зручне, а те — ні.** — This armchair is comfortable, and that one — no.

:::caution
The word **та** has two meanings. As a demonstrative pronoun, **та** means "that" (feminine) and always appears directly before a noun: **та книга** (that book). As a conjunction, **та** means "and" (like **і** or **й**) and connects two words: **мама та тато** (mom and dad). A quick test: is **та** followed directly by a noun it describes? Then it means "that." Does **та** link two separate words? Then it means "and."

- **Та книга цікава.** — That book is interesting. (demonstrative — **та** + noun)
- **Ірина та Максим** — Iryna and Maksym (conjunction — **та** links two names)
:::

Demonstratives pair naturally with question words to help you choose between objects. The question particle **чи** (or) connects the options:

- **Який стіл? — Цей чи той?** — Which table? This one or that one?
- **Яка сумка? — Ця червона чи та синя?** — Which bag? This red one or that blue one?
- **Яке вікно? — Це велике чи те маленьке?** — Which window? This big one or that small one?

The pointing word **ось** (here is / look) and the adverb **там** (there) pair naturally with demonstratives: **Ось цей телефон — дорогий.** (Here, this phone — expensive.) **А той, там, — ні.** (And that one, over there — no.)

One more thing worth noting. **Це** can stand alone to introduce or name something — **Це вікно.** means "This is a window." But **це** can also modify a noun directly — **Це вікно велике.** means "This window is big." Context always makes the meaning clear. You have been using **Це...** as "This is..." since Module 3, and now you are adding **це** as "this" before neuter nouns. Both uses are completely natural.

<!-- INJECT_ACTIVITY: quiz-demonstratives-that -->

<!-- INJECT_ACTIVITY: match-up-gender-paradigm -->

## Підсумок — Summary

Two sets of demonstrative pronouns, one simple system. **Цей/ця/це** points to things near you — this phone in your hand, this book on your desk. **Той/та/те** points to things farther away — that laptop on the shelf, that bag across the store. Both sets follow the same gender endings as **мій/моя/моє** and **який/яка/яке** — Ukrainian gender agreement is one consistent pattern you apply everywhere.

Here are all four paradigms together:

| | m | f | n |
|---|---|---|---|
| **мій** | **моя** | **моє** | (M06 — possessives) |
| **який** | **яка** | **яке** | (M09 — questions) |
| **цей** | **ця** | **це** | (M12 — this) |
| **той** | **та** | **те** | (M12 — that) |

Same endings, same logic — learn the pattern once, apply it everywhere.

Remember the **та** double meaning: **Та книга цікава** (that book — demonstrative, before a noun) vs **Ірина та Максим** (and — conjunction, between names). Quick test: is **та** followed by a noun it describes? → "that." Does it link two words? → "and."

Try this self-check to practise what you have learned:

- Look around — pick 3 objects near you. Say: **Це ___.** Then: **Цей/Ця/Це ___ (adjective) ___ (noun).**
- Now pick 3 objects far away. Say: **Те ___.** Then: **Той/Та/Те ___ (adjective) ___ (noun).**
- Choose between **цей** and **той**: ___ телефон (in your hand) **чи** ___ ноутбук (on that shelf)?
- Translate into Ukrainian: "That old chair." / "This new blue bag." / "Is this a window or a door?"

If you can point at objects around you and name them with the right demonstrative and gender — congratulations, you are thinking in Ukrainian. The gender system that seemed like three separate sets of words in Modules 6, 9, and now 12 is really one pattern repeated. Every new word you learn simply plugs into this system.

<!-- INJECT_ACTIVITY: fill-in-demonstratives-contrast -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: this-and-that
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

**Level: A1.2-A1.3 (Module 12/55) — EARLY BEGINNER**

The learner knows the alphabet and ~200 words. They:
- Can read Ukrainian slowly
- Know basic nouns, adjectives, simple verb forms
- Cannot handle complex sentences or grammar terminology in Ukrainian

**Instructions in simple English with Ukrainian key terms in bold.**
Example: 'Choose the correct form of **мій/моя/моє**'

**Good activity types:** quiz, fill-in (simple sentences), match-up, group-sort, true-false, observe, anagram, translate (English→Ukrainian).


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-gender
- **group-sort** — Він, вона чи воно?: Sort nouns by grammatical gender using ending rules
  - Instruction: *Розподіліть слова за родами*
- **quiz** — Який рід?: Determine gender from ending — consonant=masc, -а/-я=fem, -о/-е=neut
- **fill-in** — Мій, моя чи моє?: Choose possessive that matches noun gender
  - Instruction: *Вставте правильне слово*
- **match-up** — Іменник + займенник: Match nouns to він/вона/воно

### Pattern: grammar-adjectives
- **fill-in** — Який? Яка? Яке?: Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Match nouns to correct adjective forms

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
