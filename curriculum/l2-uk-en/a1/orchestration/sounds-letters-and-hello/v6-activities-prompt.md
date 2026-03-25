# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/sounds-letters-and-hello.yaml` file for module **1: Sounds, Letters, and Hello** (a1).

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

- `<!-- INJECT_ACTIVITY: group-sort-vowels-consonants -->`
- `<!-- INJECT_ACTIVITY: match-false-friends -->`
- `<!-- INJECT_ACTIVITY: fill-in-greeting -->`
- `<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Distinguish between sounds (звуки) and letters (літери). Example questions:
    ''Що ми чуємо і вимовляємо?'' → ''звуки'' | ''Що ми бачимо і пишемо?'' → ''літери''
    | ''Скільки літер в абетці?'' → ''33'' | ''Скільки звуків в українській мові?''
    → ''38''.'
  items: 6
  type: quiz
- focus: 'Match false friend Cyrillic letters to their REAL sounds. Pairs: В ↔ [в]
    (not ''b''), Н ↔ [н] (not ''h''), Р ↔ [р] (not ''p''), С ↔ [с] (not ''c/k''),
    У ↔ [у] (not ''y''), Х ↔ [х] (not ''x'').'
  items: 6
  type: match-up
- focus: 'Complete a basic greeting dialogue with blanks. EXACT pattern: ''— {Привіт}!
    Як {справи}?'' / ''— {Добре}. А у {тебе}?'' / ''— {Чудово}.'' Options per blank:
    Привіт / справи / Добре / тебе / Чудово / Нормально.'
  items: 4
  type: fill-in
- focus: 'Sort Cyrillic letters into Голосні (vowels) and Приголосні (consonants).
    Голосні: А, О, У, Е, И, І. Приголосні: К, М, Т, В, Н, Р, С, Х.'
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- банк (bank)
- аптека (pharmacy)
- метро (metro)
- пошта (post office)
- зупинка (bus stop)
- нормально (okay)
required:
- мама (mother)
- тато (father)
- вода (water)
- рука (hand)
- книга (book)
- школа (school)
- привіт (hi, informal)
- як справи (how are you)
- добре (fine, good)
- чудово (great, wonderful)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Звуки і літери — Sounds and Letters

Look at the text on this screen. What you see are letters — shapes drawn on a surface. Now say any word out loud. What you just produced are sounds — vibrations in the air. You already understand this distinction instinctively, but Ukrainian makes it explicit from day one. Every Ukrainian first-grader learns a golden rule from their very first textbook: **Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери** — "We hear and pronounce sounds, but we see and write letters." This is the foundation of everything that follows. The Ukrainian **абетка** (alphabet) has 33 **літери** (letters), but the language has 38 **звуків** (sounds). Why the mismatch? Because some letters pull double duty — they can represent more than one sound. The letters **я**, **ю**, **є**, and **ї** are the main culprits, and we will explore exactly how they work in the next module.

Ukrainian sounds split into two families. The first family is **голосні звуки** (vowel sounds). These are made with voice alone — your mouth stays open, air flows freely, nothing blocks it. A poem from a first-grade textbook captures this perfectly: **Голосні почуєш в пісні** — "You'll hear vowels in a song." There are 6 vowel sounds in Ukrainian: [а], [о], [у], [е], [и], [і]. But there are 10 vowel letters: **а**, **о**, **у**, **е**, **и**, **і**, **я**, **ю**, **є**, **ї**. The extra four — **я**, **ю**, **є**, **ї** — are called **йотовані** (iotated) letters. They can represent two sounds at once. For now, just recognize them when you see them. Try pronouncing the six pure vowel sounds in sequence: [а] — [о] — [у] — [е] — [и] — [і]. Each one rings out clearly, like singing a note.

The second family is **приголосні звуки** (consonant sounds). These are made when your lips, teeth, or tongue create an obstruction — air hits a barrier and produces noise, either with voice or without it. Another first-grade poem describes them: **Приголосні деренчать, і тихенько шелестять** — "Consonants clatter and softly rustle." Ukrainian has 32 consonant sounds, produced by just 22 consonant letters (plus **ь**, the soft sign, which has no sound of its own — it only softens the consonant before it). Try this contrast: say [а] — your mouth is open, pure voice. Now say [м] — your lips press together, blocking the air. That vibration you feel through closed lips? That is the difference between **голосний** (vowel) and **приголосний** (consonant).

<!-- INJECT_ACTIVITY: group-sort-vowels-consonants -->

## Перші слова — First Words

Some Cyrillic letters are friendly — they look like Latin letters and sound similar too. Meet your first five: **А** [а], **О** [о], **К** [к], **М** [м], and **Т** [т]. Because they are so familiar, you can start reading real Ukrainian words right now. Look at the word **мама** (mother). You already know how to read it — just sound it out: м-а-м-а. Now try **тато** (father): т-а-т-о. Here are more words built from these five letters alone: **кома** (comma), **атом** (atom), **мак** (poppy), **око** (eye). Two small pronunciation notes: Ukrainian **Т** is dental — your tongue touches the back of your upper teeth, not the gum ridge the way it does in English. And both **К** and **Т** are unaspirated — no puff of air follows them. Hold your palm in front of your mouth and say the English word "top" — you feel a burst of air. Now say **тато** without that burst. Close enough for now — awareness matters more than perfection at this stage.

Now for the biggest trap English speakers face: **false friend** letters. These look exactly like Latin letters but make completely different sounds. Memorize these six — they will save you from countless mistakes:

| Letter | Ukrainian sound | English trap | Example word |
|--------|----------------|--------------|-------------|
| **В** | [в] (like "v") | not "b" | **вода** (water) |
| **Н** | [н] (like "n") | not "h" | **ніс** (nose) |
| **Р** | [р] (rolled "r") | not "p" | **рука** (hand) |
| **С** | [с] (like "s") | not "c/k" | **сон** (dream) |
| **У** | [у] (like "oo") | not "y" | **вухо** (ear) |
| **Х** | [х] (like "ch" in Scottish "loch") | not "x" | **хата** (house) |

Your brain will see **В** and scream "b" — fight that instinct. When you see **РЕСТОРАН** on a sign in Kyiv, the **Р** is a rolled "r" and the **С** is an "s." Train your eyes to see Cyrillic, not Latin ghosts.

<!-- INJECT_ACTIVITY: match-false-friends -->

Beyond friendly letters and false friends, Ukrainian has letters with shapes entirely new to English speakers. You do not need to memorize all of them right now — just know they exist and start recognizing them through words. **Б** looks a bit like the number 6 with a hat. **Г** resembles an upside-down L. **Д** looks like a small triangle on legs. **Ж** spreads out like a snowflake. **З** is shaped like the number 3. **Л** looks like a tent. **П** is a doorway. **Ш** is a comb with three teeth. And **Щ** is **Ш** with a small tail — it always makes two sounds [шч]. Read these words to see the new letters in action: **банк** (bank), **дім** (home), **зима** (winter), **книга** (book), **школа** (school).

Four special letters deserve a quick introduction. **Ї** always sounds like [йі] — it never softens the consonant before it. This letter is unique to Ukrainian. You will not find it in Russian, Belarusian, or any other Slavic language — it belongs to Ukrainian alone. You will see it in words like **їжак** (hedgehog) and **Україна** (Ukraine). The letters **Я**, **Ю**, and **Є** serve double duty: at the start of a word or after a vowel, each one represents two sounds ([йа], [йу], [йе]); after a consonant, they soften it instead. The full rules come in the next module — for now, simply recognize these four special letters when you encounter them.

## Привіт! — Hello!

Time for your first Ukrainian conversation. These are informal greetings — use them with friends, family, and people your age or younger. The core phrases:

- **Привіт!** — Hi!
- **Як справи?** — How are you?
- **Добре.** — Fine.
- **Чудово!** — Great!
- **Нормально.** — Okay.
- **А у тебе?** — And you?

Listen for the rhythm when you say these phrases aloud. Ukrainian has a natural melodic rise and fall that differs from English — imitate the music, not just the words.

Here is what a greeting sounds like between two friends meeting on the street:

> **Оленка:** Привіт! *(Hi!)*
> **Тарас:** О, привіт! Як справи? *(Oh, hi! How are you?)*
> **Оленка:** Добре, дякую. А у тебе? *(Fine, thanks. And you?)*
> **Тарас:** Чудово! *(Great!)*
> **Оленка:** Рада тебе бачити! *(Glad to see you! — said by a woman)*

Now imagine Тарас says the same thing back. He would say: **Радий тебе бачити!** Notice the difference? Women say **рада**, men say **радий**. This is your very first encounter with grammatical gender in Ukrainian — the language marks whether the speaker is male or female. This will become a major topic starting in Module 8. For now, just pick the form that matches you: **рада** if you are female, **радий** if you are male.

Let us read **Привіт** letter by letter to see how far you have already come. **П** — a new shape (the doorway). **р** — a false friend (rolled, not "p"). **и** — a new vowel (between English "i" and "ih"). **в** — a false friend (not "b"). **і** — a vowel (like English "ee"). **т** — familiar, but dental. Blend into syllables: При-віт. This single word uses letters from all three groups — friendly, false friends, and new shapes. If you can read **Привіт**, you have already started reading Ukrainian.

<!-- INJECT_ACTIVITY: fill-in-greeting -->

## Читаємо — Reading Practice

Imagine walking through a Ukrainian city. Signs surround you — and you can already read them. Sound out each word letter by letter, then blend into syllables:

- **Аптека** (а-пте-ка) — pharmacy
- **Банк** (банк) — bank
- **Кафе** (ка-фе) — café
- **Метро** (ме-тро) — metro
- **Пошта** (по-шта) — post office
- **Школа** (шко-ла) — school
- **Зупинка** (зу-пин-ка) — bus stop

Notice how many of these words are recognizable from English or other European languages. Ukrainian has plenty of international vocabulary. The spelling follows Ukrainian rules, but the meaning is transparent. You are not starting from zero — you are starting from shared ground.

Now try Ukrainian city names — proper nouns that carry real cultural weight. **Київ** (Ки-їв) — note the **ї**! **Львів** (Льві-в) — note the **ь** softening **Л**. **Одеса** (О-де-са). **Харків** (Хар-ків). **Дніпро** (Дні-про). **Полтава** (Пол-та-ва). These are not just reading exercises — they are real places. **Київ** is the capital. **Львів** is the cultural heart of western Ukraine. Pronouncing these names correctly is a sign of respect.

Now build your first sentences using **Це** (this is). The pattern is simple: **Це** + noun.

- **Це мама.** — This is mom.
- **Це банк.** — This is a bank.
- **Це Київ.** — This is Kyiv.
- **Це школа.** — This is a school.
- **Це аптека.** — This is a pharmacy.

Two question forms unlock conversation: **Що це?** (What is this?) — for things and places, and **Хто це?** (Who is this?) — for people. Try a quick exchange:

> **Що це?** — **Це банк.** *(What is this? — This is a bank.)*
> **Хто це?** — **Це мама.** *(Who is this? — This is mom.)*

Notice the **що/хто** distinction: **що** for objects and places, **хто** for people. Ukrainian distinguishes animate from inanimate from the very start — this is how the language thinks, and now you are beginning to think that way too.

<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->

## Підсумок — Summary

Here is what you learned in this first module. Ukrainian has 33 **літери** (letters) and 38 **звуків** (sounds) — we hear and pronounce sounds, we see and write letters. Sounds split into two families: **голосні** (6 vowel sounds, 10 vowel letters) and **приголосні** (32 consonant sounds). Cyrillic letters fall into three groups for English speakers: friendly ones (**А**, **О**, **К**, **М**, **Т**), false friends (**В**, **Н**, **Р**, **С**, **У**, **Х** — the biggest trap), and new shapes (**Б**, **Г**, **Д**, **Ж**, **Ш**, **Щ**, and more). You learned your first greeting: **Привіт! Як справи?** — **Добре!** You read real Ukrainian words and city names. You formed your first sentences with **Це**. 

Self-check: How many letters in the **абетка**? How many sounds? Why the difference? What are **голосні**? What are **приголосні**? What does **Привіт** mean? How do you answer **Як справи?** 

Next module: Reading Ukrainian — where we dive deeper into how letters combine into syllables.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: sounds-letters-and-hello
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

**Level: A1.1 (Module 1/55) — COMPLETE BEGINNER**

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

**Pronunciation videos (Anna Ohoiko):**
- Overview: https://www.youtube.com/watch?v=ksXIXj7CXwc
- Full playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV
Use these in exercises: reference specific videos, embed WatchAndRepeat activities.


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
