# Phase Fix: Apply Review Fix Plan

> **You are Gemini, executing the Fix phase of an orchestrated rebuild.**
> **Your ONLY task: Apply every fix from the review's Fix Plan. Output complete fixed files.**
> **Do NOT add, remove, or change anything beyond what the Fix Plan specifies.**

## Your Input

Read these files from disk:

**Review with Fix Plan** (your instructions — follow EVERY fix listed):
```
# Рецензія: Checkpoint: Word Formation

**Level:** A2 | **Module:** 44
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [Partial match]
- Grammar scope: [Scope creep in vocab choice 'сильність']
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | Sloppy typos like `napisав` in activities break trust. |
| 2 | Coherence | 9/10 | <7 | Content flows well. |
| 3 | Relevance | 8/10 | <7 | Good topic, but some examples are awkward (`сильність`). |
| 4 | Educational | 7/10 | <7 | Teaching `сильність` as the derivation for "strength" is misleading; standard is `сила`. |
| 5 | Language | 7/10 | <8 | Grammar agreement error in Cloze (`місто... київський`), typo `napisав`. |
| 6 | Pedagogy | 7/10 | <7 | Misleading derivation example; Activity logic flaws. |
| 7 | Immersion | 8/10 | <6 | Good usage of Ukrainian. |
| 8 | Activities | 6/10 | <7 | Critical errors: agreement, typos, redundant prefixes, logic. |
| 9 | Richness | 8/10 | <6 | Good variety. |
| 10 | Beginner Safety | 7/10 | <7 | Typos and awkward words create confusion. |
| 11 | LLM Fingerprint | 10/10 | <7 | No obvious hallucination, looks authored. |
| 12 | Linguistic Accuracy | 7/10 | <9 | `читати` marked as noun in vocab file; `сильність` usage. |

**Weighted Overall:** 7.5/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [FAIL] - `сильність` (rare/awkward form).
- Activity errors: [FAIL] - `napisав`, `київський` (agreement), `пере{переписати}`, Mark-words logic.
- Beginner safety: 3.5/5

## Critical Issues Found

### Issue 1: Linguistic Accuracy (Content & Vocab)
- **Location**: Section "Skill 2: Noun Suffixes", Practice 2.
- **Original**: `сильний → сила/сильність`
- **Problem**: `Сильність` is extremely rare/technical. The standard noun is `сила`. Using this as a core example of `-ість` derivation is pedagogically poor because it teaches a word students shouldn't use.
- **Fix**: Replace with `сміливий → сміливість` (boldness) or `швидкий → швидкість` (speed). These are standard `-ість` derivations.

### Issue 2: Typo (Activities)
- **Location**: Activity 16 (mark-the-words), `text` field.
- **Original**: `Український письменник napisав музичну п'єсу`
- **Problem**: `napisав` uses Latin characters and is a typo for `написав`.
- **Fix**: Change to `написав`.

### Issue 3: Grammar Agreement (Activities)
- **Location**: Activity 15 (cloze), Item "Місто...".
- **Original**: `Місто, де я народився — {київський|Київ|київському}.`
- **Problem**: `Місто` is neuter. The adjective must be `київське`. `Київський` is masculine. `Київ` (noun) is grammatically possible ("The city is Kyiv"), but if the drill is about adjectives (as implied by the distractor `київському`), the target should be `київське`.
- **Fix**: Change options to `{київське|Київ|київському}` OR change sentence to `Мій рідний район — {київський...}`. Prefer fixing agreement: `Місто... — {київське...}`.

### Issue 4: Redundant Prefix (Activities)
- **Location**: Activity 10 (cloze), Item "Зробити ще раз".
- **Original**: `Зробити ще раз = пере{переписати|написати|дописати}`
- **Problem**: The prefix `пере` is outside the brace, and the answer inside is `переписати`. Result: `перепереписати`.
- **Fix**: Remove `пере` before the brace: `Зробити ще раз = {переписати|написати|дописати}`.

### Issue 5: Metadata Error (Vocabulary)
- **Location**: `vocabulary/44-checkpoint-word-formation.yaml`, Item `читати`.
- **Original**: `pos: noun`
- **Problem**: `читати` is a verb.
- **Fix**: Change to `pos: verb`.

### Issue 6: Mark-the-Words Logic (Activities)
- **Location**: Activity 16 (mark-the-words).
- **Original**: `answers: [при, ви, Читач, читання, важлив, Україн, музич, київ]`
- **Problem**: The answers are substrings/roots. H5P "Mark the Words" usually selects whole words. If the user clicks `прийшов`, it might not match `при`.
- **Fix**: Change answers to full words: `[прийшов, вийшов, Читач, читання, важливість, Український, музичну, київське]`.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Act 16 | napisав | написав | Typo |
| Act 15 | Місто... — київський | Місто... — київське | Grammar/Agreement |
| Cont/Voc | сильність | сміливість / швидкість | Stylistic/Pedagogy |

## Fix Plan to Reach 9/10

### Content: 7.5/10 → 9/10

