<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/transport.yaml` file for module **32: Transport** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-ticket-buying -->`
- `<!-- INJECT_ACTIVITY: quiz-transport-patterns -->`
- `<!-- INJECT_ACTIVITY: quiz-match-situation -->`
- `<!-- INJECT_ACTIVITY: fill-in-directions -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Which transport? Match situation to transport type.
  items: 8
  type: quiz
- focus: 'Buy a ticket: Один ___ до ___, будь ласка.'
  items: 6
  type: fill-in
- focus: Автобусом or на метро? Choose the right pattern.
  items: 6
  type: quiz
- focus: 'Ask for directions: Як дістатися до ___?'
  items: 6
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- трамвай (tram, m)
- маршрутка (minibus, f)
- літак (plane, m)
- направо (right)
- наліво (left)
- прямо (straight)
- дістатися (to get to)
required:
- автобус (bus, m)
- метро (metro, n)
- таксі (taxi, n)
- потяг (train, m)
- квиток (ticket, m)
- зупинка (stop, f)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Navigating a new city always starts with understanding the local transit system and learning how to ask the right questions. When arriving at the **Бориспіль** (Boryspil) airport outside of the capital city of Kyiv, the immediate practical challenge is reaching the city center. Travelers have a wide variety of choices depending on their budget, luggage, and final destination: they might take a regular public bus, board a fast express train, call a private taxi, or eventually transfer to the vast underground metro network.

> **Приїжджий:** Вибачте, як дістатися до вокзалу? *(Excuse me, how to get to the train station?)*
> **Друг:** Їдьте автобусом або на метро. *(Take a bus or by metro.)*
> **Приїжджий:** Який автобус? А можна на метро? *(Which bus? And is it possible by metro?)*
> **Друг:** Номер сім. Зупинка ось там. Спочатку треба їхати автобусом до метро «Харківська». *(Number seven. The stop is right there. First you must take a bus to the "Kharkivska" metro.)*
> **Приїжджий:** Дякую! *(Thank you!)*
> **Друг:** На здоров'я! *(You are welcome!)*

The key phrase in the first exchange is **як дістатися до...** (how to get to...), which is the most natural and common way to ask for directions to a specific place. This grammatical structure is always followed by a noun in the genitive case to indicate the destination, as seen in the word forms **до вокзалу** (to the station) and **до станції** (to the station). If a local resident helps you with directions and you thank them, a polite native response you will often hear is **На здоров'я!** (You are welcome!).

> **Пасажир:** Добрий день! Один квиток до Львова, будь ласка. *(Good day! One ticket to Lviv, please.)*
> **Касир:** В один бік чи туди й назад? *(One way or round trip?)*
> **Пасажир:** Туди й назад. Скільки коштує? *(Round trip. How much does it cost?)*
> **Касир:** П'ятсот гривень. Є потяг о дев'ятій ранку. *(Five hundred hryvnias. There is a train at nine in the morning.)*
> **Пасажир:** Дякую. О котрій годині він рушає? *(Thank you. At what time does it depart?)*
> **Касир:** О дев'ятій рівно. *(At nine exactly.)*

When buying tickets at a terminal or speaking with a conductor, the clerk will routinely ask if your journey is **в один бік** (one way) or **туди й назад** (round trip, literally "there and back"). This everyday interaction naturally integrates expressions of time like **о дев'ятій** (at nine) and simple numbers such as **п'ятсот** (five hundred) to quickly confirm the departure schedule and the final price. Knowing these set phrases makes traveling across Ukraine much smoother and reduces confusion at the ticket counter.

<!-- INJECT_ACTIVITY: fill-in-ticket-buying -->

## Транспорт (Transport Types)

Every major Ukrainian city relies on a robust and heavily utilized network of **громадський транспорт** (public transport). The core of this system typically consists of the "big four" modes of transit. You will frequently see an **автобус** (bus, masculine), a **тролейбус** (trolleybus, masculine), and a **трамвай** (tram, masculine) operating above ground, while larger metropolitan areas like Kyiv and Kharkiv feature a fast underground **метро** (metro, neuter). Grammatically, the words **метро** (metro) and **таксі** (taxi, neuter) are special cases in the language. They are nouns of foreign origin and are completely indeclinable, meaning their word endings never change regardless of their role in a sentence.

For longer journeys stretching between cities, travelers rely heavily on intercity options like a passenger **потяг** (train, masculine) or a commercial **літак** (plane, masculine). In daily conversation, the word **потяг** (train) is often used interchangeably with **поїзд** (train). Within city limits and for commuting between nearby towns, you will undoubtedly encounter the ubiquitous **маршрутка** (minibus, feminine), which operates on fixed municipal routes but traditionally stops on passenger demand. Personal transit is usually done by **машина** (car, feminine). To catch any of these transport types, you need to know the right location: you must head to a **вокзал** (station) for trains, navigate to an **аеропорт** (airport) for flights, or simply wait patiently at a local neighborhood **зупинка** (stop).

When stating exactly how you are traveling, the Ukrainian language makes a strict grammatical distinction between moving on foot and moving by a vehicle. While you say **іти пішки** (to go on foot), traveling by any type of machine requires the motion verb **їхати** (to go by transport). For standard declinable nouns, you indicate the means of transportation by putting the noun directly into the instrumental case without any added preposition. This form clearly shows the instrument or tool you use to travel.
*   «Я їду **автобусом**.» *(I am going by bus.)*
*   «Він їде **потягом**.» *(He is going by train.)*
*   «Ми їдемо **трамваєм**.» *(We are going by tram.)*
*   «Вони їдуть **тролейбусом**.» *(They are going by trolleybus.)*

A fundamentally different grammatical pattern applies to indeclinable nouns and certain specific vehicles. Instead of using the bare instrumental case, you must use the preposition **на** (on/at) followed immediately by the locative case. Since words like **метро** (metro) and **таксі** (taxi) do not decline, their forms remain identical, while words like **машина** (car) take standard locative endings. Both patterns simply mean "by" a certain transport, but they are grammatically distinct.
*   «Я їду **на метро**.» *(I am going by metro.)*
*   «Він їде **на таксі**.» *(He is going by taxi.)*
*   «Ми їдемо **на машині**.» *(We are going by car.)*

:::caution
Never mix these two grammatical patterns together. A common learner mistake is saying «на автобусом» — this structure is strictly incorrect. While the locative form «на автобусі» (on the bus) is grammatically possible and occasionally heard, using the pure instrumental form **автобусом** (by bus) is far more idiomatic and natural for native speakers. You should learn each transport type with its preferred prepositional or non-prepositional pattern from the beginning.
:::

<!-- INJECT_ACTIVITY: quiz-transport-patterns -->
<!-- INJECT_ACTIVITY: quiz-match-situation -->

## Корисні фрази (Useful Phrases)

When navigating unfamiliar city streets or crowded transit hubs, a few precise questions will help you find the correct transit option without getting lost. If you are looking for a place to wait for a ride, simply ask a friendly passerby **Де зупинка автобуса?** (Where is the bus stop?) or **Де найближча станція метро?** (Where is the nearest metro station?). Once you locate the physical stop, you must ensure you board the vehicle going in the right direction. Use these straightforward phrases to identify the correct route:
*   «**Який автобус їде в центр?**» *(Which bus goes to the center?)*
*   «**Вам потрібен номер п'ять.**» *(You need number five.)*

If you need to check the schedule or fare while standing at the terminal, you can confidently ask **Коли наступний потяг?** (When is the next train?) or **Скільки коштує квиток?** (How much is a ticket?) to gather the necessary details.

Once you board a vehicle, communicating effectively with other passengers becomes highly important, especially during the morning or evening rush hour. If you are unsure of your current location along the route, you can simply ask **Яка це зупинка?** (What stop is this?). Ukrainian public transport can get quite crowded during peak times. If someone is blocking your path to the exit doors, the standard, polite way to ask them to let you pass is **Вибачте, ви виходите?** (Excuse me, are you getting off?). If they are not stepping out, they will generally move aside. When the vehicle doors finally open, you can ask **Мені виходити тут?** (Do I get off here?) to confirm your destination, or firmly announce that you are leaving.

When asking the bus driver or a local resident to guide you to a location, you will frequently hear basic directional vocabulary. We now revisit the core movement words: **прямо** (straight), **направо** (right), and **наліво** (left). These spatial adverbs combine seamlessly with transport instructions to create clear routes. If you need help finding a specific landmark, you can ask **Вибачте, як дістатися до...?** (Excuse me, how do I get to...?).
*   «Ідіть **прямо** до вокзалу.» *(Go straight to the station.)*
*   «Поїдьте **прямо**, а потім поверніть **направо** на зупинці.» *(Drive straight, and then turn right at the stop.)*
*   «Станція метро **наліво**.» *(The metro station is to the left.)*
Recognizing these three distinct directions ensures you can properly follow instructions whether you are walking to a transit platform or directing a taxi driver to your hotel.

Discussing schedules and timetables requires using accurate verbs of departure. Many learners mistakenly use the word «відправлятися» (to depart), but this is a direct phonetic calque from Russian and sounds unnatural in standard conversational Ukrainian. Instead, you must use native verbs that describe motion accurately based on the type of vehicle. For heavy transit vehicles like trains starting to move along a track, use the verb **рушати** (to depart / to set in motion). For scheduled vehicles like buses leaving a large station, use **відбувати** (to depart) or **виїжджати** (to drive out / to leave).
*   «**Потяг рушає о восьмій.**» *(The train departs at eight.)*
*   «**Автобус виїжджає з автовокзалу.**» *(The bus leaves from the bus station.)*

<!-- INJECT_ACTIVITY: fill-in-directions -->

## Підсумок — Summary

Navigating a bustling Ukrainian city is remarkably straightforward once you master the core transport vocabulary and foundational grammatical patterns. In this module, we have learned to correctly identify the main types of transit vehicles, including the **автобус** (bus), **потяг** (train), **таксі** (taxi), and **метро** (metro). You now know exactly how to describe your specific method of travel using two distinct linguistic structures: the direct instrumental case pattern for declinable nouns like **автобусом** (by bus), and the locative construction with a preposition for indeclinable nouns like **на метро** (by metro). We also covered highly practical daily scenarios, such as buying a train ticket at a station window by asking for **один квиток** (one ticket) and inquiring about transit schedules using precise phrases like **о котрій годині** (at what time) and the authentic Ukrainian motion verb **рушати** (to depart). Mastering these fundamental elements allows you to travel across the country with much greater confidence.

Review the following questions to verify your personal understanding of this module's key phrases. Cover the provided answers and test yourself aloud before moving forward to the next lesson.

**How do you say "I am going to work by bus"?**
> «Я їду на роботу автобусом.»

**How do you ask "Where is the train station?"**
> «Де залізничний вокзал?»

**How do you buy a train ticket to Lviv (round trip)?**
> «Один квиток до Львова туди й назад, будь ласка.»

**How do you ask "What stop is this?"**
> «Яка це зупинка?»

**How do you say "Go straight and then left"?**
> «Ідіть прямо, а потім наліво.»

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: transport
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

**Level: A1.4+ (Module 32/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
