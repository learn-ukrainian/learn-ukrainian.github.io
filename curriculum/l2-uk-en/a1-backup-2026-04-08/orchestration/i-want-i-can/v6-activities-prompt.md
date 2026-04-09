<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/i-want-i-can.yaml` file for module **18: I Want, I Can** (a1).

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
- `<!-- INJECT_ACTIVITY: quiz-modal-choice -->`
- `<!-- INJECT_ACTIVITY: fill-in-modal-sentences -->`
- `<!-- INJECT_ACTIVITY: quiz-regular-irregular -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Conjugate: я хоч__, ти хоч__, він хоч__'
  items: 9
  type: fill-in
- focus: Хочу, можу, or мушу? Choose the right modal for the situation.
  items: 8
  type: quiz
- focus: 'Complete: Я ___ гуляти, але не ___ — ___ працювати.'
  items: 6
  type: fill-in
- focus: Regular or irregular? Identify the conjugation pattern.
  items: 6
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- шкода (pity, unfortunately)
- допомогти (to help)
- борщ (borscht, m)
- порекомендувати (to recommend)
- треба (need to — impersonal, preview)
required:
- хотіти (to want — irregular!)
- могти (to be able/can — irregular!)
- мусити (to must/have to)
- кава (coffee, f)
- їсти (to eat)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Before any grammar tables, hear all three modal verbs in action. Watch for **хочу** (I want), **можу** (I can), and **мушу** (I must) in every exchange below.

### Dialogue 1 — Planning the weekend

