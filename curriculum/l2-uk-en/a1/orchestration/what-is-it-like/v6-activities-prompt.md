<!-- version: 1.0.0 | updated: 2026-03-27 -->
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

- `<!-- INJECT_ACTIVITY: quiz-yakyi-yaka-yake -->`
- `<!-- INJECT_ACTIVITY: match-adjective-opposites -->`
- `<!-- INJECT_ACTIVITY: fill-in-adjective-endings -->`
- `<!-- INJECT_ACTIVITY: fill-in-describe-room -->`

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

Everything around you has qualities — a table can be big or small, a room can be bright or dark. Ukrainian adjectives bring these descriptions to life, but they have a trick: their endings change depending on the noun they describe. Two everyday conversations will show you exactly how this works.

### Dialogue 1 — Describing a Room

Imagine two friends talking about one of their rooms at home. Notice how the adjective endings shift as the nouns change.

> **Оленка:** Яка твоя кімната? *(What is your room like?)*
> **Тарас:** Моя кімната велика і світла. *(My room is big and bright.)*
> **Оленка:** А стіл? Який він? *(And the table? What is it like?)*
> **Тарас:** Стіл новий. А ліжко — старе. *(The table is new. And the bed is old.)*
> **Оленка:** А вікно? Яке воно? *(And the window? What is it like?)*
> **Тарас:** Вікно велике і чисте. *(The window is big and clean.)*

This short exchange uses six adjectives on four nouns — and every ending tells you the noun's gender. The word **кімната** (room) is feminine, so we hear **велика** and **світла** — both ending in **-а**. The word **стіл** (table) is masculine, so the adjective is **новий** — ending in **-ий**. And **ліжко** (bed) and **вікно** (window) are neuter, giving us **старе**, **велике**, and **чисте** — all ending in **-е**.

Look at the pattern: the noun changed, and the adjective ending followed. This is exactly like **мій/моя/моє** from the previous module — the same gender logic, applied to a new set of words.

### Dialogue 2 — Window Shopping

Now two friends are walking past shop windows. A new question word appears — **яке** (what kind? — neuter).

