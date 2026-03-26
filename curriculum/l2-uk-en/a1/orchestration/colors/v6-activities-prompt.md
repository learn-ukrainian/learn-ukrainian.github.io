# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/colors.yaml` file for module **10: Colors** (a1).

Output **pure YAML only** — no markdown fencing, no preamble, no explanation. Just the YAML document.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 2-3 quick checks after key teaching points. Workbook = 4-8 deeper practice exercises covering the full topic.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: fill-in-gender-agreement -->`
- `<!-- INJECT_ACTIVITY: group-sort-hard-soft -->`
- `<!-- INJECT_ACTIVITY: quiz-blue-shades -->`
- `<!-- INJECT_ACTIVITY: quiz-object-colors -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Якого кольору? Match objects to their typical color.
  items: 8
  type: quiz
- focus: 'Gender agreement with colors: син__ книга, червон__ стіл, біл__ вікно'
  items: 10
  type: fill-in
- focus: синій or блакитний? Choose the right shade of blue.
  items: 6
  type: quiz
- focus: Sort colors into тверда група (-ий) and м'яка група (-ій)
  items: 10
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- коричневий (brown)
- рожевий (pink)
- помаранчевий (orange)
- фіолетовий (purple)
- темний (dark — as prefix: темно-)
- світлий (light — as prefix: світло-)
- прапор (flag, m)
required:
- червоний (red)
- жовтий (yellow)
- зелений (green)
- синій (dark blue — soft-stem!)
- блакитний (light blue, sky blue)
- білий (white)
- чорний (black)
- сірий (grey)
- колір (color, m)
- якого кольору? (what color?)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Two friends, Оленка and Тарас, are at an outdoor market looking for a birthday gift. Listen for the color words — every single one changes its ending to match the thing it describes.

