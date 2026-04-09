<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/sounds-letters-and-hello.yaml` file for module **1: Sounds, Letters, and Hello** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-sounds-letters -->`
- `<!-- INJECT_ACTIVITY: letter-grid-alphabet -->`
- `<!-- INJECT_ACTIVITY: group-sort-sounds -->`
- `<!-- INJECT_ACTIVITY: match-up-letters -->`
- `<!-- INJECT_ACTIVITY: watch-repeat-pronunciation -->`
- `<!-- INJECT_ACTIVITY: fill-in-greeting -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Distinguish between sounds (звуки) and letters (літери). Example questions:
    ''Що ми чуємо і вимовляємо?'' → ''звуки'' | ''Що ми бачимо і пишемо?'' → ''літери''
    | ''Скільки літер в абетці?'' → ''33'' | ''Скільки звуків в українській мові?''
    → ''38'' | ''Чи можна говорити «голосна літера»?'' → ''Ні, голосний — це звук,
    не літера.'''
  items: 6
  type: quiz
- focus: 'Match Ukrainian letters to the sounds they represent — following Захарійчук''s
    ''Бачу... Чую...'' pattern. Pairs: А ↔ [а], О ↔ [о], У ↔ [у], М ↔ [м], К ↔ [к],
    Н ↔ [н]. This is how Ukrainian first-graders learn: see the letter (бачу), hear
    the sound (чую).'
  items: 6
  type: match-up
- focus: 'Complete a basic greeting dialogue with blanks. ''— {Привіт}! Як {справи}?''
    / ''— {Добре}. А у {тебе}?'' / ''— {Чудово}.'' Options per blank: Привіт / справи
    / Добре / тебе / Чудово / Нормально.'
  items: 4
  type: fill-in
- focus: 'Sort Ukrainian sounds into Голосні (vowels) and Приголосні (consonants).
    Голосні: [а], [о], [у], [е], [и], [і]. Приголосні: [к], [м], [т], [в], [н], [р],
    [с], [х].'
  items: 8
  type: group-sort
- focus: 'Interactive alphabet card grid showing all 33 Ukrainian letters. Each card:
    upper/lower case, emoji key word, vowel/consonant coloring. Vowel letters highlighted
    differently from consonant letters. Ь marked as special (no sound).'
  items: 33
  type: letter-grid
- focus: 'Pronunciation practice with Anna Ohoiko videos. Vowels: А (hvB3VpcR3ZE),
    У (VB1O6PmtYRU), Е (KFlsroBW0dk), И (W-1rCu0indE), І (Z9TH0H4ShGo). Consonants:
    М (Ez95H4ibuJo), Н (vNUfiKHPYaU), С (7UsFBgSL91E), К (J7sGEI4-xJo), Л (v6-3Xg52Buk),
    Р (fMGsQ5KPQgg). Each item: YouTube video + letter + key word + sound notation.'
  items: 11
  type: watch-and-repeat


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- нормально (okay)
- тато (father)
- око (eye)
- дім (house)
- ніс (nose)
- сон (dream)
required:
- звук (sound)
- літера (letter)
- голосний (vowel sound)
- приголосний (consonant sound)
- привіт (hi, informal)
- як справи (how are you)
- добре (fine, good)
- чудово (great, wonderful)
- мама (mother)
- молоко (milk)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Звуки і літери (Sounds and Letters)

Look at the text on this page. What you are seeing are letters. Now, say a word out loud. What you just produced is a sound. This distinction is the absolute foundation of the Ukrainian language. There is a golden rule taught to every Ukrainian student in the fifth grade, from the textbook by Zabolotnyi: **Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо** (We hear and pronounce sounds, but we see and write letters). Think of it like music: the sound is the physical note you play on an instrument, while the letter is simply the sheet music written on paper to record it. Ukrainian teachers drill this difference from the very first day of grade school because confusing the visual symbol with the physical sound causes immediate pronunciation errors. 

You might wonder how a language can have a different number of sounds and letters. The math of Ukrainian is interesting: the alphabet has exactly 33 letters, but the spoken language has 38 distinct sounds. This mismatch occurs because certain "smart" letters can represent two sounds at the exact same time. For example, the letters **Я**, **Ю**, **Є**, and **Ї** can hold a combination of sounds, acting like a hidden "y" sound before a vowel. Conversely, one specific letter—the soft sign, written as **Ь**—makes absolutely no sound of its own. It acts only as a silent modifier, slightly changing how you pronounce the consonant that stands directly before it. Remember that letters are just the visual clothing that sounds wear.

Because sounds and letters are strictly separate concepts, Ukrainian demands linguistic accuracy when you discuss them. In a fifth-grade textbook, the author Litvinova asks students a pedagogical question: **Чи можна говорити «голосна літера»?** (Is it possible to say "vowel letter"?). The answer is a strict no. The word **голосний** (vowel) describes the physical nature of a sound that is made with your voice, not the ink on a page. A letter like **А** is simply a visual symbol representing the vowel sound. It cannot be a vowel itself. This precision helps learners truly understand the phonetic logic of the language.

The complete collection of these 33 symbols is the Ukrainian alphabet. The native Ukrainian term for this sequence is **абетка**, derived directly from the names of the first two letters, А and Бе. You will also frequently hear the term **алфавіт**. Unlike English, where spelling can be completely unpredictable, Ukrainian is highly phonetic. What you see on the page is almost exactly what you hear when you speak. There are no silent letters waiting to trick you, and no surprise pronunciations. To master these 33 letters and 38 sounds, you will watch a series of short pronunciation videos by Anna Ohoiko. She will serve as your primary guide for hearing the authentic sounds of the language.

<!-- INJECT_ACTIVITY: quiz-sounds-letters -->

<!-- INJECT_ACTIVITY: letter-grid-alphabet -->

## Голосні звуки (Vowel Sounds)

The core of the language begins with **голосні звуки** (vowel sounds). In a Ukrainian first-grade textbook, author Bolshakova teaches children about vowels through a simple poem: **Голосні почуєш в пісні, і у темному у лісі, і коли дивуєшся, і коли милуєшся. Легко вимовляються, весело співаються!** (You will hear vowels in a song, and in a dark forest, and when you are surprised, and when you are admiring. They are easily pronounced, cheerfully sung!). Vowels are made entirely with your voice. The air flows freely from your lungs and through your mouth without hitting any physical obstruction like your lips, teeth, or tongue. Because they are pure voice, vowels are the only sounds in the language that you can truly sing, stretch out, or shout clearly across a large field.

There are exactly 6 pure vowel sounds in Ukrainian: [а], [о], [у], [е], [и], and [і]. However, as you look at the alphabet, you will notice there are 10 vowel letters: **А**, **О**, **У**, **Е**, **И**, **І**, **Я**, **Ю**, **Є**, and **Ї**. The extra four letters (**Я**, **Ю**, **Є**, **Ї**) are known as "iotated" vowels. They are those "smart letters" mentioned earlier that can represent two sounds at once. You will learn their exact mechanics later, but for now, know that every single Ukrainian word must have at least one vowel sound. Vowels are the absolute heart of every syllable. You cannot form a Ukrainian syllable without exactly one vowel sound holding it together.

When Ukrainian children analyze words, they use a special visual notation. According to the first-grade textbook by Zakhariichuk, a vowel sound is marked with a simple dot: [•]. You can practice hearing these vowels in basic words right now. Listen to the word **мама** (mother). You hear two distinct [а] sounds: [мА-мА]. Now listen to **молоко** (milk). This word flows with three [о] sounds: [мО-лО-кО]. The word **око** (eye) contains two [о] sounds: [О-кО]. These pure sounds must be mastered completely before you move on to complex reading. When you watch the pronunciation videos for the vowel letters, focus heavily on mimicking that clear, unobstructed airflow.

<!-- INJECT_ACTIVITY: group-sort-sounds -->

<!-- INJECT_ACTIVITY: match-up-letters -->

## Приголосні звуки (Consonant Sounds)

The partners to the vowels are the **приголосні звуки** (consonant sounds). The author Bolshakova describes them in contrast to vowels: **Приголосні деренчать і тихенько шелестять, голосно свистять і шиплять** (Consonants rattle and quietly rustle, loudly whistle and hiss). Consonants are formed very differently from vowels. Instead of free-flowing air, consonants are made by creating a physical obstruction in your mouth using your tongue, your teeth, or your lips. They consist of voice mixed with noise, or sometimes just noise alone. Because the air is blocked or squeezed, you cannot sing a pure consonant sound like [к] or [т].

The Ukrainian language features 32 consonant sounds produced by 22 consonant letters. A major feature of these sounds is the hard versus soft distinction. Many consonants come in pairs: a **твердий** (hard) version and a **м'який** (soft) version. Soft consonants are palatalized, meaning the middle of your tongue raises toward the roof of your mouth, similar to the "n" in the English word "new". The Zakhariichuk textbook notation marks hard sounds with a single dash [–] and soft sounds with a double dash [=]. This hard and soft distinction does not exist in English, but it is uniquely Slavic and completely changes the meaning of a Ukrainian word.

You will meet the primary consonant letters through video practice: **М**, **Н**, **Т**, **С**, **Л**, **К**, and **Р**. Pay special attention to the letter **Ґ**, which makes a hard [g] sound. This letter is uniquely Ukrainian and has a history of being suppressed during the Soviet era, making it an important symbol of linguistic identity. You will also encounter the letter **Щ**, which is a "double letter" that always represents two sounds together: [шч]. Finally, you will see the soft sign, **Ь**. As a reminder, this letter is the silent "helper" that changes the consonant standing directly before it from a hard sound into a soft one.

<!-- INJECT_ACTIVITY: watch-repeat-pronunciation -->

## Привіт! (Hello!)

Now that you understand the building blocks of the language, it is time for your very first Ukrainian conversation. Following the pattern from Anna Ohoiko’s Ukrainian Lessons Podcast Episode 1, we start with the most common informal greeting: **Привіт!** (Hi!). This friendly word is used exclusively for close relationships: friends, family members, classmates, and peers. You would not use it with a boss or a stranger. After saying hello, the standard follow-up question is **Як справи?** (How are you?). You have several excellent ways to respond to this question. You can say **Добре** (Fine), you can say **Чудово** (Great), or if things are just average, you can simply say **Нормально** (Okay).

Consider a simple meeting between two friends on the street:

> **Анна:** Привіт! Як справи? *(Hi! How are you?)*
> **Іван:** Чудово! А у тебе? *(Great! And you?)*
> **Анна:** Добре. *(Fine.)*

Notice Ivan's question: **А у тебе?** (And you?). This is the most natural way to return a question and keep the conversation flowing smoothly. You might also notice that these sentences are very short. In Ukrainian, we frequently omit the verb "to be" (am, is, are) in these simple present-tense phrases. You do not need to say "I am fine"; you simply state the feeling: **Добре**.

This basic greeting also provides your first encounter with grammatical gender. If someone is happy to see you, their response changes depending on who is speaking. A female speaker will say **Рада тебе бачити!** (Glad to see you!). A male speaker will say **Радий тебе бачити!** (Glad to see you!). The ending of the word changes based on the speaker's gender. Ukrainian adjectives and certain verb forms alter their shape to match gender. This concept is a major part of the language, serving as a brief preview of the "Gender and Nouns" topic arriving in Module 8.

A sound analysis (**звуковий аналіз**) of your first word, **Привіт**, reveals its structure. It breaks down letter by letter: the letter **П** represents the consonant [п], **р** is the consonant [р], **и** is the vowel [и], **в** is the consonant [в], **і** is the vowel [і], and **т** is the consonant [т]. The word contains exactly two vowel sounds and four consonant sounds. Every type of sound category you learned in this module appears in this single greeting.

<!-- INJECT_ACTIVITY: fill-in-greeting -->

## Підсумок (Summary)

Before moving forward, check your understanding of these foundational concepts with the following questions. How many letters are in the Ukrainian alphabet? There are exactly 33 letters. How many sounds exist in the Ukrainian language? There are 38 distinct sounds. What is the fundamental difference between a sound and a letter? Sounds are what you hear and pronounce with your mouth, while letters are the symbols you see and write on paper. What exactly is a **голосний звук**? It is a vowel sound, created using only your voice without any physical obstruction in your mouth. What is a **приголосний звук**? It is a consonant sound, produced by creating an obstruction with your tongue, teeth, or lips. Can you ever say **голосна літера**? Strictly speaking, no. Sounds are vowels or consonants, whereas letters merely represent them visually. Finally, how do you respond to **Як справи?** in a positive way? You can confidently answer **Добре** or **Чудово**.

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
- divide-words: split words into syllables (складоподіл)
- count-syllables: count syllables by counting vowels
- pick-syllables: select open/closed syllables
- odd-one-out: find the word that doesn't belong
- watch-and-repeat: pronunciation video practice
- translate: single words/short phrases English→Ukrainian (multiple choice)
- error-correction: find simple errors (gender agreement, missing ь)

**DO NOT use:** cloze, mark-the-words, select, essay-response, unjumble (learner can't construct Ukrainian sentences yet).

**Pronunciation videos (Anna Ohoiko):**
- Overview: https://www.youtube.com/watch?v=ksXIXj7CXwc
- Full playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV
Use these in exercises: reference specific videos, embed WatchAndRepeat activities.


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

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

### Pattern: grammar-numbers [§4.2.1.3]
**Числівники** (Numerals)
- **quiz** — Яке число?: Розпізнати числівники, записані словами / Recognize written number words
- **fill-in** — Напиши цифру словом: Записати числівник словом по-українськи / Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Зіставити цифри з їхніми українськими назвами / Match digits to their Ukrainian word forms
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Числівники складні для написання — давати варіанти на A1

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

### Pattern: general-reading [§1 (Speech activities — reading)]
**Розуміння тексту** (Reading comprehension)
- **true-false** — Правда чи ні?: Перевірити розуміння тексту або діалогу / Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Відповісти на запитання за текстом / Answer questions about a text passage


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
