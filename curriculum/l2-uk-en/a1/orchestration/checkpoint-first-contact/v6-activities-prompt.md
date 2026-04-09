<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-first-contact.yaml` file for module **7: Checkpoint: First Contact** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-comprehensive-review -->`
- `<!-- INJECT_ACTIVITY: match-up-q-and-a -->`
- `<!-- INJECT_ACTIVITY: fill-in-self-intro -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Comprehensive review: sounds, letters, greetings, family'
  items: 12
  type: quiz
- focus: Complete the full self-introduction monologue
  items: 8
  type: fill-in
- focus: Match questions with answers (Як звати? → Мене звати...)
  items: 8
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- ім'я (first name)
- прізвище (surname)
required:
- All vocabulary from M01-M06 is recycled — no new required words


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Що ми знаємо? (What Do We Know?)

Welcome to the first major checkpoint on your Ukrainian language journey. You have made the critical transition from learning individual phonetic elements to participating in a full, meaningful conversation. We began by deciphering an entirely new alphabet, and now you have established a solid Ukrainian linguistic foundation. This module represents a milestone where you consolidate those foundational skills before moving forward.

Consider the comprehensive checklist of what you have acquired so far. You have achieved phonetic mastery of the Cyrillic alphabet. You understand the fundamental rule of Ukrainian phonetics: distinguishing between a **звук** (sound) that you hear and a **літера** (letter) that you write. You understand how the **апостроф** (apostrophe) acts as a hard boundary separating sounds, and how the **м'який знак** (soft sign), while having no sound of its own, softens the preceding consonant. You grasp the vital concept of word **наголос** (stress) and how it shapes the entire rhythm of a spoken word. You confidently use basic greetings like **Привіт** (Hi) and **Добрий день** (Good afternoon), and you recognize the essential vocabulary for family members such as **мама** (mother), **тато** (father), **брат** (brother), and **сестра** (sister).

This module serves as a dedicated self-assessment phase. You will prove that you can read fluently and hold a basic introduction in a realistic context. We introduce no new vocabulary or new grammar rules here. Instead, the entire focus remains on consolidation, ensuring that the structures you have already learned become automatic and natural. The goal is moving from translation to direct comprehension.

<!-- INJECT_ACTIVITY: quiz-comprehensive-review -->

## Читання (Reading Practice)

Reading aloud is the essential bridge between recognizing individual letters on a page and producing natural speech. For this exercise, focus on your reading flow and carefully observe the stress marks provided in the text. When you read a Ukrainian sentence, read it as a single continuous thought rather than a robotic list of isolated words. Speak clearly and confidently, allowing the syllables to connect smoothly. Reading aloud engages your muscle memory. It trains your tongue and lips to produce new phonetic combinations, making it easier to speak spontaneously in real-world situations. Do not rush through the text. Pace yourself and focus on pronunciation.

Read the following passage about a woman named **Оксана Ковальчук** (Oksana Kovalchuk). Focus on understanding the meaning without translating it into English in your head.

> **Мене звати Оксана Ковальчук.** *(My name is Oksana Kovalchuk.)*
> **Я з Києва.** *(I am from Kyiv.)*
> **Я — вчителька.** *(I am a teacher.)*
> **Це — моя сім'я.** *(This is my family.)*
> **Мій чоловік — інженер.** *(My husband is an engineer.)*
> **Його звати Микола.** *(His name is Mykola.)*
> **У мене є син.** *(I have a son.)*
> **Мій син — студент.** *(My son is a student.)*
> **Ми живемо тут.** *(We live here.)*
> **Дуже приємно.** *(Very nice to meet you.)*

Analyzing the name components within this text reveals important cultural patterns. The woman's personal name is **Оксана** (first name). Her family name is **Ковальчук** (surname). In formal Ukrainian culture, people also use a patronymic based on their father's name. If her father was named Mykola, her patronymic would be **Миколаївна** (Mykolaivna). Remember the strict capitalization rule: every proper noun, including a person's **ім'я** (first name) and **прізвище** (surname), must always start with a capital letter. Proper names are central to Ukrainian identity, and writing them correctly is a sign of respect.

:::tip
When reading Ukrainian texts, remember that the spelling is highly phonetic. What you see is exactly what you hear. Trust the letters, and do not try to apply English pronunciation rules to Ukrainian words.
:::

<!-- INJECT_ACTIVITY: match-up-q-and-a -->

## Граматика (Grammar Summary)

Expressing identity and identification in Ukrainian relies on specific structural patterns. We use the **Це** (This is) + noun structure to introduce people or objects. When stating who someone is, Ukrainian employs a zero-copula rule, meaning the verb "to be" is completely omitted in the present tense. Compare the English sentence "I am a student" with the Ukrainian equivalent **Я — студент** (I am a student). The dash explicitly replaces the missing verb, indicating a direct relationship between the subject and the noun.

*   **Це — мій друг.** *(This is my friend.)*
*   **Вона — лікарка.** *(She is a doctor.)*
*   **Він — архітектор.** *(He is an architect.)*

:::caution
A common L2 error is using the verb "to be" when stating identity. English speakers often say **Я є студент** or **Моє ім'я є Анна**, which is a direct translation error. The correct forms are **Я — студент** and **Мене звати Анна**.
:::

A clear structural difference exists between stating possession and naming someone. We use the construction **У мене є** (I have) to express possession of objects or family relationships. To state what someone is called, we use the fixed phrase **Мене звати** (My name is, literally: they call me). Notice that these fixed chunks require the accusative pronouns **мене** (me), **тебе** (you, informal), and **вас** (you, formal). Treat these phrases as solid vocabulary blocks. 

*   **У мене є брат.** *(I have a brother.)*
*   **У мене є сестра.** *(I have a sister.)*
*   **Як тебе звати?** *(What is your name?)*
*   **Його звати Тарас.** *(His name is Taras.)*

When expressing origin, we use the specific preposition and case ending combination. The question **Звідки ти?** (Where are you from?) is answered with **Я з...** (I am from...) followed by the city or country name with its appropriate ending, such as **Києва** (Kyiv) or **Дніпра** (Dnipro). Memorize these origin phrases as complete units.

Possessive pronouns must always agree with the grammatical gender of the noun they modify. You say **мій тато** (my dad) because the word is masculine, **моя мама** (my mom) because it is feminine, and **моє ім'я** (my name) because it is neuter. Also, recall the Vocative case endings for direct address. When calling someone, the ending changes: **Анна** becomes **Анно!**, **Оксана** becomes **Оксано!**, and **Тарас** becomes **Тарасе!**.

:::note
English does not have a vocative case, but in Ukrainian, it is mandatory when addressing someone directly. Forgetting to change the name ending can sound unnatural or blunt to a native speaker.
:::

## Діалог (Capstone Dialogue)

Imagine the following scene at a professional conference coffee break. Two professionals, **Богдан** (Bohdan), an engineer from the city of Dnipro, and **Соломія** (Solomiia), a teacher from the city of Ternopil, meet between sessions. This realistic setting justifies a full exchange of personal information with a new acquaintance. Pay attention to how they ask questions and respond politely.

> **Богдан:** Добрий день! *(Good afternoon!)*
> **Соломія:** Добрий день! *(Good afternoon!)*
> **Богдан:** Мене звати Богдан. А як Вас звати? *(My name is Bohdan. And what is your name?)*
> **Соломія:** Мене звати Соломія. Моє прізвище — Коваль. *(My name is Solomiia. My surname is Koval.)*
> **Богдан:** Дуже приємно, пані Соломіє! Я з Дніпра. А Ви звідки? *(Very nice to meet you, Ms. Solomiia! I am from Dnipro. And where are you from?)*
> **Соломія:** Я з Тернополя. Я — вчителька. А Ви? *(I am from Ternopil. I am a teacher. And you?)*
> **Богдан:** Я — інженер. Дивіться, це моя сім'я на фото. *(I am an engineer. Look, this is my family in the photo.)*
> **Соломія:** Це Ваша дружина? *(Is this your wife?)*
> **Богдан:** Так, це моя дружина. У мене є син. *(Yes, this is my wife. I have a son.)*
> **Соломія:** Рада знайомству, пане Богдане! *(Glad to meet you, Mr. Bohdan!)*
> **Богдан:** Навзаєм! *(Mutually!)*

Notice the register used in this exchange. Because this is a professional context, they use the formal pronoun **Ви** (you, formal). They also use the respectful titles **Пане** (Mr.) and **Пані** (Ms.). Соломія addresses him directly in the Vocative case as **Пане Богдане**, rather than just stating his basic name. This shows politeness and respect in a formal setting. The dialogue moves naturally from initial contact to sharing origins, professions, and personal details. 

When Богдан shows his photo, he uses the visual aid to transition the conversation from work to personal life. Using photos on your phone is an excellent, natural way to practice vocabulary with native speakers. The full introduction cycle is a predictable social script. Mastering this script allows you to navigate first encounters smoothly and build connections.

Creating your own graduation monologue is the final step. In Ukrainian primary schools, a simple text follows a strict three-part structure. First is the **Зачин** (Introduction), where you establish contact and state the topic. Second is the **Основна частина** (Main Part), where you provide the core details about your origin and profession. Third is the **Кінцівка** (Conclusion), where you offer a simple, polite closing sentence. This structure helps organize your thoughts logically.

Use this template to practice introducing yourself out loud:

**Привіт!** *(Hi!)*
**Мене звати...** *(My name is...)*
**Моє прізвище...** *(My surname is...)*
**Я з...** *(I am from...)*
**Я — ...** *(I am a...)*
**Це моя сім'я.** *(This is my family.)*
**У мене є...** *(I have a...)*
**Дуже приємно.** *(Very nice to meet you.)*

<!-- INJECT_ACTIVITY: fill-in-self-intro -->

## Підсумок — Summary

You have reached the end of the first major phase of your language journey. Before you proceed to the next set of modules, take a moment for a final, comprehensive self-check. Can you name all 33 letters of the Ukrainian alphabet and confidently produce their corresponding sounds? Can you comfortably say hello using both formal and informal greetings depending on the specific social context? Do you clearly understand the cultural and linguistic difference between a person's **ім'я** (first name) and their **прізвище** (surname)?

Make sure you know how to use the possessive pronouns **мій** (my, masc.) and **моя** (my, fem.) correctly when talking about your family members. Check if you can use the Vocative case to call a friend directly, changing the ending of their name appropriately so that it sounds natural to a native speaker. Can you confidently introduce yourself in five connected sentences using the specific patterns from this module? If you can answer yes to all these questions, you are fully prepared. Take pride in establishing a solid foundation. You are now ready to transition to the next phase of your studies, where you will discover that all objects in the Ukrainian language have grammatical gender.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-first-contact
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

**Level: A1.1 (Module 7/55) — COMPLETE BEGINNER**

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

### Pattern: phonetics-sounds-letters [§4.1.1, §4.1.4]
**Звуки і літери** (Sounds and letters)
- **quiz** — Звук чи літера?: Розрізнити звук і літеру — основа української фонетики / Distinguish звук from літера — fundamental Ukrainian phonetics distinction
  - Instruction: *Оберіть правильну відповідь*
- **match-up** — Літера → Звук: Зіставити літери зі звуковими значеннями, особливо багатозвучні (я, ю, є, ї) / Match letters to their sound values, especially multi-sound letters (я, ю, є, ї)
  - Instruction: *З'єднайте літеру зі звуком*
- **group-sort** — Голосні й приголосні: Розподілити звуки на голосні та приголосні / Sort letters/sounds into голосні (vowel) vs приголосні (consonant)
  - Instruction: *Розподіліть звуки*
- **image-to-letter** — Знайди літеру: Побачити зображення, визначити українську літеру / See image, identify the Ukrainian letter it starts with
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує фонетичні знання
- ❌ fill-in-no-options: Занадто складно для A1 — початківці потребують варіантів відповідей

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
