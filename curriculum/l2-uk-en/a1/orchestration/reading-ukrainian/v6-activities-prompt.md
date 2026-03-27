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

- `<!-- INJECT_ACTIVITY: quiz-syllable-count -->`
- `<!-- INJECT_ACTIVITY: match-iotated-vowels -->`
- `<!-- INJECT_ACTIVITY: fill-in-syllable-division -->`
- `<!-- INJECT_ACTIVITY: quiz-read-word-meaning -->`
- `<!-- INJECT_ACTIVITY: quiz-reading-comprehension -->`

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
## Склади — Syllables

You already know Ukrainian letters from M01 — you can recognise them, name them, and connect each one to a sound. Now it is time to read real words. The secret to reading Ukrainian is not memorising individual letters harder. It is **склади** (syllables). Ukrainian children learn to read by syllables, not letter by letter, and so will you. There is a golden rule from the very first page of the Ukrainian буквар, and every student in Ukraine knows it by heart: **«У слові стільки складів, скільки голосних звуків.»** Count the vowels, count the syllables. This rule never breaks — not for short words, not for long ones, not ever.

Watch how it works with progressively longer words. Take **мама** (mother): find the vowels — **А**, **А**. Two vowels means two syllables: **ма-ма**. Now try **молоко** (milk): find the vowels — **О**, **О**, **О**. Three vowels means three syllables: **мо-ло-ко**. What about **банк** (bank)? One vowel, **А** — one syllable. **Сон** (dream): one vowel, **О** — one syllable. **Оса** (wasp): **О**, **А** — two syllables, **о-са**. **Ананас** (pineapple): **А**, **А**, **А** — three syllables, **а-на-нас**. The rule works for every Ukrainian word without exception.

So what do you do when you meet an unfamiliar word? Follow the four-step method from Большакова's звуковий аналіз. Step one: find the vowels — they are the core of every syllable. Step two: split the word at syllable boundaries. In Ukrainian, consonants prefer to start a new syllable rather than close the previous one. This is the open-syllable principle, called **складоподіл**. Step three: sound out each syllable slowly. Step four: blend the syllables together at natural speed. Walk through **аптека** (pharmacy): vowels are **А**, **Е**, **А** — three syllables, **ап-те-ка**. Now try **університет** (university): count the vowels — **У**, **І**, **Е**, **И**, **Е** — five syllables, **у-ні-вер-си-тет**.

<!-- INJECT_ACTIVITY: quiz-syllable-count -->

One note on how Ukrainian splits syllables differently from English. Ukrainian strongly prefers open syllables — syllables that end in a vowel. That is why **молоко** splits as **мо-ло-ко** (each syllable ends with a vowel), not мол-ок-о. When a consonant sits between two vowels, it belongs to the next syllable, not the previous one. When two or more consonants cluster together, most of them still move forward to start the new syllable. This will feel natural quickly — just remember that consonants want to begin syllables, not end them.

## Голосні літери — Vowel Letters

Recall from M01 that Ukrainian has six vowel sounds but ten vowel letters. Now it is time to meet all ten individually. The first group is the simple vowels — each letter makes exactly one sound, every single time, with no surprises. **А** sounds like the "a" in "father" (**мама**). **О** sounds like the "o" in "more" (**молоко**). **У** sounds like the "oo" in "food" (**рука**, meaning hand). **Е** sounds like the "e" in "bet" (**село**, meaning village). **И** is a sound English does not have — it sits between "i" in "bit" and "oo" in "hook" (**дим**, meaning smoke). **І** sounds close to "ee" in "see" but shorter (**дім**, meaning house). These six are straightforward: one letter, one sound, always.

The second group is the iotated vowels — the clever ones that do double duty. **Я** at the start of a word or after a vowel equals two sounds: [й] + [а]. Say **яблуко** (apple) — hear that glide before the "a"? That is the [й]. After a consonant, **Я** does something different: it softens that consonant and adds [а]. In **пісня** (song), the **Н** before **Я** becomes soft. The same pattern applies to **Ю**: at word start, **юнак** (young man) gives [й] + [у]; after a consonant, it softens and adds [у]. **Є** works identically: **єнот** (raccoon) at word start gives [й] + [е]; after a consonant, like in **синє** (blue, neuter), it softens and adds [е]. Then there is **Ї** — the unique one. **Ї** always equals [й] + [і], no matter where it appears. It never softens a consonant. It only appears at the start of a word, after a vowel, or after an apostrophe: **їжак** (hedgehog), **мої** (my, plural). **Ї** is uniquely Ukrainian — no other Slavic language has it.

Here is the textbook method from Grade 2 for decoding iotated vowels: determine the position first, then decode. **Букви я, ю, є на початку складу позначають два звуки**: [йа], [йу], [йе]. After a consonant, they represent one sound plus softening. Practice: **яблуко** — word start, so Я = [й] + [а]. **Маля** (baby) — Я after a consonant, so Л becomes soft + [а]. **М'ята** (mint) — after apostrophe, so Я = [й] + [а] again (the apostrophe blocks softening).

<!-- INJECT_ACTIVITY: match-iotated-vowels -->

Now for the most important vowel distinction in Ukrainian: **И** versus **І**. These two sounds do not exist in English, and confusing them changes meaning entirely. **Кит** (whale) versus **кіт** (cat). **Дим** (smoke) versus **дім** (house). **Лис** (fox) versus **ліс** (forest). **Сир** (cheese) versus **сік** (juice — a different word, but it shows the І sound clearly). **И** is a back vowel — your tongue pulls back and down. **І** is a front vowel — your tongue pushes forward and up, closer to "ee." Practice hearing and producing this difference. It is the single most important vowel contrast in Ukrainian, and getting it right early will save you from confusion later.

