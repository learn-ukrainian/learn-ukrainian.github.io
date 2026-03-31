<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/linking-ideas.yaml` file for module **44: Linking Ideas** (a1).

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

- `<!-- INJECT_ACTIVITY: group-sort-conjunctions -->`
- `<!-- INJECT_ACTIVITY: fill-in-choose-conjunction -->`
- `<!-- INJECT_ACTIVITY: fill-in-bo-tomu-shcho -->`
- `<!-- INJECT_ACTIVITY: quiz-which-conjunction -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Choose: і, а, але, бо — Я хочу ___ не можу. Він працює, ___ вона відпочиває.'
  items: 10
  type: fill-in
- focus: Which conjunction? Я не йду, ___ хворий. (і / а / бо)
  items: 8
  type: quiz
- focus: 'Connect with бо/тому що: Я вчу українську, ___.'
  items: 6
  type: fill-in
- focus: 'Sort: і/та (addition) vs а/але (contrast) vs бо/тому що (reason)'
  items: 10
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- чому (why)
- тому (therefore/that's why)
- також (also)
- теж (also — colloquial)
- або (or)
- чи (or — in questions)
required:
- і (and)
- та (and — synonym of і)
- а (and/but — contrast)
- але (but)
- бо (because)
- тому що (because — longer form)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Two friends are meeting after work. Listen to how they connect their thoughts — not with pauses or separate sentences, but with small linking words that make Ukrainian flow naturally.

> **Оля:** Привіт, Марку! Ти хочеш каву чи чай? *(Hi, Marko! Do you want coffee or tea?)*
> **Марко:** Каву, бо я дуже втомлений. *(Coffee, because I'm very tired.)*
> **Оля:** А я хочу чай, але без цукру. *(And I want tea, but without sugar.)*
> **Марко:** Ходімо в кафе, і я візьму ще тістечко. *(Let's go to a café, and I'll get a pastry too.)*
> **Оля:** Я теж хочу, але я на дієті! *(I want one too, but I'm on a diet!)*
> **Марко:** Добре, але тільки одне! *(Okay, but just one!)*

Notice the four words doing all the heavy lifting here: **і** (and), **а** (and/but — a shift), **але** (but), **бо** (because). Each one connects thoughts in a different way.

Now an evening text exchange. Данило and Соня are catching up about their day.

> **Данило:** Я працював, а потім ходив у магазин. *(I worked, and then went to the store.)*
> **Соня:** Я хотів зателефонувати, але ти не відповів. *(I wanted to call, but you didn't answer.)*
> **Данило:** Вибач, бо телефон був без звуку. *(Sorry, because my phone was on silent.)*
> **Соня:** Нічого! *(No problem!)*
> **Данило:** Завтра я вільний, і ми можемо зустрітися. *(Tomorrow I'm free, and we can meet up.)*

**Бо** explains a reason. **А** and **але** show contrast. **І** adds information. All four are natural, everyday Ukrainian — you'll hear them in every conversation.

<!-- INJECT_ACTIVITY: group-sort-conjunctions -->

These four **сполучники** (conjunctions) are among the most common words in Ukrainian. Let's look at each one in detail.

## Сполучники (Conjunctions)

The Ukrainian word **сполучник** (conjunction) comes from **сполучити** — to connect, to link. That's exactly what conjunctions do: they connect words, phrases, or whole sentences. Without them, your Ukrainian sounds choppy and disconnected. Compare:

- *Я люблю каву. Я люблю чай.* — two short, separate thoughts
- **Я люблю каву і чай.** — one natural sentence

Or:

- *Я хочу піти. Я втомлений.* — disconnected
- **Я хочу піти, бо я втомлений.** — a connected thought with a reason

One conjunction replaces an entire sentence. That's efficient.

### І / Та — "and" (addition)

**Та** is a full synonym of **і** — same meaning, same grammar. **Та** appears more in writing and literary style, while **і** dominates in speech. Both are correct everywhere: **мама і тато**, **хліб та масло**. Four examples:

- **Я читаю і пишу.** *(I read and write.)*
- **Він грає на гітарі та співає.** *(He plays guitar and sings.)*
- **Київ і Львів — красиві міста.** *(Kyiv and Lviv are beautiful cities.)*
- **Ми купили хліб та молоко.** *(We bought bread and milk.)*

The pattern: **і** and **та** join equal, compatible things — two actions, two objects, two places.

### А — "and" with a contrast or shift

**А** doesn't mean "but" exactly — it shifts focus or contrasts two different subjects. Think of it as "and meanwhile" or "and on the other hand":

- **Я люблю каву, а ти?** *(I like coffee, and you?)*
- **Він працює, а вона відпочиває.** *(He works, and she rests.)*
- **Я читаю, а він дивиться телевізор.** *(I'm reading, and he's watching TV.)*

How is **а** different from **але**? **А** is a smooth pivot between two subjects or actions. **Але** is a real contradiction — one part limits or opposes the other. Think: **а** = "and meanwhile," **але** = "but actually."

### Але — "but" (stronger contrast)

When one part contradicts or limits the other, use **але**:

- **Я хочу, але не можу.** *(I want to, but I can't.)*
- **Він молодий, але дуже розумний.** *(He's young, but very smart.)*
- **Погода гарна, але холодно.** *(The weather is nice, but it's cold.)*

Comma rule: **always put a comma before але.** The same applies before **а** when it connects two full clauses with different subjects.

<!-- INJECT_ACTIVITY: fill-in-choose-conjunction -->

Quick recap: **і/та** = addition. **А** = soft contrast or subject switch. **Але** = strong contrast or limitation.

## Бо і тому що (Because)

Ukrainian has two ways to say "because": **бо** (short, conversational) and **тому що** (longer, common in writing). Both are fully correct Standard Ukrainian. **Бо** is not slang, not informal, not wrong — it appears in proverbs, literature, and everyday speech. It's simply the natural spoken form. Compare:

- **Я не йду, бо я хворий.** *(I'm not going, because I'm sick.)*
- **Я не йду, тому що я хворий.** *(I'm not going, because I'm sick.)*

The meaning is identical. The only difference is register: **бо** sounds more conversational, **тому що** more formal or written.

### Comma rule

Always put a comma before both **бо** and **тому що**. The reason clause always comes second:

- **Я втомлений, бо багато працював.** *(I'm tired, because I worked a lot.)*
- **Ми не гуляємо, бо йде дощ.** *(We're not going for a walk, because it's raining.)*
- **Він не прийшов, бо забув.** *(He didn't come, because he forgot.)*

With **тому що**:

- **Ми не гуляємо, тому що йде дощ.** *(We're not going for a walk, because it's raining.)*
- **Я вчу українську, тому що люблю Україну.** *(I'm learning Ukrainian, because I love Ukraine.)*
- **Він не прийшов, тому що забув.** *(He didn't come, because he forgot.)*

### Чому? → Бо / Тому що…

The question **Чому?** (Why?) gets answered with **бо** or **тому що**. This is how Ukrainians explain things in everyday speech:

- **— Чому ти вчиш українську?** — *Бо я люблю Україну.*
- **— Чому ти не їси?** — *Тому що я не голодний.*
- **— Чому ви тут?** — *Бо ми чекаємо друга.*
- **— Чому ти не спиш?** — *Бо я читаю цікаву книжку.*
- **— Чому він не прийшов?** — *Тому що він хворий.*

**Чому?** always gets **бо** or **тому що** as the answer opener.

<!-- INJECT_ACTIVITY: fill-in-bo-tomu-shcho -->

Now let's see all five conjunctions working together. A couple is debating their vacation — **Карпати** (the Carpathians) or **море** (the sea):

> **Олег:** Гори гарні, але далеко. *(The mountains are beautiful, but far away.)*
> **Ліна:** Море тепле, бо літо. *(The sea is warm, because it's summer.)*
> **Олег:** Я хочу в гори, а ти — на море. *(I want the mountains, and you — the sea.)*
> **Ліна:** Поїдемо в Карпати, бо там дешевше. *(Let's go to the Carpathians, because it's cheaper there.)*

Four lines, four conjunctions: **але**, **бо**, **а**, **бо** — same words you already know, different functions, natural flow.

<!-- INJECT_ACTIVITY: quiz-which-conjunction -->

## Підсумок — Summary

Here are all five conjunctions in one place:

| Сполучник | Значення | Приклад |
|---|---|---|
| **і / та** | and (addition) | **Я їм хліб і п'ю воду.** |
| **а** | and (contrast/shift) | **Я читаю, а він пише.** |
| **але** | but (contradiction) | **Я хочу, але не можу.** |
| **бо** | because (spoken) | **Я не йду, бо хворий.** |
| **тому що** | because (written) | **Я не йду, тому що хворий.** |

### Comma rules — three simple guidelines

**Rule 1:** Always put a comma before **а**, **але**, **бо**, and **тому що**.

**Rule 2:** Put a comma before **і / та** only when connecting two full sentences with different subjects: **Сонце зайшло, і стало темно.** *(The sun set, and it got dark.)* — but NOT for joining two words: **хліб і масло** *(bread and butter)*.

**Rule 3:** No comma before **і / та** between two verbs with the same subject: **Я читаю і пишу.** *(I read and write.)*

### Self-check

Connect each pair with the best conjunction:

- *Я люблю каву. Я не люблю чай.* → **Я люблю каву, але не люблю чай.**
- *Він не прийшов. Він хворий.* → **Він не прийшов, бо він хворий.**
- *Я читаю. Моя сестра дивиться фільм.* → **Я читаю, а моя сестра дивиться фільм.**
- *Ми купили хліб. Ми купили молоко.* → **Ми купили хліб і молоко.**
- *Я хочу піти. Я дуже втомлений.* → **Я хочу піти, але я дуже втомлений.**

Яке слово найкраще підходить? Чому? *(Which word fits best? Why?)*

## Підсумок

You now have five linking words that transform choppy sentences into natural Ukrainian speech. **І** and **та** add things together. **А** shifts between two subjects or contrasts them gently. **Але** signals a real "but." **Бо** and **тому що** explain why — one short and spoken, the other longer and written.

The comma rules are straightforward: always before **а**, **але**, **бо**, **тому що**. Before **і** — only between two complete sentences with different subjects.

In the next module, you'll learn to add **де** (where) and **коли** (when) — so your sentences become even more precise and natural.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: linking-ideas
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

**Level: A1.4+ (Module 44/55) — BEGINNER**

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
