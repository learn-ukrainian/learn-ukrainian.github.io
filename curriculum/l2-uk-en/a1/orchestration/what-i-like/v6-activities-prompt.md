<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/what-i-like.yaml` file for module **15: What I Like** (a1).

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

- `<!-- INJECT_ACTIVITY: match-up-infinitives -->`
- `<!-- INJECT_ACTIVITY: fill-in-hobbies -->`
- `<!-- INJECT_ACTIVITY: quiz-like-choice -->`
- `<!-- INJECT_ACTIVITY: fill-in-negatives -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Complete: Я люблю ___. (choose infinitive for the picture)'
  items: 8
  type: fill-in
- focus: Люблю or подобається? Choose the right structure.
  items: 8
  type: quiz
- focus: 'Match infinitives to their meanings: читати ↔ to read'
  items: 8
  type: match-up
- focus: 'Make it negative: Я люблю → Я не люблю'
  items: 6
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- малювати (to draw)
- подорожувати (to travel)
- співати (to sing)
- музика (music, f)
- фільм (film, m)
- книга (book — review from M08)
required:
- любити (to love/like — verb)
- подобатися (to be pleasing — used as 'to like')
- читати (to read)
- гуляти (to walk)
- готувати (to cook)
- слухати (to listen)
- дивитися (to watch)
- грати (to play)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

When you meet someone new, one of the first topics of conversation is usually hobbies and interests. Finding common ground is a great way to build a connection. In Ukrainian, expressing what you enjoy doing is quite straightforward, but it requires learning a specific sentence pattern. 

Let us look at a typical conversation. Anna is an English speaker attending her first language exchange meetup in Kyiv. She is paired with Viktor, a local tandem partner. They are having tea and getting to know each other. Pay attention to how they ask about and describe their favorite activities.

> **Віктор:** Привіт! **Що ти любиш робити?** *(Hi! What do you like to do?)*
> **Анна:** Привіт! **Я люблю читати і слухати музику.** *(Hi! I like to read and listen to music.)*
> **Віктор:** Цікаво! А **я люблю готувати.** *(Interesting! And I like to cook.)*
> **Анна:** Правда? **Що ти готуєш?** *(Really? What do you cook?)*
> **Віктор:** Я готую борщ. *(I cook borscht.)*

In this first exchange, Viktor uses the phrase **Що ти любиш робити?** (What do you like to do?) to ask about Anna's general interests. Anna responds by pairing the verb **люблю** (I like/love) with the action words **читати** (to read) and **слухати** (to listen). 

Later in their conversation, Viktor pulls out a novel and a DVD from his bag to ask Anna about her specific tastes regarding objects. Notice how the sentence structure completely changes when they switch from talking about *actions* to talking about *things*.

