<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/free-time.yaml` file for module **26: Free Time** (a1).

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

- `<!-- INJECT_ACTIVITY: match-hobby-verbs -->`
- `<!-- INJECT_ACTIVITY: fill-in-prepositions -->`
- `<!-- INJECT_ACTIVITY: fill-in-frequency -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match the verb to the logical noun (hobbies)
  pairs:
  - грати ↔ у футбол
  - грати ↔ на гітарі
  - слухати ↔ музику
  - дивитися ↔ фільми
  - ходити ↔ в кіно
  - ходити ↔ в театр
  - читати ↔ книгу
  - малювати ↔ вдома
  type: match-up
- focus: Complete the invitations and frequency sentences
  items:
  - Я {ніколи не|завжди|часто} працюю у неділю.
  - Вона грає у теніс двічі {на тиждень|у тиждень|в тиждень}.
  - — {Ходімо|Давай|Ідемо} в кіно у суботу! — Добре!
  - Я люблю спорт, тому {часто|ніколи|рідко} граю у баскетбол.
  - Я не маю часу, тому {рідко|часто|завжди} читаю книги.
  - — Що ти робиш {у вихідні|вихідні|на вихідні}? — Відпочиваю.
  type: fill-in
- focus: Choose the correct preposition for the activity
  items:
  - Він грає {на|у|в} піаніно.
  - Ми граємо {у|на|в} футбол.
  - Я хочу ходити {на|в|у} концерт.
  - Вони ходять {в|на|у} театр раз на місяць.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- завжди (always)
