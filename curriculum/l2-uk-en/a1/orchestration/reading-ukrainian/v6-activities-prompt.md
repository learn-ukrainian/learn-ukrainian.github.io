<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/reading-ukrainian.yaml` file for module **2: Reading Ukrainian** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-syllable-count -->`
- `<!-- INJECT_ACTIVITY: match-iotated-vowels -->`
- `<!-- INJECT_ACTIVITY: fill-in-syllable-division -->`
- `<!-- INJECT_ACTIVITY: quiz-read-and-match -->`
- `<!-- INJECT_ACTIVITY: fill-in-longer-words -->`

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

Every Ukrainian first-grader learns a golden rule from their very first буквар (reading primer). The rule is simple, and it never breaks: **У слові стільки складів, скільки голосних звуків** — a word has as many syllables as it has vowel sounds. Before you read any new Ukrainian word, count the vowels. They are the key. Look at the word **мама** (mother). Two vowels — **А** and **А** — so two syllables: **ма-ма**. Now try **молоко** (milk). Three vowels — **О**, **О**, **О** — three syllables: **мо-ло-ко**. What about **банк** (bank)? One vowel — **А** — one syllable. Done.

With that rule in hand, here is your four-step method for reading any Ukrainian word, following the same звуковий аналіз (sound analysis) approach used in Ukrainian schools. Step one: scan the word and spot all the vowels. Step two: split the word into syllables — in Ukrainian, consonants prefer to start a new syllable rather than end one. This is called **складоподіл** (syllable division), and it follows the open-syllable principle. Step three: sound out each syllable separately. Step four: blend them together at natural speed. Walk through it with **аптека** (pharmacy): spot the vowels **А**, **Е**, **А** — that gives three syllables. Split: **ап-те-ка**. Sound out each piece, then blend: **аптека**.

Now apply the method to longer words. Take **шоколад** (chocolate): three vowels (**О**, **О**, **А**), three syllables — **шо-ко-лад**. Try **університет** (university): six vowels (**У**, **І**, **Е**, **И**, **Е**... wait, let us count carefully — **у-ні-вер-си-тет** gives five syllables). And **бібліотека** (library)? Five vowels (**І**, **І**, **О**, **Е**, **А**), five syllables: **біб-лі-о-те-ка**. Even a word that looks long and intimidating falls apart once you count the vowels. The rule never breaks.

<!-- INJECT_ACTIVITY: quiz-syllable-count -->

## Голосні літери (Vowel Letters)

From M01 you already know that Ukrainian has 6 vowel sounds but writes them with 10 vowel letters. The first six are straightforward — each letter makes exactly one consistent sound, every time, no exceptions:

- **А** — as in **аптека** (pharmacy)
- **О** — as in **молоко** (milk)
- **У** — as in **рука** (hand)
- **Е** — as in **вечір** (evening)
- **И** — as in **кит** (whale)
- **І** — as in **кіт** (cat)

These six are completely reliable. What you see is what you say.

The remaining four vowel letters — **Я**, **Ю**, **Є**, **Ї** — are called iotated vowels, and they have a dual nature. When **Я** appears at the start of a word or after another vowel, it produces two sounds: [й] + [а]. The word **яблуко** (apple) starts with **Я**, so you hear [йа]-блу-ко. In **моя** (my, feminine), the **Я** comes after the vowel **О** — again two sounds: мо-[йа]. But after a consonant, **Я** does something different: it softens that consonant and adds only [а]. In **пісня** (song), the **Н** before **Я** becomes soft — no [й] sound appears. The same dual pattern applies to **Ю** (either [йу] or softening + [у]) and **Є** (either [йе] or softening + [е]). Look at **людина** (person): the **Л** is softened by **Ю**, so you hear soft Л + [у], not [й]. And in **вечірнє** (evening, neuter adjective), the **Н** is softened by **Є**.

<!-- INJECT_ACTIVITY: match-iotated-vowels -->

**Ї** stands apart from the other three. It always produces two sounds — [йі] — with no exceptions and no other behavior. It never softens a consonant before it, because it simply never appears directly after a consonant. You find **Ї** only at the start of a word like **їжак** (hedgehog), after a vowel as in **країна** (country), or after an apostrophe as in **з'їсти** (to eat up). **Ї** is a distinctly Ukrainian letter — Russian has no equivalent.

One more critical distinction: **И** versus **І**. These are two separate phonemes that change meaning. Compare **кит** (whale) with **кіт** (cat), or **дим** (smoke) with **дім** (house). The sound [и] sits further back in the mouth; [і] is a high front vowel, closer to the English "ee." Mixing them up changes one word into a completely different one. Listen carefully to model pronunciations before practising — this difference is subtle but essential.

<!-- INJECT_ACTIVITY: fill-in-syllable-division -->

## Читання слів (Reading Words)

