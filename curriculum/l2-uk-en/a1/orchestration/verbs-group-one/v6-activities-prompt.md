<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/verbs-group-one.yaml` file for module **16: Verbs Group I** (a1).

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
- `<!-- INJECT_ACTIVITY: quiz-verb-forms -->`
- `<!-- INJECT_ACTIVITY: match-person-to-form -->`
- `<!-- INJECT_ACTIVITY: fill-in-context -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Conjugate: я чита__, ти чита__, він чита__'
  items: 10
  type: fill-in
- focus: 'Choose correct form: Вона (читаю/читаєш/читає) книгу.'
  items: 8
  type: quiz
- focus: 'Match person to verb form: я ↔ читаю, ти ↔ читаєш'
  items: 6
  type: match-up
- focus: 'Complete the sentence: Що ти ___? — Я ___ музику. (слухати)'
  items: 6
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- робити (to do — Group II, preview as chunk)
- вивчати (to study/learn)
- малювати (to draw)
- грати (to play)
- вечеря (dinner, f)
- музика (music — review from M15)
required:
- читати (to read)
- знати (to know)
- працювати (to work)
- слухати (to listen)
- гуляти (to walk)
- готувати (to cook)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Юля is in the kitchen. Something smells amazing. Сашко walks in and can't resist asking questions.

