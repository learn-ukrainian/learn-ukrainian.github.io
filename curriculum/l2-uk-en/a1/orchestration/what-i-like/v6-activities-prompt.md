<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/what-i-like.yaml` file for module **15: What I Like** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-infinitive-picture -->`
- `<!-- INJECT_ACTIVITY: match-infinitives-meanings -->`
- `<!-- INJECT_ACTIVITY: fill-in-infinitive-picture -->`
- `<!-- INJECT_ACTIVITY: quiz-structure-choice -->`
- `<!-- INJECT_ACTIVITY: fill-in-negative -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Complete: Я люблю ___. (choose infinitive for the picture)'
  items: 8
  type: fill-in
- focus: Люблю or подобається? Choose the right structure.
  items: 8
  type: quiz
- focus: 'Match infinitives to their meanings: читати ↔ to read'
  items: 8
  type: match-up
- focus: 'Make it negative: Я люблю → Я не люблю'
  items: 6
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- малювати (to draw)
- подорожувати (to travel)
- співати (to sing)
- музика (music, f)
- фільм (film, m)
- книга (book — review from M08)
required:
- любити (to love/like — verb)
- подобатися (to be pleasing — used as 'to like')
- читати (to read)
- гуляти (to walk)
- готувати (to cook)
- слухати (to listen)
- дивитися (to watch)
- грати (to play)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Анна walks into a cozy language café in Kyiv for her very first tandem session. Her partner Віктор is already waiting at the table, two cups of tea steaming between them.

> **Віктор:** Привіт, Анно! Що ти любиш робити? *(Hi, Anna! What do you like to do?)*
> **Анна:** Я люблю читати і слухати музику. *(I like to read and listen to music.)*
> **Віктор:** Цікаво! А ще? *(Interesting! And what else?)*
> **Анна:** Люблю гуляти в парку. А ти? *(I like to walk in the park. And you?)*
> **Віктор:** Я люблю готувати. *(I like to cook.)*
> **Анна:** Правда? Що ти готуєш? *(Really? What do you cook?)*
> **Віктор:** Борщ і вареники. *(Borshch and varenyky.)*
> **Анна:** Смачно! *(Delicious!)*

Did you spot the pattern? Every time Анна and Віктор talk about what they enjoy, the verb after **люблю** (I like) ends in **-ти**: **читати** (to read), **слухати** (to listen), **гуляти** (to walk), **готувати** (to cook). That **-ти** ending is your clue — it marks the infinitive, the base form of any Ukrainian verb.

Now Віктор changes the subject:

> **Віктор:** Тобі подобається ця книга? *(Do you like this book?)*
> **Анна:** Так, мені подобається. Дуже цікава. *(Yes, I like it. Very interesting.)*
> **Віктор:** А цей фільм? *(And this film?)*
> **Анна:** Ні, мені не подобається. *(No, I don't like it.)*
> **Віктор:** А музика? *(And music?)*
> **Анна:** О, так! Мені подобається джаз. *(Oh, yes! I like jazz.)*
> **Віктор:** Мені теж подобається музика! *(I also like music!)*
> **Анна:** Чудово! *(Wonderful!)*

You just met two different phrases for "I like" — **люблю** followed by a verb, and **мені подобається** (I like) followed by a thing. The next two sections show you exactly how each one works.

<!-- INJECT_ACTIVITY: fill-in-infinitive-picture -->

## Я люблю... (I Like...)

When you want to say you enjoy *doing* something, Ukrainian uses a simple formula: **Я люблю** (I like/love) plus a verb in the infinitive. The infinitive is the dictionary form — the one that always ends in **-ти**. Here it is in action:

- **Я люблю читати.** — I like to read.
- **Я люблю гуляти.** — I like to walk.
- **Я люблю готувати.** — I like to cook.
- **Я люблю слухати музику.** — I like to listen to music.

The structure never changes: subject + **люблю** + infinitive. The infinitive is the raw building block — you will use it with other verbs too (like **хотіти** — to want), but **люблю** is your first chance to put it to work.

Every Ukrainian infinitive ends in **-ти**. This is one of the most reliable patterns in the language — when you see **-ти** at the end of a word, you are looking at a verb in its base form. Here are the core hobby verbs for this module:

| Ukrainian | English |
|-----------|---------|
| **читати** | to read |
| **гуляти** | to walk, to hang out |
| **готувати** | to cook |
| **слухати** | to listen |
| **дивитися** | to watch |
| **грати** | to play (a game, an instrument) |

One thing to be aware of: stress varies from verb to verb. There is no single rule — you learn each one as a whole unit. You will hear the natural stress in the pronunciation videos.

<!-- INJECT_ACTIVITY: match-infinitives-meanings -->

Now let's add more hobby verbs to your toolkit, each one inside the **Я люблю...** frame so you can use them right away:

- **Я люблю малювати.** — I like to draw.
- **Я люблю подорожувати.** — I like to travel.
- **Я люблю співати.** — I like to sing.
- **Я люблю грати в ігри.** — I like to play games.
- **Я люблю дивитися фільми.** — I like to watch films.

Notice that **грати** (to play) needs context: **грати в шахи** (to play chess), **грати на гітарі** (to play guitar), **грати в ігри** (to play games). It is not a one-size-fits-all "play" — Ukrainian is more specific about *what* you play. At this stage, just learn the chunks: **грати в** + a game, **грати на** + an instrument.

You can also talk about other people. The verb **любити** changes its ending depending on who is doing the liking. For now, just two forms: **Я люблю** (I like) and **моя подруга любить** (my friend likes) or **мій брат любить** (my brother likes). Try building your own sentence: **Я люблю** + one infinitive from the list above.

<!-- INJECT_ACTIVITY: fill-in-infinitive-picture -->

## Мені подобається... (I Like...)

Ukrainian has two ways to say "I like," and each one works with different things. Here is the key distinction:

- **Я люблю + infinitive** = I like *doing* something (an activity).
- **Мені подобається + noun** = I like *something* (a thing, a place, a work).

Compare these pairs to feel the difference:

- **Я люблю читати.** (I like to read.) → activity
- **Мені подобається ця книга.** (I like this book.) → thing
- **Я люблю слухати музику.** (I like to listen to music.) → activity
- **Мені подобається джаз.** (I like jazz.) → thing

The phrase **мені подобається** (I like / it pleases me) works as a fixed chunk. You don't need to analyze why it uses **мені** — that grammar comes much later. For now, simply plug in a noun after it:

- **Мені подобається Київ.** — I like Kyiv. *(place)*
- **Мені подобається цей парк.** — I like this park. *(place)*
- **Мені подобається ця книга.** — I like this book. *(thing)*
- **Мені подобається кава.** — I like coffee. *(thing)*
- **Мені подобається цей фільм.** — I like this film. *(entertainment)*
- **Мені подобається класична музика.** — I like classical music. *(entertainment)*

<!-- INJECT_ACTIVITY: quiz-structure-choice -->

To say you *don't* like something, place **не** directly before the verb in both structures:

- **Я не люблю готувати.** — I don't like to cook.
- **Мені не подобається цей фільм.** — I don't like this film.

Here is a real exchange from a Ukrainian textbook (Авраменко, Grade 5):

> **Інна:** Я не люблю мити посуд. *(I don't like to wash dishes.)*
> **Зоя:** А мені не подобається гладити. *(And I don't like to iron.)*

See how natural that sounds? Two friends sharing what they *don't* enjoy — **не люблю** + infinitive and **мені не подобається** + infinitive, side by side. The word **не** always goes right before the verb.

To ask questions, simply use a rising intonation — no word-order change needed. **Ти любиш читати?** (Do you like to read?) **Тобі подобається?** (Do you like it?) You may have noticed that **люблю** changes to **любиш** for **ти** (you). Full conjugation of this verb group comes in M17 — for now, memorize just two forms: **я люблю**, **ти любиш**.

<!-- INJECT_ACTIVITY: fill-in-negative -->

## Підсумок — Summary

You now have two structures for "I like" in Ukrainian. **Я люблю + infinitive (-ти)** is for activities you enjoy doing: reading, cooking, walking, singing. **Мені подобається + noun** is for things, places, or works you like: a book, a city, a film, jazz. Both are negated the same way — place **не** directly before the verb: **Я не люблю**, **мені не подобається**. One more thing to remember: **люблю** changes form by person (**я люблю** / **ти любиш**), but **мені подобається** stays the same — when you switch to "you," only the first word changes: **тобі подобається**.

Test yourself with these questions:

- **Що ти любиш робити?** *(What do you like to do?)* → **Я люблю ___.** Pick three infinitives from the module: **читати**, **гуляти**, **готувати**, **слухати**, **малювати**, **подорожувати**, **співати**...
- **Що тобі подобається?** *(What do you like?)* → **Мені подобається ___.** Pick a place and a thing: **Київ**, **ця книга**, **кава**, **джаз**...
- **Що ти не любиш?** *(What don't you like?)* → **Я не люблю ___.** Name one activity.
- **Чи тобі подобається цей фільм?** *(Do you like this film?)* → **Так, мені подобається.** / **Ні, мені не подобається.**
- **Як сказати "I like jazz"?** → **Мені подобається джаз.** (It's a thing, not an activity — so **подобається**, not **люблю**.)
- **Як сказати "I like to sing"?** → **Я люблю співати.** (It's an activity — so **люблю** + infinitive.)

In M16, you will learn Group I verb conjugation — verbs like **читати** and **слухати** will gain personal endings so you can say **Я читаю** (I read) and **Ти слухаєш** (you listen), not just **Я люблю читати**. The infinitives you learned today are the raw material for everything that comes next. As a Ukrainian textbook puts it: «Люблю гортати старі книги, бо від них віє спокоєм» — *I like to leaf through old books because they breathe calmness* (Голуб, Grade 5). That sentence uses the exact same pattern you just learned. You are ready.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: what-i-like
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

**Level: A1.2-A1.3 (Module 15/55) — EARLY BEGINNER**

The learner knows the alphabet and ~200 words. They:
- Can read Ukrainian slowly
- Know basic nouns, adjectives, simple verb forms
- Cannot handle complex sentences or grammar terminology in Ukrainian

**Instructions in simple English with Ukrainian key terms in bold.**
Example: 'Choose the correct form of **мій/моя/моє**'

**Good activity types:** quiz, fill-in (simple sentences), match-up, group-sort, true-false, observe, anagram, translate (English→Ukrainian).


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