**What to fix:**
1.  **Section "Skill 2: Noun Suffixes"**: Replace `сильний → сила/сильність` with `сміливий → сміливість` (bold -> boldness). This provides a natural, high-frequency example of the `-ість` pattern.
2.  **Vocabulary File**: Remove `сильність`, add `сміливість`. Fix `читати` pos to `verb`.

### Activities: 6/10 → 9/10

**What to fix:**
1.  **Activity 10 (Cloze)**: Remove redundant `пере` in `Зробити ще раз = пере{переписати...}`.
2.  **Activity 15 (Cloze)**: Change `київський` to `київське` in the options for the `Місто` sentence.
3.  **Activity 16 (Mark-the-words)**: Fix `napisав` to `написав`. Update `answers` list to contain full words (`прийшов`, `вийшов`, etc.) instead of substrings.

## Verdict

**FAIL**

The module has a good structure, but is marred by careless errors in the activities (typos, agreement errors, broken logic) and a poor vocabulary choice (`сильність`) that misteaches a common pattern. These must be fixed before release.
```

**Current content** (the file you are fixing):
```
# Checkpoint - Word Formation

## Огляд

**Вітаємо!** Ви вивчили словотвір! Word formation is one of the most powerful tools in Ukrainian.

**Skills tested:**
1. **Verb Prefixes** - Can you use при-, ви-, пере-?
2. **Noun Suffixes** - Can you form -ння, -ість, -ач?
3. **Adjective Suffixes** - Can you use -ний, -овий, -ський?
4. **Root Families** - Can you recognize ход-, пис-, бач-?

> А потім... ми перевіримо все.

---

---

## Skill 1: Verb Prefixes

**Can you use prefixes to change verb meaning?**

### Model: Direction Prefixes

> **при-** = arrival, toward: прийти
> **ви-** = exit, out of: вийти
> **у-/в-** = entering: увійти
> **пере-** = across, re-do: перейти
> **від-** = away from: відійти
> **роз-** = spreading: розійтися

**Key patterns:**

| Prefix | Meaning | Example |
|--------|---------|---------|
| при- | arrival | прийти, приїхати, принести |
| ви- | exit | вийти, виїхати, винести |
| у-/в- | entering | увійти, в'їхати |
| пере- | across/re- | перейти, переписати |
| від- | away | відійти, відкрити |
| на- | onto/completion | написати, наклеїти |

### Practice: Choose the Right Prefix

1. Він _____йшов до класу. (arrived)
> [!solution] Перевірити
> прийшов — arrival = при-

2. Вона _____йшла з кімнати. (exited)
> [!solution] Перевірити
> вийшла — exit = ви-

3. Я _____писав текст. (rewrote)
> [!solution] Перевірити
> переписав — re-do = пере-

### Self-Check

- Do you know при- (arrival) vs ви- (exit)?
- Can you use пере- for «across» or «re-do»?
- Do you know від- (away) vs у- (into)?

> [!myth-buster] 🔍 Myth Buster
>
> **Myth:** «Ukrainian prefixes are the same as Russian.»
>
> **Truth:** While some prefixes look similar, Ukrainian has unique prefix patterns. For example, Ukrainian **від-** (away) is distinct from Russian, and forms like **відійти** show authentic Ukrainian phonology with the soft і. These prefixes trace back to Proto-Slavic, preserved independently in Ukrainian!

> [!history-bite] 📜 History Bite
>
> **Prefixes preserved our literature!** When the Ems Ukaz (1876) banned Ukrainian printing, writers used prefixes creatively. Ivan Franko's poetry is rich with **пере-**, **роз-**, **від-** combinations that carry uniquely Ukrainian meaning. Today, learning prefixes connects you to this literary heritage!

---

## Skill 2: Noun Suffixes

**Can you form nouns from verbs and adjectives?**

### Model: Suffixes That Create Nouns

> **-ння** = verbal noun (action): читати → **читання** (reading)
> **-ість** = abstract noun (quality): сміливий → **сміливість** (boldness)
> **-ач/-ик** = agent noun (person): читати → **читач** (reader)

**Patterns:**

| Suffix | Creates | Example |
|--------|---------|---------|
| -ння | action noun | писання, читання, малювання |
| -ість | quality noun | важливість, доброта, сміливість |
| -ач | agent (doer) | читач, слухач, глядач |
| -ник/-ик | agent/thing | письменник, підручник |

### Practice: Form the Noun

1. говорити → ___
> [!solution] Перевірити
> говоріння — verb + -ння = verbal noun

2. сміливий → ___
> [!solution] Перевірити
> сміливість — adjective → abstract noun

3. слухати → ___
> [!solution] Перевірити
> слухач — verb + -ач = agent noun

### Self-Check

- Can you form verbal nouns with -ння? (читання, писання)
- Can you form abstract nouns with -ість? (важливість, сміливість)
- Can you form agent nouns with -ач? (читач, слухач)

> [!tip] 🎯 Pro Tip: Suffix Patterns
>
> **-ння** = always neuter, always an action
> **-ість** = always feminine, always abstract quality
> **-ач** = always masculine, always a person who does something
>
> Once you memorize these three, you can predict the gender and meaning of hundreds of words!

---

## Skill 3: Adjective Suffixes

**Can you form adjectives from nouns?**

