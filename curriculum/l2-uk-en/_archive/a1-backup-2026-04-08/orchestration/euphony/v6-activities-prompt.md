<!-- version: 1.0.0 | updated: 2026-03-27 -->
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

- `<!-- INJECT_ACTIVITY: quiz-u-or-v -->`
- `<!-- INJECT_ACTIVITY: quiz-i-or-y -->`
- `<!-- INJECT_ACTIVITY: fill-in-z-iz-zi -->`
- `<!-- INJECT_ACTIVITY: quiz-which-sounds-natural -->`

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
## Діалоги (Dialogues)

Дарина and Олексій are sitting at a kitchen table, papers spread out. Олексій wrote a short Ukrainian essay about his **город** (garden), and Дарина — who has sharper ears for how Ukrainian flows — is helping him proofread. Their goal: find spots where the sentences stumble.

> **Олексій:** Слухай. «Я живу в Львові.» *(Listen. "I live in Lviv.")*
> **Дарина:** Стоп! «В Львові» — ні. «У Львові!» *(Stop! "V Lvovi" — no. "U Lvovi!")*
> **Олексій:** Чому? *(Why?)*
> **Дарина:** «Львів» — Л, В... Важко! «У Львові» — легко. *(Lviv — L, V... Hard! "U Lvovi" — easy.)*
> **Олексій:** Добре. А «Тарас живе у Києві?» *(OK. And "Taras lives in Kyiv?")*
> **Дарина:** Так, правильно! «Живе» — голосний Е. «У Києві»... Ні, «в Києві!» *(Yes, correct! "Zhyve" — vowel E. "U Kyievi"... No, "v Kyievi!")*
> **Олексій:** Зрозумів! А далі: «Вона працює у офісі.» *(Got it! And next: "She works in the office.")*
> **Дарина:** «Працює» — голосний Є. «Офісі» — голосний О. «В офісі!» *(Pracyuye — vowel YE. Ofisi — vowel O. "V ofisi!")*

Notice what Дарина is doing: she listens to the **sounds** around the preposition. When consonants pile up — like Л and В in **Львові** — she switches to **у**. When vowels surround it — like the Е in **живе** before К in **Києві** — she uses **в**.

> **Дарина:** Далі. «Ти й Олена йдете в парк?» *(Next. "You and Olena go to the park?")*
> **Олексій:** Тут правильно? *(Is this correct?)*
> **Дарина:** Так! «Ти» — голосний И, «Олена» — голосний О. «Й» — добре. *(Yes! "Ty" — vowel Y, "Olena" — vowel O. "Y" — good.)*
> **Олексій:** А «мама й тато»? *(And "mama y tato?")*
> **Дарина:** Теж добре — голосний А, голосний А. «Й!» *(Also good — vowel A, vowel A. "Y!")*
> **Олексій:** Ось тут: «Максим й Семен.» *(Here: "Maksym y Semen.")*
> **Дарина:** Ні! «Максим» — приголосний М. «Семен» — приголосний С. «Максим і Семен!» *(No! "Maksym" — consonant M. "Semen" — consonant S. "Maksym i Semen!")*
> **Олексій:** Тепер мій есей звучить по-справжньому гарно! *(Now my essay sounds truly good!)*

Both dialogues show the same logic: Ukrainian chooses between sound variants to avoid awkward clusters. When consonants meet consonants, the language inserts a "softer" form. When vowels meet vowels, it picks a "shorter" one. Three pairs work this way: **у/в** (in, at), **і/й** (and), and **з/із/зі** (with, from). The next sections explain exactly when to use each form.

## У чи В? (У or В?)

The **чергування** (alternation) of **у** and **в** exists for one reason: to prevent consonant pileups that are hard to pronounce. Two rules cover most situations:

**Rule 1 — Use в after a vowel before a consonant:**
- живу **в** Києві — "живу" ends in vowel У, "Києві" starts with consonant К
- вона **в** парку — "вона" ends in vowel А, "парку" starts with consonant П
- працює **в** офісі — "працює" ends in vowel Є, "офісі" starts with vowel О

**Rule 2 — Use у after a consonant before a consonant:**
- Тарас **у** Львові — "Тарас" ends in consonant С, "Львові" starts with consonant Л
- Максим **у** банку — "Максим" ends in consonant М, "банку" starts with consonant Б

Think of it as a listen-and-feel test: say the sentence aloud. If consonants crash together, switch to **у**. If it flows smoothly, **в** is fine.

At the beginning of a sentence, always use **у** before a consonant: **«У мене є квітка»** ("I have a flower"), **«У саду тихо»** ("It's quiet in the garden"). The same applies after a pause or comma: **«Знаю, у чому секрет»** ("I know what the secret is"). The sentence-start position acts like a consonant boundary — there's silence before it, so **у** prevents an abrupt start.

One exception: before a vowel at the start of a sentence, use **в**: **«В Одесі тепло»** ("It's warm in Odesa"). The vowel О makes **в** easy to pronounce, even sentence-initially.

There's a special group of consonant clusters that always take **у**, regardless of what comes before: words starting with **в, ф, кв, тв, льв, хв**. These clusters already contain a **в**-like sound, so adding another **в** preposition would create a tongue-twister:

