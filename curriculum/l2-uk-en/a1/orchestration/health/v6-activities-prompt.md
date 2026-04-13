<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/health.yaml` file for module **53: Health** (a1).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 10 | 10+ | inline + workbook combined |
| Inline (lesson tab) | 4 | 6 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 6 | 9 | extended practice |
| Items per activity | 6 | — | each activity must have at least 6 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 4 inline activities AND at least 6 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** image-to-letter, letter-grid, match-up, watch-and-repeat, quiz, true-false, fill-in, classify
- **Inline priority (preferred):** image-to-letter, match-up, fill-in, quiz, watch-and-repeat
- **Workbook types:** fill-in, match-up, group-sort, anagram, unjumble, quiz, true-false, classify, divide-words, count-syllables, pick-syllables, observe, phrase-table, odd-one-out
- **Workbook priority (preferred):** fill-in, match-up, group-sort, anagram, unjumble
- **FORBIDDEN at this level:** cloze, error-correction, mark-the-words, translate, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, highlight-morphemes, grammar-identify, select

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 4–6 quick checks after key teaching points. Workbook = 6–9 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: fill-in-dialogues -->`
- `<!-- INJECT_ACTIVITY: match-up-body-parts -->`
- `<!-- INJECT_ACTIVITY: fill-in-symptoms -->`
- `<!-- INJECT_ACTIVITY: quiz-logical-response -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match body parts to their English translations.
  items:
  - голова == head
  - живіт == stomach
  - горло == throat
  - спина == back
  - рука == hand/arm
  - нога == leg/foot
  - зуб == tooth
  - око == eye
  type: match-up
- focus: Complete the sentence with the correct symptom or body part.
  items:
  - У мене болить {голова|рука|нога}. Я хочу спати.
  - У мене болить {живіт|вухо|око}. Я не хочу їсти.
  - У мене болить {горло|спина|ніс} і є температура. Я не можу говорити.
  - У мене {кашель|нежить|зуб}, я постійно кашляю.
  - У мене болить {зуб|голова|нога}, мені потрібен стоматолог.
  - Я {хворий|лікар|аптека}. У мене болить голова і спина.
  type: fill-in
- focus: Choose the logical response to the health problem.
  items:
  - options:
    - Ось таблетки від головного болю.
    - Ось краплі від нежиті.
    - Випийте сироп від кашлю.
    question: У мене болить голова.
  - options:
    - Вам потрібні таблетки від кашлю.
    - Ось краплі для носа.
    - У мене болить зуб.
    question: У мене сильний кашель.
  - options:
    - У мене болить горло.
    - Я лікар.
    - Де аптека?
    question: Що у вас болить?
  - options:
    - Ось краплі, будь ласка.
    - У мене болить спина.
    - Це таблетки від головного болю.
    question: Добрий день. Дайте, будь ласка, щось від нежиті.
  type: quiz
- focus: At the pharmacy or doctor - using target chunks.
  items:
  - Дайте, {будь ласка|добрий день|дякую}, таблетки від головного болю.
  - Що у вас {болить|хворий|лікар}?
  - У мене {температура|аптека|лікар} і болить горло.
  - Мені {погано|хворий|добре}. Викличте лікаря!
  - Де тут найближча {аптека|голова|спина}? Мені потрібні ліки.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- спина (back, f)
- око (eye, n)
- вухо (ear, n)
- зуб (tooth, m)
- ніс (nose, m)
- температура (fever/temperature, f)
- кашель (cough, m)
- нежить (runny nose, f)
- таблетка (pill, f)
- хворий (sick, adj)
required:
- голова (head, f)
- горло (throat, n)
- живіт (stomach, m)
- рука (hand/arm, f)
- нога (leg/foot, f)
- болить (hurts — chunk: у мене болить)
- лікар (doctor, m)
- аптека (pharmacy, f)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Dialogues

Falling ill is an unfortunate but universal part of human life. When you travel or live in a new environment, knowing how to explain your physical condition is an essential survival skill. You need to know how to explain exactly what hurts in Ukrainian. This module introduces the two most important locations for handling health issues: the doctor's office (**лікар** (doctor, m)) and the pharmacy (**аптека** (pharmacy, f)). You will learn practical, everyday phrases to navigate both situations with confidence and clarity.

**Це велика лікарня.** (This is a big hospital.)
**Тут працює гарний лікар.** (A good doctor works here.)
**А там є аптека.** (And there is a pharmacy there.)
**Я купую ліки тут.** (I buy medicine here.)
> *This is a big hospital. A good doctor works here. And there is a pharmacy there. I buy medicine here.*

Observe a practical conversation between a patient (**Пацієнт**) and a medical professional (**Лікар**). Pay close attention to how the patient describes their condition and how the doctor responds.

> **Лікар:** Що у вас болить? *(What hurts you?)*
> **Пацієнт:** У мене болить голова і горло. *(My head and throat hurt.)*
> **Лікар:** Давно? *(Since when?)*
> **Пацієнт:** З учора. І в мене температура. *(Since yesterday. And I have a fever.)*
> **Лікар:** Ви кашляєте? *(Do you cough?)*
> **Пацієнт:** Так, трохи. І в мене нежить. *(Yes, a little. And I have a runny nose.)*
> **Лікар:** Зрозуміло. Це застуда. *(Understood. This is a cold.)*
> **Лікар:** Я випишу ліки. Відпочивайте! *(I will prescribe medicine. Rest!)*
> **Пацієнт:** Дякую, лікарю! *(Thank you, doctor!)*

This first dialogue demonstrates the core interaction at a clinic. The doctor always asks the foundational question: «**Що у вас болить?**» (What hurts you?). The patient responds using the most common structure for expressing pain: «**У мене болить...**». Notice how the dialogue also introduces common symptoms like **температура** (fever/temperature, f) and **нежить** (runny nose, m). You do not need complex medical terminology to communicate effectively; these simple chunks are entirely sufficient for a general diagnosis.

Now, observe a typical conversation at a pharmacy when buying medicine.

> **Пацієнт:** Добрий день! У мене болить голова. *(Good day! My head hurts.)*
> **Пацієнт:** Дайте, будь ласка, таблетки. *(Give me pills, please.)*
> **Фармацевт:** Від головного болю? *(For a headache?)*
> **Пацієнт:** Так. І від кашлю, будь ласка. *(Yes. And for a cough, please.)*
> **Фармацевт:** Ось, будь ласка. Ще щось? *(Here you go, please. Anything else?)*
> **Пацієнт:** А є щось від нежитю? *(And is there anything for a runny nose?)*
> **Фармацевт:** Так, ось краплі. *(Yes, here are drops.)*
> **Пацієнт:** Дякую! Скільки це коштує? *(Thank you! How much does this cost?)*

:::tip
In Ukraine, you can easily recognize a pharmacy (**аптека**) by a large illuminated green cross on the building exterior. Many common medications that require a prescription in other countries might be available directly from the pharmacist over the counter.
:::

<!-- INJECT_ACTIVITY: fill-in-dialogues -->

## Тіло (The Body)

Before you can accurately explain what hurts to a doctor, you must know the names of your basic body parts (**частини тіла**). We start with the most common terms you might need in a medical situation. The vocabulary for the head and face area is fundamental. Memorize these basic nouns:

* **голова** (head, f)
* **око** (eye, n)
* **вухо** (ear, n)
* **зуб** (tooth, m)
* **ніс** (nose, m)
* **горло** (throat, n)

The essential words for the torso and the limbs are crucial for describing general aches and pains that occur below the neck.

* **спина** (back, f)
* **живіт** (stomach, m)
* **рука** (hand/arm, f)
* **нога** (leg/foot, f)

:::note
In Ukrainian, the word **рука** refers to the entire arm, including the hand. Similarly, the word **нога** refers to the entire leg, including the foot. You do not need separate words for "hand" or "foot" in basic everyday communication; the context makes your meaning perfectly clear.
:::

You must remember that noun gender (masculine, feminine, neuter) remains an important concept here. As taught in previous modules, the gender of a body part dictates the adjective agreement when you describe it. Recognizing the gender helps reinforce your grammatical reflex for building accurate sentences. Look at these clear examples demonstrating the pattern:

* **велика голова** (big head — feminine)
* **велике око** (big eye — neuter)
* **великий живіт** (big stomach — masculine)
* **великий ніс** (big nose — masculine)
* **велика рука** (big arm — feminine)
* **велике вухо** (big ear — neuter)

At the A1 level, do not worry about building highly complex anatomical descriptions. Your main focus is simply recognizing these body parts in their basic dictionary form so that they can be paired with the verb **болить** (hurts — chunk: у мене болить). Knowing these nouns in the nominative case is enough for most beginner interactions. When you visit an **аптека** or a **лікар**, you will point to the specific area and use these exact base forms. You are building a foundational vocabulary that will serve as the basis for all future medical conversations.

**Це мій новий друг.** (This is my new friend.)
**У нього велика голова.** (He has a big head.)
**У нього довга рука.** (He has a long arm.)
**А це його нога.** (And this is his leg.)
> *This is my new friend. He has a big head. He has a long arm. And this is his leg.*

<!-- INJECT_ACTIVITY: match-up-body-parts -->

## У мене болить... (It Hurts...)

The magic conversational chunk for expressing physical pain is: «**У мене болить...**» (I have a pain in... / My ... hurts). This phrase literally translates to "at me hurts." You should memorize this sequence as a fixed, invariable phrase. Do not attempt to analyze the grammar cases or the sentence structure behind it right now. Just learn the chunk and apply it exactly as native speakers do.

This construction is the absolute most common and natural way that native Ukrainian speakers express discomfort. It is much more authentic than trying to directly translate the English possessive structure "my head hurts." You can easily combine this magic chunk with the newly learned body parts. The body part always remains in its basic nominative case. Here are practical examples of this pattern in action:

* **У мене болить голова.** (My head hurts.)
* **У мене болить живіт.** (My stomach hurts.)
* **У мене болить горло.** (My throat hurts.)
* **У мене болить спина.** (My back hurts.)
* **У мене болить зуб.** (My tooth hurts.)
* **У мене болить рука.** (My arm hurts.)

:::tip
If multiple parts hurt, the verb form changes to plural to match the multiple body parts. For recognition purposes only, note the plural form: **У мене болять зуби** (My teeth hurt). At this early stage, you should focus entirely on mastering the singular form.
:::

Beyond specific body parts, there are other common symptoms that act as fixed chunks. These phrases describe general medical conditions rather than localized physical pain. Memorize them exactly as they appear in these examples:

* **У мене температура.** (I have a fever.)
* **У мене кашель.** (I have a cough.)
* **У мене нежить.** (I have a runny nose.)

Finally, we teach general states of feeling unwell. When your entire body feels wrong or you are generally ill, you can express your condition using these short phrases:

* **Мені холодно.** (I'm cold.)
* **Мені погано.** (I feel bad.)
* **Я хворий.** (I'm sick. — masculine speaker)
* **Я хвора.** (I'm sick. — feminine speaker)

Notice the masculine and feminine adjective agreement for the word **хворий** (sick, adj). You must choose the specific form that matches your own gender when speaking about yourself.

**Сьогодні я весь день вдома.** (Today I am at home all day.)
**Я дуже хвора зараз.** (I am very sick now.)
**У мене болить живіт.** (My stomach hurts.)
**Мені дуже погано.** (I feel very bad.)
> *Today I am at home all day. I am very sick now. My stomach hurts. I feel very bad.*

<!-- INJECT_ACTIVITY: fill-in-symptoms -->

## Summary

The «Health toolkit» you have built in this module groups vocabulary into clear, highly practical categories. Your essential body parts include: **голова** (head), **горло** (throat), **живіт** (stomach), **спина** (back), **рука** (hand/arm), **нога** (leg/foot), **око** (eye), **вухо** (ear), **зуб** (tooth), and **ніс** (nose).

Your key symptom phrases revolve around a single, highly reliable pattern: «**У мене болить...**» followed by the body part in the nominative case. You can also state broad conditions like: **У мене температура**, **У мене кашель**, and **У мене нежить**. Finally, to describe your general state of being, you use the phrases: **Я хворий** (or **Я хвора**) and **Мені погано**. This core vocabulary allows you to handle the vast majority of standard medical complaints.

You must also remember the most critical phrases for interacting at the doctor's office or pharmacy. Always be ready for the doctor's standard diagnostic question: «**Що у вас болить?**». When you need medication, use the polite request: «**Дайте таблетки від...** [symptom], **будь ласка**». Pay special attention to the specific word forms used after the preposition «від» (for/from):

* **від головного болю** (for a headache)
* **від кашлю** (for a cough)
* **від нежитю** (for a runny nose)

These are advanced genitive forms, but you can easily learn them as highly useful set phrases right now, ensuring you get exactly the **таблетка** (pill, f) you need.

**Сьогодні мій друг вдома.** (Today my friend is at home.)
**Він дуже хворий.** (He is very sick.)
**У нього болить голова.** (His head hurts.)
**Він приймає таблетки.** (He takes pills.)
> *Today my friend is at home. He is very sick. His head hurts. He takes pills.*

Take a moment for a final self-check with these questions:

* How do you say "My throat hurts and I have a fever"? (**У мене болить горло і є температура.**)
* How do you ask for headache pills at the pharmacy? (**Дайте, будь ласка, таблетки від головного болю.**)
* How do you say "I feel bad"? (**Мені погано.**)

<!-- INJECT_ACTIVITY: quiz-logical-response -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: health
level: a1

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (10 total / 4–6 inline / 6–9 workbook,
# 6+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 6 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 6 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 6 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 6 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 6 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 6 pairs total

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
    items:                     # ← real output: ≥ 6 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 6 items total

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

**Level: A1.4+ (Module 53/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 10 activities.** Inline: 4–6. Workbook: 6–9. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 6 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 6.
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
2. Run `query_cefr_level` on any word you're unsure about — it must be a1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **at least 4** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 6** workbook activities.
- [ ] **Total ≥ 10.**
- [ ] **Every** activity has **at least 6** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 4 and 6. I did NOT create more injection markers than 6.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
