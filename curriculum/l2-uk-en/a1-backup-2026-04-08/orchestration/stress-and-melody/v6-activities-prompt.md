<!-- version: 1.0.0 | updated: 2026-03-27 -->
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

- `<!-- INJECT_ACTIVITY: quiz-stress-syllable -->`
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

Say the word **наголос** (stress) out loud. One of its three syllables — на, го, лос — comes out louder and longer than the others. That louder syllable is the **наголошений склад** (stressed syllable). Every Ukrainian word with more than one syllable has one — and only one — stressed syllable. Here is the crucial fact: Ukrainian **наголос** is free. It can land on the first syllable, the middle, or the last. **Мама** (mother) — stress on the first syllable. **Молоко** (milk) — stress on the last. **Фотографія** (photograph) — stress on the third syllable, the second а. French locks stress to the final syllable. Czech locks it to the first. Ukrainian gives no such shortcut. You must learn each word's stress individually.

Stress does more than shape how a word sounds — it changes what the word means. Consider three real pairs you will encounter as a learner. **Замок** with stress on the first syllable means "castle." **Замок** with stress on the second syllable means "lock." Same five letters, entirely different objects. **Мука** with stress on the first syllable means "torment" or "suffering." **Мука** with stress on the last syllable means "flour." **Атлас** with stress on the first syllable is a collection of maps — an atlas. **Атлас** with stress on the second syllable is satin fabric. There is a classic Ukrainian riddle from a Grade 2 textbook by Білоус that captures this perfectly: "This word is an ancient building with sharp masonry towers. Change the stress — and you lock the building shut." Wrong stress does not just sound foreign — it says the wrong word entirely. This is why stress marks matter.

In textbooks, dictionaries, and learning materials, stress is marked with an accent sign (´) over the vowel: **кава** has its mark over the first а. But in everyday Ukrainian text — newspapers, messages, novels for adults — you will not see stress marks at all. Ukrainians simply know where the stress falls. As a learner, make a habit: every time you write a new word in your notes, mark its stress. When you are unsure, check goroh.pp.ua — it shows the stressed syllable for over 500,000 Ukrainian words.

Here are common stress positions for A1 words. First-syllable stress: **мама** (mother), **тато** (father), **ранок** (morning), **кава** (coffee), **книга** (book). Last-syllable stress: **вода** (water), **зима** (winter), **метро** (metro), **кафе** (café). These are clusters, not rules — Ukrainian has exceptions in every pattern. Build the habit now: when you learn a new word, write it with its stress mark immediately. A notebook entry looks like this: **вода** — water — stress on the last syllable. Do not trust your memory on stress. Write it down.

<!-- INJECT_ACTIVITY: quiz-stress-syllable -->

<!-- INJECT_ACTIVITY: match-stress-pairs -->

## Інтонація (Intonation)

Ukrainian speech has melody. The rise and fall of your voice — **інтонація** (intonation) — tells the listener whether you are making a statement, asking a question, or expressing emotion. Same words, different melody, entirely different meaning. Three core patterns:

**Це кава.** ↘ — your voice falls on the stressed syllable of **кава**. You are telling someone: this is coffee. A statement.

**Це кава?** ↗ — your voice rises on that same stressed syllable. You are asking for confirmation: is this coffee? A yes/no question.

**Як гарно!** ↘↘ — your voice drops sharply with extra force. You are expressing emotion: how beautiful! An exclamation.

Try it yourself. Say **Це кава** three times — once as a calm statement with a falling voice, once as a surprised question with a rising voice, once as a delighted exclamation with a strong drop. Same two words, three entirely different communicative acts.

Question words change the rule. Words like **хто** (who), **що** (what), **де** (where), **коли** (when) carry the interrogative meaning themselves — they signal "this is a question" without any rise in your voice. **Що це?** ↘ — falling intonation. The word **що** already tells the listener you are asking about identity. **Де метро?** ↘ — falling. The word **де** signals a question about location. **Коли автобус?** ↘ — falling again. But yes/no questions that lack a question word must rise: **Це метро?** ↗ / **Автобус тут?** ↗. The rule: question word present = voice falls; no question word = voice rises.

Ukrainian grammar classifies sentences by purpose into three types: **розповідні** (declarative — they tell), **питальні** (interrogative — they ask), and **спонукальні** (imperative — they command or request). Any of these three can also be **окличні** (exclamatory) — carrying high emotional charge, shown by an exclamation mark. **Окличне** is a separate dimension, not a fourth type. A command can be calm — **Іди сюди.** — or exclamatory — **Іди сюди!** For A1, focus on the practical link between punctuation and melody: period (.) = voice falls ↘, question mark (?) = check for a question word, exclamation mark (!) = extra force ↘↘.

Here is a short dialogue that models all three patterns. Two friends, **Кирилко** and **Соломійка**, are near a Kyiv metro station:

> **Кирилко:** Привіт, Соломійко! ↘ *(Hi, Solomiyka!)*
> **Соломійка:** Привіт! Це метро? ↗ *(Hi! Is this the metro?)*
> **Кирилко:** Так, це метро! ↘↘ *(Yes, this is the metro!)*
> **Соломійка:** А де вихід? ↘ *(And where is the exit?)*
> **Кирилко:** Ось він. ↘ *(Here it is.)*
> **Соломійка:** Дякую! ↘↘ *(Thanks!)*

