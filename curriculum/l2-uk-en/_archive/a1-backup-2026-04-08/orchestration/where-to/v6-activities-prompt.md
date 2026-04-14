<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/where-to.yaml` file for module **31: Where To?** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in -->`
- `<!-- INJECT_ACTIVITY: group-sort -->`
- `<!-- INJECT_ACTIVITY: quiz-motion-verbs -->`
- `<!-- INJECT_ACTIVITY: quiz-de-kudy -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Де or Куди? Choose the right question for each sentence.
  items: 8
  type: quiz
- focus: 'Complete: Я йду ___ (школа). Він у ___ (банк).'
  items: 10
  type: fill-in
- focus: 'Sort phrases: Де? (locative) vs Куди? (accusative)'
  items: 10
  type: group-sort
- focus: Йти or їхати? Choose based on distance/transport.
  items: 6
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- магазин → у/в магазин (to the shop)
- бібліотека → у бібліотеку (to the library)
- ресторан → у ресторан (to the restaurant)
- Одеса → в Одесу (to Odesa)
- повертатися → додому (to return home)
required:
- куди (where to)
- йти (to go on foot)
- їхати (to go by transport)
- школа → у школу (to school)
- робота → на роботу (to work)
- банк → у банк (to the bank)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

It's Saturday morning. Оксана and Степан stand outside their apartment building, planning the day. They have a long list of errands — and not enough time to do them together. The obvious question: **Куди ти йдеш?** (Where are you going?)

> **Оксана:** Куди ти йдеш? *(Where are you going?)*
> **Степан:** Я йду в банк. А ти? *(I'm going to the bank. And you?)*
> **Оксана:** Я йду на пошту. А потім? *(I'm going to the post office. And then?)*
> **Степан:** Потім іду в аптеку. А ти? *(Then I'm going to the pharmacy. And you?)*
> **Оксана:** Я йду у бібліотеку. *(I'm going to the library.)*
> **Степан:** Добре. *(Good.)*
> **Оксана:** А потім ходімо в кафе! *(And then let's go to a café!)*
> **Степан:** Добре! Зустрінемося в кафе о третій. *(Good! Let's meet at the café at three.)*

Look at every destination in that conversation. Each one follows the same pattern: a verb of motion + **в** or **на** + the place name. **Я йду в банк** — I'm going TO the bank. **Я йду на пошту** — I'm going TO the post office. But notice Степан's last line: **зустрінемося в кафе** (we'll meet AT the café) — he's already talking about being THERE, not going there.

:::tip
**В банк** (direction — going there) vs **в банку** (location — already there). Same preposition **в**, but the noun ending changes. This is the whole lesson in one pair.
:::

Later that evening, the two friends talk about weekend travel plans.

> **Степан:** Куди ти їдеш у суботу? *(Where are you going on Saturday?)*
> **Оксана:** Я їду у Львів. *(I'm going to Lviv.)*
> **Степан:** А Олена? *(And Olena?)*
> **Оксана:** Вона їде в Одесу. *(She's going to Odesa.)*
> **Степан:** А Микола? *(And Mykola?)*
> **Оксана:** Він залишається вдома. А ти? *(He's staying home. And you?)*

Two verbs appeared in these dialogues: **йти** (to go on foot) — for local errands like **в банк** and **на пошту** — and **їхати** (to go by transport) — for cities like **у Львів** and **в Одесу**. Both take the same pattern: **в/на** + the place you're heading to, answering the question **Куди?** (Where to?).

## Куди? Знахідний відмінок (Where To? Accusative)

Ukrainian schoolchildren learn their cases with helper words. For the accusative — **знахідний відмінок** — the helper is **«бачу»** (I see): Зн.в. (бачу) — кого? що? Try it: **бачу банк**, **бачу школу**, **бачу кафе**. Whatever form the noun takes after **бачу** is its accusative form. For direction, Ukrainian simply adds **в/у** or **на** before that same accusative form: **в банк**, **у школу**, **у кафе**. That's **Куди?** (Where to?).

Here is the core contrast, built around one noun. Take **банк** (bank):

- **Де ти?** — **Я в банку.** *(Where are you? — I'm at the bank.)* — locative case, static position
- **Куди ти йдеш?** — **Я йду в банк.** *(Where are you going? — I'm going to the bank.)* — accusative case, motion toward

Same preposition **в**, same noun **банк** — but **банку** vs **банк**. The ending on the noun signals whether you are already there or moving toward it. The same contrast works with **школа** (school): **Де?** — **в школі** (locative). **Куди?** — **у школу** (accusative).

Now for the endings. As Grade 4 Ukrainian textbooks teach: masculine inanimate nouns and neuter nouns look identical in the accusative and nominative. Only feminine nouns change their ending.

| Gender | Rule | Examples |
|--------|------|----------|
| Masculine (inanimate) | = nominative (no change) | банк → в банк, магазин → у магазин, парк → у парк, ресторан → у ресторан |
| Feminine (-а/-я → -у/-ю) | final vowel shifts | школа → у школу, робота → на роботу, бібліотека → у бібліотеку, аптека → в аптеку |
| Neuter | = nominative (no change) | кафе → у кафе, місто → у місто |

Masculine and neuter nouns require no work at all — the accusative form is the same as the nominative. Only feminine nouns shift their ending: **-а** becomes **-у**, and **-я** becomes **-ю**. Think of feminine nouns as "leaning forward" toward their destination — **школа** stretches to **школу**, **бібліотека** reaches out to **бібліотеку**, **пошта** becomes **пошту**. If a place name ends in **-а** or **-я**, swap it for **-у** or **-ю**. Everything else stays exactly the same.

<!-- INJECT_ACTIVITY: fill-in -->

## Де чи куди? (Where or Where To?)

Ukrainian distinguishes two questions about location. **Де ти?** (Where are you?) describes a static position — no movement. It always uses the locative case after **в/у/на**. **Куди ти йдеш?** (Where are you going?) describes direction — movement toward a place. It always uses the accusative case after **в/у/на**. The prepositions **в**, **у**, and **на** appear in both — it is the noun ending that tells the listener whether you mean position or motion.

Here are six everyday places, each shown in both cases:

| Place | Де? (locative) | Куди? (accusative) |
|-------|----------------|---------------------|
| школа | в школі | у школу |
| робота | на роботі | на роботу |
| банк | у банку | у банк |
| парк | у парку | у парк |
| бібліотека | у бібліотеці | у бібліотеку |
| магазин | у магазині | у магазин |

Notice that **робота** uses **на** (not **в**) in both columns — **на роботі**, **на роботу**. You learned this pattern in the previous module: certain places always take **на**. The preposition stays the same whether the question is **Де?** or **Куди?** — only the noun ending changes.

<!-- INJECT_ACTIVITY: group-sort -->

Both **йти** and **їхати** answer **Куди?**, but they signal different means of getting there.

**Йти** (on foot) — for places within walking distance:

- **Я йду в магазин.** *(I'm going to the store.)*
- **Ти йдеш на зупинку.** *(You're going to the bus stop.)*
- **Він іде у бібліотеку.** *(He's going to the library.)*

**Їхати** (by vehicle) — when a bus, train, or car is involved:

- **Я їду на вокзал.** *(I'm going to the train station.)*
- **Ми їдемо у Львів.** *(We're going to Lviv.)*
- **Вона їде в Одесу.** *(She's going to Odesa.)*

Quick conjugation reminder: **йду, йдеш, іде** and **їду, їдеш, їде**.

A simple rule of thumb: if you can walk there in ten minutes, Ukrainian speakers typically say **йти**. Cities, other towns, train stations — that's **їхати**. But both verbs take **в/на** + accusative. The noun endings work exactly the same way regardless of which verb you choose.

<!-- INJECT_ACTIVITY: quiz-motion-verbs -->

<!-- INJECT_ACTIVITY: quiz-de-kudy -->

## Підсумок — Summary

Ukrainian has two distinct questions for talking about places. **Де?** (Where?) uses the locative case — you are already there, standing still. **Куди?** (Where to?) uses the accusative case — you are moving toward that place. Both questions use the same prepositions **в/у/на**. The noun ending is the only signal. When you hear the word after **в/у/на**, ask yourself: am I there, or am I going there?

Here are the accusative endings one more time, with examples:

**Masculine inanimate → no change:** банк → **у банк**, парк → **у парк**, магазин → **у магазин**, ресторан → **у ресторан**. **Neuter → no change:** кафе → **у кафе**, місто → **у місто**. **Feminine → -а/-я becomes -у/-ю:** школа → **у школу**, робота → **на роботу**, бібліотека → **у бібліотеку**, аптека → **в аптеку**, пошта → **на пошту**. Masculine and neuter require no work. Feminine: swap the final vowel.

Two motion verbs carry you to your destination. **Йти** (on foot): **я йду, ти йдеш, він/вона іде** + accusative direction — **у школу, в магазин, на пошту**. **Їхати** (by transport): **я їду, ти їдеш, він/вона їде** + accusative direction — **у Львів, на вокзал, в Одесу**. Both verbs answer **Куди ти йдеш/їдеш?** Both take **в/на** + accusative.

### Self-Check

- **Де ти?** → Use locative: **Я в банку.** / **Я у школі.** / **Я на роботі.**
- **Куди ти йдеш?** → Use accusative: **Я йду в банк.** / **Я йду у школу.** / **Я йду на роботу.**
- Is the place masculine or neuter? → No change in accusative (**банк, кафе, місто**).
- Is the place feminine (-а/-я)? → Swap to -у/-ю (**школа → школу, бібліотека → бібліотеку**).
- Walking or riding? → **Йти** on foot, **їхати** by vehicle — same accusative either way.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: where-to
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

**Level: A1.4+ (Module 31/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-cases
- **fill-in** — Який відмінок?: Fill in the correct case ending for a noun in context
  - Instruction: *Вставте іменник у правильній формі*
- **quiz** — Визнач відмінок: Identify which case a highlighted noun is in
- **group-sort** — Розподіли за відмінками: Sort noun forms by their case
- **error-correction** — Знайди помилку у відмінку: Find wrong case ending and correct it

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
