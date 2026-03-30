<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-my-world.yaml` file for module **14: Checkpoint: My World** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-gender-agreement -->`
- `<!-- INJECT_ACTIVITY: fill-in-shopping-dialogue -->`
- `<!-- INJECT_ACTIVITY: group-sort-vocabulary -->`
- `<!-- INJECT_ACTIVITY: quiz-singular-plural -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Mixed gender/agreement review: choose correct form for noun+adjective pairs'
  items: 10
  type: quiz
- focus: Complete the shopping dialogue with correct demonstratives, adjectives, and
    numbers
  items: 8
  type: fill-in
- focus: 'Sort vocabulary from M08-M13 by category: objects, colors, numbers'
  items: 12
  type: group-sort
- focus: Singular or plural? Transform sentences from singular to plural
  items: 8
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended: []
required: []


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Що ми знаємо? (What Do We Know?)

You have completed A1.2 — six modules covering the building blocks of describing your world in Ukrainian. Before moving forward, take a moment to check whether the skills from M08–M13 have stuck. Work through each self-check question honestly. If any answer feels uncertain, the grammar summary and reading practice below will help you solidify it.

**Self-check — one question per module:**

- **M08 — Gender:** What gender is **стіл** (table)? **книга** (book)? **вікно** (window)? Test with pronouns: **він** (he) → **стіл** is masculine. **вона** (she) → **книга** is feminine. **воно** (it) → **вікно** is neuter.

- **M09 — Adjectives:** What does **великий стіл** (big table) / **велика книга** (big book) / **велике вікно** (big window) show? The adjective ending changes to agree with the noun's gender: **-ий** for masculine, **-а** for feminine, **-е** for neuter.

- **M10 — Colors:** What are the two Ukrainian words for "blue"? **Синій** means dark or navy blue. **Блакитний** means sky blue or light blue. Two separate words — not one.

- **M11 — Numbers and prices:** How do you say "twenty hryvnias"? **Двадцять гривень**. Numbers are vocabulary — memorize each one as a word, not a formula.

- **M12 — Demonstratives:** How do you say "this table" / "this lamp" / "this window"? **Цей стіл** / **ця лампа** / **це вікно**. The demonstrative matches the noun's gender, just like adjectives.

- **M13 — Plurals:** How do you make **стіл**, **книга**, **вікно** plural? **Столи**, **книги**, **вікна**. Masculine and feminine nouns take **-и/-і**, neuter nouns take **-а**.

Six questions, six patterns — these are the grammar tools that drive every sentence in this module. If you answered all six correctly, you are ready for A1.3. If one or two felt shaky, read the sections below carefully. Then come back and try the self-check again.

<!-- INJECT_ACTIVITY: quiz-gender-agreement -->

## Читання (Reading Practice)

Read the text below aloud — slowly, one sentence at a time. Every word comes from M08–M13. There is no new vocabulary here. Your goal is to understand without translating word by word. If you can picture what the room looks like as you read, you are reading Ukrainian.

> **Це моя кімната.** *(This is my room.)*
> **Мій стіл великий і коричневий.** *(My table is big and brown.)*
> **На столі є три книги.** *(On the table there are three books.)*
> **Ці книги нові й цікаві.** *(These books are new and interesting.)*
> **Моя лампа маленька і біла.** *(My lamp is small and white.)*
> **А та лампа жовта.** *(And that lamp is yellow.)*
> **Вікна великі.** *(The windows are big.)*
> **Мої стіни білі.** *(My walls are white.)*
> **Ця сумка синя, а та червона.** *(This bag is navy blue, and that one is red.)*
> **У мене є два зошити.** *(I have two notebooks.)*
> **У мене є чотири олівці.** *(I have four pencils.)*
> **Олівці жовті й сині.** *(The pencils are yellow and blue.)*
> **Це моє вікно.** *(This is my window.)*
> **За вікном є парк.** *(Beyond the window there is a park.)*
> **Парк гарний.** *(The park is nice.)*

Now check your comprehension — answer these three questions mentally, in Ukrainian if you can:

- **Який стіл?** (What is the table like?) → **великий і коричневий** (big and brown)
- **Скільки книг на столі?** (How many books on the table?) → **три** (three)
- **Яка маленька лампа?** (What is the small lamp like?) → **біла** (white)

The point is immediate confirmation: Ukrainian text → understanding, with no English translation step in between. If you answered all three without scrolling back up, your reading is working.

## Граматика (Grammar Summary)

**Gender and agreement.** The **він/вона/воно** test works like this: replace the noun with a pronoun — whichever fits tells you the gender. Endings follow a pattern. Consonant-final nouns are masculine — **він**: **стіл**, **глечик** (jug). Nouns ending in **-а/-я** are feminine — **вона**: **книга**, **вишиванка** (embroidered shirt). Nouns ending in **-о/-е** are neuter — **воно**: **вікно**, **намисто** (necklace). The adjective ending must always match: **великий стіл** / **велика книга** / **велике вікно**.

**Hard vs. soft adjective stems.** Most adjectives use hard endings: **червоний** (red), **новий** (new), **великий** (big) — all end in **-ий**. Adjectives with soft stems use **-ій** instead: **синій** (navy blue), **останній** (last). The difference is the stem's final consonant — the **н** in **синій** is soft. Rule of thumb: if the masculine form ends in **-ій**, it is a soft-stem adjective; if it ends in **-ий**, it is hard.

**Demonstratives.** **Цей/ця/це** (this — close to the speaker) and **той/та/те** (that — further away) agree with noun gender: **цей глечик** (m), **ця вишиванка** (f), **це намисто** (n); **той глечик**, **та вишиванка**, **те намисто**. The plural forms are **ці** (these) and **ті** (those) for all genders.

**Nominative plurals.** Masculine and feminine nouns take **-и** or **-і**: **столи** (tables), **книги** (books), **олівці** (pencils). Neuter nouns take **-а** or **-я**: **вікна** (windows), **поля** (fields). Adjectives in the plural always end in **-і** regardless of noun gender: **великі столи**, **великі книги**, **великі вікна**.

**Numbers as vocabulary.** At this stage, treat numbers as standalone words — no morphology rules needed yet. For counting objects: **один зошит** (one notebook), **два зошити** (two notebooks), **п'ять зошитів** (five notebooks). For prices: **двадцять гривень** (twenty hryvnias), **сто гривень** (one hundred hryvnias), **двісті гривень** (two hundred hryvnias). Memorize the forms you have seen rather than trying to derive them.

<!-- INJECT_ACTIVITY: fill-in-shopping-dialogue -->

## Діалог (Connected Dialogue)

Іванко is visiting a Ukrainian **ярмарок** (outdoor street market) — a lively fair selling handmade crafts. His friend Катя is helping him choose souvenirs. The table in front of them is covered with **вишиванки** (embroidered shirts), **глечики** (jugs), **намисто** (necklaces), and **писанки** (decorated eggs). Іванко wants to buy something, but he needs to ask about colors, sizes, and prices — everything from A1.2.

> **Іванко:** Катю, дивись! Що це? *(Katia, look! What is this?)*
> **Катя:** Це вишиванка. Вона дуже гарна. *(This is a vyshyvanka. It is very beautiful.)*
> **Іванко:** Яка ця вишиванка — біла чи жовта? *(What is this vyshyvanka like — white or yellow?)*
> **Катя:** Ця біла, а та жовта. *(This one is white, and that one is yellow.)*
> **Іванко:** Скільки вона коштує? *(How much does it cost?)*
> **Катя:** Триста гривень. *(Three hundred hryvnias.)*
> **Іванко:** А цей глечик? Він великий? *(And this jug? Is it big?)*
> **Катя:** Цей великий, а той маленький. *(This one is big, and that one is small.)*
> **Іванко:** Скільки коштує маленький? *(How much does the small one cost?)*
> **Катя:** Сто гривень. *(One hundred hryvnias.)*
> **Іванко:** Добре. А це що? Це намисто? *(Good. And what is this? Is this a necklace?)*
> **Катя:** Так, це намисто. Воно синє й біле. *(Yes, this is a necklace. It is blue and white.)*
> **Іванко:** Гарне! А ці писанки? *(Beautiful! And these pysanky?)*
> **Катя:** Одна писанка — двадцять п'ять гривень. *(One pysanka — twenty-five hryvnias.)*
> **Іванко:** Я хочу три писанки. *(I want three pysanky.)*
> **Катя:** Це сімдесят п'ять гривень. *(That is seventy-five hryvnias.)*
> **Іванко:** Правильно! Дякую, Катю. *(Correct! Thank you, Katia.)*
> **Катя:** Авжеж! Це українська традиція. *(Of course! This is a Ukrainian tradition.)*

Notice how gender drives every choice in this conversation. **Вона** refers to **вишиванка** (feminine) — so the adjectives are **біла**, **гарна**. **Він** refers to **глечик** (masculine) — so the adjectives are **великий**, **маленький**. **Воно** refers to **намисто** (neuter) — so the adjective is **синє й біле**. The demonstratives **цей/ця/це** appear throughout, always matching the noun's gender. Every price uses the number vocabulary from M11. This single dialogue puts all of A1.2 into action.

<!-- INJECT_ACTIVITY: group-sort-vocabulary -->

## Підсумок — Summary

You have completed A1.2 — My World. In six modules you built the grammar architecture for describing everything around you. You know how to determine noun gender using the **він/вона/воно** test. You can choose the right adjective ending based on gender and stem type — **-ий** for hard masculine, **-ій** for soft masculine, **-а/-я** for feminine, **-е/-є** for neuter. You know both Ukrainian blues: **синій** for navy and **блакитний** for sky blue. You can count objects and ask prices. You can point at things near and far with **цей/ця/це** and **той/та/те**. And you can speak about groups using plural forms with **-и/-і/-а**.

By the end of A1.2, you actively use over twenty objects with correct genders — **стіл** (m), **книга** (f), **вікно** (n), **вишиванка** (f), **глечик** (m), **намисто** (n), and many more. You know ten or more adjectives with full agreement: **великий/велика/велике**, **новий/нова/нове**, **червоний/червона/червоне**, **синій/синя/синє**. You use six demonstrative forms — **цей, ця, це, той, та, те** — and their plurals **ці** and **ті**. You handle numbers from one to a thousand as vocabulary. And you form plurals for all three genders.

What comes next? In A1.3 — *Actions* — you will meet Ukrainian verbs for the first time. What do you do? What do you like? The nouns and adjectives from A1.2 will combine with verbs to make real sentences about real life. The building blocks are ready — now they start to move.

Ukrainian is not built in one day. It is built in six modules at a time, then six more. You just finished the second set. The language is already yours to describe the world around you. **Молодець! Продовжуємо.** *(Well done! We continue.)*

<!-- INJECT_ACTIVITY: quiz-singular-plural -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-my-world
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

**Level: A1.2-A1.3 (Module 14/55) — EARLY BEGINNER**

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

### Pattern: grammar-numbers
- **quiz** — Яке число?: Recognize written number words
- **fill-in** — Напиши цифру словом: Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Match digits to their Ukrainian word forms

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
