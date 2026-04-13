<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/special-signs.yaml` file for module **3: Special Signs** (a1).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 10 | 10+ | inline + workbook combined |
| Inline (lesson tab) | 4 | 6 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 6 | 9 | extended practice |
| Items per activity | 6 | — | each activity must have at least 6 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 4 inline activities AND at least 6 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** image-to-letter, letter-grid, match-up, watch-and-repeat, quiz, true-false, fill-in, classify
- **Inline priority (preferred):** image-to-letter, match-up, fill-in, quiz, watch-and-repeat
- **Workbook types:** fill-in, match-up, group-sort, anagram, unjumble, quiz, true-false, classify, divide-words, count-syllables, pick-syllables, observe, phrase-table, odd-one-out
- **Workbook priority (preferred):** fill-in, match-up, group-sort, anagram, unjumble
- **FORBIDDEN at this level:** cloze, error-correction, mark-the-words, translate, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, highlight-morphemes, grammar-identify, select

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 4–6 quick checks after key teaching points. Workbook = 6–9 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: odd-one-out-soft-sign -->`
- `<!-- INJECT_ACTIVITY: fill-in-missing-sign -->`
- `<!-- INJECT_ACTIVITY: error-correction-apostrophe -->`
- `<!-- INJECT_ACTIVITY: group-sort-signs -->`
- `<!-- INJECT_ACTIVITY: true-false-voicing -->`
- `<!-- INJECT_ACTIVITY: match-up-voiced-voiceless -->`
- `<!-- INJECT_ACTIVITY: quiz-g-vs-g -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Which consonant does NOT have a soft pair? (Ь can't soften it)
  items: 6
  section: М'який знак
  type: odd-one-out
- focus: 'Add the missing Ь or apostrophe: сім_я, ден_, п_ять'
  items: 6
  section: Апостроф
  type: fill-in
- focus: Find missing apostrophes in words like м'ясо, сім'я, п'ять
  items: 6
  section: Апостроф
  type: error-correction
- focus: 'Sort words into: has Ь / has apostrophe / neither'
  items: 18
  section: Апостроф
  type: group-sort
- focus: 'Match voiced-voiceless pairs: Б↔П, Д↔Т, Г↔Х, Ґ↔К, etc.'
  items: 8
  section: Дзвінкі і глухі
  type: match-up
- focus: Statements about voiced/voiceless rules and non-devoicing
  items: 6
  section: Дзвінкі і глухі
  type: true-false
- focus: 'Г vs Ґ: choose the correct letter for each word'
  items: 6
  section: Вимова українських звуків
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
- м'який (soft) — apostrophe only (NO soft sign! Й is inherently soft)
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

The **м'який знак** (soft sign) looks like a lowercase "b", but it produces absolutely no sound. Instead, it acts solely as a modifier to soften, or palatalize, the consonant that comes right before it. In Ukrainian phonetics, there is a clear three-way distinction for consonants. We have **м'які** (truly soft) consonants, **пом'якшені** (partially softened) consonants which include lip, hissing, and back-tongue sounds, and finally **тверді** (hard) consonants. The soft sign only interacts with specific letters to create those truly soft sounds. You will never hear the soft sign itself. You will only hear what it does to its neighbor.

> **Студент:** Що це? *(What is this?)*
> **Вчитель:** Це **м'який знак**. *(This is a soft sign.)*
> **Студент:** Там звук? *(Is there a sound?)*
> **Вчитель:** Ні, він тихий. *(No, it is quiet.)*

Not every consonant can be softened. There are exactly nine consonants that can be truly softened by the **м'який знак**: **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **Р**, and **ДЗ**. To help students remember these letters, Ukrainian schools use a classic mnemonic phrase: «**ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи**». If you look closely at the capital letters in that funny phrase, you will see the exact nine consonants that can pair with a soft sign. When you pronounce a hard consonant, your tongue rests normally in your mouth. But when you pronounce its soft equivalent, the middle of your tongue presses up against the roof of your mouth. This physical movement creates a distinct feeling.

:::tip
The phrase «**ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи**» is taught to every Ukrainian student in the first grade. Memorize it, and you will always know which consonants can take a soft sign!
:::

Look at some common word-final patterns where the **м'який знак** appears. You will often see the ending **-нь**, like in the word **день** (day), **кінь** (horse), or **осінь** (autumn). Another frequent ending is **-ль**, which you can find in **сіль** (salt) or **біль** (pain). You will also encounter **-ть** in **мить** (moment) and **-зь** in **мазь** (ointment). To practice reading these soft sounds aloud, try pronouncing these broader words: **учитель** (teacher), **батько** (father), and **маленький** (small). Pay attention to how your tongue moves up to soften that final consonant. It takes time for English speakers to master this palatalized movement, so practice slowly.

<!-- INJECT_ACTIVITY: odd-one-out-soft-sign -->

## Апостроф (The Apostrophe)

If the soft sign exists to soften a consonant, the Ukrainian apostrophe (') exists to do the exact opposite. You can think of the apostrophe as the "anti-soft-sign" or a structural "wall" inside a word. Its main function is to keep the preceding consonant strictly hard and force the following iotated vowel (**я**, **ю**, **є**, **ї**) to split into two distinct sounds. A softened word like **пісня** (song) flows together perfectly because the **Н** is soft. But a word with an apostrophe, like **сім'я** (family), is sharply separated. The **М** stays completely hard, and the **я** splits into a clear [й] plus [а] sound. You must clearly hear two parts.

> **Марія:** Це твоя **сім'я**? *(Is this your family?)*
> **Іван:** Так, це моя **сім'я**. *(Yes, this is my family.)*
> **Марія:** Дуже велика! *(Very big!)*
> **Іван:** Так, нас **п'ять**. *(Yes, there are five of us.)*

There is a core spelling rule for the apostrophe in Ukrainian orthography. The apostrophe appears after the labial, or lip, consonants: **б**, **п**, **в**, **м**, and **ф**. It also appears after the trill **р**. It is placed right before the iotated vowels **я**, **ю**, **є**, and **ї**. It is crucial to understand that this is a unique Ukrainian phonetic separator. It serves a very specific phonetic purpose in the Ukrainian language. When you see it, you must pause slightly and pronounce the following vowel fully. It acts as a visual command to maintain hard boundaries.

:::caution
English speakers often forget to pronounce the [й] sound after an apostrophe. Remember that the apostrophe acts as a wall: **м'ясо** is pronounced with a hard [м], followed by [йасо].
:::

Get some essential reading practice using high-frequency apostrophe words. Try reading these aloud, keeping the first part hard: **п'ять** (five), **дев'ять** (nine), **м'ясо** (meat), **м'яч** (ball), and **об'єкт** (object). You should also practice the word **м'який** (soft), which ironically contains an apostrophe to keep the **М** hard, while the **Й** provides the softness at the end. Note that for the English word "animal", Ukrainian uses **тварина**. You must always avoid the Russian cognate "тварь", which is not standard Ukrainian. The apostrophe appears frequently in borrowed words too, such as **комп'ютер** (computer), functioning exactly the same way.

<!-- INJECT_ACTIVITY: fill-in-missing-sign -->
<!-- INJECT_ACTIVITY: error-correction-apostrophe -->
<!-- INJECT_ACTIVITY: group-sort-signs -->

## Дзвінкі і глухі (Voiced and Voiceless)

Ukrainian consonants are strictly divided into voiced and voiceless pairs. The physical concept is simple: voiced consonants use your vocal cords, while voiceless ones do not. You can test this using the "hands-on-ears" vibration test. Cover your ears with your hands and say the sound [з]. You will immediately feel a vibration. Now say [с]. The vibration stops completely. There are eight primary voiced-voiceless pairs in Ukrainian: **Б-П**, **Д-Т**, **Г-Х**, **Ґ-К**, **З-С**, **Ж-Ш**, **ДЗ-Ц**, and **ДЖ-Ч**. Learning these pairs is vital for clear pronunciation. It also helps you spell correctly when you hear a new word for the first time.

> **Анна:** Це **дуб**? *(Is this an oak?)*
> **Петро:** Так, старий **дуб**. *(Yes, an old oak.)*
> **Анна:** Він там? *(Is it there?)*
> **Петро:** Ні, **дуб** тут. *(No, the oak is here.)*

A defining feature of Ukrainian phonetics is the concept of non-devoicing. In many other languages, voiced consonants lose their voice at the very end of a word. But in Ukrainian, voiced consonants mostly keep their full voiced sound at the end of a word or before voiceless consonants. For example, the word **дуб** (oak) is pronounced exactly as it is written, with a strong [б] at the end. The word **мороз** (frost) is pronounced with a clear [з] at the end. There is one rare exception to remember: the word **легко** (easily) is pronounced [лехко]. Otherwise, trust the spelling and always keep your voice active.

:::note
Unlike English or German, Ukrainian strongly preserves voicing at the end of words. A final **Б** remains a clear **Б**, never turning into a **П**. This gives Ukrainian its characteristic resonant sound.
:::

Understanding voicing is critical because it changes the meaning of words entirely. We can use minimal pairs for ear training to demonstrate this concept. Listen to the difference between **балка** (beam) and **палка** (stick). The only difference is the voicing of the first consonant. Similarly, contrast **коза** (goat) and **коса** (braid). If you accidentally turn that voiced **З** into a voiceless **С**, you will be talking about a braid of hair instead of a farm animal! Practice saying these pairs aloud while covering your ears to ensure the vibration is there.

<!-- INJECT_ACTIVITY: true-false-voicing -->

## Вимова українських звуків (Pronouncing Ukrainian Sounds)

We must focus intensely on the unique Ukrainian vowel **И** [и]. This sound does not exist in English, and it is a common stumbling block for learners. It is entirely distinct from the vowel **І** [і], which sounds like the "ee" in "feet". The sound **И** is deeper and slightly lower in the mouth. We can use minimal pairs to train the ear to hear this crucial difference. Listen to **бик** (bull) versus **бік** (side). Compare **дим** (smoke) with **дім** (house). Contrast **лист** (leaf or letter) against **ліс** (forest). Finally, hear the difference between **кит** (whale) and **кіт** (cat). Mixing these up causes major confusion.

> **Олена:** Це **кіт** чи **кит**? *(Is this a cat or a whale?)*
> **Максим:** Це маленький **кіт**. *(This is a small cat.)*
> **Олена:** Дуже **гарно**! *(Very nicely!)*

Next, we must contrast the letters **Г** and **Ґ**. They look similar, but they are two different letters representing two completely different sounds. The letter **Г** [ɦ] is a voiced fricative. This means air flows continuously through your narrowed throat, creating a soft, breathy sound. Practice this sound in words like **гарно** (nicely, beautifully), **гора** (mountain), and **голова** (head). Its voiceless partner is **Х**. If you say **Х** and add voice, you get **Г**. Do not call **Г** "soft", because in Ukrainian phonetics, **м'який** means palatalized. The letter **Ґ** [g], on the other hand, is a voiced stop. You close your throat fully and release the air, like in **ґанок** (porch) or **ґудзик** (button). Its voiceless partner is **К**.

Finally, practice the Ukrainian rolled or trilled **Р** [р]. This sound requires the tip of your tongue to vibrate rapidly against the roof of your mouth. Practice this trill with words like **рука** (hand or arm), **робота** (work), **ранок** (morning), and **риба** (fish). Many learners worry intensely about perfecting this trill immediately. Reassure yourself: while getting the trill is a great goal, an imperfect **Р** will always be understood by native speakers. Focus on getting comfortable with the language first. You will naturally develop the tongue strength over time.

<!-- INJECT_ACTIVITY: match-up-voiced-voiceless -->
<!-- INJECT_ACTIVITY: quiz-g-vs-g -->

## Підсумок — Summary

Review the fundamental phonetic tools we have covered. What does the **м'який знак** (Ь) do? It acts as a modifier that softens, or palatalizes, the preceding consonant, but it makes absolutely no sound of its own. It is a silent instruction for your tongue to move upward. After which letters does the apostrophe appear? It appears after the labial consonants **б**, **п**, **в**, **м**, **ф**, and the trill **р**, right before the iotated vowels **я**, **ю**, **є**, **ї**. It keeps the consonant completely hard and splits the vowel into two sounds. Can you name three voiced-voiceless pairs? You can use the hands-on-ears vibration test to find them, such as **Б-П**, **Д-Т**, and **З-С**. How is Ukrainian **Г** different from **Ґ**? The letter **Г** is a continuous, breathy voiced fricative that flows through the narrowed throat, while **Ґ** is a hard voiced stop that strictly blocks and releases air. To finish, read these words out loud, paying close attention to the signs and sounds we have practiced today: **сім'я**, **день**, **п'ять**, **гарно**, and **риба**. Understanding these special signs will make your pronunciation authentic and clear.
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: special-signs
level: a1

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (10 total / 4–6 inline / 6–9 workbook,
# 6+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 6 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 6 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 6 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 6 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 6 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 6 pairs total

  - id: group-sort-gender
    type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Чоловічий рід"
        items: ["стіл", "олівець", "будинок"]   # ≥ 3 items per group
      - label: "Жіночий рід"
        items: ["книга", "ручка", "школа"]
      - label: "Середній рід"
        items: ["вікно", "море", "молоко"]

  - id: true-false-grammar
    type: true-false
    instruction: "Правда чи ні?"
    items:                     # ← real output: ≥ 6 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 6 items total

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

  - type: order
    instruction: "Розставте речення в правильному порядку"
    items:                         # Lines displayed SHUFFLED to the learner
      - "— Служба порятунку, слухаю вас."
      - "— Допоможіть! Тут пожежа!"
      - "— Де ви?"
    correct_order: [0, 1, 2]       # TOP-LEVEL field, zero-based indices into items[]

  - type: unjumble
    instruction: "Складіть правильне речення зі слів"
    items:
      - words: ["швидку!", "Викличте"]            # Jumbled words
        correct_order: ["Викличте", "швидку!"]    # Words as STRINGS in correct order (NOT integers!)
      - words: ["потрібен", "Мені", "лікар."]
        correct_order: ["Мені", "потрібен", "лікар."]
        hint: "Dative + потрібен + noun"

  - type: error-correction
    instruction: "Знайдіть і виправте помилку"
    items:
      - sentence: "Мені потрібна лікар."
        error: "потрібна"
        correction: "потрібен"
        error_type: "word"           # MUST be one of: "word", "phrase", "register", "construction"
        options: ["потрібен", "потрібне", "потрібно"]
        explanation: "Лікар is masculine, so потрібен."
```

