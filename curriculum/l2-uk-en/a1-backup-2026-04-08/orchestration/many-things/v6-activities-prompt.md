<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/many-things.yaml` file for module **13: Many Things** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-plural -->`
- `<!-- INJECT_ACTIVITY: fill-in-adj-plural -->`
- `<!-- INJECT_ACTIVITY: quiz-plural-adj -->`
- `<!-- INJECT_ACTIVITY: group-sort-singular-plural -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Make it plural: стіл → столи, книга → книги, вікно → вікна'
  items: 10
  type: fill-in
- focus: 'Choose the correct plural: стіл → столи/стола/столів?'
  items: 8
  type: quiz
- focus: 'Adjective agreement in plural: нов__ книги, велик__ столи, чист__ вікна'
  items: 8
  type: fill-in
- focus: Sort words into однина (singular) and множина (plural)
  items: 12
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- ручки (pens — pl of ручка)
- сумки (bags — pl of сумка)
- лампи (lamps — pl of лампа)
- зошити (notebooks — pl of зошит)
- дзеркала (mirrors — pl of дзеркало)
- крісла (armchairs — pl of крісло)
- речі (things — pl of річ)
required:
- столи (tables — pl of стіл)
- книги (books — pl of книга)
- вікна (windows — pl of вікно)
- стільці (chairs — pl of стілець)
- ці (these — pl of цей/ця/це)
- ті (those — pl of той/та/те)
- мої (my — plural)
- які (what kind? — plural)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Олена and Іван are setting up a classroom for a Ukrainian lesson. Desks are bare, supplies are in boxes, and everything needs to be counted and arranged before students arrive.

> **Іван:** Що тут є? *(What's here?)*
> **Олена:** Столи, стільці і вікна. *(Tables, chairs, and windows.)*
> **Іван:** Які столи? *(What kind of tables?)*
> **Олена:** Столи великі й нові. А стільці — старі. *(The tables are big and new. But the chairs are old.)*
> **Іван:** А вікна? *(And the windows?)*
> **Олена:** Вікна чисті. *(The windows are clean.)*

Notice what just happened. Іван didn't ask about one table — he asked about **столи** (tables), plural. Олена answered with plural adjectives: **великі** (big), **нові** (new), **старі** (old), **чисті** (clean). Every adjective in the plural ended in **-і**. That pattern is not a coincidence — it's a rule you'll learn in this module.

Now they need supplies. Олена checks the school supply cabinet.

> **Олена:** У вас є ручки? *(Do you have pens?)*
> **Іван:** Так! Які ручки — червоні чи сині? *(Yes! What kind of pens — red or blue?)*
> **Олена:** Сині. І ще зошити. *(Blue. And also notebooks.)*
> **Іван:** Скільки зошитів? *(How many notebooks?)*
> **Олена:** Три зошити. *(Three notebooks.)*
> **Іван:** А олівці є? *(Are there pencils?)*
> **Олена:** Є. Ось жовті олівці й чорні олівці. *(Yes. Here are yellow pencils and black pencils.)*

Plurals appeared naturally throughout both dialogues. One **ручка** (pen) became **ручки** (pens). One **зошит** (notebook) became **зошити** (notebooks). One **олівець** (pencil) became **олівці** (pencils). Two patterns emerged: masculine and feminine nouns took **-и** or **-і** endings, while neuter nouns like **вікно** became **вікна** with **-а**. The next section explains why these patterns work the way they do.

## Один → багато (Singular → Plural)

Ukrainian nouns have two numbers: **однина** (singular) and **множина** (plural). A noun naming one object is in однина; a noun naming two or more is in множина. As Большакова puts it in her Grade 2 textbook (p. 18): "один предмет → багато предметів" — one object becomes many objects. There are three main plural patterns, organized by gender.

**Masculine nouns** typically take **-и** or **-і** in the plural:

| Singular | → | Plural |
|----------|---|--------|
| стіл (m) — table | → | столи — tables |
| телефон (m) — phone | → | телефони — phones |
| зошит (m) — notebook | → | зошити — notebooks |
| стілець (m) — chair | → | стільці — chairs |
| олівець (m) — pencil | → | олівці — pencils |
| підручник (m) — textbook | → | підручники — textbooks |

Most masculine nouns take **-и**. Nouns with a soft consonant at the end — like **стілець** and **олівець** — take **-і** instead. Notice how the **е** in the suffix disappears: стілець → стільці, олівець → олівці.

**Feminine nouns** also take **-и** or **-і** in the plural:

| Singular | → | Plural |
|----------|---|--------|
| книга (f) — book | → | книги — books |
| ручка (f) — pen | → | ручки — pens |
| лампа (f) — lamp | → | лампи — lamps |
| сумка (f) — bag | → | сумки — bags |
| карта (f) — map | → | карти — maps |
| дошка (f) — board | → | дошки — boards |

A useful guideline: after **г**, **к**, **х**, the plural vowel is **-и** (книга → книги, ручка → ручки, дошка → дошки). This isn't an absolute rule, but it covers most feminine nouns you'll encounter at this level.

**Neuter nouns** take **-а** in the plural:

| Singular | → | Plural |
|----------|---|--------|
| вікно (n) — window | → | вікна — windows |
| крісло (n) — armchair | → | крісла — armchairs |
| ліжко (n) — bed | → | ліжка — beds |
| дзеркало (n) — mirror | → | дзеркала — mirrors |
| слово (n) — word | → | слова — words |

The pattern is clean: drop **-о**, add **-а**. Neuter plurals are the most predictable group — learn this one pattern and it covers most neuter nouns from modules 8 through 12.

One honest caveat: Ukrainian plurals do have exceptions. The word **річ** (thing) becomes **речі** (things) — not a standard pattern. At this stage, learn each plural alongside its singular as one unit. Full declension rules come at B1.

<!-- INJECT_ACTIVITY: fill-in-plural -->

## Прикметники у множині (Adjectives in Plural)

Here is the single most useful fact about Ukrainian adjective plurals: in singular, adjectives change ending by gender — **великий** (m), **велика** (f), **велике** (n). In plural, all three genders collapse into one form: **великі**. Большакова's Grade 2 textbook (p. 42) shows this with a clear table: "який/яка/яке → які, веселий/весела/веселе → веселі." This is simpler than singular — one ending covers everything.

Three adjectives you already know, applied across all genders:

| Singular (m / f / n) | → | Plural |
|---|---|---|
| новий стіл / нова книга / нове вікно | → | нові столи / нові книги / нові вікна |
| великий стілець / велика лампа / велике крісло | → | великі стільці / великі лампи / великі крісла |
| старий олівець / стара сумка / старе ліжко | → | старі олівці / старі сумки / старі ліжка |

The ending is always **-і**. No exceptions, no gender checks, no surprises.

<!-- INJECT_ACTIVITY: fill-in-adj-plural -->

Colors work the same way. Apply the **-і** rule to the color adjectives from Module 10: **червоні ручки** (red pens), **сині зошити** (blue notebooks), **білі стіни** (white walls), **чорні стільці** (black chairs), **жовті олівці** (yellow pencils), **зелені дошки** (green boards). Color adjectives follow the exact same pattern — no special rules. Try it yourself: look around your room. Які стільці? Які стіни? Які речі на столі?

Demonstratives and possessives also have plural forms, and they follow the same simplification. Singular **цей/ця/це** (this) becomes **ці** (these). Singular **той/та/те** (that) becomes **ті** (those). Singular **мій/моя/моє** (my) becomes **мої** (my, plural).

- **Ці столи великі.** *(These tables are big.)*
- **Ці книги нові.** *(These books are new.)*
- **Ці вікна чисті.** *(These windows are clean.)*
- **Ті стільці старі.** *(Those chairs are old.)*
- **Ті крісла червоні.** *(Those armchairs are red.)*
- **Мої ручки сині.** *(My pens are blue.)*
- **Мої зошити нові.** *(My notebooks are new.)*

<!-- INJECT_ACTIVITY: quiz-plural-adj -->

## Підсумок — Summary

Three patterns covered today. For nouns: masculine and feminine take **-и** or **-і** in the plural (**столи**, **книги**, **стільці**); neuter takes **-а** (**вікна**, **крісла**, **дзеркала**). For adjectives: the plural ending is always **-і**, regardless of the noun's gender — **великі столи**, **великі книги**, **великі вікна**. For demonstratives: **ці** (these) and **ті** (those). For possessives: **мої** (my, plural). The elegant economy here is worth appreciating: plural adjectives have one form. Ukrainian makes this easier than singular.

**Self-check — test yourself:**

- Як утворити множину від **стіл**? → **столи**
- Як утворити множину від **книга**? → **книги**
- Як утворити множину від **вікно**? → **вікна**
- Як утворити множину від **стілець**? → **стільці**
- Яке закінчення мають прикметники у множині? → завжди **-і**
- Як сказати "these chairs"? → **ці стільці**
- Як сказати "my pens"? → **мої ручки**
- Утвори множину: великий стіл → ? → **великі столи**

<!-- INJECT_ACTIVITY: group-sort-singular-plural -->

Now put it all together. Describe your own space using today's patterns. Start with these questions as scaffolding: Які столи у вашому класі? Які стільці? Які вікна? Які речі на вашому столі? Here is a model answer:

- **У моєму класі є великі столи і старі стільці.** *(In my classroom there are big tables and old chairs.)*
- **Вікна чисті.** *(The windows are clean.)*
- **На моєму столі є сині ручки і нові зошити.** *(On my desk there are blue pens and new notebooks.)*
- **А ще маленький підручник.** *(And also a small textbook.)*

Write 3–4 sentences about your own room or classroom using plural nouns and plural adjectives. Use **ці** or **ті** to point at specific groups of objects. Use **мої** to claim ownership.

In Module 14 — the A1.2 Checkpoint — you'll combine everything from this phase: rooms, objects, colors, numbers, this and that, and now plurals. The **-і** adjective plural you learned today will appear in every description from here on. After the checkpoint, A1.3 introduces verbs — and plurals matter there too. When someone reads, it's not just one book: **вони читають книги** (they read books). Plural nouns and adjectives are the backbone of real sentences.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: many-things
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

**Level: A1.2-A1.3 (Module 13/55) — EARLY BEGINNER**

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

### Pattern: general-vocabulary
- **match-up** — Слово → переклад: Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Fill in the missing word from context
- **anagram** — Склади слово: Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Choose correct translation from options

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
