<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/things-have-gender.yaml` file for module **8: Things Have Gender** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-pronoun-choice -->`
- `<!-- INJECT_ACTIVITY: quiz-gender-endings -->`
- `<!-- INJECT_ACTIVITY: group-sort-gender -->`
- `<!-- INJECT_ACTIVITY: fill-in-possessives -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Sort objects into masculine/feminine/neuter
  items: 12
  type: group-sort
- focus: він, вона, or воно? Choose for each noun.
  items: 8
  type: quiz
- focus: мій/моя/моє ___ (match possessive to noun)
  items: 8
  type: fill-in
- focus: What gender? Look at the ending.
  items: 6
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- зошит (notebook, m)
- ручка (pen, f)
- сумка (bag, f)
- крісло (armchair, n)
- дзеркало (mirror, n)
- ключ (key, m)
- фото (photo, n)
- стіна (wall, f)
required:
- стіл (table, m)
- книга (book, f)
- вікно (window, n)
- кімната (room, f)
- ліжко (bed, n)
- стілець (chair, m)
- лампа (lamp, f)
- телефон (phone, m)
- комп'ютер (computer, m)
- він, вона, воно (he, she, it — gender test words)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги — Dialogues

Imagine walking into a pet shop. You are looking at the different animals and the items they need. In English, unless you know the specific sex of an animal, you refer to it as an "it." The basket it sleeps in is definitely an "it." In Ukrainian, this perspective shifts entirely. Every single noun, whether it is a living breathing creature or a woven basket, has a specific grammatical gender. It is either masculine, feminine, or neuter. Observe a conversation between two friends to see how this works in practice.

> **Марія:** Дивись, **кіт** (cat)! *(Look, a cat!)*
> **Оленка:** Так, **він** (he) спить. Тут **кошик** (basket). *(Yes, he is sleeping. Here is a basket.)*
> **Марія:** Кошик — він. *(A basket is a "he".)*
> **Оленка:** А там моя улюблена **рибка** (fish). **Вона** (she) плаває. *(And there is my favorite fish. She is swimming.)*
> **Марія:** Великий **акваріум** (aquarium)! Він дуже гарний. *(A big aquarium! He is very beautiful.)*
> **Оленка:** О, дивись! **Черепаха** (turtle). Вона тут. *(Oh, look! A turtle. She is here.)*
> **Марія:** Маленьке **кошеня** (kitten)! **Воно** (it) теж тут. *(A little kitten! It is also here.)*
> **Оленка:** І велике **дзеркало** (mirror). Воно там. *(And a big mirror. It is there.)*

Notice how Марія and Оленка talk about the animals and objects. The word **кіт** is masculine, so they use the pronoun **він**. The basket, **кошик**, is also masculine, so it is also a "he." The **рибка** and the **черепаха** are feminine, referred to as **вона**. The mirror, **дзеркало**, and the little **кошеня** are neuter, using **воно**.

Now consider a different situation. You are on a video call with a friend, showing them your room. The furniture around you also follows these strict rules of grammatical gender.

> **Олег:** Привіт! Дивись, це моя **кімната** (room). *(Hi! Look, this is my room.)*
> **Анна:** Класно! У тебе є **стіл** (table)? *(Cool! Do you have a table?)*
> **Олег:** Так, у мене є стіл. Це мій стіл. *(Yes, I have a table. This is my table.)*
> **Анна:** А де **ліжко** (bed)? *(And where is the bed?)*
> **Олег:** Моє ліжко тут. А там велика **шафа** (wardrobe). *(My bed is here. And there is a big wardrobe.)*

In this brief exchange, the gender emerges naturally through the possessive words. Oleg says **моя кімната** (my room) because room is feminine. He says **мій стіл** (my table) because table is masculine, and **моє ліжко** (my bed) because bed is neuter.

Finally, observe a quick conversation about everyday items you carry with you in a bag.

> **Максим:** Що у тебе є? *(What do you have?)*
> **Ірина:** У мене є **книга** (book), **телефон** (phone) і **фото** (photo). *(I have a book, a phone, and a photo.)*
> **Максим:** А у мене є **ручка** (pen) і **зошит** (notebook). *(And I have a pen and a notebook.)*

Even in a simple list, a Ukrainian speaker unconsciously categorizes these items: **телефон** and **зошит** are masculine, **книга** and **ручка** are feminine, while **фото** is neuter.

## Він, вона, воно — The Gender Test

For an English speaker, the idea that a table is masculine and a book is feminine feels abstract. English primarily reserves gender for living things with a biological sex. A table is an "it." A book is an "it." You must set this habit aside. In Ukrainian, grammatical gender, known as **рід** (gender), is a permanent, structural feature of every single noun. You cannot change a word's gender, just as you cannot change its core meaning.

As outlined in Ukrainian primary school materials like the Grade 3 textbook by Ponomarova, the Ukrainian language divides all nouns into three categories. These are **чоловічий рід** (masculine gender), **жіночий рід** (feminine gender), and **середній рід** (neuter gender). To determine which category a word belongs to, students use a simple substitution test with personal pronouns. Can you replace the noun with "he," "she," or "it"? If the word is a **стіл**, you refer to it as **він**. If the word is a **книга**, you refer to it as **вона**. If the word is a **вікно** (window), you refer to it as **воно**.

This concept becomes much more intuitive when you attach a possessive pronoun to the noun. This is known as the "My" test. Instead of just trying to memorize that a table is masculine, you practice saying "my table." The word for "my" changes depending on the gender of the noun it describes.

If a noun is masculine, you use **мій** (my). You say **мій стіл** (my table) and **мій телефон** (my phone). This firmly establishes the word in the masculine category. If a noun is feminine, you use **моя** (my). You say **моя книга** (my book) and **моя кімната** (my room). If a noun is neuter, you use **моє** (my). You say **моє вікно** (my window) and **моє ліжко** (my bed). By consistently pairing the noun with the correct form of "my," your brain builds a strong associative link.

<!-- INJECT_ACTIVITY: quiz-pronoun-choice -->

While the "My" test helps you confirm a word's gender, you also need a way to predict the gender of a new word you encounter. Fortunately, Ukrainian spelling is highly systematic. You can predict the gender of approximately ninety percent of nouns simply by looking at the last letter of the word in its basic, dictionary form. The Vashulenko textbook for the third grade outlines these primary rules.

If a noun ends in a consonant, it is almost certainly masculine. Look at words like **телефон**, **зошит**, and **ключ** (key). The final sounds are consonants, placing them firmly in the masculine category.

If a noun ends in the vowel **-а** or the vowel **-я**, it is typically feminine. Consider words like **лампа** (lamp), **кімната**, **книга**, and **ручка**. The open vowel ending is the strongest indicator of the feminine gender.

If a noun ends in the vowel **-о** or the vowel **-е**, it is neuter. Words such as **вікно**, **ліжко**, **місто** (city), and **дзеркало** all follow this exact pattern.

:::tip
There are a few exceptions to these rules, particularly words ending in a soft sign. However, at this stage, mastering the primary consonant, -а/-я, and -о/-е patterns allows you to correctly identify the vast majority of nouns you encounter.
:::

<!-- INJECT_ACTIVITY: quiz-gender-endings -->

## Предмети навколо — Objects Around Us

To make these rules concrete, organize common vocabulary by gender. We start with masculine objects you find in a study or carry in a bag. Read these words carefully and note the final consonant sound that defines their gender.

The word for a table is a **стіл**. The word for a chair is a **стілець** (chair). Your mobile device is a **телефон**, and your computer is a **комп'ютер** (computer). When you need to write something down, you use a **зошит**, and you unlock your door with a **ключ**. Every single one of these items belongs to the masculine gender. You refer to any of them as **він**, and if they belong to you, you use the possessive **мій**.

Now consider the feminine and neuter objects around you. The feminine words all share the characteristic open vowel endings. You read a **книга**. You turn on a **лампа** for light. You carry your belongings in a **сумка** (bag), write with a **ручка**, and sit inside a **кімната** surrounded by a **стіна** (wall). All of these end in **-а**, marking them as feminine (**вона**, **моя**).

Neuter nouns describe other essential items, clearly marked by their **-о** or **-е** endings. You look out a **вікно**. You sleep in a **ліжко**. You relax in a comfortable **крісло** (armchair). You check your reflection in a **дзеркало**, and you frame a **фото** for memories. These are all neuter objects (**воно**, **моє**).

<!-- INJECT_ACTIVITY: group-sort-gender -->

You previously learned how to talk about your family using the phrase **У мене є** (I have). You practiced saying things like "У мене є брат" (I have a brother) and "У мене є сестра" (I have a sister). This exact same grammatical construction is used to talk about inanimate objects. The gender of the object does not change the structure of the sentence. The phrase **У мене є** remains constant.

If you want to state that you own a table, you simply combine the phrase with the vocabulary word. You say **У мене є стіл** (I have a table). If you want to state that you have a book, you say **У мене є книга** (I have a book). If you are describing a room and want to say it has a window, you say **У мене є вікно** (I have a window).

This is a powerful pattern. By learning one fixed phrase, you can instantly communicate ownership or possession of any new vocabulary word you learn, regardless of whether that word is masculine, feminine, or neuter.

:::note
The phrase **У мене є** translates literally to "At me there is." The noun that follows it is the subject of the sentence, which is why it stays in its basic dictionary form. You do not need to change the ending of the object you possess in this specific construction.
:::

<!-- INJECT_ACTIVITY: fill-in-possessives -->

## Підсумок — Summary

Determining the grammatical gender of a Ukrainian noun is a foundational skill. It dictates how you use pronouns, how you form plurals later on, and how adjectives change to match the noun. Master this process by following a reliable three-step strategy.

First, apply the pronoun test. Ask yourself which personal pronoun replaces the noun naturally. Does the object feel like a **він**, a **вона**, or a **воно**?

Second, reinforce this with the "My" test. Pair the noun with a possessive pronoun to build a strong auditory and visual association. Say the combination out loud. Is it **мій** (masculine), **моя** (feminine), or **моє** (neuter)?

Third, check the ending of the dictionary form of the word. This is your visual proof.

Here is your quick-reference summary of the typical noun endings:

*   **Чоловічий рід** (Masculine gender): The word ends in a consonant. Examples include **стіл**, **зошит**, and **телефон**. You use **він** and **мій**.
*   **Жіночий рід** (Feminine gender): The word ends in the vowel **-а** or **-я**. Examples include **книга**, **сумка**, and **кімната**. You use **вона** and **моя**.
*   **Середній рід** (Neuter gender): The word ends in the vowel **-о** or **-е**. Examples include **вікно**, **ліжко**, and **дзеркало**. You use **воно** and **моє**.

Perform a self-check to ensure these concepts are clear.

What gender is the word **стіл**? It is masculine (**чоловічий рід**). We know this because it ends in a consonant sound, and we refer to it by saying **мій стіл**.

What gender is the word **книга**? It is feminine (**жіночий рід**). The visual proof is the **-а** ending, and we claim ownership by saying **моя книга**.

What gender is the word **вікно**? It is neuter (**середній рід**). It ends in the vowel **-о**, and we pair it with the neuter possessive, saying **моє вікно**.

Finally, how do you say "I have a chair" in Ukrainian? You combine the fixed possession phrase with the masculine noun for chair. The correct sentence is **У мене є стілець**. Keep practicing this structure with all the new objects around you.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: things-have-gender
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

**Level: A1.2-A1.3 (Module 8/55) — EARLY BEGINNER**

The learner knows the alphabet and ~200 words. They:
- Can read Ukrainian slowly
- Know basic nouns, adjectives, simple verb forms
- Cannot handle complex sentences or grammar terminology in Ukrainian

**Instructions in simple English with Ukrainian key terms in bold.**
Example: 'Choose the correct form of **мій/моя/моє**'

**Good activity types:** quiz, fill-in (simple sentences), match-up, group-sort, true-false, observe, anagram, translate (English→Ukrainian), error-correction (simple), divide-words, count-syllables, odd-one-out, order.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

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

### Pattern: grammar-possession [§4.2.1.4, §4.2.2]
**Присвійність** (Possession)
- **fill-in** — У мене є...: Структура «У мене/тебе/нього є...» — як українська виражає володіння / Structure «У мене/тебе/нього є...» — how Ukrainian expresses possession
  - Instruction: *Вставте правильне слово*
- **fill-in** — Мій, твій, наш...: Обрати присвійний займенник, що узгоджується з родом та числом іменника / Choose possessive pronoun matching noun gender and number
  - Instruction: *Вставте правильну форму*
- **match-up** — Чий? Чия? Чиє?: Зіставити присвійний займенник з іменником за родом / Match possessive pronoun to noun by gender
  - Instruction: *З'єднайте*
- **quiz** — У кого є?: Визначити, хто має щось, за контекстом речення / Determine who has something based on sentence context
**Anti-patterns (DO NOT generate):**
- ❌ translate: «У мене є» — унікальна українська структура. Переклад з англ. «I have» маскує різницю

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
