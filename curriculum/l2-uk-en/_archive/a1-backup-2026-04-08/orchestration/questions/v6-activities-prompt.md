<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/questions.yaml` file for module **19: Questions** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-question-words -->`
- `<!-- INJECT_ACTIVITY: match-question-answer -->`
- `<!-- INJECT_ACTIVITY: fill-in-negation -->`
- `<!-- INJECT_ACTIVITY: quiz-double-negation -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Choose the right question word: ___ ти живеш? (Де/Що/Хто)'
  items: 8
  type: quiz
- focus: 'Make it negative: Я знаю → Я не знаю, Хтось знає → Ніхто не знає'
  items: 8
  type: fill-in
- focus: 'Match question to answer: Де ти живеш? ↔ У Києві.'
  items: 6
  type: match-up
- focus: 'Double negation: choose the correct Ukrainian sentence.'
  items: 6
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- ніхто (nobody)
- нічого (nothing)
- ніколи (never)
- жити (to live)
- розуміти (to understand)
- тому що (because)
required:
- хто (who)
- що (what)
- де (where)
- куди (where to)
- коли (when)
- чому (why)
- як (how)
- не (not)
- ні (no)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Ukrainian uses special question words — **питальні слова** (question words) — to ask about the world. The two dialogues below show these words in real conversation before we study each one.

### Dialogue 1 — Getting to know someone

> **Андрій:** Привіт! Хто ти? *(Hi! Who are you?)*
> **Олег:** Я студент. А ти? *(I'm a student. And you?)*
> **Андрій:** Я теж студент. Що ти вивчаєш? *(I'm also a student. What do you study?)*
> **Олег:** Я вивчаю українську мову. *(I study the Ukrainian language.)*
> **Андрій:** Де ти живеш? *(Where do you live?)*
> **Олег:** Я живу у Львові. *(I live in Lviv.)*
> **Андрій:** Коли ти працюєш? *(When do you work?)*
> **Олег:** Вранці. А ти? *(In the morning. And you?)*
> **Андрій:** Увечері. Як тебе звати? *(In the evening. What's your name?)*
> **Олег:** Мене звати Олег. *(My name is Oleh.)*

Every question here starts with a different question word: **Хто** (who) asks about a person, **Що** (what) asks about a thing or activity, **Де** (where) asks about location, **Коли** (when) asks about time, and **Як** (how) asks about manner. Notice how the answer always matches what the question word asks about — **Хто ти?** gets a person (**студент**), **Де ти живеш?** gets a place (**у Львові**).

### Dialogue 2 — At home

> **Оля:** Де моя книга? *(Where is my book?)*
> **Тарас:** Я не знаю. *(I don't know.)*
> **Оля:** А хто знає? *(And who knows?)*
> **Тарас:** Ніхто не знає. *(Nobody knows.)*
> **Оля:** Що це на столі? *(What is this on the table?)*
> **Тарас:** Нічого цікавого. *(Nothing interesting.)*
> **Оля:** Чому ти не відповідаєш? *(Why don't you answer?)*
> **Тарас:** Тому що я не чув! *(Because I didn't hear!)*

This dialogue combines question words with negation. Notice three things the dialogues just showed you:

1. **Question words come at the start** of the sentence: **Де** моя книга? **Хто** знає? **Чому** ти не відповідаєш?
2. **Word order after the question word stays natural** — you don't need to rearrange anything. Just put the question word first and the sentence works.
3. **Не** and **ніхто/нічого** often appear together: **Ніхто не знає** uses both. This is called double negation, and it is required in Ukrainian — we will study it in detail below.

## Питальні слова (Question Words)

Seven question words cover almost everything you need to ask at A1. Here they are as a set, each with the anchor example you already saw in the dialogues:

- **Хто?** (who) — Хто ти?
- **Що?** (what) — Що ти вивчаєш?
- **Де?** (where) — Де ти живеш?
- **Куди?** (where to) — Куди ти йдеш?
- **Коли?** (when) — Коли ти працюєш?
- **Чому?** (why) — Чому ти не відповідаєш?
- **Як?** (how) — Як тебе звати?

Ukrainian textbooks introduce **Хто?** and **Що?** from the very first grade to distinguish living things (**хто** — people, animals) from non-living things (**що** — objects, concepts). The remaining five — **Де? Куди? Коли? Чому? Як?** — appear as question words for adverbs (Кравцова, Grade 2).

### Де vs. Куди — the pair learners confuse

**Де** asks about a static location — where something already is. **Куди** asks about direction — where something is moving toward. Compare:

- **Де** ти живеш? — Where do you live? (you are there)
- **Куди** ти йдеш? — Where are you going? (you are moving there)
- **Де** книга? — Where is the book? (it is somewhere)
- **Куди** вони їдуть? — Where are they driving? (they are heading somewhere)

The rule: use **де** with verbs of being or staying (**жити**, **бути**, **стояти**). Use **куди** with verbs of movement (**іти**, **їхати**, **ходити**).

<!-- INJECT_ACTIVITY: quiz-question-words -->

### Word order in questions

The typical pattern is question word + verb + subject, but Ukrainian is flexible. All of these are acceptable:

- **Де ти живеш?** (standard)
- **Ти де живеш?** (conversational)
- **Живеш де?** (very informal)

The question word carries the emphasis regardless of its position. In everyday speech, the first two options are most natural. Written Ukrainian prefers the question word at the start.

### Yes/no questions

To ask a yes/no question, you do not need a special word — just raise your intonation at the end of the sentence:

- Ти говориш українською? ↑ *(Do you speak Ukrainian?)*
- Він живе тут? ↑ *(Does he live here?)*
- Вона знає? ↑ *(Does she know?)*

English needs "do" or "does" to form these questions. Ukrainian does not — the sentence stays exactly the same, and only the rising intonation ↑ tells the listener it is a question. In formal or written Ukrainian, you may also see **чи** (whether) at the beginning: **Чи ти розумієш?** (Do you understand?) Recognise **чи** when you see it, but for everyday A1 speech, intonation alone is enough.

<!-- INJECT_ACTIVITY: match-question-answer -->

## Заперечення (Negation)

The particle **не** (not) goes directly before the verb — never separated from it. Here are five examples using verbs you already know from Modules 16–18:

- Я **не** знаю. — I don't know.
- Він **не** працює. — He doesn't work.
- Ми **не** розуміємо. — We don't understand.
- Вона **не** хоче. — She doesn't want to.
- Вони **не** говорять. — They don't speak.

In English, "do not" is two words; in Ukrainian, **не** is a single particle that sits right before the verb. It is almost always unstressed — the stress stays on the verb. No matter how long the sentence is, **не** stays glued to its verb: Я **не** хочу, Вони **не** розуміють.

### Ні — standalone "no" and the ні- pronouns

As a standalone word, **ні** (no) answers a question directly:

- Ти знаєш? — **Ні**, не знаю. *(Do you know? — No, I don't know.)*

But **ні** also forms a family of negative words by attaching to question-word pronouns and adverbs:

| Ukrainian | English | Example |
|-----------|---------|---------|
| **ніхто** | nobody | Ніхто не знає. |
| **нічого** | nothing | Я нічого не бачу. |
| **ніколи** | never | Вона ніколи не запізнюється. |
| **ніде** | nowhere | Ніде не було. |
| **нікуди** | to nowhere | Він нікуди не йде. |

Notice the pattern: the prefix **ні-** attaches directly to the question word — **хто** → **ніхто**, **коли** → **ніколи**, **де** → **ніде**, **куди** → **нікуди**. Ukrainian textbooks (Заболотний, Grade 6) teach these as negative pronouns and adverbs formed from their question-word counterparts with the prefix **ні-**.

### Double negation — the most important rule

Ukrainian requires both the **ні-** word AND **не** before the verb. This is mandatory — dropping either one makes the sentence ungrammatical.

Wrong (English pattern): ~~Ніхто знає.~~
Correct: **Ніхто не знає.** *(Nobody knows.)*

Four more examples:

- **Я нічого не знаю.** — I don't know anything. (literally: I nothing don't know.)
- **Ніхто не говорить.** — Nobody speaks.
- **Вона ніколи не запізнюється.** — She is never late.
- **Він нікуди не йде.** — He isn't going anywhere.

This is not a logic error and does not create a "double positive" like it would in English. It is standard Ukrainian grammar — both parts are required (Літвінова, Grade 6: «Ніхто не може змусити вас...»).

<!-- INJECT_ACTIVITY: fill-in-negation -->

### Не vs. ні- at a glance

**Не** alone negates one verb: **Я не знаю** (I don't know — but someone else might). A **ні-** word negates the entire idea and still needs **не** with the verb: **Ніхто не знає** (nobody at all knows). Here is the contrast in question-and-answer pairs:

- **Хто це?** — **Ніхто.** *(Who is this? — Nobody.)*
- **Що ти бачиш?** — **Нічого не бачу.** *(What do you see? — I see nothing.)*

When answering with a single word, you can say **Ніхто** or **Нічого** alone. But as soon as the answer becomes a full sentence with a verb, double negation kicks in: **Нічого не бачу**.

<!-- INJECT_ACTIVITY: quiz-double-negation -->

## Підсумок — Summary

Here is everything from this module in one place:

- **Питальні слова:** **Хто? Що? Де? Куди? Коли? Чому? Як?** — seven question words. Place the question word first; word order after it is flexible.
- **Де vs. Куди:** **Де** = location (Де книга?); **Куди** = direction (Куди ти йдеш?).
- **Так/ні питання:** rising intonation only — Ти знаєш? ↑ No special word needed. In formal writing, **чи** may appear at the start.
- **Не:** directly before the verb, never separated — Я **не** знаю. Він **не** приходить.
- **Подвійне заперечення:** **ніхто/нічого/ніколи/ніде** + **не** + verb — both parts required. **Ніхто не знає.** **Я нічого не бачу.**

:::tip Self-check — try this now
1. Ask three questions about a friend: **Де вона живе? Що він вивчає? Коли вони приходять?**
2. Make two negative sentences: **Я нічого не знаю. Ніхто не розуміє.**
3. Turn a statement into a yes/no question: Він говорить українською. → Він говорить українською? ↑
:::

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: questions
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

**Level: A1.2-A1.3 (Module 19/55) — EARLY BEGINNER**

The learner knows the alphabet and ~200 words. They:
- Can read Ukrainian slowly
- Know basic nouns, adjectives, simple verb forms
- Cannot handle complex sentences or grammar terminology in Ukrainian

**Instructions in simple English with Ukrainian key terms in bold.**
Example: 'Choose the correct form of **мій/моя/моє**'

**Good activity types:** quiz, fill-in (simple sentences), match-up, group-sort, true-false, observe, anagram, translate (English→Ukrainian).


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-verbs-present
- **fill-in** — Відмінюй дієслово: Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Find incorrectly conjugated verb and fix it

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