### Model: Suffixes That Create Adjectives

> **-ний** = relating to: музика → **музичний** (musical)
> **-овий** = made of/relating to: слово → **словниковий**
> **-ський** = nationality/place: Україна → **український**

**Patterns:**

| Suffix | Creates | Example |
|--------|---------|---------|
| -ний | general relation | музичний, важливий, цікавий |
| -овий | material/type | словниковий, кольоровий |
| -ський | place/nation | український, київський, європейський |

### Practice: Form the Adjective

1. Київ → ___
> [!solution] Перевірити
> київський — place + -ський

2. музика → ___
> [!solution] Перевірити
> музичний — noun + -ний

3. колір → ___
> [!solution] Перевірити
> кольоровий — noun + -овий

### Self-Check

- Can you form nationality adjectives with -ський? (український)
- Can you use -ний for general relation? (музичний)
- Do you know the difference: -ний vs -овий vs -ський?

> [!note] 📝 Word Formation Memory Aid
>
> **Quick suffix guide:**
> - **-ський** = place/nation: Київ → київський, Україна → український
> - **-ний** = general: музика → музичний, важливий
> - **-овий** = material/type: колір → кольоровий

---

## Skill 4: Root Families

**Can you recognize related words from the same root?**

### Model: Root = Core Meaning

> **Root ход-** (walk/go):
> вхід, вихід, перехід, пішохід, ходити, приходити

> **Root пис-** (write):
> писати, написати, переписати, письменник, писання

> **Root бач-** (see):
> бачити, побачення, передбачити, неможливо побачити

**Key roots:**

| Root | Meaning | Examples |
|------|---------|----------|
| ход- | walk/go | вхід, вихід, перехід |
| пис- | write | писати, письменник, писання |
| бач- | see | бачити, побачення |
| слух- | hear | слухати, слухач |
| говор-/мов- | speak | говорити, мова, розмова |

### Practice: Find the Root

1. вхід, вихід, перехід — what root?
> [!solution] Перевірити
> ход- — all relate to walking/going

2. письменник, писання, переписати — what root?
> [!solution] Перевірити
> пис- — all relate to writing

3. слухач, слухати, послухати — what root?
> [!solution] Перевірити
> слух- — all relate to hearing

### Self-Check

- Can you identify the root in compound words?
- Do you know: ход- (walk), пис- (write), бач- (see)?
- Can you guess new words using familiar roots?

> [!note] 📝 Root Family Practice Strategy
>
> **Step 1:** Learn the most common roots first:
> - **ход-** → вхід, вихід, перехід, пішохід, прихід
> - **пис-** → писати, написати, переписати, письменник, писанка
> - **бач-** → бачити, побачення, передбачити, вбачати
>
> **Step 2:** When you see a new word, look for the root!
> - Example: **підручник** = під + руч (рука) + ник
> - Example: **співробітник** = спів + робіт (робота) + ник
>
> **Step 3:** Practice creating new words from roots you know. This is the power of Ukrainian word formation!

**More common roots to learn:**

| Root | Meaning | Family Words |
|------|---------|--------------|
| **роб-/робіт-** | work | робота, робітник, співробітник, заробляти |
| **уч-/вч-** | learn | учень, учитель, навчання, вчитися |
| **жив-/жи-** | live | життя, живий, жити, проживати |
| **люб-** | love | любов, любити, полюбити |
| **зна-** | know | знати, знання, пізнання, незнайомий |

---

## Integration Challenge

Analyze these words by breaking them into parts:

1. **передбачити**
> [!solution] Перевірити
> перед + бач + ити

2. **письменник**
> [!solution] Перевірити
> пис + мен + ник

3. **важливість**
> [!solution] Перевірити
> важлив + ість

4. **український**
> [!solution] Перевірити
> Україн + ський

5. **читання**
> [!solution] Перевірити
> чита + ння

6. **перехід**
> [!solution] Перевірити
> пере + хід

> [!warning] ⚠️ Common Mistake
>
> Don't confuse:
> - **вхід** = entrance (в- = into)
> - **вихід** = exit (ви- = out)
> - **перехід** = crossing (пере- = across)
>
> All from root **ход-** (walk), but prefix changes meaning completely!

# Підсумок

| Skill | Key Pattern | Example |
|-------|-------------|---------|
| Prefixes | Change verb meaning | при-/ви-/пере- + йти |
| Noun Suffixes | -ння, -ість, -ач | читання, важливість, читач |
| Adj Suffixes | -ний, -овий, -ський | музичний, український |
| Root Families | Core meaning shared | ход-, пис-, бач- |

> 💡 **Лінгвістичний Інсайт**
>
> Якщо ви знаєте корінь, ви можете зрозуміти багато споріднених слів.
> *If you know the root, you can understand many related words.*

---

## Need More Practice?