> **Оля:** Денисе, що ти хочеш робити у вихідні? *(Denys, what do you want to do on the weekend?)*
> **Денис:** Я хочу гуляти в парку. А ти? *(I want to walk in the park. And you?)*
> **Оля:** Я теж хочу гуляти, але не можу — мушу працювати. *(I also want to walk, but I can't — I have to work.)*
> **Денис:** Шкода! А в неділю ти можеш? *(Pity! And on Sunday, can you?)*
> **Оля:** Так, у неділю я можу! *(Yes, on Sunday I can!)*
> **Денис:** Що ти хочеш робити? *(What do you want to do?)*
> **Оля:** Хочу піти в кіно. Ти хочеш? *(I want to go to the cinema. Do you want to?)*
> **Денис:** Звісно хочу! Домовилися! *(Of course I want to! Deal!)*

:::tip
Three modals, three meanings: **хочу** = want · **можу** = can · **мушу** = must
:::

Every modal verb here follows the same pattern: **modal + infinitive**. Оля says **хочу гуляти** (want to walk), **не можу** (can't), **мушу працювати** (must work). Денис asks **ти можеш?** (can you?), **ти хочеш?** (do you want to?). Go back to Dialogue 1 and find all three modals before reading further — they appear in nearly every line.

### Dialogue 2 — At a café

> **Офіціант:** Доброго дня! Що ви хочете? *(Good day! What would you like?)*
> **Денис:** Я хочу каву, будь ласка. *(I want coffee, please.)*
> **Офіціант:** Велику чи маленьку? *(Large or small?)*
> **Денис:** Велику. І ще я хочу їсти. *(Large. And I also want to eat.)*
> **Денис:** Що ви можете порадити? *(What can you recommend?)*
> **Офіціант:** Можу порадити борщ! *(I can recommend borscht!)*
> **Денис:** Чудово! Я хочу борщ. *(Wonderful! I want borscht.)*

Something different happened here. **Я хочу каву** — Denys wants a *thing*, not an *action*. When you want a thing, **хотіти** takes a noun directly (accusative case): **хочу каву** (coffee), **хочу борщ** (borscht). No infinitive needed. But when he says **я хочу їсти** — that's wanting an action, so the infinitive returns.

You used **хочу**, **можу**, and **мушу** intuitively through both dialogues. Now let's see exactly how each one works — starting with the most irregular: **хотіти**.

## Хотіти (To Want)

**Хотіти** (to want) is a Group I verb — but its infinitive ends in **-іти**, which normally signals Group II (like **робити**, **мусити**). Ukrainian grammarians list **хотіти** as an explicit exception. The key giveaway: its third person plural form ends in **-уть** (**хочуть**), not **-ять**. That **-уть** ending is the signature of Group I.

Every present-tense form of **хотіти** uses a changed stem. The infinitive stem is **хот-**, but in all conjugated forms it becomes **хоч-** — a **т→ч** consonant alternation. This change is absolute: there is no present-tense form that keeps the original **т**.

| | Singular | Plural |
|---|---|---|
| **я** | хочу | **ми** хочемо |
| **ти** | хочеш | **ви** хочете |
| **він/вона** | хоче | **вони** хочуть |

Compare the two stems side by side: **хот-іти** (infinitive, dictionary form) versus **хоч-у** (present, conjugated). The mutation **хот- → хоч-** is fixed across all six forms. Once you know **хоч-**, just add the regular Group I endings: **-у, -еш, -е, -емо, -ете, -уть**.

**Хотіти** has two syntactic patterns. The first: **хотіти + infinitive** — when you want to *do* something.

- **Я хочу читати.** — I want to read.
- **Ти хочеш гуляти?** — Do you want to walk?
- **Вона хоче вчитися.** — She wants to study.

The second: **хотіти + noun** (accusative) — when you want a *thing*.

- **Я хочу каву.** — I want coffee.
- **Він хоче борщ.** — He wants borscht.
- **Ми хочемо піцу.** — We want pizza.

Rule of thumb: wanting to DO something → infinitive. Wanting a THING → noun.

<!-- INJECT_ACTIVITY: fill-in-conjugation -->

Negation is straightforward. Place **не** directly before the verb: **Я не хочу.** **Ти не хочеш спати?** (Don't you want to sleep?) **Він не хоче їсти.** (He doesn't want to eat.) A polite alternative — **хотів би** / **хотіла б** (I would like) — uses the conditional mood, which comes in B1. For now, **Я хочу...** is your direct, natural option.

A Ukrainian Grade 3 poem (Vashulenko textbook) shows how **хотіти** expresses deep, persistent desire — not just mild preference: *«Я страшенно хочу мати годівницю на вікні»* (I desperately want to have a bird feeder on my window). The child wanted so intensely that he *«хотів, хотів, хотів»* — wanted and wanted and wanted. Eventually he realized wanting alone wasn't enough: *«Краще я змайструю сам»* (Better I'll build it myself). **Хотіти** carries real emotional weight — genuine desire, not just "I'd prefer."

## Могти і мусити (Can and Must)

**Могти** (to be able to, can) is the second irregular verb in this module. Like **хотіти**, it belongs to Group I — its third person plural ends in **-уть** (**можуть**). The stem mutation here: **мог- → мож-**, a **г→ж** alternation. This г→ж pattern is common in Ukrainian: **допомогти → допоможу**, **берегти → бережу**. Whenever you see **г** in an infinitive stem, expect **ж** in conjugated forms.

| | Singular | Plural |
|---|---|---|
| **я** | можу | **ми** можемо |
| **ти** | можеш | **ви** можете |
| **він/вона** | може | **вони** можуть |

**Могти** expresses ability or possibility — "I am able to" or "I can."

- **Я можу говорити українською.** — I can speak Ukrainian.
- **Ти можеш допомогти?** — Can you help?
- **Він може читати.** — He can read.
- **Ми можемо зустрітися.** — We can meet.

Note: **могти** is about *ability*. For *permission* ("May I?"), Ukrainian uses **можна** — an impersonal word coming in a later module.

Now the contrast: **мусити** (to must, to have to). Unlike the other two, **мусити** is a regular Group II verb — with one small twist. The **я**-form has a **с→ш** alternation: **мушу**. All other forms keep the regular **с**:

| | Singular | Plural |
|---|---|---|
| **я** | мушу | **ми** мусимо |
| **ти** | мусиш | **ви** мусите |
| **він/вона** | мусить | **вони** мусять |

**Мусити** means obligation — strong, unavoidable obligation. Антоненко-Давидович, the great Ukrainian stylist, warns that **мусити** should be reserved for genuine compulsion — situations where you truly have no choice. For ordinary, everyday obligation, Ukrainian speakers often prefer **маю** (from **мати** — to have): **Я маю працювати** (I need to work — ordinary duty) versus **Я мушу працювати** (I'm forced to work — no escape). At A1, focus on **мушу** for strong obligation. You'll meet **маю** and **треба** (one needs to) in later modules.

Now picture the three modals as a triangle — desire, ability, obligation — joined in one sentence: **«Я хочу гуляти, але не можу — мушу працювати.»** (I want to walk, but I can't — I must work.) **Хочу** = internal desire. **Можу** = ability or possibility. **Мушу** = external compulsion, no choice.

Quick mental test: *"I have free time and money for the cinema"* → **можу** піти в кіно. *"Tomorrow is an exam — I have to study"* → **мушу** вчити. *"I really love this book"* → **хочу** читати.

<!-- INJECT_ACTIVITY: quiz-modal-choice -->

<!-- INJECT_ACTIVITY: fill-in-modal-sentences -->

## Підсумок — Summary

Three modal verbs, three meanings — here they are side by side:

| Дієслово | Meaning | Group | Я-form | Stem change |
|---|---|---|---|---|
| хотіти | desire (want) | I (irregular) | хочу | хот → хоч (т→ч) |
| могти | ability (can) | I (irregular) | можу | мог → мож (г→ж) |
| мусити | obligation (must) | II (regular*) | мушу | *с→ш in я-form only |

All three follow the same construction: **modal verb + infinitive** (the unchanged dictionary form ending in **-ти**). **Я хочу читати.** **Ти можеш допомогти.** **Він мусить іти.** The infinitive never changes — the modal verb alone carries person and number. One exception: **хотіти** also works with a noun directly — **Я хочу каву** — when you want a thing rather than an action.

Five patterns to memorize as ready-made chunks. These cover most everyday modal situations at A1:

- **Я хочу мати...** — I want to have...
- **Я не можу.** — I can't.
- **Що ти хочеш робити?** — What do you want to do?
- **Мушу йти.** — I have to go.
- **Ти можеш допомогти?** — Can you help?

### Self-Check

Test yourself — answer each prompt out loud before checking:

- Скажи, що ти хочеш робити сьогодні. → **Я хочу ___.**
- Скажи, що ти можеш робити українською. → **Я можу ___.**
- Скажи, що ти мусиш робити завтра. → **Я мушу ___.**
- Як відмінюється **хотіти**? Яка особливість? → хот → хоч (т→ч), Group I
- Яка різниця між **можу** і **мушу**? → ability vs obligation
- Яке закінчення в 3-й особі множини у **могти**? → **можуть** (Group I: -уть)

<!-- INJECT_ACTIVITY: quiz-regular-irregular -->

In the next modules, you'll meet **можна** (one may / it's allowed) — an impersonal construction for permission. Later, at A2, **мав би** / **мала б** (should) will build on the modal foundation you've just learned. For now, **хочу**, **можу**, **мушу** — these three verbs unlock a huge range of everyday Ukrainian expression: from ordering **каву** at a café to explaining why you can't come to a party.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: i-want-i-can
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

**Level: A1.2-A1.3 (Module 18/55) — EARLY BEGINNER**

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
