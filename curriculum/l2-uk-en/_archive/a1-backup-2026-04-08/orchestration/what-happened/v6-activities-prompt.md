<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/what-happened.yaml` file for module **48: What Happened?** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-past-tense -->`
- `<!-- INJECT_ACTIVITY: matching-past-tense -->`
- `<!-- INJECT_ACTIVITY: fill-in-past-tense-core -->`
- `<!-- INJECT_ACTIVITY: fill-in-gender-based -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Form past tense (він / вона / вони) for all core verbs
  items:
  - Учора він {читав|читала|читати} книжку.
  - Олена {готувала|готував|готували} вечерю.
  - Ми {гуляли|гуляв|гуляла} в парку.
  - Вони {працювали|працював|працювало} разом.
  - Тарас {дивився|дивилася|дивилися} фільм.
  - Що ти {робив|робила|робили} учора, Іване?
  type: fill-in
- focus: Match pronoun to the correct past tense ending
  pairs:
  - він: працював
  - вона: працювала
  - воно: працювало
  - вони: працювали
  - Тарас: говорив
  - Олена: говорила
  type: matching
- focus: Choose correct gender based on the subject
  items:
  - Марія {дивилася|дивився|дивилися} фільм.
  - Мій брат {гуляв|гуляла|гуляли} у парку.
  - Вони {провели|провів|провела} вихідні разом.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- минулий (past, adj)
- вихідні (weekend, pl)
- субота (Saturday, f)
- неділя (Sunday, f)
- разом (together)
- фільм (film, m)
- провести (to spend time)
required:
- учора (yesterday)
- робити (to do)
- читати (to read)
- працювати (to work)
- гуляти (to walk)
- готувати (to cook)
- дивитися (to watch)
- говорити (to speak)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Dialogues

Monday morning. Оксана and Дмитро meet by the coffee machine at work. They haven't seen each other since Friday — time to catch up on the weekend.

> **Оксана:** Привіт, Дмитре! Що ти робив учора? *(Hi, Dmytro! What did you do yesterday?)*
> **Дмитро:** Привіт! Я читав книжку. *(Hi! I read a book.)*
> **Оксана:** А яку? *(Which one?)*
> **Дмитро:** Детектив. А ти? *(A detective novel. And you?)*
> **Оксана:** Я готувала вечерю. *(I cooked dinner.)*
> **Дмитро:** А що робив Тарас? *(And what did Taras do?)*
> **Оксана:** Він гуляв у парку. *(He walked in the park.)*
> **Дмитро:** А Олена? *(And Olena?)*
> **Оксана:** Вона працювала весь день. *(She worked all day.)*

Notice the verb **робити** (to do). Дмитро says **робив** — because he is male. Оксана would say **робила** — because she is female. Same verb, different ending. This is the key to Ukrainian past tense: the ending tells you the speaker's gender, not who they are grammatically.

The next day, Богдан and Марія compare how they spent the full weekend. Богдан asks **«Як ти провела вихідні?»** (How did you spend the weekend?) — using **провела** because he's asking a woman.

> **Богдан:** Як ти провела вихідні? *(How did you spend the weekend?)*
> **Марія:** Чудово! У суботу я ходила в кафе. *(Great! On Saturday I went to a café.)*
> **Богдан:** А в неділю? *(And on Sunday?)*
> **Марія:** У неділю я дивилася фільм вдома. А ти? *(On Sunday I watched a film at home. And you?)*
> **Богдан:** Я провів суботу вдома. Готував і читав. *(I spent Saturday at home. I cooked and read.)*
> **Марія:** А в неділю? *(And on Sunday?)*
> **Богдан:** У неділю ми гуляли в парку. *(On Sunday we walked in the park.)*
> **Марія:** Як приємно! *(How nice!)*

Марія uses feminine forms: **ходила**, **провела**, **дивилася**. Богдан uses masculine forms: **провів**, **готував**. When Богдан says **ми гуляли** (we walked), the ending is **-ли** — the plural form, which is the same regardless of gender.

Every verb in these dialogues changed its ending depending on who was speaking — and that is exactly what you will learn now.

<!-- INJECT_ACTIVITY: fill-in-past-tense -->

## Минулий час (Past Tense)

Here is the core insight: Ukrainian past tense does not mark **person** — it marks **gender**. This is completely different from present tense. Compare:

| | Present tense (person changes) | Past tense (gender changes) |
|---|---|---|
| я | читаю | читав (♂) / читала (♀) |
| ти | читаєш | читав (♂) / читала (♀) |
| він / вона | читає / читає | читав (♂) / читала (♀) |

In present tense, **я читаю** and **ти читаєш** have different endings — the ending shows the person. In past tense, **я читав** and **він читав** are identical — both masculine. The ending shows gender, not person.

### How to form the past tense

The rule is straightforward. Take any infinitive, remove **-ти**, and add the gender ending:

- **-в** → він (masculine singular)
- **-ла** → вона (feminine singular)
- **-ло** → воно (neuter singular)
- **-ли** → вони (plural, all genders)

Walk through it with **читати** (to read): **читати** → **чита-** → **він читав** / **вона читала** / **воно читало** / **вони читали**.

The same pattern works for **гуляти** (to walk): **гуляти** → **гуля-** → **він гуляв** / **вона гуляла** / **воно гуляло** / **вони гуляли**.

And for **працювати** (to work): **працювати** → **працюва-** → **він працював** / **вона працювала** / **воно працювало** / **вони працювали**.

:::tip
Four endings — that's all: **-в**, **-ла**, **-ло**, **-ли**.
:::

### Reflexive verbs

Reflexive verbs like **дивитися** (to watch) keep the **-ся** particle after the gender ending: **він дивився** / **вона дивилася** / **воно дивилося** / **вони дивилися**. Two example sentences show the pattern:

- **Тарас дивився фільм.** — Taras watched a film.
- **Ірина дивилася серіал.** — Iryna watched a series.

Compare with non-reflexive **читати**: він читав / вона читала — no **-ся** at the end. With reflexive verbs, the **-ся** simply tags along after the gender suffix.

### Gender reveals the speaker

The same speaker uses different endings depending on their own gender. A male speaker says **«Я читав книжку»** (I read a book). A female speaker says **«Я читала книжку»** — same meaning, same person **я**, different ending.

This means the question **«Що ти робив?»** is directed at a male, while **«Що ти робила?»** is directed at a female. Both mean "What did you do?" — the ending matches the listener's gender.

One more thing: **вони** (they) always takes **-ли**, regardless of whether the group is male, female, or mixed:

- **Він читав.** — He read.
- **Вона читала.** — She read.
- **Я читав.** — I (male) read.
- **Я читала.** — I (female) read.
- **Вони читали.** — They read. (always **-ли**)

<!-- INJECT_ACTIVITY: matching-past-tense -->

## Практика (Practice)

Here are the six core verbs you already know from earlier modules — now in their full past tense forms:

| Infinitive | він (♂) | вона (♀) | воно (n.) | вони (pl.) |
|---|---|---|---|---|
| читати | читав | читала | читало | читали |
| працювати | працював | працювала | працювало | працювали |
| гуляти | гуляв | гуляла | гуляло | гуляли |
| готувати | готував | готувала | готувало | готували |
| дивитися | дивився | дивилася | дивилося | дивилися |
| говорити | говорив | говорила | говорило | говорили |

The stems are familiar — you have used these verbs in present tense throughout A1. The only new piece is the ending: **-в**, **-ла**, **-ло**, **-ли** (and **-ся** sticking to reflexive verbs).

<!-- INJECT_ACTIVITY: fill-in-past-tense-core -->

### Talking about the past

To describe past events, place a time word at the beginning of the sentence. Two essential time expressions: **учора** (yesterday) and **минулого тижня** (last week). The time word doesn't change the verb form — it just sets the scene:

- **Учора я читав цікаву книжку.** — Yesterday I read an interesting book.
- **Минулого тижня вона працювала в офісі.** — Last week she worked in the office.
- **У суботу ми гуляли в парку.** — On Saturday we walked in the park.
- **В неділю вони готували вечерю разом.** — On Sunday they cooked dinner together.

Notice how the time word (**учора**, **у суботу**, **в неділю**) sits at the front of the sentence. This is natural Ukrainian word order — time comes first for emphasis, but the verb ending stays the same no matter where the time word is placed.

<!-- INJECT_ACTIVITY: fill-in-gender-based -->

### Putting it all together

Now try building short exchanges using **«Що ти робив/робила учора?»** (What did you do yesterday?):

> **Оксана:** Що ти робив учора, Андрію? *(What did you do yesterday, Andrii?)*
> **Андрій:** Я читав і гуляв у парку. *(I read and walked in the park.)*
> **Оксана:** А ввечері? *(And in the evening?)*
> **Андрій:** Ввечері я дивився фільм. *(In the evening I watched a film.)*

And the female version:

> **Тарас:** Що ти робила учора, Оксано? *(What did you do yesterday, Oksana?)*
> **Оксана:** Я готувала вечерю. Потім говорила з мамою. *(I cooked dinner. Then I talked with mom.)*

The question changes — **робив** for a male listener, **робила** for a female listener. The answers change too, matching the speaker's own gender.

## Summary

### The formation rule

Past tense in Ukrainian follows one simple pattern: take the infinitive stem (remove **-ти**) and add the gender ending — **-в** (він), **-ла** (вона), **-ло** (воно), **-ли** (вони).

:::note
In Ukrainian, the past tense ending agrees with the **gender** of the subject — not the grammatical person. **Я читав** and **він читав** are identical because both subjects are masculine. **Я читала** and **вона читала** are identical because both are feminine.
:::

English has no equivalent — "I read" and "she read" look the same regardless of gender. Ukrainian always tells you who is speaking.

### All six verbs at a glance

| Verb | він (♂) | вона (♀) | вони (pl.) |
|---|---|---|---|
| читати | читав | читала | читали |
| працювати | працював | працювала | працювали |
| гуляти | гуляв | гуляла | гуляли |
| готувати | готував | готувала | готували |
| дивитися | дивився | дивилася | дивилися |
| говорити | говорив | говорила | говорили |

The endings are consistent: **-в / -ла / -ло / -ли**. The plural **вони** always ends in **-ли** — no gender distinction in plural.

### Useful phrases for talking about the past

Four ready-made conversation starters you can use right away:

- **Що ти робив/робила учора?** — What did you do yesterday? (use **робив** for a male, **робила** for a female)
- **Як ти провів/провела вихідні?** — How did you spend the weekend? (same pattern — **провів** ♂ / **провела** ♀)
- **Учора я читав/читала книжку.** — Yesterday I read a book. (match YOUR gender)
- **Ми гуляли разом.** — We walked together. (plural = always **-ли**)

Each question comes in a pair — one masculine form, one feminine form. Choose the one that matches the person you are speaking to.

## Підсумок

Check yourself against these questions:

- Can you form the past tense of **читати** for all four forms? → **читав** / **читала** / **читало** / **читали**
- What ending does **вони** always take? → **-ли**
- What past-tense form would a female speaker use for "I worked"? → **я працювала**
- How do you ask "What did you do?" to a male friend? → **Що ти робив?**
- How do you ask a female friend? → **Що ти робила?**

**Your turn:** Tell your partner three things you did last week using three different verbs. Remember to use the correct gender ending for **я** — if you are male, every verb ends in **-в**; if you are female, every verb ends in **-ла**. For example: **«Учора я читав книжку. У суботу я гуляв у парку. В неділю я готував вечерю.»** Now swap the endings if you are female!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: what-happened
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

**Level: A1.4+ (Module 48/55) — BEGINNER**

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