To solidify your knowledge, try writing five sentences using the grammar patterns from this module. Use the vocabulary items provided in the sidecar to practice your new words in context!
```

**Current activities** (fix if review mentions activity issues):
```
---
- type: fill-in
  title: Word Formation Fill-In
  instruction: Заповніть пропуски правильною формою слова.
  items:
    - sentence: 'Він [___] до класу вчасно.'
      answer: прийшов
      options: [прийшов, вийшов, увійшов, перейшов]
    - sentence: 'Вона [___] з кімнати швидко.'
      answer: вийшла
      options: [вийшла, прийшла, увійшла, перейшла]
    - sentence: '[___] — це людина, яка читає книги.'
      answer: Читач
      options: [Читач, Читання, Читати, Читанка]
    - sentence: 'Це дуже [___] інформація.'
      answer: важлива
      options: [важлива, важливість, важливо, важливим]
    - sentence: 'Він [___] текст знову.'
      answer: переписав
      options: [переписав, написав, дописав, виписав]
    - sentence: 'Ми слухаємо [___] музику.'
      answer: українську
      options: [українську, Україна, українець, українці]
    - sentence: 'Це [___] театр у місті.'
      answer: музичний
      options: [музичний, музика, музикант, музичні]
    - sentence: 'Він відомий [___].'
      answer: письменник
      options: [письменник, писання, писати, письмо]
- type: match-up
  title: Word Formation Pairs
  pairs:
  - left: прийти
    right: при- prefix
  - left: вийти
    right: ви- prefix
  - left: читання
    right: -ння suffix
  - left: важливість
    right: -ість suffix
  - left: читач
    right: -ач suffix
  - left: музичний
    right: -ний suffix
  - left: український
    right: -ський suffix
  - left: словниковий
    right: -овий suffix
  - left: вхід
    right: ход- root
  - left: письменник
    right: пис- root
  - left: побачення
    right: бач- root
  - left: слухач
    right: слух- root
  instruction: З'єднайте відповідні елементи.
- type: cloze
  title: Formation Test
  passage: 'Місце, де входять = {вхід|вихід|перехід} Місце, де виходять = {вихід|вхід|прихід} Людина, яка читає = {читач|читання|читати}

    Дія читання = {читання|читач|читати} Якість бути важливим = {важливість|важливий|важливо} Прикметник від \«музика\» = {музичний|музика|музикант}

    Прикметник від \«Україна\» = {український|Україна|українець} Зробити ще раз = пере{переписати|написати|дописати} Прийти до місця = {прийти|вийти|увійти}

    Вийти з місця = {вийти|прийти|увійти} Людина, яка слухає = {слухач|слухати|послухати} Людина, яка пише = {письменник|писання|написати}'
  instruction: Заповніть пропуски, обравши правильні слова.
- type: quiz
  title: Word Formation Quiz
  items:
  - question: What is the primary meaning of the prefix «При-»?
    options:
    - text: Arrival
      correct: true
    - text: Exit
      correct: false
    - text: Re-do
      correct: false
    - text: Under
      correct: false
  - question: What is the primary meaning of the prefix «Ви-»?
    options:
    - text: Exit
      correct: true
    - text: Arrival
      correct: false
    - text: Entering
      correct: false
    - text: Over
      correct: false
  - question: What kind of words do you form with the suffix "-ння"?
    options:
    - text: Verbal nouns (Process)
      correct: true
    - text: Adjectives
      correct: false
    - text: Agent nouns (People)
      correct: false
    - text: Verbs (Actions)
      correct: false
  - question: What kind of words do you form with the suffix "-ість"?
    options:
    - text: Abstract nouns
      correct: true
    - text: Verbs (Actions)
      correct: false
    - text: Adjectives
      correct: false
    - text: Agent nouns (People)
      correct: false
  - question: What kind of words do you form with the suffix "-ач"?
    options:
    - text: Agent nouns
      correct: true
    - text: Abstract nouns (Concepts)
      correct: false
    - text: Verbal nouns
      correct: false
    - text: Adjectives
      correct: false
  - question: What is the main use of the suffix "-ський"?
    options:
    - text: Nationality/place adjectives
      correct: true
    - text: Abstract nouns
      correct: false
    - text: Verbs
      correct: false
    - text: Verbal nouns
      correct: false
  - question: What is the core meaning of the root «ход-»?
    options:
    - text: Walk/go (Movement)
      correct: true
    - text: Write (Text)
      correct: false
    - text: See (Vision)
      correct: false
    - text: Speak (Language)
      correct: false
  - question: What is the core meaning of the root «пис-»?
    options:
    - text: Write (Text)
      correct: true
    - text: Walk (Movement)
      correct: false
    - text: Hear (Audio)
      correct: false
    - text: Read (Text)
      correct: false
  - question: Can you identify how the Ukrainian word **«Перехід»** (Crossing) is structurally formed?
    options:
    - text: пере- + ход-
      correct: true
    - text: при- + хід
      correct: false
    - text: ви- + хід
      correct: false
    - text: під- + хід
      correct: false
  - question: What are the specific components that form the Ukrainian word **«Читання»** (Reading)?
    options:
    - text: чита- + -ння
      correct: true
    - text: чита- + -ач
      correct: false
    - text: чита- + -ість
      correct: false
    - text: чита- + -ник
      correct: false
  - question: Which suffix is used in the word «Український»?
    options:
    - text: -ський
      correct: true
    - text: -ний
      correct: false
    - text: -овий
      correct: false
    - text: -ість
      correct: false
  - question: Which suffix is used in the word «Музичний»?
    options:
    - text: -ний
      correct: true
    - text: -ський
      correct: false
    - text: -овий
      correct: false
    - text: -ач
      correct: false
  instruction: Оберіть правильну відповідь.