> **Марія:** Яка гарна сумка! *(What a nice bag!)*
> **Андрій:** Так, але вона дорога. *(Yes, but it's expensive.)*
> **Марія:** А телефон? Який він? *(And the phone? What is it like?)*
> **Андрій:** Він великий і дешевий. *(It's big and cheap.)*
> **Марія:** А це вікно? Яке воно? *(And this window? What is it like?)*
> **Андрій:** Воно чисте і світле. *(It's clean and bright.)*

Both dialogues reveal the same pattern: the question word matches the noun's gender. For masculine nouns you ask **який** (what kind?), for feminine — **яка**, and for neuter — **яке**. These three question forms are the key to describing anything in Ukrainian, and the next section explains exactly why they work this way.

## Який? Яка? Яке? (What kind?)

The question "What kind?" in Ukrainian is not a single word — it shifts to match the noun, just like **мій/моя/моє** from Module 8. Think of **який** as a mini-adjective: it agrees with whatever noun it asks about.

| Gender | Question word | Example | Answer |
|---|---|---|---|
| Masculine | **який** | **Який стіл?** *(What kind of table?)* | **Великий стіл.** *(A big table.)* |
| Feminine | **яка** | **Яка книга?** *(What kind of book?)* | **Нова книга.** *(A new book.)* |
| Neuter | **яке** | **Яке вікно?** *(What kind of window?)* | **Чисте вікно.** *(A clean window.)* |

Each answer follows the same rule: the adjective ending mirrors the noun's gender. Masculine adjectives end in **-ий** (**великий**, **новий**, **чистий**). Feminine adjectives end in **-а** (**велика**, **нова**, **чиста**). Neuter adjectives end in **-е** (**велике**, **нове**, **чисте**). This is the hard-stem pattern, and it covers most adjectives you will meet at this level.

Ukrainian textbooks state this rule simply: «Прикметник має такий рід, як іменник, з яким він зв'язаний» — the adjective takes the same gender as the noun it is connected to (Пономарова, Grade 3, p. 98). Look at how one root shifts across all three genders:

- **зелений кущ** *(a green bush — masculine)*
- **зелена трава** *(green grass — feminine)*
- **зелене дерево** *(a green tree — neuter)*

The root **зелен-** stays the same. Only the ending changes: **-ий**, **-а**, **-е**.

<!-- INJECT_ACTIVITY: quiz-yakyi-yaka-yake -->

There is another ending set — soft-stem adjectives like **синій/синя/синє** (blue). These follow the same gender logic but use endings **-ій**, **-я**, **-є**. You will learn them properly in Module 10 (Colors). For now, just know they exist — the agreement principle is identical.

This ending pattern reappears in every grammatical case you will study later. Learn it well now, and every future module becomes easier. Practice recognizing the gender by the ending with these chains:

- **новий стіл** / **нова сумка** / **нове ліжко**
- **чистий стілець** / **чиста підлога** / **чисте вікно**
- **гарний телефон** / **гарна кімната** / **гарне крісло**

:::tip
Think of the adjective as a mirror: «Прикметник — дзеркало іменника.» *(The adjective is the noun's mirror.)* Whatever gender the noun has, the adjective reflects it. The question words **який/яка/яке** follow the same mirror rule. As Zaharijchuk's Grade 1 textbook (p. 101) puts it: words that answer the questions **який? яка? яке?** point to a quality of an object.
:::

## Прикметники (Common Adjectives)

The fastest way to learn adjectives is in opposite pairs — when you learn **великий** (big), learn **маленький** (small) at the same time. Your brain remembers contrasts better than isolated words. Here are six essential pairs:

| Adjective | Meaning | Opposite | Meaning |
|---|---|---|---|
| **великий** | big | **маленький** | small |
| **новий** | new | **старий** | old |
| **гарний** | nice, beautiful | **поганий** | bad |
| **чистий** | clean | **брудний** | dirty |
| **дорогий** | expensive | **дешевий** | cheap |
| **світлий** | light, bright | **темний** | dark |

<!-- INJECT_ACTIVITY: match-adjective-opposites -->

Now combine these adjectives with the room nouns you already know from Module 8. Every model sentence below deliberately uses a different gender so you can see all three endings in action:

- **У мене є великий стіл.** *(I have a big table. — masculine)*
- **Моя кімната маленька, але гарна.** *(My room is small but nice. — feminine)*
- **Вікно велике і чисте.** *(The window is big and clean. — neuter)*
- **Стілець старий, а ліжко — нове.** *(The chair is old, and the bed is new. — m + n)*
- **Шафа нова і велика.** *(The wardrobe is new and big. — feminine)*
- **Підлога чиста.** *(The floor is clean. — feminine)*
- **Сумка дорога.** *(The bag is expensive. — feminine)*
- **Телефон дешевий і новий.** *(The phone is cheap and new. — masculine)*

Notice two little words connecting ideas in these sentences. The conjunction **і** (and) links parallel qualities: **велике і чисте** — both describe the window equally. The conjunction **а** (and/but) marks a softer contrast: **Стілець старий, а ліжко — нове** — the chair is one thing, the bed is another. For a stronger contrast, use **але** (but): **Кімната маленька, але гарна** — the room is small, *however* it is nice. Ukrainian textbooks present these connectors alongside adjective pairs — the antonym pairs naturally invite contrast words (Вашуленко, Grade 2, p. 31).

<!-- INJECT_ACTIVITY: fill-in-adjective-endings -->

Now try building your own description. Here is a model — four sentences, all three genders present:

- **Моя кімната невелика.** *(My room is not big.)*
- **Стіл новий і чистий.** *(The table is new and clean.)*
- **Вікно велике і світле.** *(The window is big and bright.)*
- **Шафа стара, але гарна.** *(The wardrobe is old but nice.)*

Your turn: describe your own room in three to four sentences using adjectives from the pairs above. Try to include at least one masculine, one feminine, and one neuter noun. This is exactly the oral task from Вашуленко's Grade 3 textbook (p. 131): «Склади усну розповідь на тему "Моя кімната"» — compose an oral description on the topic "My Room."

<!-- INJECT_ACTIVITY: fill-in-describe-room -->

## Підсумок — Summary

Today you learned adjective-noun agreement in the nominative case — the adjective ending mirrors the noun's gender, every time.

Test yourself with these questions:

- What ending does a masculine adjective have? → **-ий** / **-ій** (**великий**, **новий**, **синій**)
- What about feminine? → **-а** / **-я** (**велика**, **нова**, **синя**)
- And neuter? → **-е** / **-є** (**велике**, **нове**, **синє**)
- Which question word goes with a masculine noun? → **Який?**
- With a feminine noun? → **Яка?**
- With a neuter noun? → **Яке?**
- What is the difference between **а** and **але**? → **А** marks a soft contrast; **але** is a stronger "but."

Module 10 (Colors) introduces soft-stem adjectives like **синій** (blue) and **зелений** (green) — the same agreement logic, but with the endings **-ій/-я/-є** instead of **-ий/-а/-е**. Later modules will apply these adjectives beyond the nominative case. What you learned today — matching the adjective to the noun's gender — is the foundation for every descriptive sentence you will ever build in Ukrainian.

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

**Level: A1.2-A1.3 (Module 9/55) — EARLY BEGINNER**

The learner knows the alphabet and ~200 words. They:
- Can read Ukrainian slowly
- Know basic nouns, adjectives, simple verb forms
- Cannot handle complex sentences or grammar terminology in Ukrainian

**Instructions in simple English with Ukrainian key terms in bold.**
Example: 'Choose the correct form of **мій/моя/моє**'

**Good activity types:** quiz, fill-in (simple sentences), match-up, group-sort, true-false, observe, anagram, translate (English→Ukrainian).


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
