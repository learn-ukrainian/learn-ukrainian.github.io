<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/euphony.yaml` file for module **28: Euphony** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-u-v-choice -->`
- `<!-- INJECT_ACTIVITY: quiz-naturalness-comparison -->`
- `<!-- INJECT_ACTIVITY: quiz-i-y-choice -->`
- `<!-- INJECT_ACTIVITY: fill-in-z-iz-zi -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: У or В? Choose correct form based on surrounding sounds.
  items: 10
  type: quiz
- focus: І or Й? Choose correct conjunction.
  items: 8
  type: quiz
- focus: З, із, or зі? Complete the sentence.
  items: 6
  type: fill-in
- focus: Which sentence sounds more natural? (euphony comparison)
  items: 6
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- Київ (Kyiv)
- Львів (Lviv)
- офіс (office, m)
- парк (park, m)
- театр (theater, m)
required:
- у/в (in/at — alternating preposition)
- і/й (and — alternating conjunction)
- з/із/зі (with/from — alternating preposition)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги — Милозвучність у дії
Ukrainian is not just a language of strict grammatical rules and rigid structures; it is fundamentally a language of music. The central concept that governs how words fit together in a sentence is called **милозвучність** (euphony, literally "sweet-soundingness"). This principle is the absolute secret to sounding like a native speaker. The core goal of **милозвучність** is avoiding difficult "clashes" of sounds. When too many consonants or too many vowels pile up next to each other, the language naturally alters a preposition or a conjunction to keep the air flowing smoothly from your mouth.

> **Студент:** Я працюю в городі. *(I work in the garden.)*
> **Друг:** Краще сказати «у городі». Звук «в» тут важко вимовити. *(It is better to say "у городі". The sound "в" is hard to pronounce here.)*
> **Студент:** Зрозумів. А як правильно: «в Києві» чи «у Києві»? Де ти живеш? *(Understood. And what is correct: "в Києві" or "у Києві"? Where do you live?)*
> **Друг:** Я живу в Києві. А ти? *(I live in Kyiv. And you?)*
> **Студент:** Я живу у Львові. *(I live in Lviv.)*
> **Друг:** У Львові гарно! *(It is beautiful in Lviv!)*

Let us carefully break down the prepositional choice from that first dialogue about a **город** (garden). When the speaker says **в Києві** (in Kyiv), the word immediately before it ends in a vowel (**живу** — I live), and the word **Києві** (Kyiv) starts with a crisp consonant (**К** — K). This creates a perfect, smooth transition. If they had said **у Києві** (in Kyiv), the two vowels (**у** and the **и** sound) would collide uncomfortably. Conversely, **у Львові** (in Lviv) is used instead of **в Львові** (in Lviv) because the latter option would create a massive, unpronounceable three-consonant cluster (**в-л-ь-в**). Euphony rules make sentences flow naturally.

> **Студент:** Ти і Олена йдете в кіно? *(Are you and Olena going to the cinema?)*
> **Друг:** Ти й Олена. Так швидше. *(You and Olena. It is faster this way.)*
> **Студент:** А, добре. Ні, я і Максим йдемо в парк. *(Ah, good. No, I and Maksym are going to the park.)*
> **Друг:** А Олена й Тарас? *(And Olena and Taras?)*
> **Студент:** Вони йдуть у театр. *(They are going to the theater.)*

Now, let us closely analyze the conjunction choice from this second conversation. The word for "and" can alternate to maintain a musical rhythm across the sentence. The letter **й** (y) acts as a quick glide between two distinct vowels, allowing the voice to slide smoothly from the end of **ти** (you) to the start of **Олена** (Olena). Note how **й** sits perfectly between vowels (**ти й Олена** — you and Olena). In contrast, the letter **і** (i) is a full vowel that provides a necessary physical break between heavy consonants. When you say **я і Максим** (I and Maksym), the **і** acts as a comfortable bridge between the surrounding consonant clusters.

## У чи В? Майстерність чергування
As noted in **Авраменко Grade 5** (p.117), the alternation **у–в** ensures the euphony of the language (**чергування у–в забезпечує милозвучність мови**). The core rule for choosing between the alternating prepositions **у** (in/at) and **в** (in/at) revolves around carefully avoiding consonant clusters. Think of it as building a comfortable "V-C-V" (vowel-consonant-vowel) sandwich in your mouth. You should use **в** after a vowel before a consonant. This simple pattern completely prevents a vowel clash. Conversely, you must use **у** after a consonant before a consonant to avoid a tongue-twisting pile-up. 
*   **Я живу в Києві.** (I live in Kyiv.)
*   **Я працюю в офісі.** (I work in an office.)
*   **Тарас у Львові.** (Taras is in Lviv.)
*   **Максим у банку.** (Maksym is at the bank.)

However, there is an important and specific exception regarding "difficult neighbors." Even if a preceding word ends neatly in a vowel, you must still use **у** if the following word starts with certain challenging consonant clusters. Specifically, use **у** before words starting with **в**, **ф**, **св**, or **льв**. This rule exists purely because these specific sounds are phonetically demanding to link directly with a **в**. 
*   **Вона працює у Франції.** (She works in France. — not **в Франції**)
*   **Я працюю у Львові.** (I work in Lviv.)
*   **Вони грають у футбол.** (They play football.)

Exceptions to know exist based on sentence position and natural pauses. The letter **У** is the absolute king at the start of a sentence. It provides a strong, clear, and resonant start, whereas starting with **в** would sound weak or muffled before another consonant. This exactly same logic applies immediately after a comma or a noticeable pause in your speech. 
*   **У мене є братик.** (I have a little brother. — always **У**)
*   **Так, у нас є час.** (Yes, we have time. — **У** after pause)
*   **У понеділок ми працюємо.** (On Monday we work.)

Don't overthink it — native speakers use euphony instinctively. The goal is to create sentences that SOUND smooth, not to engage in rigid rule application. This foundational principle of euphony goes far beyond just independent prepositions. It also applies to the initial letters of certain common vocabulary words. This applies to both the preposition (**в** / **у**) and the prefix (**вже** / **уже** — already). Many Ukrainian words have twin forms that alternate their starting letter depending entirely on the previous word. For example, the word for teacher alternates freely between **учитель** (teacher) and **вчитель** (teacher).
*   **Мій учитель читає текст.** (My teacher reads a text. — **у** after a consonant)
*   **Моя вчителька читає текст.** (My teacher reads a text. — **в** after a vowel)

<!-- INJECT_ACTIVITY: quiz-u-v-choice -->

<!-- INJECT_ACTIVITY: quiz-naturalness-comparison -->

## І чи Й? З, із, чи зі?
According to **Літвінова Grade 5** (p.176), the **і/й** (and) alternation follows a very similar and highly intuitive logic. The letter **й** is a semivowel that creates a fast, natural glide between two full vowels in a sentence. You use **й** between vowels. On the other hand, **і** is a full, distinct vowel used between consonants to physically separate them.
*   **Мама й тато вдома.** (Mom and dad are at home. — **Й** between vowels)
*   **Вона й він читають.** (She and he are reading.)
*   **Брат і сестра там.** (Brother and sister are there. — **І** between consonants)
*   **Тарас і Максим там.** (Taras and Maksym are there.)

Just like the strong initial **У** we studied earlier, we always use the full, robust vowel **І** at the start of a sentence or immediately after a pause. The semivowel **й** is simply too weak to start a new thought and can never be used as the first word of a sentence.
*   **І він прийшов.** (And he arrived. — always **І**)
*   **І ми працюємо там.** (And we work there.)

As highlighted in **Літвінова Grade 5** (p.177), the **з/із/зі** (with/from) alternation handles another set of consonant challenges. The preposition **з** is the standard, default form for indicating association or origin. It is a highly "sticky" consonant that naturally wants to attach itself to the following word. In most everyday situations, you will use **з** before vowels and most consonants.
*   **Я їду з Одеси.** (I am traveling from Odesa.)
*   **Він іде з другом.** (He is walking with a friend.)
*   **Вона гуляє з братом.** (She is walking with a brother.)

To successfully prevent the **з** from sticking to already difficult consonant clusters, Ukrainian uses the extended variants **із** and **зі**. You use **із** between consonants to expertly avoid an uncomfortable cluster. The special, distinct form **зі** is reserved for use before **з**, **с**, **ш**, **щ** or thick consonant clusters, as well as the fixed phrase **зі мною** (with me). This is a smaller rule than **у/в**, but it is highly important for natural speech.
*   **Він бере із шафи.** (He takes from the wardrobe.)
*   **Максим із Семеном там.** (Maksym with Semen are there.)
*   **Вітаємо зі святом.** (We congratulate with the holiday.)
*   **Вони йдуть зі школи.** (They are walking from school.)
*   **Він іде зі мною.** (He is walking with me.)

<!-- INJECT_ACTIVITY: quiz-i-y-choice -->

<!-- INJECT_ACTIVITY: fill-in-z-iz-zi -->

## Підсумок — Summary
Ukrainian euphony operates like three distinct, well-oiled "gears" that keep your speech running smoothly without ever grinding the engine. First, the **у/в** alternation helps you expertly avoid consonant clusters or awkward vowel clashes, especially when discussing locations. Second, the **і/й** alternation ensures that the audible connections between your nouns remain perfectly musical and fluid. Third, the **з/із/зі** alternation cleanly handles the most difficult, "sticky" consonant clusters that would otherwise stop your speech in its tracks. Always remember that these essential rules are about making speech physically easier for the SPEAKER, not just the listener. 

Here is a self-check list to review the three euphony pairs we have learned today:
*   **Q:** What does the **у/в** pair do?
    **A:** It helps avoid a consonant+consonant cluster. Say **у Львові** (in Lviv) or **в Києві** (in Kyiv).
*   **Q:** What does the **і/й** pair do?
    **A:** It helps avoid a vowel+vowel clash. Use it to cleanly link **брат і сестра** (brother and sister) or **мама й тато** (mom and dad).
*   **Q:** When do we use the **з/із/зі** pair?
    **A:** Use them before difficult clusters to maintain flow, such as **з другом** (with a friend), **із сестрою** (with a sister), or **зі мною** (with me).
*   **Q:** Which is correct: "Я живу в Києві" or "Я живу у Києві"?
    **A:** **Я живу в Києві.** (I live in Kyiv.)
*   **Q:** Which is correct: "Мама і тато" or "Мама й тато"?
    **A:** **Мама й тато.** (Mom and dad.)

Practice time: read your own sentences aloud — do they flow smoothly? If you find your tongue twisting over a pile of consonants, check if you need to shift one of these three euphonic gears to keep the melody flowing.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: euphony
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

**Level: A1.4+ (Module 28/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


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
