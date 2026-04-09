<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/emergencies.yaml` file for module **54: Emergencies** (a1).

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

- `<!-- INJECT_ACTIVITY: dialogue-order -->`
- `<!-- INJECT_ACTIVITY: phrase-choice-quiz -->`
- `<!-- INJECT_ACTIVITY: fill-in-emergency-call -->`
- `<!-- INJECT_ACTIVITY: report-issue-fill-in -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose the correct emergency phrase for the situation.
  items:
  - options:
    - Тут аварія! Викличте швидку!
    - Тут пожежа! Допоможіть!
    - Я загубив паспорт.
    question: You see a car crash.
  - options:
    - Тут пожежа! Допоможіть!
    - Тут аварія!
    - Мені потрібен лікар.
    question: You see a building on fire.
  - options:
    - Людині погано! Викличте швидку!
    - Викличте поліцію!
    - Я загубив паспорт.
    question: Someone is feeling very ill on the street.
  - options:
    - Я загубив паспорт.
    - Тут аварія!
    - Мені потрібна швидка.
    question: You cannot find your passport at the airport.
  - options:
    - Викличте поліцію! Допоможіть!
    - Тут пожежа!
    - Мені потрібен лікар.
    question: Someone stole your wallet.
  type: quiz
- focus: Complete the emergency phone call.
  items:
  - Алло! {Допоможіть|Дякую|Вибачте}! Тут аварія!
  - '{Викличте|Загубив|Потрібен} швидку допомогу!'
  - Я на {вулиці|лікарні|поліції} Хрещатик, біля метро.
  - Мене {звати|прізвище|адреса} Адам.
  - Мій номер {телефону|паспорта|будинку} — нуль дев'яносто три...
  - Мені потрібна {допомога|пожежа|аварія}!
  type: fill-in
- focus: Put the dialogue with the 112 operator in the correct order.
  items:
  - — Служба порятунку, слухаю вас.
  - — Допоможіть! Тут пожежа!
  - — Де ви?
  - — На вулиці Шевченка, будинок п'ять.
  - — Зрозуміло. Швидка і пожежники вже їдуть. Як вас звати?
  - — Мене звати Анна. Дякую!
  type: order
