<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/who-am-i.yaml` file for module **5: Who Am I?** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-self-intro -->`
- `<!-- INJECT_ACTIVITY: quiz-register-choice -->`
- `<!-- INJECT_ACTIVITY: match-up-gendered-professions -->`
- `<!-- INJECT_ACTIVITY: fill-in-dialogue-final -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Complete self-introduction: Мене звати..., Я з..., Я —...'
  items: 6
  type: fill-in
- focus: Formal or informal? Choose the right introduction.
  items: 6
  type: quiz
- focus: Match professions with male/female forms
  items: 8
  type: match-up
- focus: Complete the dialogue with correct phrases
  items: 6
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- ми (we)
- вони (they)
- програміст, програмістка (programmer m/f)
- інженер, інженерка (engineer m/f)
- звідки (where from)
- друг (friend, male)
- його (his — doesn't change)
- її (her — doesn't change)
- Канада (Canada)
- Німеччина (Germany)
required:
- я (I)
- ти (you, informal)
- він (he)
- вона (she)
- ви (you, formal/plural)
- мене звати (my name is)
- як тебе звати? (what's your name, informal)
- як вас звати? (what's your name, formal)
- це (this is / these are)
- дуже приємно (pleased to meet you)
- студент, студентка (student m/f)
- вчитель, вчителька (teacher m/f)
- лікар, лікарка (doctor m/f)
- українець, українка (Ukrainian m/f)
- Україна (Ukraine)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

When traveling, the hostel common room is often the first place you use a new language. Imagine you are backpacking and walk into the kitchen. You see another traveler making coffee. In this casual environment, the conversation is informal. Two travelers, Marko from Canada and Olena from Kyiv, meet for the very first time. They use the informal register to exchange names and origins.

> **Марко:** Привіт! Як тебе звати? *(Hi! What is your name?)*
> **Олена:** Мене звати Олена. А тебе? *(My name is Olena. And you?)*
> **Марко:** Мене звати Марко. Звідки ти? *(My name is Marko. Where are you from?)*
> **Олена:** Я з України. А ти? *(I am from Ukraine. And you?)*
> **Марко:** Я з Канади. *(I am from Canada.)*
> **Олена:** Дуже приємно! *(Nice to meet you!)*

Professional settings require a different approach. At a university orientation or an international conference, you speak to colleagues and strangers with respect. The formal register replaces casual greetings with polite standard phrases. Notice how the speakers use the formal "you" and formal greetings when they meet in a conference hall.

> **Тарас:** Добрий день! Як вас звати? *(Good afternoon! What is your name?)*
> **Петро:** Мене звати Петро. Дуже приємно! *(My name is Petro. Nice to meet you!)*
> **Тарас:** Мені також! Ви з України? *(Me too! Are you from Ukraine?)*
> **Петро:** Так, я з Києва. *(Yes, I am from Kyiv.)*

This exchange sounds professional and respectful, perfect for adults meeting in a formal setting. The grammar changes slightly, but the core function remains exactly the same.

:::note
In Ukrainian culture, introductions are often accompanied by a firm handshake and direct eye contact, especially in formal or professional environments. When saying **Дуже приємно!**, a warm smile goes a long way.
:::

Often, you need to introduce other people in the room. When pointing out friends or colleagues, the focus shifts to the third person. You identify the person and give a quick fact about their origin or profession.

> **Олена:** Це Андрій. Він зі Львова. Він — інженер. *(This is Andriy. He is from Lviv. He is an engineer.)*
> **Марко:** А це Оксана. Вона з Одеси. Вона — лікарка. *(And this is Oksana. She is from Odesa. She is a doctor.)*

These short, punchy sentences are the building blocks of Ukrainian communication. You state who the person is, where they come from, and what they do.

These three conversations reveal the core mechanics of Ukrainian introductions. First, the relationship dictates the register. Informal situations rely on **ти** (you) and **тебе** (you, object form), while formal situations demand **ви** (you) and **вас** (you, object form). Second, when people state their nationality or profession, they simply link the person and the fact. A sentence like **Я з Канади** (I am from Canada) works perfectly without any verb connecting the subject and the origin.

## Мене звати... (My name is...)

The phrase **мене звати** means "my name is," but the literal translation reveals how Ukrainian thinks about identity. It actually translates to "me they call." Ukrainian does not use the verb "to be" to state a name. You do not say "My name is Marko." Instead, you use this fixed, unchangeable phrase. The word **мене** is the object form of "I," meaning "me." The word **звати** is the verb "to call." You simply add your name at the end of this construction.

To ask someone their name, you must choose the correct register based on your relationship. If you are speaking to a peer, a child, or a fellow student, use the informal question **Як тебе звати?** (What is your name?). The word **тебе** means "you" in the object form. If you are addressing a stranger, an elder, or speaking in a professional context, you must use the formal question **Як вас звати?** (What is your name?). Here, **вас** represents the formal "you."

You can easily ask about a third person by swapping the pronoun. To ask a man's name, use **Як його звати?** (What is his name?). The word **його** means "his" or "him." To ask a woman's name, use **Як її звати?** (What is her name?). The word **її** means "her." These words remain completely stable. You only change the pronoun to ask about different people in the room.

After exchanging names, politeness requires a friendly response. The standard phrase is **Дуже приємно!** (Very pleasant! or Nice to meet you!). This is a universal, safe response in any situation, formal or informal. Another excellent option is **Приємно познайомитись!** (Pleasant to get acquainted!). You say these phrases strictly AFTER the names are spoken, never as an opening greeting. It acts as the closing seal on the introduction.

<!-- INJECT_ACTIVITY: fill-in-self-intro -->

## Це... (This is...)

When you need to point something out or identify a person, you use the word **це**. This tiny word translates to "this is," "it is," or "these are." It acts as a universal identifier. Just like with names, Ukrainian requires no verb "to be" in this construction. You place **це** directly next to the noun.

**Це кава.** (This is coffee.)
**Це Київ.** (This is Kyiv.)
**Це Андрій.** (This is Andriy.)

Forming questions with this word requires attention to word order. In English, you might ask "What is this?". In Ukrainian, the question word must always come first. To ask about a person, use **Хто це?** (Who is this?). To ask about an object, use **Що це?** (What is this?). You can never say "*Це хто?" or "*Це що?". The structure is locked: question word, then identifier.

**Хто це? Це мама.** (Who is this? This is mom.)
**Що це? Це чай.** (What is this? This is tea.)

This simple pattern allows you to navigate the world around you immediately. You can point to anything and identify it or ask about it.

**Хто це? Це мій друг.** (Who is this? This is my friend.)
**Що це? Це суп.** (What is this? This is soup.)
**Хто це? Це студентка.** (Who is this? This is a student.)

This construction is the fastest way to build your vocabulary. You point, you ask, you identify.

<!-- INJECT_ACTIVITY: quiz-register-choice -->

## Особові займенники (Personal Pronouns)

Every Ukrainian sentence anchors itself to a subject. The basic personal pronouns are your core building blocks. For singular subjects, you use **я** (I), **ти** (you, informal), **він** (he), **вона** (she), and **воно** (it). The pronoun **ти** is strictly for one person you know well. The pronouns **він** and **вона** replace the names of people you are talking about. You will use **я** the most when talking about your own life.

For multiple people or formal situations, you shift to the plural pronouns. You use **ми** (we), **ви** (you, formal/plural), and **вони** (they). The pronoun **ви** serves a dual purpose. It addresses a group of people, but it also addresses one single person respectfully. When writing a formal letter or email to one specific person, you capitalize it as **Ви** to show high respect. These pronouns drive the rest of the sentence.

## Я — студент (I am a student)

Ukrainian statements of identity in the present tense operate on the "zero copula" rule. The verb "is," "am," or "are" completely vanishes. You simply place the subject pronoun directly next to the noun. In written Ukrainian, a long dash (—) marks the spot where the missing verb would normally sit.

**Я — студент.** (I am a student.)
**Він — лікар.** (He is a doctor.)
**Вона — вчителька.** (She is a teacher.)

:::tip
The dash (—) replaces the missing verb "to be" in writing, but it is completely silent when speaking. When reading the sentence **Я — лікар** out loud, simply say the two words naturally without any extra pause.
:::

Unlike English, Ukrainian professions and titles almost always change to match the gender of the person. You must choose the masculine or feminine form.

**Він студент.** (He is a student.) vs **Вона студентка.** (She is a student.)
**Він лікар.** (He is a doctor.) vs **Вона лікарка.** (She is a doctor.)
**Він вчитель.** (He is a teacher.) vs **Вона вчителька.** (She is a teacher.)
**Він програміст.** (He is a programmer.) vs **Вона програмістка.** (She is a programmer.)

Feminine forms are standard, modern, and required. Always match the profession to the person.

Nationalities behave exactly the same way. They must match the person's gender.

**Він українець.** (He is a Ukrainian.) vs **Вона українка.** (She is a Ukrainian.)
**Він американець.** (He is an American.) vs **Вона американка.** (She is an American.)
**Він канадієць.** (He is a Canadian.) vs **Вона канадка.** (She is a Canadian.)

<!-- INJECT_ACTIVITY: match-up-gendered-professions -->

## Звідки? (Where from?)

When meeting new people, origin is a natural topic. To ask where someone is from, you use the question word **звідки** (where from). Again, you must choose the correct register. Ask a peer **Звідки ти?** (Where are you from?). Ask a stranger or a professional contact **Звідки ви?** (Where are you from?). This question specifically targets a person's origin country or hometown, not necessarily where they currently live.

To answer, you state your pronoun, add the preposition **з** (from), and name the place.

**Я з України.** (I am from Ukraine.)
**Я з Канади.** (I am from Canada.)
**Я зі Штатів.** (I am from the States.)
**Я з Німеччини.** (I am from Germany.)

Notice the phrase **зі Штатів**. The preposition **з** changes to **зі** before words starting with complex consonant clusters. This makes the phrase much easier to pronounce smoothly.

:::note
The phrase **Я зі Штатів** uses the colloquial word **Штати** (the States) instead of the full formal name **Сполучені Штати Америки** (United States of America). It is the most common and natural way Ukrainians refer to the USA in everyday conversation.
:::

You might notice that the country names look slightly different after the preposition **з**. For example, **Україна** (Ukraine) becomes **України**. This happens because Ukrainian nouns change their endings based on their role in the sentence. For now, do not worry about the grammar rules behind these changes. Treat these origin phrases as solid, memorized chunks. Just learn your own country's "from" form and use it confidently.

<!-- INJECT_ACTIVITY: fill-in-dialogue-final -->

## Підсумок — Summary

You now possess the core tools to introduce yourself, identify the world around you, and engage in a first conversation. You can navigate formal and informal encounters with confidence. Use this checklist to verify your understanding of the foundational patterns:

- **Як вас звати? — Мене звати Марко.** (What is your name? — My name is Marko.)
- **Хто це? — Це мій друг.** (Who is this? — This is my friend.)
- **Що це? — Це чай.** (What is this? — This is tea.)
- **Хто ви? — Я — вчителька.** (Who are you? — I am a teacher.)
- **Звідки ви? — Я з України.** (Where are you from? — I am from Ukraine.)
- **Приємно познайомитись! — Мені також!** (Nice to meet you! — Me too!)

Mastering these phrases ensures that your first contact with a Ukrainian speaker will be natural, polite, and successful.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: who-am-i
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

**Level: A1.1 (Module 5/55) — COMPLETE BEGINNER**

The learner is on their FIRST DAYS learning Ukrainian. They:
- Cannot read Ukrainian yet (learning the alphabet)
- Know zero Ukrainian grammar
- Can recognize only a few words (мама, тато, привіт)

**ALL instructions MUST be in English.** The learner cannot read Ukrainian instructions.

**Best activity types for this level:**
- image-to-letter: hear/see → pick the letter
- letter-grid: interactive alphabet practice
- match-up: letter ↔ sound, letter ↔ word
- quiz: in ENGLISH about Ukrainian sounds ('What sound does В make?')
- observe: show patterns in Ukrainian with English prompts
- group-sort: sort letters into vowels/consonants
- divide-words: split words into syllables (складоподіл)
- count-syllables: count syllables by counting vowels
- pick-syllables: select open/closed syllables
- odd-one-out: find the word that doesn't belong
- watch-and-repeat: pronunciation video practice
- translate: single words/short phrases English→Ukrainian (multiple choice)
- error-correction: find simple errors (gender agreement, missing ь)

**DO NOT use:** cloze, mark-the-words, select, essay-response, unjumble (learner can't construct Ukrainian sentences yet).


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
