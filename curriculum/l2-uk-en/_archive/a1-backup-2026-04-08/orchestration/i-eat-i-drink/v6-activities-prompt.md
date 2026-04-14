<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/i-eat-i-drink.yaml` file for module **37: I Eat, I Drink** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-conjugation -->`
- `<!-- INJECT_ACTIVITY: fill-in-accusative -->`
- `<!-- INJECT_ACTIVITY: quiz-accusative -->`
- `<!-- INJECT_ACTIVITY: group-sort-accusative -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- blanks:
  - Я їм (риба) {рибу}.
  - Вона п'є (вода) {воду}.
  - Він їсть (хліб) {хліб}.
  - Ми п'ємо (молоко) {молоко}.
  - Вони їдять (каша) {кашу}.
  - Ти п'єш (кава) {каву}.
  - Я їм (суп) {суп}.
  - Вона їсть (картопля) {картоплю}.
  focus: Form the accusative case for feminine (-а/-я → -у/-ю) and masculine/neuter
    (no change)
  items: 8
  type: fill-in
- focus: Select the correct accusative form to complete the sentence
  items: 6
  questions:
  - Я п'ю... (каву / кава / кави)
  - Він їсть... (рибу / риба / рибі)
  - Ми п'ємо... (сік / соку / соком)
  - Вона їсть... (м'ясо / м'ясу / м'яса)
  - Вони п'ють... (воду / вода / воді)
  - Ти їш... (кашу / каша / каші)
  type: quiz
- blanks:
  - Я {їм} суп.
  - Ми {п'ємо} чай.
  - Вона {їсть} хліб.
  - Вони {п'ють} воду.
  - Ти {їси} рибу?
  - Ви {п'єте} каву?
  - Він {п'є} сік.
  - Вони {їдять} кашу.
  focus: Conjugate the verbs їсти (irregular) and пити (Group I)
  items: 8
  type: fill-in
- focus: Sort nouns based on how they change in the accusative case (inanimate)
  groups:
  - items:
    - кава
    - вода
    - риба
    - каша
    name: Змінюється (-у/-ю)
  - items:
    - хліб
    - сік
    - молоко
    - м'ясо
    name: Не змінюється (як у називному)
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- кашу (porridge — accusative)
- картоплю (potato — accusative)
- сметану (sour cream — accusative)
- їсть (he/she eats)
- п'є (he/she drinks)
- їдять (they eat)
- п'ють (they drink)
required:
- їсти (to eat — irregular)
- пити (to drink)
- їм (I eat)
- п'ю (I drink)
- каву (coffee — accusative)
- воду (water — accusative)
- рибу (fish — accusative)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Two colleagues sit down for lunch at work, unpacking their food containers. What do they eat? What do they drink?

> **Марія:** Що ти їси на сніданок? *(What do you eat for breakfast?)*
> **Олег:** Я їм кашу і п'ю каву. *(I eat porridge and drink coffee.)*
> **Марія:** А Олена? *(And Olena?)*
> **Олег:** Вона їсть хліб з маслом і п'є чай. *(She eats bread with butter and drinks tea.)*
> **Марія:** А діти? *(And the kids?)*
> **Олег:** Вони їдять яйця і п'ють молоко. *(They eat eggs and drink milk.)*

Notice how the verb **їсти** (to eat) changes with every person: **я їм**, **вона їсть**, **вони їдять**. The verb **пити** (to drink) does the same: **п'ю**, **п'є**, **п'ють**. These two verbs will look different for every subject — but by the end of this module, you will know all six forms of each.

Now the same verbs appear at lunch, with plural subjects.

> **Колега 1:** Що ви їсте на обід? *(What are you eating for lunch?)*
> **Колега 2:** Ми їмо суп і салат. *(We're eating soup and salad.)*
> **Колега 1:** А що п'єте? *(And what are you drinking?)*
> **Колега 2:** Ми п'ємо воду або сік. *(We're drinking water or juice.)*
> **Колега 1:** Я теж хочу суп. *(I want soup too.)*
> **Колега 2:** Добре, замовляй! *(Okay, go ahead and order!)*

Look back at both dialogues and answer these questions aloud: **Що їсть Олена?** (What does Olena eat?) **Що п'ють діти?** (What do the children drink?) **Що ми їмо на обід?** (What do we eat for lunch?) Each answer uses a noun right after the verb — **хліб**, **молоко**, **суп**. Some nouns change their ending, some do not. That pattern is the core of this module.

## Їсти і пити (To Eat and To Drink)

The verb **їсти** (to eat) is irregular. It does not follow Group I or Group II conjugation — it has its own pattern. Ukrainian textbooks (Заболотний, Grade 7) treat it as a special class alongside **дати** (to give). Memorize these six forms:

| Person | Singular | Plural |
|--------|----------|--------|
| 1st | я **їм** | ми **їмо** |
| 2nd | ти **їси** | ви **їсте** |
| 3rd | він/вона **їсть** | вони **їдять** |

Three sentences to anchor the pattern:

- **Я їм хліб.** — I eat bread.
- **Він їсть рибу.** — He eats fish.
- **Вони їдять кашу.** — They eat porridge.

The verb **пити** (to drink) follows regular Group I conjugation. Notice the apostrophe before **ю**, **є** — this is a standard Ukrainian spelling rule when **п** meets a soft vowel.

| Person | Singular | Plural |
|--------|----------|--------|
| 1st | я **п'ю** | ми **п'ємо** |
| 2nd | ти **п'єш** | ви **п'єте** |
| 3rd | він/вона **п'є** | вони **п'ють** |

Three sentences:

- **Я п'ю каву.** — I drink coffee.
- **Вона п'є воду.** — She drinks water.
- **Вони п'ють сік.** — They drink juice.

Compare the two verbs side by side:

| | **їсти** | **пити** |
|---|---|---|
| я | їм | п'ю |
| ти | їси | п'єш |
| він/вона | їсть | п'є |
| ми | їмо | п'ємо |
| ви | їсте | п'єте |
| вони | їдять | п'ють |

The key difference: **їсти** is the exception you must learn by heart — every form looks different from the infinitive. **Пити** is a regular model — once you see the **п'** pattern, the endings are predictable. Both verbs are extremely high-frequency. You will use them every single day.

Ukrainian schools (Grade 4, Заболотний) teach the accusative case through the question **що?** (what?). When you eat or drink something, ask yourself: **що?** The answer is always in the accusative case.

- **Я їм (що?) хліб.** — I eat (what?) bread.
- **Я п'ю (що?) каву.** — I drink (what?) coffee.

This is the **бачу що? / їм що? / п'ю що?** rule from Ukrainian textbooks. Build a habit: every time you use **їсти** or **пити**, ask **що?** — and the noun that follows takes the accusative form.

<!-- INJECT_ACTIVITY: fill-in-conjugation -->

## Знахідний відмінок — неживе (Accusative Inanimate)

Masculine inanimate nouns do not change in the accusative — they look exactly like the nominative. The same is true for neuter nouns. Here are the examples:

- **хліб → хліб** — Я їм хліб. *(I eat bread.)*
- **суп → суп** — Я їм суп. *(I eat soup.)*
- **сік → сік** — Я п'ю сік. *(I drink juice.)*
- **банан → банан** — Я їм банан. *(I eat a banana.)*
- **молоко → молоко** — Я п'ю молоко. *(I drink milk.)*
- **яйце → яйце** — Я їм яйце. *(I eat an egg.)*

Rule: masculine and neuter inanimate nouns stay the same after **їсти** and **пити**. No ending changes at all.

Feminine nouns are different — and this is the key change to learn. Feminine nouns ending in **-а** change to **-у**. Feminine nouns ending in **-я** change to **-ю**. Eight examples:

- **кава → каву** — Я п'ю каву. *(I drink coffee.)*
- **вода → воду** — Я п'ю воду. *(I drink water.)*
- **риба → рибу** — Я їм рибу. *(I eat fish.)*
- **каша → кашу** — Я їм кашу. *(I eat porridge.)*
- **картопля → картоплю** — Я їм картоплю. *(I eat potatoes.)*
- **сметана → сметану** — Я їм сметану. *(I eat sour cream.)*

The pattern is simple: **-а** becomes **-у**; **-я** becomes **-ю**. This is the only accusative ending change you need at A1. Everything else stays the same.

Compare these pairs side by side — nouns that change on the left, nouns that stay the same on the right:

| Changes (-у / -ю) | Stays the same |
|---|---|
| кава → **каву** | хліб → **хліб** |
| вода → **воду** | сік → **сік** |
| картопля → **картоплю** | молоко → **молоко** |

Now read these mixed sentences and notice which nouns changed and which did not:

- **Я їм рибу і хліб.** — I eat fish and bread.
- **Вона п'є каву і воду.** — She drinks coffee and water.
- **Ми їмо кашу і яйця.** — We eat porridge and eggs.
- **Вони п'ють сік і молоко.** — They drink juice and milk.

:::tip
If a noun ends in **-а** or **-я** (like **кава**, **вода**, **картопля**), swap the ending for **-у** or **-ю** when you eat or drink it. Everything else stays the same. One rule — that is all you need.
:::

<!-- INJECT_ACTIVITY: fill-in-accusative -->

<!-- INJECT_ACTIVITY: quiz-accusative -->

<!-- INJECT_ACTIVITY: group-sort-accusative -->

## Підсумок — Summary

Two verbs to remember — **їсти** (irregular: **їм, їси, їсть, їмо, їсте, їдять**) and **пити** (regular: **п'ю, п'єш, п'є, п'ємо, п'єте, п'ють**).

One accusative rule for inanimate nouns:

- **Masculine and neuter** — no change. **Хліб**, **суп**, **молоко**, **сік** stay the same.
- **Feminine -а → -у, -я → -ю.** **Кава → каву**, **вода → воду**, **картопля → картоплю**.

Test yourself — fill in the correct form:

- Я їм ___ (риба → ?) → **рибу**
- Я п'ю ___ (вода → ?) → **воду**
- Вони їдять ___ (хліб → ?) → **хліб**
- Вона п'є ___ (кава → ?) → **каву**

Now try this on your own: say three things you eat today and three things you drink. Use the correct accusative form for each noun. For example: **Я їм кашу, рибу і хліб. Я п'ю каву, воду і сік.** Check each feminine noun — did you change **-а** to **-у**? Did masculine and neuter nouns stay the same? If yes, you have the pattern.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: i-eat-i-drink
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

**Level: A1.4+ (Module 37/55) — BEGINNER**

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

### Pattern: grammar-cases
- **fill-in** — Який відмінок?: Fill in the correct case ending for a noun in context
  - Instruction: *Вставте іменник у правильній формі*
- **quiz** — Визнач відмінок: Identify which case a highlighted noun is in
- **group-sort** — Розподіли за відмінками: Sort noun forms by their case
- **error-correction** — Знайди помилку у відмінку: Find wrong case ending and correct it

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
