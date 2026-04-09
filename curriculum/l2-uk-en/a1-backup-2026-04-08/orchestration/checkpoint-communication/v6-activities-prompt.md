<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-communication.yaml` file for module **47: Checkpoint: Communication** (a1).

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

- `<!-- INJECT_ACTIVITY: activity-1 -->`
- `<!-- INJECT_ACTIVITY: activity-2 -->`
- `<!-- INJECT_ACTIVITY: activity-3 -->`
- `<!-- INJECT_ACTIVITY: activity-4 -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Vocative + imperative: ___(Олена), ___(читати) цей текст, будь ласка!'
  items: 8
  type: fill-in
- focus: 'Choose the conjunction: Я не йду, ___ хворий. (і / а / бо / що)'
  items: 8
  type: quiz
- focus: 'Complete complex sentences: Я знаю, ___ він тут. Скажи, ___ ти прийдеш.'
  items: 6
  type: fill-in
- focus: 'Holiday match: З Різдвом! / З Великоднем! — match greeting to holiday'
  items: 8
  type: quiz


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

Welcome to the communication checkpoint. This is not a test, but a chance to look back and see how far your skills have developed. Over the last few modules, you have learned to interact actively with others. Here are five questions to check your knowledge from this phase:

1. Can I address a friend directly using the vocative case? (Like **Тарасе!** (Taras!))
2. Can I make requests and give instructions using the imperative? (Like **Принеси!** (Bring!))
3. Can I connect ideas using coordinating conjunctions? (**і** (and), **але** (but), **бо** (because))
4. Can I build complex sentences? (using **що** (that), **де** (where), **коли** (when))
5. Can I talk about holidays and greet people? (**З Різдвом!** (Merry Christmas!))

If you remember the patterns, you have the answers. For the vocative case, names change their endings: **Олена** (Olena) becomes **Олено**, **Тарас** (Taras) becomes **Тарасе**, and **Андрій** (Andriy) becomes **Андрію**. For the imperative mood, you form direct commands like **читай** / **читайте** (read) or **дай** / **дайте** (give). You connect your thoughts with **і** / **та** (and), **а** (and/but), **але** (but), and **бо** (because). You link dependent clauses with **що** (that), **де** (where), and **коли** (when), always remembering to add a comma before them. Finally, you greet people using **З** plus the instrumental case, like **З Різдвом!** (Merry Christmas!) or **З Великоднем!** (Happy Easter!).

If you can confidently tick each box, you now possess the complete A1.7 communication toolkit. You can address real people by their names, politely tell them what to do, explain why, and build longer, natural thoughts. Together, these five tools make you sound like someone who actually speaks Ukrainian, rather than someone just reading words from a phrasebook.

## Читання (Reading Practice)

Read the text below. Notice how all five A1.7 communication tools appear naturally together in one single realistic situation.

> **Олена телефонує Тарасу напередодні Різдва.** (Olena calls Taras on the eve of Christmas.) Вона радісно каже: (She happily says:) «**Тарасе**, прийди до мене, бо ми святкуємо разом! (Taras, come to me, because we are celebrating together!) І я вже маю свічки, але я не знаю, коли ти вільний. (And I already have candles, but I do not know when you are free.) Я думаю, що це буде дуже гарне свято. (I think that it will be a very beautiful holiday.) Принеси **кутю**, будь ласка!» (Bring kutia, please!)
>
> Тарас уважно слухає. (Taras listens carefully.) Він усміхається і каже: (He smiles and says:) «Привіт, **Олено**! (Hi, Olena!) Добре, принесу! (Good, I will bring it!) Скажи, де ти будеш двадцять четвертого. (Tell me where you will be on the twenty-fourth.) Ми можемо співати разом. (We can sing together.) І я маю дуже гарні **колядки**! (And I have very beautiful carols!) **З Різдвом!**» (Merry Christmas!)

Let's check your understanding. Answer these questions in a single sentence:
1. **Що просить Олена?** (What does Olena ask for?)
2. **Коли Тарас вільний?** (When is Taras free?)

<!-- INJECT_ACTIVITY: activity-1 -->

## Граматика (Grammar Summary)

Use the vocative case whenever you call someone directly.

| Називний (Nominative) | Кличний (Vocative) | English |
|---|---|---|
| **Олена** | **Олено!** | Olena! (-а → -о) |
| **мама** | **мамо!** | Mom! (-а → -о) |
| **Тарас** | **Тарасе!** | Taras! (hard consonant → -е) |
| **друг** | **друже!** | Friend! (hard consonant → -е) |
| **Андрій** | **Андрію!** | Andriy! (soft/й → -ю) |
| **учитель** | **учителю!** | Teacher! (soft/й → -ю) |

Use the imperative to give instructions or make requests. The **ти** (you, informal) form is for a friend or child, and the **ви** (you, formal/plural) form is for an adult or group. The phrase **будь ласка** (please) softens any request.

| Дієслово (Verb) | ти (informal) | ви (formal/plural) |
|---|---|---|
| **читати** (to read) | **читай!** | **читайте!** |
| **писати** (to write) | **пиши!** | **пишіть!** |
| **дати** (to give) | **дай!** | **дайте!** |
| **принести** (to bring) | **принеси!** | **принесіть!** |