- **у** Львові — not "в Львові" (Л+В+В is brutal)
- **у** фоє — not "в фоє" (В+Ф crashes)
- **у** вагоні — not "в вагоні" (В+В doubles up)

A simple shorthand: if the next word starts with **в** or **ф** — use **у**.

<!-- INJECT_ACTIVITY: quiz-u-or-v -->

## І чи Й? З, із, чи зі?

The conjunction "and" has two forms in Ukrainian: **і** and **й**. The logic mirrors у/в:

**Use й between vowels** — it prevents a vowel-vowel hiatus:
- мама **й** тато — vowel А before, vowel А after
- вона **й** він — vowel А before, consonant В after (vowel + consonant also takes **й**)
- ти **й** Олена — vowel И before, vowel О after

**Use і between consonants** — it breaks up the consonant cluster:
- брат **і** сестра — consonant Т before, consonant С after
- Тарас **і** Максим — consonant С before, consonant М after
- Максим **і** Семен — consonant М before, consonant С after

At the start of a sentence, always **і**: **«І він прийшов»** ("And he came").

:::tip
Quick test: look at the letter before the conjunction and the letter after. Two consonants? → **і**. A vowel nearby? → **й**.
:::

The preposition "with" or "from" has three forms: **з**, **із**, and **зі**. Here's when to use each:

**З** — the default, before most words (vowels or easy consonants):
- **з** Одеси — "from Odesa" (before vowel О)
- **з** парку — "from the park" (before consonant П)
- **з** другом — "with a friend" (before consonant Д)

**Із** — between two consonant sounds, to break the cluster:
- Максим **із** Семеном — consonant М before, consonant С after
- повернувся **із** Львова — consonant С before, consonant Л after

**Зі** — before the heaviest clusters, especially starting with з, с, ш, щ:
- **зі** мною — before МН cluster
- **зі** святом — before СВ cluster ("Happy holiday!")
- **зі** школи — before ШК cluster ("from school")

Think of **зі** as a cushion — it softens the hardest consonant collisions. The rule is smaller than у/в in scope, but it appears constantly: greetings (**«Зі святом!»**), introductions (**«Я з Одеси»**), and talking about people (**«вона з братом»**). When in doubt, **з** is the default — shift to **із** or **зі** only when the consonants feel like they're crashing.

<!-- INJECT_ACTIVITY: quiz-i-or-y -->

<!-- INJECT_ACTIVITY: fill-in-z-iz-zi -->

## Підсумок — Summary

Ukrainian **милозвучність** (euphony) is not an arbitrary set of rules — it reflects how the language naturally flows. Speakers avoid consonant pileups and vowel collisions by alternating between sound variants. Three pairs do the heavy lifting:

- **у/в** — look at the surrounding sounds. Consonant + consonant? → **у**. Vowel nearby? → **в**. Before в/ф/льв clusters? → always **у**.
- **і/й** — look at the sounds before and after the conjunction. Consonants on both sides? → **і**. Vowel on either side? → **й**.
- **з/із/зі** — look at what follows. Easy consonant or vowel? → **з**. Consonant meeting consonant? → **із**. Heavy cluster with з, с, ш, щ? → **зі**.

### Self-check

Test yourself — which form is correct?

- Я живу (в / у) Києві. → **в** Києві — after vowel У, before consonant К
- Я живу (в / у) Львові. → **у** Львові — before Л+В cluster
- (В / У) мене є квіти. → **У** мене — sentence start before consonant М
- Мама (і / й) тато. → мама **й** тато — between vowels А and А
- Брат (і / й) сестра. → брат **і** сестра — after consonant Т, before consonant С
- Повернувся (з / із) Семеном. → **із** Семеном — consonant С before consonant С
- (Зі / З) святом! → **Зі** святом — before СВ cluster

Read your Ukrainian sentences aloud. Native speakers apply euphony instinctively — they don't consult tables. The goal is smooth, flowing speech, not rigid rule application. If a sentence feels like a tongue-twister, swap the variant. With practice, your ear will guide you. These alternations are one of the features that give Ukrainian its reputation as the **солов'їна мова** (nightingale language) — a language built to sing.

Next module: **Де? (Where Is It?)** — the same prepositions **у/в** and **на** return in locative constructions, telling you where things are.

<!-- INJECT_ACTIVITY: quiz-which-sounds-natural -->

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

**Level: A1.4+ (Module 28/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-sounds-letters
- **quiz** — Звук чи літера?: Distinguish звук from літера — fundamental Ukrainian phonetics distinction
  - Instruction: *Choose the correct answer*
- **match-up** — Літера → Звук: Match letters to their sound values, especially multi-sound letters (я, ю, є, ї)
  - Instruction: *Match each letter to the sound(s) it represents*
- **group-sort** — Голосні й приголосні: Sort letters/sounds into голосні (vowel) vs приголосні (consonant)
  - Instruction: *Розподіліть звуки*
- **image-to-letter** — Знайди літеру: See image, identify the Ukrainian letter it starts with

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
