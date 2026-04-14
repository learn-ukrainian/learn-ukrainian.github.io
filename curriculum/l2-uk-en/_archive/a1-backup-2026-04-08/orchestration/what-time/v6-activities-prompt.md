<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/what-time.yaml` file for module **22: What Time?** (a1).

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

- `<!-- INJECT_ACTIVITY: match-up-times -->`
- `<!-- INJECT_ACTIVITY: quiz-clock-faces -->`
- `<!-- INJECT_ACTIVITY: fill-in-o-kotrij -->`
- `<!-- INJECT_ACTIVITY: quiz-time-of-day -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Котра година? Match clock faces to spoken time.
  items: 8
  type: quiz
- focus: 'О котрій? Complete: Я снідаю о ___. (восьмій)'
  items: 8
  type: fill-in
- focus: 'Match times: 7:00 ↔ сьома, 9:00 ↔ дев''ята'
  items: 6
  type: match-up
- focus: Ранку, дня, or вечора? Choose the right time of day.
  items: 6
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- четверта, п'ята, шоста (4th, 5th, 6th)
- сьома, восьма, дев'ята (7th, 8th, 9th)
- десята, одинадцята, дванадцята (10th, 11th, 12th)
- пів (half)
- чверть (quarter)
- опівдні (at noon)
required:
- година (hour, f)
- котра (which — feminine, for time)
- перша, друга, третя (1st, 2nd, 3rd — feminine ordinals)
- ранок (morning, m)
- вечір (evening, m)
- день (day, m)
- ніч (night, f)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Ukrainian splits time into two questions. **Котра година?** (what time is it?) asks about *right now*. **О котрій?** (at what time?) asks about *when something happens*. Both questions appear in the dialogues below — spot them as you read.

### Діалог 1 — Зустріч (A Meeting)

> **Марина:** Алло, Олексію! Котра година? *(Hello, Oleksiy! What time is it?)*
> **Олексій:** Десята. *(Ten o'clock.)*
> **Марина:** О котрій ти зазвичай працюєш? *(What time do you usually work?)*
> **Олексій:** О дев'ятій. А ти? *(At nine. And you?)*
> **Марина:** Я працюю о десятій. *(I work at ten.)*
> **Олексій:** Зрозуміло. *(Got it.)*
> **Марина:** Може, зустрінемося о першій? *(Maybe we meet at one?)*
> **Олексій:** Зачекай хвилинку... Так, підходить! *(Wait a moment... Yes, that works!)*
> **Марина:** Добре, тоді о першій! *(Good, then at one!)*

Марина needs to find a gap in both schedules. She uses **Котра година?** to check the current time, then **О котрій ти працюєш?** to ask about Олексій's schedule. The final agreement — **тоді о першій** — is a chunk you'll use constantly: *тоді* (then) + the meeting time.

### Діалог 2 — Розклад дня (Daily Schedule)

> **Олексій:** Коли ти снідаєш? *(When do you eat breakfast?)*
> **Марина:** О восьмій ранку. *(At eight in the morning.)*
> **Олексій:** А обідаєш? *(And lunch?)*
> **Марина:** О першій дня. *(At one in the afternoon.)*
> **Олексій:** О котрій вечеряєш? *(What time do you eat dinner?)*
> **Марина:** О сьомій. А ти? *(At seven. And you?)*
> **Олексій:** Я вечеряю о восьмій вечора. *(I eat dinner at eight in the evening.)*

Here the verbs **снідати** (to eat breakfast), **обідати** (to eat lunch), and **вечеряти** (to eat dinner) connect directly with time expressions. These verbs appeared in A1.3 — now you're combining them with specific hours. Notice the time-of-day words after each hour: **ранку** (morning), **дня** (afternoon), **вечора** (evening). These remove ambiguity, just like "AM" and "PM" in English.

Two patterns emerged from both dialogues. First: **Котра година?** gets a bare ordinal answer — **Десята.** Second: **О котрій?** gets **о** plus a shifted form — **О десятій.** The same hour appears in two shapes: *десята* vs. *о десятій*. The ending flips from **-а** to **-ій**. The next sections break down exactly how each form works.

## Котра година? (What Time Is It?)

The question **Котра година?** literally asks "which hour?" The word **котра** (which) is feminine because **година** (hour) is a feminine noun. The answer is a feminine ordinal number — just the number, nothing else. Where English says "It is ten o'clock," Ukrainian says **Десята** — "The tenth [hour]." One word is enough.

- **Котра зараз година? — Дев'ята.** *(What time is it now? — Nine o'clock.)*

Here are all twelve hours as feminine ordinals. Learn them the way you learn months — as a set of twelve labels, not as grammar:

| | | |
|---|---|---|
| **перша** (1:00) | **друга** (2:00) | **третя** (3:00) |
| **четверта** (4:00) | **п'ята** (5:00) | **шоста** (6:00) |
| **сьома** (7:00) | **восьма** (8:00) | **дев'ята** (9:00) |
| **десята** (10:00) | **одинадцята** (11:00) | **дванадцята** (12:00) |

You are not learning the cardinal number "ten" here — you are learning the word **десята**, which means "10 o'clock." Think of each as a label for a point on the clock. A quick pronunciation note: **одинадцята** has five syllables (о-ди-над-ця-та), so take your time with it. And **друга** also means "female friend" in other contexts — but when answering **Котра година?**, the meaning is always "two o'clock."

<!-- INJECT_ACTIVITY: match-up-times -->

### Пів на... (Half Past)

The half-hour pattern is **пів на** + the *next* hour. The logic: you are halfway *toward* the next hour.

