<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/when-and-where.yaml` file for module **45: When and Where** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-conjunction-choice -->`
- `<!-- INJECT_ACTIVITY: quiz-question-or-conjunction -->`
- `<!-- INJECT_ACTIVITY: fill-in-complete-clause -->`
- `<!-- INJECT_ACTIVITY: quiz-comma-placement -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Complete: Я знаю, ___ він тут. Я не знаю, ___ вона живе. Скажи, ___ ти прийдеш.'
  items: 8
  type: fill-in
- focus: Question word or conjunction? Де ти живеш? vs Я знаю, де ти живеш.
  items: 8
  type: quiz
- focus: 'Build complex sentences: Я думаю, що ___. Він каже, що ___.'
  items: 6
  type: fill-in
- focus: Where is the comma? Choose correct punctuation in complex sentences
  items: 8
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- сказати (to say — perfective)
- бачити (to see)
- чути (to hear)
- розуміти (to understand)
- речення (sentence, n)
- головне (main — as in main clause)
required:
- що (that — conjunction)
- де (where — conjunction)
- коли (when — conjunction)
- знати (to know)
- думати (to think)
- казати (to say/tell)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

You already know **що** (what), **де** (where), and **коли** (when) as question words. Today's dialogues show them doing a completely different job — connecting two clauses inside one sentence instead of asking a question.

> **Олексій:** Ти знаєш, де нове кафе? *(Do you know where the new café is?)*
> **Марія:** Так, я знаю, де воно. *(Yes, I know where it is.)*
> **Олексій:** Скажи, коли ти вільна. *(Tell me when you're free.)*
> **Марія:** Я вільна, коли закінчу роботу. *(I'm free when I finish work.)*
> **Олексій:** Добре. Я думаю, що о шостій буде добре. *(Good. I think that six o'clock will be good.)*
> **Марія:** Так, я теж думаю, що це гарний час. *(Yes, I also think that it's a good time.)*

Notice the verbs here. **Знати** (to know) appears twice — Олексій asks what Марія knows, and she confirms. **Думати** (to think) appears twice — both speakers share their opinion using **я думаю, що...** (I think that...). The word **скажи** is the imperative of **казати** (to say/tell) — Олексій literally says "tell me when."

A second situation — talking about a mutual friend who has arrived in the city.

> **Богдан:** Ти знаєш, що Олена вже в Києві? *(Do you know that Olena is already in Kyiv?)*
> **Наталя:** Ні, я не знав! А де вона живе? *(No, I didn't know! And where does she live?)*
> **Богдан:** Я не знаю, де саме. Але я знаю, що біля центру. *(I don't know where exactly. But I know that near the centre.)*
> **Наталя:** Скажи їй, коли побачиш, що я хочу зустрітися. *(Tell her, when you see her, that I want to meet.)*
> **Богдан:** Добре, скажу, коли побачу. *(OK, I'll tell her when I see her.)*

Here **казати** (to say/tell) appears as **скажи** (tell! — imperative) and **скажу** (I'll tell). Богдан uses **знати** (to know) three times: **знаєш** (you know), **не знаю** (I don't know), **знаю** (I know). And **думати** (to think) drives the opinion patterns throughout.

Count the conjunctions. Dialogue 1 uses **що** twice, **де** twice, **коли** twice. Dialogue 2 uses **що** three times, **де** twice, **коли** twice. Every one of them connects two halves of a sentence — none of them asks a question. That is the pattern this module teaches. Keep these dialogues in mind — every grammar point below ties back to lines you just read.

## Складне речення (Complex Sentences)

In M44 you joined EQUAL ideas with coordinating conjunctions: **Я читаю, і він пише.** (I read, and he writes.) **Він прийшов, але вона пішла.** (He came, but she left.) Those conjunctions — **і** (and), **але** (but), **бо** (because) — link two clauses that could each stand alone as complete sentences. Today's pattern is different: a MAIN clause plus a DEPENDENT clause. The dependent clause cannot stand alone. **Що він тут** doesn't mean anything by itself — it needs a main clause in front of it: **Я знаю, що він тут.** (I know that he is here.) The dependent clause adds detail to the main idea. Ukrainian grammarians call this a **складнопідрядне речення** (a complex sentence with a subordinate clause — Grade 5, Заболотний).

Three structures, each built from the same formula — main clause + comma + conjunction + subordinate clause:

- **Я знаю, що він тут.** (I know that he is here.) — main clause: **Я знаю** / conjunction: **що** / subordinate: **він тут**
- **Я не знаю, де вона живе.** (I don't know where she lives.) — main clause: **Я не знаю** / conjunction: **де** / subordinate: **вона живе**
- **Скажи мені, коли ти прийдеш.** (Tell me when you'll come.) — main clause: **Скажи мені** / conjunction: **коли** / subordinate: **ти прийдеш**

The pattern is always the same: main clause + comma + **що/де/коли** + subordinate clause.

Now the comma rule. Ukrainian ALWAYS places a comma before **що**, **де**, or **коли** when they act as conjunctions. No exceptions. This differs from English, where "I know that he's here" has no comma. Three more examples to drill this:

- **Я думаю, що це правильно.** (I think that this is correct.)
- **Він не знає, де магазин.** (He doesn't know where the shop is.)
- **Зателефонуй, коли прийдеш.** (Call when you arrive.)

Look back at Dialogue 1 — every line with **що**, **де**, or **коли** in the middle has a comma immediately before it. You can verify this yourself now. The verb **думати** (to think) naturally pairs with **що**: **Я думаю, що...** The verb **знати** (to know) pairs with all three: **Я знаю, що...** / **Я знаю, де...** / **Я знаю, коли...**

One more detail. When **коли** opens the WHOLE sentence (the time-clause comes first), the comma appears after the subordinate clause instead: **Коли я прийду, ми поговоримо.** (When I arrive, we'll talk.) Same comma, different position. One example is enough at A1 — you'll learn the perfective future form **прийду** later in B1.

<!-- INJECT_ACTIVITY: fill-in-conjunction-choice -->

## Що, де, коли — двоє облич (Two Faces)

These three words already appeared in M20 as question words — you have been using them since then. Now they have a second job. The key insight: same word, two completely different positions and functions inside a sentence. Don't treat them as new vocabulary — treat them as familiar words that learned a new trick. Ukrainian children learn this same distinction in Grade 5, when they study **сполучники** (conjunctions) for the first time (Заболотний). The textbook diagnostic is simple: if you can't ask a question with the word, it's a conjunction.

**Job 1 — Question words.** They sit at the START of a sentence. The sentence ends with a question mark. The speaker expects an answer. Examples you already know from M20:

- **Що це?** (What is this?)
- **Що ти робиш?** (What are you doing?)
- **Де ти?** (Where are you?)
- **Де магазин?** (Where is the shop?)
- **Коли ти прийдеш?** (When will you come?)
- **Коли починається фільм?** (When does the film start?)

These sentences have only ONE clause. The word **що/де/коли** launches the question.

**Job 2 — Conjunctions.** They sit IN THE MIDDLE of a sentence, after a comma. The sentence does NOT end with a question mark — it makes a statement or gives a command. Examples:

- **Я знаю, що це книжка.** (I know that this is a book.)
- **Я знаю, де ти.** (I know where you are.)
- **Скажи, коли прийдеш.** (Tell me when you'll come.)

The difference is grammatical position. Start of sentence = question word. After a comma in the middle = conjunction. Compare side by side:

- **Де ти?** (question) → **Я знаю, де ти.** (conjunction)
- **Де ти живеш?** (question) → **Я знаю, де ти живеш.** (conjunction)
- **Що він хоче?** (question) → **Вона думає, що він хоче чаю.** (conjunction)

<!-- INJECT_ACTIVITY: quiz-question-or-conjunction -->

Here are the most useful patterns worth memorising as chunks. With **що** (that): **Я знаю, що...** / **Я не знаю, що...** / **Я думаю, що...** / **Він каже, що...** The verb **казати** (to say/tell) naturally pairs with **що** for reported speech — when someone tells you something, Ukrainian uses **він каже, що...** (he says that...). With **де** (where): **Я знаю, де...** / **Я не знаю, де...** With **коли** (when): **Скажи, коли...** / **Я не знаю, коли...** / **Коли я прийду, ми поговоримо.** Notice that Dialogue 2 packed two conjunctions into one sentence: **Скажи їй, коли побачиш, що я хочу зустрітися** — both **коли** and **що** connect their own subordinate clauses to the main verb **скажи**.

<!-- INJECT_ACTIVITY: fill-in-complete-clause -->

## Підсумок — Summary

The core insight of this module: **що**, **де**, and **коли** are conjunctions when they connect a main clause to a subordinate clause in the middle of a sentence, with a comma before them. Compare this with M44's coordinating conjunctions: **і**, **але**, **бо** join EQUAL parts that could each stand alone. Today's **що/де/коли** join a MAIN part to a DEPENDENT part — the subordinate clause needs the main clause to make sense. This distinction is the foundation of complex sentence-building in Ukrainian through B2 and beyond.

| Сполучник | Значення | Приклад |
|-----------|----------|---------|
| **що** | that | **Я знаю, що він тут.** |
| **де** | where | **Я не знаю, де кафе.** |
| **коли** | when | **Скажи, коли прийдеш.** |

Remember: always a comma before the conjunction — **завжди кома перед сполучником**.

Now combine what you learned in M44 with today's conjunctions. Two sentences that use BOTH types:

- **Я не йду, бо я не знаю, де це.** (I'm not going because I don't know where it is.) — **бо** from M44 + **де** from today.
- **Він каже, що прийде, коли закінчить.** (He says that he'll come when he finishes.) — **що** + **коли**, two subordinate clauses in one sentence.

These sentences feel sophisticated, but they use only words and structures you have already learned. The verbs **знати** (to know), **думати** (to think), and **казати** (to say/tell) are the engines that drive complex sentences — they are the main-clause verbs that most naturally take **що/де/коли** after them.

<!-- INJECT_ACTIVITY: quiz-comma-placement -->

## Підсумок

Self-check — build three sentences using the templates below. Fill in each blank with your own idea:

- **Я думаю, що ___.** (any opinion — e.g., це добре, він правий)
- **Я не знаю, де ___.** (any place — e.g., нове кафе, вона живе)
- **Скажи мені, коли ___.** (any time-event — e.g., ти прийдеш, почнеться фільм)

Then check two things. First: is there a comma before the conjunction (**що/де/коли**) in each sentence? Second: does the sentence make a statement or command, not a question? If yes to both — your sentence is correct.

You can now build sentences where one idea depends on another. Combined with M44's **і**, **але**, and **бо**, you have everything you need to express real thoughts in Ukrainian — opinions (**я думаю, що...**), uncertainty (**я не знаю, де...**), and requests for information (**скажи, коли...**). These are the building blocks of natural conversation.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: when-and-where
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

**Level: A1.4+ (Module 45/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-syllables
- **divide-words** — Поділи слова на склади: Interactive syllable division — tap between letters to insert hyphens
  - Instruction: *Поділіть слово на склади*
- **count-syllables** — Порахуй склади: Count syllables — each vowel = one syllable (складотворчі голосні)
  - Instruction: *How many syllables?*
- **pick-syllables** — Вибери закриті/відкриті склади: Classify syllables as відкритий (ends vowel) or закритий (ends consonant)
  - Instruction: *Select all closed syllables (закриті склади)*
- **odd-one-out** — Четверте зайве: Pick the word that doesn't belong — by syllable count, type, or pattern
  - Instruction: *Яке слово зайве?*

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