> **Сашко:** Що ти робиш, Юле? *(What are you doing, Yulia?)*
> **Юля:** Я готую вечерю. А ти що робиш? *(I'm cooking dinner. And what are you doing?)*
> **Сашко:** Я читаю. *(I'm reading.)*
> **Юля:** Що читаєш? *(What are you reading?)*
> **Сашко:** Я читаю книгу. А де Олена? *(I'm reading a book. And where's Olena?)*
> **Юля:** Вона слухає музику. *(She's listening to music.)*
> **Сашко:** Вона завжди слухає музику! *(She always listens to music!)*
> **Юля:** Так, але вона знає багато пісень! *(Yes, but she knows many songs!)*

:::tip
Помітив/-ла? Three different persons appeared in that exchange: **я готую** (I cook), **ти читаєш** (you read), **вона слухає** (she listens). Those endings — **-ю**, **-єш**, **-є** — are Group I conjugation. That's the pattern you're learning today.
:::

Here's a second situation — two people meet after work.

> **Андрій:** Де ти працюєш? *(Where do you work?)*
> **Марина:** Я працюю в офісі. А ти? *(I work in an office. And you?)*
> **Андрій:** Я не працюю — я навчаюся. Я студент. *(I don't work — I study. I'm a student.)*
> **Марина:** Ти вивчаєш українську? *(Are you studying Ukrainian?)*
> **Андрій:** Так, я вивчаю! *(Yes, I'm studying it!)*
> **Марина:** Добре! Я теж вивчаю. *(Great! I'm studying too.)*
> **Андрій:** Ти гуляєш увечері? *(Do you walk in the evening?)*
> **Марина:** Так, я гуляю в парку. *(Yes, I walk in the park.)*

Count the verbs that appeared across both dialogues: **готувати** (to cook), **читати** (to read), **слухати** (to listen), **знати** (to know), **працювати** (to work), **вивчати** (to study), **гуляти** (to walk). Seven verbs — and they all follow the same ending pattern. The verb **робити** (to do) also appeared in **Що ти робиш?** — but that one belongs to a different group. You'll learn it properly in M17. For now, just remember the question as a fixed phrase: **Що ти робиш?** means "What are you doing?"

## Перша дієвідміна (Group I Verbs)

All seven verbs from the dialogues belong to Group I — the largest verb group in Ukrainian. How do you recognize a Group I verb? Look at its infinitive, the dictionary form. Group I infinitives end in **-ати** (**читати**, **слухати**, **гуляти**, **знати**), **-увати** (**готувати**, **працювати**), or **-яти** (**вивчати**, **малювати** — to draw). To conjugate any of these verbs in the present tense, you remove **-ти** from the infinitive and add person endings.

Here is the anchor example. Take **читати** (to read) — remove **-ти**, get the stem **чита-**, and add endings:

| Особа (Person) | Однина (Singular) | Множина (Plural) |
|---|---|---|
| 1-ша (я / ми) | я **читаю** | ми **читаємо** |
| 2-га (ти / ви) | ти **читаєш** | ви **читаєте** |
| 3-тя (він, вона / вони) | він/вона **читає** | вони **читають** |

This table comes from Варзацька, Grade 4 (p. 129) — the standard Ukrainian school approach. Notice the vowel **є** running through every form from **ти** to **вони**: -**є**ш, -**є**, -**є**мо, -**є**те, -**ю**ть. That consistent **є** is the signature of Group I.

Now apply the same pattern to all six essential verbs. Here are the three singular forms — the ones you'll use most:

| Infinitive | я | ти | він/вона |
|---|---|---|---|
| **читати** (to read) | читаю | читаєш | читає |
| **знати** (to know) | знаю | знаєш | знає |
| **працювати** (to work) | працюю | працюєш | працює |
| **слухати** (to listen) | слухаю | слухаєш | слухає |
| **гуляти** (to walk) | гуляю | гуляєш | гуляє |
| **готувати** (to cook) | готую | готуєш | готує |

One detail about **-увати** verbs: when you conjugate **готувати** or **працювати**, the stem shortens. **Готувати** → **готу-** (not *готува-*), **працювати** → **працю-** (not *працюва-*). The endings stay the same — only the stem changes.

<!-- INJECT_ACTIVITY: fill-in-conjugation -->

A quick note about **робити** (to do). It appeared in the dialogue question **Що ти робиш?** (What are you doing?). But **робити** belongs to Group II — its endings are different: **робиш**, **робить** (with **-и-**, not **-є-**). For now, treat **Що ти робиш?** as a memorized chunk. You'll learn Group II conjugation in M17. Mixing up the two groups is the most common mistake at this stage, so keeping them separate is important.

## Я, ти, він/вона (Persons)

At A1, three forms cover roughly 90% of your real conversations: **я** (I — the speaker), **ти** (you — the person you're talking to), and **він/вона** (he/she — someone you're talking about). You already know these pronouns from M10. Drill those three verb forms first. The plural forms — **ми** (we), **ви** (you, plural or formal), **вони** (they) — appear below for recognition, but there's no pressure to memorize all six right now.

Here are the three persons in action, building full sentences with nouns from M08 and adjectives from M09:

- **Я читаю нову книгу.** — I'm reading a new book.
- **Ти знаєш цю пісню?** — Do you know this song?
- **Він слухає українську музику.** — He listens to Ukrainian music.
- **Вона готує смачну вечерю.** — She's cooking a tasty dinner.
- **Я гуляю в парку.** — I walk in the park.
- **Ти працюєш тут?** — Do you work here?

Each sentence follows the same structure: **person + verb form + object**. The verb ending tells you who is doing the action — **-ю** for я, **-єш** for ти, **-є** for він/вона.

<!-- INJECT_ACTIVITY: quiz-verb-forms -->

You may have noticed something: **книга** became **книгу**, **пісня** became **пісню**, **музика** became **музику**. The noun changes form when it receives the action of the verb. That's the accusative case — it's coming in M20. For now, learn these as fixed phrases: **читаю книгу**, **слухаю музику**, **готую вечерю**. No rule required yet; just recognize the pattern.

<!-- INJECT_ACTIVITY: match-person-to-form -->

Now the plural forms, presented as natural sentences — not for memorization, just for recognition:

- **Ми готуємо вечерю.** — We're cooking dinner.
- **Ви знаєте українську?** — Do you (plural) know Ukrainian?
- **Вони гуляють у парку.** — They walk in the park.

The plural endings are **-ємо** (ми), **-єте** (ви), **-ють** (вони). Notice that **ви** is also used as polite singular — when addressing one person formally, like a teacher or a stranger. That's a preview for now; no need to drill it yet. What matters most is the singular trio: **-ю / -єш / -є**. If you can produce those three forms for any Group I verb, you can hold a basic conversation.

<!-- INJECT_ACTIVITY: fill-in-context -->

## Підсумок — Summary

Group I verbs have infinitives ending in **-ати**, **-увати**, or **-яти**. To conjugate them in the present tense, remove **-ти** and add these endings:

| я | ти | він/вона | ми | ви | вони |
|---|---|---|---|---|---|
| **-ю** | **-єш** | **-є** | **-ємо** | **-єте** | **-ють** |

The six core verbs you learned: **читати**, **знати**, **працювати**, **слухати**, **гуляти**, **готувати**. A helpful anchor to remember: **ти завжди -єш** — no matter which Group I verb, the **ти** form always ends in **-єш**: ти читаєш, ти слухаєш, ти гуляєш, ти працюєш. That form is the most useful one to drill first.

### Self-check

Test yourself before moving on:

- Conjugate **слухати** for я, ти, він/вона → **слухаю** / **слухаєш** / **слухає** ✓
- What's the **ти** form of **працювати**? → **працюєш** ✓
- Say "She reads a new book" in Ukrainian → **Вона читає нову книгу.** ✓
- Ask "What are you doing?" → **Що ти робиш?** ✓
- Say two things you do every day: **Я читаю...** **Я слухаю...** (open production — use any Group I verb)

**Coming next:** M17 — Group II verbs (**говорити**, **робити**) — a different ending pattern with **-и-** instead of **-є-**.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: verbs-group-one
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

**Level: A1.2-A1.3 (Module 16/55) — EARLY BEGINNER**

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
