<!-- version: 1.0.0 | updated: 2026-03-27 -->
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

- `<!-- INJECT_ACTIVITY: group-sort-verb-groups -->`
- `<!-- INJECT_ACTIVITY: quiz-mixed-conjugation -->`
- `<!-- INJECT_ACTIVITY: fill-in-dialogue-completion -->`
- `<!-- INJECT_ACTIVITY: fill-in-describe-your-day -->`

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

You have been learning Ukrainian verbs for six modules now — from saying what you like, through conjugating two verb groups, to describing your entire morning. **Я читаю** (I read), **він хоче спати** (he wants to sleep), **вона прокидається** (she wakes up) — these are all patterns you have practiced. Before moving to the next phase, take a moment to check what you remember. This is not a test. It is a mirror: look at each skill below and honestly mark whether you feel confident.

Ask yourself these six questions:

- **(M15) Can you say what you like?** Try it now: **Я люблю каву** (I love coffee). **Мені подобається музика** (I like music). If these feel natural, you are ready.
- **(M16) Can you conjugate Group I verbs?** Say aloud: **я читаю** (I read), **ти читаєш** (you read), **він читає** (he reads). Do the endings come easily?
- **(M17) Can you conjugate Group II verbs?** Try: **я говорю** (I speak), **ти говориш** (you speak), **він говорить** (he speaks). These endings are different — do you remember why?
- **(M18) Can you use modal verbs?** Build a sentence: **Я хочу їсти** (I want to eat). **Вона може допомогти** (She can help). **Він мусить працювати** (He must work). Modal + infinitive — always.
- **(M19) Can you ask all seven question words?** List them: **Хто? Що? Де? Куди? Коли? Чому? Як?** (Who? What? Where? Where to? When? Why? How?)
- **(M20) Can you describe your morning?** Say: **Я прокидаюся, вмиваюся, снідаю** (I wake up, wash up, eat breakfast). Reflexive verbs and sequence — your daily routine in Ukrainian.

If most of these feel solid, you are in great shape. If some feel shaky, pay extra attention to those patterns as we review them below.

## Читання (Reading Practice)

Every word in the following text comes from modules M15–M20. Nothing is new. Read it aloud — focus on smooth pronunciation and recognizing the grammar patterns you have learned.

**Тарас розповідає про свій день:**

> Мене звати Тарас. Я прокидаюся о сьомій годині. Спочатку вмиваюся і чищу зуби. Потім снідаю — я люблю каву і бутерброди. Я працюю в офісі. Моя робота починається о дев'ятій. Я можу читати документи і відповідати на листи. Увечері я хочу відпочивати. Я слухаю музику або дивлюся фільм. Я мушу лягати спати о десятій — завтра знову рано вставати.

Here is what Taras said: His name is Taras. He wakes up at seven. First he washes up and brushes his teeth. Then he eats breakfast — he loves coffee and sandwiches. He works in an office. His work starts at nine. He can read documents and reply to letters. In the evening he wants to rest. He listens to music or watches a film. He must go to sleep at ten — tomorrow he has to get up early again.

Now think about these questions — answer them aloud or in your head:

- **Що Тарас робить вранці?** (What does Taras do in the morning?) Look back at the text: **прокидаюся, вмиваюся, чищу зуби, снідаю** — four actions in sequence.
- **О котрій він починає працювати?** (What time does he start work?) The text says **о дев'ятій** (at nine) — an ordinal time expression you saw in M20.
- **Що він хоче робити увечері?** (What does he want to do in the evening?) **Хоче відпочивати** — modal **хочу** + infinitive **відпочивати**, exactly the pattern from M18.

Notice how many grammar patterns appear naturally in this short text: reflexive verbs (**прокидаюся, вмиваюся**), Group I verbs (**читаю, слухаю**), Group II (**починається**), modals (**можу, хочу, мушу**), and sequence words (**спочатку, потім, увечері**). Everything connects.

<!-- INJECT_ACTIVITY: group-sort-verb-groups -->

## Граматика (Grammar Summary)

Ukrainian verbs change form depending on who performs the action. Two main conjugation patterns — **дієвідміна** (conjugation group) — cover nearly every verb you know. Modal verbs always pair with an infinitive ending in **-ти**. Reflexive verbs add **-ся** to show the action returns to the doer. And seven question words let you ask about anything.

Here are the two conjugation groups side by side:

| | **І дієвідміна (Group I)** — читати | **ІІ дієвідміна (Group II)** — говорити |
|---|---|---|
| я | читаю | говорю |
| ти | читаєш | говориш |
| він/вона | читає | говорить |
| ми | читаємо | говоримо |
| ви | читаєте | говорите |
| вони | читають | говорять |

The quickest way to tell them apart: look at the **вони** form. Group I ends in **-ють** (читають), Group II ends in **-ять** (говорять). When you hear a new verb, check its third-person plural — that tells you the group.

:::tip
**Хотіти** (to want) belongs to Group I, even though it ends in **-іти**. Its forms are: **хочу, хочеш, хоче, хочемо, хочете, хочуть**. The **-уть** ending confirms it.
:::

Modal verbs — **хотіти** (to want), **могти** (to be able), **мусити** (to have to) — always connect to an infinitive with **-ти**:

- **Я хочу читати** (I want to read)
- **Ти можеш говорити** (You can speak)
- **Він мусить працювати** (He must work)
- **Я не хочу спати** (I don't want to sleep) — negation is simply **не** before the modal

Reflexive verbs add **-ся** after the personal ending. The **-ся** means the action is directed back at the person doing it:

- **прокидаюся** (I wake up — I wake myself)
- **вмиваюся** (I wash up — I wash myself)
- **одягаюся** (I get dressed — I dress myself)
- **називаюся** (I am called — I call myself)

The pattern is always: conjugated verb + **ся** appended directly to the ending.

<!-- INJECT_ACTIVITY: quiz-mixed-conjugation -->

## Діалог (Connected Dialogue)

Оля meets Максим in the park on a Saturday morning. This conversation uses ALL the A1.3 skills together — both verb groups, modals, questions, negation, reflexives, and sequence words. Read it aloud, taking both roles.

> **Оля:** Привіт, Максиме! Що ти тут робиш? *(Hi, Maksyme! What are you doing here?)*
> **Максим:** Привіт, Олю! Я гуляю. А ти? *(Hi, Olyu! I'm walking. And you?)*
> **Оля:** Я теж хочу гуляти. Можна разом? *(I also want to walk. Can we go together?)*
> **Максим:** Звичайно! Ти часто тут гуляєш? *(Of course! Do you walk here often?)*
> **Оля:** Так, зазвичай вранці. Я прокидаюся рано. *(Yes, usually in the morning. I wake up early.)*
> **Максим:** А я мушу вставати рано через роботу. *(And I have to get up early because of work.)*
> **Оля:** Де ти працюєш? *(Where do you work?)*
> **Максим:** Я працюю в лікарні. Я лікар. А ти? *(I work in a hospital. I'm a doctor. And you?)*
> **Оля:** Я вчитель. Я викладаю математику. *(I'm a teacher. I teach math.)*
> **Максим:** Цікаво! Тобі подобається робота? *(Interesting! Do you like your job?)*
> **Оля:** Так, дуже! Я люблю говорити з дітьми. *(Yes, very much! I love talking with children.)*
> **Максим:** А що ти робиш вранці? *(And what do you do in the morning?)*
> **Оля:** Я прокидаюся о шостій, вмиваюся, снідаю. Потім їду на роботу. *(I wake up at six, wash up, eat breakfast. Then I go to work.)*
> **Максим:** Коли ти починаєш? *(When do you start?)*
> **Оля:** О восьмій. Мушу бути там вчасно! *(At eight. I must be there on time!)*
> **Максим:** А що ти робиш увечері? *(And what do you do in the evening?)*
> **Оля:** Увечері я хочу відпочивати. Я читаю або слухаю музику. А ти? *(In the evening I want to rest. I read or listen to music. And you?)*
> **Максим:** Я теж люблю читати! *(I also love to read!)*

Both verb groups appear naturally here. Group I: **гуляю, люблю, читаю, слухаю, працюю, починаю, викладаю**. Group II: **говорю**. Modals always attach to an infinitive: **мушу бути, мушу вставати, хочу гуляти, хочу відпочивати**. Question words drive the conversation: **що** (what), **де** (where), **коли** (when). And reflexive verbs anchor the morning routine: **прокидаюся, вмиваюся**.

<!-- INJECT_ACTIVITY: fill-in-dialogue-completion -->

## Підсумок — Summary

You have completed A1.3: Actions. This is a major milestone. You can now do six things in Ukrainian that are core to any conversation: describe actions, express wants and obligations, ask questions, use reflexive verbs, build a daily routine, and combine all of these in connected speech.

Here is everything you can do, with examples:

- **Дієслова І групи** (Group I verbs) — **Я читаю книгу** (I read a book). **Вони слухають музику** (They listen to music).
- **Дієслова ІІ групи** (Group II verbs) — **Ти говориш добре** (You speak well). **Вона вчить українську** (She studies Ukrainian).
- **Модальні дієслова** (Modal verbs) — **Я хочу спати** (I want to sleep). **Він може допомогти** (He can help). **Ми мусимо працювати** (We must work).
- **Питальні слова** (Question words) — **Хто це?** (Who is this?) **Що ти робиш?** (What are you doing?) **Де ти живеш?** (Where do you live?) **Куди ти йдеш?** (Where are you going?) **Коли починається?** (When does it start?) **Чому ти мовчиш?** (Why are you silent?) **Як ти себе почуваєш?** (How do you feel?)
- **Заперечення** (Negation) — **Я не хочу їсти** (I don't want to eat). **Ніхто не знає** (Nobody knows) — double negation is standard in Ukrainian.
- **Зворотні дієслова** (Reflexive verbs) — **Я прокидаюся, вмиваюся, одягаюся** (I wake up, wash up, get dressed).

<!-- INJECT_ACTIVITY: fill-in-describe-your-day -->

## Підсумок

In **A1.4 — Time and Nature**, you will learn to say what time it is — **Котра година?** (What time is it?) — name the days of the week and months, talk about the weather, and describe the seasons. These topics build directly on your verb skills. You already know how to conjugate, how to ask questions, and how to describe your routine. Now you will add time, days, and nature to your Ukrainian world.

A taste of what is coming: **Зараз третя година** (It's three o'clock now). **Сьогодні неділя** (Today is Sunday). **Надворі холодно** (It's cold outside). **Восени я люблю гуляти в парку** (In autumn I love to walk in the park). Your verbs are ready — the next phase gives them a time and place.

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

**Level: A1.2-A1.3 (Module 21/55) — EARLY BEGINNER**

The learner knows the alphabet and ~200 words. They:
- Can read Ukrainian slowly
- Know basic nouns, adjectives, simple verb forms
- Cannot handle complex sentences or grammar terminology in Ukrainian

**Instructions in simple English with Ukrainian key terms in bold.**
Example: 'Choose the correct form of **мій/моя/моє**'

**Good activity types:** quiz, fill-in (simple sentences), match-up, group-sort, true-false, observe, anagram, translate (English→Ukrainian).


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-verbs-present
- **fill-in** — Відмінюй дієслово: Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Find incorrectly conjugated verb and fix it

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