- focus: Reporting an issue at the police station or hospital.
  items:
  - Добрий день. Я {загубив|викличте|допоможіть} паспорт.
  - Моє {прізвище|ім'я|номер} — Сміт.
  - Мені {потрібен|погана|хворий} лікар.
  - У мене {алергія|пожежа|аварія} на ці таблетки.
  - Я не розумію. {Повторіть|Допоможіть|Викличте}, будь ласка.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- пожежа (fire, f)
- порятунок (rescue, m)
- паспорт (passport, m)
- адреса (address, f)
- номер (number, m)
- алергія (allergy, f)
- форма (form/document, f)
- будинок (building, m)
required:
- допомога (help, f)
- допоможіть (help! — imperative)
- швидка (ambulance, f — short for швидка допомога)
- поліція (police, f)
- лікарня (hospital, f)
- аварія (accident, f)
- загубити (to lose)
- викликати (to call/summon)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Dialogues

When you face a high-stress situation in a foreign country, communication needs to be extremely fast and direct. In emergencies, Ukrainian shifts to short, functional chunks of information. Clarity is significantly more important than perfect grammar or vocabulary. You simply need to convey exactly what happened and precisely where you are. Memorizing these simple, direct phrases allows you to deploy them automatically without overthinking the grammatical rules.

Consider a critical situation where timing is everything. Adam witnesses a minor car crash on **вулиця Хрещатик** (Khreshchatyk street) and immediately calls the emergency number. He needs to report the **аварія** (accident) and forcefully request a **швидка** (ambulance). The emergency operator asks for the incident details and his exact location to dispatch help. Adam provides his precise location near the metro station and clearly states his personal information to the operator.

> **Оператор 103:** Служба порятунку, слухаю вас. *(Rescue service, I am listening to you.)*
> **Адам:** Допоможіть! Тут аварія! *(Help! There is an accident here!)*
> **Адам:** Людина не рухається! *(A person is not moving!)*
> **Оператор 103:** Де ви? *(Where are you?)*
> **Адам:** На вулиці Хрещатик, біля метро Майдан Незалежності. *(On Khreshchatyk street, near the Independence Square metro.)*
> **Оператор 103:** Зрозуміло. Швидка вже їде. *(Understood. An ambulance is already coming.)*
> **Оператор 103:** Як вас звати? *(What is your name?)*
> **Адам:** Мене звати Адам. Мій номер — нуль дев'яносто три... *(My name is Adam. My number is zero ninety-three...)*
> **Оператор 103:** Дякую. Залишайтеся на місці. *(Thank you. Stay in place.)*

Not every emergency involves a life-threatening medical issue. Sometimes you face an incredibly frustrating administrative crisis, like losing your travel documents in a busy city. In this dialogue, Adam visits the **поліція** (police) for help. First, he asks a helpful passerby for directions to the nearest station. Once inside the station, he clearly reports his loss to the duty officer. The police officer asks for his **прізвище** (surname) and his mobile phone number. Finally, the officer gives him a **форма** (form) to complete for the official record.

> **Адам:** Вибачте, де тут поліція? *(Excuse me, where is the police here?)*
> **Перехожий:** Поліція? Прямо і наліво. *(Police? Straight and to the left.)*
> **Адам:** Дякую! *(Thank you!)*
> *(У відділку поліції / At the police station)*
> **Адам:** Добрий день. Я загубив паспорт. *(Good day. I lost my passport.)*
> **Офіцер:** Де ви його загубили? *(Where did you lose it?)*
> **Адам:** Я не знаю. Може, в метро. *(I do not know. Maybe in the metro.)*
> **Офіцер:** Як ваше прізвище? *(What is your surname?)*
> **Адам:** Сміт. Адам Сміт. *(Smith. Adam Smith.)*
> **Офіцер:** Ваш номер телефону? *(Your phone number?)*
> **Адам:** Нуль дев'яносто три, п'ятсот двадцять один... *(Zero ninety-three, five hundred twenty-one...)*
> **Офіцер:** Добре. Заповніть цю форму, будь ласка. *(Good. Fill out this form, please.)*

Both of these dialogues share a highly effective communicative strategy. Notice the reliable, repeatable pattern: first, give the urgent alert for help to get immediate attention. Second, state the core problem clearly and concisely. Third, provide your exact location using simple prepositions of place. Finally, state your personal identity and contact details so the responding officials can follow up with you later.

<!-- INJECT_ACTIVITY: dialogue-order -->

## Екстрені ситуації (Emergencies)

The universal emergency number in Ukraine is **112** (один один два). This number works absolutely everywhere in the country and connects you directly to a central dispatcher who can route your call. However, you must also know the specific direct numbers for specialized services. The number **101** connects directly to the **пожежна допомога** (fire service). The number **102** is the direct line for the **поліція** (police). Finally, **103** calls the **швидка допомога** (ambulance). These three numbers are non-negotiable memorization items for your personal safety in Ukraine.

:::caution
**Important distinction:** The numbers **101**, **102**, and **103** are the modern Ukrainian emergency lines. Never confuse these with the old Soviet lines.
:::

When you need immediate, life-saving action, you rely entirely on the power of the imperative mood. Because you are addressing an emergency operator or a random stranger on the street, you consistently use the formal plural imperative ending in **-іть**. Learn these core survival calls as complete, unbreakable chunks of language. Do not worry about grammatical analysis or verb conjugation right now; just memorize the sound and meaning so you can produce them automatically under intense pressure. For example, use the verb **викликати** (to call/summon):

*   **Допоможіть!** (Help!)
*   **Викличте швидку!** (Call an ambulance!)
*   **Викличте поліцію!** (Call the police!)

After successfully getting someone's attention, you must rapidly identify the specific situation. Introduce the exact problem using short, distinct labels. The word **тут** (here) is an incredibly useful tool for pointing out an active crisis happening right next to you. If you see someone collapse, shouting your medical alert instantly signals a severe emergency to nearby bystanders. For a more general statement of need, you can always state that you require immediate help.

*   **Тут аварія!** (There is an accident here!)
*   **Тут пожежа!** (There is a fire here!)
*   **Людині погано!** (Someone is feeling bad!)
*   **Мені потрібна допомога!** (I need help!)

The emergency operator will inevitably ask for your exact location. You must state your current address quickly and accurately. The standard Ukrainian address formula starts with the largest element and gets progressively smaller: **вулиця** (street), then **будинок** (building), and finally **квартира** (apartment). Reinforce this vital skill with the location vocabulary you learned from previous modules. Prepositions like **на** (on) and **біля** (near) become absolutely critical tools when you need to guide a speeding ambulance to your exact location.

*   **Я на вулиці Шевченка.** (I am on Shevchenko street.)
*   **Я біля метро.** (I am near the metro.)
*   **Адреса: вулиця Хрещатик, будинок десять.** (Address: Khreshchatyk street, building ten.)

<!-- INJECT_ACTIVITY: phrase-choice-quiz -->
<!-- INJECT_ACTIVITY: fill-in-emergency-call -->

## Допомога (Getting Help)

When seeking medical assistance at a local **лікарня** (hospital), always start with the direct request for a doctor. To explain your specific physical symptoms, use the standard structure for expressing pain. This unique structure literally translates to "At me aches". You just attach the necessary body part that is causing the discomfort. If you do not have a specific, localized pain but feel generally unwell, simply use the standard everyday expression for feeling ill.

*   **Мені потрібен лікар.** (I need a doctor.)
*   **У мене болить голова.** (My head hurts.)
*   **У мене болить живіт.** (My stomach hurts.)
*   **У мене болить горло.** (My throat hurts.)
*   **Мені погано.** (I feel bad.)

:::tip
The word **швидка** literally means "fast one" and is the natural, everyday word Ukrainians use for an ambulance. You do not need to say the full phrase.
:::

If you need to visit a local pharmacy for minor medical issues, use clear and polite requests for your medicine. However, the absolute most critical safety phrase you must learn involves medical precautions. You have to communicate your specific medical restrictions and severe allergies clearly before accepting any treatment. This ensures you do not receive medication that could cause a secondary emergency.

*   **Дайте, будь ласка, таблетки.** (Give me the pills, please.)
*   **Мені потрібні ліки.** (I need medicine.)
*   **У мене алергія на антибіотики.** (I am allergic to antibiotics.)
*   **У мене алергія на ці таблетки.** (I am allergic to these pills.)

Bureaucratic situations require you to provide your personal data to government officials clearly and accurately. Whether at a city hospital or a local police station, they will inevitably ask for your identity documents. Remember the critical difference between your **ім'я** (first name) and your **прізвище** (surname). If you lose something valuable, always use the past tense verb **загубити** (to lose) matched to your specific gender.

*   **Моє прізвище — Сміт.** (My surname is Smith.)
*   **Я з Канади.** (I am from Canada.)
*   **Мій паспорт у готелі.** (My passport is in the hotel.)
*   **Я загубив паспорт.** (I lost my passport. — masculine)
*   **Я загубила телефон.** (I lost my phone. — feminine)

:::note
In official contexts, your **прізвище** (surname) is much more important than your **ім'я** (first name). Always provide your surname first when speaking to police or hospital staff.
:::

During a high-stress conversation with authorities, you might simply fail to understand what the Ukrainian official is rapidly telling you. You must communicate your language barrier directly and honestly rather than just guessing what they said. Use these essential survival phrases to slow the entire exchange down and clarify the exact meaning before proceeding.

*   **Я не розумію.** (I do not understand.)
*   **Повторіть, будь ласка.** (Please repeat.)
*   **Ви говорите англійською?** (Do you speak English?)

<!-- INJECT_ACTIVITY: report-issue-fill-in -->

## Summary

Your emergency survival kit revolves entirely around a few core verbal actions. The number **112** is your absolute primary tool for any crisis. If you are in physical danger, shout the imperative for help immediately to draw massive public attention. Follow this quickly with loud requests for an ambulance or the police. Remember that sheer speed and absolute clarity in Ukrainian chunks always beat perfect grammatical case endings in these critical moments. A fast, incredibly clear alert provides all the context anyone needs.

Knowing your precise location is completely useless if you cannot express it clearly to the emergency operator. Always be ready to state your physical address using the strict logical order of street followed by building. If you are outside and feel slightly disoriented, rely heavily on large visible landmarks. Stating that you are near the metro station or directly opposite a large hotel gives the emergency services an immediate and tight search radius.

Medical and personal emergencies require highly specific vocabulary. Use the dedicated pain structure to describe your physical issues to a responding doctor. For frustrating administrative disasters, state that you lost your documents using the correct gendered past tense verb form. Always keep your official surname and mobile phone number ready for the inevitable official forms.

Before moving on to the next learning module, perform this final rigorous self-check to ensure you are truly ready for unexpected situations. Read these questions carefully and try to answer them aloud in clear Ukrainian. These phrases are your ultimate linguistic safety net. Practice them until they feel completely automatic, so you never have to search your memory for words when you truly need them the most.

*   Can you call 112 and state there is an accident? (**Тут аварія!**)
*   Can you give your current address including street and building? (**Вулиця..., будинок...**)
*   Can you tell a doctor what hurts? (**У мене болить...**)
*   Can you report a lost passport to the police? (**Я загубив паспорт. Моє прізвище...**)
*   Do you know the difference between 101, 102, and 103?

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: emergencies
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

**Level: A1.4+ (Module 54/55) — BEGINNER**

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
