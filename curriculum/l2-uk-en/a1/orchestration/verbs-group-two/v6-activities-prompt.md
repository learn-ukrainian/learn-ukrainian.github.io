<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/verbs-group-two.yaml` file for module **17: Verbs Group II** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-conjugation-paradigm -->`
- `<!-- INJECT_ACTIVITY: group-sort-verbs -->`
- `<!-- INJECT_ACTIVITY: quiz-verb-choice -->`
- `<!-- INJECT_ACTIVITY: fill-in-translation-context -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Conjugate: я говор__, ти говор__, він говор__'
  items: 10
  type: fill-in
- focus: Sort verbs into Group I (-ати) and Group II (-ити)
  items: 10
  type: group-sort
- focus: 'Choose correct form: Ти (бачу/бачиш/бачить) це?'
  items: 8
  type: quiz
- focus: 'Complete with correct verb form: Вона ___ українською. (говорити)'
  items: 6
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- дивитися (to watch — reflexive preview)
- вчитися (to learn — reflexive preview)
- любити (to love — review, Group II!)
- трохи (a little)
- добре (well)
- увечері (in the evening)
required:
- говорити (to speak)
- бачити (to see)
- робити (to do/make)
- вчити (to study/teach)
- просити (to ask/request)
- ходити (to go/walk regularly)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

When you step into a lively Ukrainian environment, you will immediately notice people performing physical actions and describing their personal abilities. We meet our good friends **Тарас** (Taras) and **Микола** (Mykola) at the local gym. This active setting provides the perfect real-world context for the highly practical verbs of the second verb family. You need these specific action words to talk about physical activities, daily routines, and skills. Observe their conversation as they exercise together. They use entirely new action words to describe their fitness routine.

> **Тарас:** Ти говориш українською? *(Do you speak Ukrainian?)*
> **Микола:** Так, я говорю трохи. А ти? *(Yes, I speak a little. And you?)*
> **Тарас:** Я бачу, що ти добре говориш! *(I see that you speak well!)*
> **Микола:** Дякую, я вчуся. *(Thanks, I am learning.)*

This dialogue establishes the natural flow of these specific verbs in casual, everyday conversation. You can clearly see how **Тарас** and **Микола** use verb forms like **бачиш** (you see) and **говоримо** (we speak). These verbs follow a completely different ending pattern than the **читаєш** (you read) verbs you learned previously in Module 16. In Ukrainian grammar, we call this new category the Second Conjugation or **Друга дієвідміна** (Second Conjugation). This new verb family requires its own unique set of vowel sounds in the endings.

Later that same day, the two friends experience a shift to a much quieter setting. They are now at home and discuss their evening plans. This situation focuses heavily on the verbs **дивитися** (to watch) and **вчити** (to study or teach).

> **Тарас:** Що ти робиш увечері? *(What are you doing in the evening?)*
> **Микола:** Я дивлюся фільм. А ти? *(I am watching a movie. And you?)*
> **Тарас:** Я вчу нові слова. *(I am studying new words.)*
> **Микола:** Молодець! *(Well done!)*

Note: **дивлюся** (I watch) — the **-ся** ending means "oneself" (preview for M20). This evening exchange previews the reflexive suffix in a very natural way. You will learn more about this specific reflexive ending soon, but you can already start using it as a memorized vocabulary word.

## Друга дієвідміна (Group II Verbs)

Most Group II verbs can be easily identified by their infinitive ending. You must contrast this with the **-ати** pattern of Group I verbs. The characteristic vowel for all these new endings is the sound **-и-** (or occasionally **-ї-**). This persistent vowel sound makes the Second Conjugation the "I-type" verb group.

We break down the conjugation paradigm using the highly frequent verb **говорити** (to speak). The root stem is **говор-**. You add the personal endings directly to this stem. Group II verbs have infinitive in **-ити** (or **-іти**): **говорити** → **я говорю**, **ти говориш**, **він/вона говорить**, **ми говоримо**, **ви говорите**, **вони говорять**. Pattern: stem + **-ю**/**-у**, **-иш**, **-ить**, **-имо**, **-ите**, **-ять**/**-ать**. 

<!-- INJECT_ACTIVITY: fill-in-conjugation-paradigm -->

To build your basic vocabulary, you must memorize these six essential Group II verbs. They appear constantly in daily Ukrainian speech. Six essential Group II verbs: **говорити** (to speak): **говорю**, **говориш**, **говорить**... **бачити** (to see): **бачу**, **бачиш**, **бачить**... **робити** (to do/make): **роблю**, **робиш**, **робить**... **вчити** (to study/teach): **вчу**, **вчиш**, **вчить**... **просити** (to ask/request): **прошу**, **просиш**, **просить**... **ходити** (to go/walk regularly): **ходжу**, **ходиш**, **ходить**... Here is a short sentence for each to show them in action:

*   **Вона вчить мову.** (She teaches the language.)
*   **Ми ходимо у парк.** (We walk to the park.)
*   **Ви просите воду.** (You ask for water.)

There is a special phonetic rule for verbs whose stems end in hissing sibilant sounds like **ч**, **ш**, **ж**, and **щ**. After these hissing sounds, the **я** ending becomes **-у** (instead of **-ю**) and the **вони** ending becomes **-ать** (instead of **-ять**). We use **бачити** (to see) and **вчити** (to study) as the primary examples of this rule. You write **я бачу** and **вони бачать**. You write **я вчу** and **вони вчать**.

:::caution
This rule is a strict requirement for Ukrainian melody. You must never write forms like *бачять or *вчять. The hissing consonants completely block the letter **я**.
:::

## Група I чи II? (Which Group?)

To master Ukrainian verbs, you must create a clear contrast between Group I (the "E-type") and Group II (the "I-type"). Compare the endings side by side:

| Особa | Group I (-ати) | Group II (-ити) |
| :--- | :--- | :--- |
| **я** | **читаю** | **говорю** |
| **ти** | **читаєш** | **говориш** |
| **він / вона** | **читає** | **говорить** |
| **вони** | **читають** | **говорять** |

Key difference: **ти** form → **-єш** (I) vs **-иш** (II), **вони** → **-ють** (I) vs **-ять**/**-ать** (II). Note: after sibilants (**ч**, **ш**, **ж**, **щ**) → **-ать** (not **-ять**): **бачать** (not *бачять), **кричать**. Other consonants → **-ять**: **говорять**, **ходять**.

<!-- INJECT_ACTIVITY: group-sort-verbs -->

<!-- INJECT_ACTIVITY: quiz-verb-choice -->

Ukrainian pronunciation prioritizes **милозвучність** (euphony or melody). Because of this focus on melody, some Group II verbs change their last stem consonant. However, this consonant change happens ONLY in the **я** (I) form.

:::tip
You can reassure yourself that the rest of the conjugation paradigm (**ти**, **він**, **ми**, **ви**, **вони**) remains perfectly regular. You only need to remember the consonant change for the first person singular.
:::

Here is the breakdown of the specific consonant changes in Group II (**я**-form only). Do not try to memorize the shift as a complex mechanical rule. Instead, learn each specific **я** form together as part of the verb's unique identity. Consonant changes in Group II (**я**-form only): **робити** → **роблю** (**б**→**бл**), **ходити** → **ходжу** (**д**→**дж**), **просити** → **прошу** (**с**→**ш**), **бачити** → **бачу** (no change). These changes only affect the **я**-form — all other forms are regular. Don't memorize the rule — just learn each **я**-form with the verb.

<!-- INJECT_ACTIVITY: fill-in-translation-context -->

You will frequently encounter the reflexive suffix **-ся** attached to the end of certain action words. We use this suffix with verbs like **вчитися** (to learn/study) and **дивитися** (to watch). This special suffix always attaches right after the conjugated personal ending. For example, **я вчу** plus **ся** becomes **я вчуся**. In the second person, **ти вчиш** plus **ся** becomes **ти вчишся**. Note that this suffix generally indicates an action that is directed back at the speaker or describes a continuous state of being.

## Підсумок — Summary

You now know the two major verb families in the Ukrainian language. You can reinforce your memory using a simple mnemonic trick. The **вони** form is the absolute best way to double-check the group. Two verb groups — two ending patterns: Group I (**-ати**): **-ю**, **-єш**, **-є**, **-ємо**, **-єте**, **-ють** Group II (**-ити**): **-ю**/**-у**, **-иш**, **-ить**, **-имо**, **-ите**, **-ять**.

:::note
If you are ever unsure which group a verb belongs to, simply test the third person plural form. If it ends in **-ють**, it is Group I. If it ends in **-ять**, it is Group II.
:::

Consonant shifts in Group II **я**-form (**роблю**, **ходжу**, **прошу**). Remember the important consonant shifts that occur exclusively in the **я** (I) form for certain verbs. You must apply these shifts correctly to sound natural. You must also remember the sibilant rule for the third person plural, which forces you to say **вони бачать** (they see) instead of using the standard ending. Mastering these specific Group II verbs unlocks your fundamental ability to describe almost all basic daily activities and personal skills.

Use this self-check question and answer list to verify your understanding of the module's core objectives. Read each question carefully and try to answer before looking at the solution.

*   **Question:** Self-check: Conjugate **бачити** for **я**, **ти**, **він/вона**.
*   **Answer:** The correct forms are **я бачу**, **ти бачиш**, and **він/вона бачить**.
*   **Question:** Is **слухати** Group I or II? How about **говорити**?
*   **Answer:** The verb **слухати** is Group I, because the infinitive ends in **-ати**, and the **ти**-form is **слухаєш**. The verb **говорити** is Group II, because it uses the **-иш** ending.
*   **Question:** What happens to the letter **д** in the **я** form of the verb **ходити** (to walk)?
*   **Answer:** The letter changes to **дж**, making the correct form **я ходжу**.
*   **Question:** What is the correct grammatical ending for the **вони** (they) pronoun in Group II?
*   **Answer:** The standard ending is **-ять**, but it changes to **-ать** after hissing sibilants.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: verbs-group-two
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

**Level: A1.2-A1.3 (Module 17/55) — EARLY BEGINNER**

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
