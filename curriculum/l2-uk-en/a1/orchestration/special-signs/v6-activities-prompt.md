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

- `<!-- INJECT_ACTIVITY: odd-one-out-softening -->`
- `<!-- INJECT_ACTIVITY: fill-in-special-signs -->`
- `<!-- INJECT_ACTIVITY: error-correction-apostrophe -->`
- `<!-- INJECT_ACTIVITY: group-sort-signs -->`
- `<!-- INJECT_ACTIVITY: true-false-devoicing -->`
- `<!-- INJECT_ACTIVITY: quiz-g-vs-ge -->`
- `<!-- INJECT_ACTIVITY: match-up-voiced-voiceless -->`

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

> **Оленка:** Хто це там? *(Who is that there?)*
> **Тарас:** Це батько. *(This is a father.)*
> **Оленка:** А там учитель? *(And is a teacher there?)*
> **Тарас:** Так, там учитель. *(Yes, a teacher is there.)*

The soft sign — written as **Ь** — is unique because it is entirely silent. It has no sound of its own, but it acts as a very specific instruction for your tongue. Its only job is to change the quality of the consonant that comes immediately before it, making it soft, or palatalized. When you see this sign, you press the middle of your tongue up toward the roof of your mouth while pronouncing the consonant. For example, look at the word **день** (day). The letter **Н** usually sounds like a firm English "n". But the soft sign at the end tells you to soften it into a delicate, almost airy sound. You can hear this same softening effect in the word **сіль** (salt), where the hard **Л** becomes light and lifted. The soft sign is a crucial part of Ukrainian phonetics. Without it, you cannot pronounce words correctly.

In Ukrainian phonetics, there is a three-way distinction: consonants can be truly soft (**м'які**), partially softened (**пом'якшені**), or hard (**тверді**). The soft sign creates truly soft sounds. However, there is a specific, closed group of consonants that can take the soft sign. Ukrainian students memorize these letters using a famous phrase: **«ДЗіДЗьо, Де Ти З’їСи Ці ЛиНи»** (Dzidzio, where will you eat these tench fish?). This phrase contains exactly the nine consonants that can be truly softened: **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **Р**, and **ДЗ**. You will never see a soft sign after labial, sibilant, or velar consonants, which can only be partially softened. To help young learners visualize this, textbooks like *Захарійчук Grade 1* use a special notation. A hard consonant is marked with a single dash **[–]**, and a soft consonant is marked with a double dash **[=]**.

:::tip
The mnemonic **«ДЗіДЗьо, Де Ти З’їСи Ці ЛиНи»** is taught to every Ukrainian first grader. Memorizing this funny phrase about eating tench fish is the fastest way to know exactly which consonants can take a soft sign.
:::

The soft sign is not restricted to the end of a word; it frequently appears right in the middle. Common structural patterns include **-нь** as in **день** (day) or **осінь** (autumn), **-ль** as in **сіль** (salt) or **біль** (pain), **-ть** as in **мить** (moment), and **-зь** as in **мазь** (ointment). When it sits inside a word, it softens the preceding consonant before the next sound begins. A classic example is the word **батько** (father). The soft sign sits right after the **Т**, making it soft before you pronounce the hard **К**. You will also see this pattern in professional titles, such as **учитель** (teacher), and very commonly in adjectives, like **маленький** (small). It is also important to know that the Ukrainian letter **Й** is inherently soft by its very nature and never needs a soft sign next to it. 

