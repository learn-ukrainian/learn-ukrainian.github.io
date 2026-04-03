<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-my-world.yaml` file for module **14: Checkpoint: My World** (a1).

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

- `<!-- INJECT_ACTIVITY: group-sort-vocab-categories -->`
- `<!-- INJECT_ACTIVITY: quiz-gender-agreement -->`
- `<!-- INJECT_ACTIVITY: quiz-singular-plural -->`
- `<!-- INJECT_ACTIVITY: fill-in-shopping-dialogue -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Mixed gender/agreement review: choose correct form for noun+adjective pairs'
  items: 10
  type: quiz
- focus: Complete the shopping dialogue with correct demonstratives, adjectives, and
    numbers
  items: 8
  type: fill-in
- focus: 'Sort vocabulary from M08-M13 by category: objects, colors, numbers'
  items: 12
  type: group-sort
- focus: Singular or plural? Transform sentences from singular to plural
  items: 8
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended: []
required: []


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Що ми знаємо? (What Do We Know?)

You have spent six modules building your Ukrainian world — objects, colors, numbers, and more. This module introduces nothing new. No new grammar, no new vocabulary. Instead, it activates everything from M08 through M13 and tests whether it has settled into your memory. Six skills to check: noun gender, adjective agreement, colors (including both blues), numbers and prices, demonstratives, and plurals. The format is simple: self-check questions first, then a reading passage, a grammar reference, and finally a full dialogue that puts it all together.

How many of these can you answer without looking back?

- **Gender:** Is **стіл** (table) він, вона, or воно?
- **Agreement:** Which is correct — **великий стіл** or **велика стіл**?
- **Colors:** What is the difference between **синій** (dark blue) and **блакитний** (sky blue)?
- **Numbers:** How do you say "fifty hryvnias" — **п'ятдесят гривень**?
- **Demonstratives:** Do you say **цей вишиванка** or **ця вишиванка** (this embroidered shirt)?
- **Plurals:** What is the plural of **книга** (book)?

If all six feel familiar, you are ready for the dialogue at the end. If even one feels shaky, the grammar summary below will set it straight.

<!-- INJECT_ACTIVITY: group-sort-vocab-categories -->

## Читання (Reading Practice)

Read the text below aloud — at least twice. Every word comes from M08–M13. There is nothing new here. Focus on reading naturally and noticing how gender, agreement, and demonstratives appear together in real sentences.

:::note
Reading aloud is essential. Your mouth needs to practice the shapes of Ukrainian words just as much as your eyes need to recognize them.
:::

> Це моя кімната. Мій стіл великий і коричневий. На столі є лампа. Ця лампа біла. А та лампа жовта — вона стоїть у кутку. У мене є три книги. Ці книги нові й цікаві. На стіні висить картина. Картина синя й зелена. Вікно велике, а двері маленькі. Моя кімната гарна!

*(This is my room. My table is big and brown. On the table there is a lamp. This lamp is white. And that lamp is yellow — it stands in the corner. I have three books. These books are new and interesting. On the wall hangs a painting. The painting is blue and green. The window is big, and the door is small. My room is nice!)*

Notice the patterns at work. **Стіл** (table) is masculine — so its adjective is **великий** (big), with the masculine ending **-ий**. **Лампа** (lamp) is feminine — so it gets **біла** (white), with **-а**. **Вікно** (window) is neuter — so its adjective is **велике** (big), with **-е**. The demonstratives follow the same logic: **ця лампа** (this lamp, feminine) vs. **ці книги** (these books, plural). And the number **три** sits naturally before **книги** (books) without any special changes.

Now answer these three questions by pointing back to the text:

- **Який стіл?** *(What is the table like?)*
- **Скільки книг у кімнаті?** *(How many books are in the room?)*
- **Яка лампа в кутку — біла чи жовта?** *(Which lamp is in the corner — white or yellow?)*

## Граматика (Grammar Summary)

Five key patterns from A1.2, presented as a quick reference. This is not new instruction — it is a map of what you already know. Each pattern has one rule and examples to confirm your understanding.

**Pattern 1 — Noun gender** (the він/вона/воно test): consonant ending → він (**стіл**, **глечик**, **зошит**). Ending **-а/-я** → вона (**книга**, **вишиванка**, **земля**). Ending **-о/-е** → воно (**вікно**, **намисто**).

**Pattern 2 — Adjective agreement:** the adjective ending mirrors the noun gender. **Великий стіл** (big table, m), **велика книга** (big book, f), **велике вікно** (big window, n). The adjective always matches.

:::tip
Ukrainian textbooks teach: «Прикметник завжди стоїть у тому числі, роді та відмінку, що й іменник.» The adjective always takes the same number, gender, and case as its noun.
:::

**Pattern 3 — Hard vs. soft adjective stems:** hard-stem adjectives end in **-ий/-а/-е**: **червоний** (red), **червона**, **червоне**. Soft-stem adjectives end in **-ій/-я/-є**: **синій** (dark blue), **синя**, **синє**. This is why **блакитний** (sky blue) takes **-ий** (hard stem) while **синій** takes **-ій** (soft stem) — different base consonants.