> **Оленка:** Яка гарна сумка! Якого вона кольору? *(What a nice bag! What color is it?)*
> **Тарас:** Червона. А дивись, є ще синя і зелена. *(Red. And look, there's also a blue and a green one.)*
> **Оленка:** Мені подобається синя. *(I like the blue one.)*
> **Тарас:** А мені — жовта! Я люблю жовтий колір. *(And I like the yellow one! I love the color yellow.)*
> **Оленка:** А ця біла? Теж гарна. *(And this white one? Also nice.)*
> **Тарас:** Так, але червона найкраща. Бери червону! *(Yes, but the red one is the best. Take the red one!)*

Notice something? Every color ended in **-а**: **червона**, **синя**, **зелена**, **жовта**, **біла**. That's because **сумка** (bag) is feminine. You already saw this pattern in M09 with adjectives like **гарна** and **велика**. Colors work exactly the same way — they change their ending to match the noun. Why not **червоний**? Because **червоний** is the masculine form, and **сумка** is feminine.

Now a different scene. Оленка and Тарас are on a video call, and Тарас is showing his room — a chance to practice colors with furniture from M08.

> **Оленка:** Якого кольору твоя кімната? *(What color is your room?)*
> **Тарас:** Біла. Стіни білі. *(White. The walls are white.)*
> **Оленка:** А килим? *(And the carpet?)*
> **Тарас:** Килим коричневий. А крісло — сіре. *(The carpet is brown. And the armchair is grey.)*
> **Оленка:** У мене крісло чорне. І стіл теж чорний. *(My armchair is black. And the desk is also black.)*
> **Тарас:** А шафа? *(And the wardrobe?)*
> **Оленка:** Шафа коричнева. Але двері білі. *(The wardrobe is brown. But the doors are white.)*

Look at how the color endings shifted across this dialogue: **коричневий** килим (masculine) but **коричнева** шафа (feminine), **сіре** крісло (neuter) but **сірий** стіл (masculine), **білі** стіни and **білі** двері (plural). The color always follows the noun — just like M09 adjectives.

## Кольори (Colors)

Six of the basic colors follow the pattern you already know from M09 — the **тверда група** (hard group), with endings **-ий** (masculine), **-а** (feminine), **-е** (neuter):

| Color | Masculine (-ий) | Feminine (-а) | Neuter (-е) | Meaning |
|-------|-----------------|---------------|-------------|---------|
| red | червоний | червона | червоне | red |
| yellow | жовтий | жовта | жовте | yellow |
| green | зелений | зелена | зелене | green |
| black | чорний | чорна | чорне | black |
| white | білий | біла | біле | white |
| grey | сірий | сіра | сіре | grey |

These follow the exact same pattern as **великий/велика/велике** from M09. If you learned adjective agreement there, you already know how all six of these colors work.

Now practice with real objects. The question **якого кольору?** (what color?) is the key phrase — learn it as a fixed chunk:

- Якого кольору автобус? — **Червоний**. *(What color is the bus? — Red.)*
- Якого кольору квітка? — **Жовта**. *(What color is the flower? — Yellow.)*
- Якого кольору яблуко? — **Зелене**. *(What color is the apple? — Green.)*
- Якого кольору кіт? — **Чорний**. *(What color is the cat? — Black.)*
- Якого кольору стіна? — **Біла**. *(What color is the wall? — White.)*
- Якого кольору день? — **Сірий**. *(What color is the day? — Grey.)*

The answer always matches the gender of the noun you're describing. **Автобус** is masculine → **червоний**. **Квітка** is feminine → **жовта**. **Яблуко** is neuter → **зелене**.

<!-- INJECT_ACTIVITY: fill-in-gender-agreement -->

Now for the one color that breaks the pattern. **Синій** (dark blue) belongs to the **м'яка група** (soft group), with endings **-ій** (masculine), **-я** (feminine), **-є** (neuter). This comes from Вашуленко Grade 3 p.130, where adjectives are divided into **тверда група** (-ий) and **м'яка група** (-ій). Among the basic colors, only **синій** follows the soft pattern — learn it as a special case.

Compare side by side:

| | Hard-stem (великий) | Soft-stem (синій) |
|---|---|---|
| Masculine | великий стіл | синій стіл |
| Feminine | велика книга | синя книга |
| Neuter | велике вікно | синє вікно |

The difference is subtle but consistent: **-ий** becomes **-ій**, **-а** becomes **-я**, **-е** becomes **-є**. The soft sign in the ending changes the vowel sound.

Practice **синій** with objects. Notice how each ending differs from the hard-stem colors:

- **синій олівець** *(blue pencil — masculine)*
- **синя ручка** *(blue pen — feminine)*
- **синє небо** *(blue sky — neuter)*
- **синій стіл** *(blue desk — masculine)*
- **синя шафа** *(blue wardrobe — feminine)*
- **синє море** *(blue sea — neuter)*

Now compare: **червоний олівець** but **синій олівець**, **червона ручка** but **синя ручка**, **червоне небо** but **синє небо**. The endings look similar but the vowel shifts — that softness is the signature of **м'яка група**.

<!-- INJECT_ACTIVITY: group-sort-hard-soft -->

## Синій ≠ блакитний (Blue ≠ Blue)

English has one word for blue. Ukrainian has two — and they are as different to a Ukrainian speaker as "red" and "pink" are to you.

**Синій** means dark blue, deep blue. Think of the sea at night, a bottle of ink, a pair of denim jeans. **Блакитний** (light blue, sky blue) means the pale blue of a clear daytime sky, baby clothes, or **незабудки** (forget-me-nots). This is not just a shade preference — Ukrainian children learn **синій** and **блакитний** as two fundamentally separate colors, the same way English-speaking children learn "red" and "pink" as distinct.

A quick test:

- Яке небо? — **Блакитне**. *(daytime sky — light blue)*
- Яке море? — **Синє**. *(the deep sea — dark blue)*

The Ukrainian flag is a powerful cultural anchor for this distinction. The poet Наталка Поклад wrote in a famous verse from Кравцова Grade 2: **Синьо-жовтий прапор маєм: синє — небо, жовте — жито** *(We have a blue-and-yellow flag: blue is the sky, yellow is the wheat)*. The flag is **синьо-жовтий** (blue-and-yellow), not *блакитно-жовтий* — because it represents the deep, full sky, not a pale shade.

:::caution
The word **голубий** for "light blue" is a Russian-influenced form. In Ukrainian, use **блакитний** for light blue and **синій** for dark blue.
:::

<!-- INJECT_ACTIVITY: quiz-blue-shades -->

Four more colors expand your palette: **коричневий** (brown), **рожевий** (pink), **помаранчевий** (orange), and **фіолетовий** (purple). All four are hard-stem (**-ий/-а/-е**), just like **червоний**. Examples with objects:

- **коричневий шоколад** *(brown chocolate)*
- **рожева квітка** *(pink flower)*
- **помаранчевий апельсин** *(orange orange — the fruit)*
- **фіолетова сукня** *(purple dress)*

The word **помаранчевий** comes from **помаранч** (orange fruit) — the color is named after the fruit, just like in English.

You can also create compound colors using **темно-** (dark) and **світло-** (light) as hyphenated prefixes: **темно-зелений** (dark green), **світло-синій** (light blue-ish), **темно-червоний** (dark red, maroon). A cultural note: traditional **вишиванка** (embroidered shirt) patterns use specific color combinations that carry regional identity — **червоний** і **чорний** in Полісся, **червоний** і **синій** on Полтавщина.

<!-- INJECT_ACTIVITY: quiz-object-colors -->

## Підсумок — Summary

Two adjective groups cover all the colors you learned. The **тверда група** (hard group) uses endings **-ий/-а/-е** — the same pattern as M09. Every basic color except one follows this group: **червоний/червона/червоне**, **жовтий/жовта/жовте**, **зелений/зелена/зелене**, **чорний/чорна/чорне**, **білий/біла/біле**, **сірий/сіра/сіре**. The lone exception is the **м'яка група** (soft group): **синій/синя/синє**, with its signature **-ій/-я/-є** endings. The key question is **Якого кольору?** — and the answer always matches the noun's gender:

- Якого кольору стіл? — **Білий**. *(masculine)*
- Якого кольору книга? — **Біла**. *(feminine)*
- Якого кольору вікно? — **Біле**. *(neuter)*

Remember the two blues: **синій** is deep, dark blue — the sea, ink, jeans. **Блакитний** is light, sky blue — a clear daytime sky, forget-me-nots. The Ukrainian flag is **синьо-жовтий**. This distinction does not exist in English, but it is completely natural for Ukrainian speakers — a child in Ukraine learns these as two separate **кольори** (colors), not shades of one.

Here is your full color inventory — twelve colors plus compound forms:

- **червоний**, **жовтий**, **зелений**, **синій**, **блакитний**, **білий**, **чорний**, **сірий**, **коричневий**, **рожевий**, **помаранчевий**, **фіолетовий**
- Compound forms: **темно-** / **світло-** + any color (e.g., **темно-зелений**, **світло-синій**)

Preview: in M11 (How Many?) you will count colored objects — and the adjective endings will change again for plural forms.

Test yourself with these questions. Якого кольору **прапор** України? (**Синьо-жовтий**.) Describe three things in your room using colors — and remember gender agreement. Яка різниця між **синій** і **блакитний**? Name something **синє** and something **блакитне**. What adjective group does **синій** belong to? (**М'яка група**.) What about **червоний**? (**Тверда група**.)

Start noticing colors around you and naming them in Ukrainian. When you see the sky — is it **синє** чи **блакитне**? When you get dressed — якого кольору твоя **сорочка** (shirt)? Colors are everywhere, and now you have the words to describe your whole world in Ukrainian.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: colors
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

**Level: A1.2-A1.3 (Module 10/55) — EARLY BEGINNER**

The learner knows the alphabet and ~200 words. They:
- Can read Ukrainian slowly
- Know basic nouns, adjectives, simple verb forms
- Cannot handle complex sentences or grammar terminology in Ukrainian

**Instructions in simple English with Ukrainian key terms in bold.**
Example: 'Choose the correct form of **мій/моя/моє**'

**Good activity types:** quiz, fill-in (simple sentences), match-up, group-sort, true-false, observe, anagram, translate (English→Ukrainian).


## Quality Rules

1. **Instructions match learner level:**
   - **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
   - **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
   - **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
   - **A2+:** Instructions in Ukrainian.
   - **B1+:** Full Ukrainian, no English.
2. **3-5 options per quiz/fill-in** — enough to prevent guessing, not so many to overwhelm
3. **No duplicate options** — each option in a quiz item must be unique
4. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
5. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
6. **Min 3 pairs for match-up** — to prevent trivial elimination
7. **Explanations for true-false and error-correction** — help the learner understand WHY
8. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

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

**Efficiency Rules:**
- **Batch your checks:** Use `mcp__rag__verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 8-15 tool calls per module**, not 50.

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