- type: group-sort
  title: Word Parts
  groups:
  - name: Prefixes
    items:
    - при-
    - ви-
    - пере-
    - від-
    - на-
    - роз-
  - name: Noun Suffixes
    items:
    - -ння
    - -ість
    - -ач
    - -ник
  - name: Adjective Suffixes
    items:
    - -ний
    - -овий
    - -ський
  - name: Roots
    items:
    - ход-
    - пис-
    - бач-
    - слух-
  instruction: Розподіліть елементи за групами.
- type: true-false
  title: Formation Rules
  items:
  - statement: «При-» = arrival.
    correct: true
    explanation: Correct! прийти = to arrive
  - statement: '"-ння" forms verbal nouns.'
    correct: true
    explanation: Yes! читання = reading
  - statement: '"-ість" forms verbs.'
    correct: false
    explanation: No! -ість forms abstract nouns
  - statement: «Ход-» relates to movement.
    correct: true
    explanation: Correct! вхід, вихід, перехід
  - statement: '"-ач" forms agent nouns.'
    correct: true
    explanation: Yes! читач = reader
  - statement: «Ви-» means "entry."
    correct: false
    explanation: No! Ви- means exit
  - statement: «Пере-» means "across" or "re-do."
    correct: true
    explanation: Correct! перехід, переписати
  - statement: '"-ський" relates to place/nationality.'
    correct: true
    explanation: Yes! український, київський
  - statement: «Слух-» means seeing.
    correct: false
    explanation: No! Слух- means hearing
  - statement: Prefixes change verb meaning.
    correct: true
    explanation: Correct! при- vs ви- vs пере-
  - statement: Suffixes do not change part of speech.
    correct: false
    explanation: No! Suffixes create new POS
  - statement: Root families share core meaning.
    correct: true
    explanation: Yes! ход- = all about walking
  instruction: Визначте, чи твердження правильне.
- type: unjumble
  title: Word Formation Rules
  items:
  - words:
    - префікс
    - змінює
    - значення
    - слова
    - і
    - стоїть
    - на
    - початку
    answer: Префікс змінює значення слова і стоїть на початку
  - words:
    - суфікс
    - стоїть
    - в
    - кінці
    - слова
    - і
    - створює
    - нові
    - частини
    - мови
    answer: Суфікс стоїть в кінці слова і створює нові частини мови
  - words:
    - корінь
    - це
    - головна
    - частина
    - слова
    - яка
    - має
    - основне
    - значення
    answer: Корінь це головна частина слова яка має основне значення
  - words:
    - ми
    - вживаємо
    - суфікс
    - ач
    - для
    - назви
    - людей
    - які
    - діють
    answer: Ми вживаємо суфікс ач для назви людей які діють
  - words:
    - українська
    - мова
    - має
    - дуже
    - багату
    - систему
    - словотвору
    - слів
    answer: Українська мова має дуже багату систему словотвору слів
  - words:
    - треба
    - знати
    - корені
    - слів
    - щоб
    - розуміти
    - нові
    - слова
    answer: Треба знати корені слів щоб розуміти нові слова
  instruction: Розташуйте слова у правильному порядку.
- type: cloze
  title: Complete the Words
  passage: 'Він {прийшов|вийшов|увійшов} до класу.

    Вона {вийшла|прийшла|увійшла} з кімнати.

    {Читач|Читання|Читати} — це людина, яка читає.

    {Читання|Читач|Читати} — це дія читати.

    {Важливість|Важливий|Важливо} — це якість бути важливим.

    Місто, де я народився — {київський|Київ|київському}.

    Ми переходимо вулицю через {перехід|вхід|вихід}.

    Він пише книги, він {письменник|писати|читач}.

    Цей прапор — {український|Україна|українець}.

    {Слухач|Співак|Танцюрист} слухає музику.

    Цей інструмент — {музичний|музика|музикант}.

    Ось {вхід|вихід|схід} у магазин.'
  instruction: Заповніть пропуски, обравши правильні слова.
- type: mark-the-words
  title: Find Word Parts
  text: Він прийшов до школи. Потім вийшов з неї. --- Читач любить читання. Він читає про важливість освіти. --- Український письменник napisав музичну п''єсу про київське життя.
  answers:
  - при
  - ви
  - Читач
  - читання
  - важлив
  - Україн
  - музич
  - київ
  instruction: Клацніть на слова, що відповідають критерію.
