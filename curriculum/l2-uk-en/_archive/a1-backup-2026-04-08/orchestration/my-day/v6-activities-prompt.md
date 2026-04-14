<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/my-day.yaml` file for module **25: My Day** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-part-of-day -->`
- `<!-- INJECT_ACTIVITY: match-time-of-day -->`
- `<!-- INJECT_ACTIVITY: fill-in-sequence -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match the activity to the logical time of day
  pairs:
  - прокидаюся ↔ вранці
  - снідаю ↔ вранці
  - працюю ↔ вдень
  - обідаю ↔ вдень
  - вечеряю ↔ ввечері
  - дивлюся фільм ↔ ввечері
  - лягаю спати ↔ вночі
  - сплю ↔ вночі
  type: match-up
- focus: Complete the logical sequence of the day
  items:
  - '{Спочатку|Потім|Нарешті} я прокидаюся і вмиваюся.'
  - Після того я {снідаю|вечеряю|лягаю спати}.
  - Вдень я {працюю|прокидаюся|снідаю} в офісі.
  - О першій годині я {обідаю|вечеряю|прокидаюся}.
  - '{Потім|Спочатку|Вранці} я читаю книгу або дивлюся фільм.'
  - '{Нарешті|Спочатку|Вдень} я лягаю спати о дванадцятій.'
  type: fill-in
- focus: Choose the correct part of the day
  items:
  - Я п'ю каву {вранці|вночі|ввечері}.
  - Ми вечеряємо {ввечері|вранці|вдень}.
  - Вона працює з дев'ятої до п'ятої {вдень|вночі|вранці}.
  - Вони гуляють у парку {після обіду|вночі|вранці}.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- прокидатися (to wake up — review from M20)
- вмиватися (to wash — review from M20)
- одягатися (to get dressed — review from M20)
- вночі (at night)
- після обіду (in the afternoon)
- також (also)
- лягати спати (to go to bed — chunk)
- типовий (typical)
- вільний (free)
required:
- вранці (in the morning)
- вдень (during the day)
- ввечері (in the evening)
- обідати (to have lunch)
- вечеряти (to have dinner)
- відпочивати (to rest)
- після (after)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

You already know how to tell time, name the days of the week, and describe the weather outside. Now it's time to put it all together — telling someone about your whole day. Below are two conversations: one about yesterday, one about tomorrow. The past-tense and future forms here are frozen phrases — just memorize them as chunks for now. The full grammar comes later.

**(Як пройшов твій день? / How was your day?)**

> **Марко:** Привіт! Як пройшов твій день? *(Hi! How was your day?)*
> **Оленка:** Добре! Вранці я працювала в офісі. *(Good! In the morning I worked at the office.)*
> **Марко:** А **потім**? *(And then?)*
> **Оленка:** **Потім** обідала о першій. **Після обіду** гуляла у парку. *(Then I had lunch at one. After lunch I walked in the park.)*
> **Марко:** А ввечері що робила? *(And in the evening, what did you do?)*
> **Оленка:** Ввечері дивилася фільм і читала книгу. **Нарешті** лягла спати о дванадцятій. *(In the evening I watched a film and read a book. Finally I went to bed at twelve.)*
> **Марко:** О дванадцятій? Пізно! *(At twelve? Late!)*

The past forms — **працювала** *(worked)*, **обідала** *(had lunch)*, **гуляла** *(walked)*, **дивилася** *(watched)*, **читала** *(read)*, **лягла** *(went to bed)* — are chunks for now. Full past-tense grammar comes in M48–49.

:::tip
Notice the pattern: **sequence word + verb + time**. For example: **Потім обідала о першій.** The sequence word opens the sentence, the verb follows, and time closes it.
:::

**(Що ти будеш робити завтра? / What will you do tomorrow?)**

> **Оленка:** Що ти будеш робити завтра? *(What will you do tomorrow?)*
> **Марко:** Вранці **буду працювати**. *(In the morning I will work.)*
> **Оленка:** А **після обіду**? *(And in the afternoon?)*
> **Марко:** **Після обіду** буду вивчати українську. *(In the afternoon I will study Ukrainian.)*
> **Оленка:** А ввечері? *(And in the evening?)*
> **Марко:** Ввечері **буду** гуляти. А вночі? **Нарешті буду** спати! *(In the evening I'll walk. And at night? Finally I'll sleep!)*

The future pattern **буду** *(I will)* + infinitive works like a chunk: **буду працювати** *(I will work)*, **буду вивчати** *(I will study)*, **буду гуляти** *(I will walk)*. Full future-tense grammar is in M46.

Same structure, two timelines — yesterday Olenka **працювала** *(worked)*, tomorrow Marko **буду працювати** *(will work)*. The sequence words stay the same either way.

## Мій типовий день (My Typical Day)

Below is a complete model day — a narrative using the present tense you already know from A1.3, combined with time expressions from M22 and the parts-of-day adverbs you'll master in this module. Read it through like a short story, then study how it's built.

> **Я прокидаюся о сьомій. Спочатку вмиваюся і одягаюся. Потім снідаю о восьмій. О дев'ятій починаю працювати. Вдень я працюю до першої. О першій обідаю. Після обіду ще працюю до п'ятої. Ввечері готую вечерю і відпочиваю. О дев'ятій дивлюся фільм або читаю книгу. Нарешті о дванадцятій лягаю спати.**

Every verb here is present tense — forms you already know from M16–M21. The sequence words **спочатку**, **потім**, **після обіду**, **нарешті** connect the actions into a story instead of a random list.

Now let's look at the five parts-of-day adverbs that make this narrative possible:

- **вранці** (in the morning) — roughly before noon. *Вранці я снідаю.*
- **вдень** (during the day) — the working hours, roughly 9 to 17. *Вдень я працюю.*
- **після обіду** (in the afternoon) — literally "after lunch." *Після обіду я відпочиваю.*
- **ввечері** (in the evening) — roughly 18 to 22. *Ввечері я читаю.*
- **вночі** (at night) — roughly 22 to 6. *Вночі я сплю.*

These are adverbs — unchanging words. No case endings, no conjugation. Just place them at the start of a sentence: **Ввечері я читаю.** Compare this with clock time: **о сьомій** *(at seven)* uses a preposition and an ordinal number, while **вранці** *(in the morning)* is a single adverb — no preposition needed.

<!-- INJECT_ACTIVITY: fill-in-part-of-day -->

One more detail: **після обіду** is two words functioning together as a time marker. You can use it alone — **Після обіду я відпочиваю.** *(In the afternoon I rest.)* — or pair it with a clock time: **Після обіду, о третій, я вчу українську.** *(In the afternoon, at three, I study Ukrainian.)*

## Від ранку до вечора (From Morning to Evening)

You've seen **потім** and **нарешті** in the dialogues. Here is the full set of sequence words that let you connect one event to the next, turning isolated sentences into a coherent story:

- **спочатку** (first, to start with) — *Спочатку я снідаю.* *(First I have breakfast.)*
- **потім** (then, next) — *Потім я йду на роботу.* *(Then I go to work.)*
- **після того** / **після цього** (after that) — *Після того я відпочиваю.* *(After that I rest.)*
- **нарешті** (finally) — *Нарешті я лягаю спати.* *(Finally I go to bed.)*
- **також** (also) — *Я також читаю вранці.* *(I also read in the morning.)*
- **а потім** (and then — with a light contrast) — *Я снідаю, а потім іду до офісу.* *(I have breakfast, and then I go to the office.)*

A quick note: **спочатку** is a sequence marker — it means "first" in a chain of events. Don't confuse it with **на початку** *(at the beginning of something)*. At A1, **після того** and **після цього** are interchangeable — use whichever feels natural.

Now let's expand your daily activity verbs. You already know **снідати** *(to have breakfast)* from M20. Here are the other two meal verbs — together they form a natural triad:

- **снідати** (to have breakfast) — review from M20
- **обідати** (to have lunch) — new
- **вечеряти** (to have dinner) — new

All three are Group I verbs ending in **-ати**, conjugated exactly like **читати**: **я снідаю**, **ти снідаєш**, **він/вона снідає**. The pattern is identical for **обідати** *(я обідаю)* and **вечеряти** *(я вечеряю)*.

Two more useful verbs: **відпочивати** *(to rest)* — also Group I: **я відпочиваю**, **ти відпочиваєш**. And the chunk **лягати спати** *(to go to bed)* — treat it as one unit at A1. Full reflexive verb grammar comes in M38.

Combine any verb with a time expression and you have a sentence about your day:

- **О першій я обідаю.** *(At one I have lunch.)*
- **Після роботи я відпочиваю.** *(After work I rest.)*
- **Ввечері я вечеряю о сьомій.** *(In the evening I have dinner at seven.)*
- **О дванадцятій я лягаю спати.** *(At twelve I go to bed.)*

<!-- INJECT_ACTIVITY: match-time-of-day -->

Here's how all three tools — sequence words, time adverbs, and activity verbs — stack together in a natural chain: **Вранці я прокидаюся о сьомій. Спочатку снідаю. Потім іду на роботу. Після того обідаю о першій. Ввечері відпочиваю. Нарешті лягаю спати.** Any two sentences about your day can be connected with **потім** or **після того** — just pick one and keep going.

## Підсумок — Summary

Every sentence you've built in this module follows one formula:

**[Time expression] + [Sequence word] + [Verb + object]**

The pieces are interchangeable. Look at how they combine:

- **О сьомій** [time] — **прокидаюся** [verb] → *At seven — I wake up.*
- **Спочатку** [sequence] — **снідаю** [verb] → *First — I have breakfast.*
- **Потім** [sequence] — **о дев'ятій** [time] — **іду на роботу** [verb + complement] → *Then — at nine — I go to work.*

Time expressions and sequence words both sit at the start of the sentence. You can use one or both — **Потім о дев'ятій іду на роботу** works just as well as **О дев'ятій іду на роботу**.

Here is a longer model day that weaves everything from this module together. Read it, then write your own version below:

> **Мій типовий понеділок починається о шостій. Спочатку я вмиваюся і одягаюся. Потім снідаю — п'ю каву і їм бутерброд. О дев'ятій починаю працювати. Вдень я дуже зайнятий. О першій обідаю в кафе. Після обіду ще працюю до шостої. Ввечері відпочиваю — готую вечерю і дивлюся серіал. Також читаю перед сном. Нарешті о дванадцятій лягаю спати. Завтра — те саме!**

*(My typical Monday starts at six. First I wash up and get dressed. Then I have breakfast — I drink coffee and eat a sandwich. At nine I start working. During the day I'm very busy. At one I have lunch at a café. After lunch I work until six. In the evening I rest — I cook dinner and watch a series. I also read before bed. Finally at twelve I go to bed. Tomorrow — the same!)*

<!-- INJECT_ACTIVITY: fill-in-sequence -->

Now it's your turn. Describe your own typical day using what you've learned:

- Write about your typical Monday from morning to evening (5–8 sentences).
- Use at least 3 time expressions (e.g., **о восьмій**, **після обіду**, **ввечері**).
- Use at least 3 sequence words (**спочатку**, **потім**, **нарешті**).
- Include at least 4 daily activity verbs (**прокидатися**, **снідати**, **обідати**, **відпочивати**, **лягати спати**).
- Starter: **Мій типовий понеділок починається о ___. Спочатку я ___…**

Try reading your text aloud. Does it flow from one event to the next? If two sentences feel disconnected, add **потім** or **після того** between them — that's all it takes to turn a list into a story.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: my-day
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

**Level: A1.4+ (Module 25/55) — BEGINNER**

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
