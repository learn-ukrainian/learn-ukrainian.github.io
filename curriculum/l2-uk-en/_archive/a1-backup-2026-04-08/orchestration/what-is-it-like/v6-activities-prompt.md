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
- `<!-- INJECT_ACTIVITY: fill-in-adjective-endings -->`
- `<!-- INJECT_ACTIVITY: match-adjective-opposites -->`
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

You already know Ukrainian nouns have gender — **стіл** (table) is masculine, **книга** (book) is feminine, **вікно** (window) is neuter. But how do you describe what these things are actually like? That is where adjectives come in. Adjectives tell you about a noun's qualities — big, small, new, old. Two dialogues below show adjectives at work: first in a room at home, then at a weekend book fair.

> **Тарас:** Яка твоя кімната? *(What is your room like?)*
> **Оля:** Моя кімната велика і світла. *(My room is big and bright.)*
> **Тарас:** А стіл? *(And the table?)*
> **Оля:** Стіл новий. *(The table is new.)*
> **Тарас:** А ліжко? *(And the bed?)*
> **Оля:** Воно старе. *(It is old.)*
> **Тарас:** Вікно? *(The window?)*
> **Оля:** Вікно чисте і велике. *(The window is clean and big.)*
> **Тарас:** А стілець? *(And the chair?)*
> **Оля:** Маленький, але зручний. *(Small, but comfortable.)*

Notice what just happened: **кімната** (room) is feminine, so Тарас asked **Яка** твоя кімната? But **стіл** (table) is masculine, and **ліжко** (bed) is neuter. The question word changed every time. All the nouns here — **кімната**, **стіл**, **ліжко**, **вікно**, **стілець** (chair) — come from M08. Now they have adjectives attached to them.

Same question words — **Який?** **Яка?** **Яке?** — but a brand-new setting: a weekend book fair. Тарас and Софія browse books, maps, and posters. Watch how the question word shifts with each noun.

> **Тарас:** Який цікавий атлас! *(What an interesting atlas!)*
> **Софія:** Так, але він дорогий. *(Yes, but it is expensive.)*
> **Тарас:** А ця книга? Яка вона? *(And this book? What is it like?)*
> **Софія:** Нова і дешева. *(New and cheap.)*
> **Тарас:** Яке гарне фото! *(What a nice photo!)*
> **Софія:** Справді! А плакат? *(Indeed! And the poster?)*
> **Тарас:** Великий і яскравий. *(Big and bright.)*
> **Софія:** Подивись — маленька листівка. *(Look — a small postcard.)*
> **Тарас:** Яка вона? *(What is it like?)*
> **Софія:** Стара, але гарна. *(Old, but nice.)*

Look at the pattern in Dialogue 2: **атлас** (atlas, m) → **Який**, **книга** (book, f) → **Яка**, **фото** (photo, n) → **Яке**. The question word matched the noun's gender each time. **Плакат** (poster) is masculine, **листівка** (postcard) is feminine — five nouns, three genders, all represented. That pattern is the entire grammar point for this module.

<!-- INJECT_ACTIVITY: quiz-yakyi-yaka-yake -->

## Який? Яка? Яке? (What kind?)

The question "What kind?" in Ukrainian changes its ending to match the noun's gender — the same principle as **мій/моя/моє** from M08. Here is the core pattern:

- Masculine noun → **Який?** — **Який стіл?** → **Великий стіл.** *(What kind of table? → A big table.)*
- Feminine noun → **Яка?** — **Яка книга?** → **Нова книга.** *(What kind of book? → A new book.)*
- Neuter noun → **Яке?** — **Яке вікно?** → **Чисте вікно.** *(What kind of window? → A clean window.)*

Three questions, three answers — the gender matches in each pair.

Adjectives change their ending in exactly the same way as the question word. Masculine adjectives end in **-ий**: **великий** (big), **новий** (new), **чистий** (clean), **дорогий** (expensive). Feminine adjectives end in **-а**: **велика**, **нова**, **чиста**, **дорога**. Neuter adjectives end in **-е**: **велике**, **нове**, **чисте**, **дороге**. This comes directly from the Ukrainian textbook rule: «Прикметник має такий рід, як іменник, з яким він зв'язаний» (Пономарова, Grade 3, p.98) — the adjective takes the same gender as its noun. Always.

This is not a new concept — you already know it from M08. You learned **мій стіл** (my table, m), **моя книга** (my book, f), **моє вікно** (my window, n). Adjectives follow the exact same logic. If you can say **мій стіл**, you can say **великий стіл**. If you can say **моя книга**, you can say **нова книга**. The gender lives in the noun — the adjective just agrees with it.

<!-- INJECT_ACTIVITY: fill-in-adjective-endings -->

A quick note about what comes next. Some adjectives have a soft stem and end in **-ій/-я/-є** instead — for example, **синій** (blue, m), **синя** (f), **синє** (n). These follow the same gender logic, but they appear in M10 (Colors). For now, every adjective in this module ends in the hard pattern: **-ий** (m), **-а** (f), **-е** (n). One pattern, one module.

