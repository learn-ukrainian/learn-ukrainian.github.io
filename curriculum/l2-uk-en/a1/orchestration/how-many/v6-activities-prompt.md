# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/how-many.yaml` file for module **11: How Many?** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-numbers-words -->`
- `<!-- INJECT_ACTIVITY: quiz-ages -->`
- `<!-- INJECT_ACTIVITY: fill-in-numbers-tens -->`
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

Numbers are part of every conversation. At a market, you ask about prices. When meeting someone new, you ask about age. When exchanging contacts, you read phone numbers aloud. This module covers all three — and it starts at the market.

> **Оксана:** Скільки коштує ця сумка? *(How much does this bag cost?)*
> **Продавець:** Двісті гривень. *(Two hundred hryvnias.)*
> **Оксана:** А ця? *(And this one?)*
> **Продавець:** Сто п'ятдесят. *(One hundred fifty.)*
> **Оксана:** Ой, дорого! А є дешевше? *(Oh, that's expensive! Is there something cheaper?)*
> **Продавець:** Ось ця — вісімдесят гривень. *(Here's this one — eighty hryvnias.)*
> **Оксана:** Добре, я беру цю. *(Alright, I'll take this one.)*

The question **Скільки коштує?** (How much does it cost?) is the most useful phrase at any Ukrainian market or shop. **Гривень** (hryvnias) is the currency word after numbers like 5 and above. **Дорого** means "expensive," **дешевше** means "cheaper," and **я беру цю** (I'll take this one) is a fixed phrase — just memorize it as a chunk for now.

> **Марина:** Привіт! Як тебе звати? *(Hi! What's your name?)*
> **Андрій:** Андрій. А тебе? *(Andriy. And yours?)*
> **Марина:** Марина. Скільки тобі років? *(Maryna. How old are you?)*
> **Андрій:** Мені двадцять п'ять. А тобі? *(I'm twenty-five. And you?)*
> **Марина:** Мені тридцять два. А це мій брат Тарас. *(I'm thirty-two. And this is my brother Taras.)*
> **Андрій:** Скільки йому років? *(How old is he?)*
> **Марина:** Йому вісімнадцять. *(He's eighteen.)*

The age question **Скільки тобі років?** literally translates as "How many to-you of-years?" The answer follows a simple pattern with three memorized forms: **рік** (year) after numbers ending in 1 — двадцять один рік; **роки** (years) after 2, 3, 4 — двадцять два роки; **років** (of years) after 5 and above — двадцять п'ять років. Do not try to analyze the grammar behind these forms — just learn them as fixed chunks. The full grammar arrives in A2.

## Числа 1-20 (Numbers 1-20)

The first ten numbers in Ukrainian:

- **один** (one), **два** (two), **три** (three), **чотири** (four), **п'ять** (five)
- **шість** (six), **сім** (seven), **вісім** (eight), **дев'ять** (nine), **десять** (ten)

A few pronunciation details matter here. **П'ять** and **дев'ять** both contain an apostrophe — the sign that tells you the lips open wide for the **я** sound right after the consonant. **Сім** has a clear **і** sound — never pronounce it as "сем." **Шість** ends with a soft **ть**. Try counting with objects you already know from Module 8: один стіл, два стільці, три книги, чотири вікна. You will notice the noun changes shape after certain numbers — that is normal. Copy the patterns you hear; the rules come later.

The number **один** changes form depending on the noun: **один** стіл (masculine), **одна** книга (feminine), **одне** вікно (neuter). The same applies to **два**: **два** стільці (masculine/neuter) but **дві** книги (feminine). These are patterns to memorize with familiar nouns, not grammar rules to analyze. You already know the nouns — just copy how the number sounds with each one.

<!-- INJECT_ACTIVITY: fill-in-numbers-words -->

Numbers 11 through 19 follow a recognizable pattern. Take the base number and add **-надцять** — similar to English "-teen":

- **одинадцять** (11), **дванадцять** (12), **тринадцять** (13), **чотирнадцять** (14)
- **п'ятнадцять** (15), **шістнадцять** (16), **сімнадцять** (17)
- **вісімнадцять** (18), **дев'ятнадцять** (19)

The stress in all of these words falls on the syllable **-на-** inside **-надцять**: одинадцять, дванадцять, п'ятнадцять. This is consistent across every single teen number — no exceptions. Then comes **двадцять** (20), which stands on its own with stress on the first syllable. Notice that the apostrophe carries over from the base: п'ять → п'ятнадцять, дев'ять → дев'ятнадцять.

Now connect these to real life. Ages in the teens all use **років** because every number from 11 to 19 triggers the 5+ form:

- Мені тринадцять років. *(I'm thirteen.)*
- Мені п'ятнадцять років. *(I'm fifteen.)*
- Мені вісімнадцять років. *(I'm eighteen.)*
- Мені дев'ятнадцять років. *(I'm nineteen.)*

<!-- INJECT_ACTIVITY: quiz-ages -->

## Десятки і сотні (Tens and Hundreds)

The full set of tens from 20 to 100:

- **двадцять** (20), **тридцять** (30), **сорок** (40), **п'ятдесят** (50)
- **шістдесят** (60), **сімдесят** (70), **вісімдесят** (80)
- **дев'яносто** (90), **сто** (100)

Most of these follow a clear pattern: take the base number and add **-десят** (п'ять → п'ятдесят, шість → шістдесят). But two numbers break the pattern completely. **Сорок** (40) is not "чотиридесят" — it is its own unique word. **Дев'яносто** (90) is not "дев'ятдесят" — it too stands alone. These two simply must be memorized.

Combining tens and units is straightforward — just say the ten, then the unit as two separate words. No hyphens, no special joining rules:

- двадцять один (21), тридцять п'ять (35), сорок сім (47)
- п'ятдесят три (53), шістдесят вісім (68), дев'яносто дев'ять (99)

Practice by saying your own age, a friend's age, a parent's age — all using this simple two-word pattern.

<!-- INJECT_ACTIVITY: fill-in-numbers-tens -->

For prices, you need hundreds. Here is the full set:

- **сто** (100), **двісті** (200), **триста** (300), **чотириста** (400)
- **п'ятсот** (500), **шістсот** (600), **сімсот** (700)
- **вісімсот** (800), **дев'ятсот** (900), **тисяча** (1000)

The pattern: numbers 2–4 use endings related to **-ста** (though **двісті** is irregular), while 5–9 all use **-сот**. Combined examples: сто двадцять п'ять (125), двісті п'ятдесят (250), п'ятсот сімдесят три (573).

The word **гривня** (hryvnia, the Ukrainian currency ₴) changes form after different numbers, following the same 1 / 2–4 / 5+ logic as **рік**:

| Number group | Form | Example |
|---|---|---|
| 1 | одна **гривня** | одна гривня |
| 2–4 | дві/три/чотири **гривні** | три гривні |
| 5+ | п'ять/десять/сто **гривень** | сто гривень |

Real Ukrainian prices to practice: кава — тридцять п'ять гривень, хліб — двадцять гривень, квиток у метро — вісім гривень.

<!-- INJECT_ACTIVITY: quiz-prices -->

## Підсумок — Summary

Ukrainian phone numbers follow the format +38 (0XX) XXX-XX-XX. When reading them aloud, Ukrainians say the area code digit by digit and then often group the last six digits into pairs. The word for zero is **нуль** (zero). Here are two examples:

- Мій номер — нуль дев'яносто сім, три два один, сорок п'ять, шістдесят сім. *(My number is 097-321-45-67.)*
- Мій номер — нуль дев'яносто три, п'ять сім два, тридцять один, дев'яносто два. *(My number is 093-572-31-92.)*

Notice how the first three digits after **нуль** are said individually (дев'яносто сім = 97, not "nine seven"), while the remaining pairs use regular two-digit numbers.

<!-- INJECT_ACTIVITY: fill-in-phone -->

Three practical uses tie this module together. First, **prices**: **Скільки коштує?** — **Двісті п'ятдесят гривень.** Is that **дорого** (expensive) or **дешево** (cheap)? Second, **age**: **Скільки тобі років?** — **Мені двадцять три роки.** Remember the three forms: **рік** after 1, **роки** after 2–4, **років** after 5+. Third, **phone numbers**: **Мій номер телефону** — read pairs of digits, starting with **нуль**. Here is a quick reference showing how the same 1 / 2–4 / 5+ logic works for both age and currency:

| Group | рік (year) | гривня (hryvnia) |
|---|---|---|
| 1 | один рік | одна гривня |
| 2–4 | два/три/чотири роки | дві/три/чотири гривні |
| 5+ | п'ять/двадцять років | п'ять/двадцять гривень |

The same pattern — just different words. Memorize both sets as chunks.

Now test yourself. Say these aloud in Ukrainian: your age (Мені ... років/роки/рік), a price (двісті п'ятдесят гривень for 250 UAH), your phone number digit by digit, the numbers from 1 to 20 without stopping, and these five tricky numbers: **сорок** (40), **дев'яносто** (90), **сто** (100), **п'ятсот** (500), **тисяча** (1000). One cultural note: Ukrainians use the **гривня** (₴), divided into 100 **копійок** (kopeks). The forms follow the familiar pattern: одна **копійка**, дві **копійки**, п'ять **копійок**.

In Module 12 (This and That), you will point at things and describe them using demonstratives. You already met **ця сумка** in the market dialogue — next you will learn how to say "this one" and "that one" for all genders. The numbers from this module will keep appearing everywhere: prices, ages, addresses, dates. Keep practicing — every number you see in daily life, try saying it in Ukrainian.

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
