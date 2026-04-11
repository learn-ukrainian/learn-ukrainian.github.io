<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-genitive.yaml` file for module **16: Контрольна робота — родовий відмінок** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-genitive-prepositions -->`
- `<!-- INJECT_ACTIVITY: fill-in-genitive-forms -->`
- `<!-- INJECT_ACTIVITY: error-correction-genitive-checks -->`
- `<!-- INJECT_ACTIVITY: match-up-genitive-situational -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Identify the Genitive preposition and its function in context sentences
  items: 8
  type: quiz
- focus: Complete sentences requiring Genitive singular and plural with correct agreement
  items: 8
  type: fill-in
- focus: Match situations (market, doctor, directions) to correct Genitive expressions
  items: 8
  type: match-up
- focus: Find and correct grammar errors in sentences covering module topics
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- виправити (to correct)
- впізнати (to recognize)
- вибрати (to choose)
required:
- родовий відмінок (genitive case)
- прийменник (preposition)
- узгодження (agreement)
- множина (plural)
- однина (singular)
- закінчення (ending)
- перевірка (check, review)
- помилка (mistake, error)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Частина 1: Впізнавання форм (Part 1: Recognizing Forms)

This module consolidates your knowledge of the **родовий відмінок** (genitive case) covered in modules M08-M13. The Genitive case is the most frequently used case in the Ukrainian language. We use it to express negation, possession, quantity, and movement. Before moving to more complex case interactions, this checkpoint ensures your foundation is solid. You must be able to recognize which **прийменник** (preposition) triggers the Genitive and correctly apply the **закінчення** (ending) for **однина** (singular) and plural nouns. Let's review the core preposition groups.

Spatial prepositions describe physical location and proximity. The prepositions **біля** (near/by), **навпроти** (opposite/across from), **коло** (around/near), and **до** (to/towards) always require the Genitive case. When you hear these words, immediately anticipate a Genitive ending. The preposition **до** indicates direction towards a destination, while the others indicate static location. Notice the endings in the following examples.

> **Читаємо українською:**
> Ми стоїмо **біля собору**. (We are standing near the cathedral.)
> Наш готель розташований **навпроти театру**. (Our hotel is located opposite the theater.)
> Діти граються **коло школи**. (The children are playing near the school.)
> Туристи йдуть **до станції**. (The tourists are walking to the station.)
> Машина під'їхала **до будинку**. (The car drove up to the house.)

Source and time prepositions explain where something comes from or when an event occurs in a sequence. We use **від** (from/away from a person or object), **з / із / зі** (from/out of a place or material), and **після** (after). The preposition **з** takes the form **із** or **зі** to make pronunciation easier, especially before clusters of consonants.

> **Читаємо українською:**
> Цей лист **від мами**. (This letter is from mom.)
> Я отримав повідомлення **від лікаря**. (I received a message from the doctor.)
> Мій друг приїхав **зі Львова**. (My friend arrived from Lviv.)
> Вона взяла книгу **з полиці**. (She took the book from the shelf.)
> Ми підемо гуляти **після обіду**. (We will go for a walk after lunch.)
> **Після роботи** я читаю новини. (After work, I read the news.)

Purpose and lack prepositions define who benefits from an action or what is missing. The preposition **для** (for) indicates the recipient or purpose. The preposition **без** (without) indicates absence, similar to the negative construction with **немає**. These are essential for everyday situations like ordering food or buying gifts.

> **Читаємо українською:**
> Я купив подарунок **для сестри**. (I bought a gift for my sister.)
> Ця кімната **для гостей**. (This room is for guests.)
> Мені, будь ласка, чорний чай **без цукру**. (Black tea without sugar for me, please.)
> Я не можу читати **без окулярів**. (I cannot read without glasses.)
> Це **квиток для студента**. (This is a ticket for a student.)

To recognize the function of a preposition, ask the question **кого?** (whom?) for people and animals, or **чого?** (what?) for objects and concepts. Distinguish between direction (**до кого? до чого?**), location (**біля кого? біля чого?**), and source (**від кого? з чого?**). When you identify the correct question, the Genitive ending follows naturally.

<!-- INJECT_ACTIVITY: quiz-genitive-prepositions -->

## Частина 2: Вибір правильної форми (Part 2: Choosing the Correct Form)

When forming the Genitive case, we must maintain **узгодження** (agreement) between the noun and its modifiers. Adjectives and possessive pronouns must match the noun in gender, number, and case. For masculine and neuter singular words, the Genitive ending is **-ого** (for adjectives and pronouns). For feminine singular words, the ending is **-ої** (or **-єї** after soft consonants).

> **Читаємо українською:**
> Це рюкзак **мого нового друга**. (This is the backpack of my new friend.)
> Я не бачив **твоєї старшої сестри**. (I haven't seen your older sister.)
> Колір **цього старого стола** дуже темний. (The color of this old table is very dark.)
> У нас немає **чистої води**. (We don't have clean water.)
> Я чекаю **наступного автобуса**. (I am waiting for the next bus.)

Forming the Genitive **множина** (plural) is often the most challenging part of Ukrainian grammar. The endings depend on the noun's gender and declension group. Masculine nouns (and some neuter nouns) typically take the ending **-ів** or **-їв**. Feminine nouns (and most neuter nouns) usually have a zero ending, meaning the final vowel is dropped. A small group of nouns, primarily feminine nouns ending in a consonant and some irregular plurals, take the ending **-ей**.

> **Читаємо українською:**
> На вечірці було **десять друзів**. (There were ten friends at the party.)
> Вона прочитала **п'ять книжок**. (She read five books.)
> На вулиці **багато людей**. (There are many people on the street.)
> Ми не спали **кілька ночей**. (We didn't sleep for a few nights.)
> У мене немає **грошей**. (I don't have money.)

For masculine nouns in the singular, you must choose between the ending **-а / -я** and **-у / -ю**. Animate nouns (people and animals) always take **-а / -я**. For inanimate nouns, the logic relies on how "concrete" the item is. Concrete objects and specific terms take **-а / -я**. Abstract concepts, collective nouns, materials, and phenomena take **-у / -ю**. 

> **Читаємо українською:**
> Водій чекає біля **автобуса**. (The driver is waiting near the bus.) *Concrete object.*
> У мене зовсім немає вільних годин, немає **часу**. (I have no free hours at all, I have no time.) *Abstract concept.*
> Я дістав зошит з **рюкзака**. (I took a notebook from the backpack.) *Concrete object.*
> Я п'ю каву без **цукру**. (I drink coffee without sugar.) *Material/substance.*
> Тут немає **вітру**. (There is no wind here.) *Natural phenomenon.*

<!-- INJECT_ACTIVITY: fill-in-genitive-forms -->

Minimal pairs of prepositions often confuse learners. Compare **з** (from/out of a place) and **від** (from/away from a person). You return **з** роботи (from work), but you receive a letter **від** колеги (from a colleague). Compare **біля** (near/next to) and **навпроти** (opposite/facing). A park can be **біля** дому (near the house), while a pharmacy might be **навпроти** дому (across from the house). Remember that **з** changes to **зі** for phonetic ease when the next word starts with multiple consonants.

> **Читаємо українською:**
> Він приїхав **зі Львова**. (He arrived from Lviv.)
> Вона взяла зошит **зі столу**. (She took the notebook from the table.)
> Лікарня розташована **навпроти парку**. (The hospital is located opposite the park.)
> Ми зустрілися **біля парку**. (We met near the park.)

A frequent **помилка** (mistake) among English speakers is leaving the noun in the Nominative case after **немає** or after prepositions. English does not change the noun's form to show absence. Another common error is using the Accusative case instead of the Genitive with certain verbs. For example, the verb **потребувати** (to need/require) always governs the Genitive case. Saying "Я потребую допомогу" (Accusative) is incorrect. The correct form is "Я потребую допомоги" (Genitive). You must **впізнати** (recognize) the trigger word to **виправити** (correct) the error.

> **Читаємо українською:**
> ❌ *У мене немає брат.* 
> ✅ У мене немає **брата**. (I don't have a brother.)
> ❌ *Я потребую допомогу.*
> ✅ Я потребую **допомоги**. (I need help.)
> ❌ *Він прийшов без квиток.*
> ✅ Він прийшов **без квитка**. (He arrived without a ticket.)

<!-- INJECT_ACTIVITY: error-correction-genitive-checks -->

## Частина 3: Вільне вживання (Part 3: Free Production)

To truly master the Genitive case, you must apply it in real-world contexts. At the market, you will use it to specify quantities and measures. At the pharmacy, you will use the preposition **від** (from/against) to describe the purpose of medication, or **для** (for) to specify the body part. Let's look at how native speakers build these phrases.

> **Читаємо українською:**
> Дайте мені, будь ласка, **два кілограми яблук**. (Give me two kilograms of apples, please.)
> Мені потрібна велика **пляшка води**. (I need a large bottle of water.)
> У вас є **таблетки від болю**? (Do you have pills for pain?)
> Я хочу купити **крем для рук**. (I want to buy hand cream.)
> Скільки коштує кілограм **сиру**? (How much does a kilogram of cheese cost?)

Let's observe a multi-turn dialogue. In this scenario, a tour guide shows a group around Kyiv. Notice how many times the Genitive case appears to express location, direction, purpose, and lack.

> **Гід:** Добрий день! Ми стоїмо **біля Золотих воріт**. *(Good day! We are standing near the Golden Gates.)*
> **Туристи:** Яка краса! А куди ми йдемо далі? *(What beauty! And where are we going next?)*
> **Гід:** Зараз ми йдемо **до Софійського собору**. Це близько. *(Now we are walking to St. Sophia's Cathedral. It is close.)*
> **Туристи:** Скільки часу туди йти? *(How much time to walk there?)*
> **Гід:** **До Хрещатика** десять хвилин, а до собору — п'ять. *(To Khreshchatyk it is ten minutes, and to the cathedral — five.)*
> **Туристи:** Чи потрібен квиток? *(Is a ticket needed?)*
> **Гід:** Так, **без квитка** заходити не можна. Але ця екскурсія **для групи з десяти людей**, тому вхід безкоштовний! *(Yes, without a ticket you cannot enter. But this tour is for tourists from Ukraine, so entry is free!)*

When translating from English to Ukrainian, you must adjust your strategy. English uses an apostrophe with an "s" ('s) or the preposition "of" to show possession. Ukrainian uses the Genitive case directly on the noun and its modifiers. Do not simply place two Nominative nouns next to each other.

> **Читаємо українською:**
> Це **машина мого брата**. (This is my brother's car.)
> Де розташований **центр міста**? (Where is the city center?)
> Ми читаємо **книгу відомого автора**. (We are reading the book of a famous author.)
> Це **смак дитинства**. (This is the taste of childhood.)

Quantity words always require the Genitive case. The words **багато** (a lot / many), **мало** (a little / few), and **кілька** (several / a few) behave like numbers. When dealing with countable objects, use the Genitive plural. When dealing with uncountable substances or abstract concepts, use the Genitive singular. You will **вибрати** (choose) the correct number form based on whether the noun is countable.

> **Читаємо українською:**
> У нього дуже **багато часу**. (He has a lot of time.) *Uncountable, singular.*
> На лекції було **кілька студентів**. (There were several students at the lecture.) *Countable, plural.*
> У річці залишилося **мало води**. (There is little water left in the river.) *Uncountable, singular.*
> Ми купили **багато свіжих овочів**. (We bought many fresh vegetables.) *Countable, plural.*

<!-- INJECT_ACTIVITY: match-up-genitive-situational -->

Consistent use of correct Genitive endings is a strong sign of A2 and early B1 proficiency. Native speakers naturally hear the difference between a concrete object and an abstract concept, or recognize the zero ending in the plural. You will make mistakes, and that is normal. The goal of a **перевірка** (review/check) is to identify your weak spots so you can practice them. Every time you correctly say "для мами" instead of "для мама", or "п'ять книжок" instead of "п'ять книги", you are thinking in Ukrainian. Pay attention to the prepositions you hear in daily conversations, and observe the endings that follow them. Your brain will gradually absorb these patterns.

## Підсумок

This checkpoint confirms your readiness to use the Genitive case in daily life. Use this self-assessment checklist to evaluate your progress. If you answer "yes" to these questions, you are ready to move on: 

*   Чи можу я використати прийменники **до**, **біля**, **від**, **для** без помилок?
*   Чи правильно я утворюю множину (**друзів**, **книжок**, **людей**)?
*   Чи вмію я узгоджувати прикметники (**мого нового**) з іменниками?
*   Чи розумію я різницю між **автобуса** та **часу**?
*   Чи можу я пояснити напрямок або рецепт, використовуючи родовий відмінок?

If you feel confident with these points, keep practicing, and always listen for the prepositions that signal a change in the ending.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-genitive
level: a2

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

**Level: A2 (Module 16/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

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
2. Run `query_cefr_level` on any word you're unsure about — it must be a2-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
