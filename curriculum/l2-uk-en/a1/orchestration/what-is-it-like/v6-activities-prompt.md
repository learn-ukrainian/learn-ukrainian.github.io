# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/what-is-it-like.yaml` file for module **9: What Is It Like?** (a1).

Output **pure YAML only** — no markdown fencing, no preamble, no explanation. Just the YAML document.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 2-3 quick checks after key teaching points. Workbook = 4-8 deeper practice exercises covering the full topic.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: quiz-yakyj-yaka-yake -->`
- `<!-- INJECT_ACTIVITY: fill-in-adj-endings -->`
- `<!-- INJECT_ACTIVITY: match-opposites -->`
- `<!-- INJECT_ACTIVITY: fill-in-describe-room -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Add correct adjective ending: нов__ книга, велик__ стіл, чист__ вікно'
  items: 10
  type: fill-in
- focus: 'Match adjective opposites: великий ↔ маленький'
  items: 6
  type: match-up
- focus: Який/яка/яке? Choose correct question word.
  items: 6
  type: quiz
- focus: Describe the room using given nouns and adjectives
  items: 6
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- поганий (bad)
- брудний (dirty)
- світлий (light, bright)
- темний (dark)
- а (and/but — contrast)
- але (but)
required:
- який, яка, яке (what kind? — m/f/n)
- великий (big)
- маленький (small)
- новий (new)
- старий (old)
- гарний (nice, beautiful)
- чистий (clean)
- дорогий (expensive)
- дешевий (cheap)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

When a friend visits your home, one of the first things you do is show them around. **Яка твоя кімната?** — "What's your room like?" This simple question opens the door to describing everything you see. The dialogue below is inspired by the "Моя кімната" task in Вашуленко Grade 3, where students describe their own space using adjectives.

> **Марко:** Яка твоя кімната? *(What is your room like?)*
> **Оленка:** Моя кімната велика і світла. *(My room is big and bright.)*
> **Марко:** А стіл? *(And the desk?)*
> **Оленка:** Стіл новий. *(The desk is new.)*
> **Марко:** А ліжко? *(And the bed?)*
> **Оленка:** Ліжко старе. *(The bed is old.)*
> **Марко:** А вікно? *(And the window?)*
> **Оленка:** Вікно велике і чисте. *(The window is big and clean.)*

Notice what happened in Оленка's answers. When she described **кімната** (room) — a feminine noun — she said **велика** and **світла**, with the ending **-а**. When she described **стіл** (desk) — a masculine noun — she said **новий**, ending in **-ий**. And **ліжко** (bed) — a neuter noun — got **старе**, ending in **-е**. The adjective ending changed each time, matching the noun's gender. This is adjective agreement, and it's the core pattern of this module.

Now a different situation. Two friends are walking past a shop window, reacting to what they see.