- type: translate
  title: English to Ukrainian
  items:
  - source: Entrance
    options:
    - text: вхід
      correct: true
    - text: вихід
      correct: false
    - text: Неправильно
      correct: false
  - source: Exit
    options:
    - text: вихід
      correct: true
    - text: вхід
      correct: false
    - text: Неправильно
      correct: false
  - source: Reading
    options:
    - text: читання
      correct: true
    - text: читач
      correct: false
    - text: Неправильно
      correct: false
  - source: Reader
    options:
    - text: читач
      correct: true
    - text: читання
      correct: false
    - text: Неправильно
      correct: false
  - source: Importance
    options:
    - text: важливість
      correct: true
    - text: важливий
      correct: false
    - text: Неправильно
      correct: false
  - source: Musical
    options:
    - text: музичний
      correct: true
    - text: музика
      correct: false
    - text: Неправильно
      correct: false
  - source: Ukrainian
    options:
    - text: український
      correct: true
    - text: Україна
      correct: false
    - text: Неправильно
      correct: false
  - source: Writer
    options:
    - text: письменник
      correct: true
    - text: писання
      correct: false
    - text: Неправильно
      correct: false
  - source: To arrive
    options:
    - text: прийти
      correct: true
    - text: вийти
      correct: false
    - text: Неправильно
      correct: false
  - source: To exit
    options:
    - text: вийти
      correct: true
    - text: прийти
      correct: false
    - text: Неправильно
      correct: false
  - source: To rewrite
    options:
    - text: переписати
      correct: true
    - text: написати
      correct: false
    - text: Неправильно
      correct: false
  - source: Crossing
    options:
    - text: перехід
      correct: true
    - text: вихід
      correct: false
    - text: Неправильно
      correct: false
  instruction: Оберіть правильний переклад.
- type: translate
  title: Word Formation Translation
  items:
  - source: The writer
    options:
    - text: Письменник
      correct: true
    - text: Писати
      correct: false
    - text: Письмовий
      correct: false
  - source: Ukrainian (adj.)
    options:
    - text: Український
      correct: true
    - text: Україна
      correct: false
    - text: Українець
      correct: false
  - source: Entrance
    options:
    - text: Вхід
      correct: true
    - text: Входити
      correct: false
    - text: Вихід
      correct: false
  - source: Exit
    options:
    - text: Вихід
      correct: true
    - text: Виходити
      correct: false
    - text: Вхід
      correct: false
  - source: A listener
    options:
    - text: Слухач
      correct: true
    - text: Слухати
      correct: false
    - text: Слух
      correct: false
  - source: Scientific
    options:
    - text: Науковий
      correct: true
    - text: Наука
      correct: false
    - text: Науковець
      correct: false
  instruction: Оберіть правильний переклад.
- type: error-correction
  title: Word Formation Errors
  instruction: Знайдіть і виправте помилки в словотворенні.
  items:
    - sentence: 'Це дуже важливість книга для мене.'
      error: важливість
      answer: важлива
      options: [важливість, важлива, важливо, важливості]
      explanation: 'Потрібен прикметник «важлива», а не іменник «важливість».'
    - sentence: 'Читання прийшов до бібліотеки.'
      error: Читання
      answer: Читач
      options: [Читання, Читач, Читати, Читав]
      explanation: 'Людина — «читач» (-ач), а не дія «читання» (-ння).'
    - sentence: 'Вона приходила з магазину.'
      error: приходила
      answer: виходила
      options: [приходила, виходила, уходила, переходила]
      explanation: '«З магазину» означає вихід, тому потрібен префікс ви-.'
    - sentence: 'Він музика грає на піаніно.'
      error: музика
      answer: музикант
      options: [музика, музикант, музичний, музично]
      explanation: 'Людина — «музикант», а не іменник «музика».'
    - sentence: 'Це київська місто.'
      error: київська
      answer: київське
      options: [київська, київське, київський, київські]
      explanation: '«Місто» — середній рід, тому «київське».'
    - sentence: 'Письмення — це моя улюблена діяльність.'
      error: Письмення
      answer: Писання
      options: [Письмення, Писання, Писач, Письма]
      explanation: 'Вірний суфікс для дії — «-ння»: писання.'

```

**Current vocabulary** (fix if review mentions vocabulary issues):
```
---
module: 44-checkpoint-word-formation
level: A2
version: '2.0'
items:
- lemma: вбачати
  ipa: /ʋbat͡ʃˈatɪ/
  translation: to see, to perceive
  pos: verb
- lemma: сильність
  ipa: /sɪlʲnistʲ/
  translation: strength
  pos: noun
  gender: f
- lemma: спів
  ipa: /spiʋ/
  translation: singing
  pos: noun
  gender: m
- lemma: читати
  ipa: /t͡ʃɪtˈa/
  translation: to read
  pos: noun
  gender: f
- lemma: інсайт
  ipa: /insˈajt/
  translation: insight
  pos: noun
  gender: m

```

**Plan file** (source of truth for scope — check if fixes align):
```
module: a2-44
level: A2
sequence: 44
slug: checkpoint-word-formation
version: '2.0'
title: 'Checkpoint: Word Formation'
subtitle: Review and Mastery Assessment
content_outline:
- section: Огляд
  words: 95
  points:
  - Skills overview
  - Checkpoint goals
- section: 'Skill 1: Verb Prefixes'
  words: 234
  points:
  - Direction prefixes
  - Practice exercises
  - Myth Buster and History
- section: 'Skill 2: Noun Suffixes'
  words: 156
  points:
  - Verbal noun -ння
  - Abstract noun -ість
  - Agent noun -ач
