<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/health.yaml` file for module **53: Health** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-medical-responses -->`
- `<!-- INJECT_ACTIVITY: match-body-vocabulary -->`
- `<!-- INJECT_ACTIVITY: fill-in-symptoms-logic -->`
- `<!-- INJECT_ACTIVITY: fill-in-medical-chunks -->`

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
When you visit a medical professional in Ukraine, the interaction is usually direct and focused on the symptoms. A general practitioner, known as a **терапевт** (general practitioner), will often begin the consultation with a very standard, practical opening phrase: **Що у вас болить?** (What hurts you?). The cultural expectation is that you will answer this question directly by listing your physical symptoms or describing how you feel, rather than making small talk. There is no need to translate English phrases like "I am not feeling well today" before getting to the point. You simply state the problem. After receiving a diagnosis from the doctor, you will likely need to visit a pharmacy, called an **аптека** (pharmacy). There, you will speak with an **аптекар** (pharmacist) to purchase the necessary treatments, using polite requests to get exactly what you need.

> **Лікар:** Добрий день! Що у вас болить? *(Good day! What hurts?)*
> **Пацієнт:** У мене болить голова і горло. *(My head and throat hurt.)*
> **Лікар:** Давно? *(For a long time?)*
> **Пацієнт:** З учора. І в мене температура. *(Since yesterday. And I have a fever.)*
> **Лікар:** Ви кашляєте? *(Are you coughing?)*
> **Пацієнт:** Так, трохи. І в мене нежить. *(Yes, a little. And I have a runny nose.)*
> **Лікар:** Зрозуміло. Це застуда. Я випишу ліки. Відпочивайте! *(I understand. It is a cold. I will prescribe medicine. Rest!)*
> **Пацієнт:** Дякую, лікарю! *(Thank you, doctor!)*

In this dialogue, the patient clearly lists the problems: **болить голова і горло** (head and throat hurt), **температура** (fever), and **нежить** (runny nose). The doctor provides a clear diagnosis of **застуда** (a cold) and promises to help: **я випишу ліки** (I will prescribe medicine).

> **Пацієнт:** Добрий день! У мене болить голова. Дайте, будь ласка, таблетки. *(Good day! My head hurts. Give me pills, please.)*
> **Аптекар:** Від головного болю? *(For a headache?)*
> **Пацієнт:** Так. І від кашлю, будь ласка. *(Yes. And for a cough, please.)*
> **Аптекар:** Ось, будь ласка. Ще щось? *(Here you go. Anything else?)*
> **Пацієнт:** А є щось від нежитю? *(And is there anything for a runny nose?)*
> **Аптекар:** Так, ось краплі. *(Yes, here are drops.)*
> **Пацієнт:** Дякую! Скільки це коштує? *(Thank you! How much does it cost?)*

At the pharmacy, the patient uses the polite command **Дайте, будь ласка** (Give me, please) to request specific items. They ask for **таблетки від головного болю** (pills for a headache) and **краплі від нежитю** (drops for a runny nose). The interaction concludes with the essential practical question for any transaction: **Скільки це коштує?** (How much does it cost?).

<!-- INJECT_ACTIVITY: quiz-medical-responses -->

## Тіло (The Body)
To describe what hurts, you must first know the names of the fundamental parts of the body. In Ukrainian textbooks for early grades, these are taught simply as **частини тіла** (body parts). For common medical complaints, you need to recognize the most essential ones. The word for head is **голова** (head), which is a feminine noun. The throat is **горло** (throat), a neuter noun. The back is **спина** (back), another feminine noun. The stomach or abdomen is **живіт** (stomach), which is a masculine noun. Knowing the grammatical gender of each word is important because it dictates how adjectives will agree with them. For example, if you want to describe a sore back, the adjective must match the feminine gender of the noun, creating a phrase like **хвора спина** (sore back).

*   **голова** (head, f)
*   **горло** (throat, n)
*   **спина** (back, f)
*   **живіт** (stomach, m)

Beyond the torso and head, you must be able to name your limbs and sensory organs. The word for an arm or a hand is **рука** (hand/arm), a feminine noun. The word for a leg or a foot is **нога** (leg/foot), also feminine. For the face and head, an eye is **око** (eye, n), an ear is **вухо** (ear, n), a tooth is **зуб** (tooth, m), and a nose is **ніс** (nose, m). These vocabulary words will cover the vast majority of basic health issues you might experience.

:::note
In Ukrainian, **рука** refers to the entire limb from the shoulder all the way down to the fingertips, and **нога** refers to the entire limb from the hip down to the toes. Ukrainian does not strictly separate the hand from the arm or the foot from the leg in everyday speech as English does.
:::

*   **рука** (hand/arm, f)
*   **нога** (leg/foot, f)
*   **око** (eye, n)
*   **вухо** (ear, n)
*   **зуб** (tooth, m)
*   **ніс** (nose, m)

