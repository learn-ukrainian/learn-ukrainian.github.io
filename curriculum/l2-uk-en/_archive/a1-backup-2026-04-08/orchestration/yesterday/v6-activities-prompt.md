<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/yesterday.yaml` file for module **49: Yesterday** (a1).

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

- `<!-- INJECT_ACTIVITY: ordering-daily-routine -->`
- `<!-- INJECT_ACTIVITY: fill-in-time-markers -->`
- `<!-- INJECT_ACTIVITY: fill-in-gender-consistency -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Put the daily routine in chronological order
  items:
  - Зранку я прокинувся.
  - Спочатку я поснідав.
  - Потім я пішов на роботу.
  - Вдень я обідав з колегою.
  - Ввечері я повернувся і дивився серіал.
  - Нарешті я ліг спати.
  type: ordering
- focus: Complete the narrative with time markers and sequenced verbs
  items:
  - Учора {зранку|вдень|потім} я прокинулася о сьомій.
  - '{Спочатку|Нарешті|Вночі} я поснідала.'
  - '{Потім|Зранку|Ввечері} я пішла на роботу.'
  - Вдень я {обідала|обідав|обідали} в кафе.
  - '{Ввечері|Вдень|Зранку} я готувала вечерю.'
  - О десятій я {лягла|ліг|лягли} спати.
  type: fill-in
- focus: Practice gender consistency in narration (Female speaker 'Anna')
  items:
  - Я мала звичайний день. Я {прокинулася|прокинувся} рано.
  - Потім я {поснідала|поснідав}.
  - Після цього я {пішла|пішов} у магазин.
  - Там я {купила|купив} продукти.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- спочатку (first/at first)
- нарешті (finally)
- повернутися (to return)
- лягти (to lie down)
- звичайний (ordinary, adj)
- продукти (groceries, pl)
- серіал (TV series, m)
- колега (colleague, m/f)
required:
- учора (yesterday)
- зранку (in the morning)
- вдень (in the afternoon)
- ввечері (in the evening)
- потім (then)
- прокинутися (to wake up)
- поснідати (to have breakfast)
- обідати (to have lunch)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Dialogues

> **Тарас:** Привіт, Оксано! Як пройшов твій день? *(Hi, Oksana! How was your day?)*
> **Оксана:** Добре! Зранку я прокинулася о сьомій. *(Good! In the morning I woke up at seven.)*
> **Тарас:** Що ти робила зранку? *(What did you do in the morning?)*
> **Оксана:** Я поснідала і пішла на роботу. *(I had breakfast and went to work.)*
> **Тарас:** А вдень? *(And in the afternoon?)*
> **Оксана:** Вдень я працювала і обідала з колегою. *(In the afternoon I worked and had lunch with a colleague.)*
> **Тарас:** А ввечері? *(And in the evening?)*
> **Оксана:** Ввечері я дивилася серіал і лягла спати о десятій. *(In the evening I watched a TV series and went to bed at ten.)*

Тарас walks Оксана through her entire day using three simple questions — **зранку** (in the morning), **вдень** (in the afternoon), **ввечері** (in the evening). These three time markers are the spine of every past-day story in Ukrainian. Notice that Оксана uses **-ла** endings throughout: **прокинулася**, **поснідала**, **пішла**, **працювала**, **обідала**, **дивилася**, **лягла**. She is female, so every verb matches.

Now a second conversation — this time with a male speaker.

> **Марія:** Що ти робив у суботу? *(What did you do on Saturday?)*
> **Іван:** О, я мав чудовий день! *(Oh, I had a wonderful day!)*
> **Марія:** Розкажи! *(Tell me!)*
> **Іван:** Зранку я ходив на ринок і купив фрукти. *(In the morning I went to the market and bought fruit.)*
> **Марія:** А потім? *(And then?)*
> **Іван:** Потім я готував обід. А вдень гуляв у парку. *(Then I cooked lunch. And in the afternoon I walked in the park.)*
> **Марія:** А ввечері? *(And in the evening?)*
> **Іван:** Ввечері ми з другом ходили в ресторан. *(In the evening my friend and I went to a restaurant.)*
> **Марія:** Як файно! *(How nice!)*

