<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/special-signs.yaml` file for module **3: Special Signs** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-soft-sign-apostrophe -->`
- `<!-- INJECT_ACTIVITY: fill-in-soft-sign-apostrophe -->`
- `<!-- INJECT_ACTIVITY: match-voiced-voiceless -->`
- `<!-- INJECT_ACTIVITY: quiz-g-vs-g -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Does this word have a soft sign, apostrophe, or neither?
  items: 8
  type: quiz
- focus: 'Match voiced-voiceless pairs: Б↔П, Д↔Т, etc.'
  items: 8
  type: match-up
- focus: 'Add the missing Ь or apostrophe: сім_я, ден_, п_ять'
  items: 6
  type: fill-in
- focus: Choose the correct pronunciation for Г vs Ґ words
  items: 4
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- батько (father, formal) — soft sign
- учитель (teacher) — soft sign at end
- дев'ять (nine) — apostrophe
- комп'ютер (computer) — apostrophe in cognate
- м'який (soft) — apostrophe + soft sign
required:
- сім'я (family) — apostrophe word
- день (day) — soft sign after Н
- сіль (salt) — soft sign after Л
- м'ясо (meat) — apostrophe after М
- п'ять (five) — apostrophe after П
- гарно (nicely, beautifully) — Г [ɦ] practice
- риба (fish) — Р and И practice


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## М'який знак (The Soft Sign — Ь)

The word **камінь** (stone) and the word **камін** (fireplace) look almost identical. One small sign at the end — **Ь** — changes the meaning completely. This sign is called the **м'який знак** (soft sign), and it has no sound of its own. Its single job: soften the consonant before it. Ukrainian distinguishes between hard consonants (тверді приголосні) and soft consonants (м'якшені приголосні). In Ukrainian textbooks, hard consonants are marked with [–] and soft consonants with [=] — a notation from Захарійчук's Grade 1 textbook. So **камінь** has a soft **Н** at the end [=], while **камін** has a hard **Н** [–]. Look at more words where Ь changes everything: **тінь** (shadow), **лінь** (laziness), **сіль** (salt), **кінь** (horse).

Where does Ь commonly appear? It follows specific consonant patterns. Here are the most frequent endings:

- **-нь** → **день** (day), **кінь** (horse), **осінь** (autumn)
- **-ль** → **сіль** (salt), **біль** (pain)
- **-ть** → **мить** (moment)
- **-зь** → **мазь** (ointment)

One key rule: Ь appears only AFTER a consonant, never at the start of a word, never after a vowel. The Літвінова Grade 5 textbook gives a handy mnemonic for which consonants can be softened — the phrase «ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи» covers all seven: Д, Т, З, С, Ц, Л, Н (plus ДЗ).

Minimal pairs prove that hard vs. soft is a real meaning distinction — not just decoration. These pairs come directly from Захарійчук's Grade 1 textbook:

- **тин** (wattle fence) vs **тінь** (shadow)
- **рис** (rice) vs **рись** (lynx)

Try this yourself: cover the Ь with your finger and read the word. Then uncover it and read again. You should hear — and feel — the difference. The tip of your tongue moves forward and up for the soft consonant.

A few more practice words from Ukrainian textbooks: **учитель** (teacher), **батько** (father), **маленький** (small), **стільчик** (little chair). The Большакова Grade 2 textbook uses this sentence for practice: «Василько сів на маленький стільчик.» Read these words aloud as a drill: **сіль, день, кінь, мить, учитель, осінь**. Can you feel the tongue shift on each final consonant?

<!-- INJECT_ACTIVITY: quiz-soft-sign-apostrophe -->

## Апостроф (The Apostrophe)

The apostrophe is not a letter — it is a separator sign, a tiny signal between a consonant and a vowel. The rule, straight from Захарійчук's Grade 1 textbook (p. 97) and confirmed by Большакова Grade 2 (p. 57): the apostrophe appears after the consonants **Б, П, В, М, Ф, Р** when followed by the vowels **Я, Ю, Є, Ї**. These six consonants would normally soften before those vowels. The apostrophe says: "Stay hard." Without it, the consonant softens. With it, the consonant stays hard and the vowel splits into two sounds.

Here is the contrast. In the word **пісня** (song), the **Н** softens — you hear one merged, soft sound. But in **п'ять** (five), the **П** stays hard, and the **Я** splits into two distinct sounds: [й] + [а]. You hear the hard **П**, then a clear [й] launching the vowel. Walk through each example with this in mind:

- **сім'я** (family) — hard **М**, then [й]+[а]
- **м'ясо** (meat) — hard **М**, then [й]+[а]
- **п'ять** (five) — hard **П**, then [й]+[а]
- **комп'ютер** (computer) — hard **П**, then [й]+[у]. A cognate you can verify immediately.

A poem from Захарійчук Grade 1 (p. 71) lists apostrophe words in a playful rhyme. Here is the reading drill from that poem: **м'яз** (muscle), **м'яч** (ball), **під'їзд** (entrance), **в'юн** (loach fish), **м'якуш** (soft part of bread), **бар'єр** (barrier), **з'їзд** (congress), **п'ятниця** (Friday), **ім'я** (name). From Большакова Grade 1: Ukrainian proper names also use the apostrophe — **Дар'я**, **Мар'яна**, **Лук'ян**. Read each word aloud. Feel the consonant stay firm, then hear the [й] launch the vowel.

One word has BOTH signs: **м'який** (soft). The apostrophe keeps **М** hard, and the **Ь** at the end softens the **Й**. Here are eight apostrophe words to memorize — they cover every vowel that can follow the apostrophe (Я, Ю, Є, Ї): **п'ять, дев'ять** (nine), **сім'я, м'ясо, м'яч, ім'я, об'єкт** (object), **здоров'я** (health).

<!-- INJECT_ACTIVITY: fill-in-soft-sign-apostrophe -->

## Дзвінкі і глухі (Voiced and Voiceless)

Place your fingers on your throat. Say **Б**. You feel vibration — your vocal cords are working. Now say **П**. Silence — only air. This is the difference between voiced (дзвінкі) and voiceless (глухі) consonants. As Большакова's Grade 2 textbook puts it: voiced consonants form with голос (voice) + шум (noise); voiceless consonants form with шум alone. This is a tactile discovery, not a rule to memorize — feel it with your own throat.

Ukrainian consonants form eight core voiced-voiceless pairs. Here they are, with a word pair for each from Большакова Grade 2 (p. 62):

| Voiced | Voiceless | Word pair |
|--------|-----------|-----------|
| **Б** | **П** | **дуб** (oak) — **суп** (soup) |
| **Г** | **Х** | **гуска** (goose) — **хустка** (kerchief) |
| **Ґ** | **К** | **ґава** (jackdaw) — **кава** (coffee) |
| **Д** | **Т** | **дуб** (oak) — **туп** (dull) |
| **З** | **С** | **злива** (downpour) — **слива** (plum) |
| **Ж** | **Ш** | **жабка** (little frog) — **шапка** (hat) |
| **ДЖ** | **Ч** | |
| **ДЗ** | **Ц** | |

Read each pair aloud. Apply the throat test to confirm which is voiced and which is voiceless.

Ukrainian has one defining phonetic feature: voiced consonants keep their full sound at the end of a word. The word **дуб** is pronounced [дуб] — you hear the full voiced **Б** at the end. The word **мороз** (frost) is pronounced [мороз] — the **З** stays voiced. Every consonant keeps its true sound in every position. This is a core feature of Ukrainian phonetics. Minimal pairs for ear training: **балка** (beam) vs **палка** (stick); **коза** (goat) vs **коса** (braid). Say **дуб** aloud — keep the [б] fully voiced at the end.

Some voiced consonants have no voiceless partner at all: **В, Л, М, Н, Й, Р** — these are always voiced. And voiceless **Ф** has no voiced partner (Ukrainian words with **Ф** are mostly loanwords: **фото**, **фарба** — paint). Short practice list: **жабка, шапка, дуб, суп, казка** (fairy tale), **каска** (helmet).

<!-- INJECT_ACTIVITY: match-voiced-voiceless -->

## Вимова українських звуків (Pronouncing Ukrainian Sounds)

**И** is a uniquely Ukrainian vowel. It is NOT the same as **І** — they are two different letters representing two different sounds. With **И**, the tongue sits slightly lower and further back in the mouth. With **І**, it moves forward and up. The difference is not decorative — it changes the meaning of a word. Minimal pairs directly from Большакова's Grade 1 Буквар:

- **бик** (bull) vs **бік** (side)
- **дим** (smoke) vs **дім** (house)
- **лис** (fox) vs **ліс** (forest)
- **кит** (whale) vs **кіт** (cat)

Read each pair aloud. The **И** word sounds lower and darker than the **І** word. Never confuse them — they are different letters, different sounds, different words.

**Г** and **Ґ** are two different Ukrainian letters for two different sounds. **Г** is a voiced fricative — air flows through a narrowed throat without full closure: **гарно** (nicely), **гора** (mountain), **голова** (head). Compare it to the "h" in "behind" — but voiced and slightly rougher. **Ґ** is a hard stop — full closure of the throat, then a burst of air: **ґанок** (porch), **ґудзик** (button). From Большакова Grade 2: the pair **ґава** (jackdaw) vs **кава** (coffee) shows **Ґ** alongside its voiceless partner **К**. The letter **Ґ** is uniquely Ukrainian — its presence in the alphabet is a mark of Ukrainian phonetic independence. As the Літвінова Grade 5 textbook confirms: both sounds are authentically Ukrainian, but **Ґ** appears in fewer words.

**Р** is the Ukrainian rolled, trilled **Р**. It is not the English "r" — the tongue taps the ridge behind the upper teeth. Practice words: **рука** (hand), **робота** (work), **ранок** (morning), **риба** (fish). A tip: start by saying [д] rapidly several times — that quick tongue tap is close to a single trill. An imperfect **Р** is always understood — native speakers never mishear a learner's **Р** for another sound. Focus on getting comfortable, not perfect.

Short reading drill combining all four sounds from this section: **риба, дим, гарно, ґудзик, кит, бік, голова, ранок, ґанок, лис**. Read each word aloud. Check yourself: **И** or **І**? **Г** or **Ґ**? Is the **Р** rolled?

<!-- INJECT_ACTIVITY: quiz-g-vs-g -->

## Підсумок — Summary

Four topics, one thread: Ukrainian gives you precise tools to control how consonants and vowels sound. **Ь** softens — the consonant before it changes its character. The apostrophe hardens — the consonant stays firm, and the vowel after it splits into two sounds. Voiced consonants vibrate; voiceless ones do not — and Ukrainian keeps every consonant's true sound in every position. **И**, **Г**, and **Ґ** are uniquely Ukrainian sounds that don't exist in English — they are worth the extra practice.

**Self-check — answer these before moving on:**

- **What does Ь do?** → It softens (м'якшує) the consonant before it. It has no sound of its own.
- **After which consonants does the apostrophe appear?** → After **Б, П, В, М, Ф, Р** — when followed by **Я, Ю, Є, Ї**.
- **Name 3 voiced-voiceless pairs.** → **Б-П, З-С, Ж-Ш** (any three from the eight pairs).
- **How is Г different from Ґ?** → **Г** is a voiced fricative (as in **гарно**); **Ґ** is a hard stop (as in **ґудзик**).
- **Read these words aloud:** **сім'я, день, п'ять, гарно, ґудзик, риба.**

These three signs — Ь, the apostrophe, and the voiced-voiceless system — are the foundation of Ukrainian pronunciation. With them, you can read almost any Ukrainian word and know how it sounds. The next module adds the final layer: **наголос** (stress). Once you know where the stress falls, pronunciation clicks into place.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: special-signs
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

**Level: A1.1 (Module 3/55) — COMPLETE BEGINNER**

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

### Pattern: phonetics-soft-hard
- **group-sort** — М'який чи твердий?: Sort consonants/words by soft vs hard pronunciation
  - Instruction: *Розподіліть*
- **quiz** — Де потрібен ь?: Choose which word needs м'який знак
- **error-correction** — Виправ помилку: Find where м'який знак or апостроф is missing/wrong

### Pattern: grammar-adjectives
- **fill-in** — Який? Яка? Яке?: Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Match nouns to correct adjective forms

### Pattern: general-vocabulary
- **match-up** — Слово → переклад: Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Fill in the missing word from context
- **anagram** — Склади слово: Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Choose correct translation from options


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
