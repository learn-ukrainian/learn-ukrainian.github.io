<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/stress-and-melody.yaml` file for module **4: Stress and Melody** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-stress-position -->`
- `<!-- INJECT_ACTIVITY: match-stress-pairs -->`
- `<!-- INJECT_ACTIVITY: quiz-sentence-type -->`
- `<!-- INJECT_ACTIVITY: fill-in-punctuation -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Where is the stress? Choose the correct syllable.
  items: 8
  type: quiz
- focus: 'Match stress pairs: замок (castle) ↔ замок (lock)'
  items: 4
  type: match-up
- focus: Statement, question, or exclamation? Choose based on punctuation.
  items: 6
  type: quiz
- focus: 'Add the correct punctuation: Це кава_ Де метро_ Як гарно_'
  items: 6
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- мука (flour) — stress pair with мука (torment)
- ранок (morning) — first-syllable stress
- метро (metro) — last-syllable stress
- фотографія (photograph) — long word practice
required:
- наголос (stress/accent) — metalanguage word
- замок (castle) — stress pair (first syllable)
- замок (lock) — stress pair (second syllable)
- кава (coffee) — first-syllable stress
- вода (water) — second-syllable stress
- столиця (capital) — Київ — столиця України


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Наголос (Stress)

**Заболотний Grade 5 p.73** teaches that the Ukrainian language has 38 distinct sounds. When you combine these sounds into words, one syllable always stands out. This emphasis is called **наголос** (stress). The **наголошений склад** (stressed syllable) is pronounced louder and held slightly longer than the rest of the word. A helpful technique to find the stress in a new word is to imagine you are "calling" the object from far away. If you call a turtle — **черепаха** (turtle) — you naturally stretch the third syllable: *черепаааха*. That stretched syllable is where the stress falls. Unlike English, where unstressed vowels often collapse into a weak "uh" sound, Ukrainian vowels keep their core phonetic shape. An unstressed **О** still sounds like **О**, just shorter and quieter.

Ukrainian stress is **вільний** (free). It is not locked to a specific position in the word. In French, the stress always falls on the last syllable. In Polish, it consistently falls on the penultimate syllable. In Ukrainian, it can appear anywhere. You must learn the stress pattern of each individual word. Many common words for beginners have stress on the first syllable: **мама** (mother), **тато** (father), **ранок** (morning), **кава** (coffee), and **книга** (book). Others have stress firmly on the second or last syllable: **вода** (water), **зима** (winter), **рука** (hand/arm), **метро** (metro), and **кафе** (cafe). Some have middle stress, like **столиця** (capital) in the phrase **Київ — столиця України** (Kyiv is the capital of Ukraine).

Furthermore, Ukrainian stress is **рухомий** (mobile). When a word changes its form, the stress can jump to a different syllable. When you talk about one hand, you say **рука** (hand). When you talk about two hands, the stress shifts to the first syllable: **руки** (hands).

Stress is critical because it dictates meaning. In English, placing stress on the wrong syllable usually just gives you a strange accent. In Ukrainian, getting the stress wrong often means you are saying a completely different word. These pairs of words that look identical but sound different are called **омографи** (homographs). Consider the word for a castle. A castle is a **замок** (castle), with the stress on the first syllable. A lock for a door is a **замок** (lock), with the stress on the second syllable. If you say the wrong one, the sentence changes entirely. Another stark pair is **мука** (torment), stressed on the first syllable, versus **мука** (flour), stressed on the second syllable. This distinction also applies to adjectives. The noun **дорога** (road) has stress on the second syllable. The adjective **дорога** (expensive) has stress on the final syllable.

:::tip
In textbooks and dictionaries, stress marks (') appear above the stressed vowel to guide learners. You will see them in your study materials. However, they do not appear in everyday Ukrainian writing. When reading a newspaper or a menu, you must know the word's stress pattern from memory. As a learner, always check *goroh.pp.ua* when you are unsure about pronunciation.
:::

<!-- INJECT_ACTIVITY: quiz-stress-position -->

<!-- INJECT_ACTIVITY: match-stress-pairs -->

## Інтонація (Intonation)

The melody of your voice is called **інтонація** (intonation). Ukrainian uses sentence melody to communicate the fundamental purpose of the sentence. The language classifies sentences by their goal. Declarative sentences, which state facts, are **розповідні** (declarative). Interrogative sentences, which ask questions, are **питальні** (interrogative). Imperative sentences, which give commands, are **спонукальні** (imperative). Any of these three types can also be exclamatory — **окличні** (exclamatory) — if spoken with strong emotion. For A1 learners, focus on the three basic punctuation patterns: the period (.) for statements, the question mark (?) for questions, and the exclamation point (!) for exclamations and commands. These marks are the visual map for your spoken melody.

The contrast between a statement and a yes/no question relies entirely on the pitch of your voice. A statement uses falling intonation. You start at a normal pitch and drop lower at the end. Look at this sentence:

> **Оксана:** Це кава. *(This is coffee.)*

Your voice falls (↘) on the word **кава**. It sounds final and decisive. Same words, different melody, different meaning. Use the exact same words, but a different melody, to ask a question:

> **Оксана:** Це кава? *(Is this coffee?)*

For a yes/no question, you must use rising intonation (↗). You raise the pitch of your voice sharply on the stressed syllable of the key word you are asking about. In this case, your voice spikes upward on the first syllable of **кава**. The rise must be distinct and obvious. If your voice stays flat or falls, a Ukrainian speaker will hear a statement, not a question.

There is a major exception: questions that begin with specific question words. Words like **хто** (who), **що** (what), **де** (where), and **коли** (when) do the grammatical work of asking the question. Because the question word already signals the intent, the sentence melody does not need to rise at the end. Instead, questions with question words usually end with a falling intonation (↘).

> **Степан:** Що це? *(What is this?)*  
> **Степан:** Де метро? *(Where is the metro?)*  

Your voice falls at the end of both sentences because the question word does the work. This creates a direct contrast with yes/no questions, which lack question words and therefore always rise: **Це метро?** (↗).

Exclamations and emotional statements use a strong falling intonation (↘↘). You place intense vocal weight on the stressed syllable of the core word, and then drop your pitch significantly. This pattern applies to enthusiastic greetings and expressions of strong feeling.

> **Максим:** Як гарно! *(How beautiful!)*  
> **Максим:** Привіт! *(Hi!)*  

You can also use **логічний наголос** (logical stress) to shift the focus of a sentence. By emphasizing one specific word, you change the exact meaning of the statement without altering the grammar or the words themselves.

<!-- INJECT_ACTIVITY: quiz-sentence-type -->

<!-- INJECT_ACTIVITY: fill-in-punctuation -->

## Читаємо вголос (Reading Aloud)

Reading multisyllable Ukrainian words correctly requires a systematic approach. Follow a simple three-step method to build muscle memory and rhythm. First, break the word into distinct syllables. Take the word for photograph: **фо-то-гра-фі-я** (photograph). Second, locate the stressed syllable. In this word, the stress falls on the third **а**: **фотографія**. Third, read the word slowly, ensuring the stressed syllable is the loudest and longest. Once you have the pattern, read at natural speed. Apply this same method to the word for Ukrainian: **у-кра-їн-ська** (Ukrainian). The stress falls on the **ї**. For the word rest, the breakdown is **ві-дпо-чи-нок** (rest), with the stress on the **и**.

Word list practice helps you internalize different stress patterns. Read the following words aloud with correct **наголос**. First, find the stressed syllable, then read the whole word at natural speed. Read these words: **Ки-їв** (Kyiv), **мо-ло-ко** (milk), **ран-ок** (morning), **ка-ва** (coffee), **во-да** (water), **зи-ма** (winter), and **у-кра-їн-ська** (Ukrainian). Break them down mentally and push your voice heavily on the stressed vowel.

Dialogue practice bridges the gap between single words and connected speech. Apply your knowledge of stress and intonation to a real conversation. In this interaction, two people exchange greetings and ask basic questions. Watch how the melody changes based on the punctuation and the sentence type.

> **Бариста:** Привіт! *(Hi!)*  
> **Клієнт:** Привіт! Як справи? *(Hi! How are you?)*  
> **Бариста:** Добре! А у тебе? *(Good! And you?)*  
> **Клієнт:** Добре! Це твоя кава? *(Good! Is this your coffee?)*  
> **Бариста:** Так, це моя кава. Дякую! *(Yes, this is my coffee. Thank you!)*  

The first **Привіт!** has a strong falling exclamation (↘↘). The question **Як справи?** contains a question word (**як**), so it has a falling intonation (↘). The question **А у тебе?** is a yes/no question without a question word, so it requires a sharp rising intonation (↗). The same rising pitch (↗) applies to **Це твоя кава?**. Finally, the response **Так, це моя кава.** is a simple declarative statement, ending with a standard falling intonation (↘), and **Дякую!** finishes the interaction with a strong falling exclamation (↘↘). Apply these intonation patterns to the greetings you have already learned.

## Підсумок — Summary

Stress and melody are the physical heartbeat of the spoken language. A single word's identity is anchored by its **наголос**. Because Ukrainian stress is free and mobile, it can fall on any syllable and can shift when a word changes form. You must memorize the stress pattern along with the word itself, because shifting the stress can completely change a word's meaning, turning a castle into a lock, or flour into torment. In written Ukrainian, punctuation marks serve as the sheet music for your voice. They tell you exactly how to manipulate your sentence melody.

Intonation distinguishes a statement of fact from a question of inquiry. A declarative statement always uses a falling pitch (↘). A yes/no question requires a sharp, noticeable rise (↗) on the specific word you are asking about. However, sentences that start with question words like **що** or **де** do the asking for you, and therefore use a falling pitch (↘). Always listen carefully to native speakers, whether in person, in podcasts, or in videos. Their natural sentence rhythm and melody are exactly what you are aiming to reproduce.

Self-check your understanding of these core principles. Answer these questions out loud:

- What is **наголос**? It is the louder, longer syllable that carries the weight of a word.
- Can stress change a word's meaning? Yes, moving the stress can create entirely different words, such as **замок** (castle) and **замок** (lock).
- What intonation do you use for a yes/no question? You use a rising intonation (↗) on the key word.
- Do questions starting with **Що** or **Де** always rise? No, they usually have a falling intonation (↘).
- Read this aloud with correct stress and melody:
  **Це аптека?** *(Is this a pharmacy?)*
  **Так, це аптека.** *(Yes, this is a pharmacy.)*
  **Як гарно!** *(How beautiful!)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: stress-and-melody
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

**Level: A1.1 (Module 4/55) — COMPLETE BEGINNER**

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

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

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
