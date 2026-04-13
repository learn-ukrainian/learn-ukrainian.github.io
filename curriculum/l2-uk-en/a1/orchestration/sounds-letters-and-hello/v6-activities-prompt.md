<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/sounds-letters-and-hello.yaml` file for module **1: Sounds, Letters, and Hello** (a1).

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

- `<!-- INJECT_ACTIVITY: letter-grid -->`
- `<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->`
- `<!-- INJECT_ACTIVITY: match-up-letters-to-sounds -->`
- `<!-- INJECT_ACTIVITY: group-sort-vowels-consonants -->`
- `<!-- INJECT_ACTIVITY: watch-and-repeat-alphabet -->`
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

When you listen to someone speaking Ukrainian, what you are actually hearing is a series of sounds. When you read a Ukrainian book or a text message, what you are looking at is a series of letters. This might seem like an obvious statement, but confusing these two concepts is a frequent mistake. There is a golden rule taught to every Ukrainian student in the fifth grade. As the textbook by Заболотний (Grade 5, page 83) states: "Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо." This means we hear and pronounce a **звук** (sound), but we see and write a **літера** (letter). A letter is nothing more than a symbol on a piece of paper or a screen. A sound is the physical vibration your mouth and vocal cords produce. They are not the same thing. This distinction is the absolute foundation of Ukrainian phonetics. Ukrainian teachers drill this concept from the very first day of first grade because everything else in the language builds upon it. You cannot truly understand how Ukrainian works until you stop looking at words as just collections of letters and start hearing them as sequences of sounds.

You might assume that every letter matches exactly one sound, but the numbers tell a different story. The Ukrainian language has exactly 33 letters, but it has 38 distinct sounds. Why is there a mismatch? The answer lies in how certain letters behave. Some letters have the special ability to represent two different sounds at the same time. Specifically, the letters Я, Ю, Є, and Ї can represent a combination of two sounds depending on where they appear in a word. On the other hand, one specific letter makes no sound at all. The soft sign, written as Ь, is completely silent. Its only job is to soften the consonant that comes right before it. Because of these rules, you must be careful with your terminology. The textbook by Litvinova (Grade 5, page 130) asks students a very specific pedagogical question: "Чи можна говорити «голосна літера»?" (Can we say "vowel letter"?). The answer is an absolute no. Sounds are either vowels or consonants, not letters. Letters only represent sounds. Calling a symbol on a page a "vowel" is factually incorrect in Ukrainian linguistics.

To start reading, you need to meet the Ukrainian alphabet, known as the **абетка** or алфавіт. It contains all 33 letters in a specific order: А, Б, В, Г, Ґ, Д, Е, Є, Ж, З, И, І, Ї, Й, К, Л, М, Н, О, П, Р, С, Т, У, Ф, Х, Ц, Ч, Ш, Щ, Ь, Ю, Я. Each letter has its own specific name. For English speakers, a major advantage is that Ukrainian spelling is highly phonetic. This means that what you see is almost always exactly what you hear. Unlike English, where the letter "a" sounds completely different in "cat," "father," and "late," Ukrainian letters are remarkably consistent. There are no silent letters hiding in words to trick you (except for the functional role of the soft sign Ь). There are no surprise pronunciations or unpredictable spelling rules to memorize. Once you learn the specific sounds that these 33 symbols represent, you will have the ability to read absolutely any Ukrainian word out loud. For example, knowing the sounds allows you to read the word **тато** (father) perfectly on the first try.

<!-- INJECT_ACTIVITY: letter-grid -->

<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->

## Голосні звуки (Vowel Sounds)

With the difference between a letter and a sound established, the focus shifts to the two main families of sounds. The first family is the **голосний** (vowel sound). A vowel sound is created using only your voice. When you pronounce a vowel, the air flows completely freely from your lungs, through your throat, and out of your mouth with absolutely no obstruction from your lips, teeth, or tongue. Because nothing blocks the air, vowels are the musical core of the language. As the textbook by Большакова (Grade 1, page 24) teaches children through a poem: "Голосні почуєш в пісні, і у темному у лісі... Легко вимовляються, весело співаються!" (You will hear vowels in a song, and in a dark forest... They are easily pronounced, cheerfully sung!). You can sing a vowel sound. You can hold it for as long as you have breath. You can shout a vowel across a wide field to get someone's attention. Without vowels, human speech would just be a series of clicks, hisses, and pops. 

There are exactly 6 vowel sounds in the Ukrainian language: [а], [о], [у], [е], [и], and [і]. However, as discussed earlier, the alphabet has 10 letters that are used to represent these 6 sounds: А, О, У, Е, И, І, Я, Ю, Є, and Ї. The extra four letters (Я, Ю, Є, Ї) are called "iotated" letters. They perform "two jobs," often representing a hidden "y" sound combined with a basic vowel sound. Their exact mechanics appear in depth in the next module. The most important rule to remember is that every single Ukrainian word must have at least one vowel sound. Vowels are the absolute heart of every syllable. A syllable cannot exist without a vowel to give it shape and volume. 

In Ukrainian schools, children learn to map out the sounds in words using special symbols. The textbook by Захарійчук (Grade 1, page 13) introduces a simple sound notation system. In these sound models, every vowel sound is marked with a heavy dot [•]. You can practice hearing these vowel sounds right now. Listen carefully to the word **мама** (mother). You can clearly hear two distinct [а] sounds: мА-мА. Next, listen to the word **молоко** (milk). It contains three identical [о] sounds strung together: мО-лО-кО. Finally, listen to the word **око** (eye), which also clearly features the [о] sound prominently. Below, you will find pronunciation videos from Anna Ohoiko for each of the primary letters that represent vowel sounds. Watch each video carefully, listen to the native pronunciation, and repeat the sounds out loud.

<!-- INJECT_ACTIVITY: match-up-letters-to-sounds -->

## Приголосні звуки (Consonant Sounds)

The second family of sounds in the Ukrainian language is the **приголосний** (consonant sound). The word itself translates to "with a vowel," showing that these sounds are designed to attach themselves to vowels to build syllables. While vowels are made of pure voice, a consonant sound is made with voice plus noise, or sometimes with just noise alone. This noise happens because your mouth creates an obstruction. Your lips might close together, your tongue might tap the roof of your mouth, or your teeth might block the airflow. The textbook by Большакова (Grade 1, page 24) explains this beautifully: "Приголосні деренчать і тихенько шелестять, голосно свистять і шиплять" (Consonants rattle and quietly rustle, loudly whistle and hiss). To prove this, try singing a pure consonant. Take the sound [к] or the sound [п] and try to hold a musical note with it. It is physically impossible. Consonants provide the structure and the hard edges of a word, while vowels provide the volume and the melody. 

The math for consonants is slightly more complex than for vowels. The Ukrainian language has 32 distinct consonant sounds, but these are derived from only 22 consonant letters in the alphabet. This is mostly because many Ukrainian consonants come in distinct pairs: тверді (hard) and м'які (soft). For example, a hard "t" and a soft "t" are considered completely separate sounds, even though they might be written using the same base letter. The notation system from Захарійчук (Grade 1, page 15) shows this clearly: hard consonant sounds are marked with a single dash [–], while soft consonant sounds are marked with a double dash [=]. This hard and soft distinction is a uniquely Slavic phonetic feature. It does not exist in English, which means you will need to train your ear to hear the difference. You can hear a hard consonant in **сон** (dream), which starts with a hard [с-] sound. Conversely, you can hear a soft consonant in **дім** (house), which starts with a soft [д=] sound, or **ніс** (nose), which starts with a soft [н=] sound.

You will meet the consonant letters through the pronunciation videos below: М, Н, С, К, Л, Р, Б, В, Д, П, Т, Г, Ґ, З, Ж, Ш, Х, Й, Ч, Щ, Ц, and Ф. Watch how the speaker shapes her mouth for each one. There are three special letters to pay close attention to. The letter Ґ with its little upturned tail is uniquely Ukrainian and represents a hard "g" sound. The letter Щ is highly efficient because it always represents two distinct sounds packed together: [шч]. Finally, the soft sign, Ь (м'який знак), makes absolutely no sound of its own, but it serves the crucial purpose of softening the consonant that comes immediately before it.

<!-- INJECT_ACTIVITY: group-sort-vowels-consonants -->

<!-- INJECT_ACTIVITY: watch-and-repeat-alphabet -->

## Привіт! (Hello!)

Understanding the mechanics of sounds and letters prepares you for your very first Ukrainian conversation. The fundamental phrases that people use every single day provide the best starting point. Imagine the setting of the first day in a Ukrainian language class. The teacher walks into the room and immediately begins speaking to the students to establish a welcoming atmosphere. 

> **Вчитель:** Добрий день! *(Good afternoon!)*
> **Учні:** Добрий день! *(Good afternoon!)*
> **Вчитель:** **Привіт**! **Як справи**? *(Hi! How are you?)*
> **Учні:** **Добре**, дякую! *(Fine, thank you!)*

In this short exchange, you see the formal greeting "Добрий день" used respectfully with a teacher, followed by the informal greeting **привіт** (hi). When someone asks **як справи** (how are you), the most common and polite response is **добре** (fine, good).

Consider another situation. Two new classmates meet in the hallway just before their first Ukrainian lesson begins. They want to introduce themselves and be friendly.

> **Марко:** **Привіт**! Як тебе звати? *(Hi! What is your name?)*
> **Софія:** **Привіт**! Мене звати Софія. А тебе? *(Hi! My name is Sofia. And you?)*
> **Марко:** Мене звати Марко. *(My name is Marko.)*

This is the very first social application of the sounds you have just learned. By putting these specific sounds together, Marko and Sofia successfully introduce themselves.

As the conversation continues, Sofia expresses her happiness at meeting her new classmate.

> **Софія:** Рада тебе бачити! *(Glad to see you!)*
> **Марко:** Радий тебе бачити! *(Glad to see you!)*

Notice carefully how they say the exact same English phrase, but the Ukrainian words are slightly different. Sofia, a female speaker, says "рада." Marko, a male speaker, says "радий." The Ukrainian language has gendered forms for many words. This is your first encounter with grammatical gender, which will become a major structural topic starting in module M08. For now, observe that speakers adapt their words based on who they are.

Applying these rules directly, a "звуковий аналіз" (sound analysis) on the word **привіт** breaks down the letters to reveal the exact sounds inside:

* П represents the sound [п] (приголосний)
* р represents the sound [р] (приголосний)
* и represents the sound [и] (**голосний**)
* в represents the sound [в] (приголосний)
* і represents the sound [і] (**голосний**)
* т represents the sound [т] (приголосний)

Counted out, the word contains exactly two **голосні** (vowels) and four приголосні (consonants). Because it has two vowel sounds, the word has two syllables. Every type of sound you learned about in this module appears right here in this one simple greeting.

<!-- INJECT_ACTIVITY: fill-in-greeting -->

## Підсумок (Summary)

This module established the foundation of Ukrainian phonetics. Review the core concepts with a few self-check questions to verify this foundation. 

First, how many letters are in the Ukrainian alphabet? There are exactly 33 літери. 
Second, how many sounds are there in the Ukrainian language? There are 38 звуків. 
Why are the numbers different? The numbers differ because iotated letters (Я, Ю, Є, Ї) can make two distinct sounds, while the soft sign (Ь) makes absolutely no sound at all. 
What are голосні? These are vowel sounds made only with your voice, meaning they can be easily sung without any airflow obstruction. 
What are приголосні? These are consonant sounds made with a physical obstruction in the mouth, which means they cannot be sung. 
Can you say "голосна літера"? Absolutely not. Sounds are голосні, not letters; letters merely represent sounds on paper. 
Finally, what does **привіт** mean? It is the informal greeting for "hi." And how do you answer **як справи**? You can say **добре**, **чудово** (great, wonderful), or **нормально** (okay).
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: sounds-letters-and-hello
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
