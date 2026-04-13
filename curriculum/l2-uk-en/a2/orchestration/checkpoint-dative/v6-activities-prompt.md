<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-dative.yaml` file for module **23: Контрольна робота — давальний відмінок** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 10 | 10+ | inline + workbook combined |
| Inline (lesson tab) | 3 | 5 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 7 | 10 | extended practice |
| Items per activity | 10 | — | each activity must have at least 10 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 3 inline activities AND at least 7 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** quiz, true-false, fill-in, match-up, group-sort, classify, mark-the-words
- **Inline priority (preferred):** fill-in, match-up, true-false
- **Workbook types:** cloze, error-correction, fill-in, unjumble, translate, match-up, group-sort, odd-one-out, quiz, true-false, mark-the-words, observe, phrase-table
- **Workbook priority (preferred):** error-correction, cloze, unjumble, translate, fill-in
- **FORBIDDEN at this level:** anagram, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, highlight-morphemes, grammar-identify

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 3–5 quick checks after key teaching points. Workbook = 7–10 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: quiz-dative-recognition -->`
- `<!-- INJECT_ACTIVITY: fill-in-dative-endings -->`
- `<!-- INJECT_ACTIVITY: match-up-dative-verbs -->`
- `<!-- INJECT_ACTIVITY: error-correction-dative -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Identify the dative form among case options (recognition — Part 1 material)
  items: 8
  type: quiz
- focus: Complete sentences with correct dative noun/adjective/pronoun endings (Part
    2 material)
  items: 8
  type: fill-in
- focus: Match dative-governing verbs to correct case forms and sentence completions
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
- закінчення (ending (grammar))
- чергування (alternation (grammar))
- узгодження (agreement (grammar))
required:
- давальний відмінок (dative case)
- допомагати (to help)
- дякувати (to thank)
- подобатися (to be pleasing to, to like)
- подарувати (to give as a gift)
- надіслати (to send)
- потрібно (necessary, needed)
- холодно (cold (impersonal state))


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Частина 1: Розпізнавання

> **Організатор:** Що подарувати Олексієві? *(What should we give to Oleksiy?)*
> **Колега 1:** Книгу! *(A book!)*
> **Організатор:** А Наталці? *(And to Natalka?)*
> **Колега 2:** Шоколад! *(Chocolate!)*
> **Організатор:** Новому колезі — чашку. *(To the new colleague — a cup.)*
> **Колега 1:** А шефу — вино. *(And to the boss — wine.)*

The office Secret Santa game revolves around matching people with gifts. When you talk about the recipient or the addressee of an action — the person who receives the book, the chocolate, or the wine — you are using the **давальний відмінок** *(dative case)*. The name of the case comes from the verb **давати** *(to give)*, which perfectly describes its primary function in the Ukrainian language. Whether you give a present, write an email, or tell a story, the person on the receiving end always takes the **давальний відмінок** *(dative case)*.

To accurately identify the **давальний відмінок** *(dative case)* in a sentence, you must ask the questions **кому?** *(to whom?)* or **чому?** *(to what?)*. These questions separate the recipient of an action from other grammatical roles. A common challenge for learners is confusing the **давальний відмінок** *(dative case)* with the locative case, because many feminine nouns share the exact same **закінчення** *(ending (grammar))* in both cases. You can distinguish them by the question they answer and the presence of a preposition. The locative case answers **на/у кому? на/у чому?** *(on/in whom? on/in what?)* and is always accompanied by a preposition. The dative case usually functions without a preposition.

*   **Ми дали білочці горішки.** *(We gave the squirrel some nuts.)* — **кому?** *(to whom?)* — **давальний відмінок** *(dative case)*.
*   **Руда шубка на білочці.** *(The red coat is on the squirrel.)* — **на кому?** *(on whom?)* — locative case.
*   **Я допомагаю сестрі.** *(I help my sister.)* — **кому?** *(to whom?)* — **давальний відмінок** *(dative case)*.

The **давальний відмінок** *(dative case)* is also fundamental for expressing physical or emotional states in impersonal constructions. When describing how someone feels, Ukrainian often uses a dative experiencer rather than a nominative active subject. A state happens to you, rather than you actively doing it. Compare the nominative subject sentence **Я замерзла.** *(I froze. - active verb)* with the impersonal dative state **Мені холодно.** *(I am cold [cold is happening to me]. - state)*. This structure is essential for expressing needs and impressions.

*   **Мені потрібно працювати.** *(I need to work.)*
*   **Тобі холодно?** *(Are you cold?)*
*   **Йому здається, що це помилка.** *(It seems to him that this is a mistake.)*
*   **Вам потрібно зачекати.** *(You need to wait.)*
*   **Нам не холодно.** *(We are not cold.)*

To form these sentences, you must match the nominative personal pronouns to their dative counterparts: **я** → **мені**, **ти** → **тобі**, **він/воно** → **йому**, **вона** → **їй**, **ми** → **нам**, **ви** → **вам**, **вони** → **їм**.

This same logic applies to the verb **подобатися** *(to be pleasing to, to like)*. Ukrainian uses a syntax inversion compared to English. The person who likes something is the *experiencer* in the **давальний відмінок** *(dative case)*, and the object being liked is the grammatical subject in the nominative case. The verb agrees with the object, not the person.

*   **Мені подобається новий планшет.** *(I like the new tablet. / The new tablet is pleasing to me.)*
*   **Їй подобаються квіти.** *(She likes flowers. / The flowers are pleasing to her.)*
*   **Йому не подобається ця кава.** *(He does not like this coffee.)*
*   **Нам подобається Київ.** *(We like Kyiv.)*

<!-- INJECT_ACTIVITY: quiz-dative-recognition -->

## Частина 2: Вибір форми

When forming the **давальний відмінок** *(dative case)* for masculine and neuter nouns, Ukrainian offers unique flexibility. For masculine nouns, there are parallel forms: **-ові / -еві / -єві** and **-у / -ю**. Both are entirely correct, but the endings **-ові / -еві / -єві** are distinctively Ukrainian and add a natural, authentic rhythm to the language. When speaking about people, these longer endings are highly preferred. Neuter nouns take the endings **-у / -ю**.

*   **батько** → **батькові / батьку** *(to the father)*
*   **учитель** → **учителеві / учителю** *(to the teacher)*
*   **Андрій** → **Андрієві / Андрію** *(to Andriy)*
*   **село** → **селу** *(to the village)*
*   **море** → **морю** *(to the sea)*

If you have two masculine nouns in a row, Ukrainians often mix the endings to avoid repetition, for example, **панові директору** *(to Mr. Director)* rather than using the same ending twice.

For feminine nouns, the standard **закінчення** *(ending (grammar))* is **-і**. However, when the noun's stem ends in the consonants **г, к,** or **х**, a mandatory consonant **чергування** *(alternation (grammar))* occurs before the **-і** ending. The consonant **г** changes to **з'**, **к** changes to **ц'**, and **х** changes to **с'**. This phonetic shift is a hallmark of the Ukrainian language and must be memorized.

*   **подруга** → **подрузі** *(to the friend)* — **г** becomes **з'**
*   **ріка** → **ріці** *(to the river)* — **к** becomes **ц'**
*   **муха** → **мусі** *(to the fly)* — **х** becomes **с'**
*   **Ольга** → **Ользі** *(to Olha)*
*   **аптека** → **аптеці** *(to the pharmacy)*

When you add adjectives or possessive pronouns to a noun, you must apply strict **узгодження** *(agreement (grammar))*. The modifier must match the noun's case, gender, and number. In the **давальний відмінок** *(dative case)*, masculine and neuter modifiers take the ending **-ому**, feminine modifiers take **-ій**, and all plural modifiers take **-им**.

*   **моєму новому колезі** *(to my new colleague)* — masculine singular
*   **твоєму великому місту** *(to your big city)* — neuter singular
*   **моїй старшій сестрі** *(to my older sister)* — feminine singular
*   **нашим добрим друзям** *(to our good friends)* — plural

Verb government—the case a verb dictates for its object—often differs between English and Ukrainian. English speakers frequently use direct objects where Ukrainian requires an indirect object in the **давальний відмінок** *(dative case)*. For instance, you see a mother (accusative case: **бачити маму**), but you help a mother (dative case: **допомагати мамі**). High-frequency verbs that always govern the dative case include: **давати** *(to give)*, **подарувати** *(to give as a gift)*, **допомагати** *(to help)*, **дякувати** *(to thank)*, and **радити** *(to advise)*.

*   **Я дякую вчителю.** *(I thank the teacher.)*
*   **Він радить братові.** *(He advises the brother.)*

These rules come together in everyday communicative applications, such as a visit to the post office or a delivery service.

> **Працівник:** Кому ви хочете надіслати пакунок? *(To whom do you want to send the package?)*
> **Клієнт:** Своєму братові в Київ. *(To my brother in Kyiv.)*
> **Працівник:** А цей лист? *(And this letter?)*
> **Клієнт:** Моїй старій подрузі. *(To my old friend.)*

In this dialogue, the customer demonstrates full noun phrase agreement working seamlessly in a natural scenario, matching possessives, adjectives, and nouns perfectly in the **давальний відмінок** *(dative case)*.

<!-- INJECT_ACTIVITY: fill-in-dative-endings -->
<!-- INJECT_ACTIVITY: match-up-dative-verbs -->

## Частина 3: Продукування

Building complete sentences with verbs governing the **давальний відмінок** *(dative case)* requires attention to natural word order. While Ukrainian word order is flexible, the most standard and clear structure is: Subject + Verb + Dative Recipient + Accusative Object. The recipient usually precedes the direct object.

*   **Я дарую своєму другові цікаву книгу.** *(I am giving my friend an interesting book.)*
*   **Ми надіслали бабусі довгий лист.** *(We sent grandmother a long letter.)*
*   **Вчитель дає студентам нове завдання.** *(The teacher gives the students a new task.)*
*   **Вона радить моїй сестрі хороший фільм.** *(She recommends a good movie to my sister.)*

When you produce complex sentences with the verb **подобатися** *(to be pleasing to, to like)*, you must integrate full noun phrases correctly. The verb must always agree in number—singular or plural—with the nominative subject (the thing being liked). Meanwhile, the experiencer phrase—the person who likes it, including any adjectives or possessive pronouns—remains entirely in the **давальний відмінок** *(dative case)*.

*   **Моєму старшому братові подобаються нові автомобілі.** *(My older brother likes new cars.)* — **автомобілі** is plural, so the verb is **подобаються**.
*   **Цій маленькій дівчинці подобається шоколад.** *(This little girl likes chocolate.)* — **шоколад** is singular, so the verb is **подобається**.
*   **Нашим іноземним гостям подобається борщ.** *(Our foreign guests like borsch.)*

The **давальний відмінок** *(dative case)* is also exclusively used to express age. Ukrainian does not use the verb "to be" to say someone is a certain age. Instead, it uses the dative case for the person experiencing the age, combined with the number of years. This applies to both simple pronouns and expanded noun phrases.

*   **Скільки років вашій сестрі?** *(How old is your sister?)*
*   **Моєму синові десять років.** *(My son is ten years old.)*
*   **Моєму найкращому другові двадцять один рік.** *(My best friend is twenty-one years old.)*
*   **Скільки тобі років?** *(How old are you?)*
*   **Мені тридцять років.** *(I am thirty years old.)*

You will frequently use the **давальний відмінок** *(dative case)* when writing short addresses, formal greetings in letters, or email salutations. A full dative noun phrase—combining an adjective, a title, and a name—is the standard way to address someone in writing. Be explicitly careful not to use the genitive case for dedications or monuments, a mistake sometimes made through direct translation from other languages. A monument is always dedicated *to* someone.

*   **Шановному пану директору** *(To the respected Mr. Director)*
*   **Дорогій Олені** *(To dear Olena)*
*   **Це пам'ятник Тарасові Шевченкові.** *(This is a monument to Taras Shevchenko.)*
*   **Це подарунок моїй мамі.** *(This is a gift for my mom.)*

## Огляд помилок та порівняння відмінків

Even advanced learners occasionally stumble with the **давальний відмінок** *(dative case)*. One of the most common errors is mixing adjective endings, such as incorrectly saying **моєму сестрі** instead of the grammatically correct **моїй сестрі**. Another frequent mistake is forgetting the **г/к/х** consonant **чергування** *(alternation (grammar))* in feminine nouns. You must never write or say **подругі**; it must always be **подрузі**. Finally, beware of the direct translation trap with the verb **дякувати** *(to thank)*. Because "thank you" takes a direct object in English, learners often say **Дякую вас** (accusative). This is incorrect. You must use the dative case: **Дякую вам**.

To consolidate your knowledge, review this summary comparison chart formatting the nominative, genitive, and dative endings for full phrases. Notice how the modifiers and nouns shift together.

| Відмінок *(Case)* | Чоловічий рід *(Masculine)* | Жіночий рід *(Feminine)* |
| :--- | :--- | :--- |
| **Називний** *(Nom)* | мій новий дім | моя старша сестра |
| **Родовий** *(Gen)* | мого нового дому | моєї старшої сестри |
| **Давальний** *(Dat)* | моєму новому дому / домові | моїй старшій сестрі |

<!-- INJECT_ACTIVITY: error-correction-dative -->

Before moving on, review this self-assessment checklist to ensure your mastery:
*   Чи можете ви утворити давальний відмінок від свого імені? *(Can you form the dative case from your name?)*
*   Чи знаєте ви, як сказати про свій вік та вік друзів? *(Do you know how to talk about your age and the age of friends?)*
*   Чи пам'ятаєте ви три дієслова, які завжди вимагають давального відмінка? *(Do you remember three verbs that always require the dative case?)*

## Підсумок

The **давальний відмінок** *(dative case)* is a cornerstone of conversational Ukrainian, bridging the gap between simply describing objects and interacting with people. It is the grammatical tool that allows you to offer gifts, give advice, express your age, and describe your feelings or needs. By mastering the core questions **кому?** and **чому?**, you can accurately identify the recipient of any action. 

You have now reviewed the essential **закінчення** *(ending (grammar))* for all genders, including the distinctly Ukrainian parallel masculine forms like **-ові** and **-еві**, and the vital consonant alternations in feminine nouns. You have practiced strict **узгодження** *(agreement (grammar))* across adjectives, possessive pronouns, and nouns. Most importantly, you understand the critical verb government for verbs like **допомагати** *(to help)*, **дякувати** *(to thank)*, and **подобатися** *(to be pleasing to, to like)*, breaking free from English syntax patterns. Recognizing these structures ensures your Ukrainian sounds natural, polite, and deeply authentic as you prepare to integrate these skills into more complex dialogues in the upcoming modules.
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-dative
level: a2

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (10 total / 3–5 inline / 7–10 workbook,
# 10+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 10 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 10 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 10 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 10 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 10 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 10 pairs total

  - id: group-sort-gender
    type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Чоловічий рід"
        items: ["стіл", "олівець", "будинок"]   # ≥ 3 items per group
      - label: "Жіночий рід"
        items: ["книга", "ручка", "школа"]
      - label: "Середній рід"
        items: ["вікно", "море", "молоко"]

  - id: true-false-grammar
    type: true-false
    instruction: "Правда чи ні?"
    items:                     # ← real output: ≥ 10 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 10 items total

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
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]. **CRITICAL: use `____` (four underscores) for the blank, NOT `{word}` curly-brace syntax. Example: `sentence: "Це ____ кімната."` with `answer: "моя"`. The validator REJECTS `{word}` format.**
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

**Level: A2 (Module 23/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 10 activities.** Inline: 3–5. Workbook: 7–10. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 10 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 10.
- **Lower minimums for specific types only:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items, essay-response/critical-analysis = 1 prompt.
- If you can't think of enough items, add more examples from the module's vocabulary and content. NEVER ship a 1-item or 2-item activity unless its type cap explicitly allows it.
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

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **at least 3** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 7** workbook activities.
- [ ] **Total ≥ 10.**
- [ ] **Every** activity has **at least 10** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 3 and 5. I did NOT create more injection markers than 5.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
