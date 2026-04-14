<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/colors.yaml` file for module **10: Colors** (a1).

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

Colors are everywhere around you — in flower markets, in wardrobes, on the Ukrainian flag. Listen to how Ukrainians talk about them in two everyday situations.

### Dialogue 1 — At the flower market

Наталка is choosing flowers for a friend's birthday. The **продавець** (seller) helps her pick the perfect bouquet.

> **Наталка:** Добрий день! Я шукаю квіти для подруги. *(Good day! I'm looking for flowers for a friend.)*
> **Продавець:** Добрий день! Ось червоні троянди. *(Good day! Here are red roses.)*
> **Наталка:** Гарні! А жовті соняшники є? *(Pretty! Are there yellow sunflowers?)*
> **Продавець:** Так, ось жовті соняшники. І білі лілії. *(Yes, here are yellow sunflowers. And white lilies.)*
> **Наталка:** Якого кольору ця ваза? *(What color is this vase?)*
> **Продавець:** Синя. Дуже гарна синя ваза! *(Dark blue. A very nice dark-blue vase!)*
> **Наталка:** А зелене листя є? *(And is there green foliage?)*
> **Продавець:** Так, зелене листя для букета. *(Yes, green leaves for the bouquet.)*
> **Наталка:** Мені подобається синя ваза. Беру! *(I like the dark-blue vase. I'll take it!)*

Notice the phrase **Мені подобається** (I like). Treat it as a memorized chunk — the same way you learned **У мене є** (I have). The grammar behind it belongs to A2; for now, just use it as a ready-made phrase whenever you want to say "I like something."

### Dialogue 2 — Choosing an outfit

Дмитро is helping his friend Ліза pick an outfit for a party. They are looking through her wardrobe.

> **Дмитро:** Ліза, яка ця сукня? *(Liza, what is this dress like?)*
> **Ліза:** Чорна. Це чорна сукня. *(Black. It's a black dress.)*
> **Дмитро:** А светр? Який він? *(And the sweater? What is it like?)*
> **Ліза:** Білий. Ось білий светр. *(White. Here's a white sweater.)*
> **Дмитро:** А пальто яке? *(And the coat — what is it like?)*
> **Ліза:** Сіре. Моє пальто сіре. *(Grey. My coat is grey.)*
> **Дмитро:** Мені подобається сіре пальто! А черевики? *(I like the grey coat! And the shoes?)*
> **Ліза:** Коричневі. Мої черевики коричневі. *(Brown. My shoes are brown.)*

Spot the pattern in this dialogue. The color adjective ending changes to match the noun's gender — exactly the rule from M09. **Сукня** (dress) is feminine, so the color is **чорна**. **Светр** (sweater) is masculine: **білий**. **Пальто** (coat) is neuter: **сіре**. And **черевики** (shoes) is plural: **коричневі**. Colors follow the same agreement rules as every other adjective.

## Кольори (Colors)

Remember the question words from M09 — **який?** (which/what kind?, masculine), **яка?** (feminine), **яке?** (neuter), **які?** (plural)? Colors are adjectives (**прикметники**), so they answer these same questions. In the poem "Кріт і Сонце" from Большакова Grade 2, a mole asks what color the sun is, and children answer: **червоне, жовте, золоте, оранжеве** — all neuter forms, because **сонце** (sun) is neuter. The adjective always matches its noun.

### Hard-stem colors — тверда група

Most basic colors belong to the **тверда група** (hard group), with endings **-ий / -а / -е**. Here are the six core hard-stem colors:

| Color | Masculine (-ий) | Feminine (-а) | Neuter (-е) |
|-------|-----------------|---------------|-------------|
| red | **червоний** | **червона** | **червоне** |
| yellow | **жовтий** | **жовта** | **жовте** |
| green | **зелений** | **зелена** | **зелене** |
| black | **чорний** | **чорна** | **чорне** |
| white | **білий** | **біла** | **біле** |
| grey | **сірий** | **сіра** | **сіре** |

The pattern is simple: drop **-ий** from the masculine form, then add **-а** for feminine or **-е** for neuter. Three quick examples: **червоний олівець** (red pencil, M), **червона книга** (red book, F), **червоне вікно** (red window, N). You already know this pattern from M09 — colors work exactly the same way.

### The soft-stem exception — м'яка група

One basic color breaks the pattern. **Синій** (dark blue) ends in **-ій**, not **-ий**. This makes it a **м'яка група** (soft group) adjective. Ukrainian textbooks — Вашуленко Grade 3 p.130 and Авраменко Grade 6 p.132 — both use **синій** as THE classic example of a soft-stem adjective. Compare side by side with a hard-stem word:

| | Masculine | Feminine | Neuter |
|---|---|---|---|
| hard: **великий** (big) | великий стіл | велика книга | велике вікно |
| soft: **синій** (dark blue) | синій стіл | синя книга | синє вікно |

The soft stem changes **-ій → -я → -є** instead of **-ий → -а → -е**. The difference is small — just one letter — but it matters. Listen for it: **синя книга**, not *"сина книга."*

Here is the key memory hook: among all twelve basic colors in this module, **синій** is the ONLY soft-stem one. Everything else follows the hard pattern. Think of **синій** as special in grammar the way it is special in culture — it is the blue of Ukraine's flag.

<!-- INJECT_ACTIVITY: fill-in-gender-agreement -->

<!-- INJECT_ACTIVITY: group-sort-hard-soft -->

## Синій ≠ блакитний (Blue ≠ Blue)

Ukrainian has TWO separate words for blue where English has only one. **Синій** means dark, deep blue — the color of the sea at night, dark ink, a deep winter sky. You would say **синє море** (dark-blue sea), **синій олівець** (dark-blue pencil), **синя ніч** (dark-blue night). **Блакитний** (light blue, sky blue) means something completely different — a clear afternoon sky, a pale ribbon, baby blue. You would say **блакитне небо** (light-blue sky) or **блакитна стрічка** (light-blue ribbon). In English, both are just "blue." In Ukrainian, choosing the wrong one sounds immediately off to a native speaker.

### The flag — синьо-жовтий прапор

The Ukrainian flag provides the perfect cultural anchor for this distinction. A well-known poem by Наталка Поклад, taught in Grade 2 (Кравцова p.22), says:

*Синьо-жовтий прапор маєм: синє — небо, жовте — жито.*

The flag's blue stripe is **синій** — deep and strong — not **блакитний**. The compound color adjective **синьо-жовтий** (blue-and-yellow) is written with a hyphen, because it joins two distinct colors into one word. The word **прапор** (flag) is masculine — so in full: **синьо-жовтий прапор**, a **державний символ** (state symbol).

:::caution
You may encounter the word **голубий** for light blue. In modern standard Ukrainian, prefer **блакитний**. While **голубий** does appear in some older texts, **блакитний** is the standard recommended choice.
:::

### More colors for your palette

Four more colors round out your vocabulary — all hard-stem (**-ий / -а / -е**): **коричневий / коричнева / коричневе** (brown — the color of chocolate and wood); **рожевий / рожева / рожеве** (pink — **рожева троянда**, a pink rose); **помаранчевий / помаранчева / помаранчеве** (orange — **помаранчевий апельсин**, an orange orange, echoing Большакова's poem: *"Сонце — стиглий помаранч"*); **фіолетовий / фіолетова / фіолетове** (purple — **фіолетова квітка**, a purple flower).

You can also modify any color with the prefixes **темно-** (dark) and **світло-** (light), always hyphenated: **темно-зелений ліс** (dark-green forest), **світло-синє небо** (light-blue-ish sky), **темно-коричневий стіл** (dark-brown table), **світло-рожева сукня** (light-pink dress). The prefix changes the shade; the base adjective still agrees in gender as normal.

One more cultural hook: the **вишиванка** (traditional Ukrainian embroidered shirt) uses specific color schemes that vary by region. In **Полісся**, the dominant colors are **червоний і чорний** (red and black). In **Полтавщина**, they are **червоний і синій** (red and dark blue). Even in folk art, Ukrainians distinguish shades of blue precisely.

<!-- INJECT_ACTIVITY: quiz-blue-shades -->

<!-- INJECT_ACTIVITY: quiz-object-colors -->

## Підсумок — Summary

Here is what you now know about colors in Ukrainian.

**Hard-stem colors** (**тверда група**) follow the pattern **-ий / -а / -е / -і**: **червоний стіл** (M) → **червона книга** (F) → **червоне вікно** (N) → **червоні олівці** (Pl). Drop **-ий**, add **-а** for feminine, **-е** for neuter, **-і** for plural. This one pattern covers nine colors: **жовтий, зелений, чорний, білий, сірий, коричневий, рожевий, помаранчевий, фіолетовий**.

**Синій** is the single soft-stem color (**м'яка група**), with the pattern **-ій / -я / -є / -і**: **синій стіл** (M) → **синя книга** (F) → **синє вікно** (N) → **сині олівці** (Pl). Drop **-ій**, add **-я** for feminine, **-є** for neuter, **-і** for plural. The soft stem feels different from the hard one — practice it until the shift is automatic, because you will reach for this word every time you describe the sky, the sea, or the flag.

**Синій** and **блакитний** are not interchangeable. **Прапор України синьо-жовтий** — the flag's blue is **синій**, deep and strong. A clear afternoon sky is **блакитне** — light and pale. You now see a distinction that Ukrainian has always had and English does not.

### Self-check

Test yourself before moving on:

- **What color is the Ukrainian flag?** → **Синьо-жовтий** (**синій** і **жовтий**).
- **Describe 3 things in your room using colors.** → For example: **Мій стіл коричневий. Моя книга синя. Моє вікно велике і біле.**
- **What is the difference between синій and блакитний?** → **Синій** = dark blue (sea, night sky, flag). **Блакитний** = light blue (daytime sky, pale ribbon).
- **Which color adjective has a soft stem (-ій)?** → **Синій** — the only one among the basic colors.
- **How do you ask "what color?"** → **Якого кольору?** (for example: **Якого кольору ця сукня?** — **Чорна.**)
- **What colors does a traditional вишиванка from Полісся use?** → **Червоний і чорний.**

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


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-gender
- **group-sort** — Він, вона чи воно?: Sort nouns by grammatical gender using ending rules
  - Instruction: *Розподіліть слова за родами*
- **quiz** — Який рід?: Determine gender from ending — consonant=masc, -а/-я=fem, -о/-е=neut
- **fill-in** — Мій, моя чи моє?: Choose possessive that matches noun gender
  - Instruction: *Вставте правильне слово*
- **match-up** — Іменник + займенник: Match nouns to він/вона/воно

### Pattern: grammar-adjectives
- **fill-in** — Який? Яка? Яке?: Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Match nouns to correct adjective forms

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