**Pattern 4 — Demonstratives:** **цей глечик** (this jug, m), **ця вишиванка** (this embroidered shirt, f), **це намисто** (this necklace, n) for things nearby. **Той/та/те** for things farther away. Gender agreement works exactly like adjectives.

**Pattern 5 — Nominative plurals:** masculine: **столи**, **глечики**; feminine: **книги**, **вишиванки**; neuter: **вікна**, **намиста**. The adjective plural is always **-і**, regardless of gender — **нові столи**, **нові книги**, **нові вікна**.

**Pattern 6 — Numbers as vocabulary:** **один** (1), **два** (2), **три** (3), **десять** (10), **двадцять** (20), **п'ятдесят** (50), **сто** (100), **двісті** (200). At this stage, use them as fixed words — no case changes needed.

These patterns all appear together in natural speech. The next section shows them working in a real conversation.

<!-- INJECT_ACTIVITY: quiz-gender-agreement -->

<!-- INJECT_ACTIVITY: quiz-singular-plural -->

## Діалог (Connected Dialogue)

Іванко is a tourist visiting Ukraine for the first time. His friend **Катя** (Katia) takes him to a **ярмарок** (street market) — an open-air market selling handmade crafts. The stalls are full of **вишиванки** (embroidered shirts, f), **глечики** (clay jugs, m), **намисто** (necklaces, n), and **писанки** (decorated eggs, pl). This is the perfect setting to use every A1.2 skill at once: pointing at objects, describing colors and sizes, asking prices, and talking about quantities.

> **Іванко:** Катю, дивись! Що це таке? *(Katia, look! What is this?)*
> **Катя:** Це вишиванка. Гарна, правда? *(This is an embroidered shirt. Beautiful, right?)*
> **Іванко:** Дуже! Яка вона — біла чи синя? *(Very! What color is it — white or blue?)*
> **Катя:** Та біла. А ця — синя й червона. *(That one is white. And this one is blue and red.)*
> **Іванко:** Скільки коштує ця синя вишиванка? *(How much does this blue embroidered shirt cost?)*
> **Катя:** Вона коштує чотириста гривень. *(It costs four hundred hryvnias.)*
> **Іванко:** А той глечик? Він великий чи маленький? *(And that jug? Is it big or small?)*
> **Катя:** Той — великий. Цей — маленький. *(That one is big. This one is small.)*
> **Іванко:** Один глечик. Маленький. Скільки він коштує? *(One jug. The small one. How much does it cost?)*
> **Катя:** Сто п'ятдесят гривень. *(One hundred fifty hryvnias.)*
> **Іванко:** Добре. А це що — намисто? *(Good. And what is this — a necklace?)*
> **Катя:** Так! Це червоне намисто. Гарне, правда? *(Yes! This is a red necklace. Beautiful, right?)*
> **Іванко:** Дуже гарне. А писанки? Скільки коштує одна писанка? *(Very beautiful. And the decorated eggs? How much does one decorated egg cost?)*
> **Катя:** Двадцять п'ять гривень. Хочеш три? *(Twenty-five hryvnias. Want three?)*
> **Іванко:** Так, три писанки, будь ласка! *(Yes, three decorated eggs, please!)*

Every A1.2 pattern appears in this dialogue. The demonstratives show gender agreement: **ця** синя вишиванка (f), **той** глечик (m), **це** намисто (n). Adjectives match their nouns: **синя вишиванка**, **великий глечик**, **червоне намисто**. Numbers combine with nouns naturally: **три писанки**, **один глечик**. And the price pattern **Скільки коштує?** + amount + **гривень** runs through the whole scene.

:::caution
**Ця** vs. **та** — both mean "this/that" but signal distance. Катя uses **ця** (this one, near me) for what she is holding and **та** (that one, over there) for what is farther away. This is not random — it mirrors the physical space of the market.
:::

Ukrainian markets — **ярмарки** — are where craft culture lives. **Вишиванка** (the embroidered shirt) is the most recognizable symbol of Ukrainian identity — worn at celebrations, protests, and everyday life. **Писанки** (decorated eggs) are an ancient tradition stretching back to the Trypillian era, thousands of years before they became associated with Easter. **Глечик** (a clay jug) is a traditional household object found in every Ukrainian home for centuries. When you use Ukrainian words for these objects, you are connecting to something much older than grammar rules.

<!-- INJECT_ACTIVITY: fill-in-shopping-dialogue -->

## Підсумок — Summary

By completing A1.2, you can now do five things in Ukrainian. First, you can identify the gender of a noun and test it with **він/вона/воно**. Second, you can describe objects with adjectives in the correct form — **новий стіл** (new table), **нова книга** (new book), **нове вікно** (new window). Third, you can point at things near and far — **цей**, **ця**, **це** vs. **той**, **та**, **те**. Fourth, you can count and talk about prices — **один**, **два**, **сто**, **двісті гривень** (two hundred hryvnias). Fifth, you can talk about groups of things — **столи**, **книги**, **вікна**, all with the adjective plural ending **-і**. This is your world in Ukrainian.