> **Андрій:** Дивись, яка гарна сумка! *(Look, what a nice bag!)*
> **Софія:** Так, але вона дорога. *(Yes, but it's expensive.)*
> **Андрій:** А цей телефон? *(And this phone?)*
> **Софія:** Він великий і дешевий. *(It's big and cheap.)*
> **Андрій:** Яке велике вікно! *(What a big window!)*
> **Софія:** Так, і чисте! *(Yes, and clean!)*

Here again, the adjective shape-shifts. **Сумка** (bag) is feminine, so Андрій exclaimed **яка гарна** — both the question word and the adjective carry feminine endings. **Телефон** (phone) is masculine: **великий і дешевий**. **Вікно** (window) is neuter: **яке велике**. Also notice the word **але** (but) — Софія uses it to signal a contrast: the bag is nice, *but* expensive.

Across both dialogues, one pattern repeats: the adjective mirrors the noun's gender. Masculine nouns get **-ий** adjectives, feminine nouns get **-а**, neuter nouns get **-е**. Can you predict what form an adjective takes just by knowing the noun's gender? That is exactly what the next section explains.

## Який? Яка? Яке? (What kind?)

To ask "What kind?" in Ukrainian, you use **який** (what kind? — masculine), **яка** (what kind? — feminine), or **яке** (what kind? — neuter). The question word changes gender to match the noun you're asking about — the same logic as **мій/моя/моє** from Module 8. Here are three question-and-answer pairs:

- **Який стіл?** — **Великий стіл.** *(What kind of desk? — A big desk.)*
- **Яка книга?** — **Нова книга.** *(What kind of book? — A new book.)*
- **Яке вікно?** — **Чисте вікно.** *(What kind of window? — A clean window.)*

Both the question word *and* the adjective in the answer change to reflect the noun's gender. The question word and the adjective move together as a team.

Ukrainian textbooks state this rule clearly. Пономарова Grade 3 (p. 98) puts it simply: "Прикметник має такий рід, як іменник" — the adjective has the same gender as the noun it is connected to. Here are the endings:

| Gender | Question word | Adjective ending | Examples |
|---|---|---|---|
| Masculine | **який?** | **-ий** | великий, новий, чистий |
| Feminine | **яка?** | **-а** | велика, нова, чиста |
| Neuter | **яке?** | **-е** | велике, нове, чисте |

:::tip
Soft-stem adjectives like **синій/синя/синє** (blue) follow a slightly different pattern — **-ій/-я/-є** instead of **-ий/-а/-е**. You'll meet those in M10 (Colors). For now, focus on the hard-stem **-ий/-а/-е** pattern.
:::

<!-- INJECT_ACTIVITY: quiz-yakyj-yaka-yake -->

Why does the ending change? Because the adjective "agrees" with its noun — think of the adjective as a mirror that reflects the noun's gender. Walk through it step by step:

- **Книга** is feminine → the question is **яка?** → the adjective takes **-а**: **нова книга**.
- **Стіл** is masculine → the question is **який?** → the adjective takes **-ий**: **новий стіл**.
- **Вікно** is neuter → the question is **яке?** → the adjective takes **-е**: **нове вікно**.

You already learned noun genders in Module 8. Now that knowledge becomes practical — every time you describe a noun, you choose the adjective ending based on its gender. One pattern, used constantly.

<!-- INJECT_ACTIVITY: fill-in-adj-endings -->

One more thing to keep in mind: Ukrainian also has a plural question form — **які?** (what kind? — plural). When a noun is plural, all genders collapse into one ending: **-і**.

- **Які стільці?** — **Нові стільці.** *(What kind of chairs? — New chairs.)*
- **Які книги?** — **Нові книги.** *(What kind of books? — New books.)*
- **Які вікна?** — **Нові вікна.** *(What kind of windows? — New windows.)*

No need to drill plurals now — just notice that **-і** works for all genders in the plural. And **який** can also express surprise or admiration in exclamations: **Яка гарна кімната!** means "What a beautiful room!" — you already saw this in Андрій's reaction at the shop window.

## Прикметники (Common Adjectives)

Ukrainian textbooks teach adjectives in opposite pairs — Grade 2 textbooks call them "слова із протилежним значенням" (words with opposite meaning). Opposites are easier to remember because each word gives context to the other. Here are six essential pairs. For the first pair, all three gender forms are shown as a model:

- **великий / велика / велике** (big) ↔ **маленький / маленька / маленьке** (small)
- **новий** (new) ↔ **старий** (old)
- **гарний** (nice, beautiful) ↔ **поганий** (bad)
- **чистий** (clean) ↔ **брудний** (dirty)
- **дорогий** (expensive) ↔ **дешевий** (cheap)
- **світлий** (light, bright) ↔ **темний** (dark)

For the remaining five pairs, only the masculine form is listed. You can already predict the feminine and neuter: **новий → нова → нове**, **старий → стара → старе**, and so on. The **-ий/-а/-е** pattern works the same way for every adjective.

<!-- INJECT_ACTIVITY: match-opposites -->

Now combine these adjectives with the nouns you learned in Module 8. Possessives, nouns, and adjectives all work together:

- **У мене є великий стіл.** *(I have a big desk.)*
- **Моя кімната маленька, але гарна.** *(My room is small but nice.)*
- **Вікно велике і чисте.** *(The window is big and clean.)*
- **Стілець старий, а ліжко — нове.** *(The chair is old, and the bed is new.)*

Two small words do important work here. **І** (and) joins things that go together: **велике і чисте** — the window is big *and* clean, two parallel qualities. **А** (and/but) signals a contrast: **стілець старий, а ліжко — нове** — the chair is old, *but* the bed is new. Both translate as "and" in English, but they serve different functions in Ukrainian.

Here is a full room description using everything from this module. Read it and try to identify each adjective's gender agreement:

- **Моя кімната невелика, але світла.** *(My room is not big, but bright.)*
- **У мене є новий стіл і старий стілець.** *(I have a new desk and an old chair.)*
- **Ліжко велике і зручне.** *(The bed is big and comfortable.)*
- **Вікно чисте.** *(The window is clean.)*
- **Шафа маленька, а тумбочка — нова.** *(The wardrobe is small, and the nightstand is new.)*

Count the adjectives: **невелика** (f), **світла** (f), **новий** (m), **старий** (m), **велике** (n), **зручне** (n), **чисте** (n), **маленька** (f), **нова** (f). Nine adjectives, each one matching its noun's gender perfectly. This is the pattern in action.

<!-- INJECT_ACTIVITY: fill-in-describe-room -->

:::caution
Two common mistakes to avoid. First, forgetting to change the ending: *«велика стіл»* is wrong because **стіл** is masculine — the correct form is **великий стіл**. Always check the noun's gender before choosing the adjective ending. Second, mixing up **а** and **але**. Both can mean "but," yet **а** is a lighter contrast within a list (**Стіл новий, а стілець старий**), while **але** marks a stronger, unexpected contrast (**Кімната маленька, але гарна** — small, *yet* nice).
:::

## Підсумок — Summary

Three patterns to take away from this module:

**Adjective endings** match the noun's gender. Masculine: **-ий** (великий, новий, чистий). Feminine: **-а** (велика, нова, чиста). Neuter: **-е** (велике, нове, чисте). Test yourself: What ending does a masculine adjective have? What about feminine? Neuter? If you answered **-ий**, **-а**, **-е** — you have it.

**Question words** follow the same pattern: **який** (m), **яка** (f), **яке** (n). The question word agrees with the noun just like the adjective does.

**Contrast words**: **і** joins parallel qualities (**велике і чисте**), **а** contrasts (**стілець старий, а ліжко нове**), and **але** marks stronger opposition (**маленька, але гарна**).

| Question | Ending | Example |
|---|---|---|
| **який?** | **-ий** | великий стіл |
| **яка?** | **-а** | нова книга |
| **яке?** | **-е** | чисте вікно |

Now put it all together. Describe your own room in 3–5 sentences using adjectives from this module. Here is a frame to get you started:

- **Моя кімната _____ і _____.** *(My room is _____ and _____.)*
- **У мене є _____ стіл.** *(I have a _____ desk.)*
- **Вікно _____.** *(The window is _____.)*

Try to use different adjective pairs — not just **великий** everywhere. Mix opposites: **великий стіл, маленька шафа, чисте вікно**. Vary the genders so you practice all three endings.

In Module 10 (Colors), you will meet soft-stem adjectives like **синій/синя/синє** (blue) — a small twist on today's pattern, where **-ій/-я/-є** replace **-ий/-а/-е**. You will also start combining colors with the adjectives you learned today: **великий червоний стіл** (a big red desk), **маленька синя сумка** (a small blue bag). For now, practice the **-ий/-а/-е** pattern until choosing the right ending feels automatic. The gender system you built in Module 8 is now a working tool — and every future module will build on it.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: what-is-it-like
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

**Level: A1.2-A1.3 (Module 9/55) — EARLY BEGINNER**

The learner knows the alphabet and ~200 words. They:
- Can read Ukrainian slowly
- Know basic nouns, adjectives, simple verb forms
- Cannot handle complex sentences or grammar terminology in Ukrainian

**Instructions in simple English with Ukrainian key terms in bold.**
Example: 'Choose the correct form of **мій/моя/моє**'

**Good activity types:** quiz, fill-in (simple sentences), match-up, group-sort, true-false, observe, anagram, translate (English→Ukrainian).


## Quality Rules

1. **Instructions match learner level:**
   - **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
   - **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
   - **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
   - **A2+:** Instructions in Ukrainian.
   - **B1+:** Full Ukrainian, no English.
2. **3-5 options per quiz/fill-in** — enough to prevent guessing, not so many to overwhelm
3. **No duplicate options** — each option in a quiz item must be unique
4. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
5. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
6. **Min 3 pairs for match-up** — to prevent trivial elimination
7. **Explanations for true-false and error-correction** — help the learner understand WHY
8. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

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

**Efficiency Rules:**
- **Batch your checks:** Use `mcp__rag__verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 8-15 tool calls per module**, not 50.

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