- section: 'Skill 3: Adjective Suffixes'
  words: 117
  points:
  - General relation -ний
  - Material/type -овий
  - Place/nation -ський
- section: 'Skill 4: Root Families'
  words: 256
  points:
  - Core root meaning
  - Root recognition practice
  - Extended root families
- section: Integration Challenge
  words: 95
  points:
  - Word analysis practice
  - Common mistakes
- section: Підсумок
  words: 50
  points:
  - Summary table
  - Linguistic insight
word_target: 1000
vocabulary_hints:
  required:
  - корінь (root)
  - префікс (prefix)
  - суфікс (suffix)
  - слово (word)
  - утворення (formation)
  - значення (meaning)
  - помилка (error)
  - правильний (correct)
  recommended:
  - морфема (morpheme)
  - аналіз (analysis)
  - синтез (synthesis)
  - похідний (derivative)
activity_hints:
- type: quiz
  focus: Word formation comprehensive
  items: 12
- type: fill-in
  focus: Create correct forms
  items: 12
- type: error-correction
  focus: Fix formation errors
  items: 8
- type: match-up
  focus: Root families and meanings
  items: 12
- type: group-sort
  focus: Sort by suffix types
  items: 12
- type: cloze
  focus: Word formation in context
  items: 12
- type: unjumble
  focus: Word formation sentences
  items: 8
- type: translate
  focus: Form equivalents
  items: 8
focus: checkpoint
pedagogy: TTT
prerequisites:
- a2-43 (WF Mastery)
connects_to:
- a2-45 (Food and Cooking)
objectives:
- Demonstrate confidence in identifying root families
- Deduce meaning using morphological clues
- Form words using correct prefixes and suffixes
- Correct common word formation errors
grammar:
- Word formation comprehensive review
- Root families review
- Prefix/suffix application
register: розмовний
phase: A2.4 [Word Formation]

```

**Research notes** (reference for factual accuracy):
```
# Research Notes: A2 M44 Checkpoint - Word Formation

**Track**: l2-uk-en
**Module**: checkpoint-word-formation
**Level**: A2
**Researched**: 2026-02-08

## 1. Grammar: State Standard 2024 Reference

According to the **Державний стандарт української мови як іноземної (2024)**, word formation (Словотвір) requirements for Level A2 are outlined in **Catalog V (Зміст мовної компетентності), Section 4.3**:

> **4.3. Словотвір.**
> 4.3.1. Ступені порівняння якісних прикметників: проста форма вищого ступеня: солодший, важливіший; проста форма найвищого ступеня: найсолодший, найважливіший...
> 4.3.2. Видові пари дієслів: робити – зробити, ділити – поділити, писати – написати, виходити – вийти, забувати – забути.

*Note: While the standard formally places noun/adjective/adverb formation suffixes in Level B1 (§4.3.3–4.3.7), this curriculum introduces them in A2 to build a richer vocabulary through pattern recognition, reflecting the "Theory-First" approach.*

## 2. Vocabulary Frequency

At the A2 level, focus is on high-frequency roots and productive patterns that expand communicative range without overwhelming the student.

### High-Frequency Bases and Derivatives
- **Verbs of Motion (Prefixation):**
  - **іти/їхати** → *прийти/приїхати* (arrival), *вийти/виїхати* (exit), *перейти/переїхати* (cross).
- **Agent/Occupation Suffixes:**
  - **-ар/-яр:** *лікар* (doctor), *школяр* (schoolboy), *кухар* (cook).
  - **-ач:** *викладач* (teacher), *читач* (reader).
  - **-тель:** *вчитель* (teacher).
- **Diminutive Suffixes (Highly Productive):**
  - **-ик/-ок:** *стіл → столик*, *дім → будинок*.
  - **-к(а):** *рука → ручка*, *книга → книжка*, *вода → водічка*.
- **Abstract/Action Nouns:**
  - **-ння/-ття:** *читання* (reading), *навчання* (studying), *життя* (life).

### Common Collocations
- *робити запис* (to make a record/note)
- *дати відповідь* (to give an answer — from *відповідати*)
- *місце навчання* (place of study)

## 3. Cultural Hook

1. **Diminutives as Emotional Language:** In Ukrainian, diminutives (*пестливі слова*) are not just for children or "small" things. They are a vital tool for expressing intimacy, politeness, and affection (*ласкавість*). Calling someone "Оленка" or asking for "кавуся" (coffee) creates a warm, hospitable atmosphere. This is a distinctive feature of the Ukrainian "soul" and linguistic etiquette.
2. **Surnames and Identity:** Many Ukrainian surnames are living examples of word formation patterns. Suffixes like **-енко** (son of, e.g., Шевченко) and **-ук/-юк** (Western Ukrainian origin, e.g., Бондарчук) reflect the historical development of the language and family structures.

## 4. Pedagogical Notes