- **Пів на другу** = 1:30 (halfway to the second hour)
- **Пів на восьму** = 7:30 (halfway to the eighth hour)
- **Пів на дев'яту** = 8:30 — from Захарійчук Grade 4: *О пів на дев'яту продзвенів дзвінок* (At 8:30 the bell rang)

At A1, full hours and **пів на** are the core skill. Practice:

- **Зараз пів на третю.** *(It's 2:30 now.)*

### Чверть (Quarter Hours) — Recognition Only

From Ponomarova Grade 4: *Сьома година п'ятнадцять хвилин, або чверть на восьму* (7:15, or a quarter past seven). And *за чверть восьма* = 7:45 (a quarter to eight). Two forms exist: **чверть на** (quarter past — looking forward to the next hour) and **за чверть** (quarter to — counting down). You don't need to produce these yet — just recognize them when you hear them.

<!-- INJECT_ACTIVITY: quiz-clock-faces -->

## О котрій? (At What Time?)

The scheduling question is **О котрій годині?** — "At what time?" The preposition **о** (or **об** before a vowel) transforms the bare ordinal into a when-it-happens expression. Compare the two questions side by side:

- **Котра година? — Десята.** *(What time is it? — Ten.)*
- **О котрій зустріч? — О десятій.** *(At what time is the meeting? — At ten.)*

Two questions, two forms of the same hour. Here is the complete set of **о** + hour forms. Memorize these as ready-made phrases — not as grammar:

| | |
|---|---|
| **о першій** (at 1:00) | **о сьомій** (at 7:00) |
| **о другій** (at 2:00) | **о восьмій** (at 8:00) |
| **о третій** (at 3:00) | **о дев'ятій** (at 9:00) |
| **о четвертій** (at 4:00) | **о десятій** (at 10:00) |
| **о п'ятій** (at 5:00) | **об одинадцятій** (at 11:00) |
| **о шостій** (at 6:00) | **о дванадцятій** (at 12:00) |

One detail: **об одинадцятій** uses **об** instead of **о** because *одинадцятій* starts with a vowel. From Захарійчук Grade 4: *Чекатиму об одинадцятій годині.* All other hours use **о**. The pattern shortcut: if the answer to **Котра?** is *десята*, the answer to **О котрій?** is *о десятій* — the ending **-а** flips to **-ій**. Spot the pattern, don't memorize a rule.

<!-- INJECT_ACTIVITY: fill-in-o-kotrij -->

### Ранку, дня, вечора, ночі (Time of Day)

After the hour, add a time-of-day word to remove ambiguity — just like "AM" and "PM" in English. There are four words:

- **ранку** — in the morning
- **дня** — in the afternoon
- **вечора** — in the evening
- **ночі** — at night

From Захарійчук Grade 4: *Прокинувся о сьомій годині ранку.* (He woke up at seven in the morning.) Here is the full picture:

- **О сьомій ранку** — 7 AM
- **О третій дня** — 3 PM
- **О десятій вечора** — 10 PM
- **О другій ночі** — 2 AM

Two special words stand alone without **о**: **опівдні** (at noon) and **опівночі** (at midnight). You simply say *Зустрінемося опівдні* — no preposition needed.

The words **ранку**, **дня**, **вечора**, **ночі** are fixed phrases here. You don't need to know why they look the way they do — just attach them after the hour. This is how Ukrainian children learn time: phrase first, grammar later. Think of each combination as a single unit: *о восьмій ранку* is one chunk, not three separate words.

<!-- INJECT_ACTIVITY: quiz-time-of-day -->

## Підсумок — Summary

Two questions, two answer shapes:

**Котра година?** → answer with a bare ordinal:
- **Десята. Сьома. Пів на третю.**

**О котрій?** → answer with **о** + the shifted form:
- **О десятій. О сьомій. О пів на третю.**

The shift at a glance:

| Котра година? | О котрій? |
|---|---|
| **перша** | **о першій** |
| **дев'ята** | **о дев'ятій** |
| **одинадцята** | **об одинадцятій** |

One anchor: whenever you see **о котрій**, the answer ends in **-ій**.

Here is your complete time vocabulary from this module, grouped by type. Hours: **перша**, **друга**, **третя**, **четверта**, **п'ята**, **шоста**, **сьома**, **восьма**, **дев'ята**, **десята**, **одинадцята**, **дванадцята**. Half hour: **пів на** + the next hour. Time of day: **ранку** (morning), **дня** (afternoon), **вечора** (evening), **ночі** (night). The four nouns behind them: **ранок** (morning), **день** (day), **вечір** (evening), **ніч** (night). Special: **опівдні** (at noon), **опівночі** (at midnight). Questions: **Котра година?** and **О котрій годині?** — your scheduling toolkit.

Test yourself — answer each question out loud in Ukrainian before reading the model answer:

- **Котра година зараз?** → Look at your clock. Say the time: e.g., *Зараз третя.*
- **О котрій ти прокидаєшся?** → e.g., *Я прокидаюся о сьомій ранку.*
- **О котрій ти обідаєш?** → e.g., *Я обідаю о першій дня.*
- **О котрій ти лягаєш спати?** → e.g., *Я лягаю спати о десятій вечора.*
- **Пів на котру буде о 8:30?** → *Пів на дев'яту.*

Aim to answer all five without scrolling back. If you hesitate on any hour form, review the table in section 2.

You can now say *what time* something happens. The next step is *what day* and *what month*. In Module 23, you'll combine time with days: **У понеділок о дев'ятій ранку** — the full coordinate of a plan. Ukrainian scheduling vocabulary builds one layer at a time.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: what-time
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

**Level: A1.4+ (Module 22/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


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
