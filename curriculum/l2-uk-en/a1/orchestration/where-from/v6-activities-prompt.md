<!-- version: 1.1.0 | updated: 2026-03-31 -->
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

- `<!-- INJECT_ACTIVITY: answer-zvidky -->`
- `<!-- INJECT_ACTIVITY: location-trio-sort -->`
- `<!-- INJECT_ACTIVITY: preposition-quiz -->`
- `<!-- INJECT_ACTIVITY: location-contrast -->`

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
## Діалоги — Dialogues

An international student mixer at a university in Kyiv is the perfect place to hear a symphony of languages and accents. When people from different backgrounds gather in one room, the most natural icebreaker is finding out where everyone comes from. In Ukrainian, asking about someone's origin is a direct, essential communicative skill. You will hear the question **Звідки ти?** (Where are you from?) echoing across the room as students connect, share their stories, and learn about each other's homes. The ability to state your origin confidently is your passport to deeper conversations. 

> **Джон:** Звідки ти? *(Where are you from?)*
> **Максим:** Я з України, з Києва. А ти? *(I am from Ukraine, from Kyiv. And you?)*
> **Джон:** Я з Канади, із Торонто. *(I am from Canada, from Toronto.)*
> **Максим:** Давно тут? *(Have you been here long?)*
> **Джон:** Ні, я приїхав місяць тому. *(No, I arrived a month ago.)*

The core interaction for stating your origin revolves around the question **Звідки ти?** (Where are you from?). Notice how the response is constructed: **Я з...** (I am from...). In Ukrainian, the present tense verb for "to be" is almost always omitted in these standard phrases. You do not need to say "I am," you simply state your pronoun, the preposition, and the place. The structure **Я з України** (I am from Ukraine) is a complete, grammatically correct sentence that you can use immediately. When talking about a specific city, you simply add it to the phrase, such as **Я з України, з Києва** (I am from Ukraine, from Kyiv).

> **Анна:** Звідки ти йдеш? *(Where are you coming from?)*
> **Марко:** Я йду з роботи. *(I am coming from work.)*
> **Анна:** А Олена? *(And Olena?)*
> **Марко:** Вона йде зі школи. *(She is coming from school.)*
> **Анна:** Куди вона йде? *(Where is she going?)*
> **Марко:** Додому. *(Home.)*

This second conversation highlights a shorter exchange about physical movement. We are contrasting the origin point — coming from work or from school — with the destination. You use the exact same preposition to describe walking away from a building as you do when stating the country you were born in.

## Звідки? — Where From?

Ukrainian categorizes spatial relations and movement into three distinct, logical questions: **Де?** (Where are you?), **Куди?** (Where are you going?), and **Звідки?** (Where are you from?). Think of this as the "Location Trio." If we take a country like **Україна** (Ukraine), it changes its shape depending on which of the three questions you are answering. At this A1 level, you will learn to use these combinations as memorized chunks, while the full grammatical rules of the genitive case will be covered in A2.

*   **Де ти? — В Україні.** (Where are you? — In Ukraine.) This uses the locative case to show exactly where you ARE.
*   **Куди ти їдеш? — В Україну.** (Where are you traveling to? — To Ukraine.) This uses the accusative case to show where you are GOING.
*   **Звідки ти? — З України.** (Where are you from? — From Ukraine.) This is a genitive chunk, showing the point where you are FROM.

To express this origin, you need a preposition. Just as you learned in Module 28, Ukrainian applies euphony rules to make speech flow smoothly. The basic preposition for "from" is **з**, and you will use it before most vowels and consonants, like **з Канади** (from Canada). If the next word starts with a sibilant sound (like s, sh, or z), you switch to **із** for easier pronunciation, as in **із США** (from the USA). For specific difficult consonant clusters, especially those starting with z, s, or sh, you use **зі**, which is why we say **зі Львова** (from Lviv).

:::note
You do not need to memorize complex euphony rules for **з**, **із**, and **зі** right now. Focus on learning the correct combinations as single blocks of vocabulary, like **зі США** (from the USA).
:::