Notice: **Це метро?** rises — yes/no question without a question word. **Де вихід?** falls — the question word **де** does the work. Exclamations like **Так, це метро!** and **Дякую!** drop sharply with force.

<!-- INJECT_ACTIVITY: quiz-sentence-type -->

<!-- INJECT_ACTIVITY: fill-in-punctuation -->

## Читаємо вголос (Reading Aloud)

Reading Ukrainian aloud — **вголос** (aloud) — is where stress and intonation come together. Here is a three-step method for reading multisyllable words correctly.

**Step 1:** Break the word into syllables. Say each syllable slowly, separately.
**Step 2:** Find the stressed syllable — say it louder and slightly longer than the others.
**Step 3:** Read the whole word at natural speed, letting the stress land naturally.

Apply this to three longer words:

- **у-кра-їн-ська** (Ukrainian) — stress on **ї**. Slow: у... кра... їн... ська. Now together: **українська**.
- **фо-то-гра-фі-я** (photograph) — stress on the second **а**. Slow: фо... то... гра... фі... я. Now together: **фотографія**.
- **від-по-чи-нок** (rest/vacation) — stress on **чи**. Slow: від... по... чи... нок. Now together: **відпочинок**.

Break first, find the stress, then read smoothly. This is how Ukrainian Grade 1 textbooks teach reading, and it works just as well for adult learners.

Now practice with eight words. Read each one aloud — first broken into syllables, then as a whole word:

- **Ки-їв** (Kyiv) — stress on **и**: Київ
- **мо-ло-ко** (milk) — stress on last **о**: молоко
- **ра-нок** (morning) — stress on **ра**: ранок
- **ка-ва** (coffee) — stress on first **ка**: кава
- **во-да** (water) — stress on **да**: вода
- **зи-ма** (winter) — stress on **ма**: зима
- **у-кра-їн-ська** (Ukrainian) — stress on **ї**: українська
- **бі-блі-о-те-ка** (library) — stress on **те**: бібліотека

:::tip
Tap the table once for each syllable as you read. The tap on the stressed syllable will land harder naturally — your hand knows the rhythm before your mouth does.
:::

Now put both skills together in a dialogue. These are greetings from Module 1, but this time read them with full stress and intonation awareness:

> **Оленка:** Привіт! ↘ *(Hi!)*
> **Тарас:** Привіт! Як справи? ↗ *(Hi! How are you?)*
> **Оленка:** Добре! А у тебе? ↗ *(Good! And you?)*
> **Тарас:** Теж добре, дякую! ↘ *(Also good, thanks!)*

Read this dialogue aloud twice. First time: slowly, tapping each syllable, exaggerating the stress. Second time: at natural speed, letting the melody flow. This is your first full integrated performance of Ukrainian sound, stress, and melody together.

Stress — **наголос** — tells you which syllable to emphasize. Intonation — **інтонація** — tells you what the sentence means. Together they are the music of Ukrainian. Reading aloud — **вголос** — is the practice method that trains both at once. Do it every time you see new Ukrainian text.

## Підсумок — Summary

Two core skills from this module: **наголос** — stress is free in Ukrainian, it can fall on any syllable, it moves between forms of the same word, and it changes meaning. **Інтонація** — the melody of your voice signals sentence type: falling for statements, rising for yes/no questions, and a strong fall for exclamations. Together, these two elements are what makes Ukrainian sound like Ukrainian.

### Self-check

- **Що таке наголос?** — The syllable you say louder and longer. In Ukrainian, stress is free — it can fall on any syllable, and there is no fixed rule for its position.

- **Чи може наголос змінити значення слова? Наведи приклад.** — Yes. **Замок** with stress on the first syllable means "castle." **Замок** with stress on the second syllable means "lock." Same letters, different word.

- **Яку інтонацію ти використовуєш для питання «так/ні»?** — Rising intonation ↗ — your voice goes up on the last stressed syllable. Example: **Це кава?** ↗

- **Яку інтонацію ти використовуєш для розповідного речення?** — Falling intonation ↘ — your voice drops at the end. Example: **Це кава.** ↘

- **Прочитай вголос:** **Це аптека?** — rising ↗ (yes/no question). **Так, це аптека.** — falling ↘ (statement). **Як гарно!** — strong falling ↘↘ (exclamation). Read all three aloud, exaggerating the melody to feel the difference.

Module 5 — **Хто Я?** (Who Am I?) — introduces names and greetings. Everything from this module applies immediately: **Мене звати Оленка.** ↘ — a statement with falling intonation. **Як тебе звати?** ↗ — a question with rising intonation. **Дуже приємно!** ↘↘ — an exclamation with strong falling force. Every new Ukrainian word you learn from now on: write it with its stress mark. Check goroh.pp.ua when unsure. This small habit — marking stress from the very first word — is the foundation of natural-sounding Ukrainian.

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

**DO NOT use:** fill-in with Ukrainian sentences, error-correction, translate (learner can't write Ukrainian yet), cloze, unjumble.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress
- **quiz** — Де наголос?: Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Pick the word with different stress pattern

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
