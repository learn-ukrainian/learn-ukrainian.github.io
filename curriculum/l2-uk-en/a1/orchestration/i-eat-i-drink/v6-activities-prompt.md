<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/i-eat-i-drink.yaml` file for module **37: I Eat, I Drink** (a1).

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

- `<!-- INJECT_ACTIVITY: verb-conjugation-drill -->`
- `<!-- INJECT_ACTIVITY: accusative-form-builder -->`
- `<!-- INJECT_ACTIVITY: noun-change-sorting -->`
- `<!-- INJECT_ACTIVITY: accusative-choice-quiz -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- blanks:
  - Я їм (риба) {рибу}.
  - Вона п'є (вода) {воду}.
  - Він їсть (хліб) {хліб}.
  - Ми п'ємо (молоко) {молоко}.
  - Вони їдять (каша) {кашу}.
  - Ти п'єш (кава) {каву}.
  - Я їм (суп) {суп}.
  - Вона їсть (картопля) {картоплю}.
  focus: Form the accusative case for feminine (-а/-я → -у/-ю) and masculine/neuter
    (no change)
  items: 8
  type: fill-in
- focus: Select the correct accusative form to complete the sentence
  items: 6
  questions:
  - Я п'ю... (каву / кава / кави)
  - Він їсть... (рибу / риба / рибі)
  - Ми п'ємо... (сік / соку / соком)
  - Вона їсть... (м'ясо / м'ясу / м'яса)
  - Вони п'ють... (воду / вода / воді)
  - Ти їш... (кашу / каша / каші)
  type: quiz
- blanks:
  - Я {їм} суп.
  - Ми {п'ємо} чай.
  - Вона {їсть} хліб.
  - Вони {п'ють} воду.
  - Ти {їси} рибу?
  - Ви {п'єте} каву?
  - Він {п'є} сік.
  - Вони {їдять} кашу.
  focus: Conjugate the verbs їсти (irregular) and пити (Group I)
  items: 8
  type: fill-in
- focus: Sort nouns based on how they change in the accusative case (inanimate)
  groups:
  - items:
    - кава
    - вода
    - риба
    - каша
    name: Змінюється (-у/-ю)
  - items:
    - хліб
    - сік
    - молоко
    - м'ясо
    name: Не змінюється (як у називному)
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- кашу (porridge — accusative)
- картоплю (potato — accusative)
- сметану (sour cream — accusative)
- їсть (he/she eats)
- п'є (he/she drinks)
- їдять (they eat)
- п'ють (they drink)
required:
- їсти (to eat — irregular)
- пити (to drink)
- їм (I eat)
- п'ю (I drink)
- каву (coffee — accusative)
- воду (water — accusative)
- рибу (fish — accusative)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги

In Ukraine, food is not just fuel; it is the center of social life and hospitality. Asking someone **Що ти їси?** (What are you eating?) or sharing a lunch break is a primary way colleagues and friends bond during the workday. Food vocabulary is universally essential, but in Ukrainian, it also acts as the perfect introduction to how verbs and nouns interact. As you will see, Ukrainians make a strict distinction between what you "eat" and what you "drink" — even when it comes to liquid dishes like soup. This topic introduces the absolute foundation of your survival vocabulary and the crucial accusative case, which you will use every single day.

> **Тарас:** Привіт! Що ти їш на сніданок? *(Hi! What are you eating for breakfast?)*
> **Ірина:** Я їм кашу і п'ю каву. *(I eat porridge and drink coffee.)*
> **Тарас:** А Олена? *(And Olena?)*
> **Ірина:** Вона їсть хліб з маслом і п'є чай. *(She eats bread with butter and drinks tea.)*
> **Тарас:** А діти? *(And the children?)*
> **Ірина:** Вони їдять яйця і п'ють молоко. *(They eat eggs and drink milk.)*

The dialogue above uses the high-frequency question **Що ти їш?** (What are you eating?) and the response **Я їм...** (I am eating...). Notice the contrast between the verbs: **їш** is highly irregular and does not look like the infinitive **їсти** (to eat), while **п'єш** follows a more recognizable pattern from its dictionary form **пити** (to drink). The distinction between singular and plural present tense forms is fundamental because you will often speak on behalf of your family or group (**ми їмо**, **вони п'ють**).

> **Колега 1:** Що ви їсте на обід? *(What are you eating for lunch?)*
> **Колега 2:** Ми їмо суп і салат. А що п'єте? *(We eat soup and salad. And what are you drinking?)*
> **Колега 1:** Ми п'ємо воду або сік. Я сьогодні їм бутерброд і п'ю чай. А ти? *(We drink water or juice. Today I eat a sandwich and drink tea. And you?)*
> **Колега 2:** Я їм салат і п'ю каву. Я теж хочу суп. *(I eat a salad and drink coffee. I also want soup.)*
> **Колега 1:** Добре, замовляй! Я ще хочу воду потім. *(Okay, order! I still want water later.)*

## Їсти і пити

The verb **їсти** (to eat) is a unique, highly irregular verb in Ukrainian grammar. It belongs to neither Group I nor Group II verb conjugations, making it a true exception. Because it is an essential daily action that you will use in almost every conversation about food, you simply need to memorize its forms. Pay close attention to the endings, as they shift noticeably between the singular and plural forms. Here is the full paradigm:

| English | Ukrainian |
|---------|-----------|
| I eat | я **їм** |
| You (singular) eat | ти **їси** |
| He/she eats | він/вона **їсть** |
| We eat | ми **їмо** |
| You (plural/formal) eat | ви **їсте** |
| They eat | вони **їдять** |

:::tip
**Pronouncing the letter Ї**
The letter **ї** always represents two distinct sounds: the consonant **й** and the vowel **і**. You must pronounce it fully, sounding similar to the English word "yee". It is never reduced to just a single **і** sound.
:::

Here are three examples using different subjects to practice this sound:
- **Я їм суп.** (I eat soup.)
- **Ми їмо яблуко.** (We eat an apple.)
- **Діти їдять банан.** (The children eat a banana.)
- **Він їсть сир.** (He eats cheese.)

The verb **пити** (to drink) is a bit friendlier for learners. It officially follows the Group I conjugation pattern, but it features a unique spelling shift in the present tense. Notice how the vowel **и** completely disappears from the stem, and the endings start with an apostrophe, resulting in the distinct sounds **'ю** or **'є**. This apostrophe indicates a brief pause before the soft vowel. Here is the complete paradigm:

| English | Ukrainian |
|---------|-----------|
| I drink | я **п'ю** |
| You (singular) drink | ти **п'єш** |
| He/she drinks | він/вона **п'є** |
| We drink | ми **п'ємо** |
| You (plural/formal) drink | ви **п'єте** |
| They drink | вони **п'ють** |

Ukrainians use the direct verb **пити** for almost all beverages. Unlike English, where you might casually say "I am having a drink" or "I will take a coffee," in Ukrainian you must always explicitly state "I drink." It is a highly frequent verb that pairs directly with almost any liquid you can consume. Notice how the direct object immediately follows the verb:
- **Я п'ю воду.** (I drink water.)
- **Ти п'єш каву.** (You drink coffee.)
- **Вони п'ють сік.** (They drink juice.)
- **Ми п'ємо чай.** (We drink tea.)

<!-- INJECT_ACTIVITY: verb-conjugation-drill -->

A uniquely Ukrainian cultural quirk is the strict "Soup Rule." In Ukraine, you always "eat" (**їсти**) thick liquid dishes like soup and borscht with a spoon. You never "drink" them from a bowl, even if they are primarily liquid. Contrast this with true beverages like tea, juice, or fruit compote, which you always "drink" (**пити**). Using the wrong verb sounds immediately unnatural to a native speaker. For example: **Я їм борщ. Я п'ю чай.** (I eat borscht. I drink tea.)

## Знахідний відмінок — неживе

When you eat or drink something, that food item becomes the direct object of your action. In Ukrainian grammar, the direct object requires a specific form called the Accusative Case (**Знахідний відмінок**). This case is the workhorse of everyday communication because you constantly interact with objects around you.

:::note
**The "Що?" Trigger**
The Ukrainian school system effectively teaches students to identify the accusative case by asking the mental trigger question: «Бачу що? Бачу кого?» (I see what? I see whom?). When dealing with inanimate food items, asking yourself **що?** (what?) signals that you must use the accusative form for the noun that follows: **Я їм (що?) хліб. Я п'ю (що?) каву.**
:::

There is excellent news for masculine and neuter inanimate nouns: they undergo absolutely no change in this situation. The accusative form looks exactly the same as the standard dictionary (nominative) form. Therefore, masculine words like **хліб** (bread), **суп** (soup), **бутерброд** (sandwich), and **сік** (juice), as well as neuter words like **молоко** (milk) and **яйце** (egg), remain completely identical when they become the object of your action. This makes learning the accusative case much easier for beginners, as you only need to focus on the sentence structure rather than changing the word.
- **хліб** → **хліб**: **Я їм хліб.** (I eat bread.)
- **суп** → **суп**: **Я їм суп.** (I eat soup.)
- **сік** → **сік**: **Я п'ю сік.** (I drink juice.)
- **молоко** → **молоко**: **Я п'ю молоко.** (I drink milk.)
- **яйце** → **яйце**: **Я їм яйце.** (I eat an egg.)

The primary grammatical change at the A1 level happens with feminine nouns. When a feminine noun ends in **-а**, it strictly shifts to **-у** in the accusative case. If it ends in **-я**, it shifts to **-ю**. This simple but crucial vowel change immediately signals to the listener that the noun is the direct object receiving the action. You must actively practice this transformation until it becomes a natural reflex. Notice how the endings transform in these highly common daily examples:
- **вода** → **воду**: **Я п'ю воду.** (I drink water.)
- **кава** → **каву**: **Я п'ю каву.** (I drink coffee.)
- **риба** → **рибу**: **Я їм рибу.** (I eat fish.)
- **каша** → **кашу**: **Я їм кашу.** (I eat porridge.)
- **сметана** → **сметану**: **Я хочу сметану.** (I want sour cream.)
- **картопля** → **картоплю**: **Я їм картоплю.** (I eat potato.)

<!-- INJECT_ACTIVITY: accusative-form-builder -->

<!-- INJECT_ACTIVITY: noun-change-sorting -->

This foundational accusative rule applies to many other essential verbs too, particularly the verb **хотіти** (to want). When you order food at a cafe or restaurant, you will often use the polite, fixed chunk **Мені, будь ласка...** (To me, please...) followed immediately by the accusative object. Even though the main verb is implied rather than spoken out loud, the food item is still acting as the direct object receiving the action, so the accusative rules remain exactly the same.
- **Мені, будь ласка, піцу і воду.** (To me, please, pizza and water.)
- **Я хочу каву.** (I want coffee.)
- **Він хоче рибу і сік.** (He wants fish and juice.)
- **Вона хоче чай.** (She wants tea.)

<!-- INJECT_ACTIVITY: accusative-choice-quiz -->

## Підсумок — Summary

The core grammar of eating and drinking relies heavily on two essential verbs and one critical case change. The verb **їсти** (to eat) is completely irregular and its unique forms (**я їм, ти їси, він їсть**) must be memorized through repetition. The verb **пити** (to drink) is a Group I verb with a specific spelling shift that adds an apostrophe (**я п'ю, ти п'єш**). Most importantly, you must remember that when you eat or drink a feminine item ending in **-а**, you must actively change that ending to **-у** (**вода** → **воду**).

:::caution
**Watch out for Russianisms!**
A very common mistake for beginners is using the Russian word *кофе* instead of the authentic Ukrainian noun **кава**. Always remember to order **каву**! Additionally, ensure you use the Ukrainian word **сир** for both hard cheese and cottage cheese at this level; actively avoid the Russianism *творог*.
:::

To quickly recap the Accusative Inanimate rules: masculine and neuter nouns equal their dictionary nominative forms exactly, while feminine nouns take **-у** or **-ю**. You can clearly see this when you compare the masculine object **Я п'ю сік** (no change) with the feminine object **Я п'ю каву** (changed to **-у**).

Test your memory of these critical concepts before you finish the module:
- Can you conjugate the irregular verb **їсти** for all pronouns from memory? (Try recalling: **Я їм**, **ти їси**, **вони їдять**)
- Can you conjugate the verb **пити** without looking at the table? (Try recalling: **Я п'ю**, **він п'є**, **ми п'ємо**)
- Test yourself: **Я їм ___** (**риба** → **рибу**). **Я п'ю ___** (**вода** → **воду**).
- Say three things you eat today, ensuring you use the correct accusative form: **Я їм...** (e.g., **суп, яблуко**)
- Say three things you drink today, using the correct accusative form: **Я п'ю...** (e.g., **чай, сік**)
- What is the correct accusative form of the feminine noun **картопля**? (Answer: **картоплю**)

If you can confidently answer these questions, you are ready to order your favorite meals in a Ukrainian cafe!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: i-eat-i-drink
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

**Level: A1.4+ (Module 37/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


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

### Pattern: grammar-verbs-present [§4.2.4.1]
**Дієвідмінювання в теперішньому часі** (Present tense conjugation)
- **fill-in** — Відмінюй дієслово: Вставити правильну форму дієслова за особою та числом / Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Розподілити дієслова за типом дієвідміни / Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Зіставити особові займенники з формами дієслова / Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Знайти неправильно відмінене дієслово та виправити / Find incorrectly conjugated verb and fix it
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує відмінювання. Англійські дієслова не змінюються за особами

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