Compare the two stories. Оксана says **прокинулася**, **пішла**, **дивилася** — all with **-ла** or **-лася**. Іван says **ходив**, **купив**, **готував**, **гуляв** — all with **-в**. The gender rule is simple: pick your form at the start and keep it for the whole story. If you are male, every past verb ends in **-в** or **-вся**. If you are female, every past verb ends in **-ла** or **-лася**. Never switch mid-story.

## Розповідь про день (Narrating a Day)

Every good story about your day has a frame. In Ukrainian, four adverbs create that frame — four time slots that carry you from morning to night:

- **Зранку** (in the morning) — Зранку я поснідав.
- **Вдень** (in the afternoon) — Вдень я обідав.
- **Ввечері** (in the evening) — Ввечері я дивився фільм.
- **Вночі** (at night) — Вночі я спав.

These words never change form. They work the same way whether you are male, female, talking about yourself or someone else. They are adverbs — **незмінні** — and they simply answer the question **коли?** (when?).

But time slots alone give you snapshots, not a story. To connect events into a flowing narrative, you need sequencing words:

- **спочатку** (first) — Спочатку я поснідав.
- **потім** (then) — Потім я пішов на роботу.
- **після цього** (after that) — Після цього я обідав.
- **нарешті** (finally) — Нарешті я ліг спати.

Compare these two versions of the same three events:

Without connectors (choppy): **Я поснідав. Я пішов на роботу. Я обідав.**

With connectors (flowing): **Спочатку я поснідав. Потім я пішов на роботу. Після цього я обідав.**

Which version sounds like a story? The second one. The connectors **спочатку → потім → після цього → нарешті** turn a list of facts into a narrative.

Now the verbs themselves. Here are the six daily routine verbs you need, with both gender forms side by side:

| Infinitive | He (male) | She (female) |
|---|---|---|
| **прокинутися** (to wake up) | прокинувся | прокинулася |
| **поснідати** (to have breakfast) | поснідав | поснідала |
| **піти** (to go) | пішов | пішла |
| **обідати** (to have lunch) | обідав | обідала |
| **повернутися** (to return) | повернувся | повернулася |
| **лягти спати** (to go to bed) | ліг спати | лягла спати |

Most pairs follow a clear pattern: **-в / -ла** or **-вся / -лася**. But two pairs look different from the rest. **Пішов / пішла** — the male form has **-шов**, not a simple **-в**. And **ліг / лягла** — the male form has no suffix at all, just **ліг**. These are irregular, so learn them as fixed pairs:

- **Він пішов на роботу.** *(He went to work.)*
- **Вона пішла на роботу.** *(She went to work.)*
- **Він ліг спати о десятій.** *(He went to bed at ten.)*
- **Вона лягла спати о десятій.** *(She went to bed at ten.)*

<!-- INJECT_ACTIVITY: ordering-daily-routine -->

## Мій учорашній день (My Yesterday)

Here is a complete story of one person's day. Read it through — every verb is in the **-ла** form because the speaker, Anna, is female.

:::note
**Учора був звичайний день.** Зранку я прокинулася о пів на сьому. Я поснідала — їла кашу і пила каву. Потім я пішла на роботу. Вдень я обідала в кафе біля офісу. Я замовила салат і сік. Після роботи я ходила в магазин і купила продукти. Ввечері я готувала вечерю і дивилася серіал. О одинадцятій я лягла спати.

*(Yesterday was an ordinary day. In the morning I woke up at half past six. I had breakfast — I ate porridge and drank coffee. Then I went to work. In the afternoon I had lunch at a café near the office. I ordered a salad and juice. After work I went to the store and bought groceries. In the evening I cooked dinner and watched a TV series. At eleven I went to bed.)*
:::

Count the past-tense verbs Anna uses: **прокинулася**, **поснідала**, **їла**, **пила**, **пішла**, **обідала**, **замовила**, **ходила**, **купила**, **готувала**, **дивилася**, **лягла** — twelve verbs, all with **-ла** or **-лася**. Not a single **-в** form. This is gender consistency in action. Anna chose her gender at the first verb and never switched.

