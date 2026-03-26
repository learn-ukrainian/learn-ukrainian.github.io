# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/things-have-gender.yaml` file for module **8: Things Have Gender** (a1).

Output **pure YAML only** — no markdown fencing, no preamble, no explanation. Just the YAML document.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 2-3 quick checks after key teaching points. Workbook = 4-8 deeper practice exercises covering the full topic.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: quiz-vin-vona-vono -->`
- `<!-- INJECT_ACTIVITY: group-sort-gender -->`
- `<!-- INJECT_ACTIVITY: fill-in-possessives -->`
- `<!-- INJECT_ACTIVITY: quiz-gender-by-ending -->`

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

Оленка just moved into a new apartment. She video-calls her friend Марко to show off her room.

> **Оленка:** Привіт, Марку! Дивись, це моя кімната! *(Hi, Marko! Look, this is my room!)*
> **Марко:** О, класно! Велика кімната! У тебе є стіл? *(Oh, cool! A big room! Do you have a table?)*
> **Оленка:** Так, у мене є стіл. Ось мій стіл. А ось моє ліжко. *(Yes, I have a table. Here's my table. And here's my bed.)*
> **Марко:** А лампа є? *(And is there a lamp?)*
> **Оленка:** Так, моя лампа ось тут. І є вікно — моє вікно велике! *(Yes, my lamp is right here. And there's a window — my window is big!)*
> **Марко:** А комп'ютер? *(And a computer?)*
> **Оленка:** Так, мій комп'ютер на столі. *(Yes, my computer is on the table.)*

Did you notice something? Оленка says **мій стіл** (my table) but **моя лампа** (my lamp) and **моє ліжко** (my bed). Three different words for "my" — **мій**, **моя**, **моє**. Why does "my" keep changing? The answer has to do with gender — grammatical gender. Every Ukrainian noun belongs to one of three groups, and the word for "my" must match.

The next day at university, Оленка and Марко compare what they have in their bags before class.

> **Марко:** Що у тебе в сумці? *(What do you have in your bag?)*
> **Оленка:** У мене є книга, ручка і зошит. А у тебе? *(I have a book, a pen, and a notebook. And you?)*
> **Марко:** У мене є телефон, ключ і фото. *(I have a phone, a key, and a photo.)*
> **Оленка:** Фото? Яке фото? *(A photo? What photo?)*
> **Марко:** Моє фото з Києва! *(My photo from Kyiv!)*

Look at the nouns: **книга** (book) and **ручка** (pen) feel like **вона** words. **Телефон** (phone) and **ключ** (key) feel like **він** words. And **фото** (photo) feels like a **воно** word. Three different groups. Ukrainian nouns belong to three genders — and every noun you learn comes with one. Let's pull out the objects from both dialogues: **стіл** (table), **кімната** (room), **ліжко** (bed), **лампа** (lamp), **вікно** (window), **комп'ютер** (computer), **книга** (book), **ручка** (pen), **зошит** (notebook), **телефон** (phone), **ключ** (key), **фото** (photo). Some are **він** words, some **вона** words, some **воно** words. How do Ukrainian speakers know which is which? There is a simple test.

## Він, вона, воно (The Gender Test)

Every Ukrainian noun has a grammatical gender: **чоловічий рід** (masculine), **жіночий рід** (feminine), or **середній рід** (neuter). Ukrainian textbooks teach a straightforward test — try replacing the noun with **він** (he), **вона** (she), or **воно** (it). Whichever fits tells you the gender. You can also test by adding **мій** (my, masculine), **моя** (my, feminine), or **моє** (my, neuter).

- **Стіл** → він. **Мій стіл.** Masculine.
- **Книга** → вона. **Моя книга.** Feminine.
- **Вікно** → воно. **Моє вікно.** Neuter.

If you can say **він** about it, the noun is masculine. If **вона** — feminine. If **воно** — neuter.

Let's walk through more nouns from the dialogues using this test. Say each one out loud with **він**, **вона**, or **воно** and hear which sounds right:

- **Телефон** — він. **Мій телефон.** Masculine.
- **Лампа** — вона. **Моя лампа.** Feminine.
- **Ліжко** — воно. **Моє ліжко.** Neuter.
- **Зошит** — він. **Мій зошит.** Masculine.
- **Ручка** — вона. **Моя ручка.** Feminine.
- **Крісло** (armchair) — воно. **Моє крісло.** Neuter.

This is not about biological gender. A **стіл** is not male — nobody thinks of a table as a man. But the word **стіл** is grammatically masculine, so it takes **він** and **мій**. Every noun has a grammatical gender, and you simply need to learn which one.

<!-- INJECT_ACTIVITY: quiz-vin-vona-vono -->

Here is the good news: you do not need the він/вона/воно test every time. The ending of the word almost always tells you the gender. Ukrainian Grade 3 textbooks present it like this:

**Чоловічий рід (він, мій)** — the word ends in a consonant:

- **стіл**, **телефон**, **зошит**, **стілець** (chair), **ключ**, **комп'ютер**

**Жіночий рід (вона, моя)** — the word ends in **-а** or **-я**:

- **книга**, **лампа**, **сумка** (bag), **ручка**, **кімната**, **стіна** (wall)

**Середній рід (воно, моє)** — the word ends in **-о** or **-е**:

- **вікно**, **ліжко**, **крісло**, **дзеркало** (mirror), **фото**

This covers the vast majority of nouns you will meet at this level. Some words ending in **-ь** (like **тінь** — shadow) are trickier — we will learn those later. For now, the rule is simple: consonant ending → **він**, ending in **-а/-я** → **вона**, ending in **-о/-е** → **воно**.

## Предмети навколо (Objects Around Us)

Time for a tour of your room. Here are common objects organized by gender — practice saying **мій**, **моя**, or **моє** with each one.

**Чоловічий рід (він, мій):**

| Ukrainian | English | Example |
|-----------|---------|---------|
| **стіл** | table | Мій стіл великий. |
| **стілець** | chair | Мій стілець зручний. |
| **телефон** | phone | Мій телефон новий. |
| **комп'ютер** | computer | Мій комп'ютер тут. |
| **зошит** | notebook | Мій зошит синій. |
| **ключ** | key | Мій ключ маленький. |

**Жіночий рід (вона, моя):**

| Ukrainian | English | Example |
|-----------|---------|---------|
| **книга** | book | Моя книга цікава. |
| **лампа** | lamp | Моя лампа яскрава. |
| **сумка** | bag | Моя сумка велика. |
| **ручка** | pen | Моя ручка червона. |
| **кімната** | room | Моя кімната тепла. |
| **стіна** | wall | Моя стіна біла. |

**Середній рід (воно, моє):**

| Ukrainian | English | Example |
|-----------|---------|---------|
| **вікно** | window | Моє вікно велике. |
| **ліжко** | bed | Моє ліжко зручне. |
| **крісло** | armchair | Моє крісло м'яке. |
| **дзеркало** | mirror | Моє дзеркало кругле. |
| **фото** | photo | Моє фото старе. |

<!-- INJECT_ACTIVITY: group-sort-gender -->

In Module 6, you learned to say **У мене є мама** and **У мене є тато** — "I have a mom" and "I have a dad." The same pattern works perfectly for objects:

- У мене є стіл.
- У мене є книга.
- У мене є вікно.

You can combine **У мене є** with a possessive to emphasize ownership:

- У мене є мій стіл.
- У мене є моя книга.
- У мене є моє ліжко.

In casual speech, Ukrainians often drop **мій/моя/моє** after **У мене є** — the meaning is clear without it. But the gender is still there, built into the noun itself. Whenever you add an adjective or possessive, the gender surfaces.

<!-- INJECT_ACTIVITY: fill-in-possessives -->

Two friends comparing their rooms:

> **Оленка:** У мене є комп'ютер, а у тебе? *(I have a computer, and you?)*
> **Марко:** У мене немає комп'ютера, але є дзеркало. *(I don't have a computer, but I have a mirror.)*

A quick preview: **немає** means "don't have" — the opposite of **є**. A full explanation comes in a later module. For now, notice that even in this short exchange, the nouns reveal their gender. **Комп'ютер** — він (masculine, consonant ending). **Дзеркало** — воно (neuter, ends in **-о**). Gender is always present in every Ukrainian sentence, whether you see **мій/моя/моє** or not.

<!-- INJECT_ACTIVITY: quiz-gender-by-ending -->

Can you apply the ending rule to nouns you have never seen before? Try these: **парта** (desk) ends in **-а** — feminine. **Олівець** (pencil) ends in a consonant — masculine. **Місто** (city) ends in **-о** — neuter. **Школа** (school) ends in **-а** — feminine. **Рюкзак** (backpack) ends in a consonant — masculine. **Море** (sea) ends in **-е** — neuter. The rule works.

## Підсумок — Summary

Gender determination in three steps:

**Step 1:** Say **він**, **вона**, or **воно** with the noun. Which sounds right?

**Step 2:** Check the ending:

| Ending | Gender | Possessive | Example |
|--------|--------|------------|---------|
| consonant | чоловічий рід | мій | стіл, телефон, ключ |
| -а / -я | жіночий рід | моя | книга, лампа, кімната |
| -о / -е | середній рід | моє | вікно, ліжко, крісло |

**Step 3:** Use the matching possessive — **мій** for він-words, **моя** for вона-words, **моє** for воно-words.

This system covers roughly 90% of Ukrainian nouns. The few exceptions — words ending in **-ь** and some borrowed words — come in later modules.

:::tip
When you learn a new noun, always learn its gender at the same time. Say the noun with **мій**, **моя**, or **моє** out loud. This builds the habit early, and soon gender will feel automatic.
:::

Test yourself. What gender is **стіл**? It ends in a consonant — **він**, masculine. **Мій стіл.** What gender is **книга**? It ends in **-а** — **вона**, feminine. **Моя книга.** What about **вікно**? It ends in **-о** — **воно**, neuter. **Моє вікно.** Say "I have a chair" in Ukrainian: **У мене є стілець.** What possessive goes with **кімната**? It ends in **-а**, so it is feminine: **моя кімната.**

Now you know that every Ukrainian noun has a gender, and you have two tools to find it — the він/вона/воно test and the ending shortcut. In the next module, you will learn adjectives — words like **великий** (big), **нова** (new), **гарне** (beautiful) — and discover how they change form to match the noun's gender.

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


## Quality Rules

1. **Instructions match learner level:**
   - **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
   - **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
   - **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
   - **A2+:** Instructions in Ukrainian.
   - **B1+:** Full Ukrainian, no English.
2. **3-5 options per quiz/fill-in** — enough to prevent guessing, not so many to overwhelm
3. **No duplicate options** — each option in a quiz item must be unique
4. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
5. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
6. **Min 3 pairs for match-up** — to prevent trivial elimination
7. **Explanations for true-false and error-correction** — help the learner understand WHY
8. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

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

**Efficiency Rules:**
- **Batch your checks:** Use `mcp__rag__verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 8-15 tool calls per module**, not 50.

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
