<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-time-nature.yaml` file for module **27: Checkpoint: Time and Nature** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-day-paragraph -->`
- `<!-- INJECT_ACTIVITY: fill-in-time-weather -->`
- `<!-- INJECT_ACTIVITY: match-questions-answers -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Mixed review of time, days, and weather chunks
  items:
  - Зустріч {о п'ятій|в п'ятій|у п'ята} годині.
  - Ми йдемо в кіно {у суботу|в суботі|на суботу}.
  - Мій день народження {у січні|в січень|січень}.
  - Сьогодні {іде дощ|іде дощова|дощить} і холодно.
  - Взимку дуже {холодно|спекотно|тепло}.
  - Я прокидаюся о сьомій {ранку|рано|вранці}.
  type: fill-in
- focus: Match the questions to logical answers
  pairs:
  - Котра година? ↔ Десята тридцять.
  - О котрій зустріч? ↔ О першій.
  - Яка сьогодні погода? ↔ Тепло і сонячно.
  - Коли твій день народження? ↔ У жовтні.
  - Що ти робиш у суботу? ↔ Граю у футбол.
  - Як часто ти читаєш? ↔ Кожен день ввечері.
  - Ходімо в парк! ↔ Добре, о котрій?
  - Що ти будеш робити завтра? ↔ Буду працювати.
  type: match-up
- focus: Complete the paragraph describing a day
  items:
  - '{Спочатку|Потім|Нарешті} я прокидаюся і снідаю.'
  - '{Потім|Вранці|Вночі} я йду на роботу.'
  - Я працюю з дев'ятої {до|і|по} п'ятої.
  - '{Після обіду|Вранці|Вночі} я гуляю в парку.'
  - Я гуляю, тому що сьогодні {тепло|холодно|дощ} і сонячно.
  - '{Ввечері|Вдень|Вранці} я вечеряю і слухаю музику.'
  - '{Нарешті|Спочатку|Потім} я лягаю спати о дванадцятій.'
  type: fill-in


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

Це підсумковий модуль фази A1.4. Over the past five modules, you learned to tell time, name days and months, describe the weather, talk about your daily routine, and discuss hobbies. This checkpoint brings everything together — let's see what you already know.

Try answering each question below out loud before reading the model answer. If you can answer confidently, you remember the pattern well. If you hesitate — that's exactly what this module is for.

**1. Час (Time) — M22:**
**Котра зараз година?** (What time is it now?) → **Зараз третя година дня.** (It's three o'clock in the afternoon.)

**2. Календар (Calendar) — M23:**
**Коли у тебе зустріч?** (When is your meeting?) → **У середу, о пів на другу.** (On Wednesday, at half past one.)

**3. Погода (Weather) — M24:**
**Яка сьогодні погода?** (What's the weather today?) → **Хмарно й іде дощ.** (It's cloudy and it's raining.)

**4. Розпорядок дня (Daily routine) — M25:**
**Що ти робиш зранку?** (What do you do in the morning?) → **Спочатку снідаю, потім іду на роботу.** (First I have breakfast, then I go to work.)

**5. Хобі (Hobbies) — M26:**
**Як часто ти займаєшся спортом?** (How often do you exercise?) → **Іноді — у вівторок і четвер.** (Sometimes — on Tuesday and Thursday.)

If you answered three or more without hesitation, your A1.4 foundation is solid. If some felt shaky, pay close attention to those patterns as we review them below.

## Читання (Reading Practice)

Read the following text carefully. As you read, look for: time expressions, days of the week, seasons, weather descriptions, and hobbies. Try to understand the overall meaning before checking the translations below.

> **Мій тиждень починається рано.** *(My week starts early.)* **У понеділок я прокидаюся о сьомій ранку.** *(On Monday I wake up at seven in the morning.)* **Спочатку снідаю, потім іду на роботу.** *(First I have breakfast, then I go to work.)* **Я працюю з дев'ятої до п'ятої.** *(I work from nine to five.)* **У середу ввечері я вивчаю українську.** *(On Wednesday evening I study Ukrainian.)* **В суботу я завжди гуляю в парку.** *(On Saturday I always walk in the park.)* **Іноді граю у футбол.** *(Sometimes I play football.)* **Взимку іде сніг, і я рідко гуляю.** *(In winter it snows, and I rarely walk.)* **Навесні тепло і сонячно — я часто ходжу в кіно.** *(In spring it's warm and sunny — I often go to the cinema.)* **Нарешті вечеряю о пів на восьму.** *(Finally I have dinner at half past seven.)*

Now check your comprehension — can you answer these two questions based on the text?

- **Яку пору року згадує автор?** (Which seasons does the author mention?)
- **Коли він/вона займається хобі?** (When does he/she do hobbies?)

The author mentions two seasons: **взимку** (in winter) and **навесні** (in spring). Hobbies happen **в суботу** (on Saturday) — walking and football — and **навесні** — going to the cinema.

<!-- INJECT_ACTIVITY: fill-in-day-paragraph -->

## Граматика (Grammar Summary)

Here are seven language patterns from A1.4. Study them — with these seven patterns, you can describe any day, any week, any season.

**Pattern 1 — Time:** Two key questions. **Котра година?** (What time is it?) uses nominative: **Третя година.** (Three o'clock.) **О котрій?** (At what time?) uses locative chunks: **Зустріч о першій.** (Meeting at one.) **Фільм о дев'ятій вечора.** (Movie at nine in the evening.)

**Pattern 2 — Days of the week:** Use **у/в** + accusative as a memorized chunk. **У понеділок** (on Monday), **у середу** (on Wednesday), **у неділю** (on Sunday). Remember: the choice between **у** and **в** follows a phonetic rule you'll study in M28 — for now, memorize each form as a chunk.

**Pattern 3 — Months:** Use **у/в** + locative chunk. **У січні** (in January), **у березні** (in March), **в серпні** (in August), **у жовтні** (in October). The pattern: **у/в** + month with the ending **-і**.

**Pattern 4 — Seasons:** These are adverbs — no preposition needed. **Взимку** (in winter), **навесні** (in spring), **влітку** (in summer), **восени** (in autumn). Example: **Влітку тепло.** (It's warm in summer.) **Взимку холодно.** (It's cold in winter.)

**Pattern 5 — Weather:** Impersonal constructions with no subject. **Тепло.** (It's warm.) **Холодно.** (It's cold.) **Сонячно.** (It's sunny.) **Хмарно.** (It's cloudy.) For precipitation: **Іде дощ.** (It's raining.) **Іде сніг.** (It's snowing.)

**Pattern 6 — Sequence:** Three adverbs that order events. **Спочатку** (first) → **потім** (then) → **нарешті** (finally). Example: **Спочатку снідаю, потім працюю.**

**Pattern 7 — Frequency:** A scale from always to never. **Завжди** (always) → **часто** (often) → **іноді** (sometimes) → **рідко** (rarely) → **ніколи** (never).

<!-- INJECT_ACTIVITY: fill-in-time-weather -->

## Діалог (Connected Dialogue)

Оля phones her friend Дмитро. They're planning a weekend outing — park, cinema, a full day together. Notice how one conversation naturally combines time, days, weather, hobbies, and invitations.

> **Оля:** Привіт, Дмитре! Яка завтра погода? *(Hi, Dmytro! What's the weather tomorrow?)*
> **Дмитро:** Привіт! Тепло і сонячно, без дощу! *(Hi! Warm and sunny, no rain!)*
> **Оля:** Чудово! Ходімо в парк у суботу? *(Wonderful! Let's go to the park on Saturday?)*
> **Дмитро:** Добре! Я завжди гуляю в суботу. *(OK! I always walk on Saturday.)*
> **Оля:** О котрій зустрінемося? *(At what time shall we meet?)*
> **Дмитро:** О десятій ранку біля метро. *(At ten in the morning near the metro.)*
> **Оля:** Люблю весну. Навесні так гарно! *(I love spring. It's so beautiful in spring!)*
> **Дмитро:** Я теж! Взимку сидиш вдома... *(Me too! In winter you sit at home...)*
> **Оля:** А потім підемо в кіно? *(And then shall we go to the cinema?)*
> **Дмитро:** О котрій починається фільм? *(What time does the movie start?)*
> **Оля:** О п'ятій тридцять. *(At five thirty.)*
> **Дмитро:** Добре, я часто ходжу в кіно ввечері. *(Good, I often go to the cinema in the evening.)*
> **Оля:** Як часто ти дивишся фільми? *(How often do you watch movies?)*
> **Дмитро:** Іноді — раз на тиждень. *(Sometimes — once a week.)*
> **Оля:** Чудово! До суботи! *(Wonderful! See you Saturday!)*
> **Дмитро:** До зустрічі! *(See you!)*

:::tip Мовні шаблони в діалозі
Notice the four key patterns at work:

- **Weather question:** **Яка погода?** → **Тепло і сонячно.**
- **Invitation:** **Ходімо** + destination — **Ходімо в парк!**
- **Meeting time:** **О котрій?** → **О десятій ранку.**
- **Frequency words:** **завжди**, **часто**, **іноді** — all three appear naturally in the conversation.
:::

<!-- INJECT_ACTIVITY: match-questions-answers -->

## Підсумок — Summary

You've completed phase A1.4 — Time and Nature. This is a real milestone. Look at what you can now do in Ukrainian:

You can tell the time using two question patterns — **Котра година?** for stating the time, and **О котрій?** for saying when something happens — with ordinal chunks like **о третій** and **о пів на дев'яту**. You know all seven days of the week and use them with the right preposition: **у понеділок**, **у середу**, **в суботу**. You can name every month and place it in a sentence: **у листопаді**, **у січні**, **в серпні**. The four seasons come naturally as adverbs: **взимку**, **навесні**, **влітку**, **восени**. You describe the weather with impersonal constructions: **Тепло і сонячно**, **Іде дощ**, **Хмарно**. You tell stories about your day using sequence words — **спочатку**, **потім**, **нарешті** — and you talk about hobbies with frequency: **Я часто читаю**, **Іноді ходжу в кіно**, **Рідко дивлюся телевізор**.

The next phase is A1.5 — Places and the City. You'll learn to ask for directions, name places around town, and buy a **квиток** (ticket). But first comes a short lesson on one of Ukrainian's most distinctive features: **евфонія** (euphony) in M28. Why do we say **у парку** but **в кіно**? You'll find out soon.

**Мова** (language) is more than grammar. When you say **навесні**, **взимку**, **іде дощ** — you're thinking in Ukrainian. That's exactly how people speak every day across Ukraine. Keep going — **у тебе виходить!** (you're doing great!)

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-time-nature
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

**Level: A1.4+ (Module 27/55) — BEGINNER**

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