- зазвичай (usually)
- ніколи (never)
- театр (theater, m)
- концерт (concert, m)
- музей (museum, m)
- давай (let's — informal)
- раз (once/time)
required:
- вихідні (weekend, pl)
- спорт (sport, m)
- футбол (football, m)
- кіно (cinema, n — indeclinable)
- часто (often)
- іноді (sometimes)
- рідко (rarely)
- ходімо (let's go!)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Вітя and Лєна are standing by a bulletin board at the community center, scanning sign-up sheets for weekend activities. Their conversation covers everything this module teaches — invitations, hobbies, and how often they do things.

### Діалог 1 — Weekend Plans

> **Лєна:** Привіт, Вітю! Що ти робиш у вихідні? *(Hi, Vitya! What are you doing on the weekend?)*
> **Вітя:** Привіт! Зазвичай я гуляю і читаю. *(Hi! Usually I walk and read.)*
> **Лєна:** А в суботу? Ходімо в кіно! *(And on Saturday? Let's go to the cinema!)*
> **Вітя:** О, добре! О котрій? *(Oh, great! At what time?)*
> **Лєна:** О п'ятій. *(At five.)*
> **Вітя:** Чудово! А потім — гуляємо? *(Wonderful! And then — we walk?)*
> **Лєна:** Так, звичайно! *(Yes, of course!)*

Notice how Лєна uses **Ходімо!** (Let's go!) to invite Вітя. This is the natural Ukrainian invitation — **Ходімо** + activity + day + time. She names the activity (**в кіно**), the day is already clear (**в суботу**), and when Вітя asks **О котрій?** (At what time?), she gives a time from M25: **О п'ятій** (At five).

### Діалог 2 — Hobbies and Frequency

> **Вітя:** Ти любиш спорт? *(Do you like sports?)*
> **Лєна:** Так, я граю у футбол. *(Yes, I play football.)*
> **Вітя:** Справді? Як часто? *(Really? How often?)*
> **Лєна:** Двічі на тиждень, у вівторок і четвер. *(Twice a week, on Tuesday and Thursday.)*
> **Вітя:** А ще? Що ти робиш? *(And what else? What do you do?)*
> **Лєна:** Іноді слухаю музику і малюю. *(Sometimes I listen to music and draw.)*
> **Вітя:** Я теж малюю! А в музей ходиш? *(I draw too! Do you go to the museum?)*
> **Лєна:** Рідко. Раз на місяць. *(Rarely. Once a month.)*

The key question here is **Як часто?** (How often?) — it opens the door to frequency adverbs like **іноді** (sometimes) and **рідко** (rarely), plus numeric expressions like **двічі на тиждень** (twice a week). Лєна answers naturally, combining hobby verbs with how often she does each one.

:::tip
Two communicative tools from these dialogues: **Ходімо!** (Let's go!) for invitations, and **Як часто?** (How often?) for asking about frequency. Both appear naturally in conversation before any formal explanation — you already understand them from context.
:::

## Хобі і спорт (Hobbies and Sports)

In M15, you learned the pattern **Я люблю** + infinitive (I like to...). Now we expand that with specific hobby verbs. Each verb naturally pairs with a noun — learn them as chunks, not separate words:

- **малювати** (to draw) — Я люблю малювати.
- **фотографувати** (to take photos) — Вона любить фотографувати.
- **слухати музику** (to listen to music) — Він слухає музику.
- **дивитися фільми** (to watch films) — Ми дивимося фільми.
- **дивитися серіали** (to watch series) — Вони дивляться серіали.

These verbs and their objects belong together. When you say **слухати**, the next word is almost always **музику**. When you say **дивитися**, you expect **фільми** or **серіали**. Think of them as a single unit.

Ukrainian has two different prepositions for **грати** (to play), depending on what you play. For sports, use **у**. For instruments, use **на**:

- **грати у футбол** (to play football)
- **грати у баскетбол** (to play basketball)
- **грати у теніс** (to play tennis)
- **грати у волейбол** (to play volleyball)
- **грати на гітарі** (to play guitar)
- **грати на піаніно** (to play piano)
- **грати на скрипці** (to play violin)

:::caution
Don't choose the preposition — learn the whole phrase. Sport → **у**, instrument → **на**. If you memorize **грати у футбол** and **грати на гітарі** as complete chunks, you'll never mix them up.
:::

<!-- INJECT_ACTIVITY: match-hobby-verbs -->

Going out for entertainment also follows a chunk pattern: **ходити** + **в** or **на** + destination. Memorize these as fixed phrases:

- **ходити в кіно** (to go to the cinema) — Я ходжу в кіно.
- **ходити в театр** (to go to the theater) — Він ходить в театр.
- **ходити на концерт** (to go to a concert) — Вона ходить на концерт.
- **ходити в музей** (to go to a museum) — Ми ходимо в музей.

The case grammar behind **в** and **на** comes later in A1.5 — for now, memorize these as full phrases. You already know the destinations; just attach **ходити** to the front.

Now combine several chunks to describe a range of hobbies. Try reading these aloud:

- Я граю у баскетбол і слухаю музику.
- Вона грає на гітарі і малює.
- Вони ходять в театр і дивляться фільми.

Your turn: pick two or three of your own hobbies and describe them using the same structures. Use **Я люблю** + infinitive, or just the verb + object.

<!-- INJECT_ACTIVITY: fill-in-prepositions -->

## Як часто? (How Often?)

Ukrainian has six core frequency adverbs. Think of them on a scale from "always" to "never":

**завжди** (always) → **зазвичай** (usually) → **часто** (often) → **іноді** (sometimes) → **рідко** (rarely) → **ніколи** (never)

Each one in a sentence:

- Я **завжди** снідаю. *(I always eat breakfast.)*
- Вона **зазвичай** читає ввечері. *(She usually reads in the evening.)*
- Він **часто** грає у теніс. *(He often plays tennis.)*
- Ми **іноді** ходимо в кіно. *(We sometimes go to the cinema.)*
- Вона **рідко** дивиться серіали. *(She rarely watches series.)*
- Він **ніколи не** грає у футбол. *(He never plays football.)*

A note on **іноді**: you may also hear **інколи**, which means the same thing. Use **іноді** as your main word — it's more common at this level.

Word order is straightforward: the frequency adverb goes **before the verb** in a neutral statement. **Я часто гуляю.** **Він іноді малює.** One special rule: **ніколи** always requires **не** directly before the verb. This is Ukrainian double negation — you saw it in M19. The two words are inseparable:

- Я **ніколи не** працюю у неділю. *(I never work on Sunday.)*
- Він **ніколи не** ходить у театр. *(He never goes to the theater.)*

:::note
**Ніколи** + **не** = always together. Dropping **не** sounds incomplete in Ukrainian, even though English uses only "never."
:::

<!-- INJECT_ACTIVITY: fill-in-frequency -->

Beyond single-word adverbs, Ukrainian uses numeric frequency expressions. These go **after the verb** — the opposite position from single-word adverbs:

- **раз на тиждень** (once a week)
- **двічі на тиждень** (twice a week)
- **тричі на тиждень** (three times a week)
- **кожен день** (every day)
- **раз на місяць** (once a month)

In full sentences:

- Я граю у футбол **двічі на тиждень**. *(I play football twice a week.)*
- Вона ходить у кіно **раз на місяць**. *(She goes to the cinema once a month.)*
- Він малює **кожен день**. *(He draws every day.)*
- Ми граємо у волейбол **тричі на тиждень**. *(We play volleyball three times a week.)*

You can even combine both types — an adverb before the verb and a numeric expression after it:

- Я **часто** граю у теніс — **двічі або тричі на тиждень**. *(I often play tennis — two or three times a week.)*
- Вона **рідко** ходить у театр — **раз на місяць**. *(She rarely goes to the theater — once a month.)*

Try it yourself: pick two of your hobbies and add a frequency to each — one single-word adverb and one numeric expression. This combination is exactly what you'll need for the A1.4 checkpoint.

## Підсумок — Summary

This module gave you three building blocks for talking about free time:

1. **Hobby verbs** — **Я люблю** + infinitive, **грати у** + sport, **грати на** + instrument, **ходити в/на** + destination. All learned as chunks — verb and object together.
2. **Invitation patterns** — **Ходімо!** (Let's go!) + activity + time + day. This is the native Ukrainian way to invite someone, using the 1st person plural imperative. Combine with days from M24 and times from M25 for a complete invitation.
3. **Frequency scale** — **завжди, зазвичай, часто, іноді, рідко, ніколи** before the verb. Numeric expressions (**двічі на тиждень, раз на місяць**) after the verb. Double negation with **ніколи не**.

### Self-Check

Test yourself — answer each question aloud in Ukrainian:

- How do you say "let's go to the cinema"? → **Ходімо в кіно!**
- What is your hobby? → **Я граю у футбол.** / **Я люблю малювати.** / **Я слухаю музику.**
- How often do you play tennis? → **Двічі на тиждень.** / **Іноді.** / **Рідко.**
- Do you always watch series? → **Так, я завжди дивлюся.** / **Ні, я ніколи не дивлюся.**
- What do you do on the weekend? → **Я зазвичай гуляю і читаю.**
- Does he play piano or football? → **Він грає на піаніно.**

If you answered four or more, you're ready for M27.

All four A1.4 skills now come together: time expressions from M25, days of the week from M24, weather from M23, and now free-time activities with frequency. At the checkpoint (M27), you'll describe a full day from **ранок** (morning) to **вечір** (evening) — including the weather, your plans, and how often you do your activities. The invitation and frequency patterns from this module are essential building blocks for that final A1.4 task.

**Ти вже вмієш говорити про хобі, запрошувати друзів і пояснювати, як часто ти щось робиш. Це — справжня розмова!** *(You can already talk about hobbies, invite friends, and explain how often you do things. That's real conversation!)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: free-time
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

**Level: A1.4+ (Module 26/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


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