At the A1 level, your primary goal is to recognize these nouns so you can point to what hurts. However, you should also begin to notice how adjectives change their endings to match the gender of these body parts. You learned about adjective agreement in earlier modules, and it applies here perfectly. A masculine noun takes a masculine adjective, a feminine noun takes a feminine adjective, and a neuter noun takes a neuter adjective. For instance, you will see **великий ніс** (big nose — masculine), **велика рука** (big hand — feminine), and **велике око** (big eye — neuter). While you will mostly use these nouns with the verb for "hurts," recognizing these endings helps build your grammatical reflex.

*   **великий ніс** (big nose)
*   **велика рука** (big hand)
*   **велике око** (big eye)

<!-- INJECT_ACTIVITY: match-body-vocabulary -->

## У мене болить... (It Hurts...)
The most important structure for discussing health in Ukrainian is the magic phrase for expressing pain. You do not say "my head hurts" using a possessive pronoun. Instead, you use the fixed chunk **У мене болить** followed by the body part in the nominative case. Literally, this translates to "at me hurts," but it simply means "my [body part] hurts." You must memorize this as a complete pattern rather than analyzing the grammar behind it.

*   **У мене болить голова.** (I have a headache. / My head hurts.)
*   **У мене болить живіт.** (My stomach hurts.)
*   **У мене болить горло.** (My throat hurts.)
*   **У мене болить спина.** (My back hurts.)
*   **У мене болить зуб.** (I have a toothache. / My tooth hurts.)

:::caution
Never translate the English phrase "my head hurts" directly word-for-word into Ukrainian. A phrase like «Моя голова болить» sounds unnatural to a native speaker. Always use the impersonal construction **У мене болить голова**.
:::

If the pain is in a body part that comes in pairs or groups, the verb must change to match the plural subject. The singular verb **болить** (hurts) changes to the plural verb **болять** (hurt). This is a simple switch from an **-ить** ending to an **-ять** ending.

*   **У мене болять очі.** (My eyes hurt.)
*   **У мене болять вуха.** (My ears hurt.)
*   **У мене болять зуби.** (My teeth hurt.)
*   **У мене болять ноги.** (My legs hurt.)

Not all illnesses involve a specific localized pain. For general symptoms and respiratory issues, you use different phrases. If your body temperature is high, you use the noun **температура** (fever/temperature). For a cough, you use the masculine noun **кашель** (cough). For a runny nose, you use the masculine noun **нежить** (runny nose). To describe these states, you often use the same "I have" construction:

*   **У мене температура.** (I have a fever.)
*   **У мене кашель.** (I have a cough.)
*   **У мене нежить.** (I have a runny nose.)

:::tip
Remember that **нежить** (runny nose) is a masculine noun. This means its ending changes differently than feminine nouns, which is why you ask for drops **від нежитю**, not від нежиті.
:::

When you want to describe your overall physical state, you can use the adjective for sick, which must agree with your gender. A man says **Я хворий** (I am sick), and a woman says **Я хвора** (I am sick). Alternatively, you can use the impersonal phrase **Мені погано** (I feel bad) or **Мені холодно** (I am cold) to express general discomfort. These are excellent chunks to memorize for times when you cannot point to a specific pain but know you need help.

*   **Я хворий.** (I am sick. — masculine)
*   **Я хвора.** (I am sick. — feminine)
*   **Мені погано.** (I feel bad.)
*   **Мені холодно.** (I am cold.)

<!-- INJECT_ACTIVITY: fill-in-symptoms-logic -->
<!-- INJECT_ACTIVITY: fill-in-medical-chunks -->

## Summary
You can identify the ten core body parts: **голова** (head), **горло** (throat), **живіт** (stomach), **спина** (back), **рука** (arm/hand), **нога** (leg/foot), **око** (eye), **вухо** (ear), **зуб** (tooth), and **ніс** (nose). You also know the primary symptoms associated with common illnesses, such as **температура** (fever), **кашель** (cough), and **нежить** (runny nose). These words allow you to point to a problem and give it a name.

You have also learned the functional structures required to express pain and discomfort. The most critical magic phrase is **У мене болить** for singular body parts and **У мене болять** for plural ones. When you feel generally unwell, you can describe your state using the phrases **Мені погано** (I feel bad), **Мені холодно** (I am cold), or **Я хворий / Я хвора** (I am sick). Finally, when you visit the pharmacy, you know how to make a polite request using the phrase **Дайте таблетки від...** (Give me pills for...). You can ask for items **від головного болю** (for a headache), **від кашлю** (for a cough), or **від нежитю** (for a runny nose).

Here is a quick self-check to review what you have learned. Read the English prompt and try to form the Ukrainian response before looking at the model answer.

How do you tell a doctor that your throat hurts?
> [!model-answer]
> **У мене болить горло.**

How do you ask a pharmacist for headache pills?
> [!model-answer]
> **Дайте, будь ласка, таблетки від головного болю.**

How do you say "My eyes hurt and I have a fever"?
> [!model-answer]
> **У мене болять очі і є температура.**

How do you say "I am sick" if you are a woman?
> [!model-answer]
> **Я хвора.**

How do you tell someone that you feel bad?
> [!model-answer]
> **Мені погано.**

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: health
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