Here are three complete sentences combining M08 nouns with M09 adjectives. Notice the adjective can appear before or after the noun — both positions are correct in Ukrainian:

- **У мене є великий стіл.** *(I have a big table.)* — masculine
- **Моя кімната маленька, але гарна.** *(My room is small, but nice.)* — feminine
- **Вікно велике і чисте.** *(The window is big and clean.)* — neuter

## Прикметники (Common Adjectives)

Ukrainian vocabulary sticks better when you learn words in opposite pairs — your brain stores both at once. This module's core adjectives come in six pairs. For each pair, an example sentence shows both words in action with a noun you already know from M08.

1. **великий** (big) ↔ **маленький** (small)
   - **Стіл великий, а стілець маленький.** *(The table is big, and/but the chair is small.)*

2. **новий** (new) ↔ **старий** (old)
   - **Книга нова, але атлас старий.** *(The book is new, but the atlas is old.)*

3. **гарний** (nice, beautiful) ↔ **поганий** (bad)
   - **Яка гарна листівка! А цей плакат поганий.** *(What a nice postcard! And this poster is bad.)*

4. **чистий** (clean) ↔ **брудний** (dirty)
   - **Вікно чисте, а підлога брудна.** *(The window is clean, and/but the floor is dirty.)*

5. **дорогий** (expensive) ↔ **дешевий** (cheap)
   - **Атлас дорогий. Книга дешева.** *(The atlas is expensive. The book is cheap.)*

6. **світлий** (light, bright) ↔ **темний** (dark)
   - **Кімната світла і велика.** *(The room is bright and big.)*

Teaching adjectives in antonym pairs is exactly how Ukrainian textbooks do it from Grade 3 onward (Вашуленко, Grade 3, p.56 — «Протилежні за значенням слова — антоніми»). Notice how the adjective endings shift depending on the noun: **чисте вікно** (n, -е) but **брудна підлога** (f, -а). The gender of the noun controls everything.

<!-- INJECT_ACTIVITY: match-adjective-opposites -->

Now let's build full descriptions — combining several M08 nouns with M09 adjectives into connected sentences. Read this short paragraph describing a room:

- **У мене є маленька кімната.** *(I have a small room.)*
- **Стіл новий, а ліжко старе.** *(The table is new, and/but the bed is old.)*
- **Вікно велике і чисте.** *(The window is big and clean.)*
- **Стілець маленький і старий, але зручний.** *(The chair is small and old, but comfortable.)*

Two connectors to notice: **і** (and) links things that are both true in parallel — **велике і чисте** means the window is both big AND clean. **А** (and/but) marks a contrast between two things — **Стіл новий, а ліжко старе** highlights that one is new while the other is old. Compare: **Кімната мала і темна** (the room is small AND dark — both true, no contrast) vs. **Стіл новий, а стілець старий** (the table is new BUT the chair is old — deliberate contrast).

<!-- INJECT_ACTIVITY: fill-in-describe-room -->

## Підсумок — Summary

Here is today's core lesson in one sentence: Ukrainian adjectives change their ending to match the gender of the noun they describe. Three endings to remember right now: **-ий** for masculine, **-а** for feminine, **-е** for neuter. The question words **Який?** (m), **Яка?** (f), **Яке?** (n) follow the same pattern. The adjective always agrees with its noun — no exceptions in this module.

Test yourself with these questions:

- What ending does a masculine adjective have? → **-ий** (**великий**, **новий**, **чистий**)
- What ending does a feminine adjective have? → **-а** (**велика**, **нова**, **чиста**)
- What ending does a neuter adjective have? → **-е** (**велике**, **нове**, **чисте**)
- Which question word goes with **книга**? → **Яка?** (**Яка книга?**)
- Which question word goes with **стіл**? → **Який?** (**Який стіл?**)
- Which question word goes with **вікно**? → **Яке?** (**Яке вікно?**)
- What is the difference between **і** and **а**? → **і** means "and" (parallel: both true); **а** means "and/but" (contrast between two things)
- Name three adjective opposites. → **великий/маленький**, **новий/старий**, **дорогий/дешевий**

Colors in Ukrainian (M10) introduce soft-stem adjectives: **синій** (blue, m), **синя** (f), **синє** (n) — the same gender logic, but with a different ending pattern. After M10, describing objects fully unlocks: **великий синій стіл** (a big blue table), **нова червона книга** (a new red book), **чисте біле вікно** (a clean white window). The pattern you learned today carries forward into every module that follows. Gender agreement is the backbone of Ukrainian adjectives — and you already have it.

Now it is your turn. Write three sentences describing your real room or your desk using today's adjectives. Use one masculine noun with an adjective, one feminine noun with an adjective, and one neuter noun with an adjective. Connect at least one pair with **і** or **а**. No English — think directly in Ukrainian. Ask yourself: **Який мій стіл?** → **Мій стіл ____.** **Яка моя кімната?** → **Моя кімната ____.** **Яке моє вікно?** → **Моє вікно ____.** Fill in the blanks. Describe, don't translate.

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
