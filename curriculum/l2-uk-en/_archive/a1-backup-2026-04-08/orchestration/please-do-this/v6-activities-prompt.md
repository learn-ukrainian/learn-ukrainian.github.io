<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/please-do-this.yaml` file for module **43: Please Do This** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-imperative-forms -->`
- `<!-- INJECT_ACTIVITY: quiz-correct-imperative -->`
- `<!-- INJECT_ACTIVITY: group-sort-ty-vy -->`
- `<!-- INJECT_ACTIVITY: fill-in-context-ty-vy -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Form imperative: читати → читай / читайте, писати → пиши / пишіть'
  items: 10
  type: fill-in
- focus: 'Choose correct: ___, будь ласка! (дай / даєш / дати)'
  items: 8
  type: quiz
- focus: 'Sort: ти-forms vs ви-forms (читай vs читайте, дай vs дайте)'
  items: 10
  type: group-sort
- focus: 'Complete: Олено, ___ книжку! Пане Іване, ___ книжку! (дай/дайте)'
  items: 6
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- відкрити (to open)
- сісти (to sit down)
- показати (to show)
- запитати (to ask)
- підручник (textbook, m)
- сторінка (page, f)
- речення (sentence, n)
required:
- читати (to read)
- писати (to write)
- слухати (to listen)
- дивитися (to look/watch)
- говорити (to speak)
- дати (to give)
- сказати (to say/tell)
- іти (to go)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

A morning Ukrainian lesson. The teacher walks in, opens her book, and class begins.

> **Вчителька:** Відкрийте підручники, будь ласка. *(Open your textbooks, please.)*
> **Вчителька:** Читайте текст на сторінці двадцять три. *(Read the text on page twenty-three.)*
> **Учень:** Вибачте, яку сторінку? *(Sorry, which page?)*
> **Вчителька:** Сторінку двадцять три. Читайте тихо. *(Page twenty-three. Read quietly.)*
> **Вчителька:** Добре. Тепер пишіть. Напишіть три речення. *(Good. Now write. Write three sentences.)*
> **Учениця:** Можна запитати? *(May I ask a question?)*
> **Вчителька:** Так, запитуйте! *(Yes, go ahead and ask!)*
> **Учениця:** Що означає це слово? *(What does this word mean?)*
> **Вчителька:** Подивіться у словник. Відкрийте його. *(Look in the dictionary. Open it.)*

The teacher used **ви**-forms throughout: **відкрийте** (open), **читайте** (read), **пишіть** (write), **напишіть** (write — completed action), **запитуйте** (ask), **подивіться** (look). She is speaking to the whole class — a group — so the **ви**-form is natural.

After school, two friends walk outside together.

> **Олесь:** Слухай, ходімо в кафе! *(Listen, let's go to a café!)*
> **Олесь:** Подивись, яка гарна погода! *(Look, what nice weather!)*
> **Дарина:** Добре! Іди, я зараз. *(OK! Go ahead, I'm coming.)*
> **Олесь:** Сідай тут, це гарне місце. *(Sit here, it's a nice spot.)*
> **Дарина:** Дай мені меню, будь ласка. *(Give me the menu, please.)*
> **Олесь:** Ось, дивись. Скажи, що ти хочеш? *(Here, look. Tell me, what do you want?)*
> **Дарина:** Я хочу каву і тістечко. *(I want coffee and a pastry.)*
> **Олесь:** Добре. Офіціанте, принесіть каву і тістечко, будь ласка! *(OK. Waiter, bring a coffee and a pastry, please!)*
> **Дарина:** Дякую, Олесю! *(Thanks, Oles!)*

Between friends, Oles used **ти**-forms: **слухай** (listen), **подивись** (look), **іди** (go), **сідай** (sit), **дай** (give), **дивись** (look), **скажи** (say). But when he spoke to the waiter — a stranger — he switched to the **ви**-form: **принесіть** (bring). Notice **будь ласка** appearing in both dialogues: Дарина used it with her friend, and Oles used it with the waiter. Which words were direct commands and which were polite requests? Any imperative + **будь ласка** becomes a request.

## Наказовий спосіб (The Imperative Mood)

In Ukrainian Grade 5, this grammar topic has a name: **наказовий спосіб** (imperative mood). You use it for commands (**Читай!** — Read!), requests (**Дай, будь ласка.** — Give me, please.), instructions (**Напишіть три речення.** — Write three sentences.), and invitations (**Ходімо в кафе!** — Let's go to a café!). At A1, you need two forms: the **ти**-form for one person you know well — a friend, a sibling, a classmate — and the **ви**-form for formal situations — a teacher, a stranger, a doctor — or when speaking to more than one person. A quick comparison: **Дай!** (to your friend) vs. **Дайте!** (to your teacher or a group).

The word **будь ласка** (please) transforms any imperative into a polite request. Watch the same verb escalate in formality:

- **Дай!** — Give! *(direct, to a friend)*
- **Дай, будь ласка.** — Please give. *(polite, to a friend)*
- **Дайте, будь ласка.** — Please give. *(polite, to a teacher or group)*
- **Пане Іване, дайте, будь ласка.** — Mr. Ivan, please give. *(very polite, with name)*

Ukrainian imperatives without **будь ласка** are NOT rude. Teachers, coaches, and parents use bare imperatives all the time. That is normal, professional speech. Tone and using someone's name add warmth: **Оленко, прочитай, будь ласка.** *(Olenka, please read.)*

English speakers sometimes feel Ukrainian commands sound blunt. In Ukrainian classrooms, **Читайте!** and **Пишіть!** are standard instructions — not harsh at all. If you open any Ukrainian textbook by Заболотний, every page says **Робіть вправу!** (Do the exercise!) or **Спишіть речення!** (Copy the sentences!). Adding **будь ласка** is for extra politeness, not basic courtesy. Three natural classroom examples from Dialogue 1 worked perfectly without it: **Читайте текст.** **Напишіть три речення.** **Запитуйте!**

When MUST you use the **ви**-form? Two situations. First, when speaking to one adult you address formally — your teacher, a stranger, a doctor: **Скажіть, будь ласка, де зупинка?** *(Tell me, please, where is the bus stop?)* Second, when speaking to more than one person, regardless of age: **Діти, сідайте!** *(Children, sit down!)* Real-life examples:

- Telling your whole family: **Сідайте!** *(Sit down!)*
- Asking a shop assistant: **Покажіть, будь ласка.** *(Please show me.)*
- Inviting friends: **Ходімо!** *(Let's go!)*

:::tip
**Ходімо!** is a uniquely Ukrainian form — the 1st person plural imperative ("let's go!"). Russian does not have this form and uses a workaround with *давайте*. In standard Ukrainian, do NOT say *давай підемо* — just say **ходімо** or **підемо**.
:::

## Як утворити? (How to Form It)

Formation takes two steps. First, find the stem from the present tense (the **вони** form): **вони читають** → the stem is **читай-**. Second, add the imperative ending. Two patterns: **-й** after a vowel stem (**читай, слухай**) and **-и/-і** after a consonant stem (**пиши, говори**). A simple summary: vowel at the end of the stem → **-й**; consonant → **-и**.

Here are eight high-frequency **ти**-forms. Notice two groups:

**Vowel-stem group** (ending in **-й**):
- **читати** (читають → **читай**) — read
- **слухати** (слухають → **слухай**) — listen

**Consonant-stem group** (ending in **-и/-і/-ь**):
- **писати** (пишуть → **пиши**) — write
- **говорити** (говорять → **говори**) — speak
- **дивитися** (дивляться → **дивись**) — look/watch
- **ходити** (ходять → **ходи**) — walk/go
- **іти** (ідуть → **іди**) — go
- **сісти** (сядуть → **сядь**) — sit down

The verbs **іди** and **сядь** are irregular but essential — learn them as vocabulary. Note the soft sign in **сядь**: Ukrainian writes **ь** after **д** in imperative forms (confirmed by Авраменко, Grade 7).

For **ви**-forms, add **-те** or **-іть** to the **ти**-form. The rule: if the **ти**-form ends in **-й**, add **-те**; if it ends in **-и**, change to **-іть**:

- читай → **читайте**, слухай → **слухайте**
- пиши → **пишіть**, говори → **говоріть**, ходи → **ходіть**
- дивись → **дивіться**, сядь → **сядьте**, іди → **ідіть**

<!-- INJECT_ACTIVITY: fill-in-imperative-forms -->

Four irregular verbs appear constantly in daily speech. They do not follow the stem pattern — memorize them:

- **дати** → **дай** / **дайте** (give)
- **сказати** → **скажи** / **скажіть** (say/tell)
- **їсти** → **їж** / **їжте** (eat)
- **взяти** → **візьми** / **візьміть** (take)

All four have short **ти**-forms: **дай, скажи, їж, візьми**. You will hear these dozens of times every day.

<!-- INJECT_ACTIVITY: quiz-correct-imperative -->

## Підсумок — Summary

Here are the essential imperatives you now know. You can give instructions in the classroom, order at a café, and direct a volleyball warm-up. Two forms: **ти** for friends and family, **ви** for teachers, strangers, and groups.

| Інфінітив | Ти | Ви | Meaning |
|---|---|---|---|
| читати | читай | читайте | read |
| писати | пиши | пишіть | write |
| слухати | слухай | слухайте | listen |
| дивитися | дивись | дивіться | look/watch |
| говорити | говори | говоріть | speak |
| іти | іди | ідіть | go |
| дати | дай | дайте | give |
| сказати | скажи | скажіть | say/tell |
| сісти | сядь | сядьте | sit down |
| відкрити | відкрий | відкрийте | open |

Three ready-made polite phrases to memorize as chunks — they work in shops, at school, and at the doctor's:

- **Скажіть, будь ласка...** — Excuse me, could you tell me...
- **Дайте, будь ласка...** — Could you give me...
- **Покажіть, будь ласка...** — Could you show me...

Learn the whole phrase, not just the verb. When you need something from a stranger, start with **Скажіть, будь ласка** — it is the universal polite opener.

<!-- INJECT_ACTIVITY: group-sort-ty-vy -->

<!-- INJECT_ACTIVITY: fill-in-context-ty-vy -->

## Підсумок

Quick self-check — can you answer these?

- Як сказати "Please read" своєму вчителеві? → **Читайте, будь ласка.**
- Як сказати "Listen!" другові? → **Слухай!**
- Як сказати "Give me, please" у магазині незнайомцю? → **Дайте, будь ласка.**

Now try this: look around where you are right now. Give three instructions to an imaginary friend using imperatives you learned. Write them down: **___! ___! ___!** Use **ти**-forms — your friend is informal. Then rewrite all three as **ви**-forms, as if speaking to your teacher.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: please-do-this
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

**Level: A1.4+ (Module 43/55) — BEGINNER**

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