## Читання слів — Reading Words

Now combine everything: letters from M01, the syllable rule, and vowel knowledge. Together they give you the ability to read real Ukrainian words. The key shift is this: stop reading letter by letter. Read syllable by syllable. For any new word, first scan for vowels — they reveal the syllable structure — then build outward. Take **книга** (book): spot the vowels **И** and **А**, so there are two syllables — **кни-га**. Now try **вулиця** (street): vowels **У**, **И**, **Я** — three syllables, **ву-ли-ця**. And **столиця** (capital city): vowels **О**, **И**, **Я** — three syllables, **сто-ли-ця**. Київ — **столиця**.

The more word patterns you recognise, the faster you read. Here are the most common shapes. The CVCV pattern — consonant, vowel, consonant, vowel — is everywhere: **мама**, **тато** (father), **каша** (porridge), **вода** (water), **рука** (hand), **хата** (house), **коза** (goat), **нога** (foot). All two syllables, all open syllables, no surprises. Next, words with a consonant cluster before the second vowel: **школа** (school), **книга**, **парта** (desk). Still two syllables, but your mouth has to handle two consonants in a row before the vowel. Finally, closed-syllable words — just one vowel, closed off by consonants: **дім**, **сон**, **ліс**, **дуб** (oak), **хліб** (bread), **банк**. One syllable each. Recognising these shapes lets your eyes jump ahead and your reading speed increase.

<!-- INJECT_ACTIVITY: fill-in-syllable-division -->

A few special letter combinations to watch for while reading. **Щ** always represents two sounds [шч] packed into one letter: **що** (what), **ще** (still/more), **щастя** (happiness). **Ь** (soft sign) has no sound of its own — it softens the consonant before it: **день** (day), **сіль** (salt), **кінь** (horse). The apostrophe (**'**) separates a consonant from an iotated vowel, forcing the two-sound pronunciation: **сім'я** (family), **м'ясо** (meat), **п'ять** (five). Without the apostrophe, the consonant would be softened instead. Do not worry about mastering these fully yet — M03 covers them in complete detail.

<!-- INJECT_ACTIVITY: quiz-read-word-meaning -->

Reading confidence comes from practice, not memorisation. Ukrainian spelling is phonetic — what you see is what you say. Unlike English, there are no silent letters (except **Ь**, which modifies rather than sounds), no surprise pronunciations, no "read" versus "read" confusion. Once you know the letter-sound mappings from M01 and the syllable rule from this module, you can read any Ukrainian word — even words you have never seen before. This is the superpower of Ukrainian's transparent orthography. Trust the letters. They will not lie to you.

## Читаємо разом — Reading Together

Time for progressive reading practice. Start simple, then build up.

**Level 1** (2 syllables): **мама**, **тато**, **вода**, **рука**, **хата**, **каша**, **нога**, **коза**. Read each one: find the vowels, split into syllables, blend. **Level 2** (3 syllables): **аптека**, **молоко**, **людина** (person), **вулиця**, **столиця**. **Level 3** (4+ syllables): **університет**, **бібліотека** (library), **фотографія** (photography). Do not rush — accuracy before speed.

Now read connected text. This short passage uses only **Це** (this is) / **Тут** (here) / **Там** (there) + nouns — no verbs, just identification. Read it syllable by syllable first, then try again faster:

> **Це Київ. Це столиця. Тут аптека і банк. Там школа. Що це? Це кафе. А це пошта. Тут університет і бібліотека.**

Every word in this passage follows the patterns you have learned. If you can read it fluently, you are ready for M03.

<!-- INJECT_ACTIVITY: quiz-reading-comprehension -->

Here are tips for building reading fluency at home. Look for Ukrainian text anywhere — signs, menus, product labels, social media posts. Sound out the words even if you do not know their meaning yet. The physical act of decoding builds neural pathways for reading. Try reading the same passage three times: first slowly, syllable by syllable; then at a normal pace; then slightly fast. Ukrainian YouTube channels with subtitles are excellent practice — pause the video, read the subtitle, then listen to the pronunciation. The goal is not speed. The goal is automatic decoding — where your brain stops seeing individual letters and starts seeing syllables and whole words. That shift happens through repetition, and it happens faster than you expect.

## Підсумок — Summary

This module gave you three key skills. First: the syllable rule — **«У слові стільки складів, скільки голосних звуків»** — count the vowels to count the syllables, and it works for every Ukrainian word without exception. Second: the ten vowel letters — six simple ones (**А**, **О**, **У**, **Е**, **И**, **І**) that each make one consistent sound, and four iotated ones (**Я**, **Ю**, **Є**, **Ї**) that produce two sounds at the start of a syllable or soften a consonant when they follow one. Third: the reading strategy — scan for vowels, split into syllables, blend, and read. Ukrainian's phonetic spelling means you can now decode any word you encounter, even if you have never seen it before.

Self-check before moving on. Can you answer these questions? How do you count syllables in a Ukrainian word? What are the six vowel sounds? Name the four iotated vowel letters and explain when they represent two sounds. What does **Ь** (soft sign) do? What does the apostrophe do? Final challenge: read **бібліотека** — how many syllables? Five: **бі-блі-о-те-ка**. Five vowels, five syllables. If you got that right, you are ready for M03: Special Signs.

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
