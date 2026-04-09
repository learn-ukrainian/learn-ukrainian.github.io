<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/my-family.yaml` file for module **6: My Family** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-dialogue -->`
- `<!-- INJECT_ACTIVITY: match-family -->`
- `<!-- INJECT_ACTIVITY: quiz-possession -->`
- `<!-- INJECT_ACTIVITY: fill-in-possessives -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'У тебе є...? — answer Так/Ні. Use ONLY the chunk ''у тебе є''. Example questions:
    ''У тебе є брат?'', ''У тебе є сестра?'', ''У тебе є бабуся?'' Answer options:
    ''Так, у мене є брат.'' / ''Ні.'' / ''Так, у мене є два брати.'' Do NOT use genitive
    names (no ''У Оксани є'').'
  items: 6
  type: quiz
- focus: 'Choose correct possessive pronoun. EXACT pattern: ''Це {___} мама.'' → моя
    | ''Де {___} тато?'' → твій | ''Ось {___} батьки.'' → мої All nominative case.
    Options: мій/моя/моє/мої or твій/твоя/твоє/твої.'
  items: 8
  type: fill-in
- focus: 'Match English family words to Ukrainian. Pairs: parents↔батьки, uncle↔дядько,
    aunt↔тітка, grandfather↔дідусь, grandmother↔бабуся, brother↔брат, sister↔сестра,
    mother and father↔мама і тато.'
  items: 8
  type: match-up
- focus: 'Complete a family introduction dialogue with blanks. Pattern: ''— Привіт!
    Це {твій} брат?'' / ''— Так, це мій брат. Ось мій {тато}.'' Options per blank:
    family members or possessives. NO genitive forms.'
  items: 4
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- батьки (parents)
- дядько (uncle)
- тітка (aunt)
- дочка (daughter)
- син (son)
- дружина (wife)
- чоловік (man / husband)
- його (his — doesn't change)
- її (her — doesn't change)
- один, одна (one — m/f)
- два, дві (two — m/f)
- чи (or — in questions)
- тільки (only)
required:
- сім'я (family) — apostrophe word
- мама (mother)
- тато (father)
- брат (brother)
- сестра (sister)
- бабуся (grandmother)
- дідусь (grandfather)
- мій, моя, моє, мої (my — m/f/n/pl)
- твій, твоя, твоє (your — m/f/n, informal)
- у мене є (I have)
- у тебе є (you have, informal)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги — Dialogues

When you meet someone new in Ukraine, small talk often quickly turns to your personal life. People want to know who you are and where you come from. Sharing information about your **сім'я** (family) is the most common way to build a connection. Showing photos of your relatives on your phone is a natural icebreaker. You can easily start a conversation by showing a picture and talking about "my family" — **моя сім'я**.

Here is a typical conversation between two friends, Оля and Марк. They are taking a break and looking at photos on their phones.

> **Оля:** У тебе є брати чи сестри? *(Do you have brothers or sisters?)*
> **Марк:** Так, у мене є два брати і одна сестра. *(Yes, I have two brothers and one sister.)*
> **Оля:** Ого! У мене тільки один брат. *(Wow! I have only one brother.)*
> **Марк:** Як його звати? *(What is his name?)*
> **Оля:** Коля. *(Kolya.)*

Notice the core question: **У тебе є брати чи сестри?** means "Do you have brothers or sisters?". The word **чи** means "or" in questions. Марк responds with a very specific pattern: **Так, у мене є два брати і одна сестра** (Yes, I have two brothers and one sister). He then asks about the brother's name using **Як його звати?** (What is his name?).

:::tip
In Ukraine, asking **У тебе є брати чи сестри?** is a very normal, polite way to show interest in a new acquaintance's life. It is not considered too personal for a friendly chat.
:::

Later, Оля shows a larger group picture on her screen.

> **Оля:** Це моя сім'я на фотографії. *(This is my family in the photograph.)*
> **Марк:** Класно! Хто це? *(Cool! Who is this?)*
> **Оля:** Це моя мама Марина. *(This is my mom Maryna.)*
> **Оля:** Це мій тато Євген. *(This is my dad Yevhen.)*
> **Оля:** Це моя сестра Катя і мої брати — Іван і Денис. *(This is my sister Katya and my brothers — Ivan and Denys.)*
> **Марк:** А це твоя бабуся? *(And is this your grandmother?)*
> **Оля:** Так, її звати Тетяна. *(Yes, her name is Tetiana.)*

This dialogue relies heavily on the **Це** (This is) pattern combined with possessive words. Оля identifies each person clearly: **Це моя мама** (This is my mom) and **Це мій тато** (This is my dad). When Марк asks about the older woman, he points and asks, **А це твоя бабуся?** (And is this your grandmother?). Оля confirms and gives her name using the phrase **її звати** (her name is).

You can combine these questions and answers into a connected self-introduction. This is how you introduce your world to someone else in a clear, structured way.

> Привіт! Мене звати Анна. *(Hi! My name is Anna.)*
> Я з Лондона. *(I am from London.)*
> Моя мама — вчителька. *(My mom is a teacher.)*
> Мій тато — інженер. *(My dad is an engineer.)*
> У мене є один брат. *(I have one brother.)*

This short monologue demonstrates how family vocabulary anchors your personal identity. You state your name, your origin, identify your parents and their professions, and mention your siblings.

<!-- INJECT_ACTIVITY: fill-in-dialogue -->

## Сім'я — Family Vocabulary

Ukrainian has two common words for "family." The word **сім'я** typically refers to the immediate, nuclear family. Notice the apostrophe in this word; it tells you to pause slightly and pronounce the **я** clearly. The word **родина** is also very common but often implies a broader network of relatives or kin. Both words are used frequently in daily life.

For your immediate family, you will use these core terms. A mother is **мати** (formal) or **мама** (informal). A father is **батько** (formal) or **тато** (informal). In everyday conversation, Ukrainians almost always use **мама** and **тато**. A brother is a **брат**, and a sister is a **сестра**. If you have children, a son is a **син**, and a daughter is a **дочка** or **донька**. Both words for daughter are equally common and correct. A husband is a **чоловік** (which also means "man"), and a wife is a **дружина**.

Your extended family network adds more essential words to your vocabulary. A grandmother is a **бабуся**, and a grandfather is a **дідусь**. An aunt is a **тітка**, and an uncle is a **дядько**. 

English has convenient grouping words like "grandparents," but Ukrainian operates differently. Ukrainian has absolutely no single word that translates to "grandparents." If you want to talk about them together, you must name them both. You say **бабуся і дідусь** (grandmother and grandfather) or **мої дідусь і бабуся** (my grandfather and grandmother). This is a strict rule of the language. You must always specify both individuals when referring to your grandparents.

<!-- INJECT_ACTIVITY: match-family -->

## У мене є — I have

Expressing possession in Ukrainian requires a completely different mindset from English. English uses the active verb "to have," as in "I have a brother." Ukrainian avoids using a direct verb for simple possession at this level. Instead, Ukrainian uses a spatial construction that literally translates to "At me there-is."

The core phrase for "I have" is **у мене є**. This is a fixed chunk of language that you should memorize exactly as it is. 
To ask someone informally if they have something, use **у тебе є** (you have). 
To ask someone formally, or a group of people, use **у вас є** (you have).

If you want to say "I have a brother," you say **У мене є брат** (At me there-is a brother). The person possessing the item comes first in this special phrase, followed by the word **є**, which simply means "is" or "exists." 

:::caution
Never try to translate "I have" word-for-word using a verb like you do in English. Always use the fixed phrase **у мене є**. This is the only natural way to express basic possession.
:::

Turning this statement into a question is incredibly simple. You do not change the word order at all. You only change your intonation. Your voice must rise clearly at the end of the sentence: **У тебе є сестра? ↗** (Do you have a sister?).

To answer "no" to these questions right now, simply say **Ні** (No). If you want to provide more context without using complex negative grammar, you can say **Ні, у мене тільки один брат** (No, I have only one brother). The word **тільки** means "only."

When you count your family members, the numbers one and two must match the gender of the person. The number one changes depending on who you are counting: **один брат** (one brother - masculine) versus **одна сестра** (one sister - feminine). The number two also changes in the exact same way: **два брати** (two brothers - masculine) versus **дві сестри** (two sisters - feminine).

<!-- INJECT_ACTIVITY: quiz-possession -->

## Мій, моя, моє — Possessive Pronouns

When you talk about your family, you need possessive words. The Ukrainian word for "my" changes its shape to match the grammatical gender of the noun it belongs to. The pronoun must agree with the person or object, not with you.

If the family member is masculine, use **мій**: **мій тато** (my dad), **мій брат** (my brother), **мій син** (my son). 
If the family member is feminine, use **моя**: **моя мама** (my mom), **моя сестра** (my sister), **моя донька** (my daughter). 
If the noun is neuter, use **моє**: **моє місто** (my city).
If you are talking about multiple people, use the plural form **мої**: **мої брати** (my brothers). 

:::note
The word for parents, **батьки**, is always grammatically plural in Ukrainian. Therefore, it must always be paired with the plural pronoun, meaning you must say **мої батьки** (my parents).
:::

The informal word for "your" follows the exact same gender pattern as "my." You use **твій** for masculine nouns, **твоя** for feminine nouns, **твоє** for neuter nouns, and **твої** for plural nouns. For example, you say **твій тато** (your dad) and **твоя мама** (your mom).

Talking about a third person is actually much easier. The words for "his" and "her" are static. They never change their shape, regardless of the noun that follows them. The word for "his" is **його**. The word for "her" is **її**.
You say **його мама** (his mom) and **його тато** (his dad). 
You say **її брат** (her brother) and **її сестра** (her sister). 
These two words remain perfectly frozen in place, making them very easy to use.

<!-- INJECT_ACTIVITY: fill-in-possessives -->

## Підсумок — Summary

This module gave you the tools to talk about the people closest to you. You should now be able to confidently answer basic questions about your family structure.

Self-check questions:
- Can you name five family members in Ukrainian? You should know **мама**, **тато**, **брат**, **сестра**, and **бабуся**.
- Can you say "I have a sister"? You must use the fixed chunk **У мене є сестра**.
- What is the fundamental difference between **мій** and **моя**? You use **мій** for masculine nouns like **брат**, and **моя** for feminine nouns like **сестра**.
- Can you use **його** and **її** correctly? Remember that these words never change their form based on the noun.

Mini-challenge: Introduce your own family right now. Speak out loud and create four sentences. Use the **Це моя...** pattern to identify people and the **У мене є...** pattern to state who is in your family. You are ready to share your world.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: my-family
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

**Level: A1.1 (Module 6/55) — COMPLETE BEGINNER**

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
