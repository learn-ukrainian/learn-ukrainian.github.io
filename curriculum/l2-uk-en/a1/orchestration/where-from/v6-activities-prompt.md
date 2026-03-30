<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/where-from.yaml` file for module **34: Where From?** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-zvidky -->`
- `<!-- INJECT_ACTIVITY: group-sort-location-trio -->`
- `<!-- INJECT_ACTIVITY: quiz-prepositions -->`
- `<!-- INJECT_ACTIVITY: fill-in-location-vs-origin -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- blanks:
  - Звідки ти? — Я {з України}.
  - Вона {з Канади}.
  - Ми {з Києва}, а ви?
  - Джон {зі США}.
  - Мій друг {з Німеччини}.
  - Я {зі Львова}.
  - Вони {з Англії}.
  - Олена {з Одеси}.
  focus: Answer Звідки? using з/із/зі + memorized genitive chunks
  items: 8
  type: fill-in
- focus: Categorize phrases into Де? (Locative), Куди? (Accusative), Звідки? (Genitive)
  groups:
  - items:
    - в Україні
    - в Києві
    - на роботі
    name: Де? (Where?)
  - items:
    - в Україну
    - в Київ
    - на роботу
    name: Куди? (Where to?)
  - items:
    - з України
    - з Києва
    - з роботи
    name: Звідки? (Where from?)
  items: 9
  type: group-sort
- focus: Choose correct preposition (в/на/з) for location/direction
  items: 8
  questions:
  - Я йду... роботи. (з / на / в)
  - Вона йде... школу. (в / на / зі)
  - Ми зараз... Україні. (в / з / на)
  - Я їду... Канаду. (в / з / на)
  - Він... Німеччини. (з / в / на)
  - Вони... Львові. (у / зі / на)
  - Я йду... магазину. (з / в / на)
  - Олена... школи. (зі / в / на)
  type: quiz
- blanks:
  - Я живу {в Києві}, але я {зі Львова}.
  - Вона живе {в Канаді}, але вона {з України}.
  - Ми зараз {в Англії}, але ми {з Польщі}.
  - Він живе {в Одесі}, але він {з Харкова}.
  - Я {з Німеччини}, але зараз я {в Україні}.
  - Ти {зі США}, але живеш {у Києві}.
  focus: Contrast current location (в/на) and origin (з/із)
  items: 6
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- Одеса (Odesa)
- Харків (Kharkiv)
- США (USA)
- Англія (England)
- Німеччина (Germany)
- Польща (Poland)
- додому (home — direction)
required:
- звідки (where from)
- з/із/зі (from — + genitive chunk)
- Україна (Ukraine)
- Київ (Kyiv)
- Львів (Lviv)
- Канада (Canada)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

It's the first week of the semester, and students from all over the world are meeting at a Kyiv university. Everyone wants to know the same thing: **Звідки ти?** (Where are you from?) Here's how that conversation sounds in Ukrainian — using **з** (from) plus a country or city name.

### Діалог 1 — На зустрічі студентів (At a student mixer)

> **Тарас:** Привіт! Мене звати Тарас. Звідки ти? *(Hi! My name is Taras. Where are you from?)*
> **Лена:** Я з України, з Києва. А ти? *(I'm from Ukraine, from Kyiv. And you?)*
> **Тарас:** Я з Канади, із Торонто. *(I'm from Canada, from Toronto.)*
> **Лена:** Давно тут? *(Been here long?)*
> **Тарас:** Ні, я приїхав місяць тому. А ти, Кенджі? *(No, I arrived a month ago. And you, Kenji?)*
> **Кенджі:** Я з Японії, з Токіо. *(I'm from Japan, from Tokyo.)*
> **Тарас:** Як цікаво! *(How interesting!)*

:::tip
**Я приїхав** (I arrived) — memorize this as a ready-made chunk. The full verb **приїхати** belongs to A2. For now, just use **я приїхав** (masculine) or **я приїхала** (feminine) when you need to say "I arrived."
:::

Notice how Dialogue 1 uses **з** (from) with both countries and cities. The same question — **Звідки ти?** — works for both. When Lena answers **Я з України, з Києва**, she's layering: country first, then city. Think of it as zooming in: "from Ukraine, from Kyiv." Tomas does the same: **Я з Канади, із Торонто** — from Canada, from Toronto.

### Діалог 2 — На вулиці (On the street)

> **Оксана:** Звідки ти йдеш? *(Where are you coming from?)*
> **Микола:** Я йду з роботи. А ти? *(I'm coming from work. And you?)*
> **Оксана:** Я зі школи. Куди ти зараз? *(From school. Where are you headed now?)*
> **Микола:** Додому. А Олена де? *(Home. And where's Olena?)*
> **Оксана:** Вона ще в магазині. Але скоро йде з магазину додому. *(She's still at the store. But she's heading home from the store soon.)*
> **Микола:** Добре. Бувай! *(Okay. Bye!)*

:::note
**з роботи** = from work | **зі школи** = from school | **додому** = homeward (direction)
:::

Look at what both dialogues share. **Звідки?** always triggers **з/із/зі** plus a place name: **з Японії** (from Japan), **з роботи** (from work), **зі школи** (from school). But notice two different uses: (1) **Звідки ти?** asks about your origin or nationality — **Я з Японії**; (2) **Звідки ти йдеш?** asks where you're physically coming from right now — **з роботи**, **зі школи**. Both use the same preposition family. Up next: the full direction trio **Де?–Куди?–Звідки?** — the three questions every Ukrainian speaker uses constantly.

<!-- INJECT_ACTIVITY: fill-in-zvidky -->

## Звідки? (Where From?)

You already know two of the three essential location questions. **Де ти?** (Where are you?) appeared in M05. **Куди ти їдеш?** (Where are you going?) came in M33. Now the trio is complete with **Звідки ти?** (Where are you from?). Here's the whole system — one country, three different forms, three different questions:

- **Де ти?** — **В Україні.** (locative — where you ARE right now)
- **Куди ти їдеш?** — **В Україну.** (accusative — direction TO)
- **Звідки ти?** — **З України.** (genitive chunk — origin FROM)

See how **Україна** changes shape each time? **В Україні**, **В Україну**, **З України** — three different endings for three different situations. Native speakers switch between them automatically. We learn the pattern now and the full grammar of these endings (**відмінки**) in A2.

### З / із / зі — the euphony rule

Remember the euphony patterns from M28? The preposition **з** (from) follows the same logic. It has three forms to keep Ukrainian sounding smooth:

**With Ukrainian cities:**
- **з Києва**, **з Одеси**, **з Харкова**, **з Дніпра**
- **зі Львова** — **зі** before the лв- cluster

**With countries:**
- **з Канади**, **з Англії**, **з Польщі**, **з Франції**, **з Японії**, **з Німеччини**
- **зі США** / **зі Штатів** — **зі** before the шт- cluster

**With everyday places:**
- **з роботи**, **з магазину**, **з банку**, **з парку**
- **зі школи** — **зі** before шк-

The pattern: **з** before most consonants and vowels; **із** between awkward consonant clusters; **зі** before combinations starting with з-, с-, ш-. At A1, don't calculate — just recognize the pattern and memorize the fixed phrases from the lists above.

### Memorize as chunks

Treat **з** + place as sealed units, the same way you learned **в Україні** as a single phrase back in M30. English speakers don't think "in + Ukraine" as separate words — they say "in Ukraine" as one chunk. Do the same here. **Я з України**, **з Києва**, **з роботи** — three set phrases to know by heart. Why does **Київ** become **Києва** and **Україна** become **України**? Those are genitive case endings — full A2 grammar. For now, recognize and reproduce the forms from this module's vocabulary. If you can say **Я з Києва** without hesitating, you're doing it right.

<!-- INJECT_ACTIVITY: group-sort-location-trio -->

## Країни і міста (Countries and Cities)

### Українські міста (Ukrainian cities)

Here are six major Ukrainian cities with their **з**-forms — the shape they take after **Звідки?**:

| Місто (City) | Звідки? (From where?) |
|---|---|
| **Київ** (Kyiv) | **з Києва** |
| **Львів** (Lviv) | **зі Львова** |
| **Одеса** (Odesa) | **з Одеси** |
| **Харків** (Kharkiv) | **з Харкова** |
| **Дніпро** (Dnipro) | **з Дніпра** |
| **Запоріжжя** (Zaporizhzhia) | **із Запоріжжя** |

Ukrainian city names carry history. **Київ** takes its name from Кий, a legendary Polanian prince. **Львів** is named for Prince Лев Данилович — Lev, son of Danylo. When you say **зі Львова**, you're using a form shaped by centuries of Ukrainian language. Notice **зі Львова** specifically — the **зі** form prevents an awkward зл- consonant cluster.

### Країни (Countries)

Countries follow the same pattern. Here are the ones you'll use most often:

**Nearby:** **Польща** → **з Польщі** | **Угорщина** (Hungary) → **з Угорщини** | **Румунія** (Romania) → **з Румунії**

**Further away:** **Канада** → **з Канади** | **США** → **зі США** (**зі Штатів**) | **Англія** (England) → **з Англії** | **Німеччина** (Germany) → **з Німеччини** | **Франція** (France) → **з Франції** | **Японія** (Japan) → **з Японії** | **Італія** (Italy) → **з Італії**

One important note: these are Ukrainian names, not transliterations of English. Germany is **Німеччина** (not "Германія"). Japan is **Японія**. Canada is **Канада** (not "Кенада"). Always use the Ukrainian forms.

### Національність і мова (Nationality and language)

Back in M05, you learned to introduce yourself. Now extend that chain with origin:

- **Я з України** → **Я українець** (m) / **українка** (f) → **Я говорю українською.**
- **Я з Польщі** → **Я поляк** (m) / **полька** (f) → **Я говорю польською.**

And here's a new contrast — where you live now versus where you're originally from:

- **Я живу в Києві, але я зі Львова.** (I live in Kyiv, but I'm from Lviv.)
- **Вона живе в Канаді, але вона з України.** (She lives in Canada, but she's from Ukraine.)

The pattern: **живу в** [place — locative] + **але я з** [place — genitive chunk]. This is how diaspora Ukrainians talk about themselves every day.

<!-- INJECT_ACTIVITY: quiz-prepositions -->

<!-- INJECT_ACTIVITY: fill-in-location-vs-origin -->

## Підсумок — Summary

You now have all three direction questions that Ukrainian speakers use constantly. Here's the complete trio — three questions, three preposition families, three memorized chunk sets:

| Питання (Question) | Прийменник (Preposition) | Приклад (Example) | Meaning |
|---|---|---|---|
| **Де?** | в/на + locative chunk | **В Україні. У Києві. На роботі.** | where you ARE |
| **Куди?** | в/на + accusative chunk | **В Україну. У Київ. На роботу.** | where you're GOING |
| **Звідки?** | з/із/зі + genitive chunk | **З України. З Києва. З роботи.** | where you're FROM |

Why does **Київ** become **Києва** in one column and **Києві** in another? Those are different case endings — the genitive and locative. Full case grammar arrives in A2. For now: recognize the pattern, memorize the fixed forms from this module. You already have all three direction questions. Use them.

### Перевір себе (Self-check)

Answer these three questions out loud in Ukrainian. Switch the prepositions correctly for each:

- **Звідки ти?** (З якої країни? З якого міста?)
- **Де ти зараз?** (В якому місті? В якій країні?)
- **Куди ти йдеш після цього уроку?** (Додому? На роботу? В магазин?)

If you can answer all three — switching smoothly between **з/із/зі**, **в/на**, and **в/на** — the **Де?/Куди?/Звідки?** trio is yours.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: where-from
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

**Level: A1.4+ (Module 34/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