> **Віктор:** Дивись. **Тобі подобається ця книга?** *(Look. Do you like this book?)*
> **Анна:** Так, **мені подобається.** *(Yes, I like it.)*
> **Віктор:** А цей фільм? *(And this film?)*
> **Анна:** Ні, **мені не подобається цей фільм. Мені подобається музика.** *(No, I don't like this film. I like music.)*

If you look closely at the two dialogues, you will see a clear division in how preferences are expressed. When Anna and Viktor talked about *doing* things—the actions of reading or cooking—they used the word **люблю**. However, when they shifted the topic to *things*—the physical book, the film, and the music—they used the phrase **подобається**. 

This transition from verbs to nouns requires two different grammatical approaches in Ukrainian. We will break down both of these essential patterns so you can start sharing your own interests confidently.

## Я люблю... (I Like...)

When you want to talk about your active hobbies, passions, and the things you physically enjoy doing, the most direct way is to use the verb **любити** (to love/to like). The formula for building these sentences is very similar to English. 

You start with the subject **Я** (I), follow it with the conjugated verb **люблю** (like/love), and finish with the action you enjoy. The action word must be in its basic, unaltered dictionary form, which we call the infinitive.

*   **Я люблю читати.** (I like to read.)
*   **Я люблю малювати.** (I like to draw.)
*   **Я люблю співати.** (I like to sing.)

To use this structure, you need to be able to recognize a Ukrainian infinitive. The infinitive is the base form of a verb before it is changed to match a person or a tense. In English, we indicate the infinitive by putting the word "to" in front of the verb (to read, to walk). In Ukrainian, the infinitive is indicated by a specific suffix at the very end of the word. 

The dictionary form of a Ukrainian verb always ends in the suffix **-ти**. When you look up a new action word, this is the form you will find. 

*   **читати** (to read)
*   **гуляти** (to walk)
*   **слухати** (to listen)

The most important rule to remember for this pattern is that the ending **-ти** never changes when it follows **Я люблю**. It functions as a single, locked unit. 

Let us expand your vocabulary with some high-frequency verbs for free time. You can plug any of these directly into the formula. 

*   **дивитися** (to watch)
*   **грати** (to play)
*   **подорожувати** (to travel)
*   **готувати** (to cook)

:::tip
When you talk about playing games or instruments, Ukrainian uses specific prepositions that you must memorize as fixed phrases. If you are playing a sport or a game, use the preposition **у** (in). If you are playing a musical instrument, use the preposition **на** (on).
*   **Я люблю грати у футбол.** (I like to play football.)
*   **Я люблю грати на гітарі.** (I like to play the guitar.)
:::

<!-- INJECT_ACTIVITY: match-up-infinitives -->

<!-- INJECT_ACTIVITY: fill-in-hobbies -->

Of course, you will not enjoy every activity. To express a negative preference, the rule is incredibly simple. To say "I don't like", we simply place the negative particle **не** (not) directly before the verb. 

In Ukrainian, **не** is always written as a completely separate word. It does not attach to the verb, and it does not change the spelling of the words around it. 

*   **Я люблю гуляти.** (I like to walk.)
*   **Я не люблю гуляти.** (I do not like to walk.)
*   **Я не люблю готувати.** (I do not like to cook.)

## Мені подобається... (I Like...)

Now that you know how to talk about actions, we need to look at the second structure. When you want to say that you like a specific *thing*—a noun, an object, a place, or a piece of art—you will use the construction **Мені подобається** (I like). 

This phrase literally translates to "To me it is pleasing." At this stage in your learning, you should treat **Мені подобається** as a fixed, memorized chunk of language. Do not worry about analyzing why the word for "I" changes to **Мені**. Just memorize the phrase as a single unit and place the object you like directly after it.

*   **Мені подобається книга.** (I like the book.)
*   **Мені подобається музика.** (I like the music.)
*   **Мені подобається Київ.** (I like Kyiv.)

You might be wondering how to choose between the two structures. The distinction is pedagogical and helps you sound much more natural. The verb **любити** is reserved for active hobbies, deep passions, and things you truly "love." It carries a strong emotional weight. 

*   **Я люблю читати.** (I love to read. This is my passion.)

The phrase **подобатися**, on the other hand, is used for general liking, everyday objects, and first impressions. It is a lighter, more objective evaluation. 

*   **Мені подобається цей фільм.** (I like this film. It is a good movie.)

To invite someone else to share their preferences, you need to know how to ask questions. Both structures can be easily turned into questions by changing your intonation and using the correct pronoun for "you."

*   **Ти любиш читати?** (Do you like to read?)
*   **Тобі подобається цей фільм?** (Do you like this film?)

If the answer is no, you apply the negative particle just as we did before. Place **не** directly before the verb **подобається**. Note that the word order in the question, such as **Тобі подобається** or **Подобається тобі**, can vary freely in conversational Ukrainian, but the core chunk remains intact.

*   **Мені не подобається.** (I do not like it.)
*   **Мені не подобається ця музика.** (I do not like this music.)

<!-- INJECT_ACTIVITY: quiz-like-choice -->

<!-- INJECT_ACTIVITY: fill-in-negatives -->

:::caution
English speakers frequently make a critical mistake by trying to translate "I like" directly word-for-word when talking about objects. They will say **Я подобаюся футбол**. This is incorrect because it literally means "I am pleasing to football." 

Always remember that in Ukrainian, the object (the football) is the thing doing the pleasing. You must use the fixed chunk: **Мені подобається футбол** (Football is pleasing to me).
:::

## Підсумок — Summary

You now have the tools to discuss your hobbies and interests confidently. We have covered two distinct ways to say "I like," each serving a specific grammatical purpose. First, when you are talking about activities and actions, use the formula **Я люблю** followed by a verb in the infinitive. Remember that the infinitive is the dictionary form of the verb and always ends in the suffix **-ти**. 

*   **Я люблю співати.** (I like to sing.)

Second, when you are talking about things, objects, or places, use the fixed phrase **Мені подобається** followed by a noun. Treat this phrase as a single memorized chunk.

*   **Мені подобається музика.** (I like the music.)

To express that you do not like something, the negative particle **не** always comes as a separate word directly before the verb. This works for both structures.

*   **Я не люблю готувати.** (I do not like to cook.)
*   **Мені не подобається фільм.** (I do not like the film.)

Before moving on to the next module, take a moment to test your understanding with this self-check checklist. Can you answer these prompts confidently?

*   Can you name three hobbies using the correct verb structure? (**Я люблю читати, малювати, гуляти.**)
*   Can you name two things or objects that you like? (**Мені подобається музика, книга.**)
*   Do you know the defining suffix of a Ukrainian infinitive verb? (**-ти**).
*   Can you tell a friend that you don't like a specific object? (**Мені не подобається...**).
*   Do you know which preposition to use when talking about playing the guitar (**на**) versus playing football (**у**)?

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: what-i-like
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

**Level: A1.2-A1.3 (Module 15/55) — EARLY BEGINNER**

The learner knows the alphabet and ~200 words. They:
- Can read Ukrainian slowly
- Know basic nouns, adjectives, simple verb forms
- Cannot handle complex sentences or grammar terminology in Ukrainian

**Instructions in simple English with Ukrainian key terms in bold.**
Example: 'Choose the correct form of **мій/моя/моє**'

**Good activity types:** quiz, fill-in (simple sentences), match-up, group-sort, true-false, observe, anagram, translate (English→Ukrainian), error-correction (simple), divide-words, count-syllables, odd-one-out, order.


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
