<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/special-signs.yaml` file for module **3: Special Signs** (a1).

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

- `<!-- INJECT_ACTIVITY: odd-one-out -->`
- `<!-- INJECT_ACTIVITY: fill-in-soft-or-apostrophe -->`
- `<!-- INJECT_ACTIVITY: error-correction-apostrophe -->`
- `<!-- INJECT_ACTIVITY: group-sort-soft-apostrophe -->`
- `<!-- INJECT_ACTIVITY: match-voiced-voiceless -->`
- `<!-- INJECT_ACTIVITY: true-false-voicing -->`
- `<!-- INJECT_ACTIVITY: quiz-g-vs-gx -->`

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

Every Ukrainian word you have read so far has been built from letters that represent sounds. Now meet a letter that breaks that rule: **Ь** — the soft sign, or **знак м'якшення**. It has no sound of its own. Zero. Its only job is to change how the consonant before it is pronounced — making it soft. Consider the difference: **лук** (onion) and **люк** (hatch) are two completely different words, and the only difference is softness. The letter **Ь** marks that softness in writing. One letter, one job, zero sounds. Look at **сіль** (salt) — the **Л** is soft because of the **Ь**. Look at **день** (day) — the **Н** is soft. The consonant changes; the **Ь** itself stays silent.

Ukrainian textbooks teach a three-way system for consonants. Not every consonant can be softened with **Ь** — only a specific group. Here is the full picture from Авраменко (Grade 5) and Большакова (Grade 2):

1. **М'які приголосні** (truly soft consonants) — exactly 8 consonants can take **Ь** to become fully soft: **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **ДЗ**. The letter **Й** is inherently soft — it never needs **Ь**. These are the consonants you will see **Ь** after in standard Ukrainian spelling.

2. **Пом'якшені приголосні** (partially softened consonants) — the labials (**Б**, **П**, **В**, **М**, **Ф**), the hushing consonants (**Ж**, **Ш**, **Ч**, **ДЖ**), and the back-tongue consonants (**К**, **Ґ**, **Г**, **Х**) can only be softened by following soft vowels like **і**, **я**, **ю**, **є**. You will **never** see **Ь** after these letters.

3. **Тверді приголосні** (hard consonants) — always hard, never softened at all.

Ukrainian schoolbooks use a simple notation from Захарійчук (Grade 1, p.15): hard consonants are marked [–], soft consonants are marked [=].

:::tip Mnemonic
Літвінова (Grade 5) gives students a phrase to remember which consonants take **Ь**: **«ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи»** — the capital letters encode exactly the 8 consonants: **ДЗ**, **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**. If a consonant is not in this phrase, **Ь** does not follow it.
:::

Common spelling patterns with **Ь**: words ending in **-нь** like **день** (day), **кінь** (horse), **осінь** (autumn); words ending in **-ль** like **сіль** (salt), **біль** (pain); words ending in **-ть** like **мить** (moment); and words ending in **-зь** like **мазь** (ointment). Practice reading these words with **Ь**: **учитель** (teacher) — **Ь** after **Л** at the end; **батько** (father) — **Ь** after **Т** before **К**; **маленький** (small) — **Ь** after **Н** before **К**.

<!-- INJECT_ACTIVITY: odd-one-out -->

## Апостроф (The Apostrophe)

The apostrophe in Ukrainian is not a letter — it is a separator sign. It does the opposite of **Ь**: instead of softening a consonant, it keeps the consonant **hard** and splits the following vowel into two sounds.

The rule comes straight from Захарійчук (Grade 1, p.97): the apostrophe appears after the consonants **б**, **п**, **в**, **м**, **ф**, **р** — and before the vowels **я**, **ю**, **є**, **ї**. When you see this combination, the consonant stays hard, and the vowel splits into **[й]** plus a vowel sound — two sounds instead of one. Without the apostrophe, the consonant would simply soften into the following vowel.

Compare what happens with and without an apostrophe. In **пісня** (song), the **Н** softens smoothly into the vowel — one flowing sound. But in **м'ясо** (meat), the **М** stays hard, and the **я** splits into two sounds: **й** + **а**. You can hear the separation. Walk through the core examples:

- **сім'я** (family) — **М** hard, then й + а
- **м'ясо** (meat) — **М** hard, then й + а
- **п'ять** (five) — **П** hard, then й + а
- **комп'ютер** (computer) — **П** hard, then й + у. A familiar cognate that anchors the rule perfectly.

Two more: **дев'ять** (nine) — **В** hard, then й + а. And **м'який** (soft) — this word has an apostrophe only, with no **Ь**, because **Й** is inherently soft and never needs a soft sign.

:::note Scope
Words like **під'їзд** and **з'їзд** also have apostrophes, but they follow a different rule — the prefix rule, where a prefix ending in a consonant separates from **ї**. That rule comes at A2. For now, focus only on the labial rule: **б**, **п**, **в**, **м**, **ф**, **р** + **я**, **ю**, **є**, **ї**.
:::

Reading practice from the textbooks (Кравцова Grade 2, Большакова Grade 1): **п'ять**, **дев'ять**, **м'яч** (ball), **м'який**, **сім'я**, **м'ясо**, **комп'ютер**, **ім'я** (name), **здоров'я** (health), **пір'я** (feathers).

<!-- INJECT_ACTIVITY: fill-in-soft-or-apostrophe -->

<!-- INJECT_ACTIVITY: error-correction-apostrophe -->

<!-- INJECT_ACTIVITY: group-sort-soft-apostrophe -->

## Дзвінкі і глухі (Voiced and Voiceless)

Place your fingers lightly on your throat. Say **з** — you feel vibration. That vibration is your voice. Now say **с** — silence. The sound is there, but the voice is gone. This is the difference between **дзвінкі** (voiced) and **глухі** (voiceless) consonants. The difference is the **голос** (voice).

Ukrainian has 8 voiced-voiceless pairs. Here they are, directly from Большакова (Grade 2, p.62):

| Дзвінкі (voiced) | Б | Д | Г | Ґ | З | Ж | ДЗ | ДЖ |
|---|---|---|---|---|---|---|---|---|
| **Глухі (voiceless)** | **П** | **Т** | **Х** | **К** | **С** | **Ш** | **Ц** | **Ч** |

There is also a group called **сонорні** — **В**, **Л**, **М**, **Н**, **Й**, **Р** — that have no voiceless partner. They sit outside the paired system entirely.

:::caution Non-devoicing — a defining Ukrainian feature
In many languages (German, Russian), voiced consonants lose their voice at the end of a word. Ukrainian does **not** do this. The word **дуб** (oak) is pronounced [дуб] — not [дуп]. The word **мороз** (frost) is [мороз] — not [морос]. Also: **гриб** (mushroom) is [гриб], **наказ** (order) is [наказ]. If your first language devoices final consonants, you need to consciously hold the voice all the way through. One well-known exception: **легко** (easily) is pronounced [лехко]. But exceptions prove the rule — Ukrainian voiced consonants stay voiced.
:::

Textbook pairs from Большакова (Grade 2, p.62) show how voicing changes meaning: **жабка** (frog, diminutive) vs **шапка** (hat), **злива** (downpour) vs **слива** (plum), **ґава** (crow) vs **кава** (coffee), **казка** (fairy tale) vs **каска** (helmet).

Minimal pairs for ear training: **балка** (beam) vs **палка** (stick), **коза** (goat) vs **коса** (braid), **зуб** (tooth) vs **суп** (soup), **жар** (heat) vs **шар** (sphere). Say each pair aloud. Feel whether the first consonant vibrates.

<!-- INJECT_ACTIVITY: match-voiced-voiceless -->

<!-- INJECT_ACTIVITY: true-false-voicing -->

## Вимова українських звуків (Pronouncing Ukrainian Sounds)

### И vs І

Ukrainian has a vowel that exists on its own terms: **И**. It is not the same as **І**. The difference between these two sounds changes meaning completely. Four minimal pairs from the cover of Большакова's Grade 1 textbook:

- **бик** (bull) vs **бік** (side)
- **дим** (smoke) vs **дім** (house)
- **лист** (leaf, letter) vs **ліс** (forest)
- **кит** (whale) vs **кіт** (cat)

These are not subtle differences — **кит** and **кіт** are completely different words. **И** sits in a mid-tongue position, between **І** and **Е**. It is a distinctly Ukrainian sound. Drill these pairs aloud: **дим** — **дім** — **бик** — **бік** — **кит** — **кіт**. Watch the pronunciation video for **И** and let your ear learn the distinction directly.

### Г vs Ґ

Two separate letters, two separate sounds. **Г** is a voiced fricative — air flows through a narrowed throat, creating turbulence, but the throat never fully closes. Its voiceless partner is **Х**. Pronounce **Х**, then add voice — that is **Г**. Words: **гарно** (beautifully), **гора** (mountain), **голова** (head).

**Ґ** is a voiced stop — full throat closure, then an abrupt release. Its voiceless partner is **К**. Pronounce **К**, then add voice — that is **Ґ**. Words: **ґанок** (porch), **ґудзик** (button). As Літвінова (Grade 5, p.133) states: both sounds are native Ukrainian. **Ґ** is an important part of Ukrainian phonetic identity.

:::caution Terminology
Do **not** describe **Г** as "soft." In Ukrainian phonetics, **м'який** means palatalized — and **Г** is not palatalized. **Г** is a fricative. **Ґ** is a stop. These are different manners of articulation, not hard vs. soft.
:::

An interesting pair: **ґрати** (iron bars, noun) vs **грати** (to play, verb) — same spelling pattern, different first letter, completely different meaning.

### Р

The Ukrainian **Р** is trilled — the tongue tip vibrates against the ridge behind the upper teeth. Practice words: **рука** (hand), **робота** (work), **ранок** (morning), **риба** (fish). Watch the pronunciation video for **Р**. An imperfect **Р** is always understood by native speakers — focus on getting comfortable, not perfect.

<!-- INJECT_ACTIVITY: quiz-g-vs-gx -->

## Підсумок — Summary

Four new pieces of the Ukrainian sound system, each with a clear function: **Ь** softens the consonant before it (and has no sound of its own). The apostrophe keeps a consonant hard and splits the following vowel into two sounds. Voiced and voiceless consonants form 8 pairs — and Ukrainian keeps voiced consonants voiced at word end, unlike many other languages. **И**, **Г**, and **Р** are sounds with no direct English equivalent, built into Ukrainian on its own terms.

**Self-check** — answer these before moving on:

- **What does Ь do?** → It softens the consonant before it. It has no sound of its own.
- **After which 8 consonants can Ь appear?** → **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **ДЗ**. Mnemonic: **«ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи»**.
- **After which letters does the apostrophe appear?** → After **б**, **п**, **в**, **м**, **ф**, **р** — before **я**, **ю**, **є**, **ї**.
- **Name 3 voiced-voiceless pairs.** → **Б–П**, **Д–Т**, **З–С** (any three from the eight).
- **Does Ukrainian «дуб» sound like [дуб] or [дуп]?** → [дуб] — Ukrainian does not devoice at word end.
- **How is Г different from Ґ?** → **Г** is a voiced fricative (air flows through, like **Х** with voice). **Ґ** is a voiced stop (full closure then release, like **К** with voice).
- **Read these words aloud:** **сім'я**, **день**, **п'ять**, **гарно**, **риба**, **ґудзик**.

## Summary

This module covered four building blocks of Ukrainian phonetics. The **soft sign (Ь)** silently modifies 8 consonants — remember the mnemonic **«ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи»**. The **apostrophe** does the opposite — it keeps consonants hard after **б**, **п**, **в**, **м**, **ф**, **р** and splits the following vowel. **Voiced-voiceless pairs** work differently in Ukrainian than in many languages: voiced consonants stay voiced at word end. And three sounds — **И**, **Г**, **Р** — are distinctly Ukrainian, with no shortcuts through English. Next: **stress and melody** — how Ukrainian uses **наголос** (stress) to shape meaning and rhythm.

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

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: examples[], prompt
- **classify**: Multi-category sort. Required: instruction, categories[{label, items[]}]

### Ukrainian pedagogy types (A1 phonetics/syllables):
- **divide-words**: Interactive syllable division. Required: instruction, items[{word, answer}]. Optional: hint. Example: word: "молоко", answer: "мо-ло-ко"
- **count-syllables**: Count syllables in a word. Required: items[{word, correct}]. Optional: instruction, maxCount, translation. Example: word: "яблуко", correct: 3
- **pick-syllables**: Select syllables matching criteria. Required: syllables[], correctIndices[], category. Example: syllables: ["ка", "май", "ре"], correctIndices: [1], category: "закриті"
- **odd-one-out**: Find the word that doesn't belong. Required: items[{words[], correct, explanation}]. `correct` is 0-based index. Example: words: ["кіт", "пес", "молоко"], correct: 2, explanation: "молоко — 3 syllables, rest have 1"
- **image-to-letter**: See image/emoji, identify letter. Required: instruction, items[{image, letter}]. Optional: options[]
- **letter-grid**: Letter reference grid. Required: letters[{upper, lower}]. Optional: name, emoji, key_word, sound_type
- **watch-and-repeat**: Watch video, repeat pronunciation. Required: items[{video}]. Optional: letter, word, note
- **phrase-table**: Grouped phrases for communication patterns. Required: groups[{label, phrases[]}]

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

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Default minimum: 6 items per activity.** Quiz = 6+, fill-in = 6+, match-up = 6+ pairs, true-false = 6+, anagram = 6+, error-correction = 6+, translate = 6+, divide-words = 6+, count-syllables = 6+, odd-one-out = 6+.
- **Lower minimums for specific types:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items.
- If you can't think of enough items, add more examples from the module's vocabulary and content.
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