When you use this preposition, the noun that follows it must change its ending. Feminine nouns ending in **-а** change to **-и**: **Україна** becomes **з України**, **Канада** becomes **з Канади**, and **Одеса** becomes **з Одеси**. Feminine nouns ending in **-я** change to **-ї**: **Англія** becomes **з Англії**. Masculine place names ending in a consonant usually add an **-а**: **Київ** becomes **з Києва**, and **Харків** becomes **з Харкова**. These predictable patterns allow you to comfortably form the origin phrase for most common locations without needing to memorize a complex table.

:::caution
English relies heavily on the verb "to be" to express location, but Ukrainian relies on prepositions and case endings. Never say **Я в України** to mean "I am from Ukraine" — always use **з** for your origin.
:::

<!-- INJECT_ACTIVITY: answer-zvidky -->

The question **Звідки?** is used for much more than just international geography. You will use it constantly in your daily life to explain your routine movements. The same exact pattern applies to everyday locations in your city. When you finish your shift, you are walking **з роботи** (from work). After buying groceries, you are coming **з магазину** (from the store). When you finish your financial tasks, you step out **з банку** (from the bank). And when classes end, a student walks **зі школи** (from school).

<!-- INJECT_ACTIVITY: location-trio-sort -->

## Країни і міста — Countries and Cities

Major Ukrainian cities provide excellent practice for forming these origin phrases. The capital city is **Київ** (Kyiv), so you would say **з Києва** (from Kyiv). The cultural hub of the west is **Львів** (Lviv), which becomes **зі Львова** (from Lviv). The southern port is **Одеса** (Odesa), forming **з Одеси** (from Odesa). In the east, we have **Харків** (Kharkiv), which changes to **з Харкова** (from Kharkiv). The central city of **Дніпро** (Dnipro) becomes **з Дніпра** (from Dnipro), and the southeastern industrial center **Запоріжжя** (Zaporizhzhia) becomes **із Запоріжжя** (from Zaporizhzhia).

:::tip
The name **Україна** historically means "land," "region," or "our country." It is not a "borderland," as Russian imperialist myths have tried to claim. And its capital, **Київ**, has always been the historical heart of this land.
:::

When interacting in international environments, you will also need to recognize common country names. If someone asks where you are from, you might need to say you are from Canada: **Канада** (Canada) becomes **з Канади** (from Canada). The United States is usually abbreviated, giving us **зі США** (from the USA) or occasionally **зі Штатів** (from the States). Other frequent European nations include **Англія** (England), which forms **з Англії** (from England), and **Німеччина** (Germany), which becomes **з Німеччини** (from Germany). You might also meet people from neighboring **Польща** (Poland), saying **з Польщі** (from Poland), or from further away like **Франція** (France), making **із Франції** (from France), **Італія** (Italy), making **з Італії** (from Italy), and **Японія** (Japan), which changes to **з Японії** (from Japan).

Your origin is deeply connected to your identity and the language you speak. We can review concepts from Module 05 and link them to the new origin pattern. Notice how these phrases flow together in a logical sequence.

*   **Мене звати Петро.** (My name is Petro.)
*   **Я з України.** (I am from Ukraine.)
*   **Я українець.** (I am a Ukrainian man.)
*   **Я говорю українською.** (I speak Ukrainian.)

We can contrast this with someone from a different background:

*   **Мене звати Джон.** (My name is John.)
*   **Я з Англії.** (I am from England.)
*   **Я англієць.** (I am an Englishman.)
*   **Я говорю англійською.** (I speak English.)

<!-- INJECT_ACTIVITY: preposition-quiz -->

Often, where you are from is not where you are right now. You can combine your origin and your current location in a single sentence to tell a richer story about yourself. To do this, use the conjunction **але** (but) and the adverb **зараз** (now). This is an excellent way to practice both the "from" pattern and the "in" pattern together. 