Now it is your turn. Build your own **учорашній день** (yesterday) using this template:

- **Учора...** *(Yesterday...)*
- **Зранку я ___.**
- **Потім ___.**
- **Вдень я ___.**
- **Ввечері ___.**
- **О ___ годині я ліг/лягла спати.**

Plug in verbs from the table above. Add places you already know — **кафе**, **парк**, **магазин**, **робота** (work). Add people — **друг** (friend, male), **колега** (colleague), **подруга** (friend, female). Remember: pick your gender at the start. If you are male, use **прокинувся**, **поснідав**, **пішов**, **ліг**. If you are female, use **прокинулася**, **поснідала**, **пішла**, **лягла**. Keep it consistent to the very last verb.

<!-- INJECT_ACTIVITY: fill-in-time-markers -->

<!-- INJECT_ACTIVITY: fill-in-gender-consistency -->

## Summary

Everything you need to narrate your day fits into four categories:

**1. Time frame** — the skeleton of the story:
**зранку** → **вдень** → **ввечері** → **вночі**

**2. Sequence chain** — the connectors that turn sentences into a story:
**спочатку** → **потім** → **після цього** → **нарешті**

**3. Past-tense forms** — the six essential daily verbs:
**прокинувся / прокинулася**, **поснідав / поснідала**, **пішов / пішла**, **обідав / обідала**, **повернувся / повернулася**, **ліг спати / лягла спати**. The irregular pairs — **пішов/пішла** and **ліг/лягла** — look different from the regular **-в / -ла** pattern. Know them cold.

**4. Gender rule** — choose male or female at sentence one and never switch mid-story.

After 49 modules, you can introduce yourself, ask for things, talk about your family, describe your home, order food, and tell the time. Now you can tell the full story of your day. **Учора я прокинувся, поснідав і пішов** — three verbs, one sentence, a whole morning. That is what narrative sounds like in Ukrainian. In модуль 50, you will learn the future tense — and the same skeleton (**зранку / вдень / ввечері**) will work for **завтра** (tomorrow) too.

The same past-narration toolkit works in any situation — not just daily routines. Here is a short scene at a police station:

> **Поліцейський:** Де ви припаркували велосипед? *(Where did you park the bicycle?)*
> **Свідок:** Я припаркував велосипед біля магазину. *(I parked the bicycle near the store.)*
> **Свідок:** Потім я зайшов у кав'ярню. *(Then I went into a café.)*
> **Свідок:** Я вийшов — велосипед зник. *(I came out — the bicycle was gone.)*
> **Поліцейський:** Ви бачили когось? *(Did you see anyone?)*
> **Свідок:** Я бачив чоловіка в куртці та кепці. *(I saw a man in a jacket and cap.)*

Five past-tense verbs — **припаркував**, **зайшов**, **вийшов**, **зник**, **бачив** — in a real-world situation. Same toolkit, different context. Past narration works everywhere.

## Підсумок

Answer these questions aloud or in writing — use full sentences:

- **О котрій ти прокинувся/прокинулася учора?**
- **Що ти робив/робила зранку?**
- **Де ти обідав/обідала вдень?**
- **Що ти робив/робила ввечері?**
- **О котрій ти ліг/лягла спати?**

Use at least five different past-tense verbs in your answers. Structure your story with **зранку → вдень → ввечері** and connect events with **спочатку**, **потім**, **після цього**. If you can tell your whole **учорашній день** without switching genders — you are ready for модуль 50.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: yesterday
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

**Level: A1.4+ (Module 49/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-gender
- **group-sort** — Він, вона чи воно?: Sort nouns by grammatical gender using ending rules
  - Instruction: *Розподіліть слова за родами*
- **quiz** — Який рід?: Determine gender from ending — consonant=masc, -а/-я=fem, -о/-е=neut
- **fill-in** — Мій, моя чи моє?: Choose possessive that matches noun gender
  - Instruction: *Вставте правильне слово*
- **match-up** — Іменник + займенник: Match nouns to він/вона/воно

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
