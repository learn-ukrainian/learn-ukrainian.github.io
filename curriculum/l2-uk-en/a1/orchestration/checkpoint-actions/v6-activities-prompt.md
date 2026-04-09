<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-actions.yaml` file for module **21: Checkpoint: Actions** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-describe-day -->`
- `<!-- INJECT_ACTIVITY: group-sort-verbs -->`
- `<!-- INJECT_ACTIVITY: quiz-mixed-conjugation -->`
- `<!-- INJECT_ACTIVITY: fill-in-dialogue-completion -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Mixed conjugation: choose correct form for Group I and II verbs'
  items: 10
  type: quiz
- focus: Complete the dialogue with modals, questions, and verb forms
  items: 8
  type: fill-in
- focus: 'Describe your day: morning routine → work → evening'
  items: 6
  type: fill-in
- focus: 'Sort verbs by group: Group I vs Group II vs Reflexive'
  items: 12
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended: []
required: []


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Що ми знаємо? (What Do We Know?)

Learning a new language is a step-by-step process of building communication skills. In our very first modules, we laid the foundation by learning how to name objects around us, identify people, and use basic adjectives. In the A1.3 phase, we started bringing those objects and people to life by adding actions. We moved from simply stating what we like in Module 15 to describing our entire morning routines in Module 20. 

This checkpoint is a moment to pause, reflect, and consolidate everything we have built so far. Before we move forward to learning about time and nature in the next phase, we need to make sure these action blocks are solid. Can you comfortably describe what you do, what you want, and what you must do? 

Take a moment to read through this structured self-check list. Do not just read the English translation; look closely at the Ukrainian examples and see if you understand exactly how the words are formed.
*   Can you say what you like? For example, **мені подобається кава** (I like coffee) or **я люблю читати** (I love to read).
*   Can you conjugate a Group I verb for all persons? Think about the verb **читати** (to read): **я читаю** (I read), **ти читаєш** (you read), **вони читають** (they read).
*   Can you conjugate a Group II verb? Take the verb **говорити** (to speak): **я говорю** (I speak), **ти говориш** (you speak), **вони говорять** (they speak).
*   Can you express a need, ability, or desire using modal verbs? For example, **я мушу йти** (I must go), **я хочу спати** (I want to sleep), or **я можу допомогти** (I can help).
*   Can you ask basic questions using the seven core question words? For example, **де офіс?** (where is the office?) or **коли ти працюєш?** (when do you work?).
*   Can you describe your morning using reflexive verbs? For example, **я прокидаюся** (I wake up) and **я вмиваюся** (I wash my face).

If these patterns feel familiar, you are ready to review them in context.

## Читання (Reading Practice)

Reading connected text is the best way to see how grammar works in the real world. Meet Pavlo. He is a designer from Kyiv. In the short text below, Pavlo describes his typical day. This narrative combines every verb group, modal verb, and sequence word you have studied so far into a single, cohesive story. As you read, pay attention to the endings of the verbs and how Pavlo connects his actions from morning until night. Read the text aloud to practice your pronunciation and rhythm.

**Мій звичайний день** (My Typical Day)
*   **Я прокидаюся о сьомій.** (I wake up at seven.)
*   **Спочатку я вмиваюся, а потім снідаю.** (First I wash my face, and then I eat breakfast.)
*   **Я дуже люблю каву.** (I really love coffee.)
*   **О дев'ятій я вже працюю.** (At nine I am already working.)
*   **Я дизайнер. Я багато думаю і малюю.** (I am a designer. I think and draw a lot.)
*   **Удень я можу гуляти в парку.** (In the afternoon I can walk in the park.)
*   **Увечері я мушу вчити англійську, але я хочу дивитися фільм.** (In the evening I must study English, but I want to watch a movie.)
*   **Одинадцята вечора — я вже сплю.** (Eleven in the evening — I am already sleeping.)

We can analyze the lexical choices in Pavlo's story. Notice how he uses sequence markers to organize his timeline. The word **спочатку** (first/at first) sets the starting point of a sequence, while **потім** (then/after that) introduces the next action. You can also use **тоді** (then) in similar contexts. These small words anchor the verbs and turn a list of separate sentences into a flowing story. 

Also, look at how Pavlo expresses his preferences. He says **я дуже люблю каву** (I really love coffee) to state a general fact about his tastes. However, when talking about his immediate desire in the evening, he uses the modal verb **хотіти** (to want): **я хочу дивитися фільм** (I want to watch a movie). Understanding the difference between a general preference (**любити**) and a specific desire (**хотіти**) gives your Ukrainian much more precision.

<!-- INJECT_ACTIVITY: fill-in-describe-day -->

## Граматика (Grammar Summary)

The core grammar patterns make these actions possible. Ukrainian verbs fall into two main conjugation groups, which we identify by their endings in the present tense. All verbs start with the infinitive ending **-ти** (for example: **читати**, **говорити**, **хотіти**).

Group I verbs typically have an infinitive ending in **-ати** or **-яти**. Their present tense endings follow this pattern: **-ю**, **-єш**, **-є**, **-ємо**, **-єте**, **-ють**. In the third-person plural ("they" form), they always end in **-уть** or **-ють**.
*   **знати** (to know) → **вони знають** (they know)
*   **працювати** (to work) → **вони працюють** (they work)
*   **думати** (to think) → **вони думають** (they think)

Group II verbs usually have an infinitive ending in **-ити** or **-іти**. Their present tense endings follow this pattern: **-ю** (or **-у**), **-иш**, **-ить**, **-имо**, **-ите**, **-ять** (or **-ать**). In the third-person plural, they end in **-ать** or **-ять**.
*   **говорити** (to speak) → **вони говорять** (they speak)
*   **робити** (to do/make) → **вони роблять** (they do/make)
*   **бачити** (to see) → **вони бачать** (they see)

Notice the stem change in the first person singular for some Group II verbs, like **бачити**: we say **я бачу** (I see), not "бачю".

Next, we have the modal verbs, which act as helpers to express ability, obligation, or desire. The big three are **хотіти** (to want), **могти** (to be able to/can), and **мусити** (must/to have to). The usage pattern is simple and strict: you conjugate the modal verb to match the subject, and the action verb that follows remains in the infinitive (unchanged).
*   **Я хочу говорити.** (I want to speak.)
*   **Він може працювати.** (He can work.)
*   **Ми мусимо йти.** (We must go.)

To have a real conversation, you need to know how to ask questions and negate statements. We learned the seven core question words: **Хто** (Who), **Що** (What), **Де** (Where), **Куди** (Where to), **Коли** (When), **Чому** (Why), and **Як** (How). When you want to ask a question, remember an important naturalness rule: in Ukrainian, we say **ставити питання** (to ask a question), never the direct translation "задавати".

For negation, simply place the particle **не** (not) directly before the verb: **я не знаю** (I do not know). Ukrainian also uses double negation, which is perfectly grammatical and required when using negative pronouns. If you use a word like **ніхто** (nobody) or **нічого** (nothing), you must still use **не** before the verb: **я нічого не знаю** (I know nothing).

Finally, we covered reflexive verbs, which describe actions you perform on yourself. These verbs add the suffix **-ся** to the end of the conjugated form.
*   **прокидатися** (to wake up)
*   **вмиватися** (to wash oneself)
*   **одягатися** (to get dressed)

Pay attention to a crucial phonetic rule regarding this suffix. The suffix **-ся** can reduce to **-сь** when the verb ending finishes with a vowel (**голосний**). Compare the full form **я вмиваюся** (I wash myself) with the shortened, but very common, form **я вмиваюсь**. However, after a consonant (**приголосний**), you must always use the full **-ся**, as in **ти вмиваєшся** (you wash yourself).

<!-- INJECT_ACTIVITY: group-sort-verbs -->
<!-- INJECT_ACTIVITY: quiz-mixed-conjugation -->

## Діалог (Connected Dialogue)

These pieces work together in a natural setting. The context is a meeting between two friends, Olena and Viktor. Olena is busy with her tasks, but Viktor wants to hang out. This scenario forces the speakers to use questions to gather information, modal verbs to express their desires and limitations, and negation to turn down proposals. This is a classic example of the **розмовний** (conversational) register, exactly how people speak in real life.

> **Віктор:** Привіт! Що ти робиш? *(Hi! What are you doing?)*
> **Олена:** Я зараз працюю, але дуже хочу каву. *(I am working right now, but I really want coffee.)*
> **Віктор:** Ти можеш гуляти зараз? *(Can you walk right now?)*
> **Олена:** Не можу, мушу працювати. Коли ти вільний? *(I cannot, I must work. When are you free?)*
> **Віктор:** Я вільний о шостій. Де ми зустрічаємося? *(I am free at six. Where are we meeting?)*
> **Олена:** У центрі. До зустрічі! *(In the center. See you!)*

Several pedagogical mechanics are at play in this conversation. 

First, notice the difference between location and direction. Viktor asks **де ми зустрічаємося?** (where are we meeting?). The word **де** (where) asks about a static location. If he were asking about a destination they were walking towards, he would use **куди** (where to).

Second, look at Olena's refusal. When Viktor asks if she can walk, she doesn't just say **ні** (no). She says **не можу** (I cannot). In Ukrainian, repeating the negated verb is much more natural and polite than a blunt negative word. It shows that you are engaged in the conversation and providing a specific reason for your answer.

Third, notice how Viktor states the time: **о шостій** (at six). When talking about hours on the clock, Ukrainian uses the preposition **о** (or **об** before a vowel) followed by the ordinal number. 

:::tip
If you ever need to interrupt or clarify something in a dialogue like this, remember to use the polite phrase **у мене є питання** (I have a question). This is the natural Ukrainian way to ask for clarification, rather than translating "I have a question" word-for-word from English.
:::

<!-- INJECT_ACTIVITY: fill-in-dialogue-completion -->

## Підсумок — Summary

You have officially reached the end of the A1.3 phase. Take a deep breath and look at the achievement checklist. You have completed A1.3 [Actions]! 

You are no longer limited to just naming objects or saying what you like. You can now conjugate the most common verbs in both Group I and Group II, allowing you to speak about yourself, the person you are talking to, and other people in your life. You can express your desires using **хотіти**, your abilities using **могти**, and your obligations using **мусити**. You can ask about anything using the seven core question words, and you can negate statements confidently. Most importantly, you can describe your daily life from morning to night using reflexive verbs and sequence words.

This is a massive step forward in your ability to communicate. You have mastered the "What" — the actions that make up daily life. Now, we need to add precision to those actions. 

In the next phase, A1.4 [Time and Nature], we will focus on the "When" and the "Where" in much greater detail. You will learn how to read the clock and talk about specific times using **години** (hours). You will learn the **дні тижня** (days of the week) to schedule meetings and make plans with friends. We will also learn how to describe the world around us by talking about the **погода** (weather). You have the actions; now we will build the stage where those actions take place. Keep practicing your verbs, and get ready for the next level!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-actions
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

**Level: A1.2-A1.3 (Module 21/55) — EARLY BEGINNER**

The learner knows the alphabet and ~200 words. They:
- Can read Ukrainian slowly
- Know basic nouns, adjectives, simple verb forms
- Cannot handle complex sentences or grammar terminology in Ukrainian

**Instructions in simple English with Ukrainian key terms in bold.**
Example: 'Choose the correct form of **мій/моя/моє**'

**Good activity types:** quiz, fill-in (simple sentences), match-up, group-sort, true-false, observe, anagram, translate (English→Ukrainian), error-correction (simple), divide-words, count-syllables, odd-one-out, order.


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