To truly understand the power of the soft sign, we must look at how it changes the actual meaning of words. In Ukrainian, a hard consonant and a soft consonant are treated as two entirely different sounds. Consider the minimal pair of **брат** (brother) and the short infinitive verb form **брать** (to take). In **брат**, your tongue taps sharply against your teeth for a hard [т]. But in **брать**, the soft sign instructs you to lift the middle of your tongue, creating a soft [т']. That single physical shift in your mouth completely changes what you are saying. Palatalization is a structural pillar of the language.

<!-- INJECT_ACTIVITY: odd-one-out-softening -->

## Апостроф (The Apostrophe)

> **Тато:** Це наша сім'я. *(This is our family.)*
> **Син:** М'ясо тут? *(Is the meat here?)*
> **Тато:** Так, м'ясо тут. *(Yes, the meat is here.)*

If the soft sign is a gentle instruction to soften a sound, the apostrophe — written as **’** — acts as a solid brick wall. The apostrophe performs the exact opposite function of the soft sign. It is a strict separator. When you see an apostrophe in a Ukrainian word, it commands you to keep the preceding consonant absolutely hard. Simultaneously, it forces the vowel that follows it to break apart and be pronounced as two completely distinct sounds: a clear **[й]** sound followed by the vowel. It creates a physical pause, a sharp phonetic boundary that you must respect.

But where does this wall appear? According to the standard orthography (*Захарійчук Grade 1*, p.97), the apostrophe is placed after the labial consonants **Б**, **П**, **В**, **М**, **Ф**, and the letter **Р**. It appears only when these consonants are followed by the iotated vowels **Я**, **Ю**, **Є**, or **Ї**. Without an apostrophe, a consonant softens naturally before these vowels, as in **пісня** (song), where the **Н** is soft. With the apostrophe, the consonant stays hard, and the vowel equals two sounds. A perfect example is the word **сім'я** (family). Because of the apostrophe, the **М** remains completely hard, and the **Я** splits into its full **[йа]** sound. You pronounce it as **[сім-йа]**, distinctly separating the syllables.

This strict separation is crucial for many high-frequency words that you will use every day. Consider the word **м'ясо** (meat). English speakers often make the mistake of softening the **М**, blending it into a mushy sound. But the apostrophe forbids this. You must say **[м-йасо]**, keeping the labial consonant firm. The same applies to the adjective **м'який** (soft) — notice that it contains an apostrophe, but absolutely no soft sign, because the **Й** is inherently soft. The strict separation also applies to numbers. When you say **п'ять** (five), you must clearly articulate **[п-йать]**. When you say **дев'ять** (nine), the **В** stays hard before the **Я**. Practicing this firm separation will immediately make your Ukrainian sound authentic.

This spelling rule is so deeply embedded in Ukrainian phonetics that it also applies to modern loanwords and international vocabulary. Whenever a foreign word contains a labial consonant followed by a "yu" or "ya" sound, Ukrainian spelling enforces the apostrophe to maintain the hard consonant. You will see this clearly in words like **комп'ютер** (computer) and **об'єкт** (object). The apostrophe is an active, consistent rule that shapes how the language absorbs new concepts.

:::caution
At this early stage, you are learning the "Lip Consonant" rule for the apostrophe. Later, you will also learn that the apostrophe appears after prefixes, such as in words like **з'їзд** (congress) or **під'їзд** (entrance). For now, focus only on the core labial letters!
:::

<!-- INJECT_ACTIVITY: fill-in-special-signs -->
<!-- INJECT_ACTIVITY: error-correction-apostrophe -->
<!-- INJECT_ACTIVITY: group-sort-signs -->

## Дзвінкі і глухі (Voiced and Voiceless)

> **Анна:** Це великий дуб? *(Is this a big oak tree?)*
> **Марко:** Так, це старий дуб. *(Yes, this is an old oak tree.)*
> **Анна:** А там коза? *(And is a goat there?)*
> **Марко:** Ні, там коса. *(No, a braid is there.)*

Ukrainian consonants have their own distinct personalities, and they often come in pairs. These pairs are categorized by how they are produced in your throat: they are either voiced (**дзвінкі**) or voiceless (**глухі**). There is a very simple physical test to understand this difference. Cover your ears with your hands (закрий долонями вуха). Now, make a strong **[б]** sound. You will hear a distinct vibration — your vocal cords are engaged, making it a voiced consonant. Now, make a **[п]** sound. The vibration stops completely. You are using the exact same lip position, but only pushing air. That makes it a voiceless consonant.

:::note
The "hands on ears" test is a perfect physical tool for learning pronunciation. If you hear a buzz, the sound is voiced. If you only hear air leaving your mouth, the sound is voiceless.
:::

This vibration test defines the eight main voiced-voiceless pairs in the Ukrainian language. They are: **Б-П**, **Д-Т**, **Г-Х**, **Ґ-К**, **З-С**, **Ж-Ш**, **ДЗ-Ц**, and **ДЖ-Ч**. Learning these partners is essential for mastering spelling and pronunciation. However, not every consonant has a partner. There is a special group of sounds called sonorants (**сонорні**), which include **В**, **Л**, **М**, **Н**, **Й**, and **Р**. These are highly resonant, musical sounds. They flow smoothly and do not have voiceless equivalents in Ukrainian.

One of the most defining and beautiful features of Ukrainian phonetics is its "Resilience Rule." In many languages, voiced consonants lose their voice and become weak when they sit at the very end of a word. Ukrainian strictly forbids this. Voiced consonants **переважно** (mostly) keep their sound, no matter where they appear. When you say **дуб** (oak tree), you must clearly pronounce the strong **[дуб]** at the end. When you say **мороз** (frost), the final **[з]** must vibrate clearly. There is only one common exception to this rule of resilience: the word **легко** (easily), which is pronounced as **[лехко]**.

This resilience is not just an aesthetic preference; it is absolutely necessary for meaning. Because Ukrainian preserves final voicing, minimal pairs sound distinctly different. Listen carefully to the difference between **балка** (beam) and **палка** (stick). The only difference is the vibration in your throat. Similarly, the vibration is the only thing separating **коза** (goat) from **коса** (braid). Ear training with these pairs is vital.

<!-- INJECT_ACTIVITY: true-false-devoicing -->

## Вимова українських звуків (Pronouncing Ukrainian Sounds)

> **Максим:** Що це там? *(What is this there?)*
> **Юля:** Це великий бик. *(This is a big bull.)*
> **Максим:** А там дім? *(And is a house there?)*
> **Юля:** Ні, це дим. *(No, this is smoke.)*

Some Ukrainian sounds require special attention because they do not have exact matches in English. The vowel **И** is one of the most unique sounds in the language. It is a completely distinct vowel, and you must never confuse it with the sharper, higher **І**. If you swap them, you will say an entirely different word. To train your ear, practice these minimal pairs out loud. Notice the difference between **бик** (bull) and **бік** (side). Feel the shift in your mouth between **дим** (smoke) and **дім** (house). Hear the stark contrast between **кит** (whale) and **кіт** (cat). Watch the Anna Ohoiko pronunciation video to see the exact mouth position for **И**.

Another crucial distinction is the difference between **Г** and **Ґ**. They look similar, but they are two different letters that produce two completely different sounds. The letter **Г** is a voiced fricative. You produce it by letting air flow smoothly through a narrowed throat, creating a deep, breathy sound. You can hear this in words like **гарно** (nicely), **гора** (mountain), and **голова** (head). Never call **Г** "soft" — in Ukrainian phonetics, it is an independent, firm sound. On the other hand, **Ґ** is a voiced stop. You close your throat completely and release it sharply, much like the English "g" in "goat". Practice this sharp stop with words like **ґанок** (porch) and **ґудзик** (button).

Finally, we meet the Ukrainian **Р**, a vibrant, rolled, or trilled consonant. To produce it, your tongue must lightly tap against the alveolar ridge right behind your upper teeth. Practice with Anna Ohoiko's video, focusing on words that build a strong rhythm: **риба** (fish), **ранок** (morning), **робота** (work), and **рука** (hand). Do not worry if your trill is imperfect at first; native speakers will always understand you.

<!-- INJECT_ACTIVITY: quiz-g-vs-ge -->
<!-- INJECT_ACTIVITY: match-up-voiced-voiceless -->

## Підсумок — Summary

We have covered the foundational rules that give the Ukrainian language its distinct phonetic character. Now it is time to review and test your understanding of these core principles.

First, what does the soft sign (**Ь**) do? It is completely silent, but it acts as an instruction to soften or palatalize the consonant that comes immediately before it.

Second, which consonants can be followed by the soft sign? Remember the mnemonic rule: **«ДЗіДЗьо, Де Ти З’їСи Ці ЛиНи»**. This phrase contains exactly the nine eligible consonants: **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **Р**, and **ДЗ**.

Third, when do we use an apostrophe? It acts as a separator and is placed after the labial consonants **Б**, **П**, **В**, **М**, **Ф**, and the letter **Р**, specifically before the iotated vowels **Я**, **Ю**, **Є**, and **Ї**.

Fourth, does a voiced consonant like "б" change its sound at the end of a word? No, it does not. The Ukrainian rule of resilience dictates that voiced consonants mostly stay proudly voiced at the end of words.

Fifth, what is the difference between **Г** and **Ґ**? The letter **Г** is a deep, breathy voiced fricative, while the letter **Ґ** is a sharp, hard voiced stop.

Finally, test yourself by reading these challenge words aloud: **сім'я** (family), **день** (day), **п'ять** (five), **гарно** (nicely), **риба** (fish), and **м'ясо** (meat).

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

**CRITICAL RULE: EVERY single activity object MUST include an `id` field (a unique string like "quiz-grammar", "match-up-vocab"). Do NOT generate an activity without an `id`.**

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: id, instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]
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

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
