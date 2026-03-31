<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/holidays.yaml` file for module **46: Holidays** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-holiday-dates -->`
- `<!-- INJECT_ACTIVITY: quiz-holiday-traditions -->`
- `<!-- INJECT_ACTIVITY: group-sort-traditions -->`
- `<!-- INJECT_ACTIVITY: fill-in-greetings -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Match holiday to date: Різдво → 25 грудня, День Незалежності → 24 серпня'
  items: 8
  type: quiz
- focus: 'Greetings: З ___! (Різдвом, Великоднем, Новим роком)'
  items: 8
  type: fill-in
- focus: Which holiday? Кутя, колядки, Свята вечеря → (Різдво / Великдень / Новий
    рік)
  items: 8
  type: quiz
- focus: 'Sort traditions by holiday: Різдво vs Великдень vs День Незалежності'
  items: 10
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- кутя (kutia, f)
- колядка (carol, f)
- писанка (decorated Easter egg, f)
- паска (Easter bread, f)
- парад (parade, m)
- прапор (flag, m)
- вишиванка (embroidered shirt, f)
- незалежність (independence, f)
- салют (fireworks, m)
required:
- свято (holiday, n)
- святкувати (to celebrate)
- Різдво (Christmas, n)
- Великдень (Easter, m)
- Новий рік (New Year)
- вітати (to congratulate/greet)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Ukrainians love their holidays — and they have special greetings for each one. Here are two conversations: one about **Різдво** (Christmas), one about **День Незалежності** (Independence Day).

> **Олена:** Коли в тебе Різдво? *(When is your Christmas?)*
> **Том:** Двадцять п'ятого грудня. А в тебе? *(December 25th. And yours?)*
> **Олена:** У нас — теж! *(Ours too!)*
> **Том:** Теж? Раніше було сьомого січня, так? *(Also? It used to be January 7th, right?)*
> **Олена:** Так, але тепер — двадцять п'ятого. *(Yes, but now it's the 25th.)*
> **Том:** Що ви робите на Різдво? *(What do you do on Christmas?)*
> **Олена:** Ми співаємо колядки і їмо кутю. *(We sing carols and eat kutia.)*
> **Том:** Що таке кутя? *(What is kutia?)*
> **Олена:** Це пшениця з медом і маком. Дуже смачно! *(It's wheat with honey and poppy seeds. Very tasty!)*
> **Том:** Як гарно! З Різдвом! *(How lovely! Merry Christmas!)*
> **Олена:** З Різдвом Христовим! *(Merry Christmas! [lit. "with Christ's Christmas"])*

Both **З Різдвом!** and **З Різдвом Христовим!** are correct greetings. The longer form with **Христовим** is the fuller, more traditional way to say it.

> **Марко:** Двадцять четверте серпня — День Незалежності! *(August 24th — Independence Day!)*
> **Оксана:** Так, це головне державне свято України. *(Yes, it's the main national holiday of Ukraine.)*
> **Марко:** Що ви робите? *(What do you do?)*
> **Оксана:** Вдень ми дивимося парад і ходимо на концерт. *(During the day we watch the parade and go to a concert.)*
> **Марко:** А ввечері? *(And in the evening?)*
> **Оксана:** Ввечері — салют і святковий вечір з друзями. *(In the evening — fireworks and a festive evening with friends.)*
> **Марко:** Усі у вишиванках? *(Everyone in vyshyvankas?)*
> **Оксана:** Так! З Днем Незалежності! *(Yes! Happy Independence Day!)*
> **Марко:** Слава Україні! *(Glory to Ukraine!)*

Now check yourself — can you answer these from the dialogues?

- Що їдять на Різдво? *(What do people eat on Christmas?)*
- Де люди бувають на День Незалежності? *(Where do people go on Independence Day?)*

<!-- INJECT_ACTIVITY: quiz-holiday-dates -->

## Українські свята (Ukrainian Holidays)

### Різдво (Christmas) — December 25

Ukraine celebrates **Різдво** on **двадцять п'яте грудня** (December 25). Until 2023, the official date was January 7 — the Russian Orthodox calendar date. Ukraine moved Christmas to December 25, aligning with most of Europe and Ukraine's own pre-Soviet tradition. This was part of a broader break from Russian cultural influence. The word **Різдво** is neuter — so in the instrumental case it becomes **різдвом**: **З Різдвом!**

The heart of Ukrainian Christmas is **Свята вечеря** (Holy Supper) on December 24 — **Святвечір** (Christmas Eve). The table has **дванадцять страв** (twelve dishes), one for each apostle. All dishes are **пісні** (fasting) — no meat. The first dish is always **кутя** — wheat porridge with **мед** (honey), **мак** (poppy seeds), and **горіхи** (nuts). After кутя come **борщ**, **вареники**, **риба** (fish), and **узвар** (dried fruit compote). As Ukrainian textbooks describe it: on Святвечір, кутя is a sacred dish that connects the family to their ancestors.

After dinner, **колядники** (carolers) go door to door singing **колядки** (Christmas carols). These songs wish the family health and happiness — **здоров'я і щастя**. A traditional folk carol from the textbook begins: «Ой перший же празник — то Різдво Христове». The verb **колядувати** means "to go caroling" — a living tradition across Ukraine to this day.

### Великдень (Easter)

**Великдень** is the biggest religious holiday in Ukraine. The date changes each year — it falls in **весна** (spring). When you meet someone on Easter, the greeting is a call-and-response:

- **Христос воскрес!** *(Christ is risen!)*
- **Воістину воскрес!** *(Indeed risen!)*

If someone says the first line, you answer with the second. The word **воістину** means "truly" or "indeed."

Three traditions define Великдень: **Писанка** — a decorated egg, not just dyed but covered in intricate wax-resist patterns. This is uniquely Ukrainian folk art. **Паска** — tall, sweet Easter bread, blessed at church. And **святити кошик** — blessing the Easter basket at church on Saturday night. The basket holds паска, писанки, meat, and other food for the Sunday meal.

<!-- INJECT_ACTIVITY: quiz-holiday-traditions -->

## Державні свята (National Holidays)

### День Незалежності — August 24

On **двадцять четверте серпня 1991 року**, Ukraine declared independence from the Soviet Union. This is the most important **державне свято** (national holiday). The word **незалежність** (independence) breaks down clearly: **не** (not) + **залежати** (to depend) — not depending on another state. **Незалежний** means "independent," and **держава** means "state" — so **державне свято** is literally a "state holiday."

How do Ukrainians celebrate? During the day — **парад** (parade) in the city center, **концерти** (concerts) on the main squares, and people carry **синьо-жовті прапори** (blue-and-yellow flags) through the streets. In the evening — **салют** (fireworks) over the city. Many people wear **вишиванка** (embroidered shirt) as a symbol of Ukrainian identity.

The standard greeting is **З Днем Незалежності!** (Happy Independence Day!). And the national call-and-response:

- **Слава Україні!** *(Glory to Ukraine!)*
- **Героям слава!** *(Glory to the heroes!)*

This is not just a holiday phrase — it is used year-round. Since the Maidan revolution in 2014, it has become the official military greeting and a symbol of Ukrainian resilience.

### Other Holidays to Know

Four more holidays every learner should recognize:

- **Новий рік** (New Year) — January 1. The biggest secular celebration. Greeting: **З Новим роком!**
- **Вишиванковий день** (Vyshyvanka Day) — the third Thursday of May. Everyone wears a **вишиванка** — a symbol of Ukrainian identity and cultural resistance.
- **День Конституції** (Constitution Day) — June 28.
- **День захисників і захисниць України** (Defenders' Day) — October 1. The official name includes both masculine (**захисник**) and feminine (**захисниця**) forms.

<!-- INJECT_ACTIVITY: group-sort-traditions -->

## Підсумок — Summary

### The З + Instrumental Greeting Pattern

Every Ukrainian holiday greeting follows one pattern: **З** + the holiday noun in the **instrumental case** + exclamation mark.

- **З Різдвом!** (Merry Christmas!) — різдво → різдвом
- **З Великоднем!** (Happy Easter!) — великдень → великоднем
- **З Новим роком!** (Happy New Year!) — новий рік → новим роком
- **З Днем Незалежності!** (Happy Independence Day!)
- **З днем народження!** (Happy birthday!)
- **Зі святом!** (Happy holiday!) — свято → святом

The instrumental endings: **-ом** for masculine and neuter nouns (різдвом, роком, святом), **-ою/-ею** for feminine (перемогою, весною).

### Connection to What You Already Know

You already know the instrumental case from **з** + noun: **кава з молоком** (coffee with milk), **борщ з хлібом** (borshch with bread), **вареники з сиром** (varenyky with cheese). Holiday greetings use the same preposition and the same case — just with a different meaning. **З молоком** = "with milk." **З Різдвом** = "with Christmas" → wishing you a happy Christmas. Same grammar, new context.

### Holiday Calendar

| Date | Holiday | Greeting |
|------|---------|----------|
| грудень 25 | Різдво | З Різдвом Христовим! |
| січень 1 | Новий рік | З Новим роком! |
| весна | Великдень | Христос воскрес! |
| травень (третій четвер) | Вишиванковий день | — |
| серпень 24 | День Незалежності | З Днем Незалежності! / Слава Україні! |
| жовтень 1 | День захисників і захисниць | — |

### Self-Check

- Як привітати з Різдвом? → **З Різдвом Христовим!**
- Що відповідають на «Христос воскрес!»? → **Воістину воскрес!**
- Коли День Незалежності? → **Двадцять четверте серпня.**
- Що таке кутя? → **Пшениця з медом, маком і горіхами.**
- Як привітати з Новим роком? → **З Новим роком!**

<!-- INJECT_ACTIVITY: fill-in-greetings -->

## Підсумок

You now know the major Ukrainian holidays and how to greet people for each one. **Різдво** on December 25 brings **Свята вечеря** with twelve fasting dishes, starting with **кутя**. **Великдень** in spring means **писанки**, **паска**, and the greeting **Христос воскрес! — Воістину воскрес!** **День Незалежності** on August 24 celebrates Ukraine's freedom with parades, flags, and **Слава Україні! — Героям слава!** The universal greeting formula is **З + instrumental**: З Різдвом, З Великоднем, З Новим роком, З Днем Незалежності. You already knew this case from кава з молоком — now you can use it to celebrate with Ukrainians. **З перемогою!**

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: holidays
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

**Level: A1.4+ (Module 46/55) — BEGINNER**

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
