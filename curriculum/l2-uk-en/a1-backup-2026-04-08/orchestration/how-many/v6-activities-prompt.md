<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/how-many.yaml` file for module **11: How Many?** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-age -->`
- `<!-- INJECT_ACTIVITY: fill-in-numbers -->`
- `<!-- INJECT_ACTIVITY: quiz-prices -->`
- `<!-- INJECT_ACTIVITY: fill-in-phone -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Write the number in words: 15 → п''ятнадцять, 47 → сорок сім'
  items: 10
  type: fill-in
- focus: Скільки коштує? Match price tags to spoken prices.
  items: 8
  type: quiz
- focus: Скільки років? Match ages to descriptions.
  items: 6
  type: quiz
- focus: Complete the phone number dictation
  items: 4
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- п'ятдесят, шістдесят, сімдесят (50, 60, 70)
- вісімдесят, дев'яносто (80, 90)
- двісті, триста, п'ятсот (200, 300, 500)
- копійка (kopek)
- номер (number — phone/room)
- нуль (zero)
required:
- один, два, три, чотири, п'ять (1-5)
- шість, сім, вісім, дев'ять, десять (6-10)
- двадцять, тридцять, сорок (20, 30, 40)
- сто, тисяча (100, 1000)
- скільки (how many/how much)
- коштує (costs — from коштувати)
- гривня (hryvnia — Ukrainian currency)
- рік, роки, років (year/years — age chunks)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

> **Покупець:** Добрий день! Скільки коштує торт? *(Good day! How much does the cake cost?)*
> **Пекар:** Двісті гривень. *(Two hundred hryvnias.)*
> **Покупець:** А хліб? *(And the bread?)*
> **Пекар:** П'ятнадцять гривень. *(Fifteen hryvnias.)*
> **Покупець:** А три булочки? *(And three buns?)*
> **Пекар:** Сорок п'ять гривень. *(Forty-five hryvnias.)*
> **Покупець:** А одне тістечко? *(And one pastry?)*
> **Пекар:** Двадцять гривень. *(Twenty hryvnias.)*
> **Покупець:** Добре. Дякую, до побачення! *(Okay. Thank you, goodbye!)*

Notice the question **Скільки коштує?** (How much does it cost?) — this is the single most useful phrase for shopping in Ukraine. The three nouns in this dialogue are recycled vocabulary from earlier modules: **торт** (cake) is masculine, **булочка** (bun) is feminine, and **тістечко** (pastry) is neuter. You might see that the noun endings change after different numbers — **одне тістечко** but **три булочки**, **п'ятнадцять гривень** but **двісті гривень**. These changes follow a pattern you will memorize as chunks now. The grammar behind them arrives in A2.

> **Оленка:** Привіт, Тарасе! Скільки тобі років? *(Hi, Taras! How old are you?)*
> **Тарас:** Мені чотирнадцять. А тобі? *(I'm fourteen. And you?)*
> **Оленка:** Мені тринадцять. А твоя сестра старша? *(I'm thirteen. Is your sister older?)*
> **Тарас:** Так, їй вісімнадцять. *(Yes, she's eighteen.)*
> **Оленка:** А твій брат? *(And your brother?)*
> **Тарас:** Йому одинадцять. *(He's eleven.)*

The age formula in Ukrainian works like a fixed chunk: **Мені** (I am), **тобі** (you are), **йому** (he is), **їй** (she is) + a number + **років**. Ukrainian uses three different words for "year(s)" depending on the number: **рік** (year) after 1, **роки** (years) after 2–4, and **років** (years) after 5 and above. At A1, memorize these as a pattern — one **рік**, two **роки**, five **років**. No case analysis needed.

<!-- INJECT_ACTIVITY: quiz-age -->

## Числа 1-20 (Numbers 1-20)

The first ten numbers in Ukrainian are: **один** (1), **два** (2), **три** (3), **чотири** (4), **п'ять** (5), **шість** (6), **сім** (7), **вісім** (8), **дев'ять** (9), **десять** (10). Three of these need extra attention when you say them aloud. First, **п'ять** has an apostrophe — the letter **п** is followed by **'ять**, giving it a "p-yat" sound. Second, **сім** is the Ukrainian word for seven — it is NOT "сем," which is a Russian ghost form. Third, **дев'ять** also carries an apostrophe, making it two syllables: "dev-yat." Try counting objects from earlier modules: **один стіл** (one table), **два стільці** (two chairs), **три книги** (three books), **чотири ручки** (four pens), **п'ять зошитів** (five notebooks). The number always comes first, and the nouns are words you already know.

Numbers 11–20 follow a clear pattern. Ukrainian textbooks (Vashulenko, Grade 3) list them as a family built from a base number plus the suffix **-надцять**, parallel to the English "-teen": **одинадцять** (11), **дванадцять** (12), **тринадцять** (13), **чотирнадцять** (14), **п'ятнадцять** (15), **шістнадцять** (16), **сімнадцять** (17), **вісімнадцять** (18), **дев'ятнадцять** (19), **двадцять** (20). The stress rule is consistent and simple: stress ALWAYS falls on the **-на-** syllable within **-надцять**. So it is одинáдцять, дванáдцять, тринáдцять, and so on through дев'ятнáдцять. One spelling trap: **шістнадцять** is written without a soft sign before **н** — not "шістьнадцять." A counting rhyme from Kravcova (Grade 2, p. 92) puts numbers 1–7 into context: «Один і два — росла трава, три, чотири — покосили, п'ять — на сонечку сушили, шість — в копичку поскладали, сім — корівку годували...» Reading this aloud is excellent pronunciation practice.

With numbers 1–20 in hand, you can already do two practical things. First, count real objects around you: **скільки стільців у кімнаті?** (how many chairs in the room?) **скільки книжок на столі?** (how many books on the table?) Second, answer age questions from the dialogue above: **Мені** + number + **років**. Say your own age, a sibling's age, a friend's age — all using numbers from this section. Combined numbers like **двадцять один** (21) and **тридцять п'ять** (35) come in the next section.

<!-- INJECT_ACTIVITY: fill-in-numbers -->

## Десятки і сотні (Tens and Hundreds)

The tens from 20 to 100 follow a predictable pattern — with two famous exceptions. Here is the full list: **двадцять** (20), **тридцять** (30), **сорок** (40), **п'ятдесят** (50), **шістдесят** (60), **сімдесят** (70), **вісімдесят** (80), **дев'яносто** (90), **сто** (100). Most tens are built from a base number plus a suffix: п'ять → **п'ятдесят**, шість → **шістдесят**. But **сорок** (40) is completely irregular — there is no "чотиридесят" in Ukrainian. Historically, **сорок** referred to a bundle of forty animal pelts used as a trading unit (Голуб, Grade 6). And **дев'яносто** (90) breaks the pattern too — it is not "дев'ятдесят." Memorize both as standalone words. To make combined numbers, place the tens word before the unit with no connector: **двадцять один** (21), **тридцять п'ять** (35), **сорок сім** (47), **вісімдесят дев'ять** (89). Practice examples: **двадцять три студенти** (23 students), **сорок вісім гривень** (48 hryvnias), **дев'яносто дві копійки** (92 kopeks).

For prices above 100, you need the hundreds: **сто** (100), **двісті** (200), **триста** (300), **чотириста** (400), **п'ятсот** (500), **шістсот** (600), **сімсот** (700), **вісімсот** (800), **дев'ятсот** (900), **тисяча** (1000). Notice the pattern shift: at 200 the form is **двісті** (not "двасто"), at 300–400 it is **триста** and **чотириста**, and from 500 onward the suffix is **-сот**. The Ukrainian currency is **гривня** (hryvnia), and it changes form after numbers just like "year" does: **одна гривня** (1), **дві гривні** (2–4), **п'ять гривень** (5+). Important: the currency word is **гривня**, not **гривна** — that is a different word meaning a neck ornament. Memorize three price chunks from the bakery dialogue: **п'ятнадцять гривень** (15₴), **сорок п'ять гривень** (45₴), **двісті гривень** (200₴). The noun changes гривня/гривні/гривень are price chunks for now — case grammar arrives in A2.

Ukrainian mobile numbers follow the format 0XX-XXX-XX-XX. Break them into groups for easier reading: **нуль дев'яносто сім** (097) — pause — **три два один** (321) — pause — **сорок п'ять** (45) — pause — **шістдесят сім** (67). Each group is read as a mini-number. A full example: **Мій номер** (my number) — **нуль дев'яносто сім, три два один, сорок п'ять, шістдесят сім**.

<!-- INJECT_ACTIVITY: quiz-prices -->

<!-- INJECT_ACTIVITY: fill-in-phone -->

## Підсумок — Summary

This module built three number systems. First, cardinal numbers 1–20: the base ten (**один** through **десять**), then the **-надцять** teens with stress always on **-на-** (одинáдцять, дванáдцять...). Two apostrophe words to remember: **п'ять** and **дев'ять**. Second, the tens from 20 to 100, with two irregulars that must simply be memorized: **сорок** (40) and **дев'яносто** (90). Third, the hundreds from **сто** to **тисяча**, where the pattern shifts at **двісті** (200) and again at **п'ятсот** (500). Combined numbers never need a connector word — just say the tens then the unit: **двадцять три** (23), **сто сорок п'ять** (145).

**Prices.** The question is **Скільки коштує?** and the answer is a number plus the right form of **гривня**: **одна гривня** (1₴), **дві гривні** (2–4₴), **п'ять гривень** (5+₴). Three memorized frames: **п'ятнадцять гривень** (bread), **сорок п'ять гривень** (three buns), **двісті гривень** (a cake). You can now ask and answer any price up to **тисяча гривень** (1000₴).

**Age.** The question is **Скільки тобі років?** and the answer follows the formula: **Мені/Йому/Їй** + number + **рік/роки/років**. Three memorized frames: **Мені чотирнадцять років** (14), **Йому двадцять два роки** (22), **Їй тридцять п'ять років** (35). The switch between рік, роки, and років is a chunk — feel it through repetition, do not analyze it.

**Phone numbers.** Read Ukrainian mobile numbers in groups of 3–2–2–2. Practice with three sample numbers: (a) 097-321-45-67, (b) 050-112-33-99, (c) 073-456-78-10. Read each one aloud in Ukrainian. The bakery could call you when your cake is ready — just say **Мій номер телефону...** and dictate it.

Self-check — answer these in Ukrainian:

- Як сказати 17? → **сімнадцять**
- Як сказати 40? → **сорок** (not "чотиридесят"!)
- Як сказати 90? → **дев'яносто** (not "дев'ятдесят"!)
- Торт коштує 250₴. Як сказати? → **Двісті п'ятдесят гривень.**
- Скажіть своє ім'я і вік: **Мене звати ___, мені ___ років.**
- Продиктуйте свій номер телефону по-українськи.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: how-many
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

**Level: A1.2-A1.3 (Module 11/55) — EARLY BEGINNER**

The learner knows the alphabet and ~200 words. They:
- Can read Ukrainian slowly
- Know basic nouns, adjectives, simple verb forms
- Cannot handle complex sentences or grammar terminology in Ukrainian

**Instructions in simple English with Ukrainian key terms in bold.**
Example: 'Choose the correct form of **мій/моя/моє**'

**Good activity types:** quiz, fill-in (simple sentences), match-up, group-sort, true-false, observe, anagram, translate (English→Ukrainian).


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-numbers
- **quiz** — Яке число?: Recognize written number words
- **fill-in** — Напиши цифру словом: Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Match digits to their Ukrainian word forms

### Pattern: general-vocabulary
- **match-up** — Слово → переклад: Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Fill in the missing word from context
- **anagram** — Склади слово: Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Choose correct translation from options

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