- **Root Identification:** Students often struggle with vowel shifts in the root (*чергування*) during word formation (e.g., *стіл* → *столик*, *кіт* → *котик*). It is helpful to present these as "logical shifts" for ease of pronunciation.
- **Gender Consistency:** Nouns formed with specific suffixes often have a fixed gender. For example, all nouns ending in **-ння** (derived from verbs) are neuter. Teaching the suffix and the gender as a package reduces errors.
- **Prefix Meaning vs. Aspect:** Students should distinguish between prefixes that purely change aspect (*писати* → *написати*) and those that add lexical meaning (*писати* → *виписати* - to write out/extract).
- **Comparison with English:** English often uses separate words or adjectives (e.g., "little table"), whereas Ukrainian internalizes the meaning into the word structure (*столик*).

## 5. Scope Boundaries

### In Scope
- **Cases:** All 6 main cases (Nominative, Accusative, Locative, Genitive, Dative, Instrumental) and the **Vocative** (*Кличний відмінок*).
- **Aspect:** Basic imperfective/perfective pairs.
- **Prefixes:** Primary motion verb prefixes (*при-, ви-, пере-, за-, по-, в-, з-*) and aspectual prefixes (*на-, з-, по-*).
- **Suffixes:** Basic agentive (-ар, -ач), diminutive (-ик, -к-), and deverbal (-ння).
- **Adjectives:** Comparative and Superlative forms.

### Out of Scope
- **Participles & Gerunds:** Forms like *читаючий* or *прочитавши* are B1/B2 level.
- **Complex Suffixes:** Collective nouns (*-ство*, e.g., *козацтво*) or specialized scientific suffixes.
- **Passive Voice:** Complex passive constructions (though simple reflexive forms like *відчиняється* may be familiar).
- **Archaic/Poetic Word Formation:** Rare suffixes used in folklore but not in daily life.

```

## Your Task

1. Read the review file completely — focus on:
   - **"Critical Issues Found"** section
   - **"Fix Plan to Reach 9/10"** section
   - **"Ukrainian Language Issues"** table
2. For each fix listed, apply it to the correct file
3. Output the COMPLETE fixed files (not diffs, not partial)

### Rules

1. **Apply EVERY fix** from the Fix Plan — do not skip any, even if they require adding substantial content
2. **Scope your changes** — change/add ONLY what the Fix Plan specifies, leave unflagged sections untouched
3. **Adding content IS expected** — if the Fix Plan says "add a table", "add examples", "add vocabulary to the section", you MUST add it. This is not "rewriting" — it's applying the fix.
4. **Preserve structure** — keep the same H2/H3 headings, same activity order, same vocabulary order
5. **Preserve voice** — do not change the writing style of unflagged content
6. **Activities YAML must be bare list at root** — no `activities:` wrapper
7. **Vocabulary YAML keeps its header** — preserve `module:`, `level:`, `version:`, `items:` structure
8. **If a fix is ambiguous**, choose the option that matches the plan file
9. **Never output "no changes needed"** — if the Fix Plan lists fixes, there ARE changes to make. Read more carefully.

### What NOT to Do

- Do NOT rewrite the entire file — only change what the Fix Plan says
- Do NOT add engagement boxes unless the Fix Plan says to
- Do NOT change IPA unless the Fix Plan flags specific IPA errors
- Do NOT remove content unless the Fix Plan says to remove it
- Do NOT request skills, delegate to Claude, or skip fixes
- Do NOT add commentary — just output the fixed files

## Output Format

**CRITICAL: You MUST output fixed files between delimiter lines. Delimiters must appear on their own line, NOT inside code blocks.**

Output ONLY the files that need changes. If a file has no fixes, skip it entirely.

For EACH file that needs changes, output the COMPLETE file between these EXACT delimiter lines:

**Content fixes** — put the delimiter on its own line, then the complete markdown, then the end delimiter:

===CONTENT_START===
(complete fixed content markdown — ALL of it, not just changed parts)
===CONTENT_END===

**Activity fixes** — same pattern:

===ACTIVITIES_START===
(complete fixed activities YAML — bare list at root, NO `activities:` wrapper)
===ACTIVITIES_END===

**Vocabulary fixes** — same pattern:

===VOCABULARY_START===
(complete fixed vocabulary YAML — with module/level/version/items header)
===VOCABULARY_END===

**After all files, report what you changed:**

===CHANGES_START===
## Applied Fixes

1. [File: content] Line {N}: {what changed} — {which review issue this addresses}
2. [File: activities] Activity "{title}", Item {N}: {what changed} — {which review issue}
3. [File: vocabulary] Added/removed: {lemma} — {which review issue}

## Fixes NOT Applied (explain why)

- {If any fix was unclear or contradictory, explain here}

## Files Changed: {list: content, activities, vocabulary — or subset}
## Files Unchanged: {list of files that needed no fixes}
===CHANGES_END===

## Boundaries

- Do NOT output files that have no changes — only output what you fixed
- Do NOT fabricate fixes — only apply what the review specified
- Do NOT change the module's pedagogical approach or structure
- Do NOT add vocabulary not in the plan unless the Fix Plan explicitly says to
- If you cannot apply a fix, explain why in the "Fixes NOT Applied" section
- If you encounter `NEEDS_HELP:` situations, report them clearly


## FIX PREVIOUS ERRORS
Your previous attempt failed validation with these errors:

```
Your output was truncated (missing end delimiter). Please continue exactly where you left off, starting from the last complete sentence.
```

Please fix these issues and regenerate the content.