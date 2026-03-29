<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/things-have-gender.yaml` file for module **8: Things Have Gender** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-gender-pronoun -->`
- `<!-- INJECT_ACTIVITY: quiz-gender-ending -->`
- `<!-- INJECT_ACTIVITY: group-sort-gender -->`
- `<!-- INJECT_ACTIVITY: fill-in-possessive -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Sort objects into masculine/feminine/neuter
  items: 12
  type: group-sort
- focus: він, вона, or воно? Choose for each noun.
  items: 8
  type: quiz
- focus: мій/моя/моє ___ (match possessive to noun)
  items: 8
  type: fill-in
- focus: What gender? Look at the ending.
  items: 6
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- зошит (notebook, m)
- ручка (pen, f)
- сумка (bag, f)
- крісло (armchair, n)
- дзеркало (mirror, n)
- ключ (key, m)
- фото (photo, n)
- стіна (wall, f)
required:
- стіл (table, m)
- книга (book, f)
- вікно (window, n)
- кімната (room, f)
- ліжко (bed, n)
- стілець (chair, m)
- лампа (lamp, f)
- телефон (phone, m)
- комп'ютер (computer, m)
- він, вона, воно (he, she, it — gender test words)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Марія is on a video call, showing her room to her friend. As she points at objects around her, something interesting happens — the word for "my" keeps changing: **мій**, **моя**, **моє**. Why? Because every noun in Ukrainian has a **рід** (gender).

> **Марія:** Привіт! Дивись, це моя кімната. *(Hi! Look, this is my room.)*
> **Оленка:** Класно! У тебе є стіл? *(Cool! Do you have a table?)*
> **Марія:** Так, у мене є стіл і ліжко. *(Yes, I have a table and a bed.)*
> **Оленка:** А комп'ютер? *(And a computer?)*
> **Марія:** У мене є комп'ютер і лампа. *(I have a computer and a lamp.)*
> **Оленка:** А ліжко? Яке воно? *(And the bed? What is it like?)*
> **Марія:** Моє ліжко зручне! *(My bed is comfortable!)*
> **Оленка:** А стіл — мій стіл теж зручний! *(And the table — my table is also comfortable!)*

Notice how Марія says **моя кімната** (my room), **моє ліжко** (my bed), and Оленка says **мій стіл** (my table). Three different words for "my" — and each one matches the noun it describes. That pattern is not random. It's gender at work.

Now another situation: at school, two students check what's in their bags before class.

> **Олег:** Що у тебе є? *(What do you have?)*
> **Соня:** У мене є книга, ручка і зошит. А у тебе? *(I have a book, a pen, and a notebook. And you?)*
> **Олег:** У мене є телефон і сумка. *(I have a phone and a bag.)*
> **Соня:** А ключ у тебе є? *(Do you have a key?)*
> **Олег:** Так, ось мій ключ. *(Yes, here's my key.)*
> **Соня:** А це моє фото — з сім'єю. *(And this is my photo — with family.)*

Again — **мій ключ** (my key), **моє фото** (my photo). Соня's bag holds **книга** (book), **ручка** (pen), **сумка** (bag) — all feminine. Олег's **телефон** (phone), **зошит** (notebook), **ключ** (key) — all masculine. And **фото** (photo) is neuter.

Did you notice **мій**, **моя**, **моє** changing? That's because every **іменник** (noun) in Ukrainian has a **рід** (gender). Understanding gender is the key to speaking Ukrainian correctly — and that's what this module is about.

## Він, вона, воно (The Gender Test)

Every Ukrainian noun belongs to one of three genders: **чоловічий рід** (masculine), **жіночий рід** (feminine), or **середній рід** (neuter). Ukrainian textbooks teach a simple test — try replacing the noun with **він** (he), **вона** (she), or **воно** (it). Whichever fits, that's the gender. Take **стіл** (table): you can say **він** about it, so it's **чоловічий рід**. Take **книга** (book): you'd say **вона**, so it's **жіночий рід**. And **вікно** (window)? That's **воно** — **середній рід**.

Gender connects directly to the possessives you already saw in the dialogues — and that you know from Module 6 (family). Masculine nouns (**він**) take **мій**: **мій стіл** (my table), **мій телефон** (my phone), **мій зошит** (my notebook). Feminine nouns (**вона**) take **моя**: **моя книга** (my book), **моя кімната** (my room), **моя лампа** (my lamp). Neuter nouns (**воно**) take **моє**: **моє вікно** (my window), **моє ліжко** (my bed), **моє фото** (my photo). The possessives **мій**, **моя**, **моє** from the dialogues map exactly onto gender — this is why they kept changing.

<!-- INJECT_ACTIVITY: quiz-gender-pronoun -->

Now here's a useful shortcut. Most nouns follow predictable ending patterns, as described in Вашуленко's Grade 3 textbook. **Чоловічий рід** — the noun usually ends in a consonant: **стіл**, **телефон**, **зошит**, **ключ**, **стілець** (chair). **Жіночий рід** — the noun usually ends in **-а** or **-я**: **книга**, **лампа**, **кімната**, **ручка** (pen), **сумка** (bag), **стіна** (wall). **Середній рід** — the noun usually ends in **-о** or **-е**: **вікно**, **ліжко**, **крісло** (armchair), **дзеркало** (mirror), **фото**. This pattern covers roughly 90% of the nouns you'll encounter at this level. There are exceptions — for instance, some words ending in **-ь** like **ніч** (night) — but those come in a later module.

So you have a reliable two-step method. Step 1: say **він**, **вона**, or **воно** with the noun — which one fits naturally? Step 2: check the ending for confirmation. Take **телефон** — it ends in a consonant (н), and you'd say **він** about it, so it's masculine: **мій телефон**. Take **кімната** — it ends in **-а**, and you'd say **вона**, so it's feminine: **моя кімната**. Take **ліжко** — it ends in **-о**, and you'd say **воно**, so it's neuter: **моє ліжко**. Two clues always pointing the same direction makes gender predictable, not arbitrary.

<!-- INJECT_ACTIVITY: quiz-gender-ending -->

## Предмети навколо (Objects Around Us)

Let's look around a typical Ukrainian room and a school bag. The objects here cover all three genders. Learning them now with gender attached — not just **стіл**, but **стіл — він** — builds the right habit from the start. In Ukrainian, you always know a noun's gender. It's built into how you speak about every single object.

Here are 18 common objects organized by gender:

| Чоловічий рід (він, мій) | Жіночий рід (вона, моя) | Середній рід (воно, моє) |
|---|---|---|
| **стіл** — table | **книга** — book | **вікно** — window |
| **стілець** — chair | **лампа** — lamp | **ліжко** — bed |
| **телефон** — phone | **сумка** — bag | **крісло** — armchair |
| **комп'ютер** — computer | **ручка** — pen | **дзеркало** — mirror |
| **зошит** — notebook | **кімната** — room | **фото** — photo |
| **ключ** — key | **стіна** — wall | |

Notice the pattern: every masculine noun ends in a consonant, every feminine noun ends in **-а**, and every neuter noun ends in **-о**. The endings are not decoration — they are signals.

<!-- INJECT_ACTIVITY: group-sort-gender -->

Now let's extend the **У мене є** pattern you learned in Module 6 with family members. Same structure, new world of objects:

- **У мене є стіл.** — I have a table.
- **У мене є книга.** — I have a book.
- **У мене є вікно.** — I have a window.
- **У мене є крісло.** — I have an armchair.

The phrase stays exactly the same — only the noun changes. And when you add a possessive, gender shows up: **Це мій стіл** (This is my table), **Це моя книга** (This is my book), **Це моє вікно** (This is my window). The possessive always matches the gender of the noun that follows it.

<!-- INJECT_ACTIVITY: fill-in-possessive -->

:::tip
In Ukrainian, gender is not just abstract grammar — it shapes how speakers relate to every object. Unlike English, where "it" covers everything, Ukrainian speakers feel the gender of every noun. **Стіл** is **він**, **книга** is **вона**, **вікно** is **воно** — each has its own identity. When you start thinking of objects this way — not translating "my table" but feeling **мій стіл** — you're beginning to think in Ukrainian. That cognitive shift is the real goal of this module.
:::

## Підсумок — Summary

Gender determination works in three steps:

1. **Скажи він, вона, або воно з іменником — яке підходить?** Say **він**, **вона**, or **воно** with the noun — which one fits?
2. **Перевір закінчення — приголосна? -а/-я? -о/-е?** Check the ending — consonant? **-а/-я**? **-о/-е**?
3. **Вибери мій, моя, або моє.** Choose the right possessive — **мій**, **моя**, or **моє**.

Each step reinforces the others. The gender test, the ending pattern, and the possessive all point to the same answer. Three clues, one gender — no guessing needed.

Test yourself with these questions:

- **Який рід у слова «стіл»?** → Чоловічий (**він**, **мій**) — ends in a consonant (л).
- **Який рід у слова «книга»?** → Жіночий (**вона**, **моя**) — ends in **-а**.
- **Який рід у слова «вікно»?** → Середній (**воно**, **моє**) — ends in **-о**.
- **Як сказати "I have a chair" українською?** → **У мене є стілець.**
- **Як сказати "my lamp" і "my mirror"?** → **Моя лампа** (feminine), **моє дзеркало** (neuter).
- **Яке закінчення у слів жіночого роду?** → **-а** або **-я**.
- **Яке закінчення у слів середнього роду?** → **-о** або **-е**.

In the next module, you'll learn to describe these objects: **великий стіл** (big table), **маленьке вікно** (small window), **нова книга** (new book). Adjectives in Ukrainian also change their endings based on gender — but you already hold the key to adjective agreement, because you know gender. Everything connects.

Here's a micro-challenge: look around where you are right now. Pick three objects. What gender would each one be in Ukrainian? Say aloud: **У мене є ___. Це мій/моя/моє ___.** Start noticing gender everywhere — it will become instinct.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: things-have-gender
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

**Level: A1.2-A1.3 (Module 8/55) — EARLY BEGINNER**

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