Your vocabulary milestone is real. You now know 20+ Ukrainian nouns with their genders, 10+ adjectives that you can inflect for gender, both Ukrainian words for blue — **синій** (saturated, dark blue) and **блакитний** (sky blue, light blue) — and a working set of numbers for prices. These words cover your physical world: furniture, clothing, objects, colors, quantities. A Ukrainian speaker could understand you when you describe a room, a market stall, or a price tag.

:::tip
Two blues, not one. English has "blue" for everything. Ukrainian distinguishes **синій** (the deep blue of the sea or a dark shirt) from **блакитний** (the pale blue of the sky). Both are basic color terms — neither is optional.
:::

So far, A1.2 has been about things: objects, their appearance, their price, their number. A1.3 shifts to actions — what people do, what they like, what they want. The next module (M15: What I Like) introduces Ukrainian verbs for the first time. The same careful, step-by-step approach applies. You will discover how Ukrainian verbs work through real situations, not grammar tables.

**Ти вже вмієш говорити про свій світ українською.** *(You can already talk about your world in Ukrainian.)* This is real. You proved it in the dialogue above.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-my-world
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

**Level: A1.2-A1.3 (Module 14/55) — EARLY BEGINNER**

The learner knows the alphabet and ~200 words. They:
- Can read Ukrainian slowly
- Know basic nouns, adjectives, simple verb forms
- Cannot handle complex sentences or grammar terminology in Ukrainian

**Instructions in simple English with Ukrainian key terms in bold.**
Example: 'Choose the correct form of **мій/моя/моє**'

**Good activity types:** quiz, fill-in (simple sentences), match-up, group-sort, true-false, observe, anagram, translate (English→Ukrainian), error-correction (simple), divide-words, count-syllables, odd-one-out, order.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-gender [§4.2.1.1, §4.2.2]
**Рід іменників** (Noun gender)
- **group-sort** — Він, вона чи воно?: Розподілити іменники за граматичним родом за закінченням / Sort nouns by grammatical gender using ending rules
  - Instruction: *Розподіліть слова за родами*
- **quiz** — Який рід?: Визначити рід за закінченням: приголосний=чол., -а/-я=жін., -о/-е=серед. / Determine gender from ending — consonant=masc, -а/-я=fem, -о/-е=neut
- **fill-in** — Мій, моя чи моє?: Обрати присвійний займенник, що узгоджується з родом іменника / Choose possessive that matches noun gender
  - Instruction: *Вставте правильне слово*
- **match-up** — Іменник + займенник: Зіставити іменники з він/вона/воно / Match nouns to він/вона/воно
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: На рівні A1 завжди давати варіанти для вибору

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

### Pattern: grammar-numbers [§4.2.1.3]
**Числівники** (Numerals)
- **quiz** — Яке число?: Розпізнати числівники, записані словами / Recognize written number words
- **fill-in** — Напиши цифру словом: Записати числівник словом по-українськи / Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Зіставити цифри з їхніми українськими назвами / Match digits to their Ukrainian word forms
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Числівники складні для написання — давати варіанти на A1

### Pattern: grammar-pronouns [§4.2.1.4, §4.2.2]
**Особові займенники** (Personal pronouns)
- **match-up** — Займенник → дієслово: Зіставити особовий займенник із правильною формою дієслова — зв'язок займенника з дієвідмінюванням / Match personal pronoun with correct verb form — linking pronouns to conjugation
  - Instruction: *З'єднайте займенник із дієсловом*
- **fill-in** — Вставте займенник: Обрати правильний займенник за контекстом речення / Choose the correct pronoun based on sentence context
  - Instruction: *Вставте правильний займенник*
- **group-sort** — Однина чи множина?: Розподілити займенники на однину та множину / Sort pronouns into singular and plural
  - Instruction: *Розподіліть*
- **quiz** — Ти чи Ви?: Обрати правильну форму звертання — неформальне (ти) чи ввічливе (Ви) / Choose correct address form — informal (ти) vs polite (Ви)
**Anti-patterns (DO NOT generate):**
- ❌ translate: Займенники — про зв'язок з дієсловом, а не переклад

### Pattern: grammar-pluralization [§4.2.1.1]
**Множина іменників** (Noun plurals)
- **fill-in** — Утвори множину: Утворити множину іменника — закінчення -и vs -і залежно від приголосного / Form noun plural — -и vs -і endings depending on consonant
  - Instruction: *Напишіть множину*
- **group-sort** — Закінчення -и чи -і?: Розподілити іменники за типом закінчення множини / Sort nouns by plural ending type
  - Instruction: *Розподіліть*
- **match-up** — Однина → множина: Зіставити форму однини з формою множини / Match singular form to plural form
  - Instruction: *З'єднайте*
- **error-correction** — Виправ множину: Знайти неправильну форму множини та виправити / Find incorrect plural form and fix it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Множина — це словотворення. Учні мають продукувати форми, а не тільки вибирати
- ❌ fill-in-no-options: На A1 завжди давати варіанти — учень ще не знає всіх закінчень

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options

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
