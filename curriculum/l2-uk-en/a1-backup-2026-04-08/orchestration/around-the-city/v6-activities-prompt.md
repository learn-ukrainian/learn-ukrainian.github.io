<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/around-the-city.yaml` file for module **33: Around the City** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-directions -->`
- `<!-- INJECT_ACTIVITY: quiz-de-kudy -->`
- `<!-- INJECT_ACTIVITY: fill-in-transport -->`
- `<!-- INJECT_ACTIVITY: match-navigation -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- blanks:
  - Ідіть {прямо}, потім {направо}. Бібліотека на розі.
  - Вибачте, як дістатися до музею? — Ідіть {наліво}.
  - Аптека близько. Ідіть {прямо} п'ять хвилин.
  - Потім ідіть {направо}, школа там.
  - Йдіть {прямо}, а потім {наліво}.
  - Ресторан поруч. Ідіть {прямо} і {направо}.
  focus: Give directions using прямо, направо, наліво
  items: 6
  type: fill-in
- focus: Де (locative) or Куди (accusative) in context
  items: 6
  questions:
  - Я зараз... (в парку / в парк)
  - Я йду... (в магазин / в магазині)
  - Магазин на... (вулиці / вулицю)
  - Потім їду на... (роботу / роботі)
  - Ми зараз у... (центрі / центр)
  - Вона йде в... (офіс / офісі)
  type: quiz
- blanks:
  - Я їду в центр {на метро}.
  - Потім іду {пішки} п'ять хвилин.
  - Вона їде на роботу {автобусом}.
  - Школа далеко, треба їхати {на метро}.
  - Парк близько, ми йдемо {пішки}.
  - Ми їдемо в ресторан {автобусом}.
  focus: Describe route with transport (автобусом, пішки, на метро)
  items: 6
  type: fill-in
- focus: Match question to logical response for navigation
  items: 6
  pairs:
  - Вибачте, як дістатися до бібліотеки?: Ідіть прямо, потім направо.
  - Де музей?: Він у центрі.
  - Як ти дістаєшся на роботу?: Їду автобусом.
  - Школа далеко?: Ні, близько. П'ять хвилин пішки.
  - Куди ви йдете?: У магазин.
  - Де ти живеш?: На вулиці Франка.
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- дістатися (to get to)
- ідіть (go! — imperative, preview)
- їдьте (go by transport! — imperative, preview)
- поруч (nearby)
required:
- пішки (on foot)
- хвилина (minute, f)
- район (neighborhood, m)
- центр (center, m)
- вибачте (excuse me)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Navigating a Ukrainian city means juggling two questions at once: **де?** (where?) for your current location and **куди?** (where to?) for your destination. You also need to ask for directions and describe how you travel. Two real situations show this in action — a stranger asking for help on a Lviv street, and a friend describing their morning commute.

### Діалог 1 — Asking for Directions

> **Турист:** Вибачте, як дістатися до бібліотеки? *(Excuse me, how do I get to the library?)*
> **Перехожий:** Ідіть прямо, потім направо. Бібліотека на розі. *(Go straight, then right. The library is at the corner.)*
> **Турист:** А музей? *(And the museum?)*
> **Перехожий:** Музей далеко. Їдьте на метро до центру. *(The museum is far. Take the metro to the center.)*
> **Турист:** Дякую! *(Thank you!)*

The tourist opens with **вибачте** (excuse me) — the standard polite formula for addressing a stranger. The full question **як дістатися до...?** (how to get to...?) is a survival phrase — memorize it as one chunk. You will study the verb **дістатися** (to get to) properly at B1; for now, just use the whole phrase.

Notice the two commands: **ідіть** (go — on foot) and **їдьте** (go — by vehicle). Both are formal imperatives, a preview of grammar you will learn later. The difference is simple: **ідіть** means walking, **їдьте** means riding. The phrase **на розі** (at the corner) is a locative chunk — learn it as a fixed unit.

### Діалог 2 — Describing Your Route

> **Олена:** Як ти дістаєшся на роботу? *(How do you get to work?)*
> **Тарас:** Спочатку йду на зупинку. Потім їду автобусом до центру. *(First I walk to the stop. Then I ride the bus to the center.)*
> **Олена:** А потім? *(And then?)*
> **Тарас:** Потім іду пішки п'ять хвилин. Робота в офісі на площі. *(Then I walk five minutes. Work is in an office on the square.)*

Tарас uses sequence words to structure his route: **спочатку** (first) → **потім** (then) → **а потім** (and then). This is how Ukrainians naturally describe any multi-step journey. Notice the transport contrast: **їду автобусом** (I ride by bus — instrumental case, taught as a chunk) versus **іду пішки** (I walk — literally "go on foot"). The destination uses accusative: **на зупинку** (to the stop), **до центру** (to the center). His current location uses locative: **в офісі** (in the office), **на площі** (on the square).

<!-- INJECT_ACTIVITY: fill-in-directions -->

## Де і куди разом (Where and Where To Together)

Real Ukrainian navigation constantly switches between two questions. When you say where you are, you use **де?** with locative case. When you say where you are heading, you use **куди?** with accusative case. A single journey might alternate between these several times:

- **Я зараз у парку.** (I'm in the park now.) — де? → locative: у парку
- **Я йду в магазин.** (I'm going to the store.) — куди? → accusative: в магазин
- **Магазин на вулиці Шевченка.** (The store is on Shevchenko Street.) — де? → locative: на вулиці
- **Потім їду на роботу.** (Then I ride to work.) — куди? → accusative: на роботу

The pattern is consistent: **question → preposition → case**. Static location = locative. Motion toward = accusative.

Here is the full navigation toolkit in one table:

| Ситуація | Питання | Форма | Приклад |
|---|---|---|---|
| Static location | Де? | в/на + locative | Я в офісі. На площі. |
| Motion toward | Куди? | в/на + accusative | Іду в театр. На роботу. |
| Transport mode | Як? Чим? | автобусом / на метро / пішки | Їду автобусом. |
| Distance | Далеко? | далеко / близько / хвилин пішки | П'ять хвилин пішки. |

:::tip
Streets, avenues, and squares always use **на**: **на вулиці Франка**, **на площі**, **на проспекті**. Buildings you enter use **в/у**: **в магазині**, **в офісі**, **у театрі**. Metro always stays with **на**: **на метро** — both for location and transport.
:::

Now see how all four rows work together in connected speech. **Марія** lives in Lviv and is heading to the theater:

**Марія живе у Львові** (де? — locative). **Сьогодні вона йде в театр** (куди? — accusative). **Театр на площі** (де? — locative). **Потім вона їде на метро до центру** (куди? — accusative). **Центр далеко** — п'ять хвилин на метро, а потім **іде пішки** три хвилини. The question type shifts six times in this short passage — and that is completely natural.

<!-- INJECT_ACTIVITY: quiz-de-kudy -->

## Мій район (My Neighborhood)

Every learner needs to describe where they live. Here is a model paragraph you can adapt with your own details:

**Я живу на вулиці Франка.** **Біля мого дому є парк і маленький магазин.** **Школа далеко** — треба їхати автобусом десять хвилин. **Аптека близько**, можна піти **пішки**. **У моєму районі є кафе, два ресторани і бібліотека.**

Key structures to notice: **біля мого дому** (near my house) is a genitive chunk — learn it as a fixed unit. The construction **є** + noun list means "there is / there are." Two modal chunks appear: **треба їхати** (must go by vehicle) and **можна піти** (can go on foot).

Now put the required vocabulary into full sentences:

- **пішки** (on foot) → Аптека близько — іду **пішки**.
- **хвилина** (minute) → П'ять **хвилин** пішки від зупинки.
- **далеко від** / **близько від** (far from / near) → Школа **далеко від** дому. Парк **близько від** роботи.
- **у центрі міста** (in the city center) → Готель **у центрі міста**.
- **на околиці** (on the outskirts) → Я живу **на околиці**, не в центрі.

:::note
The chunks **далеко від** and **близько від** are followed by genitive case. At this stage, memorize them as fixed phrases with common nouns: далеко від дому, близько від роботи, далеко від зупинки.
:::

Now try building your own description using these sentence frames:

1. **Я живу** [де — вулиця / місто]. **Біля мого дому є** [що].
2. [Місце] [далеко / близько]. **Треба їхати** [чим] / **Можна піти пішки.**
3. **У моєму районі є** [list 3 places].

Three example outputs for different situations:

- City center: **Я живу на вулиці Хрещатик. Біля мого дому є метро. Парк близько — п'ять хвилин пішки. У моєму районі є театр, музей і кафе.**
- Suburb: **Я живу на околиці. Біля мого дому є зупинка. Центр далеко — треба їхати автобусом. У моєму районі є школа, магазин і аптека.**
- Small town: **Я живу у маленькому місті. Біля мого дому є парк. Магазин близько — три хвилини пішки. У моєму районі є бібліотека, кафе і школа.**

The sentence frames stay identical — only the details change.

<!-- INJECT_ACTIVITY: fill-in-transport -->

## Підсумок — Summary

Here is your urban communication toolkit — a reference card for navigating any Ukrainian city:

**Запитати дорогу** (asking for directions):
- Вибачте, як дістатися до [місця]?
- Де знаходиться [місце]?

**Напрямок** (direction):
- **прямо** (straight) → **направо** (right) → **наліво** (left) → **на розі** (at the corner)

**Де?** (locative — static):
- в/на + locative: **у парку**, **в театрі**, **на вулиці**, **на площі**

**Куди?** (accusative — motion):
- в/на + accusative: **у парк**, **в театр**, **на вулицю**, **на площу**

**Транспорт** (transport):
- **автобусом** / **на метро** / **пішки** — П'ять **хвилин** пішки.

### Self-Check

Answer these five prompts mentally or aloud, then check your answers:

1. You are standing on a street. A stranger asks how to get to the library. The library: straight, then left. What do you say? — *Ідіть прямо, потім наліво. Бібліотека там.*

2. Describe your morning route in three sentences using **спочатку... потім... а потім...** — *(Free production — use your real route.)*

3. Choose the correct form: Я зараз — **в театрі** чи **в театр**? Я йду — **в театрі** чи **в театр**? — *В театрі (static, де?) / В театр (motion, куди?).*

4. How do you say "five minutes on foot"? — *П'ять хвилин пішки.*

5. Where do you live? What is near your house? Say it in two sentences. — *(Free production using Я живу на... Біля мого дому є...)*

<!-- INJECT_ACTIVITY: match-navigation -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: around-the-city
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

**Level: A1.4+ (Module 33/55) — BEGINNER**

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
