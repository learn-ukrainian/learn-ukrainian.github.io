<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/i-want-i-can.yaml` file for module **18: I Want, I Can** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-khotity-conjugation -->`
- `<!-- INJECT_ACTIVITY: quiz-verb-patterns -->`
- `<!-- INJECT_ACTIVITY: quiz-modal-choice -->`
- `<!-- INJECT_ACTIVITY: fill-in-modal-logic -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Conjugate: я хоч__, ти хоч__, він хоч__'
  items: 9
  type: fill-in
- focus: Хочу, можу, or мушу? Choose the right modal for the situation.
  items: 8
  type: quiz
- focus: 'Complete: Я ___ гуляти, але не ___ — ___ працювати.'
  items: 6
  type: fill-in
- focus: Regular or irregular? Identify the conjugation pattern.
  items: 6
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- шкода (pity, unfortunately)
- допомогти (to help)
- борщ (borscht, m)
- порекомендувати (to recommend)
- треба (need to — impersonal, preview)
required:
- хотіти (to want — irregular!)
- могти (to be able/can — irregular!)
- мусити (to must/have to)
- кава (coffee, f)
- їсти (to eat)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги — Making Plans

To express your weekend plans, daily intentions, or obligations, you need to navigate between what you desire, what is actually possible, and what is required. When two friends negotiate their free time, they are constantly weighing these three factors to find an activity that works for both of them. Consider a typical conversation about making plans between **Оля** (Olya) and **Денис** (Denys). They are trying to figure out their weekend schedule.

> **Оля:** Що ти хочеш робити? *(What do you want to do?)*
> **Денис:** Я хочу гуляти. А ти? *(I want to walk. And you?)*
> **Оля:** Я не можу, я мушу працювати. *(I can't, I must work.)*
> **Денис:** Шкода! *(Pity!)*

In another common situation, such as ordering at a café or asking a waiter for advice, expressing a clear desire for an object is essential.

> **Відвідувач:** Я хочу каву. *(I want coffee.)*
> **Офіціант:** Велику чи маленьку? *(Large or small?)*
> **Відвідувач:** Велику. І ще я хочу їсти. Що ви можете порекомендувати? *(Large. And also I want to eat. What can you recommend?)*
> **Офіціант:** Можу порекомендувати борщ! *(I can recommend borscht!)*

Breaking down the key phrases from these dialogues reveals how Ukrainian structures them. The exclamation **шкода** means "pity" or "unfortunately," and it is a very natural and highly common reaction when someone cannot join your plans. More importantly, notice how the verb "to want" behaves differently depending on what exactly follows it. You can pair it directly with a physical object, as in **я хочу каву** (I want coffee). Here, the original dictionary noun **кава** (coffee) changes its ending to **каву** because it is the grammatical object of the desire. Alternatively, you can pair the verb "to want" with another action entirely, as in **я хочу їсти** (I want to eat) or **я хочу гуляти** (I want to walk), demonstrating your intention to perform a specific activity.

## Хотіти (To Want)

The verb **хотіти** (to want) is one of the most frequently used words in the Ukrainian language, and it operates as a true irregular verb. Despite ending in **-іти**, which typically signals a Group II conjugation pattern, **хотіти** actually conjugates according to the specific rules of Group I. When pronouncing this word, you must ensure that you make the first vowel a clear, open Ukrainian **о**, carefully distinguishing it from the reduced sounds you might encounter in other Slavic languages. 

A key morphological feature of **хотіти** is the consistent consonant shift that occurs right in its root. As you conjugate it through the present tense, the letter **т** from the dictionary form (**хот-**) changes entirely to the letter **ч** (**хоч-**) across every single grammatical person. This shift is a very common and essential phonetic pattern in Ukrainian.

*   **я хочу** (I want)
*   **ти хочеш** (you want)
*   **він/вона хоче** (he/she wants)
*   **ми хочемо** (we want)
*   **ви хочете** (you want - formal/plural)
*   **вони хочуть** (they want)

When you express a direct desire for a physical object, you use **хотіти** followed immediately by a noun. This noun must take the Accusative case because it directly receives the action of wanting. For feminine nouns ending in **-а**, the ending changes to **-у**. Thus, **вода** (water) becomes **воду**, and **кава** (coffee) becomes **каву**. For masculine inanimate nouns, the form remains exactly the same as the dictionary form, requiring no visible change at all.

*   **Я хочу воду.** (I want water.)
*   **Він хоче каву.** (He wants coffee.)
*   **Я хочу сік.** (I want juice.)
*   **Вона хоче борщ.** (She wants borscht.)

When you want to express a clear desire to perform an action, you use what is called a Compound Verbal Predicate structure. This simply means you take the conjugated modal verb (**хочу**, **хочеш**, etc.) and immediately follow it with the infinitive form of the main verb. Unlike English, which explicitly requires the particle "to" placed between the two verbs, Ukrainian simply links them directly together. To form the negative, place the particle **не** directly before the verb: **я не хочу** (I do not want), **ти не хочеш?** (do you not want?), **вона не хоче** (she does not want). While polite requests use conditional forms like **хотів би** or **хотіла би** (I would like) — which you will learn later — for now, **я хочу** is the standard, direct way to express a want.

*   **Я хочу читати.** (I want to read.)
*   **Я не хочу спати.** (I do not want to sleep.)
*   **Ти не хочеш гуляти?** (Do you not want to walk?)

<!-- INJECT_ACTIVITY: fill-in-khotity-conjugation -->
<!-- INJECT_ACTIVITY: quiz-verb-patterns -->

## Могти і мусити (Can and Must)

The verb **могти** (can, to be able) expresses personal ability or granted permission, and it is also classified as an irregular Group I verb. Much like "to want", it features a significant consonant shift within its root structure. The original letter **г** (**мог-**) transforms into **ж** (**мож-**) in almost all present tense forms, but uniquely, it returns back to the original letter **г** strictly in the "they" form.

*   **я можу** (I can)
*   **ти можеш** (you can)
*   **він/вона може** (he/she can)
*   **ми можемо** (we can)
*   **ви можете** (you can - formal/plural)
*   **вони можуть** (they can)

You will use **могти** primarily to talk about your internal physical abilities, to discuss newly acquired skills, or to formally ask for permission from someone else. It functions identically to **хотіти** by forming a compound structure with a following infinitive verb to create a complete thought.

*   **Я можу говорити українською.** (I can speak Ukrainian.)
*   **Ти можеш допомогти?** (Can you help?)
*   **Він не може працювати.** (He cannot work.)

In sharp contrast, the verb **мусити** (must, to have to) expresses a strong, unavoidable obligation. This verb operates as a regular Group II verb with only one minor, yet critical exception: the consonant **с** shifts to **ш** strictly in the first-person singular ("I" form). The rest of the conjugation paradigm follows the standard Group II pattern flawlessly. While **хотіти** focuses entirely on personal choice, **мусити** equals pure obligation. It is much stronger than **треба** (need to), which functions as a simpler, impersonal alternative that you will use later.

*   **я мушу** (I must)
*   **ти мусиш** (you must)
*   **він/вона мусить** (he/she must)
*   **ми мусимо** (we must)
*   **ви мусите** (you must - formal/plural)
*   **вони мусять** (they must)

*   **Я мушу працювати.** (I must work.)
*   **Ти мусиш вчити слова.** (You must learn the words.)

These three distinct modal verbs form the logical linguistic foundation for negotiating any daily situation. You can combine them to easily explain complex circumstances, weighing your internal desires against your actual abilities and your pressing duties. Observe how beautifully they work together in a single context: **я хочу гуляти** (I possess the internal desire to walk), **але не можу** (but I lack the physical possibility or ability to do so) — **я мушу працювати** (because I hold the strict necessity to work).

:::tip
For a slightly softer or more impersonal way to say "it is necessary" or "I need to," Ukrainians frequently use the single word **треба** (need to). It does not conjugate at all for different grammatical persons, making it very beginner-friendly for rapidly expressing everyday needs.
:::

*   **Я хочу читати книгу.** (I want to read a book.)
*   **Але я не можу читати.** (But I cannot read.)
*   **Я мушу спати.** (I must sleep.)

<!-- INJECT_ACTIVITY: quiz-modal-choice -->
<!-- INJECT_ACTIVITY: fill-in-modal-logic -->

## Підсумок — Summary

You have now successfully built the grammatical foundation necessary for expressing complex thoughts using the Compound Verbal Predicate structure. By seamlessly combining a conjugated modal verb with any infinitive action, you instantly multiply the variety of sentences you can independently create. Always remember the critical consonant shifts that define the two major irregular verbs: the root of **хотіти** completely trades its **т** for a **ч** across the entire paradigm, while the root of **могти** shifts its **г** to a **ж**, returning to the **г** only in the "they" form (**вони можуть**). You also learned that the verb of strict obligation, **мусити**, remains entirely regular for Group II, except for the **с** shifting to **ш** exclusively in the specific **я мушу** form.

From a strictly practical standpoint, it is incredibly important to remember the core equations of these modals: **Хочу** + infinitive expresses desire (I want to). **Можу** + infinitive expresses ability (I can). **Мушу** + infinitive expresses obligation (I must). Furthermore, **хотіти** is by far the most versatile of the three verbs discussed. It stands as the only modal verb that frequently pairs directly with a noun object to express a direct physical desire, such as **я хочу каву** (I want coffee). On the other hand, both **могти** and **мусити** almost always demand an accompanying infinitive action to make logical sense, such as **я можу працювати** (I can work). To effectively negate any of these statements, you simply place the negative particle **не** immediately before the conjugated modal verb: **я не хочу** (I do not want), **ми не можемо** (we cannot).

As a final self-check to conclude this topic, actively try to answer the following questions out loud to verify your absolute understanding of these core modal concepts:
*   Can you say exactly what you want to do right now using a full, grammatically correct sentence? (For example, **Я хочу пити чай**).
*   Can you list three distinct things you can confidently do in Ukrainian, focusing heavily on your current abilities? (For example, **Я можу читати**, **я можу говорити українською**).
*   Can you express a mandatory duty you have scheduled for tomorrow? (For example, **Я мушу працювати**).
*   Can you quickly conjugate the irregular verb **хотіти** for all grammatical persons out loud from memory, entirely without checking the reference table provided earlier in the module?

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: i-want-i-can
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

**Level: A1.2-A1.3 (Module 18/55) — EARLY BEGINNER**

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