*   **Я живу в Києві, але я зі Львова.** (I live in Kyiv, but I am from Lviv.)
*   **Вона з Канади, але зараз вона живе в Україні.** (She is from Canada, but now she lives in Ukraine.)

<!-- INJECT_ACTIVITY: location-contrast -->

## Підсумок — Summary

You now have a complete, functional system for describing spatial relations and movement in Ukrainian. A review of the three core questions will solidify this system. 

When you want to express a static location, you ask **Де?** (Where?). The answer usually requires the prepositions **в** or **на** and the locative case, such as **в Україні** (in Ukraine). 

When you want to talk about a destination, you ask **Куди?** (Where to?). The answer also uses **в** or **на** but with the accusative case, such as **в Україну** (to Ukraine). 

Finally, when you are talking about an origin, you ask **Звідки?** (Where from?). The answer requires the prepositions **з**, **із**, or **зі** plus a genitive chunk, like **з України** (from Ukraine).

Here is a summary of the most frequent city and country changes you learned in this module:
*   **Україна** → **з України**
*   **Канада** → **з Канади**
*   **Німеччина** → **з Німеччини**
*   **Київ** → **з Києва**
*   **Львів** → **зі Львова**
*   **Харків** → **з Харкова**

To ensure you have mastered these concepts, try to answer the following self-check questions out loud. Use your own real-world information where possible.

*   **Звідки ти?** (Where are you from?) → **Я з...**
*   **Звідки твій друг?** (Where is your male friend from?) → **Він з...**
*   **Звідки твоя подруга?** (Where is your female friend from?) → **Вона з...**
*   **Ти зараз у Києві чи у Львові?** (Are you in Kyiv or in Lviv right now?) → **Я зараз у...**
*   **Звідки ти йдеш зараз?** (Where are you coming from right now?) → **Я йду з...**
*   **Де ти живеш?** (Where do you live now?) → **Я живу в...**
*   **Куди ти йдеш після уроку?** (Where are you going after this lesson?) → **Я йду в/на...**

By mastering the question **Звідки?**, you have unlocked the final piece of the basic location puzzle. You can now confidently describe where you are, where you are heading, and where you came from. In the next module, Checkpoint — Places, you will review and consolidate all of this spatial vocabulary before moving on to new topics.

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

  - type: order
    instruction: "Розставте речення в правильному порядку"
    items:                         # Lines displayed SHUFFLED to the learner
      - "— Служба порятунку, слухаю вас."
      - "— Допоможіть! Тут пожежа!"
      - "— Де ви?"
    correct_order: [0, 1, 2]       # TOP-LEVEL field, zero-based indices into items[]

  - type: unjumble
    instruction: "Складіть правильне речення зі слів"
    items:
      - words: ["швидку!", "Викличте"]            # Jumbled words
        correct_order: ["Викличте", "швидку!"]    # Words as STRINGS in correct order (NOT integers!)
      - words: ["потрібен", "Мені", "лікар."]
        correct_order: ["Мені", "потрібен", "лікар."]
        hint: "Dative + потрібен + noun"

  - type: error-correction
    instruction: "Знайдіть і виправте помилку"
    items:
      - sentence: "Мені потрібна лікар."
        error: "потрібна"
        correction: "потрібен"
        error_type: "word"           # MUST be one of: "word", "phrase", "register", "construction"
        options: ["потрібен", "потрібне", "потрібно"]
        explanation: "Лікар is masculine, so потрібен."