Conjunctions connect your thoughts. Coordinating conjunctions link equal parts:
- **і** / **та** (and — adds)
- **а** (and/but — contrasts: **Олена йде, а Тарас залишається.** - Olena goes, but Taras stays.)
- **але** (but — contradicts: **Я хочу прийти, але я хворий.** - I want to come, but I am sick.)
- **бо** (because: **Принеси кутю, бо я не вмію варити.** - Bring kutia, because I don't know how to cook.)

Subordinating conjunctions link a dependent clause to a main clause, and always require a comma before them:
- **що** (**Я знаю, що ти тут.** - I know that you are here.)
- **де** (**Скажи, де ти.** - Tell me where you are.)
- **коли** (**Я не знаю, коли ти вільний.** - I don't know when you are free.)

<!-- INJECT_ACTIVITY: activity-2 -->

The holiday greeting formula uses **З** (with) plus a noun in the instrumental case. Just take the holiday name, put it in the instrumental (**Різдво** → **Різдвом**, **Великдень** → **Великоднем**), and add **З** before it. This formula works for every Ukrainian celebration: **З Різдвом!** (Merry Christmas!), **З Великоднем!** (Happy Easter!), **З Новим роком!** (Happy New Year!), **З днем народження!** (Happy Birthday!).

<!-- INJECT_ACTIVITY: activity-3 -->

## Діалог (Connected Dialogue)

**Організатор готує шкільний ярмарок.** (An organizer is preparing a school fair.) **Він розподіляє завдання між волонтерами.** (He distributes tasks among volunteers.)

> **Організатор:** **Олено**, принеси, будь ласка, плакати, бо стіл уже готовий. *(Olena, bring the posters, please, because the table is already ready.)*
> **Олена:** Добре, принесу! Скажи, де покласти їх. *(Good, I will bring them! Tell me where to put them.)*
> **Організатор:** Ось біля входу. **Тарасе**, постав столи, але спочатку перевір стільці. *(Here near the entrance. Taras, place the tables, but first check the chairs.)*
> **Тарас:** Я вже знаю, де вони. І я маю квитки та напої — все готово. *(I already know where they are. And I have the tickets and drinks — everything is ready.)*
> **Організатор:** Чудово! Я думаю, що ярмарок буде гарний, бо ми добре підготувалися. *(Wonderful! I think that the fair will be beautiful, because we prepared well.)*
> **Волонтери:** З ярмарком! *(Happy fair!)*

Read through the dialogue again and circle every vocative case, imperative verb, conjunction, and subordinating clause you see. You should find at least two vocatives, three imperatives, three coordinating conjunctions, and three subordinating clauses. This is exactly what natural A1.7 Ukrainian looks like in action.

<!-- INJECT_ACTIVITY: activity-4 -->

## Підсумок — Summary

You have worked hard through this checkpoint phase. Let's review the concrete communication skills you have successfully built:

- ✅ **Ти можеш звертатися до людей по імені:** (You can address people by name:) **Олено! Тарасе! Андрію!**
- ✅ **Ти можеш попросити когось щось зробити:** (You can ask someone to do something:) **Принеси! Напиши! Дайте, будь ласка!**
- ✅ **Ти можеш з'єднувати думки:** (You can connect thoughts:) **і**, **а**, **але**, **бо** — чотири різні зв'язки.
- ✅ **Ти можеш будувати складні речення:** (You can build complex sentences:) **Я знаю, що… Скажи, де… Я не знаю, коли…**
- ✅ **Ти можеш говорити про українські свята та вітати людей:** (You can talk about Ukrainian holidays and greet people:) **З Різдвом! З Великоднем!**

## Підсумок

This checkpoint concludes the communication phase of your A1 journey. You are no longer just naming objects; you are actively engaging with people, giving instructions, and linking your ideas into fluent, multi-part sentences.

👉 **Далі:** (Next:) A1.8 — минулий і майбутній час, і фінальний випускний модуль A1. (Past and future tense, and the final A1 graduation module.)

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-communication
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
```

---

## Activity Type Reference

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: instruction, items[{sentence, error, correction}]
- **anagram**: Letter rearrangement. Required: instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: instruction, items[{words[], correct_order[]}]
- **observe**: Pattern discovery. Required: examples[], prompt
- **classify**: Multi-category sort. Required: instruction, categories[{label, items[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: prompt. Optional: min_words, model_answer, evaluation_criteria[]
- **reading**: Required: passage, questions[]
- **source-evaluation**: Required: source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A1.4+ (Module 47/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: general-reading
- **true-false** — Правда чи ні?: Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Answer questions about a text passage


**Use these patterns.** If the pattern library recommends `divide-words` for a syllable module, generate a `divide-words` exercise. If it recommends `group-sort` for gender, generate a `group-sort`. The patterns encode how Ukrainian teachers actually test these concepts.

---

## Quality Rules

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Every activity MUST have at least 6 items.** Quiz = 6+ questions. Fill-in = 6+ sentences. Match-up = 6+ pairs. True-false = 6+ statements. Group-sort = 6+ items per group minimum. Anagram = 6+ words.
- If you can't think of 6 items, add more examples from the module's vocabulary and content. NEVER submit an activity with fewer than 6 items.
- **3-5 options per quiz/fill-in question** — enough to prevent guessing, not so many to overwhelm.

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
- `mcp__rag__verify_words` / `mcp__rag__verify_word` / `mcp__rag__verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp__rag__search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp__rag__search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp__rag__query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp__rag__query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp__rag__search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp__rag__query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp__rag__search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp__rag__search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp__rag__search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp__rag__search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp__rag__translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp__rag__query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp__rag__query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp__rag__query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp__rag__search_style_guide` first (it knows calques). Then `mcp__rag__query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp__rag__verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp__rag__query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp__rag__verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp__rag__search_idioms` for Ukrainian expressions, `mcp__rag__search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp__rag__query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp__rag__query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp__rag__verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp__rag__verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp__rag__verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp__rag__query_pravopys` or `mcp__rag__search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp__rag__verify_words` with 5-15 words at once.
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