Counting vowels and splitting syllables is the scaffold. The goal is fluency — reading whole words without pausing at each letter. Here is the reading strategy one more time, applied to real words: (1) spot the vowels first, because they are the syllable cores; (2) build the consonant clusters around them; (3) read syllable by syllable; (4) repeat until the word flows as a single unit. Try it with **книга** (book): two vowels, **И** and **А**, so two syllables — **кни-га**. Now read it again faster: **книга**. That is the rhythm.

Ukrainian words tend to follow a few common patterns. The easiest are words where consonants and vowels alternate evenly: **мама** (mother), **тато** (father), **каша** (porridge), **вода** (water), **рука** (hand), **хата** (house), **коза** (goat), **нога** (leg). Each syllable is open — it ends on a vowel — so blending is smooth. Next come words with a consonant cluster before a vowel, which are slightly harder: **школа** (school), **книга** (book), **парта** (school desk). Your mouth has to handle two consonants in a row before reaching the vowel. Finally, closed-syllable words end on a consonant: **дім** (house), **сон** (dream), **ліс** (forest), **дуб** (oak), **хліб** (bread), **банк** (bank). These are short — usually one syllable — but they build confidence because you hear the whole word instantly.

<!-- INJECT_ACTIVITY: quiz-read-and-match -->

Time for a progressive reading drill across three difficulty levels.

**Level 1 — two-syllable words:** Read each word first split, then blended.
**Ма-ма** → **мама**. **Та-то** → **тато**. **Во-да** → **вода**. **Ру-ка** → **рука**. **Ха-та** → **хата**. **Ка-ша** → **каша**.

**Level 2 — three-syllable words:** Split, then blend.
**Ап-те-ка** → **аптека** (pharmacy). **Мо-ло-ко** → **молоко** (milk). **Лю-ди-на** → **людина** (person). **Ву-ли-ця** → **вулиця** (street).

**Level 3 — four or more syllables:** These look intimidating, but the vowel-counting method conquers them.
**У-ні-вер-си-тет** → **університет** (university) — 5 syllables. **Біб-лі-о-те-ка** → **бібліотека** (library) — 5 syllables. **Фо-то-гра-фі-я** → **фотографія** (photography) — 5 syllables.

Finish with Ukrainian city names as a confidence-builder: **Ки-їв** (Kyiv — notice the **Ї**), **О-де-са** (Odesa), **Хар-ків** (Kharkiv), **Дні-про** (Dnipro), **Пол-та-ва** (Poltava).

Before moving on, here is a preview of three special features you will meet in M03 — not the focus today, but worth recognizing when they appear. First: **Щ** always reads as [шч] — one letter, two sounds. In **що** (what) and **ще** (still, yet), do not read it as [ш] alone. Second: **Ь** (м'який знак, the soft sign) has no sound of its own. It only softens the consonant before it. In **день** (day), the **Н** is soft. In **сіль** (salt), the **Л** is soft. In **кінь** (horse), the **Н** is soft. Think of **Ь** as a silent softener. Third: the apostrophe (**'**) does the opposite — it separates a consonant from a following iotated vowel, preventing softening. In **сім'я** (family), the **М** stays hard and then **Я** produces its full [йа]. Same in **м'ясо** (meat) and **п'ять** (five). These three features will be drilled thoroughly in M03; for now, just recognize them when you see them.

> **Аня:** Біб-лі-о-те-ка... **бібліотека**! *(Library!)*
> **Марко:** Так! А це? *(Yes! And this one?)*
> **Аня:** Яб-лу-ко... **яблуко**! *(Apple!)*
> **Марко:** А це? *(And this?)*
> **Аня:** Шо-ко-лад... **шоколад**! *(Chocolate!)*
> **Марко:** **Шоколад** — смачно! *(Chocolate — delicious!)*

Аня uses the syllable method — split, then blend — and reads three words she has never seen before. Марко confirms each one. Notice how even a five-syllable word like **бібліотека** becomes manageable once you count the vowels and take it piece by piece.

<!-- INJECT_ACTIVITY: fill-in-longer-words -->

## Підсумок — Summary

Self-check — test yourself on the key concepts from this module:

- **How do you count syllables in a Ukrainian word?** → Count the vowels. Each vowel = one syllable.
- **What are the 6 vowel sounds?** → [а], [о], [у], [е], [и], [і].
- **Name the 4 iotated vowel letters.** → **Я**, **Ю**, **Є**, **Ї**.
- **What do Я, Ю, Є do at the start of a word?** → They produce two sounds: **Я** = [й] + [а], **Ю** = [й] + [у], **Є** = [й] + [е].
- **What does Ї always produce?** → Always [йі] — two sounds, no exceptions.
- **What does Ь do?** → It softens the consonant before it but has no sound of its own.
- **What does the apostrophe do?** → It separates the consonant from a following iotated vowel, so no softening occurs.
- **Read this word and count syllables: бібліотека.** → **Біб-лі-о-те-ка**. Five syllables (five vowels: **І**, **І**, **О**, **Е**, **А**).

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