```

---

## Activity Type Reference

**CRITICAL RULE: EVERY single activity object MUST include an `id` field (a unique string like "quiz-grammar", "match-up-vocab"). Do NOT generate an activity without an `id`.**

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: id, instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: id, instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: id, instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: id, instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: id, instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: id, instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: id, instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: id, instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: id, examples[], prompt
- **classify**: Multi-category sort. Required: id, instruction, categories[{label, items[]}]

### Ukrainian pedagogy types (A1 phonetics/syllables):
- **divide-words**: Interactive syllable division. Required: id, instruction, items[{word, answer}]. Optional: hint. Example: word: "молоко", answer: "мо-ло-ко"
- **count-syllables**: Count syllables in a word. Required: id, items[{word, correct}]. Optional: instruction, maxCount, translation. Example: word: "яблуко", correct: 3
- **pick-syllables**: Select syllables matching criteria. Required: id, syllables[], correctIndices[], category. Example: syllables: ["ка", "май", "ре"], correctIndices: [1], category: "закриті"
- **odd-one-out**: Find the word that doesn't belong. Required: id, items[{words[], correct, explanation}]. `correct` is 0-based index. Example: words: ["кіт", "пес", "молоко"], correct: 2, explanation: "молоко — 3 syllables, rest have 1"
- **image-to-letter**: See image/emoji, identify letter. Required: id, instruction, items[{image, letter}]. Optional: options[]
- **letter-grid**: Letter reference grid. Required: id, letters[{upper, lower}]. Optional: name, emoji, key_word, sound_type
- **watch-and-repeat**: Watch video, repeat pronunciation. Required: id, items[{video}]. Optional: letter, word, note
- **phrase-table**: Grouped phrases for communication patterns. Required: id, groups[{label, phrases[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: id, prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Required: id, passage, questions[]
- **source-evaluation**: Required: id, source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A1.4+ (Module 34/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

### Pattern: grammar-cases [§4.2.3.1, §4.2.3.2, §4.2.3.3]
**Відмінки іменників** (Noun cases)
- **fill-in** — Який відмінок?: Вставити іменник у правильній відмінковій формі / Fill in the correct case ending for a noun in context
  - Instruction: *Вставте іменник у правильній формі*
- **quiz** — Визнач відмінок: Визначити, у якому відмінку стоїть виділений іменник / Identify which case a highlighted noun is in
- **group-sort** — Розподіли за відмінками: Розподілити форми іменників за відмінками / Sort noun forms by their case
- **error-correction** — Знайди помилку у відмінку: Знайти неправильне відмінкове закінчення та виправити / Find wrong case ending and correct it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Учні мають ПРОДУКУВАТИ форми, а не тільки розпізнавати. Обов'язково fill-in
- ❌ translate: Англійська не має відмінків — переклад не тестує відмінювання

### Pattern: general-reading [§1 (Speech activities — reading)]
**Розуміння тексту** (Reading comprehension)
- **true-false** — Правда чи ні?: Перевірити розуміння тексту або діалогу / Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Відповісти на запитання за текстом / Answer questions about a text passage


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Default minimum: 6 items per activity.** Quiz = 6+, fill-in = 6+, match-up = 6+ pairs, true-false = 6+, anagram = 6+, error-correction = 6+, translate = 6+, divide-words = 6+, count-syllables = 6+, odd-one-out = 6+.
- **Lower minimums for specific types:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items.
- If you can't think of enough items, add more examples from the module's vocabulary and content.
- **Exactly 4 options per quiz question at A2+** — enough to prevent guessing, not so many to overwhelm. A1 allows 3-4.
- **BINARY CONCEPTS (e.g., НВ/ДВ, masculine/feminine, true/false):** Do NOT use `quiz` with only 2 options — use `true-false` (for statement evaluation) or `group-sort` (for categorization) instead. Quiz type requires 4 options at A2+.

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
- `mcp_rag_verify_words` / `mcp_rag_verify_word` / `mcp_rag_verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp_rag_search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp_rag_search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp_rag_query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp_rag_query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp_rag_search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp_rag_query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp_rag_search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp_rag_search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp_rag_search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp_rag_search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp_rag_translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp_rag_query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp_rag_query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp_rag_search_style_guide` first (it knows calques). Then `mcp_rag_query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp_rag_verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp_rag_query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp_rag_verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp_rag_search_idioms` for Ukrainian expressions, `mcp_rag_search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp_rag_query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp_rag_query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp_rag_verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp_rag_verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp_rag_verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp_rag_query_pravopys` or `mcp_rag_search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp_rag_verify_words` with 5-15 words at once.
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
