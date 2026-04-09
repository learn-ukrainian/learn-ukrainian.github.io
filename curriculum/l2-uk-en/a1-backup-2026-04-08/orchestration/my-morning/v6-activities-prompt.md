<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/my-morning.yaml` file for module **20: My Morning** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-add-sya -->`
- `<!-- INJECT_ACTIVITY: quiz-reflexive-or-not -->`
- `<!-- INJECT_ACTIVITY: fill-in-morning-order -->`
- `<!-- INJECT_ACTIVITY: fill-in-describe-morning -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Add -ся: я вмиваю__ , ти одягаєш__ , він прокидаєть__'
  items: 10
  type: fill-in
- focus: 'Reflexive or not? Choose: Я (вмиваю/вмиваюся) руки.'
  items: 8
  type: quiz
- focus: 'Put the morning routine in order: спочатку ___, потім ___, нарешті ___'
  items: 6
  type: fill-in
- focus: Describe your morning in 3 sentences
  items: 3
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- збиратися (to get ready)
- повертатися (to return)
- навчатися (to study/learn)
- поспішати (to hurry)
- після цього (after this)
- нарешті (finally)
- вранці (in the morning)
- пізно (late)
required:
- прокидатися (to wake up)
- вмиватися (to wash face/hands)
- одягатися (to get dressed)
- снідати (to have breakfast)
- йти (to go — irregular)
- спочатку (first, at first)
- потім (then, next)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

It's Monday morning. Ліна and Настя share an apartment. They're both in the kitchen — one is already dressed, the other still half-asleep. Their conversation is about to teach you one of the most useful verb patterns in Ukrainian.

### Діалог 1 — Ранок у будні (Weekday morning)

> **Настя:** Ліно, коли ти прокидаєшся? *(Lina, when do you wake up?)*
> **Ліна:** Я прокидаюся о сьомій. *(I wake up at seven.)*
> **Настя:** А що ти робиш потім? *(And what do you do next?)*
> **Ліна:** Спочатку вмиваюся, потім одягаюся і снідаю. *(First I wash up, then I get dressed and have breakfast.)*
> **Настя:** А коли йдеш на роботу? *(And when do you go to work?)*
> **Ліна:** О восьмій. А ти? *(At eight. And you?)*
> **Настя:** Я прокидаюся о шостій. Довго збираюся! *(I wake up at six. I take a long time getting ready!)*
> **Ліна:** О шостій? Це рано! *(At six? That's early!)*

Look at the verbs Ліна uses to describe her morning: **прокидаюся** (I wake up), **вмиваюся** (I wash up), **одягаюся** (I get dressed), **збираюся** (I get ready). Every single one ends in **-ся**. That's not a coincidence — it's a pattern, and it's the grammar heart of this module.

### Діалог 2 — Вихідний ранок (Weekend morning)

> **Ліна:** У суботу я не поспішаю. *(On Saturday I don't rush.)*
> **Настя:** А що ти робиш? *(And what do you do?)*
> **Ліна:** Прокидаюся пізно, лежу, дивлюся в телефон. *(I wake up late, lie around, look at my phone.)*
> **Настя:** А я навчаюся вранці. Снідаю, потім гуляю. *(And I study in the morning. I have breakfast, then go for a walk.)*
> **Ліна:** Ти навчаєшся у суботу? *(You study on Saturday?)*
> **Настя:** Так! Я повертаюся додому о другій. *(Yes! I come back home at two.)*

This dialogue mixes two kinds of verbs. Some end in **-ся**: **прокидаюся**, **дивлюся**, **навчаюся** (I study), **повертаюся** (I return). Others don't: **снідаю** (I have breakfast), **гуляю** (I walk), **лежу** (I lie down). Notice the difference? Verbs with **-ся** describe actions you do *to yourself* or *for yourself*. Verbs without it describe actions directed outward. The next section explains exactly how this works.

## Дієслова на -ся (Reflexive Verbs)

Ukrainian textbooks call these **зворотні дієслова** — verbs where the action turns back onto the person doing it. The suffix **-ся** (short for the old pronoun **себе**, meaning "oneself") attaches to the end of the verb and changes its direction.

Compare these pairs:

- **вмивати** (to wash someone) → **вмиватися** (to wash oneself)
- **одягати** (to dress someone) → **одягатися** (to dress oneself)

A mother washes her child: **Мама вмиває дитину.** *(Mom washes the child.)* But when you wash your own face in the morning: **Я вмиваюся.** *(I wash up.)* The action loops back — that's what **-ся** signals.

### How to conjugate reflexive verbs

The good news: reflexive verbs use the same endings as regular Group I verbs. You just add **-ся** after every ending. Here is **вмиватися** (to wash up) in the present tense:

| | вмиватися |
|---|---|
| я | вмиваюся |
| ти | вмиваєшся |
| він/вона | вмивається |
| ми | вмиваємося |
| ви | вмиваєтеся |
| вони | вмиваються |

The pattern is identical for **прокидатися** (to wake up): **я прокидаюся, ти прокидаєшся, він прокидається**. Once you know how to conjugate one reflexive verb, you can conjugate them all.

### Pronunciation secret

Here's something that trips up learners: the way you *write* these endings and the way you *say* them are different.

- **-шся** (written) sounds like a long, soft "с" — say it quickly and your mouth naturally makes the right sound. So **вмиваєшся** sounds like "вмиваєс':а" in fast speech.
- **-ться** (written) sounds like a long, soft "ц" — so **вмивається** sounds like "вмиваєц':а."

:::tip
Don't overthink the pronunciation. Spell it correctly on paper: **вмиваєшся**, **вмивається**. When you say it aloud at normal speed, the sounds merge naturally. Ukrainian children learn this the same way — Kravtsova's Grade 4 textbook has students whisper the endings quickly to discover the sound shift themselves.
:::

<!-- INJECT_ACTIVITY: fill-in-add-sya -->

<!-- INJECT_ACTIVITY: quiz-reflexive-or-not -->

## Мій ранок (My Morning)

Now you have the tools to describe an entire morning. Let's build your vocabulary in two groups: reflexive verbs (actions on yourself) and non-reflexive verbs (actions on the world around you).

### Reflexive morning verbs

Each of these describes something you do to or for yourself:

- **прокидатися** (to wake up) — Я прокидаюся о сьомій годині. *(I wake up at seven o'clock.)*
- **вмиватися** (to wash face/hands) — Вона вмивається в ванній. *(She washes up in the bathroom.)*
- **одягатися** (to get dressed) — Він одягається швидко. *(He gets dressed quickly.)*
- **збиратися** (to get ready) — Ти збираєшся довго! *(You take a long time getting ready!)*
- **навчатися** (to study) — Ми навчаємося разом. *(We study together.)*
- **повертатися** (to return) — Я повертаюся додому о шостій. *(I return home at six.)*

### Non-reflexive morning verbs

These describe actions directed at something else — food, coffee, the outside world:

- **снідати** (to have breakfast) — Я снідаю о восьмій. *(I have breakfast at eight.)*
- **пити каву** (to drink coffee) — Він п'є каву. *(He drinks coffee.)*
- **гуляти** (to walk/stroll) — Вона гуляє вранці. *(She takes a walk in the morning.)*

No **-ся** here — because you eat breakfast, you don't "breakfast yourself." The action goes outward.

### The irregular verb йти (to go)

One essential morning verb breaks the rules. **Йти** (to go on foot) has its own conjugation that doesn't follow Group I or Group II patterns. Memorize these forms:

| | йти |
|---|---|
| я | йду |
| ти | йдеш |
| він/вона | йде |
| ми | йдемо |
| ви | йдете |
| вони | йдуть |

- Я йду на роботу о восьмій. *(I go to work at eight.)*
- Вона йде до школи. *(She goes to school.)*
- Ти йдеш зараз? *(Are you going now?)*

### Telling your morning as a story

Four words let you string your morning into a sequence:

- **спочатку** (first, at first)
- **потім** (then, next)
- **після цього** (after this)
- **нарешті** (finally)

Put them together and you get a complete mini-narrative:

- Спочатку я прокидаюся о сьомій. *(First I wake up at seven.)*
- Потім вмиваюся і одягаюся. *(Then I wash up and get dressed.)*
- Після цього снідаю і п'ю каву. *(After this I have breakfast and drink coffee.)*
- Нарешті йду на роботу о восьмій. *(Finally I go to work at eight.)*

These sequence words typically stand at the beginning of the sentence. They're the glue that turns isolated actions into a real story.

<!-- INJECT_ACTIVITY: fill-in-morning-order -->

## Підсумок — Summary

### Grammar recap

Reflexive verbs = a regular verb + the suffix **-ся**. The suffix never changes — it attaches after every personal ending: **-юся, -єшся, -ється, -ємося, -єтеся, -ються** (Group I pattern). The action turns back onto the person doing it: **вмивати** (to wash someone else) versus **вмиватися** (to wash yourself).

Two pronunciation rules to keep in mind: **-шся** sounds like a long soft "с," and **-ться** sounds like a long soft "ц." Write the full spelling, say the short form.

One irregular verb to know by heart: **я йду, ти йдеш, він йде, ми йдемо, ви йдете, вони йдуть**.

### Your morning vocabulary

Here's the full chain for describing a morning routine:

**Reflexive chain:** прокидатися (to wake up) → вмиватися (to wash up) → одягатися (to get dressed) → збиратися (to get ready) → йти на роботу (to go to work)

**Return:** повертатися додому (to return home)

**Non-reflexive:** снідати (to have breakfast), пити каву (to drink coffee), гуляти (to walk)

**Supporting words:** вранці (in the morning), пізно (late), поспішати (to hurry), навчатися (to study)

**Sequence glue:** спочатку (first), потім (then), після цього (after this), нарешті (finally)

### The reflexive test

:::note
How do you know if a verb is reflexive? Ask: can I do this action *to another person*? If yes, the non-reflexive form exists and means something different. **Вмивати когось** (to wash someone) ≠ **вмиватися** (to wash oneself). **Одягати дитину** (to dress a child) ≠ **одягатися** (to get dressed). The **-ся** signals the action loops back to the subject.
:::

## Підсумок

Now it's your turn. Describe your own morning using the sequence words and reflexive verbs from this module. Three sentences is enough to start:

- **Спочатку** я ___ (what time? what do you do?)
- **Потім** я ___ і ___.
- **Нарешті** я ___.

Use the verbs you've learned: **прокидатися, вмиватися, одягатися, снідати, йти**. Combine them with **спочатку, потім, після цього, нарешті** — and you can tell anyone about your morning in Ukrainian.

<!-- INJECT_ACTIVITY: fill-in-describe-morning -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: my-morning
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

**Level: A1.2-A1.3 (Module 20/55) — EARLY BEGINNER**

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