---

## Activity Type Reference

**CRITICAL RULE: EVERY single activity object MUST include an `id` field (a unique string like "quiz-grammar", "match-up-vocab"). Do NOT generate an activity without an `id`.**

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: id, instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]. **CRITICAL: use `____` (four underscores) for the blank, NOT `{word}` curly-brace syntax. Example: `sentence: "Це ____ кімната."` with `answer: "моя"`. The validator REJECTS `{word}` format.**
- **match-up**: Pair matching. Required: id, instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: id, instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: id, instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: id, instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: id, instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: id, instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: id, instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: id, examples[], prompt
- **classify**: Multi-category sort. Required: id, instruction, categories[{label, items[]}]

### Ukrainian pedagogy types (A1 phonetics/syllables):
- **divide-words**: Interactive syllable division. Required: id, instruction, items[{word, answer}]. Optional: hint. Example: word: "молоко", answer: "мо-ло-ко"
- **count-syllables**: Count syllables in a word. Required: id, items[{word, correct}]. Optional: instruction, maxCount, translation. Example: word: "яблуко", correct: 3
- **pick-syllables**: Select syllables matching criteria. Required: id, syllables[], correctIndices[], category. Example: syllables: ["ка", "май", "ре"], correctIndices: [1], category: "закриті"
- **odd-one-out**: Find the word that doesn't belong. Required: id, items[{words[], correct, explanation}]. `correct` is 0-based index. Example: words: ["кіт", "пес", "молоко"], correct: 2, explanation: "молоко — 3 syllables, rest have 1"
- **image-to-letter**: See image/emoji, identify letter. Required: id, instruction, items[{image, letter}]. Optional: options[]
- **letter-grid**: Letter reference grid. Required: id, letters[{upper, lower}]. Optional: name, emoji, key_word, sound_type
- **watch-and-repeat**: Watch video, repeat pronunciation. Required: id, items[{video}]. Optional: letter, word, note
- **phrase-table**: Grouped phrases for communication patterns. Required: id, groups[{label, phrases[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: id, prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Required: id, passage, questions[]
- **source-evaluation**: Required: id, source_text, criteria[], guiding_questions[]

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
- divide-words: split words into syllables (складоподіл)
- count-syllables: count syllables by counting vowels
- pick-syllables: select open/closed syllables
- odd-one-out: find the word that doesn't belong
- watch-and-repeat: pronunciation video practice
- translate: single words/short phrases English→Ukrainian (multiple choice)
- error-correction: find simple errors (gender agreement, missing ь)

**DO NOT use:** cloze, mark-the-words, select, essay-response, unjumble (learner can't construct Ukrainian sentences yet).


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-sounds-letters [§4.1.1, §4.1.4]
**Звуки і літери** (Sounds and letters)
- **quiz** — Звук чи літера?: Розрізнити звук і літеру — основа української фонетики / Distinguish звук from літера — fundamental Ukrainian phonetics distinction
  - Instruction: *Оберіть правильну відповідь*
- **match-up** — Літера → Звук: Зіставити літери зі звуковими значеннями, особливо багатозвучні (я, ю, є, ї) / Match letters to their sound values, especially multi-sound letters (я, ю, є, ї)
  - Instruction: *З'єднайте літеру зі звуком*
- **group-sort** — Голосні й приголосні: Розподілити звуки на голосні та приголосні / Sort letters/sounds into голосні (vowel) vs приголосні (consonant)
  - Instruction: *Розподіліть звуки*
- **image-to-letter** — Знайди літеру: Побачити зображення, визначити українську літеру / See image, identify the Ukrainian letter it starts with
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує фонетичні знання
- ❌ fill-in-no-options: Занадто складно для A1 — початківці потребують варіантів відповідей

### Pattern: phonetics-soft-hard [§4.1.2, §4.1.3]
**М'який знак і апостроф** (Soft sign and apostrophe)
- **group-sort** — М'який чи твердий?: Розподілити приголосні/слова за м'якістю чи твердістю вимови / Sort consonants/words by soft vs hard pronunciation
  - Instruction: *Розподіліть*
- **quiz** — Де потрібен ь?: Обрати слово, де потрібен м'який знак / Choose which word needs м'який знак
- **error-correction** — Виправ помилку: Знайти, де м'який знак або апостроф пропущено або вжито неправильно / Find where м'який знак or апостроф is missing/wrong
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Занадто складно для A1 без варіантів

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

### Pattern: grammar-pronouns [§4.2.1.4, §4.2.2]
**Особові займенники** (Personal pronouns)
- **match-up** — Займенник → дієслово: Зіставити особовий займенник із правильною формою дієслова — зв'язок займенника з дієвідмінюванням / Match personal pronoun with correct verb form — linking pronouns to conjugation
  - Instruction: *З'єднайте займенник із дієсловом*
- **fill-in** — Вставте займенник: Обрати правильний займенник за контекстом речення / Choose the correct pronoun based on sentence context
  - Instruction: *Вставте правильний займенник*
- **group-sort** — Однина чи множина?: Розподілити займенники на однину та множину / Sort pronouns into singular and plural
  - Instruction: *Розподіліть*
- **quiz** — Ти чи Ви?: Обрати правильну форму звертання — неформальне (ти) чи ввічливе (Ви) / Choose correct address form — informal (ти) vs polite (Ви)
**Anti-patterns (DO NOT generate):**
- ❌ translate: Займенники — про зв'язок з дієсловом, а не переклад

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 10 activities.** Inline: 4–6. Workbook: 6–9. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 6 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 6.
- **Lower minimums for specific types only:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items, essay-response/critical-analysis = 1 prompt.
- If you can't think of enough items, add more examples from the module's vocabulary and content. NEVER ship a 1-item or 2-item activity unless its type cap explicitly allows it.
- **Exactly 4 options per quiz question at A2+** — enough to prevent guessing, not so many to overwhelm. A1 allows 3-4.
- **BINARY CONCEPTS (e.g., НВ/ДВ, masculine/feminine, true/false):** Do NOT use `quiz` with only 2 options — use `true-false` (for statement evaluation) or `group-sort` (for categorization) instead. Quiz type requires 4 options at A2+.

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
- `mcp_rag_verify_words` / `mcp_rag_verify_word` / `mcp_rag_verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp_rag_search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp_rag_search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp_rag_query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp_rag_query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp_rag_search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp_rag_query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp_rag_search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp_rag_search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp_rag_search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp_rag_search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp_rag_translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp_rag_query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp_rag_query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp_rag_search_style_guide` first (it knows calques). Then `mcp_rag_query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp_rag_verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp_rag_query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp_rag_verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp_rag_search_idioms` for Ukrainian expressions, `mcp_rag_search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp_rag_query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp_rag_query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp_rag_verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp_rag_verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp_rag_verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp_rag_query_pravopys` or `mcp_rag_search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp_rag_verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 10-20 tool calls per module** (was 8-15; mandatory checks added).

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **at least 4** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 6** workbook activities.
- [ ] **Total ≥ 10.**
- [ ] **Every** activity has **at least 6** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 4 and 6. I did NOT create more injection markers than 6.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
