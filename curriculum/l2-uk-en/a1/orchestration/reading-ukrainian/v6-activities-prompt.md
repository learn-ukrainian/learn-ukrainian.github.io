# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/reading-ukrainian.yaml` file for module **2: Reading Ukrainian** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-syllable-division -->`
- `<!-- INJECT_ACTIVITY: match-iotated-vowels -->`
- `<!-- INJECT_ACTIVITY: quiz-syllable-count -->`
- `<!-- INJECT_ACTIVITY: quiz-read-meaning -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Divide words into syllables: мо-ло-ко, ап-те-ка'
  items: 8
  type: fill-in
- focus: How many syllables? Count the vowels.
  items: 8
  type: quiz
- focus: 'Match iotated vowels to their sound components: Я=[й]+[а]'
  items: 4
  type: match-up
- focus: Read the word and choose its meaning
  items: 6
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- університет (university) — long word practice
- бібліотека (library) — 5 syllables
- фотографія (photography) — long word with Ф
- шоколад (chocolate) — Ш + О + К combination
required:
- яблуко (apple) — Я at word start = [йа]
- молоко (milk) — 3 syllables, all simple vowels
- людина (person) — Л + Ю combination
- вулиця (street) — Ц sound practice
- столиця (capital) — Київ — столиця України
- каша (porridge) — Ш sound practice
- пісня (song) — softening by Я after consonant


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Склади (Syllables)

You know all 33 Ukrainian letters from the previous module. You can recognize **А**, **М**, **К**, and the rest on sight. But knowing individual letters is like knowing individual notes on a piano — the real music happens when you combine them. Right now, you will learn to read *any* Ukrainian word, even ones you have never seen before. The secret? Ukrainian spelling is phonetic. Each letter makes one sound, every time. There are no silent letters, no spelling surprises, no guessing. If you can sound out syllables, you can read anything. So the question becomes: how do you break a word into syllables?

Ukrainian first-graders learn one golden rule from their very first **буквар** (primer). Большакова, Grade 1, page 25, states it clearly: **«У слові стільки складів, скільки голосних звуків.»** — "A word has as many syllables as it has vowel sounds." This rule never breaks. Not once, not ever. Count the vowels, count the syllables. Take **мама** (mother): the vowels are **А** and **А** — two vowels, two syllables: **ма-ма**. Now **молоко** (milk): **О**, **О**, **О** — three vowels, three syllables: **мо-ло-ко**. What about **банк** (bank)? Just one **А** — one vowel, one syllable. And **сон** (dream)? One **О** — one syllable. Try **аптека** (pharmacy): **А**, **Е**, **А** — three vowels, three syllables: **а-пте-ка**. Notice something: consonants prefer to start new syllables rather than close old ones. That is the open-syllable principle — **складоподіл** in Ukrainian. The word splits as **мо-ло-ко**, not "мол-ок-о."

Now you have the rule. Here is the method Ukrainian children use to read new words — the **звуковий аналіз** (sound analysis) method from Большакова, page 29. Four steps: (1) Find the vowels — circle them mentally, they are your anchors. (2) Split the word at syllable boundaries. (3) Sound out each syllable slowly. (4) Blend everything together at natural speed. Walk through **університет** (university): the vowels are **У**, **І**, **Е**, **И**, **Е** — five vowels, five syllables: **у-ні-вер-си-тет**. Now try **бібліотека** (library): **І**, **І**, **О**, **Е**, **А** — five vowels, five syllables: **бі-блі-о-те-ка**. The method works for every word, no matter how long.

<!-- INJECT_ACTIVITY: fill-in-syllable-division -->

## Голосні літери (Vowel Letters)

In Module 1, you learned that Ukrainian has 6 vowel sounds but 10 vowel letters. Now it is time to meet each one individually. The first group is straightforward — six simple vowels, each making exactly one sound, always: **А** sounds like the "a" in "father," **О** like the "o" in "or," **У** like the "oo" in "moon," **Е** like the "e" in "bet," **И** like a sound between English "i" and "e" (no exact English match), and **І** like the "ee" in "see." That is it. **А** always sounds the same. **О** always sounds the same. Compare that to English, where the letter "a" alone has five or more possible sounds. In Ukrainian: one letter, one sound, no exceptions.

The second group is where it gets interesting — the **iotated vowels**: **Я**, **Ю**, **Є**, and **Ї**. These are "two-in-one" letters. Their behavior depends on *where* they appear. At the start of a word or after another vowel, they produce two sounds: **Я** = [й] + [а] — hear it in **яблуко** (apple) and **моя** (my, feminine). **Ю** = [й] + [у] — hear it in **юнак** (young man). **Є** = [й] + [е] — hear it in **єнот** (raccoon) and **синє** (blue, neuter). But after a consonant, these letters soften that consonant and give only the vowel part: in **пісня** (song), the **Н** is softened by **Я**, and you hear just [а] after the soft **Н**. The Grade 2 textbook sums it up perfectly: **«Букви я, ю, є на початку складу позначають два звуки: [йа], [йу], [йе].»**

Then there is **Ї** — a letter unique to Ukrainian. It *always* makes two sounds: [й] + [і], no matter where it appears. It never softens a consonant. You will find it at the start of a word (**їжак** — hedgehog), after a vowel (**мої** — my, plural; **твої** — your, plural), or after an apostrophe. It never appears directly after a consonant — that is what makes it unique among the iotated vowels. No other Slavic language has this letter.

Finally, a critical distinction: **И** versus **І**. These two vowels change meaning. **Кит** (whale) versus **кіт** (cat). **Дим** (smoke) versus **дім** (house). **Лис** (fox) versus **ліс** (forest). **И** is a back vowel — the tongue sits back, lips stay neutral. **І** is a front vowel — the tongue moves forward, lips spread slightly. The Большакова **буквар** places these pairs on the same page deliberately. Practice hearing and producing the difference, because it changes the meaning of words completely.

<!-- INJECT_ACTIVITY: match-iotated-vowels -->

<!-- INJECT_ACTIVITY: quiz-syllable-count -->

## Читання слів (Reading Words)

Time for a strategy shift. Stop reading letter by letter. Start reading syllable by syllable. When you encounter an unfamiliar word, follow this approach: find the vowels first — they are your anchors — then build syllables around them, then blend. Take **книга** (book): spot the vowels **И** and **А** — two syllables — **кни-га** — now say it at natural speed. Try **столиця** (capital city): **О**, **И**, **Я** — three syllables — **сто-ли-ця**. And **вулиця** (street): **У**, **И**, **Я** — three syllables — **ву-ли-ця**. The vowels are your roadmap through any Ukrainian word, no matter how unfamiliar it looks at first glance.

Here are common word patterns for reading practice. Two-syllable words with simple open syllables — the most natural Ukrainian rhythm: **мама** (mother), **тато** (father), **каша** (porridge), **вода** (water), **рука** (hand), **хата** (house), **коза** (goat), **нога** (foot). These flow easily — every syllable ends in a vowel. Two-syllable words with consonant clusters: **школа** (school), **книга** (book), **парта** (desk). The cluster stays together in one syllable. One-syllable words — just one vowel, quick to read: **дім** (house), **сон** (dream), **ліс** (forest), **дуб** (oak), **хліб** (bread), **банк** (bank). Three-syllable words: **аптека** (pharmacy), **людина** (person), **вулиця** (street), **столиця** (capital). The more patterns your eyes recognize, the faster you read — your brain starts seeing syllable shapes automatically instead of processing individual letters.

Watch for three special letter combinations (a preview — Module 3 covers them fully). **Щ** is always two sounds [шч]: **що** (what), **ще** (still/yet), **щастя** (happiness) — one letter, two sounds blended together. **Ь** (the soft sign) has no sound of its own — it softens the consonant before it: **день** (day), **сіль** (salt), **кінь** (horse). The apostrophe (**'**) separates a consonant from an iotated vowel: **сім'я** (family), **м'ясо** (meat), **п'ять** (five). Recognize these combinations when you encounter them — do not let them slow you down.

<!-- INJECT_ACTIVITY: quiz-read-meaning -->

Now build speed. Re-read the word lists above, faster each time. First pass: syllable by syllable. Second pass: whole words without pausing. Third pass: pairs of words in sequence. Ukrainian reading fluency comes from repetition and pattern recognition, not from memorizing definitions.

## Читаємо разом (Reading Together)

A progressive reading ladder. Start where you are comfortable, then push higher.

**Level 1** — two-syllable words (you should read these quickly by now): **мама**, **тато**, **вода**, **рука**, **хата**, **каша**, **школа**, **книга**.

**Level 2** — three-syllable words (find the vowels first): **аптека**, **молоко**, **людина**, **вулиця**, **столиця**, **пісня**.

**Level 3** — four or more syllables (the real test): **університет**, **бібліотека**, **фотографія**, **шоколад**. If you can read **бібліотека** without stopping between syllables, you can read anything in Ukrainian.

Now, your first Ukrainian text. Read it aloud, sentence by sentence. Every word here uses only letters and patterns from Module 1 and this module:

> **Це Київ.** *(This is Kyiv.)* **Це столиця.** *(This is the capital.)* **Тут аптека і банк.** *(Here is a pharmacy and a bank.)* **Там школа.** *(There is a school.)* **Що це?** *(What is this?)* **Це кафе.** *(This is a café.)* **А це пошта.** *(And this is a post office.)* **Ось бібліотека.** *(Here is a library.)* **Тут книги.** *(Here are books.)*

Read it again, faster. You just read real Ukrainian sentences — not isolated words, but connected meaning.

A few tips for self-study. Read aloud — Ukrainian is a phonetic language, and hearing yourself reinforces the letter-sound connections. Point to each syllable as you read, then graduate to pointing at whole words. Look for Ukrainian text online — signs, menus, social media posts — and try to sound out words before checking a translation. Every word you successfully decode builds confidence and speed. In Module 3, you will learn the special signs (**Ь**, the apostrophe, and the uniquely Ukrainian letter **Ґ**) in full detail and start reading longer texts.

## Підсумок — Summary

Four skills from this module. First: the syllable rule — **«У слові стільки складів, скільки голосних звуків»** — count vowels to count syllables. This rule never breaks. **Молоко** has 3 vowels, so 3 syllables: **мо-ло-ко**. Second: the 10 vowel letters — six simple ones (**А**, **О**, **У**, **Е**, **И**, **І**), each making one predictable sound, and four iotated ones (**Я**, **Ю**, **Є**, **Ї**) that can produce two sounds or soften a consonant. Third: the reading strategy — find vowels first, build syllables around them, blend into words at natural speed. Fourth: pattern recognition — the more word shapes you see, the faster you read without thinking.

Self-check: How many syllables in **бібліотека**? Five — count the vowels: **І**, **І**, **О**, **Е**, **А**. What two sounds does **Я** make at the start of **яблуко**? [й] + [а]. What is the difference between **кит** and **кіт**? Whale versus cat — **И** versus **І**, one vowel changes everything. What does **Ь** do? It softens the consonant before it, with no sound of its own. What does the apostrophe do? It separates a consonant from an iotated vowel, as in **сім'я**.

Next in Module 3: the soft sign, the apostrophe, and the uniquely Ukrainian letter **Ґ** — explored in full detail.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: reading-ukrainian
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

**Level: A1.1 (Module 2/55) — COMPLETE BEGINNER**

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

### Pattern: phonetics-sounds-letters
- **quiz** — Звук чи літера?: Distinguish звук from літера — fundamental Ukrainian phonetics distinction
  - Instruction: *Choose the correct answer*
- **match-up** — Літера → Звук: Match letters to their sound values, especially multi-sound letters (я, ю, є, ї)
  - Instruction: *Match each letter to the sound(s) it represents*
- **group-sort** — Голосні й приголосні: Sort letters/sounds into голосні (vowel) vs приголосні (consonant)
  - Instruction: *Розподіліть звуки*
- **image-to-letter** — Знайди літеру: See image, identify the Ukrainian letter it starts with

### Pattern: phonetics-syllables
- **divide-words** — Поділи слова на склади: Interactive syllable division — tap between letters to insert hyphens
  - Instruction: *Поділіть слово на склади*
- **count-syllables** — Порахуй склади: Count syllables — each vowel = one syllable (складотворчі голосні)
  - Instruction: *How many syllables?*
- **pick-syllables** — Вибери закриті/відкриті склади: Classify syllables as відкритий (ends vowel) or закритий (ends consonant)
  - Instruction: *Select all closed syllables (закриті склади)*
- **odd-one-out** — Четверте зайве: Pick the word that doesn't belong — by syllable count, type, or pattern
  - Instruction: *Яке слово зайве?*

### Pattern: phonetics-soft-hard
- **group-sort** — М'який чи твердий?: Sort consonants/words by soft vs hard pronunciation
  - Instruction: *Розподіліть*
- **quiz** — Де потрібен ь?: Choose which word needs м'який знак
- **error-correction** — Виправ помилку: Find where м'який знак or апостроф is missing/wrong

### Pattern: grammar-numbers
- **quiz** — Яке число?: Recognize written number words
- **fill-in** — Напиши цифру словом: Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Match digits to their Ukrainian word forms

### Pattern: general-vocabulary
- **match-up** — Слово → переклад: Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Fill in the missing word from context
- **anagram** — Склади слово: Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Choose correct translation from options

### Pattern: general-reading
- **true-false** — Правда чи ні?: Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Answer questions about a text passage


**Use these patterns.** If the pattern library recommends `divide-words` for a syllable module, generate a `divide-words` exercise. If it recommends `group-sort` for gender, generate a `group-sort`. The patterns encode how Ukrainian teachers actually test these concepts.

---

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
